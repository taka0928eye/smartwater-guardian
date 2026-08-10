"use client";

/**
 * FE-5: ダッシュボード本体（Client Component）。
 *
 * アラート一覧・詳細ドロワー・センサー地図の選択状態を束ねる。
 * - alerts / selectedAlertId を保持し、SensorMap / AlertList / AlertDetailDrawer に配る。
 * - アラートは 5秒間隔の setInterval ポーリングで取得する（新着反映）。
 *   useEffect のクリーンアップで確実に clearInterval する。
 * - ポーリング失敗時は画面を壊さず、最終状態を維持して控えめなエラー表示に留める。
 *
 * page.tsx（Server Component）から sensorFeatures（サーバー側取得済み）を props で受ける。
 */
import { useState } from "react";

import AlertDetailDrawer from "@/components/alert/AlertDetailDrawer";
import AlertList from "@/components/alert/AlertList";
import { useAlertPolling } from "@/hooks/useAlertPolling";
import SensorMap from "@/components/map/SensorMap";
import type { SensorFeatureCollection } from "@/types/sensor";

/** アラートのポーリング間隔（ミリ秒）。 */
export const ALERT_POLL_INTERVAL_MS = 5000;

export interface DashboardClientProps {
  /** サーバー側（page.tsx）で取得済みのセンサー GeoJSON。 */
  sensorFeatures: SensorFeatureCollection;
}

export default function DashboardClient({
  sensorFeatures,
}: DashboardClientProps) {
  // 5秒間隔のポーリングは useAlertPolling が担う（clearInterval クリーンアップ含む）。
  const { alerts, error: pollError } = useAlertPolling(ALERT_POLL_INTERVAL_MS);
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);

  const selectedAlert =
    alerts.find((alert) => alert.telemetryId === selectedAlertId) ?? null;

  /** 地図マーカー（センサー）選択を、そのセンサーのアラート選択へ変換する。 */
  const handleSelectMarker = (sensorId: string) => {
    const alert = alerts.find((item) => item.sensorId === sensorId);
    setSelectedAlertId(alert ? alert.telemetryId : null);
  };

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
      {/* GIS マップ（FE-3: Leaflet センサー地図）。マーカー選択は selectedAlertId と連動 */}
      <section className="rounded-xl bg-white p-4 lg:col-span-2">
        <h2 className="mb-2 text-sm font-semibold text-slate-500">
          センサー地図
        </h2>
        <SensorMap
          data={sensorFeatures}
          selectedAlertId={selectedAlertId}
          onSelectMarker={handleSelectMarker}
        />
      </section>

      {/* アラート一覧 */}
      <section className="rounded-xl bg-white p-4">
        <AlertList
          alerts={alerts}
          selectedAlertId={selectedAlertId}
          onSelect={setSelectedAlertId}
        />
        {pollError ? (
          <p
            data-testid="alerts-error"
            className="mt-2 text-xs text-amber-600"
          >
            {pollError}
          </p>
        ) : null}
      </section>

      {/* 詳細ドロワー（選択中のみ表示）。選択が変わるたびに再マウントして
          loading 状態をリセットする（key による状態リセット） */}
      {selectedAlert ? (
        <AlertDetailDrawer
          key={selectedAlert.telemetryId}
          alert={selectedAlert}
          onClose={() => setSelectedAlertId(null)}
        />
      ) : null}
    </div>
  );
}
