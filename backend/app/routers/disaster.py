"""防災モード API ルーター (GET /summary, POST /simulate)。

DEMO-2 再設計: 実在する23消火栓のうち無作為に選んだセンサーを Level 3 に変化
させる（架空センサーの新規追加はしない）。信号データも合成波形
（``app/services/disaster_signal.py``）で更新する。「被災エリア」クラスタ
（GET /summary）は、シミュレーションで選ばれたセンサーのみを対象とする
（通常の漏水検知でたまたま Level 3 になったセンサーは対象外）。
"""

from __future__ import annotations

import base64
import math
import random
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.disaster import (
    DisasterCluster,
    DisasterResetResponse,
    DisasterSimulateResponse,
    DisasterSummaryResponse,
    GeoJSONPolygon,
)
from app.schemas.telemetry import GeoLocation
from app.services.audio import SAMPLE_RATE_HZ, analyze_audio
from app.services.disaster_signal import encode_signal_to_base64, generate_level3_signal
from app.store import (
    StoredTelemetry,
    get_disaster_sensor_ids,
    get_hydrants,
    get_store,
    register_disaster_sensors,
    restore_disaster_baseline,
)

router = APIRouter(prefix="/api/v1/disaster", tags=["disaster"])


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """2点間の大円距離(メートル)を計算。"""
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    return R * (2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a)))


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
def get_disaster_summary(
    threshold_meters: float = Query(300.0, description="クラスタリング距離閾値(m)"),
) -> DisasterSummaryResponse:
    """防災シミュレーションで選出されたセンサーの現在状態を距離でクラスタリングして返す。

    ``register_disaster_sensors()`` に記録された sensor_id のみを対象とする。
    通常の漏水検知でたまたま Level 3 になった別センサーはここに含めない。
    """
    disaster_ids = get_disaster_sensor_ids()
    latest = get_store().latest_sensor_states()
    disaster_alerts = [latest[sensor_id] for sensor_id in disaster_ids if sensor_id in latest]

    if not disaster_alerts:
        return DisasterSummaryResponse(
            total_clusters=0,
            total_affected_households=0,
            clusters=[],
        )

    clusters_raw: list[list[StoredTelemetry]] = []
    for alert in disaster_alerts:
        assigned = False
        for cluster in clusters_raw:
            head = cluster[0]
            distance = haversine_distance(
                alert.location.latitude,
                alert.location.longitude,
                head.location.latitude,
                head.location.longitude,
            )
            if distance <= threshold_meters:
                cluster.append(alert)
                assigned = True
                break
        if not assigned:
            clusters_raw.append([alert])

    result_clusters = []
    total_households = 0
    for idx, group in enumerate(clusters_raw, start=1):
        lats = [item.location.latitude for item in group]
        lngs = [item.location.longitude for item in group]
        center = (sum(lats) / len(lats), sum(lngs) / len(lngs))

        households = len(group) * 120 + 50
        total_households += households

        result_clusters.append(
            DisasterCluster(
                cluster_id=f"CLS-{idx:03d}",
                center_lat=round(center[0], 6),
                center_lng=round(center[1], 6),
                affected_sensor_ids=[item.sensor_id for item in group],
                affected_pipe_ids=[item.hydrant_id for item in group],
                estimated_households=households,
                priority_valve_hydrant_id=group[0].hydrant_id,
                geometry=create_circle_polygon(center[1], center[0], radius_m=threshold_meters),
            )
        )

    return DisasterSummaryResponse(
        total_clusters=len(result_clusters),
        total_affected_households=total_households,
        clusters=result_clusters,
    )


@router.post("/simulate", response_model=DisasterSimulateResponse)
def simulate_disaster(count: int = Query(6, ge=1, le=23)) -> DisasterSimulateResponse:
    """実在消火栓のうち count 件を無作為に選び、信号データごと Level 3 へ変化させる。

    ストア内の全23件を読み直し、選出分は合成波形で新しい解析結果を組み立て、
    非選出分は現在の状態をそのまま保持したうえで、ストアを一括で置き換える
    （常に23件を維持し、アラート一覧・KPI 集計で重複を発生させない）。
    """
    if get_disaster_sensor_ids():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="防災シミュレーションはすでに実行中です",
        )

    store = get_store()
    hydrants = get_hydrants()
    target_count = min(count, len(hydrants))
    selected = random.sample(hydrants, target_count)
    selected_sensor_ids = {hydrant.sensor_id for hydrant in selected}

    baseline_records = store.get_all()
    current = store.latest_sensor_states()
    now = datetime.now(timezone.utc)

    rebuilt: list[StoredTelemetry] = []
    for hydrant in hydrants:
        if hydrant.sensor_id in selected_sensor_ids:
            signal = generate_level3_signal()
            audio_base64 = encode_signal_to_base64(signal)
            analysis = analyze_audio(audio_base64, sample_rate_hz=SAMPLE_RATE_HZ, duration_sec=1.0)
            analysis = analysis.model_copy(update={"severity_level": 3})
            rebuilt.append(
                StoredTelemetry(
                    telemetry_id=f"tlm_disaster_{uuid4().hex[:12]}",
                    sensor_id=hydrant.sensor_id,
                    hydrant_id=hydrant.hydrant_id,
                    recorded_at=now,
                    received_at=now,
                    location=GeoLocation(latitude=hydrant.latitude, longitude=hydrant.longitude),
                    analysis=analysis,
                    audio_pcm16=base64.b64decode(audio_base64, validate=True),
                    sample_rate_hz=SAMPLE_RATE_HZ,
                )
            )
        else:
            existing = current.get(hydrant.sensor_id)
            if existing is not None:
                rebuilt.append(existing)

    store.replace_all(rebuilt)

    register_disaster_sensors(
        sorted(selected_sensor_ids), baseline_records=baseline_records
    )

    return DisasterSimulateResponse(
        inserted_count=target_count,
        message=f"防災シミュレーション: {target_count} 件のセンサーを Level 3 に変化させました",
    )


@router.delete("/simulate", response_model=DisasterResetResponse)
def stop_disaster_simulation() -> DisasterResetResponse:
    """開始前の23件を復元し、同じボタンから通常モードへ戻す。"""
    restored_count = restore_disaster_baseline(get_store())
    return DisasterResetResponse(
        removed_count=restored_count,
        message="防災シミュレーションを終了し、通常モードへ戻りました",
    )
