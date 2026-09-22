"""Async client tests — mocked HTTP, no network needed."""

from __future__ import annotations

import httpx
import pytest

from deezify import AsyncDeezerClient, DeezerAPIError


def make_async_client(handler) -> AsyncDeezerClient:
    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(
        transport=transport, base_url="https://api.deezer.com"
    )
    return AsyncDeezerClient(http_client=http_client)


@pytest.mark.asyncio
async def test_async_track_get():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/track/3135556"
        return httpx.Response(200, json={"id": 3135556, "title": "Harder"})

    async with make_async_client(handler) as client:
        track = await client.track.get(3135556)
        assert track["title"] == "Harder"


@pytest.mark.asyncio
async def test_async_search_and_error():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/search":
            return httpx.Response(200, json={"data": [{"id": 1}], "total": 1})
        return httpx.Response(
            200,
            json={"error": {"type": "DataException", "message": "nope", "code": 800}},
        )

    async with make_async_client(handler) as client:
        page = await client.search.all("x")
        assert page.total == 1
        with pytest.raises(DeezerAPIError):
            await client.track.get(0)

