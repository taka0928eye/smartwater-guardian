<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-08-11T00:12:00Z — 単一イテレーションのダイレクティブで unit-of-work が存在しないため、`{unit-name}` を `be4-ledger` に解決して記録パスを決定
- 2026-08-11T00:12:00Z — 「モジュールロード時のキャッシュ」は store.py の `@lru_cache(maxsize=1)` 先例に合わせ、初回呼び出し時に読み込んで以後キャッシュする設計と解釈（「リクエスト毎の再読み込みをしない」要件を満たし、テスト分離も壊さない）

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-08-11T00:12:00Z — store.py は欠損を RuntimeError で包むが、BE-4 受け入れ条件は FileNotFoundError / ValueError の明示指定のため、ledger.py はそのまま伝播・変換する

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-08-11T00:12:00Z — find_nearest_pipe は路線の LineString 頂点との Haversine 最小距離で判定（路線全体の中心点方式より、消火栓位置に近い頂点を考慮でき直感的）

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->

