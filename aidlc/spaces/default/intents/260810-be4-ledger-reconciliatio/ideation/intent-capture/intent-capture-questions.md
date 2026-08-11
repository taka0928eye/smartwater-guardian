# Intent Capture Questions — BE-4 配管台帳照合サービス

## Sources

- [desc] Initial description: "GitHub Issue「BE-4: 配管台帳照合サービス（ledger.py）」を実装してください。FR-3 の前段で、センサー位置（消火栓）から該当する水道管路（材質・口径・布設年等）を引き当て、BE-5（補修部材選定）に必要な入力を揃える。対象ファイル: backend/app/data/pipes.json（新規: 配管台帳10路線）、backend/app/schemas/pipe.py（新規: PipeRecord Pydantic v2 スキーマ）、backend/app/services/ledger.py（新規: 照合ロジック & キャッシュ & ヘルパー）、backend/scripts/check_ledger.py（新規: 動作検証スクリプト）。詳細は以下のIssue内容を参照。"
- [scope] Workflow-selected scope: `be4-ledger-reconciliation`.

## Q1. 製品境界（スコープ）の確認

GitHub Issue の記載に基づき、このワークフローは **`be4-ledger-reconciliation`** スコープで進みます。対象は配管台帳データ（`pipes.json`）・スキーマ（`pipe.py`）・照合サービス（`ledger.py`）・検証スクリプト（`check_ledger.py`）の4ファイル新規作成と、`GET /api/v1/alerts/{id}` への配管情報（`pipe_info`）配線です。この製品境界は想定どおりですか？

- A. はい、この境界で正しい（4ファイル + alerts API への配線）
- B. いいえ、配管台帳サービス本体（ledger.py とデータ定義）に絞りたい
- C. いいえ、もっと広げたい（範囲は自由記述で指定）
- D. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Q2. 主要ステークホルダーと価値


このサービスの主な消費者は誰で、どんな痛みを解決しますか？

- A. BE-5（補修部材選定・見積自動起票）が直接の消費者。配管の材質・口径・布設年を渡して部材選定の入力を揃える
- B. 監視UIの利用者（アラート詳細画面で対象管路の情報を見たい）
- C. その両方（BE-5 と監視UIの両方に配管情報を提供）
- D. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: C

## Q3. 成功指標

Issue の受け入れ条件（全10件の消火栓が配管に解決される、未知 ID は None、最近傍検索、例外時は明示的エラー、alerts 連携、キャッシュ、検証スクリプト成功）以外に、デモで測りたい成功指標はありますか？

- A. 受け入れ条件の通過で十分（8/15 デモ完了を最優先）
- B. hydrants.json との整合性チェック（全消火栓が配管に紐付く）を明示的に確認する
- C. 照合の応答性（リクエストごとの再読込がないこと）を確認する
- D. まだ特定されていない（None / Not identified）
- X. Other (please specify)

[Answer]: A

## Q4. BE-6（alerts API）への配線タイミング

Issue には「`GET /api/v1/alerts/{id}` のレスポンスに配管情報を載せられるように連携すること」と明記されています。`app/routers/alerts.py` には既に `pipe_info=None` のプレースホルダと `PipeInfo` スキーマがあります。配線はどこで実施しますか？

- A. この BE-4 タスク内で実施する（Issue の指示どおり、ledger.py 実装後に alerts.py を接続）
- B. BE-6 側のタスクで実施する（今回は ledger.py まで）
- C. まだ未定（Not decided）
- X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- スコープは `be4-ledger-reconciliation`（4ファイル新規作成 + alerts API への配管情報配線）で正しい。
- 主な消費者は BE-5 と監視UIの両方。配管の材質・口径・布設年・経過年数を提供して、部材選定入力とアラート詳細表示の両方を支える。
- 成功指標は Issue の受け入れ条件の通過で十分（8/15 デモ完了を最優先）。
- BE-6 配線はこの BE-4 タスク内で実施する（ledger.py 実装後に alerts.py を接続）。

- Looks correct
- Request changes

[Answer]: Looks correct

