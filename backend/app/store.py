"""スレッドセーフなインメモリストア（BE-6）。

CLAUDE.md §3 の「本番用DBは構築しない」規定に基づき、
``collections.deque(maxlen=500)`` + ``dict`` 索引を ``threading.Lock`` で保護する。
FastAPI は同期 ``def`` ハンドラをスレッドプールで並行実行するため、Lock なしの
dict 更新は競合する。

本モジュールは BE-3（services/audio.py の FFT 解析）が本実装を追加するまで、
解析結果を保存する仮の受け皿として機能する。BE-2（消火栓マスタ）も本番実装で
hydrants.json を正式に管理する。
"""

from __future__ import annotations

import json
import threading
from collections import deque
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from app.schemas.alert import HydrantMaster
from app.schemas.telemetry import AnalysisResult, GeoLocation

# 保持件数の上限（maxlen 超過時は最古から破棄される）
DEFAULT_MAXLEN = 500

# 消火栓マスタ JSON のパス（cwd 非依存で解決する）
HYDRANTS_PATH = Path(__file__).resolve().parent / "data" / "hydrants.json"


class StoredTelemetry(BaseModel):
    """ストア内部で保持する1件分の解析済みテレメトリ。

    frozen=True で意図しない変異を防ぐ。``AlertSummary`` / ``AlertDetail`` は
    これを起点にルーター側で変換する。
    """

    model_config = ConfigDict(frozen=True, strict=True, extra="forbid")

    telemetry_id: str
    sensor_id: str
    hydrant_id: str
    recorded_at: datetime  # センサー録音日時（payload 由来）
    received_at: datetime  # サーバー受信日時（= detected_at）
    location: GeoLocation
    analysis: AnalysisResult
    audio_pcm16: bytes | None = None
    sample_rate_hz: int | None = None


class InMemoryStore:
    """解析済みテレメトリを保持するスレッドセーフなインメモリストア。"""

    def __init__(self, maxlen: int = DEFAULT_MAXLEN) -> None:
        if maxlen < 1:
            raise ValueError("maxlen は1以上である必要があります")
        self._maxlen = maxlen
        self._records: deque[StoredTelemetry] = deque(maxlen=maxlen)
        self._index: dict[str, StoredTelemetry] = {}
        self._sensor_latest: dict[str, StoredTelemetry] = {}
        self._lock = threading.Lock()

    def add(self, record: StoredTelemetry) -> None:
        """レコードを追加する。満杯時は最古を明示的に破棄し、索引からも削除する。

        ``deque(maxlen=N)`` は自動破棄のため「どの ID が破棄されたか」が分からない。
        そこで追加前に満杯チェックし、``popleft`` で ID を取得してから ``_index`` を
        同期する。
        """
        with self._lock:
            if len(self._records) == self._maxlen:
                evicted = self._records.popleft()
                self._index.pop(evicted.telemetry_id, None)
                # sensor_latest は「最後に知った状態」として破棄しない。
                # デモで同一センサーから 500 件超送っても地図のマーカーが消えないようにする
                # （破棄済み ID の詳細は 404 だが、地図には残る非対称を許容する設計）。
            self._records.append(record)
            self._index[record.telemetry_id] = record
            self._sensor_latest[record.sensor_id] = record

    def get(self, telemetry_id: str) -> StoredTelemetry | None:
        """ID でレコードを取得する。無ければ None。"""
        with self._lock:
            return self._index.get(telemetry_id)

    def get_all(self) -> list[StoredTelemetry]:
        """全レコードを挿入順で返す（防災クラスタリング等の全件走査用）。"""
        with self._lock:
            return list(self._records)

    def list_alerts(
        self, level: int | None = None, limit: int | None = None
    ) -> list[StoredTelemetry]:
        """アラート一覧を深刻度降順・時刻降順で返す。

        level / limit で絞り込み可能。ソート → フィルタ → limit の順に適用する。
        """
        with self._lock:
            records = list(self._records)
        records.sort(
            key=lambda r: (r.analysis.severity_level, r.received_at), reverse=True
        )
        if level is not None:
            records = [r for r in records if r.analysis.severity_level == level]
        if limit is not None:
            records = records[:limit]
        return records

    def latest_sensor_states(self) -> dict[str, StoredTelemetry]:
        """センサー別の最新レコードを浅いコピーで返す。"""
        with self._lock:
            return dict(self._sensor_latest)

    def clear(self) -> None:
        """ストアを空にする（テスト用）。"""
        with self._lock:
            self._records.clear()
            self._index.clear()
            self._sensor_latest.clear()

    def replace_all(self, records: list[StoredTelemetry]) -> None:
        """全レコードをアトミックに置換し、索引を再構築する。"""
        with self._lock:
            self._records = deque(records, maxlen=self._maxlen)
            self._index = {
                record.telemetry_id: record for record in self._records
            }
            self._sensor_latest = {}
            for record in self._records:
                self._sensor_latest[record.sensor_id] = record

    def __len__(self) -> int:
        with self._lock:
            return len(self._records)


# --- モジュールレベルシングルトン ---

_store: InMemoryStore | None = None


def get_store() -> InMemoryStore:
    """アプリ全体で共有するシングルトンを返す。

    ルーターは必ずハンドラ実行時にこの関数を呼ぶ（import 時捕捉はテスト隔離を壊す）。
    """
    global _store
    if _store is None:
        _store = InMemoryStore(maxlen=DEFAULT_MAXLEN)
    return _store


def reset_store() -> None:
    """テスト用: シングルトンを破棄し、次回 get_store() で新規生成させる。"""
    global _store
    _store = None


# --- 消火栓マスタローダー ---

_disaster_sensor_ids: set[str] = set()
_disaster_baseline_records: list[StoredTelemetry] | None = None


def register_disaster_sensors(
    sensor_ids: list[str], baseline_records: list[StoredTelemetry] | None = None
) -> None:
    """防災シミュレーションで Level 3 に変化した sensor_id を記録する。

    ``/disaster/summary`` はこの集合に含まれる sensor_id のみを被災エリア
    クラスタの対象とする（通常の漏水検知で Level 3 になったセンサーは対象外）。
    複数回のシミュレーション実行分を**累積**する（直近の選出で上書きしない）。
    テスト隔離・``/demo/clear``・``/demo/seed-batch`` 実行時は
    ``clear_disaster_state()`` で明示的にクリアする。
    """
    global _disaster_sensor_ids, _disaster_baseline_records
    _disaster_sensor_ids = _disaster_sensor_ids | set(sensor_ids)
    if baseline_records is not None and _disaster_baseline_records is None:
        _disaster_baseline_records = list(baseline_records)


def get_disaster_sensor_ids() -> set[str]:
    """防災シミュレーションで Level 3 に変化した sensor_id の集合を返す。"""
    return set(_disaster_sensor_ids)


def clear_disaster_state() -> None:
    """防災シミュレーションで記録した sensor_id をクリアする。"""
    global _disaster_sensor_ids, _disaster_baseline_records
    _disaster_sensor_ids = set()
    _disaster_baseline_records = None


def restore_disaster_baseline(store: InMemoryStore) -> int:
    """開始前スナップショットを復元し、防災状態をクリアする。"""
    global _disaster_baseline_records
    restored_sensor_count = len(_disaster_sensor_ids)
    if _disaster_baseline_records is not None:
        store.replace_all(_disaster_baseline_records)
    clear_disaster_state()
    return restored_sensor_count


@lru_cache(maxsize=1)
def _get_hydrants_from_file() -> list[HydrantMaster]:
    """hydrants.json を1度だけ読み込んでキャッシュする（内部用）。

    欠損・破損はサイレントな空台帳にせず、明確に例外を上げる。``@lru_cache`` による
    遅延初期化のため、例外が実際に飛ぶのはアプリ起動時ではなく初回呼び出し時（最初に
    ``/api/v1/sensors`` 等が呼ばれたタイミング）。
    """
    try:
        data = json.loads(HYDRANTS_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"hydrants.json を読み込めません: {HYDRANTS_PATH}") from exc
    return [HydrantMaster.model_validate(item) for item in data]


def get_hydrants() -> list[HydrantMaster]:
    """hydrants.json の消火栓一覧を返す。"""
    return _get_hydrants_from_file()


def initialize_sensors(store: InMemoryStore) -> None:
    """マスタ登録済みのセンサを正常状態（Level 0）で初期化する。

    hydrants.json のセンサに対して severity_level=0 のレコードを生成し、
    ストアに追加する。アプリ起動時の初期状態を表現する。
    """
    from app.schemas.telemetry import AnalysisResult, GeoLocation, SpectrumPoint

    now = datetime.now(timezone.utc)

    # hydrants.json の実データ分のみ初期化（ランタイムセンサー除外）
    base_hydrants = _get_hydrants_from_file()

    for idx, hydrant in enumerate(base_hydrants):
        record = StoredTelemetry(
            telemetry_id=f"INIT-{hydrant.sensor_id}",
            sensor_id=hydrant.sensor_id,
            hydrant_id=hydrant.hydrant_id,
            recorded_at=now,
            received_at=now,
            location=GeoLocation(
                latitude=hydrant.latitude,
                longitude=hydrant.longitude,
            ),
            analysis=AnalysisResult(
                severity_level=0,  # 正常状態
                leak_confidence=0.0,
                dominant_freq_hz=0.0,
                band_energy_ratio=0.0,
                spectrum=[SpectrumPoint(freq_hz=float(i), magnitude=0.0) for i in range(128)],
            ),
        )
        store.add(record)
