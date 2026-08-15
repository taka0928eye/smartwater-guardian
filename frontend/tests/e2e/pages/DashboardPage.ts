/**
 * FE-8: ダッシュボードのページオブジェクトモデル（POM）。
 *
 * セレクタをテスト本体から分離し、保守性を確保する（受入条件）。
 * セレクタは実装（data-testid / role / Leaflet クラス）に依存するため、
 * コンポーネントの構造変更時は本ファイルのみ修正すればよい。
 */
import type { Locator, Page } from "@playwright/test";

export class DashboardPage {
  constructor(private readonly page: Page) {}

  /** ダッシュボードルートを開く。 */
  async goto(): Promise<void> {
    await this.page.goto("/");
  }

  /** ヘッダー見出し（SmartWater Guardian タイトル）。 */
  get title(): Locator {
    return this.page.getByRole("heading", {
      name: /SmartWater Guardian/,
    });
  }

  // --- KPI サマリ（FE-7） ---

  get kpiSensors(): Locator {
    return this.page.getByTestId("kpi-card-sensors");
  }

  get kpiLevel1(): Locator {
    return this.page.getByTestId("kpi-card-level1");
  }

  get kpiLevel2(): Locator {
    return this.page.getByTestId("kpi-card-level2");
  }

  get kpiLevel3(): Locator {
    return this.page.getByTestId("kpi-card-level3");
  }

  get kpiCost(): Locator {
    return this.page.getByTestId("kpi-card-cost");
  }

  /** 取得中（初回・失敗後の再取得待ち）に表示されるスケルトン。 */
  get kpiSkeleton(): Locator {
    return this.page.getByTestId("kpi-skeleton");
  }

  // --- アラート一覧（FE-5） ---

  /** アラート行の一覧（深刻度降順にソート済み）。 */
  get alertRows(): Locator {
    return this.page.getByTestId("alert-row");
  }

  /**
   * 指定した消火栓 ID のアラート行。
   *
   * DEMO-2: バックエンド起動時の自動初期化（`initialize_sensors()`。20件Lv0）と
   * `global-setup.ts` の `POST /alerts/seed`（実在マスタ HYD-001〜010 を再利用）が
   * 同じセンサーIDに対して別レコードを投入しうるため、同一 hydrantId で複数行が
   * ヒットする場合がある（`list_alerts()` はセンサー単位で重複排除しない設計）。
   * `.first()` で最新（深刻度降順ソートの先頭）の1件に絞り、Playwright の
   * 厳格モード（複数要素マッチ時のエラー）を回避する。
   */
  alertRow(hydrantId: string): Locator {
    return this.alertRows.filter({ hasText: hydrantId }).first();
  }

  /** アラート一覧が描画されるまで待つ。 */
  async waitForAlertList(): Promise<void> {
    await this.alertRows.first().waitFor();
  }

  /** 指定した消火栓 ID の行をクリックして詳細ドロワーを開く。 */
  async openAlert(hydrantId: string): Promise<void> {
    await this.alertRow(hydrantId).click();
  }

  // --- 詳細ドロワー（FE-5 / FE-4 / FE-6） ---

  get drawer(): Locator {
    return this.page.getByTestId("alert-detail-drawer");
  }

  // --- センサー地図（FE-3） ---

  get map(): Locator {
    return this.page.locator(".leaflet-container");
  }

  /** Leaflet マーカー（CircleMarker は SVG path として描画される）。 */
  get mapMarkers(): Locator {
    return this.page.locator("path.leaflet-interactive");
  }

  /**
   * 画面内に実描画されたマーカー。
   * Leaflet は画面外マーカーを `d="M0 0"`（非描画）にするが、ストローク分の
   * 境界ボックスが残るため Playwright の「可視」判定では除外できない。
   * 実描画マーカーは `d` 属性が `M0 0` 以外になる CSS で確定できる。
   */
  get mapDrawnMarkers(): Locator {
    return this.page.locator('path.leaflet-interactive:not([d="M0 0"])');
  }

  // --- 防災モード（BE-7） ---

  /** 「防災シミュレーション」実行ボタン（Level 3 を一括投入する）。 */
  get simulateDisasterButton(): Locator {
    return this.page.getByTestId("disaster-simulate-button");
  }

  /**
   * 被災エリアクラスタの Polygon（SVG path）。
   * DisasterOverlay の clusterStyle が `className: "disaster-cluster"` を付与するため、
   * `path.disaster-cluster` で特定できる。
   */
  get disasterClusters(): Locator {
    return this.page.locator("path.disaster-cluster");
  }

  /** クラスタ Polygon クリックで開くポップアップ本文。 */
  get disasterPopup(): Locator {
    return this.page.locator(".leaflet-popup-content");
  }
}
