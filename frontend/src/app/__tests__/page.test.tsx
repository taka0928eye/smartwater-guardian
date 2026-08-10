// @vitest-environment jsdom
/**
 * FE-3/FE-5: ダッシュボードルート（src/app/page.tsx）のデータ取得連携テスト。
 *
 * page.tsx は Server Component として fetchSensorsGeoJson() で実データを取得し、
 * DashboardClient へ渡す。バックエンドが応答しない場合はフォールバック（モック GeoJSON）
 * で描画する。fetchSensorsGeoJson / fetchAlerts と SensorMap のみをモックし、
 * Header / KpiSummary は実物で描画する。
 */
import { describe, expect, it, vi } from "vitest";
import { act, render, screen } from "@testing-library/react";
import React from "react";

import { fetchSensorsGeoJson } from "@/lib/api";
import type { SensorFeatureCollection } from "@/types/sensor";

vi.mock("@/lib/api", () => ({
  fetchSensorsGeoJson: vi.fn(),
  fetchAlerts: vi.fn().mockResolvedValue([]),
}));

vi.mock("@/components/map/SensorMap", () => ({
  default: (props: { data?: SensorFeatureCollection }) =>
    React.createElement(
      "div",
      { "data-testid": "sensor-map" },
      props.data === undefined
        ? "no-data"
        : `count=${props.data.features.length}`,
    ),
}));

const mockedFetch = vi.mocked(fetchSensorsGeoJson);

/** 最小の GeoJSON FeatureCollection（camelCase）。 */
const REAL_DATA: SensorFeatureCollection = {
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
  ],
};

describe("Home (page.tsx)", () => {
  it("取得した実データを DashboardClient（SensorMap）へ渡して描画する", async () => {
    mockedFetch.mockResolvedValue(REAL_DATA);

    const { default: Home } = await import("@/app/page");
    await act(async () => {
      render(await Home());
    });
    // DashboardClient の fetchAlerts（ポーリング初回）を flush する
    await act(async () => {});

    expect(mockedFetch).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId("sensor-map").textContent).toBe("count=1");
  });

  it("取得失敗時はフォールバック（モック GeoJSON）で描画する", async () => {
    mockedFetch.mockRejectedValue(new Error("backend unreachable"));

    const { default: Home } = await import("@/app/page");
    await act(async () => {
      render(await Home());
    });
    await act(async () => {});

    // フォールバックは hydrants.json 由来の10件で描画される。
    expect(screen.getByTestId("sensor-map").textContent).toBe("count=10");
  });

  it("取得失敗時はフォールバックで描画するだけでなく、原因をログに記録する", async () => {
    const consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    const backendError = new Error("backend unreachable");
    mockedFetch.mockRejectedValue(backendError);

    const { default: Home } = await import("@/app/page");
    await act(async () => {
      render(await Home());
    });
    await act(async () => {});

    expect(consoleErrorSpy).toHaveBeenCalledWith(
      expect.stringContaining("fetchSensorsGeoJson"),
      backendError,
    );
    consoleErrorSpy.mockRestore();
  });
});
