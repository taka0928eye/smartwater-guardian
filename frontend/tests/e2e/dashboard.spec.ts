/**
 * FE-8: ダッシュボード E2E テスト（シナリオ 1・6）。
 *
 * シナリオ 1（初期表示）: KPI サマリ・センサー地図・アラート一覧が読み込まれる。
 * シナリオ 6（ポーリング）: KPI / アラート一覧が 5 秒間隔で自動更新される。
 *
 * 前提: `tests/e2e/global-setup.ts` がデモシード（L3×1 / L2×1 / L1×2 / L0×1）を投入済み。
 * シードの厳密な件数は、並列実行で他スペックがストアへ追加する可能性を考慮し、
 * 深刻度別に「以上」または実シード確定値の範囲で検証する。
 */
import { test, expect } from "./fixtures";
import { DashboardPage } from "./pages/DashboardPage";
import { seedAlert } from "./helpers";

test.describe("ダッシュボード初期表示（シナリオ 1）", () => {
  test("KPI サマリ・センサー地図・アラート一覧が読み込まれる", async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();

    // ヘッダー（SmartWater Guardian タイトル）
    await expect(dashboard.title).toBeVisible();

    // KPI サマリ（FE-7）: 5 枚のカードが描画される
    await expect(dashboard.kpiSensors).toBeVisible();
    await expect(dashboard.kpiLevel3).toBeVisible();
    await expect(dashboard.kpiLevel2).toBeVisible();
    await expect(dashboard.kpiLevel1).toBeVisible();
    await expect(dashboard.kpiCost).toBeVisible();

    // センサー地図（FE-3）: セクション見出しと Leaflet コンテナ
    await expect(page.getByRole("heading", { name: "センサー地図" })).toBeVisible();
    await expect(dashboard.map).toBeVisible();

    // アラート一覧（FE-5）: シード済みアラートの行が描画される
    await expect(dashboard.alertRows.first()).toBeVisible();
  });

  test("KPI スケルトン → 実データカードへ遷移する", async ({ page }) => {
    // KPI レスポンスを少し遅延させ、スケルトン表示を確実に観測できるようにする
    // （レスポンス自体は実データをそのまま通す）。
    await page.route("**/api/v1/kpi/summary", async (route) => {
      const response = await route.fetch();
      await new Promise((resolve) => setTimeout(resolve, 1500));
      await route.fulfill({ response });
    });

    const dashboard = new DashboardPage(page);
    await dashboard.goto();

    // 初回はスケルトン（h2・ランドマークは維持される）
    await expect(dashboard.kpiSkeleton).toBeVisible();
    // 取得成功後はカードグリッドへ切り替わる
    await expect(dashboard.kpiSensors).toBeVisible({ timeout: 10_000 });
    await expect(dashboard.kpiSkeleton).not.toBeVisible();
  });

  test("KPI 実データ値（深刻度別件数・推定削減コスト）が反映される", async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();

    // シード確定値: Level 3×1 / Level 2×1（他スペックが追加しないため厳密検証）
    await expect(dashboard.kpiLevel3).toContainText("1件");
    await expect(dashboard.kpiLevel2).toContainText("1件");
    // Level 1 はシード 2 件 + ポーリング検証で追加されるため「2 件以上」で検証
    await expect(dashboard.kpiLevel1).toContainText(/[2-9]\d*件/);

    // 推定削減コスト: 万円表記 + 試算値の 2 段注記（FR-6）
    await expect(dashboard.kpiCost).toContainText("万円");
    await expect(dashboard.kpiCost).toContainText("試算値");
    await expect(dashboard.kpiCost).toContainText("前提:");
  });
});

test.describe("ポーリング動作（シナリオ 6）", () => {
  test("アラート一覧が 5 秒間隔でポーリングされ、新着アラートが自動反映される", async ({
    page,
    request,
  }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    await dashboard.waitForAlertList();

    // シード未使用の消火栓（HYD-007）へ Level 1 を 1 件投入する
    await seedAlert(request, "HYD-007", { level: 1 });

    // 5 秒間隔のポーリング（+ 遅延を考慮した余裕）で、新着行が自動表示される
    const newRow = dashboard.alertRow("HYD-007");
    await expect(newRow).toBeVisible({ timeout: 8_000 });
  });
});
