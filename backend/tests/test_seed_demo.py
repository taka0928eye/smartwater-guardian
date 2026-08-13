"""DEMO-1: デモシードスクリプトとシードAPIのテスト。

Issue #23（DEMO-1）の受け入れ条件を検証する:

- ``build_demo_sequence()`` が Level 0 ベースラインから始まり、内訳が
  Level 1×8 / Level 2×3 / Level 3×1 になる
- 同一 ``seed`` で同一シーケンスが再現され、hydrant_id がマスタに実在する
- Level 1 のステップが Level 3 より先に現れる（山場は Level 1）
- シードAPI（``POST /api/v1/demo/seed``）が意図した深刻度でストアへ投入する
  （実 SVM の合成波形誤分類をデモシード専用に補正）
- ``run_seed`` が ``--seed`` 固定で送信でき、``--dry-run`` は送信しない
"""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime

import numpy as np
import pytest

from scripts.seed_demo import (
    BASELINE_LEVEL,
    DEMO_COMPOSITION,
    build_demo_sequence,
    main,
    parse_args,
    run_seed,
)
from scripts.simulate_sensor import (
    encode_audio,
    generate_signal,
    load_hydrants,
)

SEED_SAMPLE_RATE_HZ = 8_000
SEED_DURATION_SEC = 1.0

# デモ既定値（docs/business-model.md §3.4）: Level 1×8 / Level 2×3 / Level 3×1
EXPECTED_STEP_COUNT = 1 + sum(DEMO_COMPOSITION.values())


def test_sequence_starts_with_level0_baseline() -> None:
    """Level 0（正常）ベースラインが先頭にあり、対比の起点になる。"""
    steps = build_demo_sequence(seed=42)
    assert steps
    assert steps[0].level == BASELINE_LEVEL


def test_sequence_composition_matches_demo_defaults() -> None:
    """内訳が Level 1×8 / Level 2×3 / Level 3×1 になる。"""
    steps = build_demo_sequence(seed=42)
    counts = Counter(step.level for step in steps)
    assert counts[0] == 1  # Level 0 ベースライン
    for level, expected in DEMO_COMPOSITION.items():
        assert counts[level] == expected


def test_same_seed_reproduces_identical_sequence() -> None:
    """同一 seed で2回呼ぶと同一シーケンスが返る（デモの再現性）。"""
    first = build_demo_sequence(seed=42)
    second = build_demo_sequence(seed=42)
    assert first == second


def test_different_seed_produces_different_order() -> None:
    """異なる seed では消火栓の割当順が変わる。"""
    assert build_demo_sequence(seed=42) != build_demo_sequence(seed=43)


def test_hydrant_ids_exist_in_master() -> None:
    """全ステップの hydrant_id が hydrants.json に実在する。"""
    valid_ids = {h["hydrant_id"] for h in load_hydrants()}
    for step in build_demo_sequence(seed=42):
        assert step.hydrant_id in valid_ids


def test_level1_steps_appear_before_level3() -> None:
    """Level 1 のステップが Level 3 より先に現れる（山場は Level 1）。"""
    steps = build_demo_sequence(seed=42)
    last_level1 = max(index for index, step in enumerate(steps) if step.level == 1)
    first_level3 = min(index for index, step in enumerate(steps) if step.level == 3)
    assert last_level1 < first_level3


def test_baseline_hydrant_is_not_reused() -> None:
    """Level 0 ベースラインの消火栓は後続ステップで再利用されない。

    センサー最新状態が上書きされると「Level 0（正常）が画面上に存在し、
    Level 1 との対比が成立する」という受け入れ条件が満たせないため。
    """
    steps = build_demo_sequence(seed=42)
    baseline_id = steps[0].hydrant_id
    assert all(step.hydrant_id != baseline_id for step in steps[1:])


def test_run_seed_posts_all_steps_with_level_field() -> None:
    """run_seed が全ステップを送信し、各 payload に意図レベルが入る。"""
    captured: list[tuple[str, dict, float]] = []

    def fake_post(url: str, payload: dict, timeout: float) -> dict:
        captured.append((url, payload, timeout))
        return {"telemetry_id": f"tlm_{len(captured)}"}

    results = run_seed(
        seed=42,
        url="http://test.local/api/v1/demo/seed",
        post_func=fake_post,
    )
    assert len(results) == EXPECTED_STEP_COUNT
    assert len(captured) == EXPECTED_STEP_COUNT

    levels = [payload["level"] for _, payload, _ in captured]
    assert Counter(levels) == {0: 1, **DEMO_COMPOSITION}
    # 先頭は Level 0 ベースライン
    assert captured[0][1]["level"] == BASELINE_LEVEL


def test_run_seed_dry_run_does_not_post() -> None:
    """--dry-run では送信せず、組み立て結果だけを返す。"""

    def boom(url: str, payload: dict, timeout: float) -> dict:
        raise AssertionError("dry-run では送信してはいけない")

    results = run_seed(seed=42, dry_run=True, post_func=boom)
    assert results
    assert all(result["dry_run"] for result in results)
    assert all(result["level"] in (0, 1, 2, 3) for result in results)


def test_parse_args_requires_seed() -> None:
    """--seed が必須で、デフォルトで dry_run は無効。"""
    args = parse_args(["--seed", "42"])
    assert args.seed == 42
    assert args.dry_run is False


def test_parse_args_dry_run_flag() -> None:
    """--dry-run フラグを解釈する。"""
    args = parse_args(["--seed", "42", "--dry-run"])
    assert args.dry_run is True


def test_main_dry_run_returns_zero(capsys: pytest.CaptureFixture[str]) -> None:
    """CLI の --dry-run は送信せず成功終了する。"""
    rc = main(["--seed", "42", "--dry-run"])
    assert rc == 0
    assert "[DRY-RUN]" in capsys.readouterr().out


# --- シードAPI（POST /api/v1/demo/seed）---


def _build_seed_request(level: int, hydrant_id: str = "HYD-001") -> dict:
    """シードAPIに送る1件分のリクエストボディを組み立てる。"""
    signal = generate_signal(
        level, sample_rate_hz=SEED_SAMPLE_RATE_HZ, duration_sec=SEED_DURATION_SEC, seed=1
    )
    return {
        "level": level,
        "sensor_id": "SNS-001",
        "hydrant_id": hydrant_id,
        "recorded_at": datetime.now(UTC).isoformat(),
        "location": {"latitude": 35.7022, "longitude": 139.7448},
        "sample_rate_hz": SEED_SAMPLE_RATE_HZ,
        "duration_sec": SEED_DURATION_SEC,
        "audio_base64": encode_audio(signal),
        "battery_pct": 87,
    }


@pytest.mark.parametrize("level", [0, 1, 2, 3])
def test_seed_endpoint_stores_intended_severity(client, level: int) -> None:
    """シードAPIが意図した深刻度でストアへ投入する（SVM誤分類を補正）。"""
    response = client.post("/api/v1/demo/seed", json=_build_seed_request(level=level))
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "accepted"
    assert body["analysis"]["severity_level"] == level
    assert len(body["analysis"]["spectrum"]) > 0  # 実スペクトルが算出される


def test_seed_endpoint_appears_in_alerts(client) -> None:
    """投入したレコードがアラート一覧に意図レベルで現れる。"""
    client.post("/api/v1/demo/seed", json=_build_seed_request(level=0))
    alerts = client.get("/api/v1/alerts").json()
    assert any(
        alert["hydrant_id"] == "HYD-001" and alert["severity_level"] == 0
        for alert in alerts
    )


def test_seed_endpoint_rejects_invalid_base64(client) -> None:
    """不正な Base64 は 422（TelemetryRequest の検証を継承）。"""
    payload = _build_seed_request(level=1)
    payload["audio_base64"] = "これはBase64ではありません!!!"
    response = client.post("/api/v1/demo/seed", json=payload)
    assert response.status_code == 422


def test_seed_endpoint_rejects_all_zero_audio(client) -> None:
    """全ゼロ音声は解析不能のため 422（AudioValidationError 経路）。"""
    payload = _build_seed_request(level=1)
    payload["audio_base64"] = encode_audio(np.zeros(SEED_SAMPLE_RATE_HZ, dtype=np.int16))
    response = client.post("/api/v1/demo/seed", json=payload)
    assert response.status_code == 422
