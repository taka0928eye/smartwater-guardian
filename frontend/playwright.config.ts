/**
 * FE-8: Playwright E2E テスト設定。
 *
 * - `webServer` でバックエンド（FastAPI / uvicorn）とフロントエンド（Next.js dev）を
 *   自動起動し、`npm run e2e` 1 コマンドで完結させる（Issue #29 検証方法の 3 ターミナル
 *   を Playwright に委譲した形）。
 * - バックエンドは `ORCAROUTER_ENABLED=false` で起動し、LLM 自動起票（シナリオ 8）を
 *   実 API キーなしのフォールバック経路（source == "fallback"）で決定的に検証する
 *   （実 LLM 呼び出しは行わずコストも発生しない。テスト用 stub ではなく実フォールバック経路）。
 * - `.env.e2e` を読み込み、`PLAYWRIGHT_BASE_URL` / `E2E_API_BASE_URL` を上書きできる。
 * - 前後処理の順序: Playwright は webServer を起動してから globalSetup を実行するため、
 *   `tests/e2e/global-setup.ts` は起動済みバックエンドへデモシードを投入できる。
 * - ストアはインメモリ共有のため、件数カウントの厳密アサートは並列でも壊れない範囲
 *   （深刻度別件数・特定IDの存在・順序）に限定する。
 */
import { defineConfig, devices } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

/**
 * `.env.e2e` を読み込む（存在する場合のみ）。既に環境変数が設定されていれば上書きしない
 * （シェル側の値が優先される）。
 */
function loadEnvFile(file: string): void {
  if (!fs.existsSync(file)) return;
  for (const line of fs.readFileSync(file, "utf8").split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eq = trimmed.indexOf("=");
    if (eq <= 0) continue;
    const key = trimmed.slice(0, eq).trim();
    const value = trimmed.slice(eq + 1).trim();
    if (process.env[key] === undefined) process.env[key] = value;
  }
}
loadEnvFile(path.join(__dirname, ".env.e2e"));

/** ブラウザテストの接続先（フロントエンド）。 */
const BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000";
/** バックエンド API の接続先（シード・ヘルスチェック・テスト内 API 呼び出し）。 */
const API_BASE_URL = process.env.E2E_API_BASE_URL ?? "http://localhost:8000";
/** CI 実行かどうか（ローカルでは既起動サーバーを再利用し、CI では毎回起動する）。 */
const IS_CI = Boolean(process.env.CI);

export default defineConfig({
  testDir: "./tests/e2e",
  // デモシードを globalSetup で投入する（webServer 起動後に実行される）。
  globalSetup: "./tests/e2e/global-setup.ts",
  // テストファイル内は直列（ポーリングでストアを更新するため）。ファイル間は並列。
  fullyParallel: false,
  // ネットワーク遅延・Next.js dev の初回コンパイルを想定した余裕。
  timeout: 30_000,
  expect: { timeout: 10_000 },
  // CI でのみリトライ（ローカルと CI で挙動差を出さないため失敗時はレポートで確認）。
  retries: IS_CI ? 1 : 0,
  // Issue #29 指定の並列ワーカー数。ストア共有のため厳密カウントは並列非依存の範囲で検証する。
  workers: 4,
  reporter: [
    ["list"],
    ["html", { open: "never" }],
  ],
  // プロジェクト分離: 防災シミュレーション（シナリオ 9）は simulate で Level 3 アラートを
  // インメモリストアへ追加するため、既存シナリオの厳密カウント検証
  // （KPI の Level 3 件数・alertRow('HYD-003') の部分一致など）と衝突する。
  // main（シナリオ 1〜8）を先に並列実行し、その完了後に disaster（シナリオ 9）を
  // 直列実行する。disaster の simulate が後続テストに影響しないことを保証する。
  projects: [
    {
      name: "main",
      testIgnore: /disaster\.spec\.ts/,
    },
    {
      name: "disaster",
      testMatch: /disaster\.spec\.ts/,
      dependencies: ["main"],
    },
  ],
  use: {
    ...devices["Desktop Chrome"],
    baseURL: BASE_URL,
    // 失敗時のスクリーンショット・ビデオ・トレースを自動保存する（受入条件）。
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    trace: "on-first-retry",
  },
  webServer: [
    {
      // バックエンド（FastAPI）。--reload なしで安定起動する。
      // cwd を backend に固定し、Windows の cmd が `/` をスイッチと解釈しないよう
      // パスはバックスラッシュで指定する（`cd ../backend && venv/Scripts/...` は不可）。
      command: "venv\\Scripts\\uvicorn.exe main:app --port 8000",
      cwd: path.resolve(__dirname, "../backend"),
      url: `${API_BASE_URL}/api/v1/sensors`,
      timeout: 60_000,
      reuseExistingServer: !IS_CI,
      env: { ...process.env, ORCAROUTER_ENABLED: "false" },
    },
    {
      // フロントエンド（Next.js 本番ビルド）。npm run e2e が先に next build を実行するため、
      // next dev のコールドコンパイル待ちでテストがタイムアウトするのを防ぎ、高速・決定論的にする。
      command: "npm run start",
      url: BASE_URL,
      timeout: 60_000,
      reuseExistingServer: !IS_CI,
      env: { ...process.env, NEXT_PUBLIC_API_BASE_URL: API_BASE_URL },
    },
  ],
});
