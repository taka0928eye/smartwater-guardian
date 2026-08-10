// @vitest-environment jsdom
/**
 * FE-5: アラート詳細ドロワー（components/alert/AlertDetailDrawer.tsx）の TDD テスト。
 *
 * 解析結果・配管情報の表示、FE-4 チャート差込スロット（children）、取得失敗時の
 * エラー表示、閉じる操作を検証する。fetchAlertDetail（@/lib/api）はモックする。
 *
 * 実行: npm run test
 */
import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import type { AlertDetail, AlertSummary } from "@/types/api";
import AlertDetailDrawer from "../AlertDetailDrawer";

vi.mock("@/lib/api", () => ({
  fetchAlertDetail: vi.fn(),
}));

import { fetchAlertDetail } from "@/lib/api";

const mockedFetchDetail = vi.mocked(fetchAlertDetail);

/** テスト用の AlertSummary。 */
const ALERT: AlertSummary = {
  telemetryId: "t1",
  sensorId: "SNS-001",
  hydrantId: "HYD-001",
  severityLevel: 3,
  leakConfidence: 88,
  detectedAt: "2026-08-10T09:00:00Z",
};

/** 配管情報ありの詳細。 */
const DETAIL_WITH_PIPE: AlertDetail = {
  ...ALERT,
  location: { latitude: 35.7022, longitude: 139.7448 },
  analysis: {
    leakConfidence: 88,
    severityLevel: 3,
    dominantFreqHz: 1200,
    bandEnergyRatio: 0.75,
    spectrum: [],
  },
  pipeInfo: {
    pipeId: "P-001",
    material: "ductile_iron",
    diameterMm: 150,
    installedYear: 1990,
    burialDepthM: 1.2,
    ageYears: 36,
  },
};

describe("AlertDetailDrawer", () => {
  it("詳細取得成功後に解析結果と配管情報を表示する", async () => {
    mockedFetchDetail.mockResolvedValue(DETAIL_WITH_PIPE);

    render(<AlertDetailDrawer alert={ALERT} onClose={vi.fn()} />);

    expect(await screen.findByText("解析結果")).toBeInTheDocument();
    expect(screen.getByText("1200 Hz")).toBeInTheDocument();
    expect(screen.getByText("ductile_iron")).toBeInTheDocument();
    expect(mockedFetchDetail).toHaveBeenCalledWith("t1");
  });

  it("pipeInfo が null の場合は「配管台帳情報は未登録です」を表示する", async () => {
    mockedFetchDetail.mockResolvedValue({ ...DETAIL_WITH_PIPE, pipeInfo: null });

    render(<AlertDetailDrawer alert={ALERT} onClose={vi.fn()} />);

    expect(
      await screen.findByText("配管台帳情報は未登録です"),
    ).toBeInTheDocument();
  });

  it("取得失敗時は画面が壊れずエラーを表示する", async () => {
    mockedFetchDetail.mockRejectedValue(new Error("boom"));

    render(<AlertDetailDrawer alert={ALERT} onClose={vi.fn()} />);

    expect(await screen.findByTestId("detail-error")).toBeInTheDocument();
  });

  it("children（FE-4 チャート差込スロット）を描画する", async () => {
    mockedFetchDetail.mockResolvedValue(DETAIL_WITH_PIPE);

    render(
      <AlertDetailDrawer alert={ALERT} onClose={vi.fn()}>
        <div data-testid="chart-slot">スペクトルチャート</div>
      </AlertDetailDrawer>,
    );

    expect(await screen.findByTestId("chart-slot")).toBeInTheDocument();
  });

  it("閉じるボタンで onClose が呼ばれる", () => {
    mockedFetchDetail.mockResolvedValue(DETAIL_WITH_PIPE);
    const onClose = vi.fn();

    render(<AlertDetailDrawer alert={ALERT} onClose={onClose} />);
    fireEvent.click(screen.getByTestId("drawer-close"));

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
