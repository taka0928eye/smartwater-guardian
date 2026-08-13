/**
 * FE-8: アラート一覧・詳細ドロワー E2E テスト（シナリオ 3・4）。
 *
 * シナリオ 3（一覧のフィルタ・ソート）: 深刻度降順ソート、Level 0 トグル。
 * シナリオ 4（詳細ドロワー）: 選択行の詳細（分析結果・スペクトル・波形・配管情報）表示。
 *
 * 前提: `tests/e2e/global-setup.ts` が L3(HYD-300)/L2(HYD-200)/L1×3/HYD-100(L0) を投入済み。
 * L3・L2 は他スペックが追加しないため一覧の上位 2 件は常に確定する。
 */
import { test, expect } from "./fixtures";
import { DashboardPage } from "./pages/DashboardPage";

test.describe("アラート一覧のソート・フィルタ（シナリオ 3）", () => {
  test("深刻度降順でソートされ、Level 0（正常）は既定で非表示", async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    await dashboard.waitForAlertList();

    // 最上位: Level 3 管路破裂（HYD-300）
    await expect(dashboard.alertRows.nth(0)).toContainText("HYD-300");
    await expect(dashboard.alertRows.nth(0)).toContainText("Level 3 管路破裂");

    // 2 番目: Level 2 進行性漏水（HYD-200）
    await expect(dashboard.alertRows.nth(1)).toContainText("HYD-200");
    await expect(dashboard.alertRows.nth(1)).toContainText("Level 2 進行性漏水");

    // 以降は Level 1（シード 3 件 + 並列実行で追加されうる）
    await expect(dashboard.alertRows.nth(2)).toContainText(/Level 1/);

    // 正常（Level 0）は既定で一覧に表示されない
    await expect(dashboard.alertRow("HYD-100")).not.toBeVisible();
  });

  test('「正常も表示」トグルで Level 0 の表示を切り替えられる', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    await dashboard.waitForAlertList();

    const toggle = page.getByTestId("show-level0-toggle");
    await expect(dashboard.alertRow("HYD-100")).not.toBeVisible();

    // チェックで正常（Level 0）も表示される
    await toggle.check();
    await expect(dashboard.alertRow("HYD-100")).toBeVisible();

    // チェックを外すと非表示へ戻る
    await toggle.uncheck();
    await expect(dashboard.alertRow("HYD-100")).not.toBeVisible();
  });
});

test.describe("詳細ドロワー表示（シナリオ 4）", () => {
  test("アラート選択でドロワーが開き、解析結果・スペクトル・波形・配管情報が表示される", async ({
    page,
  }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    await dashboard.openAlert("HYD-300");

    // ドロワーが開く（見出し・アラート識別情報）
    await expect(dashboard.drawer).toBeVisible();
    await expect(dashboard.drawer.getByRole("heading", { name: "アラート詳細" })).toBeVisible();
    await expect(dashboard.drawer).toContainText("HYD-300");
    await expect(dashboard.drawer).toContainText("SEN-300");
    await expect(dashboard.drawer).toContainText("Level 3 管路破裂");
    await expect(dashboard.drawer).toContainText("センサーID");

    // FE-4: 解析結果（卓越周波数）・周波数スペクトル・時間軸波形
    await expect(
      dashboard.drawer.getByRole("heading", { name: "解析結果" }),
    ).toBeVisible();
    await expect(dashboard.drawer).toContainText("卓越周波数");
    await expect(
      dashboard.drawer.getByRole("heading", { name: /周波数スペクトル/ }),
    ).toBeVisible();
    await expect(
      dashboard.drawer.getByRole("heading", { name: "時間軸波形" }),
    ).toBeVisible();

    // 配管情報（BE-6 管台帳参照: HYD-300 → P-300）
    await expect(
      dashboard.drawer.getByRole("heading", { name: "配管情報" }),
    ).toBeVisible();
    await expect(dashboard.drawer).toContainText("管ID");
    await expect(dashboard.drawer).toContainText("P-300");

    // FE-6: AI 自動起票ボタンが表示される
    await expect(
      dashboard.drawer.getByRole("button", { name: /AI自動起票/ }),
    ).toBeVisible();

    // 閉じるボタンでドロワーが閉じる
    await dashboard.drawer.getByTestId("drawer-close").click();
    await expect(dashboard.drawer).not.toBeVisible();
  });
});
