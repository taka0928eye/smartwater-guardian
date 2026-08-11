# Code Generation Plan — BE-4 配管台帳照合サービス

| 項目 | 内容 |
|------|------|
| ユニット | `be4-ledger`（単一イテレーション / 単一論理ユニット） |
| テスト戦略 | Minimal（要求駆動のユニットテスト、コンポーネント毎にハッピーパス下限） |
| 手法 | TDD（Red → Green → Refactor）を各ステップで徹底 |
| 言語 / 規約 | Python 3.11 / Pydantic v2（STRICT_INPUT_CONFIG）/ コメント・ドキュメントは日本語 |

## 成果物マップ

| 種別 | ファイル | 対応 |
|------|----------|------|
| 新規データ | `backend/app/data/pipes.json` | 配管台帳 10 路線 |
| 新規スキーマ | `backend/app/schemas/pipe.py` | `PipeRecord` / `GeoJSONLineString` |
| 新規サービス | `backend/app/services/ledger.py` | 照合ロジック + キャッシュ + ヘルパー |
| 新規テスト | `backend/tests/test_pipes.py` | pipes.json データ整合 |
| 新規テスト | `backend/tests/test_ledger.py` | 照合ロジック |
| 既存テスト更新 | `backend/tests/test_alerts.py` | pipe_info 配線（null 検証 → 実値検証へ） |
| 新規スクリプト | `backend/scripts/check_ledger.py` | 受け入れ条件 7 項目の自動検証 |
| 既存修正 | `backend/app/routers/alerts.py` | `pipe_info` を ledger で実値化（BE-6 配線） |

## トレーサビリティ（要求 → 実装ステップ）

BE-4 受け入れ条件（A1〜A7）と決定（D-4, D-5）への対応関係：

| 受け入れ条件 | 内容 | 実装ステップ |
|--------------|------|--------------|
| A1 | 全 10 消火栓が `find_pipe_by_hydrant()` で解決（P-001〜P-010） | Step 2, 4, 5 |
| A2 | 未知 ID → `None` | Step 4, 5 |
| A3 | `find_nearest_pipe()` が Haversine で動作 | Step 4, 5 |
| A4 | 欠損 → `FileNotFoundError` / 破損 → `ValueError` の明示例外 | Step 4, 5 |
| A5 | `GET /api/v1/alerts/{id}` の `pipe_info` に配管情報が入る | Step 6, 7 |
| A6 | モジュールキャッシュ（リクエスト毎の再読み込みをしない） | Step 5 |
| A7 | `python scripts/check_ledger.py` が PASS | Step 8 |
| D-4 | `pipe_id` は `P-001` 形式（hydrants.json と整合） | Step 2, 3 |
| D-5 | 経過年数は `2026 - installed_year` | Step 4, 5, 7 |

---

## 実装ステップ（TDD 順序）

### Step 1: スキーマ `app/schemas/pipe.py`（Green の土台）

- [x] `PipeRecord`（Pydantic v2、`STRICT_INPUT_CONFIG`）を定義
  - `pipe_id: str`
  - `material: Literal["ductile_iron", "cast_iron", "pvc", "steel"]`
  - `diameter_mm: Literal[75, 100, 150, 200]`
  - `installed_year: int`（`ge=1965, le=2015` を Field で検証）
  - `burial_depth_m: float`（`gt=0`）
  - `route: GeoJSONLineString`
  - `hydrant_ids: list[str]`
- [x] `GeoJSONLineString`（GeoJSON LineString 型）を定義
  - `type: Literal["LineString"] = "LineString"`
  - `coordinates: list[list[float]]`（各頂点 `[経度, 緯度]`、`min_length=2` で路線の最低 2 頂点を保証）

> 本ステップは Step 4/5 のテスト・実装が依存する型を先に固定する。スキーマ自体の網羅テストは
> ledger 経由のロードと alerts 配線で間接的に検証する（Minimal 戦略）。

### Step 2: データ整合テスト `tests/test_pipes.py`（Red）

- [x] `pipes.json` が丁度 10 路線を含む
- [x] `pipe_id` が 10 件でユニーク、`P-001`〜`P-010` と一致（D-4）
- [x] `material` が許容値のみ
- [x] `diameter_mm` が `{75, 100, 150, 200}` のみ
- [x] `installed_year` が `[1965, 2015]` 内
- [x] `burial_depth_m` が正値
- [x] `route` が `type: "LineString"`、頂点 2 以上、各頂点 `[lng, lat]` が範囲内
- [x] `hydrant_ids` の全要素が `hydrants.json` の `pipe_id` 参照（P-001〜P-010）と整合

### Step 3: 配管台帳データ `app/data/pipes.json`（Green）

- [x] 10 路線を定義（P-001〜P-010）
  - 各消火栓の `pipe_id`（P-001〜P-010）と 1:1 対応
  - 路線座標は対応消火栓の `[longitude, latitude]` 付近を通る LineString で、消火栓位置を含む
  - 素材は `ductile_iron` / `cast_iron` / `pvc` / `steel` を複合
  - 口径は `75 / 100 / 150 / 200` を複合
  - 布設年は `1965〜2015` の範囲で分散
- [x] `backend/venv/Scripts/pytest.exe tests/test_pipes.py -v` が Green になることを確認

### Step 4: 照合ロジックテスト `tests/test_ledger.py`（Red）

- [x] `find_pipe_by_hydrant()` が全 10 消火栓（HYD-001〜HYD-010）を解決し、`hydrant_ids` に対応する `PipeRecord` を返す（A1）
- [x] 未知の `hydrant_id` → `None`（A2）
- [x] `find_nearest_pipe()` が既知座標（例: 消火栓の位置）に対して最近接路線を返す（A3）
- [x] `find_nearest_pipe()` が空台帳で `None` を返す（モンキーパッチで `get_pipes` を `[]` に差し替え）（A3 エッジ）
- [x] `get_pipe_age(installed_year)` が `2026 - installed_year` を返す（D-5）
- [x] `pipes.json` 欠損時に `FileNotFoundError` が上がる（`PIPES_PATH` を実在しないパスへ差し替え）（A4）
- [x] `pipes.json` 破損（不正 JSON）時に `ValueError` が上がる（一時ファイルへ破損 JSON を書き差し替え）（A4）
- [x] キャッシュ: `get_pipes()` を 2 回呼んでもファイル読み込みは 1 回（`json.loads` をモンキーパッチして呼び出し回数を検証）（A6）
- [x] 各テストで `get_pipes.cache_clear()` してキャッシュを隔離

### Step 5: 照合サービス `app/services/ledger.py`（Green）

- [x] `PIPES_PATH` を cwd 非依存で解決（store.py の `HYDRANTS_PATH` と同様）
- [x] `_load_pipes(path)` — 内部ローダー（パス指定可能でテスト・検証スクリプトから再利用）
  - `FileNotFoundError` はそのまま伝播
  - `json.JSONDecodeError` は `ValueError` に変換して伝播
  - 各要素を `PipeRecord.model_validate` で検証（不正レコードは `ValidationError`）
- [x] `@lru_cache(maxsize=1) get_pipes()` — 初回読み込みのみ実行し以後キャッシュ（A6、store.py の `get_hydrants` と同パターン）
- [x] `find_pipe_by_hydrant(hydrant_id) -> PipeRecord | None` — `hydrant_ids` を走査（A1, A2）
- [x] `find_nearest_pipe(lat, lng) -> PipeRecord | None` — 各路線の全頂点に対する Haversine 距離の最小値で最近接を判定（A3）
- [x] `get_pipe_age(installed_year) -> int` — `2026 - installed_year`（D-5）
- [x] `backend/venv/Scripts/pytest.exe tests/test_ledger.py -v` が Green になることを確認

### Step 6: alerts 配線テスト更新 `tests/test_alerts.py`（Red）

- [x] `TestAlertDetail::test_returns_detail_with_spectrum_and_null_pipe` を更新 — HYD-001 の詳細で `pipe_info` が `None` でなく、`P-001` の配管情報（material / diameter_mm / installed_year / burial_depth_m / age_years）を含むことを検証（A5, D-5）
- [x] 未知 hydrant（例: `HYD-999`）のレコードでは `pipe_info` が `None` のまま（A5 エッジ）

### Step 7: alerts 配線 `app/routers/alerts.py`（Green）

- [x] `get_alert_detail` で `pipe_info=None` の固定を撤廃
  - `find_pipe_by_hydrant(record.hydrant_id)` で照合
  - 該当があれば `PipeInfo`（material / diameter_mm / installed_year / burial_depth_m / age_years）を構築
  - 該当がなければ `None`（既存の null 許容設計を維持）
- [x] `backend/venv/Scripts/pytest.exe tests/test_alerts.py -v` が Green になることを確認

### Step 8: 検証スクリプト `scripts/check_ledger.py`

- [x] サーバー不要・依存なしで実行できるスタンドアロン検証（check_telemetry.py の流儀）
- [x] 受け入れ条件 7 項目（A1〜A7）を個別ケースとして検証
  1. pipes.json が 10 路線（データ整合の主要チェック）
  2. 全 10 消火栓の `find_pipe_by_hydrant()` 解決（A1）
  3. 未知 ID → `None`（A2）
  4. `find_nearest_pipe()` が既知座標で非 None（A3）
  5. `get_pipe_age()` の値（A5/D-5 の入力）
  6. 明示例外: 欠損パス → `FileNotFoundError` / 破損 JSON → `ValueError`（A4）
  7. モジュールキャッシュ: `cache_info().currsize == 1`（A6）
- [x] `backend/venv/Scripts/python.exe scripts/check_ledger.py` が 7/7 PASS で終了コード 0

### Step 9: 自走確認（Refactor）

- [x] `backend/venv/Scripts/pytest.exe --cov=app --cov-report=term-missing` で全テスト Green + カバレッジ **80% 以上**
- [x] コード品質: `any` 禁止、Pydantic v2 徹底、不要な公開関数なし
- [x] `scripts/check_ledger.py` の最終 PASS 確認
- [x] git status で変更対象ファイル（6 新規 + 1 修正）が期待通り

---

## 計画外（スコープ外の明示）

- 本番用 GIS DB、認証、リアルタイム通知は CLAUDE.md §3 により実装しない
- `find_nearest_pipe` の既存テスト内での「厳密な最寄り」比較は、台帳データ依存のため
  座標指定での非 None + 空台帳 None の検証に留める（A3 は check_ledger.py で実値確認）
