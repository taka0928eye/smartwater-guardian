# SmartWater Guardian - 依存関係

## 外部依存

### Python（backend/requirements.txt・== ピン固定）

| パッケージ | バージョン | 用途 | 使用箇所 |
|------------|------------|------|----------|
| fastapi | 0.141.1 | Web フレームワーク | main.py・routers/* |
| pydantic | 2.13.4 | データ検証（v2 strict） | schemas/*・store.py |
| uvicorn | 0.52.1 | ASGI サーバー | 起動 |
| numpy | 2.5.2 | FFT モック解析 | routers/telemetry.py |
| scipy | 1.18.0 | （未使用）BE-3 予定 | - |
| httpx | 0.28.1 | 外部 API クライアント | app/dependencies.py（未使用） |
| python-dotenv | 1.2.2 | .env 読込 | 環境設定 |
| pytest | 9.1.1 | テスト | tests/* |
| requests | 2.34.2 | 検証スクリプト | scripts/check_*.py 等 |

（annotated-doc / anyio / certifi / click 等は上記の推移的依存）

### npm（frontend/package.json）

**dependencies**
- `axios ^1.19.0`（lib/api.ts）
- `leaflet ^1.9.4` + `react-leaflet ^5.0.0`（components/map）
- `lucide-react ^1.31.0`（アイコン）
- `next 16.3.0` / `react 19.2.8` / `react-dom 19.2.8`
- `recharts ^3.10.1`（**import 未使用**・FE-4 予定）

**devDependencies**
- `typescript ^5` / `@types/*`（node/react/react-dom/leaflet）
- `vitest ^4.1.10` / `@vitest/coverage-v8 ^4.1.10`
- `@testing-library/react ^16.3.2` / `@testing-library/jest-dom ^7.0.1` / `@testing-library/dom ^10.4.1` / `jsdom ^30.0.1`
- `eslint ^9` / `eslint-config-next 16.3.0`
- `tailwindcss ^4` / `@tailwindcss/postcss ^4`

## 内部依存（パッケージ間）

### フロントエンド（page → api → backend）

```
page.tsx (Server Component)
  -> Header / KpiSummary / DashboardClient / lib/api(fetchSensorsGeoJson)
DashboardClient.tsx (Client)
  -> useAlertPolling / SensorMap / AlertList / AlertDetailDrawer
useAlertPolling
  -> lib/api(fetchAlerts)
lib/api
  -> types/api (AlertSummary, AlertDetail, SensorInfo, WorkOrder, ...)
  -> types/sensor (SensorFeatureCollection)
KpiSummary
  -> lib/severity (getSeverityMeta) / props KpiData
AlertList -> lib/alertSort / SeverityBadge
SensorMap/SensorMapInner -> lib/severity (getSeverityColor) / types/sensor
AlertDetailDrawer -> lib/api (fetchAlertDetail)
```

### バックエンド（routers → store / services / schemas）

```
main.py
  -> routers/telemetry | alerts | sensors | kpi
routers/telemetry
  -> schemas/telemetry / store(get_store, StoredTelemetry)
routers/alerts
  -> schemas/alert / store(get_store) / services/ledger(find_pipe_by_hydrant, get_pipe_age)
routers/sensors
  -> schemas/alert / store(get_store, get_hydrants) / schemas/telemetry(GeoLocation)
routers/kpi
  -> schemas/kpi / services/kpi(calculate_kpi_summary)
services/kpi
  -> schemas/kpi / store(get_store, get_hydrants) / schemas/telemetry(SeverityLevel)
services/ledger
  -> schemas/pipe(PipeRecord) / data/pipes.json
store
  -> schemas/alert(HydrantMaster) / schemas/telemetry(AnalysisResult, GeoLocation) / data/hydrants.json
schemas/alert -> schemas/telemetry(SeverityLevel, GeoLocation, AnalysisResult, STRICT_INPUT_CONFIG) / schemas/pipe(PipeMaterial)
schemas/kpi  -> schemas/telemetry(STRICT_INPUT_CONFIG)
schemas/pipe -> schemas/telemetry(STRICT_INPUT_CONFIG)
```

### フロント ↔ バックエンドの契約境界

- バックエンドは snake_case（Pydantic）、フロントは camelCase。変換は `lib/api.ts` の `unwrap()` が 1 回実施
- 型対応: `KpiSummary`(BE) ↔ `KpiData`(FE・**要整合**)、`AlertSummary/Detail` ↔ `types/api.ts`、
  `SensorFeatureCollection` ↔ `types/sensor.ts`
- **FE-7 ギャップ**: バックエンド `GET /api/v1/kpi/summary`（7 フィールド）は実装済みだが、
  `lib/api.ts` に `fetchKpiSummary` がなく、`KpiData` 型も契約と乖離している

## データ依存

### マスタデータ（JSON）

| ファイル | 内容 | 読込元 | キャッシュ |
|----------|------|--------|------------|
| `backend/app/data/hydrants.json` | 消火栓マスタ（10 件） | store.get_hydrants() | `@lru_cache(maxsize=1)` |
| `backend/app/data/pipes.json` | 配管台帳（10 路線・GeoJSON LineString） | ledger.get_pipes() | `@lru_cache(maxsize=1)` |

### ランタイムデータ（インメモリ）

- `Store._records: deque[StoredTelemetry]`（maxlen=500・`threading.Lock` 保護）
- `Store._index: dict[telemetry_id, StoredTelemetry]` / `Store._sensor_latest: dict[sensor_id, StoredTelemetry]`
- プロセス再起動で消える（MVP スコープ）

## 依存関係の監査

| 項目 | 結果 |
|------|------|
| 循環依存 | なし（クリーンな DAG） |
| 未使用 import | `scipy`（BE-3 予定）・`recharts`（FE-4 予定）・`HttpClientDep`（BE-5 予定） |
| 重複定義 | `SeverityLevel` が `types/api.ts` と `lib/severity.ts` の 2 箇所（単一ソース化方針は確定済み） |
| 破壊的変更リスク | `types/api.ts` の `SeverityLevel` を re-export に変える際、import 元の影響確認が必要 |
