# Code Summary — BU-1（FE-7: KPIサマリの実データ連携と「試算値」注記）

| 項目 | 内容 |
|------|------|
| ユニット | `BU-1`（GitHub Issue #19 / FE-7、フロントエンドのみ） |
| テスト戦略 | Minimal（要求駆動）+ カバレッジ 80% 充足 |
| 手法 | TDD（Red → Green → Refactor）を全ステップで徹底 |
| 会話言語 | 日本語（NFR-4） |

## 生成・変更ファイル

| 種別 | ファイル | 内容 |
|------|----------|------|
| 新規フック | `frontend/src/hooks/useKpiPolling.ts` | `intervalMs` 間隔で `fetchKpiSummary` をポーリング。成功時のみ `kpiData` セット、失敗時は値を破棄して再スケルトン（FR-8）。`cancelled` + `clearInterval` でクリーンアップ |
| 新規テスト | `frontend/src/hooks/__tests__/useKpiPolling.test.ts` | 即時取得 / 再取得 / 失敗時値破棄 / 失敗→成功復帰 / アンマウント後 setState 抑止（cancelled ブランチを手動 Promise 制御でカバー） |
| 型 | `frontend/src/types/api.ts` | `SeverityLevel` を `lib/severity.ts` からの再エクスポートへ単一ソース化（FR-2）。`KpiSummary` 型（7 フィールド camelCase）を追加（FR-1） |
| ユーティリティ | `frontend/src/lib/severity.ts` | 陳腐コメント（L12-13「API 型の SeverityLevel(1|2|3)」）を現状（`0|1|2|3`・単一ソース）に更新 |
| API クライアント | `frontend/src/lib/api.ts` | `fetchKpiSummary(): Promise<KpiSummary>` を追加（FR-3）。`unwrap<KpiSummary>(apiClient.get('/api/v1/kpi/summary'))` で snake_case→camelCase を境界で 1 回変換（C-3） |
| コンポーネント | `frontend/src/components/dashboard/KpiSummary.tsx` | `KpiData` interface を廃止し `KpiSummaryData = KpiSummary` 別名へ（`todayDetections` 除去）。5 カード降順（センサー数 / L3 / L2 / L1 / 推定削減コスト）。Level 1 に `getSeverityMeta(1).accentClass`（lime）。コストカードに「試算値」+「前提: docs/business-model.md」の 2 段注記を常時表示（FR-5/FR-6） |
| コンポーネント | `frontend/src/components/dashboard/DashboardClient.tsx` | `useKpiPolling(ALERT_POLL_INTERVAL_MS)` を接続。KPI section のランドマーク（`section[aria-labelledby="kpi-summary-title"]` / `h2`「KPI サマリ」/ `aria-busy`）を一元所有。`kpi-skeleton` スケルトン ↔ カードグリッドを切替（FR-7/FR-8） |
| ページ | `frontend/src/app/page.tsx` | `MOCK_KPI_DATA` / `<KpiSummary kpiData={MOCK_KPI_DATA} />` を削除（FR-4）。**Server Component のまま維持**（C-2） |
| テスト | `frontend/src/lib/__tests__/api.test.ts` | `fetchKpiSummary` の camelCase 変換 / ApiError（500）/ 非 axios 透過の 3 テスト追加 |
| テスト | `frontend/src/components/dashboard/__tests__/KpiSummary.test.tsx` | 新契約（`KpiSummaryData` 5 フィールド）へ全面書き換え（12 テスト）。5 カード降順・lime・試算値 2 段注記（正規表現 `/試算値[\s\S]*前提: docs\/business-model\.md/` でカード内順序検証）・全 0 表示 |
| テスト | `frontend/src/components/dashboard/__tests__/DashboardClient.test.tsx` | `vi.mock("@/lib/api")` に `fetchKpiSummary` を追加（既存 5 テスト維持）。ランドマーク / スケルトン切替 / 失敗時再スケルトンの 3 テスト追加 |
| テスト | `frontend/src/app/__tests__/page.test.tsx` | `vi.mock("@/lib/api")` に `fetchKpiSummary` を追加。モック KPI 由来数値（1,420,000 / 1,240 等）が描画されないことを検証 |
| 設定（**スコープ追加**） | `frontend/vitest.config.mts` | `coverage: { enabled: true, thresholds: { lines: 80, functions: 80, branches: 80, statements: 80 } }` を追加（NFR-1。Plan Approval で承認済み） |
| 設定（**スコープ追加**） | `.github/workflows/ci.yml` | Vitest ステップを `npx vitest run --coverage --coverage.thresholds.*=80` → `npm run test` に簡素化（thresholds 単一ソース化。NFR-1。Plan Approval で承認済み） |

## 主要な実装決定

- **`SeverityLevel` の単一ソース化（FR-2 / Q9=A）**: `lib/severity.ts` を本拠とし、契約層 `types/api.ts` から `export type { SeverityLevel }` で再エクスポート。`type SeverityLevel` の定義は grep で 1 件のみ（Refactor 3-1 で確認）。
- **ポーリング失敗時の再スケルトン（FR-8 / T3）**: `useAlertPolling` と対称の専用フック `useKpiPolling` を新設（application-design:c5: 共通化より責務分離を優先）。取得失敗時は古い `kpiData` を**破棄**し `isLoading=true` へ戻す（stale 値を最新として見せない）。
- **KPI ランドマークの一元所有（refined-mockups:c4 / application-design:c1）**: `section` / `h2` / `aria-labelledby` / `aria-busy` は常時描画される `DashboardClient` が所有し、配下でスケルトンかカードグリッドを切替。スケルトン中も h2 とランドマークを維持。
- **表示ラベルの固定化（application-design:c6）**: カード見出しは承認済み表示文言の固定値とし、表示メタ（`SEVERITY_META`）の label とは分離。
- **Issue 前提の陳腐化（requirements-analysis:c2）**: Issue #19 の「SeverityLevel を 1|2|3 に修正」は FE-5（commit 69da0ff）で既に `0|1|2|3` へ解消済みのため実施せず、二重定義解消とコメント更新のみに限定。
- **試算値注記の 2 段構成（refined-mockups:c1）**: 見出しラベル「試算値」+ 本文「前提: docs/business-model.md」を常時表示。FR-6 の結合リテラルは詳細化後の 2 段構成を言い表したものと解釈。
- **`assumptionDoc` / `isEstimate` は契約のみ**: BE-8 契約として型・API で受け取るが、表示には使わない（FR-6 / ADR-004 引継ぎ）。
- **カバレッジゲート恒久化（NFR-1）**: `vitest.config.mts` の thresholds を単一ソースとし、ローカル `npm run test` と CI のゲートを一致（team-practices Q3=A）。CI の冗長 CLI フラグを撤去。

## テストカバレッジ

- 全テスト: **11 ファイル / 91 テスト 全 Green**（`npm run test` = `vitest run`）。
- カバレッジ 4 指標（グローバル閾値 80%）:
  - Statements: **93.11%**（203/218）/ Branches: **84.15%**（85/101）/ Functions: **90.12%**（73/81）/ Lines: **94.02%**（189/201）
- FE-7 対象ファイルの個別カバレッジ（HTML レポートより、すべて ≥80%）:
  - `useKpiPolling.ts` 100% / `KpiSummary.tsx` 100% / `app/page.tsx` 100% / `DashboardClient.tsx` 92.85% / `lib/api.ts` 100% / `lib/severity.ts` 83.33% / `types/api.ts` 計測対象外（型のみ）
- **対象ファイルの 80% 未達はゼロ**。カバレッジ充足のため、`useKpiPolling.ts` の cancelled ブランチ（アンマウント後 in-flight 成功/失敗で setState しない）を手動 Promise 制御のテストで追加（branches 50% → 100%）。
- 既存の非スコープファイル（`SensorMap.tsx` / `Header.tsx` / `useAlertPolling.ts`）は個別には 80% 未満だが、グローバル閾値のためゲートは通過（今回のスコープ外として据え置き）。

## プランからの逸脱

- **スコープ追加（承認済み）**: `vitest.config.mts` / `.github/workflows/ci.yml` は C-1（Issue 記載の 6 ファイル）対象外だが、NFR-1「カバレッジゲート恒久化」のため必須。code-generation-questions.md の Plan Approval でユーザー確認（Approve Plan）済み。
- **`todayDetections` カードは削除**（BE-8 契約上 FE-7 以降の項目。intent-capture:c3 参照）。
- **コミットは未実施**（ユーザー指示なし。Build and Test 完了後のコミットを想定）。
- **その他の逸脱なし**。計画 5 ステップ（Red → Green → Refactor → NFR-1 → 自走確認）を完遂。
