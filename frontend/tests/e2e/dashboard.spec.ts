/**
 * ダッシュボード E2E テスト（シナリオ 1-8: 通常オペレーション）
 *
 * 検証内容: 読み込み / KPI サマリ / アラート一覧 / 詳細ドロワー /
 * 正常（Level 0）表示切替 / 修繕管理（AI 自動起票エントリーポイント）。
 *
 * 前提: global-setup が実在マスタ（HYD-001〜010）へシードを投入する。
 * 先頭行は Level 3（HYD-003）、Level 0（HYD-002）は既定で非表示。
 * セレクタは DashboardPage（pages/DashboardPage.ts）に集約する。
 */
import { test, expect } from "./fixtures";
import { DashboardPage } from "./pages/DashboardPage";

test.describe("ダッシュボード E2E テスト", () => {
  test("1. ダッシュボード読み込みと KPI サマリ表示", async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();

    // ページタイトル確認
    await expect(page).toHaveTitle(/SmartWater|Guardian/i);

    // KPI カードが実データで描画される（スケルトンから切替わるまで自動待機）
    await expect(dashboard.kpiSensors).toBeVisible();
  });

  test("2. 監視中センサー数と異常検知数の表示", async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();

    // 監視センサー数カード
    await expect(dashboard.kpiSensors).toBeVisible();
    await expect(dashboard.kpiSensors).toContainText(/センサー|監視/);

    // Level 3（管路破裂）カード
    await expect(dashboard.kpiLevel3).toBeVisible();
    await expect(dashboard.kpiLevel3).toContainText(/Level 3|管路破裂/);
  });

  test("3. アラート一覧表示", async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();

    // アラート一覧が描画されるまで待つ（ポーリング）
    await dashboard.waitForAlertList();
    expect(await dashboard.alertRows.count()).toBeGreaterThan(0);
  });

  test("4. アラート行に検査対象（消火栓 ID）が表示される", async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    await dashboard.waitForAlertList();

    // 先頭行（Level 3・HYD-003）に検査対象の消火栓 ID が表示される
    await expect(dashboard.alertRows.first()).toContainText("HYD-003");
  });

  test("5. アラート詳細パネル表示", async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    await dashboard.waitForAlertList();

    // アラート行をクリックして詳細ドロワーを開く
    await dashboard.alertRows.first().click();

    // 配管情報（BE-6 管台帳参照: HYD-003 → P-003）が表示される
    await expect(dashboard.drawer).toBeVisible();
    await expect(
      dashboard.drawer.getByRole("heading", { name: "配管情報" }),
    ).toBeVisible();
    await expect(dashboard.drawer).toContainText("P-003");
  });

  test("6. Level 0（正常）の表示切替", async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    await dashboard.waitForAlertList();

    // Level 0（HYD-002）は既定で非表示
    await expect(dashboard.alertRow("HYD-002")).not.toBeVisible();

    // 「正常も表示」トグルで表示を切り替えられる
    const toggle = page.getByTestId("show-level0-toggle");
    await toggle.check();
    await expect(dashboard.alertRow("HYD-002")).toBeVisible();

    await toggle.uncheck();
    await expect(dashboard.alertRow("HYD-002")).not.toBeVisible();
  });

  test("7. 詳細ドロワーから修繕管理（AI 自動起票）へ入れる", async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    await dashboard.waitForAlertList();

    await dashboard.alertRows.first().click();
    await expect(dashboard.drawer).toBeVisible();

    // 修繕管理エントリーポイント（FE-6: AI 自動起票ボタン）
    await expect(
      dashboard.drawer.getByRole("button", { name: /AI自動起票/ }),
    ).toBeVisible();
  });

  test("8. 修繕工事票（Work Order）の起票と成功確認", async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    await dashboard.waitForAlertList();

    await dashboard.alertRows.first().click();
    await expect(dashboard.drawer).toBeVisible();

    // AI 自動起票 → モーダルが開き見積が表示される（fallback 経路・決定論的）
    await dashboard.drawer
      .getByRole("button", { name: /AI自動起票/ })
      .click();
    const modal = page.getByRole("dialog", {
      name: "作業指示書 (Work Order)",
    });
    await expect(modal).toBeVisible();
    await expect(modal).toContainText("概算見積合計:");
  });

  test("9. ページスクロール・ナビゲーション確認", async ({ page }) => {
    await page.goto("/");

    // KPI セクションへスクロール
    const kpiSection = page.locator("section").first();
    await kpiSection.scrollIntoViewIfNeeded();
    await expect(kpiSection).toBeInViewport();

    // アラートセクションへスクロール
    const alertSection = page.locator("section").nth(1);
    await alertSection.scrollIntoViewIfNeeded();
    await expect(alertSection).toBeInViewport();
  });

  test("10. レスポンシブ表示確認（デスクトップ）", async ({ page }) => {
    // viewport は playwright.config.ts の devices["Desktop Chrome"] で固定
    await page.goto("/");

    // ビューポート確認
    const viewport = page.viewportSize();
    expect(viewport?.width).toBeGreaterThan(800);

    // レイアウトが壊れていないことを確認
    const mainSection = page.locator("main");
    const boundingBox = await mainSection.boundingBox();
    expect(boundingBox?.width).toBeGreaterThan(100);
  });
});
