# Feasibility & Constraints — Stage Diary

> ステージ観測日誌。ステージ実行中に随時追記する（実行後に手編集しない）。

## Interpretations

- 2026-08-11T06:30:00Z — Q1（本日の検知数カード）で「カード削除」を選択。BE-8 スキーマに `today_detections` が無く、intent-capture でも「FE-7 以降対応」と明記されていたため、モック廃止と同時にカードを削除するのが最も整合的。;
- 2026-08-11T06:30:00Z — Q2 は「X. Other」で「`0 | 1 | 2 | 3` に統一」と回答。単一ソース化の「方向」（lib/severity.ts を本拠にする）は Issue #19 指定を根拠に確定した。値の統一先（`0|1|2|3`）と本拠ファイル（`lib/severity.ts`）を区別して記録。;
- 2026-08-11T06:30:00Z — Q3（規制・コンプライアンス）は N/A。デモ評価者向け内部機能・PIIなし・認証は CLAUDE.md スコープ外という intent-capture の前提を裏付け。;

## Deviations

- 2026-08-11T06:30:00Z — ステージファイルは AWS ランドスケープ・規制スキャンを含むが、本件はフロントのみ・BE-8 実装済みのため、AWS サービス利用は皆無として AWS プラットフォーム視点は N/A 扱い（RAID・制約レジスタに AWS 関連の依存なしと明記）。質問は実決定に必要な4問に絞った（project.md#Corrections: approval-handoff:c2）。;

## Tradeoffs

- 2026-08-11T06:30:00Z — KPI カード構成: 「本日の検知数」カード削除 vs プレースホルダ表示。削除を選択（実データ不在で誤値を防ぎ、モック残し0件を達成）。レベル1カードは BE-8 が返すため追加し、5カード構成（総数・レベル1〜3・削減コスト）に揃える。;
- 2026-08-11T06:30:00Z — SeverityLevel 単一ソース化: `lib/severity.ts` を本拠（Issue 指定・表示メタと同居）vs `types/api.ts` を本拠。Issue 指定と intent-statement 成功指標（「`lib/severity.ts` の `0 | 1 | 2 | 3`」）に従い前者を採用。;

## Open questions

- 2026-08-11T06:30:00Z — 「試算値」注記の表示内容・位置の詳細は Refined Mockups / Application Design で具体化する（現時点では「常時表示」要件のみ確定）。;
