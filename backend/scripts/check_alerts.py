"""BE-6 検証スクリプト: アラート・センサー参照APIの E2E 検証。

前提: 別ターミナルでサーバーが起動していること。

    backend/venv/Scripts/uvicorn.exe main:app --reload --port 8000

実行:

    backend/venv/Scripts/python.exe scripts/check_alerts.py

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
TELEMETRY_ENDPOINT = f"{BASE_URL}/api/v1/telemetry"
ALERTS_ENDPOINT = f"{BASE_URL}/api/v1/alerts"
SENSORS_ENDPOINT = f"{BASE_URL}/api/v1/sensors"

SAMPLE_RATE_HZ = 16_000
DURATION_SEC = 1.0
TONE_FREQ_HZ = 900.0  # 漏水帯域(500〜1500Hz)内のテスト用トーン

# モック解析の仮閾値に依存する振幅（check_telemetry.py と同手法）
SEVERITY_SAMPLES = [
    ("SNS-001", "HYD-001", 0.8, 3),   # 大振幅 → severity 3
    ("SNS-002", "HYD-002", 0.15, 2),  # 中振幅 → severity 2
    ("SNS-003", "HYD-003", 0.05, 1),  # 小振幅 → severity 1
]


def build_audio_base64(amplitude: float) -> str:
    """指定振幅の 900Hz 正弦波を PCM16 モノラル WAV にして Base64 で返す。"""
    sample_count = int(SAMPLE_RATE_HZ * DURATION_SEC)
    t = np.arange(sample_count, dtype=np.float64) / SAMPLE_RATE_HZ
    waveform = amplitude * np.sin(2.0 * np.pi * TONE_FREQ_HZ * t)

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


def build_payload(sensor_id: str, hydrant_id: str, amplitude: float) -> dict:
    return {
        "sensor_id": sensor_id,
        "hydrant_id": hydrant_id,
        "recorded_at": datetime.now(UTC).isoformat(),
        "location": {"latitude": 35.7022, "longitude": 139.7448},
        "sample_rate_hz": SAMPLE_RATE_HZ,
        "duration_sec": DURATION_SEC,
        "audio_base64": build_audio_base64(amplitude),
        "battery_pct": 87,
    }


class CheckFailure(Exception):
    """検証項目の失敗。"""


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailure(message)


# 登録で返る telemetry_id を case 間で共有する
POSTED_IDS: list[str] = []


def case_1_register_alerts() -> None:
    """BE-2 連携予行: 3種の振幅で severity 1〜3 のアラートを登録できる。"""
    for sensor_id, hydrant_id, amplitude, expected in SEVERITY_SAMPLES:
        response = requests.post(
            TELEMETRY_ENDPOINT,
            json=build_payload(sensor_id, hydrant_id, amplitude),
            timeout=10,
        )
        expect(
            response.status_code == 200,
            f"POST /telemetry 期待 200 / 実際 {response.status_code}: {response.text}",
        )
        body = response.json()
        expect(body["analysis"] is not None, f"analysis が null ではいけない: {body['analysis']}")
        actual = body["analysis"]["severity_level"]
        expect(
            actual == expected,
            f"{sensor_id}: 期待 severity {expected} / 実際 {actual}（振幅の仮閾値と不一致）",
        )
        POSTED_IDS.append(body["telemetry_id"])


def case_2_list_sorted() -> None:
    """GET /alerts が深刻度降順（3,2,1）・契約フィールドで返る。"""
    response = requests.get(ALERTS_ENDPOINT, timeout=10)
    expect(
        response.status_code == 200,
        f"GET /alerts 期待 200 / 実際 {response.status_code}: {response.text}",
    )
    body = response.json()
    expect(len(body) >= len(SEVERITY_SAMPLES), f"登録分のアラートがあるはず: {len(body)}")
    severities = [item["severity_level"] for item in body[: len(SEVERITY_SAMPLES)]]
    expect(severities == sorted(severities, reverse=True), f"深刻度降順ではない: {severities}")

    first = body[0]
    for key in (
        "telemetry_id",
        "sensor_id",
        "hydrant_id",
        "severity_level",
        "leak_confidence",
        "detected_at",
    ):
        expect(key in first, f"AlertSummary に {key} が無い: {list(first.keys())}")


def case_3_filter_by_level() -> None:
    """?level=3 で Level 3 のみに絞り込める。"""
    response = requests.get(ALERTS_ENDPOINT, params={"level": 3}, timeout=10)
    expect(
        response.status_code == 200,
        f"?level=3 期待 200 / 実際 {response.status_code}: {response.text}",
    )
    body = response.json()
    expect(body, "Level 3 のアラートが1件以上あるはず")
    expect(all(item["severity_level"] == 3 for item in body), "Level 3 以外が混ざっている")


def case_4_limit() -> None:
    """?limit=2 で最大2件に絞り込める。"""
    response = requests.get(ALERTS_ENDPOINT, params={"limit": 2}, timeout=10)
    expect(
        response.status_code == 200,
        f"?limit=2 期待 200 / 実際 {response.status_code}: {response.text}",
    )
    expect(len(response.json()) == 2, f"limit=2 で2件のはず: {len(response.json())}")


def case_5_detail() -> None:
    """GET /alerts/{id} が詳細（spectrum 128点・pipe_info null）を返す。"""
    response = requests.get(f"{ALERTS_ENDPOINT}/{POSTED_IDS[0]}", timeout=10)
    expect(
        response.status_code == 200,
        f"GET /alerts/{{id}} 期待 200 / 実際 {response.status_code}: {response.text}",
    )
    body = response.json()
    expect(
        len(body["analysis"]["spectrum"]) == 128,
        f"spectrum が 128 点ではない: {len(body['analysis']['spectrum'])}",
    )
    expect(body["pipe_info"] is None, f"pipe_info は BE-4 未実装のため null のはず: {body['pipe_info']}")
    expect("location" in body, "AlertDetail に location が無い")


def case_6_unknown_id_404() -> None:
    """存在しない ID の詳細は 404（500 でない）。"""
    response = requests.get(f"{ALERTS_ENDPOINT}/tlm_not_exist", timeout=10)
    expect(response.status_code == 404, f"不明 ID 期待 404 / 実際 {response.status_code}: {response.text}")


def case_7_sensors() -> None:
    """GET /sensors が消火栓10件 + 契約フィールド + 登録反映を返す。"""
    response = requests.get(SENSORS_ENDPOINT, timeout=10)
    expect(
        response.status_code == 200,
        f"GET /sensors 期待 200 / 実際 {response.status_code}: {response.text}",
    )
    body = response.json()
    expect(len(body) == 10, f"消火栓は10件のはず: {len(body)}")

    first = body[0]
    for key in ("sensor_id", "hydrant_id", "status", "location", "last_reading_at"):
        expect(key in first, f"SensorInfo に {key} が無い: {list(first.keys())}")

    # 登録済み SNS-001 は critical、SNS-003 は normal のはず
    by_id = {item["sensor_id"]: item for item in body}
    expect(
        by_id["SNS-001"]["status"] == "critical",
        f"SNS-001 は critical のはず: {by_id['SNS-001']['status']}",
    )
    expect(
        by_id["SNS-003"]["status"] == "normal",
        f"SNS-003 は normal のはず: {by_id['SNS-003']['status']}",
    )


def case_8_geojson() -> None:
    """?format=geojson が [経度, 緯度] 順の FeatureCollection を返す。"""
    response = requests.get(SENSORS_ENDPOINT, params={"format": "geojson"}, timeout=10)
    expect(
        response.status_code == 200,
        f"?format=geojson 期待 200 / 実際 {response.status_code}: {response.text}",
    )
    body = response.json()
    expect(body["type"] == "FeatureCollection", f"type が FeatureCollection ではない: {body['type']}")
    expect(len(body["features"]) == 10, f"features は10件のはず: {len(body['features'])}")

    for feature in body["features"]:
        lon, lat = feature["geometry"]["coordinates"]
        # GeoJSON 標準は [経度, 緯度]。逆にすると東京が海に落ちる
        expect(-180.0 <= lon <= 180.0, f"経度が範囲外: {lon}")
        expect(-90.0 <= lat <= 90.0, f"緯度が範囲外: {lat}")


def case_9_work_order_501() -> None:
    """POST work-order は BE-5 スタブ（実在 ID は 501）。"""
    response = requests.post(f"{ALERTS_ENDPOINT}/{POSTED_IDS[0]}/work-order", timeout=10)
    expect(
        response.status_code == 501,
        f"実在 ID の work-order 期待 501 / 実際 {response.status_code}: {response.text}",
    )


def case_10_work_order_unknown_404() -> None:
    """POST work-order（未存在 ID）は 404。"""
    response = requests.post(f"{ALERTS_ENDPOINT}/tlm_not_exist/work-order", timeout=10)
    expect(
        response.status_code == 404,
        f"不明 ID の work-order 期待 404 / 実際 {response.status_code}: {response.text}",
    )


CASES = [
    ("登録: 3種の振幅で severity 1〜3 のアラート登録（BE-2 連携予行）", case_1_register_alerts),
    ("一覧: GET /alerts が深刻度降順・契約フィールド", case_2_list_sorted),
    ("フィルタ: ?level=3 で Level 3 のみ", case_3_filter_by_level),
    ("フィルタ: ?limit=2 で最大2件", case_4_limit),
    ("詳細: GET /alerts/{id} が spectrum 128点・pipe_info null", case_5_detail),
    ("404: 不明 ID の詳細", case_6_unknown_id_404),
    ("センサー: GET /sensors が10件・契約フィールド", case_7_sensors),
    ("GeoJSON: ?format=geojson が [経度, 緯度] 順", case_8_geojson),
    ("スタブ: 実在 ID の work-order → 501", case_9_work_order_501),
    ("404: 不明 ID の work-order", case_10_work_order_unknown_404),
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
