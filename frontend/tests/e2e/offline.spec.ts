/**
 * FE-8: バックエンド停止時フォールバック E2E テスト（シナリオ 5）。
 *
 * シナリオ 5（バックエンド停止）: バックエンド未応答でも画面は白紙にならない。
 * - SSR（サーバー側取得）はルート遮断の対象外のため、地図は SSR 取得値で描画される。
 * - クライアント側ポーリング（KPI / アラート / センサー）は遮断され、
 *   各フックのフォールバック（KPI 再スケルトン / アラートエラー表示・空表示）を検証する。
 *
 * 実バックエンドを停止する代わりに、ブラウザからの `/api/v1/**` 要求のみを
 * `page.route` で abort して再現する（テストの並列実行を壊さない）。
 */
import { test, expect } from "./fixtures";
import { DashboardPage } from "./pages/DashboardPage";
import { interceptBackendFailure } from "./helpers";

test.describe("バックエンド停止時フォールバック（シナリオ 5）", () => {
  test("ページは白紙にならず、スケルトンとエラー表示で代替される", async ({
    page,
  }) => {
    await interceptBackendFailure(page);
    const dashboard = new DashboardPage(page);
    await dashboard.goto();

    // SSR で描画されるヘッダー・セクション見出しは表示される
    await expect(dashboard.title).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "センサー地図" }),
    ).toBeVisible();

    // KPI: 取得失敗 → スケルトン表示（白紙にしない）
    await expect(dashboard.kpiSkeleton).toBeVisible();

    // アラート: 取得失敗メッセージ + 空表示（白紙にしない）
    await expect(page.getByTestId("alerts-error")).toContainText(
      "アラートの取得に失敗しました",
    );
    await expect(page.getByTestId("alert-empty")).toBeVisible();

    // 地図: SSR 取得値で描画される（クライアント側ポーリング失敗後も据え置き）
    await expect(dashboard.map).toBeVisible();
  });
});
