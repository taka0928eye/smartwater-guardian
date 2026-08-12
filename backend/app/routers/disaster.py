"""防災モード API ルーター (GET /summary, POST /simulate)。"""

import math
from typing import Any

from fastapi import APIRouter, Query

from app.schemas.disaster import (
    DisasterCluster,
    DisasterSimulateResponse,
    DisasterSummaryResponse,
    GeoJSONPolygon,
)
from app.store import get_store

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


@router.get("/summary", response_model=DisasterSummaryResponse)
async def get_disaster_summary(
    threshold_meters: float = Query(300.0, description="クラスタリング距離閾値(m)"),
) -> DisasterSummaryResponse:
    """Level 3 アラートを一括取得し、距離閾値でクラスタリングして被災エリアを返却する。"""
    store = get_store()

    # store 内のアラートデータ（dictまたはオブジェクト）を取得
    if hasattr(store, "get_all_alerts"):
        all_alerts = store.get_all_alerts()
    elif hasattr(store, "alerts"):
        all_alerts = store.alerts
    elif hasattr(store, "get_all"):
        all_alerts = store.get_all()
    else:
        all_alerts = getattr(store, "_alerts", [])

    level3_alerts = []
    for a in all_alerts:
        sev = getattr(a, "severity_level", None)
        if sev is None and isinstance(a, dict):
            sev = a.get("severity_level") or a.get("severityLevel")
        if sev == 3:
            level3_alerts.append(a)

    if not level3_alerts:
        return DisasterSummaryResponse(
            total_clusters=0,
            total_affected_households=0,
            clusters=[],
        )

    # 貪欲法クラスタリング
    clusters_raw: list[list[Any]] = []
    for alert in level3_alerts:
        if isinstance(alert, dict):
            loc = alert.get("location", {})
            lat = loc.get("latitude", 0.0) if isinstance(loc, dict) else alert.get("lat", 0.0)
            lng = loc.get("longitude", 0.0) if isinstance(loc, dict) else alert.get("lng", 0.0)
        else:
            lat = alert.location.latitude
            lng = alert.location.longitude

        assigned = False
        for cluster in clusters_raw:
            for item in cluster:
                if isinstance(item, dict):
                    loc_i = item.get("location", {})
                    item_lat = loc_i.get("latitude", 0.0) if isinstance(loc_i, dict) else item.get("lat", 0.0)
                    item_lng = loc_i.get("longitude", 0.0) if isinstance(loc_i, dict) else item.get("lng", 0.0)
                else:
                    item_lat = item.location.latitude
                    item_lng = item.location.longitude

                dist = haversine_distance(lat, lng, item_lat, item_lng)
                if dist <= threshold_meters:
                    cluster.append(alert)
                    assigned = True
                    break
            if assigned:
                break

        if not assigned:
            clusters_raw.append([alert])

    result_clusters: list[DisasterCluster] = []
    total_households = 0

    for idx, group in enumerate(clusters_raw, start=1):
        cluster_id = f"CLS-{idx:03d}"

        lats, lngs, sensor_ids, hydrant_ids = [], [], [], []
        for item in group:
            if isinstance(item, dict):
                loc_g = item.get("location", {})
                lats.append(loc_g.get("latitude", 0.0) if isinstance(loc_g, dict) else item.get("lat", 0.0))
                lngs.append(loc_g.get("longitude", 0.0) if isinstance(loc_g, dict) else item.get("lng", 0.0))
                sensor_ids.append(item.get("sensor_id", f"SEN-{idx}"))
                hydrant_ids.append(item.get("hydrant_id", f"HYD-{idx}"))
            else:
                lats.append(item.location.latitude)
                lngs.append(item.location.longitude)
                sensor_ids.append(getattr(item, "sensor_id", f"SEN-{idx}"))
                hydrant_ids.append(getattr(item, "hydrant_id", f"HYD-{idx}"))

        center_lat = sum(lats) / len(lats)
        center_lng = sum(lngs) / len(lngs)

        unique_pipe_ids = [f"PIPE-SYS-{idx}"]
        households = len(group) * 120 + len(unique_pipe_ids) * 50
        total_households += households

        polygon = create_circle_polygon(center_lng, center_lat, radius_m=threshold_meters)

        result_clusters.append(
            DisasterCluster(
                cluster_id=cluster_id,
                center_lat=round(center_lat, 6),
                center_lng=round(center_lng, 6),
                affected_sensor_ids=list(set(sensor_ids)),
                affected_pipe_ids=unique_pipe_ids,
                estimated_households=households,
                priority_valve_hydrant_id=hydrant_ids[0] if hydrant_ids else f"HYD-{idx}",
                geometry=polygon,
            )
        )

    return DisasterSummaryResponse(
        total_clusters=len(result_clusters),
        total_affected_households=total_households,
        clusters=result_clusters,
    )


@router.post("/simulate", response_model=DisasterSimulateResponse)
async def simulate_disaster(
    count: int = Query(6, ge=1, le=20, description="生成するLevel 3アラート件数"),
) -> DisasterSimulateResponse:
    """デモ用に一括で Level 3 アラートをシミュレーション投入する。"""
    store = get_store()
    base_lat, base_lng = 35.6812, 139.7671

    for i in range(count):
        offset_lat = (i // 3) * 0.005 + (i % 3) * 0.001
        offset_lng = (i // 3) * 0.005 + (i % 3) * 0.001

        alert_item = {
            "telemetry_id": f"TEL-DISASTER-{i+1:03d}",
            "sensor_id": f"SEN-DISASTER-{i+1:03d}",
            "hydrant_id": f"HYD-DISASTER-{i+1:03d}",
            "severity_level": 3,
            "leak_confidence": 95.0,
            "location": {
                "latitude": base_lat + offset_lat,
                "longitude": base_lng + offset_lng,
            },
        }

        if hasattr(store, "add_alert"):
            store.add_alert(alert_item)
        elif hasattr(store, "alerts") and isinstance(store.alerts, list):
            store.alerts.append(alert_item)
        elif hasattr(store, "add"):
            store.add(alert_item)

    return DisasterSimulateResponse(
        inserted_count=count,
        message=f"震災モードシミュレーション: Level 3 アラートを {count} 件一括追加しました",
    )
