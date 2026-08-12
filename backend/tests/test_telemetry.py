"""BE-1: POST /api/v1/telemetry + BE-3: production解析のテスト。

pytest + FastAPI TestClient を使用し、サーバー起動なしで検証する。
Issue #2（BE-1）の受け入れ条件と、BE-3のMVP音声入力契約を検証する。

実行方法（backend ディレクトリで）:

    venv/Scripts/python.exe -m pytest tests/ -v
"""

from __future__ import annotations

import base64
from datetime import datetime, timezone

import numpy as np
import pytest

SAMPLE_RATE_HZ = 8_000
DURATION_SEC = 1.0


def build_tone_base64(
    freq_hz: float = 900.0,
    amplitude: float = 0.8,
    sample_rate_hz: int = SAMPLE_RATE_HZ,
    duration_sec: float = 1.0,
) -> str:
    """指定周波数のPCM16LE mono raw bytesをBase64で返す。

    漏水帯域（500〜1500Hz）内のトーンを合成する（check_telemetry.py と同手法）。
    """
    sample_count = int(sample_rate_hz * duration_sec)
    t = np.arange(sample_count, dtype=np.float64) / sample_rate_hz
    waveform = amplitude * np.sin(2.0 * np.pi * freq_hz * t)
    clipped = np.clip(waveform, -1.0, 1.0)
    pcm16 = (clipped * np.iinfo(np.int16).max).astype(np.int16)

    return base64.b64encode(pcm16.astype("<i2").tobytes()).decode("ascii")


VALID_AUDIO_B64 = build_tone_base64()


def valid_payload() -> dict:
    """全フィールドを揃えた妥当なリクエストボディ。"""
    return {
        "sensor_id": "SNS-001",
        "hydrant_id": "HYD-001",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "location": {"latitude": 35.7022, "longitude": 139.7448},
        "sample_rate_hz": SAMPLE_RATE_HZ,
        "duration_sec": DURATION_SEC,
        "audio_base64": VALID_AUDIO_B64,
        "battery_pct": 87,
    }


class TestRootAndCORS:
    """既存の GET / と CORS 設定が壊れていないことの確認。"""

    def test_get_root_ok(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "SmartWater Guardian API Ready"}

    def test_cors_header_for_frontend_origin(self, client):
        response = client.post(
            "/api/v1/telemetry",
            json=valid_payload(),
            headers={"Origin": "http://localhost:3000"},
        )
        assert response.status_code == 200
        assert (
            response.headers.get("access-control-allow-origin")
            == "http://localhost:3000"
        )


class TestValidPayload:
    """正常系: 契約どおりのフィールドが返る。"""

    def test_returns_200_with_contract_fields(self, client):
        response = client.post("/api/v1/telemetry", json=valid_payload())
        assert response.status_code == 200

        body = response.json()
        assert body["status"] == "accepted"
        # BE-3のproduction pipelineによりanalysisへ解析結果が入る。
        assert body["analysis"] is not None
        assert body["analysis"]["severity_level"] in (0, 1, 2, 3)
        assert len(body["analysis"]["spectrum"]) == 128  # FE-4 描画用の固定点数
        assert body["sensor_id"] == "SNS-001"
        assert body["telemetry_id"].startswith("tlm_")
        assert body["received_at"]

    def test_optional_battery_field_can_be_omitted(self, client):
        payload = valid_payload()
        payload.pop("battery_pct")
        response = client.post("/api/v1/telemetry", json=payload)
        assert response.status_code == 200


class TestInvalidPayload:
    """異常系: すべて 422 (ValidationError)。"""

    def test_type_mismatch_sample_rate(self, client):
        # strict=True により文字列の sample_rate_hz は 422
        payload = valid_payload()
        payload["sample_rate_hz"] = "48000"
        assert client.post("/api/v1/telemetry", json=payload).status_code == 422

    def test_invalid_base64(self, client):
        # field_validator により不正な Base64 は 422
        payload = valid_payload()
        payload["audio_base64"] = "これはBase64ではありません!!!"
        assert client.post("/api/v1/telemetry", json=payload).status_code == 422

    def test_latitude_out_of_range(self, client):
        payload = valid_payload()
        payload["location"]["latitude"] = 200.0
        assert client.post("/api/v1/telemetry", json=payload).status_code == 422

    def test_empty_audio_returns_422_not_500(self, client):
        # 空データは Base64 としては妥当だが解析不能。境界で 422 に変換されるべき（500 ではない）
        payload = valid_payload()
        payload["audio_base64"] = base64.b64encode(b"").decode("ascii")
        response = client.post("/api/v1/telemetry", json=payload)
        assert response.status_code == 422

    def test_odd_byte_length_audio_returns_422_not_500(self, client):
        # PCM16 は2バイト/サンプル。奇数バイト長は np.frombuffer が例外を送出するが、
        # 境界で 422 に変換されるべき（500 ではない）
        payload = valid_payload()
        payload["audio_base64"] = base64.b64encode(b"\x00" * 3).decode("ascii")
        response = client.post("/api/v1/telemetry", json=payload)
        assert response.status_code == 422

    def test_longitude_out_of_range(self, client):
        payload = valid_payload()
        payload["location"]["longitude"] = -181.0
        assert client.post("/api/v1/telemetry", json=payload).status_code == 422

    def test_extra_field_rejected(self, client):
        # extra="forbid" により未定義フィールドは 422
        payload = valid_payload()
        payload["unknown_field"] = "should be rejected"
        assert client.post("/api/v1/telemetry", json=payload).status_code == 422

    def test_naive_datetime_rejected(self, client):
        # AwareDatetime によりタイムゾーン無しの録音時刻は 422
        payload = valid_payload()
        payload["recorded_at"] = "2026-08-10T06:00:00"
        assert client.post("/api/v1/telemetry", json=payload).status_code == 422

    def test_sample_rate_zero_rejected(self, client):
        # gt=0
        payload = valid_payload()
        payload["sample_rate_hz"] = 0
        assert client.post("/api/v1/telemetry", json=payload).status_code == 422

    def test_duration_sec_too_long_rejected(self, client):
        # le=60
        payload = valid_payload()
        payload["duration_sec"] = 61.0
        assert client.post("/api/v1/telemetry", json=payload).status_code == 422


class TestTelemetrySchemaUnit:
    """Pydantic スキーマ単体の境界値確認。"""

    def test_strict_input_config_applied(self):
        from app.schemas.telemetry import TelemetryRequest

        assert TelemetryRequest.model_config.get("extra") == "forbid"
        assert TelemetryRequest.model_config.get("strict") is True

    def test_geo_location_boundaries(self):
        from pydantic import ValidationError

        from app.schemas.telemetry import GeoLocation

        # 境界値は許容される
        GeoLocation(latitude=90.0, longitude=180.0)
        GeoLocation(latitude=-90.0, longitude=-180.0)
        # 範囲外は ValidationError
        with pytest.raises(ValidationError):
            GeoLocation(latitude=90.0001, longitude=0.0)
        with pytest.raises(ValidationError):
            GeoLocation(latitude=0.0, longitude=180.0001)


class TestRouteRegistration:
    """Issue #2 検証: /api/v1/telemetry がルーター経由で登録されているか。

    従来は ``[r.path for r in app.routes]`` で確認していたが、fastapi 0.141.1 では
    ``include_router`` が ``_IncludedRouter`` として遅延マウントされるため、この
    走査では ``/api/v1/telemetry`` が見えない。名前解決（``url_path_for``）で確認する。
    """

    def test_telemetry_endpoint_resolvable(self):
        from main import app

        assert app.url_path_for("ingest_telemetry") == "/api/v1/telemetry"

    def test_docs_endpoint_available(self, client):
        # /docs にスキーマUIが表示される（Issue #2 の受け入れ条件）
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower()


class TestProductionAnalysis:
    """BE-3 serviceが既存AnalysisResult契約を満たすことを確認する。"""

    def test_tone_returns_complete_analysis(self):
        from app.services.audio import analyze_audio

        result = analyze_audio(
            build_tone_base64(freq_hz=900.0, amplitude=0.8),
            sample_rate_hz=SAMPLE_RATE_HZ,
            duration_sec=DURATION_SEC,
        )
        assert result.severity_level in (0, 1, 2, 3)
        assert result.band_energy_ratio > 0.5
        assert 700 <= result.dominant_freq_hz <= 1100
        assert len(result.spectrum) == 128

    def test_all_zero_audio_is_rejected(self):
        from app.services.audio import AudioValidationError, analyze_audio

        zeros = base64.b64encode(b"\x00" * 16_000).decode("ascii")
        with pytest.raises(AudioValidationError):
            analyze_audio(
                zeros,
                sample_rate_hz=SAMPLE_RATE_HZ,
                duration_sec=DURATION_SEC,
            )
