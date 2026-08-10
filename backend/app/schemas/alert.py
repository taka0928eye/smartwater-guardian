"""アラート・センサー参照APIのレスポンススキーマ（Pydantic v2）。

BE-6 用。``AnalysisResult`` 等は ``app.schemas.telemetry`` を再利用する（再定義しない）。
``pipe_info`` は BE-4（疑似GIS配管台帳）実装までは常に ``None`` を返す（フロントの
クラッシュ防止のため null を許容する設計）。
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.telemetry import (
    STRICT_INPUT_CONFIG,
    AnalysisResult,
    GeoLocation,
    SeverityLevel,
)


class AlertSummary(BaseModel):
    """検知アラートの一覧行（GET /api/v1/alerts の要素）。"""

    model_config = STRICT_INPUT_CONFIG

    telemetry_id: str = Field(description="テレメトリ識別子")
    sensor_id: str = Field(description="センサー識別子")
    hydrant_id: str = Field(description="消火栓識別子")
    severity_level: SeverityLevel = Field(description="深刻度 Level 1〜3")
    leak_confidence: float = Field(ge=0.0, le=100.0, description="漏水確信度（%）")
    detected_at: datetime = Field(description="検知時刻（サーバー受信時刻）")


class PipeInfo(BaseModel):
    """配管台帳情報（BE-4 実装時の型を先に固定する）。

    BE-6 では常に ``None`` を返す。BE-4（app/services/ledger.py）が実装されたら
    ここに配管情報が入る。
    """

    model_config = STRICT_INPUT_CONFIG

    pipe_id: str
    material: str
    diameter_mm: int = Field(gt=0)
    installed_year: int
    burial_depth_m: float
    age_years: int


class AlertDetail(AlertSummary):
    """アラート詳細（GET /api/v1/alerts/{telemetry_id}）。"""

    location: GeoLocation
    analysis: AnalysisResult
    pipe_info: PipeInfo | None = Field(default=None, description="BE-4 実装までは null")


class SensorInfo(BaseModel):
    """消火栓マスタ + センサーの最新状態（GET /api/v1/sensors の要素）。"""

    model_config = STRICT_INPUT_CONFIG

    sensor_id: str
    hydrant_id: str
    status: Literal["normal", "warning", "critical", "unknown"] = Field(
        description="監視状態（最新 severity から導出）"
    )
    location: GeoLocation
    last_reading_at: datetime | None = Field(default=None, description="最終計測時刻")


class HydrantMaster(BaseModel):
    """消火栓マスタ（app/data/hydrants.json）の1件。"""

    model_config = STRICT_INPUT_CONFIG

    hydrant_id: str
    sensor_id: str
    name: str
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    pipe_id: str


# --- GeoJSON（GET /api/v1/sensors?format=geojson 用）---
# 座標順序は GeoJSON 標準どおり [経度, 緯度]。Leaflet 側の [緯度, 経度] 変換は FE-3 の責務。


class GeoJSONPoint(BaseModel):
    """GeoJSON の Point ジオメトリ。座標は [経度, 緯度] の順。"""

    model_config = ConfigDict(strict=True)

    type: Literal["Point"] = "Point"
    coordinates: list[float] = Field(min_length=2, max_length=2, description="[経度, 緯度]")


class SensorProperties(BaseModel):
    """Feature.properties（マーカー描画用のセンサー状態）。"""

    model_config = ConfigDict(strict=True)

    sensor_id: str
    status: str
    severity_level: SeverityLevel | None = None
    last_reading_at: datetime | None = None


class SensorFeature(BaseModel):
    """GeoJSON Feature。"""

    model_config = ConfigDict(strict=True)

    type: Literal["Feature"] = "Feature"
    properties: SensorProperties
    geometry: GeoJSONPoint


class SensorFeatureCollection(BaseModel):
    """GeoJSON FeatureCollection（GET /api/v1/sensors?format=geojson）。"""

    model_config = ConfigDict(strict=True)

    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[SensorFeature]
