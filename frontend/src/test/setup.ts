/**
 * vitest セットアップ（FE-2）。
 *
 * 1) @testing-library/jest-dom のカスタムマッチャー（toBeInTheDocument 等）を
 *    vitest の expect に登録する。
 * 2) vitest は globals 無効のため RTL の自動クリーンアップが働かない。
 *    afterEach で明示的に cleanup を実行し、テスト間の DOM を破棄する。
 */
import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

afterEach(() => {
  cleanup();
});
