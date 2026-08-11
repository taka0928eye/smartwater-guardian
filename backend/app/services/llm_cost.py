"""LLM原価計算およびWorkOrder補完サービス."""

import json
import logging
from typing import Any

from app.schemas.work_order import WorkOrder

logger = logging.getLogger(__name__)

# 単価定数（取得日: 2026-08-12, 出典: docs/llm-cost.md §2.2）
# Orcarouterデフォルト単価（1kトークンあたりUSD）
DEFAULT_UNIT_PRICE_INPUT_PER_1K: float = 0.00015   # $0.15 / 1M
DEFAULT_UNIT_PRICE_OUTPUT_PER_1K: float = 0.00060  # $0.60 / 1M
DEFAULT_USD_JPY_RATE: float = 155.0                # 1USD = 155.0 JPY


def calc_cost_yen(
    prompt_tokens: int,
    completion_tokens: int,
    unit_price_input_per_1k: float = DEFAULT_UNIT_PRICE_INPUT_PER_1K,
    unit_price_output_per_1k: float = DEFAULT_UNIT_PRICE_OUTPUT_PER_1K,
    usd_jpy_rate: float = DEFAULT_USD_JPY_RATE,
) -> float:
    """トークン数と単価から日本円原価を算出する."""
    if prompt_tokens == 0 and completion_tokens == 0:
        return 0.0

    input_cost_usd = (prompt_tokens / 1000.0) * unit_price_input_per_1k
    output_cost_usd = (completion_tokens / 1000.0) * unit_price_output_per_1k
    total_usd = input_cost_usd + output_cost_usd

    return round(total_usd * usd_jpy_rate, 5)


def calculate_and_enrich_cost(
    work_order: WorkOrder,
    usage: dict[str, Any] | None,
    model_name: str = "orcarouter",
    latency_ms: int = 0,
    telemetry_id: str | None = None,
) -> WorkOrder:
    """WorkOrderに原価メタデータを補完し構造化ログを出力する."""
    # source == "fallback" の時は LLM 未使用のため 0.0 円固定
    if work_order.source == "fallback":
        work_order.prompt_tokens = 0
        work_order.completion_tokens = 0
        work_order.cost_yen = 0.0
        work_order.model = model_name
        work_order.latency_ms = latency_ms
        work_order.is_estimated = False
        return work_order

    # usage の有無で数値・概算フラグを設定
    if usage and "prompt_tokens" in usage and "completion_tokens" in usage:
        prompt_tokens = int(usage["prompt_tokens"])
        completion_tokens = int(usage["completion_tokens"])
        is_estimated = False
    else:
        # usage 欠損時は想定値（入力800, 出力200）で概算計算
        prompt_tokens = 800
        completion_tokens = 200
        is_estimated = True

    cost_yen = calc_cost_yen(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )

    work_order.prompt_tokens = prompt_tokens
    work_order.completion_tokens = completion_tokens
    work_order.cost_yen = cost_yen
    work_order.model = model_name
    work_order.latency_ms = latency_ms
    work_order.is_estimated = is_estimated

    # 1行 JSON 構造化ログ（機密情報 API キー等は含まない）
    log_payload = {
        "event": "llm_cost_measured",
        "telemetry_id": telemetry_id,
        "model": model_name,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_yen": cost_yen,
        "source": work_order.source,
        "latency_ms": latency_ms,
        "is_estimated": is_estimated,
    }
    logger.info(json.dumps(log_payload, ensure_ascii=False))

    return work_order
