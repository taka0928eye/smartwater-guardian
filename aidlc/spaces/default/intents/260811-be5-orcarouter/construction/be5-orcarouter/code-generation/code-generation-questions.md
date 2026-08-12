# Code Generation — Plan Approval

`be5-orcarouter` ユニットのコード生成プランを承認するか確認します。

## プラン概要（コード生成プラン本文: `code-generation-plan.md`）

- **対象ファイル（5）**: `data/repair_parts.json`（新規）/ `app/services/orcarouter.py`（新規）/ `app/routers/alerts.py`（501 スタブ差替）/ `tests/test_orcarouter.py`（新規）/ `.env.example`（定義確認）
- **付随変更**: `tests/test_alerts.py` の `TestWorkOrderStub`（501 → 200 + fallback に最小更新。受入条件1の必然的帰結）
- **一次ソース**: GitHub Issue #13 の受入条件13件（トレーサビリティ表で TDD ステップと対応付け）
- **TDD 手順**: Step 1 テスト Red → Step 2-4 最小実装 Green → Step 5 ルーター統合 → Step 6 Refactor（ruff / mypy）→ Step 7 自走確認（カバレッジ 行 + branch 各 80%・`.env` gitignore 再確認）
- **再利用**: OR-1（HttpClientDep）/ OR-2（prompts・WorkOrder）/ OR-4（llm_cost）を流用し、新規実装は HTTP 呼出・リトライ分類・フォールバック・キャッシュ・FR-6 計測に集中

## Plan Approval

受入条件13件を一次ソースとし、5 ファイル + 付随変更（test_alerts.py）の TDD 実装プランを承認しますか？

[Answer]: Approve Plan
