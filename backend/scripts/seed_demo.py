"""DEMO-1: デモ初期状態を1コマンドで構築するシードスクリプト。

Issue #23（DEMO-1）の実装。デモの山場である Level 1（微小漏水）と
Level 0（正常）との対比を、決定的なシーケンスで1コマンド投入する。

実装方針:
- BE-2 の ``generate_signal()`` を再利用し、音響生成ロジックを重複させない。
- 投入内訳は ``docs/business-model.md`` §3.4 のデモ既定値
  （Level 1×8 / Level 2×3 / Level 3×1）。
- Level 0（正常）ベースラインを先頭に投入し、「AIだけが気づいた」対比を成立させる。
- 同一 ``--seed`` で同一シーケンスを再現する（デモの再現性）。
- 深刻度は ``POST /api/v1/demo/seed``（デモシード専用エンドポイント）で意図レベルに
  確定する。実 SVM は合成波形を意図レベルに分類できないため（DEMO-1 調査で確認）。
  ハイブリッド方針（実信号 + 深刻度確定）の受け皿であり、実録音リプレイ時も
  この経路で深刻度が保証される。
"""

from __future__ import annotations

import argparse
import random
import sys
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

# スクリプト直接実行時も backend/ を sys.path に載せ、scripts.simulate_sensor を
# import できるようにする（train_leak_svm.py と同じブートストラップ）。
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from scripts.simulate_sensor import (  # noqa: E402
    DEFAULT_HYDRANTS_PATH,
    Hydrant,
    SimulationError,
    build_payload,
    find_hydrant,
    generate_signal,
    load_hydrants,
    send_telemetry,
)

# BE-3 MVP は 8000Hz・1.0 秒のみ対応（decode_pcm16 の契約）
SEED_SAMPLE_RATE_HZ = 8_000
SEED_DURATION_SEC = 1.0

# デモ既定値（docs/business-model.md §3.4）
DEMO_COMPOSITION: dict[int, int] = {1: 8, 2: 3, 3: 1}
# Level 0（正常）ベースラインの件数（PRD §6.1 の対比用）
BASELINE_LEVEL = 0
BASELINE_COUNT = 1
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


def build_demo_sequence(
    seed: int,
    hydrants: list[Hydrant] | None = None,
) -> list[DemoStep]:
    """デモ初期状態の投入シーケンスを決定的に組み立てる（純粋関数）。

    - 先頭に Level 0（正常）ベースラインを置き、続いて Level 1×8 / Level 2×3 /
      Level 3×1（§3.4 のデモ既定値）。
    - 同一 ``seed`` で同一シーケンス（再現性）。Level 1 は Level 3 より必ず先に出現。
    - 消火栓はマスタから seed でシャッフルして割り当て、件数超過時は循環させる。
    """
    if hydrants is None:
        hydrants = load_hydrants()
    if len(hydrants) < 2:
        raise SimulationError(
            "消火栓マスタが少なすぎます。"
            "Level 0 ベースラインと内訳投入には2件以上必要です"
        )
    hydrant_ids = [hydrant["hydrant_id"] for hydrant in hydrants]
    rng = random.Random(seed)
    rng.shuffle(hydrant_ids)

    levels: list[int] = []
    for level, count in sorted(DEMO_COMPOSITION.items()):
        levels.extend([level] * count)

    steps: list[DemoStep] = []
    offset = 0
    # Level 0 ベースラインは先頭の1件に投入し、後続ステップでは再利用しない
    # （再投入すると最新状態が上書きされ、画面上の「正常」対比が消えるため）。
    baseline_id = hydrant_ids[0]
    steps.append(
        DemoStep(level=BASELINE_LEVEL, hydrant_id=baseline_id, offset_sec=offset)
    )
    offset += BASELINE_INTERVAL_SEC
    for index, level in enumerate(levels, start=1):
        hydrant_id = hydrant_ids[1 + ((index - 1) % (len(hydrant_ids) - 1))]
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
    hydrants_path: Path = DEFAULT_HYDRANTS_PATH,
    post_func: PostFunc = send_telemetry,
    sample_rate_hz: int = SEED_SAMPLE_RATE_HZ,
    duration_sec: float = SEED_DURATION_SEC,
) -> list[dict[str, Any]]:
    """デモシーケンスを組み立ててデモシード API へ投入する。

    ``post_func`` はテストで差し替え可能。``dry_run`` は送信せず、
    組み立て結果（level / hydrant_id / recorded_at）だけを返す。
    """
    hydrants = load_hydrants(hydrants_path)
    steps = build_demo_sequence(seed, hydrants)
    base_time = datetime.now(UTC)
    results: list[dict[str, Any]] = []
    for index, step in enumerate(steps):
        hydrant = find_hydrant(hydrants, step.hydrant_id)
        signal = generate_signal(
            step.level,
            sample_rate_hz=sample_rate_hz,
            duration_sec=duration_sec,
            seed=seed + index,
        )
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
                }
            )
        else:
            results.append(post_func(url, payload, 10.0))
    return results


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI 引数を解釈する。``--seed`` は必須（再現性担保のため）。"""
    parser = argparse.ArgumentParser(
        description="デモ初期状態を1コマンドで投入します"
        "（Level 0 ベースライン + Level 1×8 / Level 2×3 / Level 3×1）。"
    )
    parser.add_argument(
        "--seed",
        type=int,
        required=True,
        help="シーケンス再現用シード（同一値で同一結果）",
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
    """CLI エントリポイント。成功 0 / マスタ起因 1 / 引数起因 2。"""
    args = parse_args(argv)
    try:
        results = run_seed(seed=args.seed, url=args.url, dry_run=args.dry_run)
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
                f"recorded_at={result['recorded_at']}"
            )
    else:
        print(f"[OK] {len(results)} 件を {args.url} へ投入しました")
    return 0


if __name__ == "__main__":
    sys.exit(main())
