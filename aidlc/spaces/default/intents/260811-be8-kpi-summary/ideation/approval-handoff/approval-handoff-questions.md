# Initiative Approval & Handoff Questions — BE-8 KPI「推定削減コスト」算定ロジックとサマリAPI

## Sources

- [desc] Initial description: "GitHub内のISSUESを確認し、ISSUE#18「BE-8: KPI「推定削減コスト」の算定ロジックとサマリAPIの実装」を実装してください。なお、BE-3は未実装であることに留意してください。"
- [scope] Workflow-selected scope: `be8-kpi-summary`.

## Q1. ステークホルダー合意（意図とスコープ）

インテントステートメントで定義した製品境界は「`GET /api/v1/kpi/summary` で算定根拠のある推定削減コストと実データ由来の内訳カウントを返す（バックエンド5ファイル、フロント変更なし、8/15デモ完了を最優先）」です。関係者（実装担当＝ユーザー、デモ参加者）はこの意図とスコープに合意していますか？

- A. 合意している — 今回のMVPスコープ（`be8-kpi-summary`）で進める
- B. 合意しない — スコープを見直す必要がある（範囲は自由記述で指定）
- X. Other (please specify)

[Answer]: A. 合意している

## Q2. 重要なリスクと対策の認識

本イニシアティブの主要リスクと対策は以下です。これを認識し、対策を講じることで合意しますか？

- **BE-3 未実装**（FFT解析による実漏水検知なし）→ 実データ源は `scripts/simulate_sensor.py` 投入分（解析済みテレメトリ）を使用し、既存 `SeverityLevel`（Literal[0,1,2,3]）で集計する
- **仮説定数ベースの試算値**（デモ内訳合計 2,048,400 円は `docs/business-model.md` §3 の仮説定数に基づく）→ `is_estimate`・`assumption_doc` で試算値である旨をAPIレスポンスで明示する
- **フロント連携時の型不一致**（API snake_case 5項目 vs フロント `KpiData` の camelCase・`today_detections` 有無）→ フロント変更はスコープ外とし、実API接続（FE-7 等）は後続ストーリーで対応する

- A. 認識・対策に合意する
- B. 追加のリスクがある（自由記述で追記）
- X. Other (please specify)

[Answer]: A. 認識・対策に合意

## Q3. 予算・リソースコミットメント

8/15 デモ完了を最優先とし、本イニシアティブの実装（バックエンド5ファイル: `app/services/kpi.py`・`app/schemas/kpi.py`・`app/routers/kpi.py`・`tests/test_kpi.py` 新規、`main.py` へのルーター登録）にリソースを投入することで合意しますか？

- A. 合意する — MVP 実装にリソースを投入し 8/15 デモ完了を目指す
- B. リソースに制約がある（自由記述で指定）
- X. Other (please specify)

[Answer]: A. 合意する

## Consolidated Summary Confirmation

- Looks correct
- Request changes

[Answer]: Looks correct
