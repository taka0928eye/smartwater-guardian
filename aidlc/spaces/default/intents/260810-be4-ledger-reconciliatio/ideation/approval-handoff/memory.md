<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-08-11T00:01:29Z — 本スコープでは scope-document / intent-backlog が `consumes_absent`（カスタムスコープの最小経路で意図的省略）。イニシアティブ・ブリーフは既存アーティファクト（intent-statement / stakeholder-map）とリポジトリ実態で整合を担保

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-08-11T00:01:29Z — ステージ Step 3 の質問群（市場検証・モックアップ・モブ編成）は本スコープに該当しないため省略し、実決定に必要な2問（pipe_id形式・経過年数基準）のみ提示

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-08-11T00:01:29Z — pipe_id は Issue 例示（PIPE-001）ではなく hydrants.json 整合（P-001）を選択。マスタとの変換不要で照合の信頼性が高い（Q1 でユーザー承認）

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->

