# FE-8: Playwright によるE2Eテストの実装

## 目的

FE-5（アラート一覧・詳細ドロワー）/ FE-7（KPIサマリ実データ連携）が完成した後、**ユーザーシナリオ全体の動作を自動検証するE2Eテストスイート**を構築する。手動リハーサルの負担軽減と、デモ本番への前夜検証を実現する。

## スコープ

### テスト対象シナリオ
1. **ダッシュボード初期表示**: KPIサマリ・センサー地図・アラート一覧が読み込まれる
2. **センサー地図インタラクション**: マーカークリックでアラート詳細ドロワーが表示される
3. **アラート一覧フィルタリング・ソート**: 深刻度・日時による操作が反映される
4. **詳細ドロワー内容表示**: スペクトル（FE-4）を含む詳細情報が表示される
5. **バックエンド未応答時のフォールバック**: 画面が白紙にならずフォールバックデータで描画される
6. **ポーリング動作**: KPI / アラート一覧の自動更新が動作する（5秒ごと）

### テスト対象外
- ユニットテスト（既に Vitest + Testing Library で実施）
- ビジュアルリグレッション（デザイン微細変更の頻度を考慮し、後続タスクで別途検討）
- パフォーマンステスト（FE-6 の最適化タスクとして後回し）

## 変更予定ファイル

| ファイル | 種別 | 内容 |
|---|---|---|
| `frontend/playwright.config.ts` | 新規 | Playwright 設定 |
| `frontend/tests/e2e/dashboard.spec.ts` | 新規 | ダッシュボードシナリオ |
| `frontend/tests/e2e/alerts.spec.ts` | 新規 | アラート一覧・詳細 |
| `frontend/tests/e2e/map.spec.ts` | 新規 | センサー地図インタラクション |
| `frontend/package.json` | 修正 | `npm run e2e` スクリプト追加 |
| `frontend/.env.e2e` | 新規 | E2E 環境変数（バックエンドURL等） |
| `frontend/.env.e2e.example` | 新規 | サンプル |
| `docs/e2e-runbook.md` | 新規 | E2E テスト実行手順 |

## 実装方針

### 1. セットアップ
- `npm install -D @playwright/test` を `package.json` に追加
- `playwright.config.ts`: 
  - `baseURL`: 環境変数 `PLAYWRIGHT_BASE_URL`（デフォルト `http://localhost:3000`）
  - Headless mode デフォルト（ローカル開発時は `--headed` で起動可能）
  - タイムアウト: 30秒（ネットワーク遅延を想定）
  - Screenshots / Videos オンスクリーンフェイル時に記録
  - 並列実行: 4ワーカー

### 2. フィクスチャ設計
```typescript
// tests/e2e/fixtures.ts
export type TestOptions = {
  apiBaseUrl: string;
  skipBackendCheck: boolean;  // バックエンド未応答時をテスト
};

export const test = base.extend<TestOptions>({
  // セットアップ: バックエンドのヘルスチェック等
});
```

### 3. テストケース例

#### `dashboard.spec.ts`
- 初期ロード: KPI カード・地図・アラート一覧が表示される
- スケルトン → 実データへの遷移が正常
- バックエンド未応答時: フォールバックデータで描画される
- 5秒ごとのポーリング: 新しいアラートが追加される

#### `alerts.spec.ts`
- 一覧表示: Level 1 / 2 / 3 アラートが色分けされて表示
- ソート: 日時・深刻度による並び替えが反映
- 詳細ドロワー: マーカー / 一覧行クリック両方で表示
- スペクトルチャート（FE-4）が描画される
- ドロワー内のスクロール・リサイズ

#### `map.spec.ts`
- マーカー表示: GeoJSON から正しい位置にマーカーが配置
- マーカークリック → ドロワー表示の連鎖
- ズーム・パン操作

### 4. ポーリング・タイミングの扱い
```typescript
// 例: ポーリング検証
test('KPI should refresh every 5 seconds', async ({ page }) => {
  const initialValue = await page.locator('[data-testid="kpi-total-sensors"]').textContent();
  
  // バックエンドに新データを投入（seed_demo.py 等）
  await seedNewAlert();
  
  // 5秒待つ + 遅延を考慮して余裕を持たせる
  await page.waitForTimeout(6000);
  
  const updatedValue = await page.locator('[data-testid="kpi-total-sensors"]').textContent();
  expect(updatedValue).not.toBe(initialValue);
});
```

### 5. バックエンド未応答シミュレーション
```typescript
// tests/e2e/fixtures.ts
export const test = base.extend<TestOptions>({
  async skipBackendCheck({ }, use, testInfo) {
    if (testInfo.title.includes('[offline]')) {
      // ネットワークインターセプト: API 呼び出しを遮断
      // フォールバック描画が発動することを検証
    }
    await use();
  },
});
```

## 作業内容

### 【Step 1】Red — 失敗するテストを先に書く
- [ ] `playwright.config.ts` を作成
- [ ] `tests/e2e/dashboard.spec.ts` を作成し、全テストが RED になることを確認
  - [ ] 初期ロード
  - [ ] ポーリング動作
  - [ ] バックエンド未応答時
- [ ] `tests/e2e/alerts.spec.ts` を作成（RED 確認）
- [ ] `tests/e2e/map.spec.ts` を作成（RED 確認）
- [ ] `npm run e2e` コマンドで全て RED になることを確認

### 【Step 2】Green — テストを通す実装
- [ ] 必要に応じてコンポーネントに `data-testid` を追加（セレクタ安定化）
  - 例: `data-testid="kpi-card-total-sensors"`, `data-testid="alert-row-{telemetryId}"` 等
- [ ] Playwright テストが GREEN になるよう調整
- [ ] **テスト用にバックエンドの mock / stub は作らない**（FE-5 / FE-7 / BE-6 等の実装が前提）
- [ ] 全テスト GREEN を確認

### 【Step 3】Refactor — 拡張性確保と文書化
- [ ] ページオブジェクトモデル（POM）を導入
  ```typescript
  // tests/e2e/pages/DashboardPage.ts
  export class DashboardPage {
    constructor(page: Page) { this.page = page; }
    async goto() { await this.page.goto('/'); }
    async getKpiValue(label: string) { ... }
    async clickAlertRow(index: number) { ... }
  }
  ```
- [ ] テストヘルパー: `waitForPoll()`, `interceptBackendError()` 等を共通化
- [ ] `docs/e2e-runbook.md` を作成（実行手順・CI 統合予定・トラブルシューティング）
- [ ] `package.json` に `npm run e2e` / `npm run e2e:debug` / `npm run e2e:headed` を追加

### 【Step 4】CI 統合準備（後続タスク枠）
- [ ] GitHub Actions ワークフロー作成（`.github/workflows/e2e.yml`）
- [ ] 本番ビルド後に E2E 実行
- [ ] Artifact 保存（失敗時のスクリーンショット・ビデオ）
- [ ] **このタスクでは実装しない。後続タスク「CI-1: E2E テスト自動実行」で実施**

### 自走確認
- [ ] `npm run e2e` で全テスト GREEN
- [ ] `npm run e2e:headed` で実挙動が目視確認できる
- [ ] ローカル・CI 共通コマンドで同一結果

## 受け入れ条件
- [ ] `npm install -D @playwright/test` が正常に実行できる
- [ ] `npm run e2e` で全テストが GREEN
- [ ] 各テストスイート（dashboard / alerts / map）のカバレッジが網羅的
- [ ] バックエンド起動状態・未応答状態の両方で検証済み
- [ ] スクリーンショット・ビデオが自動保存される（オプション）
- [ ] ページオブジェクトモデルにより テスト保守性が確保されている
- [ ] `docs/e2e-runbook.md` に実行手順・トラブルシューティングが記載されている
- [ ] **ローカル・CI の両環境で同一コマンド・同一結果**
- [ ] E2E テストの実行時間が 2 分以内（4 ワーカー並列）

## 検証方法

```powershell
# 環境構築
cd frontend
npm install -D @playwright/test
cp .env.e2e.example .env.e2e

# ローカル実行
# ターミナル1: フロントエンド起動
npm run dev

# ターミナル2: バックエンド起動（別フォルダ）
cd ../backend
venv/Scripts/uvicorn.exe main:app --reload --port 8000

# ターミナル3: E2E テスト実行
cd ../frontend
npm run e2e

# Headed モード（ブラウザ表示）
npm run e2e:headed

# 単一ファイル実行
npm run e2e -- tests/e2e/dashboard.spec.ts

# デバッグモード
npm run e2e:debug
```

## 依存関係
- **前提**: FE-5, FE-7, BE-6 が実装済み（テスト対象機能）
- **後続**: CI-1（GitHub Actions による E2E 自動実行）

---

- **優先度**: P1
- **想定日**: 8/15 〜 8/16
- **関連**: FE-5 / FE-7 / BE-6 / docs/demo-runbook.md（デモ検証の一部）
- **参考**: https://playwright.dev/docs/intro, Vitest との共存方法
