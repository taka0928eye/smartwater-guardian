# Approval & Handoff Questions — FE-7 KPIサマリの実データ連携と「試算値」注記

## Sources

- [desc] Initial description: "GitHub内のISSUESを確認し、ISSUE#19「FE-7: KPIサマリの実データ連携と「試算値」注記の実装」を実装してください。"
- [scope] Workflow-selected scope: `feature`.
- [intent] `ideation/intent-capture/intent-statement.md`（Issue #19 要件・成功指標・配線方式・対象6ファイル）。
- [Q1] `ideation/scope-definition/scope-document.md`（スコープ境界・6ファイル対象・バックエンド変更なし）。
- [feasibility] `ideation/feasibility/feasibility-assessment.md`・`constraint-register.md`（技術成立・TC/OC/RC）。
- [Q4] Rough Mockups 質問ファイル `ideation/rough-mockups/rough-mockups-questions.md` の回答 A（カード構成・試算値・スケルトン・アクセシビリティ）。
- [review] `ideation/rough-mockups/wireframes.md` の Review 節（aidlc-product-lead-agent の Major 2件）。
- [memory:M1] `aidlc/spaces/default/memory/project.md#Corrections`: "ステージの質問群のうちスコープに該当しない質問（市場検証・モックアップ・モブ編成等）は省略し、実決定に必要な質問のみ提示する。 (learned 2026-08-11) <!-- cid:approval-handoff:c2 -->"

## Q1. スコープ境界の最終確認

イニシアティブ・ブリーフには、Issue #19 記載の6ファイル（`types/api.ts`・`lib/api.ts`・`page.tsx`・`KpiSummary.tsx`・`api.test.ts`・`KpiSummary.test.tsx`）のみを対象とし、バックエンド（BE-8）は変更しないスコープ境界を記載します。これで確定してよいですか？ [intent] [Q1]

- A. このスコープ境界で確定（推奨 — 上流成果物と整合）
- B. 範囲を変更する（コメントで指定）
- X. Other (please specify)

[Answer]: A

## Q2. 上流レビューで残った2件の Major 指摘の扱い

rough-mockups のアドバイザリーレビューで2件の Major 指摘が残っています。(1) 両成果物が intent-backlog を Sources に未参照、(2)「試算値」注記の表示方式が「ツールチップまたは短文」と曖昧。イニシアティブ・ブリーフでどう扱いますか？ [review] [intent]

- A. 「カード内の常時表示インライン短文」に確定し、ブリーフに明記（推奨 — 成功指標の常時表示と整合）
- B. 現状のまま許容（実装時に実装者判断）
- X. Other (please specify)

[Answer]: A

## Q3. タイムライン・リソースのコミットメント

8/15 デモ完了（P0・想定完了日 8/12）を最優先とし、ソロ開発者 + AI-DLC エージェントで進行します。外部リソースは不要（team-formation Q1=A）。追加の予算・リソース・モブ編成のコミットメントは不要で確定してよいですか？ [intent] [feasibility]

- A. 現状の体制・期限で確定（推奨 — 見積「小」と整合）
- B. 期限・体制を見直す（コメントで指定）
- X. Other (please specify)

[Answer]: A

## Q4. ラフモックアップが共有ビジョンを反映しているか

rough-mockups のワイヤーフレーム（5カード構成・試算値注記・スケルトン5枚・アクセシビリティ注記）は、KPI サマリの共有ビジョンを反映しています。これをイニシアティブ・ブリーフのコンセプト資料として採用してよいですか？ [Q4]

- A. 採用する（推奨 — rough-mockups 承認済み）
- B. 修正を希望する（コメントで指定）
- X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- スコープ境界は6ファイルのみ・バックエンド変更なしで確定。
- 「試算値」注記は「カード内の常時表示インライン短文」に確定。
- タイムライン（8/15 デモ P0）・体制（ソロ + AI エージェント）で確定。
- ラフモックアップをイニシアティブ・ブリーフのコンセプト資料として採用。

- Looks correct
- Request changes

[Answer]: Looks correct
