"""センサー状態参照API（BE-6）。

GET /api/v1/sensors で消火栓マスタ（app/data/hydrants.json）を台帳に、各センサーの
最新解析状態を重ねて返す。``?format=geojson`` では Leaflet 地図（FE-3）向けに
FeatureCollection を返す。座標は GeoJSON 標準の [経度, 緯度] 順
（緯度・経度を逆にすると東京が海に落ちる。Leaflet 側の変換は FE-3 の責務）。
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Query

from app.schemas.alert import (
    GeoJSONPoint,
    HydrantMaster,
    SensorFeature,
    SensorFeatureCollection,
    SensorInfo,
    SensorProperties,
)
from app.schemas.telemetry import GeoLocation
from app.store import StoredTelemetry, get_hydrants, get_store

router = APIRouter(prefix="/api/v1", tags=["sensors"])

# 最新解析の severity → 監視状態の対応（最新レコード未読込は unknown）
# 0=正常 / 1=微小漏水・要注視 / 2=進行性漏水・要点検 / 3=破裂・緊急対応
SensorStatus = Literal["normal", "watch", "warning", "critical", "unknown"]
STATUS_BY_SEVERITY: dict[int, SensorStatus] = {0: "normal", 1: "watch", 2: "warning", 3: "critical"}


def _derive_status(record: StoredTelemetry | None) -> SensorStatus:
    """最新レコードから監視状態を導出する。未読込なら unknown。"""
    if record is None:
        return "unknown"
    return STATUS_BY_SEVERITY[record.analysis.severity_level]


def _to_sensor_info(hydrant: HydrantMaster, latest: StoredTelemetry | None) -> SensorInfo:
    """マスタ1件 + 最新レコードから SensorInfo を組み立てる。"""
    return SensorInfo(
        sensor_id=hydrant.sensor_id,
        hydrant_id=hydrant.hydrant_id,
        status=_derive_status(latest),
        location=GeoLocation(latitude=hydrant.latitude, longitude=hydrant.longitude),
        last_reading_at=latest.received_at if latest else None,
    )


def _to_sensor_feature(
    hydrant: HydrantMaster, latest: StoredTelemetry | None
) -> SensorFeature:
    """マスタ1件 + 最新レコードから GeoJSON Feature を組み立てる。"""
    return SensorFeature(
        properties=SensorProperties(
            sensor_id=hydrant.sensor_id,
            status=_derive_status(latest),
            severity_level=latest.analysis.severity_level if latest else None,
            last_reading_at=latest.received_at if latest else None,
        ),
        geometry=GeoJSONPoint(coordinates=[hydrant.longitude, hydrant.latitude]),
    )


@router.get("/sensors", summary="センサー一覧（JSON / GeoJSON）")
def list_sensors(
    format: Literal["json", "geojson"] = Query(default="json", description="応答形式"),
):
    """消火栓マスタを台帳に、センサーごとの最新状態を返す。

    応答形式は format で切り替わるため response_model は指定しない
    （Pydantic インスタンスを返し FastAPI がシリアライズする）。
    """
    latest = get_store().latest_sensor_states()
    hydrants = get_hydrants()
    if format == "geojson":
        return SensorFeatureCollection(
            features=[
                _to_sensor_feature(hydrant, latest.get(hydrant.sensor_id))
                for hydrant in hydrants
            ]
        )
    return [_to_sensor_info(hydrant, latest.get(hydrant.sensor_id)) for hydrant in hydrants]
