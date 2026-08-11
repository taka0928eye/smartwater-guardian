<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
- 2026-08-11T10:45:00Z — CI Pipeline ステージは CONDITIONAL 実行。既存 `.github/workflows/ci.yml`（GitHub Actions）が frontend の NFR-1（`npm run test` + vitest.config.mts thresholds 単一ソース化）は反映済みだが、backend の確定品質ゲート（Q4: `--cov-branch` 行+branch 各 80% / Q6: ruff+mypy 導入）が未反映のため「有意な変更が必要」と判断して実行した。
- 2026-08-11T10:45:00Z — 質問は実決定が必要な 1 問（Q4: backend 品質ゲートの CI 反映範囲）のみ提示し、CI ツール（GitHub Actions）・ブランチ（main 直コミット）・成果物リポジトリ（なし）は既存実態からリード導出で確定（approval-handoff:c2 / requirements-analysis:c1 と整合）。
- 2026-08-11T10:45:00Z — ユーザーは Q4 で「C. Q4 + Q6 反映」を選択。backend に ruff+mypy を導入し CI に反映する方針が確定。

## Deviations
- 2026-08-11T10:45:00Z — `ruff format` は今回導入しない。既存 8 ファイルを再整形すると大量 diff が発生し、BU-1（フロントのみ）のスコープを超えるため。lint（`ruff check`）のみ CI ゲート化し、format 導入は backend 側の別 Issue で検討する旨を quality-gates.md に明記。
- 2026-08-11T10:45:00Z — mypy の対象は実稼働コード `app/` + `main.py` に限定。検証スクリプト `scripts/`（check_ledger.py 等）は `expect()` パターンで型ガードにならないため対象外とし、quality-gates.md に明記。

## Tradeoffs
- 2026-08-11T10:45:00Z — 「文書化のみ（A）」「Q4 のみ（B）」「Q4 + Q6（C）」の選択肢を提示し、ユーザーが C を選択。C は backend の ruff/mypy 導入（pyproject.toml / requirements-dev.txt 作成・依存追加・コード微修正）を伴う追加投資だが、practices-discovery で確定済みの Q6 を CI に反映できる。
- 2026-08-11T10:45:00Z — ruff は `app/` `main.py` `scripts/` を対象に `--fix` で 15 件自動修正（import 整理・noqa 除去・ソート）。sensors.py の mypy エラー（`STATUS_BY_SEVERITY: dict[int, str]` → `SensorStatus` Literal 型）は動作不変の型注釈で解消。mypy の python_version は numpy の stubs が 3.12 要求のため CI（Python 3.12）に合わせ 3.12 に設定。

## Open questions
- None.
- 2026-08-11T10:45:00Z — 実測検証: ruff `All checks passed` / mypy `Success: no issues found in 18 source files` / pytest `--cov-branch` 132 passed 99.60%（行+branch 各 80% ゲート充足）。frontend は build-and-test 実測（4 指標 80% 超）を参照。CI 設定の実装は完了し、ローカル実行とゲートが一致。
