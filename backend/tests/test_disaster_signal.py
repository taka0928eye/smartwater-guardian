"""BE-7: 防災シミュレーション用合成 Level 3 波形生成のテスト。

実行方法（backend ディレクトリで）:

    venv/Scripts/python.exe -m pytest tests/test_disaster_signal.py -v
"""

from __future__ import annotations

import base64

import numpy as np

from app.services.audio import SAMPLE_COUNT, SAMPLE_RATE_HZ, analyze_audio
from app.services.disaster_signal import encode_signal_to_base64, generate_level3_signal


def test_generate_level3_signal_shape_and_contract():
    """8000Hz/1.0秒/8000サンプルのMVP契約に一致するPCM16信号を返す。"""
    signal = generate_level3_signal(seed=1)
    assert signal.dtype == np.int16
    assert len(signal) == SAMPLE_COUNT


def test_generate_level3_signal_reproducible_with_same_seed():
    """同一seedで同一波形が再現される。"""
    a = generate_level3_signal(seed=42)
    b = generate_level3_signal(seed=42)
    assert np.array_equal(a, b)


def test_generate_level3_signal_differs_across_seeds():
    """異なるseedでは異なる波形になる（センサーごとに信号データが変化する）。"""
    a = generate_level3_signal(seed=1)
    b = generate_level3_signal(seed=2)
    assert not np.array_equal(a, b)


def test_encode_signal_to_base64_roundtrip():
    """Base64エンコード結果がPCM16LE 8000サンプル分のバイト長を持つ。"""
    signal = generate_level3_signal(seed=7)
    encoded = encode_signal_to_base64(signal)
    decoded = base64.b64decode(encoded, validate=True)
    assert len(decoded) == SAMPLE_COUNT * 2


def test_generate_level3_signal_is_analyzable():
    """analyze_audio() が例外なく実スペクトルを算出できる（全ゼロにならない）。"""
    signal = generate_level3_signal(seed=3)
    encoded = encode_signal_to_base64(signal)
    result = analyze_audio(encoded, sample_rate_hz=SAMPLE_RATE_HZ, duration_sec=1.0)
    assert result.band_energy_ratio >= 0.0
    assert len(result.spectrum) > 0
