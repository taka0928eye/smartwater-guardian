---
name: numpy-scipy-signal-processing
description: >
  NumPy（2.5.2）/ SciPy（1.18.0）を使ったFFT・周波数解析・ノイズ除去の実装パターン。
  漏水音の周波数解析と深刻度（Level 1〜3）判定ロジックをバグなく書くためのリファレンス。
  Triggers on: backend/app/services/audio.py の実装・編集、Base64音響データのデコード、
  FFT/周波数解析、scipy.signal / scipy.fft の利用、ノイズフィルタリング、
  漏水音の深刻度判定ロジック。
---

# NumPy / SciPy 信号処理パターン（漏水音解析向け）

CLAUDE.md の規約：音響データのFFT解析・深刻度（Level 1〜3）判定ロジックは
`backend/app/services/audio.py` に集約する。具体的な関数骨格は
[references/fft-severity-classification.md](references/fft-severity-classification.md)
を参照。ここでは、この種の処理でバグを生みやすい落とし穴を中心にまとめる。

## Base64 → PCM → numpy 配列のデコード

センサーは音響データを Base64 文字列で送ってくる想定（`fastapi-pydantic-v2-patterns`
スキルの `SensorReading.audio_base64` 参照）。デコード時の典型的なバグ：

```python
import base64

import numpy as np


def decode_pcm16_mono(audio_base64: str) -> np.ndarray:
    raw_bytes = base64.b64decode(audio_base64)
    # dtype=np.int16 を明示しないと勝手な型解釈でビット列が壊れる
    samples = np.frombuffer(raw_bytes, dtype=np.int16)
    # int16のまま演算するとオーバーフローする（例: 2つの大きな振幅を足す等）ので
    # 解析用には float に正規化してから使う
    return samples.astype(np.float64) / np.iinfo(np.int16).max
```

- `np.frombuffer` の `dtype` を省略しない（既定は `float64` 解釈になり、PCM16の
  バイト列を無関係な浮動小数点として読んでしまう）。
- サンプルレート・チャンネル数（モノラル前提）・ビット深度は**センサー側の送信仕様に
  依存する定数**。コード中でマジックナンバーとして埋め込まず、`SensorReading` の
  フィールド（`sample_rate_hz` 等）から受け取るか、モジュール冒頭の定数として明示する。
- `int16` の配列同士を直接足し算・二乗するとオーバーフローする。FFT前の前処理
  （窓関数適用、正規化）は必ず `float32`/`float64` に変換してから行う。

## 窓関数をかけてからFFTする

生の信号にそのまま `np.fft.fft` をかけると、信号の切り出し境界が不連続になり
スペクトル漏れ（spectral leakage）でノイズフロアが持ち上がる。解析前に窓関数
（Hann窓など）を掛けるのが定石：

```python
from scipy.fft import rfft, rfftfreq
from scipy.signal.windows import hann


def compute_spectrum(samples: np.ndarray, sample_rate_hz: int) -> tuple[np.ndarray, np.ndarray]:
    window = hann(len(samples))
    windowed = samples * window

    # 実数信号には rfft を使う（fft の半分の計算量で済み、負の周波数の重複も出ない）
    spectrum = rfft(windowed)
    # rfftfreq(n, d=1/sample_rate) で正しいビン幅になる。d に sample_rate を
    # そのまま渡す間違いが多い（1/サンプルレート＝サンプリング周期を渡す）
    freqs = rfftfreq(len(samples), d=1.0 / sample_rate_hz)

    magnitude = np.abs(spectrum)
    return freqs, magnitude
```

- 実数信号（マイク入力は実数）には `rfft`/`rfftfreq` を使う。`fft`/`fftfreq` を使うと
  負の周波数側も含めた対称なスペクトルが返り、ピーク検出や帯域エネルギー計算で
  二重カウントするバグになりやすい。
- `rfftfreq` の第二引数 `d` は「サンプリング周期」（`1 / sample_rate_hz`）。
  `sample_rate_hz` をそのまま渡す取り違えが典型的なバグ。

## 生FFTより `scipy.signal.welch`（PSD）の方がノイズに強い

単発のFFTは環境ノイズの影響を受けやすい。複数フレームに分割して平均を取る
Welch法（パワースペクトル密度: PSD）を使うと、突発ノイズに対してロバストな
判定ができる：

```python
from scipy.signal import welch


def compute_psd(samples: np.ndarray, sample_rate_hz: int) -> tuple[np.ndarray, np.ndarray]:
    freqs, psd = welch(
        samples,
        fs=sample_rate_hz,
        window="hann",
        nperseg=min(1024, len(samples)),  # サンプル数がnpersegより短いとエラーになる
    )
    return freqs, psd
```

- `nperseg` がサンプル数を超えるとエラーになる（短い録音クリップを扱う場合は
  `min(1024, len(samples))` のようにガードする）。
- 深刻度判定は「特定周波数帯のエネルギー比率」（例: 着目帯域のPSD積分値 ÷
  全帯域のPSD積分値）のような相対指標にすると、マイクのゲイン差・距離差に対して
  頑健になりやすい。

## バンドパスフィルタでノイズ除去する場合

```python
from scipy.signal import butter, sosfiltfilt


def bandpass_filter(
    samples: np.ndarray, sample_rate_hz: int, low_hz: float, high_hz: float
) -> np.ndarray:
    nyquist = sample_rate_hz / 2
    sos = butter(N=4, Wn=[low_hz / nyquist, high_hz / nyquist], btype="bandpass", output="sos")
    # filtfilt系は位相遅延が出ない。sosfiltfilt はSOS形式で数値的に安定
    return sosfiltfilt(sos, samples)
```

- カットオフ周波数は必ずナイキスト周波数（`sample_rate_hz / 2`）で正規化する
  （`butter` の `Wn` は 0〜1 の正規化周波数を期待する）。生のHz値をそのまま渡すのは
  よくある間違い。
- `output="sos"` + `sosfiltfilt` を使う（`b, a` 係数形式の `filtfilt` は次数が
  高くなると数値的に不安定になりやすい）。

## 深刻度（Level 1〜3）判定のロジック配置

判定の周波数帯・閾値は水道管の材質・センサー設置条件によって変わる**要チューニングの
仮値**であり、このスキルの時点では断定できない。判定ロジックの実装骨格・関数分割の
やり方は
[references/fft-severity-classification.md](references/fft-severity-classification.md)
を参照。閾値そのものは実データでの検証（またはドメイン知識を持つ関係者への確認）が
必要な値としてコード中に明示コメントを残す。
