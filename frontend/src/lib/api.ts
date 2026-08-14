/**
 * FE-1: axios クライアントと API 関数群。
 *
 * - バックエンドの snake_case レスポンスを camelCase へ変換して返す（境界で一度だけ）。
 * - エラーは ApiError に変換して throw する（axios 以外のエラーはそのまま透過）。
 * - any 型は使用しない（CLAUDE.md §5.2）。
 */

import axios from "axios";

import type {
  AlertDetail,
  AlertSummary,
  KpiSummary,
  SensorInfo,
  SeverityLevel,
  WorkOrder,
} from "../types/api";
import type {
  DisasterSimulateResponse,
  DisasterSummary,
} from "../types/disaster";
import type { SensorFeatureCollection } from "../types/sensor";

/** NEXT_PUBLIC_API_BASE_URL はクライアントバンドルに載るため、機密情報は置かない（CLAUDE.md §5.1）。 */
const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

/**
 * axios インスタンス。テストや外部から参照できるよう export する。
 * モックは vi.spyOn(apiClient, "get") 等で行う。
 */
export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 10_000,
});

/** 取得条件（GET /api/v1/alerts）。 */
export interface FetchAlertsParams {
  level?: SeverityLevel;
  limit?: number;
}

/** API 呼び出し失敗を表す独自エラー。 */
export class ApiError extends Error {
  readonly status: number | undefined;
  readonly data: unknown;

  constructor(
    message: string,
    status: number | undefined = undefined,
    data: unknown = undefined,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

/** snake_case キーを camelCase キーへ変換する（例: last_reading_at -> lastReadingAt）。 */
function toCamelCaseKey(key: string): string {
  return key.replace(/_([a-z0-9])/g, (_match, char: string) =>
    char.toUpperCase(),
  );
}

/**
 * レスポンス全体を再帰的に camelCase へ変換する。
 * 配列・ネストオブジェクトも対応し、null / プリミティブはそのまま返す。
 */
function toCamelCase<T>(value: T): T {
  if (Array.isArray(value)) {
    return value.map((item) => toCamelCase(item)) as unknown as T;
  }
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>).map(([key, item]) => [
        toCamelCaseKey(key),
        toCamelCase(item),
      ]),
    ) as unknown as T;
  }
  return value;
}

/** axios のエラーを ApiError へ変換しつつ、非 axios エラーは透過する。 */
async function unwrap<T>(request: Promise<{ data: unknown }>): Promise<T> {
  try {
    const { data } = await request;
    return toCamelCase(data) as T;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const status = error.response?.status;
      const responseData = error.response?.data as
        | { message?: string; detail?: unknown }
        | undefined;
      const message =
        responseData?.message ??
        (typeof responseData?.detail === "string"
          ? responseData.detail
          : undefined) ??
        error.message;
      throw new ApiError(message, status, error.response?.data);
    }
    throw error;
  }
}

/** 消火栓・センサー一覧を取得する。 */
export function fetchSensors(): Promise<SensorInfo[]> {
  return unwrap<SensorInfo[]>(apiClient.get("/api/v1/sensors"));
}

/**
 * センサー地図（FE-3）用の GeoJSON FeatureCollection を取得する。
 * GET /api/v1/sensors?format=geojson（BE-6）。unwrap の camelCase 変換により
 * sensor_id -> sensorId / severity_level -> severityLevel / last_reading_at -> lastReadingAt
 * へ変換され、src/types/sensor.ts の SensorFeatureCollection と一致する。
 * 座標は GeoJSON 標準の [経度, 緯度] 順のまま保持される（Leaflet 側の変換は FE-3 の責務）。
 */
export function fetchSensorsGeoJson(): Promise<SensorFeatureCollection> {
  return unwrap<SensorFeatureCollection>(
    apiClient.get("/api/v1/sensors", { params: { format: "geojson" } }),
  );
}

/** アラート一覧を取得する。level / limit で絞り込み可能。 */
export function fetchAlerts(params?: FetchAlertsParams): Promise<AlertSummary[]> {
  return unwrap<AlertSummary[]>(apiClient.get("/api/v1/alerts", { params }));
}

/** アラート詳細（解析結果・配管情報）を取得する。 */
export function fetchAlertDetail(telemetryId: string): Promise<AlertDetail> {
  return unwrap<AlertDetail>(
    apiClient.get(`/api/v1/alerts/${encodeURIComponent(telemetryId)}`),
  );
}

/** 選択したアラートの受信音響（WAV）URLを返す。 */
export function getAlertAudioUrl(telemetryId: string): string {
  const baseUrl = BASE_URL.replace(/\/$/, "");
  return `${baseUrl}/api/v1/alerts/${encodeURIComponent(telemetryId)}/audio`;
}

/** AI 自動起票を実行し、WorkOrder を取得する。 */
export function createWorkOrder(telemetryId: string): Promise<WorkOrder> {
  return unwrap<WorkOrder>(
    apiClient.post(`/api/v1/alerts/${encodeURIComponent(telemetryId)}/work-order`),
  );
}

/** KPI サマリ（BE-8: GET /api/v1/kpi/summary）を取得する。
 *  unwrap により snake_case 7 フィールドを camelCase へ変換して返す。 */
export function fetchKpiSummary(): Promise<KpiSummary> {
  return unwrap<KpiSummary>(apiClient.get("/api/v1/kpi/summary"));
}

/** 防災モードの被災エリアクラスタ（BE-7: GET /api/v1/disaster/summary）を取得する。
 *  unwrap により snake_case を camelCase へ変換して返す（cluster_id -> clusterId 等）。
 *  geometry（GeoJSON Polygon）の座標は [経度, 緯度] 順のまま保持される。 */
export function fetchDisasterSummary(): Promise<DisasterSummary> {
  return unwrap<DisasterSummary>(apiClient.get("/api/v1/disaster/summary"));
}

/** デモ用に Level 3 アラートを一括投入する（BE-7: POST /api/v1/disaster/simulate）。 */
export function simulateDisaster(
  count: number,
): Promise<DisasterSimulateResponse> {
  return unwrap<DisasterSimulateResponse>(
    apiClient.post("/api/v1/disaster/simulate", null, { params: { count } }),
  );
}
