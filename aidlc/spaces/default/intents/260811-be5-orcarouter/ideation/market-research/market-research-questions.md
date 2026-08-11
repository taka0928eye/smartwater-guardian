# Market Research Questions — BE-5: services/orcarouter.py によるLLM自動起票の実装

## Sources

- [desc] Initial description: "GitHub内のISUUESを確認し、ISSUE#13「BE-5: services/orcarouter.py によるLLM自動起票の実装」を実装してください。短期開発で時間が限られているので、GitHub ISSUEに書かれている作業内容に沿ってコード生成を始めてください。手が離せないので自動承認でOKです。"
- [scope] Workflow-selected scope: `feature`.
- [intent] 前段イニシアティブ・ステートメント `ideation/intent-capture/intent-statement.md`（対象: Issue #13 記載の4ファイルのみ、実装方針: httpx.AsyncClient + HttpClientDep、成功指標: Issue 受入条件11件）。
- [memory:M1] `aidlc/spaces/default/memory/project.md#Corrections`: "ステージの質問群のうちスコープに該当しない質問（市場検証・モックアップ・モブ編成等）は省略し、実決定に必要な質問のみ提示する。 (learned 2026-08-11) <!-- cid:approval-handoff:c2 -->"
- [memory:M2] `aidlc/spaces/default/memory/project.md#Corrections`: "外部 BI・可視化ツールの導入は build-vs-buy の評価対象外（既存 Next.js/Recharts スタックとの一貫性を優先）。 (learned 2026-08-11) <!-- cid:market-research:c3 -->"

## Q1. 市場調査の実施方針（外部調査 vs 既存資産の再利用）

本イニシアティブ（BE-5）は、外部 LLM サービス（Orcarouter API）経由の補修自動起票という内部機能の実装です。製品の市場コンテキスト（競合・市場トレンド・ビジネスモデル）は既に前段イニシアティブ FE-7 の market-research 成果物（competitive-analysis / market-trends / build-vs-buy）と `docs/business-model.md`・PRD に存在します。8/15 デモ完了が最優先という制約の下、市場調査の実施方針はどれにしますか？ [intent]

- A. 既存成果物（FE-7 market-research・`docs/business-model.md`・PRD）を市場コンテキストの出典とし、新規の外部調査は実施しない
- B. Web 検索等で外部調査を軽く実施し、競合・トレンドを補足する
- C. 市場調査成果物は N/A 表明（対象外理由の記載のみ）に留める
- D. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Q2. build-vs-buy の評価対象（LLM 自動起票）

BE-5 は外部 LLM サービス（Orcarouter API）を利用します。Issue #13・PRD（FR-3 / FR-4）で Orcarouter 採用が確定済みです。本イニシアティブで build-vs-buy の評価対象となる要素と結論はどれにしますか？ [intent]

- A. buy 確定 — Orcarouter API（外部 LLM サービス）を利用。Issue/PRD で採用確定済みのため、内製モデル構築や他 LLM プロバイダーへの乗り換えはデモ期間内に選択肢としない（確定判断の根拠整理のみ行う）
- B. 代替 LLM プロバイダー（OpenAI 直契約等）との比較を build-vs-buy に含める
- C. 内製モデルの構築余地を評価する
- D. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Q3. 競合分析・市場トレンドの粒度

製品全体の競合分析・市場トレンドは FE-7 で概要版を作成済みです。BE-5 はその中の「LLM 自動起票（アセットマネジメント自動化）」機能に相当します。成果物の粒度はどれにしますか？ [Q1]

- A. 概要のみ — 製品レベルの競合分析（FE-7 成果物）を引用し、LLM 自動起票機能の差別化の位置づけを簡潔に整理（軽量版）
- B. 詳細版 — LLM 自動起票機能に特化した機能比較マトリクスまで含む
- C. 本イニシアティブでは対象外として N/A 表明に留める
- D. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Q4. 市場規模（TAM/SAM/SOM）の扱い

`docs/business-model.md` §1.2 に LLM 自動起票の価格仮説（¥50/起票・従量オプション）、`docs/llm-cost.md` §3.2 に年間起票件数の仮説（Phase 2・1,000台で年間約300件）が定義済みです。市場規模の試算は必要ですか？ [intent]

- A. 新規試算不要 — business-model / llm-cost の既存仮説（¥50/起票・年間300件）を引用して整理する
- B. 必要 — 8/15 デモ資料に含めるため TAM/SAM/SOM の簡易試算を行う
- C. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- 市場調査は既存成果物（FE-7 market-research・business-model・PRD）を出典とし、新規の外部調査は実施しない。 [Q1]
- build-vs-buy は buy 確定（Orcarouter API）— Issue/PRD で採用確定済み。内製モデル構築や他プロバイダー乗り換えはデモ期間内に選択肢としない。 [Q2]
- 競合分析・市場トレンドの成果物は概要のみ（軽量版）— 製品レベル分析（FE-7）を引用し、LLM 自動起票機能の位置づけを整理。 [Q3]
- 市場規模は新規試算せず、business-model の価格仮説（¥50/起票）と llm-cost の件数仮説（年間300件）を引用して整理。 [Q4]
- 前提3件は承諾済み（Orcarouter 採用は確定判断の根拠整理 / 市場規模は既存仮説の引用 / 競合分析は FE-7 成果物の引用で網羅的ではない）。 [assumption]

- Looks correct
- Request changes

[Answer]: Looks correct

## Assumption Confirmation

- Orcarouter API の採用は Issue/PRD で確定済みであり、本ステージで再判断しない（build-vs-buy は確定判断の根拠整理として文書化する）。 [assumption]
- LLM 自動起票の市場規模は business-model の価格仮説（¥50/起票）と llm-cost の件数仮説（年間300件）を引用し、新規試算はしない。 [assumption]
- 競合分析・市場トレンドは FE-7 成果物の製品レベル分析を引用し、LLM 自動起票機能の位置づけを整理する軽量版である（網羅的ではない）。 [assumption]

- A. Accept assumptions
- B. Convert to follow-up questions

[Answer]: A. Accept assumptions
