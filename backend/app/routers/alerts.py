"""アラート参照API（BE-6）。

GET /api/v1/alerts で解析済みテレメトリをアラートとして一覧・詳細参照できる。
データは ``app.store`` のインメモリストアを参照する（本番用 DB は CLAUDE.md §3
で構築しない）。``work-order`` は BE-5（補修部材選定・見積自動起票）のスタブで、
実在 ID には 501 を返す。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.alert import AlertDetail, AlertSummary
from app.schemas.telemetry import SeverityLevel
from app.store import StoredTelemetry, get_store

router = APIRouter(prefix="/api/v1", tags=["alerts"])


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
        pipe_info=None,  # BE-4（配管台帳）実装までは常に null
    )


@router.post(
    "/alerts/{telemetry_id}/work-order",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="工事発注書の自動起票（BE-5 スタブ）",
)
def create_work_order(telemetry_id: str) -> None:
    """BE-5（補修部材選定・見積自動起票）のスタブ。

    実在する ID には 501、存在しない ID には 404 を返す。
    """
    if get_store().get(telemetry_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"テレメトリ {telemetry_id} は見つかりません",
        )
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="BE-5 未実装のため自動起票は利用できません",
    )
