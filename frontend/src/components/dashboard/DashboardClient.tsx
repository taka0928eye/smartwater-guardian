"use client";

/**
 * FE-5/FE-7: ダッシュボード本体（Client Component）。
 *
 * - アラート一覧・詳細ドロワー・センサー地図の選択状態を束ねる（FE-5）。
 * - KPI サマリ（BE-8: GET /api/v1/kpi/summary）は同一間隔（5 秒）のポーリングで取得し、
 *   失敗時は再スケルトンへ戻す（FE-7 / FR-8）。KPI section のランドマーク
 *   （section / h2 / aria-labelledby / aria-busy）は本コンポーネントが一元所有し、
 *   スケルトン中も h2 とランドマークを維持する。
 * - アラートは 5秒間隔の setInterval ポーリングで取得する（新着反映）。
 *   useEffect のクリーンアップで確実に clearInterval する。
 * - ポーリング失敗時は画面を壊さず、最終状態を維持して控えめなエラー表示に留める。
 *
 * page.tsx（Server Component）から sensorFeatures（サーバー側取得済み）を props で受ける。
 */
import { useState } from "react";

import AlertDetailDrawer from "@/components/alert/AlertDetailDrawer";
import AlertList from "@/components/alert/AlertList";
import KpiSummary from "@/components/dashboard/KpiSummary";
import { useAlertPolling } from "@/hooks/useAlertPolling";
import { useKpiPolling } from "@/hooks/useKpiPolling";
import SensorMap from "@/components/map/SensorMap";
import type { SensorFeatureCollection } from "@/types/sensor";

/** アラート・KPI のポーリング間隔（ミリ秒）。 */
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
  // KPI も同一間隔でポーリング（成功時のみ更新 / 失敗時は再スケルトン: FR-8）。
  const { kpiData, isLoading } = useKpiPolling(ALERT_POLL_INTERVAL_MS);
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);

  const selectedAlert =
    alerts.find((alert) => alert.telemetryId === selectedAlertId) ?? null;

  /** 地図マーカー（センサー）選択を、そのセンサーのアラート選択へ変換する。 */
  const handleSelectMarker = (sensorId: string) => {
    const alert = alerts.find((item) => item.sensorId === sensorId);
    setSelectedAlertId(alert ? alert.telemetryId : null);
  };

  return (
    <div className="space-y-4">
      {/* KPI サマリ（FE-7・全面幅）。ランドマークは本コンポーネントが一元所有。
          スケルトン中も h2 と aria-labelledby を維持し、配下でスケルトン↔カードを切替える */}
      <section aria-labelledby="kpi-summary-title" aria-busy={isLoading}>
        <h2
          id="kpi-summary-title"
          className="mb-2 text-sm font-semibold text-slate-500"
        >
          KPI サマリ
        </h2>
        {isLoading || kpiData === null ? (
          <div
            data-testid="kpi-skeleton"
            aria-hidden="true"
            className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5"
          >
            {Array.from({ length: 5 }, (_item, index) => (
              <div
                key={index}
                className="h-24 animate-pulse rounded-xl border border-slate-200 bg-slate-100"
              />
            ))}
          </div>
        ) : (
          <KpiSummary kpiData={kpiData} />
        )}
      </section>

      {/* 既存 3 列グリッド（地図 / アラート一覧 / 詳細ドロワー） */}
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
    </div>
  );
}
