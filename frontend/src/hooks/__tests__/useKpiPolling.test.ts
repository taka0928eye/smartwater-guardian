// @vitest-environment jsdom
/**
 * FE-7: KPI ポーリングフック（src/hooks/useKpiPolling.ts）の TDD テスト。
 *
 * - マウント直後に fetchKpiSummary を即時呼び出し、成功で kpiData / isLoading=false
 * - intervalMs 経過で再取得し、kpiData を更新する（フェイクタイマー）
 * - 取得失敗時は kpiData=null / isLoading=true（再スケルトン。古い値を破棄）
 * - 失敗→次回成功で kpiData 復帰・isLoading=false
 * - アンマウントで cancelled + clearInterval（以後 setState / 再取得しない）
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import { act, renderHook } from "@testing-library/react";

import type { KpiSummary } from "@/types/api";

vi.mock("@/lib/api", () => ({
  fetchKpiSummary: vi.fn(),
}));

import { fetchKpiSummary } from "@/lib/api";
import { useKpiPolling } from "../useKpiPolling";

const mockedFetchKpiSummary = vi.mocked(fetchKpiSummary);

/** BE-8 契約フィクスチャ（ADR-003）。 */
const KPI: KpiSummary = {
  totalSensors: 10,
  level1Count: 8,
  level2Count: 3,
  level3Count: 1,
  estimatedCostSavedYen: 2048400,
  isEstimate: true,
  assumptionDoc: "docs/business-model.md",
};

const KPI_UPDATED: KpiSummary = {
  ...KPI,
  totalSensors: 20,
};

afterEach(() => {
  vi.useRealTimers();
  vi.clearAllMocks();
});

describe("useKpiPolling", () => {
  it("マウント直後に fetchKpiSummary を呼び、成功で kpiData をセット・isLoading=false にする", async () => {
    mockedFetchKpiSummary.mockResolvedValue(KPI);

    const { result } = renderHook(() => useKpiPolling(5000));
    await act(async () => {});

    expect(mockedFetchKpiSummary).toHaveBeenCalledTimes(1);
    expect(result.current.kpiData).toEqual(KPI);
    expect(result.current.isLoading).toBe(false);
  });

  it("intervalMs 経過で再取得され、kpiData が更新される（フェイクタイマー）", async () => {
    vi.useFakeTimers();
    mockedFetchKpiSummary
      .mockResolvedValueOnce(KPI)
      .mockResolvedValueOnce(KPI_UPDATED);

    const { result } = renderHook(() => useKpiPolling(5000));
    await act(async () => {});

    expect(mockedFetchKpiSummary).toHaveBeenCalledTimes(1);
    expect(result.current.kpiData?.totalSensors).toBe(10);

    act(() => {
      vi.advanceTimersByTime(5000);
    });
    await act(async () => {});

    expect(mockedFetchKpiSummary).toHaveBeenCalledTimes(2);
    expect(result.current.kpiData?.totalSensors).toBe(20);
    expect(result.current.isLoading).toBe(false);
  });

  it("取得失敗時は kpiData=null / isLoading=true（再スケルトン）", async () => {
    mockedFetchKpiSummary.mockRejectedValue(new Error("backend down"));

    const { result } = renderHook(() => useKpiPolling(5000));
    await act(async () => {});

    expect(result.current.kpiData).toBeNull();
    expect(result.current.isLoading).toBe(true);
  });

  it("成功後に失敗すると古い値を破棄し、次回成功で kpiData 復帰・isLoading=false", async () => {
    vi.useFakeTimers();
    mockedFetchKpiSummary
      .mockResolvedValueOnce(KPI)
      .mockRejectedValueOnce(new Error("down"))
      .mockResolvedValueOnce(KPI_UPDATED);

    const { result } = renderHook(() => useKpiPolling(5000));
    await act(async () => {});

    // T1: 初回成功
    expect(result.current.kpiData).toEqual(KPI);
    expect(result.current.isLoading).toBe(false);

    // T3: 失敗 → 値破棄・再スケルトン
    act(() => {
      vi.advanceTimersByTime(5000);
    });
    await act(async () => {});
    expect(result.current.kpiData).toBeNull();
    expect(result.current.isLoading).toBe(true);

    // T4: 次回成功 → 復帰
    act(() => {
      vi.advanceTimersByTime(5000);
    });
    await act(async () => {});
    expect(result.current.kpiData).toEqual(KPI_UPDATED);
    expect(result.current.isLoading).toBe(false);
  });

  it("アンマウントで clearInterval され、以後タイマーで再取得しない", async () => {
    vi.useFakeTimers();
    const { unmount } = renderHook(() => useKpiPolling(5000));
    await act(async () => {});

    unmount();
    mockedFetchKpiSummary.mockClear();
    act(() => {
      vi.advanceTimersByTime(15_000);
    });
    await act(async () => {});

    expect(mockedFetchKpiSummary).not.toHaveBeenCalled();
  });

  it("アンマウント後に in-flight が成功しても setState しない（cancelled ガード）", async () => {
    let resolveFn: (value: KpiSummary) => void = () => {};
    mockedFetchKpiSummary.mockImplementation(
      () =>
        new Promise<KpiSummary>((resolve) => {
          resolveFn = resolve;
        }),
    );

    const { result, unmount } = renderHook(() => useKpiPolling(5000));
    await act(async () => {});

    act(() => {
      unmount();
    });

    await act(async () => {
      resolveFn(KPI);
    });

    // 完了しても setState はされないため、状態は初期値のまま（クラッシュしない）
    expect(mockedFetchKpiSummary).toHaveBeenCalledTimes(1);
    expect(result.current.kpiData).toBeNull();
    expect(result.current.isLoading).toBe(true);
  });

  it("先発（古い）レスポンスが後発（新しい）レスポンスより遅延して解決しても、新しい値を上書きしない（アウトオブオーダーガード）", async () => {
    vi.useFakeTimers();
    let resolveFirst: (value: KpiSummary) => void = () => {};
    let resolveSecond: (value: KpiSummary) => void = () => {};

    mockedFetchKpiSummary
      .mockImplementationOnce(
        () =>
          new Promise<KpiSummary>((resolve) => {
            resolveFirst = resolve;
          }),
      )
      .mockImplementationOnce(
        () =>
          new Promise<KpiSummary>((resolve) => {
            resolveSecond = resolve;
          }),
      );

    const { result } = renderHook(() => useKpiPolling(5000));
    await act(async () => {}); // 1回目リクエスト in-flight

    act(() => {
      vi.advanceTimersByTime(5000);
    });
    await act(async () => {}); // 2回目リクエスト in-flight（1回目もまだ未解決）

    // 後発（新しい）が先に解決する
    await act(async () => {
      resolveSecond(KPI_UPDATED);
    });
    expect(result.current.kpiData).toEqual(KPI_UPDATED);

    // 先発（古い）が遅れて解決しても、新しい値を上書きしない
    await act(async () => {
      resolveFirst(KPI);
    });
    expect(result.current.kpiData).toEqual(KPI_UPDATED);
    expect(result.current.isLoading).toBe(false);
  });

  it("アンマウント後に in-flight が失敗しても setState しない（cancelled ガード）", async () => {
    let rejectFn: (error: Error) => void = () => {};
    mockedFetchKpiSummary.mockImplementation(
      () =>
        new Promise<KpiSummary>((_resolve, reject) => {
          rejectFn = reject;
        }),
    );

    const { result, unmount } = renderHook(() => useKpiPolling(5000));
    await act(async () => {});

    act(() => {
      unmount();
    });

    await act(async () => {
      rejectFn(new Error("late failure"));
    });

    expect(mockedFetchKpiSummary).toHaveBeenCalledTimes(1);
    expect(result.current.kpiData).toBeNull();
    expect(result.current.isLoading).toBe(true);
  });

  it("refresh() で即時再取得できる（シード投入・クリア直後の反映）", async () => {
    mockedFetchKpiSummary
      .mockResolvedValueOnce(KPI)
      .mockResolvedValueOnce(KPI_UPDATED);

    const { result } = renderHook(() => useKpiPolling(5000));
    await act(async () => {});

    expect(result.current.kpiData?.totalSensors).toBe(10);

    await act(async () => {
      await result.current.refresh();
    });

    expect(mockedFetchKpiSummary).toHaveBeenCalledTimes(2);
    expect(result.current.kpiData?.totalSensors).toBe(20);
  });

  it("refresh() 失敗時は古い値を破棄し、再スケルトンへ戻す", async () => {
    mockedFetchKpiSummary
      .mockResolvedValueOnce(KPI)
      .mockRejectedValueOnce(new Error("backend down"));

    const { result } = renderHook(() => useKpiPolling(5000));
    await act(async () => {});

    expect(result.current.kpiData).toEqual(KPI);

    await act(async () => {
      await result.current.refresh();
    });

    expect(result.current.kpiData).toBeNull();
    expect(result.current.isLoading).toBe(true);
  });

  it("アンマウント後の refresh() は setState しない（cancelled ガード）", async () => {
    mockedFetchKpiSummary.mockResolvedValue(KPI);

    const { result, unmount } = renderHook(() => useKpiPolling(5000));
    await act(async () => {});

    unmount();
    mockedFetchKpiSummary.mockClear();

    await act(async () => {
      await result.current.refresh();
    });

    expect(mockedFetchKpiSummary).not.toHaveBeenCalled();
  });
});
