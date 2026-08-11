# Code Generation — BU-1 質問

> FE-7「KPIサマリの実データ連携と「試算値」注記の実装」BU-1 の Code Generation 計画確認。
> **Conversation language: 日本語**

## スコープ追加の確認（NFR-1）

計画 Step 4 の対象（`frontend/vitest.config.mts` / `.github/workflows/ci.yml`）は C-1
（Issue #19 記載の 6 ファイル）対象外のため、NFR-1「カバレッジゲート恒久化」実現のための
**スコープ追加**を伴う。以下は計画の前提として確認いただきたい:

- `vitest.config.mts` に `coverage: { enabled: true, thresholds: { lines: 80, functions: 80, branches: 80, statements: 80 } }` を追加
- `ci.yml` の冗長な CLI フラグを `npm run test` に簡素化（thresholds の単一ソース化）

## Plan Approval

上記の実装計画（`code-generation-plan.md`）で Code Generation を進めてよいか?

- Approve Plan — 実装（Step 1 Red → Step 2 Green → Step 3 Refactor）へ進む
- Request Changes — 計画を修正する

[Answer]: Approve Plan
