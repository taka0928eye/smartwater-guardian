# Unit Test Instructions — BU-1（FE-7: KPIサマリの実データ連携と「試算値」注記）

> 本指示書は `code-generation-plan.md`（Step 1【Red】テスト一覧）と `code-summary.md`
> （実装・テストファイル一覧）に基づく、ユニットテストの実行手順書。
> テスト戦略 **Standard**（aidlc-state §`**Test Strategy**`）: 各コンポーネント 5-8 テストの主要挙動カバレッジ。

## 1. テストフレームワークと設定

- **フレームワーク**: Vitest 4.1.10 + Testing Library（`@testing-library/react` / `@testing-library/jest-dom`）
- **環境**: デフォルト `node`。tsx のコンポーネントテストはファイル先頭 `// @vitest-environment jsdom`
- **カバレッジ**: `vitest.config.mts` の `coverage.thresholds`（lines / functions / branches / statements 各 80%）を単一ソースに強制（NFR-1）
- **セットアップ**: `src/test/setup.ts`（jest-dom マッチャー読み込み）

## 2. 実行コマンド

```powershell
cd frontend
npm run test          # vitest run（カバレッジ計測 + 80% ゲート強制）
npm run test -- <pattern>   # 特定ファイルのみ（例: npm run test -- KpiSummary）
```

## 3. 対象と期待カバレッジ

| ユニット | 対象ファイル | テストファイル | テスト数 | 期待カバレッジ |
|----------|--------------|----------------|---------|----------------|
| KPI 型契約 | `src/types/api.ts` | （型のみ。計測対象外） | — | 型検査で担保 |
| API クライアント | `src/lib/api.ts` | `src/lib/__tests__/api.test.ts` | 12（うち FE-7 で 3 追加） | 100% |
| 表示メタ | `src/lib/severity.ts` | 同上 | — | 83.33% |
| KPI ポーリングフック | `src/hooks/useKpiPolling.ts` | `src/hooks/__tests__/useKpiPolling.test.ts` | 5（新規） | 100% |
| KPI サマリ表示 | `src/components/dashboard/KpiSummary.tsx` | `src/components/dashboard/__tests__/KpiSummary.test.tsx` | 12 | 100% |
| ダッシュボード統合 | `src/components/dashboard/DashboardClient.tsx` | `src/components/dashboard/__tests__/DashboardClient.test.tsx` | 8（うち FE-7 で 3 追加） | 92.85% |
| ルート | `src/app/page.tsx` | `src/app/__tests__/page.test.tsx` | 4 | 100% |

> 全 11 ファイル / 91 テスト。カバレッジ実測は `build-test-results.md` 参照（全 4 指標 80% 超）。

## 4. 主要なテストケース（要求駆動）

### 4.1 `lib/api.ts` — fetchKpiSummary（US-1 / FR-3）
- [ ] GET `/api/v1/kpi/summary` を呼び、snake_case 7 フィールドを camelCase へ変換して返す
- [ ] HTTP 500 を `ApiError` に変換して throw する
- [ ] axios 以外のエラーは透過で throw する

### 4.2 `hooks/useKpiPolling.ts` — ポーリング（US-3 / FR-7・FR-8）
- [ ] 即時 `fetchKpiSummary` が呼ばれ、成功で `kpiData` セット・`isLoading=false`
- [ ] `intervalMs` 経過で再取得され `kpiData` が更新される
- [ ] 取得失敗時 `kpiData=null`・`isLoading=true`（再スケルトン。FR-8 / T3）
- [ ] 失敗→次回成功で復帰・`isLoading=false`
- [ ] アンマウントで `cancelled` + `clearInterval`（以後 setState しない）

### 4.3 `KpiSummary.tsx` — 表示（US-2 / FR-5・FR-6）
- [ ] 5 カードを降順（センサー数 / L3 / L2 / L1 / 推定削減コスト）で描画
- [ ] `totalSensors` を桁区切り + 台で表示（固定値でない）
- [ ] Level 1 に lime（`getSeverityMeta(1).accentClass`）が適用される
- [ ] コストカードに「試算値」+「前提: docs/business-model.md」の 2 段注記が常時表示
  （正規表現 `/試算値[\s\S]*前提: docs\/business-model\.md/` でカード内順序検証）
- [ ] `estimatedCostSavedYen: 2_048_400` → 「204.8万円」（formatManYen）
- [ ] 全値 0 でも表示崩れしない

### 4.4 `DashboardClient.tsx` — ランドマーク・スケルトン切替（US-3 / FR-7）
- [ ] KPI section のランドマーク（`section[aria-labelledby="kpi-summary-title"]` / `h2` / `aria-busy`）が常時存在
- [ ] `kpi-skeleton` ↔ カードグリッドの切替（初回スケルトン → 成功でカード）
- [ ] ポーリング失敗時の再スケルトン（stale 値非表示）

### 4.5 `app/page.tsx` — サーバーコンポーネント（US-2 / FR-4）
- [ ] 実データを DashboardClient（SensorMap）へ渡して描画
- [ ] 取得失敗時フォールバック（モック GeoJSON）で描画
- [ ] モック KPI 由来の固定数値（`1,420,000` / `1,240` 等）が描画されない

## 5. テストデータ管理

- テストフィクスチャは各テストファイル内に定義（`vi.mock("@/lib/api")` で `fetchKpiSummary` を解決値にモック）。
- シリアル実行前提なし。`act()` + フェイクタイマー（`vi.useFakeTimers`）でポーリングを制御。
- テスト分離はファイルごとの `vi.clearAllMocks()` / フェイクタイマー復元で担保（autouse フィクスチャのバックエンド版は `conftest.py`。フロントは Vitest のセットアップで管理）。

## 6. カバレッジ目標

- **4 指標（lines / functions / branches / statements）各 80% 以上**（NFR-1。ローカル = CI = `vitest.config.mts` thresholds）。
- FE-7 対象ファイルは個別に 80% 以上を維持（`useKpiPolling.ts` / `KpiSummary.tsx` / `page.tsx` / `lib/api.ts` は 100%）。
- ゲート失敗時は未達ファイルの HTML レポート（`coverage/`）で不足行を特定し、テストを追加する。
