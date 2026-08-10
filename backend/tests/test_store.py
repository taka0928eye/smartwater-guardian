"""BE-6: インメモリストア（app/store.py）の単体テスト。

実行方法（backend ディレクトリで）:

    venv/Scripts/python.exe -m pytest tests/test_store.py -v
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone

import pytest

from app.schemas.telemetry import AnalysisResult, GeoLocation, SpectrumPoint
from app.store import InMemoryStore, StoredTelemetry, get_store, reset_store

# テスト間で再利用する固定時刻（UTC）
BASE_AT = datetime(2026, 8, 10, 0, 0, tzinfo=timezone.utc)


def make_record(
    telemetry_id: str = "tlm_1",
    sensor_id: str = "SNS-001",
    severity: int = 1,
    received_at: datetime = BASE_AT,
) -> StoredTelemetry:
    """テスト用の StoredTelemetry を1件生成する。"""
    return StoredTelemetry(
        telemetry_id=telemetry_id,
        sensor_id=sensor_id,
        hydrant_id="HYD-001",
        recorded_at=received_at,
        received_at=received_at,
        location=GeoLocation(latitude=35.7022, longitude=139.7448),
        analysis=AnalysisResult(
            leak_confidence=50.0,
            severity_level=severity,
            dominant_freq_hz=900.0,
            band_energy_ratio=0.5,
            spectrum=[SpectrumPoint(freq_hz=100.0, magnitude=0.1)],
        ),
    )


class TestAddGet:
    """add / get の基本動作。"""

    def test_add_then_get_same_id(self):
        store = InMemoryStore()
        store.add(make_record(telemetry_id="tlm_1"))
        assert store.get("tlm_1") is not None
        assert store.get("tlm_1").telemetry_id == "tlm_1"

    def test_get_unknown_id_returns_none(self):
        store = InMemoryStore()
        store.add(make_record(telemetry_id="tlm_1"))
        assert store.get("tlm_unknown") is None

    def test_len(self):
        store = InMemoryStore()
        store.add(make_record(telemetry_id="tlm_1"))
        store.add(make_record(telemetry_id="tlm_2"))
        assert len(store) == 2


class TestMaxlen:
    """maxlen 超過時の追い出しと index 整合。"""

    def test_eviction_when_over_maxlen(self):
        store = InMemoryStore(maxlen=5)
        for i in range(6):
            store.add(make_record(telemetry_id=f"tlm_{i}"))
        assert len(store) == 5
        # 最古が破棄され、最新が残る
        assert store.get("tlm_0") is None
        assert store.get("tlm_5") is not None

    def test_index_and_deque_consistent_after_eviction(self):
        store = InMemoryStore(maxlen=5)
        for i in range(10):
            store.add(make_record(telemetry_id=f"tlm_{i}"))
        with store._lock:
            assert len(store._index) == len(store._records) == 5

    def test_maxlen_zero_rejected(self):
        with pytest.raises(ValueError):
            InMemoryStore(maxlen=0)


class TestSensorLatest:
    """センサー別の最新状態（_sensor_latest）。"""

    def test_latest_returns_newest_record(self):
        store = InMemoryStore()
        store.add(make_record(telemetry_id="a", sensor_id="SNS-1", received_at=BASE_AT))
        store.add(
            make_record(
                telemetry_id="b",
                sensor_id="SNS-1",
                received_at=BASE_AT + timedelta(minutes=1),
            )
        )
        latest = store.latest_sensor_states()
        assert latest["SNS-1"].telemetry_id == "b"

    def test_latest_survives_eviction(self):
        store = InMemoryStore(maxlen=3)
        for i in range(4):
            store.add(
                make_record(
                    telemetry_id=f"tlm_{i}",
                    sensor_id="SNS-1",
                    received_at=BASE_AT + timedelta(minutes=i),
                )
            )
        assert store.get("tlm_0") is None  # 最古は破棄済み
        latest = store.latest_sensor_states()
        assert latest["SNS-1"].telemetry_id == "tlm_3"  # 破棄されても最新は残る


class TestSortAndFilter:
    """深刻度降順・時刻降順のソートと level / limit フィルタ。"""

    def test_sorted_by_severity_desc(self):
        store = InMemoryStore()
        store.add(make_record("a", severity=2, received_at=BASE_AT))
        store.add(make_record("b", severity=3, received_at=BASE_AT + timedelta(minutes=1)))
        store.add(make_record("c", severity=1, received_at=BASE_AT + timedelta(minutes=2)))
        result = store.list_alerts()
        assert [r.telemetry_id for r in result] == ["b", "a", "c"]
        assert [r.analysis.severity_level for r in result] == [3, 2, 1]

    def test_same_level_newest_first(self):
        store = InMemoryStore()
        store.add(make_record("old", severity=2, received_at=BASE_AT))
        store.add(make_record("new", severity=2, received_at=BASE_AT + timedelta(minutes=5)))
        result = store.list_alerts()
        assert [r.telemetry_id for r in result] == ["new", "old"]

    def test_filter_by_level(self):
        store = InMemoryStore()
        store.add(make_record("a", severity=3, received_at=BASE_AT))
        store.add(make_record("b", severity=2, received_at=BASE_AT + timedelta(minutes=1)))
        store.add(make_record("c", severity=3, received_at=BASE_AT + timedelta(minutes=2)))
        result = store.list_alerts(level=3)
        assert [r.telemetry_id for r in result] == ["c", "a"]

    def test_limit(self):
        store = InMemoryStore()
        for i in range(5):
            store.add(make_record(f"tlm_{i}", severity=1, received_at=BASE_AT + timedelta(minutes=i)))
        result = store.list_alerts(limit=2)
        assert len(result) == 2
        assert result[0].telemetry_id == "tlm_4"

    def test_filter_and_limit(self):
        store = InMemoryStore()
        for i in range(5):
            store.add(
                make_record(
                    f"tlm_{i}",
                    severity=(3 if i % 2 == 0 else 1),
                    received_at=BASE_AT + timedelta(minutes=i),
                )
            )
        result = store.list_alerts(level=3, limit=1)
        assert len(result) == 1
        assert result[0].analysis.severity_level == 3


class TestThreadSafety:
    """threading.Lock による並行 add の安全性。"""

    def test_concurrent_add_no_race(self):
        store = InMemoryStore(maxlen=500)
        errors: list[Exception] = []

        def worker(worker_id: int) -> None:
            try:
                for i in range(100):
                    store.add(
                        make_record(
                            telemetry_id=f"w{worker_id}_{i}",
                            sensor_id=f"SNS-{worker_id}",
                        )
                    )
            except Exception as exc:  # noqa: BLE001 - 失敗を記録して継続
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(w,)) for w in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        assert len(store) == 500
        # index と deque の件数が一致し、ID が一意であること（レースが無いこと）
        with store._lock:
            assert len(store._index) == len(store._records) == 500
            assert len(set(store._index.keys())) == 500


class TestSingleton:
    """get_store / reset_store のシングルトン管理。"""

    def test_get_store_returns_same_instance(self):
        reset_store()
        assert get_store() is get_store()

    def test_reset_store_creates_fresh_instance(self):
        reset_store()
        store = get_store()
        store.add(make_record(telemetry_id="tlm_1"))
        assert len(get_store()) == 1

        reset_store()
        fresh = get_store()
        assert fresh is not store
        assert len(fresh) == 0


class TestClear:
    """clear() でストア全体を空にする（テスト・リセット用の公開API）。"""

    def test_clear_empties_store(self):
        store = InMemoryStore()
        store.add(make_record(telemetry_id="tlm_1", sensor_id="SNS-1"))
        store.add(make_record(telemetry_id="tlm_2", sensor_id="SNS-2"))
        store.clear()
        assert len(store) == 0
        assert store.get("tlm_1") is None
        assert store.latest_sensor_states() == {}


class TestGetHydrants:
    """消火栓マスタローダー（app/data/hydrants.json）。"""

    def test_returns_hydrant_masters(self):
        from app.store import get_hydrants

        hydrants = get_hydrants()
        assert len(hydrants) == 10
        assert hydrants[0].hydrant_id == "HYD-001"
        assert hydrants[0].sensor_id == "SNS-001"
        assert hydrants[0].pipe_id == "P-001"
        assert isinstance(hydrants[0].latitude, float)

    def test_raises_on_missing_file(self, monkeypatch):
        from app.store import HYDRANTS_PATH, get_hydrants

        # 存在しないパスを指すように差し替え、キャッシュ済みマスタを破棄して
        # 「サイレント空台帳にせず例外を上げる」設計を検証する。
        monkeypatch.setattr(
            "app.store.HYDRANTS_PATH",
            HYDRANTS_PATH.parent / "missing.json",
        )
        get_hydrants.cache_clear()
        with pytest.raises(RuntimeError):
            get_hydrants()
        get_hydrants.cache_clear()  # 後続テストで本来のパスを読み直す
