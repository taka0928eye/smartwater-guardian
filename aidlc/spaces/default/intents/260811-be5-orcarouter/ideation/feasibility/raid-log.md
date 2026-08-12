# RAID Log — BE-5: Orcarouter による LLM 自動起票

## 目的と方法

本ログは、BE-5（`services/orcarouter.py` による LLM 自動起票）の実装に伴うリスク（Risks）・前提（Assumptions）・問題（Issues）・依存（Dependencies）を整理し、デモ（8/15）完了までの追跡を可能にするものです。出典は前段イニシアティブ・ステートメント（`ideation/intent-capture/intent-statement.md`）・feasibility 質問ファイル（Q1〜Q3）・`main` リポジトリ実態の確認結果です。 [intent] [Q1] [Q2] [Q3]

## リスク（Risks）

| ID | リスク | 確度 | 影響 | 対処方針 | 所有者 |
|---|---|---|---|---|---|
| R-1 | Orcarouter 実 API キーがデモ時点で未入手 | 高 | 中 | モック中心検証（`httpx.MockTransport`）で TDD・CI 完結。実キーはデモ直前に環境変数（`ORCAROUTER_API_KEY`）で注入。未入手時はフォールバック（`source == "fallback"`）でデモ成立 | 実装者 |
| R-2 | OR-3（#14）のフォールバックが未実装 | 確定 | 中 | フォールバック応答は BE-5 の `orcarouter.py` 内で実装し、フォールバック用部材マスタ `data/repair_parts.json` を BE-5 で新規作成。後続 OR-3 マージ時に委譲へ切替（Q2: A） | 実装者 |
| R-3 | フォールバック部材選定ロジックの過渡実装 | 中 | 低 | `repair_parts.json` は材質×口径の最小版で実装し、OR-3 マージ時に強化・委譲 | 実装者 |
| R-4 | キャッシュ・リトライ境界の実装複雑度 | 中 | 低 | 同一アラート2回目はキャッシュを返す（LLM 再呼び出しなし）・タイムアウト時1回リトライ・4xx は即フォールバックの方針を関数境界で分離して実装 | 実装者 |
| R-5 | 実装完了タイムラインの超過 | 低 | 高 | 単一サービス + 既存ルーター差し替え + モックテスト構成で、上流（OR-1/OR-2/OR-4）が実装済みのため TDD で1〜2日以内の実装・カバレッジ80%到達は現実的 | 実装者 |

[Q1] [Q2] [Q3]

## 前提（Assumptions）

| ID | 前提 | 出典 |
|---|---|---|
| A-1 | Orcarouter の実 API キーはデモ（8/13）時点で入手できるか不確定であり、モック中心で検証し、実キーは環境変数で注入する。 | [assumption] |
| A-2 | OR-2（`WorkOrder` スキーマ / `prompts.py`）と OR-4（`llm_cost.py`）は `main` に実装済みであり再利用する。OR-3（#14）のフォールバックは未実装のため、フォールバック応答とフォールバック用部材マスタ（`data/repair_parts.json`）は BE-5 の実装内で必要最小限を内包して作成し、後続 OR-3 マージ時に委譲・強化へ切替可能な設計に保つ。 | [assumption] |
| A-3 | Orcarouter API の採用は Issue / PRD で確定済み（`build-vs-buy` で buy 確定）であり、本ステージで再判断しない。 | [build] |

## 問題（Issues）

| ID | 問題 | 状態 | 対処 |
|---|---|---|---|
| I-1 | OR-3（#14）のフォールバック（`source == "fallback"` 応答）が未実装。 | 未解決（実態確認済み） | BE-5 の `orcarouter.py` 内でフォールバック応答を実装し、フォールバック用部材マスタ（`data/repair_parts.json`）を新規作成して受入条件（`source == "fallback"`・FR-6 原価5フィールド・`WorkOrder` 型返却）を満たす（Q2: A） |
| I-2 | `alerts.py` の `POST /alerts/{id}/work-order` が 501 スタブのまま。 | 未解決 | BE-5 で `orcarouter.py` を呼び出し `WorkOrder` を返す実装へ差し替える（実在 ID は 404 を維持） |

## 依存（Dependencies）

| ID | 依存 | 状態 | 種別 |
|---|---|---|---|
| D-1 | `backend/app/dependencies.py` の `HttpClientDep`（OR-1） | 実装済み | 実装基盤 |
| D-2 | `docs/llm-cost.md` §2 のレスポンス契約（`model` / `usage` / `latency_ms`） | 規定済み | 外部契約 |
| D-3 | `backend/app/schemas/work_order.py`（OR-2 `WorkOrder` / `RepairPart`・FR-6 原価5フィールド） | 実装済み（再利用） | 上流成果物 |
| D-4 | `backend/app/services/prompts.py`（OR-2 `build_system_prompt` / `build_user_prompt` / `extract_json_from_response`） | 実装済み（再利用） | 上流成果物 |
| D-5 | `backend/app/services/llm_cost.py`（OR-4 `calc_cost_yen` / `calculate_and_enrich_cost`） | 実装済み（再利用） | 上流成果物 |
| D-6 | `backend/app/data/repair_parts.json`（フォールバック用・材質×口径の最小版） | BE-5 で新規作成 | 実装資産 |
| D-7 | フロント FE-6（起票モーダル） | 並行開発中 | 並行作業（BE-5 完了をブロックしない） |

## Assumptions & Open Questions

- 実 API キーはデモ時点で不確定であり、モック中心で検証し、実キーは環境変数で注入する。 [assumption]
- OR-2（`WorkOrder` スキーマ / `prompts.py`）と OR-4（`llm_cost.py`）は `main` に実装済みであり再利用する。OR-3（#14）のフォールバックは未実装のため、フォールバック応答とフォールバック用部材マスタ（`data/repair_parts.json`）は BE-5 の実装内で必要最小限を内包して作成する。 [assumption]
- その他の未確定項目はなし（None.）

## Sources

- [desc] GitHub Issue #13「BE-5: services/orcarouter.py によるLLM自動起票の実装」— 目的（FR-3 / FR-4 中核）・実装方針・FR-6 計測要件
- [intent] `ideation/intent-capture/intent-statement.md`（問題定義・成功指標・対象ファイル・実装方針）
- [Q1] feasibility 質問ファイルの回答 A（モック中心検証・実キーは環境変数注入）
- [Q2] 同 Q2 の回答 A（上流依存は BE-5 内包で新規作成）
- [Q3] 同 Q3 の回答 A（8/13 実装完了成立見込み）
- [build] `ideation/market-research/build-vs-buy.md`（buy 確定 — Orcarouter API 採用）
- [competition] `ideation/market-research/competitive-analysis.md`（LLM 自動起票の差別化位置づけ）
- [trends] `ideation/market-research/market-trends.md`（アセットマネジメント自動化トレンド）
- [memory:M2] `aidlc/spaces/default/memory/project.md#Corrections` 学習 `feasibility:c3`（デモ評価者向け内部機能・PIIなし・認証スコープ外は規制要件 N/A）
