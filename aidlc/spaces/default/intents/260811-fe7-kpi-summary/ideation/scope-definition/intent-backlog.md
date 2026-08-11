# Intent Backlog — FE-7 KPIサマリの実データ連携と「試算値」注記

## バックログ方針

Issue #19 は単一イニシアティブで、6ファイルが相互に依存する1まとまりの変更です。Q3 の決定により **単一 proto-Unit** として扱います。 [Q3]

## proto-Unit 一覧

### BU-1: FE-7 KPI サマリの実データ連携と「試算値」注記

| 項目 | 内容 |
|---|---|
| **優先度** | Must-have（Q2=A: 受入条件をすべて満たす） [Q2] |
| **実装順序** | 依存先順（型 → APIクライアント → 表示、Q4=A） [Q4] |
| **対象ファイル** | `frontend/src/types/api.ts`・`frontend/src/lib/api.ts`・`frontend/src/app/page.tsx`・`frontend/src/components/dashboard/KpiSummary.tsx`・`frontend/src/lib/__tests__/api.test.ts`・`frontend/src/components/dashboard/__tests__/KpiSummary.test.tsx`（6ファイル） [intent] [Q1] |
| **変更内容** | ① `SeverityLevel` 単一ソース化（`lib/severity.ts` 本拠・`types/api.ts` から re-export） ② `fetchKpiSummary()` 追加 ③ `MOCK_KPI_DATA` 削除 ④ カード構成変更（本日の検知数削除・レベル1追加） ⑤ 試算値注記 ⑥ スケルトン表示 [intent] [feasibility] |
| **受入条件** | `MOCK_KPI_DATA` 削除・KPIハードコード0件 / `SeverityLevel` 1箇所のみ / 試算値注記の常時表示 / スケルトン表示 / `'use client'` なし・`any` なし / build・lint・test 成功・カバレッジ80% [intent] |
| **依存** | BE-8 `GET /api/v1/kpi/summary`（実装済み）・既存 `lib/api.ts` ヘルパー [intent] [feasibility] |
| **見積** | 小（フロントのみ・BE-8 実装済み） [feasibility] |

## MoSCoW 分類

| 分類 | 対象 |
|---|---|
| **Must-have** | BU-1 全要素（型単一ソース化・fetchKpiSummary・MOCK削除・カード構成変更・試算値注記・スケルトン表示） |
| **Should-have** | なし（単一 Issue 完結） |
| **Could-have** | なし |
| **Won't-have** | `today_detections` 表示・バックエンド変更・外部BI導入・AWSインフラ |

## バリューストリーム

<!-- テキストフォールバック: 型統一 → APIクライアント実データ取得 → ダッシュボードKPI表示（試算値注記付き）→ 評価者確認 -->
```
[lib/severity.ts] ---> [types/api.ts] ---> [lib/api.ts fetchKpiSummary]
                                              |
                                              v
                              [DashboardClient ポーリング] ---> [KpiSummary 表示]
                                                                    |
                                                                    v
                                                  [試算値注記 + スケルトン fallback] ---> [8/15 デモ評価]
```

## Assumptions & Open Questions

- その他の未確定項目はなし（None.）

## Sources

- [desc] Initial description: "GitHub内のISSUESを確認し、ISSUE#19「FE-7: KPIサマリの実データ連携と「試算値」注記の実装」を実装してください。"
- [scope] Workflow-selected scope: `feature`.
- [intent] `ideation/intent-capture/intent-statement.md`（Issue #19 要件・配線方式・成功指標）
- [feasibility] `ideation/feasibility/feasibility-assessment.md`・`constraint-register.md`・`raid-log.md`
- [Q1] Scope Definition 質問ファイル `ideation/scope-definition/scope-definition-questions.md` の回答 A（スコープ境界確定）
- [Q2] 同 Q2 回答 A（すべて Must-have）
- [Q3] 同 Q3 回答 A（単一 proto-Unit）
- [Q4] 同 Q4 回答 A（依存先順）
