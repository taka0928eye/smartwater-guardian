# SmartWater Guardian Backend

消火栓貼付型IoT音響センサーとハイブリッドAI解析により、水道管の微小漏水を早期検知する
「SmartWater Guardian」のバックエンド API サーバー（FastAPI / Python）。

- **現状のスコープ**: BE-6（解析済みテレメトリの保持 + アラート・センサー参照 API）まで。
  BE-2（疑似センサー・消火栓マスタ）/ BE-3（FFT 解析）は未実装のため、仮データとモック解析で先行。
- **環境**: Windows PowerShell / Python 3.11+（venv 使用）

---

## 1. 技術スタック

| 項目 | 内容 |
|---|---|
| フレームワーク | FastAPI 0.141 / Starlette |
| 検証 | Pydantic v2（`strict=True` / `extra="forbid"`） |
| 数値解析 | NumPy 2.5 / SciPy（FFT解析は BE-3 以降で使用） |
| HTTP クライアント | httpx（テスト / Orcarouter 連携で使用） |
| テスト | pytest + FastAPI TestClient（サーバー起動不要） |

---

## 2. ディレクトリ構成

```
backend/
├── app/
│   ├── __init__.py
│   ├── store.py              # インメモリストア（deque+dict+Lock / シングルトン）
│   ├── data/
│   │   ├── __init__.py
│   │   └── hydrants.json     # 消火栓マスタ仮データ（BE-2 の将来形式と互換）
│   ├── schemas/              # Pydantic v2 モデル（API契約）
│   │   ├── __init__.py
│   │   ├── telemetry.py      # TelemetryRequest / Response / AnalysisResult 等
│   │   └── alert.py          # AlertSummary / Detail / SensorInfo / GeoJSON 等
│   └── routers/              # APIRouter（エンドポイント）
│       ├── __init__.py
│       ├── telemetry.py      # POST /api/v1/telemetry（モック解析つき）
│       ├── alerts.py         # GET /api/v1/alerts 系
│       └── sensors.py        # GET /api/v1/sensors（JSON / GeoJSON）
├── scripts/                  # 手動検証スクリプト
│   ├── check_telemetry.py    # E2E検証（サーバー起動前提・requests使用）
│   └── check_alerts.py       # アラート・センサーAPI の E2E検証
├── tests/                    # pytest テスト
│   ├── conftest.py           # TestClient / ストアリセット フィクスチャ
│   ├── test_telemetry.py     # BE-1 の正常系・異常系 + モック解析
│   ├── test_store.py         # インメモリストア単体（maxlen / 並行性）
│   └── test_alerts.py        # 参照 API 統合（404 / 501 / GeoJSON）
├── main.py                   # FastAPI アプリ本体（router 登録・CORS）
├── requirements.txt          # 依存パッケージ（pip freeze で固定）
├── .env                      # 環境変数（git 管理外）
└── .env.example              # 環境変数のサンプル
```

---

## 3. セットアップ

### 3.1 仮想環境と依存パッケージ

初回のみ。`venv/` は `.gitignore` 済み。

```powershell
cd backend
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
```

> 依存を追加した場合は `venv\Scripts\python.exe -m pip freeze > requirements.txt` で固定する。
> ライブラリの新規追加は CLAUDE.md §1（Human-in-the-Loop）により**事前承認が必要**。

### 3.2 環境変数

`backend/.env` を作成し、必要に応じて設定する（現状は Orcarouter 関連のみ）。

```
# 例: backend/.env（.env.example 参照）
ORCAROUTER_API_KEY=your_orcarouter_api_key_here
PORT=8000
```

> API キー等の機密情報は必ず `.env` に置き、コミットしないこと（CLAUDE.md §5.1）。

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

```powershell
cd backend
venv\Scripts\python.exe -m pytest tests/ -v
```

- `tests/conftest.py` が `TestClient(app)` をセッションスコープで提供
- 全ケース（正常系・異常系・スキーマ単体・ルート登録）をカバー

### 5.1 実サーバーでの E2E 検証（既存スクリプト）

サーバー起動前提の手動検証スクリプトも用意している。

```powershell
# ターミナル1: サーバー起動
cd backend
venv\Scripts\uvicorn.exe main:app --reload --port 8000

# ターミナル2: E2E検証
cd backend
venv\Scripts\python.exe scripts/check_telemetry.py   # 受信 API（6ケース）
venv\Scripts\python.exe scripts/check_alerts.py      # アラート・センサー API（10ケース）
```

それぞれ `N/N PASS` が表示されれば成功。

---

## 6. API エンドポイント

| メソッド | パス | 説明 | 現状 |
|---|---|---|---|
| GET | `/` | ヘルスチェック | 実装済み |
| POST | `/api/v1/telemetry` | センサテレメトリ受取（モック解析つき） | 実装済み（`analysis` に解析結果） |
| GET | `/api/v1/alerts` | アラート一覧（`?level=` / `?limit=`） | 実装済み |
| GET | `/api/v1/alerts/{telemetry_id}` | アラート詳細 | 実装済み（不明 ID は 404） |
| POST | `/api/v1/alerts/{telemetry_id}/work-order` | 工事発注書の自動起票 | スタブ（501 / BE-5 未実装） |
| GET | `/api/v1/sensors` | センサー状態一覧（`?format=geojson` 可） | 実装済み |
| GET | `/docs` | Swagger UI | 実装済み |

### POST /api/v1/telemetry のリクエスト例

```json
{
  "sensor_id": "SNS-001",
  "hydrant_id": "HYD-001",
  "recorded_at": "2026-08-10T06:00:00Z",
  "location": { "latitude": 35.7022, "longitude": 139.7448 },
  "sample_rate_hz": 16000,
  "duration_sec": 2.0,
  "audio_base64": "<PCM16モノラル音声のBase64>",
  "battery_pct": 87
}
```

- 入力は `strict=True` / `extra="forbid"` のため、型不一致・未知フィールド・TZなし時刻は `422` になる。
- `analysis` は BE-3（`app/services/audio.py`）実装まではモック解析（`telemetry.py` の `_analyze_audio_mock`）で生成する。BE-3 実装で `analyze_audio()` に置き換わる。

---

## 7. 関連ドキュメント・規約

- プロジェクト規約: [../CLAUDE.md](../CLAUDE.md)
- 要件定義: [../docs/PRD.md](../docs/PRD.md)
- GitHub Issues 概要: [../docs/issues-summary.md](../docs/issues-summary.md)
- バックエンドの設計・実装規約（`app/services/audio.py` への解析ロジック集約など）は `CLAUDE.md §5` を参照。
