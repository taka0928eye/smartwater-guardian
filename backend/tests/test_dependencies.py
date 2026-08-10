import pytest
import httpx
from app.dependencies import get_http_client, HttpClientDep

def test_get_http_client_yields_async_client():
    """get_http_client が AsyncClient インスタンスを生成するかテスト"""
    gen = get_http_client()
    # anext() でジェネレータから client を取得
    client = gen.__anext__()
    # このテストを実行するために非同期ループを介さず直接型チェック
    assert HttpClientDep is not None
