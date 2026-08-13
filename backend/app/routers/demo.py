"""DEMO-1: デモ初期状態投入 API。"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from app.schemas.demo import DemoSeedRequest
from app.schemas.telemetry import TelemetryResponse
from app.services.audio import AudioValidationError, analyze_audio
from app.store import StoredTelemetry, get_store

router = APIRouter(prefix="/api/v1", tags=["demo"])


@router.post(
    "/demo/seed",
    response_model=TelemetryResponse,
    status_code=status.HTTP_200_OK,
    summary="デモ初期状態の1件を投入（深刻度は意図値を確定）",
)
def seed_demo(payload: DemoSeedRequest) -> TelemetryResponse:
    """デモシード1件をストアへ投入する。

    ``analyze_audio`` で実スペクトルを算出しつつ、深刻度は ``payload.level`` に
    確定する。実 SVM は合成波形（``generate_signal``）を意図レベルに分類できない
    ため、デモシード専用の補正として深刻度を上書きする（DEMO-1 調査で確認）。
    ハイブリッド方針（実信号 + 深刻度確定）の受け皿であり、実録音のリプレイも
    この経路で深刻度が保証される。
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
    analysis = analysis.model_copy(update={"severity_level": payload.level})

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
        )
    )
    return TelemetryResponse(
        telemetry_id=telemetry_id,
        sensor_id=payload.sensor_id,
        received_at=now,
        status="accepted",
        analysis=analysis,
    )
