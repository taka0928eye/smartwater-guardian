# 機能設計 — フロントエンドコンポーネント（BU-1: KPI サマリ）

> FE-7「KPIサマリの実データ連携と「試算値」注記の実装」BU-1（kind: `ui`）のフロントエンドコンポーネント設計。
> BE-8 の `GET /api/v1/kpi/summary` をポーリングし、`DashboardClient`（ランドマーク所有者）→
> `KpiSummary`（表示専用 5 カード）で描画する。フロントエンドのみ（C-1）。
> 質問回答: Q1=A / Q2=A / Q3=A。**Conversation language: 日本語**

## 1. コンポーネントツリーと責務

```
page.tsx（Server Component・変更: MOCK_KPI_DATA 除去）
└── <DashboardClient>  … section/h2/aria-labelledby/aria-busy を一元所有。KPI スケルトン↔カードグリッドを切替
    ├── <KpiSummary kpiData={kpiData}>  … 表示専用。5 カード降順 + 試算値注記（ランドマークは持たない）
    │   └── <KpiCard>（5 枚: sensors / level3 / level2 / level1 / cost）
    └── <AlertList>（既存・変更なし）
```

| コンポーネント | 種別 | 責務 | 変更 |
|---|---|---|---|
| `DashboardClient` | Client（`'use client'` 済み） | KPI セクションのランドマーク（`section`/`h2`/`aria-labelledby`/`aria-busy`）一元所有。`useKpiPolling` を呼び、`isLoading` でスケルトン ↔ `KpiSummary` を切替 | **拡張** |
| `useKpiPolling` | Hook（新設） | 5 秒ポーリング。失敗時 `isLoading=true`（再スケルトン）、成功時 `kpiData` 更新 | **新規** |
| `KpiSummary` | 表示専用 | `KpiSummaryData` を受け、5 カード（監視センサー数 / L3 / L2 / L1 / 推定削減コスト）を降順描画。試算値注記 | **改修** |
| `KpiCard` | 表示専用 | 単一カード（ラベル / 値 / 補足注記）。`data-testid` を保持 | **改修** |
| `fetchKpiSummary`（lib/api.ts） | API クライアント | `GET /api/v1/kpi/summary` を `unwrap<T>` で取得し camelCase 変換 | **追加** |
| `KpiSummary`（types/api.ts） | 型 | BE-8 契約を camelCase で表現（`KpiSummaryData` は表示層の別名） | **追加** |
| `SeverityLevel`（types/api.ts） | 型 | `lib/severity.ts` から re-export に変更（FR-2 単一ソース化） | **変更** |
| `page.tsx` | Server | `MOCK_KPI_DATA`・`KpiSummary` import を除去。Server Component のまま | **改修** |

## 2. 型設計

### 2.1 契約層（`frontend/src/types/api.ts`）

BE-8 スキーマ（`backend/app/schemas/kpi.py`）を camelCase で表現する新規型：

```ts
/** GET /api/v1/kpi/summary のレスポンス（BE-8 契約・snake_case→camelCase 変換済み） */
export interface KpiSummary {
  totalSensors: number;            // total_sensors
  level1Count: number;             // level1_count
  level2Count: number;             // level2_count
  level3Count: number;             // level3_count
  estimatedCostSavedYen: number;   // estimated_cost_saved_yen
  isEstimate: boolean;             // is_estimate
  assumptionDoc: string;           // assumption_doc
}
```

`SeverityLevel` は FR-2 に従い二重定義を解消し、`lib/severity.ts` からの re-export に変更する：

```ts
export type { SeverityLevel } from '../lib/severity';
```

### 2.2 表示層（`frontend/src/components/dashboard/KpiSummary.tsx`）

`KpiData`（現行インターフェース）を契約型の別名に置き換え、`todayDetections` を除去：

```ts
import type { KpiSummary } from '../../types/api';
type KpiSummaryData = KpiSummary;  // 表示層の別名（component-methods.md §4）
```

## 3. コンポーネント仕様

### 3.1 `DashboardClient`（拡張）

- KPI セクションの**ランドマークを一元所有**する（refined-mockups:c4 / application-design:c1。`KpiSummary` は表示専用のため section を持たない）。
- 既存 `section` はアラート用。KPI 用に**新たな section** を追加する。

```tsx
// KPI セクション（DashboardClient が所有）
<section aria-labelledby="kpi-summary-title" aria-busy={isLoading}>
  <h2 id="kpi-summary-title">KPIサマリ</h2>
  {isLoading ? (
    <div data-testid="kpi-skeleton" aria-hidden="true">
      {/* スケルトン表示（例: animate-pulse のカード形） */}
    </div>
  ) : (
    <KpiSummary kpiData={kpiData} />
  )}
</section>
```

- `useKpiPolling(ALERT_POLL_INTERVAL_MS)` を呼び、`{ kpiData, isLoading }` を受け取る（Q1=A）。
  `ALERT_POLL_INTERVAL_MS = 5000` は既存 export（L23）を再利用（FR-7 / intent-capture:c4）。
- `kpiData` が `null` かつ `isLoading === false` の状態は状態遷移表上発生しない（不変条件）。
  防御的に `kpiData` 非 null 時のみ `KpiSummary` を描画する。

### 3.2 `useKpiPolling`（新規 Hook）

```ts
interface UseKpiPollingResult {
  kpiData: KpiSummary | null;
  isLoading: boolean;
}
function useKpiPolling(intervalMs: number): UseKpiPollingResult
```

- `useAlertPolling` と対称の構造（即時 `load()` + `setInterval` + クリーンアップで
  `cancelled = true` と `clearInterval`）。
- **成功時のみ** `setKpiData(data)`。失敗時は `kpiData` を `null` に破棄し `isLoading = true`（Q2=A / FR-8）。
- 依存配列 `[intervalMs]`。`fetchKpiSummary` はモジュール定数（既存 `fetchAlerts` と同様）。

### 3.3 `KpiSummary`（改修）

- props: `{ kpiData: KpiSummaryData }`。表示専用（`section`/`h2` を描画しない）。
- **5 カードを降順**でグリッド表示（FR-5 / refined-mockups:c2）:
  1. 監視センサー数（`totalSensors`）→ `data-testid="kpi-card-sensors"`
  2. Level 3（`level3Count`）→ `data-testid="kpi-card-level3"`
  3. Level 2（`level2Count`）→ `data-testid="kpi-card-level2"`
  4. Level 1（`level1Count`）→ `data-testid="kpi-card-level1"` — `getSeverityMeta(1).accentClass`（lime 黄緑）を適用
  5. 推定削減コスト（`estimatedCostSavedYen`）→ `data-testid="kpi-card-cost"` — 試算値注記を伴う
- `todayDetections` カードは**削除**（BE-8 契約に含まれるが FE-7 対象外・intent-capture:c3）。

### 3.4 試算値注記（コストカード）

refined-mockups:c1 の 2 段構成を実装する:

```tsx
<div data-testid="kpi-card-cost">
  <span className="...">試算値</span>            {/* 見出しラベル（固定リテラル） */}
  <p className="...">前提: docs/business-model.md</p>  {/* 本文注記（固定リテラル） */}
</div>
```

- 表示文字列は **承認済み表示文言の固定値** とし、`SEVERITY_META` の label とは分離する（application-design:c6）。
- テストは連結文字列の部分一致でなく**カード内スコープの順序検証**（正規表現
  `/試算値[\s\S]*前提: docs\/business-model\.md/`）で検証する（project.md cid:application-design:c2）。
- `isEstimate` / `assumptionDoc` は表示に使わない（ADR-004。契約のみ保持）。

## 4. インタラクションフロー

| 操作 | フロー | 画面効果 |
|---|---|---|
| 初回マウント | `useKpiPolling(5000)` が即 `load()` | スケルトン → 成功時 5 カード |
| 5 秒ポーリング | `load()` 再実行・成功 | `kpiData` 更新（カード値が変わる） |
| ポーリング失敗 | `isLoading=true` + `kpiData=null` | 再スケルトン（stale 値非表示・FR-8） |
| 復旧 | 次回成功 | カード復帰 |
| アンマウント | `cancelled` + `clearInterval` | 非同期 setState なし |

- KPI とアラートは**独立したポーリングループ**（アラートは既存 `useAlertPolling` 据え置き、KPI は再スケルトン）。
  共通フックに統合しない（application-design:c5）。

## 5. API 統合

### 5.1 `fetchKpiSummary`（`frontend/src/lib/api.ts`）

```ts
export async function fetchKpiSummary(): Promise<KpiSummary> {
  const data = await apiClient.get('/api/v1/kpi/summary');
  return unwrap<KpiSummary>(data);  // snake_case→camelCase 変換 + ApiError 変換
}
```

- `unwrap<T>`（既存）がバックエンドの snake_case を camelCase へ変換するため、**境界で 1 回だけ**の変換
  が実現される（C-3 / team-practices）。
- 4xx/5xx は既存 `ApiError` に変換して throw（エラーハンドリング規約を踏襲）。

### 5.2 テスト観測点（component-methods.md §3 と整合）

| 観測点 | 対象 |
|---|---|
| `data-testid="kpi-skeleton"` | スケルトン描画（初回・失敗時） |
| `data-testid="kpi-card-*"` | 各カードの値・注記 |
| `section[aria-labelledby="kpi-summary-title"]` / `aria-busy` | ランドマーク所有・busy 状態 |
| `KpiSummary` props | `kpiData` 表示専用性 |

## Sources

- [unit-of-work] `inception/units-generation/unit-of-work.md`（BU-1 境界・§2.2 フックシグネチャ権威）
- [unit-of-work-story-map] `inception/units-generation/unit-of-work-story-map.md`（US-1〜4 の BU-1 割当て・実装順）
- [requirements] `inception/requirements-analysis/requirements.md`（FR-1〜8 / NFR-1〜5 / Constraints C-1〜C-5）
- [components] `inception/application-design/components.md`（8 コンポーネント責務・ランドマーク所有・表示専用）
- [component-methods] `inception/application-design/component-methods.md`（公開シグネチャ・テスト観測点・`KpiSummaryData` 別名）
- [services] `inception/application-design/services.md`（オーケストレーション方針・データフロー）

## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-08-11T09:36:56Z
**Iteration:** 1

### Findings

| # | Severity | Location | Finding | Recommendation |
|---|---|---|---|---|
| 1 | Minor | §3.4（L115-129） | 試算値注記の DOM 構造が上流と乖離する。本設計は `<span>試算値</span>` を独立要素とし、`<p>前提: docs/business-model.md</p>` を従える 2 段構成だが、interaction-spec（L59-64）は「カード見出し『推定削減コスト』に `· 試算値` を併記」、component-methods §4 は「カード見出し『推定削減コスト · 試算値』」とし、refined-mockups:c1 は「コストカード見出しラベル『試算値』」とする。`getByText("試算値")` 完全一致はこの構造差に依存するため、テスト観測点が実装により変わる。また §3.4 スニペットは金額値（`formatManYen` = 204.8万円）とカードラベル「推定削減コスト」の配置を示しておらず、コストカード全体の DOM が未確定 | コストカード完全形（ラベル「推定削減コスト」+ 値 + 注記 `試算値`/`前提`）を 1 図で固定し、interaction-spec の「推定削減コスト · 試算値」表記との関係（どちらが権威か）を明記する |
| 2 | Minor | §3.1（L73） | h2 文言「KPIサマリ」が上流と異なる。interaction-spec §テスト観測点は `h2「KPI サマリ」`（スペース有り）、現行 `KpiSummary.tsx` の section も `aria-label="KPI サマリ"`（スペース有り）。h2 の完全一致アサート（getByRole name）はスペース有無に敏感で、build-and-test でテストを書く際にどちらを正とするか不明 | h2 文言を上流（`KPI サマリ`）に揃えるか、本設計が権威である旨を §5.2 の観測点に明記する |
| 3 | Minor | §3.4（L129） | `isEstimate` / `assumptionDoc` の「表示に使わない」根拠を ADR-004 としているが、ADR-004 は試算値注記のテストアサート方式が主題で、表示未使用の根拠は requirements FR-6 と application-design Minor 4 の解決。引用が不正確 | 引用を FR-6 / application-design 引き継ぎ表へ変更する |
| 4 | Minor | §3.1・§1 ツリー | DashboardClient のルート構造変更が未図示。現行は `<div className="grid grid-cols-1 gap-4 lg:grid-cols-3">` を直接返すが、KPI 全面幅セクションを追加するには親ラッパーが必要（interaction-spec L106-107「既存 3 列グリッドを包む親要素を追加し、その先頭に KPI 全面幅セクション」）。§3.1 は KPI section のスニペットのみでラッパー構造を示していない | DashboardClient の返却 JSX 全体（KPI section + 既存 3 列グリッドを包む構造）を 1 図で示す |
| 5 | Minor | §5.2 テスト観測点 | 既存テストへの影響が明示されていない。`DashboardClient.test.tsx`（L56-59）と `page.test.tsx`（L17-20）の `vi.mock("@/lib/api")` は fetchKpiSummary を含まず、DashboardClient が `useKpiPolling` 経由で `fetchKpiSummary` を呼ぶと undefined 参照で既存テストが壊れる。両ファイルは story-map で変更対象（US-2/US-3）に入っており境界内だが、モック追加が必要な旨を明記すると build-and-test での取りこぼしを防げる | §5.2 に「`@/lib/api` のモックへ fetchKpiSummary を追加」をテスト観測点として追記する |
| 6 | Minor | Sources（L168-175） | 本文で ADR-004（decisions.md）を引用するが Sources に decisions.md が無い。consumes 契約には含まれないため upstream-coverage センサーは通るが、引用元の追跡性が不十分 | Sources に decisions.md を追記する |

### Validation Tool Results

ステージ定義（functional-design）の検証ツールはセンサー（required-sections / upstream-coverage / linter / type-check）のみで専用スクリプトなし。以下は上流契約・既存実装との手動照合結果:

| 照合対象 | 結果 | 解釈 |
|---|---|---|
| FR-1 型定義（7 フィールド camelCase） | PASS | `backend/app/schemas/kpi.py` の 7 フィールドと §2.1 の `KpiSummary` 型が 1:1 対応。snake_case→camelCase 変換は `unwrap` の既存実装（lib/api.ts L82）で担保 |
| FR-2 `SeverityLevel` re-export | PASS | 型チェーン `lib/api → types/api → lib/severity` は循環なし（lib/severity.ts は他モジュールを import しない）。`export type { SeverityLevel }` は TS 的に有効 |
| FR-4 `MOCK_KPI_DATA` 撤去 | PASS | 現行 page.tsx L25-31 の `MOCK_KPI_DATA` / L164 の `<KpiSummary kpiData={MOCK_KPI_DATA} />` が設計の削除対象と一致。`page.tsx` は `'use client'` なし（C-2）を維持 |
| FR-5 カード降順 | PASS | 設計の降順（sensors→level3→level2→level1→cost）は refined-mockups:c2 / component-methods §4 / interaction-spec L47-53 と一致。requirements FR-5 の昇順表記は上流で解決済み（unit-of-work §2.2）の乖離であり本設計の採用が正 |
| `getSeverityMeta(1).accentClass`（lime） | PASS | `lib/severity.ts` L42 に `border-lime-200 text-lime-700` を確認。Level 1 カードの lime 適用は既存トークンで充足（新規追加不要） |
| ADR-002 ランドマーク所有 | PASS | `DashboardClient` が section/h2/aria-labelledby/aria-busy を所有し KpiSummary は表示専用という分割は ADR-002・refined-mockups:c4 と一致。スケルトン中も h2 維持を充足 |
| 既存テストへの影響 | 影響あり・境界内 | `DashboardClient.test.tsx` / `page.test.tsx` の `@/lib/api` モックに fetchKpiSummary 追加が必要（Finding 5）。両ファイルは unit-of-work §2.1・story-map US-2/US-3 の変更対象に含まれ、スコープ外の破壊ではない |
| `ALERT_POLL_INTERVAL_MS` export | PASS | `DashboardClient.tsx` L23 に存在。§3.1「既存 export（L23）を再利用」の主張と一致 |
| NFR-1 カバレッジゲート | 未記述 | vitest.config.mts に coverage 設定なし / `npm run test` = `vitest run` / CI は CLI フラグ強制。本成果物に記述なし（business-logic-model Finding 3 と同系。build-and-test への引継ぎ対象） |

### Summary

コンポーネント境界（DashboardClient=ランドマーク所有 / KpiSummary=表示専用 / useKpiPolling=データ取得）・型設計（`KpiSummary` 7 フィールド / `KpiSummaryData` 別名 / `SeverityLevel` re-export）・`fetchKpiSummary`（unwrap 経由の 1 回変換）は FR-1〜8・ADR-001/002/005・既存実装（KpiSummary / useAlertPolling / lib/api / lib/severity / page.tsx / BE-8 スキーマ）と全て整合し、開発者はこの文書＋ unit-of-work の境界から余計な質問なしに実装できる。循環依存なし・モック非残置（C-4）・Server Component 維持（C-2）も充足。残る 6 件は試算値注記・h2 文言の表示文字列の上流乖離（Finding 1/2）、既存テストのモック追加明示（Finding 5）等の Minor で、いずれも実装を妨げず build-and-test で吸収可能。Critical 0・Major 0 → **READY**。
