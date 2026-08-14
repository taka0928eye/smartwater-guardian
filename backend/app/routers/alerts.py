"""アラート参照API（BE-6）。

GET /api/v1/alerts で解析済みテレメトリをアラートとして一覧・詳細参照できる。
データは ``app.store`` のインメモリストアを参照する（本番用 DB は CLAUDE.md §3
で構築しない）。``work-order`` は BE-5（補修部材選定・見積自動起票）で実装済みで、
LLM 呼び出しは ``app.services.orcarouter`` にカプセル化する（CLAUDE.md §5.3）。
"""

from __future__ import annotations

import io
import wave
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel

from app.dependencies import HttpClientDep
from app.schemas.alert import AlertDetail, AlertSummary, PipeInfo, WaveformPoint
from app.schemas.telemetry import AnalysisResult, GeoLocation
from app.schemas.work_order import WorkOrder
from app.services import orcarouter
from app.services.ledger import find_pipe_by_hydrant, get_pipe_age
from app.store import StoredTelemetry, get_hydrants, get_store

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


def _has_audio(record: StoredTelemetry) -> bool:
    """ブラウザ再生に必要なPCM本体とサンプリング周波数が揃っているか返す。"""
    return record.audio_pcm16 is not None and record.sample_rate_hz is not None


def _build_wav(record: StoredTelemetry) -> bytes:
    """保存済みPCM16LE monoを標準WAVコンテナへ格納する。"""
    assert record.audio_pcm16 is not None
    assert record.sample_rate_hz is not None
    output = io.BytesIO()
    with wave.open(output, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(record.sample_rate_hz)
        wav_file.writeframes(record.audio_pcm16)
    return output.getvalue()


def _build_waveform(record: StoredTelemetry) -> list[WaveformPoint]:
    """保存済みPCMから描画用の実サンプルを最大256点抽出する。"""
    if not _has_audio(record):
        return []
    assert record.audio_pcm16 is not None
    assert record.sample_rate_hz is not None

    sample_count = len(record.audio_pcm16) // 2
    point_count = min(256, sample_count)
    if point_count == 0:
        return []
    indices = (
        [0]
        if point_count == 1
        else [
            point_index * (sample_count - 1) // (point_count - 1)
            for point_index in range(point_count)
        ]
    )
    return [
        WaveformPoint(
            time_ms=index * 1000.0 / record.sample_rate_hz,
            amplitude=int.from_bytes(
                record.audio_pcm16[index * 2 : index * 2 + 2],
                "little",
                signed=True,
            )
            / 32768.0,
        )
        for index in indices
    ]


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
        has_audio=_has_audio(record),
        waveform=_build_waveform(record),
        pipe_info=_build_pipe_info(record.hydrant_id),  # BE-4: 配管台帳から照合
    )


@router.get(
    "/alerts/{telemetry_id}/audio",
    response_class=Response,
    summary="アラートの受信音響をWAVで取得",
)
def get_alert_audio(telemetry_id: str) -> Response:
    """指定テレメトリに保存されたPCM16LE monoをWAVとして返す。"""
    record = get_store().get(telemetry_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"テレメトリ {telemetry_id} は見つかりません",
        )
    if not _has_audio(record):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="このアラートには音声データがありません",
        )
    return Response(
        content=_build_wav(record),
        media_type="audio/wav",
        headers={"Cache-Control": "no-store"},
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


# E2E テスト用シードのレベル割当（実在マスタ hydrants.json に対する決定論的マッピング）。
# 実在マスタ（HYD-001〜010 / SNS-001〜010）を使うことで、
# - 詳細ドロワーの配管情報（BE-4: 管台帳 P-xxx 表示）
# - 地図マーカー（SNS-xxx）とアラート（sensor_id）の連動（FE-5）
# が E2E で一貫して検証できる。Level 0（正常）を 1 件含めることで
# 「正常も表示」トグル（FE-5）の切替も検証できる。
_SEED_HYDRANT_LEVELS: dict[str, Literal[0, 1, 2, 3]] = {
    "HYD-003": 3,
    "HYD-004": 3,
    "HYD-007": 3,
    "HYD-005": 2,
    "HYD-006": 2,
    "HYD-008": 2,
    "HYD-009": 1,
    "HYD-010": 1,
    "HYD-001": 1,
    "HYD-002": 0,
}


@router.post(
    "/alerts/seed",
    response_model=SeedResponse,
    status_code=status.HTTP_200_OK,
    summary="E2E テスト用デモシード投入",
)
def seed_alerts_for_e2e(payload: SeedRequest) -> SeedResponse:
    """E2E テスト用にデモアラートをストアへ投入する。

    ``_SEED_HYDRANT_LEVELS`` に従い、実在マスタ（hydrants.json）の消火栓へ
    レベルを決定論的に割り当てて投入する（合計 10 件: L3×3 / L2×3 / L1×3 / L0×1）。
    ``payload.count`` は後方互換用の受領のみで、投入件数には影響しない。
    """
    hydrants = {h.hydrant_id: h for h in get_hydrants()}
    now = datetime.now(UTC)
    store = get_store()

    inserted = 0
    for hydrant_id, level in _SEED_HYDRANT_LEVELS.items():
        hydrant = hydrants.get(hydrant_id)
        if hydrant is None:
            # マスタに無い ID は投入しない（防御的）。実在マスタは全て揃っている前提。
            continue
        store.add(
            StoredTelemetry(
                telemetry_id=f"tlm_e2e_{level}_{inserted}_{uuid4().hex[:8]}",
                sensor_id=hydrant.sensor_id,
                hydrant_id=hydrant.hydrant_id,
                recorded_at=now,
                received_at=now,
                location=GeoLocation(
                    latitude=hydrant.latitude,
                    longitude=hydrant.longitude,
                ),
                analysis=AnalysisResult(
                    severity_level=level,
                    leak_confidence=90.0 + level * 2,
                    dominant_freq_hz=100 + level * 20,
                    band_energy_ratio=(level - 1) * 0.1 + 0.8,
                ),
            )
        )
        inserted += 1

    return SeedResponse(
        inserted_count=inserted,
        message=f"E2E テスト用シード投入完了: {inserted} 件のアラートをストアへ追加しました",
    )
