"""BE-1: POST /api/v1/telemetry のテスト + BE-6: モック解析のテスト。

pytest + FastAPI TestClient を使用し、サーバー起動なしで検証する。
Issue #2（BE-1）の受け入れ条件に加え、BE-6 で追加したモック解析
（telemetry.py の ``_analyze_audio_mock``）の単体テストも含む。

実行方法（backend ディレクトリで）:

    venv/Scripts/python.exe -m pytest tests/ -v
"""

from __future__ import annotations

import base64
import io
import wave
from datetime import datetime, timezone

import numpy as np
import pytest

# テスト用の妥当な Base64 音声（全ゼロの PCM16）。
# PCM16 の内容そのものの妥当性は BE-3（services/audio.py）のスコープで、
# BE-1 では「Base64 文字列として解読できるか」のみを見る。
VALID_AUDIO_B64 = base64.b64encode(b"\x00" * 256).decode("ascii")

SAMPLE_RATE_HZ = 16_000
DURATION_SEC = 2.0


def build_tone_base64(
    freq_hz: float = 900.0,
    amplitude: float = 0.8,
    sample_rate_hz: int = SAMPLE_RATE_HZ,
    duration_sec: float = 1.0,
) -> str:
    """指定周波数の正弦波を PCM16 モノラル WAV にして Base64 で返す。

    漏水帯域（500〜1500Hz）内のトーンを合成する（check_telemetry.py と同手法）。
    """
    sample_count = int(sample_rate_hz * duration_sec)
    t = np.arange(sample_count, dtype=np.float64) / sample_rate_hz
    waveform = amplitude * np.sin(2.0 * np.pi * freq_hz * t)
    clipped = np.clip(waveform, -1.0, 1.0)
    pcm16 = (clipped * np.iinfo(np.int16).max).astype(np.int16)

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)  # PCM16 = 2 bytes
        wav.setframerate(sample_rate_hz)
        wav.writeframes(pcm16.tobytes())

    return base64.b64encode(buffer.getvalue()).decode("ascii")


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
        # BE-6 ではモック解析により analysis に解析結果が入る（BE-1 の null ではない）
        assert body["analysis"] is not None
        assert body["analysis"]["severity_level"] in (1, 2, 3)
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


class TestMockAnalysis:
    """BE-6: telemetry.py のモック解析（``_analyze_audio_mock``）の単体テスト。

    BE-3（services/audio.py）が本実装を追加するまでの仮実装の検証。
    """

    def test_tone_in_leak_band(self):
        from app.routers.telemetry import _analyze_audio_mock

        result = _analyze_audio_mock(
            build_tone_base64(freq_hz=900.0, amplitude=0.8), SAMPLE_RATE_HZ
        )
        assert result.severity_level in (1, 2, 3)
        assert result.severity_level >= 2  # 漏水帯域の高振幅トーンは高い深刻度
        assert result.band_energy_ratio > 0.5  # 漏水帯域(500-1500Hz)に卓越
        assert 700 <= result.dominant_freq_hz <= 1100  # 900Hz 付近にピーク
        assert len(result.spectrum) == 128  # FE-4 描画用ダウンサンプル数
        assert all(p.freq_hz >= 0.0 for p in result.spectrum)

    def test_mid_amplitude_tone_is_severity_2(self):
        from app.routers.telemetry import _analyze_audio_mock

        # 中程度振幅（rms ≈ 0.106）の漏水帯域トーン → severity 2（要点検）になる
        result = _analyze_audio_mock(
            build_tone_base64(freq_hz=900.0, amplitude=0.15), SAMPLE_RATE_HZ
        )
        assert result.severity_level == 2
        assert result.band_energy_ratio > 0.5

    def test_low_amplitude_tone_is_severity_1(self):
        from app.routers.telemetry import _analyze_audio_mock

        # 帯域内にピークはあるが極小振幅（rms ≈ 0.035 < 0.08）→ severity 1（経過観察）
        result = _analyze_audio_mock(
            build_tone_base64(freq_hz=900.0, amplitude=0.05), SAMPLE_RATE_HZ
        )
        assert result.severity_level == 1
        assert result.band_energy_ratio > 0.5  # ピーク自体は帯域内にある

    def test_all_zero_audio_does_not_crash(self):
        from app.routers.telemetry import _analyze_audio_mock

        # 全ゼロの 256B（128サンプル）でもクラッシュせず、severity 1 を返す
        result = _analyze_audio_mock(VALID_AUDIO_B64, SAMPLE_RATE_HZ)
        assert result.severity_level == 1
        assert result.leak_confidence == 0.0
        assert len(result.spectrum) == 128

    def test_empty_audio_raises_value_error(self):
        from app.routers.telemetry import _analyze_audio_mock

        empty_b64 = base64.b64encode(b"").decode("ascii")
        with pytest.raises(ValueError):
            _analyze_audio_mock(empty_b64, SAMPLE_RATE_HZ)
