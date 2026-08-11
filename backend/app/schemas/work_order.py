"""ワークオーダースキーマ定義."""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class RepairPart(BaseModel):
    """補修部材モデル."""

    name: str = Field(..., description="補修部材名称")
    spec: str = Field(..., description="規格・サイズ")
    quantity: int = Field(..., description="数量")
    unit_price_yen: int = Field(..., description="単価（円）")
    subtotal_yen: int = Field(..., description="小計（円）")


class WorkOrder(BaseModel):
    """ワークオーダーモデル."""

    parts: list[RepairPart] = Field(..., description="推奨補修部材リスト")
    total_estimate_yen: int = Field(..., description="概算見積合計（円）")
    work_steps: list[str] = Field(..., description="作業手順リスト")
    required_workers: int = Field(..., description="推奨人員")
    estimated_duration_hours: float = Field(..., description="想定作業時間（時間）")
    urgency: Literal["low", "medium", "high", "critical"] = Field(..., description="緊急度")
    notification_text: str = Field(..., description="Teams/Email通知用文面")
    source: Literal["llm", "fallback"] = Field("llm", description="生成元")

    # FR-6 原価5フィールド（LLMプロンプトのSchemaからは除外される）
    prompt_tokens: Optional[int] = Field(0, description="プロンプトトークン数")
    completion_tokens: Optional[int] = Field(0, description="生成トークン数")
    cost_yen: Optional[float] = Field(0.0, description="概算コスト（円）")
    model: Optional[str] = Field("orcarouter", description="使用モデル")
    latency_ms: Optional[int] = Field(0, description="レイテンシ（ms）")
