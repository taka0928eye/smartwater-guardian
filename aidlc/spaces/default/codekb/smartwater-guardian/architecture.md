# SmartWater Guardian - システムアーキテクチャ

## アーキテクチャスタイル

**Hybrid Monolithic + API Microservices**
- バックエンド: FastAPI 単一プロセス（スケーラビリティは将来の継ぎ足し設計）
- フロントエンド: Next.js SPA（API に依存）
- データレイヤー: インメモリストア + JSON マスタファイル（本番 DB は out-of-scope）

## システム全体図

```
┌─────────────────────────────────────────────────────────────┐
│                     Web UI (FE)                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Next.js + React                                      │  │
│  │ - Leaflet 地図表示                                   │  │
│  │ - リアルタイムアラート一覧・詳細                     │  │
│  │ - GeoJSON センサー位置可視化                         │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTP/REST
                         ↓
┌────────────────────────────────────────────────────────────┐
│            Backend API (FastAPI / Python)                 │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Router Layer (app/routers/)                         │  │
│  │ - POST /api/v1/telemetry  ← センサーから音声受信  │  │
│  │ - GET /api/v1/alerts      ← アラート一覧参照      │  │
│  │ - GET /api/v1/alerts/{id} ← アラート詳細参照      │  │
│  │ - GET /api/v1/sensors     ← センサーマスタ参照    │  │
│  │ - GET /api/v1/sensors?format=geojson ← GeoJSON  │  │
│  └────────────────────┬────────────────────────────────┘  │
│                       │                                   │
│  ┌────────────────────┴────────────────────────────────┐  │
│  │ Service Layer                                       │  │
│  │ ┌──────────────────┐  ┌──────────────────────────┐ │  │
│  │ │ audio.py (BE-3)  │  │ ledger.py (BE-4)        │ │  │
│  │ │ FFT 解析・判定   │  │ 配管台帳照合・距離計算  │ │  │
│  │ │ 信頼度 → 深刻度 │  │ Haversine 距離          │ │  │
│  │ └──────────────────┘  └──────────────────────────┘ │  │
│  └────────────────────┬───────────────────────────────┘  │
│                       │                                   │
│  ┌────────────────────┴───────────────────────────────┐  │
│  │ Schema & Validation Layer (Pydantic v2)          │  │
│  │ - TelemetryRequest / TelemetryResponse           │  │
│  │ - AlertSummary / AlertDetail                    │  │
│  │ - PipeInfo / PipeRecord                         │  │
│  │ - SensorInfo, HydrantMaster, GeoJSON*          │  │
│  └────────────────────┬───────────────────────────────┘  │
│                       │                                   │
│  ┌────────────────────┴───────────────────────────────┐  │
│  │ Data Layer (app/store.py)                        │  │
│  │ - StoredTelemetry (インメモリ連想リスト)          │  │
│  │ - スレッド安全ロック機構                          │  │
│  │ - キャッシュされた get_store() インスタンス       │  │
│  └────────────────────┬───────────────────────────────┘  │
│                       │                                   │
│  ┌────────────────────┴───────────────────────────────┐  │
│  │ Master Data (JSON)                               │  │
│  │ - pipes.json (10路線、GeoJSON LineString)        │  │
│  │ - hydrants.json (消火栓マスタ)                   │  │
│  └────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

## コンポーネント関係図

### テレメトリ受信フロー（BE-1）
```
IoTセンサー
    ↓
POST /api/v1/telemetry (TelemetryRequest)
    ↓
TelemetryRequest バリデーション（Pydantic strict）
    ├─ Base64 解読チェック ✓
    ├─ AwareDatetime タイムゾーン検証 ✓
    └─ GeoLocation 範囲チェック ✓
    ↓
store.add_telemetry() → StoredTelemetry
    ↓
TelemetryResponse（status="accepted", analysis=null ※BE-1段階）
```

### アラート詳細取得フロー（BE-6）
```
GET /api/v1/alerts/{telemetry_id}
    ↓
store.get(telemetry_id) → StoredTelemetry
    ↓
AlertDetail 組み立て
    ├─ AlertSummary ベース（telemetry_id, sensor_id, hydrant_id, ...）
    ├─ location ← StoredTelemetry.location
    ├─ analysis ← StoredTelemetry.analysis (BE-3)
    └─ pipe_info ← ledger.find_pipe_by_hydrant(hydrant_id)
            ├─ PipeRecord.model_validate (BE-4)
            ├─ get_pipe_age() 計算
            └─ PipeInfo 組み立て ← ★型不整合ここ
    ↓
AlertDetail (JSON)
```

## パターンと慣行

### 1. 入力検証（Boundary Pattern）
- 全ての外部入力は Pydantic strict モード
- 未知フィールドは `extra="forbid"` で拒否
- Base64、座標範囲など明示的なバリデータ実装

### 2. キャッシング（Lazy Load）
- `@lru_cache(maxsize=1)` でマスタデータを初回ロード時だけ読み込み
- `app/store.get_store()` で singleton インスタンス返却
- `app/services/ledger.get_pipes()` で台帳キャッシュ

### 3. スレッド安全性
- FastAPI の同期ハンドラは ThreadPoolExecutor で実行
- `StoredTelemetry` リスト操作は `threading.Lock` で保護

### 4. エラーハンドリング
- ファイル欠損 `FileNotFoundError` → 伝播（呼び出し側で処理）
- JSON 破損 `JSONDecodeError` → `ValueError` に変換
- API エラーは HTTPException（404, 501 など）で応答

## データフロー（全体）

```
IoT Sensor (音声 + メタデータ)
    ↓
Backend (BE-1: telemetry 受信 / BE-3: AI判定 / BE-4: 台帳照合)
    ├─ TelemetryRequest バリデーション
    ├─ (将来) audio.py で FFT解析 → AnalysisResult
    ├─ store 保持
    └─ alerting 対象判定（深刻度）
    ↓
アラート集約 (GET /api/v1/alerts)
    ↓
Web UI (FE-3/FE-5)
    ├─ Leaflet 地図表示
    ├─ 一覧・詳細ドロワー
    └─ 配管情報・年数表示
```

## 設計上の決定と制約

| 項目 | 判定 | 理由 |
|------|------|------|
| インメモリストア | 制約 | 本番 DB は out-of-scope; デモ期間の簡易運用用 |
| JSON マスタファイル | 制約 | 本番 GIS DB は out-of-scope; デモ用固定台帳 |
| 単一プロセス (FastAPI) | 設計 | MVP 規模; 将来は Kubernetes 等での水平スケール |
| Pydantic v2 | 選択 | 厳密な入力検証が IoT データの信頼性に重要 |
| Haversine 距離 | 選択 | 緯度経度からの最近接配管検索精度（中国地方〜北東北）対応 |
| GeoJSON LineString | 標準 | Leaflet との連携; 座標順序は [経度, 緯度] 標準 |
| 非同期 I/O 未使用 | 制約 | I/O 待機が少ない（マスタファイルのみ）; async 化は過剰 |

