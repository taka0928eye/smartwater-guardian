"use client";

/**
 * FE-5: アラートのポーリングを担うカスタムフック。
 *
 * DashboardClient から抽出した（Step 3 Refactor）。間隔は呼び出し側が指定し、
 * useEffect のクリーンアップで必ず clearInterval を呼ぶ（アンマウント後の
 * setState は cancelled / cancelledRef で防ぐ）。
 *
 * ポーリング失敗時は alerts / lastUpdatedAt を据え置き、控えめなエラー表示に
 * 留める（画面を壊さない）。
 *
 * refresh() は「シード投入」「シードクリア」「防災シミュレーション」ボタン押下
 * 直後にアラート一覧を即時反映するための手動再取得関数（useDisasterSummary と
 * 同じ方式で使う）。ポーリング本体（useEffect 内の load）と refresh は別実装に
 * なるが、どちらも同一の fetch + setState フローであり、アンマウント後の
 * setState は cancelled / cancelledRef で防ぐ。
 */
import { useCallback, useEffect, useRef, useState } from "react";

import { fetchAlerts } from "@/lib/api";
import type { AlertSummary } from "@/types/api";

export interface UseAlertPollingResult {
  /** 取得済みのアラート一覧。 */
  alerts: AlertSummary[];
  /** 直近の取得失敗メッセージ。成功時は null。 */
  error: string | null;
  /** 最終取得成功時刻。失敗時は据え置き（null のまま）。 */
  lastUpdatedAt: Date | null;
  /** 即時再取得（デモ操作ボタン押下直後に呼ぶと直ちに反映される）。 */
  refresh: () => Promise<void>;
}

/** intervalMs 間隔で fetchAlerts をポーリングする。 */
export function useAlertPolling(intervalMs: number): UseAlertPollingResult {
  const [alerts, setAlerts] = useState<AlertSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<Date | null>(null);
  // アンマウント後の setState を防ぐためのフラグ（refresh からも参照する）。
  const cancelledRef = useRef(false);

  useEffect(() => {
    let cancelled = false;
    cancelledRef.current = false;

    const load = async (): Promise<void> => {
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
      cancelledRef.current = true;
      clearInterval(id);
    };
  }, [intervalMs]);

  // デモ操作ボタン押下直後の即時再取得。ポーリング本体と同じ fetch + setState フロー。
  const refresh = useCallback(async (): Promise<void> => {
    if (cancelledRef.current) return;
    try {
      const data = await fetchAlerts();
      if (cancelledRef.current) return;
      setAlerts(data);
      setError(null);
      setLastUpdatedAt(new Date());
    } catch {
      if (cancelledRef.current) return;
      setError("アラートの取得に失敗しました");
    }
  }, []);

  return { alerts, error, lastUpdatedAt, refresh };
}
