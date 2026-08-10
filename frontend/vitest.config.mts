import { fileURLToPath, URL } from "node:url";

import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    // api.ts は純 TypeScript（DOM 不要）のため node 環境で十分。
    environment: "node",
    // tests ディレクトリ等の補助コードをテスト対象から除外する。
    include: ["src/**/*.test.ts"],
  },
  resolve: {
    alias: {
      // tsconfig.json の paths と同一の @/* -> src/* エイリアス。
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
});
