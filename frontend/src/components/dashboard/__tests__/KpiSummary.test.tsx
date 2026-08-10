// @vitest-environment jsdom
/**
 * FE-2: KPI サマリ（components/dashboard/KpiSummary.tsx）の TDD テスト。
 *
 * 5枚のKPIカード（監視センサー数 / Level 3 破裂リスク / Level 2 警告 /
 * 本日の検知数 / 推定削減コスト）の表示内容・数値フォーマット・
 * 深刻度強調クラスを検証する。UI-1 のワイヤーフレーム・デモ数値に準拠する。
 */
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import KpiSummary, { formatManYen } from "../KpiSummary";
import type { KpiData } from "../KpiSummary";

/** UI-1 デモシナリオの数値（監視センサー数 1,240 台 / L3:1件 / L2:3件 / 本日12件 / 削減 ¥1,420,000）。 */
const BASE_KPI: KpiData = {
  totalSensors: 1240,
  level3Count: 1,
  level2Count: 3,
  todayDetections: 12,
  estimatedCostSavedYen: 1420000,
};

describe("formatManYen", () => {
  it("円を万円表記へ自動フォーマットする", () => {
    expect(formatManYen(1420000)).toBe("142万円");
    expect(formatManYen(12000)).toBe("1.2万円");
    expect(formatManYen(0)).toBe("0万円");
  });
});

describe("KpiSummary", () => {
  it("5枚のカードラベルを描画する", () => {
    render(<KpiSummary kpiData={BASE_KPI} />);
    expect(screen.getByText("監視センサー数")).toBeInTheDocument();
    expect(screen.getByText("Level 3 破裂リスク")).toBeInTheDocument();
    expect(screen.getByText("Level 2 警告")).toBeInTheDocument();
    expect(screen.getByText("本日の検知数")).toBeInTheDocument();
    expect(screen.getByText("推定削減コスト")).toBeInTheDocument();
  });

  it("監視センサー数を桁区切り（1,240）と単位（台）で表示する", () => {
    render(<KpiSummary kpiData={BASE_KPI} />);
    const card = screen.getByTestId("kpi-card-sensors");
    expect(card).toHaveTextContent("1,240");
    expect(card).toHaveTextContent("台");
  });

  it("Level 3 件数・Level 2 件数・本日検知数を表示する", () => {
    render(<KpiSummary kpiData={BASE_KPI} />);
    expect(screen.getByTestId("kpi-card-level3")).toHaveTextContent("1");
    expect(screen.getByTestId("kpi-card-level2")).toHaveTextContent("3");
    expect(screen.getByTestId("kpi-card-today")).toHaveTextContent("12");
  });

  it("推定削減コストを万円表記（142万円）で表示する", () => {
    render(<KpiSummary kpiData={BASE_KPI} />);
    expect(screen.getByTestId("kpi-card-cost")).toHaveTextContent("142万円");
  });

  it("Level 3 カードは赤系、Level 2 カードは黄系で強調される", () => {
    render(<KpiSummary kpiData={BASE_KPI} />);
    expect(screen.getByTestId("kpi-card-level3").className).toContain("red");
    expect(screen.getByTestId("kpi-card-level2").className).toContain("amber");
  });

  it("値がすべて 0 でも各カードに 0 が表示される", () => {
    render(
      <KpiSummary
        kpiData={{
          totalSensors: 0,
          level3Count: 0,
          level2Count: 0,
          todayDetections: 0,
          estimatedCostSavedYen: 0,
        }}
      />,
    );
    expect(screen.getByTestId("kpi-card-sensors")).toHaveTextContent("0");
    expect(screen.getByTestId("kpi-card-level3")).toHaveTextContent("0");
    expect(screen.getByTestId("kpi-card-level2")).toHaveTextContent("0");
    expect(screen.getByTestId("kpi-card-today")).toHaveTextContent("0");
    expect(screen.getByTestId("kpi-card-cost")).toHaveTextContent("0万円");
  });
});
