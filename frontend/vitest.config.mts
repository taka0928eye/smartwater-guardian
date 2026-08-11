import { fileURLToPath, URL } from "node:url";

import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    // デフォルト環境は node。tsx のコンポーネントテストはファイル先頭の
    // `// @vitest-environment jsdom` で jsdom に切り替える（FE-2）。
    environment: "node",
    // tests ディレクトリ等の補助コードをテスト対象から除外する。
    include: ["src/**/*.test.{ts,tsx}"],
    // jest-dom のカスタムマッチャー（toBeInTheDocument 等）を読み込む。
    setupFiles: ["./src/test/setup.ts"],
    // NFR-1: ローカル npm run test（= vitest run）でもカバレッジ計測 + 80% ゲートを
    // 強制する（team-practices Q3=A。thresholds の単一ソースを本ファイルへ）。
    coverage: {
      enabled: true,
      reporter: ["text", "html"],
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 80,
        statements: 80,
      },
    },
  },
  resolve: {
    alias: {
      // tsconfig.json の paths と同一の @/* -> src/* エイリアス。
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
});
