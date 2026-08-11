<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
- 2026-08-11T09:12:38Z — ユニット名は上流 stories.md が命名した **BU-1** をそのまま踏襲した（uppercase を含む安全なレガシー単一セグメント名としてランタイムが保持）。改めて小文字化（bu-1）すると上流トレーサビリティが切れるため、stage ファイルの「in-flight legacy Unit を改名しない」指針に従った。
- 2026-08-11T09:12:38Z — 実装順序（型 → APIクライアント → 表示 → 状態遷移 → 設定）は**ユニット内部の手順**として unit-of-work-story-map.md に記録した。DAG 上の順序付け（Bolt 順序）は 2.8 Delivery Planning の責務であるため、story-map 内に「2.8 の決定を侵さない」注記を添えた。

## Deviations
- 2026-08-11T09:12:38Z — stage ファイル Step 5「Get Plan Approval」は、質問フロー末尾の Consolidated Summary Confirmation（Q1〜Q3 の統合サマリ確認）で兼ねた。Q1/Q2/Q3 すべて A（単一ユニット・依存なし・monolithic deploy）で確定済みのため、別途の計画承認は重複と判断。

## Tradeoffs
- 2026-08-11T09:12:38Z — 単一ユニット（BU-1）を選択。レイヤー分割（契約/表示/設定）やストーリー分割は Bolt 分割・並行開発の余地を生むが、13 ファイルが相互依存し 1 Issue 完結のため分割の利益が小さい（scope-definition:c1 学習）。分割コスト（DAG 管理・Bolt 境界調整）を回避する方を優先。

## Open questions
- 2026-08-11T09:12:38Z — なし（None.）— Q1〜Q3 と Application Design レビュアー指摘（Major 1 / Minor 2〜4）の解決方針が確定済み。functional-design でテストアサート詳細（ADR-004 正規表現・fixture 7 フィールド固定）を具体化する。
