// @vitest-environment jsdom
/**
 * FE-7: KPI サマリ（components/dashboard/KpiSummary.tsx）の TDD テスト。
 *
 * 5枚のKPIカード（監視センサー数 / Level 3 破裂リスク / Level 2 警告 /
 * Level 1 微小漏水（AI検知） / 推定削減コスト）を降順で描画し、
 * コストカードに「試算値」注記を常時表示することを検証する。
 * 値は実データ（BE-8 契約）由来で、固定のモック値ではない。
 */
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { getSeverityMeta } from "@/lib/severity";
import type { KpiSummary as KpiSummaryData } from "@/types/api";
import KpiSummary, { formatManYen } from "../KpiSummary";

/** BE-8 契約フィクスチャ（ADR-003: totalSensors 10 / L1:8 / L2:3 / L3:1 / ¥2,048,400）。 */
const BASE_KPI: KpiSummaryData = {
  totalSensors: 10,
  level3Count: 1,
  level2Count: 3,
  level1Count: 8,
  estimatedCostSavedYen: 2048400,
  isEstimate: true,
  assumptionDoc: "docs/business-model.md",
};

describe("formatManYen", () => {
  it("円を万円表記へ自動フォーマットする", () => {
    expect(formatManYen(2048400)).toBe("204.8万円");
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
    expect(screen.getByText("Level 1 微小漏水（AI検知）")).toBeInTheDocument();
    expect(screen.getByText("推定削減コスト")).toBeInTheDocument();
  });

  it("5カードを降順（sensors → level3 → level2 → level1 → cost）で描画する", () => {
    const { container } = render(<KpiSummary kpiData={BASE_KPI} />);
    const cards = container.querySelectorAll('[data-testid^="kpi-card-"]');
    expect(Array.from(cards, (el) => el.getAttribute("data-testid"))).toEqual([
      "kpi-card-sensors",
      "kpi-card-level3",
      "kpi-card-level2",
      "kpi-card-level1",
      "kpi-card-cost",
    ]);
  });

  it("監視センサー数を桁区切り（2,048）+ 単位（台）で表示する", () => {
    render(<KpiSummary kpiData={{ ...BASE_KPI, totalSensors: 2048 }} />);
    const card = screen.getByTestId("kpi-card-sensors");
    expect(card).toHaveTextContent("2,048");
    expect(card).toHaveTextContent("台");
  });

  it("監視センサー数は props の値（固定値でない）を反映する", () => {
    render(<KpiSummary kpiData={BASE_KPI} />);
    expect(screen.getByTestId("kpi-card-sensors")).toHaveTextContent("10");
    expect(screen.getByTestId("kpi-card-sensors")).not.toHaveTextContent("2,048");
  });

  it("Level 3・Level 2・Level 1 の件数を表示する", () => {
    render(<KpiSummary kpiData={BASE_KPI} />);
    expect(screen.getByTestId("kpi-card-level3")).toHaveTextContent("1");
    expect(screen.getByTestId("kpi-card-level2")).toHaveTextContent("3");
    expect(screen.getByTestId("kpi-card-level1")).toHaveTextContent("8");
  });

  it("Level 1 カードに lime（getSeverityMeta(1).accentClass）が適用される", () => {
    render(<KpiSummary kpiData={BASE_KPI} />);
    expect(screen.getByTestId("kpi-card-level1").className).toContain(
      getSeverityMeta(1).accentClass,
    );
  });

  it("Level 3 カードは赤系、Level 2 カードは黄系で強調される", () => {
    render(<KpiSummary kpiData={BASE_KPI} />);
    expect(screen.getByTestId("kpi-card-level3").className).toContain(
      getSeverityMeta(3).accentClass,
    );
    expect(screen.getByTestId("kpi-card-level2").className).toContain(
      getSeverityMeta(2).accentClass,
    );
  });

  it("推定削減コストを万円表記（204.8万円）で表示する", () => {
    render(<KpiSummary kpiData={BASE_KPI} />);
    expect(screen.getByTestId("kpi-card-cost")).toHaveTextContent("204.8万円");
  });

  it("コストカードに「試算値」見出し +「前提: docs/business-model.md」本文の 2 段注記を常時表示する", () => {
    render(<KpiSummary kpiData={BASE_KPI} />);
    const costCard = screen.getByTestId("kpi-card-cost");
    // カード内スコープの順序検証（project.md cid:application-design:c2）
    expect(costCard.textContent).toMatch(
      /試算値[\s\S]*前提: docs\/business-model\.md/,
    );
    expect(costCard).toHaveTextContent("推定削減コスト");
  });

  it("todayDetections（本日の検知数）カードは表示しない", () => {
    render(<KpiSummary kpiData={BASE_KPI} />);
    expect(screen.queryByText("本日の検知数")).not.toBeInTheDocument();
    expect(screen.queryByTestId("kpi-card-today")).not.toBeInTheDocument();
  });

  it("値がすべて 0 でも各カードに 0 が表示される", () => {
    render(
      <KpiSummary
        kpiData={{
          totalSensors: 0,
          level3Count: 0,
          level2Count: 0,
          level1Count: 0,
          estimatedCostSavedYen: 0,
          isEstimate: true,
          assumptionDoc: "docs/business-model.md",
        }}
      />,
    );
    expect(screen.getByTestId("kpi-card-sensors")).toHaveTextContent("0");
    expect(screen.getByTestId("kpi-card-level3")).toHaveTextContent("0");
    expect(screen.getByTestId("kpi-card-level2")).toHaveTextContent("0");
    expect(screen.getByTestId("kpi-card-level1")).toHaveTextContent("0");
    expect(screen.getByTestId("kpi-card-cost")).toHaveTextContent("0万円");
  });
});
