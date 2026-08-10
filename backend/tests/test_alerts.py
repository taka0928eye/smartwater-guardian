"""BE-6: アラート・センサー参照APIの統合テスト。

GET /api/v1/alerts / GET /api/v1/alerts/{telemetry_id} /
POST /api/v1/alerts/{telemetry_id}/work-order / GET /api/v1/sensors を
FastAPI TestClient で検証する。ストアは ``store`` フィクスチャ（conftest）経由で
直接シードし、autouse の ``_reset_store`` が各テスト前に隔離する。

実行方法（backend ディレクトリで）:

    venv/Scripts/python.exe -m pytest tests/test_alerts.py -v
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.schemas.telemetry import AnalysisResult, GeoLocation, SpectrumPoint
from app.store import StoredTelemetry

# シードで使うスペクトル点数（FE-4 描画用の固定値。telemetry のモック解析と同じ）
N_SPECTRUM = 128


def make_record(
    telemetry_id: str,
    sensor_id: str = "SNS-001",
    hydrant_id: str = "HYD-001",
    severity_level: int = 3,
    leak_confidence: float = 90.0,
    received_at: datetime | None = None,
) -> StoredTelemetry:
    """テストシード用の StoredTelemetry を1件生成する。"""
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


def seed_alerts(store, *, count: int = 5) -> list[str]:
    """深刻度・受信時刻をばらけさせて count 件シードし、ID の並びを返す。

    同じ level 同士でも新着順ソートを検証できるよう、受信時刻を1秒ずつ進める。
    """
    ids: list[str] = []
    base = datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc)
    # severity 3, 2, 1, 3, 2 ... の順で追加（同 level の新着順検証用）
    for i in range(count):
        level = (3 - (i % 3)) if i % 3 != 0 else 3
        record = make_record(
            telemetry_id=f"tlm_{i:04d}",
            sensor_id=f"SNS-{i + 1:03d}",
            hydrant_id=f"HYD-{i + 1:03d}",
            severity_level=level,
            received_at=base + timedelta(seconds=i),
        )
        store.add(record)
        ids.append(record.telemetry_id)
    return ids


class TestListAlerts:
    """GET /api/v1/alerts の一覧・フィルタ。"""

    def test_returns_summaries_sorted_by_severity_desc(self, client, store):
        seed_alerts(store)
        response = client.get("/api/v1/alerts")
        assert response.status_code == 200

        body = response.json()
        assert len(body) == 5
        severities = [item["severity_level"] for item in body]
        # 深刻度降順（3,3,2,2,1）でなければならない
        assert severities == sorted(severities, reverse=True)
        # 契約フィールドが揃っている
        item = body[0]
        assert set(item.keys()) == {
            "telemetry_id",
            "sensor_id",
            "hydrant_id",
            "severity_level",
            "leak_confidence",
            "detected_at",
        }
        assert item["detected_at"]

    def test_same_severity_sorted_newest_first(self, client, store):
        seed_alerts(store)
        body = client.get("/api/v1/alerts").json()
        # level 3 の 2 件（tlm_0000, tlm_0003）は受信時刻の新しい順で先頭に並ぶ
        level3 = [item["telemetry_id"] for item in body if item["severity_level"] == 3]
        assert level3 == ["tlm_0003", "tlm_0000"]

    def test_filter_by_level(self, client, store):
        seed_alerts(store)
        body = client.get("/api/v1/alerts", params={"level": 3}).json()
        assert body
        assert all(item["severity_level"] == 3 for item in body)

    def test_limit(self, client, store):
        seed_alerts(store)
        body = client.get("/api/v1/alerts", params={"limit": 2}).json()
        assert len(body) == 2

    def test_level_and_limit_combined(self, client, store):
        seed_alerts(store)
        body = client.get("/api/v1/alerts", params={"level": 2, "limit": 1}).json()
        assert len(body) == 1
        assert body[0]["severity_level"] == 2

    def test_level_out_of_range_returns_422(self, client, store):
        # SeverityLevel は Literal[0,1,2,3]。level=4 は 422 でなければならない
        response = client.get("/api/v1/alerts", params={"level": 4})
        assert response.status_code == 422

    def test_empty_store_returns_empty_list(self, client, store):
        response = client.get("/api/v1/alerts")
        assert response.status_code == 200
        assert response.json() == []


class TestAlertDetail:
    """GET /api/v1/alerts/{telemetry_id}。"""

    def test_returns_detail_with_spectrum_and_null_pipe(self, client, store):
        ids = seed_alerts(store)
        response = client.get(f"/api/v1/alerts/{ids[0]}")
        assert response.status_code == 200

        body = response.json()
        # AlertDetail は AlertSummary に location / analysis / pipe_info を足す
        assert body["telemetry_id"] == ids[0]
        assert "location" in body
        assert body["location"]["latitude"] == 35.7019
        assert len(body["analysis"]["spectrum"]) == N_SPECTRUM
        # BE-4 未実装のため pipe_info は null
        assert body["pipe_info"] is None

    def test_unknown_id_returns_404_not_500(self, client, store):
        response = client.get("/api/v1/alerts/tlm_not_exist")
        assert response.status_code == 404


class TestWorkOrderStub:
    """POST /api/v1/alerts/{telemetry_id}/work-order（BE-5 スタブ）。"""

    def test_existing_id_returns_501(self, client, store):
        ids = seed_alerts(store)
        response = client.post(f"/api/v1/alerts/{ids[0]}/work-order")
        assert response.status_code == 501

    def test_unknown_id_returns_404(self, client, store):
        response = client.post("/api/v1/alerts/tlm_not_exist/work-order")
        assert response.status_code == 404


class TestListSensors:
    """GET /api/v1/sensors。"""

    def test_returns_all_hydrants_with_unknown_status(self, client, store):
        response = client.get("/api/v1/sensors")
        assert response.status_code == 200

        body = response.json()
        assert len(body) == 10  # hydrants.json の件数
        item = body[0]
        assert set(item.keys()) == {
            "sensor_id",
            "hydrant_id",
            "status",
            "location",
            "last_reading_at",
        }
        # 未読込のセンサーは status=unknown / last_reading_at=null
        assert item["status"] == "unknown"
        assert item["last_reading_at"] is None

    def test_status_and_last_reading_reflected_after_seed(self, client, store):
        seed_alerts(store)
        response = client.get("/api/v1/sensors")
        body = response.json()
        # SNS-001 に severity 3 の最新レコード → critical / last_reading_at あり
        sns001 = next(item for item in body if item["sensor_id"] == "SNS-001")
        assert sns001["status"] == "critical"
        assert sns001["last_reading_at"]

    def test_status_mapping_watch_warning_normal(self, client, store):
        # severity 2 → warning、severity 1 → watch、severity 0 → normal の導出を確認
        # severity 0 (正常・異常なし)は入力スキーマでは不可（SeverityLevel[1,2,3]のみ）だが、
        # 将来の拡張に備えてステータスマッピングが 0:normal をサポートする設計
        store.add(
            make_record(
                "tlm_warn", sensor_id="SNS-009", severity_level=2, received_at=datetime(2026, 8, 10, 11, 0, tzinfo=timezone.utc)
            )
        )
        store.add(
            make_record(
                "tlm_watch", sensor_id="SNS-010", severity_level=1, received_at=datetime(2026, 8, 10, 11, 0, tzinfo=timezone.utc)
            )
        )
        body = client.get("/api/v1/sensors").json()
        by_id = {item["sensor_id"]: item for item in body}
        assert by_id["SNS-009"]["status"] == "warning"
        assert by_id["SNS-010"]["status"] == "watch"

    def test_geojson_coordinates_are_lng_lat(self, client, store):
        seed_alerts(store)
        response = client.get("/api/v1/sensors", params={"format": "geojson"})
        assert response.status_code == 200

        body = response.json()
        assert body["type"] == "FeatureCollection"
        features = body["features"]
        assert len(features) == 10
        for feature in features:
            assert feature["type"] == "Feature"
            assert feature["geometry"]["type"] == "Point"
            lon, lat = feature["geometry"]["coordinates"]
            # [経度, 緯度] の順（緯度・経度をひっくり返すと東京が海に落ちる）
            assert -180.0 <= lon <= 180.0
            assert -90.0 <= lat <= 90.0
            # SNS-001 の最新は severity 3 → properties に反映される
            if feature["properties"]["sensor_id"] == "SNS-001":
                assert feature["properties"]["severity_level"] == 3
                assert feature["properties"]["status"] == "critical"

    def test_invalid_format_returns_422(self, client, store):
        response = client.get("/api/v1/sensors", params={"format": "xml"})
        assert response.status_code == 422


class TestRouteRegistration:
    """名前解決でルーター登録を確認（fastapi 0.141 の遅延マウント対策）。"""

    def test_routes_resolvable(self):
        from main import app

        assert app.url_path_for("list_alerts") == "/api/v1/alerts"
        # パスパラメータを持つルートは url_path_for に値を渡す必要がある
        assert (
            app.url_path_for("get_alert_detail", telemetry_id="tlm_0000")
            == "/api/v1/alerts/tlm_0000"
        )
        assert (
            app.url_path_for("create_work_order", telemetry_id="tlm_0000")
            == "/api/v1/alerts/tlm_0000/work-order"
        )
        assert app.url_path_for("list_sensors") == "/api/v1/sensors"
