// @vitest-environment jsdom
/**
 * FE-2: 深刻度バッジ（components/common/SeverityBadge.tsx）の TDD テスト。
 *
 * 各深刻度レベル（1 / 2 / 3 / 0）が正しいラベルと色クラスで描画されることを
 * @testing-library/react で検証する。UI-1 の深刻度カラー定義に準拠する。
 */
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import SeverityBadge from "../SeverityBadge";

describe("SeverityBadge", () => {
  it("Level 1 は「Level 1 微小漏水」を緑系クラスで描画する", () => {
    render(<SeverityBadge level={1} />);
    const badge = screen.getByText("Level 1 微小漏水");
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain("green");
  });

  it("Level 2 は「Level 2 進行性漏水」を黄系クラスで描画する", () => {
    render(<SeverityBadge level={2} />);
    const badge = screen.getByText("Level 2 進行性漏水");
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain("amber");
  });

  it("Level 3 は「Level 3 管路破裂」を赤系クラスで描画する", () => {
    render(<SeverityBadge level={3} />);
    const badge = screen.getByText("Level 3 管路破裂");
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain("red");
  });

  it("レベル 0 は「正常」をグレー系クラスで描画する", () => {
    render(<SeverityBadge level={0} />);
    const badge = screen.getByText("正常");
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain("slate");
  });
});
