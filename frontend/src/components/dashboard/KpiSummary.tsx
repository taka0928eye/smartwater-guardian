/**
 * FE-7: KPI サマリ（5枚の監視カード・表示専用）。
 *
 * 監視センサー数 / Level 3 破裂リスク / Level 2 警告 / Level 1 微小漏水（AI検知） /
 * 推定削減コスト を降順で表示する。値は BE-8 の GET /api/v1/kpi/summary の実データ
 * （camelCase 変換済み）を受け取って描画する。
 * ランドマーク（section / h2 / aria-labelledby / aria-busy）はラッパー側
 * （DashboardClient）が一元所有するため、本コンポーネントは描画しない（表示専用）。
 * コメント・docstring は日本語（NFR-4 / FE-7）。
 */
import type { ReactNode } from "react";

import { getSeverityMeta } from "@/lib/severity";
import type { KpiSummary } from "../../types/api";

/** KPI サマリの表示層データ型（契約層 KpiSummary の別名。BE-8 契約と 1:1）。 */
export type KpiSummaryData = KpiSummary;

/** 円を万円表記へ変換する（例: 2,048,400 → "204.8万円"）。 */
export function formatManYen(yen: number): string {
  const man = yen / 10000;
  const formatted = man.toLocaleString("ja-JP", {
    maximumFractionDigits: 1,
  });
  return `${formatted}万円`;
}

interface KpiCardProps {
  label: string;
  value: string;
  unit?: string;
  accentClass?: string;
  testId: string;
  /** 値の下に表示する注記（コストカードの試算値 2 段注記など）。 */
  note?: ReactNode;
}

/** KPI カード1枚の表示。 */
function KpiCard({
  label,
  value,
  unit,
  accentClass,
  testId,
  note,
}: KpiCardProps) {
  return (
    <div
      data-testid={testId}
      className={`rounded-xl border bg-white p-4 shadow-sm ${
        accentClass ?? "border-slate-200 text-slate-900"
      }`}
    >
      <p className="text-xs font-medium text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-bold tabular-nums">
        {value}
        {unit ? (
          <span className="ml-1 text-sm font-semibold text-slate-500">
            {unit}
          </span>
        ) : null}
      </p>
      {note}
    </div>
  );
}

/** コストカードの 2 段注記（見出し「試算値」+ 本文「前提: docs/business-model.md」）。
 *  固定リテラルは承認済み表示文言（FE-7 FR-6・application-design:c6）。 */
function EstimateNote() {
  return (
    <div className="mt-2 border-t border-slate-200 pt-2">
      <p className="text-xs font-semibold text-slate-500">試算値</p>
      <p className="mt-0.5 text-xs text-slate-400">前提: docs/business-model.md</p>
    </div>
  );
}

export interface KpiSummaryProps {
  kpiData: KpiSummaryData;
}

/** KPI サマリ（表示専用）。5 カードを降順（sensors → L3 → L2 → L1 → cost）で描画する。 */
export default function KpiSummary({ kpiData }: KpiSummaryProps) {
  const level3Meta = getSeverityMeta(3);
  const level2Meta = getSeverityMeta(2);
  const level1Meta = getSeverityMeta(1);

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
      <KpiCard
        testId="kpi-card-sensors"
        label="監視センサー数"
        value={kpiData.totalSensors.toLocaleString("ja-JP")}
        unit="台"
      />
      <KpiCard
        testId="kpi-card-level3"
        label="Level 3 破裂リスク"
        value={kpiData.level3Count.toLocaleString("ja-JP")}
        unit="件"
        accentClass={level3Meta.accentClass}
      />
      <KpiCard
        testId="kpi-card-level2"
        label="Level 2 警告"
        value={kpiData.level2Count.toLocaleString("ja-JP")}
        unit="件"
        accentClass={level2Meta.accentClass}
      />
      <KpiCard
        testId="kpi-card-level1"
        label="Level 1 微小漏水（AI検知）"
        value={kpiData.level1Count.toLocaleString("ja-JP")}
        unit="件"
        accentClass={level1Meta.accentClass}
      />
      <KpiCard
        testId="kpi-card-cost"
        label="推定削減コスト"
        value={formatManYen(kpiData.estimatedCostSavedYen)}
        note={<EstimateNote />}
      />
    </div>
  );
}
