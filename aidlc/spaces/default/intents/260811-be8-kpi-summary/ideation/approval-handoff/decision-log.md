# Decision Log — BE-8 KPI「推定削減コスト」算定ロジックとサマリAPI

イデエーション段階（intent-capture・approval-handoff）で記録された決定の一覧。各決定は質問ファイルのソースレジスタ（[Q1]〜[Q4]）に対応する。

## 1. スコープ境界（intent-capture Q1）

- 製品境界は「`GET /api/v1/kpi/summary` で算定根拠のある推定削減コストと実データ由来の内訳カウントを返す」。
- 対象はバックエンド5ファイル（`app/services/kpi.py`・`app/schemas/kpi.py`・`app/routers/kpi.py`・`tests/test_kpi.py` 新規、`main.py` へのルーター登録）。フロント（`page.tsx` の `MOCK_KPI_DATA`）は変更しない。
- 8/15デモ完了を最優先とする。
- 出典: `intent-capture/intent-capture-questions.md` Q1（`[Answer]: A`）

## 2. 型とデータ源（intent-capture Q2）

- 深刻度は既存 `app.schemas.telemetry.SeverityLevel`（Literal[0,1,2,3]）を再利用する。
- アラートデータ源はインメモリストア（`get_store().list_alerts()`）。
- BE-3未実装のため、実データは `scripts/simulate_sensor.py` 投入分（解析済みテレメトリ）を使用する。
- 出典: `intent-capture/intent-capture-questions.md` Q2（`[Answer]: A`）

## 3. レスポンス仕様（intent-capture Q3）

- レスポンスは5項目（`total_sensors` / `level1_count` / `level2_count` / `level3_count` / `estimated_cost_saved_yen`）+ `is_estimate`・`assumption_doc`。
- `today_detections` は今回の対象外とする。
- 出典: `intent-capture/intent-capture-questions.md` Q3（`[Answer]: A`）

## 4. 空ストア時の挙動（intent-capture Q4）

- 空ストアでも 200 OK で全項目0を返す（500にしない）。
- `total_sensors` は `hydrants.json` の実件数（現状10件）と一致させる。
- デモシナリオでの合計が 2,048,400 円になることを確認する。pytestカバレッジは80%以上。
- 出典: `intent-capture/intent-capture-questions.md` Q4（`[Answer]: A`）

## 5. ステークホルダー合意（approval-handoff Q1）

- 関係者（実装担当＝ユーザー、デモ参加者）は意図とスコープに合意。
- 出典: `approval-handoff/approval-handoff-questions.md` Q1（`[Answer]: A. 合意している`）

## 6. リスク認識・対策（approval-handoff Q2）

- BE-3未実装・仮説定数ベースの試算値・フロント連携時の型不一致の主要リスクと対策を認識し合意。
- 出典: `approval-handoff/approval-handoff-questions.md` Q2（`[Answer]: A. 認識・対策に合意`）

## 7. 予算・リソースコミットメント（approval-handoff Q3）

- MVP実装（バックエンド5ファイル）にリソースを投入し、8/15デモ完了を目指すことに合意。
- 出典: `approval-handoff/approval-handoff-questions.md` Q3（`[Answer]: A. 合意する`）
