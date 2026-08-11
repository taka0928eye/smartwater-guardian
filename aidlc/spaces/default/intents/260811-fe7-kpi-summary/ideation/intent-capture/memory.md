<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
- 2026-08-11T05:12:58Z — スコープ境界は Issue #19 記載の6ファイルのみと解釈（`[memory:M1]` の「対象ファイル・配線範囲はユーザー確認で確定」に従い Q1 で確認済み）; バックエンド BE-8 は実装済みで変更対象外。
- 2026-08-11T05:12:58Z — KPI 配線は Issue 推奨の「DashboardClient で fetchKpiSummary をポーリングし KpiSummary を配下に描画」を Q2 で確認。page.tsx は Server Component のまま維持。
- 2026-08-11T05:12:58Z — `today_detections` はバックエンドスキーマ上 FE-7 以降の対応とされているため本件対象外と明記。

## Deviations

## Tradeoffs
- 2026-08-11T05:12:58Z — Q2 の配線方式は A（DashboardClient ポーリング）を採用。B（Server 側1回 fetch）の方が実装は単純だが、アラートと KPI の更新タイミングを揃える Issue 推奨を優先した。

## Open questions

