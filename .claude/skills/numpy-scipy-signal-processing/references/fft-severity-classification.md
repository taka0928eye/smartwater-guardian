# `backend/app/services/audio.py` 関数骨格

CLAUDE.md の規約により、音響データのFFT解析・深刻度（Level 1〜3）判定ロジックは
この1ファイルに集約する。以下は「デコード → 前処理 → PSD計算 → 判定」という処理の
流れをバグなく組むための骨格。**周波数帯・閾値の具体値は仮値**であり、実データでの
検証が必要（コード中にその旨のコメントを残すこと）。

```python
# backend/app/services/audio.py
from dataclasses import dataclass
from enum import IntEnum

import numpy as np
import base64
from scipy.signal import welch
from scipy.signal.windows import hann


class LeakSeverity(IntEnum):
    LEVEL_1 = 1  # 経過観察
    LEVEL_2 = 2  # 要点検
    LEVEL_3 = 3  # 緊急対応


@dataclass(frozen=True)
class AnalysisResult:
    severity: LeakSeverity
    band_energy_ratio: float
    dominant_frequency_hz: float


# --- 仮値: 実データでのチューニングが必要 ---
# 漏水音の卓越周波数帯として一般に語られる範囲（要検証）
LEAK_BAND_HZ = (200.0, 2500.0)
SEVERITY_THRESHOLDS = {
    LeakSeverity.LEVEL_3: 0.60,  # band_energy_ratio がこれ以上ならLevel3
    LeakSeverity.LEVEL_2: 0.30,  # これ以上ならLevel2、それ未満はLevel1
}
# --------------------------------------------


def decode_pcm16_mono(audio_base64: str) -> np.ndarray:
    raw_bytes = base64.b64decode(audio_base64)
    samples = np.frombuffer(raw_bytes, dtype=np.int16)
    return samples.astype(np.float64) / np.iinfo(np.int16).max


def compute_psd(samples: np.ndarray, sample_rate_hz: int) -> tuple[np.ndarray, np.ndarray]:
    nperseg = min(1024, len(samples))
    if nperseg == 0:
        raise ValueError("samples is empty")
    freqs, psd = welch(samples, fs=sample_rate_hz, window="hann", nperseg=nperseg)
    return freqs, psd


def band_energy_ratio(freqs: np.ndarray, psd: np.ndarray, band_hz: tuple[float, float]) -> float:
    total_energy = np.trapz(psd, freqs)
    if total_energy <= 0:
        return 0.0
    mask = (freqs >= band_hz[0]) & (freqs <= band_hz[1])
    band_energy = np.trapz(psd[mask], freqs[mask])
    return float(band_energy / total_energy)


def classify_severity(ratio: float) -> LeakSeverity:
    if ratio >= SEVERITY_THRESHOLDS[LeakSeverity.LEVEL_3]:
        return LeakSeverity.LEVEL_3
    if ratio >= SEVERITY_THRESHOLDS[LeakSeverity.LEVEL_2]:
        return LeakSeverity.LEVEL_2
    return LeakSeverity.LEVEL_1


def analyze_audio(audio_base64: str, sample_rate_hz: int) -> AnalysisResult:
    samples = decode_pcm16_mono(audio_base64)
    freqs, psd = compute_psd(samples, sample_rate_hz)

    ratio = band_energy_ratio(freqs, psd, LEAK_BAND_HZ)
    severity = classify_severity(ratio)
    dominant_frequency_hz = float(freqs[np.argmax(psd)])

    return AnalysisResult(
        severity=severity,
        band_energy_ratio=ratio,
        dominant_frequency_hz=dominant_frequency_hz,
    )
```

## 分割方針

- `decode_pcm16_mono` / `compute_psd` / `band_energy_ratio` / `classify_severity` を
  個別関数に分けているのは、それぞれを単体テストしやすくするため（例:
  `classify_severity` は純粋関数なので閾値のユニットテストが書きやすい）。
- `LEAK_BAND_HZ` / `SEVERITY_THRESHOLDS` はモジュール冒頭の定数にまとめ、関数の中に
  マジックナンバーとして埋め込まない。実データで再チューニングする際にここだけ
  変更すれば済む。
- FastAPI エンドポイント側からこの `analyze_audio` を呼ぶ際は、CPUバウンドな処理
  （FFT/PSD計算）なので `run_in_threadpool` 経由で呼ぶ（`fastapi-pydantic-v2-patterns`
  スキル参照）。
- `np.trapz` は台形積分でエネルギー（PSD × 周波数幅）を近似している。周波数ビンの
  刻み幅が不均一な場合でも積分区間を正しく扱える。
