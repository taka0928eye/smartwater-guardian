# Team Assessment — BE-5: services/orcarouter.py によるLLM自動起票の実装

## 目的と方法

本アセスメントは、前段スコープ定義書（`ideation/scope-definition/scope-document.md`）・インテント・バックログ（`ideation/scope-definition/intent-backlog.md`）・フィージビリティ評価（`ideation/feasibility/feasibility-assessment.md`）を入力とし、BE-5（Issue #13）の実装に必要なチーム編成・能力・キャパシティを評価します。質問ファイル（`ideation/team-formation/team-formation-questions.md`、Q1 回答済み）とチーム実践（`approval-handoff:c2` 学習）を引用します。本プロジェクトは単独開発者 + AI-DLC ワークフロー（11専門エージェント）で進行するため、実体のない従来チーム編成項目は省略します。 [scope-doc] [backlog] [feasibility] [Q1]

## チーム編成（Team Composition）

BE-5 の編成は、単独開発者（人間1名）と AI-DLC エージェント群で構成されます（Q1: A 確定）。 [Q1] [scope-doc]

| 役割 | 実体 | 責務 |
|---|---|---|
| 単独開発者（人間） | 1名 | 承認ゲート・実決定・レビュー（自動承認下では最短の関与） |
| aidlc-product-agent | AI-DLC エージェント | 要件・スコープ・ユーザーストーリー（本スコープは既に上流で確定済み） |
| aidlc-delivery-agent | AI-DLC エージェント | チーム編成・Bolt 順序・ハンドオフ（本ステージ） |
| aidlc-architect-agent | AI-DLC エージェント | 設計・NFR・コンポーネント分解（アプリケーション設計以降） |
| aidlc-developer-agent | AI-DLC エージェント | コード生成・reverse engineering（Code Generation） |
| aidlc-quality-agent | AI-DLC エージェント | テスト設計・品質ゲート・カバレッジ検証 |
| その他（devsecops / operations 等） | AI-DLC エージェント | スコープに該当する場合のみ関与（本スコープは限定的） |

## キャパシティ評価（Capacity & Utilization）

- スコープは単一 Issue（BE-5・単一 proto-Unit PU-1）であり、実装対象はバックエンドのみ（`orcarouter.py` 新規・`alerts.py` 修正・`repair_parts.json` 新規・テスト・`.env.example` 修正）。 [scope-doc] [backlog]
- フルタイム割当1名で充足可能（Q1: A）。並行する競合イニシアティブはなく、FE-6（起票モーダル）は並行開発中だが BE-5 の完了をブロックしない。 [feasibility]
- 実装完了は 8/13 想定（デモ 8/15）。上流の OR-1 / OR-2 / OR-4 は実装済みで再利用するため、実装工数はフォールバック内包（`repair_parts.json` + `orcarouter.py` 内フォールバック応答）に集中する。 [feasibility]

## 能力要件（Skills Required）

| 要件 | 必要レベル | 充足 |
|---|---|---|
| FastAPI（Pydantic v2・strict / extra=forbid） | 高度 | AI-DLC エージェント群 + 実装済み OR-2 資産で充足 |
| pytest（`python -m pytest`・カバレッジ80% 行 + branch） | 高度 | AI-DLC quality-agent + 既存テスト基盤で充足 |
| httpx.AsyncClient（`HttpClientDep`・タイムアウト30秒・モックテスト `MockTransport`） | 高度 | 実装済み OR-1 資産 + AI-DLC エージェント群で充足 |
| 外部 LLM 統合（Orcarouter API・リトライ/フォールバック・キャッシュ） | 中高度 | AI-DLC architect / developer エージェントで充足 |
| 原価計測（FR-6・`llm_cost.py` 再利用・構造化ログ） | 中 | 実装済み OR-4 資産で充足 |

追加調達（外部パートナー・AWS ProServ・人材増強）は不要です。 [feasibility] [Q1]

## タイムゾーン・場所（Location & Time Zones）

- 単独開発者のみのため、タイムゾーン調整・分散チームの連絡手段設計は不要（該当者なし）。 [Q1]
- AI-DLC ワークフローは非同期で進行し、承認ゲートのみ人間のターンが発生する。 [desc]

## Assumptions & Open Questions

- チーム編成は単独開発者（人間1名）+ AI-DLC エージェント群とし、外部パートナーは不要と仮定する。 [assumption]
- スコープは単一 Issue（BE-5）のため、フルタイム割当1人で充足可能と仮定する。 [assumption]
- その他の未確定項目はなし（None.）

## Sources

- [desc] GitHub Issue #13「BE-5: services/orcarouter.py によるLLM自動起票の実装」— 目的（FR-3 / FR-4 中核）・実装方針・受入条件11件
- [scope-doc] `ideation/scope-definition/scope-document.md`（イン/アウト境界・単一 proto-Unit・依存先順の実装順序）
- [backlog] `ideation/scope-definition/intent-backlog.md`（単一 proto-Unit PU-1・受入条件11件・Definition of Done）
- [feasibility] `ideation/feasibility/feasibility-assessment.md`（OR-1/OR-2/OR-4 実装済み・OR-3 未実装を BE-5 内包・8/13 実装完了成立見込み）
- [Q1] team-formation 質問ファイルの回答 A（単独開発者 + AI-DLC エージェント群で確定）
- [memory:M1] `aidlc/spaces/default/memory/project.md#Corrections` 学習 `approval-handoff:c2`（スコープに該当しない質問は省略）
