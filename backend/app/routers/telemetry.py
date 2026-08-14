"""センサテレメトリ受取API（BE-1 + BE-3 + BE-6）。"""

from __future__ import annotations

import base64
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from app.schemas.telemetry import TelemetryRequest, TelemetryResponse
from app.services.audio import AudioValidationError, analyze_audio
from app.store import StoredTelemetry, get_store

router = APIRouter(prefix="/api/v1", tags=["telemetry"])


@router.post(
    "/telemetry",
    response_model=TelemetryResponse,
    status_code=status.HTTP_200_OK,
    summary="センサテレメトリ受取（SVM + DSP解析つき）",
)
def ingest_telemetry(payload: TelemetryRequest) -> TelemetryResponse:
    """IoTセンサーからの音響テレメトリを解析して保存する。

    同期 ``def`` にしているのは意図的。音響解析は CPU バウンドなため、同期ハンドラの
    まま FastAPI のスレッドプール実行に任せることで、``run_in_threadpool`` も
    シグネチャ変更も不要になる。
    """
    try:
        analysis = analyze_audio(
            payload.audio_base64,
            sample_rate_hz=payload.sample_rate_hz,
            duration_sec=payload.duration_sec,
        )
    except AudioValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"audio_base64 を解析できません: {exc}",
        ) from exc
    now = datetime.now(UTC)
    telemetry_id = f"tlm_{uuid4().hex[:12]}"

    get_store().add(
        StoredTelemetry(
            telemetry_id=telemetry_id,
            sensor_id=payload.sensor_id,
            hydrant_id=payload.hydrant_id,
            recorded_at=payload.recorded_at,
            received_at=now,
            location=payload.location,
            analysis=analysis,
            audio_pcm16=base64.b64decode(payload.audio_base64, validate=True),
            sample_rate_hz=payload.sample_rate_hz,
        )
    )

    return TelemetryResponse(
        telemetry_id=telemetry_id,
        sensor_id=payload.sensor_id,
        received_at=now,
        status="accepted",
        analysis=analysis,
    )
