// @vitest-environment jsdom
/**
 * FE-5: ダッシュボード本体（components/dashboard/DashboardClient.tsx）の TDD テスト。
 *
 * - マウント時にアラートを取得する
 * - 5秒ポーリングで再取得する（フェイクタイマー）
 * - アンマウント時に clearInterval（以後タイマーで再取得しない）
 * - 取得失敗時は画面が壊れず控えめなエラー表示に留まる
 * - 地図マーカー選択と一覧選択が同じ selectedAlertId を更新する（連動）
 *
 * Leaflet / next/dynamic に依存する SensorMap はモックし、AlertList / AlertDetailDrawer は
 * 実物を描画して連動を検証する。API は @/lib/api を丸ごとモックする。
 *
 * 実行: npm run test
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";

import type { AlertDetail, AlertSummary } from "@/types/api";
import type { DisasterSummary } from "@/types/disaster";
import type { SensorFeatureCollection } from "@/types/sensor";

// --- モック共通の記録領域（vi.mock より先に初期化されるため vi.hoisted） ---
const { captured } = vi.hoisted(() => ({
  captured: { sensorMapProps: [] as Record<string, unknown>[] },
}));

/** SensorMap のモック。props を記録しつつ、マーカークリック（onSelectMarker）と
 *  選択中 ID（selectedAlertId）をテストから操作できるようにする。 */
function SensorMapMock(props: Record<string, unknown>) {
  captured.sensorMapProps.push(props);
  const onSelectMarker = props.onSelectMarker as
    | ((sensorId: string) => void)
    | undefined;
  const selectedAlertId = (props.selectedAlertId as string | null) ?? null;
  return React.createElement(
    "div",
    { "data-testid": "sensor-map" },
    React.createElement(
      "button",
      { "data-testid": "map-marker", onClick: () => onSelectMarker?.("SNS-001") },
      "マーカー",
    ),
    React.createElement(
      "span",
      { "data-testid": "map-selected-id" },
      selectedAlertId === null ? "null" : selectedAlertId,
    ),
  );
}

vi.mock("@/components/map/SensorMap", () => ({
  default: SensorMapMock,
}));

vi.mock("@/lib/api", () => ({
  fetchAlerts: vi.fn(),
  fetchAlertDetail: vi.fn(),
  getAlertAudioUrl: vi.fn(
    (telemetryId: string) =>
      `http://localhost:8000/api/v1/alerts/${telemetryId}/audio`,
  ),
  // FE-7: DashboardClient が useKpiPolling 経由で呼ぶ。既存テストを壊さないよう
  // デフォルトで BE-8 契約の解決値を返す（FE-7 のカード描画用）。
  fetchKpiSummary: vi.fn().mockResolvedValue({
    totalSensors: 10,
    level1Count: 8,
    level2Count: 3,
    level3Count: 1,
    estimatedCostSavedYen: 2048400,
    isEstimate: true,
    assumptionDoc: "docs/business-model.md",
  }),
  // FE-3/FE-5 統合: DashboardClient が useSensorPolling 経由で呼ぶ。デフォルトで
  // FEATURES の値を返す（ポーリング同期の基本ケースをカバー）。
  fetchSensorsGeoJson: vi.fn().mockResolvedValue({
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
  }),
  // BE-7: DashboardClient が useDisasterSummary 経由で呼ぶ。既存テストを壊さないよう
  // デフォルトで空クラスタ（0 件）を返す（オーバーレイ非表示）。
  fetchDisasterSummary: vi.fn().mockResolvedValue({
    totalClusters: 0,
    totalAffectedHouseholds: 0,
    clusters: [],
  }),
  // BE-7: 防災シミュレーションボタンで呼ぶ。デフォルトは未解決（テストごとに設定）。
  simulateDisaster: vi.fn(),
}));

// --- API モックの参照（vi.mock の後で取得する） ---
import {
  fetchAlertDetail,
  fetchAlerts,
  fetchDisasterSummary,
  fetchKpiSummary,
  fetchSensorsGeoJson,
  simulateDisaster,
} from "@/lib/api";
import DashboardClient from "../DashboardClient";

const mockedFetchAlerts = vi.mocked(fetchAlerts);
const mockedFetchAlertDetail = vi.mocked(fetchAlertDetail);
const mockedFetchKpiSummary = vi.mocked(fetchKpiSummary);
const mockedFetchSensorsGeoJson = vi.mocked(fetchSensorsGeoJson);
const mockedFetchDisasterSummary = vi.mocked(fetchDisasterSummary);
const mockedSimulateDisaster = vi.mocked(simulateDisaster);

/** DashboardClient に渡す最小の GeoJSON（FE-3 型）。 */
const FEATURES: SensorFeatureCollection = {
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

/** テスト用の AlertSummary を生成する（渡した値で上書き可能）。 */
function makeAlert(overrides: Partial<AlertSummary>): AlertSummary {
  return {
    telemetryId: "t1",
    sensorId: "SNS-001",
    hydrantId: "HYD-001",
    severityLevel: 1,
    leakConfidence: 55,
    detectedAt: "2026-08-10T06:00:00Z",
    ...overrides,
  };
}

const ALERTS: AlertSummary[] = [
  makeAlert({
    telemetryId: "t1",
    sensorId: "SNS-001",
    hydrantId: "HYD-001",
    severityLevel: 3,
    leakConfidence: 88,
    detectedAt: "2026-08-10T09:00:00Z",
  }),
  makeAlert({
    telemetryId: "t2",
    sensorId: "SNS-002",
    hydrantId: "HYD-002",
    severityLevel: 1,
    leakConfidence: 40,
    detectedAt: "2026-08-10T08:00:00Z",
  }),
];

/** fetchAlertDetail のモック戻り値（t1 用）。 */
const DETAIL: AlertDetail = {
  ...ALERTS[0]!,
  location: { latitude: 35.7022, longitude: 139.7448 },
  hasAudio: false,
  waveform: [],
  analysis: {
    leakConfidence: 88,
    severityLevel: 3,
    dominantFreqHz: 1200,
    bandEnergyRatio: 0.75,
    spectrum: [],
  },
  pipeInfo: null,
};

/** KPI ポーリングのモック戻り値（BE-8 契約・ADR-003）。 */
const KPI = {
  totalSensors: 10,
  level1Count: 8,
  level2Count: 3,
  level3Count: 1,
  estimatedCostSavedYen: 2048400,
  isEstimate: true,
  assumptionDoc: "docs/business-model.md",
};

afterEach(() => {
  vi.useRealTimers();
  vi.clearAllMocks();
  captured.sensorMapProps.length = 0;
});

describe("DashboardClient", () => {
  it("マウント時にアラートを取得し、一覧に表示する", async () => {
    mockedFetchAlerts.mockResolvedValue(ALERTS);

    render(<DashboardClient sensorFeatures={FEATURES} />);

    expect(await screen.findAllByTestId("alert-row")).toHaveLength(2);
    expect(mockedFetchAlerts).toHaveBeenCalledTimes(1);
  });

  it("5秒経過で再取得する（フェイクタイマー）", async () => {
    vi.useFakeTimers();
    mockedFetchAlerts.mockResolvedValue(ALERTS);

    render(<DashboardClient sensorFeatures={FEATURES} />);
    await act(async () => {});

    expect(mockedFetchAlerts).toHaveBeenCalledTimes(1);

    act(() => {
      vi.advanceTimersByTime(5000);
    });
    await act(async () => {});

    expect(mockedFetchAlerts).toHaveBeenCalledTimes(2);
  });

  it("アンマウント時にクリーンアップされ、以後タイマーで再取得しない", async () => {
    vi.useFakeTimers();
    mockedFetchAlerts.mockResolvedValue(ALERTS);

    const { unmount } = render(<DashboardClient sensorFeatures={FEATURES} />);
    await act(async () => {});

    expect(mockedFetchAlerts).toHaveBeenCalledTimes(1);

    unmount();
    mockedFetchAlerts.mockClear();
    act(() => {
      vi.advanceTimersByTime(15_000);
    });
    await act(async () => {});

    expect(mockedFetchAlerts).not.toHaveBeenCalled();
  });

  it("取得失敗時は画面が壊れず、控えめなエラー表示に留まる", async () => {
    mockedFetchAlerts.mockRejectedValue(new Error("backend down"));

    render(<DashboardClient sensorFeatures={FEATURES} />);

    expect(await screen.findByText(/取得に失敗/)).toBeInTheDocument();
    // 地図・一覧（空状態）は壊れず表示される
    expect(screen.getByTestId("sensor-map")).toBeInTheDocument();
    expect(screen.getByTestId("alert-empty")).toBeInTheDocument();
  });

  it("地図マーカー選択と一覧選択が同じ selectedAlertId を更新する（連動）", async () => {
    mockedFetchAlerts.mockResolvedValue(ALERTS);
    mockedFetchAlertDetail.mockResolvedValue(DETAIL);

    render(<DashboardClient sensorFeatures={FEATURES} />);
    await screen.findAllByTestId("alert-row");

    // 初期状態では選択なし
    expect(captured.sensorMapProps.at(-1)?.selectedAlertId).toBeNull();

    // 地図マーカークリック（SNS-001）→ 対応するアラート t1 が選択され、ドロワーが開く
    fireEvent.click(screen.getByTestId("map-marker"));
    expect(await screen.findByTestId("alert-detail-drawer")).toBeInTheDocument();
    expect(captured.sensorMapProps.at(-1)?.selectedAlertId).toBe("t1");

    // 一覧の別行クリック → 同じ selectedAlertId が更新される（地図側にも反映）
    const t2Row = screen
      .getAllByTestId("alert-row")
      .find((row) => row.getAttribute("data-alert-id") === "t2");
    expect(t2Row).toBeDefined();
    fireEvent.click(t2Row!);
    await waitFor(() =>
      expect(captured.sensorMapProps.at(-1)?.selectedAlertId).toBe("t2"),
    );
  });

  it("KPI セクションのランドマーク（section[aria-labelledby]/h2/aria-busy）を所有する", async () => {
    mockedFetchKpiSummary.mockResolvedValue(KPI);
    mockedFetchAlerts.mockResolvedValue(ALERTS);

    render(<DashboardClient sensorFeatures={FEATURES} />);
    const section = screen.getByRole("region", { name: "KPI サマリ" });
    expect(section).toHaveAttribute("aria-labelledby", "kpi-summary-title");
    expect(
      screen.getByRole("heading", { level: 2, name: "KPI サマリ" }),
    ).toHaveAttribute("id", "kpi-summary-title");

    // 取得成功後は aria-busy=false（スケルトン中は true）
    await waitFor(() => expect(section).toHaveAttribute("aria-busy", "false"));
  });

  it("KPI: 初回スケルトン → 成功でカードグリッドへ切り替わる", async () => {
    mockedFetchKpiSummary.mockResolvedValue(KPI);
    mockedFetchAlerts.mockResolvedValue(ALERTS);

    render(<DashboardClient sensorFeatures={FEATURES} />);
    // 初回はスケルトン（h2 とランドマークは維持される）
    expect(screen.getByTestId("kpi-skeleton")).toBeInTheDocument();
    expect(
      screen.getByRole("region", { name: "KPI サマリ" }),
    ).toHaveAttribute("aria-busy", "true");

    // 成功後はカードグリッドへ切り替わり、スケルトンは消える
    expect(await screen.findByTestId("kpi-card-sensors")).toBeInTheDocument();
    expect(screen.queryByTestId("kpi-skeleton")).not.toBeInTheDocument();
  });

  it("KPI セクションに aria-live=\"polite\" を設定し、更新をスクリーンリーダーへ通知する", async () => {
    mockedFetchKpiSummary.mockResolvedValue(KPI);
    mockedFetchAlerts.mockResolvedValue(ALERTS);

    render(<DashboardClient sensorFeatures={FEATURES} />);
    const section = screen.getByRole("region", { name: "KPI サマリ" });
    expect(section).toHaveAttribute("aria-live", "polite");
  });

  it("KPI: ポーリング失敗時は再スケルトン（stale 値非表示）", async () => {
    vi.useFakeTimers();
    mockedFetchKpiSummary
      .mockResolvedValueOnce(KPI)
      .mockRejectedValueOnce(new Error("backend down"));
    mockedFetchAlerts.mockResolvedValue(ALERTS);

    render(<DashboardClient sensorFeatures={FEATURES} />);
    await act(async () => {});

    // 初回成功 → カード表示
    expect(screen.getByTestId("kpi-card-sensors")).toBeInTheDocument();

    // 5 秒後のポーリング失敗 → 再スケルトン（古い値を最新として見せない）
    act(() => {
      vi.advanceTimersByTime(5000);
    });
    await act(async () => {});

    expect(screen.getByTestId("kpi-skeleton")).toBeInTheDocument();
    expect(screen.queryByTestId("kpi-card-sensors")).not.toBeInTheDocument();
  });

  it("地図マーカーが同じ5秒間隔でポーリングされ、漏水判定の新しい色が反映される", async () => {
    vi.useFakeTimers();
    mockedFetchAlerts.mockResolvedValue(ALERTS);
    // FEATURES（Level 1）で初回ポーリング、その後 Level 3 の更新を返す
    mockedFetchSensorsGeoJson
      .mockResolvedValueOnce(FEATURES)
      .mockResolvedValueOnce({
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
      });

    render(<DashboardClient sensorFeatures={FEATURES} />);
    await act(async () => {});

    // 初回ポーリングは FEATURES（Level 1）の状態で地図が表示される
    expect(mockedFetchSensorsGeoJson).toHaveBeenCalledTimes(1);
    const mapProps1 = captured.sensorMapProps.at(-1) as {
      data: SensorFeatureCollection;
    };
    expect(mapProps1.data.features[0]?.properties.severityLevel).toBe(1);

    // 5 秒後のポーリングで新しい GeoJSON（Level 3）が取得され、SensorMap へ渡される
    act(() => {
      vi.advanceTimersByTime(5000);
    });
    await act(async () => {});

    expect(mockedFetchSensorsGeoJson).toHaveBeenCalledTimes(2);
    const mapProps2 = captured.sensorMapProps.at(-1) as {
      data: SensorFeatureCollection;
    };
    expect(mapProps2.data.features[0]?.properties.severityLevel).toBe(3);
  });

  it("「正常も表示」トグルが機能する: Level 0 のアラートが非表示→表示→非表示に切り替わる", async () => {
    mockedFetchAlerts.mockResolvedValue([
      ALERTS[0]!,
      ALERTS[1]!,
      {
        telemetryId: "t0",
        sensorId: "SNS-000",
        hydrantId: "HYD-000",
        severityLevel: 0,
        leakConfidence: 0,
        detectedAt: "2026-08-10T07:00:00Z",
      },
    ]);

    render(<DashboardClient sensorFeatures={FEATURES} />);
    await screen.findAllByTestId("alert-row");

    // 初期状態: Level 0 は非表示（3行 Level 3/1 のみ表示）
    const rows = screen.getAllByTestId("alert-row");
    expect(rows).toHaveLength(2);
    expect(rows.every((row) => {
      const alertId = row.getAttribute("data-alert-id");
      return alertId === "t1" || alertId === "t2";
    })).toBe(true);

    // チェックボックスを ON → Level 0 が表示される
    const toggle = screen.getByTestId("show-level0-toggle");
    fireEvent.click(toggle);
    expect((toggle as HTMLInputElement).checked).toBe(true);
    const rowsWithLevel0 = screen.getAllByTestId("alert-row");
    expect(rowsWithLevel0).toHaveLength(3);
    expect(
      rowsWithLevel0.some((row) => row.getAttribute("data-alert-id") === "t0"),
    ).toBe(true);

    // 再度クリック → Level 0 が非表示に戻る
    fireEvent.click(toggle);
    expect((toggle as HTMLInputElement).checked).toBe(false);
    const rowsWithoutLevel0 = screen.getAllByTestId("alert-row");
    expect(rowsWithoutLevel0).toHaveLength(2);
    expect(
      rowsWithoutLevel0.some((row) => row.getAttribute("data-alert-id") === "t0"),
    ).toBe(false);
  });
});

describe("防災モード（BE-7）", () => {
  /** BE-7 契約フィクスチャ（クラスタ 1 件・世帯数 170）。 */
  const DISASTER_SUMMARY: DisasterSummary = {
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
              [139.7691, 35.6832],
              [139.7671, 35.6812],
            ],
          ],
        },
      },
    ],
  };

  it("初期表示では SensorMap の disasterSummary が空（0 クラスタ）である", async () => {
    mockedFetchAlerts.mockResolvedValue(ALERTS);

    render(<DashboardClient sensorFeatures={FEATURES} />);
    await act(async () => {});

    // 初回ポーリングで空クラスタが取得され、SensorMap へ渡る
    const props = captured.sensorMapProps.at(-1) as {
      disasterSummary?: { totalClusters: number } | null;
    };
    expect(props.disasterSummary?.totalClusters).toBe(0);
    // 防災シミュレーションボタンが表示される
    expect(
      screen.getByTestId("disaster-simulate-button"),
    ).toHaveTextContent("防災シミュレーション");
  });

  it("防災シミュレーションボタンで simulate API（count=6）が呼ばれ、クラスタが地図に反映される", async () => {
    mockedFetchAlerts.mockResolvedValue(ALERTS);
    mockedFetchDisasterSummary.mockResolvedValue(DISASTER_SUMMARY);
    mockedSimulateDisaster.mockResolvedValue({
      insertedCount: 6,
      message: "震災モードシミュレーション: Level 3 アラートを 6 件一括追加しました",
    });

    render(<DashboardClient sensorFeatures={FEATURES} />);
    await act(async () => {});

    fireEvent.click(screen.getByTestId("disaster-simulate-button"));

    // simulate API が固定件数（DISASTER_SIMULATE_COUNT = 6）で呼ばれる
    await waitFor(() => expect(mockedSimulateDisaster).toHaveBeenCalledWith(6));

    // simulate 後の refresh で fetchDisasterSummary が再取得され、SensorMap へクラスタが渡る
    await waitFor(() => {
      const props = captured.sensorMapProps.at(-1) as {
        disasterSummary?: { totalClusters: number } | null;
      };
      expect(props.disasterSummary?.totalClusters).toBe(1);
    });

    // 成功メッセージが表示される
    expect(screen.getByTestId("disaster-simulate-message")).toHaveTextContent(
      /6 件/,
    );
  });

  it("シミュレーション中はボタンが disabled になり「シミュレーション中…」を表示する", async () => {
    mockedFetchAlerts.mockResolvedValue(ALERTS);
    // simulate を保留させ、pending 中のボタン表示を検証する
    let resolveSimulate!: (value: {
      insertedCount: number;
      message: string;
    }) => void;
    mockedSimulateDisaster.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveSimulate = resolve;
        }),
    );

    render(<DashboardClient sensorFeatures={FEATURES} />);
    await act(async () => {});

    const button = screen.getByTestId("disaster-simulate-button");
    fireEvent.click(button);

    expect(button).toBeDisabled();
    expect(button).toHaveTextContent("シミュレーション中…");

    // 保留を解決して終了
    await act(async () => {
      resolveSimulate({
        insertedCount: 6,
        message: "震災モードシミュレーション: Level 3 アラートを 6 件一括追加しました",
      });
    });
  });

  it("simulate 失敗時は控えめなエラー表示に留まり、画面は壊れない", async () => {
    mockedFetchAlerts.mockResolvedValue(ALERTS);
    mockedSimulateDisaster.mockRejectedValue(new Error("backend down"));

    render(<DashboardClient sensorFeatures={FEATURES} />);
    await act(async () => {});

    fireEvent.click(screen.getByTestId("disaster-simulate-button"));

    expect(
      await screen.findByTestId("disaster-simulate-error"),
    ).toHaveTextContent("防災シミュレーションに失敗しました");
    // 地図は壊れず表示される
    expect(screen.getByTestId("sensor-map")).toBeInTheDocument();
  });

  it("被災エリア取得失敗時は控えめにエラー表示し、画面は壊れない", async () => {
    mockedFetchAlerts.mockResolvedValue(ALERTS);
    mockedFetchDisasterSummary.mockRejectedValue(new Error("down"));

    render(<DashboardClient sensorFeatures={FEATURES} />);

    expect(await screen.findByTestId("disaster-error")).toHaveTextContent(
      "被災エリアの取得に失敗しました",
    );
    expect(screen.getByTestId("sensor-map")).toBeInTheDocument();
  });
});
