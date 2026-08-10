/**
 * FE-2/FE-3: ダッシュボードルート（Server Component）。
 *
 * ヘッダー・KPIサマリ・GISマップ（FE-3）・アラート一覧（FE-5 で実装予定）を配置する。
 * センサー地図のデータは BE-6 の GET /api/v1/sensors?format=geojson から取得し、
 * Client Component の SensorMap へ渡す。バックエンド未応答時はフォールバック
 * （hydrants.json 由来のモック）で描画する。
 *
 * データはリクエスト時に毎回取得する（静的生成だとビルド時の取得結果が焼き込まれ、
 * センサー状態の変化が反映されないため force-dynamic）。
 * Client Component 化はしない（時刻表示は Header が内部で担う）。
 */
import Header from "@/components/dashboard/Header";
import KpiSummary from "@/components/dashboard/KpiSummary";
import SensorMap from "@/components/map/SensorMap";
import { fetchSensorsGeoJson } from "@/lib/api";
import type { KpiData } from "@/components/dashboard/KpiSummary";
import type { SensorFeatureCollection } from "@/types/sensor";

/** センサー状態は常に最新を返すため、リクエスト時に描画する。 */
export const dynamic = "force-dynamic";

/** FE-2 デモ用のモック KPI データ（UI-1 デモシナリオの数値）。 */
const MOCK_KPI_DATA: KpiData = {
  totalSensors: 1240,
  level3Count: 1,
  level2Count: 3,
  todayDetections: 12,
  estimatedCostSavedYen: 1_420_000,
};

/**
 * FE-3 フォールバック用のモック GeoJSON データ。
 * backend/app/data/hydrants.json の10件から生成し、深刻度をバラけさせて
 * マーカーの色分け・Level 3 の点滅を確認できるようにする。
 * バックエンド未応答時のみ使用する（正常時は fetchSensorsGeoJson() の実データ）。
 * 座標は GeoJSON 標準の [経度, 緯度] 順。
 */
const FALLBACK_SENSOR_FEATURES: SensorFeatureCollection = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      properties: {
        sensorId: "SNS-001",
        status: "normal",
        severityLevel: 1,
        lastReadingAt: "2026-08-10T09:00:00Z",
      },
      geometry: { type: "Point", coordinates: [139.7444, 35.7019] },
    },
    {
      type: "Feature",
      properties: {
        sensorId: "SNS-002",
        status: "normal",
        severityLevel: 1,
        lastReadingAt: "2026-08-10T08:55:00Z",
      },
      geometry: { type: "Point", coordinates: [139.7703, 35.6917] },
    },
    {
      type: "Feature",
      properties: {
        sensorId: "SNS-003",
        status: "critical",
        severityLevel: 3,
        lastReadingAt: "2026-08-10T09:02:00Z",
      },
      geometry: { type: "Point", coordinates: [139.7744, 35.6812] },
    },
    {
      type: "Feature",
      properties: {
        sensorId: "SNS-004",
        status: "warning",
        severityLevel: 2,
        lastReadingAt: "2026-08-10T08:40:00Z",
      },
      geometry: { type: "Point", coordinates: [139.7583, 35.6667] },
    },
    {
      type: "Feature",
      properties: {
        sensorId: "SNS-005",
        status: "normal",
        severityLevel: 1,
        lastReadingAt: "2026-08-10T08:30:00Z",
      },
      geometry: { type: "Point", coordinates: [139.7006, 35.6896] },
    },
    {
      type: "Feature",
      properties: {
        sensorId: "SNS-006",
        status: "unknown",
        severityLevel: null,
        lastReadingAt: null,
      },
      geometry: { type: "Point", coordinates: [139.7005, 35.6595] },
    },
    {
      type: "Feature",
      properties: {
        sensorId: "SNS-007",
        status: "warning",
        severityLevel: 2,
        lastReadingAt: "2026-08-10T08:15:00Z",
      },
      geometry: { type: "Point", coordinates: [139.777, 35.7121] },
    },
    {
      type: "Feature",
      properties: {
        sensorId: "SNS-008",
        status: "normal",
        severityLevel: 1,
        lastReadingAt: "2026-08-10T08:00:00Z",
      },
      geometry: { type: "Point", coordinates: [139.7603, 35.7083] },
    },
    {
      type: "Feature",
      properties: {
        sensorId: "SNS-009",
        status: "warning",
        severityLevel: 2,
        lastReadingAt: "2026-08-10T07:45:00Z",
      },
      geometry: { type: "Point", coordinates: [139.7232, 35.6261] },
    },
    {
      type: "Feature",
      properties: {
        sensorId: "SNS-010",
        status: "unknown",
        severityLevel: null,
        lastReadingAt: null,
      },
      geometry: { type: "Point", coordinates: [139.7048, 35.6355] },
    },
  ],
};

export default async function Home() {
  // BE-6 の GeoJSON API からセンサー状態を取得する。
  // バックエンド未起動でもビルド・表示を壊さないよう、失敗時はフォールバックで描画する。
  let sensorFeatures: SensorFeatureCollection;
  try {
    sensorFeatures = await fetchSensorsGeoJson();
  } catch (error) {
    console.error(
      "fetchSensorsGeoJson に失敗したため、フォールバックデータで描画します。",
      error,
    );
    sensorFeatures = FALLBACK_SENSOR_FEATURES;
  }

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <Header />
      <main className="mx-auto max-w-7xl space-y-4 p-4 lg:p-6">
        <KpiSummary kpiData={MOCK_KPI_DATA} />
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          {/* GIS マップ（FE-3: Leaflet センサー地図） */}
          <section className="rounded-xl bg-white p-4 lg:col-span-2">
            <h2 className="mb-2 text-sm font-semibold text-slate-500">
              センサー地図
            </h2>
            <SensorMap data={sensorFeatures} />
          </section>
          {/* アラート一覧（FE-5 で実装） */}
          <section className="rounded-xl border-2 border-dashed border-slate-300 bg-white p-4">
            <h2 className="text-sm font-semibold text-slate-500">
              アラート一覧（FE-5 で実装予定）
            </h2>
          </section>
        </div>
      </main>
    </div>
  );
}
