/**
 * FE-2: 漏水深刻度バッジ。
 *
 * 深刻度レベル（1〜3 / 0=正常）に応じたラベルと背景・文字色を描画する。
 * ラベル・カラーは src/lib/severity.ts の共通定義を参照する。
 * 状態表示のみで副作用がないため Server Component として実装する。
 */
import { getSeverityBadgeClass, getSeverityLabel } from "@/lib/severity";
import type { SeverityLevel } from "@/lib/severity";

export interface SeverityBadgeProps {
  level: SeverityLevel;
}

export default function SeverityBadge({ level }: SeverityBadgeProps) {
  return (
    <span
      data-testid="severity-badge"
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${getSeverityBadgeClass(level)}`}
    >
      {getSeverityLabel(level)}
    </span>
  );
}
