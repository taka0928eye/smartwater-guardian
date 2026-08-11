# User Stories — FE-7 KPIサマリの実データ連携と「試算値」注記

> 一次ソース: **GitHub Issue #19**（ユーザー指示）。Issue #19 の受入条件・検証方法・実装方針を
> INVEST 準拠のストーリーへ整理・形式化した。Q2 確定（A）: 機能領域別 4 ストーリー。
> Q3 確定（A）: カード順は承認済みワイヤーフレーム降順・全面幅・コストカード見出しに試算値注記。
> モブ編成 Round 1 の contribution を統合（Q4=A: Level 1 カード色は lime 黄緑 / Q5=A: coverage ゲートは設定で恒久化）。

## ストーリー一覧（MoSCoW: 全 Must-have — 単一 proto-Unit BU-1 完結）

| ID | ストーリー | ペルソナ | 優先度 | 依存 |
|---|---|---|---|---|
| US-1 | `KpiSummary` 型定義と `fetchKpiSummary` API クライアント | P1 | Must-have | — |
| US-2 | KPI サマリの実データ表示と「試算値」注記 | P1 | Must-have | US-1 |
| US-3 | 取得失敗時のスケルトン表示フォールバック | P1 | Must-have | US-2 |
| US-4 | `SeverityLevel` 型の単一ソース化（内部品質） | 開発者 | Must-have | — |

---

## US-1: `KpiSummary` 型定義と `fetchKpiSummary` API クライアント

**As a** 水道事業者オペレータ（P1）、**I want** バックエンド BE-8 が返す KPI サマリを型安全に取得できること、**so that** ダッシュボードが実データを表示できる。

### 受入条件（Given/When/Then）

1. Given BE-8 の `GET /api/v1/kpi/summary` が `KpiSummary`（total_sensors / level1_count / level2_count / level3_count / estimated_cost_saved_yen / is_estimate / assumption_doc）を返すとき、When `fetchKpiSummary()` を呼ぶと、Then `KpiSummary` 型（camelCase の `totalSensors` / `level1Count` / `level2Count` / `level3Count` / `estimatedCostSavedYen` / `isEstimate` / `assumptionDoc`）を返す。テストは **7 フィールドすべて**の snake→camel 変換を fixture で検証する（quality agent 指摘）。
2. Given バックエンドがエラー（4xx/5xx）を返すとき、When `fetchKpiSummary()` を呼ぶと、Then `ApiError` に変換して throw する（既存 `unwrap<T>` を再利用。4xx・5xx 両方のケースを検証する）。
3. Given `snake_case` のレスポンスのとき、When 変換すると、Then camelCase への変換は `lib/api.ts` 境界で 1 回だけ行う。検証は「返り値の camelCase アサート（ランタイム）+ コンポーネント側に `toCamelCase`／snake_case キー直参照が無いことの grep 静的確認」で行う（「変換は 1 回だけ」自体はランタイムテスト単体では観測不能なため、検証手段を明記する。quality agent 指摘）。
4. Given TS strict のとき、When 型を定義すると、Then `any` を使用しない（検証は `npm run build` / `tsc --noEmit`）。

### 実装対象（Issue #19 の作業内容 Step 1〜2）

- `frontend/src/types/api.ts` — `KpiSummary` 型追加
- `frontend/src/lib/api.ts` — `fetchKpiSummary()` 追加
- `frontend/src/lib/__tests__/api.test.ts` — Red（失敗テスト）→ Green

---

## US-2: KPI サマリの実データ表示と「試算値」注記

**As a** 水道事業者オペレータ（P1）、**I want** ダッシュボードの KPI カードに実データ（センサー総数 / Level 1〜3 / 推定削減コスト）と「試算値」注記が表示されること、**so that** 根拠のないモック数値を見せられず、事業の健全性を正しく確認できる。

### 受入条件（Given/When/Then）

1. Given BE-8 が実データを返すとき、When KPI サマリを描画すると、Then 5 カード（監視センサー数 / Level 3 / Level 2 / Level 1 / 推定削減コスト）を**降順**で表示する（承認済みワイヤーフレーム、Q3=A）。降順は DOM 出現順で検証する — testId `kpi-card-sensors` → `kpi-card-level3` → `kpi-card-level2` → `kpi-card-level1` → `kpi-card-cost` の順に出現すること（quality agent 指摘 P3）。
2. Given カード構成変更後のとき、When 表示すると、Then 「本日の検知数（`todayDetections`）」カードは表示せず「レベル 1 カード（`level1Count`）」を表示する（FR-5）。Level 1 カードのラベルは `getSeverityMeta(1).label`（例: 「Level 1 微小漏水」）と整合させる（design agent 指摘 2 / quality agent 指摘 P6）。
3. Given KPI サマリを表示するとき、When 描画すると、Then **コストカード見出しに「試算値」ラベルを併記し、カード本文に「前提: `docs/business-model.md`」のインライン短文を常時表示**する（2 段構成。Q3=A / design agent 指摘 4）。表示文字列は「試算値」と「前提: docs/business-model.md」を固定し、テストの完全一致アサートで検証する（quality agent 指摘 P6）。
4. Given KPI サマリを表示するとき、When 描画すると、Then セクションに見出し `h2`「KPI サマリ」を追加し、`aria-labelledby` で見出しに紐付ける。各カードは引き続き `p`（ラベル）のまま（design agent 指摘 3 / wireframes.md:65 の h1→h2→p 階層）。
5. Given `page.tsx` のとき、When 変更すると、Then `MOCK_KPI_DATA`（`KpiData`）定義と `KpiSummary` へのハードコード値を削除し、`page.tsx` は **Server Component のまま**維持する（`'use client'` を付けない）（FR-4）。撤去は `page.test.tsx` で `queryByText("1,240")` / `queryByText("142万円")` の非存在アサートとして検証する（quality agent 指摘 P1）。
6. Given KPI サマリの表示位置のとき、When 描画すると、Then 全面幅セクションとして DashboardClient 配下に描画する（Q3=A / レビュー指摘 #4 解消）。**配置のコード変更は US-3 の `DashboardClient.tsx` で行う**ため、本ストーリー（US-2）完了時点では位置移動は未完了である旨を注記する（developer agent 指摘）。
7. Given 型 `KpiSummary` とコンポーネント `KpiSummary` が同名になる場合、When import するとき、Then `KpiSummary.tsx` 内で `import type { KpiSummary as KpiSummaryData }` のエイリアスを採用する（Minor #6 解消。developer agent 指摘）。

### 実装対象

- `frontend/src/app/page.tsx` — `MOCK_KPI_DATA` 撤去（Server Component 維持）
- `frontend/src/components/dashboard/KpiSummary.tsx` — `KpiData` → `KpiSummary` 契約へ置換、カード構成・試算値注記・h2 見出し・Level 1 ラベル（`getSeverityMeta(1)` lime）
- `frontend/src/components/dashboard/__tests__/KpiSummary.test.tsx` — Red → Green（`BASE_KPI` fixture を 7 フィールド化）
- `frontend/src/app/__tests__/page.test.tsx` — `MOCK_KPI_DATA` 撤去の検証（`queryByText("1,240")` 非存在等）

---

## US-3: 取得失敗時のスケルトン表示フォールバック

**As a** 水道事業者オペレータ（P1）、**I want** バックエンド停止中に KPI カード群がスケルトン表示に切り替わり白画面にならないこと、**so that** 監視を継続でき、古い値を最新として誤解しない。

### 受入条件（Given/When/Then）

1. Given 初回取得成功前または取得失敗後、When KPI をポーリングすると、Then KPI カード群をすべてスケルトン表示に切り替え、取得成功まで更新しない（FR-8 / Q4=A）。状態遷移は **3 ケース**を網羅する: (a) 初回ローディング中＝スケルトン、(b) 取得成功＝カード値表示、(c) **成功後に失敗＝再スケルトン（stale 値を表示しない）**（quality agent 指摘 P4 / FR-8 の核心要件・分岐カバレッジ）。
2. Given バックエンド停止中、When ポーリングすると、Then 固定の KPI 数値モック（`MOCK_KPI_DATA`）を実データの代わりに表示しない（team-practices Q10: A）。同一テスト内で `queryByText("1,240")` / `queryByText("142万円")` の非存在をアサートする。
3. Given DashboardClient がポーリングするとき、When アンマウントまたはエラー時には、Then `clearInterval` と `cancelled` フラグでクリーンアップし、ポーリングリークを防ぐ（FR-7 / team-practices）。既存のアンマウントテストと同じフェイクタイマー手法で、アンマウント後 `advanceTimersByTime` で `fetchKpiSummary` が再呼び出しされないことを検証する。
4. Given KPI とアラートのポーリング、When 周期を設定すると、Then KPI のポーリング周期はアラートと同じ **5 秒**に統一する。単一の間隔定数（既存 `ALERT_POLL_INTERVAL_MS = 5000`）を共用し、`advanceTimersByTime(5000)` で `fetchKpiSummary` が再呼び出しされることを検証する（FR-7）。
5. Given スケルトン表示をテストするとき、When 観測すると、Then testId **`kpi-skeleton`**（固定・コンテナ単一）を付与し、取得成功後にカード値が表示されることを含めて検証する（レビュー指摘 #5 解消 / quality agent P4）。スケルトン描画は **DashboardClient が `kpiData` 未取得成功時に `data-testid="kpi-skeleton"` を描画**する方式とし、KpiSummary は表示専用のまま保つ（US-2=表示単位・US-3=状態遷移単位の責務分割。quality agent 指摘 P4）。
6. Given スケルトン表示中、When 描画すると、Then KPI セクションコンテナに `aria-busy="true"` を付与し、取得成功時に解除する。セクション全体への `aria-live` は付与しない（5 秒ポーリングでの読上げノイズ回避。`aria-live` を付ける場合はステータス 1 行に限定。design agent 指摘 6 / wireframes.md:67）。
7. Given `page.tsx` が DashboardClient を描画するとき、When `fetchKpiSummary` が未定義のとき、Then 既存テストが壊れないよう、`page.test.tsx` の `@/lib/api` モックに `fetchKpiSummary: vi.fn()` を追加する（Critical #2 完全解消。developer / quality agent 指摘）。

### 実装対象

- `frontend/src/components/dashboard/DashboardClient.tsx` — `fetchKpiSummary()` のポーリング追加・スケルトン切替・ルート構造変更（3 列グリッドを包む親要素 + KPI 全面幅セクション先頭描画。AC5 で要件化）
- `frontend/src/components/dashboard/__tests__/DashboardClient.test.tsx` — `fetchKpiSummary` モック追加（**Critical #2 解消のためスコープに含める**）
- `frontend/src/app/__tests__/page.test.tsx` — `fetchKpiSummary` モック追加（**Critical #2 完全解消のためスコープに含める**）

---

## US-4: `SeverityLevel` 型の単一ソース化（内部品質）

**As a** 開発者、**I want** `SeverityLevel` 型をリポジトリ内 1 箇所のみに定義すること、**so that** 二重定義による型の乖離（ドリフト）を防ぎ、メンテナンス性を高める。

### 受入条件（Given/When/Then）

1. Given `frontend/src/lib/severity.ts` が `SeverityLevel = 0 | 1 | 2 | 3` を定義しているとき、When `types/api.ts` を変更すると、Then `lib/severity.ts` を単一ソースとし、`types/api.ts` は `import type { SeverityLevel } from "@/lib/severity"` を **re-export** し、自前の再定義を削除する（FR-2 / Q9=要求）。re-export 後に既存コードの型参照が壊れないこと（値として使用可能）を api.test.ts で検証する。
2. Given リポジトリ全体のとき、When grep すると、Then `SeverityLevel` の定義はリポジトリ内 **1 箇所のみ**（`Literal[0,1,2,3]` と一致）である。検証は (a) ソース文字列の grep／静的アサート（`types/api.ts` に `export type { SeverityLevel } from "@/lib/severity"` が在り、`export type SeverityLevel =` が無いこと）、(b) `npm run build` / `tsc --noEmit` の型チェック成功で行う（vitest は esbuild で型を除去するためランタイムテストでは検出不能。quality agent 指摘 P5）。
3. Given Issue #19 の「1|2|3」前提が陳腐化しているとき、When コメントを確認すると、Then 陳腐化コメント（`lib/severity.ts` L12-13 の「(1|2|3)」）を現状の `0|1|2|3` に合わせて更新し、前提ズレを注記する（FR-2 / requirements-analysis:c2 学習）。検証はソース静的確認（コメント文言）で行う。

### 実装対象

- `frontend/src/lib/severity.ts` — 陳腐化コメント更新（**スコープに含める**。レビュー指摘 Minor #8 解消）
- `frontend/src/types/api.ts` — re-export 化
- `frontend/src/lib/__tests__/api.test.ts` または型テスト — Red → Green

---

## 依存関係と関係性

- US-1 → US-2 → US-3 の依存先順で実装する（scope-definition:c2 学習と整合。型 → APIクライアント → 表示）。
- US-4 は表示契約に直接依存しない独立ストーリーだが、`KpiSummary` 型追加（US-1）と同じ `types/api.ts` を触るため、同じパスを編集する US-1 と同順で実装する。
- 全ストーリーが単一 proto-Unit（BU-1）に含まれ、分割せず 1 イテレーションで完結する（scope-definition:c1 学習）。

## 対象ファイル一覧（スコープ統合版）

Issue #19 の「6 ファイル」に、モブトリアージとレビュー指摘の解決で追加したファイルを含めた**全対象一覧**を 1 箇所に明示する（developer agent 指摘）。

| ファイル | 関連ストーリー | 備考 |
|---|---|---|
| `frontend/src/types/api.ts` | US-1 / US-4 | `KpiSummary` 型追加 + `SeverityLevel` re-export |
| `frontend/src/lib/api.ts` | US-1 | `fetchKpiSummary()` 追加 |
| `frontend/src/lib/severity.ts` | US-4 | 陳腐化コメント更新（Minor #8 解消のため追加） |
| `frontend/src/app/page.tsx` | US-2 | `MOCK_KPI_DATA` 撤去（Server Component 維持） |
| `frontend/src/components/dashboard/KpiSummary.tsx` | US-2 | カード構成・試算値注記・h2・Level 1（lime） |
| `frontend/src/components/dashboard/DashboardClient.tsx` | US-3 | KPI ポーリング・スケルトン切替（**Critical #1 解消のため追加**） |
| `frontend/src/lib/__tests__/api.test.ts` | US-1 / US-4 | Red → Green |
| `frontend/src/components/dashboard/__tests__/KpiSummary.test.tsx` | US-2 | Red → Green（fixture 7 フィールド化） |
| `frontend/src/components/dashboard/__tests__/DashboardClient.test.tsx` | US-3 | `fetchKpiSummary` モック追加（**Critical #2 のため追加**） |
| `frontend/src/app/__tests__/page.test.tsx` | US-2 / US-3 | モック数値非表示 + `fetchKpiSummary` モック（**Critical #2 のため追加**） |
| `frontend/vitest.config.mts` | NFR-1 | coverage 設定追加（thresholds 各 80%。**Q5=A のため追加**） |
| `frontend/package.json` | NFR-1 | `test` を `vitest run --coverage` に変更（**Q5=A のため追加**） |
| `.github/workflows/ci.yml` | NFR-1 | coverage 設定と一致させる（**Q5=A のため追加**） |

> **スコープ拡大の根拠**: 元の 6 ファイル → 13 ファイル（+3 config/CI）。この拡大は Q2=A（配線方式 →
> DashboardClient が実装必須）、レビュー指摘 Critical #1（DashboardClient.tsx）/ Critical #2
> （DashboardClient.test.tsx / page.test.tsx）/ Minor #8（lib/severity.ts）、および Q5=A
> （NFR-1 カバレッジゲートの恒久化）で正当化される。表示契約（KpiSummary 型）とコンポーネント
> （KpiSummary.tsx）の責務は単一 proto-Unit 内で完結する。

## INVEST 準拠ノート

- **Independent**: 各ストーリーは依存先順で独立にテスト可能（US-1: api.test.ts / US-2: KpiSummary.test.tsx / US-3: DashboardClient.test.tsx + page.test.tsx / US-4: 型テスト + grep 静的確認）。
- **Negotiable**: 実装詳細（スケルトン描画の所在、`aria-live` のステータス行限定等）はストーリー内で方向性を確定したが、`refined-mockups` で視覚仕様化する余地を残す。
- **Valuable**: 各ストーリーはオペレータの監視体験または開発者の保守性に直接の価値を持つ。
- **Estimable**: 対象ファイル・受入条件が具体的で見積もり可能。
- **Small**: 各ストーリーは 1〜4 ファイルの変更に収まる。
- **Testable**: 全ストーリーに Given/When/Then の受入条件があり、テストで検証可能。

## Sources

- [Issue #19] GitHub Issue #19「FE-7: KPIサマリの実データ連携と「試算値」注記の実装」（一次ソース）
- [requirements] `inception/requirements-analysis/requirements.md`（FR-1〜8 / NFR / Constraints / Review）
- [team-practices] `inception/practices-discovery/team-practices.md`（変換境界・エラーハンドリング・フォールバック Q10 / 単一ソース Q9 / coverage ゲート）
- [business-overview] `aidlc/spaces/default/codekb/smartwater-guardian/business-overview.md`
- [wireframes] `ideation/rough-mockups/wireframes.md`・`ideation/approval-handoff/initiative-brief.md` §5（Q3=A カード順・配置）
- [contributions] `inception/user-stories/contributions/`（design / developer / quality の Round 1 contribution）
