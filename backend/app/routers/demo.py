"""DEMO-1/DEMO-2: デモ初期状態投入 API。"""

from __future__ import annotations

import base64
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.schemas.demo import DemoSeedBatchResponse, DemoSeedRequest
from app.schemas.telemetry import TelemetryResponse
from app.services import demo_seed
from app.services.audio import AudioValidationError, analyze_audio
from app.services.demo_seed import DemoSeedError
from app.store import StoredTelemetry, clear_disaster_state, get_store, initialize_sensors

router = APIRouter(prefix="/api/v1", tags=["demo"])


class DemoClearResponse(BaseModel):
    """デモシードクリア API の応答スキーマ。"""

    status: str
    cleared_count: int
    message: str


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


@router.post(
    "/demo/seed-batch",
    response_model=DemoSeedBatchResponse,
    status_code=status.HTTP_200_OK,
    summary="デモ初期状態を一括投入（Lv0×8/Lv1×8/Lv2×3/Lv3×1、常に20件）",
)
def seed_demo_batch(
    seed: int | None = Query(default=None, description="配分・音声選択の再現用シード"),
) -> DemoSeedBatchResponse:
    """20消火栓へLv0×8/Lv1×8/Lv2×3/Lv3×1を一括投入する（DEMO-2）。

    ``app/services/demo_seed.py`` が ``backend/dataset`` の実音響WAVを replay し、
    既存レコードを破棄してから20件を書き直す（重複を作らない）。音声データ
    セット未配置（gitignore 対象のため起こり得る）は 404 を返す（500にしない）。
    """
    try:
        result = demo_seed.run_seed_batch(get_store(), demo_seed.DEFAULT_AUDIO_DIR, seed=seed)
    except DemoSeedError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"デモシード一括投入に失敗しました: {exc}",
        ) from exc

    return DemoSeedBatchResponse(
        status="seeded",
        inserted_count=result.inserted_count,
        level_counts=result.level_counts,
        message=f"{result.inserted_count} 件投入しました（内訳: {result.level_counts}）",
    )


@router.delete(
    "/demo/clear",
    response_model=DemoClearResponse,
    status_code=status.HTTP_200_OK,
    summary="デモシード状態をクリアし、20件Lv0の初期状態に戻す",
)
def clear_demo() -> DemoClearResponse:
    """デモシード状態をクリアし、20件Lv0（正常）の初期状態に戻す。

    - ストア内の全アラート・分析結果を破棄し、hydrants.json 20件を
      severity_level=0 で再初期化する（``initialize_sensors()``）
    - 防災シミュレーションで記録された Level 3 対象センサーIDもクリア

    地図・アラート一覧・KPI サマリは常に「20件・全て正常」の初期表示状態に
    戻る。バックエンド再起動不要。
    """
    store = get_store()
    cleared_count = len(store)
    store.clear()
    # 防災シミュレーションで記録された対象センサーIDもクリアして、
    # 被災エリアクラスタ表示をリセット
    clear_disaster_state()
    initialize_sensors(store)
    message = (
        f"{cleared_count} 件のアラートをクリアし、"
        "20件Lv0（正常）の初期状態にリセットしました"
    )
    return DemoClearResponse(
        status="cleared",
        cleared_count=cleared_count,
        message=message,
    )
