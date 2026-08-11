# Code Generation Plan — alert-schema-cleanup

## 参照元

- 要件: `aidlc/spaces/default/intents/260811-alert-schema-cleanup/inception/requirements-analysis/requirements.md`（FR-1〜FR-5, NFR-1〜NFR-3）
- コード知識ベース: `aidlc/spaces/default/codekb/smartwater-guardian/`（code-structure.md, code-quality-assessment.md）
- テスト戦略: Minimal（`aidlc-state.md` Test Strategy）— リクエスト駆動で1要件1テストの happy-path floor

このユニットは bugfix スコープのため units-generation・application-design をスキップしている。計画は requirements.md と codekb から直接組み立てる。

## 実装ステップ

- [x] Step 1: `backend/app/schemas/pipe.py` — マジックナンバーの named constant 化（FR-4）
  - モジュールレベルで `MIN_INSTALL_YEAR = 1965`、`MAX_INSTALL_YEAR = 2015` を定義
  - `PipeRecord.installed_year` の `Field(ge=1965, le=2015, ...)` を `Field(ge=MIN_INSTALL_YEAR, le=MAX_INSTALL_YEAR, ...)` に変更
  - Story: FR-4

- [x] Step 2: `backend/app/schemas/pipe.py` — `STRICT_INPUT_CONFIG` の重複解消（利用側）（FR-5）
  - `app.schemas.pipe` 内の独自 `STRICT_INPUT_CONFIG` 定義を削除し、`from app.schemas.telemetry import STRICT_INPUT_CONFIG` に置き換える
  - `PipeRecord`, `GeoJSONLineString` の `model_config` が共通定義を参照することを確認
  - Story: FR-5

- [x] Step 3: `backend/app/schemas/alert.py` — `PipeInfo.material` の型統一（FR-1）
  - `from app.schemas.pipe import PipeMaterial` をインポートに追加
  - `PipeInfo.material: str` を `PipeInfo.material: PipeMaterial` に変更
  - Story: FR-1

- [x] Step 4: `backend/app/schemas/alert.py` — `PipeInfo` docstring の更新（FR-2）
  - 「BE-6 では常に ``None`` を返す」という記述を、BE-4実装済みの実態（該当消火栓があれば実データ、なければ `pipe_info` 自体が `None`）に書き換える
  - Story: FR-2

- [x] Step 5: `backend/app/schemas/alert.py` — `STRICT_INPUT_CONFIG` の重複解消（利用側）（FR-5）
  - `app.schemas.alert` 内の独自 `STRICT_INPUT_CONFIG` 定義を削除し、`from app.schemas.telemetry import STRICT_INPUT_CONFIG` に置き換える
  - `AlertSummary`, `PipeInfo` の `model_config` が共通定義を参照することを確認（`AlertDetail` は `AlertSummary` を継承するため個別設定不要、`GeoJSONPoint`・`SensorProperties`・`SensorFeature`・`SensorFeatureCollection` は元々 `ConfigDict(strict=True)` のみで `extra="forbid"` を持たないため対象外とする）
  - Story: FR-5

- [x] Step 6: リグレッションテストの追加（`backend/tests/test_alerts.py`）（FR-1, FR-3）
  - **既存確認**: `TestAlertDetail::test_returns_detail_with_spectrum_and_pipe_info` は既に `pipe_info["material"] == "ductile_iron"` を検証しており、値レベルの回帰は既にカバー済み（変更不要）
  - **新規追加**: `PipeInfo` を直接インポートし、型統一の効果が観測できる単体テストを1件追加する — `PipeInfo(..., material="invalid_material", ...)` が `pydantic.ValidationError` を送出することを検証する（`material: str` のままでは通ってしまうが、`PipeMaterial` Literal 化後は拒否される — これが Red→Green で観測可能な唯一の挙動変化）
  - Story: FR-1, FR-3

- [x] Step 7: 単体テストの追加（`backend/tests/test_pipes.py`）（FR-4）
  - `PipeRecord` を直接インポートし、`installed_year` の境界値（`MIN_INSTALL_YEAR`, `MAX_INSTALL_YEAR`, および範囲外の値 `MIN_INSTALL_YEAR - 1`）を検証するテストケースを1件追加（happy-path floor）。既存の `test_installed_year_within_range`（生JSON検証）とは別観点（Pydanticバリデーション境界）のため独立して追加する
  - Story: FR-4

- [x] Step 8: 既存テストスイートの回帰確認（org.md Testing Posture: bugfix）
  - `venv/Scripts/python.exe -m pytest --cov=app --cov-report=term-missing` を実行し、既存テストが green のまま、カバレッジ80%以上を維持することを確認
  - Story: FR-1〜FR-5（全体の非機能要件確認）

## テストファイル方針（Minimal 戦略）

- 新規・変更ユニットテストのみ（統合・性能・セキュリティのテスト指示書はスキップ — project.md learned practice に基づく）
- `test_alerts.py` の `TestClient` エンドポイントテストが統合境界を実質カバーするため、追加の統合テストは作成しない
- テスト設定ファイル（`pytest.ini` 等）は既存のものを使用し、新規作成は不要（既にプロジェクトに存在）

## 適用外ステップ

このユニットはバックエンドのスキーマ・サービス層の修正のみであり、以下は適用外:
- フロントエンド変更（対象外と requirements.md Out of Scope に明記）
- データベースマイグレーション（インメモリ・JSON構成のため不要）
- デプロイメント成果物（Dockerfile/IaC の変更は不要）
- API/エンドポイント層の新規追加（既存エンドポイントの内部型変更のみ）
