# SmartWater Guardian - API ドキュメント

## Base URL

```
http://localhost:8000
```

OpenAPI ドキュメントは FastAPI が自動生成（`/docs`）。CORS 許可オリジンは環境変数 `ALLOWED_ORIGINS`
（カンマ区切り）で制御（未設定時は `http://localhost:3000` のみ）。

## 外部 API サマリ（バックエンド 11 エンドポイント）

| # | Method | Path | 目的 | 状態 |
|---|--------|------|------|------|
| 1 | GET | `/` | ヘルスチェック | 実装済み |
| 2 | POST | `/api/v1/telemetry` | 音響テレメトリ受信（SVM + DSP 解析・BE-3） | 実装済み |
| 3 | GET | `/api/v1/alerts` | アラート一覧（深刻度降順） | 実装済み |
| 4 | GET | `/api/v1/alerts/{telemetry_id}` | アラート詳細（配管情報付与） | 実装済み |
| 5 | POST | `/api/v1/alerts/{telemetry_id}/work-order` | 工事発注書の自動起票（BE-5・Orcarouter） | 実装済み |
| 6 | POST | `/api/v1/alerts/seed` | E2E テスト用デモシード投入 | 実装済み |
| 7 | GET | `/api/v1/sensors?format=json\|geojson` | センサー一覧（JSON / GeoJSON） | 実装済み |
| 8 | GET | `/api/v1/kpi/summary` | KPI サマリ（推定削減コスト・BE-8） | 実装済み |
| 9 | GET | `/api/v1/disaster/summary` | 防災モードの被災エリアクラスタ（BE-7） | 実装済み |
| 10 | POST | `/api/v1/disaster/simulate` | Level 3 アラートの一括シミュレーション投入（BE-7） | 実装済み |
| 11 | POST | `/api/v1/demo/seed` | デモ初期状態の 1 件投入（DEMO-1） | 実装済み |

レスポンスはすべて snake_case（Pydantic v2）。フロントは `lib/api.ts` が camelCase へ変換する。

---

## 1. GET /

**Response 200**
```json
{ "message": "SmartWater Guardian API Ready" }
```

---

## 2. POST /api/v1/telemetry

疑似 IoT センサーからの音響テレメトリを受信・検証し、`app/services/audio.py` の SVM + DSP 解析
（BE-3）を実行してストアに登録する。

**Request Body**（`TelemetryRequest`、strict / extra=forbid）
```json
{
  "sensor_id": "S-001",
  "hydrant_id": "H-001",
  "recorded_at": "2026-08-11T10:30:00+09:00",
  "location": { "latitude": 35.6762, "longitude": 139.7674 },
  "sample_rate_hz": 8000,
  "duration_sec": 1.0,
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

**解析（BE-3・`services/audio.py`）**
- MVP 契約: 8000Hz / 1.0s（8000 PCM16 サンプル）。`sample_rate_hz` は 8000 前提
- 14 次元特徴量（帯域エネルギー比・スペクトル形状等）を抽出し、`leak_svm_v1.joblib`（SHA-256 検証付き）で判定
- `is_leak` + `band_energy_ratio` から深刻度を分類: `ratio >= 0.60` → 3 / `>= 0.30` → 2 / それ以外 → 1

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
- `200` — 受け入れ成功（`analysis` は SVM 解析結果）
- `422` — バリデーション失敗 / `audio_base64` を解析できない（`AudioValidationError`）

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

工事発注書の自動起票（BE-5）。`app/services/orcarouter.py` が LLM（Orcarouter API）で
補修部材選定・概算見積・作業指示書を生成する。API キー未設定または LLM 失敗時は
規定ルールによるフォールバック（`source: "fallback"`）を返す。成功時のみキャッシュ
（フォールバックはキャッシュしない）。

**Response 200** — `WorkOrder`
```json
{
  "parts": [
    { "name": "ダクタイル鋳鉄管 150mm", "spec": "DIP φ150", "quantity": 1, "unit_price_yen": 45000, "subtotal_yen": 45000 }
  ],
  "total_estimate_yen": 185000,
  "work_steps": ["現場確認", "管体露出", "補修部材交換"],
  "required_workers": 3,
  "estimated_duration_hours": 4.5,
  "urgency": "high",
  "notification_text": "漏水を検知しました。至急対応をお願いします。",
  "source": "llm",
  "prompt_tokens": 812,
  "completion_tokens": 240,
  "cost_yen": 0.051,
  "model": "orcarouter",
  "latency_ms": 1840,
  "is_estimated": false
}
```

**Status Codes**
- `200` — 起票成功（`source` は `llm` / `fallback`）
- `404` — テレメトリが存在しない

---

## 6. POST /api/v1/alerts/seed

E2E テスト用のデモシード。実在マスタ（HYD-001〜010）へレベルを決定論的に投入する
（L3×3 / L2×3 / L1×3 / L0×1 の合計 10 件）。`payload.count` は後方互換用の受領のみで件数には影響しない。

**Request Body**（`SeedRequest`）
```json
{ "count": 10 }
```

**Response 200** — `SeedResponse`
```json
{
  "inserted_count": 10,
  "message": "E2E テスト用シード投入完了: 10 件のアラートをストアへ追加しました"
}
```

---

## 7. GET /api/v1/sensors

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

## 8. GET /api/v1/kpi/summary

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

**注記**: `today_detections` は本スキーマに**存在しない**（D-3 で FE-7 以降の対応と明記。現状も未採用）。

---

## 9. GET /api/v1/disaster/summary

Level 3 アラートを距離閾値（`threshold_meters` デフォルト 300m）でクラスタリングし、
被災エリア（GeoJSON Polygon）・想定断水世帯・優先閉栓バルブを返す（BE-7）。
シミュレーション投入分（`TEL-DISASTER-*`）がストアにある場合のみクラスタを算出する。

**Query Parameters**
| Name | Type | Description |
|------|------|-------------|
| `threshold_meters` | float | クラスタリング距離閾値（m）。デフォルト 300.0 |

**Response 200** — `DisasterSummaryResponse`
```json
{
  "total_clusters": 2,
  "total_affected_households": 290,
  "clusters": [
    {
      "cluster_id": "CLS-001",
      "center_lat": 35.6812,
      "center_lng": 139.7671,
      "affected_sensor_ids": ["SEN-DISASTER-001"],
      "affected_pipe_ids": ["PIPE-1"],
      "estimated_households": 170,
      "priority_valve_hydrant_id": "HYD-DISASTER-001",
      "geometry": { "type": "Polygon", "coordinates": [[[139.7671, 35.6812], "..."] ] }
    }
  ]
}
```

**Status Codes**
- `200` — Level 3 が 0 件・シミュレーション未投入時は `clusters: []`

---

## 10. POST /api/v1/disaster/simulate

デモ用に Level 3 アラートを一括シミュレーション投入する（BE-7）。東京駅周辺を起点に
`count` 件を格子状に配置し、`TEL-DISASTER-XXX` としてストア + `/tmp/disaster_simulated_items.json` に記録。

**Query Parameters**
| Name | Type | Description |
|------|------|-------------|
| `count` | int | 投入件数。`ge=1, le=23`。デフォルト 6 |

**Response 200** — `DisasterSimulateResponse`
```json
{
  "inserted_count": 6,
  "message": "震災モードシミュレーション: Level 3 アラートを 6 件一括追加しました"
}
```

---

## 11. POST /api/v1/demo/seed

デモ初期状態の 1 件を投入（DEMO-1）。`DemoSeedRequest`（= TelemetryRequest + `level`）で
深刻度を意図値に確定しつつ、`analyze_audio` で実スペクトルを算出する
（実 SVM は合成波形を意図レベルに分類できないため、デモシード専用の補正として上書き）。

**Request Body**（`DemoSeedRequest`・`level` 追加）
```json
{
  "sensor_id": "S-001",
  "hydrant_id": "H-001",
  "recorded_at": "2026-08-11T10:30:00+09:00",
  "location": { "latitude": 35.6762, "longitude": 139.7674 },
  "sample_rate_hz": 8000,
  "duration_sec": 1.0,
  "audio_base64": "//NExAAAAANIAAAyAABAAJAA...",
  "level": 3
}
```

**Response 200** — `TelemetryResponse`（`analysis.severity_level` は `level` の意図値）

**Status Codes**
- `200` — 投入成功
- `422` — バリデーション失敗 / `audio_base64` を解析できない

---

## エラーハンドリング

- **422**: FastAPI が自動生成するバリデーションエラー。`audio_base64` 不正・解析不能等は明示メッセージ
- **404**: `テレメトリ {id} は見つかりません`（存在しない ID はクライアント起因として 404。500 にしない）
- **502**: `RuntimeError`（配管台帳欠損など）は `バックエンド リソース読み込み失敗`（main.py のハンドラ）
- **500**: 予測不能な例外は構造化レスポンス（`detail` / `error_type` / `error_id`）で返す（意図的に 500 を出し続けない設計）

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
| `createWorkOrder(telemetryId)` | `POST /api/v1/alerts/{id}/work-order` | `Promise<WorkOrder>` | BE-5 実装済み（llm / fallback） |
| `fetchKpiSummary()` | `GET /api/v1/kpi/summary` | `Promise<KpiSummary>` | BE-8 + FE-7 実装済み |
| `fetchDisasterSummary()` | `GET /api/v1/disaster/summary` | `Promise<DisasterSummary>` | BE-7 |
| `simulateDisaster(count)` | `POST /api/v1/disaster/simulate?count=` | `Promise<DisasterSimulateResponse>` | 防災シミュレーションボタン |

**契約型（camelCase）**: `KpiSummary`（totalSensors / level1Count / level2Count / level3Count /
estimatedCostSavedYen / isEstimate / assumptionDoc）・`WorkOrder`（source は `"llm" | "fallback"` ほか FR-6 原価フィールド）・
`DisasterSummary` / `DisasterCluster`（types/disaster.ts）。

### フロント専用 Route Handler

`GET /api/docs/business-model`（`frontend/src/app/api/docs/business-model/route.ts`）— KPI コストカードの
「前提: docs/business-model.md」リンクボタンが `docs/business-model.md` の本文を取得してモーダル表示する。
取得成功時 `{ "content": "..." }`、失敗時 `{ "content": null, "error": "..." }` を 404 で返す。

---

## 内部 API（バックエンド store / services）

### store.py
- `InMemoryStore.add(record)` — 登録。満杯時は最古を破棄し索引から削除
- `InMemoryStore.get(telemetry_id)` — ID 取得（無ければ None）
- `InMemoryStore.get_all()` — 全件取得（防災モードのクラスタリングで使用）
- `InMemoryStore.list_alerts(level, limit)` — 深刻度降順・新着順で返す（ソート→フィルタ→limit）
- `InMemoryStore.latest_sensor_states()` — センサー別最新レコードの浅いコピー
- `InMemoryStore.clear()` — テスト用リセット
- `get_store()` / `reset_store()` — モジュールレベルシングルトン（ハンドラ実行時取得・import 時捕捉は禁止）
- `get_hydrants()` — `@lru_cache` で hydrants.json を 1 回読み込み

### services/ledger.py（BE-4）
- `get_pipes()` — `@lru_cache` で pipes.json を 1 回読み込み
- `find_pipe_by_hydrant(hydrant_id)` — 消火栓 ID から所属配管を返す（無ければ None）
- `find_nearest_pipe(lat, lng)` — 各路線の頂点との Haversine 最小距離で最近接配管を返す
- `get_pipe_age(installed_year)` — `REFERENCE_YEAR(2026) - installed_year`

### services/audio.py（BE-3）
- `analyze_audio(audio_base64, sample_rate_hz, duration_sec)` — PCM16 をデコードし 14 次元特徴量を
  抽出 → SVM（`leak_svm_v1.joblib`・SHA-256 検証）で漏水判定 → `classify_severity()` で Level 分類 → `AnalysisResult` を返す
- `AudioValidationError` — 解析不能な音声（空・デコード失敗）は 422 へ変換
- `_load_model()` — `@lru_cache` で joblib + metadata.json（期待 SHA-256）を 1 回読み込み

### services/orcarouter.py（BE-5）
- `create_work_order(client, telemetry_id, alert, pipe)` — LLM プロンプト構築（prompts.py）→ `_post_with_retry`
  （1 リトライ）→ `_parse_llm_response` → `llm_cost.calculate_and_enrich_cost` で原価付与 → キャッシュ。失敗時は `build_fallback_work_order`
- `build_fallback_work_order(...)` — 規定ルールによる算出（`source: "fallback"`・repair_parts.json マスタ参照）
- `_work_order_cache` / `_work_order_lock` — 成功時のみキャッシュ・`asyncio.Lock` で直列化

### services/llm_cost.py（FR-6）
- `calc_cost_yen(prompt_tokens, completion_tokens)` — 単価（input $0.00015 / output $0.00060 per 1K・`USD_JPY=155.0`）から原価円を算出
- `calculate_and_enrich_cost(work_order, ...)` — WorkOrder に原価フィールドを付与 + JSON 構造化ログ出力

### services/kpi.py（BE-8）
- `expected_cost_saved(severity_level)` — 深刻度別 1 件あたり期待回避コスト（§3.1）
- `calculate_kpi_summary()` — ストア全件走査でレベル別件数と推定削減コストを集計。`total_sensors` は hydrants.json 実件数
