# Team Availability Assessment — FE-7 KPIサマリの実データ連携と「試算値」注記

## チーム構成

本イニシアティブは **ソロ開発者（ユーザー） + AI-DLC エージェント（各ステージのペルソナ）** で編成します。Q1=A で外部リソース不要を確定。 [Q1]

| リソース | 役割 | 備考 |
|---|---|---|
| ユーザー（開発者） | 実装・レビュー・承認 | 最終意思決定者。8/15 デモ完了（P0）が最優先 [intent] |
| AI-DLC ペルソナ群 | 各ステージのリード役割 | product / delivery / architect / developer / quality 等。ステージ進行に応じて1人ずつ起動 [Q2] |

## キャパシティ

- ソロ開発者1名で、変更対象はフロントエンド6ファイル（`types/api.ts`・`lib/api.ts`・`page.tsx`・`KpiSummary.tsx`・`api.test.ts`・`KpiSummary.test.tsx`）。 [intent]
- 見積は「小」（フロントのみ・BE-8 実装済み）。 [feasibility]
- 競合イニシアティブなし。本ワークフローが唯一のアクティブ案件。 [Q1]
- タイムライン制約: 8/15 デモ完了（P0）。残り期間と作業量の整合は取れている。 [intent]

## 外部リソース

- 外部パートナー・契約リソース・AWS Professional Services は **不要**（Q1=A）。 [Q1]

## 意思決定者とエスカレーション

- 全ステージの承認ゲートでユーザーが最終承認。 [intent] [scope]
- 技術的判断（型統一・配線方式等）は各ステージのリードエージェントが案を提示し、ユーザーが確定。 [Q2]
- エスカレーション経路は単純（ユーザー1名）のため、明確な経路は不要。 [Q1]

## Assumptions & Open Questions

- その他の未確定項目はなし（None.）

## Sources

- [desc] Initial description: "GitHub内のISSUESを確認し、ISSUE#19「FE-7: KPIサマリの実データ連携と「試算値」注記の実装」を実装してください。"
- [scope] Workflow-selected scope: `feature`.
- [intent] `ideation/intent-capture/intent-statement.md`（対象6ファイル・8/15 デモ完了・配線方式）
- [feasibility] `ideation/feasibility/feasibility-assessment.md`（技術的成立・チームは同スタック実績あり）
- [Q1] Team Formation 質問ファイル `ideation/team-formation/team-formation-questions.md` の回答 A（ソロ + AIエージェントで確定）
- [Q2] 同 Q2 回答 A（モブ編成は適用しない）
- [scope] `ideation/scope-definition/scope-document.md`・`intent-backlog.md`（スコープ境界・単一 proto-Unit）
