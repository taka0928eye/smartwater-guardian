# Requirements — FE-7 KPIサマリの実データ連携と「試算値」注記

> 本要件は上流成果物（`ideation/intent-capture/intent-statement.md`・`ideation/scope-definition/scope-document.md`・
> `inception/practices-discovery/team-practices.md`）と、本ステージの明確化質問
> `requirements-analysis-questions.md`（Q1〜Q4 回答）を統合して記述する。
> 対象は Issue #19「FE-7: KPIサマリの実データ連携と「試算値」注記の実装」。

## Intent Analysis（意図分析）

### 背景と課題

ダッシュボードの KPI サマリは、現状 `frontend/src/app/page.tsx` の `MOCK_KPI_DATA`（`estimatedCostSavedYen: 1_420_000` /
`totalSensors: 1240` 等）というハードコード値を表示しており、算定根拠のない金額を断定的に見せている。
`docs/business-model.md` §3.5 は「根拠のない金額を断定的に見せない」ことを求めるため、この状態は規約違反にあたる。

バックエンド側は BE-8 で `GET /api/v1/kpi/summary`（`backend/app/schemas/kpi.py` の `KpiSummary`）が実装済みであり、
実データ（`total_sensors` / `level1_count` / `level2_count` / `level3_count` / `estimated_cost_saved_yen` /
`is_estimate` / `assumption_doc`）を返す。本スコープはこれをフロントの実表示へ配線し、`MOCK_KPI_DATA` を撤去する。

あわせて `SeverityLevel` 型が `frontend/src/types/api.ts` と `frontend/src/lib/severity.ts` の 2 箇所に定義されており
（単一ソース原則に反する）、`intent-statement` と `team-practices`（Q9: A 確定）は FE-7 での解消を求めている。

### 上流成果物との整合

- **intent-statement.md** — 成功指標は「`MOCK_KPI_DATA` 削除」「`SeverityLevel` をリポジトリ内 1 箇所のみ」「試算値注記の常時表示」
  「バックエンド停止中のスケルトン表示」「`page.tsx` は Server Component のまま」「`any` 不使用」「build/lint/test 成功・カバレッジ 80%」。
  配線方式は「`DashboardClient` 側で `fetchKpiSummary()` をポーリングし `KpiSummary` をその配下で描画」（Q2 確定）を採用する。
- **scope-document.md** — 対象は Issue #19 記載の **6 ファイルのみ**（`frontend/src/types/api.ts`・`frontend/src/lib/api.ts`・
  `frontend/src/app/page.tsx`・`frontend/src/components/dashboard/KpiSummary.tsx`・
  `frontend/src/lib/__tests__/api.test.ts`・`frontend/src/components/dashboard/__tests__/KpiSummary.test.tsx`）。
  バックエンド（BE-8）は変更しない。カード構成は「本日の検知数カード削除・レベル1カード追加」。
- **team-practices.md** — フロント↔バックエンドの `snake_case`→`camelCase` 変換は `lib/api.ts` 境界で 1 回だけ行う。
  API エラーは `ApiError` へ変換し、ポーリングはクリーンアップで `clearInterval` と `cancelled` フラグを徹底する。
  フォールバックはスケルトン表示のみで、`MOCK_KPI_DATA` を実データの代わりに表示しない（Q10: A 確定）。

### 前提の補正（Q1 確定）

Issue #19 は「`types/api.ts` の `SeverityLevel` は `1 | 2 | 3`（Level 0 を表現できない）」という前提で修正を求めているが、
**現状コード `frontend/src/types/api.ts:16` は既に `0 | 1 | 2 | 3` を定義済み**（FE-5 commit 69da0ff で Level 0 を追加済み）。
`lib/severity.ts` も `0 | 1 | 2 | 3` であり、値集合は両ファイル一致している。よって「`1|2|3` への修正」は既に完了済みであり、
残る作業は **二重定義解消（`lib/severity.ts` を単一ソースとし `types/api.ts` から re-export）のみ** とする。
Issue #19 の「1|2|3」記述は陳腐化した前提として、成果物・コードコメントに注記する。

## Functional Requirements

### FR-1: `KpiSummary` 型定義（`types/api.ts`）
- バックエンド `KpiSummary`（BE-8 / `backend/app/schemas/kpi.py`）と 1:1 に対応する型を `frontend/src/types/api.ts` に追加する。
  camelCase 側のみ公開し、`snake_case`→`camelCase` 変換は `lib/api.ts` 境界で行う（team-practices 規約）。
- フィールド: `totalSensors: number` / `level1Count: number` / `level2Count: number` / `level3Count: number` /
  `estimatedCostSavedYen: number` / `isEstimate: boolean` / `assumptionDoc: string`。
- `any` は使用しない（TS strict）。

### FR-2: `SeverityLevel` 二重定義の解消
- `lib/severity.ts` の `SeverityLevel = 0 | 1 | 2 | 3` を単一ソースとする。
- `types/api.ts` は `lib/severity.ts` からの `import type { SeverityLevel }` を re-export し、自前の再定義を削除する。
- 値集合は現状の `0 | 1 | 2 | 3` を維持し、バックエンド `Literal[0,1,2,3]` と一致させる。
- 陳腐化コメント（Issue #19 の「1|2|3」前提）を現状に合わせて更新する。

### FR-3: `fetchKpiSummary` API クライアント（`lib/api.ts`）
- `fetchKpiSummary(): Promise<KpiSummary>` を `frontend/src/lib/api.ts` に追加する。
- `GET /api/v1/kpi/summary` を `apiClient.get` で呼び、既存 `unwrap<T>` で camelCase 変換 + `ApiError` 変換を適用する。
- `apiClient` / `ApiError` / `unwrap` の既存実装を再利用する。

### FR-4: `page.tsx` からの `MOCK_KPI_DATA` 撤去
- `frontend/src/app/page.tsx` の `MOCK_KPI_DATA`（`KpiData`）定義と `<KpiSummary kpiData={MOCK_KPI_DATA} />` を削除する。
- `page.tsx` は **Server Component のまま維持**する（`'use client'` を付けない。intent-statement Q2 確定）。
- KPI 由来のハードコード数値（`1_420_000` / `1420000` / `1240` 等）を 0 件にする。

### FR-5: KPI サマリ表示の実データ構成（`KpiSummary.tsx`）
- `KpiSummary.tsx` の `KpiData` interface を、バックエンド `KpiSummary` と対応する契約（`KpiSummary` 型）に置き換える。
- カード構成を「本日の検知数（`todayDetections`）→ **レベル 1 カード（`level1Count`）**」へ変更し、
  5 カード（センサー総数 / Level 1 / Level 2 / Level 3 / 推定削減コスト）で実データのみを描画する。
- 金額表示 `formatManYen`（ja-JP / `maximumFractionDigits: 1`）等の既存フォーマットは維持する。
- `todayDetections`（本日の検知数）はバックエンドスキーマ上 FE-7 以降の対応であり、本スコープでは表示しない（scope-document Out of Scope）。

### FR-6: 「試算値」注記の常時表示
- KPI サマリに固定リテラル **「試算値（前提: `docs/business-model.md`）」** の注記を常時表示する（Q2 確定）。
- バックエンドの `assumption_doc`（`docs/business-model.md §3`）や `is_estimate` フラグでは表示を切替えない
  （現状 BE-8 は `is_estimate: true` を常時返すため、フラグ駆動にしても実質常時表示になる。実装単純性を優先する）。

### FR-7: KPI のポーリング取得（`DashboardClient`）
- `DashboardClient` で `fetchKpiSummary()` をポーリングし、`KpiSummary` をその配下で描画する（intent-statement Q2 確定）。
- ポーリング周期は **アラートと同じ 5 秒**（既存 `useAlertPolling` の `ALERT_POLL_INTERVAL_MS = 5000` に統一。Q3 確定）。
- ポーリングは `useEffect` クリーンアップで `clearInterval` と `cancelled` フラグを徹底する（team-practices 規約）。

### FR-8: 取得失敗時のスケルトン表示
- 初回取得成功前・取得失敗後・再取得成功までは、**KPI カード群をすべてスケルトン表示**に切替え、取得成功まで更新しない（Q4 確定）。
- 「古い値を最新として見せない」要件を厳密に守り、最終成功値をそのまま表示し続けない。
- バックエンド停止中でも白画面にしない（intent-statement 成功指標）。
- スケルトン表示は表示崩れ防止を目的とし、固定の KPI 数値モック（`MOCK_KPI_DATA`）を実データの代わりに表示する用途には使わない（team-practices Q10: A 確定）。

## Non-Functional Requirements

- **NFR-1（カバレッジ）**: frontend のテストカバレッジは lines / functions / branches / statements の各 **80% 以上**。
  `vitest.config.mts` の `coverage.thresholds` に設定し、ローカル `npm run test` と CI でゲートを一致させる。
- **NFR-2（品質ゲート）**: `npm run build` / `npm run lint` / `npm run test` が成功すること。TS strict を維持し、`any` を禁止する。
- **NFR-3（エラーハンドリング）**: API エラーは `lib/api.ts` 境界で `ApiError` に変換し、取得失敗時は最終状態を据え置いて
  控えめな表示に留める。ポーリングの重複実行・リークを防ぐため `clearInterval` と `cancelled` フラグを徹底する。
- **NFR-4（可読性）**: コメント・docstring は日本語で書き、docstring には Issue 参照（FE-7）を明記する。
- **NFR-5（UI 一貫性）**: 表示は既存の Tailwind v4 トーン・リテラルクラス名・`lg:grid-cols-5` グリッドを踏襲し、デザインを崩さない。

## Constraints

- **C-1（対象ファイル）**: 変更対象は Issue #19 記載の 6 ファイルのみ。バックエンド（BE-8）のスキーマ・実装は変更しない。
- **C-2（Server Component）**: `page.tsx` は Server Component のまま維持し、`'use client'` を付けない。
- **C-3（変換境界）**: `snake_case`→`camelCase` 変換は `lib/api.ts` 境界で 1 回だけ行う。
- **C-4（モック非残置）**: 実データで埋められる KPI カードに `MOCK_KPI_DATA` を残さない（project.md Forbidden）。
- **C-5（デモ期限）**: 8/15 デモ完了を最優先（P0）とし、最もシンプルな実装を選択する。

## Assumptions & Open Questions

- `SeverityLevel` の値集合は現状の `0 | 1 | 2 | 3` を維持し、二重定義解消のみ実施する（Q1 で確認済み）。Issue #19 の
  「1|2|3」記述は陳腐化した前提として注記に留める。
- 「試算値」注記は固定リテラル「試算値（前提: `docs/business-model.md`）」を常時表示する（Q2 で確認済み）。
- KPI のポーリング周期はアラートと同じ 5 秒とする（Q3 で確認済み）。
- KPI 取得失敗時はカード群をすべてスケルトン表示に切替え、取得成功まで更新しない（Q4 で確認済み）。
- `today_detections`（本日の検知数）は表示対象外（カード削除。intent-statement / scope-document で確認済み）。
- その他の未確定項目はなし（None.）

## Out of Scope

- バックエンド（BE-8）のスキーマ・実装変更
- `today_detections`（本日の検知数）の表示対応
- 認証・権限管理 / リアルタイム通知 / 本番用大型 GIS DB（CLAUDE.md スコープ外）
- 外部 BI・可視化ツールの導入（既存 Next.js / Recharts スタックとの一貫性を優先）
- AWS / クラウドインフラ（本スコープで変更なし。ローカル FastAPI + Next.js）

## Sources

- [intent-statement] `ideation/intent-capture/intent-statement.md`（問題背景・成功指標・配線方式 Q2・対象境界 Q1）
- [scope-document] `ideation/scope-definition/scope-document.md`（In Scope 6ファイル・Out of Scope・カード構成）
- [team-practices] `inception/practices-discovery/team-practices.md`（変換境界・エラーハンドリング・フォールバック Q10 / 単一ソース Q9）
- [questions] `inception/requirements-analysis/requirements-analysis-questions.md`（Q1〜Q4 回答 A）

## Review

**Verdict:** NOT-READY
**Reviewer:** aidlc-product-lead-agent
**Date:** 2026-08-11T07:50:00Z
**Iteration:** 1（advisory — 単一パス、修正ループなし）

### Findings

| # | Severity | Location | Finding | Recommendation |
|---|---|---|---|---|
| 1 | Critical | C-1 と FR-7 / FR-8 | FR-7/FR-8 は `DashboardClient.tsx` の変更を要求するが、C-1 は「Issue #19 記載の 6 ファイルのみ」で `DashboardClient.tsx` は対象外。6 ファイルは types/api.ts・lib/api.ts・page.tsx・KpiSummary.tsx・api.test.ts・KpiSummary.test.tsx のみ。FR-7「DashboardClient でポーリングし KpiSummary を配下に描画」は DashboardClient.tsx の編集なしには実装不能。上流も同じ矛盾を引き継いでおり、本ステージで解消されていない。 | `DashboardClient.tsx` を In Scope に追加し、ユーザー確認を得る（配線方式は Q2=A で確定済みのため、実質 7 ファイル目の追加が必要）。または配線方式自体を再検討（例: B 方式=Server 側 fetch）を人間に諮る。 |
| 2 | Critical | FR-7 / FR-8 と C-1 / `DashboardClient.test.tsx`（L56-59）・`page.test.tsx`（L17-20） | FR-7/FR-8 のテストファイルがスコープ外で、既存テストが壊れる。DashboardClient.test.tsx は `@/lib/api` を fetchAlerts/fetchAlertDetail のみモックしており、DashboardClient が `fetchKpiSummary` を呼ぶと undefined 参照でテストが失敗する。page.test.tsx も同様に `fetchKpiSummary` 未モック。TDD（Standard 戦略）で FR-7/FR-8 の失敗テストを書く場所がスコープ内に存在しない。 | DashboardClient.test.tsx（必要に応じ page.test.tsx）を In Scope に追加し、`fetchKpiSummary` のモック追加・スケルトン/ポーリング/クリーンアップのテストケースを明示する。 |
| 3 | Major | FR-5 と initiative-brief ワイヤーフレーム（L35, L41） | カード表示順が矛盾。FR-5 は「センサー総数 / Level 1 / Level 2 / Level 3 / 推定削減コスト」（昇順）だが、承認済みコンセプト（approval-handoff Q4=A）は「監視センサー数 / Level 3 / Level 2 / Level 1 / 推定削減コスト」（降順）で、現状の KpiSummary.tsx も L3→L2 の降順。開発者はどちらを実装すべきか判断できない。 | FR-5 のカード順を承認済みワイヤーフレーム（L3→L2→L1）に揃えるか、昇順へ変える意図を明記して人間確認する。 |
| 4 | Major | FR-7 と NFR-5 | KPI セクションの DOM 配置が未規定。FR-7 で KpiSummary が DashboardClient 配下に移るが、(a) ページ内のどこに描画するか（現状は `<main>` 直下の全面幅）、(b) DashboardClient の `lg:grid-cols-3` グリッド内に 5 列グリッドをどう収めるかの構造変更が記載されていない。page.tsx からの KpiSummary import 削除も暗黙のまま。 | KPI セクションの配置（例: DashboardClient 先頭に全面幅で描画し、その下に地図/一覧グリッド）を FR として明記する。 |
| 5 | Minor | FR-8 | スケルトン表示のテスト識別手段（data-testid 等）が未規定。KpiSummary.test.tsx で「スケルトンに切り替わった」をアサートする観測点が曖昧。 | スケルトンに testId（例: `kpi-skeleton`）を付与し、取得成功後にカード値が表示されることを含めて受入条件を具体化する。 |
| 6 | Minor | FR-1 / FR-5 | `types/api.ts` の型 `KpiSummary` とコンポーネント `KpiSummary`（KpiSummary.tsx）が同名になる。TS 上は type と value で共存可能だが、props 型名として同ファイル内に両者が現れ混乱を招く。 | 型名を `KpiSummaryData` 等に分けるか、import 時にエイリアスする旨を FR に明記する。 |
| 7 | Minor | NFR-1 | NFR-1 は「vitest.config.mts の coverage.thresholds に設定」と書くが、現状 vitest.config.mts に coverage 設定は無く（CI は CLI フラグ `--coverage.thresholds.*=80` で強制）、ローカル `npm run test`（=`vitest run`）はカバレッジを計測しない。設定を入れると vitest.config.mts（スコープ外）の変更が必要。 | NFR-1 の実現手段を「CI は CLI フラグ、ローカルは `--coverage` 付き実行」等の実態に合わせて書き直すか、vitest.config.mts を In Scope に含める。 |
| 8 | Minor | FR-2 | 「陳腐化コメントの更新」の対象ファイルが曖昧。実際に「1\|2\|3」に言及した陳腐コメントは `lib/severity.ts:12-13` にあり、これは 6 ファイル対象外。types/api.ts のコメント（L11-15）は現状と整合済み。 | 陳腐コメント更新の対象を lib/severity.ts と明記し、同ファイルをスコープに含めるか、コメント更新をスコープ外とするかを確定する。 |
| 9 | Minor | FR-6 | 「試算値」注記の表示位置が未確定。「KPI サマリに…注記を常時表示」のみで、上流ワイヤーフレームは「コストカード見出し」としている。 | 注記の配置（例: コストカード見出しのインライン短文）を FR に明記する。 |

### Summary

要件の実質（MOCK_KPI_DATA 撤去・SeverityLevel 二重定義解消・試算値注記・スケルトンフォールバック・5 秒ポーリング・today_detections 除外）は上流の意図を正しく反映しており、Q1 の前提補正（現状 `0|1|2|3` 定義済み・Issue の「1|2|3」は陳腐化）も現状コードと一致。しかし最大の問題は、**スコープが「6 ファイルのみ」と宣言されているにもかかわらず、FR-7/FR-8 のポーリング・スケルトン挙動はスコープ外の DashboardClient.tsx とそのテスト（DashboardClient.test.tsx / page.test.tsx）の変更を必須とする根本矛盾**で、このままでは C-1 を守れば FR-7/FR-8 を実装できず、守らなければスコープ境界を無断で拡大することになる。加えてカード表示順（FR-5 昇順 vs 承認済みワイヤーフレーム降順）という顧客視点の表示仕様矛盾がある。Critical 2 件の是正（DashboardClient 関連ファイルのスコープ追加の人間確認、または配線方式の再決定）と Major 2 件（カード順・KPI 配置）の解消が必要。advisory パスのため、本所見は承認ゲートでの Request Changes 判断に供する。
