# Decision Log — FE-7 KPIサマリの実データ連携と「試算値」注記

> イデアーションフェーズで行われた決定の記録。各ステージの質問ファイル・回答を出典とする。

## Intent Capture（イデアテーション初期）

- **DECIDED: 対象は Issue #19 記載の6ファイルのみ、バックエンド（BE-8）は変更しない**（intent-capture Q1=A）。 [intent]
- **DECIDED: KPI 配線方式は `DashboardClient` 側で `fetchKpiSummary()` をポーリングし `KpiSummary` を配下に描画（Issue 推奨方式）**（intent-capture Q2=A）。`page.tsx` は Server Component のまま維持。 [intent]
- **DECIDED: `today_detections`（本日の検知数）は KPI 表示対象外**（intent-capture Q3=A、バックエンドスキーマ上 FE-7 以降対応）。 [intent]
- **DECIDED: 成功指標は受入条件の通過**（intent-capture Q5=A、8/15 デモ完了を最優先）。 [intent]
- **DECIDED: コミュニケーション要件は「特になし」（個別 Issue ベース）**（intent-capture Q8=A）。 [intent]

## Market Research（市場調査）

- **DECIDED: 競合分析は概要のみの軽量版（網羅的な機能比較は行わない）**（market-research Q3=A）。 [market-research]
- **DECIDED: 外部 BI・可視化ツールの導入は build-vs-buy の評価対象外**（既存 Next.js/Recharts スタックとの一貫性を優先）。 [feasibility] [market-research]

## Feasibility（実現性評価）

- **DECIDED: 技術的成立（BE-8 配線・カード構成変更・単一ソース化・スケルトン表示すべて成立）**（feasibility Q1=A）。 [feasibility]
- **DECIDED: `SeverityLevel` は `0 | 1 | 2 | 3` に統一し、`lib/severity.ts` を本拠・`types/api.ts` から re-export**（feasibility Q2=X）。 [feasibility]
- **DECIDED: 規制・コンプライアンス要件は N/A**（デモ用途・PII なし・認証スコープ外、feasibility Q3=A）。 [feasibility]
- **DECIDED: タイムライン・組織制約は特になし（8/15 デモ P0 を最優先）**（feasibility Q4=A）。 [feasibility]

## Scope Definition（スコープ定義）

- **DECIDED: スコープ境界は6ファイルのみ・バックエンド変更なし**（scope-definition Q1=A、ユーザー確認済み）。 [scope-document]
- **DECIDED: バックログはすべて Must-have**（scope-definition Q2=A、単一 Issue 完結で Should-have 分離は不要）。 [scope-document] [intent-backlog]
- **DECIDED: 単一 proto-Unit（BU-1）として扱う**（scope-definition Q3=A、相互依存する6ファイルの1まとまり）。 [scope-document] [intent-backlog]
- **DECIDED: 実装順序は依存先順（型 → API クライアント → 表示）**（scope-definition Q4=A）。 [scope-document] [intent-backlog]

## Team Formation（チーム編成）

- **DECIDED: ソロ開発者 + AI-DLC エージェントで編成、外部リソース不要**（team-formation Q1=A）。 [team-formation]
- **DECIDED: モブ編成は適用しない**（team-formation Q2=A、AI-DLC のステージ構成が専門役割を担う）。 [team-formation]
- **DECIDED: スキルギャップはなし**（team-formation Q3=A、TS/React/Next.js/Tailwind/Vitest/API クライアントすべて保有）。 [team-formation]

## Rough Mockups（ラフモックアップ）

- **DECIDED: KPI カード構成は「監視センサー数 / Level 3 / Level 2 / Level 1 / 推定削減コスト」の5枚**（本日の検知数カードを削除し Level 1 を追加、rough-mockups Q1=A）。 [wireframes]
- **DECIDED: 「試算値」注記は推定削減コストカード内に表示**（rough-mockups Q2=A）。 [wireframes]
- **DECIDED: スケルトンはカードと同じ形状で5枚表示**（rough-mockups Q3=A、白画面回避）。 [wireframes]
- **DECIDED: アクセシビリティは既存パターン維持 + WCAG 2.1 AA 適合**（rough-mockups Q4=A）。 [wireframes]

## Approval & Handoff（承認・ハンドオフ）

- **DECIDED: スコープ境界（6ファイルのみ・バックエンド変更なし）をイニシアティブ・ブリーフに記載して確定**（approval-handoff Q1=A）。 [Q1]
- **DECIDED: 上流レビューの Major 2件を解決 — 「試算値」注記は「カード内の常時表示インライン短文」に確定**（approval-handoff Q2=A）。 [Q2] [review]
- **DECIDED: タイムライン（8/15 デモ P0）・体制（ソロ + AI エージェント）で確定**（approval-handoff Q3=A）。 [Q3]
- **DECIDED: ラフモックアップをイニシアティブ・ブリーフのコンセプト資料として採用**（approval-handoff Q4=A）。 [Q4]

## Assumptions & Open Questions

- その他の未確定項目はなし（None.）

## Sources

- [desc] Initial description: "GitHub内のISSUESを確認し、ISSUE#19「FE-7: KPIサマリの実データ連携と「試算値」注記の実装」を実装してください。"
- [scope] Workflow-selected scope: `feature`.
- [intent] `ideation/intent-capture/intent-statement.md`（Issue #19 要件・成功指標・配線方式）
- [market-research] `ideation/market-research/`（competitive-analysis・market-trends・build-vs-buy）
- [feasibility] `ideation/feasibility/feasibility-assessment.md`・`constraint-register.md`・`raid-log.md`
- [scope-document] `ideation/scope-definition/scope-document.md`（スコープ境界・MoSCoW）
- [intent-backlog] `ideation/scope-definition/intent-backlog.md`（単一 proto-Unit BU-1）
- [team-formation] `ideation/team-formation/team-assessment.md`・`skill-matrix.md`・`mob-composition.md`
- [wireframes] `ideation/rough-mockups/wireframes.md`・`user-flow.md`
- [Q1]-[Q4] `ideation/approval-handoff/approval-handoff-questions.md` の回答
- [review] `ideation/rough-mockups/wireframes.md` の Review 節（Major 2件）
