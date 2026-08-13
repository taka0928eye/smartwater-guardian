/**
 * FE-8: センサー地図 E2E テスト（シナリオ 2）。
 *
 * シナリオ 2（地図操作）: マーカー描画・マーカー選択（詳細ドロワー連動）・ズーム操作。
 *
 * 前提: SSR 取得（GET /api/v1/sensors?format=geojson）で 10 基の消火栓マーカーが描画される。
 * Leaflet は**画面外のマーカーを `d="M0 0"`（非描画化）**するため、クリック・カウントの
 * 対象は実描画マーカー（`d` が `M0 0` 以外）を `DashboardPage.mapDrawnMarkers` で選ぶ
 * （`d="M0 0"` でもストローク分の境界ボックスが残り Playwright の可視判定を満たすため、
 *  `filter({ visible: true })` では除外できない）。
 *
 * 既定ビュー（全 10 基の重心 = 中心 / zoom 15）では HYD-004 のマーカーのみ実描画され、
 * シード済みアラート（L2）を持つためクリックでドロワーが開く。
 *
 * ズーム検証は**ズームアウトで実描画マーカーが増える**ことを使う（画面外 9 基が描画範囲に
 * 入るため決定論的。ズームイン直後の pane transform はアニメーション収束で元に戻るため
 * 不安定で、ズームレベルは DOM から直接読めない）。
 *
 * タイル（OSM）はネットワーク環境で読めない場合も灰色になるだけで、SVG マーカーや
 * ズーム操作（描画マーカー数の変化）には影響しないため、オフラインでも検証可能。
 */
import { test, expect } from "./fixtures";
import { DashboardPage } from "./pages/DashboardPage";

test.describe("センサー地図（シナリオ 2）", () => {
  test("マーカーが描画される（10 基の消火栓）", async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();

    await expect(dashboard.map).toBeVisible();
    // GeoJSON から 10 基すべての CircleMarker（SVG path）が生成される
    await expect
      .poll(async () => dashboard.mapMarkers.count(), { timeout: 10_000 })
      .toBe(10);
    // 既定ビューでは実描画マーカーが存在する（画面外マーカーは d="M0 0" で非描画）
    await expect(dashboard.mapDrawnMarkers.first()).toBeVisible();
  });

  test("マーカーをクリックすると詳細ドロワーが開く", async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();

    // マーカー選択はアラート一覧と連動するため、先に一覧の読み込みを待つ
    await dashboard.waitForAlertList();

    // 実描画されたマーカー（既定ビューでは HYD-004 / シード済み L2）をクリックする。
    // HYD-004 は地図下端ギリギリ（円中心がコンテナ下端より下）に位置するため、
    // Playwright の実クリックはヒットテストでコンテナに遮られて失敗する。そこで
    // 実際のユーザー操作と同じ Leaflet のクリック処理経路（パスの DOM イベント →
    // レンダラー点検出 _getLayerAt → レイヤー click → GeoJSON eventHandlers →
    // onSelectMarker）を、マーカー中心の実画面座標を持つ MouseEvent の dispatch で
    // 確実に通す（座標があるため _containsPoint の判定も正常に成立する）。
    const drawnMarker = dashboard.mapDrawnMarkers.first();
    await expect(drawnMarker).toBeVisible();
    await page.evaluate(() => {
      const el = document.querySelector<SVGPathElement>(
        'path.leaflet-interactive:not([d="M0 0"])',
      );
      if (!el) throw new Error("実描画マーカーが見つかりません");
      const rect = el.getBoundingClientRect();
      el.dispatchEvent(
        new MouseEvent("click", {
          bubbles: true,
          cancelable: true,
          view: window,
          clientX: rect.left + rect.width / 2,
          clientY: rect.top + rect.height / 2,
        }),
      );
    });

    // マーカー選択 → アラート一覧と連動して詳細ドロワーが開く（FE-5）
    await expect(dashboard.drawer).toBeVisible();
    await expect(dashboard.drawer).toContainText(/HYD-\d{3}/);
  });

  test("ズームコントロールでズームレベルを変更できる", async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    await expect(dashboard.map).toBeVisible();

    // 既定ビュー（zoom 15）では HYD-004 のみ実描画される。ズームアウトすると
    // 描画範囲が広がり実描画マーカーが増えるため、ズーム変更を決定論的に検証できる。
    const drawnBefore = await dashboard.mapDrawnMarkers.count();
    await expect(drawnBefore).toBeGreaterThanOrEqual(1);

    await page.locator(".leaflet-control-zoom-out").click();
    await expect
      .poll(async () => dashboard.mapDrawnMarkers.count(), { timeout: 10_000 })
      .toBeGreaterThan(drawnBefore);
  });
});
