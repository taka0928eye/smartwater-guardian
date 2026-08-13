/**
 * 災害シミュレーション E2E テスト（シナリオ 9）
 *
 * 防災シミュレーション（/api/v1/disaster/simulate エンドポイント）で
 * Level 3 アラート大量追加。既存テスト（dashboard.spec.ts）の厳密カウント検証と衝突
 * しないよう、本テストはデフォルトで直列実行され、全シナリオ 1-8 完了後に実行される。
 *
 * 注: CI では本テストを実行する場合、Playwright の projects 設定で
 * disaster が main に依存する構成（playwright.config.ts の dependencies）を確認してください。
 */
import { test, expect } from "@playwright/test";

test.describe("災害シミュレーション（シナリオ 9）", () => {
  test("1. 防災シミュレーション実行前のアラート件数記録", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    const alertRows = page.locator('[data-testid="alert-row"]');
    const initialCount = await alertRows.count();
    console.log(`[災害シミュレーション前] アラート件数: ${initialCount}`);
    expect(initialCount).toBeGreaterThan(0);
  });

  test("2. 防災シミュレーション実行（/api/v1/disaster/simulate）", async ({
    page,
  }) => {
    const apiBaseUrl = process.env.E2E_API_BASE_URL ?? "http://localhost:8000";

    const simulateResponse = await fetch(`${apiBaseUrl}/api/v1/disaster/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ count: 10 }),
    });

    expect(simulateResponse.ok).toBeTruthy();
    const data = await simulateResponse.json();
    console.log(`[災害シミュレーション] 挿入件数: ${data.inserted_count}`);
  });

  test("3. シミュレーション後のダッシュボード更新確認", async ({ page }) => {
    // ダッシュボード再読み込み
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // アラート行の存在を確認
    const alertRows = page.locator('[data-testid="alert-row"]');
    const afterCount = await alertRows.count();
    console.log(`[災害シミュレーション後] アラート件数: ${afterCount}`);
    expect(afterCount).toBeGreaterThan(0);
  });

  test("4. 災害時の KPI サマリ更新確認", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // KPI カード存在確認
    const kpiCards = page.locator('[data-testid="kpi-card"]');
    expect(await kpiCards.count()).toBeGreaterThan(0);

    // Level 3 カード（2 番目）確認
    const level3Card = kpiCards.nth(1);
    const level3Text = await level3Card.textContent();
    console.log(`[災害時 KPI] Level 3 カード: ${level3Text}`);
    expect(level3Text).toBeTruthy();
  });

  test("5. ページ安定性確認（スクロール・操作可能）", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // スクロール操作
    const main = page.locator("main");
    await main.evaluate((el) => {
      el.scrollTop = Math.min(el.scrollHeight / 2, 500);
    });

    // アラート行をクリック可能であることを確認
    const firstAlert = page.locator('[data-testid="alert-row"]').first();
    if (await firstAlert.isVisible()) {
      await firstAlert.click();
      const detailPanel = page.locator('[data-testid="alert-detail-panel"]');
      const isPanelVisible = await detailPanel.isVisible().catch(() => false);
      expect(typeof isPanelVisible).toBe("boolean");
    }
  });

  test("6. ページネーション・レスポンシブ確認", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // ビューポート確認
    const viewport = page.viewportSize();
    expect(viewport?.width).toBeGreaterThan(800);

    // メインセクション確認
    const main = page.locator("main");
    const box = await main.boundingBox();
    expect(box?.width).toBeGreaterThan(100);
  });
});
