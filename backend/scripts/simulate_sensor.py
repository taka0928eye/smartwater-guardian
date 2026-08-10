"""BE-2: 疑似センサーデータ生成・送信スクリプト。

レベル 0～3 の音響シグナルを生成し、POST /api/v1/telemetry へ複数回送信する。
デモシナリオで「異常検知」を実演するため、再現可能性（seed 固定）を提供。

前提: 別ターミナルでサーバーが起動していること。

    backend/venv/Scripts/uvicorn.exe main:app --reload --port 8000

実行例:

    # Level 1（微小漏水）を3回、5秒間隔で送信
    backend/venv/Scripts/python.exe scripts/simulate_sensor.py --level 1 --count 3 --interval 5

    # Level 0（正常）10回、同一ハイドラント、固定 seed で再現可能に
    backend/venv/Scripts/python.exe scripts/simulate_sensor.py --level 0 --count 10 --hydrant HYD-001 --seed 42

コマンドラインオプション:
    --level {0,1,2,3}  : 深刻度。0=正常 / 1=微小漏水 / 2=進行性漏水 / 3=大漏水（デフォルト: 1）
    --count N          : 送信回数（デフォルト: 1）
    --interval SEC     : 送信間隔（秒）（デフォルト: 0）
    --hydrant ID       : 固定送信先の消火栓 ID。未指定なら hydrants.json から巡回（デフォルト: 未指定）
    --url URL          : テレメトリエンドポイント（デフォルト: http://localhost:8000/api/v1/telemetry）
    --seed N           : 乱数 seed（デフォルト: 固定値で再現可能に）
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import sys
import time
import wave
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import requests

# 疑似センサーのサンプリング設定
SAMPLE_RATE_HZ = 16_000
DURATION_SEC = 2.0  # 2秒の音響データを毎回送信

# 消火栓マスタのパス（hydrant を指定しない場合に巡回用）
HYDRANTS_PATH = Path(__file__).resolve().parent.parent / "app" / "data" / "hydrants.json"

# デフォルト seed（再現可能なデモの実現）
DEFAULT_SEED = 12345


def load_hydrants() -> list[dict]:
    """hydrants.json から消火栓マスタを読み込む。"""
    try:
        with open(HYDRANTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"エラー: {HYDRANTS_PATH} が見つかりません", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"エラー: {HYDRANTS_PATH} の JSON が不正です: {e}", file=sys.stderr)
        sys.exit(1)


def generate_signal(
    level: int,
    sample_rate_hz: int,
    duration_sec: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    深刻度レベル別に音響シグナルを生成する。

    Args:
        level: 深刻度 (0=正常, 1=微小漏水, 2=進行性漏水, 3=大漏水)
        sample_rate_hz: サンプリング周波数
        duration_sec: 信号長（秒）
        rng: NumPy 乱数生成器（seed 制御用）

    Returns:
        float64 正規化音響データ (-1.0 ~ 1.0)
    """
    n_samples = int(sample_rate_hz * duration_sec)
    t = np.linspace(0, duration_sec, n_samples, dtype=np.float64)

    if level == 0:
        # Level 0: 正常。環境ノイズのみ。
        signal = rng.normal(0, 0.02, n_samples).astype(np.float64)

    elif level == 1:
        # Level 1: 微小漏水。800〜1200Hz の狭帯域トーン。
        freq_hz = rng.uniform(800, 1200)
        signal = 0.15 * np.sin(2 * np.pi * freq_hz * t)
        # ノイズを微量混入
        signal += rng.normal(0, 0.01, n_samples)

    elif level == 2:
        # Level 2: 進行性漏水。500〜1500Hz に複数トーン + 増幅。
        signal = np.zeros(n_samples, dtype=np.float64)
        for _ in range(3):
            freq_hz = rng.uniform(500, 1500)
            amplitude = rng.uniform(0.1, 0.2)
            signal += amplitude * np.sin(2 * np.pi * freq_hz * t)
        signal += rng.normal(0, 0.02, n_samples)

    elif level == 3:
        # Level 3: 大漏水。広帯域・大振幅。
        signal = np.zeros(n_samples, dtype=np.float64)
        for _ in range(5):
            freq_hz = rng.uniform(200, 3000)
            amplitude = rng.uniform(0.15, 0.3)
            signal += amplitude * np.sin(2 * np.pi * freq_hz * t)
        signal += rng.normal(0, 0.05, n_samples)

    else:
        raise ValueError(f"不正な深刻度: {level}。0-3 を指定してください")

    # クリッピング
    signal = np.clip(signal, -1.0, 1.0)
    return signal


def encode_pcm16(samples: np.ndarray) -> str:
    """
    float64 信号を PCM16 WAV エンコード → Base64 文字列に変換する。
    """
    # float64 → int16
    pcm16 = (samples * np.iinfo(np.int16).max).astype(np.int16)

    # WAV フォーマットで出力（モノラル）
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE_HZ)
        wav_file.writeframes(pcm16.tobytes())

    # Base64 エンコード
    wav_buffer.seek(0)
    return base64.b64encode(wav_buffer.read()).decode("ascii")


def send_telemetry(
    level: int,
    count: int,
    interval_sec: float,
    hydrant: dict | None,
    endpoint_url: str,
    seed: int | None,
) -> None:
    """テレメトリを count 回送信する。"""
    # seed の初期化（未指定なら DEFAULT_SEED）
    actual_seed = seed if seed is not None else DEFAULT_SEED
    rng = np.random.default_rng(actual_seed)

    hydrants_list = load_hydrants()

    for i in range(count):
        # 送信先ハイドラントを決定
        if hydrant:
            target = hydrant
        else:
            target = hydrants_list[i % len(hydrants_list)]

        # シグナル生成
        signal = generate_signal(level, SAMPLE_RATE_HZ, DURATION_SEC, rng)
        audio_base64 = encode_pcm16(signal)

        # テレメトリペイロード
        now = datetime.now(timezone.utc)
        payload = {
            "sensor_id": target["sensor_id"],
            "hydrant_id": target["hydrant_id"],
            "recorded_at": (now - timedelta(seconds=1)).isoformat(),
            "location": {
                "latitude": target["latitude"],
                "longitude": target["longitude"],
            },
            "sample_rate_hz": SAMPLE_RATE_HZ,
            "duration_sec": DURATION_SEC,
            "audio_base64": audio_base64,
            "battery_pct": 85,
        }

        # POST 送信
        try:
            response = requests.post(endpoint_url, json=payload, timeout=10)
            status = "✓" if response.status_code == 200 else "✗"
            print(
                f"{status} [{i+1}/{count}] {target['hydrant_id']} "
                f"(Level {level}) → {response.status_code}"
            )
            if response.status_code != 200:
                print(f"  応答: {response.text[:200]}")
        except requests.RequestException as e:
            print(
                f"✗ [{i+1}/{count}] {target['hydrant_id']} "
                f"(Level {level}) → 通信エラー: {e}",
                file=sys.stderr,
            )

        # 次回送信の遅延
        if i < count - 1 and interval_sec > 0:
            time.sleep(interval_sec)


def main():
    parser = argparse.ArgumentParser(
        description="疑似センサーからテレメトリを送信する"
    )
    parser.add_argument(
        "--level",
        type=int,
        default=1,
        choices=[0, 1, 2, 3],
        help="深刻度レベル (デフォルト: 1)",
    )
    parser.add_argument(
        "--count", type=int, default=1, help="送信回数 (デフォルト: 1)"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0,
        help="送信間隔（秒） (デフォルト: 0)",
    )
    parser.add_argument(
        "--hydrant",
        type=str,
        default=None,
        help="固定送信先の消火栓 ID (未指定なら巡回)",
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:8000/api/v1/telemetry",
        help="テレメトリエンドポイント",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="乱数 seed (未指定なら {})".format(DEFAULT_SEED),
    )

    args = parser.parse_args()

    # ハイドラントが指定されている場合は検証
    target_hydrant = None
    if args.hydrant:
        hydrants_list = load_hydrants()
        matches = [h for h in hydrants_list if h["hydrant_id"] == args.hydrant]
        if not matches:
            print(
                f"エラー: ハイドラント '{args.hydrant}' が見つかりません",
                file=sys.stderr,
            )
            sys.exit(1)
        target_hydrant = matches[0]

    print(f"送信開始: Level {args.level} × {args.count} 回")
    send_telemetry(
        level=args.level,
        count=args.count,
        interval_sec=args.interval,
        hydrant=target_hydrant,
        endpoint_url=args.url,
        seed=args.seed,
    )
    print("送信完了")


if __name__ == "__main__":
    main()
