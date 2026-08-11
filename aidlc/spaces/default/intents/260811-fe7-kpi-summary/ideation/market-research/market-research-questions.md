# Market Research Questions — FE-7 KPIサマリの実データ連携と「試算値」注記

## Sources

- [desc] Initial description: "GitHub内のISSUESを確認し、ISSUE#19「FE-7: KPIサマリの実データ連携と「試算値」注記の実装」を実装してください。"
- [scope] Workflow-selected scope: `feature`.
- [intent] 前段イニシアティブ・ステートメント `ideation/intent-capture/intent-statement.md`（対象: Issue #19 記載の6ファイルのみ、配線方式: DashboardClient ポーリング、8/15 デモ完了優先）。
- [memory:M1] `aidlc/spaces/default/memory/project.md#Corrections`: "ステージの質問群のうちスコープに該当しない質問（市場検証・モックアップ・モブ編成等）は省略し、実決定に必要な質問のみ提示する。 (learned 2026-08-11) <!-- cid:approval-handoff:c2 -->"

## Q1. 市場調査の実施方針（外部調査 vs 既存ドキュメント参照）

本イニシアティブ（FE-7）は、ダッシュボードの KPI サマリを実データへ置き換え「試算値」注記を付す内部機能実装です。製品の市場コンテキストは既に `docs/business-model.md` と PRD に存在します。8/15 デモ完了が最優先という制約の下、市場調査の実施方針はどれにしますか？ [intent]

- A. 既存ドキュメント（`docs/business-model.md`・PRD）を市場コンテキストの出典とし、外部調査は実施しない（軽量版）
- B. Web 検索等で外部調査を軽く実施し、競合・トレンドを補足する
- C. 市場調査成果物は N/A 表明（対象外理由の記載のみ）に留める
- D. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: B

## Q2. build-vs-buy の評価対象

KPI 算定は BE-8 で実装済み（`GET /api/v1/kpi/summary`）です。本イニシアティブで build-vs-buy の判断が必要な要素はありますか？ [intent]

- A. なし — バックエンドは実装済み、フロント表示は既存 Next.js スタックのカスタム実装が既定（build 確定）
- B. ダッシュボード表示に外部 BI・可視化ツール（Recharts 以外）の導入余地を評価すべき
- C. その他（自由記述で指定）
- D. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Q3. 競合分析・市場トレンドの粒度

競合分析・市場トレンドの成果物の粒度はどれにしますか？ [Q1]

- A. 概要のみ — 水道インフラ DX・漏水検知 IoT の競合と市場動向を簡潔に整理（軽量版）
- B. 詳細版 — 機能比較マトリクス・ポジショニングマップまで含む
- C. 本イニシアティブでは対象外として N/A 表明に留める
- D. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Q4. 市場規模（TAM/SAM/SOM）の扱い

市場規模の試算は必要ですか？ [Q3]

- A. 不要 — デモ評価者向けの内部機能実装であり、市場規模試算は本イニシアティブの目的外
- B. 必要 — 8/15 デモ資料に含めるため簡易試算を行う
- C. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: B

## Consolidated Summary Confirmation

- 市場調査は外部調査を軽く実施し、競合・市場トレンドを補足する。 [Q1]
- build-vs-buy は評価対象なし（build確定）— BE-8 実装済み、フロントは既存 Next.js スタックのカスタム実装。 [Q2]
- 競合分析・市場トレンドの成果物は概要のみ（軽量版）。 [Q3]
- 簡易市場規模試算（TAM/SAM/SOM）を 8/15 デモ資料に含める。 [Q4]
- 前提3件は承諾済み（直接競合の網羅性は推測に基づく / 市場規模は概算値 / 外部 BI 導入はスコープ外・将来再評価）。 [assumption]

- Looks correct
- Request changes

[Answer]: Looks correct

## Assumption Confirmation

- 直接競合の網羅性は、英語市場レポートの主要プレイヤー列挙と日本語市場調査のプレイヤー群から整理した推測に基づく（網羅的ではない）。 [assumption]
- 市場規模の数値は公開市場レポートの要約であり、レポート間で集計範囲が異なるため概算値として扱う。 [assumption]
- 外部 BI・可視化ツールの導入は本イニシアティブでは評価しない（スコープ外）。将来、ダッシュボードの可視化要求が高度化した場合に再評価する。 [assumption]

- A. Accept assumptions
- B. Convert to follow-up questions

[Answer]: A. Accept assumptions
