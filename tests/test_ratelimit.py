"""Rate limiter + retry tests (offline, mocked HTTP)."""

from __future__ import annotations

import time

import httpx
import pytest

from deezify import DeezerAPIError, DeezerClient
from deezify.ratelimit import (
    AsyncRateLimiter,
    SyncRateLimiter,
    retry_delay,
    should_retry,
)


def make_client(handler, **kwargs) -> DeezerClient:
    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, base_url="https://api.deezer.com")
    return DeezerClient(http_client=http_client, **kwargs)


def test_limiter_throttles_to_budget():
    limiter = SyncRateLimiter(max_calls=2, period=0.3)
    start = time.monotonic()
    for _ in range(4):
        limiter.acquire()
    elapsed = time.monotonic() - start
    assert elapsed >= 0.28  # second window of 2 must wait ~period


def test_limiter_disabled_is_noop():
    for kwargs in ({"max_calls": None}, {"max_calls": 0}):
        limiter = SyncRateLimiter(**kwargs)
        assert limiter.enabled is False
        start = time.monotonic()
        for _ in range(5):
            limiter.acquire()
        assert time.monotonic() - start < 0.2


def test_should_retry_quota_and_busy_only():
    quota = DeezerAPIError("Exception", "quota", 4)
    busy = DeezerAPIError("Exception", "busy", 700)
    notfound = DeezerAPIError("DataException", "no data", 800)
    assert should_retry(error=quota, attempt=0) is True
    assert should_retry(error=busy, attempt=0) is True
    assert should_retry(error=notfound, attempt=0) is False
    assert should_retry(error=quota, attempt=0, max_retries=0) is False
    assert should_retry(error=None, status_code=429, attempt=0) is True
    assert should_retry(error=None, status_code=500, attempt=0) is False
    assert retry_delay(0, jitter=0) < retry_delay(1, jitter=0)


def test_quota_error_is_retried_then_succeeds():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(
                200,
                json={"error": {"type": "Exception", "message": "quota", "code": 4}},
            )
        return httpx.Response(200, json={"id": 1, "title": "ok"})

    client = make_client(handler, rate_limit=False, retry_base=0.01)
    track = client.track.get(1)
    assert track["title"] == "ok"
    assert len(calls) == 2


def test_non_retryable_error_raises_immediately():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(
            200,
            json={"error": {"type": "DataException", "message": "no", "code": 800}},
        )

    client = make_client(handler, rate_limit=False, retry_base=0.01)
    with pytest.raises(DeezerAPIError):
        client.track.get(0)
    assert len(calls) == 1


def test_retry_exhaustion_reraises():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"error": {"type": "Exception", "message": "q", "code": 4}}
        )

    client = make_client(handler, rate_limit=False, max_retries=2, retry_base=0.01)
    with pytest.raises(DeezerAPIError):
        client.track.get(1)


@pytest.mark.asyncio
async def test_async_limiter_throttles():
    import asyncio

    limiter = AsyncRateLimiter(max_calls=2, period=0.3)
    start = asyncio.get_running_loop().time()
    for _ in range(4):
        await limiter.acquire()
    assert asyncio.get_running_loop().time() - start >= 0.28

