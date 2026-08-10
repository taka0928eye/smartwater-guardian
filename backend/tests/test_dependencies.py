import pytest
import httpx
from app.dependencies import get_http_client, HttpClientDep

@pytest.mark.asyncio
async def test_get_http_client_yields_async_client():
    async for client in get_http_client():
        assert isinstance(client, httpx.AsyncClient)
        assert not client.is_closed
    assert client.is_closed
