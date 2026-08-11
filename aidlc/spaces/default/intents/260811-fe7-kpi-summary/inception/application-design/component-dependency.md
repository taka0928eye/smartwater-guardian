# Application Design — Component Dependency

> FE-7「KPIサマリの実データ連携と「試算値」注記の実装」のコンポーネント依存関係・データフロー設計。
> 既存構造は RE 成果物（`codekb/architecture.md` / `codekb/component-inventory.md`）を基に、本スコープで
> 追加・変更される依存を整理する。

## 1. 依存マトリクス

「行 → 列」の方向で依存する。

| コンポーネント | `page.tsx` | `DashboardClient` | `useKpiPolling` | `KpiSummary` | `fetchKpiSummary` | `lib/severity.ts` | `types/api.ts` |
|---|---|---|---|---|---|---|---|
| `page.tsx` | — | 依存（子として描画） | — | **撤去**（import 削除） | — | — | 依存（型） |
| `DashboardClient` | — | — | **依存（新規）** | **依存（描画）** | — | 依存 | 依存（型） |
| `useKpiPolling` | — | — | — | — | **依存（新規）** | — | 依存（型） |
| `KpiSummary` | — | — | — | — | — | 依存（`getSeverityMeta`） | 依存（型） |
| `fetchKpiSummary` | — | — | — | — | — | — | 依存（型） |
| `lib/severity.ts` | — | — | — | — | — | — | —（**被 re-export**） |
| `types/api.ts` | — | — | — | — | — | **re-export 元** | — |

## 2. 通信パターン

| ペア | パターン | 内容 |
|---|---|---|
| `DashboardClient` → `useKpiPolling` | 同期（hook 呼び出し） | フックを呼び `{ kpiData, isLoading }` を受領 |
| `useKpiPolling` → `fetchKpiSummary` | 非同期待ち（Promise） | 5 秒ごとに API 呼び出し。成功時のみ更新・失敗時は再スケルトン |
| `DashboardClient` → `KpiSummary` | 同期（props） | 取得成功時に `kpiData` を渡してカードグリッド描画 |
| `KpiSummary` → `lib/severity.ts` | 同期（関数呼び出し） | `getSeverityMeta(level).accentClass` でカード枠線・文字色を取得 |
| `fetchKpiSummary` → バックエンド API | 非同期（HTTP GET） | `GET /api/v1/kpi/summary`（BE-8） |

## 3. データフロー（詳細）

```
[バックエンド BE-8]
  GET /api/v1/kpi/summary
  → snake_case JSON（total_sensors / level1_count / level2_count / level3_count /
      estimated_cost_saved_yen / is_estimate / assumption_doc）
        │  HTTP 5 秒ポーリング（useKpiPolling 内で周期的に呼び出し）
        ▼
[useKpiPolling]
  fetchKpiSummary() → lib/api.ts 境界で snake_case→camelCase 変換（1 回だけ）
  → KpiSummary（totalSensors / level1Count / level2Count / level3Count /
      estimatedCostSavedYen / isEstimate / assumptionDoc）
  → { kpiData, isLoading } を返す
        │  props（kpiData）
        ▼
[DashboardClient]
  section（h2「KPI サマリ」+ aria-labelledby + aria-busy）を常時描画
  → isLoading なら kpi-skeleton / 成功なら <KpiSummary kpiData={...} />
        │  props（kpiData）
        ▼
[KpiSummary]
  getSeverityMeta(level).accentClass でアクセント色を解決
  → 5 カード（降順）+ 試算値注記（2 段構成）を描画
```

## 4. 共有リソース

| リソース | 所有者 | 共有先 | 内容 |
|---|---|---|---|
| `ALERT_POLL_INTERVAL_MS`（=5000） | 既存定数 | `useKpiPolling`（追加） | KPI とアラートで同一のポーリング周期を共用（requirements FR-7） |
| `SeverityLevel` / `SEVERITY_META` / `getSeverityMeta` | `lib/severity.ts`（単一ソース） | `KpiSummary`・`types/api.ts`（re-export） | 深刻度の型・表示メタを一箇所で管理（team-practices Q9=A） |
| `KpiSummary` 型 | `types/api.ts`（契約層） | `DashboardClient`・`useKpiPolling`・`fetchKpiSummary`・`KpiSummary` | API 契約の型。コンポーネントでは `KpiSummaryData` エイリアスで衝突回避 |

## 5. 依存の新規追加 / 変更まとめ

| 変更種別 | 内容 | 根拠 |
|---|---|---|
| 新規依存 | `DashboardClient → useKpiPolling` | Q1=A（専用フック新設） |
| 新規依存 | `useKpiPolling → fetchKpiSummary` | ポーリング実装（requirements FR-7） |
| 新規依存 | `DashboardClient → KpiSummary`（描画） | スケルトン/実データ切替（Q2=A・requirements FR-8） |
| 依存撤去 | `page.tsx → KpiSummary`（直接描画） | `MOCK_KPI_DATA` 撤去・Server Component 維持（requirements FR-4） |
| 変更 | `types/api.ts → lib/severity.ts`（re-export） | 型の二重定義解消（team-practices Q9=A） |

## 6. 循環依存チェック

- 依存グラフに循環は**なし**。すべて DAG 構造（`page.tsx → DashboardClient → {useKpiPolling → fetchKpiSummary, KpiSummary → lib/severity.ts}`）。
- `KpiSummary` 型とコンポーネント `KpiSummary` の同名衝突は、`import type { KpiSummary as KpiSummaryData }` のエイリアスで回避
  （`interaction-spec.md` 記載の解消策を踏襲）。

## Assumptions & Open Questions

- `ALERT_POLL_INTERVAL_MS` は既存定数の値をそのまま共用する（新規定数を追加しない）。
- バックエンドのレスポンスフィールド名（snake_case）は BE-8 実装済みの契約に従う。
- その他の未確定項目はなし（None.）

## Sources

- [requirements] `inception/requirements-analysis/requirements.md`（FR-4〜8 / Constraints）
- [stories] `inception/user-stories/stories.md`（US-1〜4）
- [refined-mockups] `inception/refined-mockups/interaction-spec.md`・`design-system-mapping.md`（責務分担・レイアウト・型エイリアス）
- [architecture] `aidlc/spaces/default/codekb/smartwater-guardian/architecture.md`（コンポーネント関係・レイヤー構造）
- [component-inventory] `aidlc/spaces/default/codekb/smartwater-guardian/component-inventory.md`（既存コンポーネント・依存グラフ・定数）
- [team-practices] `inception/practices-discovery/team-practices.md`（変換境界・単一ソース Q9）
