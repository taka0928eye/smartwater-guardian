"""DEMO-2: デモ初期状態を一括投入するサービス。

23消火栓それぞれにちょうど1レベルを重複なく割り当て（Lv0×11 / Lv1×8 / Lv2×3 /
Lv3×1）、``backend/dataset/`` の実音響WAV（BE-2 由来）を replay して
``analyze_audio()`` で実スペクトルを算出しつつ、深刻度は意図値に確定する
（``app/routers/demo.py::seed_demo`` と同じハイブリッド方針）。

``POST /api/v1/demo/seed-batch``（``app/routers/demo.py``）と
``scripts/seed_demo.py``（CLI）の両方から呼ばれる、内訳計算・音声選択ロジックの
単一の実体。``app/`` は ``scripts/`` に依存できないため、WAV読込み等の
ヘルパーは（``scripts/simulate_sensor.py`` と重複するが）ここに独立実装する。
"""

from __future__ import annotations

import base64
import random
import re
import wave
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np

from app.schemas.alert import HydrantMaster
from app.schemas.telemetry import GeoLocation
from app.services.audio import DURATION_SEC, SAMPLE_COUNT, SAMPLE_RATE_HZ, analyze_audio
from app.store import InMemoryStore, StoredTelemetry, clear_disaster_state, get_hydrants

# デモ既定内訳（23台へ1対1で割り当てる）。
DEMO_COMPOSITION: dict[int, int] = {0: 11, 1: 8, 2: 3, 3: 1}

# 実音響WAVの既定ディレクトリ（backend/dataset）。Git 管理外（.gitignore）。
DEFAULT_AUDIO_DIR = Path(__file__).resolve().parents[2] / "dataset"

# 利用者が手動配置するファイル名。レベルとの対応をここで一元管理する。
REQUIRED_AUDIO_FILENAMES: dict[int, str] = {
    0: "BE3_demo_no-leak_level0.wav",
    1: "BE3_demo_leak_level1.wav",
    2: "BE3_demo_leak_level2.wav",
    3: "BE3_demo_leak_level3.wav",
}


class DemoSeedError(Exception):
    """デモ一括シード投入で扱う明示的な失敗（マスタ・音源起因）。"""

    def __init__(self, message: str, *, status_code: int = 422) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class SeedStep:
    """一括投入1件分。``level`` は意図した深刻度、``hydrant_id`` は投入先。"""

    level: int
    hydrant_id: str


@dataclass(frozen=True)
class SeedBatchResult:
    """一括投入の結果サマリ。"""

    inserted_count: int
    level_counts: dict[str, int]


def build_seed_batch(
    hydrants: list[HydrantMaster], *, seed: int | None = None
) -> list[SeedStep]:
    """23消火栓それぞれにちょうど1レベルを重複なく割り当てる（純粋関数）。

    同一 ``seed`` で同一シーケンスが再現される（デモの再現性）。
    """
    total = sum(DEMO_COMPOSITION.values())
    if len(hydrants) < total:
        raise DemoSeedError(
            f"消火栓マスタが{total}件未満です（実際: {len(hydrants)}件）。"
            f"{total}消火栓すべてに1レベルを割り当てるには{total}件必要です"
        )
    hydrant_ids = [hydrant.hydrant_id for hydrant in hydrants[:total]]
    rng = random.Random(seed)
    rng.shuffle(hydrant_ids)

    levels: list[int] = []
    for level, count in sorted(DEMO_COMPOSITION.items()):
        levels.extend([level] * count)

    return [
        SeedStep(level=level, hydrant_id=hydrant_id)
        for level, hydrant_id in zip(levels, hydrant_ids)
    ]


def _classify_audio_name(path: Path) -> tuple[bool, int | None]:
    """ファイル名から (is_leak, 意図レベル) を決定論的に導出する。

    規約: ``*no-leak*_level{N}.wav`` は正常音、``*leak*_level{N}.wav`` は漏水音。
    """
    name = path.stem.lower()
    if "no-leak" in name:
        is_leak = False
    elif "leak" in name:
        is_leak = True
    else:
        raise DemoSeedError(f"leak / no-leak が判別できないファイル名です: {path.name}")
    match = re.search(r"level(\d+)", name)
    level = int(match.group(1)) if match else None
    return is_leak, level


def resolve_replay_files(audio_dir: Path) -> tuple[list[Path], list[Path]]:
    """必須4ファイルの存在・形式を検証し、no-leak / leak に分けて返す。"""
    missing = [
        filename
        for filename in REQUIRED_AUDIO_FILENAMES.values()
        if not (audio_dir / filename).is_file()
    ]
    if missing:
        location = (
            "backend/dataset/"
            if audio_dir == DEFAULT_AUDIO_DIR
            else "指定したaudio_dir"
        )
        raise DemoSeedError(
            f"WAVが不足しています。{location} に以下を配置してください: "
            f"{', '.join(missing)}",
            status_code=404,
        )

    paths = {
        level: audio_dir / filename
        for level, filename in REQUIRED_AUDIO_FILENAMES.items()
    }
    for path in paths.values():
        _validate_wav_format(path)
    return [paths[0]], [paths[1], paths[2], paths[3]]


def _validate_wav_format(path: Path) -> None:
    """WAVヘッダーが mono / PCM16 / 8000Hz / 1秒かを安全に検証する。"""
    try:
        with wave.open(str(path), "rb") as wav_file:
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            sample_rate_hz = wav_file.getframerate()
            sample_count = wav_file.getnframes()
            compression = wav_file.getcomptype()
    except (OSError, EOFError, wave.Error) as exc:
        raise DemoSeedError(
            f"不正なWAVです: {path.name} (WAVとして読み込めません)"
        ) from exc

    invalid: list[str] = []
    if channels != 1:
        invalid.append(f"mono（実際: {channels}ch）")
    if compression != "NONE" or sample_width != 2:
        invalid.append(
            f"PCM16（実際: {sample_width * 8}bit, compression={compression}）"
        )
    if sample_rate_hz != SAMPLE_RATE_HZ:
        invalid.append(f"8000Hz（実際: {sample_rate_hz}Hz）")
    if sample_count != SAMPLE_COUNT:
        invalid.append(f"1秒・8000サンプル（実際: {sample_count}サンプル）")
    if invalid:
        raise DemoSeedError(f"不正なWAVです: {path.name} ({'; '.join(invalid)})")


def select_replay_file(
    no_leak_files: list[Path],
    leak_files: list[Path],
    level: int,
    rng: random.Random,
) -> Path:
    """ステップの深刻度に合う実音響ファイルを決定論的に選ぶ。

    ``_level{N}`` が一致するものを優先し、無ければ同バケット内から選ぶ
    （件数不足は循環で補える。同一WAVを複数消火栓で再利用してよい）。
    """
    files = no_leak_files if level == 0 else leak_files
    exact = [path for path in files if _classify_audio_name(path)[1] == level]
    pool = exact if exact else files
    return pool[rng.randrange(len(pool))]


def validate_mvp_contract(
    signal: np.ndarray,
    sample_rate_hz: int,
    duration_sec: float,
    path: Path,
) -> None:
    """シードAPIのMVP契約（8000Hz / 1.0秒 / 8000サンプル）に適合するか検証する。"""
    if (
        sample_rate_hz != SAMPLE_RATE_HZ
        or duration_sec != DURATION_SEC
        or len(signal) != SAMPLE_COUNT
    ):
        raise DemoSeedError(
            f"{path.name}: シードAPIは 8000Hz / 1.0秒 / 8000サンプルのWAVのみ"
            f"受付可能です（実際: {sample_rate_hz}Hz / {duration_sec:.3f}秒 / "
            f"{len(signal)}サンプル）。8000Hz・1.0秒に変換して配置してください"
        )


def load_audio_file(path: Path) -> tuple[np.ndarray, int, float]:
    """Replay用の非圧縮PCM16モノラルWAVを読み込む。"""
    try:
        with wave.open(str(path), "rb") as wav_file:
            if wav_file.getcomptype() != "NONE":
                raise DemoSeedError("圧縮WAVには対応していません")
            if wav_file.getnchannels() != 1:
                raise DemoSeedError("音声ファイルはモノラルWAVである必要があります")
            if wav_file.getsampwidth() != 2:
                raise DemoSeedError("音声ファイルは16bit PCMである必要があります")

            sample_rate_hz = wav_file.getframerate()
            sample_count = wav_file.getnframes()
            pcm_bytes = wav_file.readframes(sample_count)
    except FileNotFoundError as exc:
        raise DemoSeedError(
            f"音声ファイルが見つかりません: {path.name}", status_code=404
        ) from exc
    except (OSError, EOFError, wave.Error) as exc:
        raise DemoSeedError(f"音声ファイルを読み込めません: {path.name}") from exc

    if sample_rate_hz <= 0 or sample_count <= 0:
        raise DemoSeedError("音声ファイルのsample rateまたはsample countが不正です")
    if len(pcm_bytes) != sample_count * 2:
        raise DemoSeedError("音声ファイルのPCMデータが破損しています")

    signal = np.frombuffer(pcm_bytes, dtype="<i2").copy()
    duration_sec = sample_count / sample_rate_hz
    return signal, sample_rate_hz, duration_sec


def run_seed_batch(
    store: InMemoryStore, audio_dir: Path, *, seed: int | None = None
) -> SeedBatchResult:
    """デモシーケンスを組み立て、ストアを23件・新内訳で一括再構築する。

    音声は ``audio_dir`` 内の実音響 WAV を replay する。全23件を組み立てた後に
    ``store.clear()`` してから ``add()`` することで、既存レコードとの重複
    （アラート一覧・KPI 集計の二重カウント）を防ぐ。以前の防災シミュレーション
    選出記録（``register_disaster_sensors()``）も新しいベースラインのために
    クリアする（そのまま持ち越すと、Lv3 でなくなったセンサーが「被災エリア」
    として表示され続ける不整合が生じる）。
    """
    hydrants = get_hydrants()
    steps = build_seed_batch(hydrants, seed=seed)
    no_leak_files, leak_files = resolve_replay_files(audio_dir)
    rng = random.Random(seed)
    hydrants_by_id = {hydrant.hydrant_id: hydrant for hydrant in hydrants}
    now = datetime.now(timezone.utc)

    records: list[StoredTelemetry] = []
    level_counts: Counter[int] = Counter()
    for step in steps:
        hydrant = hydrants_by_id[step.hydrant_id]
        audio_path = select_replay_file(no_leak_files, leak_files, step.level, rng)
        signal, sample_rate_hz, duration_sec = load_audio_file(audio_path)
        validate_mvp_contract(signal, sample_rate_hz, duration_sec, audio_path)

        pcm_bytes = signal.astype("<i2", copy=False).tobytes()
        audio_base64 = base64.b64encode(pcm_bytes).decode("ascii")
        analysis = analyze_audio(
            audio_base64, sample_rate_hz=sample_rate_hz, duration_sec=duration_sec
        )
        analysis = analysis.model_copy(update={"severity_level": step.level})

        records.append(
            StoredTelemetry(
                telemetry_id=f"tlm_seed_{uuid4().hex[:12]}",
                sensor_id=hydrant.sensor_id,
                hydrant_id=hydrant.hydrant_id,
                recorded_at=now,
                received_at=now,
                location=GeoLocation(latitude=hydrant.latitude, longitude=hydrant.longitude),
                analysis=analysis,
                audio_pcm16=base64.b64decode(audio_base64, validate=True),
                sample_rate_hz=sample_rate_hz,
            )
        )
        level_counts[step.level] += 1

    store.clear()
    for record in records:
        store.add(record)
    clear_disaster_state()

    return SeedBatchResult(
        inserted_count=len(records),
        level_counts={str(level): count for level, count in sorted(level_counts.items())},
    )
