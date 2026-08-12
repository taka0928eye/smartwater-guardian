# Scope Definition — BE-5: services/orcarouter.py によるLLM自動起票の実装

## 目的と方法

本スコープ定義書は、前段イニシアティブ・ステートメント（`ideation/intent-capture/intent-statement.md`）・フィージビリティ評価（`ideation/feasibility/feasibility-assessment.md`）・制約レジスタ（`ideation/feasibility/constraint-register.md`）を入力とし、BE-5（Issue #13）のイン / アウト境界・優先順位・依存関係・実装順序を確定します。質問ファイル（`ideation/scope-definition/scope-definition-questions.md`、Q1〜Q3 回答済み）とチーム実践（`scope-definition:c1 / c2 / c5` 学習）を引用し、デモ（8/15）完了・実装完了（8/13 想定）に直結する最小スコープを定義します。 [intent] [feasibility] [constraint] [Q1] [Q2] [Q3]

## インスコープ（In Scope）

BE-5 の実装対象は、Issue #13 記載の4ファイルにフォールバック用部材マスタを加えた以下の通りです（Q1: A 確定）。 [Q1] [intent]

| # | ファイル | 変更種別 | 内容 |
|---|---|---|---|
| 1 | `backend/app/services/orcarouter.py` | 新規 | Orcarouter API 呼び出し・リトライ（5xx/ネットワーク1回）・4xx/パース失敗即フォールバック・キャッシュ・FR-6 原価記録（`llm_cost.calculate_and_enrich_cost` 再利用）の編成。フォールバック応答（`source == "fallback"`）を内包 |
| 2 | `backend/app/routers/alerts.py` | 修正 | `POST /alerts/{telemetry_id}/work-order` の 501 スタブを `orcarouter.py` 呼び出しへ差し替え。実在 ID は 404 を維持 |
| 3 | `backend/.env.example` | 修正 | `ORCAROUTER_API_KEY` 環境変数定義の追記 |
| 4 | `backend/tests/test_orcarouter.py` | 新規 | `httpx.MockTransport` によるモックテスト（Q1: A の方針・feasibility 回答 A） |
| 5 | `backend/app/data/repair_parts.json` | 新規 | フォールバック用部材マスタ（材質×口径の最小版） |

## アウトオブスコープ（Out of Scope）

- フロントエンド変更（FE-6 起票モーダルは並行開発中・BE-5 の完了をブロックしない） [intent]
- 認証・権限管理 / 物理 IoT 通信プロトコル / リアルタイム通知 / 本番用大型 GIS DB（Strict Out of Scope） [constraint]
- 本番用 DB・クラウドインフラ（インメモリストア + JSON マスタでデモ成立） [constraint]
- OR-3（#14）の完全なフォールバック実装（BE-5 では最小内包に留め、後続 OR-3 マージ時に委譲・強化へ切替） [feasibility]
- 規制・コンプライアンス要件（PCI / HIPAA / SOC2 / データレジデンシー）は N/A [feasibility]

## 優先順位（MoSCoW）

単一 Issue（BE-5）完結スコープのため、バックログの優先度はすべて Must-have として扱います（`scope-definition:c5` 学習に整合）。 [memory:M4] [Q2]

| 優先度 | 内容 |
|---|---|
| Must-have | 全11受入条件（Issue #13 記載）: LLM 自動起票（FR-3 / FR-4 中核）・`WorkOrder` 型返却・`source == "llm"` / `"fallback"`・FR-6 原価5フィールド記録・タイムアウト30秒・リトライ/フォールバック・API キー非出力（NFR-4）・カバレッジ80%以上 |
| Should-have | なし（単一 Issue のため分離不要） |
| Could-have / Won't-have | なし |

## 依存関係（Dependencies）

| ID | 依存 | 状態 | 種別 |
|---|---|---|---|
| D-1 | `backend/app/dependencies.py` の `HttpClientDep`（OR-1） | 実装済み | 実装基盤（再利用） |
| D-2 | `docs/llm-cost.md` §2 のレスポンス契約（`model` / `usage` / `latency_ms`） | 規定済み | 外部契約 |
| D-3 | `backend/app/schemas/work_order.py`（OR-2 `WorkOrder` / `RepairPart`・FR-6 原価5フィールド） | 実装済み | 上流成果物（再利用） |
| D-4 | `backend/app/services/prompts.py`（OR-2 `build_system_prompt` / `build_user_prompt` / `extract_json_from_response`） | 実装済み | 上流成果物（再利用） |
| D-5 | `backend/app/services/llm_cost.py`（OR-4 `calc_cost_yen` / `calculate_and_enrich_cost`） | 実装済み | 上流成果物（再利用） |
| D-6 | `backend/app/data/repair_parts.json`（フォールバック用・材質×口径の最小版） | BE-5 で新規作成 | 実装資産 |
| D-7 | フロント FE-6（起票モーダル） | 並行開発中 | 並行作業（BE-5 をブロックしない） |

## 実装順序（Sequencing）

依存先順で実装を進めます（Q3: A 確定・`scope-definition:c2` 学習に整合）。テスト（Red）も同順に追加し TDD サイクルを維持します。 [Q3] [memory:M3]

1. `repair_parts.json` — フォールバック用部材マスタ（材質×口径の最小版）
2. `services/orcarouter.py` — LLM 呼び出し・リトライ・フォールバック・キャッシュ・原価記録の編成（`prompts.py` / `llm_cost.py` / `schemas/work_order.py` 再利用）
3. `routers/alerts.py` — 501 スタブを `orcarouter.py` 呼び出しへ差し替え
4. `tests/test_orcarouter.py` — モックテスト（`httpx.MockTransport`）・カバレッジ80%以上（行 + branch 各80%）
5. `.env.example` — `ORCAROUTER_API_KEY` の定義追記

## 成果物境界（Artifact Boundary）

- `orcarouter.py` は薄いルーターにせず、ビジネスロジック（LLM 編成・フォールバック）をサービス層に集約する（TC-8 レイヤー境界）。 [constraint]
- API キーはログ・例外メッセージ・HTTP レスポンスのいずれにも出力しない（NFR-4・TC-5）。 [intent] [constraint]

## Assumptions & Open Questions

- スコープは単一 proto-Unit（BE-5）として扱い、受入条件11件を集約する。 [assumption]
- 実装順序は依存先順で進め、テストも同順に追加する。 [assumption]
- その他の未確定項目はなし（None.）

## Sources

- [desc] GitHub Issue #13「BE-5: services/orcarouter.py によるLLM自動起票の実装」— 目的（FR-3 / FR-4 中核）・実装方針・FR-6 計測要件・受入条件11件
- [intent] `ideation/intent-capture/intent-statement.md`（問題定義・成功指標・対象ファイル・実装方針）
- [feasibility] `ideation/feasibility/feasibility-assessment.md`（技術的実現性・リスク・タイムライン）
- [constraint] `ideation/feasibility/constraint-register.md`（TC-1〜TC-9 / OC-1〜OC-6 / RC-1）
- [Q1] scope-definition 質問ファイルの回答 A（スコープ境界確定 — 4ファイル + `repair_parts.json`・FE 変更なし）
- [Q2] 同 Q2 の回答 A（単一 proto-Unit）
- [Q3] 同 Q3 の回答 A（依存先順の実装順序）
- [memory:M3] `aidlc/spaces/default/memory/project.md#Corrections` 学習 `scope-definition:c2`（実装順序は依存先順）
- [memory:M4] 同学習 `scope-definition:c5`（単一 Issue のバックログ優先度は全て Must-have）
