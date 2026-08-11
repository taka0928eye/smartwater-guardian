# Scope Definition & Constraints — Stage Diary

> ステージ観測日誌。ステージ実行中に随時追記する（実行後に手編集しない）。

## Interpretations

- 2026-08-11T07:00:00Z — バックログ単位（proto-Unit）は Q3=A で単一 Unit に確定。Issue #19 は6ファイルが相互依存する1まとまりの変更で、分割より1実装単位の方がスコープ管理・受入条件検証が容易。;
- 2026-08-11T07:00:00Z — 実装順序は Q4=A で依存先順（型 → APIクライアント → 表示）。TDD（Red→Green）と整合する順序で、テストも型→API→表示の順に追加できる。;

## Deviations

- 2026-08-11T07:00:00Z — ステージファイルの Step 5 は「value stream map」の生成を含むが、単一 Unit のためバリューストリームは簡潔なフローチャート（テキストフォールバック付き）として intent-backlog 内に内包した。独立した value-stream.md は作成しない（単一 Unit では過剰）。;

## Tradeoffs

- 2026-08-11T07:00:00Z — カード構成: 本日の検知数カード削除（実データ不在・誤値防止）vs プレースホルダ表示。Feasibility Q1=A と一貫し、削除を採用。;
- 2026-08-11T07:00:00Z — MoSCoW: すべて Must-have（単一 Issue 完結・受入条件全満たし）を採用。Should-have 分離は Issue の受入条件が全て必須のため不要。;

## Open questions

- 2026-08-11T07:00:00Z — 「試算値」注記の具体的な表示位置・文言は Refined Mockups で具体化する。;
