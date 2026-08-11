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
 * setState は cancelled フラグで防ぐ（team-practices 規約 / FR-7）。
 */
import { useEffect, useState } from "react";

import { fetchKpiSummary } from "@/lib/api";
import type { KpiSummary } from "@/types/api";

export interface UseKpiPollingResult {
  /** 直近の取得成功値。失敗時は null（再スケルトン）。 */
  kpiData: KpiSummary | null;
  /** 取得中（初回・失敗後の再取得待ち）かどうか。 */
  isLoading: boolean;
}

/** intervalMs 間隔で fetchKpiSummary をポーリングする（FR-7 / FR-8）。 */
export function useKpiPolling(intervalMs: number): UseKpiPollingResult {
  const [kpiData, setKpiData] = useState<KpiSummary | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const data = await fetchKpiSummary();
        if (cancelled) return;
        setKpiData(data);
        setIsLoading(false);
      } catch (err) {
        if (cancelled) return;
        // 古い値を最新として見せない（FR-8 / T3）: 成功値を破棄して再スケルトン。
        setKpiData(null);
        setIsLoading(true);
        // 詳細は console ログに留める（business-logic-model.md §5 / construction ガードレール）。
        // 画面は白紙にせずスケルトンへフォールバックする（Q10=A）。
        console.error("[useKpiPolling] KPI サマリ取得失敗:", err);
      }
    };

    void load();
    // 前回 in-flight の完了を待たず次回発火する out-of-order は既存 useAlertPolling と
    // 同型の既知制約（デモスコープで許容。将来はリクエスト連番で対策）。
    const id = setInterval(() => {
      void load();
    }, intervalMs);

    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [intervalMs]);

  return { kpiData, isLoading };
}
