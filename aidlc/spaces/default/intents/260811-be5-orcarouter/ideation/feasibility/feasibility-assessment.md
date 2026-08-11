# Feasibility Assessment — BE-5: Orcarouter による LLM 自動起票

## 目的と方法

本評価は、前段イニシアティブ・ステートメント（`ideation/intent-capture/intent-statement.md`）で確定した BE-5（`services/orcarouter.py` による LLM 自動起票の実装）の技術的実現性・リスク・タイムラインを、feasibility 質問ファイル（`ideation/feasibility/feasibility-questions.md`、Q1〜Q3 回答済み）と上流成果物（`build-vs-buy` / `competitive-analysis` / `market-trends`）を引用して整理するものです。外部調査は実施せず、既存リポジトリ実態（`main` の `backend/`）と Issue #12 / #13 / #14 の仕様記述に基づいて評価します。実態確認（2026-08-11）により、**OR-1・OR-2・OR-4 は実装済み**であり、**OR-3（フォールバック）のみ未実装**であることを前提とします。 [intent] [Q2] [build] [competition] [trends]

## 技術的実現性（Technical Viability）

BE-5 は技術的に実現可能であり、以下の既存資産・確定仕様が実装を支えます。

- **呼び出し基盤は実装済み** — `backend/app/dependencies.py` に OR-1 で実装済みの `HttpClientDep`（`httpx.AsyncClient`・タイムアウト30秒）が存在し、外部 LLM 呼び出しの非同期クライアント基盤が揃っています。`services/orcarouter.py` はこの依存を注入して Orcarouter API を呼び出すラッパーとして新規実装します。 [intent] [Q1]
- **OR-2 / OR-4 は実装済みで再利用可能** — `schemas/work_order.py`（`WorkOrder` / `RepairPart`・FR-6 原価5フィールド含む）・`services/prompts.py`（`build_system_prompt` / `build_user_prompt` / `extract_json_from_response`）・`services/llm_cost.py`（`calc_cost_yen` / `calculate_and_enrich_cost`・1行 JSON 構造化ログ出力）が `main` に存在し、BE-5 はこれらをそのまま再利用できます。`orcarouter.py` が担当するのは、Orcarouter API 呼び出し・リトライ・フォールバック・キャッシュの編成です。 [Q2]
- **不足分は最小** — フォールバック用の補修部材マスタ `data/repair_parts.json`（材質×口径の最小版）のみ BE-5 で新規作成します。フォールバック応答（`source == "fallback"`）は OR-3（#14）が未実装のため `orcarouter.py` 内で実装し、後続 OR-3 マージ時に委譲へ切替可能に保ちます。 [Q2]
- **外部契約・実装方針は確定済み** — Orcarouter API のレスポンス契約（`model` / `usage` / `latency_ms`）は `docs/llm-cost.md` §2 に規定済みです。タイムアウト30秒・5xx/ネットワークのみ1回リトライ・4xx/パース失敗は即フォールバック、という実装方針も intent-statement の Initial Scope Signal で確定済みです。 [intent]
- **検証はモックで完結** — テストは `httpx.MockTransport` で LLM をモックするため、実 API キーなしで TDD・CI が完結します（Q1: A）。既存の `backend/tests/test_alerts.py`・`test_llm_cost.py`・`test_prompts.py` がテスト基盤として再利用できます。 [Q1]
- **Brownfield 資産の活用** — 既存ルーター（`alerts.py`）・スキーマ境界（Pydantic v2）・マスタローダー（`@lru_cache`）・カバレッジ基盤（pytest-cov 行 + branch 各80%）が揃っており、レイヤー境界（routers → services → schemas → store）に沿った追加は低リスクです。 [memory:M2]

## リスク分析（Risk Analysis）

| ID | リスク | 確度 | 影響 | 対処方針 |
|---|---|---|---|---|
| R-1 | Orcarouter 実 API キーがデモ時点で未入手 | 高 | 中 | モック中心検証（`httpx.MockTransport`）で TDD・CI 完結。実キーはデモ直前に環境変数（`ORCAROUTER_API_KEY`）で注入。未入手時はフォールバック（`source == "fallback"`）でデモ成立（Q1: A） |
| R-2 | OR-3（#14）のフォールバックが未実装 | 確定 | 中 | フォールバック応答は BE-5 の `orcarouter.py` 内で実装し、フォールバック用部材マスタ `data/repair_parts.json` を BE-5 で新規作成。後続 OR-3 マージ時に委譲へ切替（Q2: A） |
| R-3 | フォールバック部材選定ロジックの過渡実装 | 中 | 低 | `repair_parts.json` は材質×口径の最小版で実装し、OR-3 マージ時に強化・委譲 |
| R-4 | キャッシュ・リトライ境界の実装複雑度 | 中 | 低 | 同一アラート2回目はキャッシュを返す（LLM 再呼び出しなし）・タイムアウト時1回リトライ・4xx は即フォールバックの方針を関数境界で分離して実装 |
| R-5 | 実装完了タイムラインの超過 | 低 | 高 | 単一サービス + 既存ルーター差し替え + モックテスト構成で、上流（OR-1/OR-2/OR-4）が実装済みのため TDD で1〜2日以内の実装・カバレッジ80%到達は現実的（Q3: A） |

[Q1] [Q2] [Q3]

## タイムライン評価

- **8/13 実装完了は成立見込み**（Q3: A）。変更範囲はバックエンドのみで、`orcarouter.py` 新規 + `alerts.py` 修正（501 スタブの差し替え）+ テスト + `repair_parts.json` 新規であり、上流の OR-1（`HttpClientDep`）・OR-2（`WorkOrder` スキーマ / `prompts.py`）・OR-4（`llm_cost.py`）は実装済みのため、BE-5 は再利用と不足分の内包に集中できます。 [Q3] [Q2]
- **フロント並行開発の影響はなし** — FE-6（起票モーダル）は並行開発中ですが、BE-5 の完了をブロックしません。 [intent]
- 8/15 デモ（P1）までのバッファを確保でき、フェイルオーバーとしてフォールバック動作でもデモを成立させられます。 [intent] [Q1]

## 結論

BE-5 は技術的・組織的に実現可能です。デモスコープ（インメモリストア + JSON マスタ）の範囲内で、外部 LLM サービスの購入（`build-vs-buy` で buy 確定）を前提に実装します。OR-2 / OR-4 が実装済みのため、BE-5 は既存サービスを再利用して Orcarouter API 呼び出し・リトライ・フォールバック・キャッシュを編成し、`repair_parts.json` とフォールバック応答のみを内包します。主要リスク（実キー不確定・OR-3 フォールバック未実装）はモック中心検証と BE-5 内包で対処可能であり、いずれもデモ成立を阻害しません。8/13 実装完了想定も成立見込みです。 [build] [Q1] [Q2] [Q3]

## Assumptions & Open Questions

- 実 API キーはデモ（8/13）時点で入手できるか不確定であり、モック中心で検証し、実キーは環境変数で注入する。 [assumption]
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
