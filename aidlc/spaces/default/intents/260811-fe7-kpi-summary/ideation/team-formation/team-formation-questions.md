# Team Formation Questions — FE-7 KPIサマリの実データ連携と「試算値」注記

## Sources

- [desc] Initial description: "GitHub内のISSUESを確認し、ISSUE#19「FE-7: KPIサマリの実データ連携と「試算値」注記の実装」を実装してください。"
- [scope] Workflow-selected scope: `feature`.
- [intent] `ideation/intent-capture/intent-statement.md`（対象: Issue #19 記載の6ファイルのみ、配線方式: DashboardClient ポーリング）。
- [feasibility] `ideation/feasibility/feasibility-assessment.md`（技術的成立・チームは FE-1〜FE-6 で同スタック実績あり）。
- [Q1] Scope Definition 質問ファイル `ideation/scope-definition/scope-definition-questions.md`（スコープ境界確定・単一 proto-Unit・依存先順）。
- [memory:M1] `aidlc/spaces/default/memory/project.md#Corrections`: "ステージの質問群のうちスコープに該当しない質問（市場検証・モックアップ・モブ編成等）は省略し、実決定に必要な質問のみ提示する。 (learned 2026-08-11) <!-- cid:approval-handoff:c2 -->"

## Q1. チーム構成（人間リソース）の確認

FE-7 はフロントエンド6ファイルの変更で、既存スタック（Next.js / TS / Tailwind / Vitest）で BE-1〜FE-6 の実績があります。チームはソロ開発者（ユーザー）+ AI-DLC エージェント（各ステージのペルソナ）で進める想定です。この構成で確定しますか？ [feasibility] [Q1]

- A. ソロ開発者 + AIエージェントで確定（外部リソース不要。推奨）
- B. 追加の人間リソース・支援が必要（具体を指定）
- X. Other (please specify)

[Answer]: A

## Q2. モブ編成（mob-composition）の扱い

モブプログラミングは複数人の同時開発に有効ですが、本件はソロ開発です。モブ編成をどう扱いますか？ [Q1]

- A. モブ編成は適用しない。AI-DLC の各ステージ・品質ゲートが役割を担う（推奨）
- B. モブ編成を計画する（具体を指定）
- X. Other (please specify)

[Answer]: A

## Q3. スキルギャップ対応の要否

必要なスキル（TypeScript / React / Next.js フロント・Vitest テスト）は既存実績で充足しており、ギャップは無いと見込んでいます。スキルギャップ対応の要否をどうしますか？ [feasibility] [Q1]

- A. ギャップなし — 追加の育成・外部調達は不要（推奨）
- B. ギャップあり（具体を指定）
- X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- チーム構成はソロ開発者 + AIエージェントで確定。外部リソースは不要。
- モブ編成は適用しない（AI-DLC のステージ・品質ゲートが役割を担う）。
- スキルギャップなし（追加の育成・外部調達は不要）。

- Looks correct
- Request changes

[Answer]: Looks correct
