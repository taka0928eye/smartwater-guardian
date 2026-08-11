# Skill Matrix — FE-7 KPIサマリの実データ連携と「試算値」注記

## 必要スキル vs 保有スキル

| 必要スキル | 必要度 | 保有状況 | ギャップ | 根拠 |
|---|---|---|---|---|
| TypeScript / React / Next.js（App Router） | 高 | 保有（FE-1〜FE-6 で実績） | なし | [feasibility] |
| Tailwind CSS | 中 | 保有（ダッシュボード UI 実績） | なし | [feasibility] |
| Vitest（ユニットテスト・axios spy） | 高 | 保有（`api.test.ts`・`KpiSummary.test.tsx` 実績） | なし | [feasibility] |
| API クライアント設計（snake_case→camelCase 変換） | 中 | 保有（`lib/api.ts` の `unwrap` / `toCamelCase` 実績） | なし | [feasibility] |
| バックエンド（Python / FastAPI） | 不要 | — | なし（変更対象外） | [intent] |
| AWS / インフラ | 不要 | — | なし（本スコープで変更なし） | [feasibility] |

## ギャップ分析

Q3=A により **スキルギャップなし** を確定。追加の育成・外部調達は不要。 [Q3]

- 型の単一ソース化は既存の型定義（`types/api.ts`・`lib/severity.ts`）の再編成のみで、新技術は不要。 [feasibility]
- 試算値注記・スケルトン表示は既存の Tailwind / コンポーネントパターンで実装可能。 [feasibility]

## スキルギャップ改善計画

- 対象外（ギャップなしのため計画不要）。 [Q3]

## オンボーディングチェックリスト

- 対象外（新規メンバーなしのため不要）。 [Q1]

## Assumptions & Open Questions

- その他の未確定項目はなし（None.）

## Sources

- [desc] Initial description: "GitHub内のISSUESを確認し、ISSUE#19「FE-7: KPIサマリの実データ連携と「試算値」注記の実装」を実装してください。"
- [scope] Workflow-selected scope: `feature`.
- [intent] `ideation/intent-capture/intent-statement.md`（対象6ファイル・バックエンド変更対象外）
- [feasibility] `ideation/feasibility/feasibility-assessment.md`（同スタック実績・`unwrap`/`toCamelCase` 流用）
- [Q1] Team Formation 質問ファイル `ideation/team-formation/team-formation-questions.md` の回答 A（ソロ + AIエージェントで確定）
- [Q3] 同 Q3 回答 A（スキルギャップなし）
