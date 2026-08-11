# Scope Definition Questions — FE-7 KPIサマリの実データ連携と「試算値」注記

## Sources

- [desc] Initial description: "GitHub内のISSUESを確認し、ISSUE#19「FE-7: KPIサマリの実データ連携と「試算値」注記の実装」を実装してください。"
- [scope] Workflow-selected scope: `feature`.
- [intent] 前段イニシアティブ・ステートメント `ideation/intent-capture/intent-statement.md`（対象: Issue #19 記載の6ファイルのみ、配線方式: DashboardClient ポーリング、8/15 デモ完了優先）。
- [intent] Feasibility 成果物 `ideation/feasibility/feasibility-assessment.md` / `constraint-register.md` / `raid-log.md`（カード構成変更・単一ソース化・コンプラ N/A 等）。
- [memory:M1] `aidlc/spaces/default/memory/project.md#Corrections`: "ステージの質問群のうちスコープに該当しない質問（市場検証・モックアップ・モブ編成等）は省略し、実決定に必要な質問のみ提示する。 (learned 2026-08-11) <!-- cid:approval-handoff:c2 -->"
- [memory:M2] `aidlc/spaces/default/memory/project.md#Corrections`: "スコープ境界（対象ファイル・配線範囲）はユーザー確認で確定する。 (learned 2026-08-10) <!-- cid:intent-capture:c1 -->"

## Q1. スコープ境界（In/Out）の最終確認

本イニシアティブの対象は Issue #19 記載の6ファイルのみ（`types/api.ts`・`lib/api.ts`・`page.tsx`・`KpiSummary.tsx`・`api.test.ts`・`KpiSummary.test.tsx`）で、バックエンド（BE-8）は変更しない方針です。加えて Feasibility で確定した下記の変更がスコープに含まれます。この境界で確定しますか？ [intent] [Q1]

- 「本日の検知数」カード削除とレベル1カード追加（BE-8 実データ構成への変更）
- `lib/severity.ts` を単一ソースとした `SeverityLevel` の `0 | 1 | 2 | 3` への統一（`types/api.ts` から re-export）
- 「試算値（前提: `docs/business-model.md`）」注記の常時表示
- バックエンド停止時のスケルトン表示

- A. 上記の6ファイル + 上記変更をスコープとして確定する（推奨）
- B. スコープを狭める（一部を対象外にする。具体を指定）
- C. スコープを広げる（追加対応あり。具体を指定）
- X. Other (please specify)

[Answer]: A

## Q2. バックログの優先度割当（MoSCoW）

上記スコープ内の変更群を MoSCoW で分類すると、どれにしますか？ [Q1]

- A. すべて Must-have — 受入条件（成功指標）をすべて満たす（推奨。単一 Issue 完結のため）
- B. Must-have と Should-have に分ける（必須でない要素を分離。具体を指定）
- C. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Q3. バックログ単位（proto-Unit）の粒度

Issue #19 は単一イニシアティブであり、6ファイルが相互に依存する1まとまりの変更です。バックログの proto-Unit はどう分割しますか？ [intent] [Q2]

- A. 単一 Unit として扱う（分割しない。推奨 — 1実装単位で完結）
- B. 2つ以上に分割する（型/API 層と表示/配線層など。具体を指定）
- C. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Q4. 実装順序の選好

実装順序の選好（リスク先・価値先・依存先）はありますか？ [Q3]

- A. 依存先順で進める（型 → APIクライアント → 表示、が自然な依存関係。推奨）
- B. リスク先（不確実な連携を最初に）
- C. 価値先（ユーザーに見える表示を最初に）
- D. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- スコープは Issue #19 記載の6ファイル + Feasibility 確定の変更（本日の検知数カード削除・レベル1カード追加・SeverityLevel 単一ソース化・試算値注記・スケルトン表示）で確定。バックエンドは変更しない。 [Q1] [intent]
- バックログはすべて Must-have（受入条件をすべて満たす）。 [Q2]
- バックログ単位は単一 proto-Unit（分割しない）。 [Q3]
- 実装順序は依存先順（型 → APIクライアント → 表示）。 [Q4]

- Looks correct
- Request changes

[Answer]: Looks correct
