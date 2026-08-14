// @vitest-environment node
/**
 * FE-7: GET /api/docs/business-model ルートハンドラのテスト。
 *
 * 環境変数 BUSINESS_MODEL_CONTENT から docs/business-model.md の内容を返し、
 * 環境変数が未設定の場合は 404 と error を返すことを検証する。
 */
import { describe, expect, it, beforeEach, afterEach } from "vitest";
import { GET } from "../route";

describe("GET /api/docs/business-model", () => {
  const originalEnv = process.env.BUSINESS_MODEL_CONTENT;

  afterEach(() => {
    // テスト後に環境変数を復元
    if (originalEnv !== undefined) {
      process.env.BUSINESS_MODEL_CONTENT = originalEnv;
    } else {
      delete process.env.BUSINESS_MODEL_CONTENT;
    }
  });

  it("正常系: BUSINESS_MODEL_CONTENT から内容を { content } で返す", async () => {
    process.env.BUSINESS_MODEL_CONTENT = "# ビジネスモデル\n\nテスト本文";
    const response = await GET();
    expect(response.status).toBe(200);
    const body = (await response.json()) as { content: string };
    expect(body.content).toContain("# ビジネスモデル");
    expect(body.content).toContain("テスト本文");
  });

  it("異常系: BUSINESS_MODEL_CONTENT が未設定の場合は 404 と error を返す", async () => {
    delete process.env.BUSINESS_MODEL_CONTENT;
    const response = await GET();
    expect(response.status).toBe(404);
    const body = (await response.json()) as { content: null; error: string };
    expect(body.content).toBeNull();
    expect(body.error).toBeTruthy();
  });
});
