# SmartWater Guardian - API ドキュメント

## Base URL

```
http://localhost:8000
```

OpenAPI ドキュメントは FastAPI が自動生成（`/docs`）。

## 外部 API サマリ（バックエンド 7 エンドポイント）

| # | Method | Path | 目的 | 状態 |
|---|--------|------|------|------|
| 1 | GET | `/` | ヘルスチェック | 実装済み |
| 2 | POST | `/api/v1/telemetry` | 音響テレメトリ受信（モック解析付き） | 実装済み |
| 3 | GET | `/api/v1/alerts` | アラート一覧（深刻度降順） | 実装済み |
| 4 | GET | `/api/v1/alerts/{telemetry_id}` | アラート詳細（配管情報付与） | 実装済み |
| 5 | POST | `/api/v1/alerts/{telemetry_id}/work-order` | 工事発注書自動起票 | 501 スタブ（BE-5 未実装） |
| 6 | GET | `/api/v1/sensors?format=json|geojson` | センサー一覧（JSON / GeoJSON） | 実装済み |
| 7 | GET | `/api/v1/kpi/summary` | KPI サマリ（推定削減コスト） | 実装済み（BE-8） |

レスポンスはすべて snake_case（Pydantic v2）。フロントは `lib/api.ts` が camelCase へ変換する。

---

## 1. GET /

**Response 200**
```json
{ "message": "SmartWater Guardian API Ready" }
```

---

## 2. POST /api/v1/telemetry

疑似 IoT センサーからの音響テレメトリを受信・検証し、モック FFT 解析してストアに登録する。

**Request Body**（`TelemetryRequest`、strict / extra=forbid）
```json
{
  "sensor_id": "S-001",
  "hydrant_id": "H-001",
  "recorded_at": "2026-08-11T10:30:00+09:00",
  "location": { "latitude": 35.6762, "longitude": 139.7674 },
  "sample_rate_hz": 16000,
  "duration_sec": 10.5,
  "audio_base64": "//NExAAAAANIAAAyAABAAJAA...",
  "battery_pct": 85
}
```

**Validation**
- `sensor_id` / `hydrant_id`: 1〜64 文字
- `recorded_at`: AwareDatetime（タイムゾーン必須。strict はこのフィールドのみ外し TZ 必須で補強）
- `location.latitude` / `longitude`: 範囲チェック
- `sample_rate_hz`: 1〜192,000 / `duration_sec`: 0 < x <= 60
- `audio_base64`: 妥当な Base64（`b64decode(validate=True)` で検証）

**Response 200**（`TelemetryResponse`）
```json
{
  "telemetry_id": "tlm_1a2b3c4d5e6f",
  "sensor_id": "S-001",
  "received_at": "2026-08-11T01:30:15Z",
  "status": "accepted",
  "analysis": {
    "leak_confidence": 87.5,
    "severity_level": 2,
    "dominant_freq_hz": 900.0,
    "band_energy_ratio": 0.75,
    "spectrum": [ { "freq_hz": 0.0, "magnitude": 0.5 } ]
  }
}
```

**Status Codes**
- `200` — 受け入れ成功（`analysis` はモック解析結果）
- `422` — バリデーション失敗（Base64 不正・座標範囲外・音声データ空等）

---

## 3. GET /api/v1/alerts

解析済みテレメトリをアラートとして一覧返す（深刻度降順 → 新着順）。

**Query Parameters**
| Name | Type | Description |
|------|------|-------------|
| `level` | int | 1〜3 で絞り込み（`ge=1, le=3`。strict の Literal だとクエリ文字列が弾かれるため int で受ける） |
| `limit` | int | 1〜500（デフォルト: 全件） |

**Response 200** — `list[AlertSummary]`
```json
[
  {
    "telemetry_id": "tlm_1a2b3c4d5e6f",
    "sensor_id": "S-001",
    "hydrant_id": "H-001",
    "severity_level": 2,
    "leak_confidence": 87.5,
    "detected_at": "2026-08-11T01:30:15Z"
  }
]
```

---

## 4. GET /api/v1/alerts/{telemetry_id}

指定テレメトリの詳細を返す。消火栓 ID から配管台帳を照合し `pipe_info` を自動付与する（BE-4）。

**Response 200** — `AlertDetail`（= AlertSummary + location + analysis + pipe_info）
```json
{
  "telemetry_id": "tlm_1a2b3c4d5e6f",
  "sensor_id": "S-001",
  "hydrant_id": "H-001",
  "severity_level": 2,
  "leak_confidence": 87.5,
  "detected_at": "2026-08-11T01:30:15Z",
  "location": { "latitude": 35.6762, "longitude": 139.7674 },
  "analysis": { "leak_confidence": 87.5, "severity_level": 2, "dominant_freq_hz": 900.0, "band_energy_ratio": 0.75, "spectrum": [] },
  "pipe_info": {
    "pipe_id": "P-001",
    "material": "ductile_iron",
    "diameter_mm": 150,
    "installed_year": 1995,
    "burial_depth_m": 1.5,
    "age_years": 31
  }
}
```

**Status Codes**
- `200` — 成功（台帳未登録の hydrant は `pipe_info: null`）
- `404` — テレメトリが存在しない

---

## 5. POST /api/v1/alerts/{telemetry_id}/work-order

工事発注書の自動起票（BE-5 スタブ。Orcarouter 連携は将来）。

**Status Codes**
- `404` — テレメトリが存在しない
- `501` — `BE-5 未実装のため自動起票は利用できません`

---

## 6. GET /api/v1/sensors

消火栓マスタ（hydrants.json）を台帳に、各センサーの最新状態を重ねて返す。

**Query Parameters**
| Name | Type | Description |
|------|------|-------------|
| `format` | `json` \| `geojson` | 応答形式（デフォルト `json`） |

**Response 200（format=json）** — `list[SensorInfo]`
```json
[
  {
    "sensor_id": "S-001",
    "hydrant_id": "H-001",
    "status": "watch",
    "location": { "latitude": 35.6762, "longitude": 139.7674 },
    "last_reading_at": "2026-08-11T01:30:15Z"
  }
]
```

**Response 200（format=geojson）** — `SensorFeatureCollection`（Leaflet 地図用）
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "sensor_id": "S-001",
        "status": "watch",
        "severity_level": 2,
        "last_reading_at": "2026-08-11T01:30:15Z"
      },
      "geometry": { "type": "Point", "coordinates": [139.7674, 35.6762] }
    }
  ]
}
```

**Coordinate Order**: GeoJSON 標準の `[経度, 緯度]`（Leaflet 側の逆順変換は FE-3 の責務）。
`status` は最新 severity から導出: 0→normal / 1→watch / 2→warning / 3→critical / 未読込→unknown。

---

## 7. GET /api/v1/kpi/summary

アラート実データから KPI サマリを集計して返す（BE-8・`docs/business-model.md` §3 の算定式）。
固定値は返さない。常に試算値である旨を明示する。

**Response 200** — `KpiSummary`（7 フィールド）
```json
{
  "total_sensors": 10,
  "level1_count": 8,
  "level2_count": 3,
  "level3_count": 1,
  "estimated_cost_saved_yen": 2048400,
  "is_estimate": true,
  "assumption_doc": "docs/business-model.md §3"
}
```

**Status Codes**
- `200` — 空ストアでも 200 を返し、件数・コストは 0（`total_sensors` のみ実件数。500 にしない）

**注記**: `today_detections` は本スキーマに**存在しない**（D-3 で FE-7 以降の対応と明記）。

---

## エラーハンドリング

- **422**: FastAPI が自動生成するバリデーションエラー。`audio_base64` 不正等は明示メッセージ
- **404**: `テレメトリ {id} は見つかりません`（存在しない ID はクライアント起因として 404。500 にしない）
- **501**: `BE-5 未実装のため自動起票は利用できません`

---

## 内部 API（フロント lib/api.ts）

axios クライアント `apiClient`（baseURL: `NEXT_PUBLIC_API_BASE_URL` / default `http://localhost:8000`・timeout 10s）経由。
すべて snake_case→camelCase 変換 + `ApiError` 変換を透過。`any` 型は不使用。

| 関数 | 呼び出し先 | 戻り型 | 備考 |
|------|-----------|--------|------|
| `fetchSensors()` | `GET /api/v1/sensors` | `Promise<SensorInfo[]>` | |
| `fetchSensorsGeoJson()` | `GET /api/v1/sensors?format=geojson` | `Promise<SensorFeatureCollection>` | 座標 [lng, lat] 保持 |
| `fetchAlerts(params?)` | `GET /api/v1/alerts` | `Promise<AlertSummary[]>` | `level` / `limit` で絞り込み |
| `fetchAlertDetail(telemetryId)` | `GET /api/v1/alerts/{id}` | `Promise<AlertDetail>` | `encodeURIComponent` 適用 |
| `createWorkOrder(telemetryId)` | `POST /api/v1/alerts/{id}/work-order` | `Promise<WorkOrder>` | 現状 501 で失敗 |
| `fetchKpiSummary()` | **未実装** | （FE-7 で追加予定） | **FE-7 の対象。現在 page.tsx がモックを表示** |

### FE-7 で追加予定の契約（バックエンド側は実装済み）

`KpiSummary`（camelCase 相当）: `totalSensors / level1Count / level2Count / level3Count / estimatedCostSavedYen / isEstimate / assumptionDoc`
現状フロントの `KpiData`（`KpiSummary.tsx`）は `totalSensors / level3Count / level2Count / todayDetections / estimatedCostSavedYen`
の 5 項目で、バックエンド契約と乖離している（`level1Count` 欠如・`todayDetections` は契約外）。FE-7 で整合させる。

---

## 内部 API（バックエンド store / services）

### store.py
- `InMemoryStore.add(record)` — 登録。満杯時は最古を破棄し索引から削除
- `InMemoryStore.get(telemetry_id)` — ID 取得（無ければ None）
- `InMemoryStore.list_alerts(level, limit)` — 深刻度降順・新着順で返す（ソート→フィルタ→limit）
- `InMemoryStore.latest_sensor_states()` — センサー別最新レコードの浅いコピー
- `InMemoryStore.clear()` — テスト用リセット
- `get_store()` / `reset_store()` — モジュールレベルシングルトン（ハンドラ実行時取得・import 時捕捉は禁止）
- `get_hydrants()` — `@lru_cache` で hydrants.json を 1 回読み込み

### services/ledger.py
- `get_pipes()` — `@lru_cache` で pipes.json を 1 回読み込み
- `find_pipe_by_hydrant(hydrant_id)` — 消火栓 ID から所属配管を返す（無ければ None）
- `find_nearest_pipe(lat, lng)` — 各路線の頂点との Haversine 最小距離で最近接配管を返す
- `get_pipe_age(installed_year)` — `REFERENCE_YEAR(2026) - installed_year`

### services/kpi.py
- `expected_cost_saved(severity_level)` — 深刻度別 1 件あたり期待回避コスト（§3.1）
- `calculate_kpi_summary()` — ストア全件走査でレベル別件数と推定削減コストを集計。`total_sensors` は hydrants.json 実件数
