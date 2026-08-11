# Unit Test Instructions — BE-4 配管台帳照合サービス（ledger.py）

> テスト戦略: **Minimal（Nyquist モデル）** — 要求駆動のユニットテストのみ（統合・E2E・性能・セキュリティはスキップ）
> 上流成果物: `construction/be4-ledger/code-generation/code-generation-plan.md`（Step 2/4/6 のテスト計画）・`construction/be4-ledger/code-generation/code-summary.md`
> 品質基準: カバレッジ **80% 以上**（CLAUDE.md §4。実績は 100%）

## 1. テストフレームワークとセットアップ

- フレームワーク: **pytest**（`backend/requirements.txt` に含む）
- カバレッジ計測: `pytest-cov`
- **実行は必ず `venv/Scripts/python.exe -m pytest`**（`pytest.exe` 単体は cwd を sys.path に挿入しないため `app` が import できない — 環境の既知特性）

```bash
cd backend
venv/Scripts/python.exe -m pytest -v
```

カバレッジ付きで実行:

```bash
venv/Scripts/python.exe -m pytest --cov=app --cov-report=term-missing
```

## 2. テスト一覧（要求駆動マッピング）

Minimal 戦略: 受け入れ条件ごとに最低 1 テスト + 各コンポーネントのハッピーパス下限。

| テストファイル | 要求 / 決定 | 検証内容 |
|----------------|-------------|----------|
| `tests/test_pipes.py`（7 件） | A1 前提 / D-4 | `pipes.json` が丁度 10 路線、`P-001`〜`P-010` と一致、素材・口径・布設年・埋設深が許容値、LineString 頂点検証、`hydrant_ids` が台帳と整合 |
| `tests/test_ledger.py`（12 件） | A1〜A4 / A6 / D-4 / D-5 | `find_pipe_by_hydrant` が全 10 消火栓を解決（A1）/ 未知 ID → None（A2）/ `find_nearest_pipe` が Haversine で動作（A3）/ 欠損 → `FileNotFoundError`・破損 → `ValueError`（A4）/ キャッシュ 1 回読み込み（A6）/ `get_pipe_age = 2026 - installed_year`（D-5）/ スキーマ境界エッジ |
| `tests/test_alerts.py`（更新） | A5 / D-5 | `GET /api/v1/alerts/{id}` の `pipe_info` が台帳照合で実値（material / diameter_mm / installed_year / burial_depth_m / age_years）。未知 hydrant は `pipe_info: null` のまま |

### 主要テストケース設計（TC 形式）

```
TC-01 (A1): find_pipe_by_hydrant("HYD-001") → PipeRecord(pipe_id="P-001")
TC-02 (A2): find_pipe_by_hydrant("HYD-999") → None
TC-03 (A3): find_nearest_pipe(既知緯度, 既知経度) → 非 None の最近接路線
TC-04 (A3 エッジ): find_nearest_pipe(空台帳) → None（get_pipes をモンキーパッチ）
TC-05 (A4): PIPES_PATH を欠損パスへ差し替え → FileNotFoundError
TC-06 (A4): 不正 JSON の一時ファイル → ValueError
TC-07 (A6): get_pipes() を 2 回呼び json.loads は 1 回
TC-08 (D-5): get_pipe_age(2012) == 14
TC-09 (A5): TestClient で HYD-001 詳細の pipe_info に P-001 の実値
```

## 3. 実行コマンド

```bash
# 全テスト（Green 前提の最終確認）
venv/Scripts/python.exe -m pytest --cov=app --cov-report=term-missing

# 対象ファイルのみ
venv/Scripts/python.exe -m pytest tests/test_ledger.py tests/test_pipes.py -v

# 独立検証スクリプト（受け入れ条件 7 項目のスタンドアロン確認）
venv/Scripts/python.exe scripts/check_ledger.py   # → 7/7 PASS・終了コード 0
```

## 4. カバレッジ目標

- **下限 80%**（CLAUDE.md §4 の品質基準）
- 実績: **app 全体 372 stmts / 0 miss（100%）** — `ledger.py`(41)・`pipe.py`(29)・`alerts.py`(28) いずれも 100%

## 5. テストデータ管理

- 台帳データは `backend/app/data/pipes.json`（固定）を参照。テストからは `PIPES_PATH` を差し替えることで欠損・破損・空台帳の経路を検証（実ファイルに依存しない）。
- 各テストで `get_pipes.cache_clear()` を呼び、キャッシュをテスト間で隔離（実行順に依存しない独立性を維持）。
- テストは外部ネットワーク・DB に依存しない（TestClient はインメモリストアを利用）。
