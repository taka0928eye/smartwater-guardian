// @vitest-environment jsdom
/**
 * FE-5: アラートポーリングフック（src/hooks/useAlertPolling.ts）の TDD テスト。
 *
 * - マウント直後に fetchAlerts を即時呼び出し、成功で alerts / lastUpdatedAt をセット
 * - intervalMs 経過で再取得し、alerts を更新する（フェイクタイマー）
 * - 取得失敗時は最終状態を据え置き、控えめに error を表示する
 * - refresh() で即時再取得できる（デモ操作ボタン押下直後の反映に使う）
 * - アンマウントで cancelled + clearInterval（以後 setState / 再取得しない）
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import { act, renderHook } from "@testing-library/react";

import type { AlertSummary } from "@/types/api";

vi.mock("@/lib/api", () => ({
  fetchAlerts: vi.fn(),
}));

import { fetchAlerts } from "@/lib/api";
import { useAlertPolling } from "../useAlertPolling";

const mockedFetchAlerts = vi.mocked(fetchAlerts);

const ALERTS: AlertSummary[] = [
  {
    telemetryId: "tlm_1",
    sensorId: "SNS-001",
    hydrantId: "HYD-001",
    severityLevel: 1,
    leakConfidence: 60,
    detectedAt: "2026-08-15T09:00:00Z",
  },
];

const ALERTS_UPDATED: AlertSummary[] = [
  ...ALERTS,
  {
    telemetryId: "tlm_2",
    sensorId: "SNS-002",
    hydrantId: "HYD-002",
    severityLevel: 3,
    leakConfidence: 95,
    detectedAt: "2026-08-15T09:05:00Z",
  },
];

afterEach(() => {
  vi.useRealTimers();
  vi.clearAllMocks();
});

describe("useAlertPolling", () => {
  it("マウント直後に fetchAlerts を呼び、成功で alerts をセットする", async () => {
    mockedFetchAlerts.mockResolvedValue(ALERTS);

    const { result } = renderHook(() => useAlertPolling(5000));
    await act(async () => {});

    expect(mockedFetchAlerts).toHaveBeenCalledTimes(1);
    expect(result.current.alerts).toEqual(ALERTS);
    expect(result.current.error).toBeNull();
    expect(result.current.lastUpdatedAt).not.toBeNull();
  });

  it("intervalMs 経過で再取得され、alerts が更新される（フェイクタイマー）", async () => {
    vi.useFakeTimers();
    mockedFetchAlerts
      .mockResolvedValueOnce(ALERTS)
      .mockResolvedValueOnce(ALERTS_UPDATED);

    const { result } = renderHook(() => useAlertPolling(5000));
    await act(async () => {});

    expect(result.current.alerts).toHaveLength(1);

    act(() => {
      vi.advanceTimersByTime(5000);
    });
    await act(async () => {});

    expect(mockedFetchAlerts).toHaveBeenCalledTimes(2);
    expect(result.current.alerts).toHaveLength(2);
  });

  it("取得失敗時は最終状態を据え置き、error を表示する", async () => {
    mockedFetchAlerts.mockRejectedValue(new Error("backend down"));

    const { result } = renderHook(() => useAlertPolling(5000));
    await act(async () => {});

    expect(result.current.alerts).toEqual([]);
    expect(result.current.error).toBe("アラートの取得に失敗しました");
  });

  it("refresh() で即時再取得できる（デモ操作ボタン押下直後の反映）", async () => {
    mockedFetchAlerts
      .mockResolvedValueOnce(ALERTS)
      .mockResolvedValueOnce(ALERTS_UPDATED);

    const { result } = renderHook(() => useAlertPolling(5000));
    await act(async () => {});

    expect(result.current.alerts).toHaveLength(1);

    await act(async () => {
      await result.current.refresh();
    });

    expect(mockedFetchAlerts).toHaveBeenCalledTimes(2);
    expect(result.current.alerts).toHaveLength(2);
  });

  it("refresh() 失敗時は最終状態を据え置き、error を表示する", async () => {
    mockedFetchAlerts
      .mockResolvedValueOnce(ALERTS)
      .mockRejectedValueOnce(new Error("backend down"));

    const { result } = renderHook(() => useAlertPolling(5000));
    await act(async () => {});

    await act(async () => {
      await result.current.refresh();
    });

    expect(result.current.alerts).toEqual(ALERTS);
    expect(result.current.error).toBe("アラートの取得に失敗しました");
  });

  it("アンマウント後は cancelled で以後 setState / 再取得しない", async () => {
    vi.useFakeTimers();
    mockedFetchAlerts.mockResolvedValue(ALERTS);

    const { unmount } = renderHook(() => useAlertPolling(5000));
    await act(async () => {});

    unmount();
    mockedFetchAlerts.mockClear();
    act(() => {
      vi.advanceTimersByTime(10_000);
    });

    expect(mockedFetchAlerts).not.toHaveBeenCalled();
  });
});
