// @vitest-environment jsdom
/**
 * 地図マーカー同期: センサー GeoJSON ポーリングフック（src/hooks/useSensorPolling.ts）の TDD テスト。
 *
 * - マウント時は initialData（page.tsx がSSRで取得した初期値）を即座に返す
 * - intervalMs 経過で fetchSensorsGeoJson を再取得し、sensorFeatures を更新する（フェイクタイマー）
 * - 取得失敗時は直前の sensorFeatures を維持する（useKpiPolling とは異なり破棄しない。
 *   地図をバックエンド停止中も白紙にしないフォールバック規約に合わせる）
 * - アンマウントで cancelled + clearInterval（以後 setState / 再取得しない）
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import { act, renderHook } from "@testing-library/react";

import type { SensorFeatureCollection } from "@/types/sensor";

vi.mock("@/lib/api", () => ({
  fetchSensorsGeoJson: vi.fn(),
}));

import { fetchSensorsGeoJson } from "@/lib/api";
import { useSensorPolling } from "../useSensorPolling";

const mockedFetchSensorsGeoJson = vi.mocked(fetchSensorsGeoJson);

const INITIAL: SensorFeatureCollection = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      properties: {
        sensorId: "SNS-001",
        status: "normal",
        severityLevel: 0,
        lastReadingAt: null,
      },
      geometry: { type: "Point", coordinates: [139.7444, 35.7019] },
    },
  ],
};

const UPDATED: SensorFeatureCollection = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      properties: {
        sensorId: "SNS-001",
        status: "critical",
        severityLevel: 3,
        lastReadingAt: "2026-08-11T09:00:00Z",
      },
      geometry: { type: "Point", coordinates: [139.7444, 35.7019] },
    },
  ],
};

afterEach(() => {
  vi.useRealTimers();
  vi.clearAllMocks();
});

describe("useSensorPolling", () => {
  it("マウント直後は initialData を返し、fetchSensorsGeoJson を1回呼ぶ", async () => {
    mockedFetchSensorsGeoJson.mockResolvedValue(INITIAL);

    const { result } = renderHook(() => useSensorPolling(INITIAL, 5000));

    expect(result.current.sensorFeatures).toEqual(INITIAL);
    await act(async () => {});
    expect(mockedFetchSensorsGeoJson).toHaveBeenCalledTimes(1);
  });

  it("intervalMs 経過で再取得され、sensorFeatures が更新される（フェイクタイマー）", async () => {
    vi.useFakeTimers();
    mockedFetchSensorsGeoJson
      .mockResolvedValueOnce(INITIAL)
      .mockResolvedValueOnce(UPDATED);

    const { result } = renderHook(() => useSensorPolling(INITIAL, 5000));
    await act(async () => {});

    expect(mockedFetchSensorsGeoJson).toHaveBeenCalledTimes(1);

    act(() => {
      vi.advanceTimersByTime(5000);
    });
    await act(async () => {});

    expect(mockedFetchSensorsGeoJson).toHaveBeenCalledTimes(2);
    expect(result.current.sensorFeatures).toEqual(UPDATED);
    expect(result.current.sensorFeatures.features[0]?.properties.severityLevel).toBe(3);
  });

  it("取得失敗時は直前の sensorFeatures を維持する（破棄しない）", async () => {
    vi.useFakeTimers();
    mockedFetchSensorsGeoJson
      .mockResolvedValueOnce(UPDATED)
      .mockRejectedValueOnce(new Error("backend down"));

    const { result } = renderHook(() => useSensorPolling(INITIAL, 5000));
    await act(async () => {});
    expect(result.current.sensorFeatures).toEqual(UPDATED);
    expect(result.current.error).toBeNull();

    act(() => {
      vi.advanceTimersByTime(5000);
    });
    await act(async () => {});

    expect(result.current.sensorFeatures).toEqual(UPDATED);
    expect(result.current.error).not.toBeNull();
  });

  it("アンマウントで clearInterval され、以後タイマーで再取得しない", async () => {
    vi.useFakeTimers();
    mockedFetchSensorsGeoJson.mockResolvedValue(INITIAL);

    const { unmount } = renderHook(() => useSensorPolling(INITIAL, 5000));
    await act(async () => {});

    unmount();
    mockedFetchSensorsGeoJson.mockClear();
    act(() => {
      vi.advanceTimersByTime(15_000);
    });
    await act(async () => {});

    expect(mockedFetchSensorsGeoJson).not.toHaveBeenCalled();
  });

  it("アンマウント後に in-flight が成功しても setState しない（cancelled ガード）", async () => {
    let resolveFn: (value: SensorFeatureCollection) => void = () => {};
    mockedFetchSensorsGeoJson.mockImplementation(
      () =>
        new Promise<SensorFeatureCollection>((resolve) => {
          resolveFn = resolve;
        }),
    );

    const { result, unmount } = renderHook(() => useSensorPolling(INITIAL, 5000));
    await act(async () => {});

    act(() => {
      unmount();
    });

    await act(async () => {
      resolveFn(UPDATED);
    });

    expect(mockedFetchSensorsGeoJson).toHaveBeenCalledTimes(1);
    expect(result.current.sensorFeatures).toEqual(INITIAL);
  });

  it("アンマウント後に in-flight が失敗しても setState しない（cancelled ガード）", async () => {
    let rejectFn: (error: Error) => void = () => {};
    mockedFetchSensorsGeoJson.mockImplementation(
      () =>
        new Promise<SensorFeatureCollection>((_resolve, reject) => {
          rejectFn = reject;
        }),
    );

    const { result, unmount } = renderHook(() => useSensorPolling(INITIAL, 5000));
    await act(async () => {});

    act(() => {
      unmount();
    });

    await act(async () => {
      rejectFn(new Error("late failure"));
    });

    expect(mockedFetchSensorsGeoJson).toHaveBeenCalledTimes(1);
    expect(result.current.sensorFeatures).toEqual(INITIAL);
    expect(result.current.error).toBeNull();
  });
});
