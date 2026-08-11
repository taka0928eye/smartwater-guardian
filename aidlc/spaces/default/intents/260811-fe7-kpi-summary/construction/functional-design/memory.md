<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-08-11T09:30:00Z — Q1（useKpiPolling シグネチャ）の権威を unit-of-work §2.2 とし、component-methods.md §2.1（`useKpiPolling()` 入力なし）は陳腐化として引き継ぎ対象に留めた。Application Design レビュアー Major 1（循環依存）の解消策が正しく引き継がれ、`DashboardClient ↔ useKpiPolling` の循環は解消された。
- 2026-08-11T09:30:00Z — Q2 は「失敗時点で即 isLoading=true（再スケルトン）→ 次回成功時に kpiData 更新 + カード復帰」を採択。FR-8「古い値を最新として見せない」を厳密に充足し、既存 useAlertPolling（据え置き）とは挙動を分離した（application-design:c5 学習と整合）。

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-08-11T09:30:00Z — frontend-components.md は optional_produces だが、unit kind `ui` により produces_kinds で適用と判定し作成した（business-rules.md / domain-entities.md は kind `ui` 非適用のため未作成）。ステージ定義の produces_kinds フィルタに従った意図的な取捨。
- 2026-08-11T09:30:00Z — 成果物に Review セクションを仮置きしないこととした。実際のレビュアー審査（aidlc-architecture-reviewer-agent ディスパッチ）後に、その審査結果で Review セクションを追記する方式に統一した。

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-08-11T09:30:00Z — Q3 は Minimal 戦略の 3 シナリオ（ハッピーパス / 失敗パス / アンマウント時クリーンアップ）を採択し、初回ポーリング前・連続失敗等のエッジケース詳細化（B 案）は build-and-test へ委ねた。FR-7/FR-8 の検証に必要な最小網羅を優先した。

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-08-11T09:36:56Z — レビュアー Minor の引き継ぎ事項: ①試算値注記の DOM 構造（span 独立要素 vs interaction-spec の「推定削減コスト · 試算値」併記）の権威確定、②h2 文言「KPIサマリ」のスペース有無（完全一致アサートに影響）、③NFR-1 カバレッジゲート恒久化（vitest.config.mts thresholds）の実現手段を build-and-test で確定、④useKpiPolling の配置パス（frontend/src/hooks/useKpiPolling.ts）を code-generation で固定。
