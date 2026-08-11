# Feasibility Assessment — FE-7 KPIサマリの実データ連携と「試算値」注記

## 目的と方法

本評価は、前段のイニシアティブ・ステートメント（`ideation/intent-capture/intent-statement.md`）で確定した FE-7（KPI サマリの実データ連携と「試算値」注記）の技術的成立性・リスクを、アーキテクト視点で評価するものです。 [intent]

対象スコープは Issue #19 記載のフロントエンド6ファイルのみで、バックエンド（BE-8 実装済み）は変更しません。 [intent] [Q1]

## 技術的成立性の結論

**成立する。** 本イニシアティブは既存のバックエンド API（BE-8 `GET /api/v1/kpi/summary`）へのフロント配線と、`SeverityLevel` 型の重複解消という、リスクの低い内部変更です。 [intent] [Q1] [Q2]

| 評価項目 | 判断 | 根拠 |
|---|---|---|
| BE-8 との配線（`fetchKpiSummary()` 追加） | 成立 | `lib/api.ts` の既存 `fetchSensors` / `fetchAlerts` と同じ snake_case→camelCase 変換パターン（`unwrap` / `toCamelCase`）で実装可能 [intent] |
| KPI 表示の実データ化 | 成立 | モック `MOCK_KPI_DATA` を廃止し、`GET /api/v1/kpi/summary` の実データへ置換 [intent] |
| 「本日の検知数」カード | 対象外 | BE-8 スキーマに `today_detections` が無く（FE-7 以降で対応）、Q1 でカード削除を確定 [intent] [Q1] |
| レベル1カードの追加 | 成立 | BE-8 が `level1_count` を返すため、センサー総数・レベル1〜3別・推定削減コストの構成に揃える [intent] [Q1] |
| `SeverityLevel` 単一ソース化 | 成立 | 現状 `types/api.ts` と `lib/severity.ts` に同一の `0 \| 1 \| 2 \| 3` が重複定義。`lib/severity.ts` を本拠とし `types/api.ts` から re-export する [intent] [Q2] |
| バックエンド停止時の動作 | 成立 | スケルトン表示（白画面回避）を既存のポーリング失敗時と同様にハンドリング [intent] |
| `page.tsx` の Server Component 維持 | 成立 | KPI 取得は DashboardClient（Client Component）側で実施し、`page.tsx` に `'use client'` を付けない [intent] |

## 技術リスク分析

- **SeverityLevel の依存方向**: `types/api.ts`（API 契約層）が `lib/severity.ts`（UI ユーティリティ層）に依存する方向になる。`lib/severity.ts` は `types/api.ts` に依存しないため循環 import は発生しない。 `SEVERITY_META` 等の表示メタと型を同居させることで一貫性が保てる。 [Q2] [intent]
- **スキーマ差分**: BE-8 の `KpiSummary` は `is_estimate` / `assumption_doc` を持ち、フロントの `KpiData` は現状これらを持たない。試算値注記（「試算値（前提: `docs/business-model.md`）」）を常時表示する要件は `is_estimate` に依存せず定常表示で満たせるため、型は後方互換を保ちつつ追加可能。 [intent]
- **カバレッジ**: 変更6ファイルのうちテスト対象（`lib/api.ts` の `fetchKpiSummary`・`KpiSummary.tsx` の表示ロジック）は既存テストパターン（vitest + axios spy）で80%以上を維持可能。 [intent]
- **`any` 禁止**: 型変換は既存の `toCamelCase` / `unwrap` ヘルパーを流用するため `any` は不要。 [intent]

## 開発スキル・体制の適合性

- 変更範囲はフロントエンドのみ（Next.js / TS / Tailwind / Vitest）で、チームは FE-1〜FE-6 で同スタックの実績あり。 [intent]
- バックエンドは変更対象外のため Python / FastAPI の追加作業は不要。 [intent]

## 結論と推奨

**実装を推奨する。** 技術的障壁・未解決リスクはなく、8/15 デモ完了（P0）に間に合う作業量です。実装時は下記を遵守する。 [intent] [Q4]

- `lib/severity.ts` を `SeverityLevel` の単一ソースとし、`types/api.ts` から re-export（`0 | 1 | 2 | 3` に統一、陳腐化コメントの更新を含む）。 [Q2]
- 「本日の検知数」カードを削除し、センサー総数・レベル1〜3別・推定削減コストのカード構成に変更。 [Q1]
- `fetchKpiSummary(): Promise<KpiSummary>` を `lib/api.ts` に追加し、DashboardClient 側でポーリング。 [intent]

## Assumptions & Open Questions

- 単一ソース化の方向は Issue #19 の指定（`lib/severity.ts` を本拠・`types/api.ts` から re-export）に従う。 [Q2] [intent]
- その他の未確定項目はなし（None.）

## Sources

- [desc] Initial description: "GitHub内のISSUESを確認し、ISSUE#19「FE-7: KPIサマリの実データ連携と「試算値」注記の実装」を実装してください。"
- [scope] Workflow-selected scope: `feature`.
- [intent] `ideation/intent-capture/intent-statement.md`（Issue #19 要件・配線方式・成功指標・対象外明記）
- [Q1] Feasibility 質問ファイル `ideation/feasibility/feasibility-questions.md` の回答 A（本日の検知数カード削除）
- [Q2] 同 Q2 回答 X（`0 | 1 | 2 | 3` に統一）
- [Q4] 同 Q4 回答 A（タイムライン・組織制約なし）
- [competitive-analysis] `ideation/market-research/competitive-analysis.md`（市場コンテキスト — 表示方針への直接影響なし）
- [market-trends] `ideation/market-research/market-trends.md`（市場トレンド — 同上）
- [build-vs-buy] `ideation/market-research/build-vs-buy.md`（build 確定 — 配線は既存スタックで実装）
