"""BE-2: 疑似音響センサーデータを生成して telemetry API へ送信するCLI。"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import time
import wave
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import requests

DEFAULT_SAMPLE_RATE_HZ = 16_000
DEFAULT_DURATION_SEC = 2.0
DEFAULT_HYDRANTS_PATH = (
    Path(__file__).resolve().parents[1] / "app" / "data" / "hydrants.json"
)
INT16_MAX = np.iinfo(np.int16).max

Hydrant = dict[str, Any]
Payload = dict[str, Any]
AudioData = tuple[np.ndarray, int, float]
PostFunc = Callable[[str, Payload, float], dict[str, Any]]


class SimulationError(Exception):
    """疑似センサーCLIで扱う明示的な失敗。"""


class HydrantDataError(SimulationError):
    """消火栓マスタを読み込めない、または形式が不正。"""


class HydrantNotFoundError(SimulationError):
    """指定された消火栓IDがマスタに存在しない。"""


class SignalGenerationError(SimulationError):
    """指定パラメータでは疑似音響信号を生成できない。"""


class TelemetrySendError(SimulationError):
    """Telemetry APIへの送信失敗。"""


REQUIRED_HYDRANT_KEYS = ("hydrant_id", "sensor_id", "latitude", "longitude")
# irfft後の信号がほぼ無音（帯域内にエネルギーが存在しない）とみなす閾値。
_MIN_FILTERED_STD = 1e-9


class AudioFileError(SimulationError):
    """Replay用音声ファイルが存在しない、または形式が不正。"""


def _time_axis(sample_rate_hz: int, duration_sec: float) -> np.ndarray:
    sample_count = int(sample_rate_hz * duration_sec)
    return np.arange(sample_count, dtype=np.float64) / sample_rate_hz


def _tone(t: np.ndarray, freq_hz: float, amplitude: float) -> np.ndarray:
    return amplitude * np.sin(2.0 * np.pi * freq_hz * t)


def _band_limited_noise(
    rng: np.random.Generator,
    sample_count: int,
    sample_rate_hz: float,
    low_hz: float,
    high_hz: float,
    amplitude: float,
) -> np.ndarray:
    noise = rng.normal(0.0, 1.0, size=sample_count)
    spectrum = np.fft.rfft(noise)
    freqs = np.fft.rfftfreq(sample_count, d=1.0 / sample_rate_hz)
    spectrum[(freqs < low_hz) | (freqs > high_hz)] = 0.0
    filtered = np.fft.irfft(spectrum, n=sample_count)
    std = np.std(filtered)
    if std < _MIN_FILTERED_STD:
        raise SignalGenerationError(
            f"帯域 {low_hz}-{high_hz}Hz にエネルギーが存在しません "
            f"(sample_rate_hz={sample_rate_hz}, duration_sec={sample_count / sample_rate_hz})。"
            "sample_rate_hz または duration_sec を見直してください。"
        )
    return filtered * (amplitude / std)


def _validate_signal_options(level: int, sample_rate_hz: int, duration_sec: float) -> None:
    if level not in (0, 1, 2, 3):
        raise ValueError("level must be one of 0, 1, 2, 3")
    if sample_rate_hz <= 0:
        raise ValueError("sample_rate_hz must be positive")
    if duration_sec <= 0:
        raise ValueError("duration_sec must be positive")


def _compose_waveform(
    level: int,
    t: np.ndarray,
    rng: np.random.Generator,
    sample_rate_hz: int,
) -> np.ndarray:
    if level == 0:
        return rng.normal(0.0, 0.035, size=t.size)
    if level == 1:
        return rng.normal(0.0, 0.05, size=t.size) + _tone(t, 980.0, 0.025)
    if level == 2:
        waveform = rng.normal(0.0, 0.06, size=t.size)
        tones = _tone(t, 650.0, 0.04) + _tone(t, 950.0, 0.05)
        return waveform + tones + _tone(t, 1_320.0, 0.04)

    broadband = rng.normal(0.0, 0.06, size=t.size)
    leak_band = _band_limited_noise(
        rng, t.size, sample_rate_hz, 500.0, 1_500.0, amplitude=0.18
    )
    return broadband + leak_band


def generate_signal(
    level: int,
    sample_rate_hz: int = DEFAULT_SAMPLE_RATE_HZ,
    duration_sec: float = DEFAULT_DURATION_SEC,
    seed: int | None = None,
) -> np.ndarray:
    """漏水レベルごとの疑似PCM16モノラル信号を生成する。"""
    _validate_signal_options(level, sample_rate_hz, duration_sec)
    rng = np.random.default_rng(seed)
    t = _time_axis(sample_rate_hz, duration_sec)
    waveform = _compose_waveform(level, t, rng, sample_rate_hz)
    return np.clip(waveform * INT16_MAX, -32768, 32767).astype(np.int16)


def encode_audio(signal: np.ndarray) -> str:
    """PCM16 little-endian raw bytesをBase64文字列へ変換する。"""
    pcm_bytes = signal.astype("<i2", copy=False).tobytes()
    return base64.b64encode(pcm_bytes).decode("ascii")


def load_audio_file(path: Path) -> AudioData:
    """Replay用の非圧縮PCM16モノラルWAVを読み込む。"""
    try:
        with wave.open(str(path), "rb") as wav_file:
            if wav_file.getcomptype() != "NONE":
                raise AudioFileError("圧縮WAVには対応していません")
            if wav_file.getnchannels() != 1:
                raise AudioFileError("音声ファイルはモノラルWAVである必要があります")
            if wav_file.getsampwidth() != 2:
                raise AudioFileError("音声ファイルは16bit PCMである必要があります")

            sample_rate_hz = wav_file.getframerate()
            sample_count = wav_file.getnframes()
            pcm_bytes = wav_file.readframes(sample_count)
    except FileNotFoundError as exc:
        raise AudioFileError(f"音声ファイルが見つかりません: {path}") from exc
    except (OSError, EOFError, wave.Error) as exc:
        raise AudioFileError(f"音声ファイルを読み込めません: {path}") from exc

    if sample_rate_hz <= 0 or sample_count <= 0:
        raise AudioFileError("音声ファイルのsample rateまたはsample countが不正です")
    if len(pcm_bytes) != sample_count * 2:
        raise AudioFileError("音声ファイルのPCMデータが破損しています")

    signal = np.frombuffer(pcm_bytes, dtype="<i2").copy()
    duration_sec = sample_count / sample_rate_hz
    return signal, sample_rate_hz, duration_sec


def load_hydrants(path: Path = DEFAULT_HYDRANTS_PATH) -> list[Hydrant]:
    """デモ用消火栓マスタを読み込む。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise HydrantDataError(f"hydrants.json が見つかりません: {path}") from exc
    except json.JSONDecodeError as exc:
        raise HydrantDataError(f"hydrants.json が壊れています: {path}") from exc

    if not isinstance(data, list):
        raise HydrantDataError("hydrants.json は配列である必要があります")

    for index, entry in enumerate(data):
        if not isinstance(entry, dict):
            raise HydrantDataError(
                f"hydrants.json の要素[{index}]はオブジェクトである必要があります"
            )
        missing_keys = [key for key in REQUIRED_HYDRANT_KEYS if key not in entry]
        if missing_keys:
            raise HydrantDataError(
                f"hydrants.json の要素[{index}]に必須キーがありません: {missing_keys}"
            )
    return data


def find_hydrant(hydrants: list[Hydrant], hydrant_id: str) -> Hydrant:
    """消火栓IDから1件を選ぶ。"""
    for hydrant in hydrants:
        if hydrant.get("hydrant_id") == hydrant_id:
            return hydrant
    raise HydrantNotFoundError(f"指定された hydrant が見つかりません: {hydrant_id}")


def build_payload(
    hydrant: Hydrant,
    signal: np.ndarray,
    sample_rate_hz: int = DEFAULT_SAMPLE_RATE_HZ,
    duration_sec: float = DEFAULT_DURATION_SEC,
    recorded_at: datetime | None = None,
    battery_pct: int | None = 87,
) -> Payload:
    """BE-1のTelemetryRequestに一致するpayloadを組み立てる。"""
    timestamp = recorded_at or datetime.now(UTC)
    payload: Payload = {
        "sensor_id": hydrant["sensor_id"],
        "hydrant_id": hydrant["hydrant_id"],
        "recorded_at": timestamp.isoformat(),
        "location": {
            "latitude": hydrant["latitude"],
            "longitude": hydrant["longitude"],
        },
        "sample_rate_hz": sample_rate_hz,
        "duration_sec": duration_sec,
        "audio_base64": encode_audio(signal),
        "battery_pct": battery_pct,
    }
    return payload


def send_telemetry(url: str, payload: Payload, timeout_sec: float = 10.0) -> dict[str, Any]:
    """Telemetry APIへ1件送信する。テストでは差し替え可能。"""
    try:
        response = requests.post(url, json=payload, timeout=timeout_sec)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise TelemetrySendError(f"Telemetry API への送信に失敗しました: {exc}") from exc
    except ValueError as exc:
        raise TelemetrySendError("Telemetry API のレスポンスJSONを解読できません") from exc


def _validate_run_options(count: int, interval_sec: float) -> None:
    if count <= 0:
        raise ValueError("count must be greater than 0")
    if interval_sec < 0:
        raise ValueError("interval must be 0 or greater")


def run_simulation(
    level: int | None,
    count: int,
    interval_sec: float,
    hydrant_id: str,
    url: str,
    seed: int | None = None,
    hydrants_path: Path = DEFAULT_HYDRANTS_PATH,
    post_func: PostFunc = send_telemetry,
    sample_rate_hz: int = DEFAULT_SAMPLE_RATE_HZ,
    duration_sec: float = DEFAULT_DURATION_SEC,
    audio_file: Path | None = None,
) -> list[dict[str, Any]]:
    """人工信号またはReplay音声を指定回数送信する。"""
    _validate_run_options(count, interval_sec)
    if level is not None and audio_file is not None:
        raise ValueError("level and audio_file cannot be specified together")

    replay_audio: AudioData | None = None
    if audio_file is not None:
        replay_audio = load_audio_file(audio_file)
    else:
        if level is None:
            raise ValueError("level or audio_file must be specified")
        _validate_signal_options(level, sample_rate_hz, duration_sec)

    hydrant = find_hydrant(load_hydrants(hydrants_path), hydrant_id)

    results: list[dict[str, Any]] = []
    for index in range(count):
        audio = replay_audio
        if audio is None:
            assert level is not None
            signal_seed = None if seed is None else seed + index
            audio = (
                generate_signal(level, sample_rate_hz, duration_sec, seed=signal_seed),
                sample_rate_hz,
                duration_sec,
            )
        signal, payload_sample_rate_hz, payload_duration_sec = audio
        payload = build_payload(
            hydrant,
            signal,
            payload_sample_rate_hz,
            payload_duration_sec,
        )
        results.append(post_func(url, payload, 10.0))
        if index < count - 1:
            time.sleep(interval_sec)
    return results


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="疑似センサーデータをtelemetry APIへ送信します。")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--level", type=int, choices=[0, 1, 2, 3], default=None)
    source.add_argument("--audio-file", type=Path, default=None)
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--hydrant", default="HYD-001")
    parser.add_argument("--url", default="http://localhost:8000/api/v1/telemetry")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args(argv)
    if args.level is None and args.audio_file is None:
        args.level = 0
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        results = run_simulation(
            level=args.level,
            count=args.count,
            interval_sec=args.interval,
            hydrant_id=args.hydrant,
            url=args.url,
            seed=args.seed,
            audio_file=args.audio_file,
        )
    except SimulationError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    print(f"[OK] {len(results)} telemetry payload(s) sent to {args.url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
