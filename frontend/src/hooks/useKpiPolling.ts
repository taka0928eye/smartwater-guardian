"use client";

/**
 * FE-7: KPI サマリのポーリングを担うカスタムフック。
 *
 * DashboardClient が intervalMs 間隔で fetchKpiSummary を呼び、成功時のみ
 * kpiData を更新する。**失敗時は古い値を最新として見せない**ため（FR-8 / Q2=A）、
 * kpiData を null に破棄して isLoading=true（再スケルトン）へ戻す。
 * 既存 useAlertPolling（最終状態据え置き）とは挙動が異なるため、共通フックに
 * 統合せず専用フックとして新設する（application-design:c5）。
 *
 * useEffect のクリーンアップで必ず clearInterval を呼び、アンマウント後の
 * setState は cancelled / cancelledRef フラグで防ぐ（team-practices 規約 / FR-7）。
 *
 * 前回 in-flight の完了を待たず次回発火しうるため、リクエスト連番（requestSeqRef）で
 * アウトオブオーダーを防ぐ。先発リクエストが後発より遅れて解決しても、
 * 「最新の発行リクエストではない」応答は破棄し、新しい値を上書きしない。連番は
 * ポーリング本体（useEffect 内の load）と refresh（デモ操作ボタン押下直後の即時
 * 反映用）の両方で共有し、どちらが最後に発行されたかを正しく判定する。
 */
import { useCallback, useEffect, useRef, useState } from "react";

import { fetchKpiSummary } from "@/lib/api";
import type { KpiSummary } from "@/types/api";

export interface UseKpiPollingResult {
  /** 直近の取得成功値。失敗時は null（再スケルトン）。 */
  kpiData: KpiSummary | null;
  /** 取得中（初回・失敗後の再取得待ち）かどうか。 */
  isLoading: boolean;
  /** 即時再取得（デモ操作ボタン押下直後に呼ぶと直ちに反映される）。 */
  refresh: () => Promise<void>;
}

/** intervalMs 間隔で fetchKpiSummary をポーリングする（FR-7 / FR-8）。 */
export function useKpiPolling(intervalMs: number): UseKpiPollingResult {
  const [kpiData, setKpiData] = useState<KpiSummary | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  // アンマウント後の setState を防ぐためのフラグ（refresh からも参照する）。
  const cancelledRef = useRef(false);
  // ポーリングと refresh の両方が発行するリクエストを連番で管理する（共有）。
  const requestSeqRef = useRef(0);

  useEffect(() => {
    let cancelled = false;
    cancelledRef.current = false;

    const load = async (): Promise<void> => {
      const seq = ++requestSeqRef.current;
      try {
        const data = await fetchKpiSummary();
        if (cancelled || seq !== requestSeqRef.current) return;
        setKpiData(data);
        setIsLoading(false);
      } catch (err) {
        if (cancelled || seq !== requestSeqRef.current) return;
        // 古い値を最新として見せない（FR-8 / T3）: 成功値を破棄して再スケルトン。
        setKpiData(null);
        setIsLoading(true);
        // 詳細は console ログに留める（business-logic-model.md §5 / construction ガードレール）。
        // 画面は白紙にせずスケルトンへフォールバックする（Q10=A）。
        console.error("[useKpiPolling] KPI サマリ取得失敗:", err);
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

  // デモ操作ボタン押下直後の即時再取得。ポーリング本体と同じ連番ガードを共有する。
  const refresh = useCallback(async (): Promise<void> => {
    if (cancelledRef.current) return;
    const seq = ++requestSeqRef.current;
    try {
      const data = await fetchKpiSummary();
      if (cancelledRef.current || seq !== requestSeqRef.current) return;
      setKpiData(data);
      setIsLoading(false);
    } catch (err) {
      if (cancelledRef.current || seq !== requestSeqRef.current) return;
      setKpiData(null);
      setIsLoading(true);
      console.error("[useKpiPolling] KPI サマリ取得失敗:", err);
    }
  }, []);

  return { kpiData, isLoading, refresh };
}
