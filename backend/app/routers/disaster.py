"""防災モード API ルーター (GET /summary, POST /simulate)。"""

import math
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Query

from app.schemas.disaster import (
    DisasterCluster,
    DisasterSimulateResponse,
    DisasterSummaryResponse,
    GeoJSONPolygon,
)
from app.schemas.telemetry import AnalysisResult, GeoLocation, SeverityLevel
from app.store import StoredTelemetry, get_store

router = APIRouter(prefix="/api/v1/disaster", tags=["disaster"])


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """2点間の大円距離(メートル)を計算。"""
    R = 6371000.0  # 地球の半径(m)
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


def create_circle_polygon(center_lng: float, center_lat: float, radius_m: float = 300.0, num_points: int = 16) -> GeoJSONPolygon:
    """重心から半径 radius_m メートルの多角形近似 GeoJSON Polygon を生成。"""
    coords = []
    lat_rad = math.radians(center_lat)
    
    # 1度あたりの距離(約)
    meters_per_lat = 111111.0
    meters_per_lng = 111111.0 * math.cos(lat_rad)

    for i in range(num_points):
        angle = 2.0 * math.pi * i / num_points
        dx = radius_m * math.cos(angle)
        dy = radius_m * math.sin(angle)

        lng = center_lng + (dx / meters_per_lng)
        lat = center_lat + (dy / meters_per_lat)
        coords.append([round(lng, 6), round(lat, 6)])

    # 始点と終点を一致させる
    coords.append(coords[0])
    return GeoJSONPolygon(type="Polygon", coordinates=[coords])


@router.get("/summary", response_model=DisasterSummaryResponse)
def get_disaster_summary(threshold_meters: float = Query(300.0, description="クラスタリング距離閾値(m)")) -> DisasterSummaryResponse:
    """Level 3 アラートを一括取得し、距離閾値でクラスタリングして被災エリアを返却する。"""
    store = get_store()
    all_alerts = store.list_alerts()
    # Level 3 のアラートのみフィルタリング
    level3_alerts = [a for a in all_alerts if a.analysis.severity_level == 3]

    if not level3_alerts:
        return DisasterSummaryResponse(
            total_clusters=0,
            total_affected_households=0,
            clusters=[],
        )

    # 貪欲法クラスタリング
    clusters_raw: list[list[Any]] = []
    for alert in level3_alerts:
        lat = alert.location.latitude
        lng = alert.location.longitude
        
        assigned = False
        for cluster in clusters_raw:
            # クラスタ内の各要素との距離を検証
            for item in cluster:
                dist = haversine_distance(lat, lng, item.location.latitude, item.location.longitude)
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
        
        lats = [item.location.latitude for item in group]
        lngs = [item.location.longitude for item in group]
        center_lat = sum(lats) / len(lats)
        center_lng = sum(lngs) / len(lngs)

        sensor_ids = list({item.sensor_id for item in group if hasattr(item, "sensor_id")})
        
        # 影響配管・優先バルブ（消火栓）の選定
        pipe_ids = []
        hydrant_ids = []
        for item in group:
            if hasattr(item, "pipe_info") and item.pipe_info:
                pipe_ids.append(item.pipe_info.pipe_id)
            if hasattr(item, "hydrant_id"):
                hydrant_ids.append(item.hydrant_id)

        unique_pipe_ids = list(set(pipe_ids)) if pipe_ids else [f"PIPE-SYS-{idx}"]
        priority_hydrant = hydrant_ids[0] if hydrant_ids else f"HYD-PRIORITY-{idx}"

        # 口径/件数から試算した仮世帯数
        households = len(group) * 120 + len(unique_pipe_ids) * 50
        total_households += households

        polygon = create_circle_polygon(center_lng, center_lat, radius_m=300.0)

        result_clusters.append(
            DisasterCluster(
                cluster_id=cluster_id,
                center_lat=round(center_lat, 6),
                center_lng=round(center_lng, 6),
                affected_sensor_ids=sensor_ids,
                affected_pipe_ids=unique_pipe_ids,
                estimated_households=households,
                priority_valve_hydrant_id=priority_hydrant,
                geometry=polygon,
            )
        )

    return DisasterSummaryResponse(
        total_clusters=len(result_clusters),
        total_affected_households=total_households,
        clusters=result_clusters,
    )


@router.post("/simulate", response_model=DisasterSimulateResponse)
def simulate_disaster(count: int = Query(6, ge=1, le=20, description="生成するLevel 3アラート件数")) -> DisasterSimulateResponse:
    """デモ用に一括で Level 3 アラートをシミュレーション投入する（震災時の被害マッピング用）。"""
    store = get_store()
    base_lat, base_lng = 35.6812, 139.7671  # 東京駅周辺

    for i in range(count):
        # グリッド状にアラートを分布させる（3x列）
        offset_lat = (i // 3) * 0.005 + (i % 3) * 0.001
        offset_lng = (i // 3) * 0.005 + (i % 3) * 0.001

        # シミュレーション用アラートを構築
        telemetry_id = f"sim-{uuid.uuid4().hex[:8]}"
        sensor_id = f"SENSOR-SIM-{i+1:03d}"
        hydrant_id = f"HYDRANT-SIM-{i+1:03d}"

        # Level 3（管路破裂）のアナリシス結果を生成
        analysis = AnalysisResult(
            leak_confidence=95.0,  # AI スコア（0-100）
            severity_level=3,  # type: ignore[arg-type]
            dominant_freq_hz=950.0,  # 卓越周波数 (Hz)
            band_energy_ratio=0.85,  # エネルギー比（0-1.0）
            spectrum=[],  # スペクトルポイント（デモ用に空）
        )

        record = StoredTelemetry(
            telemetry_id=telemetry_id,
            sensor_id=sensor_id,
            hydrant_id=hydrant_id,
            recorded_at=datetime.now(timezone.utc),
            received_at=datetime.now(timezone.utc),
            location=GeoLocation(
                latitude=base_lat + offset_lat,
                longitude=base_lng + offset_lng,
            ),
            analysis=analysis,
        )

        store.add(record)

    return DisasterSimulateResponse(
        inserted_count=count,
        message=f"震災モードシミュレーション: Level 3 アラートを {count} 件一括追加しました（東京駅周辺）",
    )
