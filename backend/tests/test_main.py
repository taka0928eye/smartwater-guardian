"""DEMO-2: main.py 起動処理（lifespan）のテスト。

「初期表示時は20件・全てLv0」という要求が、FastAPI 起動時の lifespan で
満たされることを検証する。あわせて、AWS環境向けの S3 データセット同期
（DEMO_DATASET_S3_URI 環境変数）が起動を止めないことも検証する。

実行方法（backend ディレクトリで）:

    venv/Scripts/python.exe -m pytest tests/test_main.py -v
"""

from __future__ import annotations

from unittest.mock import patch

from app.store import get_store, reset_store


async def test_lifespan_initializes_twenty_level0_sensors() -> None:
    """起動時 lifespan がhydrants.json 20件を severity_level=0 で登録する。"""
    from main import app, lifespan

    reset_store()
    try:
        async with lifespan(app):
            store = get_store()
            records = store.get_all()
            assert len(records) == 20
            assert all(record.analysis.severity_level == 0 for record in records)
            assert {record.sensor_id for record in records} == {
                f"SNS-{i:03d}" for i in range(1, 21)
            }
    finally:
        reset_store()


async def test_lifespan_skips_s3_sync_when_env_unset(monkeypatch) -> None:
    """DEMO_DATASET_S3_URI 未設定時は S3 同期を試みない（ローカル開発既定）。"""
    from main import app, lifespan

    monkeypatch.delenv("DEMO_DATASET_S3_URI", raising=False)
    reset_store()
    try:
        with patch("main.sync_dataset_from_s3") as mock_sync:
            async with lifespan(app):
                pass
            mock_sync.assert_not_called()
    finally:
        reset_store()


async def test_lifespan_syncs_s3_dataset_when_env_set(monkeypatch) -> None:
    """DEMO_DATASET_S3_URI 設定時は起動時にS3同期を試みる（AWS環境向け）。"""
    from main import app, lifespan

    monkeypatch.setenv("DEMO_DATASET_S3_URI", "s3://demo-bucket/dataset/")
    reset_store()
    try:
        with patch("main.sync_dataset_from_s3", return_value=4) as mock_sync:
            async with lifespan(app):
                pass
            mock_sync.assert_called_once()
            args, _kwargs = mock_sync.call_args
            assert args[0] == "s3://demo-bucket/dataset/"
    finally:
        reset_store()


async def test_lifespan_continues_startup_when_s3_sync_fails(monkeypatch) -> None:
    """S3同期に失敗しても起動を継続する（500にしない設計と同じ思想）。"""
    from app.services.dataset_sync import DatasetSyncError
    from main import app, lifespan

    monkeypatch.setenv("DEMO_DATASET_S3_URI", "s3://demo-bucket/dataset/")
    reset_store()
    try:
        with patch(
            "main.sync_dataset_from_s3", side_effect=DatasetSyncError("boom")
        ):
            async with lifespan(app):
                store = get_store()
                # S3同期に失敗しても、20件Lv0の初期化は行われる
                assert len(store.get_all()) == 20
    finally:
        reset_store()
