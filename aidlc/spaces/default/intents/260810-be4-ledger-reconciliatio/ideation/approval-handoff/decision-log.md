# Decision Log — BE-4 配管台帳照合サービス

イデアーション期に下された決定の記録。

## 決定一覧

| # | 決定 | 根拠 | 出典 | ステージ |
|---|------|------|------|----------|
| D-1 | 配管台帳は軽量 JSON ファイル（`pipes.json`）で代替し、本番用大型 GIS DB はスコープ外とする | MVP 最優先・対象ファイル指定 | [desc] [Q1] | intent-capture |
| D-2 | 新規作成は 4 ファイル（pipes.json / pipe.py / ledger.py / check_ledger.py）に限定 | スコープ境界をユーザー確認で確定 | [Q1] | intent-capture |
| D-3 | BE-6 配線（`GET /api/v1/alerts/{id}` の `pipe_info`）はこの BE-4 タスク内で実施する | プレースホルダが実装待ちのため | [Q4] | intent-capture |
| D-4 | `pipe_id` は `hydrants.json` と整合する `P-001` 形式を採用する（Issue 例示 `PIPE-001` は不採用） | マスタとの突合を簡素化し変換不要 | [Q1] | approval-handoff |
| D-5 | `get_pipe_age()` の経過年数は 2026 年基準（`2026 - installed_year`）で算出する | デモ時点の実年齢を部材選定へ渡すため | [Q2] | approval-handoff |
| D-6 | 実装は TDD（Red → Green → Refactor）、カバレッジ 80% 以上を維持する | プロジェクト品質基準 | org / project | approval-handoff |

## 検討の記録

- **pipe_id 形式（P-001 vs PIPE-001）**: `hydrants.json` は HYD-001〜010 が `pipe_id: P-001〜P-010` を参照。Issue 例示は `PIPE-001`。整合する `P-001` を採用（変換不要）。→ D-4
- **経過年数基準**: 固定年（2026）を基準とする保守的な算出を選択。→ D-5

## Assumptions & Open Questions

None.
