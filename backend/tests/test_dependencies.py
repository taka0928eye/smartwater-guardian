import asyncio

import httpx
import pytest

from app.dependencies import HttpClientDep, get_http_client


def test_get_http_client_yields_async_client():
    """get_http_client が httpx.AsyncClient を yield し、使用後にクローズすることを検証する。"""

    async def _drive() -> httpx.AsyncClient:
        gen = get_http_client()
        client = await gen.__anext__()
        assert isinstance(client, httpx.AsyncClient)
        assert not client.is_closed
        # ジェネレータを最後まで進め、`async with` の __aexit__（クローズ処理）を実行させる
        with pytest.raises(StopAsyncIteration):
            await gen.__anext__()
        return client

    client = asyncio.run(_drive())
    assert client.is_closed
    assert HttpClientDep is not None
