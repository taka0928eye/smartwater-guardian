# SmartWater Guardian - コード構造

## ディレクトリ階層

```
backend/
├── app/
│   ├── __init__.py                 # パッケージ定義
│   ├── main.py                     # FastAPI app インスタンス（CLAUDE.md に従い起動: uvicorn main:app --reload --port 8000）
│   ├── dependencies.py             # DI コンテナ
│   ├── store.py                    # インメモリストア（StoredTelemetry、get_store()）
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── telemetry.py            # TelemetryRequest/Response, AnalysisResult, SeverityLevel, GeoLocation
│   │   ├── alert.py                # AlertSummary, AlertDetail, PipeInfo ★型不整合
│   │   └── pipe.py                 # PipeRecord, PipeMaterial, GeoJSONLineString
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── telemetry.py            # POST /api/v1/telemetry (BE-1)
│   │   ├── alerts.py               # GET /api/v1/alerts(s/{id}) (BE-6) ★PipeInfo 組み立て
│   │   └── sensors.py              # GET /api/v1/sensors (GeoJSON)
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── audio.py                # FFT 解析（BE-3: 未実装スタブ）
│   │   └── ledger.py               # 配管台帳照合（BE-4）
│   │
│   └── data/
│       ├── __init__.py
│       ├── pipes.json              # GIS 配管台帳（10路線、GeoJSON LineString）
│       └── hydrants.json           # 消火栓マスタ
│
├── tests/
│   ├── test_alerts.py              # アラートAPI エンドポイントテスト
│   └── test_*.py
│
├── requirements.txt                # 依存パッケージ一覧
├── pyproject.toml                  # pytest, ruff 設定
├── venv/                           # 仮想環境（本番ビルドで除外）
└── README.md                       # API ドキュメント

frontend/
├── app/                            # Next.js app directory
├── components/                     # React コンポーネント
├── public/                         # 静的アセット
├── package.json
└── ...

docs/
└── ...                             # 補足ドキュメント
```

## モジュール設計

### 1. Schemas (Pydantic v2 Models)

#### telemetry.py
```python
- SeverityLevel = Literal[0, 1, 2, 3]  # 漏水深刻度定義
- STRICT_INPUT_CONFIG                   # ConfigDict(strict=True, extra="forbid")
- GeoLocation                           # lat/lng 範囲チェック付き
- TelemetryRequest                      # IoT入力（Base64 audio, AwareDatetime）
- AnalysisResult                        # FFT 判定結果（BE-3実装時）
- TelemetryResponse                     # 受信確認応答
- SpectrumPoint                         # スペクトル1点（周波数-振幅ペア）
```

#### alert.py
```python
- AlertSummary                          # 一覧行（telemetry_id, sensor_id, hydrant_id, severity_level, leak_confidence, detected_at）
- PipeInfo                              # 配管情報 ★ material: str (要修正)
- AlertDetail                           # 詳細（AlertSummary + location + analysis + pipe_info|None）
- SensorInfo                            # センサー・マスタ統合（status導出）
- HydrantMaster                         # 消火栓マスタ行
- GeoJSONPoint, SensorProperties,
  SensorFeature, SensorFeatureCollection # GeoJSON形式
```

#### pipe.py
```python
- PipeMaterial = Literal[...]           # 素材enum（ductile_iron, cast_iron, pvc, steel）
- PipeDiameterMm = Literal[...]         # 口径enum（mm）
- GeoJSONLineString                     # 路線ジオメトリ（座標検証）
- PipeRecord                            # 台帳1路線（pipe_id, material, diameter_mm, ...）
```

### 2. Routers (FastAPI Endpoints)

#### telemetry.py (BE-1)
```python
POST /api/v1/telemetry
  ├─ Request: TelemetryRequest (Base64検証)
  ├─ Validate: GeoLocation, AwareDatetime, audio_base64
  ├─ Action: store.add_telemetry() → StoredTelemetry
  └─ Response: TelemetryResponse(status="accepted", analysis=None)  # BE-1段階
```

#### alerts.py (BE-6)
```python
GET /api/v1/alerts
  ├─ Query: level (1-3 深刻度), limit
  ├─ Action: store.list_alerts() + _to_alert_summary()
  └─ Response: list[AlertSummary] (深刻度降順)

GET /api/v1/alerts/{telemetry_id}
  ├─ Param: telemetry_id
  ├─ Action: 
  │   ├─ store.get(telemetry_id) → StoredTelemetry
  │   ├─ ledger.find_pipe_by_hydrant(hydrant_id) → PipeRecord
  │   ├─ get_pipe_age() → age_years
  │   └─ _build_pipe_info() → PipeInfo ★ material型
  └─ Response: AlertDetail (404 if not found)

POST /api/v1/alerts/{telemetry_id}/work-order
  └─ Response: 501 Not Implemented (BE-5スタブ)
```

#### sensors.py (FE連携)
```python
GET /api/v1/sensors
  └─ Response: list[SensorInfo]

GET /api/v1/sensors?format=geojson
  └─ Response: GeoJSONFeatureCollection (Leaflet用)
```

### 3. Services (Business Logic)

#### ledger.py (BE-4)
```python
_haversine_km(lat1, lng1, lat2, lng2) → float  # 大円距離計算

get_pipes() → list[PipeRecord]                  # @lru_cache マスタ読込
  ├─ _load_pipes(PIPES_PATH) → validation
  └─ FileNotFoundError, JSONDecodeError 伝播

find_pipe_by_hydrant(hydrant_id) → PipeRecord|None
  └─ 消火栓ID で配管検索

find_nearest_pipe(lat, lng) → PipeRecord|None
  └─ Haversine距離で最近接路線検索（FE-3での位置〜配管照合用将来機能）

get_pipe_age(installed_year) → int
  └─ 2026 - installed_year （デモ用固定基準年）
```

#### audio.py (BE-3)
```python
# 未実装スタブ
analyze_audio(audio_base64, sample_rate) → AnalysisResult
  ├─ FFT 解析（NumPy）
  ├─ 周波数スペクトル抽出
  ├─ 漏水帯域（通常 2-10 kHz）のエネルギー比
  └─ leak_confidence + severity_level 判定
```

### 4. Data Layer

#### store.py
```python
StoredTelemetry(dataclass)
  ├─ telemetry_id: str
  ├─ sensor_id, hydrant_id, received_at
  ├─ location: GeoLocation
  ├─ analysis: AnalysisResult (None if BE-3不実装)
  └─ (cached) analysis のための timestamp

Store(class)
  ├─ _records: dict[str, StoredTelemetry]  # threading.Lock で保護
  ├─ add_telemetry(req: TelemetryRequest) → StoredTelemetry
  ├─ get(telemetry_id) → StoredTelemetry|None
  ├─ list_alerts(level, limit) → list[StoredTelemetry]  # ソート済み
  └─ (private) _store_singleton (lazy init)

get_store() → Store  # @lru_cache singleton
```

#### JSON Master Files
```
pipes.json
  [
    {
      "pipe_id": "P-001",
      "material": "ductile_iron",
      "diameter_mm": 150,
      "installed_year": 1995,
      "burial_depth_m": 1.5,
      "route": {
        "type": "LineString",
        "coordinates": [[経度, 緯度], ...]
      },
      "hydrant_ids": ["H-001", "H-002", ...]
    },
    ...
  ]

hydrants.json
  [
    {
      "hydrant_id": "H-001",
      "sensor_id": "S-001",
      "name": "消火栓001",
      "latitude": 35.xxx,
      "longitude": 139.xxx,
      "pipe_id": "P-001"
    },
    ...
  ]
```

## コード分類

| ファイル | 分類 | 言語 | 目的 |
|---------|------|------|------|
| telemetry.py | Schema | Python | テレメトリ入出力契約 |
| alert.py | Schema | Python | アラート出力契約 ★型 |
| pipe.py | Schema | Python | 配管台帳スキーマ |
| telemetry.py (router) | Endpoint | Python | テレメトリ受信API |
| alerts.py | Endpoint | Python | アラート参照API ★フロー |
| sensors.py | Endpoint | Python | センサー参照API |
| ledger.py | Service | Python | 配管台帳ロジック |
| audio.py | Service | Python | FFT解析ロジック（BE-3） |
| store.py | Storage | Python | インメモリストア |
| dependencies.py | DI | Python | 依存関係注入 |
| main.py | Bootstrap | Python | FastAPI アプリ初期化 |

## 命名規則

### モジュール
- Snake case: `telemetry.py`, `ledger.py`
- 用途別ディレクトリ: schemas/, routers/, services/

### クラス/型
- Pascal case: `TelemetryRequest`, `PipeRecord`, `AlertDetail`
- Pydantic BaseModel サブクラス
- Type aliases (Literal): `SeverityLevel`, `PipeMaterial`, `PipeDiameterMm`

### 関数
- Snake case: `get_pipes()`, `find_pipe_by_hydrant()`, `get_pipe_age()`
- API ハンドラは動詞+名詞: `list_alerts()`, `get_alert_detail()`
- 内部ヘルパー: `_haversine_km()`, `_build_pipe_info()`

### 変数
- Snake case: `telemetry_id`, `hydrant_id`, `leak_confidence`
- 定数: UPPER_CASE: `REFERENCE_YEAR`, `EARTH_RADIUS_KM`, `STRICT_INPUT_CONFIG`

