# Refined Mockups — FE-7 KPIサマリの実データ連携と「試算値」注記

> 上流のラフワイヤーフレーム（`ideation/rough-mockups/wireframes.md`・`user-flow.md`）を、
> 承認済みユーザーストーリー（`inception/user-stories/stories.md`）と要件
> （`inception/requirements-analysis/requirements.md`）に照らしてミッド〜ハイフィデリティへ洗練した。
> 表示対象はダッシュボードの KPI サマリ部のみ（既存 FE-1〜FE-6 の残部は変更しない）。
> 表示文字列・色・状態は `design-system-mapping.md` ・`interaction-spec.md` ・`accessibility-checklist.md`
> と整合させる。

## 変更後の KPI サマリセクション（デスクトップ / ラージグリッド）

```
+-----------------------------------------------------------------------------------------------+
|  KPI サマリ                                                        (h2・aria-labelledby 紐付) |
|  +-----------+ +-----------+ +-----------+ +-------------------+ +-------------------------+ |
|  | 監視センサー数 | | Level 3   | | Level 2   | | Level 1           | | 推定削減コスト · 試算値  | |
|  |            | | 破裂リスク | | 警告       | | 微小漏水（AI検知）  | |                         | |
|  |  999       | |  1        | |  3        | |  8                | |  204.8万円             | |
|  |  台         | |  件        | |  件        | |  件                | |  前提:                 | |
|  |            | |           | |           | |                   | |  docs/business-model.md| |
|  +-----------+ +-----------+ +-----------+ +-------------------+ +-------------------------+ |
|                                                                                               |
|  カード間隔: gap-4 / カード: rounded-xl border bg-white p-4 shadow-sm（既存 KpiCard を踏襲）      |
+-----------------------------------------------------------------------------------------------+
```

**カード並び（降順・DOM 出現順）:** [wireframes] [Q1=A]

| 順 | testId | ラベル | 値 | 単位 | アクセント |
|---|---|---|---|---|---|
| 1 | `kpi-card-sensors` | 監視センサー数 | `totalSensors`（ja-JP 数値） | 台 | なし |
| 2 | `kpi-card-level3` | Level 3 破裂リスク | `level3Count`（ja-JP 数値） | 件 | 赤（`getSeverityMeta(3).accentClass`） |
| 3 | `kpi-card-level2` | Level 2 警告 | `level2Count`（ja-JP 数値） | 件 | 黄（`getSeverityMeta(2).accentClass`） |
| 4 | `kpi-card-level1` | Level 1 微小漏水（AI検知） | `level1Count`（ja-JP 数値） | 件 | **lime 黄緑**（`getSeverityMeta(1).accentClass`） |
| 5 | `kpi-card-cost` | 推定削減コスト · 試算値 | `formatManYen(estimatedCostSavedYen)` | — | なし |

**変更点（既存 `KpiSummary.tsx` からの差分）:**
- 「本日の検知数（`todayDetections`）」カードを削除し、**Level 1 カード（`level1Count`）**を追加。 [requirements FR-5] [stories US-2 AC2]
- Level 1 ラベルは **`getSeverityMeta(1).label` と整合**させる（例: 「Level 1 微小漏水（AI検知）」）。 [stories US-2 AC2]
- Level 1 カード色は **lime 黄緑**（`getSeverityMeta(1)` 再利用。承認済み Q4=A）。 [stories]
- カード構成は 5 枚のままなので `lg:grid-cols-5` グリッドは不変。 [NFR-5] [wireframes]

## 「試算値」注記（推定削減コストカード）— 2 段構成

> **Q1=A（承認済み 2026-08-11・統合サマリ確認済み）:** User Stories レビュー Major 指摘（FR-6 結合リテラル vs
> US-2 AC3 2段構成の乖離）を本ステージで解消し、**2 段構成**に確定した。 [stories] [requirements]

```
+------------------------------------------+
| 推定削減コスト · 試算値      <- 見出し p + ラベル「試算値」  [Q1=A]
|                                          |
|  204.8万円                 <- 金額（formatManYen）        |
|  前提:                     <- インライン短文（常時表示）     |
|  docs/business-model.md                   |
+------------------------------------------+
```

**表示文字列（固定・完全一致アサート対象）:**
- **見出しラベル:** `試算値` — カード見出し「推定削減コスト」の隣に `· 試算値` として併記
- **カード本文注記:** `前提: docs/business-model.md` — カード本文の金額下にインライン短文として常時表示
- テストは 2 文字列の完全一致 + 連結文字列「試算値（前提: docs/business-model.md）」の部分一致
  で、FR-6 の文言要件（両文字列が常に画面にあること）を満たす。 [requirements FR-6] [stories US-2 AC3]

**注記が 2 段構成である根拠:** [requirements FR-6] は「結合リテラル」と書くが、上流ワイヤーフレーム
（承認済み Q2=A）と US-2 AC3 はいずれも 2 段構成（見出しラベル + カード本文注記）を指示する。
カード見出し（視認性）と前提文書の注記（透明性）を分離することで「根拠のない金額を断定的に
見せない」（business-model.md §3.5）を満たす。 **実装・QA は本 2 段構成を正とし、FR-6 の「結合
リテラル」表記は 2 段構成の表示内容を言い表したものと解釈する**（approval-handoff:c6 学習:
Major 指摘は次段成果物で解決・明記して引き継ぐ）。

## スケルトン表示（初回ロード中 / 取得失敗後）

```
+-----------------------------------------------------------------------------------------------+
|  KPI サマリ                                                    (aria-busy="true" 付与)       |
|  +---------+ +---------+ +---------+ +---------+ +---------+                                  |
|  | ▓▓▓▓    | | ▓▓▓▓    | | ▓▓▓▓    | | ▓▓▓▓    | | ▓▓▓▓    |  スケルトンカード×5              |
|  | ▓▓▓▓    | | ▓▓▓▓    | | ▓▓▓▓    | | ▓▓▓▓    | | ▓▓▓▓    |  （animate-pulse）             |
|  +---------+ +---------+ +---------+ +---------+ +---------+                                  |
+-----------------------------------------------------------------------------------------------+
```

**仕様:**
- 初回取得成功前・取得失敗後・再取得成功までは KPI カード群を**すべてスケルトン表示**に切り替え、
  取得成功まで更新しない（「古い値を最新として見せない」）。 [requirements FR-8] [stories US-3 AC1]
- スケルトンはカードと同じ形状・サイズのグレーアニメーション 5 枚で、レイアウトの跳びを防止。 [wireframes]
- スケルトン描画は **DashboardClient が `kpiData` 未取得成功時に `data-testid="kpi-skeleton"` を描画**する
  方式とし、KpiSummary は表示専用のまま保つ（US-2=表示単位・US-3=状態遷移単位の責務分割）。 [stories US-3 AC5]
- アニメーションは `animate-pulse`。`prefers-reduced-motion` では無効化。 [interaction-design-patterns]
- スケルトン表示中は数値テキストを一切表示しない（stale 値非表示の担保）。 [stories US-3 AC2]

## 配置（DashboardClient 内の全面幅セクション）

```
+-----------------------------------------------------------------------------------------------+
|  <main>                                                                                       |
|    <KpiSummary …/>            <- 全面幅セクション（DashboardClient のルート構造変更で先頭に描画） |
|    <div class="grid grid-cols-1 gap-4 lg:grid-cols-3">   <- 既存の3列グリッドを包む親要素        |
|      <section センサー地図  lg:col-span-2 />                                                  |
|      <section アラート一覧 />                                                                   |
|      {selectedAlert && <AlertDetailDrawer />}                                                  |
|    </div>                                                                                     |
+-----------------------------------------------------------------------------------------------+
```

**変更点（既存 `DashboardClient.tsx` からの差分）:**
- KPI セクションを DashboardClient の**先頭に全面幅**で描画し、既存 3 列グリッド（地図 / 一覧 / ドロワー）
  はその下に置く（KPI はページ最上部の俯瞰情報として地図・一覧より先に見せる）。 [requirements FR-7] [stories US-2 AC6]
- `page.tsx` は `<KpiSummary …/>` の直接描画を削除し、**Server Component のまま**維持する
  （`MOCK_KPI_DATA` 撤去・KpiSummary import 削除）。 [requirements FR-4] [stories US-2 AC5]
- KPI のポーリング周期はアラートと同じ **5 秒**（`ALERT_POLL_INTERVAL_MS = 5000` を共用）。 [requirements FR-7] [stories US-3 AC4]

## レスポンシブ挙動

| ブレークポイント | 挙動 |
|---|---|
| mobile（<640px） | `grid-cols-1` — カード 5 枚が縦積み（既存どおり。専用レイアウトはスコープ外） |
| sm（640–1023px） | `sm:grid-cols-2` — カード 2 列 + 残り 1 枚（既存どおり） |
| lg（≥1024px） | `lg:grid-cols-5` — カード 5 枚が 1 行（デモの主表示対象） |

- モバイル専用レイアウトは**スコープ外**と明記する（ダッシュボード中心の変更で許容。wireframes レビュー Minor 5 解消）。 [team-practices]

## Assumptions & Open Questions

- スケルトン・試算値注記の表示文字列は本成果物で確定済み。追加の未確定項目はなし（None.）
- `today_detections`（本日の検知数）は表示対象外（カード削除。requirements Out of Scope と整合）。

## Sources

- [wireframes] `ideation/rough-mockups/wireframes.md`（カード構成・試算値注記配置・スケルトン・アクセシビリティ注記）
- [user-flow] `ideation/rough-mockups/user-flow.md`（ハッピーパス / エラーフロー / スケルトン切替）
- [stories] `inception/user-stories/stories.md`（US-1〜4・試算値 2 段構成 Q1=A・Minor 1/4 引き継ぎ）
- [requirements] `inception/requirements-analysis/requirements.md`（FR-4〜8 / NFR-5 / Out of Scope）
- [team-practices] `inception/practices-discovery/team-practices.md`（変換境界・フォールバック Q10 / 単一ソース Q9 / coverage ゲート）
- [Q1] 本ステージ質問 `inception/refined-mockups/refined-mockups-questions.md`（Q1=A 2段構成・承認ゲート確認済み）
