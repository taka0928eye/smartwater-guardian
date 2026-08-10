/**
 * FE-5: アラート一覧のソート・フィルタ純粋関数（src/lib/alertSort.ts）の単体テスト。
 *
 * AlertList の表示順（深刻度降順 → 検知時刻降順）と Level 0 除外ロジックを
 * コンポーネントから切り離して検証する。
 *
 * 実行: npm run test
 */
import { describe, expect, it } from "vitest";

import type { AlertSummary } from "@/types/api";
import { filterLevelZero, sortAlerts } from "../alertSort";

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

describe("sortAlerts", () => {
  it("深刻度降順で並べる", () => {
    const sorted = sortAlerts([
      makeAlert({ telemetryId: "t1", severityLevel: 1 }),
      makeAlert({ telemetryId: "t3", severityLevel: 3 }),
      makeAlert({ telemetryId: "t2", severityLevel: 2 }),
    ]);
    expect(sorted.map((a) => a.telemetryId)).toEqual(["t3", "t2", "t1"]);
  });

  it("同じ深刻度内では検知時刻が新しい順に並ぶ", () => {
    const sorted = sortAlerts([
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
    ]);
    expect(sorted.map((a) => a.telemetryId)).toEqual(["t2", "t1"]);
  });

  it("元の配列を変更しない（不変）", () => {
    const input = [
      makeAlert({ telemetryId: "t1", severityLevel: 1 }),
      makeAlert({ telemetryId: "t3", severityLevel: 3 }),
    ];
    sortAlerts(input);
    expect(input.map((a) => a.telemetryId)).toEqual(["t1", "t3"]);
  });
});

describe("filterLevelZero", () => {
  it("既定（false）は Level 0 を除外する", () => {
    const filtered = filterLevelZero(
      [
        makeAlert({ telemetryId: "t1", severityLevel: 1 }),
        makeAlert({ telemetryId: "t0", severityLevel: 0 }),
      ],
      false,
    );
    expect(filtered.map((a) => a.telemetryId)).toEqual(["t1"]);
  });

  it("true のときは Level 0 を含めて全て返す", () => {
    const filtered = filterLevelZero(
      [
        makeAlert({ telemetryId: "t1", severityLevel: 1 }),
        makeAlert({ telemetryId: "t0", severityLevel: 0 }),
      ],
      true,
    );
    expect(filtered.map((a) => a.telemetryId)).toEqual(["t1", "t0"]);
  });
});
