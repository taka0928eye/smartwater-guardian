# Rough Mockups — User Flow — FE-7 KPIサマリの実データ連携と「試算値」注記

## 主要ユーザーフロー（ハッピーパス）

デモ評価者（水道事業者オペレータ / レビュー評価者）がダッシュボードを開き、KPI サマリで漏水削減効果（推定削減コスト）を確認するまでの流れ。 [intent]

```
[ダッシュボードにアクセス]
        |
        v
[KPI サマリ初期表示]
  - 初回ロード中: スケルトンカード×5を表示  [Q3]
        |
        v
[BE-8 から実データ取得成功]
  - fetchKpiSummary() が KpiSummary を返す
  - 5枚のカードを実データで描画  [Q1]
  - 推定削減コストカードに「試算値」注記  [Q2]
        |
        v
[監視・確認]
  - カード値を確認（センサー数 / Level 3・2・1 / コスト）
  - レベルカードは深刻度色で即時把握  [Q4]
```

<!-- テキストフォールバック: ダッシュボードアクセス → KPIサマリ（スケルトン→実データ）→ カード確認 → 監視継続 -->

## エラー / フォールバックフロー

バックエンド（BE-8）が停止中またはタイムアウトの場合、白画面にせずスケルトン表示に留めます。 [intent]

```
[KPI サマリ表示中]
        |
        +-- 取得成功 -------------> [実データで5枚描画]
        |
        +-- 失敗（停止・タイムアウト）--> [スケルトン表示を維持]
                                              |
                                              v
                                        [白画面を回避]  [Q3]
```

<!-- テキストフォールバック: 成功時は実データ描画、失敗時はスケルトン表示を維持して白画面を回避 -->

## 情報階層

- **一次情報（常時表示）**: 監視センサー数 / Level 3・2・1 件数 / 推定削減コスト（試算値）。 [Q1]
- **二次情報（注記）**: 試算値の前提文書（`docs/business-model.md`）への言及。 [Q2]
- **表示優先度**: 深刻度の高いレベルほど強調色で目立たせる（Level 3=赤 / Level 2=黄 / Level 1=青）。 [Q4]

## Assumptions & Open Questions

- その他の未確定項目はなし（None.）

## Sources

- [desc] Initial description: "GitHub内のISSUESを確認し、ISSUE#19「FE-7: KPIサマリの実データ連携と「試算値」注記の実装」を実装してください。"
- [scope] Workflow-selected scope: `feature`.
- [intent] `ideation/intent-capture/intent-statement.md`（ターゲット顧客・配線方式・成功指標）
- [Q1] `ideation/scope-definition/scope-document.md`（カード構成・スケルトン表示）
- [Q1] Rough Mockups 質問ファイル `ideation/rough-mockups/rough-mockups-questions.md` の回答 A（カード構成）
- [Q2] 同 Q2 回答 A（試算値注記はコストカード内）
- [Q3] 同 Q3 回答 A（スケルトンカード5枚）
- [Q4] 同 Q4 回答 A（アクセシビリティ維持 + WCAG 2.1 AA）
