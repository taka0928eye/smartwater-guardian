from collections.abc import AsyncGenerator
from typing import Annotated

import httpx
from fastapi import Depends


async def get_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """
    OrcaRouter等の外部API呼び出し用AsyncClientを提供するジェネレータ
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client

HttpClientDep = Annotated[httpx.AsyncClient, Depends(get_http_client)]
