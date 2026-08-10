/**
 * FE-2: KPI サマリ（5枚の監視カード）。
 *
 * 監視センサー数 / Level 3 破裂リスク / Level 2 警告 / 本日の検知数 /
 * 推定削減コスト を表示する。値のフォーマットは UI-1 ワイヤーフレームに準拠し、
 * Level 3・Level 2 カードは深刻度色（赤・黄）で強調する。
 * 表示専用で副作用がないため Server Component として実装する。
 */
import { getSeverityMeta } from "@/lib/severity";

/** KPI サマリに渡す監視指標データ。 */
export interface KpiData {
  /** 監視対象センサーの総数。 */
  totalSensors: number;
  /** Level 3（管路破裂リスク）の件数。 */
  level3Count: number;
  /** Level 2（進行性漏水警告）の件数。 */
  level2Count: number;
  /** 本日の検知数。 */
  todayDetections: number;
  /** 推定削減コスト（円）。 */
  estimatedCostSavedYen: number;
}

/** 円を万円表記へ変換する（例: 1,420,000 → "142万円"）。 */
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
}

/** KPI カード1枚の表示。 */
function KpiCard({
  label,
  value,
  unit,
  accentClass,
  testId,
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
    </div>
  );
}

export interface KpiSummaryProps {
  kpiData: KpiData;
}

export default function KpiSummary({ kpiData }: KpiSummaryProps) {
  const level3Meta = getSeverityMeta(3);
  const level2Meta = getSeverityMeta(2);

  return (
    <section
      aria-label="KPI サマリ"
      className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5"
    >
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
        testId="kpi-card-today"
        label="本日の検知数"
        value={kpiData.todayDetections.toLocaleString("ja-JP")}
        unit="件"
      />
      <KpiCard
        testId="kpi-card-cost"
        label="推定削減コスト"
        value={formatManYen(kpiData.estimatedCostSavedYen)}
      />
    </section>
  );
}
