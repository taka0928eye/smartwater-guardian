/**
 * BE-7: 防災モード E2E テスト（シナリオ 9）。
 *
 * シナリオ 9（防災モード）: ダッシュボードの「防災シミュレーション」ボタンで
 * Level 3 破裂を一括投入（POST /api/v1/disaster/simulate）し、被災エリアクラスタの
 * Polygon が地図に描画されることを検証する。
 *
 * - クラスタ Polygon は `path.disaster-cluster`（DisasterOverlay の clusterStyle が
 *   `className: "disaster-cluster"` を付与）で特定する。
 * - simulate 後に DashboardClient が refresh() で即時再取得するため、5 秒ポーリングを
 *   待たずにクラスタが描画される。
 * - クラスタ中心（35.6812, 139.7671 起点）は地図の既定ビュー（全消火栓の重心）から
 *   東側に生成されるため、**ズームアウトして描画範囲に入れてから**検証する
 *   （map.spec.ts と同じく、Leaflet は画面外の path を `d="M0 0"` で非描画にするため）。
 * - クラスタ popup には「想定断水世帯」「優先閉栓バルブ」が表示される。
 */
import { test, expect } from "./fixtures";
import { DashboardPage } from "./pages/DashboardPage";

test.describe("防災モード（BE-7）", () => {
  test("防災シミュレーションで被災エリアクラスタが地図に描画される", async ({
    page,
  }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    await expect(dashboard.map).toBeVisible();

    // 「防災シミュレーション」ボタンをクリック → simulate API + クラスタ即時反映
    await dashboard.simulateDisasterButton.click();

    // クラスタ中心は既定ビューの東側にあるため、ズームアウトして描画範囲に入れる
    await page.locator(".leaflet-control-zoom-out").click();

    // クラスタ Polygon が実描画される（refresh 直後 + ズームアニメーション収束を待つ）
    await expect(dashboard.disasterClusters.first()).toBeVisible({
      timeout: 15_000,
    });
  });

  test("クラスタ Polygon のポップアップに想定断水世帯・優先閉栓バルブが表示される", async ({
    page,
  }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();

    await dashboard.simulateDisasterButton.click();
    await page.locator(".leaflet-control-zoom-out").click();

    const cluster = dashboard.disasterClusters.first();
    await expect(cluster).toBeVisible({ timeout: 15_000 });

    // クラスタ Polygon をクリックしてポップアップを開く。
    // Leaflet の SVG path はヒットテストでクリック判定されるため、実描画範囲をクリックする。
    await cluster.click();
    await expect(dashboard.disasterPopup).toBeVisible();
    await expect(dashboard.disasterPopup).toContainText("想定断水世帯");
    await expect(dashboard.disasterPopup).toContainText("優先閉栓バルブ");
    // クラスタ ID（CLS-xxx）も表示される
    await expect(dashboard.disasterPopup).toContainText(/CLS-\d{3}/);
  });
});

