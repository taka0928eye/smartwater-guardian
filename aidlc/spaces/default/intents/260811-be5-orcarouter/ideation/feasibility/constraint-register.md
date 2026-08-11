# Constraint Register — BE-5: Orcarouter による LLM 自動起票

## 目的と方法

本レジスタは、BE-5（`services/orcarouter.py` による LLM 自動起票）の実装を縛る制約を、技術的（TC）・組織的（OC）・規制（RC）の3区分で整理します。制約の出典は前段イニシアティブ・ステートメント（`ideation/intent-capture/intent-statement.md`）・チーム実践（`aidlc/spaces/default/memory/{team,project}.md`）・feasibility 質問ファイル（Q1〜Q3）です。 [intent] [memory:M2] [Q1] [Q2] [Q3]

## 技術的制約（Technical Constraints）

| ID | 制約 | 内容 | 出典 |
|---|---|---|---|
| TC-1 | 変更対象ファイルの限定 | 対象は Issue 記載の4ファイル（`backend/app/services/orcarouter.py` 新規・`backend/app/routers/alerts.py` 修正・`backend/.env.example` 修正・`backend/tests/test_orcarouter.py` 新規）。実態確認（2026-08-11）により OR-2 / OR-4 が実装済みのため、Q2 の決定で不足分の `backend/app/data/repair_parts.json`（フォールバック用）のみ追加し、フロントエンドは変更しない。 | [intent] [Q2] |
| TC-2 | Pydantic v2 徹底 | 入力検証は Pydantic v2（strict / extra=forbid）。`any` は禁止。 | [memory:M2] |
| TC-3 | カバレッジ 80% 以上 | backend は行 + branch の各 80%（`--cov=app --cov-branch --cov-fail-under=80`）。実行は `python -m pytest`（pytest.exe 不使用）。 | [memory:M2] |
| TC-4 | 静的チェック | ruff + mypy を導入し CI ゲートに追加。 | [memory:M2] |
| TC-5 | シークレット管理 | API キーは環境変数（`ORCAROUTER_API_KEY`）から注入し、`.env` は gitignore で管理。ログ・例外メッセージ・HTTP レスポンスのいずれにも API キーを出力しない（NFR-4）。 | [intent] [memory:M2] |
| TC-6 | 障害処理方針 | タイムアウト30秒・5xx/ネットワークのみ1回リトライ・4xx/パース失敗は即フォールバック（NFR-5）。API キー未設定時は 500 ではなくフォールバック応答（`source == "fallback"`）。 | [intent] [Q1] |
| TC-7 | FR-6 原価計測 | 起票のたびに 1 行 JSON の構造化ログ（`telemetry_id` / `model` / トークン数 / `cost_yen` / `source` / `latency_ms`）。キャッシュヒット時に原価を二重計上しない。原価算出は実装済み `services/llm_cost.py` の `calculate_and_enrich_cost` を再利用する。 | [intent] [Q2] |
| TC-8 | レイヤー境界 | `routers`（薄く保つ）→ `services`（ビジネスロジック）→ `schemas`（外部契約）→ `store`（データ保持）の責務分離を維持し、ビジネスロジックをルーターに書かない。`orcarouter.py` は実装済みの `prompts.py` / `llm_cost.py` / `schemas/work_order.py` を再利用する。 | [memory:M2] [Q2] |
| TC-9 | 上流成果物の委譲可能性 | OR-2 / OR-4 は実装済みのためそのまま利用。BE-5 内包のフォールバック実装と `repair_parts.json` は、後続 OR-3 マージ時に委譲・強化へ切替可能な境界を保つ。 | [Q2] |

## 組織的制約（Organizational Constraints）

| ID | 制約 | 内容 | 出典 |
|---|---|---|---|
| OC-1 | デモ完了の優先 | 8/15 デモ完了（P1・想定日 8/13）を最優先とし、最もシンプルな実装を選択する。 | [desc] [Q3] |
| OC-2 | ブランチ戦略 | trunk-based。main 直コミット中心で、短命フィーチャーブランチ + PR は大規模変更時のみ。 | [memory:M2] |
| OC-3 | コミット規約 | Conventional Commits 形式（`feat:` / `fix:` 等）+ Issue 参照（BE-5）。本文は日本語。 | [memory:M2] |
| OC-4 | TDD 順守 | Red（失敗テスト）→ Green（最小実装）→ Refactor のサイクルを厳格に順守。 | [memory:M2] |
| OC-5 | レビュー体制 | 短期開発で人手が限られており、承認ゲートは自動承認で進行する。 | [desc] |
| OC-6 | フロント並行開発 | FE-6（起票モーダル）は並行開発中だが、BE-5 の完了をブロックしない。 | [intent] |

## 規制・コンプライアンス制約（Regulatory Constraints）

| ID | 制約 | 内容 | 出典 |
|---|---|---|---|
| RC-1 | 規制要件は N/A | デモ評価者向け内部機能・PIIなし・認証スコープ外の実装であり、規制・コンプライアンス要件（PCI / HIPAA / SOC2 / データレジデンシー）は N/A として扱う。 | [memory:M2] |

## 制約の充足方針

- 技術的制約（TC-1〜TC-9）は、以降の construction ステージ（functional design / code generation / build-and-test）でテスト・CI ゲートとして具現化します。特にカバレッジ・静的チェック・シークレット非出力は受入条件として検証します。 [intent]
- 組織的制約（OC-1〜OC-6）は、単一 Issue（BE-5）完結スコープとしてユニット生成・配線を進める前提を形成します。 [memory:M2]
- 規制制約（RC-1）は N/A のため、追加のコンプライアンス作業は発生しません。 [memory:M2]

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
- [memory:M2] `aidlc/spaces/default/memory/{team,project}.md`（チーム実践・プロジェクト制約）
