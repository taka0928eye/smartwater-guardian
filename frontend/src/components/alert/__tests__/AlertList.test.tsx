// @vitest-environment jsdom
/**
 * FE-5: アラート一覧（components/alert/AlertList.tsx）の TDD テスト。
 *
 * - 深刻度降順 → 検知時刻降順のソート
 * - Level 0（正常）の既定非表示と「正常も表示」トグル
 * - Level 3 行の強調スタイル
 * - 行クリックで onSelect(alertId) が呼ばれる
 * - アラート0件時の空状態メッセージ
 *
 * 実行: npm run test
 */
import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import type { AlertSummary } from "@/types/api";
import AlertList from "../AlertList";

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

/** 指定 telemetryId の行要素を返す。無ければ null。 */
function alertRow(id: string): HTMLElement | null {
  return (
    screen
      .queryAllByTestId("alert-row")
      .find((row) => row.getAttribute("data-alert-id") === id) ?? null
  );
}

/** DOM 上の行を先頭から順に telemetryId の配列で返す。 */
function renderedAlertIds(): string[] {
  return screen
    .getAllByTestId("alert-row")
    .map((row) => row.getAttribute("data-alert-id") ?? "");
}

describe("AlertList", () => {
  it("深刻度降順 → 検知時刻降順にソートして表示する", () => {
    render(
      <AlertList
        alerts={[
          makeAlert({
            telemetryId: "t1",
            severityLevel: 1,
            detectedAt: "2026-08-10T06:00:00Z",
          }),
          makeAlert({
            telemetryId: "t3",
            severityLevel: 3,
            detectedAt: "2026-08-10T07:00:00Z",
          }),
          makeAlert({
            telemetryId: "t2",
            severityLevel: 2,
            detectedAt: "2026-08-10T09:00:00Z",
          }),
        ]}
        selectedAlertId={null}
        onSelect={vi.fn()}
      />,
    );
    // Level 3 → Level 2 → Level 1 の順になる
    expect(renderedAlertIds()).toEqual(["t3", "t2", "t1"]);
  });

  it("同じ深刻度内では検知時刻が新しい順に並ぶ", () => {
    render(
      <AlertList
        alerts={[
          makeAlert({
            telemetryId: "t1",
            severityLevel: 3,
            detectedAt: "2026-08-10T08:00:00Z",
          }),
          makeAlert({
            telemetryId: "t2",
            severityLevel: 3,
            detectedAt: "2026-08-10T09:00:00Z",
          }),
        ]}
        selectedAlertId={null}
        onSelect={vi.fn()}
      />,
    );
    expect(renderedAlertIds()).toEqual(["t2", "t1"]);
  });

  it("Level 0（正常）は既定で一覧に表示されない", () => {
    render(
      <AlertList
        alerts={[
          makeAlert({ telemetryId: "t1", severityLevel: 1 }),
          makeAlert({ telemetryId: "t0", severityLevel: 0 }),
        ]}
        selectedAlertId={null}
        onSelect={vi.fn()}
      />,
    );
    expect(alertRow("t0")).toBeNull();
    expect(renderedAlertIds()).toEqual(["t1"]);
  });

  it("「正常も表示」トグルをONにすると Level 0 が表示される", () => {
    render(
      <AlertList
        alerts={[
          makeAlert({ telemetryId: "t1", severityLevel: 1 }),
          makeAlert({ telemetryId: "t0", severityLevel: 0 }),
        ]}
        selectedAlertId={null}
        onSelect={vi.fn()}
      />,
    );
    expect(alertRow("t0")).toBeNull();

    fireEvent.click(screen.getByTestId("show-level0-toggle"));

    expect(alertRow("t0")).not.toBeNull();
  });

  it("Level 3 の行に強調スタイルが付く", () => {
    render(
      <AlertList
        alerts={[
          makeAlert({ telemetryId: "t3", severityLevel: 3 }),
          makeAlert({ telemetryId: "t1", severityLevel: 1 }),
        ]}
        selectedAlertId={null}
        onSelect={vi.fn()}
      />,
    );
    expect(alertRow("t3")).toHaveClass("border-red-500");
    expect(alertRow("t1")).not.toHaveClass("border-red-500");
  });

  it("行クリックで onSelect(alertId) が呼ばれる", () => {
    const onSelect = vi.fn();
    render(
      <AlertList
        alerts={[makeAlert({ telemetryId: "t2", severityLevel: 2 })]}
        selectedAlertId={null}
        onSelect={onSelect}
      />,
    );
    fireEvent.click(alertRow("t2")!);
    expect(onSelect).toHaveBeenCalledWith("t2");
    expect(screen.getByText("55点")).toBeInTheDocument();
  });

  it("アラート0件時は例外にならず空状態メッセージを表示する", () => {
    render(<AlertList alerts={[]} selectedAlertId={null} onSelect={vi.fn()} />);
    expect(screen.getByText("アラートはありません")).toBeInTheDocument();
  });

  it("アラート一覧がスクロール可能な状態（overflow-y-auto と max-h-80）で描画される", () => {
    render(
      <AlertList
        alerts={[
          makeAlert({ telemetryId: "t1" }),
          makeAlert({ telemetryId: "t2" }),
          makeAlert({ telemetryId: "t3" }),
        ]}
        selectedAlertId={null}
        onSelect={vi.fn()}
      />,
    );
    const alertList = screen.getByRole("list");
    expect(alertList).toHaveClass("overflow-y-auto");
    expect(alertList).toHaveClass("max-h-80");
  });
});
