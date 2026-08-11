# Skill Matrix — BE-5: services/orcarouter.py によるLLM自動起票の実装

## 目的と方法

本マトリクスは、前段フィージビリティ評価（`ideation/feasibility/feasibility-assessment.md`）・スコープ定義書（`ideation/scope-definition/scope-document.md`）・インテント・バックログ（`ideation/scope-definition/intent-backlog.md`）で確定した BE-5 の実装要件に対する、能力ギャップ分析（gap analysis）を整理します。単独開発者 + AI-DLC エージェント群の構成（`ideation/team-formation/team-formation-questions.md` Q1: A）に基づき、要件ごとの必要レベルと充足状況を評価します。 [feasibility] [scope-doc] [backlog] [Q1]

## スキルマトリクス

| スキル領域 | 必要レベル | 担当エージェント/資産 | 現状 | ギャップ |
|---|---|---|---|---|
| FastAPI + Pydantic v2（strict / extra=forbid・`any` 禁止） | 高度 | developer / architect エージェント + 実装済み OR-2 | 充足（`schemas/work_order.py` 実装済み） | なし |
| pytest（`python -m pytest`・カバレッジ80% 行 + branch） | 高度 | quality エージェント + 既存テスト基盤 | 充足（`test_alerts.py` / `test_llm_cost.py` / `test_prompts.py` 実装済み） | なし |
| httpx.AsyncClient（`HttpClientDep`・タイムアウト30秒・`MockTransport` モック） | 高度 | architect / developer エージェント + 実装済み OR-1 | 充足（`dependencies.py` 実装済み） | なし |
| 外部 LLM 統合（Orcarouter API・リトライ/フォールバック・キャッシュ） | 中高度 | architect / developer エージェント | 設計方針確定（タイムアウト30秒・5xx 1回リトライ・4xx/パース失敗即フォールバック） | なし（BE-5 で内包実装） |
| 原価計測（FR-6・1行 JSON 構造化ログ） | 中 | developer エージェント + 実装済み OR-4 | 充足（`llm_cost.py` 実装済み） | なし |
| プロンプト編成（`build_system_prompt` / `build_user_prompt` / `extract_json_from_response`） | 中 | developer エージェント + 実装済み OR-2 | 充足（`prompts.py` 実装済み） | なし |

## ギャップ分析（Gap Analysis）

- ギャップなし: 必要なスキルはすべて AI-DLC エージェント群と実装済み上流資産（OR-1 / OR-2 / OR-4）で充足されます。 [feasibility] [Q1]
- 追加調達・スキルアップ・外部パートナーは不要です。唯一の不足成果物（`repair_parts.json` フォールバック用部材マスタ）は資産不足ではなく、実装対象として BE-5 内で新規作成します（フィージビリティ Q2: A 決定）。 [feasibility] [scope-doc]

## Assumptions & Open Questions

- 能力要件はすべて AI-DLC エージェント群と実装済み上流資産で充足可能と仮定する。 [assumption]
- その他の未確定項目はなし（None.）

## Sources

- [feasibility] `ideation/feasibility/feasibility-assessment.md`（OR-1/OR-2/OR-4 実装済み・OR-3 未実装を BE-5 内包）
- [scope-doc] `ideation/scope-definition/scope-document.md`（イン/アウト境界・依存関係 D-1〜D-6）
- [backlog] `ideation/scope-definition/intent-backlog.md`（単一 proto-Unit PU-1・Definition of Done）
- [Q1] team-formation 質問ファイルの回答 A（単独開発者 + AI-DLC エージェント群で確定）
