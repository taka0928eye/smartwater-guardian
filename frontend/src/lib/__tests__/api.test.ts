/**
 * FE-1: API クライアント（src/lib/api.ts）の TDD テスト。
 *
 * axios インスタンス（apiClient）の get/post を vi.spyOn でモックし、
 * サーバーなしで正常系・異常系を検証する。
 *
 * 実行: npm run test
 */

import { afterEach, describe, expect, it, vi } from "vitest";
import axios from "axios";
import type { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from "axios";

import {
  ApiError,
  apiClient,
  createWorkOrder,
  fetchAlertDetail,
  fetchAlerts,
  fetchKpiSummary,
  fetchSensors,
  fetchSensorsGeoJson,
} from "../api";

const MOCK_SENSOR = {
  sensor_id: "SNS-001",
  hydrant_id: "HYD-001",
  status: "normal",
  location: { latitude: 35.7022, longitude: 139.7448 },
  last_reading_at: "2026-08-10T06:00:00Z",
};

const MOCK_ALERT_SUMMARY = {
  telemetry_id: "tlm_001",
  sensor_id: "SNS-001",
  hydrant_id: "HYD-001",
  severity_level: 3,
  leak_confidence: 88,
  detected_at: "2026-08-10T06:00:00Z",
};

const MOCK_ALERT_DETAIL = {
  ...MOCK_ALERT_SUMMARY,
  location: { latitude: 35.7022, longitude: 139.7448 },
  analysis: {
    leak_confidence: 88,
    severity_level: 3,
    dominant_freq_hz: 1200,
    band_energy_ratio: 0.75,
    spectrum: [
      { freq_hz: 500, magnitude: 0.1 },
      { freq_hz: 1200, magnitude: 0.9 },
    ],
  },
  pipe_info: {
    pipe_id: "P-001",
    material: "ductile_iron",
    diameter_mm: 150,
    installed_year: 1990,
    burial_depth_m: 1.2,
    age_years: 36,
  },
};

const MOCK_WORK_ORDER = {
  work_order_id: "wo_001",
  alert_id: "tlm_001",
  created_at: "2026-08-10T06:00:00Z",
  parts: [
    {
      name: "補修用割Tクランプ",
      spec: "鋳鉄管150mm",
      quantity: 1,
      unit_price_yen: 48000,
      subtotal_yen: 48000,
    },
  ],
  total_estimate_yen: 48000,
  work_steps: ["閉栓する", "クランプを装着する"],
  required_workers: 4,
  estimated_duration_hours: 8,
  urgency: "critical",
  notification_text: "至急対応してください。",
  source: "fallback",
};

/** GET /api/v1/kpi/summary のレスポンス（BE-8）。snake_case 7 フィールド。 */
const MOCK_KPI_SUMMARY = {
  total_sensors: 10,
  level1_count: 8,
  level2_count: 3,
  level3_count: 1,
  estimated_cost_saved_yen: 2048400,
  is_estimate: true,
  assumption_doc: "docs/business-model.md",
};

/** status:500 の AxiosError を生成するためのレスポンス。 */
const badResponse: AxiosResponse = {
  data: { detail: "boom" },
  status: 500,
  statusText: "Internal Server Error",
  headers: {},
  config: {} as InternalAxiosRequestConfig,
};

/** GET /api/v1/sensors?format=geojson のレスポンス（BE-6）。座標は [経度, 緯度] 順。 */
const MOCK_GEOJSON = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      properties: {
        sensor_id: "SNS-001",
        status: "critical",
        severity_level: 3,
        last_reading_at: "2026-08-10T09:02:00Z",
      },
      geometry: { type: "Point", coordinates: [139.7744, 35.6812] },
    },
    {
      type: "Feature",
      properties: {
        sensor_id: "SNS-006",
        status: "unknown",
        severity_level: null,
        last_reading_at: null,
      },
      geometry: { type: "Point", coordinates: [139.7005, 35.6595] },
    },
  ],
};

function axiosError(
  message: string,
  code: string,
  response?: AxiosResponse,
): AxiosError {
  return new axios.AxiosError(message, code, undefined, undefined, response);
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("apiClient の設定", () => {
  it("NEXT_PUBLIC_API_BASE_URL 未設定時はデフォルトURLを使う", async () => {
    vi.resetModules();
    const original = process.env.NEXT_PUBLIC_API_BASE_URL;
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
    try {
      const fresh = await import("../api");
      expect(fresh.apiClient.defaults.baseURL).toBe("http://localhost:8000");
      expect(fresh.apiClient.defaults.timeout).toBe(10_000);
    } finally {
      if (original !== undefined) process.env.NEXT_PUBLIC_API_BASE_URL = original;
    }
  });

  it("NEXT_PUBLIC_API_BASE_URL 設定時はその値を使う", async () => {
    vi.resetModules();
    const original = process.env.NEXT_PUBLIC_API_BASE_URL;
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://example.test:9999";
    try {
      const fresh = await import("../api");
      expect(fresh.apiClient.defaults.baseURL).toBe("http://example.test:9999");
    } finally {
      if (original === undefined) {
        delete process.env.NEXT_PUBLIC_API_BASE_URL;
      } else {
        process.env.NEXT_PUBLIC_API_BASE_URL = original;
      }
    }
  });
});

describe("fetchSensors", () => {
  it("GET /api/v1/sensors を呼び、snake_case を camelCase へ変換して返す", async () => {
    const spy = vi
      .spyOn(apiClient, "get")
      .mockResolvedValue({ data: [MOCK_SENSOR] });

    const sensors = await fetchSensors();

    expect(spy).toHaveBeenCalledWith("/api/v1/sensors");
    expect(sensors).toEqual([
      {
        sensorId: "SNS-001",
        hydrantId: "HYD-001",
        status: "normal",
        location: { latitude: 35.7022, longitude: 139.7448 },
        lastReadingAt: "2026-08-10T06:00:00Z",
      },
    ]);
  });

  it("axios エラー（HTTP 500）を ApiError に変換して throw する", async () => {
    vi.spyOn(apiClient, "get").mockRejectedValue(
      axiosError("Request failed with status code 500", "ERR_BAD_RESPONSE", badResponse),
    );

    const promise = fetchSensors();
    await expect(promise).rejects.toBeInstanceOf(ApiError);
    await expect(promise).rejects.toMatchObject({
      name: "ApiError",
      status: 500,
      message: "boom",
    });
  });

  it("axios 以外のエラーはそのまま throw する", async () => {
    const boom = new Error("non-axios failure");
    vi.spyOn(apiClient, "get").mockRejectedValue(boom);

    const promise = fetchSensors();
    await expect(promise).rejects.toBe(boom);
  });
});

describe("fetchSensorsGeoJson", () => {
  it("GET /api/v1/sensors を format=geojson で呼び、camelCase へ変換して返す", async () => {
    const spy = vi
      .spyOn(apiClient, "get")
      .mockResolvedValue({ data: MOCK_GEOJSON });

    const fc = await fetchSensorsGeoJson();

    expect(spy).toHaveBeenCalledWith("/api/v1/sensors", {
      params: { format: "geojson" },
    });
    // トップレベル構造は GeoJSON のまま
    expect(fc.type).toBe("FeatureCollection");
    expect(fc.features).toHaveLength(2);
    // properties は camelCase へ変換される
    expect(fc.features[0]?.properties).toEqual({
      sensorId: "SNS-001",
      status: "critical",
      severityLevel: 3,
      lastReadingAt: "2026-08-10T09:02:00Z",
    });
    // 座標順序は GeoJSON[lng, lat] のまま保持される（変換しない）
    expect(fc.features[0]?.geometry.coordinates).toEqual([139.7744, 35.6812]);
  });

  it("severity_level / last_reading_at が null の場合は null のまま返す", async () => {
    vi.spyOn(apiClient, "get").mockResolvedValue({ data: MOCK_GEOJSON });

    const fc = await fetchSensorsGeoJson();
    const second = fc.features[1]?.properties;
    expect(second?.severityLevel).toBeNull();
    expect(second?.lastReadingAt).toBeNull();
  });

  it("axios エラー（HTTP 500）を ApiError に変換して throw する", async () => {
    vi.spyOn(apiClient, "get").mockRejectedValue(
      axiosError("Request failed with status code 500", "ERR_BAD_RESPONSE", badResponse),
    );

    const promise = fetchSensorsGeoJson();
    await expect(promise).rejects.toBeInstanceOf(ApiError);
    await expect(promise).rejects.toMatchObject({ status: 500, message: "boom" });
  });
});

describe("fetchAlerts", () => {
  it("GET /api/v1/alerts をパラメータなしで呼ぶ", async () => {
    const spy = vi
      .spyOn(apiClient, "get")
      .mockResolvedValue({ data: [MOCK_ALERT_SUMMARY] });

    const alerts = await fetchAlerts();

    expect(spy).toHaveBeenCalledWith("/api/v1/alerts", { params: undefined });
    expect(alerts).toEqual([
      {
        telemetryId: "tlm_001",
        sensorId: "SNS-001",
        hydrantId: "HYD-001",
        severityLevel: 3,
        leakConfidence: 88,
        detectedAt: "2026-08-10T06:00:00Z",
      },
    ]);
  });

  it("level / limit パラメータをクエリに渡す", async () => {
    const spy = vi
      .spyOn(apiClient, "get")
      .mockResolvedValue({ data: [] });

    await fetchAlerts({ level: 3, limit: 10 });

    expect(spy).toHaveBeenCalledWith("/api/v1/alerts", {
      params: { level: 3, limit: 10 },
    });
  });
});

describe("fetchAlertDetail", () => {
  it("GET /api/v1/alerts/{id} を呼び、入れ子の snake_case も変換する", async () => {
    const spy = vi
      .spyOn(apiClient, "get")
      .mockResolvedValue({ data: MOCK_ALERT_DETAIL });

    const detail = await fetchAlertDetail("tlm_001");

    expect(spy).toHaveBeenCalledWith("/api/v1/alerts/tlm_001");
    expect(detail.telemetryId).toBe("tlm_001");
    expect(detail.severityLevel).toBe(3);
    // analysis.spectrum も変換されている
    expect(detail.analysis?.spectrum).toEqual([
      { freqHz: 500, magnitude: 0.1 },
      { freqHz: 1200, magnitude: 0.9 },
    ]);
    expect(detail.analysis?.dominantFreqHz).toBe(1200);
    // pipeInfo も変換されている
    expect(detail.pipeInfo).toEqual({
      pipeId: "P-001",
      material: "ductile_iron",
      diameterMm: 150,
      installedYear: 1990,
      burialDepthM: 1.2,
      ageYears: 36,
    });
  });

  it("pipe_info が null でも返る（クラッシュしない）", async () => {
    const detail = { ...MOCK_ALERT_DETAIL, pipe_info: null, analysis: null };
    vi.spyOn(apiClient, "get").mockResolvedValue({ data: detail });

    const result = await fetchAlertDetail("tlm_001");
    expect(result.pipeInfo).toBeNull();
    expect(result.analysis).toBeNull();
  });
});

describe("createWorkOrder", () => {
  it("POST /api/v1/alerts/{id}/work-order を呼び、WorkOrder を返す", async () => {
    const spy = vi
      .spyOn(apiClient, "post")
      .mockResolvedValue({ data: MOCK_WORK_ORDER });

    const order = await createWorkOrder("tlm_001");

    expect(spy).toHaveBeenCalledWith("/api/v1/alerts/tlm_001/work-order");
    expect(order.workOrderId).toBe("wo_001");
    expect(order.totalEstimateYen).toBe(48000);
    expect(order.parts[0]).toEqual({
      name: "補修用割Tクランプ",
      spec: "鋳鉄管150mm",
      quantity: 1,
      unitPriceYen: 48000,
      subtotalYen: 48000,
    });
    expect(order.workSteps).toEqual(["閉栓する", "クランプを装着する"]);
    expect(order.urgency).toBe("critical");
    expect(order.source).toBe("fallback");
    expect(order.notificationText).toBe("至急対応してください。");
  });
});

describe("fetchKpiSummary", () => {
  it("GET /api/v1/kpi/summary を呼び、snake_case 7 フィールドを camelCase へ変換して返す", async () => {
    const spy = vi
      .spyOn(apiClient, "get")
      .mockResolvedValue({ data: MOCK_KPI_SUMMARY });

    const summary = await fetchKpiSummary();

    expect(spy).toHaveBeenCalledWith("/api/v1/kpi/summary");
    expect(summary).toEqual({
      totalSensors: 10,
      level1Count: 8,
      level2Count: 3,
      level3Count: 1,
      estimatedCostSavedYen: 2048400,
      isEstimate: true,
      assumptionDoc: "docs/business-model.md",
    });
  });

  it("axios エラー（HTTP 500）を ApiError に変換して throw する", async () => {
    vi.spyOn(apiClient, "get").mockRejectedValue(
      axiosError("Request failed with status code 500", "ERR_BAD_RESPONSE", badResponse),
    );

    const promise = fetchKpiSummary();
    await expect(promise).rejects.toBeInstanceOf(ApiError);
    await expect(promise).rejects.toMatchObject({ status: 500, message: "boom" });
  });

  it("axios 以外のエラーはそのまま throw する（透過）", async () => {
    const boom = new Error("non-axios failure");
    vi.spyOn(apiClient, "get").mockRejectedValue(boom);

    const promise = fetchKpiSummary();
    await expect(promise).rejects.toBe(boom);
  });
});
