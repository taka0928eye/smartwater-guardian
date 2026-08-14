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
import AlertDetailDrawer, {
  buildSpectrumData,
  buildWaveformData,
} from "../AlertDetailDrawer";

vi.mock("@/lib/api", () => ({
  fetchAlertDetail: vi.fn(),
  getAlertAudioUrl: vi.fn(
    (telemetryId: string) =>
      `http://localhost:8000/api/v1/alerts/${telemetryId}/audio`,
  ),
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
  hasAudio: false,
  waveform: [
    { timeMs: 0, amplitude: 0.1 },
    { timeMs: 500, amplitude: -0.2 },
  ],
  analysis: {
    leakConfidence: 88,
    severityLevel: 3,
    dominantFreqHz: 1200,
    bandEnergyRatio: 0.75,
    spectrum: [
      { freqHz: 500, magnitude: 0.1 },
      { freqHz: 1200, magnitude: 0.9 },
    ],
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
    expect(screen.getByTestId("alert-detail-drawer")).toHaveClass("z-[2000]");
    expect(screen.getAllByText("AI漏水スコア")).toHaveLength(1);
    expect(screen.getAllByText("88点")).toHaveLength(1);
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

  it("選択したアラートの実音響をWAVプレーヤーで再生できる", async () => {
    mockedFetchDetail.mockResolvedValue({
      ...DETAIL_WITH_PIPE,
      hasAudio: true,
    } as AlertDetail);

    render(<AlertDetailDrawer alert={ALERT} onClose={vi.fn()} />);

    const player = await screen.findByTestId("alert-audio-player");
    expect(player).toHaveAttribute("controls");
    expect(player).toHaveAttribute("preload", "metadata");
    expect(player).toHaveAttribute(
      "src",
      "http://localhost:8000/api/v1/alerts/t1/audio",
    );
    expect(screen.getByText("センサー実音響")).toBeInTheDocument();
  });

  it("音声がないアラートではプレーヤーを表示しない", async () => {
    mockedFetchDetail.mockResolvedValue({
      ...DETAIL_WITH_PIPE,
      hasAudio: false,
    } as AlertDetail);

    render(<AlertDetailDrawer alert={ALERT} onClose={vi.fn()} />);

    expect(await screen.findByText("音声データはありません")).toBeInTheDocument();
    expect(screen.queryByTestId("alert-audio-player")).not.toBeInTheDocument();
  });

  it("バックエンドの実スペクトルと実波形をチャート形式へ変換する", () => {
    expect(
      buildSpectrumData({
        ...DETAIL_WITH_PIPE.analysis!,
        spectrum: [{ freqHz: 625, magnitude: 4.2 }],
      }),
    ).toEqual([{ freqHz: 625, power: 4.2 }]);
    expect(buildWaveformData([{ timeMs: 125, amplitude: -0.25 }])).toEqual([
      { timeMs: 125, amplitude: -0.25 },
    ]);
  });

  it("閉じるボタンで onClose が呼ばれる", () => {
    mockedFetchDetail.mockResolvedValue(DETAIL_WITH_PIPE);
    const onClose = vi.fn();

    render(<AlertDetailDrawer alert={ALERT} onClose={onClose} />);
    fireEvent.click(screen.getByTestId("drawer-close"));

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
