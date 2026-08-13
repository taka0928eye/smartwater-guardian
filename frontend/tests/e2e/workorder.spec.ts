/**
 * FE-8: AI 自動起票（作業指示書）E2E テスト（シナリオ 8）。
 *
 * シナリオ 8（LLM 自動起票）: 詳細ドロワーの「AI自動起票」から作業指示書（Work Order）
 * モーダルが生成され、見積・作業時間・原価脚注が表示される。
 *
 * 決定論の確保: playwright.config.ts がバックエンドを `ORCAROUTER_ENABLED=false` で起動する
 * ため、LLM を呼ばず規定ルール（fallback）で Work Order が生成される（原価 = ¥0 相当、
 * 脚注「LLM未使用（規定ルールによる算出）」）。実 LLM は呼ばれないため実行コストは発生せず、
 * 結果も一定になる。ユーザーが既存サーバーを再利用する場合（reuseExistingServer）は
 * この前提を満たさない可能性があるため、runbook に明記する。
 */
import { test, expect } from "./fixtures";
import { DashboardPage } from "./pages/DashboardPage";

test.describe("AI 自動起票（シナリオ 8）", () => {
  /** Level 3（HYD-003）の詳細ドロワーから作業指示書モーダルを開く。 */
  async function openWorkOrderModal(
    page: import("@playwright/test").Page,
    dashboard: DashboardPage,
  ) {
    await dashboard.openAlert("HYD-003");
    await expect(dashboard.drawer).toBeVisible();
    await dashboard.drawer
      .getByRole("button", { name: /AI自動起票/ })
      .click();

    const modal = page.getByRole("dialog", { name: "作業指示書 (Work Order)" });
    await expect(modal).toBeVisible();
    return modal;
  }

  test("作業指示書モーダルに見積・作業時間が表示される", async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    const modal = await openWorkOrderModal(page, dashboard);

    await expect(
      modal.getByRole("heading", { name: "作業指示書 (Work Order)" }),
    ).toBeVisible();
    // Level 3（管路破裂）は緊急対応対象の見積として表示される
    await expect(modal).toContainText("緊急度:");
    await expect(modal).toContainText("概算見積合計:");
    await expect(modal).toContainText("想定作業時間:");
    await expect(modal).toContainText("名)");
  });

  test("fallback 経路では API 原価脚注（LLM未使用）が表示される", async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    const modal = await openWorkOrderModal(page, dashboard);

    await expect(modal).toContainText("LLM未使用（規定ルールによる算出）");
  });

  test("モーダルを閉じて再起票できる", async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    const modal = await openWorkOrderModal(page, dashboard);

    // モーダルスコープ内の閉じるボタンで閉じる（ドロワーの閉じるボタンとは別）
    await modal.getByRole("button", { name: "閉じる" }).click();
    await expect(modal).not.toBeVisible();

    // ドロワーは開いたまま → 再起票でモーダルが再度開く
    await expect(dashboard.drawer).toBeVisible();
    await dashboard.drawer
      .getByRole("button", { name: /AI自動起票/ })
      .click();
    const reopened = page.getByRole("dialog", {
      name: "作業指示書 (Work Order)",
    });
    await expect(reopened).toBeVisible();
  });
});
