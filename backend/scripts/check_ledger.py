"""BE-4 検証スクリプト: 配管台帳照合サービス（app/services/ledger.py）の自己検証。

サーバー起動不要・追加依存なしで、受け入れ条件 A1〜A4 / A6 / D-4 / D-5 を
個別ケースで検証する（A5 は API 配線のため pytest の test_alerts.py 側で検証）。
check_telemetry.py と同じ流儀（PASS/FAIL 逐次表示、終了コード 0/1）。

実行（backend ディレクトリで）:

    venv/Scripts/python.exe scripts/check_ledger.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

# scripts/ から実行されるため、backend ルートを sys.path に追加して app を import 可能にする
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.ledger import (  # noqa: E402
    PIPES_PATH,
    _load_pipes,
    find_nearest_pipe,
    find_pipe_by_hydrant,
    get_pipe_age,
    get_pipes,
)


class CheckFailure(Exception):
    """検証項目の失敗。"""


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailure(message)


def case_1_pipes_json_has_10_routes() -> None:
    """A前提: pipes.json が10路線で、pipe_id が P-001〜P-010 と一致する（D-4）。"""
    data = json.loads(PIPES_PATH.read_text(encoding="utf-8"))
    expect(len(data) == 10, f"路線数が10ではない: {len(data)}")
    expect(
        sorted(pipe["pipe_id"] for pipe in data)
        == [f"P-{index:03d}" for index in range(1, 11)],
        f"pipe_id が P-001〜P-010 と一致しない: {[pipe['pipe_id'] for pipe in data]}",
    )


def case_2_all_hydrants_resolve() -> None:
    """A1: 全10消火栓（HYD-001〜010）が find_pipe_by_hydrant で解決される。"""
    for index in range(1, 11):
        hydrant_id = f"HYD-{index:03d}"
        pipe = find_pipe_by_hydrant(hydrant_id)
        expect(pipe is not None, f"{hydrant_id} が解決されない")
        expect(pipe.pipe_id == f"P-{index:03d}", f"{hydrant_id} の pipe_id 不一致: {pipe.pipe_id}")


def case_3_unknown_id_returns_none() -> None:
    """A2: 未知の hydrant_id は None を返す。"""
    expect(find_pipe_by_hydrant("HYD-999") is None, "未知IDで None を返すべき")


def case_4_nearest_pipe_at_known_coords() -> None:
    """A3: 既知座標（消火栓位置 = 路線頂点）で最近接路線が非 None で返る。"""
    pipe = find_nearest_pipe(35.7019, 139.7444)  # HYD-001 の位置
    expect(pipe is not None, "既知座標で最近接路線が None になってはいけない")
    expect(pipe.pipe_id == "P-001", f"最近接が P-001 のはず: {pipe.pipe_id}")


def case_5_pipe_age() -> None:
    """D-5: get_pipe_age が 2026 - installed_year を返す。"""
    expect(get_pipe_age(1998) == 28, f"get_pipe_age(1998) は 28 のはず: {get_pipe_age(1998)}")
    expect(get_pipe_age(2015) == 11, f"get_pipe_age(2015) は 11 のはず: {get_pipe_age(2015)}")


def case_6_explicit_exceptions() -> None:
    """A4: 欠損パス→FileNotFoundError / 破損JSON→ValueError の明示例外。"""
    # 欠損パス
    missing = BACKEND_ROOT / "app" / "data" / "no_such_pipes.json"
    try:
        _load_pipes(missing)
    except FileNotFoundError:
        pass
    else:
        raise CheckFailure("欠損パスで FileNotFoundError を送出するべき")

    # 破損 JSON（一時ファイルに不正 JSON を書いて検証）
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        fh.write("{ これは不正なJSONです !!")
        corrupt_path = Path(fh.name)
    try:
        try:
            _load_pipes(corrupt_path)
        except ValueError:
            pass
        else:
            raise CheckFailure("破損 JSON で ValueError を送出するべき")
    finally:
        corrupt_path.unlink(missing_ok=True)


def case_7_module_cache() -> None:
    """A6: get_pipes() がキャッシュを1要素だけ保持する。"""
    get_pipes.cache_clear()
    get_pipes()
    expect(
        get_pipes.cache_info().currsize == 1,
        f"キャッシュ保持件数が1のはず: {get_pipes.cache_info().currsize}",
    )


CASES = [
    ("台帳: pipes.json が10路線（P-001〜P-010）", case_1_pipes_json_has_10_routes),
    ("A1: 全10消火栓が find_pipe_by_hydrant で解決", case_2_all_hydrants_resolve),
    ("A2: 未知の hydrant_id は None", case_3_unknown_id_returns_none),
    ("A3: find_nearest_pipe が既知座標で非 None", case_4_nearest_pipe_at_known_coords),
    ("D-5: get_pipe_age が 2026 - installed_year", case_5_pipe_age),
    ("A4: 欠損→FileNotFoundError / 破損→ValueError", case_6_explicit_exceptions),
    ("A6: モジュールキャッシュ保持（currsize==1）", case_7_module_cache),
]


def main() -> int:
    failures = 0
    for index, (name, case) in enumerate(CASES, start=1):
        try:
            case()
        except CheckFailure as exc:
            failures += 1
            print(f"[FAIL] {index}. {name}\n       {exc}")
        except Exception as exc:  # noqa: BLE001 - 予期しない例外も FAIL として表示する
            failures += 1
            print(f"[FAIL] {index}. {name}\n       予期しない例外: {type(exc).__name__}: {exc}")
        else:
            print(f"[PASS] {index}. {name}")

    print(f"\n結果: {len(CASES) - failures}/{len(CASES)} PASS")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
