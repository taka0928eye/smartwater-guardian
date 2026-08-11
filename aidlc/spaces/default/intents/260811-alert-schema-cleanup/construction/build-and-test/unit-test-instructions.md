# Unit Test Instructions — alert-schema-cleanup

## テスト戦略

**Minimal**（`aidlc-state.md` Test Strategy）— リクエスト駆動で1要件1テストの happy-path floor。project.md の学習事項（cid:build-and-test:c1）に従い、統合・性能・セキュリティのテスト指示書は生成しない。

## 参照元

- 承認済みプラン: `aidlc/spaces/default/intents/260811-alert-schema-cleanup/construction/alert-schema-cleanup/code-generation/code-generation-plan.md`（Step 6, Step 7）
- 実装サマリー: `aidlc/spaces/default/intents/260811-alert-schema-cleanup/construction/alert-schema-cleanup/code-generation/code-summary.md`

## テストフレームワーク設定

- **フレームワーク**: pytest 9.1.1 + pytest-cov 7.1.0（既存 venv にインストール済み）
- **設定ファイル**: `backend/pyproject.toml`（既存、変更なし）
- **新規設定は不要**: 本修正はテスト構成ファイルを変更しない

## テスト実行コマンド

project.md の学習事項（cid:build-and-test:c3）に従い、`pytest.exe` ではなく `python.exe -m pytest` を使用する（`pytest.exe` は cwd を `sys.path` に挿入せず `app` を import できないため）。

```
cd backend
venv/Scripts/python.exe -m pytest --cov=app --cov-report=term-missing
```

本修正の変更ファイルのみに絞ったテスト実行（開発時の高速フィードバック用）:

```
cd backend
venv/Scripts/python.exe -m pytest tests/test_alerts.py tests/test_pipes.py -v
```

## 対象テストケース（今回追加分）

### `backend/tests/test_alerts.py::TestPipeInfoSchema`

| テスト名 | 検証内容 | 対応要件 |
|---------|---------|---------|
| `test_material_outside_pipe_material_literal_raises_validation_error` | `PipeInfo(material="invalid_material", ...)` が `pydantic.ValidationError` を送出する（`PipeMaterial` Literal 型統一の効果） | FR-1, FR-3 |

### `backend/tests/test_pipes.py`

| テスト名 | 検証内容 | 対応要件 |
|---------|---------|---------|
| `test_installed_year_boundary_rejects_below_min_accepts_min_and_max` | `installed_year` が `MIN_INSTALL_YEAR - 1` で `ValidationError`、`MIN_INSTALL_YEAR`/`MAX_INSTALL_YEAR` 自体は受理される（named constant 境界の検証） | FR-4 |

## 既存テストとの関係（回帰確認対象）

以下は変更していないが、本修正の影響を受けうるため回帰確認の対象とする：

| 既存テスト | 関連性 |
|-----------|--------|
| `test_alerts.py::TestAlertDetail::test_returns_detail_with_spectrum_and_pipe_info` | `pipe_info.material == "ductile_iron"` を検証済み（FR-1型変更後も値は不変であることの確認） |
| `test_alerts.py::TestAlertDetail::test_unknown_hydrant_detail_keeps_pipe_info_null` | `pipe_info` が `None` になるケース（`PipeInfo` 自体が構築されない経路）に型変更が影響しないことの確認 |
| `test_pipes.py::test_material_and_diameter_within_allowed_values` | 生JSON（`pipes.json`）の `material` 値が許容集合内であることの検証（`PipeMaterial` Literal と同じ集合を別観点で保証） |
| `test_pipes.py::test_installed_year_within_range` | 生JSON の `installed_year` が 1965〜2015 の範囲内であることの検証（named constant 化後も範囲は不変であることの確認） |
| `test_ledger.py`（全体） | `PipeRecord`・`find_pipe_by_hydrant` 等、`pipe.py` の変更が波及しうるサービス層のテスト |

## カバレッジ目標

- CLAUDE.md §4 の要求: 80%以上
- 実測（Code Generation 段階で確認済み）: 100%（375 stmts, 0 miss）
- Build and Test 段階で再実行し、同水準を維持することを確認する

## テストデータ管理

- マスタデータ（`app/data/pipes.json`, `app/data/hydrants.json`）は変更なし。既存のフィクスチャ（`conftest.py` の `client`, `store` フィクスチャ）をそのまま使用
- 新規テストは `PipeInfo`/`PipeRecord` を直接構築するため、追加のフィクスチャファイルは不要
