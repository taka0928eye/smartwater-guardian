"""BE-7: 防災シミュレーション用の合成 Level 3 波形生成。

外部音声ファイル（``backend/dataset/``、gitignore 対象）に依存せず、ブラウザ操作
のみでいつでも実行できるようにするため、合成波形のみを使う（シード投入＝実音響
WAV の replay、防災シミュレーション＝合成波、と意図的に使い分ける）。波形の形は
``scripts/simulate_sensor.py::generate_signal(level=3, ...)`` と同種の帯域制限
ノイズだが、``app/`` は ``scripts/`` に依存できないためここに独立実装する。
"""

from __future__ import annotations

import base64

import numpy as np

from app.services.audio import SAMPLE_COUNT, SAMPLE_RATE_HZ

INT16_MAX = np.iinfo(np.int16).max
_LEAK_BAND_LOW_HZ = 500.0
_LEAK_BAND_HIGH_HZ = 1_500.0
# irfft 後の信号がほぼ無音（帯域内にエネルギーが存在しない）場合のゼロ割回避。
_MIN_FILTERED_STD = 1e-9


def _band_limited_noise(
    rng: np.random.Generator,
    sample_count: int,
    sample_rate_hz: int,
    low_hz: float,
    high_hz: float,
    amplitude: float,
) -> np.ndarray:
    """指定帯域にのみエネルギーを持つノイズを生成する。"""
    noise = rng.normal(0.0, 1.0, size=sample_count)
    spectrum = np.fft.rfft(noise)
    freqs = np.fft.rfftfreq(sample_count, d=1.0 / sample_rate_hz)
    spectrum[(freqs < low_hz) | (freqs > high_hz)] = 0.0
    filtered = np.fft.irfft(spectrum, n=sample_count)
    std = max(float(np.std(filtered)), _MIN_FILTERED_STD)
    return filtered * (amplitude / std)


def generate_level3_signal(seed: int | None = None) -> np.ndarray:
    """Level 3（破裂相当）を想定した合成 PCM16 モノラル信号を生成する。

    ``app/services/audio.py`` の MVP 契約（8000Hz / 1.0秒 / 8000サンプル）に
    一致させる。500-1500Hz 帯域（漏水帯域）にエネルギーを持つ帯域制限ノイズに
    ブロードバンドノイズを重畳し、``analyze_audio()`` で意味のあるスペクトルを
    算出できるようにする。
    """
    rng = np.random.default_rng(seed)
    broadband = rng.normal(0.0, 0.06, size=SAMPLE_COUNT)
    leak_band = _band_limited_noise(
        rng,
        SAMPLE_COUNT,
        SAMPLE_RATE_HZ,
        _LEAK_BAND_LOW_HZ,
        _LEAK_BAND_HIGH_HZ,
        amplitude=0.18,
    )
    waveform = broadband + leak_band
    clipped: np.ndarray = np.clip(waveform * INT16_MAX, -32768, 32767).astype(np.int16)
    return clipped


def encode_signal_to_base64(signal: np.ndarray) -> str:
    """PCM16 little-endian raw bytes を Base64 文字列へ変換する。"""
    pcm_bytes = signal.astype("<i2", copy=False).tobytes()
    return base64.b64encode(pcm_bytes).decode("ascii")
