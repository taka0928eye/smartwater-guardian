# Code Generation Plan — BU-1（FE-7: KPIサマリの実データ連携と「試算値」注記）

> GitHub Issue #19（FE-7）を一次ソースとし、承認済みの unit-of-work §2.2・functional-design
> 2 成果物（business-logic-model / frontend-components）に従って TDD（Red → Green → Refactor）で実装する。
> フロントエンドのみ（C-1、ただしスコープ拡張は上流で解決済み・Plan Approval で確認）。
> **Conversation language: 日本語**

## 0. スコープ（BU-1 境界・unit-of-work §2.1）

| # | ファイル | 種別 | 対応ストーリー |
|---|---|---|---|
| 1 | `frontend/src/types/api.ts` | 修正 | US-1 / US-4 |
| 2 | `frontend/src/lib/severity.ts` | 修正（陳腐コメント更新のみ） | US-4 |
| 3 | `frontend/src/lib/api.ts` | 修正 | US-1 |
| 4 | `frontend/src/hooks/useKpiPolling.ts` | **新規** | US-3 |
| 5 | `frontend/src/components/dashboard/KpiSummary.tsx` | 修正 | US-2 |
| 6 | `frontend/src/components/dashboard/DashboardClient.tsx` | 修正 | US-3 |
| 7 | `frontend/src/app/page.tsx` | 修正 | US-2 / US-3 |
| 8 | `frontend/src/lib/__tests__/api.test.ts` | 修正 | US-1 / US-4 |
| 9 | `frontend/src/components/dashboard/__tests__/KpiSummary.test.tsx` | 修正 | US-2 |
| 10 | `frontend/src/components/dashboard/__tests__/DashboardClient.test.tsx` | 修正 | US-3 |
| 11 | `frontend/src/app/__tests__/page.test.tsx` | 修正 | US-2 / US-3 |
| 12 | `frontend/src/hooks/__tests__/useKpiPolling.test.ts` | **新規** | US-3 |
| 13 | `frontend/vitest.config.mts` | 修正（**スコープ追加**） | NFR-1 |
| 14 | `.github/workflows/ci.yml` | 修正（**スコープ追加**） | NFR-1 |

> 13・14 は C-1（Issue 記載の 6 ファイル）対象外のため、**Plan Approval でユーザー確認**を取る
> （nfr-requirements レビュアー Minor 2 引継ぎ）。NFR-1「ローカルと CI のゲート一致」のため必須。

---

## PART 1 — 実装計画（TDD: Red → Green → Refactor）

### Step 1【Red】失敗するテストを先に書く（テスト戦略: Minimal＋カバレッジ 80% 充足）

- [x] 1-1. `lib/__tests__/api.test.ts` に `fetchKpiSummary` の失敗テストを追加
  - [x] GET `/api/v1/kpi/summary` を呼び、snake_case 7 フィールドを camelCase へ変換して返す
  - [x] axios エラー（HTTP 500）を `ApiError` に変換して throw する
  - [x] axios 以外のエラーはそのまま throw する（透過）
  - [x] `types/api.ts` の `SeverityLevel` が `lib/severity.ts` の再エクスポートであることの確認（型レベル・grep 1 件）
- [x] 1-2. `components/dashboard/__tests__/KpiSummary.test.tsx` を新しい契約（`KpiSummaryData` 5 フィールド）へ書き換え
  - [x] 5 カード（監視センサー数 / L3 / L2 / L1 / 推定削減コスト）を**降順**で描画（`todayDetections` 削除）
  - [x] `data-testid="kpi-card-sensors"` が `totalSensors` を桁区切り + 台で表示（固定値でない）
  - [x] `data-testid="kpi-card-level1"` に lime（`getSeverityMeta(1).accentClass`）が適用される
  - [x] コストカードに「試算値」+「前提: docs/business-model.md」の 2 段注記が常時表示
    （正規表現 `/試算値[\s\S]*前提: docs\/business-model\.md/` でカード内順序検証。project.md c2）
  - [x] `estimatedCostSavedYen: 2_048_400` → 「204.8万円」（ADR-003 フィクスチャ）
  - [x] 値がすべて 0 でも表示崩れしない
- [x] 1-3. `hooks/__tests__/useKpiPolling.test.ts`（新規）の失敗テスト
  - [x] 即時 `fetchKpiSummary` が呼ばれ、成功で `kpiData` / `isLoading=false`
  - [x] `intervalMs` 経過で再取得され `kpiData` が更新される（フェイクタイマー）
  - [x] 取得失敗時 `kpiData=null` / `isLoading=true`（再スケルトン。FR-8・T3 の値破棄）
  - [x] 失敗→次回成功で `kpiData` 復帰・`isLoading=false`（T4）
  - [x] アンマウントで `cancelled` + `clearInterval`（以後 setState しない）
- [x] 1-4. `components/dashboard/__tests__/DashboardClient.test.tsx` の `vi.mock("@/lib/api")` へ `fetchKpiSummary` を追加
  - [x] 既存 5 テストが壊れないこと（`fetchKpiSummary` モックのデフォルト解決）
  - [x] KPI section のランドマーク（`section[aria-labelledby="kpi-summary-title"]` / `aria-busy`）を検証
  - [x] `kpi-skeleton` ↔ カードグリッドの切替（初回スケルトン → 成功でカード）
  - [x] ポーリング失敗時の再スケルトン（stale 値非表示）
- [x] 1-5. `app/__tests__/page.test.tsx` の `vi.mock("@/lib/api")` へ `fetchKpiSummary` を追加
  - [x] 既存 3 テストが壊れないこと
  - [x] `MOCK_KPI_DATA` 由来のハードコード数値（1,420,000 / 1,240 等）が描画されないこと
- [x] 1-6. `npm run test` が **RED**（新テスト失敗・既存テストは Green 維持）になることを確認

### Step 2【Green】最小実装でテストを通す

- [x] 2-1. `lib/severity.ts` の陳腐コメント（L12-13「API 型の SeverityLevel(1|2|3)」）を現状（`0|1|2|3`・types/api.ts は再エクスポート）に更新
- [x] 2-2. `types/api.ts` で `SeverityLevel` の自前再定義を削除し `export type { SeverityLevel } from "../lib/severity"` に変更（FR-2）
- [x] 2-3. `types/api.ts` に `KpiSummary` 型を追加（FR-1: `totalSensors` / `level1Count` / `level2Count` / `level3Count` / `estimatedCostSavedYen` / `isEstimate` / `assumptionDoc` の 7 フィールド camelCase）
- [x] 2-4. `lib/api.ts` に `fetchKpiSummary(): Promise<KpiSummary>` を追加（FR-3: `apiClient.get('/api/v1/kpi/summary')` → `unwrap<KpiSummary>`。境界 1 回変換 C-3）
- [x] 2-5. `KpiSummary.tsx` を改修（FR-5/FR-6）
  - [x] `KpiData` interface を削除し、`KpiSummaryData = KpiSummary` 別名へ置換（`todayDetections` 除去）
  - [x] 5 カードを降順（sensors → level3 → level2 → level1 → cost）に並べ替え
  - [x] Level 1 カードに `getSeverityMeta(1).accentClass`（lime）適用
  - [x] コストカードに 2 段注記（「試算値」見出し + 「前提: docs/business-model.md」本文）を常時表示
  - [x] `formatManYen` は既存のまま維持
- [x] 2-6. `useKpiPolling.ts`（新規）を実装（FR-7/FR-8・functional-design §3.2）
  - [x] `useKpiPolling(intervalMs: number): { kpiData, isLoading }`
  - [x] 即時 `load()` + `setInterval`。成功時のみ `setKpiData` / 失敗時 `kpiData=null` + `isLoading=true`
  - [x] クリーンアップで `cancelled = true` + `clearInterval`
- [x] 2-7. `DashboardClient.tsx` を拡張（FR-7/FR-8・functional-design §3.1）
  - [x] `useKpiPolling(ALERT_POLL_INTERVAL_MS)` を呼び `{ kpiData, isLoading }` を取得
  - [x] KPI section（`section[aria-labelledby="kpi-summary-title"]` / `h2` / `aria-busy`）を一元所有
  - [x] `isLoading` で `data-testid="kpi-skeleton"` のスケルトン ↔ `<KpiSummary kpiData={kpiData}>` を切替
  - [x] 既存 3 列グリッドを包む親ラッパーを追加し、先頭に KPI 全面幅セクションを配置
- [x] 2-8. `page.tsx` から `MOCK_KPI_DATA` / `<KpiSummary kpiData={MOCK_KPI_DATA} />` を削除（FR-4）
  - [x] `KpiSummary` import・`KpiData` type import を削除。Server Component のまま維持（C-2）
- [x] 2-9. `npm run test` が **GREEN** になることを確認

### Step 3【Refactor】GREEN を維持したまま整理

- [x] 3-1. `grep -c "type SeverityLevel" frontend/src` が **1**（`lib/severity.ts` のみ）であることを確認
- [x] 3-2. `grep -rn "1_420_000\|1420000\|1240" frontend/src` が KPI 由来ハードコード **0 件**であることを確認
- [x] 3-3. `MOCK_KPI_DATA` が残っていないことを確認（`grep -rn "MOCK_KPI_DATA" frontend/src` 0 件）
- [x] 3-4. `any` 不使用（TS strict / eslint）を確認
- [x] 3-5. コメント・docstring が日本語・Issue 参照（FE-7）を含むことを確認（NFR-4）

### Step 4【NFR-1】カバレッジゲート恒久化（スコープ追加・要承認）

- [x] 4-1. `vitest.config.mts` に `coverage: { enabled: true, reporter: [...], thresholds: { lines: 80, functions: 80, branches: 80, statements: 80 } }` を追加
  - ローカル `npm run test`（=`vitest run`）でもカバレッジ計測 + 80% ゲートを強制（team-practices Q3=A）
- [x] 4-2. `.github/workflows/ci.yml` の Vitest ステップを `npx vitest run --coverage --coverage.thresholds.*=80` → `npm run test` に簡素化
  - thresholds の単一ソースを vitest.config.mts へ（冗長 CLI フラグ撤去）
- [x] 4-3. `npm run test` で 4 指標 80% 以上を確認（必要ならテスト追加でカバレッジを充足）

### Step 5【自走確認】

- [x] 5-1. `npm run lint` 成功（ESLint）
- [x] 5-2. `npm run build` 成功（Next.js・TS strict）
- [x] 5-3. `npm run test` 成功（全 Green + カバレッジ 80%）

---

## ストーリー → コードステップ対応表（トレーサビリティ）

| ストーリー | 実装ステップ | テストステップ | 受入条件 |
|---|---|---|---|
| US-1（`KpiSummary` 型 + `fetchKpiSummary`） | 2-3 / 2-4 | 1-1 | camelCase 7 フィールド・ApiError 変換 |
| US-2（実データ表示 + 試算値注記） | 2-5 / 2-8 | 1-2 / 1-5 | 5 カード降順・注記常時表示・MOCK 撤去 |
| US-3（スケルトン表示フォールバック） | 2-6 / 2-7 / 2-8 | 1-3 / 1-4 / 1-5 | 失敗時再スケルトン・クリーンアップ |
| US-4（`SeverityLevel` 単一ソース化） | 2-1 / 2-2 | 1-1 | `type SeverityLevel` が 1 件 |
| NFR-1（カバレッジゲート恒久化） | 4-1 / 4-2 | 4-3 | ローカル = CI = 80% |

## Assumptions & Open Questions

- `assumptionDoc` / `isEstimate` は契約のみで表示に使わない（FR-6 / ADR-004 引継ぎ）。
- テストフィクスチャ: `totalSensors: 10`・counts L1:8 / L2:3 / L3:1・`estimatedCostSavedYen: 2_048_400`（unit-of-work §2.2 / ADR-003）。
- KPI section の `h2` 文言は **「KPI サマリ」**（スペース有り）で統一（functional-design レビュアー Minor 2・上流 interaction-spec に揃える）。
- その他の未確定項目はなし（None.）

## Sources

- [requirements] `inception/requirements-analysis/requirements.md`（FR-1〜8 / NFR-1〜5 / C-1〜C-5）
- [unit-of-work] `inception/units-generation/unit-of-work.md`（BU-1 境界・§2.2 実装ノート）
- [story-map] `inception/units-generation/unit-of-work-story-map.md`（US-1〜4 割当て・実装順）
- [business-logic-model] `construction/BU-1/functional-design/business-logic-model.md`（状態遷移 T1〜T4）
- [frontend-components] `construction/BU-1/functional-design/frontend-components.md`（型設計 §2・コンポーネント仕様 §3）
- [performance-requirements] `construction/BU-1/nfr-requirements/performance-requirements.md`（NFR-1 引継ぎ）

## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-08-11T10:28:16Z
**Iteration:** 1

### Findings

| # | Severity | Location | Finding | Recommendation |
|---|---|---|---|---|
| 1 | Minor | `frontend/src/hooks/useKpiPolling.ts` L41-46 | ポーリング失敗時の catch ブロックが空で、エラー詳細を console に記録しない。消費契約 `business-logic-model.md` §5 のエラーハンドリング方針（「例外を画面へ伝播させない。詳細は console ログに留める」）と construction フェーズ・ガードレール（「Errors must be surfaced to the caller or logged — silent failures are not acceptable」）を満たさない。状態遷移（再スケルトン）自体は FR-8 を正しく充足 | catch 内（cancelled ガード後）で `console.error` によりエラー詳細を記録する（1 行追加の trivial 修正） |
| 2 | Minor | `code-summary.md` L23 | KpiSummary.test.tsx のテスト数を「13 テスト」と記載するが、実際は 12 の it() ケース（`grep -c "it("` = 12）。実装・結果に影響なしの文書ドリフト | 記載数を 12 に修正 |
| 3 | Minor | `frontend/src/hooks/useKpiPolling.ts` L50-52 | setInterval が前回の in-flight リクエスト完了を待たずに次回 `load()` を発火するため、レスポンスが 5 秒を超えると古いレスポンスが新しい値を上書きしうる（out-of-order）。機能設計レビュー（business-logic-model Minor 5）で既知の制約として許容済み（既存 `useAlertPolling` と同型・デモスコープ）だが、新設フックとして対策余地が残る | デモスコープでは許容。将来の対策候補としてリクエスト連番 / in-flight ガードを注記に留める |
| 4 | Minor | `frontend/src/app/__tests__/page.test.tsx` L119 | 「モック KPI データ由来の固定数値（1,420,000 等）は描画されない」の `queryByText("1,420,000")` 否定アサートは、金額が常に `formatManYen` で変換される（1,420,000 → 「142万円」）ため検証として空振り（vacuously true）。実効的なガードは `queryByText("1,240")`（センサー数は toLocaleString 素通し）と Refactor 3-3 の grep チェック | 「142万円」等、実際に描画されうる形式に対するアサートへ変更 |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| `cd frontend && npm run test`（vitest run・coverage） | PASS: 11 ファイル / 91 テスト全 Green。Statements 93.11% / Branches 84.15% / Functions 90.12% / Lines 94.02%（すべて閾値 80% 超） | NFR-1 の 4 指標 80% を充足。vitest.config.mts の thresholds 単一ソースによりローカル = CI のゲート一致を確認 |
| `cd frontend && npm run lint`（ESLint） | PASS | 型・リントエラーなし |
| `cd frontend && npm run build`（Next.js 16.3.0 / Turbopack） | PASS | TS strict 型検査・ビルド成功。page.tsx は force-dynamic で Server Component のまま |
| `grep -rn "type SeverityLevel" frontend/src` | 1 件（`lib/severity.ts` のみ） | FR-2 単一ソース化（Refactor 3-1 と一致） |
| `grep -rn "MOCK_KPI_DATA" frontend/src` | 0 件 | C-4 モック非残置（Refactor 3-3 と一致） |
| `grep -rn "1_420_000\\|1420000\\|1240" frontend/src` | 0 件 | FR-4 ハードコード数値撤去（Refactor 3-2 と一致） |
| `grep -rn ": any\\|as any"`（FE-7 対象ファイル） | 0 件（コメント 1 件のみ） | NFR-2 `any` 不使用 |
| `grep -n "^\\"use client\\"" frontend/src/app/page.tsx` | 0 件 | C-2 Server Component 維持 |
| BE-8 スキーマ照合（`backend/app/schemas/kpi.py`） | PASS | 7 フィールド（total_sensors / level1_count / level2_count / level3_count / estimated_cost_saved_yen / is_estimate / assumption_doc）が FR-1 契約と 1:1 一致 |
| 循環依存チェック（手動照合） | PASS | `types/api → lib/severity` 単方向（lib/severity は他 import なし）。`useKpiPolling(intervalMs)` 引数化で `DashboardClient ↔ useKpiPolling` の循環は解消済み |

### Summary

実装は消費契約（FR-1〜8 / NFR-1〜5 / C-1〜C-5 / business-logic-model T1〜T4 / frontend-components）と 1:1 で整合し、機械的証拠（テスト 91 件全 Green・4 指標 80% 超・lint/build 成功・MOCK 撤去 grep 0 件・SeverityLevel 単一ソース 1 件・Server Component 維持）で裏付けられた。T3（失敗時値破棄→再スケルトン）の状態遷移、KPI ランドマークの DashboardClient 一元所有、5 カード降順 + lime Level 1 + 試算値 2 段注記は設計どおり実装済みで、開発者は計画のみから実装を再現できる。残る 4 件はすべて Minor（エラー詳細の console 記録欠如・テスト数表記・out-of-order 既知制約・空振りアサート）で、実装・ランタイムを妨げない。Critical 0・Major 0 → **READY**。
