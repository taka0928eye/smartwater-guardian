<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
- 2026-08-11T00:00:00Z — refined-mockups:c4 学習（ランドマークは常時描画ラッパー側が一元所有）を Q2=A で確定し、US-2 AC4 の「KpiSummary に h2」を DashboardClient 側所有に読み替えて components.md / component-dependency.md に明記。
- 2026-08-11T00:00:00Z — 試算値注記のテストアサート（Minor 4）は、連結文字列の部分一致が 2 段構成 DOM と噛み合わないため、カード内スコープの順序検証（正規表現 `/試算値[\s\S]*前提: docs\/business-model\.md/`）へ変更し ADR-004 に記録。2 文字列の完全一致は維持。

## Deviations
- 2026-08-11T00:00:00Z — refined-mockups 再レビュー指摘のうち Minor 3（`[interaction-design-patterns]` タグの Sources 未掲載）は、承認済み refined-mockups 成果物を改変せず、本ステージの成果物で wireframes 参照を明記して解決（decisions.md 引き継ぎ表に記録）。
- 2026-08-11T00:00:00Z — ADR は本ステージの decisions.md 内にインライン記載（repository ルート `/docs/adr/` は設けない）。インテント単位で決定履歴を完結させる既存慣行と整合。

## Tradeoffs
- 2026-08-11T00:00:00Z — useKpiPolling 新設（Q1=A）を採用。アラートと KPI の失敗時挙動が異なる（再スケルトン vs 据え置き）ため共通化より分離を優先。ファイル 1 つ増のコストをテスト分離容易性で相殺。
- 2026-08-11T00:00:00Z — カードラベルを SEVERITY_META.label と分離（ADR-005）。ラベル定義が 2 箇所に分かれるが、承認済み表示文言の無断変更（approval-handoff:c6 に反する）を回避する方を優先。

## Open questions
- 2026-08-11T00:00:00Z — なし（None.）— Q1〜Q3 と引き継ぎ 5 件の解決方針が確定済み。functional-design でテストアサート詳細（ADR-004 の正規表現適用範囲）を具体化する。
