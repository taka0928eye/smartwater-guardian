import { describe, expect, it } from "vitest";

import {
  buildFrequencyTicks,
  formatSpectrumPower,
  LEAK_BAND_MAX_HZ,
  LEAK_BAND_MIN_HZ,
} from "../SpectrumChart";

describe("SpectrumChart", () => {
  it("小さい正のパワーを0へ丸めず表示する", () => {
    expect(formatSpectrumPower(0.000347)).toBe("0.000347");
    expect(formatSpectrumPower(0)).toBe("0");
  });

  it("周波数軸の目盛りを1000Hz刻みで生成する", () => {
    expect(
      buildFrequencyTicks([
        { freqHz: 0, power: 0 },
        { freqHz: 4000, power: 1 },
      ]),
    ).toEqual([0, 1000, 2000, 3000, 4000]);
  });

  it("漏水帯域を500〜1500Hzとして定義する", () => {
    expect(LEAK_BAND_MIN_HZ).toBe(500);
    expect(LEAK_BAND_MAX_HZ).toBe(1500);
  });
});
