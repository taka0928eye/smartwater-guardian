/**
 * FE-8: E2E テストの共通フィクスチャ。
 *
 * `apiBaseUrl` をテストオプションとして公開する（バックエンド URL の差し替えを
 * テスト単位・プロジェクト単位で行える）。既定値は helpers と同じ解決
 * （`E2E_API_BASE_URL` / `http://localhost:8000`）。
 *
 * バックエンド未応答の検証（シナリオ 5）は `helpers.interceptBackendFailure` で
 * ネットワーク遮断する方式を採るため、`skipBackendCheck` オプションは設けない
 * （テストごとに明示的に遮断する方が意図が明確で、ストア共有を乱さない）。
 */
import { test as base, expect } from "@playwright/test";
import { API_BASE_URL } from "./helpers";

export interface TestOptions {
  /** バックエンド API の接続先。 */
  apiBaseUrl: string;
}

export const test = base.extend<TestOptions>({
  apiBaseUrl: [API_BASE_URL, { option: true }],
});

export { expect };
