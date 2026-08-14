"use client";

/**
 * FE-5: アラート一覧。
 *
 * 検知されたアラートを深刻度降順 → 検知時刻降順（新着順）で表示する。
 * PRD §2（2026-08-10）に基づき、Level 0（正常）は既定で一覧から除外し、
 * 「正常も表示」トグルで切替える。Level 3 の行は行全体を強調する。
 * 行クリックで onSelect(alertId) を親へ通知する（地図との連動用）。
 */
import { memo, useState } from "react";

import SeverityBadge from "@/components/common/SeverityBadge";
import { filterLevelZero, sortAlerts } from "@/lib/alertSort";
import type { AlertSummary } from "@/types/api";

export interface AlertListProps {
  /** 検知されたアラート（未ソートでもよい。表示時にソートする）。 */
  alerts: AlertSummary[];
  /** 選択中のアラート ID（telemetryId）。一致する行を強調する。 */
  selectedAlertId: string | null;
  /** 行クリック時に呼ばれる。引数は telemetryId。 */
  onSelect: (alertId: string) => void;
}

/** ISO8601 を JST 表記（例: 2026-08-10 09:00）へ変換する。 */
function formatDateTime(iso: string): string {
  try {
    return new Intl.DateTimeFormat("ja-JP", {
      timeZone: "Asia/Tokyo",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    })
      .format(new Date(iso))
      .replace(/\//g, "-");
  } catch {
    return iso;
  }
}

/**
 * 行の CSS クラスを組み立てる（Tailwind v4 は動的連結ができないため
 * クラス名は必ずリテラルで持つ）。
 */
function rowClass(severityLevel: number, selected: boolean): string {
  const base =
    "flex w-full items-center justify-between gap-2 rounded-lg border px-3 py-2 text-left text-sm transition";
  const severity =
    severityLevel === 3
      ? "border-l-4 border-red-500 bg-red-50"
      : "border-slate-200 bg-white";
  const state = selected
    ? "ring-2 ring-indigo-500"
    : "hover:bg-slate-50";
  return `${base} ${severity} ${state}`;
}

/** React.memo: props（alerts / selectedAlertId / onSelect）が不変な再描画
 *  （例: KPI ポーリングによる親の再描画）ではスキップする。 */
function AlertList({ alerts, selectedAlertId, onSelect }: AlertListProps) {
  const [showLevel0, setShowLevel0] = useState(false);

  // 深刻度降順 → 検知時刻降順（新着順）に並べ、Level 0 をトグルに応じて除外する。
  // ソート・フィルタは純粋関数（src/lib/alertSort.ts）に切り出してある。
  const visibleAlerts = filterLevelZero(sortAlerts(alerts), showLevel0);

  return (
    <section aria-label="アラート一覧" className="flex h-full flex-col">
      <div className="mb-2 flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-slate-500">アラート一覧</h2>
        <label className="flex cursor-pointer items-center gap-1.5 text-xs text-slate-500">
          <input
            type="checkbox"
            data-testid="show-level0-toggle"
            checked={showLevel0}
            onChange={(event) => setShowLevel0(event.target.checked)}
            className="h-3.5 w-3.5 cursor-pointer"
          />
          正常も表示
        </label>
      </div>

      {visibleAlerts.length === 0 ? (
        <p
          data-testid="alert-empty"
          className="rounded-lg border border-dashed border-slate-300 p-4 text-center text-sm text-slate-500"
        >
          {alerts.length === 0
            ? "アラートはありません"
            : "表示できるアラートはありません（正常・Level 0 は非表示です）"}
        </p>
      ) : (
        <ul className="space-y-2">
          {visibleAlerts.map((alert) => {
            const selected = selectedAlertId === alert.telemetryId;
            return (
              <li key={alert.telemetryId}>
                <button
                  type="button"
                  data-testid="alert-row"
                  data-alert-id={alert.telemetryId}
                  data-selected={selected ? "true" : "false"}
                  onClick={() => onSelect(alert.telemetryId)}
                  className={rowClass(alert.severityLevel, selected)}
                >
                  <span className="flex items-center gap-2">
                    <SeverityBadge level={alert.severityLevel} />
                    <span className="font-medium text-slate-700">
                      {alert.hydrantId}
                    </span>
                  </span>
                  <span className="flex items-center gap-3">
                    <span className="tabular-nums text-xs text-slate-500">
                      {alert.leakConfidence}点
                    </span>
                    <time
                      dateTime={alert.detectedAt}
                      className="text-xs text-slate-400"
                    >
                      {formatDateTime(alert.detectedAt)}
                    </time>
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

export default memo(AlertList);
