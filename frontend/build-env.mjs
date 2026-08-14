/**
 * ビルド前スクリプト: docs/business-model.md の内容を読み込み、.env.local に埋め込む。
 * npm run dev / npm run build 実行時に自動的に実行され、BUSINESS_MODEL_CONTENT 環境変数
 * が設定される。テスト・本番環境では task definition / .env で定義すること。
 */
import fs from "node:fs";
import path from "node:path";

const businessModelPath = path.join(
  import.meta.dirname,
  "..",
  "docs",
  "business-model.md"
);
try {
  const content = fs.readFileSync(businessModelPath, "utf-8");
  const envContent = `BUSINESS_MODEL_CONTENT=${JSON.stringify(content)}\n`;
  const envLocalPath = path.join(import.meta.dirname, ".env.local");
  fs.writeFileSync(envLocalPath, envContent);
  console.log(
    `✓ .env.local を生成しました (${businessModelPath} の内容を埋め込み)`
  );
} catch (error) {
  const msg = error instanceof Error ? error.message : String(error);
  console.error(`✗ build-env.mjs 失敗: ${msg}`);
  // ECS 本番環境では docs/business-model.md は不要（環境変数で定義される）
  // したがって失敗しても CI は止めない
}
