# 機能設計 — ビジネスロジックモデル（BU-1: KPI サマリ）

> FE-7「KPIサマリの実データ連携と「試算値」注記の実装」BU-1（kind: `ui`）のビジネスロジックモデル。
> 本ユニットは**フロントエンドのみ**（C-1）で、バックエンド BE-8 の `GET /api/v1/kpi/summary` を
> ポーリングして描画する。バックエンド側に新規ビジネスロジックは発生しない（`services.md` §1）。
> 質問回答: Q1=A（`useKpiPolling(intervalMs: number)`）/ Q2=A（失敗時即スケルトン → 成功時復帰）/ Q3=A（3 シナリオ）。
>
> **Conversation language: 日本語**

## 1. データフロー（情報処理の流れ）

```
[BE-8] GET /api/v1/kpi/summary        … KpiSummary (snake_case 7 フィールド)
   │  5 秒ポーリング（intervalMs = ALERT_POLL_INTERVAL_MS = 5000）
   ▼
[lib/api.ts] fetchKpiSummary()        … unwrap<T> で snake_case→camelCase 変換 + ApiError 変換（C-3・1 回だけ）
   │  Promise<KpiSummary>
   ▼
[hooks/useKpiPolling] (intervalMs)    … 取得成功時のみ kpiData 更新 / 失敗時 isLoading=true（再スケルトン）
   │  { kpiData: KpiSummary | null, isLoading: boolean }
   ▼
[DashboardClient]                     … section/h2/aria-labelledby/aria-busy を一元所有（Q2=A・application-design:c1）
   │  isLoading ? <スケルトン kpi-skeleton> : <KpiSummary kpiData={kpiData} />
   ▼
[KpiSummary]                          … 5 カード + 試算値注記（表示専用。US-2）
```

- 変換は `lib/api.ts` 境界で 1 回のみ。コンポーネント層は camelCase のみを参照する（C-3 / team-practices）。
- ポーリング周期は既存 `useAlertPolling(ALERT_POLL_INTERVAL_MS)` と同一の `ALERT_POLL_INTERVAL_MS = 5000` を
  `DashboardClient` から渡す（FR-7）。KPI とアラートで更新タイミングを揃える（intent-capture:c4）。

## 2. 状態遷移（`useKpiPolling` のステートマシン）

本ユニットのビジネスロジックの中核は、KPI ポーリングの状態遷移と、それに対する描画切替である。

### 2.1 状態の定義

| 状態 | 条件 | `kpiData` | `isLoading` | 描画（DashboardClient） |
|---|---|---|---|---|
| `initial` | 初回ポーリング完了前 | `null` | `true` | スケルトン（`kpi-skeleton`） |
| `success` | 直近のポーリング成功 | `KpiSummary` | `false` | `KpiSummary` カードグリッド |
| `failure` | 直近のポーリング失敗（初回成功後を含む） | 直前値を破棄（`null`） | `true` | スケルトン（再スケルトン） |

### 2.2 遷移規則

| # | 遷移 | トリガー | 結果 | 根拠 |
|---|---|---|---|---|
| T1 | `initial → success` | `fetchKpiSummary()` 成功 | `kpiData = レスポンス` / `isLoading = false` | FR-7 |
| T2 | `initial → failure` | `fetchKpiSummary()` 失敗（初回） | `kpiData = null` のまま / `isLoading = true` | FR-8 |
| T3 | `success → failure` | ポーリング失敗 | `kpiData = null` に**破棄** / `isLoading = true` | FR-8（Q2=A） |
| T4 | `failure → success` | 次回ポーリング成功 | `kpiData = 新レスポンス` / `isLoading = false` | FR-8（Q2=A） |

- **T3 が最重要の業務ルール**: 「古い値を最新として見せない」要件を厳密に充足するため、失敗時は
  直前の成功値を**破棄**して即スケルトンへ戻す（`requirements.md` FR-8 / Q2=A）。既存
  `useAlertPolling`（最終状態据え置き）とは挙動が異なるため、共通フックに統合せず専用フック
  `useKpiPolling` を新設する（application-design:c5）。
- **不変条件**: `isLoading === true` のとき `kpiData` は `null`（スケルトン中はカード値を絶対に描画しない）。

### 2.3 ポーリング制御

- `useEffect` 内で初回 `load()` を即時実行し、その後 `setInterval(load, intervalMs)` を開始する
  （既存 `useAlertPolling` のパターンを踏襲）。
- クリーンアップで `cancelled = true` にした上で `clearInterval(id)` を呼び、アンマウント後の
  `setState` を防ぐ（team-practices 規約 / FR-7）。
- `intervalMs` 変更時は依存配列の変更で setInterval を張り替える（`[intervalMs]` 依存。既存と同じ）。

## 3. ビジネスシナリオ（データフロー検証）

Minimal 戦略（Q3=A）に従い、次の 3 シナリオを機能設計で固定する。詳細なテストケースは
`build-and-test`（テスト指示書）へ委ねる。

### 3.1 ハッピーパス

1. `DashboardClient` がマウントされ、`useKpiPolling(ALERT_POLL_INTERVAL_MS)` を開始。
2. 初回 `fetchKpiSummary()` が成功し、`kpiData` に実データ（7 フィールド）が格納される。
3. `isLoading = false` → `DashboardClient` は `KpiSummary` カードグリッド（5 カード降順）を描画。
4. 以降 5 秒ごとに再取得され、値が更新される（Level 1 カードは lime 黄緑で強調）。

### 3.2 失敗パス

1. ポーリング失敗（バックエンド停止等）。`unwrap` が `ApiError` に変換して throw。
2. `useKpiPolling` は `kpiData` を破棄し `isLoading = true` へ遷移（T3）。
3. `DashboardClient` は再スケルトン（`kpi-skeleton`）を描画。stale 値は表示されない（FR-8）。
4. バックエンド復旧後、次回ポーリング成功で T4 によりカードへ復帰。

### 3.3 アンマウント時クリーンアップ

1. ユーザーがページ遷移等で `DashboardClient` をアンマウント。
2. クリーンアップ関数が `cancelled = true` + `clearInterval` を実行。
3. ポーリング中の in-flight リクエストが完了しても `cancelled` により `setState` されない（メモリリーク防止）。

## 4. ビジネスルール・制約（UI ユニット固有）

- **カード構成**: 5 枚を降順（監視センサー数 / Level 3 / Level 2 / Level 1 / 推定削減コスト）で固定
  （FR-5 / refined-mockups:c2。`todayDetections` は表示しない）。
- **試算値注記**: 固定リテラル「試算値」見出し +「前提: docs/business-model.md」本文の 2 段構成を
  コストカードに常時表示（FR-6 / refined-mockups:c1・c3）。`assumptionDoc` は契約のみで表示未使用
  （component-methods.md §4 / ADR-004）。
- **実データのみ**: 実データで埋められるカードに `MOCK_KPI_DATA` を残さない（C-4 / project.md Forbidden）。
- **`page.tsx` は Server Component のまま**: `'use client'` を付けない（C-2 / intent-capture:c2）。
- **`any` 不使用**: TS strict を維持（NFR-2）。

## 5. エラーハンドリング方針（ロジック層）

| レイヤー | 方針 |
|---|---|
| `fetchKpiSummary`（lib/api.ts） | `unwrap<T>` が 4xx/5xx を `ApiError` へ変換して throw。非 axios エラーは透過（既存仕様） |
| `useKpiPolling` | 失敗を `isLoading = true`（再スケルトン）で吸収。例外を画面へ伝播させない。詳細は console ログに留める |
| `DashboardClient` | KPI 失敗＝スケルトン表示（白画面回避・FR-8）。アラート側は既存 `alerts-error` の控えめ表示を維持 |

## Sources

- [unit-of-work] `inception/units-generation/unit-of-work.md`（BU-1 境界・§2.2 フックシグネチャ権威）
- [unit-of-work-story-map] `inception/units-generation/unit-of-work-story-map.md`（US-1〜4 の BU-1 割当て・実装順）
- [requirements] `inception/requirements-analysis/requirements.md`（FR-4〜8 / NFR-1〜5 / Constraints C-1〜C-5）
- [components] `inception/application-design/components.md`（DashboardClient / useKpiPolling / KpiSummary 責務）
- [component-methods] `inception/application-design/component-methods.md`（公開シグネチャ・テスト観測点）
- [services] `inception/application-design/services.md`（新規サービスなし・オーケストレーション方針・データフロー）

## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-08-11T09:36:56Z
**Iteration:** 1

### Findings

| # | Severity | Location | Finding | Recommendation |
|---|---|---|---|---|
| 1 | Minor | ヘッダ（L6） | 「Q1=A（useKpiPolling(intervalMs: number)）/ Q2=A（失敗時即スケルトン → 成功時復帰）/ Q3=A（3 シナリオ）」の Q 番号が上流と対応しない。requirements の Q1〜Q4 は「SeverityLevel 前提補正 / 試算値注記 / 5秒ポーリング / 失敗時スケルトン」であり、application-design の Q1〜Q3 は「専用フック / ランドマーク所有 / フィクスチャ 2,048,400」。「3 シナリオ」は ADR に存在しない。開発者が決定トレースすると混乱する | Q 番号を application-design の質問（Q1=フック / Q2=ランドマーク / Q3=フィクスチャ）に揃えるか、無番号の決定事項として列挙する |
| 2 | Minor | §4（L98） | `isEstimate` / `assumptionDoc` の「表示未使用」根拠を ADR-004 としているが、ADR-004 の主題は試算値注記のテストアサート方式（カード内順序検証）であり、表示未使用の根拠は requirements FR-6（`assumption_doc` / `is_estimate` で表示を切替えない）と application-design Minor 4 の解決。引用が不正確 | ADR-004 への言及を FR-6 / application-design 引き継ぎ表へ変更する |
| 3 | Minor | 全体・§4 | NFR-1（カバレッジゲート恒久化: vitest.config.mts / package.json / ci.yml）が BU-1 境界（unit-of-work §2.1）に含まれるが、本成果物に実現手段の記述がない。現状 vitest.config.mts に coverage 設定は無く、package.json の `test` は `vitest run`（カバレッジ非計測）、CI は CLI フラグ（ci.yml L85）で強制。ローカルと CI のゲート一致（team-practices Q3=A）の実現手段が未定義のまま build-and-test へ渡る | build-and-test のテスト指示書対象である旨を明記するか、実現手段（thresholds 設定 or CLI フラグ統一）を 1 行で引き継ぐ |
| 4 | Minor | Sources（L111-118） | 本文で ADR-004（decisions.md）を引用するが、Sources に decisions.md が無い。consumes 契約には含まれないため upstream-coverage センサーは通るが、引用元の追跡性が不十分 | Sources に decisions.md を追記する |
| 5 | Minor | §2.3・§3.3 | `useKpiPolling` の配置ファイルパスが未記載（既存 `frontend/src/hooks/useAlertPolling.ts` から `frontend/src/hooks/useKpiPolling.ts` を推定する）。また setInterval ポーリングの特性上、リクエストが 5 秒を超えた場合に古いレスポンスが新しいレスポンスを上書きしうる out-of-order 問題が残るが、これは既存 `useAlertPolling` と同型でありデモスコープでは許容。既知の制約として明記を推奨 | フック配置パスを明記し、out-of-order 対策（リクエスト連番等）が現パターン踏襲のため未対策である旨を注記する |

### Validation Tool Results

ステージ定義（functional-design）の検証ツールはセンサー（required-sections / upstream-coverage / linter / type-check）のみで専用スクリプトなし。以下は上流契約・既存実装との手動照合結果:

| 照合対象 | 結果 | 解釈 |
|---|---|---|
| FR-7 / FR-8 との状態遷移照合（T1〜T4） | PASS | `initial→success→failure→success` の 4 遷移と不変条件（`isLoading===true ⟹ kpiData===null`）は FR-8「古い値を最新として見せない」を厳密に充足。Q2=A と整合 |
| `ALERT_POLL_INTERVAL_MS = 5000` の export | PASS | `DashboardClient.tsx` L23 に `export const ALERT_POLL_INTERVAL_MS = 5000` を確認。設計の「既存 export を DashboardClient から渡す」主張と一致 |
| 循環依存チェック | PASS | `useKpiPolling(intervalMs)` 引数化により `DashboardClient ↔ useKpiPolling` の循環は解消済み。`useKpiPolling → lib/api` の単方向依存のみ |
| 既存 `useAlertPolling` との挙動差 | PASS | 既存は失敗時 `error` 設定・最終状態据え置き。設計の「再スケルトン（破棄）」は FR-8 に基づく意図的な差で、専用フック新設の根拠（application-design:c5）と整合 |
| BE-8 契約（backend/app/schemas/kpi.py） | PASS | 7 フィールド snake_case（total_sensors / level1_count / level2_count / level3_count / estimated_cost_saved_yen / is_estimate / assumption_doc）が設計のデータフローと一致 |
| `unwrap` / `ApiError` の既存実装 | PASS | `lib/api.ts` L82 の `unwrap<T>` と L39 の `ApiError` は存在。`fetchKpiSummary` を同モジュール内に追加する設計は境界 1 回変換（C-3）を充足 |
| NFR-1 実現手段 | 一部未定義 | vitest.config.mts に coverage 設定なし / package.json `test` = `vitest run` / CI は CLI フラグ強制。機能設計に記述なし（Finding 3） |

### Summary

状態遷移（T1〜T4）・不変条件・ポーリング制御・エラーハンドリング方針は FR-7 / FR-8 / Q1=A / Q2=A と正確に整合し、循環依存は `useKpiPolling(intervalMs)` の引数化で解消済み、既存実装（`ALERT_POLL_INTERVAL_MS` / `useAlertPolling` / `unwrap` / BE-8 スキーマ）との照合も全て一致。ビジネスロジックの核となる T3（成功後失敗＝値を破棄して即スケルトン）は FR-8 を厳密に充足しており、開発者はこの文書から実装上の推測を強いられない。残る 5 件は Q 番号の帰属・ADR 引用・NFR-1 の引継ぎ明示・Sources 補完・out-of-order 注記という Minor で、いずれも実装を妨げない。Critical 0・Major 0 → **READY**。
