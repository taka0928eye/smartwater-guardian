# Intent Statement — BE-8 KPI「推定削減コスト」算定ロジックとサマリAPI

## Problem Statement

ダッシュボードKPI「推定削減コスト」は、現状フロントにハードコード（`estimatedCostSavedYen: 1_420_000`）されており算定根拠が存在しない。このKPIを `docs/business-model.md` §3 の算定式のみを根拠にバックエンドで算出し、`GET /api/v1/kpi/summary` で返すことで、根拠のない金額を断定的に表示しない。 [desc] [Q1]

## Target Customer

- **ダッシュボード表示層（フロント `page.tsx` / `KpiSummary`）**: 算出済みの推定削減コストと実データ由来の内訳カウントを受け取って表示する（今回の変更対象はバックエンドのみで、フロントは変更しない）。 [Q1] [Q3]
- **デモ参加者（8/15 デモ）**: 算定根拠のあるKPIを確認する。デモ完了（8/15）が最優先。 [Q4]

## Success Metrics

- `GET /api/v1/kpi/summary` が 200 と5項目（`total_sensors` / `level1_count` / `level2_count` / `level3_count` / `estimated_cost_saved_yen`）+ `is_estimate`・`assumption_doc` を返す。 [Q3]
- KPI がアラート実データ（インメモリストアの解析済みテレメトリ）から算出され、固定値を返さない。 [Q2] [Q3]
- `total_sensors` が `hydrants.json` の実件数（現状10件）と一致する（`1240` のような架空値でない）。 [Q4]
- 空ストアでも 200 で全項目0を返す（500 にしない）。 [Q4]
- デモシナリオでの合計が 2,048,400 円になる。 [Q4]
- pytest カバレッジが80%以上。 [Q4]
- 受け入れ条件の通過で十分であり、追加の成功指標は設けない（8/15 デモ完了を最優先）。 [Q4]

## Initiative Trigger

- GitHub Issue #18「BE-8: KPI『推定削減コスト』の算定ロジックとサマリAPIの実装」の実装指示。 [desc]
- 現状フロントに算定根拠のないハードコード値が表示されており、算定式（`docs/business-model.md` §3）による算出へ置き換える必要がある。 [Q1]

## Initial Scope Signal

- **Workflow-selected scope:** `be8-kpi-summary`（workflow-selected） [scope]
- **User-confirmed product boundary:** バックエンド5ファイル（`app/services/kpi.py`・`app/schemas/kpi.py`・`app/routers/kpi.py`・`tests/test_kpi.py` 新規、`main.py` へのルーター登録）。フロント（`page.tsx` の `MOCK_KPI_DATA`）は変更しない。 [Q1]
- **型とデータ源:** 深刻度は既存 `app.schemas.telemetry.SeverityLevel`（Literal[0,1,2,3]）を再利用し、アラートデータ源はインメモリストア（`get_store().list_alerts()`）。BE-3 未実装のため実データは `scripts/simulate_sensor.py` 投入分。 [Q2]
- **レスポンス:** 5項目 + `is_estimate`・`assumption_doc`。`today_detections` は今回の対象外。 [Q3]
- **空ストア時の挙動:** 200 OK で全項目0・`total_sensors` は `hydrants.json` 実件数。 [Q4]

## Assumptions & Open Questions

None.

## Review

**Verdict:** READY
**Reviewer:** aidlc-product-lead-agent
**Date:** 2026-08-11T02:54:21Z
**Iteration:** 1

### Findings

| # | Severity | Location | Finding | Recommendation |
|---|---|---|---|---|
| 1 | Minor | intent-statement.md — Success Metrics 3行目 | 「`1240` のような架空値でない」の括弧書き値 `1240` は、質問ファイルのソースレジスタ（[desc] / [scope] / Q1〜Q4）に存在しない未登録ソースの提示。Issue #18 には記載があるが、引用タグ [Q4] だけでは解決できない。 | 括弧書きを削除するか、質問ファイルに当該値を根拠として追記し [Q4] で解決可能にする。 |
| 2 | Minor | stakeholder-map.md — Communication Requirements 表 | claim-sources センサーは最新実行（f8a417b1, 2026-08-11T02:49:13Z）でも Pass: false。「[assumption] が Assumptions 節の外」から「ソースタグなし」へ指摘内容が変わっただけで、行にセンサーが認識するインラインタグが無い状態が続く。前提そのものは質問ファイルの `## Assumption Confirmation`（`[Answer]: A. Accept assumptions`）で確認済みのため実質的根拠は intact だが、今回の再レビューの目的（センサー適合）は未達。 | Communication Requirements の行を非実体的ポインタ（Assumptions 節参照）に整理するか、前提を `## Assumptions & Open Questions` 節に一本化して表から独立した主張を除去する。センサーは advisory のため READY 判定は阻害しない。 |
| 3 | Minor | intent-statement.md — Initial Scope Signal / リスク明示 | API の snake_case 5項目（`total_sensors` ほか）と現行フロント `KpiData`（camelCase で `todayDetections` を含む）の間にはフィールド名・構成の不一致があるが、後続のフロント連携で必要になるマッピング（`today_detections` 除外を含む）が「既知の延期事項」として明示されていない。 | Initial Scope Signal または Assumptions に「フロント連携時のフィールド名マッピングは別ストーリーで対応」と1行明記する。 |

### Summary

Critical / Major なし。内容は Issue #18 と `docs/business-model.md` §3 の主旨（算定根拠のある KPI をバックエンドで算出し固定値を返さない）に整合し、成功指標はいずれもテスト可能（200 と5項目＋`is_estimate`、空ストアでも200・全項目0、デモ内訳合計 2,048,400 円、カバレッジ80%以上）。前回 READY から実質不変。3件の Minor はいずれも実装を妨げない。承認ゲートで認識すべき点は、今回の再レビューの契機となった claim-sources センサー指摘が stakeholder-map の Communication Requirements 表で未解消（最新実行も Pass: false）なこと。advisory のため READY 判定は維持するが、この残余を許容するか、次段階着手前に表記整理を求めるかを人間が判断されたい。
