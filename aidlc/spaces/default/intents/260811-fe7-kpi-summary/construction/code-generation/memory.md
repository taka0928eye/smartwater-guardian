<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
- 2026-08-11T09:58:20Z — 実装は GitHub Issue #19（FE-7）を一次ソースとし、承認済みの unit-of-work §2.2（実装順: 型 → APIクライアント → 表示 → 設定）・functional-design 2 成果物に従って TDD（Red → Green → Refactor）で進める（ユーザー指示: 短期開発で時間が限られているため Issue 内容に沿って実装開始）。

## Deviations
- 2026-08-11T09:58:20Z — C-1（Issue 記載の 6 ファイル）は上流で解決済みのスコープ矛盾（requirements review Critical 1/2）により、unit-of-work §2.1 の BU-1 境界（14 ファイル: 10 ソース + 3 config/CI + 新規 useKpiPolling）へ拡張して実装する。DashboardClient.tsx / DashboardClient.test.tsx / page.test.tsx / useKpiPolling.ts は FR-7/FR-8 の実装に必須（承認済み）。
- 2026-08-11T09:58:20Z — NFR-1（カバレッジゲート恒久化: vitest.config.mts / ci.yml）は C-1 対象外のスコープ追加であるため、Plan Approval でユーザー確認を取る（nfr-requirements レビュアー Minor 2 引継ぎ）。

## Tradeoffs
- 2026-08-11T09:58:20Z — NFR-1 の実現手段は vitest.config.mts の `coverage: { enabled: true, thresholds: {...} }` を単一ソースとし、ci.yml の冗長な CLI フラグを `npm run test` に簡素化する方針（ローカルと CI のゲート一致。team-practices Q3=A）。thresholds は global（集計）で CI と同条件。

## Open questions
- 2026-08-11T09:58:20Z — NFR-1 実現のため vitest.config.mts / ci.yml の変更（C-1 対象外）をスコープ追加として承認いただく必要がある（Plan Approval で確認）。

## Review
- 2026-08-11T10:30:00Z — aidlc-architecture-reviewer-agent による adversarial review で **READY**（Critical 0・Major 0・Minor 4）。Minor 4 件（catch ブロックの console ログ欠落 / code-summary.md のテスト数ドリフト / setInterval out-of-order の既知制約注記 / page.test.tsx の vacuous アサート）をすべて反映済み（useKpiPolling.ts に console.error + 注記追加、code-summary.md を 13→12 テストへ修正、page.test.tsx を「142万円」「1,240台」の描画可能形式へ変更）。修正後の frontend テスト（91 Green・Statements 93.15% / Branches 84.15% / Functions 90.12% / Lines 94.05%）・lint・build を再確認。REVIEW_COMPLETED（--verdict READY）を記録済み。
