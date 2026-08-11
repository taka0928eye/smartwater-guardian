"""KPI「推定削減コスト」の算定サービス（BE-8）。

``docs/business-model.md`` §3 の算定式のみを根拠に、アラート実データ（インメモリストア）
から期待回避コストを算出する。算定定数はこのモジュールの1箇所に定義し、フロントは
算出済みの値を受け取る（§3.5: 定数の二重管理を避ける）。
"""

from __future__ import annotations

from app.schemas.kpi import KpiSummary
from app.schemas.telemetry import SeverityLevel
from app.store import get_hydrants, get_store

# --- 算定定数（docs/business-model.md §3.2。この1箇所に定義） ---

# 管路破裂1件あたりの総対応費（緊急出動＋道路復旧＋断水対応＋漏水損失）
C_BURST = 1_200_000
# Level 1 の計画補修費
C_REPAIR_LEVEL1 = 185_000
# Level 2 の早期補修費
C_REPAIR_LEVEL2 = 320_000
# Level 1 を放置した場合に一定期間内に破裂へ進展する確率
P_LEVEL1 = 0.12
# 同 Level 2
P_LEVEL2 = 0.35
# Level 3 の位置即時特定による復旧時間短縮効果
C_RESPONSE_SAVED = 150_000

# レスポンスの assumption_doc に設定する算定根拠ドキュメント参照
KPI_ASSUMPTION_DOC = "docs/business-model.md §3"


def expected_cost_saved(severity_level: SeverityLevel) -> int:
    """深刻度別の1件あたり期待回避コスト（E_avoided）を返す（§3.1）。

    - Level 0: 0（正常。回避コストは発生しない）
    - Level 1: p1 × (C_burst − C_repair1)
    - Level 2: p2 × (C_burst − C_repair2)
    - Level 3: C_response_saved（固定）

    浮動小数点の丸め誤差を吸収するため ``round()`` で整数化して返す。
    許容値は ``SeverityLevel``（Literal[0,1,2,3]）のみ。
    """
    if severity_level == 0:
        return 0
    if severity_level == 1:
        return round(P_LEVEL1 * (C_BURST - C_REPAIR_LEVEL1))
    if severity_level == 2:
        return round(P_LEVEL2 * (C_BURST - C_REPAIR_LEVEL2))
    if severity_level == 3:
        return C_RESPONSE_SAVED
    raise ValueError(f"未対応の深刻度です: {severity_level}")


def calculate_kpi_summary() -> KpiSummary:
    """ストアのアラート実データから KPI サマリを組み立てる。

    ``get_store()`` はハンドラ実行時に呼ぶ（import 時捕捉はテスト隔離を壊す）。
    Level 0（正常）は集計対象外。``total_sensors`` は hydrants.json の実件数を
    ``get_hydrants()``（``@lru_cache`` 済みローダー）から取得する。固定値を返さず、
    常に試算値である旨（``is_estimate=True``）と算定根拠（``assumption_doc``）を付与する。
    """
    level1_count = 0
    level2_count = 0
    level3_count = 0
    estimated_cost_saved_yen = 0
    for record in get_store().list_alerts():
        level = record.analysis.severity_level
        if level == 1:
            level1_count += 1
        elif level == 2:
            level2_count += 1
        elif level == 3:
            level3_count += 1
        estimated_cost_saved_yen += expected_cost_saved(level)
    return KpiSummary(
        total_sensors=len(get_hydrants()),
        level1_count=level1_count,
        level2_count=level2_count,
        level3_count=level3_count,
        estimated_cost_saved_yen=estimated_cost_saved_yen,
        is_estimate=True,
        assumption_doc=KPI_ASSUMPTION_DOC,
    )
