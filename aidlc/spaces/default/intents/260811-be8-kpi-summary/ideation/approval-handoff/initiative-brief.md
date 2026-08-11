# Initiative Brief — BE-8 KPI「推定削減コスト」算定ロジックとサマリAPI

> イニシアティブの全体像を1ページにまとめた承認用ブリーフ。イデエーション段階の成果物（intent-statement.md・stakeholder-map.md）とリポジトリ実態に基づいて編纂する。

## 1. 意図と問題定義

ダッシュボードKPI「推定削減コスト」は、現状フロントにハードコード（`estimatedCostSavedYen: 1_420_000`）されており算定根拠が存在しない。このKPIを `docs/business-model.md` §3 の算定式のみを根拠にバックエンドで算出し、`GET /api/v1/kpi/summary` で返すことで、根拠のない金額を断定的に表示しない。

- 出典: [intent-statement.md](../intent-capture/intent-statement.md)（Problem Statement）
- 契機: GitHub Issue #18「BE-8: KPI『推定削減コスト』の算定ロジックとサマリAPIの実装」の実装指示

## 2. スコープ境界

| 項目 | 決定内容 |
|------|----------|
| 対象ファイル | バックエンド5ファイル: `app/services/kpi.py`・`app/schemas/kpi.py`・`app/routers/kpi.py`・`tests/test_kpi.py` 新規、`main.py` へのルーター登録 |
| 変更対象外 | フロント（`page.tsx` の `MOCK_KPI_DATA`）は変更しない |
| 型とデータ源 | 深刻度は既存 `app.schemas.telemetry.SeverityLevel`（Literal[0,1,2,3]）を再利用。アラートデータ源はインメモリストア（`get_store().list_alerts()`）。BE-3未実装のため実データは `scripts/simulate_sensor.py` 投入分 |
| レスポンス | 5項目（`total_sensors` / `level1_count` / `level2_count` / `level3_count` / `estimated_cost_saved_yen`）+ `is_estimate`・`assumption_doc`。`today_detections` は今回の対象外 |
| 空ストア時の挙動 | 200 OK で全項目0・`total_sensors` は `hydrants.json` 実件数 |

- 出典: [intent-statement.md](../intent-capture/intent-statement.md)（Initial Scope Signal）

## 3. 市場検証サマリ

本イニシアティブは8/15デモ完了を最優先としたMVPスコープ（`be8-kpi-summary`）であり、市場調査・競合分析はスコープ外として省略する（ワークフローが対象としないステージ）。市場検証の代替として、デモ参加者（ダッシュボード表示層・デモ参加者）がステークホルダーマップで特定されており、デモで算定根拠のあるKPIを確認できることをもって検証とする。

- 出典: [stakeholder-map.md](../intent-capture/stakeholder-map.md)（Key Stakeholders and Their Interests）

## 4. フィージビリティとリスク

### 実現性
- バックエンド限定の追加実装であり、既存のインメモリストア・`SeverityLevel`・FastAPIルーター登録パターンを再利用するため、実現リスクは低い。
- 既存テスト（`tests/test_alerts.py` 等）と同パターンで `TestClient` エンドポイントテストを追加する。

### 主要リスクと対策
| リスク | 対策 |
|--------|------|
| **BE-3 未実装**（FFT解析による実漏水検知なし） | 実データ源は `scripts/simulate_sensor.py` 投入分（解析済みテレメトリ）を使用し、既存 `SeverityLevel` で集計する |
| **仮説定数ベースの試算値**（デモ内訳合計 2,048,400 円は `docs/business-model.md` §3 の仮説定数に基づく） | `is_estimate`・`assumption_doc` で試算値である旨をAPIレスポンスで明示する |
| **フロント連携時の型不一致**（API snake_case 5項目 vs フロント `KpiData` の camelCase・`today_detections` 有無） | フロント変更はスコープ外とし、実API接続（FE-7 等）は後続ストーリーで対応する |

- 出典: [approval-handoff-questions.md](approval-handoff-questions.md)（Q2）、[intent-statement.md](../intent-capture/intent-statement.md)

## 5. コンセプト

UIモックアップはスコープ外（フロント変更なし・バックエンドAPI追加のみ）のため作成しない。コンセプトは「算定根拠を持つ推定削減コストをバックエンドで算出しAPIで返す」一点に集約される。

```
[フロント KpiSummary] --(GET /api/v1/kpi/summary)--> [app/routers/kpi.py]
                                                        |
                                                        v
                                               [app/services/kpi.py]
                                                算定式: docs/business-model.md §3
                                                        |
                                                        v
                                        [インメモリストア解析済みテレメトリ]
```

<!-- Text fallback: フロントは /api/v1/kpi/summary を呼び、ルーターからサービス層で算定式を適用し、インメモリストアのアラート実データを集計してレスポンスを返す -->

## 6. チームプラン

- 実装担当: ユーザー（単一イテレーション・単一ユニット）。ステークホルダーはダッシュボード表示層とデモ参加者。
- 進め方: AI-DLCワークフローに沿って Requirements Analysis → Application Design → Code Generation → Build & Test を順次実施し、各段階で人間が承認。
- 完了期限: 8/15デモ完了を最優先。品質基準はpytestカバレッジ80%以上。
- 出典: [stakeholder-map.md](../intent-capture/stakeholder-map.md)、[approval-handoff-questions.md](approval-handoff-questions.md)（Q3）

## 7. Go/No-Go 推奨

**推奨: GO**

- 関係者は意図とスコープに合意（approval-handoff Q1）
- 主要リスクは認識・対策済み（approval-handoff Q2）
- 8/15デモ完了に向けたリソース投入に合意（approval-handoff Q3）
- バックエンド限定・既存パターン再利用で実現性が高く、空ストア時も200で返す等の受け入れ条件が明確

## 参考元

- [intent-statement.md](../intent-capture/intent-statement.md)
- [stakeholder-map.md](../intent-capture/stakeholder-map.md)
- [approval-handoff-questions.md](approval-handoff-questions.md)
