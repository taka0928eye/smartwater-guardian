# Developer Code Scan Results

## Developer Code Scan Results

### Scan Coverage
- **Analyzed deeply**:
  - backend/app/schemas/alert.py (PipeInfo 型定義と不整合)
  - backend/app/schemas/pipe.py (PipeMaterial 型定義)
  - backend/app/routers/alerts.py (アラートAPI実装)
  - backend/app/services/ledger.py (配管台帳参照サービス)
  - backend/app/schemas/telemetry.py (共有スキーマ)
  - backend/app/store.py (データストア実装)
  - backend/app/data/ (マスタデータ構造)
  - backend/requirements.txt (依存関係)
  - backend/app/dependencies.py (DI定義)

- **Skimmed only**:
  - frontend/ (アラート機能は BE-6 APIに依存; FE 実装は本スコープ外)
  - docs/ (参考資料のみ)

### Packages Found
- **backend.app.schemas** — Python module — Pydantic v2 スキーマ定義
- **backend.app.routers** — Python module — FastAPI ルーター実装
- **backend.app.services** — Python module — ビジネスロジック (ledger.py は配管台帳検索)
- **backend.app.store** — Python module — マスタデータロード・キャッシュ
- **backend.app.data** — Python module — JSON マスタデータファイル

### Build System
- **Type**: pip with requirements.txt
- **Config Files**: backend/requirements.txt, backend/pyproject.toml (pytest, ruff config)
- **Build Dependencies**: FastAPI 0.104+, Pydantic v2, NumPy, SciPy (FFT信号処理), pytest, ruff

### APIs Discovered
- **REST API**
  - `GET /api/v1/alerts` — アラート一覧（BE-6）
  - `GET /api/v1/alerts/{telemetry_id}` — アラート詳細（BE-6、pipe_info は常時 null）
  - `GET /api/v1/sensors` — センサー・マスタ一覧
  - `GET /api/v1/sensors?format=geojson` — GeoJSON形式センサー位置
  
- **Internal APIs**
  - ledger.find_nearest_pipe(hydrant_id, location) → PipeInfo（BE-4実装時）
  - store.load_pipes(), store.load_hydrants()

### Frameworks & Libraries
- **FastAPI** — 0.104+ — Web framework
- **Pydantic** — v2.x — データ検証・直列化
- **NumPy** — 信号処理（FFT解析）
- **SciPy** — 信号フィルタリング
- **Pytest** — テストフレームワーク
- **Ruff** — Python linter

### Test Coverage
- **Test Directories**: backend/tests/
- **Test Frameworks**: pytest
- **Coverage Config**: pyproject.toml に coverage 設定あり
- **Test Examples**: test_alerts.py（エンドポイントテスト）

### Code Quality Indicators
- **Linting**: Ruff で実装・チェック
- **CI/CD**: GitHub Actions workflows (backend テスト・カバレッジ検証)
- **Documentation**: docstring 部分的に実装、一部陳腐化
- **Type Hints**: Pydantic v2 strict モード、型チェック実装

### Technical Debt Signals
1. **型不整合**: 
   - `PipeInfo.material` は `str` 型（alert.py:46）
   - `PipeRecord.material` は `PipeMaterial` 型（pipe.py:17、Literal["ductile_iron", "cast_iron", "pvc", "steel"]）
   - 型統一が必要

2. **陳腐化したドキュメント**:
   - PipeInfo docstring（alert.py:37-40）が「BE-6 では常に None を返す」と述べるが、BE-4 ledger.py 実装で状態変化
   - docstring 更新必要

3. **ドキュメントギャップ**:
   - スキーマ間の依存関係（alert → pipe）の説明不足
   - API 統合仕様（PipeInfo 挿入タイミング）の明示化が必要

4. **値のバリデーション**:
   - GeoJSONLineString（pipe.py:33-43）で緯度経度チェックあり
   - GeoLocation（telemetry.py）での座標チェック状況は要確認

