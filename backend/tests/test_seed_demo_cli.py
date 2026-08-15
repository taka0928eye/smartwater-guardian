"""DEMO-2: scripts/seed_demo.py（薄いCLIラッパー）のテスト。

内訳計算・音声選択ロジックは ``app/services/demo_seed.py`` に一本化されており
（``tests/test_demo_seed_service.py`` で検証済み）、本スクリプトは
``POST /api/v1/demo/seed-batch`` を1回叩くだけの薄いラッパーである。
``--dry-run`` はネットワークを使わない組み立てプレビューであることを検証する。

実行方法（backend ディレクトリで）:

    venv/Scripts/python.exe -m pytest tests/test_seed_demo_cli.py -v
"""

from __future__ import annotations

import pytest

from scripts.seed_demo import (
    DEFAULT_URL,
    SeedBatchCliError,
    main,
    parse_args,
    run_seed_batch_cli,
)


def test_run_seed_batch_cli_posts_seed_param() -> None:
    """CLIがseed-batchエンドポイントへseedパラメータ付きでPOSTする。"""
    captured: list[tuple[str, dict, float]] = []

    def fake_post(url: str, params: dict, timeout: float) -> dict:
        captured.append((url, params, timeout))
        return {"inserted_count": 20, "level_counts": {"0": 8, "1": 8, "2": 3, "3": 1}}

    result = run_seed_batch_cli(
        seed=42, url="http://test.local/api/v1/demo/seed-batch", post_func=fake_post
    )
    assert result["inserted_count"] == 20
    assert len(captured) == 1
    url, params, _timeout = captured[0]
    assert url == "http://test.local/api/v1/demo/seed-batch"
    assert params == {"seed": 42}


def test_run_seed_batch_cli_wraps_request_failure() -> None:
    """POST失敗はSeedBatchCliErrorに変換される。"""

    def failing_post(url: str, params: dict, timeout: float) -> dict:
        raise ConnectionError("boom")

    def wrapping_post(url: str, params: dict, timeout: float) -> dict:
        try:
            return failing_post(url, params, timeout)
        except ConnectionError as exc:
            raise SeedBatchCliError(str(exc)) from exc

    with pytest.raises(SeedBatchCliError):
        run_seed_batch_cli(seed=1, post_func=wrapping_post)


def test_parse_args_requires_seed() -> None:
    """--seed が必須で、url は既定値。"""
    args = parse_args(["--seed", "42"])
    assert args.seed == 42
    assert args.url == DEFAULT_URL
    assert args.dry_run is False


def test_parse_args_dry_run_flag() -> None:
    """--dry-run フラグを解釈する。"""
    args = parse_args(["--seed", "42", "--dry-run"])
    assert args.dry_run is True


def test_main_dry_run_shows_assignment_without_network(capsys: pytest.CaptureFixture[str]) -> None:
    """--dry-run は送信せず、消火栓へのレベル割当てだけを表示する。"""
    rc = main(["--seed", "42", "--dry-run"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "[DRY-RUN]" in out
    assert "level=" in out
    assert "hydrant_id=" in out


def test_main_success_returns_zero(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """API呼び出し成功時は0で終了し、投入結果を表示する。"""
    import scripts.seed_demo as seed_demo_cli

    monkeypatch.setattr(
        seed_demo_cli,
        "run_seed_batch_cli",
        lambda seed, url=DEFAULT_URL: {
            "inserted_count": 20,
            "level_counts": {"0": 8, "1": 8, "2": 3, "3": 1},
        },
    )
    rc = main(["--seed", "42"])
    assert rc == 0
    assert "[OK]" in capsys.readouterr().out


def test_main_failure_returns_one(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """API呼び出し失敗時は1で終了する。"""
    import scripts.seed_demo as seed_demo_cli

    def boom(seed: int, url: str = DEFAULT_URL) -> dict:
        raise SeedBatchCliError("接続できません")

    monkeypatch.setattr(seed_demo_cli, "run_seed_batch_cli", boom)
    rc = main(["--seed", "42"])
    assert rc == 1
    assert "[ERROR]" in capsys.readouterr().err
