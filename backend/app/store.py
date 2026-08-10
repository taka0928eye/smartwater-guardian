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
from datetime import datetime
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


@lru_cache(maxsize=1)
def get_hydrants() -> list[HydrantMaster]:
    """hydrants.json を1度だけ読み込んでキャッシュする。

    欠損・破損はサイレントな空台帳にせず、起動時に明確に例外を上げる。
    本ファイルは BE-2 が正式に管理する予定のため、BE-6 は互換データの先行作成に留める。
    """
    try:
        data = json.loads(HYDRANTS_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"hydrants.json を読み込めません: {HYDRANTS_PATH}") from exc
    return [HydrantMaster.model_validate(item) for item in data]
