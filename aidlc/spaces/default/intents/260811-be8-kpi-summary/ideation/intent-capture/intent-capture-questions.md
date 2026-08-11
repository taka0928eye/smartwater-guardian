# Intent Capture Questions — BE-8 KPI「推定削減コスト」算定ロジックとサマリAPI

## Sources

- [desc] Initial description: "GitHub内のISSUESを確認し、ISSUE#18「BE-8: KPI「推定削減コスト」の算定ロジックとサマリAPIの実装」を実装してください。なお、BE-3は未実装であることに留意してください。"
- [scope] Workflow-selected scope: `be8-kpi-summary`.

## Q1. 製品境界（スコープ）の確認

このワークフローは **`be8-kpi-summary`** スコープで進みます。GitHub Issue #18 の主旨は「ダッシュボードKPI『推定削減コスト』は現状フロントにハードコード（`estimatedCostSavedYen: 1_420_000`）されており算定根拠がないため、`docs/business-model.md` §3 の算定式のみを根拠にバックエンドで算出し、`GET /api/v1/kpi/summary` で返す」ことです。この製品境界は想定どおりですか？

- A. はい、`be8-kpi-summary` スコープで正しい — 対象はバックエンド5ファイル（`app/services/kpi.py`・`app/schemas/kpi.py`・`app/routers/kpi.py`・`tests/test_kpi.py` の新規、`main.py` へのルーター登録）。フロント（`page.tsx` の `MOCK_KPI_DATA`）は変更しない
- B. いいえ、フロントの `MOCK_KPI_DATA` を実API置き換え（`page.tsx` から `/api/v1/kpi/summary` を呼ぶ）まで含めたい
- C. いいえ、もっと狭める・変えたい（範囲は自由記述で指定）
- D. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Q2. 深刻度レベル（SeverityLevel）の型ソースとアラートデータ源

BE-3（`app/services/audio.py` の FFT 解析）は未実装のため、`AnalysisResult.severity_level` に使う型は既存の `app/schemas/telemetry.py` に `SeverityLevel = Literal[0, 1, 2, 3]` として定義済みです。KPI の集計入力となるアラート実データはインメモリストア（BE-6 `get_store()`）が保持し、`scripts/simulate_sensor.py` 経由で投入されます。型ソースとデータ源はこれで確定しますか？

- A. 既存の `app.schemas.telemetry.SeverityLevel` を再利用し、アラートデータ源はインメモリストア（`get_store().list_alerts()`）の解析済みテレメトリとする（BE-3 未実装のため、実データは `scripts/simulate_sensor.py` 投入分）
- B. 深刻度の型は KPI 用に新規定義する
- C. アラートデータ源はストアではなく別手段（例: hydrants.json のみ・固定データ）
- D. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Q3. KpiSummary レスポンスの項目（5項目）の内訳

Issue の受け入れ条件は「`GET /api/v1/kpi/summary` が 200 と5項目 + `is_estimate` を返す」とあります。フロントの現行 `KpiData` は `totalSensors` / `level3Count` / `level2Count` / `todayDetections` / `estimatedCostSavedYen` の5項目です。API が返す5項目はどれにしますか？

- A. `total_sensors` / `level1_count` / `level2_count` / `level3_count` / `estimated_cost_saved_yen` + `is_estimate`・`assumption_doc`（内訳カウントはアラート実データ由来。`today_detections` は今回の対象外）
- B. `total_sensors` / `estimated_cost_saved_yen` のみ（内訳カウントは不要）
- C. フロント `KpiData` に合わせて `today_detections` も含める
- D. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Q4. 空ストア（アラート0件）時の挙動と成功指標

Issue の指示は「ストアが空でも 200 と全項目0を返す（500 にしない）」です。`total_sensors` は `hydrants.json` の実件数（現状10件）から算出します。この挙動と、成功指標は受け入れ条件の通過（デモ内訳で合計 2,048,400 円・カバレッジ80%以上）で十分、という判断で確定しますか？

- A. 空ストアでも 200 OK で全項目0・`total_sensors` は実件数（10件）を返す。成功指標は Issue 受け入れ条件の通過で十分（8/15 デモ完了を最優先）
- B. 空ストア時は `total_sensors` も 0 を返す
- C. 空ストア時はエラー（404/500）を返す
- D. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- スコープは `be8-kpi-summary` で正しい。対象はバックエンド5ファイル（`app/services/kpi.py`・`app/schemas/kpi.py`・`app/routers/kpi.py`・`tests/test_kpi.py` 新規、`main.py` へのルーター登録）。フロント（`page.tsx` の `MOCK_KPI_DATA`）は変更しない。 [Q1]
- 深刻度の型は既存 `app.schemas.telemetry.SeverityLevel`（Literal[0,1,2,3]）を再利用し、アラートデータ源はインメモリストア（`get_store().list_alerts()`）の解析済みテレメトリ。BE-3 未実装のため実データは `scripts/simulate_sensor.py` 投入分。 [Q2]
- KpiSummary の5項目は `total_sensors` / `level1_count` / `level2_count` / `level3_count` / `estimated_cost_saved_yen` + `is_estimate`・`assumption_doc`（内訳カウントはアラート実データ由来。`today_detections` は今回の対象外）。 [Q3]
- 空ストアでも 200 OK で全項目0・`total_sensors` は `hydrants.json` 実件数（10件）を返す。成功指標は Issue 受け入れ条件の通過で十分（8/15 デモ完了を最優先）。 [Q4]

- Looks correct
- Request changes

[Answer]: Looks correct

## Assumption Confirmation

- コミュニケーション要件（報告頻度・報告対象・連絡体制）は確認されていない。 [assumption]

- A. Accept assumptions
- B. Convert to follow-up questions

[Answer]: A. Accept assumptions
