// @vitest-environment node
/**
 * FE-7: GET /api/docs/business-model ルートハンドラのテスト。
 *
 * docs/business-model.md の内容を { content } で返し、読み込み失敗時は 404 と
 * error を返すことを検証する。実ファイルへの依存を避けるため fs の readFile を
 * モックする。TDD（Red → Green → Refactor）。
 */
import { describe, expect, it, vi } from "vitest";

// readFile をモックして、実行環境（dev / CI）のパス差に依存しないようにする
vi.mock("node:fs/promises", () => ({ readFile: vi.fn() }));

import { readFile } from "node:fs/promises";

import { GET } from "../route";

const mockedReadFile = vi.mocked(readFile);

describe("GET /api/docs/business-model", () => {
  it("正常系: docs/business-model.md の内容を { content } で返す", async () => {
    mockedReadFile.mockResolvedValue("# ビジネスモデル\n\nテスト本文");
    const response = await GET();
    expect(response.status).toBe(200);
    const body = (await response.json()) as { content: string };
    expect(body.content).toContain("# ビジネスモデル");
    expect(body.content).toContain("テスト本文");
  });

  it("異常系: 読み込み失敗時は 404 と error を返す", async () => {
    mockedReadFile.mockRejectedValue(new Error("ENOENT: no such file"));
    const response = await GET();
    expect(response.status).toBe(404);
    const body = (await response.json()) as { content: null; error: string };
    expect(body.content).toBeNull();
    expect(body.error).toBeTruthy();
  });
});
