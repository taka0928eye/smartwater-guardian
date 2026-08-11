"""KPIサマリAPIのレスポンススキーマ（Pydantic v2）。

BE-8 用。ダッシュボードKPI「推定削減コスト」をバックエンドで算出して返す
（算出元は ``app/services/kpi.py``）。``estimated_cost_saved_yen`` は
``docs/business-model.md`` §3 の算定式のみを根拠とする**試算値**である旨を、
``is_estimate`` / ``assumption_doc`` で常時明示する（§3.5: 根拠のない金額を
断定的に見せない）。
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.telemetry import STRICT_INPUT_CONFIG


class KpiSummary(BaseModel):
    """KPIサマリ（GET /api/v1/kpi/summary のレスポンス）。

    アラート実データ（インメモリストア）から集計し、固定値を返さない。
    ``today_detections`` は本ユニットの対象外（D-3、FE-7 以降で対応）。
    """

    model_config = STRICT_INPUT_CONFIG

    total_sensors: int = Field(ge=0, description="監視対象センサー総数（hydrants.json 実件数）")
    level1_count: int = Field(ge=0, description="Level 1（微小漏水）の検知アラート件数")
    level2_count: int = Field(ge=0, description="Level 2（進行性漏水）の検知アラート件数")
    level3_count: int = Field(ge=0, description="Level 3（管路破裂）の検知アラート件数")
    estimated_cost_saved_yen: int = Field(ge=0, description="推定削減コスト（円）")
    is_estimate: bool = Field(description="試算値であることを常時明示（True）")
    assumption_doc: str = Field(description="算定根拠ドキュメント（docs/business-model.md §3）")
