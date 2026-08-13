// @vitest-environment jsdom
/**
 * BE-7: 防災モードポーリングフック（src/hooks/useDisasterSummary.ts）の TDD テスト。
 *
 * - マウント直後に fetchDisasterSummary を即時呼び出し、成功で disasterSummary をセット
 * - intervalMs 経過で再取得し、disasterSummary を更新する（フェイクタイマー）
 * - 取得失敗時は最終状態を据え置き（null のまま）、控えめに error を表示する
 * - 失敗→次回成功で disasterSummary 復帰・error クリア
 * - refresh() で即時再取得できる（simulate 直後のクラスタ反映に使う）
 * - アンマウントで cancelled + clearInterval（以後 setState / 再取得しない）
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import { act, renderHook } from "@testing-library/react";

import type { DisasterSummary } from "@/types/disaster";

vi.mock("@/lib/api", () => ({
  fetchDisasterSummary: vi.fn(),
}));

import { fetchDisasterSummary } from "@/lib/api";
import { useDisasterSummary } from "../useDisasterSummary";

const mockedFetchDisasterSummary = vi.mocked(fetchDisasterSummary);

/** BE-7 契約フィクスチャ（クラスタ 1 件・世帯数 170）。 */
const SUMMARY: DisasterSummary = {
  totalClusters: 1,
  totalAffectedHouseholds: 170,
  clusters: [
    {
      clusterId: "CLS-001",
      centerLat: 35.6812,
      centerLng: 139.7671,
      affectedSensorIds: ["SEN-DISASTER-001"],
      affectedPipeIds: ["PIPE-1"],
      estimatedHouseholds: 170,
      priorityValveHydrantId: "HYD-001",
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [139.7671, 35.6812],
            [139.7671, 35.6812],
          ],
        ],
      },
    },
  ],
};

/** クラスタが追加された更新版。 */
const SUMMARY_UPDATED: DisasterSummary = {
  ...SUMMARY,
  totalClusters: 2,
  totalAffectedHouseholds: 340,
};

afterEach(() => {
  vi.useRealTimers();
  vi.clearAllMocks();
});

describe("useDisasterSummary", () => {
  it("マウント直後に fetchDisasterSummary を呼び、成功で disasterSummary をセットする", async () => {
    mockedFetchDisasterSummary.mockResolvedValue(SUMMARY);

    const { result } = renderHook(() => useDisasterSummary(5000));
    await act(async () => {});

    expect(mockedFetchDisasterSummary).toHaveBeenCalledTimes(1);
    expect(result.current.disasterSummary).toEqual(SUMMARY);
    expect(result.current.error).toBeNull();
  });

  it("intervalMs 経過で再取得され、disasterSummary が更新される（フェイクタイマー）", async () => {
    vi.useFakeTimers();
    mockedFetchDisasterSummary
      .mockResolvedValueOnce(SUMMARY)
      .mockResolvedValueOnce(SUMMARY_UPDATED);

    const { result } = renderHook(() => useDisasterSummary(5000));
    await act(async () => {});

    expect(mockedFetchDisasterSummary).toHaveBeenCalledTimes(1);
    expect(result.current.disasterSummary?.totalClusters).toBe(1);

    act(() => {
      vi.advanceTimersByTime(5000);
    });
    await act(async () => {});

    expect(mockedFetchDisasterSummary).toHaveBeenCalledTimes(2);
    expect(result.current.disasterSummary?.totalClusters).toBe(2);
  });

  it("取得失敗時は最終状態を据え置き（null のまま）、error を表示する", async () => {
    mockedFetchDisasterSummary.mockRejectedValue(new Error("backend down"));

    const { result } = renderHook(() => useDisasterSummary(5000));
    await act(async () => {});

    expect(result.current.disasterSummary).toBeNull();
    expect(result.current.error).toBe("被災エリアの取得に失敗しました");
  });

  it("成功後に失敗しても直前の値を破棄せず据え置き、次回成功で復帰する", async () => {
    vi.useFakeTimers();
    mockedFetchDisasterSummary
      .mockResolvedValueOnce(SUMMARY)
      .mockRejectedValueOnce(new Error("down"))
      .mockResolvedValueOnce(SUMMARY_UPDATED);

    const { result } = renderHook(() => useDisasterSummary(5000));
    await act(async () => {});

    // 初回成功
    expect(result.current.disasterSummary).toEqual(SUMMARY);

    // 2 回目は失敗 → 直前の値を据え置き
    act(() => {
      vi.advanceTimersByTime(5000);
    });
    await act(async () => {});
    expect(result.current.disasterSummary).toEqual(SUMMARY);
    expect(result.current.error).toBe("被災エリアの取得に失敗しました");

    // 3 回目は成功 → 値復帰・error クリア
    act(() => {
      vi.advanceTimersByTime(5000);
    });
    await act(async () => {});
    expect(result.current.disasterSummary?.totalClusters).toBe(2);
    expect(result.current.error).toBeNull();
  });

  it("refresh() で即時再取得できる（simulate 直後のクラスタ反映）", async () => {
    mockedFetchDisasterSummary
      .mockResolvedValueOnce(SUMMARY)
      .mockResolvedValueOnce(SUMMARY_UPDATED);

    const { result } = renderHook(() => useDisasterSummary(5000));
    await act(async () => {});

    expect(result.current.disasterSummary?.totalClusters).toBe(1);

    await act(async () => {
      await result.current.refresh();
    });

    expect(mockedFetchDisasterSummary).toHaveBeenCalledTimes(2);
    expect(result.current.disasterSummary?.totalClusters).toBe(2);
  });

  it("アンマウント後は cancelled で以後 setState / 再取得しない", async () => {
    vi.useFakeTimers();
    mockedFetchDisasterSummary.mockResolvedValue(SUMMARY);

    const { unmount } = renderHook(() => useDisasterSummary(5000));
    await act(async () => {});

    unmount();
    // アンマウント後のタイマー発火で再取得しない
    act(() => {
      vi.advanceTimersByTime(10_000);
    });

    expect(mockedFetchDisasterSummary).toHaveBeenCalledTimes(1);
  });
});
