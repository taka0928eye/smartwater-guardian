"""KPIサマリAPI（BE-8）。

GET /api/v1/kpi/summary でダッシュボードKPI「推定削減コスト」を返す。
データは ``app.store`` のインメモリストアを参照し、``app.services.kpi`` が
``docs/business-model.md`` §3 の式で算出する（固定値は返さない）。
"""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.kpi import KpiSummary
from app.services.kpi import calculate_kpi_summary

router = APIRouter(prefix="/api/v1", tags=["kpi"])


@router.get(
    "/kpi/summary",
    response_model=KpiSummary,
    summary="KPIサマリ（推定削減コスト）",
)
def get_kpi_summary() -> KpiSummary:
    """推定削減コストとレベル別検知件数を返す。

    同期 ``def`` は FastAPI のスレッドプールで実行される。組み立てはサービスのみで
    完結するため、空ストア・例外時にも HTTPException を上げず 200 を返す（500 にしない）。
    """
    return calculate_kpi_summary()
