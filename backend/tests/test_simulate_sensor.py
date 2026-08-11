"""BE-2: 疑似センサーデータ生成CLIのテスト。"""

from __future__ import annotations

import base64
import json
import struct
import wave
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest
import requests

from app.schemas.telemetry import TelemetryRequest
from scripts.simulate_sensor import (
    DEFAULT_DURATION_SEC,
    DEFAULT_SAMPLE_RATE_HZ,
    HydrantDataError,
    HydrantNotFoundError,
    SignalGenerationError,
    SimulationError,
    TelemetrySendError,
    build_payload,
    encode_audio,
    generate_signal,
    load_hydrants,
    parse_args,
    run_simulation,
    send_telemetry,
)


def write_test_wav(
    path: Path,
    pcm_bytes: bytes,
    *,
    sample_rate_hz: int = 8_000,
    channels: int = 1,
    sample_width: int = 2,
) -> None:
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate_hz)
        wav_file.writeframes(pcm_bytes)


def write_compressed_wav(path: Path) -> None:
    audio_format_alaw = 6
    channels = 1
    sample_rate_hz = 8_000
    sample_width = 1
    pcm_bytes = b"\xd5" * 8
    fmt_chunk = struct.pack(
        "<HHIIHH",
        audio_format_alaw,
        channels,
        sample_rate_hz,
        sample_rate_hz * channels * sample_width,
        channels * sample_width,
        sample_width * 8,
    )
    riff_size = 4 + (8 + len(fmt_chunk)) + (8 + len(pcm_bytes))
    path.write_bytes(
        struct.pack("<4sI4s", b"RIFF", riff_size, b"WAVE")
        + struct.pack("<4sI", b"fmt ", len(fmt_chunk))
        + fmt_chunk
        + struct.pack("<4sI", b"data", len(pcm_bytes))
        + pcm_bytes
    )


def run_replay(
    audio_file: Path,
    post_func,
    *,
    count: int = 1,
    interval_sec: float = 0,
):
    return run_simulation(
        level=None,
        count=count,
        interval_sec=interval_sec,
        hydrant_id="HYD-001",
        url="http://example.test/api/v1/telemetry",
        audio_file=audio_file,
        post_func=post_func,
    )


def assert_replay_rejected_before_posting(audio_file: Path) -> None:
    post_calls = 0

    def fake_post(url: str, payload: dict, timeout_sec: float) -> dict:
        nonlocal post_calls
        post_calls += 1
        return {"status": "accepted"}

    with pytest.raises(SimulationError):
        run_replay(audio_file, fake_post)

    assert post_calls == 0


def rms(signal: np.ndarray) -> float:
    return float(np.sqrt(np.mean(signal.astype(np.float64) ** 2)))


def dominant_freq_hz(signal: np.ndarray, sample_rate_hz: int) -> float:
    spectrum = np.abs(np.fft.rfft(signal.astype(np.float64)))
    freqs = np.fft.rfftfreq(signal.size, d=1.0 / sample_rate_hz)
    spectrum[0] = 0.0
    return float(freqs[int(np.argmax(spectrum))])


def band_energy_ratio(
    signal: np.ndarray,
    sample_rate_hz: int,
    low_hz: float,
    high_hz: float,
) -> float:
    spectrum = np.abs(np.fft.rfft(signal.astype(np.float64))) ** 2
    freqs = np.fft.rfftfreq(signal.size, d=1.0 / sample_rate_hz)
    total = float(np.sum(spectrum[1:]))
    band = float(np.sum(spectrum[(freqs >= low_hz) & (freqs <= high_hz)]))
    return band / total


def spectral_flatness(signal: np.ndarray) -> float:
    spectrum = np.abs(np.fft.rfft(signal.astype(np.float64)))[1:]
    spectrum = spectrum[spectrum > 0]
    return float(np.exp(np.mean(np.log(spectrum))) / np.mean(spectrum))


def test_generate_signal_returns_pcm16_array_with_expected_length():
    signal = generate_signal(level=0, sample_rate_hz=16_000, duration_sec=2.0, seed=42)

    assert isinstance(signal, np.ndarray)
    assert signal.dtype == np.int16
    assert len(signal) == 32_000


def test_generate_signal_seed_is_deterministic_and_varies_by_seed():
    signal_a = generate_signal(level=2, sample_rate_hz=16_000, duration_sec=2.0, seed=42)
    signal_b = generate_signal(level=2, sample_rate_hz=16_000, duration_sec=2.0, seed=42)
    signal_c = generate_signal(level=2, sample_rate_hz=16_000, duration_sec=2.0, seed=43)

    assert np.array_equal(signal_a, signal_b)
    assert not np.array_equal(signal_a, signal_c)


@pytest.mark.parametrize("level", [-1, 4, 99])
def test_generate_signal_rejects_unknown_level(level: int):
    with pytest.raises(ValueError):
        generate_signal(level=level, sample_rate_hz=16_000, duration_sec=2.0, seed=42)


def test_level_1_has_dominant_peak_in_leak_tone_band():
    signal = generate_signal(level=1, sample_rate_hz=16_000, duration_sec=2.0, seed=42)

    assert 800.0 <= dominant_freq_hz(signal, 16_000) <= 1_200.0


def test_leak_band_energy_ratio_increases_with_level():
    signals = [
        generate_signal(level=level, sample_rate_hz=16_000, duration_sec=2.0, seed=42)
        for level in range(4)
    ]
    ratios = [band_energy_ratio(signal, 16_000, 500.0, 1_500.0) for signal in signals]

    assert ratios == sorted(ratios)
    assert ratios[1] < 0.3
    assert 0.3 < ratios[2] < 0.6
    assert ratios[3] > 0.6


def test_level_3_has_higher_rms_and_broadband_content():
    normal = generate_signal(level=0, sample_rate_hz=16_000, duration_sec=2.0, seed=42)
    mild = generate_signal(level=1, sample_rate_hz=16_000, duration_sec=2.0, seed=42)
    medium = generate_signal(level=2, sample_rate_hz=16_000, duration_sec=2.0, seed=42)
    severe = generate_signal(level=3, sample_rate_hz=16_000, duration_sec=2.0, seed=42)

    assert rms(mild) > rms(normal)
    assert rms(medium) > rms(mild)
    assert rms(severe) > rms(medium)
    assert spectral_flatness(severe) > 0.25


def test_generate_signal_level_3_raises_when_leak_band_has_no_energy():
    # sample_rate_hz=100 => Nyquist=50Hz。漏水帯域(500-1500Hz)が完全にナイキスト周波数を
    # 超えるため、帯域フィルタ後の信号にエネルギーが残らずゼロ除算が発生し得る条件。
    with pytest.raises(SignalGenerationError):
        generate_signal(level=3, sample_rate_hz=100, duration_sec=1.0, seed=1)


def test_encode_audio_uses_pcm16_little_endian_raw_bytes():
    signal = np.array([1, -2, 256], dtype=np.int16)

    encoded = encode_audio(signal)

    assert base64.b64decode(encoded) == signal.astype("<i2").tobytes()


def test_build_payload_matches_be_1_schema_contract():
    signal = generate_signal(
        level=2,
        sample_rate_hz=DEFAULT_SAMPLE_RATE_HZ,
        duration_sec=DEFAULT_DURATION_SEC,
        seed=42,
    )
    hydrant = {
        "hydrant_id": "HYD-001",
        "sensor_id": "SNS-001",
        "latitude": 35.6812,
        "longitude": 139.7671,
        "pipe_id": "PIPE-001",
    }

    payload = build_payload(
        hydrant=hydrant,
        signal=signal,
        sample_rate_hz=DEFAULT_SAMPLE_RATE_HZ,
        duration_sec=DEFAULT_DURATION_SEC,
        recorded_at=datetime(2026, 8, 10, 6, 0, tzinfo=timezone.utc),
    )

    TelemetryRequest.model_validate(payload)
    assert payload["hydrant_id"] == "HYD-001"
    assert payload["sensor_id"] == "SNS-001"
    assert payload["location"] == {"latitude": 35.6812, "longitude": 139.7671}


def test_run_simulation_posts_count_times_without_real_network(monkeypatch):
    posted: list[tuple[str, dict]] = []
    slept: list[float] = []

    def fake_post(url: str, payload: dict, timeout_sec: float) -> dict:
        posted.append((url, payload))
        TelemetryRequest.model_validate(payload)
        return {"status": "accepted"}

    monkeypatch.setattr("scripts.simulate_sensor.time.sleep", slept.append)

    results = run_simulation(
        level=2,
        count=3,
        interval_sec=0.25,
        hydrant_id="HYD-001",
        url="http://example.test/api/v1/telemetry",
        seed=42,
        post_func=fake_post,
    )

    assert len(results) == 3
    assert [url for url, _ in posted] == ["http://example.test/api/v1/telemetry"] * 3
    assert slept == [0.25, 0.25]
    assert len({payload["audio_base64"] for _, payload in posted}) == 3


def test_run_simulation_reproduces_the_same_distinct_signal_sequence():
    sequences: list[list[str]] = []

    for _ in range(2):
        audio_payloads: list[str] = []

        def fake_post(url: str, payload: dict, timeout_sec: float) -> dict:
            audio_payloads.append(payload["audio_base64"])
            return {"status": "accepted"}

        run_simulation(
            level=2,
            count=3,
            interval_sec=0,
            hydrant_id="HYD-001",
            url="http://example.test/api/v1/telemetry",
            seed=42,
            post_func=fake_post,
        )
        sequences.append(audio_payloads)

    assert len(set(sequences[0])) == 3
    assert sequences[0] == sequences[1]


def test_replay_pcm16_mono_wav_builds_payload_from_audio_file(tmp_path):
    sample_rate_hz = 8_000
    samples = np.array([0, 1, -2, 1_024, -32_768, 32_767], dtype="<i2")
    pcm_bytes = samples.tobytes()
    audio_file = tmp_path / "replay.wav"
    write_test_wav(audio_file, pcm_bytes, sample_rate_hz=sample_rate_hz)
    posted_payloads: list[dict] = []

    def fake_post(url: str, payload: dict, timeout_sec: float) -> dict:
        posted_payloads.append(payload)
        TelemetryRequest.model_validate(payload)
        return {"status": "accepted"}

    results = run_replay(audio_file, fake_post)

    assert results == [{"status": "accepted"}]
    assert len(posted_payloads) == 1
    payload = posted_payloads[0]
    assert payload["sample_rate_hz"] == sample_rate_hz
    assert payload["duration_sec"] == pytest.approx(len(samples) / sample_rate_hz)
    assert base64.b64decode(payload["audio_base64"]) == pcm_bytes


def test_parse_args_accepts_audio_file_without_level(tmp_path):
    audio_file = tmp_path / "replay.wav"

    args = parse_args(["--audio-file", str(audio_file)])

    assert args.level is None
    assert Path(args.audio_file) == audio_file


def test_parse_args_rejects_level_and_audio_file_together(tmp_path, capsys):
    audio_file = tmp_path / "replay.wav"

    with pytest.raises(SystemExit):
        parse_args(["--level", "1", "--audio-file", str(audio_file)])

    assert "not allowed with argument" in capsys.readouterr().err


def test_replay_rejects_missing_file_before_posting(tmp_path):
    assert_replay_rejected_before_posting(tmp_path / "missing.wav")


def test_replay_rejects_corrupt_wav_before_posting(tmp_path):
    audio_file = tmp_path / "corrupt.wav"
    audio_file.write_bytes(b"not a wav file")

    assert_replay_rejected_before_posting(audio_file)


def test_replay_rejects_stereo_wav_before_posting(tmp_path):
    audio_file = tmp_path / "stereo.wav"
    stereo_samples = np.array([[1, -1], [2, -2]], dtype="<i2")
    write_test_wav(audio_file, stereo_samples.tobytes(), channels=2)

    assert_replay_rejected_before_posting(audio_file)


def test_replay_rejects_non_pcm16_wav_before_posting(tmp_path):
    audio_file = tmp_path / "pcm8.wav"
    write_test_wav(audio_file, b"\x00\x7f\xff", sample_width=1)

    assert_replay_rejected_before_posting(audio_file)


def test_replay_rejects_compressed_wav_before_posting(tmp_path):
    audio_file = tmp_path / "compressed.wav"
    write_compressed_wav(audio_file)

    assert_replay_rejected_before_posting(audio_file)


def test_replay_count_reuses_existing_send_flow(tmp_path, monkeypatch):
    samples = np.array([1, -2, 3, -4], dtype="<i2")
    pcm_bytes = samples.tobytes()
    audio_file = tmp_path / "replay.wav"
    write_test_wav(audio_file, pcm_bytes)
    posted_audio: list[bytes] = []
    slept: list[float] = []

    def fake_post(url: str, payload: dict, timeout_sec: float) -> dict:
        posted_audio.append(base64.b64decode(payload["audio_base64"]))
        return {"status": "accepted"}

    monkeypatch.setattr("scripts.simulate_sensor.time.sleep", slept.append)

    results = run_replay(
        audio_file,
        fake_post,
        count=3,
        interval_sec=0.25,
    )

    assert len(results) == 3
    assert posted_audio == [pcm_bytes, pcm_bytes, pcm_bytes]
    assert slept == [0.25, 0.25]


def test_run_simulation_rejects_unknown_hydrant_without_posting():
    calls = 0

    def fake_post(url: str, payload: dict, timeout_sec: float) -> dict:
        nonlocal calls
        calls += 1
        return {"status": "accepted"}

    with pytest.raises(HydrantNotFoundError):
        run_simulation(
            level=2,
            count=1,
            interval_sec=0,
            hydrant_id="HYD-NOT-FOUND",
            url="http://example.test/api/v1/telemetry",
            seed=42,
            post_func=fake_post,
        )

    assert calls == 0


@pytest.mark.parametrize(
    ("count", "interval_sec"),
    [(0, 0), (-1, 0), (1, -0.1)],
)
def test_run_simulation_rejects_invalid_count_and_interval(count: int, interval_sec: float):
    with pytest.raises(ValueError):
        run_simulation(
            level=2,
            count=count,
            interval_sec=interval_sec,
            hydrant_id="HYD-001",
            url="http://example.test/api/v1/telemetry",
            seed=42,
        )


def test_load_hydrants_reports_missing_file(tmp_path):
    with pytest.raises(HydrantDataError):
        load_hydrants(tmp_path / "missing.json")


def test_load_hydrants_reports_broken_json(tmp_path):
    broken = tmp_path / "hydrants.json"
    broken.write_text("{broken", encoding="utf-8")

    with pytest.raises(HydrantDataError):
        load_hydrants(broken)


def test_load_hydrants_reports_missing_required_key(tmp_path):
    broken = tmp_path / "hydrants.json"
    broken.write_text(
        json.dumps(
            [
                {
                    "hydrant_id": "HYD-001",
                    # sensor_id が欠落
                    "latitude": 35.6812,
                    "longitude": 139.7671,
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(HydrantDataError):
        load_hydrants(broken)


def test_load_hydrants_reports_non_object_entry(tmp_path):
    broken = tmp_path / "hydrants.json"
    broken.write_text(json.dumps(["HYD-001"]), encoding="utf-8")

    with pytest.raises(HydrantDataError):
        load_hydrants(broken)


def test_send_telemetry_raises_clear_error_on_api_failure(monkeypatch):
    class FailingResponse:
        def raise_for_status(self) -> None:
            raise requests.RequestException("boom")

    monkeypatch.setattr(
        "scripts.simulate_sensor.requests.post",
        lambda url, json, timeout: FailingResponse(),
    )

    with pytest.raises(TelemetrySendError):
        send_telemetry("http://example.test/api/v1/telemetry", {}, 0.1)


def test_send_telemetry_rejects_invalid_json_response(monkeypatch):
    class InvalidJsonResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            raise ValueError("invalid JSON")

    monkeypatch.setattr(
        "scripts.simulate_sensor.requests.post",
        lambda url, json, timeout: InvalidJsonResponse(),
    )

    with pytest.raises(TelemetrySendError):
        send_telemetry("http://example.test/api/v1/telemetry", {}, 0.1)
