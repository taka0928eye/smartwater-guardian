"""BE-8: KPIサマリ（推定削減コスト）のテスト。

単価計算（``expected_cost_saved``）・サマリ集計（``calculate_kpi_summary``）・
エンドポイント（``GET /api/v1/kpi/summary``）を TDD で検証する。ストアは
``store`` フィクスチャ経由でシードし、autouse の ``_reset_store`` が各テスト前に隔離する。

実行方法（backend ディレクトリで）:

    venv/Scripts/python.exe -m pytest tests/test_kpi.py -v
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.schemas.kpi import KpiSummary
from app.schemas.telemetry import AnalysisResult, GeoLocation, SpectrumPoint
from app.services.kpi import KPI_ASSUMPTION_DOC, calculate_kpi_summary, expected_cost_saved
from app.store import StoredTelemetry, get_hydrants

# シードで使うスペクトル点数（test_alerts.py と同じ）
N_SPECTRUM = 128


def make_record(
    telemetry_id: str,
    sensor_id: str = "SNS-001",
    hydrant_id: str = "HYD-001",
    severity_level: int = 3,
    leak_confidence: float = 90.0,
    received_at: datetime | None = None,
) -> StoredTelemetry:
    """テストシード用の StoredTelemetry を1件生成する（test_alerts.py と同様）。"""
    now = received_at or datetime.now(timezone.utc)
    return StoredTelemetry(
        telemetry_id=telemetry_id,
        sensor_id=sensor_id,
        hydrant_id=hydrant_id,
        recorded_at=now - timedelta(seconds=30),
        received_at=now,
        location=GeoLocation(latitude=35.7019, longitude=139.7444),
        analysis=AnalysisResult(
            leak_confidence=leak_confidence,
            severity_level=severity_level,
            dominant_freq_hz=900.0,
            band_energy_ratio=0.75,
            spectrum=[SpectrumPoint(freq_hz=float(i), magnitude=1.0) for i in range(N_SPECTRUM)],
        ),
    )


def seed_demo_alerts(store) -> None:
    """デモ内訳（Level1×8 / Level2×3 / Level3×1）をストアにシードする。

    S-5: 8×121,800 + 3×308,000 + 1×150,000 = 2,048,400 円になる。
    """
    base = datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc)
    i = 0
    for level, count in ((1, 8), (2, 3), (3, 1)):
        for _ in range(count):
            store.add(
                make_record(
                    telemetry_id=f"tlm_kpi_{i:04d}",
                    sensor_id=f"SNS-{i % 10 + 1:03d}",
                    hydrant_id=f"HYD-{i % 10 + 1:03d}",
                    severity_level=level,
                    received_at=base + timedelta(seconds=i),
                )
            )
            i += 1


class TestExpectedCostSaved:
    """expected_cost_saved() の単価計算（docs/business-model.md §3.3）。"""

    def test_level0_is_zero(self) -> None:
        # E_avoided(0) = 0（正常。回避コストは発生しない）
        assert expected_cost_saved(0) == 0

    def test_level1_matches_formula(self) -> None:
        # E_avoided(1) = p1 × (C_burst − C_repair1) = 0.12 × (1,200,000 − 185,000)
        assert expected_cost_saved(1) == 121_800

    def test_level2_matches_formula(self) -> None:
        # E_avoided(2) = p2 × (C_burst − C_repair2) = 0.35 × (1,200,000 − 320,000)
        assert expected_cost_saved(2) == 308_000

    def test_level3_is_fixed_response_saved(self) -> None:
        # E_avoided(3) = C_response_saved = 150,000（位置の即時特定による復旧時間短縮分）
        assert expected_cost_saved(3) == 150_000


class TestCalculateKpiSummary:
    """calculate_kpi_summary() の集計ロジック（S-2 / S-3 / S-4）。"""

    def test_aggregates_from_store_data(self, store) -> None:
        # デモ内訳（L1×8 / L2×3 / L3×1）→ 件数と合計 2,048,400 円（S-5）
        seed_demo_alerts(store)
        summary = calculate_kpi_summary()
        assert summary.level1_count == 8
        assert summary.level2_count == 3
        assert summary.level3_count == 1
        assert summary.estimated_cost_saved_yen == 2_048_400
        # total_sensors は hydrants.json の実件数（現状20件）と一致（S-3）
        assert summary.total_sensors == len(get_hydrants()) == 20
        # 試算値である旨と算定根拠を常時明示
        assert summary.is_estimate is True
        assert summary.assumption_doc == KPI_ASSUMPTION_DOC

    def test_empty_store_returns_zero_counts_with_real_sensor_count(self, store) -> None:
        # 空ストアでも全項目0（total_sensors のみ実件数）を返す（S-4）
        summary = calculate_kpi_summary()
        assert summary.level1_count == 0
        assert summary.level2_count == 0
        assert summary.level3_count == 0
        assert summary.estimated_cost_saved_yen == 0
        assert summary.total_sensors == len(get_hydrants())

    def test_level0_only_store_counts_zero(self, store) -> None:
        # Level 0（正常）は集計対象外。カウント・コストとも0
        store.add(make_record("tlm_lvl0", severity_level=0))
        summary = calculate_kpi_summary()
        assert summary.level1_count == 0
        assert summary.level2_count == 0
        assert summary.level3_count == 0
        assert summary.estimated_cost_saved_yen == 0


class TestKpiSummaryEndpoint:
    """GET /api/v1/kpi/summary（TestClient 統合境界）。"""

    def test_returns_200_with_seven_fields(self, client, store) -> None:
        # S-1: 5項目 + is_estimate / assumption_doc の7項目を返す
        response = client.get("/api/v1/kpi/summary")
        assert response.status_code == 200
        body = response.json()
        assert set(body.keys()) == {
            "total_sensors",
            "level1_count",
            "level2_count",
            "level3_count",
            "estimated_cost_saved_yen",
            "is_estimate",
            "assumption_doc",
        }

    def test_seeded_store_returns_demo_total(self, client, store) -> None:
        # S-5: シード済みストアで合計 2,048,400 円を返す
        seed_demo_alerts(store)
        response = client.get("/api/v1/kpi/summary")
        assert response.status_code == 200
        body = response.json()
        assert body["level1_count"] == 8
        assert body["level2_count"] == 3
        assert body["level3_count"] == 1
        assert body["estimated_cost_saved_yen"] == 2_048_400
        assert body["is_estimate"] is True

    def test_empty_store_returns_200_with_zeros(self, client, store) -> None:
        # S-4: 空ストアでも 200 で全項目0・total_sensors=20（500にしない）
        response = client.get("/api/v1/kpi/summary")
        assert response.status_code == 200
        body = response.json()
        assert body["level1_count"] == 0
        assert body["level2_count"] == 0
        assert body["level3_count"] == 0
        assert body["estimated_cost_saved_yen"] == 0
        assert body["total_sensors"] == 20
        assert body["assumption_doc"] == KPI_ASSUMPTION_DOC


class TestKpiSummarySchema:
    """KpiSummary の型制約をランタイム検証する。

    プロジェクト学習済みルール（mypy 非導入）に基づき、Pydantic の型制約
    （ge=0 / strict / extra=forbid）が実際に ValidationError を送出することを
    検証する。``today_detections`` が契約外であること（D-3）の確認も兼ねる。
    """

    def _base_kwargs(self) -> dict[str, object]:
        return {
            "total_sensors": 10,
            "level1_count": 0,
            "level2_count": 0,
            "level3_count": 0,
            "estimated_cost_saved_yen": 0,
            "is_estimate": True,
            "assumption_doc": KPI_ASSUMPTION_DOC,
        }

    def test_negative_count_rejected(self) -> None:
        with pytest.raises(ValidationError):
            KpiSummary(**{**self._base_kwargs(), "level1_count": -1})

    def test_negative_cost_rejected(self) -> None:
        with pytest.raises(ValidationError):
            KpiSummary(**{**self._base_kwargs(), "estimated_cost_saved_yen": -1})

    def test_wrong_type_rejected(self) -> None:
        # strict=True のため str は int へ暗黙キャストされず弾かれる
        with pytest.raises(ValidationError):
            KpiSummary(**{**self._base_kwargs(), "total_sensors": "ten"})

    def test_extra_field_rejected(self) -> None:
        # extra="forbid" + today_detections は契約外（D-3）
        with pytest.raises(ValidationError):
            KpiSummary(**{**self._base_kwargs(), "today_detections": 5})


class TestInitialSensorState:
    """マスタ20台のセンサの初期正常状態（ユーザー要求）。

    hydrants.json のセンサは初期状態で全て正常（severity_level=0）として初期化される。
    """

    def test_initial_sensors_are_normal(self, store) -> None:
        # アプリ初期化時、hydrants.json の20台は全て正常状態でストアに登録される
        from app.store import initialize_sensors
        initialize_sensors(store)

        # ストアが empty で かつ初期化後
        alerts = store.get_all()

        # 20 件の正常状態レコード（Level 0）が登録されているはず
        assert len(alerts) == 20
        for alert in alerts:
            assert alert.analysis.severity_level == 0
            assert alert.sensor_id in [f"SNS-{i:03d}" for i in range(1, 21)]

    def test_kpi_summary_counts_initial_normal_sensors(self, store) -> None:
        # 初期化後、KPI サマリで Level 1-3 はすべて 0
        from app.store import initialize_sensors
        initialize_sensors(store)

        summary = calculate_kpi_summary()
        assert summary.level1_count == 0
        assert summary.level2_count == 0
        assert summary.level3_count == 0
        # 正常状態は集計対象外（Level 0）
        assert summary.total_sensors == 20
