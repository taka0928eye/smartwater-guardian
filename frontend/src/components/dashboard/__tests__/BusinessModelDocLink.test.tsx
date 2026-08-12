// @vitest-environment jsdom
/**
 * FE-7: 「前提: docs/business-model.md」リンクボタン（BusinessModelDocLink）のテスト。
 *
 * ボタンクリックで /api/docs/business-model から内容を取得し、モーダルに
 * docs/business-model.md の内容を表示することを検証する。fetch はグローバルに
 * モックして外部依存をなくす。TDD（Red → Green → Refactor）。
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import BusinessModelDocLink from "../BusinessModelDocLink";

/** グローバル fetch をモックする（成功/失敗を使い分ける）。 */
function mockFetchOnce(response: { ok: boolean; body: unknown }) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: response.ok,
    json: async () => response.body,
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("BusinessModelDocLink", () => {
  it("「docs/business-model.md」ボタンを描画する", () => {
    render(<BusinessModelDocLink />);
    const button = screen.getByRole("button", {
      name: /docs\/business-model\.md/,
    });
    expect(button).toBeInTheDocument();
  });

  it("クリックで /api/docs/business-model を取得し、モーダルに内容を表示する", async () => {
    const fetchMock = mockFetchOnce({
      ok: true,
      body: { content: "# ビジネスモデル\n\nテスト本文" },
    });
    render(<BusinessModelDocLink />);

    fireEvent.click(
      screen.getByRole("button", { name: /docs\/business-model\.md/ }),
    );

    expect(fetchMock).toHaveBeenCalledWith("/api/docs/business-model");
    const dialog = await screen.findByRole("dialog");
    expect(dialog).toHaveTextContent("docs/business-model.md");
    await waitFor(() => {
      // <pre> は本文全体を1つのテキストノードとして持つため、部分一致（regex）で検証する
      expect(screen.getByText(/テスト本文/)).toBeInTheDocument();
    });
  });

  it("取得失敗時はモーダルにエラーメッセージを表示する", async () => {
    mockFetchOnce({ ok: false, body: { content: null, error: "読み込み失敗" } });
    render(<BusinessModelDocLink />);

    fireEvent.click(
      screen.getByRole("button", { name: /docs\/business-model\.md/ }),
    );

    const dialog = await screen.findByRole("dialog");
    await waitFor(() => {
      expect(screen.getByText(/読み込み失敗/)).toBeInTheDocument();
    });
    expect(dialog).toBeInTheDocument();
  });

  it("ネットワークエラー時もモーダルにエラーメッセージを表示する", async () => {
    // fetch 自体が reject するケース（API ルート未到達）
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("Network Error")),
    );
    render(<BusinessModelDocLink />);

    fireEvent.click(
      screen.getByRole("button", { name: /docs\/business-model\.md/ }),
    );

    const dialog = await screen.findByRole("dialog");
    await waitFor(() => {
      expect(screen.getByText(/取得に失敗しました/)).toBeInTheDocument();
    });
    expect(dialog).toBeInTheDocument();
  });

  it("閉じるボタンでモーダルを閉じられる", async () => {
    mockFetchOnce({
      ok: true,
      body: { content: "# ビジネスモデル\n\nテスト本文" },
    });
    render(<BusinessModelDocLink />);

    fireEvent.click(
      screen.getByRole("button", { name: /docs\/business-model\.md/ }),
    );
    const dialog = await screen.findByRole("dialog");
    expect(dialog).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /閉じる/ }));
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
  });
});
