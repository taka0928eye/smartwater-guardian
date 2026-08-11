"""BE-1 + BE-6 検証スクリプト: POST /api/v1/telemetry の正常系・異常系を確認する。

BE-6 でモック解析が入ったため、正常系の ``analysis`` は null ではなく解析結果が返る。

前提: 別ターミナルでサーバーが起動していること。

    backend/venv/Scripts/uvicorn.exe main:app --reload --port 8000

実行:

    backend/venv/Scripts/python.exe scripts/check_telemetry.py

httpx は未導入のため、導入済みの requests を使う。
"""

from __future__ import annotations

import base64
import io
import sys
import wave
from datetime import UTC, datetime

import numpy as np
import requests

BASE_URL = "http://localhost:8000"
ENDPOINT = f"{BASE_URL}/api/v1/telemetry"

SAMPLE_RATE_HZ = 16_000
DURATION_SEC = 2.0
TONE_FREQ_HZ = 900.0  # 漏水帯域(500〜1500Hz)内のテスト用トーン


def build_sample_audio_base64() -> str:
    """900Hz の正弦波を PCM16 モノラル WAV にして Base64 で返す。"""
    sample_count = int(SAMPLE_RATE_HZ * DURATION_SEC)
    t = np.arange(sample_count, dtype=np.float64) / SAMPLE_RATE_HZ
    waveform = 0.5 * np.sin(2.0 * np.pi * TONE_FREQ_HZ * t)

    # int16 へ変換する前にクリッピングしてオーバーフローを防ぐ。
    clipped = np.clip(waveform, -1.0, 1.0)
    pcm16 = (clipped * np.iinfo(np.int16).max).astype(np.int16)

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)  # PCM16 = 2 bytes
        wav.setframerate(SAMPLE_RATE_HZ)
        wav.writeframes(pcm16.tobytes())

    return base64.b64encode(buffer.getvalue()).decode("ascii")


def build_valid_payload() -> dict:
    return {
        "sensor_id": "SNS-001",
        "hydrant_id": "HYD-001",
        "recorded_at": datetime.now(UTC).isoformat(),
        "location": {"latitude": 35.7022, "longitude": 139.7448},
        "sample_rate_hz": SAMPLE_RATE_HZ,
        "duration_sec": DURATION_SEC,
        "audio_base64": build_sample_audio_base64(),
        "battery_pct": 87,
    }


class CheckFailure(Exception):
    """検証項目の失敗。"""


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailure(message)


def post(payload: dict) -> requests.Response:
    return requests.post(ENDPOINT, json=payload, timeout=10)


def case_1_valid_payload() -> None:
    """正常系: 200 が返り、契約どおりのフィールドが揃う。"""
    response = post(build_valid_payload())
    expect(response.status_code == 200, f"期待 200 / 実際 {response.status_code}: {response.text}")

    body = response.json()
    expect(body["status"] == "accepted", f"status が accepted ではない: {body['status']}")
    # BE-6: モック解析により analysis に解析結果が入る（BE-1 の null ではない）
    expect(body["analysis"] is not None, f"BE-6 では analysis に解析結果が入るはず: {body['analysis']}")
    expect(body["analysis"]["severity_level"] in (1, 2, 3), f"severity_level が 1〜3 ではない: {body['analysis']['severity_level']}")
    expect(len(body["analysis"]["spectrum"]) == 128, f"spectrum が 128 点ではない: {len(body['analysis']['spectrum'])}")
    expect(body["sensor_id"] == "SNS-001", f"sensor_id がエコーされていない: {body['sensor_id']}")
    expect(bool(body["telemetry_id"]), "telemetry_id が空")
    expect(bool(body["received_at"]), "received_at が空")


def case_2_type_mismatch() -> None:
    """異常系: strict=True により文字列の sample_rate_hz は 422。"""
    payload = build_valid_payload()
    payload["sample_rate_hz"] = "48000"
    response = post(payload)
    expect(response.status_code == 422, f"期待 422 / 実際 {response.status_code}: {response.text}")


def case_3_invalid_base64() -> None:
    """異常系: field_validator により不正な Base64 は 422。"""
    payload = build_valid_payload()
    payload["audio_base64"] = "これはBase64ではありません!!!"
    response = post(payload)
    expect(response.status_code == 422, f"期待 422 / 実際 {response.status_code}: {response.text}")


def case_4_latitude_out_of_range() -> None:
    """異常系: 緯度の範囲外は 422。"""
    payload = build_valid_payload()
    payload["location"]["latitude"] = 200.0
    response = post(payload)
    expect(response.status_code == 422, f"期待 422 / 実際 {response.status_code}: {response.text}")


def case_5_extra_field() -> None:
    """異常系: extra="forbid" により未定義フィールドは 422。"""
    payload = build_valid_payload()
    payload["unknown_field"] = "should be rejected"
    response = post(payload)
    expect(response.status_code == 422, f"期待 422 / 実際 {response.status_code}: {response.text}")


def case_6_naive_datetime() -> None:
    """異常系: AwareDatetime によりタイムゾーン無しの録音時刻は 422。"""
    payload = build_valid_payload()
    payload["recorded_at"] = "2026-08-10T06:00:00"
    response = post(payload)
    expect(response.status_code == 422, f"期待 422 / 実際 {response.status_code}: {response.text}")


CASES = [
    ("正常系: 妥当なペイロードで 200 / analysis=mock結果", case_1_valid_payload),
    ("異常系: sample_rate_hz が文字列 → 422", case_2_type_mismatch),
    ("異常系: audio_base64 が不正 → 422", case_3_invalid_base64),
    ("異常系: latitude が範囲外 → 422", case_4_latitude_out_of_range),
    ("異常系: 未定義フィールド → 422", case_5_extra_field),
    ("異常系: recorded_at にTZが無い → 422", case_6_naive_datetime),
]


def main() -> int:
    try:
        requests.get(BASE_URL, timeout=5).raise_for_status()
    except requests.RequestException as exc:
        print(f"[FATAL] サーバーへ接続できません ({BASE_URL}): {exc}", file=sys.stderr)
        print("        backend/venv/Scripts/uvicorn.exe main:app --reload --port 8000", file=sys.stderr)
        return 2

    failures = 0
    for index, (name, case) in enumerate(CASES, start=1):
        try:
            case()
        except CheckFailure as exc:
            failures += 1
            print(f"[FAIL] {index}. {name}\n       {exc}")
        except requests.RequestException as exc:
            failures += 1
            print(f"[FAIL] {index}. {name}\n       リクエスト失敗: {exc}")
        else:
            print(f"[PASS] {index}. {name}")

    print(f"\n結果: {len(CASES) - failures}/{len(CASES)} PASS")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
