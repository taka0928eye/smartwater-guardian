"""センサテレメトリ受取API（BE-1 + BE-6 モック解析）。

BE-1 では受信とバリデーションのみで ``analysis`` を ``None`` にしていたが、
BE-6 で「解析済みテレメトリの保持とアラートAPI参照」を実現するため、受信した
音声データから擬似的な解析結果を生成し、インメモリストア（``app.store``）へ
登録する。

音響解析は BE-3（``app/services/audio.py``）のスコープ。ここに実装している
``_analyze_audio_mock`` は **BE-3 が実装されるまでの仮実装**であり、
``analyze_audio()`` に置き換えて破棄する。
"""

from __future__ import annotations

import base64
from datetime import datetime, timezone
from uuid import uuid4

import numpy as np
from fastapi import APIRouter, status

from app.schemas.telemetry import (
    AnalysisResult,
    SeverityLevel,
    SpectrumPoint,
    TelemetryRequest,
    TelemetryResponse,
)
from app.store import StoredTelemetry, get_store

router = APIRouter(prefix="/api/v1", tags=["telemetry"])

# 漏水帯域（BE-3 の本実装と同じ仮値。PRD §2 準拠）
LEAK_BAND_HZ = (500.0, 1500.0)
# FE-4 が描画するスペクトル点数（PSD をダウンサンプルする）
N_SPECTRUM = 128
# 帯域エネルギー比がこれ未満なら卓越ピークなしとして severity 1
SEVERITY_BAND_RATIO_MIN = 0.20
# RMS 振幅の仮閾値（BE-2 の実振幅が確定したら再調整が必要）
SEVERITY_RMS_THRESHOLDS = {3: 0.25, 2: 0.08}


def _decode_pcm16(audio_base64: str) -> np.ndarray:
    """PCM16 モノラル音声の Base64 を float64（-1.0〜1.0）に正規化して返す。

    ``dtype=np.int16`` を明示しないと float64 解釈でビット列が壊れる（BE-3 地雷2）。
    """
    raw = base64.b64decode(audio_base64)
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float64)
    return samples / np.iinfo(np.int16).max


def _periodogram(samples: np.ndarray, sample_rate_hz: int) -> tuple[np.ndarray, np.ndarray]:
    """ハニング窓付き rfft による振幅スペクトルを返す。

    実信号なので ``rfft`` / ``rfftfreq`` を使う（``fft`` だと負周波数を二重計上する）。
    ``d`` に渡すのはサンプリング周期 ``1/sample_rate_hz``。
    空配列チェックは呼び出し元（``_analyze_audio_mock``）で実施済みのため、ここでは行わない。
    """
    n = len(samples)
    windowed = samples * np.hanning(n)
    magnitudes = np.abs(np.fft.rfft(windowed))
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate_hz)
    return freqs, magnitudes


def _downsample_spectrum(
    freqs: np.ndarray, magnitudes: np.ndarray, n: int = N_SPECTRUM
) -> list[SpectrumPoint]:
    """スペクトルを n 点へダウンサンプルする。

    ``np.interp`` の線形補間で必ず n 点を返す。全ビンを返すとレスポンスが肥大するため、
    短い音声（rfft のビン数 < n）でも破綻しない。
    """
    target_freqs = np.linspace(freqs[0], freqs[-1], n)
    target_magnitudes = np.interp(target_freqs, freqs, magnitudes)
    return [
        SpectrumPoint(freq_hz=float(f), magnitude=float(m))
        for f, m in zip(target_freqs, target_magnitudes)
    ]


def _band_energy_ratio(
    freqs: np.ndarray, magnitudes: np.ndarray, band: tuple[float, float]
) -> float:
    """漏水帯域のエネルギー比を返す（全帯域の総和に対する帯域内の割合）。

    numpy 2.5 では ``np.trapz`` が削除済みのため、``np.sum`` で近似する（BE-3 地雷1）。
    """
    mask = (freqs >= band[0]) & (freqs <= band[1])
    total = float(np.sum(magnitudes))
    if total <= 0.0:
        return 0.0
    return float(np.sum(magnitudes[mask]) / total)


def _classify_severity(rms: float, band_ratio: float) -> SeverityLevel:
    """帯域エネルギー比 + RMS 振幅の2因子で深刻度 Level 1〜3 を仮判定する。

    閾値は BE-2 の実振幅が未確定のため仮値。BE-3 の本実装が入れば不要になる。
    """
    if band_ratio < SEVERITY_BAND_RATIO_MIN:
        return 1  # 漏水帯域に卓越ピークが無い → 正常/微小
    if rms >= SEVERITY_RMS_THRESHOLDS[3]:
        return 3
    if rms >= SEVERITY_RMS_THRESHOLDS[2]:
        return 2
    return 1


def _analyze_audio_mock(audio_base64: str, sample_rate_hz: int) -> AnalysisResult:
    """受信音声から擬似的な解析結果を生成する【仮実装】。

    TODO(BE-3): ``app/services/audio.py`` の ``analyze_audio()`` に置き換える。
    ハイパスフィルタ・Welch 法 PSD・帯域比判定は BE-3 のスコープ。
    """
    samples = _decode_pcm16(audio_base64)
    if samples.size == 0:
        # _periodogram 側にも同じガードがあるが、RMS 計算（np.mean）の前に
        # 弾いておかないと「Mean of empty slice」の RuntimeWarning が出る。
        raise ValueError("音声データが空です")
    rms = float(np.sqrt(np.mean(samples**2)))  # RMS 振幅
    freqs, magnitudes = _periodogram(samples, sample_rate_hz)
    ratio = _band_energy_ratio(freqs, magnitudes, LEAK_BAND_HZ)
    severity = _classify_severity(rms, ratio)
    dominant_freq_hz = float(freqs[int(np.argmax(magnitudes))])
    # 仮の確信度換算（帯域比 100% 換算 + RMS 振幅加点）。BE-3 で見直す。
    confidence = round(min(100.0, ratio * 100.0 + rms * 80.0), 1)
    return AnalysisResult(
        leak_confidence=confidence,
        severity_level=severity,
        dominant_freq_hz=dominant_freq_hz,
        band_energy_ratio=ratio,
        spectrum=_downsample_spectrum(freqs, magnitudes),
    )


@router.post(
    "/telemetry",
    response_model=TelemetryResponse,
    status_code=status.HTTP_200_OK,
    summary="センサテレメトリ受取（モック解析つき）",
)
def ingest_telemetry(payload: TelemetryRequest) -> TelemetryResponse:
    """疑似IoTセンサーからの音響テレメトリを受け取り、モック解析して保存する。

    同期 ``def`` にしているのは意図的。FFT 解析は CPU バウンドなため、同期ハンドラの
    まま FastAPI のスレッドプール実行に任せることで、``run_in_threadpool`` も
    シグネチャ変更も不要になる。
    """
    # TODO(BE-3): app/services/audio.py の analyze_audio() を呼び出し analysis を格納する。
    #   解析ロジックは CLAUDE.md §5.3 により audio.py に集約する。ここは BE-6 までの仮実装。
    analysis = _analyze_audio_mock(payload.audio_base64, payload.sample_rate_hz)
    now = datetime.now(timezone.utc)
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
