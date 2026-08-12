"""プロンプト生成およびレスポンス解析サービス."""

import json
from typing import Any, cast

from app.schemas.work_order import WorkOrder

# 原価5フィールド（LLMに入力させない除外キー定数）
EXCLUDE_COST_FIELDS = {
    "prompt_tokens",
    "completion_tokens",
    "cost_yen",
    "model",
    "latency_ms",
}

SYSTEM_PROMPT = """あなたは日本の水道事業体の補修設計担当エンジニアです。
音響解析データおよび配管台帳情報に基づき、最適な補修部材の選定、作業手順、概算見積、および通知文言を作成してください。

【重要指示】
1. 本見積および金額は概算であり、正式な見積ではない旨を必ず通知文面および思考に
   反映してください。
2. 出力は以下のJSON Schemaに従った純粋なJSON形式のみで出力してください。
   解説や挨拶などの余計なテキストは一切含めないでください。
"""


def get_clean_work_order_schema() -> dict[str, Any]:
    """WorkOrderモデルから原価5フィールドを除外したJSON Schemaを取得する."""
    schema = WorkOrder.model_json_schema()
    properties = schema.get("properties", {})
    for field in EXCLUDE_COST_FIELDS:
        properties.pop(field, None)
    return schema


def build_system_prompt() -> str:
    """システムプロンプトを構築する."""
    schema = get_clean_work_order_schema()
    return (
        f"{SYSTEM_PROMPT}\n"
        f"【出力JSON Schema】\n"
        f"```json\n{json.dumps(schema, ensure_ascii=False, indent=2)}\n```"
    )


def build_user_prompt(telemetry_data: dict[str, Any], pipe_info: dict[str, Any]) -> str:
    """ユーザープロンプトを構築する（スペクトル128点はコスト削減のため除外）."""
    clean_telemetry = {
        k: v for k, v in telemetry_data.items() if k not in ["spectrum", "raw_audio"]
    }

    user_payload = {
        "telemetry_analysis": clean_telemetry,
        "pipe_inventory": pipe_info,
        "note": "金額は概算であり正式見積ではありません。",
    }

    return (
        f"以下の解析結果と配管情報からワークオーダーを出力してください:\n"
        f"{json.dumps(user_payload, ensure_ascii=False, indent=2)}"
    )


def extract_json_from_response(response_text: str) -> dict[str, Any]:
    """LLMの応答テキストからコードフェンスを除去してJSONを抽出する."""
    text = response_text.strip()

    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and start < end:
        text = text[start : end + 1]

    try:
        res = json.loads(text)
    except Exception as e:
        raise ValueError(f"有効なJSON文字列をパースできませんでした: {e}") from e

    return cast(dict[str, Any], res)
