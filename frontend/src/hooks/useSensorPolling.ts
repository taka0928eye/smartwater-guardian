"use client";

/**
 * 地図マーカー同期: センサー GeoJSON のポーリングを担うカスタムフック。
 *
 * page.tsx（Server Component）が初回に1度だけ取得する sensorFeatures は、以後
 * リフレッシュされないと漏水判定の色更新がアラート一覧（5秒ポーリング）から遅れる。
 * 本フックは同じ間隔で fetchSensorsGeoJson を再取得し、地図マーカーの色をアラート一覧と
 * 同期させる。
 *
 * 取得失敗時は useAlertPolling と同様に直前の sensorFeatures を据え置く（useKpiPolling の
 * 「失敗時に破棄して再スケルトン」とは異なり、地図はバックエンド停止中も白紙にしない）。
 * useEffect のクリーンアップで必ず clearInterval を呼び、アンマウント後の setState は
 * cancelled フラグで防ぐ。
 */
import { useEffect, useState } from "react";

import { fetchSensorsGeoJson } from "@/lib/api";
import type { SensorFeatureCollection } from "@/types/sensor";

export interface UseSensorPollingResult {
  /** 直近の取得成功値。失敗時は直前の値を維持する。 */
  sensorFeatures: SensorFeatureCollection;
  /** 直近の取得失敗メッセージ。成功時は null。 */
  error: string | null;
}

/** initialData を初期値に、intervalMs 間隔で fetchSensorsGeoJson をポーリングする。 */
export function useSensorPolling(
  initialData: SensorFeatureCollection,
  intervalMs: number,
): UseSensorPollingResult {
  const [sensorFeatures, setSensorFeatures] =
    useState<SensorFeatureCollection>(initialData);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const data = await fetchSensorsGeoJson();
        if (cancelled) return;
        setSensorFeatures(data);
        setError(null);
      } catch {
        if (cancelled) return;
        // 取得失敗でも最終状態は維持し、控えめにエラー表示する（地図を白紙にしない）。
        setError("センサー地図の取得に失敗しました");
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

  return { sensorFeatures, error };
}
