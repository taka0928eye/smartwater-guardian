"use client";

/**
 * FE-5: アラートのポーリングを担うカスタムフック。
 *
 * DashboardClient から抽出した（Step 3 Refactor）。間隔は呼び出し側が指定し、
 * useEffect のクリーンアップで必ず clearInterval を呼ぶ（アンマウント後の
 * setState は cancelled フラグで防ぐ）。
 *
 * ポーリング失敗時は alerts / lastUpdatedAt を据え置き、控えめなエラー表示に
 * 留める（画面を壊さない）。
 */
import { useEffect, useState } from "react";

import { fetchAlerts } from "@/lib/api";
import type { AlertSummary } from "@/types/api";

export interface UseAlertPollingResult {
  /** 取得済みのアラート一覧。 */
  alerts: AlertSummary[];
  /** 直近の取得失敗メッセージ。成功時は null。 */
  error: string | null;
  /** 最終取得成功時刻。失敗時は据え置き（null のまま）。 */
  lastUpdatedAt: Date | null;
}

/** intervalMs 間隔で fetchAlerts をポーリングする。 */
export function useAlertPolling(intervalMs: number): UseAlertPollingResult {
  const [alerts, setAlerts] = useState<AlertSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<Date | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const data = await fetchAlerts();
        if (cancelled) return;
        setAlerts(data);
        setError(null);
        setLastUpdatedAt(new Date());
      } catch {
        if (cancelled) return;
        // 取得失敗でも最終状態は維持し、控えめにエラー表示する。
        setError("アラートの取得に失敗しました");
      }
    };

    void load();
    const id = setInterval(() => {
      void load();
    }, intervalMs);

    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [intervalMs]);

  return { alerts, error, lastUpdatedAt };
}
