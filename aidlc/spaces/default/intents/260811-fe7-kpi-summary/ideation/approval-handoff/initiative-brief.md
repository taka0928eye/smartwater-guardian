# Initiative Brief — FE-7 KPIサマリの実データ連携と「試算値」注記

> イデアーション全成果物を集約したイニシアティブ・ブリーフ（1ページ要約）。承認ゲート後にインセプション（Reverse Engineering 以降）へ引き継ぐ。

## 1. Intent & Problem Statement

ダッシュボードの KPI サマリは現状ハードコードされたモック値（`MOCK_KPI_DATA`: `estimatedCostSavedYen: 1_420_000` / `totalSensors: 1240`）を表示しており、算定根拠のない金額を断定的に見せている。BE-8 が `GET /api/v1/kpi/summary` で実データを返せるようになったため、これを実データへ置き換え、「試算値」注記を常時表示する（`docs/business-model.md` §3.5 準拠）。あわせて `SeverityLevel` 型の二重定義（`types/api.ts` の `1|2|3` と `lib/severity.ts` の `0|1|2|3`）が矛盾しており、Level 0（正常）を表現できない API 型を解消する。 [intent] [desc]

**一次顧客**: 水道事業者（オペレータ・管理者）。**最終確認者**: デモ・レビュー評価者（8/15 デモのステークホルダー）。 [intent]

## 2. Market Validation Summary

対象は既存ダッシュボードのカード構成変更であり、新規市場投入ではない。競合分析（competitive-analysis）では、SMG は「低導入コスト × 常時監視」の象限に位置し、「消火栓貼付型」「ハイブリッド AI 解析」「自動アセットマネジメント」で差別化する。本変更はそのうち「試算値」注記の透明性（根拠のない金額を断定的に見せない）を高めるもので、市場ポジションと整合する。外部 BI・可視化ツールの導入は build-vs-buy の評価対象外（既存 Next.js/Recharts スタックとの一貫性を優先）。 [market-research] [feasibility]

## 3. Feasibility & Risk Highlights

**技術的成立性**: 成立。既存 API（BE-8 実装済み）へのフロント配線と型の重複解消という低リスクの内部変更。 [feasibility]

| リスク | 評価 | 軽減策 |
|---|---|---|
| `SeverityLevel` の依存方向（契約層→UI層） | 低 | `lib/severity.ts` は `types/api.ts` に依存しないため循環 import なし。単一ソースを `lib/severity.ts` に確定 [feasibility] |
| スキーマ差分（`is_estimate` / `assumption_doc` の未保有） | 低 | 「試算値」注記は `is_estimate` に依存せず定常表示で充足。型は後方互換を保ち追加可能 [feasibility] |
| カバレッジ 80% 維持 | 低 | 既存テストパターン（vitest + axios spy）で達成可能 [feasibility] |
| 上流レビューの Major 2件 | 中 | ① intent-backlog 未参照 → イニシアティブ・ブリーフで intent-backlog を明示参照 ② 「試算値」注記の表示方式 → Q2=A で「カード内の常時表示インライン短文」に確定 [review] |

## 4. Scope Boundary

- **対象（In Scope）**: Issue #19 記載の6ファイルのみ。 `frontend/src/types/api.ts`（`SeverityLevel` re-export）・`frontend/src/lib/api.ts`（`fetchKpiSummary()` 追加）・`frontend/src/app/page.tsx`（`MOCK_KPI_DATA` 削除、Server Component 維持）・`frontend/src/components/dashboard/KpiSummary.tsx`（カード構成変更）・`frontend/src/lib/__tests__/api.test.ts`（テスト追加）・`frontend/src/components/dashboard/__tests__/KpiSummary.test.tsx`（テスト更新）。 [intent] [Q1]
- **対象外（Out of Scope）**: バックエンド（BE-8）変更 / `today_detections`（本日の検知数）表示 / 認証・権限管理 / リアルタイム通知 / 本番用大型 GIS DB / 外部 BI 導入 / AWS・クラウドインフラ / 規制・コンプライアンス対応（N/A）。 [scope-document]
- **配線方式**: `DashboardClient` 側で `fetchKpiSummary()` をポーリングし、`KpiSummary` をその配下で描画。`page.tsx` は Server Component のまま。 [intent]
- **受入条件（成功指標）**: `MOCK_KPI_DATA` 削除・KPI ハードコード 0件 / `SeverityLevel` がリポジトリ内 1箇所のみ（`0 | 1 | 2 | 3`）で BE `Literal[0,1,2,3]` と一致 / 「試算値（前提: `docs/business-model.md`）」注記の常時表示 / バックエンド停止中もスケルトン表示で白画面回避 / `'use client'` なし・`any` なし / `npm run build`・`lint`・`test` 成功・カバレッジ 80% 以上。 [intent]

## 5. Concept Visuals

rough-mockups のワイヤーフレーム（`ideation/rough-mockups/wireframes.md`）をコンセプト資料として採用する（Q4=A）。KPI サマリは5カード構成（監視センサー数 / Level 3 / Level 2 / Level 1 / 推定削減コスト）で、コストカード見出しに「試算値」ラベルを常時表示し、ロード中・失敗時はスケルトン5枚を表示する。 [Q4] [wireframes]

```
+-------------------------------------------------------------------------------+
|  KPI サマリ                                             (h2 見出し)            |
|  +-----------+ +-----------+ +-----------+ +-----------+ +------------------+ |
|  | 監視センサー数 | | Level 3    | | Level 2    | | Level 1    | | 推定削減コスト    | |
|  |  1,240    | |  3         | |  12        | |  45        | | [試算値] 142万円  | |
|  +-----------+ +-----------+ +-----------+ +-----------+ +------------------+ |
|  （失敗時・ロード中はスケルトンカード×5を表示）                                 |
+-------------------------------------------------------------------------------+
```

<!-- テキストフォールバック: KPI サマリは5カード（監視センサー数 / Level 3 / Level 2 / Level 1 / 推定削減コスト）。コストカードに「試算値」注記。ロード中・失敗時はスケルトン5枚。 -->

## 6. Team Plan

- **体制**: ソロ開発者（ユーザー）+ AI-DLC エージェント（各ステージのリードペルソナ）。外部リソース不要（Q1=A）。モブ編成は適用しない。 [team-formation]
- **意思決定者**: 全ステージの承認ゲートでユーザーが最終承認。技術的判断は各ステージのリードエージェントが案を提示しユーザーが確定。 [team-formation]
- **キャパシティ**: 変更はフロントエンド6ファイル・見積「小」。8/15 デモ完了（P0・想定完了日 8/12）と作業量は整合。競合イニシアティブなし。 [team-formation] [feasibility]

## 7. Go/No-Go Recommendation

**GO を推奨する。** 技術的障壁・未解決リスクはなく、8/15 デモ完了（P0）に間に合う作業量である。上流レビューの Major 2件は本ブリーフで解決済み（intent-backlog を明示参照、試算値注記を「カード内の常時表示インライン短文」に確定）。インセプション（Reverse Engineering → Practices Discovery → Requirements Analysis → User Stories → Refined Mockups → Application Design → Units Generation → Delivery Planning）へ進行する。

**リスク調整済みビルド順序**（イニセプション以降）: 依存先順（型 → API クライアント → 表示）で単一 proto-Unit（BU-1）として構築する。 [intent] [scope-document] [intent-backlog]

```
[lib/severity.ts 型統一] --> [types/api.ts re-export] --> [lib/api.ts fetchKpiSummary]
                                                                |
                                                                v
                                        [DashboardClient ポーリング] --> [KpiSummary 表示]
                                                                        |
                                                                        v
                                                        [試算値注記 + スケルトン fallback] --> [8/15 デモ評価]
```

<!-- テキストフォールバック: 型統一 → APIクライアント実データ取得 → ダッシュボードKPI表示（試算値注記付き）→ 評価者確認 -->

## Assumptions & Open Questions

- その他の未確定項目はなし（None.）

## Sources

- [desc] Initial description: "GitHub内のISSUESを確認し、ISSUE#19「FE-7: KPIサマリの実データ連携と「試算値」注記の実装」を実装してください。"
- [scope] Workflow-selected scope: `feature`.
- [intent] `ideation/intent-capture/intent-statement.md`（Issue #19 要件・成功指標・配線方式・対象6ファイル・対象外明記）
- [stakeholder-map] `ideation/intent-capture/stakeholder-map.md`（ステークホルダー・意思決定者・コミュニケーション要件）
- [scope-document] `ideation/scope-definition/scope-document.md`（スコープ境界・In/Out）
- [intent-backlog] `ideation/scope-definition/intent-backlog.md`（単一 proto-Unit BU-1・依存先順）
- [market-research] `ideation/market-research/competitive-analysis.md`（競合分類・差別化・ポジショニング）
- [feasibility] `ideation/feasibility/feasibility-assessment.md`（技術成立性・リスク）
- [constraint-register] `ideation/feasibility/constraint-register.md`（TC-1〜TC-9 / OC-1〜OC-3 / RC-1）
- [team-formation] `ideation/team-formation/team-assessment.md`（ソロ + AI エージェント・キャパシティ・意思決定者）
- [wireframes] `ideation/rough-mockups/wireframes.md`（5カード構成・試算値注記・スケルトン5枚）
- [Q1] Approval & Handoff 質問ファイル `ideation/approval-handoff/approval-handoff-questions.md` の回答 A（スコープ境界確定）
- [Q2] 同 Q2 回答 A（試算値注記を「カード内の常時表示インライン短文」に確定）
- [Q3] 同 Q3 回答 A（タイムライン・体制で確定）
- [Q4] 同 Q4 回答 A（ラフモックアップをコンセプト資料として採用）
- [review] `ideation/rough-mockups/wireframes.md` の Review 節（Major 2件の扱い）
