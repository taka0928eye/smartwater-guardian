# Code Generation Plan — BE-5（services/orcarouter.py による LLM 自動起票の実装）

| 項目 | 値 |
|------|-----|
| インテント | `260811-be5-orcarouter` |
| ユニット | `be5-orcarouter` |
| ステージ | code-generation |
| 一次ソース | GitHub Issue #13（受入条件13件・実装方針・検証方法） |
| テスト戦略 | Standard（ステージ別ユニットテスト5-8本 + 統合境界スタブ） |
| カバレッジゲート | 行 + branch 各 80%（`--cov=app --cov-branch --cov-fail-under=80`） |
| 静的チェック | ruff 0.16.2 / mypy 2.3.0（pyproject.toml 設定済み・CI ゲート Q6: C 確定） |
| テスト実行 | `backend/venv/Scripts/python.exe -m pytest`（pytest.exe 不使用 — project.md `build-and-test:c3`） |
| 会話言語 | 日本語（コメント・docstring・コミットメッセージ） |

## 前提（既存実装の再利用 — OR-1 / OR-2 / OR-4）

| 成果物 | モジュール | 再利用内容 |
|--------|-----------|------------|
| OR-1 | `app/dependencies.py` | `get_http_client()`（httpx.AsyncClient timeout 30s）・`HttpClientDep` |
| OR-2 | `app/services/prompts.py` | `SYSTEM_PROMPT` / `build_system_prompt()` / `build_user_prompt()` / `extract_json_from_response()` |
| OR-2 | `app/schemas/work_order.py` | `WorkOrder` / `RepairPart`（Pydantic v2 strict / extra=forbid、FR-6 コストフィールド含む） |
| OR-4 | `app/services/llm_cost.py` | `calculate_and_enrich_cost()`（usage 有無で cost 算出・構造化ログ出力） |

## 対象ファイル（スコープ: 5 ファイル）

| ファイル | 種別 | 内容 |
|----------|------|------|
| `backend/data/repair_parts.json` | 新規 | 材質×口径の最小補修部材マスタ（フォールバック用。pipes.json の材質・口径と整合） |
| `backend/app/services/orcarouter.py` | 新規 | LLM 自動起票サービス（HTTP 呼出・リトライ分類・フォールバック・キャッシュ・FR-6 計測） |
| `backend/app/routers/alerts.py` | 修正 | `POST /alerts/{telemetry_id}/work-order` の 501 スタブを async + `HttpClientDep` で差替 |
| `backend/tests/test_orcarouter.py` | 新規 | httpx.MockTransport によるサービス単体テスト（受入条件13件を網羅） |
| `backend/.env.example` | 修正 | `ORCAROUTER_API_KEY` の定義確認（既存定義あり。追加はしない） |

**付随変更（スコープ注記）**: `backend/tests/test_alerts.py` の `TestWorkOrderStub` は、501 スタブ差替により既存 501 アサーションが成立しなくなるため、実装後の挙動（200 + `source=="fallback"`）に合わせて最小更新する。これは受入条件1の必然的帰結であり、テストスイートを Green に保つためにのみ行う（store.py・conftest.py は変更しない）。

**委譲境界（TC-9 / project.md `feasibility:c1`）**: `repair_parts.json` は BE-5 内包の最小フォールバック実装。完全版 OR-3（#14）は後続マージで委譲・強化へ切替可能な境界（ローダー `@lru_cache` + サービスの `build_fallback_work_order()` 単体関数）を保つ。

## 受入条件 → TDD ステップ トレーサビリティ（一次ソース: Issue #13 の13件）

| # | 受入条件 | TDD ステップ |
|---|----------|--------------|
| 1 | `POST /alerts/{id}/work-order` が 501 でなく WorkOrder を返す | S4（ルーター差替）・S5（test_alerts 更新） |
| 2 | 正常応答で部材リスト・見積合計・作業手順・通知文面が WorkOrder に含まれる（source=="llm"） | S1-T1 |
| 3 | レスポンス usage からトークン数（prompt/completion）が取り込まれる | S1-T2 |
| 4 | 実モデル名が WorkOrder.model に反映される | S1-T2 |
| 5 | latency_ms が計測・反映される | S1-T2 |
| 6 | API キー未設定時はフォールバック（source=="fallback"）で 500 にしない | S1-T3 |
| 7 | タイムアウトは1回リトライし、再失敗でフォールバック | S1-T4 |
| 8 | 4xx / パース失敗はリトライせず即フォールバック + 理由ログ | S1-T6 / S1-T7 |
| 9 | フォールバック時も部材リスト・見積合計・通知文面が生成される | S1-T5 / S2（repair_parts.json） |
| 10 | ログ・例外・レスポンスに API キーが含まれない（NFR-4） | S1-T8 |
| 11 | 同一アラート2回目以降はキャッシュを返す（LLM 再呼び出しなし） | S1-T9 |
| 12 | キャッシュヒット時に原価を二重計上しない（FR-6） | S1-T9 |
| 13 | 起票のたびに1行 JSON の構造化ログ（telemetry_id / model / トークン数 / cost_yen / source / latency_ms） | S1-T10 |

**引継ぎ欠落2件（approval-handoff Q1 承認・phase-check-ideation 明記）**: (a) `backend/.env` の gitignore 再確認 → S7、(b) §5.3 カプセル化（Pydantic v2 strict / extra=forbid の契約境界検証）→ S1-T1 / S5。

## TDD 実装ステップ

### 【Step 1】Red — `backend/tests/test_orcarouter.py`（サービス単体テスト新規作成・失敗確認）
先に `httpx.MockTransport` でサービスの公開インターフェース契約を固定する。テストは以下の 10 ケース（受入条件13件 + カプセル化を網羅）:

- [ ] T1 正常応答: source=="llm" で WorkOrder が返り、部材リスト・見積合計（total_estimate_yen == 部材 subtotal 合計）・作業手順・通知文面が非空（受入2・§5.3）
- [ ] T2 FR-6: usage（prompt_tokens / completion_tokens）→ トークン数反映・実モデル名が model に反映・latency_ms > 0（受入3・4・5）
- [ ] T3 API キー未設定（ORCAROUTER_API_KEY を unset）: HTTP 呼び出し0回・source=="fallback"・cost_yen == 0.0・例外を出さない（受入6）
- [ ] T4 タイムアウト: 1回リトライ（呼び出し回数 == 2）→ 再失敗で source=="fallback"（受入7）
- [ ] T5 フォールバック内容: 部材リスト・見積合計・作業手順・通知文面が repair_parts.json 由来で生成される（受入9）
- [ ] T6 5xx は1回リトライ → 再失敗でフォールバック / 4xx はリトライなし（呼び出し回数 == 1）で即フォールバック + 理由ログ（受入8）
- [ ] T7 パース失敗（非 JSON / choices 欠落 / スキーマ不整合 = ValidationError）: リトライなしで即フォールバック（受入8）
- [ ] T8 NFR-4: caplog・WorkOrder・例外メッセージのいずれにも API キー（sk-… 等）が含まれない（受入10）
- [ ] T9 キャッシュ: 同一 telemetry_id で2回目は HTTP 呼び出し0回・原価再計上なし（受入11・12）。`clear_work_order_cache()` で分離
- [ ] T10 構造化ログ: caplog で1行 JSON が `telemetry_id` / `model` / トークン数 / `cost_yen` / `source` / `latency_ms` を包含（受入13）

### 【Step 2】Green — `backend/data/repair_parts.json` + ローダー
- [ ] pipes.json の材質（ductile_iron / cast_iron / pvc / steel）× 口径（75 / 100 / 150 / 200）と整合する最小エントリ + 未知組合わせ用 `default` エントリ
- [ ] エントリ毎に 部材リスト（name / spec / quantity / unit_price_yen / subtotal_yen）・work_steps・required_workers・estimated_duration_hours
- [ ] `@lru_cache(maxsize=1)` のローダー `_load_repair_parts()`（store.py 先例。初回呼び出し時読込・以後キャッシュ、欠損は例外）
- [ ] `build_fallback_work_order(alert, pipe)` 単体関数: 材質×口径マッチ → 未知は default → severity から urgency 導出 → 通知文面（日本語）→ source=="fallback"・cost 0

### 【Step 3】Green — `backend/app/services/orcarouter.py`
- [ ] 公開インターフェース: `async def create_work_order(client: httpx.AsyncClient, telemetry_id: str, alert: AlertDetail, pipe: PipeRecord | None) -> WorkOrder`
- [ ] 環境変数読込（呼び出し時・import 時でなく）: `ORCAROUTER_API_KEY` / `ORCAROUTER_BASE_URL`（既定値あり）/ `ORCAROUTER_MODEL`（既定 "orcarouter"）/ `ORCAROUTER_ENABLED`
- [ ] API キー欠落 or `ORCAROUTER_ENABLED == "false"` → HTTP 呼出なしでフォールバック（受入6）
- [ ] リクエスト組立: prompts 再利用（system / user）・Authorization: Bearer <key>（キーはログに書かない）
- [ ] リトライ分類: timeout / 5xx → 1回リトライ→再失敗フォールバック / 4xx・パース失敗 → リトライなし即フォールバック + 理由ログ
- [ ] 成功: `extract_json_from_response` → `WorkOrder.model_validate`（Pydantic v2 strict / extra=forbid）
- [ ] FR-6: latency_ms = (perf_counter 差分)*1000、usage・model を抽出し `llm_cost.calculate_and_enrich_cost()` に委譲
- [ ] キャッシュ: `_work_order_cache[telemetry_id]` に保存、2回目以降は直接返却（コスト再計上しない）。`clear_work_order_cache()` を公開
- [ ] フォールバック時も構造化ログ（source=="fallback"・cost_yen 0.0）を1行 JSON で出力（受入13）

### 【Step 4】Green — `backend/app/routers/alerts.py`（501 スタブ差替）
- [ ] `create_work_order` を `async def` に変更し `HttpClientDep` を注入
- [ ] 未知 telemetry_id → 404（既存挙動維持）
- [ ] 既知 → AlertDetail（GET /alerts/{id} の組立ロジック再利用）+ `find_pipe_by_hydrant()` → `orcarouter.create_work_order()` 呼出（ルーターは薄く保つ・TC-8）
- [ ] `response_model=WorkOrder`・既存ルート名 `create_work_order` を維持（url_path_for 互換）

### 【Step 5】Red→Green — `backend/tests/test_alerts.py` 更新
- [ ] `TestWorkOrderStub` の 501 アサーションを実装後挙動へ更新: 既知 ID → 200 + source=="fallback"（API キー未設定環境・monkeypatch.delenv で保証）・未知 ID → 404 維持
- [ ] 同一 ID 2回 POST → 2回目も 200（キャッシュ返却）・LLM 再呼なし
- [ ] 全テスト実行で Green 維持（既存 test_alerts 他ケースの回帰なし）

### 【Step 6】Refactor — 静的チェック・構造整理
- [ ] 失敗分類（timeout / 5xx / 4xx / parse）を小さなヘルパーに抽出し可読性向上（挙動不変）
- [ ] ruff 0.16.2: `backend/venv/Scripts/python.exe -m ruff check app`（0 エラー）
- [ ] mypy 2.3.0: `backend/venv/Scripts/python.exe -m mypy app main.py`（0 エラー。`any` 禁止）
- [ ] docstring・コメント日本語化・Issue 参照（BE-5）明記

### 【Step 7】自走確認・検証
- [ ] (a) `backend/.env` が gitignore 対象であることを `git check-ignore` で再確認（引継ぎ欠落2件の1つ目）
- [ ] 全テスト: `python -m pytest`（既存 test_alerts / test_llm_cost / test_prompts 含む Green）
- [ ] カバレッジ: `python -m pytest --cov=app --cov-branch --cov-fail-under=80 --cov-report=term-missing` で 行 + branch 各 80% 以上
- [ ] ルーター統合境界: TestClient で POST /alerts/{id}/work-order（200 / 404 / 2回目キャッシュ）確認

## 計画外（Out of Scope）

- OR-3（#14）完全版フォールバック・部材マスタ拡充（本ステージでは最小版を内包）
- store.py へのワークオーダー永続化・`GET /alerts/{id}/work-order`（取得エンドポイント）追加
- フロントエンド（FE-6 起票モーダル）・CI ワークフロー変更
- 実 Orcarouter API キー・エンドポイントの設定（デモ直前に環境変数で注入。NFR-4 によりコミット禁止）

---

## Review

**Reviewer:** aidlc-architecture-reviewer-agent
**Verdict:** NOT-READY

**日時:** 2026-08-11T23:24:38Z（1パス・敵対的レビュー）

### 検証ツール実測（証拠）

- `pytest --cov=app --cov-branch --cov-fail-under=80`: **177 passed** / TOTAL **99.49%**（行+branch 各80%ゲート通過）。orcarouter.py は行・branch とも100%
- `ruff check app`: All checks passed
- `mypy app main.py`: no issues found in 22 source files
- 敵対的プローブ（実機）: (a) usage に `{"prompt_tokens": "abc"}` を渡すと `create_work_order()` から `ValueError: invalid literal for int() with base 10: 'abc'` が送出（→ ルーターで未捕捉 → 500）。(b) `WorkOrder.model_validate` が未知フィールドをサイレント無視・`quantity: "2"`（文字列）を int に強制変換（strict / extra=forbid 非適用）。(c) `RepairPart` も文字列 quantity を強制変換

### Findings（重大度順）

1. **[Major]** 不正な usage 値で 500 が発生（LLM レスポンス統合境界の未ハードニング）
   - 根拠: `backend/app/services/orcarouter.py` L341-347 は `usage` を「dict である」ことしか検証せず `llm_cost.calculate_and_enrich_cost()` へ委譲。`llm_cost.py` L55-57 の `int(usage["prompt_tokens"])` が非数値（"abc" 等）で `ValueError` を送出。これは orcarouter の try/except（L338）の**外**にあり、ルーターにも catch がないため FastAPI が 500 を返す。実機で `ValueError` 送出を確認済み。
   - 受入条件違反: Issue #13「JSON パース失敗・スキーマ不一致 → フォールバック」に抵触（usage の値不整合は LLM レスポンスのスキーマ不整合）。team.md「**意図的に 500 にしない**」・construction.md「統合境界エラーは回復可能/致命的を区別し表面化」にも反する。テスト未カバー（test_orcarouter.py に不正 usage 値ケースなし。orcarouter.py 行100%でもこのパスは llm_cost 側の未テスト分岐）。
   - 推奨: usage を Pydantic スキーマで検証するか、トークン数の int 変換を try/except で包み、不正ならフォールバック（または概算 estimated）に落とすテストを追加。

2. **[Minor]** 「Pydantic v2 strict / extra=forbid の契約境界」という主張が実態と不一致
   - 根拠: 本プラン L56 と code-summary.md L40 は WorkOrder/RepairPart の strict/extra=forbid 検証を主張するが、`backend/app/schemas/work_order.py` L8-16 に `model_config` がなく、Pydantic v2 既定（lax 強制変換 + extra="ignore"）。実機で未知フィールドがサイレント無視され、文字列 `quantity: "2"` が int に強制変換されることを確認。
   - 影響: LLM 出力境界が「extra 許容 + 非 strict」のまま。T7 の schema_mismatch は必須キー欠落のみ検証し、extra / coercion を検証していない。
   - 推奨: OR-2 の `WorkOrder` / `RepairPart` に `ConfigDict(strict=True, extra="forbid")` を付与するか（他ユニットのファイルのため本ユニットでは変更不可）、少なくとも主張を訂正して緩い境界であることを明記する。

3. **[Minor]** ワークオーダーキャッシュが並行アクセスに対して非アトミック（受入11・12 が並行時に破れる）
   - 根拠: `orcarouter.py` L53 `_work_order_cache` は Lock なし dict。`create_work_order()` のキャッシュ get（L301）と set（L348）の間に await 点（L327 HTTP POST）があるため、同一 telemetry_id への並行 POST が両方ミス → LLM 二重呼び出し・原価二重ログ。store.py は `threading.Lock` で保護しているのにキャッシュは未保護の非対称。
   - 推奨: `asyncio.Lock` で get/set を直列化するか、in-flight デデュープ（同一 ID の先行呼び出しに await させる）を導入。

4. **[Minor]** フォールバック結果も無期限キャッシュされ、一時的失敗が永続化する
   - 根拠: `orcarouter.py` `_fallback()`（L279-282）がフォールバック WorkOrder をキャッシュに保存。初回 POST が一時的障害（キー未設定・timeout・5xx）だった場合、以降その telemetry_id は永久に fallback を返し、LLM 回復後も再試行されない。Issue #13 の文言（「2回目以降はキャッシュを返す」）には合致するが、デモで LLM 出力を一度も見せられない状態が固定化されうる。
   - 推奨: キャッシュ TTL、LLM 成功時のみキャッシュ、またはフォールバック結果のキャッシュ除外を設計判断として明記する。

5. **[Minor]** フォールバック安全網自身がマスタの部分破損で 500 になりうる
   - 根拠: `build_fallback_work_order()`（L130-141）が `entry["parts"]` / `entry["work_steps"]` 等を直接参照。`_load_repair_parts()`（L86-92）は entries/default が「dict である」ことしか検証せず、エントリ内の必須キー欠落を検証しない。`{"parts": []}` 等の部分形状エントリで `KeyError` → フォールバック経路で 500。「失敗しない安全網」の前提が破れる。
   - 推奨: エントリ形状を Pydantic で検証、または必須キーを `entry.get` + 既定値で安全に補完。

6. **[Info]** test_alerts.py のルーター級キャッシュテストがキャッシュを実証していない
   - 根拠: `test_alerts.py` L217-227 `test_same_id_second_post_returns_cached` は 2 回のレスポンス内容一致のみ検証。API キー未設定（フォールバック）環境ではキャッシュ無しでも同一内容を返すため、このテストはキャッシュ有無を検証できない（実証はサービス級 T9 の `handler.calls == 1` が担う）。
   - 推奨: ルーター級でもハンドラ呼び出し回数を検証するか、「キャッシュ実証は T9 が担う」と明記。

7. **[Info]** `.env.example` に ORCAROUTER_BASE_URL / MODEL / ENABLED が未記載
   - 根拠: `.env.example` は ORCAROUTER_API_KEY のみ（L1）。コードは BASE_URL（L312）/ MODEL（L69）/ ENABLED（L306）を環境変数で読み、既定値を持つ。引継ぎ事項（code-summary.md L68）には記載済みだが、`.env.example` にも追記するとデモセットアップの可視性が上がる。
   - 推奨: 任意（3項目のコメント付き追記）。

### 検証済み受入条件（Issue #13 の13件）

| # | 受入条件 | 判定 | 根拠 |
|---|----------|------|------|
| 1 | 501 でなく WorkOrder を返す | OK | test_alerts `TestWorkOrder`（200 + source=="fallback"）、未知 ID は 404 維持 |
| 2 | 部材・見積合計・手順・通知文面（source=="llm"） | OK | T1（total==subtotal 合計・非空） |
| 3 | usage からトークン数が取り込まれる | OK | T2（prompt=800 / completion=200） |
| 4 | 実モデル名が model に反映 | OK | T2（"orcarouter-pro-2026"） |
| 5 | latency_ms が計測・反映 | OK | T2（`max(1, ...)` で常に >0） |
| 6 | API キー未設定でフォールバック・500 にしない | OK | T3（HTTP 0 回・cost 0）・enabled=false テスト |
| 7 | タイムアウト1回リトライ→再失敗フォールバック | OK | T4（呼出 2 回） |
| 8 | 4xx / パース失敗は即フォールバック + 理由ログ | OK | T6（401=1回・"401" ログ）・T7（6系統・"応答パース失敗"） |
| 9 | フォールバック時も部材・見積・文面を生成 | OK | T5 + build_fallback_work_order 単体 |
| 10 | ログ・例外・レスポンスに API キーを含めない | OK | T8（caplog / model_dump_json 非出現・Authorization ヘッダ使用確認） |
| 11 | 同一アラート2回目はキャッシュ（LLM 再呼なし） | OK（直列時） | T9（2回目 HTTP 0 回）。並行時は保証されず（Finding #3） |
| 12 | キャッシュヒットで原価を二重計上しない | OK（直列時） | T9（llm_cost_measured 1 回）。並行時は保証されず（Finding #3） |
| 13 | 毎回1行 JSON 構造化ログ（必須キー） | OK | T10（成功 `llm_cost_measured` / フォールバック `work_order_fallback`） |

### サマリ

受入条件 13 件は直列シナリオで全てテスト実証され、カバレッジ・ruff・mypy もゲート通過。ただし LLM レスポンスの **usage 値が不正な場合に未捕捉の ValueError が 500 へ化ける**（Finding #1・実機確認済み）のは、Issue #13 の「パース失敗はフォールバック」と team.md の「意図的に 500 にしない」に直接反する検証済み Major 欠陥であり、NOT-READY とする。加えて strict/extra=forbid 契約の主張ズレ、キャッシュの並行非安全性・フォールバック永続化など Minor 5 件が残る。

---

## Review（iteration 2）

**Reviewer:** aidlc-architecture-reviewer-agent
**Verdict:** READY
**日時:** 2026-08-11T23:47:14Z（1パス・敵対的レビュー。iteration 1 の指摘7件の修正検証 + 残存欠陥探索）

### 前回指摘の対応検証（#1〜#7）

| # | 重大度 | 判定 | 根拠 |
|---|--------|------|------|
| 1 | Major | **解決** | `_UsageTokens`（Pydantic v2・非負 int・extra ignore）を `_parse_llm_response()` に追加。`llm_cost` の `int()` 変換に不正値が届く経路は消滅。実機プローブ（httpx.MockTransport）で非数値 "abc" / 非数値 completion / prompt 欠落 / completion 欠落 / 負値 -1 / 非 dict 文字列 / float 小数 800.5 の**全て**が例外送出なしで `source=="fallback"`（`test_invalid_usage_falls_back_without_500` 6 ケースと一致）。2xx 成功パスの try/except `(TypeError, ValueError, ValidationError)` がフォールバックへ振り分け。 |
| 2 | Minor | **解決（要注記）** | code-summary.md L25 / L40 は再利用契約（lax 強制変換 + extra ignore）と実態一致に訂正済み。ただし本プラン本文 L21（前提表）・L56（引継ぎ欠落）に「Pydantic v2 strict / extra=forbid」の旧主張が残存。code-summary が権威レコードであり実害なしのため Info 相当（#2 の検証欄で記録）。 |
| 3 | Minor | **解決** | `_work_order_lock`（モジュール `asyncio.Lock`）で get/生成/set を直列化。`test_concurrent_same_id_calls_llm_once` がハンドラ遅延で割り込みを発生させ `handler.calls == 1` を検証（Green）。デッドロックなし（HTTP await 中に再入する経路なし）。イベントループ跨ぎ: Python 3.14 実測で非競合 acquire はループへ束縛せず発火しない（188 件 Green）。競合 acquire が複数ループを跨ぐ将来パターンでは Python <3.14 で `RuntimeError: is bound to a different event loop` が発火しうる（Info 注記）。 |
| 4 | Minor | **解決（設計判断）** | フォールバック結果は非キャッシュ化（LLM 成功時のみ保存）。`test_fallback_not_cached_retries_llm_on_next_call`（503 継続で計4回呼出）で検証。受入11「2回目はキャッシュ（LLM を再度呼ばない）」は LLM 成功時キャッシュ解釈で整合 — フォールバック時も LLM 呼出は 0 回のため「LLM を再度呼ばない」は両分岐で成立。設計判断は code-summary に明記。 |
| 5 | Minor | **部分解決 → 新規 Minor #1** | 必須キー欠落は `_validate_entry_shape()` で fail-fast（`test_entry_missing_required_key_raises_type_error` Green）。ただし**キーの存在のみ検証で値の型を検証しない**ため、`"parts": "oops"` / part アイテム必須フィールド欠落 / `"work_steps": "oops"` 等はローダーを通過し `build_fallback_work_order()` の `RepairPart/WorkOrder.model_validate` が ValidationError → `_fallback()` は try/except 外 → 500（実機確認）。詳しくは新規 Finding 1。 |
| 6 | Info | **解決** | `test_same_id_second_post_returns_cached` → `test_same_id_second_post_returns_same_content` に改名、コメントで「キャッシュ実証はサービス級 T9 が担う」と明記。 |
| 7 | Info | **解決** | `.env.example` に `ORCAROUTER_BASE_URL` / `ORCAROUTER_MODEL` / `ORCAROUTER_ENABLED` をコメント付きで追記（実キーなし）。 |

### 新規 Findings（重大度順）

1. **[Minor]** `_validate_entry_shape()` が値の型を検証しないため、フォールバック安全網が値型破損マスタで 500 に化ける（Minor #5 の部分残存）。
   - 根拠: `orcarouter.py` L108-114 の `_validate_entry_shape` は必須キーの「存在」のみ判定。実機プローブで `{"parts": "oops"}` / `{"parts": [{"name": "x"}]}` / `{"work_steps": "oops"}` のエントリが「LOAD OK（形状チェック通過）」→ `build_fallback_work_order()` で `ValidationError` 送出 → 公開経路 `create_work_order()`（API キー無し=フォールバック分岐）でも `RAISED ValidationError` を確認（ルーターで未捕捉 → 500）。元指摘 #5 の blast radius（「失敗しない安全網」の意図）内。
   - 重大度の判断: トリガは静的・自前管理の `repair_parts.json` の破損コミットのみで、LLM 応答や実行時データでは発火しない。元指摘が Minor だったことと同類であるため Minor。デモでは実質リスクなし。
   - 推奨: `_validate_entry_shape` で `parts: list` / `work_steps: list` 等の型検証を追加するか、`_fallback()` / `build_fallback_work_order()` を try/except で包みフォールバック生成失敗を別系統（例外ログ + 既定 WorkOrder）に閉じ込める。

2. **[Minor]** 陳腐化した検証スクリプト `backend/scripts/check_alerts.py` が旧 501 スタブ挙動をアサート。
   - 根拠: `check_alerts.py` L222-227 `case_9_work_order_501` は「実在 ID の work-order 期待 501」をアサート。BE-5 で 501 → 200 + `source=="fallback"` に変わり、このスクリプトは実行時に誤失敗する。プラン L34 の付随変更は `test_alerts.py` のみ列挙し本スクリプトを失念。CI（`.github/workflows/ci.yml`）は `check_telemetry.py` / `check_kpi.py` のみ実行するため CI は壊れない（dev 専用・サーバー起動前提の手動スクリプトの陳腐化）。
   - 推奨: `case_9` を 200 + fallback アサートへ更新するか、BE-5 完了済みとして削除/スキップ化し、code-summary の引継ぎ事項に明記。

3. **[Info]** 不正 `ORCAROUTER_BASE_URL` で `client.post` が `httpx.InvalidURL`（`TransportError` のサブクラスでない）を送出し 500。
   - 根拠: 実機プローブで `not-a-url` / 空文字 / `://bad` / `http://` の全てが `ValueError: unknown url type` を送出（`_post_with_retry` の `except httpx.TransportError` が捕捉しない → ルーターへ伝播）。team.md「算出不能はサイレントな既定値で誤魔化さず例外を明確に上げる」に照らせば、運用設定ミスへの fail-fast は一貫的で現在の挙動も「誤魔化さない」に整合する。どちらの解釈（設定ミスは 500 で露呈 vs フォールバックへ落とす）を採るか設計判断として明記することを推奨（実害は設定ミス時のみ）。

4. **[Info]** `_UsageTokens` は既定 lax のため bool `True` → int `1` に強制変換され `source=="llm"`（実機確認）。`800.0` → `800`。
   - 根拠: 実機プローブで `{"prompt_tokens": True, "completion_tokens": 200}` が `source=llm / prompt_tokens=1`。code-summary L28 の「非数値は遮断」は bool について厳密でないが、500 化はしないため Major #1 の解決は有効。実 LLM は int を返すため実害なし。
   - 推奨: 完全厳格化するなら `_UsageTokens` に `ConfigDict(strict=True)` を付与（任意）。

5. **[Info]** モジュールレベル `asyncio.Lock` のイベントループ跨ぎは、現行テストパターンでは発火しないが、Python <3.14 では競合 acquire を別ループで行うテスト追加時に `RuntimeError: is bound to a different event loop` が発火しうる。本番（uvicorn 単一ループ）は無問題。code-summary の「Python 3.14 で複数イベントループ跨ぎの安全性確認」は現行パターンに限定して正しい。

6. **[Info]** `repair_parts.json` の実配置（`backend/app/data/repair_parts.json`）と、プラン表 L28・code-summary L13 の表記（`backend/data/repair_parts.json`）が不一致。`backend/data/` ディレクトリは存在しない。コードは `Path(__file__).parent.parent / "data"` で自己解決し実行は完全に整合（`app/data/` は hydrants.json / pipes.json と同居の既存マスタ配置）。表記のみの誤りでコード変更は不要 — code-summary の表記を実体に合わせる修正を推奨。

### 検証ツール実測

- `pytest --cov=app --cov-branch --cov-fail-under=80`: **188 passed** / TOTAL **99.52%**（行 99%・branch 99%、ゲート通過）。`orcarouter.py` は行 100% / branch 100%。
- `ruff check app`: All checks passed。
- `mypy app main.py`: Success, no issues found in 22 source files。
- 実機プローブ（httpx.MockTransport・`create_work_order()` 公開経路）:
  - 不正 usage 6 種 + 追加 3 種（bool / float 800.5 / float 800.0）: 非数値・キー欠落・負値・非 dict・float 小数は**例外なしで `source=="fallback"`**。bool → 1・float 整数 → int に lax 変換され `source=="llm"`（500 なし）。
  - 破損マスタ値型（parts 文字列 / part 必須欠落 / work_steps 文字列）: ローダー通過 → `build_fallback_work_order` / 公開経路で `ValidationError` 送出（Finding 1）。
  - 不正 BASE_URL 4 種: `ValueError: unknown url type` 送出（Finding 3）。
  - `asyncio.Lock` の複数ループ跨ぎ: Python 3.14.5 で非競合 acquire は発火なし（プローブ + 188 件 Green）。

### 検証済み受入条件（Issue #13 の13件）

| # | 受入条件 | 判定 | 根拠 |
|---|----------|------|------|
| 1 | 有効キーで POST が WorkOrder を返し source=="llm" | OK | T1（service 級 source llm・呼出1回） |
| 2 | 部材・見積合計・手順・通知文面が日本語で埋まる | OK | T1（total==subtotal 合計・非空・日本語マスタ/フィクスチャ） |
| 3 | usage→トークン数・実モデル名・latency_ms（FR-6） | OK | T2（800/200・"orcarouter-pro-2026"・>0） |
| 4 | 毎回1行 JSON 構造化ログ（必須6キー） | OK | T10 成功 `llm_cost_measured` / フォールバック `work_order_fallback` |
| 5 | API キー未設定で 500 にせず fallback | OK | T3（HTTP 0 回・cost 0） |
| 6 | タイムアウト1回リトライ→再失敗フォールバック | OK | T4（呼出2回） |
| 7 | 4xx はリトライせず即フォールバック | OK | T6（401=1回・"401" ログ） |
| 8 | ログ・例外・レスポンスに API キーを含めない（NFR-4） | OK | T8（caplog / model_dump_json 非出現）+ コード全文読解（キーは Authorization ヘッダのみ） |
| 9 | 同一アラート2回目はキャッシュ（LLM 再呼なし） | OK | T9（2回目 HTTP 0 回）。フォールバック非キャッシュは設計判断として文書化（#4） |
| 10 | キャッシュヒットで原価二重計上しない（FR-6） | OK | T9（`llm_cost_measured` ログ 1 回のみ） |
| 11 | `backend/.env` がコミットされていない | OK | `git check-ignore -v backend/.env` → `.gitignore:11:.env` |
| 12 | LLM 呼出ロジックが orcarouter.py 以外に散らない | OK | grep で API キー読込・`chat/completions` URL 組立は orcarouter.py のみ。ルーターは委譲のみ |
| 13 | カバレッジ 80% 以上 | OK | 行 + branch 各 80% ゲート通過（TOTAL 99.52%） |

### サマリ

iteration 1 でブロック要因だった Major #1（不正 usage → 未捕捉 ValueError → 500）は、`_UsageTokens` 検証 + 2xx 成功パス try/except により実機プローブ・テスト双方で**完全に塞がった**ことを確認。Minor #3（並行キャッシュ）・#4（フォールバック永続化）もロック/非キャッシュ化と実証テストで解決し、受入条件13件は全て満たす。残るのは、フォールバック安全網の値型検証欠落（Minor・元 #5 の部分残存）と陳腐化した dev スクリプト `check_alerts.py`（Minor・CI 外）の2件の Minor と、Info 数件（BASE_URL 設定ミス時の 500、usage lax 補正、Lock のループ跨ぎ限界、配置パス表記ズレ、プラン本文の旧 strict 主張）である。いずれもデモスコープの実行時リスクを構成せず、開発者がこの成果物から推測なしに実装可能な状態と判断し **READY** とする。
