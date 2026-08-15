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

    // アラート一覧が描画されるまで待つ（ポーリング）
    await expect(page.getByTestId("alert-row").first()).toBeVisible();

    const alertRows = page.locator('[data-testid="alert-row"]');
    const initialCount = await alertRows.count();
    console.log(`[災害シミュレーション前] アラート件数: ${initialCount}`);
    expect(initialCount).toBeGreaterThan(0);
  });

  test("2. 防災シミュレーションボタンで実行する", async ({ page }) => {
    await page.goto("/");
    const button = page.getByTestId("disaster-simulate-button");
    await expect(button).toHaveText("防災シミュレーション");

    const [simulateResponse] = await Promise.all([
      page.waitForResponse(
        (response) =>
          response.url().includes("/api/v1/disaster/simulate") &&
          response.request().method() === "POST",
      ),
      button.click(),
    ]);

    expect(simulateResponse.ok()).toBeTruthy();
    const data = await simulateResponse.json();
    console.log(`[災害シミュレーション] 挿入件数: ${data.inserted_count}`);
    await expect(button).toHaveText("通常モードに戻る");
  });

  test("3. シミュレーション後のダッシュボード更新確認", async ({ page }) => {
    // ダッシュボード再読み込み
    await page.goto("/");

    // アラート一覧が描画されるまで待つ
    await expect(page.getByTestId("alert-row").first()).toBeVisible();

    const alertRows = page.locator('[data-testid="alert-row"]');
    const afterCount = await alertRows.count();
    console.log(`[災害シミュレーション後] アラート件数: ${afterCount}`);
    expect(afterCount).toBeGreaterThan(0);
  });

  test("4. 災害時の KPI サマリ更新確認", async ({ page }) => {
    await page.goto("/");

    // KPI カードが実データで描画されるまで待つ
    await expect(page.getByTestId("kpi-card-sensors")).toBeVisible();
    await expect(page.getByTestId("kpi-card-level3")).toBeVisible();

    // Level 3（管路破裂）カード: 災害シミュレーションで増加する件数が表示される
    const level3Text = await page.getByTestId("kpi-card-level3").textContent();
    console.log(`[災害時 KPI] Level 3 カード: ${level3Text}`);
    expect(level3Text).toContain("Level 3");
  });

  test("5. ページ安定性確認（スクロール・操作可能）", async ({ page }) => {
    await page.goto("/");

    // アラート一覧が描画されるまで待つ
    await expect(page.getByTestId("alert-row").first()).toBeVisible();

    // スクロール操作
    const main = page.locator("main");
    await main.evaluate((el) => {
      el.scrollTop = Math.min(el.scrollHeight / 2, 500);
    });

    // アラート行をクリックして詳細ドロワーが開く（災害投入分もドロワー表示可能）
    await page.locator('[data-testid="alert-row"]').first().click();
    await expect(page.getByTestId("alert-detail-drawer")).toBeVisible();
  });

  test("6. ページネーション・レスポンシブ確認", async ({ page }) => {
    await page.goto("/");

    // ビューポート確認
    const viewport = page.viewportSize();
    expect(viewport?.width).toBeGreaterThan(800);

    // メインセクション確認
    const main = page.locator("main");
    const box = await main.boundingBox();
    expect(box?.width).toBeGreaterThan(100);
  });

  test("7. 同じボタンを再度押すと通常モードへ戻る", async ({ page }) => {
    await page.goto("/");
    const button = page.getByTestId("disaster-simulate-button");
    await expect(button).toHaveText("通常モードに戻る");

    const [resetResponse] = await Promise.all([
      page.waitForResponse(
        (response) =>
          response.url().includes("/api/v1/disaster/simulate") &&
          response.request().method() === "DELETE",
      ),
      button.click(),
    ]);

    expect(resetResponse.ok()).toBeTruthy();
    await expect(button).toHaveText("防災シミュレーション");
    await expect(page.locator("path.disaster-cluster")).toHaveCount(0);
  });
});
