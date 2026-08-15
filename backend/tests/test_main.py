"""DEMO-2: main.py 起動処理（lifespan）のテスト。

「初期表示時は20件・全てLv0」という要求が、FastAPI 起動時の lifespan で
満たされることを検証する。

実行方法（backend ディレクトリで）:

    venv/Scripts/python.exe -m pytest tests/test_main.py -v
"""

from __future__ import annotations

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
