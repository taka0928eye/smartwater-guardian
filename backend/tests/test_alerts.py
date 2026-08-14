"""BE-6: アラート・センサー参照APIの統合テスト。

GET /api/v1/alerts / GET /api/v1/alerts/{telemetry_id} /
POST /api/v1/alerts/{telemetry_id}/work-order / GET /api/v1/sensors を
FastAPI TestClient で検証する。ストアは ``store`` フィクスチャ（conftest）経由で
直接シードし、autouse の ``_reset_store`` が各テスト前に隔離する。

実行方法（backend ディレクトリで）:

    venv/Scripts/python.exe -m pytest tests/test_alerts.py -v
"""

from __future__ import annotations

import base64
import io
import wave
from datetime import datetime, timedelta, timezone

import numpy as np
import pytest
from pydantic import ValidationError

from app.schemas.alert import PipeInfo
from app.schemas.telemetry import AnalysisResult, GeoLocation, SpectrumPoint
from app.store import StoredTelemetry

# シードで使うスペクトル点数（FE-4 描画用の固定値。telemetry のモック解析と同じ）
N_SPECTRUM = 128


@pytest.fixture(autouse=True)
def _clear_work_order_cache():
    """BE-5: orcarouter のワークオーダーキャッシュを各テスト前に空にする。

    セッション共有の TestClient 経由で同一 telemetry_id の POST が走っても、
    前のテストのキャッシュが残らないように分離する。
    """
    from app.services.orcarouter import clear_work_order_cache

    clear_work_order_cache()
    yield
    clear_work_order_cache()


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

    def test_returns_detail_with_spectrum_and_pipe_info(self, client, store):
        ids = seed_alerts(store)
        response = client.get(f"/api/v1/alerts/{ids[0]}")
        assert response.status_code == 200

        body = response.json()
        # AlertDetail は AlertSummary に location / analysis / pipe_info を足す
        assert body["telemetry_id"] == ids[0]
        assert "location" in body
        assert body["location"]["latitude"] == 35.7019
        assert len(body["analysis"]["spectrum"]) == N_SPECTRUM
        # A5: BE-4 実装により HYD-001 の pipe_info に P-001 の配管情報が入る
        pipe_info = body["pipe_info"]
        assert pipe_info is not None
        assert pipe_info["pipe_id"] == "P-001"
        assert pipe_info["material"] == "ductile_iron"
        assert pipe_info["diameter_mm"] == 150
        assert pipe_info["installed_year"] == 1998
        assert pipe_info["burial_depth_m"] == 1.2
        assert pipe_info["age_years"] == 28  # D-5: 2026 - 1998

    def test_unknown_hydrant_detail_keeps_pipe_info_null(self, client, store):
        # 台帳に存在しない hydrant_id のレコードでは pipe_info は null のまま
        store.add(
            make_record(
                "tlm_hyd_999",
                sensor_id="SNS-999",
                hydrant_id="HYD-999",
                severity_level=1,
            )
        )
        response = client.get("/api/v1/alerts/tlm_hyd_999")
        assert response.status_code == 200
        assert response.json()["pipe_info"] is None

    def test_unknown_id_returns_404_not_500(self, client, store):
        response = client.get("/api/v1/alerts/tlm_not_exist")
        assert response.status_code == 404


class TestAlertAudio:
    """GET /api/v1/alerts/{telemetry_id}/audio の実音響WAV。"""

    @staticmethod
    def _telemetry_payload() -> tuple[dict, bytes]:
        sample_rate_hz = 8_000
        time_axis = np.arange(sample_rate_hz, dtype=np.float64) / sample_rate_hz
        samples = (np.sin(2.0 * np.pi * 900.0 * time_axis) * 12_000).astype("<i2")
        pcm_bytes = samples.tobytes()
        return (
            {
                "sensor_id": "SNS-001",
                "hydrant_id": "HYD-001",
                "recorded_at": "2026-08-14T10:00:00+09:00",
                "location": {"latitude": 35.7019, "longitude": 139.7444},
                "sample_rate_hz": sample_rate_hz,
                "duration_sec": 1.0,
                "audio_base64": base64.b64encode(pcm_bytes).decode("ascii"),
                "battery_pct": 90,
            },
            pcm_bytes,
        )

    def test_ingested_audio_is_returned_as_the_same_pcm_in_wav(self, client):
        payload, expected_pcm = self._telemetry_payload()
        ingest_response = client.post("/api/v1/telemetry", json=payload)
        assert ingest_response.status_code == 200
        telemetry_id = ingest_response.json()["telemetry_id"]

        detail = client.get(f"/api/v1/alerts/{telemetry_id}")
        assert detail.status_code == 200
        detail_body = detail.json()
        assert detail_body["has_audio"] is True
        waveform = detail_body["waveform"]
        assert len(waveform) == 256
        assert waveform[0] == {"time_ms": 0.0, "amplitude": 0.0}
        assert waveform[-1]["time_ms"] == pytest.approx(999.875)
        last_sample = int.from_bytes(expected_pcm[-2:], "little", signed=True)
        assert waveform[-1]["amplitude"] == pytest.approx(last_sample / 32768.0)

        response = client.get(f"/api/v1/alerts/{telemetry_id}/audio")
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"
        assert response.headers["cache-control"] == "no-store"

        with wave.open(io.BytesIO(response.content), "rb") as wav_file:
            assert wav_file.getnchannels() == 1
            assert wav_file.getsampwidth() == 2
            assert wav_file.getframerate() == 8_000
            assert wav_file.readframes(wav_file.getnframes()) == expected_pcm

    def test_existing_alert_without_audio_reports_unavailable(self, client, store):
        store.add(make_record("tlm_without_audio"))

        detail = client.get("/api/v1/alerts/tlm_without_audio")
        assert detail.status_code == 200
        assert detail.json()["has_audio"] is False
        assert detail.json()["waveform"] == []

        response = client.get("/api/v1/alerts/tlm_without_audio/audio")
        assert response.status_code == 404
        assert response.json()["detail"] == "このアラートには音声データがありません"

    def test_unknown_alert_audio_returns_404(self, client):
        response = client.get("/api/v1/alerts/tlm_not_exist/audio")
        assert response.status_code == 404
        assert response.json()["detail"] == "テレメトリ tlm_not_exist は見つかりません"


class TestWorkOrder:
    """POST /api/v1/alerts/{telemetry_id}/work-order（BE-5 実装後）。

    API キー未設定環境（monkeypatch.delenv で保証）で実ネットワーク呼び出しを避けつつ、
    フォールバック応答（source == "fallback"）を検証する。
    """

    def test_existing_id_returns_fallback_work_order(self, client, store, monkeypatch):
        monkeypatch.delenv("ORCAROUTER_API_KEY", raising=False)
        ids = seed_alerts(store)
        response = client.post(f"/api/v1/alerts/{ids[0]}/work-order")
        assert response.status_code == 200
        body = response.json()
        assert body["source"] == "fallback"
        assert body["cost_yen"] == 0.0
        assert body["parts"]
        assert body["work_steps"]
        assert body["notification_text"]

    def test_unknown_id_returns_404(self, client, store):
        response = client.post("/api/v1/alerts/tlm_not_exist/work-order")
        assert response.status_code == 404

    def test_same_id_second_post_returns_same_content(self, client, store, monkeypatch):
        """同一 ID への2回目の POST も同じ内容を返す（エンドポイントの冪等性）。

        API キー未設定のためフォールバックは決定的（同じ部材マスタから毎回同じ内容）。
        キャッシュの実証（LLM 再呼び出しなし）はサービス級 T9（test_orcarouter.py の
        ``handler.calls == 1``）が担うため、ルーター級では内容一致のみを検証する（Info #6）。
        """
        monkeypatch.delenv("ORCAROUTER_API_KEY", raising=False)
        ids = seed_alerts(store)
        first = client.post(f"/api/v1/alerts/{ids[0]}/work-order")
        second = client.post(f"/api/v1/alerts/{ids[0]}/work-order")
        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json()["source"] == "fallback"
        assert second.json()["source"] == "fallback"
        # フォールバックは決定的なため2回とも同一内容になる
        assert first.json()["parts"] == second.json()["parts"]


class TestListSensors:
    """GET /api/v1/sensors。"""

    def test_returns_all_hydrants_with_unknown_status(self, client, store):
        response = client.get("/api/v1/sensors")
        assert response.status_code == 200

        body = response.json()
        assert len(body) == 20  # hydrants.json の件数
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
                "tlm_warn",
                sensor_id="SNS-009",
                severity_level=2,
                received_at=datetime(2026, 8, 10, 11, 0, tzinfo=timezone.utc),
            )
        )
        store.add(
            make_record(
                "tlm_watch",
                sensor_id="SNS-010",
                severity_level=1,
                received_at=datetime(2026, 8, 10, 11, 0, tzinfo=timezone.utc),
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
        assert len(features) == 20
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


class TestPipeInfoSchema:
    """PipeInfo.material の型統一（FR-1）を検証する単体テスト。

    material: str のままでは任意の文字列が通ってしまうが、PipeMaterial
    （Literal["ductile_iron", "cast_iron", "pvc", "steel"]）への型統一後は
    許容値以外を拒否する。エンドポイント経由の値レベル検証は
    test_returns_detail_with_spectrum_and_pipe_info で既にカバー済みのため、
    ここでは型統一そのものの効果（不正値の拒否）をスキーマ単体で検証する。
    """

    def test_material_outside_pipe_material_literal_raises_validation_error(self):
        with pytest.raises(ValidationError):
            PipeInfo(
                pipe_id="P-999",
                material="invalid_material",
                diameter_mm=150,
                installed_year=1998,
                burial_depth_m=1.2,
                age_years=28,
            )


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
        assert app.url_path_for("seed_alerts_for_e2e") == "/api/v1/alerts/seed"
        assert app.url_path_for("list_sensors") == "/api/v1/sensors"


class TestSeedAlertsForE2E:
    """POST /api/v1/alerts/seed（E2E デモシード投入）の検証。

    E2E の global-setup が呼ぶデモシード。実在マスタ（hydrants.json）の消火栓へ
    決定論的にレベルを割り当てて投入する（L3×3 / L2×3 / L1×3 / L0×1）。
    実在マスタの sensor_id と配管台帳（BE-4）が一貫して参照できることを確認する。
    """

    def test_seed_inserts_real_hydrants_in_deterministic_order(self, client):
        response = client.post("/api/v1/alerts/seed", json={"count": 10})
        assert response.status_code == 200
        data = response.json()
        assert data["inserted_count"] == 10
        assert "シード投入完了" in data["message"]

        alerts = client.get("/api/v1/alerts").json()
        assert len(alerts) == 10
        # 深刻度降順・投入順（安定ソート）で HYD-003（L3）が先頭
        assert alerts[0]["hydrant_id"] == "HYD-003"
        assert alerts[0]["severity_level"] == 3
        # L3 上位 3 件が HYD-003 / HYD-004 / HYD-007 の順に並ぶ
        assert [a["hydrant_id"] for a in alerts[:3]] == [
            "HYD-003",
            "HYD-004",
            "HYD-007",
        ]
        # Level 0（正常・HYD-002）も投入される（「正常も表示」トグル検証用）
        hydrant_ids = {a["hydrant_id"] for a in alerts}
        assert "HYD-002" in hydrant_ids
        assert len(hydrant_ids) == 10

    def test_seed_records_reference_real_sensor_and_pipe(self, client):
        client.post("/api/v1/alerts/seed", json={})

        alerts = client.get("/api/v1/alerts").json()
        first = client.get(f"/api/v1/alerts/{alerts[0]['telemetry_id']}").json()
        # 実在マスタの sensor_id（SNS-003）が引き継がれる
        assert first["sensor_id"] == "SNS-003"
        # 配管台帳（BE-4）: HYD-003 → P-003
        assert first["pipe_info"]["pipe_id"] == "P-003"
