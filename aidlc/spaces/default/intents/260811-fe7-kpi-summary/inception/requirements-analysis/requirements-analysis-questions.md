# Requirements Analysis — 明確化質問

> FE-7「KPIサマリの実データ連携と「試算値」注記の実装」の要件明確化質問。
> 上流成果物（intent-statement / scope-document / practices-discovery / Issue #19）で
> 決定済みの事項は省略し、要件記述の前提となる実決定のみを質問する（project.md 学習
> approval-handoff:c2 と整合）。

## 前提確認

1. **SeverityLevel の二重定義解消の扱い** — Issue #19 は「`types/api.ts` の `SeverityLevel` は
   `1 | 2 | 3`（Level 0 を表現できない）」という前提で修正を求めているが、**現状コード
   `frontend/src/types/api.ts:16` は既に `0 | 1 | 2 | 3` を定義済み**（FE-5 commit 69da0ff で解消済み）。
   `lib/severity.ts` も `0 | 1 | 2 | 3` であり、値集合は両ファイル一致している。よって残る作業は
   「`lib/severity.ts` を単一ソースとし `types/api.ts` から re-export する二重定義解消」のみと解釈するが、
   この前提で要件化してよいか？

- A. その解釈で確定（現状の `0 | 1 | 2 | 3` を維持し、単一ソース化 + re-export のみ実施。
  前提ズレ（Issue の「1|2|3」記述が陳腐化）は要件に注記する）
- B. 値集合自体の見直しも必要（例: Level 0 の扱いを再検討し `SeverityLevel` の定義を変更）
- C. その他
- X. Other (please specify)

[Answer]: A

## 表示要件

2. **「試算値」注記の表示ソース** — Issue #19 の受入条件は注記「試算値（前提: `docs/business-model.md`）」
   を常時表示すること。一方バックエンド `KpiSummary` は `assumption_doc: "docs/business-model.md §3"` と
   `is_estimate: true` を返す。注記の文言はどちらを表示するか？

- A. 固定リテラル「試算値（前提: `docs/business-model.md`）」を常時表示（受入条件・
  intent-statement 成功指標どおり）
- B. バックエンドの `assumption_doc` 値（例: `docs/business-model.md §3`）を動的表示
  （単一ソースだが受入条件の文言例と厳密には異なる）
- C. `is_estimate` フラグで表示/非表示を切替（現状 BE-8 は常に true のため実質常時表示。
  将来フラグが false になり得る場合に備える）
- X. Other (please specify)

[Answer]: A

3. **KPI のポーリング周期** — `DashboardClient` で `fetchKpiSummary` をポーリングして取得する。
   周期はどうするか？（既存 `useAlertPolling` は 5000ms でポーリング中）

- A. アラートと同じ 5 秒（既存のポーリング方式に統一し実装を単純化）
- B. 別周期で分離（例: 30 秒。更新頻度はアラートより低くてよい）
- C. ポーリングせずマウント時に 1 回のみ取得
- X. Other (please specify)

[Answer]: A

## 失敗時挙動

4. **KPI 取得失敗時・再取得成功までのカード表示** — 受入条件は「バックエンド停止中はスケルトン表示、
   古い値を最新として見せない」こと。具体的な表示方針はどうするか？

- A. KPI カード群をすべてスケルトン表示に切替え、取得成功まで更新しない
  （古い値を最新として見せない要件を厳密に守る）
- B. 最終成功値を表示しつつ更新失敗の注記を併記
  （「古い値を最新として見せない」要件と矛盾するため非推奨）
- X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

**回答の統合サマリ**:

- Q1: `SeverityLevel` は二重定義解消のみ実施（現状の `0 | 1 | 2 | 3` を維持し、`lib/severity.ts` を単一ソースとし `types/api.ts` から re-export。Issue の「1|2|3」記述の陳腐化は要件に注記）
- Q2: 「試算値」注記は固定リテラル「試算値（前提: `docs/business-model.md`）」を常時表示（受入条件どおり）
- Q3: KPI のポーリング周期はアラートと同じ 5 秒（既存 `useAlertPolling` に統一）
- Q4: KPI 取得失敗時はカード群をすべてスケルトン表示に切替え、取得成功まで更新しない（古い値を最新として見せない）

この内容で要件成果物を生成してよいか？

- Looks correct
- Request changes

[Answer]: Looks correct
