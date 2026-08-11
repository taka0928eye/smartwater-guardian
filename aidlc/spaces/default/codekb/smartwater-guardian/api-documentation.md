# SmartWater Guardian - API ドキュメント

## Base URL

```
http://localhost:8000/api/v1
```

## Endpoints Overview

| Method | Endpoint | Purpose | Status |
|--------|----------|---------|--------|
| POST | `/telemetry` | IoT音響テレメトリ受信 | ✓ BE-1 実装 |
| GET | `/alerts` | アラート一覧（深刻度降順） | ✓ BE-6 実装 |
| GET | `/alerts/{telemetry_id}` | アラート詳細 | ✓ BE-6 実装 |
| POST | `/alerts/{telemetry_id}/work-order` | 工事発注（スタブ） | ⊘ BE-5 未実装 |
| GET | `/sensors` | センサー・マスタ一覧 | ✓ 実装 |
| GET | `/sensors?format=geojson` | GeoJSON形式センサー位置 | ✓ FE連携 |

---

## 1. テレメトリ受信

### POST `/telemetry`

IoT消火栓型センサーから音響データを受信。BE-1段階では解析なし（analysis=null）。

**Request Body**

```json
{
  "sensor_id": "S-001",
  "hydrant_id": "H-001",
  "recorded_at": "2026-08-11T10:30:00+09:00",
  "location": {
    "latitude": 35.6762,
    "longitude": 139.7674
  },
  "sample_rate_hz": 16000,
  "duration_sec": 10.5,
  "audio_base64": "//NExAAAAANIAAAyAABAAJAA...",
  "battery_pct": 85
}
```

**Validation Rules**

- `sensor_id`, `hydrant_id`: 1-64文字
- `recorded_at`: ISO 8601形式、タイムゾーン必須（複数自治体対応）
- `location.latitude`: -90.0 〜 90.0
- `location.longitude`: -180.0 〜 180.0
- `sample_rate_hz`: 1 〜 192000 Hz
- `duration_sec`: 0.0 < x ≤ 60.0 秒
- `audio_base64`: 妥当なBase64（デコード試行で検証）
- `battery_pct`: 0 〜 100（オプション）

**Response**

```json
{
  "telemetry_id": "T-20260811-001",
  "sensor_id": "S-001",
  "received_at": "2026-08-11T10:30:15Z",
  "status": "accepted",
  "analysis": null
}
```

**Status Codes**

- `200` — 受け入れ成功
- `422` — バリデーション失敗（Base64エラー、座標範囲外、ISO 8601エラーなど）

---

## 2. アラート参照

### GET `/alerts`

深刻度降順・新着順に並んだアラート一覧を返す。

**Query Parameters**

| Name | Type | Description |
|------|------|-------------|
| `level` | int | 深刻度 1〜3 でフィルタ（オプション） |
| `limit` | int | 取得件数上限 1〜500（デフォルト: 全件） |

**Response**

```json
[
  {
    "telemetry_id": "T-20260811-001",
    "sensor_id": "S-001",
    "hydrant_id": "H-001",
    "severity_level": 2,
    "leak_confidence": 87.5,
    "detected_at": "2026-08-11T10:30:15Z"
  },
  ...
]
```

**Status Codes**

- `200` — 成功（空配列も含む）

---

### GET `/alerts/{telemetry_id}`

指定したテレメトリの詳細を返す。配管情報（BE-4）を自動付与。

**Response**

```json
{
  "telemetry_id": "T-20260811-001",
  "sensor_id": "S-001",
  "hydrant_id": "H-001",
  "severity_level": 2,
  "leak_confidence": 87.5,
  "detected_at": "2026-08-11T10:30:15Z",
  "location": {
    "latitude": 35.6762,
    "longitude": 139.7674
  },
  "analysis": {
    "leak_confidence": 87.5,
    "severity_level": 2,
    "dominant_freq_hz": 4500.0,
    "band_energy_ratio": 0.68,
    "spectrum": [
      {"freq_hz": 0.0, "magnitude": 0.5},
      ...
    ]
  },
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

- `200` — 成功
- `404` — テレメトリが見つからない

---

### POST `/alerts/{telemetry_id}/work-order`

補修部材選定・見積自動起票（BE-5スタブ）。

**Response**

- `501` — 実装待ち（存在しない ID なら `404`）

---

## 3. センサー・マスタ参照

### GET `/sensors`

センサーとマスタ情報の統合情報を返す。

**Response**

```json
[
  {
    "sensor_id": "S-001",
    "hydrant_id": "H-001",
    "status": "normal",
    "location": {
      "latitude": 35.6762,
      "longitude": 139.7674
    },
    "last_reading_at": "2026-08-11T10:30:15Z"
  },
  ...
]
```

---

### GET `/sensors?format=geojson`

GeoJSON FeatureCollection 形式でセンサー位置を返す（Leaflet用）。

**Response**

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "sensor_id": "S-001",
        "status": "normal",
        "severity_level": 0,
        "last_reading_at": "2026-08-11T10:30:15Z"
      },
      "geometry": {
        "type": "Point",
        "coordinates": [139.7674, 35.6762]
      }
    },
    ...
  ]
}
```

**Coordinate Order**: GeoJSON 標準 `[経度, 緯度]`

---

## Error Handling

### 422 Unprocessable Entity

入力検証エラーの詳細は FastAPI が自動生成：

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "audio_base64"],
      "msg": "audio_base64 は妥当な Base64 文字列である必要があります",
      "input": "!!invalid!!",
      "ctx": {"error": "..."}
    }
  ]
}
```

### 404 Not Found

```json
{
  "detail": "テレメトリ T-nonexistent は見つかりません"
}
```

### 501 Not Implemented

```json
{
  "detail": "BE-5 未実装のため自動起票は利用できません"
}
```

---

## Data Contracts

### Schema: TelemetryRequest / TelemetryResponse

| Field | Type | Description |
|-------|------|-------------|
| `sensor_id` | string | センサー識別子 |
| `hydrant_id` | string | 消火栓識別子 |
| `recorded_at` | datetime | 録音日時（AwareDatetime） |
| `location` | GeoLocation | 緯度経度 |
| `sample_rate_hz` | int | サンプリング周波数 |
| `duration_sec` | float | 録音長（秒） |
| `audio_base64` | string | PCM16 モノラル音声（Base64） |
| `battery_pct` | int | 電池残量（%、オプション） |
| `telemetry_id` | string | 受信ID（レスポンスのみ） |
| `status` | string | ステータス（"accepted"） |
| `analysis` | AnalysisResult | FFT判定結果（BE-1では null） |

### Schema: AlertSummary / AlertDetail

| Field | Type | Description |
|-------|------|-------------|
| `telemetry_id` | string | 一意の受信識別子 |
| `sensor_id` | string | センサーID |
| `hydrant_id` | string | 消火栓ID |
| `severity_level` | int | 0〜3（0=正常） |
| `leak_confidence` | float | 漏水確信度（0-100%） |
| `detected_at` | datetime | 検知時刻 |
| `location` | GeoLocation | センサー位置（詳細のみ） |
| `analysis` | AnalysisResult | 解析結果（詳細のみ） |
| `pipe_info` | PipeInfo | 配管情報（詳細のみ、null可） |

### Schema: PipeInfo ★TYPE INCONSISTENCY

| Field | Type | Current | Should Be |
|-------|------|---------|-----------|
| `pipe_id` | string | ✓ | ✓ |
| `material` | **str** | ⚠️ | **PipeMaterial** |
| `diameter_mm` | int | ✓ | ✓ |
| `installed_year` | int | ✓ | ✓ |
| `burial_depth_m` | float | ✓ | ✓ |
| `age_years` | int | ✓ | ✓ |

---

## Threading & Concurrency

- FastAPI 同期ハンドラは ThreadPoolExecutor で実行
- `Store._records` は `threading.Lock` で保護
- 並行 GET/POST アクセスでも安全

---

## Future Extensions (Out of Scope)

- **BE-3**: FFT 解析実装時に `analysis` フィールド埋込
- **BE-4**: 配管台帳 DBカネクタ化（現在 JSON）
- **BE-5**: 工事発注 API 実装
- **認証/権限**: CLAUDE.md §3 に従い本プロジェクト外

