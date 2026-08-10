/**
 * FE-2: 漏水深刻度の共通ユーティリティ。
 *
 * UI-1 ワイヤーフレーム（docs/ui-wireframe.md）で確定した深刻度カラー定義を
 * 単一ソースとして管理する。Leaflet マーカー（FE-3）やアラート一覧（FE-5）でも
 * 本モジュールの getSeverityColor / 各関数を再利用する。
 *
 * 注意: Tailwind v4 の JIT は動的クラス連結（例: `bg-${color}`）を検出できないため、
 * クラス名は必ずリテラル文字列で保持すること。
 */

/** 深刻度レベル。0 は正常（異常なし）。API 型の SeverityLevel(1|2|3) とは別に、
 *  ダッシュボード表示用として正常状態を含むレベルを定義する。 */
export type SeverityLevel = 0 | 1 | 2 | 3;

/** 深刻度の表示メタ情報。 */
export interface SeverityMeta {
  level: SeverityLevel;
  /** UI に表示するラベル。 */
  label: string;
  /** カラーコード（UI-1 深刻度カラー。Leaflet マーカー等で共通利用）。 */
  color: string;
  /** バッジ（背景 + 文字色）の Tailwind クラス。 */
  badgeClass: string;
  /** KPI カード等のアクセント（枠線 + 文字色）クラス。 */
  accentClass: string;
}

export const SEVERITY_META: Record<SeverityLevel, SeverityMeta> = {
  0: {
    level: 0,
    label: "正常",
    color: "#64748b",
    badgeClass: "bg-slate-500/15 text-slate-700",
    accentClass: "border-slate-200 text-slate-700",
  },
  1: {
    level: 1,
    label: "Level 1 微小漏水",
    color: "#22c55e",
    badgeClass: "bg-green-500/15 text-green-700",
    accentClass: "border-green-200 text-green-700",
  },
  2: {
    level: 2,
    label: "Level 2 進行性漏水",
    color: "#f59e0b",
    badgeClass: "bg-amber-500/15 text-amber-700",
    accentClass: "border-amber-200 text-amber-700",
  },
  3: {
    level: 3,
    label: "Level 3 管路破裂",
    color: "#ef4444",
    badgeClass: "bg-red-500/15 text-red-700",
    accentClass: "border-red-200 text-red-700",
  },
};

/** レベルのメタ情報を返す純粋関数。 */
export function getSeverityMeta(level: SeverityLevel): SeverityMeta {
  return SEVERITY_META[level];
}

/** ラベルを返す純粋関数。 */
export function getSeverityLabel(level: SeverityLevel): string {
  return SEVERITY_META[level].label;
}

/** カラーコードを返す純粋関数。 */
export function getSeverityColor(level: SeverityLevel): string {
  return SEVERITY_META[level].color;
}

/** バッジの CSS クラスを返す純粋関数。 */
export function getSeverityBadgeClass(level: SeverityLevel): string {
  return SEVERITY_META[level].badgeClass;
}

/** KPI カード等のアクセント CSS クラスを返す純粋関数。 */
export function getSeverityAccentClass(level: SeverityLevel): string {
  return SEVERITY_META[level].accentClass;
}
