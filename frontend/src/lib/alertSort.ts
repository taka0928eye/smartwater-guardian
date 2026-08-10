/**
 * FE-5: アラート一覧の並び順・フィルタを担う純粋関数。
 *
 * テスト容易性のため AlertList から切り出した（Step 3 Refactor）。
 * 副作用を持たず、受け取った配列を変更しない（不変）。
 */
import type { AlertSummary } from "@/types/api";

/**
 * 深刻度降順 → 検知時刻降順（新着順）に並べ替えた新配列を返す純粋関数。
 * 同一深刻度内では ISO8601（UTC）の文字列比較で時刻の新しい順にする。
 */
export function sortAlerts(alerts: readonly AlertSummary[]): AlertSummary[] {
  return [...alerts].sort((a, b) => {
    if (a.severityLevel !== b.severityLevel) {
      return b.severityLevel - a.severityLevel;
    }
    return b.detectedAt.localeCompare(a.detectedAt);
  });
}

/**
 * Level 0（正常）を除いた新配列を返す純粋関数。
 * includeLevelZero が true のときは全て返す（「正常も表示」トグル）。
 */
export function filterLevelZero(
  alerts: readonly AlertSummary[],
  includeLevelZero: boolean,
): AlertSummary[] {
  if (includeLevelZero) return [...alerts];
  return alerts.filter((alert) => alert.severityLevel !== 0);
}
