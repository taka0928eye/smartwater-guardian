# Rough Mockups Questions — FE-7 KPIサマリの実データ連携と「試算値」注記

## Sources

- [desc] Initial description: "GitHub内のISSUESを確認し、ISSUE#19「FE-7: KPIサマリの実データ連携と「試算値」注記の実装」を実装してください。"
- [scope] Workflow-selected scope: `feature`.
- [intent] `ideation/intent-capture/intent-statement.md`（Issue #19 要件・成功指標・配線方式・対象6ファイル）。
- [Q1] `ideation/scope-definition/scope-document.md`（カード構成変更・試算値注記・スケルトン表示・対象6ファイル）。
- [Q2] `ideation/scope-definition/intent-backlog.md`（単一 proto-Unit・依存先順）。
- [feasibility] `ideation/feasibility/feasibility-assessment.md`（実データ構成・モック値非表示）。
- [memory:M1] `aidlc/spaces/default/memory/project.md#Corrections`: "実データ不在のカードは削除し、実データで埋められるカード（例: BE-8 が返す level1_count）を追加する構成に揃える。モック値の表示を残さない。 (learned 2026-08-11) <!-- cid:feasibility:c5 -->"
- [memory:M2] `aidlc/spaces/default/memory/project.md#Corrections`: "ステージの質問群のうちスコープに該当しない質問（市場検証・モックアップ・モブ編成等）は省略し、実決定に必要な質問のみ提示する。 (learned 2026-08-11) <!-- cid:approval-handoff:c2 -->"

## Q1. KPI カード構成（並び順・レベル1カードの位置）

既存は「監視センサー数 / Level 3 / Level 2 / 本日の検知数 / 推定削減コスト」の5枚です。本イニシアティブで「本日の検知数」を削除し「Level 1（注意）」を追加します。並び順をどうしますか？ [Q1] [feasibility]

- A. 監視センサー数 / Level 3 / Level 2 / Level 1 / 推定削減コスト（既存の深刻度順を維持し、Level 1 を右端へ。推奨 — 変更を最小化）
- B. 監視センサー数 / Level 1 / Level 2 / Level 3 / 推定削減コスト（レベル昇順に整理）
- C. 監視センサー数 / Level 1 / Level 2 / Level 3 / 推定削減コスト / 注記（コストカードを左寄せにする等の変更）
- X. Other (please specify)

[Answer]: A

## Q2. 「試算値」注記の表示位置・文言

受入条件は「KPI カードに『試算値（前提: `docs/business-model.md`）』の注記が常時表示される」です。注記の表示方法をどうしますか？ [intent] [Q1]

- A. 「推定削減コスト」カード内に「試算値」ラベルを追加（カード見出しに併記。推奨 — 金額の性質をカード単位で明示）
- B. KPI サマリセクションの最下部に一行注記（全カードに共通の但し書き）
- C. コストカード内 + セクション下部の両方に表示
- X. Other (please specify)

[Answer]: A

## Q3. スケルトン表示のパターン

バックエンド停止中に白画面を避けるため、KPI サマリ部分をスケルトン表示にします。どのパターンにしますか？ [intent] [Q1]

- A. カードと同じ形状のスケルトンカードを5枚表示（レイアウトの跳びを防ぐ。推奨）
- B. 単一のローディングバーを1行表示
- C. その他（具体を指定）
- X. Other (please specify)

[Answer]: A

## Q4. アクセシビリティ要件

本アプリはダッシュボード表示中心で、既存実装は `aria-label` を付与しています。アクセシビリティ要件をどう扱いますか？ [Q1]

- A. 既存パターン（`aria-label`・セマンティック見出し・キーボード操作）を維持し、WCAG 2.1 AA の達成基準に適合させる（推奨）
- B. 追加のアクセシビリティ要件はなし（既存維持のみ）
- X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- KPI カード構成は「監視センサー数 / Level 3 / Level 2 / Level 1 / 推定削減コスト」の5枚（本日の検知数を削除、Level 1 を追加）。
- 「試算値」注記は推定削減コストカード内に表示。
- スケルトンはカードと同じ形状で5枚表示。
- アクセシビリティは既存パターン維持 + WCAG 2.1 AA 適合。

- Looks correct
- Request changes

[Answer]: Looks correct
