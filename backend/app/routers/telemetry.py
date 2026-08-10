"""センサテレメトリ受取API（BE-1: ダミー実装）。

音響解析は BE-3（``app/services/audio.py``）のスコープ。ここでは受信と
バリデーションのみを行い、``analysis`` は ``None`` を返す。
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, status

from app.schemas.telemetry import TelemetryRequest, TelemetryResponse

router = APIRouter(prefix="/api/v1", tags=["telemetry"])


@router.post(
    "/telemetry",
    response_model=TelemetryResponse,
    status_code=status.HTTP_200_OK,
    summary="センサテレメトリ受取（ダミー実装）",
)
def ingest_telemetry(payload: TelemetryRequest) -> TelemetryResponse:
    """疑似IoTセンサーからの音響テレメトリを受け取る。

    同期 ``def`` にしているのは意図的。BE-3 で追加する FFT 解析は CPU バウンド
    なため、同期ハンドラのまま FastAPI のスレッドプール実行に任せることで、
    ``run_in_threadpool`` もシグネチャ変更も不要になる。
    """
    # TODO(BE-3): app/services/audio.py の analyze_audio() を呼び出し analysis を格納する。
    #   解析ロジックは CLAUDE.md §5.3 により audio.py に集約する。
    return TelemetryResponse(
        telemetry_id=f"tlm_{uuid4().hex[:12]}",
        sensor_id=payload.sensor_id,
        received_at=datetime.now(timezone.utc),
        status="accepted",
        analysis=None,
    )
