# Application Design — Component Methods

> FE-7「KPIサマリの実データ連携と「試算値」注記の実装」のコンポーネント公開インターフェース（メソッド・
> シグネチャ）設計。詳細なビジネスルール・実装手順は Functional Design へ委ね、本成果物は公開 API
> 面・入力/出力型・エラーハンドリング方針を定める。表示仕様は refined-mockups、
> 型定義は `interaction-spec.md` と整合させる。

## 1. メソッド一覧（公開インターフェース）

| # | コンポーネント | メソッド / シグネチャ | 種別 |
|---|---|---|---|
| 1 | `useKpiPolling` | `useKpiPolling(): { kpiData: KpiSummary \| null; isLoading: boolean }` | hook（新規） |
| 2 | `fetchKpiSummary` | `fetchKpiSummary(): Promise<KpiSummary>` | async 関数（新規） |
| 3 | `KpiSummary` | `(props: { kpiData: KpiSummaryData }) => JSX.Element` | display component |
| 4 | `DashboardClient` | `(props: { sensorFeatures: SensorFeatureCollection }) => JSX.Element` | client component |
| 5 | `getSeverityMeta` | `getSeverityMeta(level: SeverityLevel): SeverityMeta` | 既存・再利用 |
| 6 | `getSeverityColor` | `getSeverityColor(level: SeverityLevel): string` | 既存・再利用 |
| 7 | `formatManYen` | `formatManYen(yen: number): string` | 既存・再利用 |

## 2. メソッド詳細

### 2.1 `useKpiPolling`

```
useKpiPolling(): { kpiData: KpiSummary | null; isLoading: boolean }
```

| 項目 | 内容 |
|---|---|
| 目的 | KPI サマリを 5 秒ポーリングし、取得成功時のみ `kpiData` を更新。失敗時・初回取得前は `isLoading: true`（スケルトン状態）を返す |
| 入力 | なし（ポーリング周期は内部で `ALERT_POLL_INTERVAL_MS` を参照） |
| 出力 | `{ kpiData: KpiSummary \| null, isLoading: boolean }` |
| エラーハンドリング | 取得失敗は `isLoading: true` への遷移（再スケルトン）で処理し、例外を画面に出すまで伝播させない。エラー詳細はコンソールログに留める（フロント規約: 最終状態を据え置かず、控えめに表示） |
| クリーンアップ | `useEffect` クリーンアップで `clearInterval` + `cancelled` フラグを徹底（ポーリングリーク防止・team-practices 規約） |
| 参照 | `requirements.md` FR-7 / FR-8、`stories.md` US-3、`team-practices.md` |

### 2.2 `fetchKpiSummary`

```
fetchKpiSummary(): Promise<KpiSummary>
```

| 項目 | 内容 |
|---|---|
| 目的 | `GET /api/v1/kpi/summary` を呼び、KPI サマリ（camelCase 7 フィールド）を返す |
| 入力 | なし |
| 出力 | `Promise<KpiSummary>` — `{ totalSensors, level1Count, level2Count, level3Count, estimatedCostSavedYen, isEstimate, assumptionDoc }` |
| エラーハンドリング | バックエンド 4xx/5xx は `unwrap<T>` が `ApiError` へ変換して throw。非 axios エラーはそのまま透過（既存 `unwrap` の仕様を維持） |
| 変換境界 | snake_case→camelCase 変換は `lib/api.ts` 境界で 1 回だけ行う（コンポーネント側に snake_case 直参照なし） |
| 参照 | `requirements.md` FR-4、`stories.md` US-1 AC1、`team-practices.md` |

### 2.3 `KpiSummary`（表示コンポーネント）

```
KpiSummary(props: { kpiData: KpiSummaryData }): JSX.Element
```

| 項目 | 内容 |
|---|---|
| 目的 | 5 カード（監視センサー数 / Level 3 / Level 2 / Level 1 / 推定削減コスト · 試算値）を降順で描画し、試算値注記（2 段構成）を表示 |
| 入力 | `kpiData: KpiSummaryData`（`import type { KpiSummary as KpiSummaryData }` で型名衝突を回避） |
| 出力 | JSX（カードグリッド `grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5`） |
| エラーハンドリング | 発生しない（表示専用。取得失敗時の状態遷移は `DashboardClient` / `useKpiPolling` が担う） |
| 非責務 | `section`/`h2`/`aria-labelledby`/`aria-busy` を描画しない（Q2=A: `DashboardClient` が所有） |
| 参照 | `requirements.md` FR-5 / FR-6、`stories.md` US-2、`interaction-spec.md`（カード詳細・試算値 2 段構成） |

### 2.4 `DashboardClient`（ラッパー）

```
DashboardClient(props: { sensorFeatures: SensorFeatureCollection }): JSX.Element
```

| 項目 | 内容 |
|---|---|
| 目的 | KPI セクションのランドマークを常時描画し、`useKpiPolling` の状態に応じてスケルトンか `KpiSummary` を切替え。既存 3 列グリッド（地図/アラート一覧/詳細ドロワー）の先頭に KPI 全面幅セクションを配置 |
| 入力 | `sensorFeatures: SensorFeatureCollection`（サーバー側取得済み GeoJSON・既存） |
| 出力 | JSX — `section`（`aria-labelledby` 参照 h2 の ID、`aria-busy`）配下に `kpi-skeleton` または `<KpiSummary kpiData={...} />`、続いて既存 3 列グリッド |
| エラーハンドリング | KPI 取得失敗はスケルトン表示（白画面回避・FR-8）。アラート側は既存 `alerts-error` の控えめ表示を維持 |
| 参照 | `requirements.md` FR-7 / FR-8、`stories.md` US-2 / US-3、`accessibility-checklist.md`（aria 実装仕様） |

### 2.5 `getSeverityMeta` / `getSeverityColor`（既存・再利用）

```
getSeverityMeta(level: SeverityLevel): SeverityMeta   // { label, color, accentClass }
getSeverityColor(level: SeverityLevel): string
```

| 項目 | 内容 |
|---|---|
| 目的 | Level 3 / Level 2 / Level 1 カードの accentClass（枠線 + 文字色）を取得。Level 1（lime）は本スコープで追加適用 |
| 参照 | `design-system-mapping.md`（デザイントークン）、`codekb/component-inventory.md`（既存実装） |

### 2.6 `formatManYen`（既存・再利用）

```
formatManYen(yen: number): string
```

| 項目 | 内容 |
|---|---|
| 目的 | 推定削減コストカードの金額を「204.8万円」形式（ja-JP / `maximumFractionDigits: 1`）で表示 |
| 検証 | `formatManYen(2_048_400)` = `"204.8万円"`（Q3=A のフィクスチャ 2,048,400 と整合） |
| 参照 | `design-system-mapping.md`、`docs/business-model.md` §3.4 |

## 3. エラーハンドリング方針（コンポーネント別）

| レイヤー | 方針 |
|---|---|
| API 境界（`fetchKpiSummary`） | `ApiError` へ変換して throw（4xx/5xx）。非 axios エラーは透過 |
| フック（`useKpiPolling`） | 取得失敗を `isLoading: true`（再スケルトン）で吸収。例外を画面に伝播させない |
| 表示（`KpiSummary`） | エラー処理を持たない（表示専用） |
| ラッパー（`DashboardClient`） | KPI 失敗＝スケルトン表示（stale 値非表示・FR-8）。アラート失敗＝既存 `alerts-error` 控えめ表示 |

## 4. スケルトン・注記の固定識別子（テスト観測点）

| 対象 | 識別子 / 文字列 | 検証観点 |
|---|---|---|
| スケルトン | `data-testid="kpi-skeleton"` | 未取得時表示・成功時にカードへ切替 |
| カード降順 | testId の DOM 出現順 | `kpi-card-sensors` → `kpi-card-level3` → `kpi-card-level2` → `kpi-card-level1` → `kpi-card-cost` |
| 試算値見出し | `試算値`（完全一致） | カード見出し「推定削減コスト · 試算値」 |
| 試算値本文 | `前提: docs/business-model.md`（完全一致） | カード本文のインライン短文 |
| 注記の一体性 | コストカード内で `試算値` が `前提: docs/business-model.md` より**前**に出現（順序検証） | 2 段構成の構造維持（Minor 4 解消方針） |

## Assumptions & Open Questions

- ポーリング周期は `ALERT_POLL_INTERVAL_MS = 5000` を定数参照で共用する（アラートと同一周期。requirements FR-7）。
- スケルトン・試算値注記の表示文字列は refined-mockups で確定済みの固定値を本設計の正とする。
- その他の未確定項目はなし（None.）

## Sources

- [requirements] `inception/requirements-analysis/requirements.md`（FR-4〜8 / NFR）
- [stories] `inception/user-stories/stories.md`（US-1〜4・テスト観測点）
- [refined-mockups] `inception/refined-mockups/interaction-spec.md`・`mockups.md`・`design-system-mapping.md`（カード詳細・試算値 2 段構成・デザイントークン）
- [team-practices] `inception/practices-discovery/team-practices.md`（変換境界・エラーハンドリング・ポーリングクリーンアップ）
- [architecture] `aidlc/spaces/default/codekb/smartwater-guardian/architecture.md`（KPI 配線予定）
- [component-inventory] `aidlc/spaces/default/codekb/smartwater-guardian/component-inventory.md`（既存メソッド・useAlertPolling 先例）
- [business-model] `docs/business-model.md`（§3.4 デモ算出例）
