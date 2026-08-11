# Interaction Specification — FE-7 KPIサマリの実データ連携と「試算値」注記

> 上流のユーザーフロー（`ideation/rough-mockups/user-flow.md`）とユーザーストーリー
> （`inception/user-stories/stories.md`）に基づき、KPI サマリ関連コンポーネントの状態遷移・
> インタラクション・受入条件をコンポーネントレベルで仕様化する。表示詳細は
> `mockups.md`、デザインシステムへの適合は `design-system-mapping.md`、
> アクセシビリティは `accessibility-checklist.md` を参照。

## 対象コンポーネントと責務分担

| コンポーネント | 責務 | 変更種別 |
|---|---|---|
| `KpiSummary.tsx` | **表示専用** — `KpiSummary` 型（7 フィールド）を受け取り 5 カード + 試算値注記を描画 | 表示契約・カード構成変更 |
| `DashboardClient.tsx` | **状態遷移・データ取得** — `fetchKpiSummary` を 5 秒ポーリングし、取得成功時のみ `KpiSummary` を描画。未取得成功時はスケルトン描画 | ルート構造変更 + ポーリング追加 |
| `page.tsx` | Server Component のまま維持 — `MOCK_KPI_DATA` 撤去・`KpiSummary` import 削除 | ハードコード値削除 |
| `lib/api.ts` | `fetchKpiSummary(): Promise<KpiSummary>` 追加（`GET /api/v1/kpi/summary`） | 新規関数 |
| `types/api.ts` | `KpiSummary` 型追加 + `SeverityLevel` を `lib/severity.ts` から re-export | 型・re-export |

## KpiSummary（表示コンポーネント）

| Field | Value |
|---|---|
| Component | `KpiSummary` |
| Description | 監視指標 5 カード（監視センサー数 / Level 3 / Level 2 / Level 1 / 推定削減コスト）を表示する表示専用コンポーネント |
| Category | display |

### States

| State | Description | Trigger |
|---|---|---|
| default | 5 カード + 試算値注記を実データで表示 | props `kpiData` 受領 |
| loading | スケルトンカード 5 枚を表示 | props 受領前（本コンポーネントは表示専用のため、描画は DashboardClient が制御） |
| error | 発生しない（取得失敗時の状態遷移は DashboardClient が担う） | — |

### Props / Inputs

| Prop | Type | Required | Default | Description |
|---|---|---|---|---|
| `kpiData` | `KpiSummary`（型エイリアス `KpiSummaryData` を import） | yes | — | 監視指標 7 フィールド（camelCase） |

> `types/api.ts` の型 `KpiSummary` とコンポーネント `KpiSummary` の同名を回避するため、
> コンポーネント内で `import type { KpiSummary as KpiSummaryData }` のエイリアスを採用する
> （requirements Minor #6 解消 / stories US-2 AC7）。 [stories] [requirements]

### Rendering（カード降順・DOM 出現順）

| 順 | testId | ラベル | 値 | 単位 | アクセント |
|---|---|---|---|---|---|
| 1 | `kpi-card-sensors` | 監視センサー数 | `totalSensors.toLocaleString("ja-JP")` | 台 | なし |
| 2 | `kpi-card-level3` | Level 3 破裂リスク | `level3Count.toLocaleString("ja-JP")` | 件 | `getSeverityMeta(3).accentClass` |
| 3 | `kpi-card-level2` | Level 2 警告 | `level2Count.toLocaleString("ja-JP")` | 件 | `getSeverityMeta(2).accentClass` |
| 4 | `kpi-card-level1` | Level 1 微小漏水（AI検知） | `level1Count.toLocaleString("ja-JP")` | 件 | `getSeverityMeta(1).accentClass`（lime） |
| 5 | `kpi-card-cost` | 推定削減コスト · 試算値 | `formatManYen(estimatedCostSavedYen)` | — | なし |

- 降順は DOM 出現順で検証（testId `kpi-card-sensors` → `kpi-card-level3` → `kpi-card-level2`
  → `kpi-card-level1` → `kpi-card-cost`）。 [stories US-2 AC1]
- 「本日の検知数（`todayDetections`）」カードは表示しない。 [requirements FR-5] [stories US-2 AC2]

### 試算値注記（2 段構成 — Q1=A・統合サマリ確認済み）

- **見出しラベル:** カード見出し「推定削減コスト」に `· 試算値` を併記（固定文字列）。
- **カード本文注記:** 金額下に `前提: docs/business-model.md` のインライン短文を常時表示（固定文字列）。
- テスト: 2 文字列の完全一致 + 連結文字列「試算値（前提: docs/business-model.md）」の部分一致。
  [requirements FR-6] [stories US-2 AC3]

### Accessibility

| Requirement | Implementation |
|---|---|
| ARIA role | `section`（KPI サマリ領域）。role は明示不要（ネイティブ section） |
| Heading | セクション内に `h2`「KPI サマリ」を追加し、`aria-labelledby` で見出しに紐付け |
| Card label | 各カードは `p`（見出しを使わない）。ラベル文言で色に依存せず区別 |
| Contrast ratio | 既存 Tailwind トーン（`text-slate-500` / `text-slate-900` / accent）は WCAG AA 達成済みを維持 |
| Screen reader | `aria-busy="true"` は DashboardClient が KPI セクションコンテナに付与（取得成功で解除） |

## DashboardClient（状態遷移・データ取得コンポーネント）

| Field | Value |
|---|---|
| Component | `DashboardClient` |
| Description | KPI の 5 秒ポーリング取得・スケルトン切替・地図/アラート一覧/詳細ドロワーを束ねる Client Component |
| Category | layout + data-fetching |

### States（KPI セクション）

| State | Description | Trigger |
|---|---|---|
| loading（スケルトン） | `data-testid="kpi-skeleton"` を描画（カード 5 枚相当） | 初回取得成功前 / 取得失敗後 / 再取得成功前 |
| success | `KpiSummary` を実データで描画 | `fetchKpiSummary` 成功 |
| error（成功後失敗） | **再スケルトン**（stale 値を表示しない） | 成功後にポーリング失敗 |

- 状態遷移は **3 ケース**を網羅: (a) 初回ローディング中＝スケルトン、(b) 取得成功＝カード値表示、
  (c) **成功後に失敗＝再スケルトン**。 [stories US-3 AC1] [requirements FR-8]

### Props / Inputs

| Prop | Type | Required | Default | Description |
|---|---|---|---|---|
| `sensorFeatures` | `SensorFeatureCollection` | yes | — | サーバー側取得済みセンサー GeoJSON |

### Interaction

- **ポーリング周期:** `ALERT_POLL_INTERVAL_MS = 5000` を共用（KPI とアラートで同一周期）。 [requirements FR-7]
- **クリーンアップ:** `useEffect` クリーンアップで `clearInterval` + `cancelled` フラグを徹底
  （ポーリングリーク防止。team-practices 規約）。 [team-practices]
- **ルート構造変更:** 既存 3 列グリッド（`lg:grid-cols-3`）を包む親要素を追加し、その**先頭**に
  KPI 全面幅セクションを描画。 [requirements FR-7] [stories US-2 AC6]
- **エラー表示:** アラート側は既存 `data-testid="alerts-error"` の控えめ表示を維持。KPI 側は
  スケルトン表示で白画面を回避（エラーメッセージを断定的に出さない）。 [team-practices] [requirements FR-8]

### Accessibility

| Requirement | Implementation |
|---|---|
| aria-busy | KPI セクションコンテナに `aria-busy="true"`（スケルトン中）。取得成功で解除 |
| aria-live | セクション全体への `aria-live` は**付与しない**（5 秒ポーリングでの読上げノイズ回避） |
| Keyboard | カードは非インタラクティブのため `tabindex` 不要 |

## fetchKpiSummary（API クライアント）

| Field | Value |
|---|---|
| Component | `fetchKpiSummary` |
| Description | `GET /api/v1/kpi/summary` を呼び、`KpiSummary`（camelCase）を返す |
| Category | input（データ取得） |

### Inputs / Outputs

| Direction | Type | Description |
|---|---|---|
| In | なし（引数なし） | バックエンド BE-8 が返す KPI サマリを取得 |
| Out | `Promise<KpiSummary>` | 7 フィールド（camelCase） |

### Errors

| Condition | Behavior |
|---|---|
| バックエンド 4xx/5xx | `unwrap<T>` が `ApiError` へ変換して throw（4xx・5xx 両方をテストで検証） |
| 非 axios エラー | そのまま透過（既存 unwrap の仕様を維持） |

### Acceptance Criteria

- 7 フィールドすべての `snake_case`→`camelCase` 変換を fixture で検証。 [stories US-1 AC1]
- 変換は `lib/api.ts` 境界で 1 回だけ（コンポーネント側に snake_case 直参照が無いことを grep で静的確認）。 [team-practices]

## テスト観測点（QA 検証のための固定識別子）

| 対象 | 識別子 | 検証内容 |
|---|---|---|
| KPI セクション | `h2`「KPI サマリ」+ `aria-labelledby` | 見出し存在・紐付け |
| カード降順 | testId の DOM 出現順 | `kpi-card-sensors` → `kpi-card-level3` → `kpi-card-level2` → `kpi-card-level1` → `kpi-card-cost` |
| Level 1 カード | `kpi-card-level1` + lime accent | 存在・ラベル・アクセント |
| 試算値注記 | `試算値` 完全一致 + `前提: docs/business-model.md` 完全一致 + 連結部分一致 | 2 段構成の常時表示 |
| スケルトン | `data-testid="kpi-skeleton"` | 未取得時表示・成功時にカード値へ切替 |
| モック撤去 | `queryByText("1,240")` / `queryByText("142万円")` 非存在 | MOCK_KPI_DATA 非表示 |

## Assumptions & Open Questions

- なし（None.）— 表示・状態・テスト観測点は上流成果物と本仕様で確定済み。

## Sources

- [wireframes] `ideation/rough-mockups/wireframes.md`（カード構成・試算値注記・スケルトン）
- [user-flow] `ideation/rough-mockups/user-flow.md`（ハッピーパス / エラーフロー / スケルトン切替）
- [stories] `inception/user-stories/stories.md`（US-1〜4・試算値 2 段構成・テスト観測点）
- [requirements] `inception/requirements-analysis/requirements.md`（FR-4〜8 / NFR-5 / Out of Scope）
- [team-practices] `inception/practices-discovery/team-practices.md`（変換境界・ポーリングクリーンアップ / フォールバック Q10）
