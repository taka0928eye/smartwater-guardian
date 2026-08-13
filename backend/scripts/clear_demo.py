"""DEMO-1: デモシード状態をクリアするスクリプト。

Issue #23（DEMO-1）の補助スクリプト。投入済みのアラート・シード状態をリセットし、
初期状態（空のストア）に戻す。バックエンド再起動不要。

使用シーン:
- デモリハーサル中に「正常状態 → Level 1 検知」を何度も実演したい
- AWS 環境でバックエンド再起動が難しい場合
- シード再投入前にストア状態をリセットしたい
- 別シード（--seed 999）で異なるシナリオをテストしたい

実装方針:
- backend のシングルトン InMemoryStore.clear() を直接呼び出す
- または HTTP DELETE /api/v1/demo/clear エンドポイントに POST する
- 当スクリプトはスタンドアロン mode で、HTTP 経由で backend にリセット指示を送る
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

# スクリプト直接実行時も backend/ を sys.path に載せ、
# app.store を import できるようにする（seed_demo.py と同じブートストラップ）。
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from scripts.simulate_sensor import SimulationError, send_telemetry  # noqa: E402


# デモシードクリア API のエンドポイント
CLEAR_ENDPOINT = "http://localhost:8000/api/v1/demo/clear"


def run_clear(url: str = CLEAR_ENDPOINT) -> dict[str, Any]:
    """デモシード状態をクリアする API を呼び出す。

    backend 側の /api/v1/demo/clear エンドポイントに DELETE リクエストを送り、
    ストアをリセット（全アラート削除）させる。
    """
    try:
        # DELETE メソッドを使う。ペイロードは不要。
        import urllib.request
        import json

        req = urllib.request.Request(url, method="DELETE")
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=10.0) as response:
                data = json.loads(response.read().decode("utf-8"))
                return data
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise SimulationError(
                    f"クリア API が見つかりません（404）: {url}\n"
                    f"backend が起動していてエンドポイント /api/v1/demo/clear が "
                    f"実装されていることを確認してください。"
                )
            else:
                body = exc.read().decode("utf-8", errors="replace")
                raise SimulationError(
                    f"API エラー（{exc.code}）: {url}\n{body}"
                )
        except urllib.error.URLError as exc:
            raise SimulationError(
                f"backend に接続できません（{url}）: {exc.reason}\n"
                f"backend が起動していることを確認してください。"
            )
    except SimulationError:
        raise
    except Exception as exc:
        raise SimulationError(f"予期しないエラー: {exc}") from exc


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI 引数を解釈する。"""
    parser = argparse.ArgumentParser(
        description="デモシード状態をクリアします（ストア内のアラート全削除）。"
        "バックエンド再起動不要。"
    )
    parser.add_argument(
        "--url",
        default=CLEAR_ENDPOINT,
        help="デモシードクリア API の URL（既定: http://localhost:8000/api/v1/demo/clear）",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI エントリポイント。成功 0 / API 起因 1 / 引数起因 2。"""
    args = parse_args(argv)
    try:
        result = run_clear(url=args.url)
    except SimulationError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    # 結果を表示
    cleared_count = result.get("cleared_count", "?")
    print(f"[OK] {cleared_count} 件のアラートをクリアしました")
    return 0


if __name__ == "__main__":
    sys.exit(main())
