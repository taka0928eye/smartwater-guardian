"""アラート参照API（BE-6）。

GET /api/v1/alerts で解析済みテレメトリをアラートとして一覧・詳細参照できる。
データは ``app.store`` のインメモリストアを参照する（本番用 DB は CLAUDE.md §3
で構築しない）。``work-order`` は BE-5（補修部材選定・見積自動起票）で実装済みで、
LLM 呼び出しは ``app.services.orcarouter`` にカプセル化する（CLAUDE.md §5.3）。
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.dependencies import HttpClientDep
from app.schemas.alert import AlertDetail, AlertSummary, PipeInfo
from app.schemas.telemetry import AnalysisResult, GeoLocation
from app.schemas.work_order import WorkOrder
from app.services import orcarouter
from app.services.ledger import find_pipe_by_hydrant, get_pipe_age
from app.store import StoredTelemetry, get_store

router = APIRouter(prefix="/api/v1", tags=["alerts"])


class SeedRequest(BaseModel):
    """E2E テスト用シードリクエスト。"""

    count: int = 3


class SeedResponse(BaseModel):
    """E2E テスト用シードレスポンス。"""

    inserted_count: int
    message: str


def _build_pipe_info(hydrant_id: str) -> PipeInfo | None:
    """消火栓IDから配管台帳（BE-4）を照合し、PipeInfo を組み立てる。

    台帳に該当しない hydrant_id は None（フロントは null を許容する設計）。
    """
    pipe = find_pipe_by_hydrant(hydrant_id)
    if pipe is None:
        return None
    return PipeInfo(
        pipe_id=pipe.pipe_id,
        material=pipe.material,
        diameter_mm=pipe.diameter_mm,
        installed_year=pipe.installed_year,
        burial_depth_m=pipe.burial_depth_m,
        age_years=get_pipe_age(pipe.installed_year),
    )


def _to_alert_summary(record: StoredTelemetry) -> AlertSummary:
    """ストア保持レコードを一覧行（AlertSummary）へ変換する。"""
    return AlertSummary(
        telemetry_id=record.telemetry_id,
        sensor_id=record.sensor_id,
        hydrant_id=record.hydrant_id,
        severity_level=record.analysis.severity_level,
        leak_confidence=record.analysis.leak_confidence,
        detected_at=record.received_at,
    )


@router.get(
    "/alerts",
    response_model=list[AlertSummary],
    summary="アラート一覧（深刻度降順）",
)
def list_alerts(
    # Literal[1,2,3] を直接使うと、クエリ文字列 "3" が strict 検証で弾かれて 422 になる。
    # クエリパラメータは常に文字列で届くため、int で受けて ge/le で 1〜3 を強制する
    # （SeverityLevel の許容値と一致させるのが目的）。
    level: int | None = Query(default=None, ge=1, le=3, description="深刻度 Level 1〜3 で絞り込み"),
    limit: int | None = Query(default=None, ge=1, le=500, description="取得件数上限"),
) -> list[AlertSummary]:
    """深刻度降順・新着順に並んだアラート一覧を返す。

    同期 ``def`` は FastAPI のスレッドプールで実行される。ストア操作は内部で
    ``threading.Lock`` に保護されているため、並行アクセスでも安全。
    """
    records = get_store().list_alerts(level=level, limit=limit)
    return [_to_alert_summary(record) for record in records]


@router.get(
    "/alerts/{telemetry_id}",
    response_model=AlertDetail,
    summary="アラート詳細",
)
def get_alert_detail(telemetry_id: str) -> AlertDetail:
    """指定したテレメトリの詳細を返す。存在しない ID は 404。

    エラー時に 500 を返さない（存在しない ID はクライアント起因の 404）。
    """
    record = get_store().get(telemetry_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"テレメトリ {telemetry_id} は見つかりません",
        )
    return AlertDetail(
        **_to_alert_summary(record).model_dump(),
        location=record.location,
        analysis=record.analysis,
        pipe_info=_build_pipe_info(record.hydrant_id),  # BE-4: 配管台帳から照合
    )


@router.post(
    "/alerts/{telemetry_id}/work-order",
    response_model=WorkOrder,
    status_code=status.HTTP_200_OK,
    summary="工事発注書の自動起票（BE-5）",
)
async def create_work_order(telemetry_id: str, client: HttpClientDep) -> WorkOrder:
    """指定したテレメトリの補修部材選定・概算見積・作業指示書を自動起票する。

    BE-5 実装。LLM 呼び出しは ``services/orcarouter.py`` にカプセル化する
    （CLAUDE.md §5.3）。API キー未設定時はフォールバック応答（source == "fallback"）を
    返す。存在しない ID は 404（クライアント起因で 500 にしない）。
    """
    record = get_store().get(telemetry_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"テレメトリ {telemetry_id} は見つかりません",
        )
    alert = AlertDetail(
        **_to_alert_summary(record).model_dump(),
        location=record.location,
        analysis=record.analysis,
        pipe_info=_build_pipe_info(record.hydrant_id),
    )
    pipe = find_pipe_by_hydrant(record.hydrant_id)
    return await orcarouter.create_work_order(client, telemetry_id, alert, pipe)


@router.post(
    "/alerts/seed",
    response_model=SeedResponse,
    status_code=status.HTTP_200_OK,
    summary="E2E テスト用デモシード投入",
)
def seed_alerts_for_e2e(payload: SeedRequest) -> SeedResponse:
    """E2E テスト用にデモアラートをストアへ投入する。

    Level 1, 2, 3 を各 count/3 件ずつ投入する（合計 count 件）。
    global-setup.ts から呼び出され、テスト開始前の初期状態を準備する。
    """
    store = get_store()
    now = datetime.now(UTC)
    base_lat, base_lng = 35.6812, 139.7671
    levels_per_type = payload.count // 3 if payload.count >= 3 else 1

    inserted = 0
    severity_levels: list[Literal[1, 2, 3]] = [3, 2, 1]
    for level in severity_levels:
        for i in range(levels_per_type):
            telemetry_id = f"tlm_e2e_{level}_{i}_{uuid4().hex[:8]}"
            hydrant_id = f"HYD-{(level * 100 + i):03d}"
            sensor_id = f"SEN-{(level * 100 + i):03d}"

            cur_lat = base_lat + (i * 0.0001)
            cur_lng = base_lng + (i * 0.0001)

            stored_telemetry = StoredTelemetry(
                telemetry_id=telemetry_id,
                sensor_id=sensor_id,
                hydrant_id=hydrant_id,
                recorded_at=now,
                received_at=now,
                location=GeoLocation(
                    latitude=cur_lat,
                    longitude=cur_lng,
                ),
                analysis=AnalysisResult(
                    severity_level=level,
                    leak_confidence=90.0 + level * 2,
                    dominant_freq_hz=100 + level * 20,
                    band_energy_ratio=0.8 + level * 0.1,
                ),
            )
            store.add(stored_telemetry)
            inserted += 1

    return SeedResponse(
        inserted_count=inserted,
        message=f"E2E テスト用シード投入完了: {inserted} 件のアラートをストアへ追加しました",
    )
