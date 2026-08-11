# Intent Statement — FE-7 KPIサマリの実データ連携と「試算値」注記

## Problem Statement

ダッシュボードの KPI サマリは現状ハードコードされたモック値（`MOCK_KPI_DATA`: `estimatedCostSavedYen: 1_420_000` / `totalSensors: 1240`）を表示しており、算定根拠のない金額を断定的に見せている。BE-8 が `GET /api/v1/kpi/summary` で実データを返せるようになったため、これを実データへ置き換え、根拠のない金額を断定的に見せない（`docs/business-model.md` §3.5）という要件に準拠する。あわせて `SeverityLevel` 型の二重定義（`types/api.ts` の `1|2|3` と `lib/severity.ts` の `0|1|2|3`）が矛盾しており、Level 0（正常）を表現できない API 型を解消する。 [desc] [Q1] [Q3]

## Target Customer

- **一次顧客**: 水道事業者（オペレータ・管理者）。監視状況の一覧把握と漏水削減効果（推定削減コスト）の確認に使う。 [Q4]
- **最終確認者**: デモ・レビュー評価者（8/15 デモのステークホルダー）。 [Q7]

## Success Metrics

受け入れ条件の通過を成功指標とする（8/15 デモ完了を最優先、追加指標なし）。 [Q5]

- `MOCK_KPI_DATA` が削除され、KPI 由来のハードコード（`1_420_000` / `1420000` / `1240`）が0件
- `SeverityLevel` の型定義がリポジトリ内で1箇所のみ（`lib/severity.ts` の `0 | 1 | 2 | 3`）で、バックエンド `Literal[0,1,2,3]` と一致
- KPI カードに「試算値（前提: `docs/business-model.md`）」の注記が常時表示される
- バックエンド停止中でも白画面にならずスケルトン表示にとどまる
- `page.tsx` に `'use client'` が付いていない / `any` を使用していない
- `npm run build` / `npm run lint` / `npm run test` 成功、カバレッジ80%以上

## Initiative Trigger

- **規約・品質要件への準拠**: PRD §3.1 / 評価軸3 / `docs/business-model.md` §3.5（根拠のない金額を断定的に見せない）。 [Q6]
- **デモ期限**: 8/15 デモ完了を最優先（P0・想定日8/12）。 [Q5] [Q6]

## Initial Scope Signal

- **ワークフロー選択スコープ**: `feature`（workflow-selected）。 [scope]
- **ユーザー確認済み製品境界**: 対象は Issue #19 記載の6ファイルのみ（`frontend/src/types/api.ts`・`frontend/src/lib/api.ts`・`frontend/src/app/page.tsx`・`frontend/src/components/dashboard/KpiSummary.tsx`・`frontend/src/lib/__tests__/api.test.ts`・`frontend/src/components/dashboard/__tests__/KpiSummary.test.tsx`）。バックエンド（BE-8 実装済み）は変更しない。 [Q1]
- **KPI 配線方式**: `DashboardClient` 側で `fetchKpiSummary()` をポーリングし、`KpiSummary` をその配下で描画する（Issue 推奨方式）。`page.tsx` は Server Component のまま維持。 [Q2]

## Assumptions & Open Questions

- コミュニケーション要件は「特になし」（個別 Issue ベースで進捗管理）で確定。 [Q8]
- `today_detections` はバックエンドスキーマ上も「FE-7 以降で対応」とされており、本イニシアティブの KPI 表示対象外。 [Q3]
- その他の未確定項目はなし（None）。

## Review

**Verdict:** NOT-READY
**Reviewer:** aidlc-product-lead-agent
**Date:** 2026-08-11T05:16:13Z
**Iteration:** 1

### Findings

| # | Severity | Location | Finding | Recommendation |
|---|---|---|---|---|
| 1 | Major | intent-statement.md — Success Metrics 一覧（6行） | claim-sources センサーが Success Metrics の6つの主張ブロック（`MOCK_KPI_DATA` 削除〜カバレッジ80%）にソースタグが無いと検出（センサー詳細 claim-sources-325fe828.md、全11件中6件）。内容は Q5 の質問文・回答に由来し実質は成立するが、接地契約ルール2「全クレームブロックへインラインタグ付与」に違反し、センサーが赤のまま。 | 各箇条書きに `[Q5]` を付与する。 |
| 2 | Major | intent-statement.md — ## Assumptions & Open Questions ／ intent-capture-questions.md に ## Assumption Confirmation が無い | 非Noneの前提2件（コミュニケーション要件 [Q8]・today_detections [Q3]）が `[assumption]` タグ無しで記載され、ステップ6で必須の「## Assumption Confirmation」が質問ファイルに存在しない。センサーは "retained assumptions require an answered ## Assumption Confirmation with Accept assumptions" を報告。前提が人間確認なしに保持されている。 | Assumption Confirmation 節を追加し A/B の回答を得る。あわせてコミュニケーション要件行は Q8 で確定済みの事実なので Assumptions 節から除去し、真の前提のみ残す。 |
| 3 | Major | intent-statement.md — ## Assumptions & Open Questions の today_detections 行 | 「`today_detections` は…本イニシアティブの KPI 表示対象外」というスコープ排除が [Q3] を引用するが、Q3 の質問・回答は today_detections に一切言及せず解決不能。根拠はバックエンド `backend/app/schemas/kpi.py:21`（"FE-7 以降で対応"）に実在するが許容ソース外であり、この除外をユーザーは明示確認していない。 | 引用を [Q3] から `[assumption]` に変更し、Assumption Confirmation でユーザー確認する。もしくは today_detections の扱いを明示質問として追加する。 |
| 4 | Minor | intent-capture-questions.md — Sources レジスタ [memory:M1] | 引用ルールが先頭のリストマーカー `- ` 付きで記載され、センサーはマーカーを除去して比較するため、4回全ての claim-sources 実行で "[memory:M1] quoted rule does not exactly match" を報告。ルール自体は project.md に実在する。 | 引用文字列から先頭 `- ` を除去し、`スコープ境界（対象ファイル・配線範囲）はユーザー確認で確定する。 (learned 2026-08-10) <!-- cid:intent-capture:c1 -->` のみを引用する。 |
| 5 | Minor | intent-statement.md / stakeholder-map.md — ## Assumptions & Open Questions の None 行 | 送り値は固定トークン `None.` と規定されているが、「その他の未確定項目はなし（None）。」「追加の前提・未確定項目はなし（None）。」と言い換えており、センサー（isNoneBlock）は `None.` のみを除外対象とするため、この行を未タグの前提として検出する。 | 各行を `None.` に変更する。 |
| 6 | Minor | stakeholder-map.md — Key Stakeholders の「PRD / Issue（要件定義）」行 | ステークホルダーとして成果物（PRD / Issue）が列挙されており、Q7 回答に由来はするが、ステークホルダーは人／役割であるべき。決定の主体は実質「要件定義者」または「開発チーム」。 | 主体を「要件定義者（PRD / Issue の作成者）」等に置き換え、関心事の欄で要件の出所として明示する。 |

### Summary

内容の実質（Problem Statement・Target Customer・Success Metrics・Initial Scope Signal）は Issue #19 と整合し、実装可否の観点では成立している。ただし claim-sources センサーが両成果物で赤（intent-statement 11件・stakeholder-map 12件）であり、接地契約ルール2違反（Success Metrics のタグ欠落6件）、前提の [assumption] タグ欠落とステップ6の Assumption Confirmation 未実施、today_detections の解決不能引用による未確認スコープ除外が残る。いずれも機械的・手続的修正で解消可能だが、advisory パスのため修正ループは後ろに無い。承認ゲートで「センサーの赤を許容して先へ進む」か「上記5件の是正を要求して Request Changes」かを人間が判断されたい。実装ブロッカー（Critical）は無い。

