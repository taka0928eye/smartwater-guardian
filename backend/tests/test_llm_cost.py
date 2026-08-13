"""LLM原価計算および構造化ログの単体テスト."""

import logging

import pytest

from app.schemas.work_order import WorkOrder
from app.services.llm_cost import (
    calc_cost_yen,
    calculate_and_enrich_cost,
)


def test_calc_cost_yen_exact_calculation() -> None:
    """計算式が指定通りに正しく算出されるかのテスト."""
    # prompt: 1000 tokens, completion: 1000 tokens
    # input_per_1k = 0.00015, output_per_1k = 0.00060, rate = 155.0
    # cost = ((1000/1000 * 0.00015) + (1000/1000 * 0.00060)) * 155.0 = 0.11625 円
    cost = calc_cost_yen(
        prompt_tokens=1000,
        completion_tokens=1000,
        unit_price_input_per_1k=0.00015,
        unit_price_output_per_1k=0.00060,
        usd_jpy_rate=155.0,
    )
    assert pytest.approx(cost, 0.0001) == 0.11625


def test_calc_cost_yen_zero_tokens() -> None:
    """トークン数0でZeroDivisionError等にならず0.0が返るかのテスト."""
    cost = calc_cost_yen(0, 0)
    assert cost == 0.0


def test_fallback_cost_is_zero() -> None:
    """source == 'fallback' の時は cost_yen == 0.0 かつ prompt_tokens == 0 となるかのテスト."""
    base_order = WorkOrder(
        parts=[],
        total_estimate_yen=0,
        work_steps=["手動確認"],
        required_workers=1,
        estimated_duration_hours=1.0,
        urgency="low",
        notification_text="フォールバック文面",
        source="fallback",
    )

    enriched = calculate_and_enrich_cost(
        work_order=base_order,
        usage=None,
        model_name="orcarouter",
        latency_ms=100,
    )

    assert enriched.cost_yen == 0.0
    assert enriched.prompt_tokens == 0
    assert enriched.completion_tokens == 0
    assert enriched.is_estimated is False


def test_usage_missing_sets_is_estimated_true() -> None:
    """usage が無い場合に事前指定単価で計算し is_estimated == True が立つかのテスト."""
    base_order = WorkOrder(
        parts=[],
        total_estimate_yen=10000,
        work_steps=["確認"],
        required_workers=1,
        estimated_duration_hours=1.0,
        urgency="low",
        notification_text="テスト",
        source="llm",
    )

    enriched = calculate_and_enrich_cost(
        work_order=base_order,
        usage=None,  # usage 欠損
        model_name="orcarouter",
        latency_ms=500,
    )

    assert enriched.is_estimated is True
    assert enriched.model == "orcarouter"


def test_usage_present_sets_is_estimated_false() -> None:
    """usage がある場合に is_estimated == False かつ実モデル名が入るかのテスト."""
    base_order = WorkOrder(
        parts=[],
        total_estimate_yen=10000,
        work_steps=["確認"],
        required_workers=1,
        estimated_duration_hours=1.0,
        urgency="low",
        notification_text="テスト",
        source="llm",
    )

    usage_data = {"prompt_tokens": 800, "completion_tokens": 200}

    enriched = calculate_and_enrich_cost(
        work_order=base_order,
        usage=usage_data,
        model_name="gpt-4o-mini",
        latency_ms=800,
    )

    assert enriched.is_estimated is False
    assert enriched.model == "gpt-4o-mini"
    assert enriched.prompt_tokens == 800
    assert enriched.completion_tokens == 200
    assert enriched.cost_yen > 0.0


def test_structured_log_output_no_api_key(caplog: pytest.LogCaptureFixture) -> None:
    """構造化ログが出力され、APIキーなどの機密情報が含まれないかのテスト."""
    caplog.set_level(logging.INFO)

    base_order = WorkOrder(
        parts=[],
        total_estimate_yen=5000,
        work_steps=["検査"],
        required_workers=1,
        estimated_duration_hours=0.5,
        urgency="low",
        notification_text="ログテスト",
        source="llm",
    )

    calculate_and_enrich_cost(
        work_order=base_order,
        usage={"prompt_tokens": 100, "completion_tokens": 50},
        model_name="orcarouter",
        latency_ms=300,
        telemetry_id="TEL-999",
    )

    # ログに含まれるキーの確認
    log_text = caplog.text
    assert "TEL-999" in log_text
    assert "cost_yen" in log_text
    assert "api_key" not in log_text.lower()
    assert "sk-" not in log_text
