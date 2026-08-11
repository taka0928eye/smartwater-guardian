# Initiative Brief — BE-4 配管台帳照合サービス

## イニシアティブ概要

- **名称**: BE-4 配管台帳照合サービス（ledger.py）
- **種別**: FR-3 の前段サービス。センサー位置（消火栓）から該当する水道管路（材質・口径・布設年等）を引き当て、BE-5（補修部材選定）に必要な入力を揃える。
- **発端**: GitHub Issue「BE-4: 配管台帳照合サービス（ledger.py）」。BE-6 アラート詳細 API の `pipe_info` プレースホルダが実装待ち。 [desc]

## 問題定義

消火栓マスタ（`hydrants.json`）しか存在せず、対象管路の属性（材質・口径・布設年）を照合する手段がない。軽量な JSON ファイルで配管台帳を代替し、照合ロジックを提供する。 [desc] [Q2]

## スコープ境界（ユーザー確認済み）

- **新規作成（4ファイル）**:
  - `backend/app/data/pipes.json` — 配管台帳 10 路線
  - `backend/app/schemas/pipe.py` — `PipeRecord` Pydantic v2 スキーマ
  - `backend/app/services/ledger.py` — 照合ロジック & キャッシュ & ヘルパー
  - `backend/scripts/check_ledger.py` — 動作検証スクリプト
- **配線**: `GET /api/v1/alerts/{id}` への配管情報（`pipe_info`）を BE-4 内で実装。 [Q1] [Q4]

## 成功指標（受け入れ条件）

1. `hydrants.json` の全 10 件の消火栓が `find_pipe_by_hydrant()` で配管データに解決される（`None` が返らない）。
2. 未知の `hydrant_id` は `None` を返す（エラーにしない）。
3. `find_nearest_pipe(lat, lng)` が最近傍の配管を正しく返す。
4. `pipes.json` 欠損/破損時に明確な例外（FileNotFoundError / ValueError）で失敗し、サイレント失敗しない。
5. `GET /api/v1/alerts/{id}` レスポンスに材質・口径・布設年・経過年数が含まれる。
6. JSON はリクエストごとに再読み込みせずモジュールキャッシュ。
7. `python scripts/check_ledger.py` が全検証成功。

## 本ステージで確定した決定

- **pipe_id 形式**: `P-001` 形式（`hydrants.json` の参照と整合）。Issue 例示の `PIPE-001` は採用しない。 [Q1]
- **経過年数基準**: 2026年基準（`2026 - installed_year`）。 [Q2]

## 技術・実装方針

- **Tech Stack**: Python 3.11+ / Pydantic v2 / FastAPI（既存スタックに準拠）。
- **照合方式**: 消火栓マスタの `pipe_id` 参照による直接解決 + Haversine 距離による最近傍照合。
- **キャッシュ**: モジュールロード時の `@lru_cache(maxsize=1)`（既存 `store.py` の `get_hydrants()` パターンに準拠）。
- **TDD**: Red → Green → Refactor を厳格に順守。カバレッジ 80% 以上。

## リスク

| リスク | 深刻度 | 対処 |
|--------|--------|------|
| `hydrants.json` の pipe_id 参照（P-001）と Issue 例示（PIPE-001）の形式差 | 低 | ユーザー確認済み：`P-001` 形式を採用（Q1） |
| `pipes.json` の座標/属性データの不整合 | 低 | `check_ledger.py` と Pydantic v2 バリデーションで検出 |

## チーム計画

- AI 主導の単一配信ユニットで進行。コード生成ステージで TDD に沿って実装し、ビルド&テストで受入条件を検証する。

## Go / No-Go 推奨

**Go（進めることを推奨）**。スコープはユーザー確認済みで、受け入れ条件が明示され、既存スタックに沿った最小実装である。8/15 デモに向け BE-6 配線まで BE-4 内で完了できる。

## Sources

- GitHub Issue「BE-4: 配管台帳照合サービス（ledger.py）」
- `<record>/ideation/intent-capture/intent-statement.md`
- `<record>/ideation/intent-capture/stakeholder-map.md`
- `<record>/ideation/approval-handoff/approval-handoff-questions.md`（Q1・Q2 回答）
- リポジトリ実態: `backend/app/data/hydrants.json`, `backend/app/schemas/alert.py`, `backend/app/routers/alerts.py`
