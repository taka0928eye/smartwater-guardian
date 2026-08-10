"""pytest 共有フィクスチャ。

実行方法（backend ディレクトリで）:

    venv/Scripts/python.exe -m pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="session")
def client():
    """FastAPI アプリのテストクライアント（サーバー起動不要）。"""
    with TestClient(app) as test_client:
        yield test_client
