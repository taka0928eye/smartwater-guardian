"""pytest 共有フィクスチャ。

実行方法（backend ディレクトリで）:

    venv/Scripts/python.exe -m pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient

from app.store import clear_disaster_state, get_store, reset_store
from main import app


@pytest.fixture(scope="session")
def client():
    """FastAPI アプリのテストクライアント（サーバー起動不要）。"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def store():
    """BE-6: 現在のインメモリストア（シングルトン）。"""
    return get_store()


@pytest.fixture(autouse=True)
def _reset_store():
    """BE-6: 各テスト実行前にインメモリストアとランタイムセンサーをリセットし、テスト間を隔離する。

    ルーターはハンドラ実行時に ``get_store()`` を呼ぶため、``reset_store()`` で
    シングルトンを破棄すれば次リクエストは新規ストアを生成して完全に隔離される。
    ランタイムセンサーも防災シミュレーションの影響を各テスト間で隔離するため
    クリアする。
    """
    reset_store()
    clear_disaster_state()
    yield
    reset_store()
    clear_disaster_state()
