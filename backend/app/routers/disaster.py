"""防災モード API ルーター (GET /summary, POST /simulate)。"""

import math
import traceback
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse

from app.schemas.disaster import (
    DisasterCluster,
    DisasterSimulateResponse,
    DisasterSummaryResponse,
    GeoJSONPolygon,
)
from app.schemas.telemetry import AnalysisResult, GeoLocation
from app.store import StoredTelemetry, get_store

router = APIRouter(prefix="/api/v1/disaster", tags=["disaster"])


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """2点間の大円距離(メートル)を計算。"""
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def create_circle_polygon(
    center_lng: float, center_lat: float, radius_m: float = 300.0, num_points: int = 16
) -> GeoJSONPolygon:
    """重心から半径 radius_m メートルの多角形近似 GeoJSON Polygon を生成。"""
    coords = []
    lat_rad = math.radians(center_lat)

    meters_per_lat = 111111.0
    meters_per_lng = 111111.0 * math.cos(lat_rad)

    for i in range(num_points):
        angle = 2.0 * math.pi * i / num_points
        dx = radius_m * math.cos(angle)
        dy = radius_m * math.sin(angle)

        lng = center_lng + (dx / meters_per_lng)
        lat = center_lat + (dy / meters_per_lat)
        coords.append([round(lng, 6), round(lat, 6)])

    coords.append(coords[0])
    return GeoJSONPolygon(type="Polygon", coordinates=[coords])


def _extract_lat_lng(item: Any) -> tuple[float, float]:
    """アイテムから緯度・経度を安全に抽出するヘルパー。"""
    if isinstance(item, dict):
        loc = item.get("location", {})
        if isinstance(loc, dict):
            lat = loc.get("latitude", 0.0) or loc.get("lat", 0.0)
            lng = loc.get("longitude", 0.0) or loc.get("lng", 0.0)
        else:
            lat = item.get("lat", 0.0)
            lng = item.get("lng", 0.0)
    else:
        loc = getattr(item, "location", None)
        lat = getattr(loc, "latitude", getattr(item, "lat", 0.0))
        lng = getattr(loc, "longitude", getattr(item, "lng", 0.0))
    return float(lat), float(lng)


def _is_level3(item: Any) -> bool:
    """アイテムが Level 3 アラートかどうか判定。"""
    candidates = []

    if isinstance(item, dict):
        candidates.extend([
            item.get("severity_level"),
            item.get("severityLevel"),
            item.get("severity"),
        ])
        analysis = item.get("analysis")
        if isinstance(analysis, dict):
            candidates.extend([
                analysis.get("severity_level"),
                analysis.get("severityLevel"),
                analysis.get("severity"),
            ])
    else:
        candidates.extend([
            getattr(item, "severity_level", None),
            getattr(item, "severityLevel", None),
            getattr(item, "severity", None),
        ])
        analysis = getattr(item, "analysis", None)
        if analysis is not None:
            candidates.extend([
                getattr(analysis, "severity_level", None),
                getattr(analysis, "severityLevel", None),
                getattr(analysis, "severity", None),
            ])

    for val in candidates:
        if val is not None and str(val).strip() == "3":
            return True
    return False


@router.get("/summary", response_model=DisasterSummaryResponse)
async def get_disaster_summary(
    threshold_meters: float = Query(300.0, description="クラスタリング距離閾値(m)"),
) -> DisasterSummaryResponse:
    """Level 3 アラートを一括取得し、距離閾値でクラスタリングして被災エリアを返却する。"""
    store = get_store()

    all_items: list[Any] = []
    if hasattr(store, "_telemetry") and getattr(store, "_telemetry") == []:
        all_items = []
    elif hasattr(store, "_alerts") and getattr(store, "_alerts") == []:
        all_items = []
    elif hasattr(store, "get_all"):
        all_items = store.get_all()

    level3_alerts = [item for item in all_items if _is_level3(item)]

    if not level3_alerts:
        return DisasterSummaryResponse(
            total_clusters=0,
            total_affected_households=0,
            clusters=[],
        )

    clusters_raw: list[list[Any]] = []
    for alert in level3_alerts:
        lat, lng = _extract_lat_lng(alert)
        assigned = False
        for cluster in clusters_raw:
            if haversine_distance(lat, lng, *_extract_lat_lng(cluster[0])) <= threshold_meters:
                cluster.append(alert)
                assigned = True
                break
        if not assigned:
            clusters_raw.append([alert])

    result_clusters = []
    total_households = 0
    for idx, group in enumerate(clusters_raw, start=1):
        lats = [_extract_lat_lng(i)[0] for i in group]
        lngs = [_extract_lat_lng(i)[1] for i in group]
        center = (sum(lats) / len(lats), sum(lngs) / len(lngs))

        h = len(group) * 120 + 50
        total_households += h
        result_clusters.append(
            DisasterCluster(
                cluster_id=f"CLS-{idx:03d}",
                center_lat=round(center[0], 6),
                center_lng=round(center[1], 6),
                affected_sensor_ids=[getattr(i, "sensor_id", f"SEN-{idx}") for i in group],
                affected_pipe_ids=[f"PIPE-{idx}"],
                estimated_households=h,
                priority_valve_hydrant_id=getattr(group[0], "hydrant_id", f"HYD-{idx}"),
                geometry=create_circle_polygon(center[1], center[0], radius_m=threshold_meters),
            )
        )

    return DisasterSummaryResponse(
        total_clusters=len(result_clusters),
        total_affected_households=total_households,
        clusters=result_clusters,
    )


@router.post("/simulate", response_model=DisasterSimulateResponse)
async def simulate_disaster(count: int = Query(6, ge=1, le=20)) -> Any:
    """デモ用に一括で Level 3 アラートをシミュレーション投入する。"""
    try:
        store = get_store()
        now = datetime.now(timezone.utc)
        base_lat, base_lng = 35.6812, 139.7671

        for i in range(count):
            item = StoredTelemetry(
                telemetry_id=f"TEL-DISASTER-{i+1:03d}",
                sensor_id=f"SEN-DISASTER-{i+1:03d}",
                hydrant_id=f"HYD-DISASTER-{i+1:03d}",
                recorded_at=now,
                received_at=now,
                location=GeoLocation(
                    latitude=base_lat + (i * 0.001),
                    longitude=base_lng + (i * 0.001),
                ),
                analysis=AnalysisResult(
                    severity_level=3,
                    leak_confidence=95.0,
                    dominant_freq_hz=100,
                    band_energy_ratio=1.0,
                ),
            )

            if hasattr(store, "add"):
                store.add(item)

        return DisasterSimulateResponse(
            inserted_count=count,
            message=f"震災モードシミュレーション: Level 3 アラートを {count} 件一括追加しました",
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": traceback.format_exc()},
        )
