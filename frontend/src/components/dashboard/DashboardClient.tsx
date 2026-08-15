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
 * - 地図マーカーの色も同一間隔（useSensorPolling）でポーリングし、漏水判定発生後に
 *   アラート一覧と地図が異なる色のまま取り残されないようにする。
 *
 * page.tsx（Server Component）から sensorFeatures（サーバー側取得済みの初期値）を
 * props で受け、以後は useSensorPolling が同じ間隔でリフレッシュする。
 */
import { useCallback, useState } from "react";

import AlertDetailDrawer from "@/components/alert/AlertDetailDrawer";
import AlertList from "@/components/alert/AlertList";
import KpiSummary, {
  KPI_CARD_COUNT,
  KPI_GRID_CLASS,
} from "@/components/dashboard/KpiSummary";
import { useAlertPolling } from "@/hooks/useAlertPolling";
import { useDisasterSummary } from "@/hooks/useDisasterSummary";
import { useKpiPolling } from "@/hooks/useKpiPolling";
import { useSensorPolling } from "@/hooks/useSensorPolling";
import { clearDemo, seedDemoBatch, simulateDisaster } from "@/lib/api";
import SensorMap from "@/components/map/SensorMap";
import type { SensorFeatureCollection } from "@/types/sensor";

/** アラート・KPI のポーリング間隔（ミリ秒）。 */
export const ALERT_POLL_INTERVAL_MS = 5000;

/** 防災シミュレーションで投入する Level 3 の件数（BE-7 / POST /simulate）。 */
export const DISASTER_SIMULATE_COUNT = 6;

export interface DashboardClientProps {
  /** サーバー側（page.tsx）で取得済みのセンサー GeoJSON（初期表示用。以後は useSensorPolling が引き継ぐ）。 */
  sensorFeatures: SensorFeatureCollection;
}

export default function DashboardClient({
  sensorFeatures: initialSensorFeatures,
}: DashboardClientProps) {
  // 5秒間隔のポーリングは useAlertPolling が担う（clearInterval クリーンアップ含む）。
  const {
    alerts,
    error: pollError,
    refresh: refreshAlerts,
  } = useAlertPolling(ALERT_POLL_INTERVAL_MS);
  // KPI も同一間隔でポーリング（成功時のみ更新 / 失敗時は再スケルトン: FR-8）。
  const { kpiData, isLoading, refresh: refreshKpi } = useKpiPolling(
    ALERT_POLL_INTERVAL_MS,
  );
  // 地図マーカーの色をアラート一覧と同じ間隔で同期させる（初回は SSR 取得値、以後はポーリング値）。
  const { sensorFeatures, refresh: refreshSensors } = useSensorPolling(
    initialSensorFeatures,
    ALERT_POLL_INTERVAL_MS,
  );
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);

  // BE-7: 被災エリアクラスタのポーリング（5 秒間隔）。simulate 直後は refresh() で即時反映する。
  const {
    disasterSummary,
    error: disasterError,
    refresh: refreshDisaster,
  } = useDisasterSummary(ALERT_POLL_INTERVAL_MS);
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulateMessage, setSimulateMessage] = useState<string | null>(null);
  const [simulateError, setSimulateError] = useState<string | null>(null);

  // DEMO-2: 「シード投入」ボタンの処理状態。
  const [isSeeding, setIsSeeding] = useState(false);
  const [seedMessage, setSeedMessage] = useState<string | null>(null);
  const [seedError, setSeedError] = useState<string | null>(null);

  // DEMO-2: 「シードクリア」ボタンの処理状態。
  const [isClearing, setIsClearing] = useState(false);
  const [clearMessage, setClearMessage] = useState<string | null>(null);
  const [clearError, setClearError] = useState<string | null>(null);

  /** 「防災シミュレーション」ボタン押下: Level 3 を一括投入してクラスタを即時反映する。
   *  useCallback で refreshDisaster の変化時のみ参照を更新する。 */
  const handleSimulateDisaster = useCallback(async (): Promise<void> => {
    setIsSimulating(true);
    setSimulateError(null);
    try {
      const response = await simulateDisaster(DISASTER_SIMULATE_COUNT);
      setSimulateMessage(response.message);
      await refreshDisaster();
    } catch {
      // 画面は壊さず、ボタン横に控えめなエラー表示に留める。
      setSimulateError("防災シミュレーションに失敗しました");
    } finally {
      setIsSimulating(false);
    }
  }, [refreshDisaster]);

  /** 「シード投入」ボタン押下: 20件（Lv0×8/Lv1×8/Lv2×3/Lv3×1）を一括投入し、
   *  アラート一覧・KPI・地図を即時反映する（DEMO-2）。 */
  const handleSeedDemo = useCallback(async (): Promise<void> => {
    setIsSeeding(true);
    setSeedError(null);
    try {
      const response = await seedDemoBatch();
      setSeedMessage(response.message);
      await Promise.all([refreshAlerts(), refreshKpi(), refreshSensors()]);
    } catch {
      setSeedError("シード投入に失敗しました");
    } finally {
      setIsSeeding(false);
    }
  }, [refreshAlerts, refreshKpi, refreshSensors]);

  /** 「シードクリア」ボタン押下: 20件Lv0の初期状態に戻し、被災エリア表示も含めて
   *  即時反映する（DEMO-2）。 */
  const handleClearDemo = useCallback(async (): Promise<void> => {
    setIsClearing(true);
    setClearError(null);
    try {
      const response = await clearDemo();
      setClearMessage(response.message);
      await Promise.all([
        refreshAlerts(),
        refreshKpi(),
        refreshSensors(),
        refreshDisaster(),
      ]);
    } catch {
      setClearError("シードクリアに失敗しました");
    } finally {
      setIsClearing(false);
    }
  }, [refreshAlerts, refreshKpi, refreshSensors, refreshDisaster]);

  const selectedAlert =
    alerts.find((alert) => alert.telemetryId === selectedAlertId) ?? null;

  /** 地図マーカー（センサー）選択を、そのセンサーのアラート選択へ変換する。
   *  useCallback で alerts 変化時のみ参照を更新し、KPI ポーリング等の無関係な
   *  再描画では SensorMap（React.memo）が再描画されないようにする。 */
  const handleSelectMarker = useCallback(
    (sensorId: string) => {
      const alert = alerts.find((item) => item.sensorId === sensorId);
      setSelectedAlertId(alert ? alert.telemetryId : null);
    },
    [alerts],
  );

  return (
    <div className="space-y-4">
      {/* KPI サマリ（FE-7・全面幅）。ランドマークは本コンポーネントが一元所有。
          スケルトン中も h2 と aria-labelledby を維持し、配下でスケルトン↔カードを切替える */}
      <section
        aria-labelledby="kpi-summary-title"
        aria-busy={isLoading}
        aria-live="polite"
      >
        <h2
          id="kpi-summary-title"
          className="mb-2 text-sm font-semibold text-slate-500"
        >
          KPI サマリ
        </h2>
        {kpiData === null ? (
          <div
            data-testid="kpi-skeleton"
            aria-hidden="true"
            className={KPI_GRID_CLASS}
          >
            {Array.from({ length: KPI_CARD_COUNT }, (_item, index) => (
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
        {/* GIS マップ（FE-3: Leaflet センサー地図）。マーカー選択は selectedAlertId と連動。
            BE-7: ヘッダーに防災シミュレーションボタンを置き、Level 3 破裂クラスタを描画する */}
        <section className="rounded-xl bg-white p-4 lg:col-span-2">
          <div className="mb-2 flex items-center justify-between gap-2">
            <h2 className="text-sm font-semibold text-slate-500">
              センサー地図
            </h2>
            <div className="flex items-center gap-2">
              <button
                type="button"
                data-testid="seed-demo-button"
                onClick={handleSeedDemo}
                disabled={isSeeding}
                className="rounded-lg bg-slate-600 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isSeeding ? "投入中…" : "シード投入"}
              </button>
              <button
                type="button"
                data-testid="clear-demo-button"
                onClick={handleClearDemo}
                disabled={isClearing}
                className="rounded-lg bg-slate-400 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-slate-500 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isClearing ? "クリア中…" : "シードクリア"}
              </button>
              <button
                type="button"
                data-testid="disaster-simulate-button"
                onClick={handleSimulateDisaster}
                disabled={isSimulating}
                className="rounded-lg bg-red-600 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isSimulating
                  ? "シミュレーション中…"
                  : "防災シミュレーション"}
              </button>
            </div>
          </div>
          <SensorMap
            data={sensorFeatures}
            selectedAlertId={selectedAlertId}
            onSelectMarker={handleSelectMarker}
            disasterSummary={disasterSummary}
          />
          {simulateMessage ? (
            <p
              data-testid="disaster-simulate-message"
              className="mt-2 text-xs text-slate-600"
            >
              {simulateMessage}
            </p>
          ) : null}
          {simulateError ? (
            <p
              data-testid="disaster-simulate-error"
              className="mt-2 text-xs text-red-600"
            >
              {simulateError}
            </p>
          ) : null}
          {disasterError ? (
            <p
              data-testid="disaster-error"
              className="mt-2 text-xs text-amber-600"
            >
              {disasterError}
            </p>
          ) : null}
          {seedMessage ? (
            <p
              data-testid="seed-demo-message"
              className="mt-2 text-xs text-slate-600"
            >
              {seedMessage}
            </p>
          ) : null}
          {seedError ? (
            <p
              data-testid="seed-demo-error"
              className="mt-2 text-xs text-red-600"
            >
              {seedError}
            </p>
          ) : null}
          {clearMessage ? (
            <p
              data-testid="clear-demo-message"
              className="mt-2 text-xs text-slate-600"
            >
              {clearMessage}
            </p>
          ) : null}
          {clearError ? (
            <p
              data-testid="clear-demo-error"
              className="mt-2 text-xs text-red-600"
            >
              {clearError}
            </p>
          ) : null}
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
