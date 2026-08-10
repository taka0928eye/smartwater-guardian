// @vitest-environment jsdom
/**
 * FE-2: ダッシュボードヘッダー（components/dashboard/Header.tsx）のタイマー共有ストアのテスト。
 *
 * Header はモジュールレベルの単一ストア（currentTimestamp / listeners）を
 * useSyncExternalStore で購読する。複数インスタンスが同時にマウントされても
 * setInterval は1本だけ生成され、最後の購読者がアンマウントするまでは
 * 維持される（タイマーが多重生成・リークしない）ことを検証する。
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import { render } from "@testing-library/react";

import Header from "../Header";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("Header の時刻更新ストア", () => {
  it("複数インスタンスを同時にマウントしても setInterval は1本だけ生成される", () => {
    const setIntervalSpy = vi.spyOn(global, "setInterval");

    const first = render(<Header />);
    const second = render(<Header />);

    expect(setIntervalSpy).toHaveBeenCalledTimes(1);

    first.unmount();
    second.unmount();
  });

  it("すべてのインスタンスをアンマウントすると生成した setInterval と同数の clearInterval が呼ばれる（タイマーリークがない）", () => {
    const setIntervalSpy = vi.spyOn(global, "setInterval");
    const clearIntervalSpy = vi.spyOn(global, "clearInterval");

    const first = render(<Header />);
    const second = render(<Header />);
    first.unmount();
    second.unmount();

    expect(clearIntervalSpy).toHaveBeenCalledTimes(setIntervalSpy.mock.calls.length);
  });
});
