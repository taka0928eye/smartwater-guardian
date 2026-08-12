# Mob Composition — BE-5: services/orcarouter.py によるLLM自動起票の実装

## 目的と方法

本編成計画は、前段チーム評価（`ideation/team-formation/team-assessment.md`）で確定した単独開発者 + AI-DLC エージェント群の構成に基づき、BE-5（Issue #13）の実行体制を整理します。質問ファイル（`ideation/team-formation/team-formation-questions.md` Q1: A）とスコープ定義書（`ideation/scope-definition/scope-document.md`）・インテント・バックログ（`ideation/scope-definition/intent-backlog.md`）を引用します。本プロジェクトは単独開発者（人間1名）のため、従来のモブ編成（全員同一キーボード・ドライバー/ナビゲーター回転）は成立せず、AI-DLC エージェントが段階ごとにロールを担う構成を採用します。 [Q1] [scope-doc] [backlog]

## 実行体制（コンポジション）

単一 Issue（BE-5）を単一 proto-Unit（PU-1）として、AI-DLC ワークフローの各ステージで担当エージェントが順にロールを担います。 [scope-doc] [backlog]

| ステージ | 担当 | モブ代替 |
|---|---|---|
| スコープ定義（済） | product エージェント + delivery サポート | 済（承認済み） |
| チーム編成（本ステージ） | delivery エージェント | 単独開発者 + AI エージェント群（Q1: A） |
| Rough Mockups / Refined Mockups | design エージェント | スコープ対象外の場合は省略 |
| 要件分析（Inception） | product エージェント | 上流確定のため最小 |
| アプリケーション設計 | architect エージェント | 設計・NFR パターン |
| Functional Design | architect / developer エージェント | 機能設計 |
| Code Generation | developer エージェント | TDD（Red → Green → Refactor） |
| Build and Test | quality エージェント | カバレッジ80%（行 + branch）・ruff + mypy |

## 回転・ファシリテーション

- 人間（単独開発者）は承認ゲート・実決定にのみ関与します（自動承認下では最短のターン）。 [desc]
- AI エージェントのロール切替は AI-DLC オーケストレータ（`/aidlc`）が管理し、人手のファシリテーションは不要です。 [Q1]

## オンボーディング（Knowledge Transfer）

- 単独開発者のため、従来のオンボーディングチェックリストは不要です。ただし実装資産の把握（OR-1 `HttpClientDep`・OR-2 `WorkOrder`/`prompts.py`・OR-4 `llm_cost.py` の再利用境界）は、`ideation/feasibility/feasibility-assessment.md` と `ideation/scope-definition/scope-document.md` の依存関係 D-1〜D-6 に記録済みです。 [feasibility] [scope-doc]

## Assumptions & Open Questions

- チーム編成は単独開発者（人間1名）+ AI-DLC エージェント群とし、従来モブは成立しないと仮定する。 [assumption]
- その他の未確定項目はなし（None.）

## Sources

- [desc] GitHub Issue #13「BE-5: services/orcarouter.py によるLLM自動起票の実装」— 目的（FR-3 / FR-4 中核）・実装方針
- [Q1] team-formation 質問ファイルの回答 A（単独開発者 + AI-DLC エージェント群で確定）
- [scope-doc] `ideation/scope-definition/scope-document.md`（単一 proto-Unit・依存関係 D-1〜D-6・実装順序）
- [backlog] `ideation/scope-definition/intent-backlog.md`（単一 proto-Unit PU-1・Definition of Done）
- [feasibility] `ideation/feasibility/feasibility-assessment.md`（OR-1/OR-2/OR-4 実装済み・再利用境界）
