<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations

- 2026-08-12T00:00:00Z — `{unit-name}` を intent slug `be5-orcarouter` に解決して記録パスを `construction/be5-orcarouter/code-generation/` に決定（unit-of-work.md は `consumes_absent` expected:false。be4-ledger / be8-kpi-summary の先例を踏襲。project.md `code-generation:c1` / `asc-c1` と整合）。
- 2026-08-12T00:00:00Z — ジャンプ（--stage code-generation）により Inception フェーズの設計成果物（requirements-analysis / application-design 等）が存在しないため、本ステージのスコープは一次ソース（GitHub Issue #13 の受入条件13件・実装方針・検証方法）とリポジトリ実態（OR-1 HttpClientDep / OR-2 prompts・WorkOrder / OR-4 llm_cost 実装済み）から編成する。欠落成果物の内容は創作しない。
- 2026-08-12T00:00:00Z — キャッシュの実装場所を `services/orcarouter.py` 内のモジュールレベル dict（`_work_order_cache` + `clear_work_order_cache()`）とし、store.py は変更しない。Issue の「結果をストアへ保存」はスコープ外ファイル（store.py）を対象としないため、受入条件11/12（2回目以降キャッシュ返却・原価二重計上なし）を満たす最小実装としてサービス層に内包する（OC-1 デモ最優先・TC-1 対象ファイル限定と整合）。
- 2026-08-12T00:00:00Z — アーキテクチャレビューは 2 パスで READY。iteration 1 NOT-READY（Major #1: 不正 usage 値で未捕捉 ValueError → 500）→ リード修正 → iteration 2 READY。レビューアは LLM レスポンス統合境界（usage 値）の実機プローブまで実施し、`WorkOrder.model_validate` の lax/extra ignore 挙動も検証。NOT-READY の核心は「テストの行カバレッジ 100% でも llm_cost 側の未テスト分岐（int() 変換）が 500 に化ける」こと。Pydantic 契約の主張は実態（lax + extra ignore の再利用契約）と一致させる。

## Deviations

- 2026-08-12T00:00:00Z — 対象ファイルは scope-document の5ファイル（repair_parts.json / orcarouter.py / alerts.py / test_orcarouter.py / .env.example）だが、alerts.py の 501 スタブ差替に伴い `backend/tests/test_alerts.py` の `TestWorkOrderStub`（既存 501 アサーション）が成立しなくなるため、テストスイートを Green に保つ最小更新を付随変更としてプランに明記した（受入条件1の必然的帰結）。store.py・conftest.py は変更しない。
- 2026-08-12T00:00:00Z — `repair_parts.json` の実配置は `backend/app/data/`（orcarouter.py が `Path(__file__).parent.parent / "data"` で自己解決）。プラン表記（`backend/data/`）と表記ズレがあるがコードは実行時整合のため変更不要。コードサマリへは実パスで記載する。
- 2026-08-12T00:00:00Z — `backend/scripts/check_alerts.py` の `case_9_work_order_501` が旧 501 スタブをアサートする陳腐化（BE-5 付随更新漏れ・iteration 2 レビュー Minor #2）。CI は check_telemetry.py / check_kpi.py のみのため CI は壊れないが、dev スクリプトの整合を引継ぎ事項として明記する（project.md asc-c3: スコープ外は承認ゲート確認事項に明記・無断拡大しない）。

## Tradeoffs

- 2026-08-12T00:00:00Z — ワークオーダーキャッシュを「store.py に保存する（Issue 文言どおり・アーキテクチャ上は store が正）」か「orcarouter.py のモジュール内キャッシュ（スコープ外ファイルを触らない・最小）」か比較。TC-1（対象ファイル限定）と OC-1（最もシンプルな実装）を優先し、後者を選択。ローテータは薄く、キャッシュの存在はサービス層に閉じる（TC-8 と整合）。OR-3（#14）マージ時にストア保存へ委譲可能。
- 2026-08-12T00:00:00Z — `.env.example` への追記は scope-document の決定（ORCAROUTER_API_KEY のみ）を優先する。Issue 実装方針は BASE_URL / MODEL / ENABLED も列挙するが、受入条件13件はいずれも .env.example の内容を検証せず、コードは os.environ から既定値つきで読むため、既存の ORCAROUTER_API_KEY 定義を確認して終了とする（コード既定値・ドキュメントで補完）。
- 2026-08-12T00:00:00Z — `practices-discovery:c4` の学習（aidlc エージェントへのディスパッチがモデル解決で 503）は **aidlc-developer-agent では再現しなかった**。今回のディスパッチは成功し（69 tool_uses・約13分）、モデル解決キャッシュの問題は対象エージェントや時期により変動しうる。一般用途エージェントへのフォールバック（c4 のワークアラウンド）は今後も保険として認識しつつ、まず名前付きエージェントへの直接ディスパッチを試す方針が有効。
- 2026-08-12T00:00:00Z — フォールバック結果はワークオーダーキャッシュに**保存しない**方式を採用（Minor #4）。一時的障害（キー未設定・timeout・5xx）が telemetry_id に永続化して LLM 出力を一度も見せられなくなるのを防ぎ、デモで LLM 出力を実演できることを優先。受入条件11の「2回目以降はキャッシュ」は LLM 成功時生成に適用する解釈とした（フォールバック時も HTTP 呼出 0 回のため「LLM を再度呼ばない」は両分岐で成立）。
- 2026-08-12T00:00:00Z — キャッシュの並行安全性は `asyncio.Lock` で生成処理全体を直列化して担保（Minor #3）。get/検証/set を await を跨がないクリティカル区間に収める精密な構成ではなく、シンプルに生成全体をロックで囲む構成（異なる telemetry_id も直列化されるが、単一ワーカー・同時操作が稀なデモスコープでは許容）。store.py の threading.Lock と非対称だがサービス層に閉じた判断。

## Open questions

- 2026-08-12T00:00:00Z — なし（None.）。一次ソース（Issue #13）13件 + 引継ぎ欠落2件（.env gitignore 再確認・Pydantic カプセル化）をプランのトレーサビリティに明記した。実 API キー・エンドポイントはデモ直前に環境変数で注入する（R-1 引継ぎ）。

## Learnings

<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
