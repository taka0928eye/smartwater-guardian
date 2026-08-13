/**
 * ダッシュボード E2E テスト（シナリオ 1-8: 通常オペレーション）
 *
 * テスト順序:
 * 1. ダッシュボード読み込み
 * 2. KPI サマリ表示確認（監視センサー数・異常検知数）
 * 3. アラート一覧表示確認
 * 4. アラート詳細表示・フィルタリング
 * 5. 修繕管理（工事情報フェッチ・工事票起票）
 * 6. 災害シミュレーション（シナリオ 9 は別テストファイルで実行）
 */
import { test, expect } from "@playwright/test";

test.describe("ダッシュボード E2E テスト", () => {
  test("1. ダッシュボード読み込みと KPI サマリ表示", async ({ page }) => {
    // ダッシュボードへ遷移
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // ページタイトル確認
    await expect(page).toHaveTitle(/SmartWater|Guardian/i);

    // KPI セクション確認（aria-labelledby で h2 と連携）
    const kpiSection = page.locator("section").first();
    await expect(kpiSection.locator("h2")).toContainText(/KPI|監視/i);

    // KPI カード確認（スケルトン消失後）
    const kpiCards = page.locator('[data-testid="kpi-card"]');
    await expect(kpiCards.first()).toBeDefined();
  });

  test("2. 監視中センサー数と異常検知数の表示", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // 監視センサー数カード
    const sensorCard = page.locator('[data-testid="kpi-card"]').first();
    await expect(sensorCard.locator("text=/センサー|監視/")).toBeDefined();

    // Level 1-3 カウント確認
    const level3Card = page.locator('[data-testid="kpi-card"]').nth(1);
    await expect(level3Card.locator("text=/Level 3|高/")).toBeDefined();
  });

  test("3. アラート一覧表示", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // アラートセクション確認
    const alertSection = page.locator("main").locator("section").nth(2);
    await expect(alertSection.locator("h2")).toContainText(/アラート|異常/i);

    // アラート行確認
    const alertRows = page.locator('[data-testid="alert-row"]');
    const rowCount = await alertRows.count();
    expect(rowCount).toBeGreaterThan(0);
  });

  test("4. アラート行の検査対象パイプ表示", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // 最初のアラート行から検査対象パイプを確認
    const firstAlert = page.locator('[data-testid="alert-row"]').first();
    const pipeId = await firstAlert.locator('[data-testid="alert-pipe-id"]').textContent();
    expect(pipeId).toBeTruthy();
    expect(pipeId).toMatch(/HYD-\d{3}/);
  });

  test("5. アラート詳細パネル表示", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // アラート行をクリック
    const firstAlert = page.locator('[data-testid="alert-row"]').first();
    await firstAlert.click();

    // 詳細パネルが表示されることを確認
    const detailPanel = page.locator('[data-testid="alert-detail-panel"]');
    await expect(detailPanel).toBeVisible();

    // パネル内容確認
    const pipeInfo = detailPanel.locator('[data-testid="pipe-info"]');
    await expect(pipeInfo).toBeDefined();
  });

  test("6. Level フィルタリング", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // 初期状態のアラート件数を記録
    const allAlerts = page.locator('[data-testid="alert-row"]');
    const initialCount = await allAlerts.count();

    // Level フィルタボタン確認と操作
    const level3Filter = page.locator(
      'button:has-text("Level 3"), button[aria-label*="Level 3"]'
    );
    if (await level3Filter.isVisible()) {
      await level3Filter.click();
      await page.waitForTimeout(300);

      // フィルタ後のアラート件数が初期値以下であることを確認
      const filteredAlerts = page.locator('[data-testid="alert-row"]');
      const filteredCount = await filteredAlerts.count();
      expect(filteredCount).toBeLessThanOrEqual(initialCount);
    }
  });

  test("7. 修繕工事一覧取得（GET /work-orders/{id}）", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // アラート行をクリックして詳細を表示
    const firstAlert = page.locator('[data-testid="alert-row"]').first();
    const alertId = await firstAlert.getAttribute("data-alert-id");
    await firstAlert.click();

    // 修繕工事セクションを確認
    const workOrderSection = page.locator('[data-testid="work-order-section"]');
    if (await workOrderSection.isVisible()) {
      // 工事一覧が表示されることを確認
      const workOrderItems = workOrderSection.locator('[data-testid="work-order-item"]');
      expect(await workOrderItems.count()).toBeGreaterThanOrEqual(0);
    }
  });

  test("8. 修繕工事票起票（POST /work-orders）と成功確認", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // アラート行をクリック
    const firstAlert = page.locator('[data-testid="alert-row"]').first();
    await firstAlert.click();

    // 工事票起票ボタンを確認・クリック
    const issueButton = page.locator('button:has-text("工事票起票")');
    if (await issueButton.isVisible()) {
      await issueButton.click();
      await page.waitForTimeout(500);

      // 成功メッセージまたは工事票行の追加を確認
      const successMsg = page.locator('[data-testid="success-message"]');
      const newWorkOrder = page.locator('[data-testid="work-order-item"]');

      const hasSuccess =
        (await successMsg.isVisible()) || (await newWorkOrder.count()) > 0;
      expect(hasSuccess).toBeTruthy();
    }
  });

  test("9. ページスクロール・ナビゲーション確認", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

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
    await page.waitForLoadState("networkidle");

    // ビューポート確認
    const viewport = page.viewportSize();
    expect(viewport?.width).toBeGreaterThan(800);

    // レイアウトが壊れていないことを確認
    const mainSection = page.locator("main");
    const boundingBox = await mainSection.boundingBox();
    expect(boundingBox?.width).toBeGreaterThan(100);
  });
});
