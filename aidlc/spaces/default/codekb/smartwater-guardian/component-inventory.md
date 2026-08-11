# SmartWater Guardian - コンポーネントインベントリ

## Backend Components (Python/FastAPI)

### 1. Routing Layer (FastAPI Routers)

#### telemetry.py
- **Responsibility**: IoT音響テレメトリの受信・検証・保存
- **Endpoints**:
  - `POST /api/v1/telemetry` — テレメトリ受信
- **Dependencies**: TelemetryRequest, TelemetryResponse, store
- **Related**: BE-1 stage

#### alerts.py
- **Responsibility**: アラート一覧・詳細の参照、配管情報の付与
- **Endpoints**:
  - `GET /api/v1/alerts` — 一覧（深刻度降順）
  - `GET /api/v1/alerts/{telemetry_id}` — 詳細（pipe_info自動付与）
  - `POST /api/v1/alerts/{telemetry_id}/work-order` — 工事発注（501 stub）
- **Dependencies**: AlertSummary, AlertDetail, PipeInfo, ledger.find_pipe_by_hydrant
- **Key Functions**:
  - `_build_pipe_info()` — PipeRecord から PipeInfo 構築 ★型不整合箇所
  - `_to_alert_summary()` — StoredTelemetry を一覧行に変換
- **Related**: BE-6 stage

#### sensors.py
- **Responsibility**: センサー・マスタ情報の参照（FE連携用GeoJSON含む）
- **Endpoints**:
  - `GET /api/v1/sensors` — SensorInfo 一覧
  - `GET /api/v1/sensors?format=geojson` — GeoJSONFeatureCollection
- **Dependencies**: SensorInfo, HydrantMaster, GeoJSONPoint
- **Related**: FE-3/FE-5 連携

---

### 2. Business Logic Layer (Services)

#### ledger.py (BE-4: 配管台帳照合)
- **Responsibility**: 疑似GIS配管台帳の参照・検索・年数計算
- **Functions**:
  - `get_pipes()` → list[PipeRecord] — @lru_cache マスタ読込
  - `find_pipe_by_hydrant(hydrant_id)` → PipeRecord|None — 消火栓 ID で検索
  - `find_nearest_pipe(lat, lng)` → PipeRecord|None — 座標から Haversine 距離検索
  - `get_pipe_age(installed_year)` → int — 経過年数計算（基準年2026）
  - `_haversine_km()` — 大円距離計算ユーティリティ
- **Dependencies**: PipeRecord, Path
- **Data Source**: app/data/pipes.json （GeoJSON LineString ジオメトリ）
- **Cache**: @lru_cache(maxsize=1) — 初回呼び出し時のみ読込
- **Error Handling**: FileNotFoundError（伝播）、JSONDecodeError → ValueError

#### audio.py (BE-3: FFT解析)
- **Status**: 未実装スタブ
- **Intended Responsibility**: 音響信号の周波数解析・漏水判定
- **Functions** (plan):
  - `analyze_audio(audio_base64, sample_rate)` → AnalysisResult
  - FFT（NumPy）で周波数スペクトル抽出
  - 2-10 kHz 帯域のエネルギー検出
  - leak_confidence + severity_level 判定
- **Dependencies**: NumPy, SciPy, AnalysisResult
- **Related**: BE-3 stage（future implementation）

---

### 3. Data Validation Layer (Pydantic Schemas)

#### telemetry.py
- **SeverityLevel** = Literal[0, 1, 2, 3]
- **STRICT_INPUT_CONFIG** = ConfigDict(strict=True, extra="forbid")
- **GeoLocation**: lat/lng 範囲チェック
- **TelemetryRequest**: IoT入力（Base64 audio, AwareDatetime）
  - Validators: audio_base64 デコード検証
- **AnalysisResult**: FFT 判定結果（leak_confidence, severity_level, spectrum）
- **TelemetryResponse**: 受信確認応答
- **SpectrumPoint**: 周波数-振幅ペア

#### alert.py
- **AlertSummary**: 一覧行（telemetry_id, sensor_id, hydrant_id, severity_level, leak_confidence, detected_at）
- **PipeInfo**: 配管情報 ★ `material: str` (要修正 → PipeMaterial)
  - Fields: pipe_id, material ⚠️, diameter_mm, installed_year, burial_depth_m, age_years
  - Docstring: "BE-6では常に null"（陳腐化 — BE-4実装で状態変化）
- **AlertDetail** = AlertSummary + location + analysis + pipe_info|None
- **SensorInfo**: センサー・マスタ統合
- **HydrantMaster**: 消火栓マスタ行
- **GeoJSONPoint, SensorProperties, SensorFeature, SensorFeatureCollection**: GeoJSON形式

#### pipe.py
- **PipeMaterial** = Literal["ductile_iron", "cast_iron", "pvc", "steel"]
- **PipeDiameterMm** = Literal[75, 100, 150, 200]
- **GeoJSONLineString**: 路線ジオメトリ（座標 [lng, lat] 範囲チェック）
  - Validators: _validate_vertices() で [lng, lat] 2要素、範囲内を検証
- **PipeRecord**: 台帳1路線
  - Fields: pipe_id, material (PipeMaterial), diameter_mm (PipeDiameterMm), installed_year, burial_depth_m, route (GeoJSONLineString), hydrant_ids (list[str])

---

### 4. Data Storage Layer

#### store.py
- **StoredTelemetry** (dataclass): インメモリ保持レコード
  - telemetry_id, sensor_id, hydrant_id, received_at, location, analysis (AnalysisResult|None)
- **Store** (class): 連想配列型ストア
  - `_records: dict[str, StoredTelemetry]` — threading.Lock で保護
  - `add_telemetry(req: TelemetryRequest)` → StoredTelemetry
  - `get(telemetry_id)` → StoredTelemetry|None
  - `list_alerts(level, limit)` → list[StoredTelemetry] （深刻度降順）
- **get_store()** → Store — singleton (lazy init, @lru_cache)

---

### 5. Master Data Files

#### app/data/pipes.json
- **Content**: 配管台帳（10路線）
- **Schema**: 
  ```json
  [
    {
      "pipe_id": "P-001",
      "material": "ductile_iron" | "cast_iron" | "pvc" | "steel",
      "diameter_mm": 75 | 100 | 150 | 200,
      "installed_year": 1965-2015,
      "burial_depth_m": > 0.0,
      "route": {
        "type": "LineString",
        "coordinates": [[lng, lat], [lng, lat], ...]
      },
      "hydrant_ids": ["H-001", "H-002", ...]
    }
  ]
  ```
- **Usage**: ledger.get_pipes() でキャッシュ読込
- **Validation**: Pydantic PipeRecord.model_validate()

#### app/data/hydrants.json
- **Content**: 消火栓マスタ
- **Schema**:
  ```json
  [
    {
      "hydrant_id": "H-001",
      "sensor_id": "S-001",
      "name": "消火栓001",
      "latitude": -90 to 90,
      "longitude": -180 to 180,
      "pipe_id": "P-001"
    }
  ]
  ```
- **Usage**: sensors.py で参照（SensorInfo組み立て）
- **Validation**: Pydantic HydrantMaster.model_validate()

---

### 6. Dependency Injection & Bootstrap

#### dependencies.py
- **Purpose**: DI コンテナ、共有リソース定義
- **Exports**: Depends() ターゲット関数

#### main.py
- **Purpose**: FastAPI アプリ初期化
- **Config**: CORS、middleware設定
- **Routers**: app.include_router() で各ルーター登録

---

## Frontend Components (Next.js/React)

### Web UI Layer

#### app/ (Next.js App Router)
- **Purpose**: ページレイアウト、API統合
- **Pages**: /alerts, /sensors 等

#### components/
- **AlertList.tsx**: アラート一覧表示
- **AlertDetail.tsx**: 詳細ドロワー（pipe_info含む）
- **Map.tsx**: Leaflet 地図（GeoJSON センサー位置）

### Styling & Design System

- **Tailwind CSS**: スタイリング
- **Lucide React**: アイコン
- **Leaflet 5.0.0 + react-leaflet**: 地図表示

---

## Dependencies Graph

```
telemetry.py (router)
  ├─ TelemetryRequest/Response (schemas/telemetry.py)
  └─ store.py → StoredTelemetry

alerts.py (router)
  ├─ AlertSummary/AlertDetail (schemas/alert.py)
  ├─ PipeInfo (schemas/alert.py) ★
  ├─ ledger.find_pipe_by_hydrant() (services/ledger.py)
  │   ├─ PipeRecord (schemas/pipe.py)
  │   └─ app/data/pipes.json
  └─ store.py → StoredTelemetry

sensors.py (router)
  ├─ SensorInfo (schemas/alert.py)
  ├─ HydrantMaster (schemas/alert.py)
  └─ app/data/hydrants.json

ledger.py (service)
  ├─ PipeRecord (schemas/pipe.py)
  └─ app/data/pipes.json

store.py
  ├─ StoredTelemetry (dataclass)
  ├─ AnalysisResult (schemas/telemetry.py)
  └─ threading.Lock

main.py (bootstrap)
  ├─ FastAPI
  ├─ routers (telemetry, alerts, sensors)
  └─ CORS middleware
```

---

## Ownership Matrix

| Component | Owner | Status | Maintenance |
|-----------|-------|--------|-------------|
| telemetry.py | aidlc-developer-agent | ✓ BE-1 | テレメトリ受信 |
| alerts.py | aidlc-developer-agent | ✓ BE-6 | アラート API ★PipeInfo型 |
| sensors.py | aidlc-developer-agent | ✓ | センサーAPI |
| ledger.py | aidlc-developer-agent | ✓ BE-4 | 配管台帳検索 |
| audio.py | aidlc-developer-agent | ⊘ BE-3 | FFT解析（未実装） |
| schemas/telemetry.py | aidlc-developer-agent | ✓ | 共有スキーマ |
| schemas/alert.py | aidlc-developer-agent | ✓ BE-6 | アラートスキーマ ★型不整合 |
| schemas/pipe.py | aidlc-developer-agent | ✓ BE-4 | 配管台帳スキーマ |
| store.py | aidlc-developer-agent | ✓ | ストア実装 |
| Web UI (FE) | Team | ✓ FE-3/FE-5 | Leaflet・リアルタイム |
| CI/CD | Team | ✓ GitHub Actions | テスト・カバレッジ |

