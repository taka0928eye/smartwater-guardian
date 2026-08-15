# SmartWater Guardian - 依存関係

## 外部依存

### Python（backend/requirements.txt・== ピン固定）

| パッケージ | バージョン | 用途 | 使用箇所 |
|------------|------------|------|----------|
| fastapi | 0.141.1 | Web フレームワーク | main.py・routers/* |
| pydantic | 2.13.4 | データ検証（v2 strict） | schemas/*・store.py |
| uvicorn | 0.52.1 | ASGI サーバー | 起動 |
| numpy | 2.5.2 | FFT / 数値演算 | services/audio.py |
| scipy | 1.18.0 | DSP（フィルタ・窓関数等） | services/audio.py |
| scikit-learn | 1.9.0 | SVM 漏水判定 | services/audio.py |
| joblib | 1.5.3 | 学習済みモデル読込 | services/audio.py（leak_svm_v1.joblib） |
| httpx | 0.28.1 | 外部 API クライアント | app/dependencies.py（HttpClientDep）→ services/orcarouter.py |
| python-dotenv | 1.2.2 | .env 読込 | main.py・orcarouter |
| pytest | 9.1.1 | テスト | tests/* |
| requests | 2.34.2 | 検証スクリプト | scripts/check_*.py 等 |
| boto3 | 1.43.72 | AWS SDK（S3クライアント） | services/dataset_sync.py（DEMO-2・AWS向けデータセット同期） |
| botocore | 1.43.72 | boto3 の低レベル実装 | boto3 の推移的依存（明示ピン） |

（annotated-doc / anyio / certifi / click / jmespath / python-dateutil / s3transfer / six 等は上記の推移的依存）

### npm（frontend/package.json）

**dependencies**
- `axios ^1.19.0`（lib/api.ts）
- `leaflet ^1.9.4` + `react-leaflet ^5.0.0`（components/map）
- `lucide-react ^1.31.0`（アイコン）
- `next 16.3.0` / `react 19.2.8` / `react-dom 19.2.8`
- `recharts ^3.10.1`（**使用中**・SpectrumChart / WaveformChart / FE-4）

**devDependencies**
- `typescript ^5` / `@types/*`（node/react/react-dom/leaflet）
- `vitest ^4.1.10` / `@vitest/coverage-v8 ^4.1.10`
- `@testing-library/react ^16.3.2` / `@testing-library/jest-dom ^7.0.1` / `@testing-library/dom ^10.4.1` / `jsdom ^30.0.1`
- `eslint ^9` / `eslint-config-next 16.3.0`
- `tailwindcss ^4` / `@tailwindcss/postcss ^4`
- `@playwright/test ^1.62.1`（E2E・scripts: `e2e` / `e2e:headed` / `e2e:debug` / `e2e:report` / `e2e:install`）

## 内部依存（パッケージ間）

### フロントエンド（page → api → backend）

```
page.tsx (Server Component)
  -> Header / DashboardClient / lib/api(fetchSensorsGeoJson)
DashboardClient.tsx (Client)
  -> useKpiPolling / useAlertPolling / useSensorPolling / useDisasterSummary
  -> SensorMap / DisasterOverlay / AlertList / AlertDetailDrawer / KpiSummary
  -> lib/api(seedDemoBatch, clearDemo)  # DEMO-2: シード投入・シードクリアボタン
useKpiPolling -> lib/api(fetchKpiSummary)  # refresh() あり（DEMO-2）
useAlertPolling -> lib/api(fetchAlerts)  # refresh() あり（DEMO-2）
useSensorPolling -> lib/api(fetchSensorsGeoJson)  # refresh() あり（DEMO-2）
useDisasterSummary -> lib/api(fetchDisasterSummary)  # refresh() あり
lib/api
  -> types/api (AlertSummary, AlertDetail, SensorInfo, WorkOrder, KpiSummary, ...)
  -> types/sensor (SensorFeatureCollection)
  -> types/disaster (DisasterSummary, DisasterCluster, ...)
  -> types/demo (DemoSeedBatchResponse, DemoClearResponse)  # DEMO-2
KpiSummary -> lib/severity (getSeverityMeta) / BusinessModelDocLink / props KpiSummary
BusinessModelDocLink -> app/api/docs/business-model/route.ts (fetch)
AlertList -> lib/alertSort / SeverityBadge
AlertDetailDrawer -> lib/api (fetchAlertDetail, createWorkOrder) / SpectrumChart / WaveformChart / WorkOrderModal
SensorMap/SensorMapInner -> lib/severity (getSeverityColor) / types/sensor
DisasterOverlay -> types/disaster / react-leaflet
```

### バックエンド（routers → services → store / schemas）

```
main.py
  -> routers/telemetry | alerts | sensors | kpi | disaster | demo
  -> services/dataset_sync (sync_dataset_from_s3)  # lifespan: DEMO_DATASET_S3_URI 設定時のみ（DEMO-2）
  -> store(initialize_sensors)  # lifespan: 起動時に23件Lv0構築（DEMO-2）
routers/telemetry
  -> services/audio (analyze_audio, AudioValidationError) / schemas/telemetry / store
routers/demo
  -> services/audio (analyze_audio) / services/demo_seed (run_seed_batch, DemoSeedError)  # DEMO-2
  -> schemas/demo (DemoSeedRequest, DemoSeedBatchResponse) / schemas/telemetry / store
routers/alerts
  -> schemas/alert / store / services/ledger / services/orcarouter (create_work_order)
routers/sensors
  -> schemas/alert / store / schemas/telemetry(GeoLocation)
routers/kpi
  -> schemas/kpi / services/kpi(calculate_kpi_summary)
routers/disaster
  -> services/audio (analyze_audio) / services/disaster_signal (generate_level3_signal)  # DEMO-2
  -> schemas/disaster / store(get_hydrants, register_disaster_sensors, get_disaster_sensor_ids) / schemas/telemetry
services/audio
  -> schemas/telemetry(AnalysisResult, SpectrumPoint) / models/leak_svm_v1.joblib / scipy / sklearn / joblib
services/demo_seed
  -> services/audio(analyze_audio) / store(get_hydrants, clear_disaster_state) / backend/dataset/（DEMO-2）
services/disaster_signal
  -> numpy（DEMO-2・外部ファイル非依存）
services/dataset_sync
  -> boto3 / botocore（DEMO-2）
services/orcarouter
  -> schemas/work_order(WorkOrder, RepairPart) / schemas/alert / schemas/pipe / services/prompts
  -> services/llm_cost (calculate_and_enrich_cost) / app/dependencies(HttpClientDep)
  -> app/data/repair_parts.json (@lru_cache)
services/llm_cost -> schemas/work_order / logger
services/kpi
  -> schemas/kpi / store(get_store, get_hydrants) / schemas/telemetry(SeverityLevel)
services/ledger
  -> schemas/pipe(PipeRecord) / data/pipes.json
store
  -> schemas/alert(HydrantMaster) / schemas/telemetry(AnalysisResult, GeoLocation) / data/hydrants.json
schemas/alert -> schemas/telemetry(SeverityLevel, GeoLocation, AnalysisResult, STRICT_INPUT_CONFIG) / schemas/pipe(PipeMaterial)
schemas/work_order -> （独立・STRICT_CONFIG）
schemas/disaster -> （独立・strict）
schemas/demo  -> schemas/telemetry(TelemetryRequest, SeverityLevel)
schemas/kpi  -> schemas/telemetry(STRICT_INPUT_CONFIG)
schemas/pipe -> schemas/telemetry(STRICT_INPUT_CONFIG)
```

### フロント ↔ バックエンドの契約境界

- バックエンドは snake_case（Pydantic）、フロントは camelCase。変換は `lib/api.ts` の `unwrap()` が 1 回実施
- 型対応: `KpiSummary`(BE) ↔ `KpiSummary`(FE・**整合済み**)、`AlertSummary/Detail` ↔ `types/api.ts`、
  `SensorFeatureCollection` ↔ `types/sensor.ts`、`DisasterSummary` ↔ `types/disaster.ts`、`WorkOrder` ↔ `types/api.ts`

## データ依存

### マスタデータ（JSON）

| ファイル | 内容 | 読込元 | キャッシュ |
|----------|------|--------|------------|
| `backend/app/data/hydrants.json` | 消火栓マスタ（20 件） | store.get_hydrants() | `@lru_cache(maxsize=1)` |
| `backend/app/data/pipes.json` | 配管台帳（10 路線・GeoJSON LineString） | ledger.get_pipes() | `@lru_cache(maxsize=1)` |
| `backend/app/data/repair_parts.json` | 補修部材マスタ（フォールバック WorkOrder 用） | orcarouter._load_repair_parts() | `@lru_cache(maxsize=1)` |
| `backend/dataset/*.wav`（**git管理外**） | Zenodo由来の実音響4本（no-leak/leak×level1-3） | services/demo_seed.py（シード投入） | なし（ファイル読込のたび） |

### 学習済みモデル

| ファイル | 内容 | 読込元 | 検証 |
|----------|------|--------|------|
| `backend/app/models/leak_svm_v1.joblib` | 漏水判定 SVM | services/audio._load_model() | metadata.json の期待 SHA-256 と照合（不一致は例外） |

### ランタイムデータ（インメモリ）

- `Store._records: deque[StoredTelemetry]`（maxlen=500・`threading.Lock` 保護）
- `Store._index: dict[telemetry_id, StoredTelemetry]` / `Store._sensor_latest: dict[sensor_id, StoredTelemetry]`
- `Store._disaster_sensor_ids: set[str]`（DEMO-2・防災シミュレーションで選出された sensor_id の累積記録。
  `/disaster/summary` の対象抽出に使用。旧 `/tmp/disaster_simulated_items.json` 一時ファイルキャッシュは廃止）
- `orcarouter._work_order_cache`（LLM 成功時のみ・`asyncio.Lock` 直列化）
- プロセス再起動で消える（MVP スコープ）。起動時 `lifespan` が `initialize_sensors()` で
  23件Lv0の初期状態を自動再構築する（DEMO-2）

## 依存関係の監査

| 項目 | 結果 |
|------|------|
| 循環依存 | なし（クリーンな DAG） |
| 未使用 import | なし（scipy / scikit-learn / joblib / recharts / HttpClientDep はすべて実使用） |
| 重複定義 | なし（`SeverityLevel` は lib/severity.ts が単一ソース・types/api.ts は re-export。FE-7 で解消済み） |
| 破壊的変更リスク | `lib/severity.ts` の `SeverityLevel` を変更する場合、`types/api.ts` 経由の import 元に影響。`_work_order_cache` のキー設計変更は並行安全の再検証が必要 |
