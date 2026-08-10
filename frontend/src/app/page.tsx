/**
 * FE-2: ダッシュボードルート（Server Component）。
 *
 * ヘッダー・KPIサマリ・GISマップ/アラート一覧のプレースホルダ枠を配置する。
 * データ取得（BE-6 アラートAPI）は実装前のため、KPI は UI-1 デモ数値の
 * mock データで描画する（CLAUDE.md §3: Mockデータで代用）。
 * Client Component 化はしない（時刻表示は Header が内部で担う）。
 */
import Header from "@/components/dashboard/Header";
import KpiSummary from "@/components/dashboard/KpiSummary";
import type { KpiData } from "@/components/dashboard/KpiSummary";

/** FE-2 デモ用のモック KPI データ（UI-1 デモシナリオの数値）。 */
const MOCK_KPI_DATA: KpiData = {
  totalSensors: 1240,
  level3Count: 1,
  level2Count: 3,
  todayDetections: 12,
  estimatedCostSavedYen: 1_420_000,
};

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <Header />
      <main className="mx-auto max-w-7xl space-y-4 p-4 lg:p-6">
        <KpiSummary kpiData={MOCK_KPI_DATA} />
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          {/* GIS マップ（FE-3 で Leaflet 実装） */}
          <section className="rounded-xl border-2 border-dashed border-slate-300 bg-white p-4 lg:col-span-2">
            <h2 className="text-sm font-semibold text-slate-500">
              GIS マップ（FE-3 で実装予定）
            </h2>
          </section>
          {/* アラート一覧（FE-5 で実装） */}
          <section className="rounded-xl border-2 border-dashed border-slate-300 bg-white p-4">
            <h2 className="text-sm font-semibold text-slate-500">
              アラート一覧（FE-5 で実装予定）
            </h2>
          </section>
        </div>
      </main>
    </div>
  );
}
