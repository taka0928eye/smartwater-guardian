"""DEMO-2: デモ初期状態を1コマンドで一括投入するCLIラッパー。

内訳計算・音声選択ロジックは ``app/services/demo_seed.py`` に一本化されており
（フロントの「シード投入」ボタンからも同じロジックを ``POST
/api/v1/demo/seed-batch`` 経由で呼ぶ）、本スクリプトはそのエンドポイントを
1回叩く薄い CLI ラッパーである。``--dry-run`` はネットワークを使わず、
``build_seed_batch()`` で消火栓へのレベル割当てだけをプレビューする。
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import requests

# スクリプト直接実行時も backend/ を sys.path に載せ、app.* を import できるようにする。
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.demo_seed import build_seed_batch  # noqa: E402
from app.store import get_hydrants  # noqa: E402

DEFAULT_URL = "http://localhost:8000/api/v1/demo/seed-batch"

PostFunc = Callable[[str, dict[str, Any], float], dict[str, Any]]


class SeedBatchCliError(Exception):
    """CLI実行時の明示的な失敗（API起因）。"""


def _post_seed_batch(url: str, params: dict[str, Any], timeout_sec: float) -> dict[str, Any]:
    """seed-batch エンドポイントへ1回POSTする。テストでは差し替え可能。"""
    try:
        response = requests.post(url, params=params, timeout=timeout_sec)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise SeedBatchCliError(f"デモシード一括投入 API への送信に失敗しました: {exc}") from exc
    except ValueError as exc:
        raise SeedBatchCliError("デモシード一括投入 API のレスポンスJSONを解読できません") from exc


def run_seed_batch_cli(
    seed: int,
    url: str = DEFAULT_URL,
    timeout_sec: float = 30.0,
    post_func: PostFunc = _post_seed_batch,
) -> dict[str, Any]:
    """seed-batch エンドポイントを1回叩き、結果 JSON を返す。"""
    return post_func(url, {"seed": seed}, timeout_sec)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI 引数を解釈する。``--seed`` は必須（再現性担保のため）。"""
    parser = argparse.ArgumentParser(
        description="デモ初期状態(Lv0×8/Lv1×8/Lv2×3/Lv3×1、計20件)を一括投入します。"
    )
    parser.add_argument(
        "--seed", type=int, required=True, help="配分・音声選択の再現用シード（同一値で同一結果）"
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="デモシード一括投入 API の URL")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="送信せず、消火栓へのレベル割当てだけを表示する",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI エントリポイント。成功 0 / API起因 1。"""
    args = parse_args(argv)

    if args.dry_run:
        hydrants = get_hydrants()
        steps = build_seed_batch(hydrants, seed=args.seed)
        print(f"[DRY-RUN] {len(steps)} 件の消火栓へレベルを割り当てます")
        for step in steps:
            print(f"  level={step.level} hydrant_id={step.hydrant_id}")
        return 0

    try:
        result = run_seed_batch_cli(args.seed, args.url)
    except SeedBatchCliError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    print(
        f"[OK] {result['inserted_count']} 件を {args.url} へ投入しました"
        f"（内訳: {result['level_counts']}）"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
