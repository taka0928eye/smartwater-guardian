# Requirements Analysis — ステージ日誌

> ステージ進行中の観察記録。ステージ開始時に自動生成され、ステージ実行中に自動更新される。
> 手編集はしない。

## Interpretations

- 2026-08-11T07:30:00Z — Depth Standard / Test Strategy Standard（state 確認）。質問数は Standard レンジ（5〜8）だが、本スコープ（FE-7）は Issue #19・intent-statement・scope-document・practices-discovery で要件が高度に確定済みのため、実決定が必要な事項（SeverityLevel 前提補正・試算値注記の表示方式・取得失敗時フォールバック・ポーリング周期）に絞って 4 問にした（approval-handoff:c2 学習と整合）。
- 2026-08-11T07:30:00Z — Issue #19 は `types/api.ts` の `SeverityLevel` を「1|2|3（Level 0 を表現できない）」と記すが、現状コード `frontend/src/types/api.ts:16` は既に `0|1|2|3` を定義（FE-5 commit 69da0ff で解消済み）。よって「1|2|3 → 0|1|2|3 修正」は既に完了済みであり、残る作業は二重定義解消（`lib/severity.ts` 単一ソース → `types/api.ts` から re-export）のみ。この前提補正を Q1 で人間に確認する。

## Deviations

- なし（現時点）。質問ファイルはステージ日誌より先に作成する（Step 7 が先）。

## Tradeoffs

- 試算値注記の表示方式（Q2）は、Issue 例示の固定文言 vs バックエンド `assumption_doc` 駆動の 3 択で提示。`is_estimate` は常時 true（BE-8 実装）のため、フラグ駆動にしても常時表示になる点を踏まえ、実装単純性と将来の契約変化耐性の両方を選択肢に含めた。
- KPI 取得失敗時フォールバック（Q3）は、プラクティス Q10:A（スケルトン/実マスタ由来のみ、モック非残置）を前提に、ポーリング継続での復旧を推奨にした。

## Open questions

- （質問ファイル Q1〜Q4 に反映予定）ポーリング周期（Q4）はアラート 5 秒に揃えるか、分離するかは人間判断に委ねる。
- 2026-08-11T07:40:00Z — Q1〜Q4 すべて A で確定（自己編集モード）。Q1: SeverityLevel は二重定義解消のみ。Q2: 試算値注記は固定リテラル常時表示。Q3: KPI ポーリングはアラートと同じ 5 秒。Q4: 取得失敗時はスケルトン表示に切替え更新しない。Consolidated Summary Confirmation = Looks correct。次の Step 11 で requirements.md を生成する。
- 2026-08-11T07:45:00Z — Step 11 完了。requirements.md を生成（Intent Analysis / FR-1〜8 / NFR / Constraints / Assumptions / Out of Scope / Sources）。実装前提の補正（Issue #19 の「1|2|3」陳腐化・`types/api.ts:16` は既に `0|1|2|3` 定義済み）を Intent Analysis に明記し、Q1〜Q4 の確定回答を FR に反映。上流成果物（intent-statement / scope-document / team-practices）は prose 内で明示参照（upstream-coverage センサー対応）。次の Step 12 で reviewer パス（aidlc-product-lead-agent / advisory）を実行する。
- 2026-08-11T07:50:00Z — Step 12 完了。reviewer（aidlc-product-lead-agent / advisory・単一パス）が **NOT-READY**（Critical 2・Major 2・Minor 5）。審査記録を requirements.md の `## Review` 節に追記し、REVIEW_COMPLETED（NOT-READY）を記録。advisory のため修正ループなし・指摘は承認ゲートで人間が判断する。主要指摘: (1) Critical — C-1「6 ファイルのみ」と FR-7/FR-8 の `DashboardClient.tsx` 変更要求が矛盾（配線方式は Q2=A 確定のため実質 7 ファイル目が必要）。(2) Critical — DashboardClient.test.tsx / page.test.tsx が `fetchKpiSummary` をモックしていないため既存テストが壊れる。(3) Major — カード表示順（FR-5 昇順 vs 承認済みワイヤーフレーム降順）。(4) Major — KPI セクションの DOM 配置未規定。次の §13 学びリチュアルを実行し、承認ゲートへ進む。
