# SmartWater Guardian - コンポーネントインベントリ

本インベントリの H2 見出しはスコープ検証（codekb-scope-diff）と正規表現で照合される。見出し文言を変更しないこと。

## FastAPI App (main.py)

- **責務**: FastAPI アプリの初期化。CORS ミドルウェア設定、4 ルーターの登録、ヘルスチェック `GET /`
- **依存**: FastAPI / CORSMiddleware / app.routers.{alerts,kpi,sensors,telemetry}
- **注記**: `allow_origins=["http://localhost:3000"]` は開発用に硬コード

## Router: telemetry.py

- **責務**: `POST /api/v1/telemetry` で音響テレメトリを受信・検証し、モック FFT 解析してストアに登録する
- **主要関数**: `_decode_pcm16()` / `_periodogram()` / `_downsample_spectrum()` / `_band_energy_ratio()` / `_classify_severity()` / `_analyze_audio_mock()` / `ingest_telemetry()`
- **依存**: schemas/telemetry（TelemetryRequest / TelemetryResponse / AnalysisResult / SpectrumPoint / SeverityLevel）、store（get_store / StoredTelemetry）、NumPy
- **関連**: BE-1（受信）＋ BE-6（モック解析）。BE-3（audio.py 本実装）で置き換え予定
- **注記**: 同期 `def`（FFT は CPU バウンド → スレッドプール実行）。空音声は 422

## Router: alerts.py

- **責務**: アラート一覧・詳細の参照、配管台帳照合による pipe_info 付与、工事発注 501 スタブ
- **主要関数**: `_build_pipe_info()` / `_to_alert_summary()` / `list_alerts()` / `get_alert_detail()` / `create_work_order()`
- **依存**: schemas/alert（AlertSummary / AlertDetail / PipeInfo）、services/ledger（find_pipe_by_hydrant / get_pipe_age）、store（get_store / StoredTelemetry）
- **関連**: BE-6。`_build_pipe_info()` は PipeInfo 組み立ての要

## Router: sensors.py

- **責務**: `GET /api/v1/sensors` で消火栓マスタ + 最新センサー状態を返す。`?format=geojson` で Leaflet 用 FeatureCollection
- **主要関数**: `_derive_status()` / `_to_sensor_info()` / `_to_sensor_feature()` / `list_sensors()`
- **依存**: schemas/alert（SensorInfo / HydrantMaster / GeoJSON 型一式）、schemas/telemetry（GeoLocation）、store（get_store / get_hydrants / StoredTelemetry）
- **関連**: FE-3 / FE-5。座標は [経度, 緯度] 順

## Router: kpi.py

- **責務**: `GET /api/v1/kpi/summary` で KPI サマリ（推定削減コスト）を返す（BE-8）
- **主要関数**: `get_kpi_summary()`
- **依存**: schemas/kpi（KpiSummary）、services/kpi（calculate_kpi_summary）
- **注記**: 組み立てはサービスで完結。空ストア・例外時も 200 を返す（500 にしない）

## Store (store.py)

- **責務**: 解析済みテレメトリを保持するスレッドセーフなインメモリストア（BE-6）
- **主要要素**: `StoredTelemetry`（Pydantic・frozen / strict / extra=forbid）/ `InMemoryStore`（`deque(maxlen=500)` + `dict` 索引 + `threading.Lock`）/ `get_store()` / `reset_store()` / `get_hydrants()`（`@lru_cache`）
- **主要メソッド**: `add()` / `get()` / `list_alerts()` / `latest_sensor_states()` / `clear()`
- **依存**: schemas/alert（HydrantMaster）、schemas/telemetry（AnalysisResult / GeoLocation）、data/hydrants.json
- **設計判断**: 満杯時は最古を索引と同期して破棄。`sensor_latest` は破棄しない（デモでマーカーを消さない非対称設計）

## Service: ledger.py

- **責務**: 疑似 GIS 配管台帳（pipes.json・10 路線）の照合サービス（BE-4）
- **主要関数**: `get_pipes()` / `find_pipe_by_hydrant()` / `find_nearest_pipe()` / `get_pipe_age()` / `_haversine_km()` / `_load_pipes()`
- **依存**: schemas/pipe（PipeRecord）、data/pipes.json、functools.lru_cache
- **注記**: `find_nearest_pipe` は各路線の LineString 頂点との Haversine 最小距離で判定。欠損は FileNotFoundError 伝播、破損は JSONDecodeError → ValueError

## Service: kpi.py

- **責務**: KPI「推定削減コスト」の算定（BE-8・docs/business-model.md §3）
- **主要関数**: `expected_cost_saved(severity_level)` / `calculate_kpi_summary()`
- **算定定数**: `C_BURST=1,200,000` / `C_REPAIR_LEVEL1=185,000` / `C_REPAIR_LEVEL2=320,000` / `P_LEVEL1=0.12` / `P_LEVEL2=0.35` / `C_RESPONSE_SAVED=150,000` / `KPI_ASSUMPTION_DOC`
- **依存**: schemas/kpi（KpiSummary）、schemas/telemetry（SeverityLevel）、store（get_store / get_hydrants）
- **注記**: `get_store()` はハンドラ実行時に呼ぶ（import 時捕捉はテスト隔離を壊す）。Level 0 は集計対象外。`round()` で整数化

## Schemas (Pydantic v2)

- **責務**: 外部契約の境界。strict（`STRICT_INPUT_CONFIG` = `strict=True` + `extra="forbid"`）を共通利用
- **schemas/telemetry.py**: `SeverityLevel = Literal[0,1,2,3]` / `STRICT_INPUT_CONFIG` / `GeoLocation` / `TelemetryRequest`（Base64 検証・AwareDatetime）/ `SpectrumPoint` / `AnalysisResult` / `TelemetryResponse`
- **schemas/alert.py**: `AlertSummary` / `PipeInfo`（material は PipeMaterial）/ `AlertDetail` / `SensorInfo`（status は Literal 5 値）/ `HydrantMaster` / `GeoJSONPoint` / `SensorProperties` / `SensorFeature` / `SensorFeatureCollection`
- **schemas/pipe.py**: `PipeMaterial = Literal["ductile_iron","cast_iron","pvc","steel"]` / `PipeDiameterMm = Literal[75,100,150,200]` / `GeoJSONLineString`（頂点検証）/ `PipeRecord`
- **schemas/kpi.py**: `KpiSummary`（7 フィールド・`ge=0`）。`today_detections` は契約外（D-3）
- **依存**: Pydantic v2 / datetime / typing。pipe.py は telemetry.py の STRICT_INPUT_CONFIG を再利用

## Frontend Page (page.tsx)

- **責務**: ダッシュボードルート（Server Component・`force-dynamic`）。GeoJSON 取得とフォールバック、各コンポーネント配置
- **主要要素**: `MOCK_KPI_DATA`（モック KPI・**FE-7 で撤去予定**）/ `FALLBACK_SENSOR_FEATURES`（GeoJSON フォールバック）/ `Home()`
- **依存**: components/dashboard（Header / KpiSummary / DashboardClient）、lib/api（fetchSensorsGeoJson）、types/sensor
- **関連**: FE-2 / FE-3 / FE-5 / FE-7。`'use client'` を付けない（Server Component 維持）

## DashboardClient.tsx

- **責務**: ダッシュボード本体（Client Component）。アラート・地図・一覧・ドロワーの選択状態を束ねる
- **主要要素**: `ALERT_POLL_INTERVAL_MS = 5000` / `useAlertPolling()` / `selectedAlertId` 状態 / `handleSelectMarker()`
- **依存**: hooks/useAlertPolling、components/map/SensorMap、components/alert/AlertList / AlertDetailDrawer、types/sensor
- **関連**: FE-5 / FE-7。**FE-7 では KPI ポーリング（fetchKpiSummary）と KpiSummary 描画をここに配線する**

## KpiSummary.tsx

- **責務**: KPI サマリ 5 枚の監視カード表示（Server Component・表示専用）
- **主要要素**: `KpiData` 型 / `formatManYen()`（万円表記）/ `KpiCard` / `KpiSummary()`
- **依存**: lib/severity（getSeverityMeta）、prop `kpiData`
- **関連**: FE-2 / FE-7。`KpiData` は現状バックエンド契約と乖離（`level1Count` 欠如・`todayDetections` 契約外）

## Header.tsx

- **責務**: ダッシュボード上部のヘッダー表示（`useSyncExternalStore` で時刻を更新）
- **依存**: React（useSyncExternalStore）
- **関連**: FE-2

## AlertList.tsx

- **責務**: アラート一覧の表示（深刻度降順・新着順、Level 0 フィルタ、「正常も表示」トグル）
- **依存**: components/common/SeverityBadge、lib/alertSort（sortAlerts / filterLevelZero）、types/api（AlertSummary）
- **関連**: FE-5

## AlertDetailDrawer.tsx

- **責務**: 選択中アラートの詳細ドロワー表示（解析結果・配管情報 pipe_info 含む）
- **依存**: lib/api（fetchAlertDetail）、types/api（AlertDetail）
- **関連**: FE-5。選択が変わるたび `key` で再マウントし loading 状態をリセット

## SeverityBadge.tsx

- **責務**: 深刻度レベルを表す共通バッジ
- **依存**: lib/severity（getSeverityMeta / getSeverityBadgeClass）、types/api（SeverityLevel）
- **関連**: FE-5 共通 UI

## SensorMap.tsx / SensorMapInner.tsx

- **責務**: Leaflet センサー地図。SensorMap は `dynamic(..., { ssr: false })` でクライアント専用化し、SensorMapInner が `MapContainer` / `GeoJSON` を描画
- **主要関数**: `calculateMapView` / `pointToLayer`（XSS エスケープ含む）
- **依存**: react-leaflet / leaflet / lib/severity（getSeverityColor）/ types/sensor（SensorFeatureCollection）
- **関連**: FE-3。座標は [lng, lat] → Leaflet LatLng の逆順変換をここで実施

## useAlertPolling.ts

- **責務**: アラートのポーリングを担うカスタムフック（DashboardClient から抽出）
- **主要要素**: `useAlertPolling(intervalMs)` → `{ alerts, error, lastUpdatedAt }`
- **依存**: lib/api（fetchAlerts）、types/api（AlertSummary）
- **注記**: `useEffect` クリーンアップで `clearInterval` + `cancelled` フラグ。失敗時は最終状態を据え置く

## lib/api.ts

- **責務**: axios クライアントと API 関数群。snake_case→camelCase 変換と `ApiError` 変換を境界で 1 回実施
- **主要要素**: `apiClient`（baseURL / timeout 10s）/ `ApiError` / `toCamelCase` / `unwrap` / `fetchSensors` / `fetchSensorsGeoJson` / `fetchAlerts` / `fetchAlertDetail` / `createWorkOrder`
- **依存**: axios、types/api、types/sensor
- **関連**: FE-1 / FE-7。**`fetchKpiSummary` は未実装（FE-7 の対象）**

## lib/severity.ts

- **責務**: 漏水深刻度の表示メタ単一ソース（UI-1 深刻度カラー定義）
- **主要要素**: `SeverityLevel = 0|1|2|3` / `SeverityMeta` / `SEVERITY_META` / `getSeverityMeta` / `getSeverityLabel` / `getSeverityColor` / `getSeverityBadgeClass` / `getSeverityAccentClass`
- **依存**: なし（純粋モジュール）
- **関連**: FE-2 / FE-3 / FE-5。Tailwind v4 JIT のためクラス名はリテラル文字列で保持

## lib/alertSort.ts

- **責務**: アラート一覧の並び順・フィルタを担う純粋関数（AlertList から抽出）
- **主要関数**: `sortAlerts()`（深刻度降順 → 検知時刻降順）/ `filterLevelZero()`（Level 0 除外。includeLevelZero で全件）
- **依存**: types/api（AlertSummary）
- **関連**: FE-5。受け取った配列を変更しない（不変）

---

### コンポーネント間の主な依存グラフ

```
page.tsx
  -> Header / KpiSummary / DashboardClient / lib/api(fetchSensorsGeoJson)
DashboardClient
  -> useAlertPolling / SensorMap / AlertList / AlertDetailDrawer
useAlertPolling -> lib/api(fetchAlerts)
lib/api -> types/api / types/sensor
main.py -> routers(telemetry, alerts, sensors, kpi)
routers/telemetry -> store / schemas/telemetry
routers/alerts -> store / services/ledger / schemas/alert
routers/sensors -> store / schemas/alert
routers/kpi -> services/kpi / schemas/kpi
services/kpi -> store(get_store, get_hydrants) / schemas/kpi
services/ledger -> schemas/pipe / data/pipes.json
store -> data/hydrants.json / schemas/alert / schemas/telemetry
```

### オーナーシップ・マトリクス（Issue 対応）

| コンポーネント | 関連 Issue | 状態 |
|----------------|------------|------|
| Router: telemetry.py | BE-1 / BE-6 | 実装済み（モック解析） |
| Router: alerts.py | BE-6 | 実装済み |
| Router: sensors.py | BE-6 | 実装済み |
| Router: kpi.py | BE-8 | 実装済み |
| Store (store.py) | BE-6 | 実装済み |
| Service: ledger.py | BE-4 | 実装済み |
| Service: kpi.py | BE-8 | 実装済み |
| Frontend Page (page.tsx) | FE-2/3/5 / **FE-7** | **FE-7 でモック KPI 撤去・実データ配線** |
| DashboardClient.tsx | FE-5 / **FE-7** | **FE-7 で KPI ポーリング配線** |
| KpiSummary.tsx | FE-2 / **FE-7** | **FE-7 で KpiData 契約整合** |
| lib/api.ts | FE-1 / **FE-7** | **FE-7 で fetchKpiSummary 実装** |
| lib/severity.ts | FE-2/3/5 | 実装済み（単一ソース方針） |
