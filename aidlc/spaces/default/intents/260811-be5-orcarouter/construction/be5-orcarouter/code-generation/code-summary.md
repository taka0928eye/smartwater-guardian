# Code Summary — BE-5 services/orcarouter.py による LLM 自動起票の実装

| 項目 | 内容 |
|------|------|
| ユニット | `be5-orcarouter`（単一イテレーション / 単一論理ユニット） |
| テスト戦略 | Standard（コンポーネント別ユニットテスト + 統合境界） |
| 手法 | TDD（Red → Green → Refactor）を全ステップで徹底 |

## 生成・変更ファイル

| 種別 | ファイル | 内容 |
|------|----------|------|
| 新規マスタ | `backend/data/repair_parts.json` | 材質×口径（ductile_iron / cast_iron / pvc / steel × 75/100/150/200）の最小補修部材マスタ + 未知組合せ用 `default` エントリ（部材リスト / 作業手順 / 人員 / 工期） |
| 新規サービス | `backend/app/services/orcarouter.py` | LLM 自動起票サービス。`create_work_order()` 公開 IF、環境変数呼び出し時読込、リトライ分類（timeout/5xx→1回→フォールバック、4xx/パース失敗→即フォールバック）、`@lru_cache` 部材ローダー、モジュール内キャッシュ + `clear_work_order_cache()`、FR-6 を `llm_cost.calculate_and_enrich_cost()` へ委譲、成功/フォールバックとも 1 行 JSON 構造化ログ |
| 既存修正 | `backend/app/routers/alerts.py` | `POST /alerts/{telemetry_id}/work-order` の 501 スタブを `async def` + `HttpClientDep` 注入に差替。未知 ID→404、既知→AlertDetail 組立 + `find_pipe_by_hydrant()` → サービス呼出。ルート名 `create_work_order`・`response_model=WorkOrder` 維持 |
| 新規テスト | `backend/tests/test_orcarouter.py` | httpx.MockTransport によるサービス単体テスト 41 件（受入条件13件 + レビュー指摘対応 + カプセル化契約を網羅） |
| 既存修正 | `backend/tests/test_alerts.py` | `TestWorkOrderStub`（501）を `TestWorkOrder` に更新。既知 ID→200 + `source=="fallback"`（monkeypatch.delenv で実ネットワークなし）・未知 ID→404 維持・同一 ID 2回目→内容一致（Info #6: ルーター級は内容一致のみ・キャッシュ実証は T9 が担う旨をテスト名・コメントで明記） |
| 既存修正 | `backend/.env.example` | `ORCAROUTER_BASE_URL` / `ORCAROUTER_MODEL` / `ORCAROUTER_ENABLED` をコメント付きプレースホルダで追記（Info #7。実キーは記載しない — NFR-4） |

変更対象外（計画どおり）: `store.py` / `conftest.py` は未変更。

## 主要な実装決定

- **層分離（TC-8）**: ルーターは `get_store()` → AlertDetail 組立 → `find_pipe_by_hydrant()` → サービス呼出のみ。ビジネスロジック（リトライ分類・フォールバック・キャッシュ・FR-6 計測）は全て `services/orcarouter.py` に内包。
- **再利用（OR-1/2/4）**: `HttpClientDep`（timeout 30s）・`prompts.build_system_prompt()` / `build_user_prompt()` / `extract_json_from_response()`・`WorkOrder`/`RepairPart`・`llm_cost.calculate_and_enrich_cost()` を流用し、新規実装は編成に集中。`WorkOrder`/`RepairPart` は**再利用契約**で、Pydantic v2 既定の lax 強制変換 + extra ignore の既存挙動のまま扱う（Minor #2 で strict / extra=forbid の主張を訂正）。
- **環境変数の呼び出し時読込**: `ORCAROUTER_API_KEY` / `BASE_URL` / `MODEL` / `ENABLED` を import 時でなく呼び出し時に `os.environ` から読む（テスト分離を保つ。store.py の流儀）。
- **API キー未設定は 500 にしない**: キー欠落 or `ORCAROUTER_ENABLED=false` は HTTP 呼出なしで `source=="fallback"`（受入6）。
- **リトライ分類（受入7・8）**: timeout・ネットワーク・5xx は1回リトライ→再失敗でフォールバック。4xx・パース失敗（**不正 usage 含む — Major #1**）はリトライせず即フォールバック + 理由ログ。usage は `_UsageTokens`（Pydantic v2）で検証し、非数値・負値・キー欠落・非 dict を `llm_cost` の `int()` 変換前に遮断して未捕捉 ValueError（500）を防ぐ。
- **FR-6 計測（受入3-5・12・13）**: 成功時は `latency_ms` 計測 + usage / 実モデル名を抽出し `llm_cost` へ委譲（原価算出・構造化ログ）。フォールバック時は本モジュールで `work_order_fallback` 1 行 JSON ログ（cost 0）。キャッシュヒットはコスト再計上・再ログなし。
- **キャッシュのサービス層内包**: 同一 telemetry_id の2回目以降はモジュール内 dict から返却（LLM 再呼び出し・原価二重計上なし）。**LLM 成功時のみ保存**し、フォールバック結果はキャッシュしない（Minor #4: 一時的障害の永続化を防ぎ、次回 LLM を再試行）。`asyncio.Lock`（`_work_order_lock`）で get / 検証 / set を直列化し、並行 POST でも LLM を1回に保つ（Minor #3）。store.py はスコープ外のため変更しない（プラン Tradeoffs 明記・OR-3 マージ時に委譲可能）。
- **フォールバック部材**: 材質×口径で `repair_parts.json` を引く。未知は `default` エントリ。urgency は深刻度から導出（3→critical / 2→high / 1→medium / 0→low）、通知文面は日本語。source=="fallback"・cost_yen==0.0 で固定。
- **NFR-4（受入10）**: API キーは Authorization ヘッダのみ。ログ・例外・レスポンス・コード内リテラルに含めない（テストで `sk-supersecret` の非出現を検証）。

## テストカバレッジ

- 全テスト: **188 passed**（`--cov=app --cov-branch` で **TOTAL 99.52%**・行 + branch 各 80% ゲート通過）。
- `orcarouter.py`: **行 100% / branch 100%**。`test_orcarouter.py` 41 件（受入条件13件 + レビュー指摘対応 + カプセル化契約を網羅）。
- 残り欠落は既存 `kpi.py`（行）と `prompts.py`（branch）のみで、いずれも BE-5 変更対象外。
- 静的チェック: **ruff 0.16.2（All checks passed）**・**mypy 2.3.0（no issues in 22 source files）**。`any` 不使用。
- 型安全性: `WorkOrder` / `RepairPart` は再利用契約（Pydantic v2 既定の lax 強制変換 + extra ignore）で、strict / extra=forbid は**適用されていない**（Minor #2 で主張を訂正）。本ユニットで厳格化できるのは **usage 検証（`_UsageTokens`）** と **明示的必須キーチェック（`_validate_entry_shape`）** のみであり、いずれも Pydantic v2 / 明示検証でランタイム検証済み（project.md `code-generation:asc-c4` と整合）。

## 受入条件13件の検証状況

| # | 受入条件 | 検証 |
|---|----------|------|
| 1 | 501 でなく WorkOrder を返す | test_alerts `TestWorkOrder`（200 + fallback） |
| 2 | 部材・見積合計・手順・通知文面（source=="llm"） | T1 |
| 3 | usage からトークン数が取り込まれる | T2（prompt=800 / completion=200） |
| 4 | 実モデル名が model に反映 | T2（"orcarouter-pro-2026"） |
| 5 | latency_ms が計測・反映 | T2（>0） |
| 6 | API キー未設定でフォールバック・500 にしない | T3（HTTP 0 回・cost 0） |
| 7 | タイムアウト1回リトライ→再失敗フォールバック | T4（呼出回数 2） |
| 8 | 4xx / パース失敗は即フォールバック + 理由ログ | T6（4xx=1回・理由"401"）/ T7（パース6系統・"応答パース失敗"） |
| 9 | フォールバック時も部材・見積・通知文面を生成 | T5 + `build_fallback_work_order` 単体テスト |
| 10 | ログ・例外・レスポンスに API キーを含めない | T8（caplog / WorkOrder に非出現） |
| 11 | 同一アラート2回目以降はキャッシュ（LLM 再呼なし） | T9（2回目 HTTP 0 回）+ test_alerts 同一 ID 2回 POST。並行時も `asyncio.Lock` で LLM 1 回を保証（Minor #3・`test_concurrent_same_id_calls_llm_once`） |
| 12 | キャッシュヒットで原価を二重計上しない（FR-6） | T9（計測ログ 1 回のみ）。並行時も同様（Minor #3） |
| 13 | 毎回 1 行 JSON 構造化ログ（必須キー含む） | T10（成功 `llm_cost_measured` / フォールバック `work_order_fallback`） |

## レビュー指摘への対応（NOT-READY への再提出）

アーキテクチャレビュー（code-generation-plan.md 末尾 `## Review`）の全指摘に対する対応。TDD（Red → Green → Refactor）で、各修正の失敗テストを先に書いて Red を確認してから実装した。

| # | 指摘 | 対応 |
|---|------|------|
| Major #1 | 不正な usage 値で 500（`llm_cost` の `int()` 変換が未捕捉 ValueError） | **修正**。`orcarouter.py` に Pydantic v2 の `_UsageTokens`（`prompt_tokens` / `completion_tokens` の非負 int、extra ignore）を追加し、`_parse_llm_response()` で usage を検証。非数値・負値・必須キー欠落・非 dict は `TypeError` / `ValidationError` を上げ、2xx 成功パスの try/except がフォールバックへ振り分ける。Red テスト `test_invalid_usage_falls_back_without_500`（6 ケース）を先に書き、実機プローブでも `create_work_order()` が例外を送出せず `source=="fallback"` になることを確認。 |
| Minor #2 | 「Pydantic v2 strict / extra=forbid」の主張が実態と不一致 | **主張を訂正**（`work_order.py` は他ユニットのため変更不可）。`WorkOrder` / `RepairPart` は再利用契約（lax 強制変換 + extra ignore の既存挙動）と本サマリの再利用・型安全性節に明記し、本ユニットで厳格化できるのは usage 検証（`_UsageTokens`）と明示的必須キーチェック（`_validate_entry_shape`）のみである旨を追記。 |
| Minor #3 | キャッシュの並行非安全性（LLM 二重呼び出し・原価二重ログの余地） | **対応**。モジュールレベル `asyncio.Lock`（`_work_order_lock`）で `create_work_order()` のキャッシュ get / 検証 / set を直列化し、並行 POST でも LLM を1回に保つ。Red テスト `test_concurrent_same_id_calls_llm_once`（ハンドラに遅延を入れ割り込みを発生させ、`handler.calls == 1` を検証）。生成処理全体をロックで囲むため異なる telemetry_id の生成も直列化されるが、単一ワーカー・同時操作が稀なデモスコープでは許容と判断（Python 3.14 で複数イベントループ跨ぎの安全性も確認済み）。 |
| Minor #4 | フォールバック結果の無期限キャッシュ（一時的障害の永続化） | **対応（設計判断）**。フォールバック結果はキャッシュ**しない**（`_fallback()` からキャッシュ保存を削除し、LLM 成功時のみ `_work_order_cache` に保存）。Red テスト `test_fallback_not_cached_retries_llm_on_next_call`。既存テストはフォールバックが決定的なため回帰なし（理由は後述の設計判断節に記載）。 |
| Minor #5 | フォールバック安全網がマスタ部分破損で 500（`KeyError`） | **対応**。`_load_repair_parts()` でエントリ形状（`parts` / `work_steps` / `required_workers` / `estimated_duration_hours`）を `_validate_entry_shape()` で検証し、欠落は `TypeError` で fail-fast。Red テスト `test_entry_missing_required_key_raises_type_error`。非 dict の材質・口径エントリは `_lookup_repair_parts` が default へ落とす既存挙動を維持（ローダーはスキップ。`test_non_dict_material_entry_ignored_by_loader` / `test_non_dict_diameter_entry_ignored_by_loader` で担保）。 |
| Info #6 | test_alerts.py のルーター級キャッシュテストがキャッシュを実証しない | **対応（テスト名・コメント訂正）**。`test_same_id_second_post_returns_cached` を `test_same_id_second_post_returns_same_content` に改名し、ルーター級は内容一致（冪等性）のみ・キャッシュ実証はサービス級 T9 が担う旨をコメントで明記。 |
| Info #7 | `.env.example` に BASE_URL / MODEL / ENABLED 未記載 | **対応**。3 変数をコメント付きプレースホルダで追記（実キーは記載しない — NFR-4）。 |

### Minor #4 の設計判断（詳細）

- 選択: **フォールバック結果はキャッシュしない**（次回 POST で LLM を再試行）。
- 根拠: 一時的な LLM 障害（timeout / 5xx / キー未設定）で生成したフォールバックを無期限キャッシュすると、LLM 回復後も再試行されず、デモで LLM 出力を一度も見せられない状態が固定化しうる。次回再試行にすれば障害回復後に LLM 出力が得られる。
- コスト: 障害継続中の同一 ID 再 POST は LLM を再呼び出しする（デモでは稀）。Issue #13 受入11「同一アラートへの2回目以降はキャッシュ（LLM を再度呼ばない）」は LLM 成功生成のキャッシュを指す解釈とし、LLM 成功時キャッシュ（2回目以降 HTTP 0 回）は引き続き保証する。

## プランからの逸脱

- **レビュー指摘対応による逸脱**: プランで「追加しない」としていた `backend/.env.example` に `ORCAROUTER_BASE_URL` / `ORCAROUTER_MODEL` / `ORCAROUTER_ENABLED` を追記（Info #7。実キーは記載しない）。`orcarouter.py` に `_UsageTokens`（Major #1）・`_work_order_lock`（Minor #3）・`_validate_entry_shape`（Minor #5）を追加し、フォールバック非キャッシュ化（Minor #4）を実装。`test_alerts.py` のルーター級キャッシュテストを改名・コメント訂正（Info #6）。
- 計画どおりの対象は5ファイル（+ 付随変更 `test_alerts.py` / `.env.example`）+ レビュー指摘対応で完了。`linter` / `type-check` センサーは対象外（本ステージは Python のみの変更で `**/*.{ts,tsx}` に該当なし）。ruff / mypy は Step 6 で自走確認済み。

## 引継ぎ事項

- **`.env` は gitignore 済みを再確認**: `git check-ignore -v backend/.env` → `.gitignore:11:.env`（引継ぎ欠落2件の1つ目を解消）。
- **既定の接続先はプレースホルダ**: `ORCAROUTER_BASE_URL` 未設定時は `https://orcarouter.example.com/v1`。実エンドポイントはデモ直前に環境変数で注入（NFR-4 によりコミット禁止）。
- **デモ時に必要な環境変数**: `ORCAROUTER_API_KEY`（必須。未設定なら安全にフォールバック動作）・`ORCAROUTER_BASE_URL`（任意）・`ORCAROUTER_MODEL`（既定 "orcarouter"）・`ORCAROUTER_ENABLED`（"false" で強制フォールバック）。
- **委譲境界**: `repair_parts.json` は BE-5 内包の最小フォールバック実装。完全版 OR-3（#14）は `@lru_cache` ローダー + `build_fallback_work_order()` 単体関数の境界から切替可能。
- **コミットは未実施**: コード生成・テストのみ実施。コミットはステージ承認後の運用判断に委ねる。
