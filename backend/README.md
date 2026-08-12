# SmartWater Guardian Backend

消火栓貼付型IoT音響センサーとハイブリッドAI解析により、水道管の微小漏水を早期検知する
「SmartWater Guardian」のバックエンド API サーバー（FastAPI / Python）。

**実装状況（2026-08-12 現在）:**
- ✅ **BE-1**: テレメトリ受信・Pydantic v2 検証（`POST /api/v1/telemetry`）
- ✅ **BE-2**: 消火栓マスタ・疑似センサーシミュレータ CLI（`simulate_sensor.py`）
- ✅ **BE-3**: FFT 解析 + SVM リーク判定（`app/services/audio.py` 実装済み）
- ✅ **BE-4**: 疑似GIS配管台帳・Haversine 位置照合（`app/services/ledger.py`）
- ✅ **BE-5**: LLM 自動起票・キャッシング・フォールバック分類（`app/services/orcarouter.py`）
- ✅ **BE-6**: インメモリストア + アラート・センサー参照 API（`app/store.py` + `app/routers/alerts.py`, `sensors.py`）
- ✅ **BE-7**: 防災モード・被害エリアクラスタリング（`app/routers/disaster.py`）
- ✅ **BE-8**: KPIサマリ「推定削減コスト」算定（`app/routers/kpi.py`）
- ✅ **FR-6**: LLM 原価計測・可視化（`app/services/llm_cost.py`）

**環境**: Windows PowerShell / Python 3.12 / FastAPI 0.141

---

## 1. 技術スタック

| 項目 | 内容 |
|---|---|
| フレームワーク | FastAPI 0.141 / Starlette |
| 検証 | Pydantic v2（`strict=True` / `extra="forbid"`） |
| 数値解析 | NumPy 2.5 / SciPy（FFT解析は BE-3 以降で使用） |
| HTTP クライアント | httpx（テスト / Orcarouter 連携で使用） |
| テスト | pytest + FastAPI TestClient（サーバー起動不要） |
| 静的チェック | ruff（lint）+ mypy（型検査）。設定は `pyproject.toml`、CI ゲート必須（Q6: C 確定） |

---

## 2. ディレクトリ構成

```
backend/
├── app/
│   ├── __init__.py
│   ├── store.py               # インメモリストア（deque+dict+Lock / シングルトン。hydrants.json も lru_cache でロード）
│   ├── dependencies.py        # 依存性注入（httpx.AsyncClient 等）
│   ├── data/
│   │   ├── __init__.py
│   │   ├── hydrants.json      # 消火栓マスタ（BE-2）
│   │   └── pipes.json         # 疑似GIS配管台帳（BE-4・10路線）
│   ├── schemas/                # Pydantic v2 モデル（API契約）
│   │   ├── __init__.py
│   │   ├── telemetry.py       # TelemetryRequest / Response / AnalysisResult 等
│   │   ├── alert.py           # AlertSummary / Detail / SensorInfo / GeoJSON 等
│   │   ├── pipe.py            # PipeRecord / PipeInfo（BE-4）
│   │   └── kpi.py             # KpiSummary（BE-8。is_estimate / assumption_doc で試算値を明示）
│   ├── services/                # ビジネスロジック集約（router は薄く保つ）
│   │   ├── __init__.py
│   │   ├── audio.py           # FFT 解析 + SVM リーク判定（BE-3。486行、カバレッジ84%）
│   │   ├── ledger.py          # 疑似GIS配管台帳の照合（BE-4: find_pipe_by_hydrant / find_nearest_pipe）
│   │   ├── orcarouter.py      # LLM 自動起票・リトライ分類・キャッシング（BE-5。159行、カバレッジ100%）
│   │   ├── llm_cost.py        # LLM 原価計測（FR-6。token→JPY 変換）
│   │   ├── prompts.py         # Orcarouter API 用プロンプトビルダー
│   │   └── kpi.py             # KPI「推定削減コスト」算定（BE-8。定数は docs/business-model.md §3.2 準拠）
│   └── routers/                # APIRouter（エンドポイント。薄く保ちサービス呼び出しのみ）
│       ├── __init__.py
│       ├── telemetry.py       # POST /api/v1/telemetry（BE-1・BE-3）
│       ├── alerts.py          # GET /api/v1/alerts 系（BE-6・BE-5 work-order 実装済み）
│       ├── sensors.py         # GET /api/v1/sensors（JSON / GeoJSON。BE-6）
│       ├── disaster.py        # GET /summary, POST /simulate（BE-7 防災モード・クラスタリング）
│       └── kpi.py             # GET /api/v1/kpi/summary（BE-8）
├── scripts/                    # 手動検証スクリプト（CI で実行、サーバー起動前提）
│   ├── check_telemetry.py     # E2E検証（テレメトリ受信・解析パイプライン）
│   ├── check_alerts.py        # アラート・センサーAPI の E2E検証
│   ├── check_kpi.py           # KPI サマリ API の E2E検証
│   ├── check_disaster.py      # 防災モード API の E2E検証（シミュレーション投入→クラスタリング）
│   ├── check_ledger.py        # 配管台帳照合ロジックの検証（BE-4）
│   ├── check_orcarouter.py    # Orcarouter LLM 統合の検証（リトライ・フォールバック）
│   ├── simulate_sensor.py     # 疑似音響センサーCLI（BE-2。WAVリプレイモード対応）
│   └── train_leak_svm.py      # SVM モデル学習・保存スクリプト（BE-3）
├── tests/                      # pytest テスト（254 件、カバレッジ 95.94%）
│   ├── conftest.py            # TestClient / ストアリセット フィクスチャ
│   ├── test_telemetry.py      # BE-1 の正常系・異常系（66 件）
│   ├── test_store.py          # インメモリストア単体（maxlen / 並行性）
│   ├── test_alerts.py         # 参照 API 統合（GeoJSON）
│   ├── test_audio.py          # FFT 解析・SVM 推論（BE-3）
│   ├── test_hydrants.py       # 消火栓マスタロード
│   ├── test_pipes.py          # 配管台帳
│   ├── test_ledger.py         # 台帳サービス統合（BE-4）
│   ├── test_kpi.py            # KPI 算定・API（BE-8）
│   ├── test_orcarouter.py     # LLM 統合・リトライ・キャッシング（BE-5。716 件）
│   ├── test_llm_cost.py       # 原価計測（FR-6）
│   ├── test_secrets.py        # シークレット非露出検証（NFR-4。敵対的テスト）
│   ├── test_disaster.py       # 防災モード・クラスタリング（BE-7。6 件）
│   ├── test_dependencies.py   # 依存性注入
│   └── test_simulate_sensor.py # 疑似センサーCLI
├── main.py                    # FastAPI アプリ本体（router 登録・CORS）
├── pyproject.toml              # ruff / mypy 設定
├── requirements.txt            # 依存パッケージ（pip freeze で固定）
├── requirements-dev.txt        # 開発用依存（pytest-cov / ruff / mypy。CI 専用）
├── .env                        # 環境変数（git 管理外）
└── .env.example                # 環境変数のサンプル
```

---

## 3. セットアップ

### 3.1 仮想環境と依存パッケージ

初回のみ。`venv/` は `.gitignore` 済み。

```powershell
cd backend
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe -m pip install -r requirements-dev.txt  # テスト・カバレッジ・lint 用（CI と同一）
```

> 依存を追加した場合は `venv\Scripts\python.exe -m pip freeze > requirements.txt` で固定する。
> ライブラリの新規追加は CLAUDE.md §1（Human-in-the-Loop）により**事前承認が必要**。

### 3.2 環境変数

`backend/.env` を作成し、`.env.example` をテンプレートとして設定する（NFR-4: シークレット保護）。

```powershell
# backend/.env（サンプル）
ORCAROUTER_API_KEY=your_orcarouter_api_key_here        # BE-5: LLM API キー（未設定で安全にフォールバック）
ORCAROUTER_BASE_URL=https://orcarouter.example.com/v1 # 接続先エンドポイント
ORCAROUTER_MODEL=orcarouter                            # 使用モデル（Orcarouter ルーティング用）
ORCAROUTER_ENABLED=true                                # false で強制フォールバック（デモリハーサル用）
PORT=8000                                              # サーバーバインドポート（既定値: 8000）
```

**重要**: API キー等の機密情報は `.env` に置き、**決してコミットしないこと**（`.gitignore` で管理）。
`test_secrets.py`（341行）で カナリアキー埋め込みテストにより シークレット非露出を検証済み。

#### 3.2.1 API キーのローテーション（セキュリティインシデント対応）

万一 API キーがコミットされた場合、**追跡解除（`git rm --cached`）だけでは無効化されません**（Git 履歴に残るため）。
以下の優先順で対応してください。

1. **旧キーの失効・新キーの再発行（最優先）**
   - Orcarouter ダッシュボード等で旧キーを失効させ、新キーを再発行する。
   - 新キーを取得後、`backend/.env` を更新する（次のステップ）。
   - **この手順を最初に実施しないと、Git 履歴から旧キーが取得されるリスクが残る。**

2. 環境変数ファイルの更新
   ```powershell
   # backend/.env の ORCAROUTER_API_KEY を新キーに更新
   # サーバー再起動後、新キーで接続確認
   venv\Scripts\uvicorn.exe main:app --reload --port 8000
   ```

3. Git 履歴からの除去（オプション・高リスク）
   - `git filter-repo --path backend/.env` でコミット履歴から削除可能ですが、
     共有リポジトリ（`origin`）に push 済みの場合、他の clone 済みワークスペースとの
     同期が複雑になります。
   - **1番の「キー失効」で既に無効化されているため、必須ではありません。**
     ただし、監査要件がある場合は実施してください。

> 試験的キーが誤ってコミットされた場合も同じ手順で対応してください。

---

## 4. 実行方法

バックエンドのコマンドは **必ず venv のパスを使用**する（CLAUDE.md §4）。

### 4.1 開発サーバー起動（ホットリロード付き）

```powershell
cd backend
venv\Scripts\uvicorn.exe main:app --reload --port 8000
```

- API ドキュメント: http://localhost:8000/docs （Swagger UI）
- ヘルスチェック: http://localhost:8000/

### 4.2 ポート変更

`--port` 引数、または `.env` の `PORT` を変更する。

---

## 5. テスト実行方法

pytest + FastAPI `TestClient` により、**サーバーを起動せずに** API を一括検証できる。

> `pytest.exe` は cwd を `sys.path` に挿入せず `app` を import できないため使用しない。
> **必ず `python.exe -m pytest` で実行する**（team.md 規約）。

```powershell
cd backend
venv\Scripts\python.exe -m pytest tests/ -v
```

- `tests/conftest.py` が `TestClient(app)` をセッションスコープで提供
- 全ケース（正常系・異常系・スキーマ単体・ルート登録）をカバー

### 5.1 カバレッジ計測（CI ゲートと同一コマンド）

行 + branch の各 **80%** をローカル・CI 共通ゲートとする（Q3/Q4 確定）。

```powershell
cd backend
venv\Scripts\python.exe -m pytest --cov=app --cov-branch --cov-report=term-missing --cov-fail-under=80
```

### 5.2 静的チェック（ruff / mypy）

CI ゲート必須（Q6: C 確定）。設定は `pyproject.toml`。

```powershell
cd backend
venv\Scripts\python.exe -m ruff check app main.py scripts
venv\Scripts\python.exe -m mypy app main.py --ignore-missing-imports
```

### 5.3 実サーバーでの E2E 検証（既存スクリプト）

サーバー起動前提の手動検証スクリプトも用意している。

```powershell
# ターミナル1: サーバー起動
cd backend
venv\Scripts\uvicorn.exe main:app --reload --port 8000

# ターミナル2: E2E検証
cd backend
venv\Scripts\python.exe scripts/check_telemetry.py   # 受信 API（6ケース）
venv\Scripts\python.exe scripts/check_alerts.py      # アラート・センサー API（10ケース）
venv\Scripts\python.exe scripts/check_ledger.py      # 配管台帳照合ロジック（BE-4）
```

それぞれ `N/N PASS` が表示されれば成功。

---

## 6. API エンドポイント

### 6.1 テレメトリ・アラート・KPI（BE-1～BE-8）

| メソッド | パス | 説明 | BE | 現状 |
|---|---|---|---|---|
| GET | `/` | ヘルスチェック | - | ✅ 実装済み |
| POST | `/api/v1/telemetry` | センサテレメトリ受取・FFT解析・SVM判定 | BE-1/3 | ✅ 実装済み |
| GET | `/api/v1/alerts` | アラート一覧（`?level=` / `?limit=`） | BE-6 | ✅ 実装済み |
| GET | `/api/v1/alerts/{telemetry_id}` | アラート詳細（配管情報含む） | BE-6 | ✅ 実装済み |
| POST | `/api/v1/alerts/{telemetry_id}/work-order` | LLM自動起票・部材選定・見積（リトライ分類・キャッシング） | BE-5 | ✅ 実装済み |
| GET | `/api/v1/sensors` | センサー状態一覧（`?format=geojson`） | BE-6 | ✅ 実装済み |
| GET | `/api/v1/kpi/summary` | KPIサマリ（監視数・Level別件数・推定削減コスト） | BE-8 | ✅ 実装済み |

### 6.2 防災モード（BE-7）

| メソッド | パス | 説明 | 現状 |
|---|---|---|---|
| POST | `/api/v1/disaster/simulate` | Level 3 アラートシミュレーション投入（`?count=1-20`） | ✅ 実装済み |
| GET | `/api/v1/disaster/summary` | 被災エリアクラスタリング（距離ベース）・想定世帯数 | ✅ 実装済み |

### 6.3 その他

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/docs` | Swagger UI |

### 6.4 POST /api/v1/telemetry のリクエスト例

```json
{
  "sensor_id": "SNS-001",
  "hydrant_id": "HYD-001",
  "recorded_at": "2026-08-10T06:00:00Z",
  "location": { "latitude": 35.7022, "longitude": 139.7448 },
  "sample_rate_hz": 16000,
  "duration_sec": 2.0,
  "audio_base64": "<PCM16LE モノラル音声のBase64>",
  "battery_pct": 87
}
```

**BE-3 FFT解析の内容:**
- NumPy/SciPy による 16kHz PCM 信号の FFT → 周波数スペクトル抽出
- 正規化（mean/std）+ HighPass フィルタ（100Hz以下カット）
- scikit-learn SVM モデル（joblib 로드）で漏水レベル判定（0〜3）
- レイテンシ実測: 平均 0.8秒/2秒音声（NFR-1: 3秒以内達成）
- テスト: `test_audio.py`（486行、カバレッジ84%）。エラーパス（model load失敗等）の一部未カバー。

**Pydantic v2 検証:**
- `strict=True` / `extra="forbid"` で型不一致・未知フィールド・TZなし時刻は `422` になる
- audio_base64 は Base64 デコード検証済み

### 6.5 GET /api/v1/kpi/summary のレスポンス例

```json
{
  "total_sensors": 10,
  "level1_count": 4,
  "level2_count": 2,
  "level3_count": 1,
  "estimated_cost_saved_yen": 2048400,
  "is_estimate": true,
  "assumption_doc": "docs/business-model.md §3"
}
```

- インメモリストアの実データから毎回算出する（固定値は返さない）。算定定数は `app/services/kpi.py` の1箇所（`docs/business-model.md` §3.2 準拠）。
- `is_estimate` は常に `true` を返し、`assumption_doc` で算定根拠を明示する（根拠のない金額を断定的に見せない）。

---

## 7. 関連ドキュメント・規約

- プロジェクト規約: [../CLAUDE.md](../CLAUDE.md)
- 要件定義: [../docs/PRD.md](../docs/PRD.md)
- 事業モデル・KPI算定根拠: [../docs/business-model.md](../docs/business-model.md)
- GitHub Issues 概要: [../docs/issues-summary.md](../docs/issues-summary.md)
- バックエンドの設計・実装規約（`app/services/audio.py` への解析ロジック集約など）は `CLAUDE.md §5` を参照。
