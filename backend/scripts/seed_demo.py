"""DEMO-1: デモ初期状態を1コマンドで構築するシードスクリプト。

Issue #23（DEMO-1）の実装。デモの山場である Level 1（微小漏水）と
Level 0（正常）との対比を、決定的なシーケンスで1コマンド投入する。

実装方針:
- 音源は BE-2 の ``load_audio_file()``（replay）で読み込む**実音響WAV**。
  ``generate_signal()`` の人工音は実 SVM が意図レベルに分類できないため
  （DEMO-1 調査で確認）、学習未使用の Zenodo 実音響（``backend/dataset``）を
  用いる。実 no-leak 音は SVM が自然に severity 0 を返す「正しい正常」になる。
- 投入内訳は ``docs/business-model.md`` §3.4 のデモ既定値
  （Level 1×8 / Level 2×3 / Level 3×1）。
- Level 0（正常）は既存ベースライン1件に正常専用センサー10件を追加する。
- 同一 ``--seed`` で同一シーケンスを再現する（デモの再現性）。
- 深刻度は ``POST /api/v1/demo/seed``（デモシード専用エンドポイント）で意図レベルに
  確定する。実スペクトルは ``analyze_audio()`` で算出され、実 leak 音は SVM でも
  leak と判定される（ハイブリッド: 実信号 + 深刻度確定）。
"""

from __future__ import annotations

import argparse
import random
import re
import sys
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np

# スクリプト直接実行時も backend/ を sys.path に載せ、scripts.simulate_sensor を
# import できるようにする（train_leak_svm.py と同じブートストラップ）。
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.audio import DURATION_SEC, SAMPLE_COUNT, SAMPLE_RATE_HZ  # noqa: E402
from scripts.simulate_sensor import (  # noqa: E402
    DEFAULT_HYDRANTS_PATH,
    Hydrant,
    SimulationError,
    build_payload,
    find_hydrant,
    load_audio_file,
    load_hydrants,
    send_telemetry,
)

# BE-3 MVP 契約（analyze_audio が受付可能な形式）。replay する WAV もこの契約に一致させる。

# 実音響WAVの既定ディレクトリ（backend/dataset）。Git 管理外（.gitignore）の
# デモ用カットを配置する。ファイル名規約: ``*_level{N}.wav`` + ``leak`` / ``no-leak``。
DEFAULT_AUDIO_DIR = Path(__file__).resolve().parents[1] / "dataset"

# デモ既定値（docs/business-model.md §3.4）
DEMO_COMPOSITION: dict[int, int] = {1: 8, 2: 3, 3: 1}
# Level 0（正常）ベースラインの件数（PRD §6.1 の対比用）
BASELINE_LEVEL = 0
BASELINE_COUNT = 1
ADDITIONAL_LEVEL0_COUNT = 10
# 既存の異常デモで使う消火栓（HYD-001〜010）の件数。
ALERT_HYDRANT_COUNT = 10
# タイムライン表現用の相対秒（録音時刻にデモの進行を反映する）
BASELINE_INTERVAL_SEC = 8
STEP_INTERVAL_SEC = 4

# デモシード投入先エンドポイント
SEED_ENDPOINT = "http://localhost:8000/api/v1/demo/seed"

# 送信関数の型（simulate_sensor.send_telemetry と互換）
PostFunc = Callable[[str, dict[str, Any], float], dict[str, Any]]


@dataclass(frozen=True)
class DemoStep:
    """デモ送信1回分のステップ。

    ``level`` は意図した深刻度（0〜3）、``hydrant_id`` は送信先消火栓、
    ``offset_sec`` はベース時刻からの相対秒（タイムライン表現用）。
    frozen=True で順序・内訳の不変条件を守る。
    """

    level: int
    hydrant_id: str
    offset_sec: int


def _classify_audio_name(path: Path) -> tuple[bool, int | None]:
    """ファイル名から (is_leak, 意図レベル) を決定論的に導出する。

    規約: ``*no-leak*_level{N}.wav`` は正常音、``*leak*_level{N}.wav`` は漏水音。
    leak / no-leak を判別できない名前は投入ミスを防ぐためエラーにする。
    """
    name = path.stem.lower()
    if "no-leak" in name:
        is_leak = False
    elif "leak" in name:
        is_leak = True
    else:
        raise SimulationError(
            f"leak / no-leak が判別できないファイル名です: {path.name}"
        )
    match = re.search(r"level(\d+)", name)
    level = int(match.group(1)) if match else None
    return is_leak, level


def resolve_replay_files(audio_dir: Path) -> tuple[list[Path], list[Path]]:
    """音声ディレクトリから no-leak と leak の WAV 一覧を返す。

    ``backend/dataset`` のデモ用カット（``BE3_demo_no-leak_level0.wav`` /
    ``BE3_demo_leak_level2.wav``）が先例。決定論のためにソートする。
    """
    if not audio_dir.is_dir():
        raise SimulationError(f"音声ディレクトリが見つかりません: {audio_dir}")
    wavs = sorted(path for path in audio_dir.glob("*.wav") if path.is_file())
    no_leak: list[Path] = []
    leak: list[Path] = []
    for path in wavs:
        is_leak, _ = _classify_audio_name(path)
        (leak if is_leak else no_leak).append(path)
    if not no_leak:
        raise SimulationError(
            f"no-leak（正常音）のWAVが見つかりません: {audio_dir}"
        )
    if not leak:
        raise SimulationError(
            f"leak（漏水音）のWAVが見つかりません: {audio_dir}"
        )
    return no_leak, leak


def select_replay_file(
    no_leak_files: list[Path],
    leak_files: list[Path],
    level: int,
    rng: random.Random,
) -> Path:
    """ステップの深刻度に合う実音響ファイルを決定論的に選ぶ。

    Level 0 は no-leak 音（SVM が自然に severity 0 を返す正常音）を使い、
    Level 1〜3 は leak 音を使う。ファイル名の ``_level{N}`` が一致するものを
    優先し、無ければ同バケット内から seed で選ぶ（件数不足は循環で補える）。
    """
    files = no_leak_files if level == 0 else leak_files
    exact = [
        path for path in files if _classify_audio_name(path)[1] == level
    ]
    pool = exact if exact else files
    return pool[rng.randrange(len(pool))]


def validate_mvp_contract(
    signal: np.ndarray,
    sample_rate_hz: int,
    duration_sec: float,
    path: Path,
) -> None:
    """シードAPI（BE-3 MVP 契約）に適合する WAV かを投入前に検証する。"""
    if (
        sample_rate_hz != SAMPLE_RATE_HZ
        or duration_sec != DURATION_SEC
        or len(signal) != SAMPLE_COUNT
    ):
        raise SimulationError(
            f"{path.name}: シードAPIは 8000Hz / 1.0秒 / 8000サンプルのWAVのみ"
            f"受付可能です（実際: {sample_rate_hz}Hz / {duration_sec:.3f}秒 / "
            f"{len(signal)}サンプル）。8000Hz・1.0秒に変換して配置してください"
        )


def build_demo_sequence(
    seed: int,
    hydrants: list[Hydrant] | None = None,
) -> list[DemoStep]:
    """デモ初期状態の投入シーケンスを決定的に組み立てる（純粋関数）。

    - 先頭に Level 0（正常）ベースライン1件と追加10件を置き、続いて
      Level 1×8 / Level 2×3 / Level 3×1（§3.4 のデモ既定値）。
    - 同一 ``seed`` で同一シーケンス（再現性）。Level 1 は Level 3 より必ず先に出現。
    - 消火栓はマスタから seed でシャッフルして割り当て、件数超過時は循環させる。
    """
    if hydrants is None:
        hydrants = load_hydrants()
    required_count = ALERT_HYDRANT_COUNT + ADDITIONAL_LEVEL0_COUNT
    if len(hydrants) < required_count:
        raise SimulationError(
            "消火栓マスタが少なすぎます。"
            f"正常専用10件を含むデモ投入には{required_count}件以上必要です"
        )
    alert_hydrant_ids = [
        hydrant["hydrant_id"] for hydrant in hydrants[:ALERT_HYDRANT_COUNT]
    ]
    additional_level0_ids = [
        hydrant["hydrant_id"]
        for hydrant in hydrants[
            ALERT_HYDRANT_COUNT : ALERT_HYDRANT_COUNT + ADDITIONAL_LEVEL0_COUNT
        ]
    ]
    rng = random.Random(seed)
    rng.shuffle(alert_hydrant_ids)
    rng.shuffle(additional_level0_ids)

    levels: list[int] = []
    for level, count in sorted(DEMO_COMPOSITION.items()):
        levels.extend([level] * count)

    steps: list[DemoStep] = []
    offset = 0
    # Level 0 ベースラインは先頭の1件に投入し、後続ステップでは再利用しない
    # （再投入すると最新状態が上書きされ、画面上の「正常」対比が消えるため）。
    baseline_id = alert_hydrant_ids[0]
    steps.append(
        DemoStep(level=BASELINE_LEVEL, hydrant_id=baseline_id, offset_sec=offset)
    )
    offset += BASELINE_INTERVAL_SEC
    for hydrant_id in additional_level0_ids:
        steps.append(
            DemoStep(level=BASELINE_LEVEL, hydrant_id=hydrant_id, offset_sec=offset)
        )
        offset += STEP_INTERVAL_SEC
    for index, level in enumerate(levels, start=1):
        hydrant_id = alert_hydrant_ids[
            1 + ((index - 1) % (len(alert_hydrant_ids) - 1))
        ]
        steps.append(
            DemoStep(level=level, hydrant_id=hydrant_id, offset_sec=offset)
        )
        offset += STEP_INTERVAL_SEC
    return steps


def run_seed(
    seed: int,
    url: str = SEED_ENDPOINT,
    *,
    dry_run: bool = False,
    audio_dir: Path = DEFAULT_AUDIO_DIR,
    hydrants_path: Path = DEFAULT_HYDRANTS_PATH,
    post_func: PostFunc = send_telemetry,
) -> list[dict[str, Any]]:
    """デモシーケンスを組み立ててデモシード API へ投入する。

    音源は ``audio_dir`` 内の実音響 WAV（BE-2 の ``load_audio_file`` で再生）。
    ``post_func`` はテストで差し替え可能。``dry_run`` は送信せず、
    組み立て結果（level / hydrant_id / recorded_at）だけを返す。
    """
    hydrants = load_hydrants(hydrants_path)
    steps = build_demo_sequence(seed, hydrants)
    no_leak_files, leak_files = resolve_replay_files(audio_dir)
    rng = random.Random(seed)
    base_time = datetime.now(UTC)
    results: list[dict[str, Any]] = []
    for index, step in enumerate(steps):
        hydrant = find_hydrant(hydrants, step.hydrant_id)
        audio_path = select_replay_file(no_leak_files, leak_files, step.level, rng)
        signal, sample_rate_hz, duration_sec = load_audio_file(audio_path)
        validate_mvp_contract(signal, sample_rate_hz, duration_sec, audio_path)
        payload = build_payload(
            hydrant,
            signal,
            sample_rate_hz=sample_rate_hz,
            duration_sec=duration_sec,
            recorded_at=base_time + timedelta(seconds=step.offset_sec),
        )
        payload["level"] = step.level
        if dry_run:
            results.append(
                {
                    "dry_run": True,
                    "level": step.level,
                    "hydrant_id": step.hydrant_id,
                    "recorded_at": payload["recorded_at"],
                    "audio_file": audio_path.name,
                }
            )
        else:
            results.append(post_func(url, payload, 10.0))
    return results


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI 引数を解釈する。``--seed`` は必須（再現性担保のため）。"""
    parser = argparse.ArgumentParser(
        description="デモ初期状態を1コマンドで投入します"
        "（Level 0×11 + Level 1×8 / Level 2×3 / Level 3×1）。"
        "音源は実音響WAVの replay（BE-2 load_audio_file）。"
    )
    parser.add_argument(
        "--seed",
        type=int,
        required=True,
        help="シーケンス再現用シード（同一値で同一結果）",
    )
    parser.add_argument(
        "--audio-dir",
        type=Path,
        default=DEFAULT_AUDIO_DIR,
        help="実音響WAVのディレクトリ"
        "（*_level{N}.wav の leak / no-leak 規約。既定: backend/dataset）",
    )
    parser.add_argument(
        "--url",
        default=SEED_ENDPOINT,
        help="デモシード API の URL",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="送信せずに組み立て結果だけを表示する",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI エントリポイント。成功 0 / マスタ・音源起因 1 / 引数起因 2。"""
    args = parse_args(argv)
    try:
        results = run_seed(
            seed=args.seed, url=args.url, dry_run=args.dry_run,
            audio_dir=args.audio_dir,
        )
    except SimulationError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    if args.dry_run:
        counts = Counter(result["level"] for result in results)
        print(
            f"[DRY-RUN] {len(results)} steps（内訳: "
            f"{dict(sorted(counts.items()))}）"
        )
        for result in results:
            print(
                f"  level={result['level']} hydrant_id={result['hydrant_id']} "
                f"audio={result['audio_file']} recorded_at={result['recorded_at']}"
            )
    else:
        print(f"[OK] {len(results)} 件を {args.url} へ投入しました")
    return 0


if __name__ == "__main__":
    sys.exit(main())
