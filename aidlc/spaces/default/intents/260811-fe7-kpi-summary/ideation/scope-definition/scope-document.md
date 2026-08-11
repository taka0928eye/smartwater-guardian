# Scope Document — FE-7 KPIサマリの実データ連携と「試算値」注記

## スコープの目的

ダッシュボードの KPI サマリを、ハードコードされたモック値（`MOCK_KPI_DATA`）から BE-8 の実データ（`GET /api/v1/kpi/summary`）へ置き換え、「試算値」注記を常時表示します。あわせて `SeverityLevel` 型の二重定義（`types/api.ts` と `lib/severity.ts`）を解消し、バックエンド `Literal[0,1,2,3]` と整合させます。 [desc] [intent]

## In Scope（対象）

- **対象ファイル（Issue #19 記載の6ファイルのみ）**: [intent] [Q1]
  - `frontend/src/types/api.ts` — `SeverityLevel` を `lib/severity.ts` から re-export
  - `frontend/src/lib/api.ts` — `fetchKpiSummary(): Promise<KpiSummary>` を追加
  - `frontend/src/app/page.tsx` — `MOCK_KPI_DATA` 削除（Server Component のまま維持）
  - `frontend/src/components/dashboard/KpiSummary.tsx` — 実データ構成への変更（本日の検知数カード削除・レベル1カード追加）
  - `frontend/src/lib/__tests__/api.test.ts` — `fetchKpiSummary` のテスト追加
  - `frontend/src/components/dashboard/__tests__/KpiSummary.test.tsx` — 表示変更のテスト更新
- **カード構成の変更**: 「本日の検知数」カードを削除し、BE-8 が返す実データのみで構成（センサー総数・レベル1〜3別・推定削減コスト）。 [Q1] [feasibility]
- **SeverityLevel 単一ソース化**: `lib/severity.ts` の `0 | 1 | 2 | 3` を本拠とし、`types/api.ts` から re-export（陳腐化コメントの更新を含む）。 [Q1] [feasibility]
- **「試算値」注記**: KPI カードに「試算値（前提: `docs/business-model.md`）」を常時表示。 [intent] [feasibility]
- **スケルトン表示**: バックエンド停止中は白画面にせずスケルトン表示にフォールバック。 [intent] [feasibility]
- **配線方式**: `DashboardClient` 側で `fetchKpiSummary()` をポーリングし、`KpiSummary` をその配下で描画。`page.tsx` は Server Component のまま。 [intent]

## Out of Scope（対象外）

- **バックエンド（BE-8）の変更**: `GET /api/v1/kpi/summary` の実装・スキーマ変更はしない。 [intent] [feasibility]
- **`today_detections`（本日の検知数）**: バックエンドスキーマ上 FE-7 以降の対応。カード削除により表示しない。 [intent] [feasibility]
- **認証・権限管理 / リアルタイム通知 / 本番用大型 GIS DB**: CLAUDE.md のスコープ外事項。 [intent]
- **外部 BI・可視化ツールの導入**: 既存 Next.js / Recharts スタックとの一貫性を優先（build-vs-buy 評価対象外）。 [intent] [market-research]
- **AWS / クラウドインフラ**: 本スコープで変更なし（ローカル FastAPI + Next.js）。 [feasibility]
- **規制・コンプライアンス対応**: デモ用途・機微データなしで N/A。 [feasibility] [Q]

## スコープ境界の根拠

- **Issue #19 のファイル指定**: 対象は6ファイルのみで、バックエンドは変更しない（ユーザー確認済み）。 [intent] [Q1]
- **Feasibility での技術確認**: 成立性・カード構成・単一ソース化・コンプラ N/A を確定。 [feasibility]
- **8/15 デモ完了（P0）**: タイムライン制約に合わせシンプルな実装を選択。 [intent]

## Assumptions & Open Questions

- バックログはすべて Must-have で、単一 proto-Unit として扱う。 [Q2] [Q3]
- 実装順序は依存先順（型 → APIクライアント → 表示）。 [Q4]
- その他の未確定項目はなし（None.）

## Sources

- [desc] Initial description: "GitHub内のISSUESを確認し、ISSUE#19「FE-7: KPIサマリの実データ連携と「試算値」注記の実装」を実装してください。"
- [scope] Workflow-selected scope: `feature`.
- [intent] `ideation/intent-capture/intent-statement.md`（Issue #19 要件・配線方式・成功指標）
- [feasibility] `ideation/feasibility/feasibility-assessment.md`・`constraint-register.md`・`raid-log.md`
- [market-research] `ideation/market-research/build-vs-buy.md`
- [Q1] Scope Definition 質問ファイル `ideation/scope-definition/scope-definition-questions.md` の回答 A
- [Q2] 同 Q2 回答 A（すべて Must-have）
- [Q3] 同 Q3 回答 A（単一 proto-Unit）
- [Q4] 同 Q4 回答 A（依存先順）
