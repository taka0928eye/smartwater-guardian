"use client";

/**
 * BE-7: 防災モード（被災エリアクラスタ）のポーリングを担うカスタムフック。
 *
 * DashboardClient が intervalMs 間隔で fetchDisasterSummary を呼び、成功時のみ
 * disasterSummary を更新する。失敗時は最終状態を据え置き、控えめなエラー表示に
 * 留める（地図・画面を壊さない。useAlertPolling と同じ最終状態据え置き方式）。
 *
 * refresh() は「防災シミュレーション」ボタン押下直後にクラスタを即時反映する
 * ための手動再取得関数（simulate API -> refresh の流れで使う）。
 * ポーリング本体（useEffect 内の load）と refresh は別実装になるが、どちらも
 * 同一の fetch + setState フローであり、アンマウント後の setState は
 * cancelled / cancelledRef で防ぐ（team-practices 規約 / FR-7）。
 */
import { useCallback, useEffect, useRef, useState } from "react";

import { fetchDisasterSummary } from "@/lib/api";
import type { DisasterSummary } from "@/types/disaster";

export interface UseDisasterSummaryResult {
  /** 直近の取得成功値。失敗時は最終状態を据え置き（null のまま）。 */
  disasterSummary: DisasterSummary | null;
  /** 直近の取得失敗メッセージ。成功時は null。 */
  error: string | null;
  /** 即時再取得（シミュレーション後に呼ぶと直ちにクラスタが反映される）。 */
  refresh: () => Promise<void>;
}

/** intervalMs 間隔で fetchDisasterSummary をポーリングする（BE-7）。 */
export function useDisasterSummary(
  intervalMs: number,
): UseDisasterSummaryResult {
  const [disasterSummary, setDisasterSummary] =
    useState<DisasterSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  // アンマウント後の setState を防ぐためのフラグ（refresh からも参照する）。
  const cancelledRef = useRef(false);

  useEffect(() => {
    let cancelled = false;
    cancelledRef.current = false;

    const load = async (): Promise<void> => {
      try {
        const data = await fetchDisasterSummary();
        if (cancelled) return;
        setDisasterSummary(data);
        setError(null);
      } catch {
        if (cancelled) return;
        // 取得失敗でも最終状態は維持し、控えめにエラー表示する。
        setError("被災エリアの取得に失敗しました");
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

  // シミュレーション直後の即時再取得。ポーリング本体と同じ fetch + setState フロー。
  const refresh = useCallback(async (): Promise<void> => {
    if (cancelledRef.current) return;
    try {
      const data = await fetchDisasterSummary();
      if (cancelledRef.current) return;
      setDisasterSummary(data);
      setError(null);
    } catch {
      if (cancelledRef.current) return;
      setError("被災エリアの取得に失敗しました");
    }
  }, []);

  return { disasterSummary, error, refresh };
}
