# Intent Capture Questions — FE-7 KPIサマリの実データ連携と「試算値」注記

## Sources

- [desc] Initial description: "GitHub内のISSUESを確認し、ISSUE#19「FE-7: KPIサマリの実データ連携と「試算値」注記の実装」を実装してください。"
- [scope] Workflow-selected scope: `feature`.
- [memory:M1] `aidlc/spaces/default/memory/project.md#Corrections`: "- スコープ境界（対象ファイル・配線範囲）はユーザー確認で確定する。 (learned 2026-08-10) <!-- cid:intent-capture:c1 -->"

## Q1. 製品境界（スコープ）の確認

このワークフローは **`feature`** スコープで進みます。GitHub Issue #19 の主旨は「BE-8 が算出した KPI（`GET /api/v1/kpi/summary`）を実データとして表示し、ハードコードされた `MOCK_KPI_DATA`（`estimatedCostSavedYen: 1_420_000` / `totalSensors: 1240`）を破棄する。あわせて `SeverityLevel` 型の二重定義（`types/api.ts` の `1|2|3` と `lib/severity.ts` の `0|1|2|3`）を解消する」ことです。変更対象は Issue 記載の6ファイル（`frontend/src/types/api.ts`・`frontend/src/lib/api.ts`・`frontend/src/app/page.tsx`・`frontend/src/components/dashboard/KpiSummary.tsx`・`frontend/src/lib/__tests__/api.test.ts`・`frontend/src/components/dashboard/__tests__/KpiSummary.test.tsx`）です。この製品境界は想定どおりですか？

- A. はい、`feature` スコープで正しい — 対象は上記6ファイルのみ。バックエンド（BE-8 実装済み）は変更しない
- B. いいえ、フロント対象ファイルを増やす（範囲は自由記述で指定）
- C. いいえ、対象ファイルを減らす（範囲は自由記述で指定）
- D. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Q2. KPI データの配線方法（取得場所）

Issue の実装方針は「`page.tsx` は Server Component のまま維持。KPI はポーリング対象なので FE-5 の `DashboardClient`（Client Component、5秒間隔ポーリング実装済み）が保持する形に寄せる。ただし FE-5 未完なら暫定的に `page.tsx` の Server 側 fetch でも可」とあります。FE-5 は実装済みです。KPI サマリの取得・表示はどちらの方式にしますか？

- A. `DashboardClient` 側で `fetchKpiSummary()` をポーリングし、`KpiSummary` をその配下で描画する（Issue 推奨。KPI がアラートと同タイミングで更新される）
- B. `page.tsx` の Server 側で `fetchKpiSummary()` を1回実行し、`KpiSummary`（Server Component のまま）へ props で渡す（シンプル。ただしリクエスト毎の取得でポーリングはしない）
- C. 両方の暫定版として、まず B で実装し後続 FE で A に寄せる
- D. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Q3. ビジネス課題と解決価値

Issue の目的は「PRD §3.1 / 評価軸3。ハードコードされた KPI を実データに置き換え、根拠のない金額（1,420,000円）を断定的に見せない（`docs/business-model.md` §3.5 の「試算値」注記）」ことです。ビジネス課題の理解はこれで合っていますか？

- A. 合っている — 実データ化により KPI の信頼性が上がり、試算値注記により根拠のない数値の断定的表示を防ぐ
- B. 実データ化は主目的ではなく、試算値注記が主目的
- C. 課題の理解が違う（自由記述で指定）
- D. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Q4. ターゲット顧客（誰の課題か）

この画面は消火栓センサーによる漏水監視ダッシュボードで、KPI サマリは水道事業者（オペレータ・管理者）が監視状況と漏水削減効果を把握するために使います。ターゲット顧客とペインの理解はこれで合っていますか？

- A. 水道事業者（オペレータ・管理者） — 監視状況の一覧把握と漏水削減効果（推定削減コスト）の確認
- B. デモ・レビュー評価者（8/15 デモのステークホルダー）が主対象
- C. 顧客像が違う（自由記述で指定）
- D. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Q5. 成功指標

Issue の受け入れ条件がそのまま成功指標になり得ます（`MOCK_KPI_DATA` 削除 / `SeverityLevel` 定義がリポジトリ内1箇所 / バックエンド `Literal[0,1,2,3]` と一致 / 試算値注記の常時表示 / バックエンド停止時もスケルトン表示で白画面にしない / `'use client'` なし / `any` なし / build・lint・test 成功 / カバレッジ80%以上）。成功指標は受け入れ条件の通過で確定しますか？

- A. 受け入れ条件の通過を成功指標とする（8/15 デモ完了を最優先、追加指標なし）
- B. デモでの目視確認（実データ表示・注記表示）も成功指標に含める
- C. 別の成功指標がある（自由記述で指定）
- D. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Q6. イニシアティブのトリガー

このイニシアティブのトリガーは「PRD §3.1 / 評価軸3 / `docs/business-model.md` §3.5 の要件（根拠のない金額を断定的に見せない）への準拠」と「8/15 デモ完了のマイルストーン」です。トリガーの理解はこれで合っていますか？

- A. 規約・品質要件への準拠とデモ期限（P0・想定日8/12）がトリガー
- B. 実データ連携のビジネス価値（漏水削減効果の可視化）が主トリガー
- C. トリガーが違う（自由記述で指定）
- D. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Q7. ステークホルダーと決定権者

ステークホルダー候補は「開発チーム（FE/BE）」「PRD・ビジネスモデルの要件定義者」「デモ評価者（8/15）」です。スコープ・優先度の決定権者と、影響力を持つ人は誰ですか？

- A. 開発チームが実装判断、要件は PRD / Issue が決定済み。デモ評価者が最終確認
- B. 要件定義者（PRD・docs の作成者）がスコープ決定の主権者
- C. 別のステークホルダーがいる（自由記述で指定）
- D. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Q8. コミュニケーション要件

報告頻度・報告対象・連絡体制に関する要件（例: 定例レビューの有無、進捗報告先）はありますか？

- A. 特になし（個別 Issue ベースで進捗管理、コミュニケーション要件なし）
- B. 進捗報告が必要（対象・頻度は自由記述で指定）
- C. 報告先や体制が決まっている（自由記述で指定）
- D. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- スコープは `feature` で正しい。対象は Issue 記載の6ファイルのみ（`frontend/src/types/api.ts`・`frontend/src/lib/api.ts`・`frontend/src/app/page.tsx`・`frontend/src/components/dashboard/KpiSummary.tsx`・`frontend/src/lib/__tests__/api.test.ts`・`frontend/src/components/dashboard/__tests__/KpiSummary.test.tsx`）。バックエンド（BE-8 実装済み）は変更しない。 [Q1]
- KPI データは `DashboardClient` 側で `fetchKpiSummary()` をポーリングし、`KpiSummary` をその配下で描画する（Issue 推奨方式。アラートと同タイミングで更新）。 `page.tsx` は Server Component のまま維持。 [Q2]
- ビジネス課題は「実データ化により KPI の信頼性を上げ、試算値注記により根拠のない金額の断定的表示を防ぐ」ことで合っている。 [Q3]
- ターゲット顧客は水道事業者（オペレータ・管理者）。監視状況の一覧把握と漏水削減効果（推定削減コスト）の確認。 [Q4]
- 成功指標は Issue 受け入れ条件の通過（`MOCK_KPI_DATA` 削除 / `SeverityLevel` 1箇所 / 注記常時表示 / スケルトン / `'use client'` なし / `any` なし / build・lint・test・カバレッジ80%）。8/15 デモ完了を最優先。 [Q5]
- トリガーは PRD §3.1 / 評価軸3 / `docs/business-model.md` §3.5 への準拠とデモ期限（P0・想定日8/12）。 [Q6]
- ステークホルダーは開発チーム（実装判断）、PRD / Issue（要件決定済み）、デモ評価者（最終確認）。 [Q7]
- コミュニケーション要件は特になし（個別 Issue ベースで進捗管理）。 [Q8]

- Looks correct
- Request changes

[Answer]: Looks correct
