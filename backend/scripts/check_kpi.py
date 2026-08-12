"""BE-8: KPI「推定削減コスト」算定ロジック + サマリAPIの E2E 検証。

ダッシュボードの KPI サマリ（GET /api/v1/kpi/summary）が、アラート実データ
（インメモリストア）と docs/business-model.md §3 の算定式のみで正しく算出される
ことを、実サーバーへリクエストして検証する。

前提: 別ターミナルでサーバーが起動していること。

    backend/venv/Scripts/uvicorn.exe main:app --reload --port 8000

実行:

    backend/venv/Scripts/python.exe scripts/check_kpi.py

check_alerts.py と同じ流儀（PASS/FAIL 逐次表示、終了コード 0/1）。
ストアはプロセス内のインメモリ共有のため、実行前の登録済みアラートが残りうる。
そこで「ベースラインの KPI サマリ → 既知のアラートを追加登録 → 差分を検証」とし、
事前状態に依存せず決定的に検証する。
"""

from __future__ import annotations

import base64
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import requests

BASE_URL = "http://localhost:8000"
TELEMETRY_ENDPOINT = f"{BASE_URL}/api/v1/telemetry"
KPI_ENDPOINT = f"{BASE_URL}/api/v1/kpi/summary"

SAMPLE_RATE_HZ = 8_000
DURATION_SEC = 1.0
TONE_FREQ_HZ = 900.0  # 漏水帯域(500〜1500Hz)内のテスト用トーン
OUT_OF_BAND_FREQ_HZ = 2_500.0
WAVEFORM_AMPLITUDE = 0.2

# 現行BE-3のDSP帯域比に対応する決定的な入力でseverityを作る
SEVERITY_SAMPLES = [
    # (センサーID, 消火栓ID, 目標帯域比, 期待severity, 1件あたり期待回避コスト)
    ("SNS-101", "HYD-001", 0.75, 3, 150_000),
    ("SNS-102", "HYD-002", 0.45, 2, 308_000),
    ("SNS-103", "HYD-003", 0.15, 1, 121_800),
]

class CheckFailure(Exception):
    """検証項目の失敗。"""


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailure(message)


def build_audio_base64(target_band_ratio: float) -> str:
    """目標帯域比の決定的な2音をPCM16LE mono rawとしてBase64で返す。"""
    sample_count = int(SAMPLE_RATE_HZ * DURATION_SEC)
    t = np.arange(sample_count, dtype=np.float64) / SAMPLE_RATE_HZ
    waveform = WAVEFORM_AMPLITUDE * (
        np.sqrt(target_band_ratio) * np.sin(2.0 * np.pi * TONE_FREQ_HZ * t)
        + np.sqrt(1.0 - target_band_ratio)
        * np.sin(2.0 * np.pi * OUT_OF_BAND_FREQ_HZ * t)
    )
    clipped = np.clip(waveform, -1.0, 1.0)
    pcm16 = (clipped * np.iinfo(np.int16).max).astype("<i2")
    return base64.b64encode(pcm16.tobytes()).decode("ascii")


def build_payload(
    sensor_id: str, hydrant_id: str, target_band_ratio: float
) -> dict:
    return {
        "sensor_id": sensor_id,
        "hydrant_id": hydrant_id,
        "recorded_at": datetime.now(UTC).isoformat(),
        "location": {"latitude": 35.7022, "longitude": 139.7448},
        "sample_rate_hz": SAMPLE_RATE_HZ,
        "duration_sec": DURATION_SEC,
        "audio_base64": build_audio_base64(target_band_ratio),
        "battery_pct": 87,
    }


def get_kpi_summary() -> requests.Response:
    return requests.get(KPI_ENDPOINT, timeout=10)


def case_1_kpi_contract() -> None:
    """KPIサマリAPIが200 + 契約どおりのフィールド（7項目）で返る。"""
    response = get_kpi_summary()
    expect(
        response.status_code == 200,
        f"GET /kpi/summary 期待 200 / 実際 {response.status_code}: {response.text}",
    )
    body = response.json()
    expected_fields = {
        "total_sensors",
        "level1_count",
        "level2_count",
        "level3_count",
        "estimated_cost_saved_yen",
        "is_estimate",
        "assumption_doc",
    }
    expect(
        set(body.keys()) == expected_fields,
        f"フィールド集合が契約と不一致: {set(body.keys())}",
    )
    expect(body["is_estimate"] is True, f"is_estimate が True のはず: {body['is_estimate']}")
    expect(
        body["assumption_doc"] == "docs/business-model.md §3",
        f"assumption_doc が不正: {body['assumption_doc']}",
    )


def case_2_deterministic_add() -> None:
    """既知severity(1/2/3)を1件ずつ登録すると、KPI差分が算定式どおり増える。

    - Level 1/2/3 の各件数が +1
    - estimated_cost_saved_yen が +150,000+308,000+121,800 = 579,800 増える
    - total_sensors は変わらない（hydrants.json 実件数=10）
    """
    baseline = get_kpi_summary().json()

    # 3件を登録する前に、それぞれの severity が期待どおり解析されることを確認する
    for (
        sensor_id,
        hydrant_id,
        target_band_ratio,
        expected_sev,
        _cost,
    ) in SEVERITY_SAMPLES:
        response = requests.post(
            TELEMETRY_ENDPOINT,
            json=build_payload(sensor_id, hydrant_id, target_band_ratio),
            timeout=10,
        )
        expect(
            response.status_code == 200,
            f"POST /telemetry 期待 200 / 実際 {response.status_code}: {response.text}",
        )
        body = response.json()
        actual_sev = body["analysis"]["severity_level"]
        expect(
            actual_sev == expected_sev,
            f"{sensor_id}: 期待 severity {expected_sev} / 実際 {actual_sev}",
        )

    after = get_kpi_summary().json()

    for level in (1, 2, 3):
        expect(
            after[f"level{level}_count"] == baseline[f"level{level}_count"] + 1,
            f"Level {level} 件数が +1 になっていない: {baseline} -> {after}",
        )

    expected_delta = sum(cost for _s, _h, _a, _sev, cost in SEVERITY_SAMPLES)
    actual_delta = (
        after["estimated_cost_saved_yen"] - baseline["estimated_cost_saved_yen"]
    )
    expect(
        actual_delta == expected_delta,
        f"コスト増分が誤り: 期待 +{expected_delta} / 実際 +{actual_delta}",
    )
    expect(
        after["total_sensors"] == baseline["total_sensors"] == 10,
        f"total_sensors は 10 のはず: {after['total_sensors']}",
    )


def case_3_est_levels_isolated() -> None:
    """1件あたり期待回避コストが docs/business-model.md §3.3 と一致する。

    サーバー内部の算定ロジック（app/services/kpi.py の expected_cost_saved）を
    scripts 側から直接 import して、定数・式が仕様（§3.3 の単価）と一致することを
    確認する（check_ledger.py と同手法。API 経由の増分検証は case_2 で担保）。
    """
    # backend ルートを sys.path に追加して app を import 可能にする
    BACKEND_ROOT = Path(__file__).resolve().parents[1]
    if str(BACKEND_ROOT) not in sys.path:
        sys.path.insert(0, str(BACKEND_ROOT))

    from app.services.kpi import expected_cost_saved  # 実行時 import（check_ledger.py と同手法）

    # §3.3: Level 1 = 121,800 / Level 2 = 308,000 / Level 3 = 150,000 / Level 0 = 0
    expected = {1: 121_800, 2: 308_000, 3: 150_000, 0: 0}
    for level, cost in expected.items():
        expect(
            expected_cost_saved(level) == cost,
            f"expected_cost_saved({level}) は {cost} のはず: {expected_cost_saved(level)}",
        )


CASES = [
    ("KPI: GET /kpi/summary が 200 + 契約7フィールド", case_1_kpi_contract),
    (
        "算定: severity1/2/3 を1件ずつ登録 → 差分が公式どおり",
        case_2_deterministic_add,
    ),
    (
        "定数: 単体コストが §3.3 と一致（121,800 / 308,000 / 150,000 / 0）",
        case_3_est_levels_isolated,
    ),
]


def main() -> int:
    try:
        requests.get(BASE_URL, timeout=5).raise_for_status()
    except requests.RequestException as exc:
        print(
            f"[FATAL] サーバーへ接続できません ({BASE_URL}): {exc}", file=sys.stderr
        )
        print(
            "        backend/venv/Scripts/uvicorn.exe main:app --reload --port 8000",
            file=sys.stderr,
        )
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
