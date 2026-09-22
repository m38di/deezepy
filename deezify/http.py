"""Sync + async HTTP layer over httpx with Deezer error mapping,
rate limiting (50 requests / 5 s) and quota/busy retries.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

from .errors import DeezerAPIError, DeezerTransportError
from .ratelimit import (
    AsyncRateLimiter,
    SyncRateLimiter,
    retry_delay,
    should_retry,
)

API_BASE_URL = "https://api.deezer.com"
DEFAULT_TIMEOUT = 30.0
DEFAULT_USER_AGENT = "deezify/1.0 (+https://developers.deezer.com/api)"


def _raise_for_envelope(
    payload: Any, *, status_code: int | None, endpoint: str
) -> Any:
    if isinstance(payload, dict) and isinstance(payload.get("error"), dict):
        raise DeezerAPIError.from_payload(
            payload, status_code=status_code, endpoint=endpoint
        )
    return payload


def _decode(
    response: httpx.Response, *, endpoint: str, output: str | None = None
) -> Any:
    if output in ("xml", "php"):
        raise DeezerTransportError(
            "output='xml'/'php' is not decoded by this SDK; use output=None (JSON)",
            status_code=response.status_code,
        )
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        try:
            payload = response.json()
        except ValueError:
            payload = None
        if isinstance(payload, dict) and isinstance(payload.get("error"), dict):
            raise DeezerAPIError.from_payload(
                payload, status_code=response.status_code, endpoint=endpoint
            ) from exc
        if response.status_code in (429, 502, 503, 504):
            raise DeezerTransportError(
                f"Transient HTTP failure for {endpoint}: {exc}",
                status_code=response.status_code,
            ) from exc
        raise DeezerTransportError(
            f"HTTP request failed for {endpoint}: {exc}",
            status_code=response.status_code,
        ) from exc
    try:
        payload = response.json()
    except ValueError as exc:
        raise DeezerTransportError(
            f"Could not decode JSON response from {endpoint}",
            status_code=response.status_code,
        ) from exc
    return _raise_for_envelope(
        payload, status_code=response.status_code, endpoint=endpoint
    )


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, DeezerAPIError):
        return should_retry(error=exc, attempt=0)
    if isinstance(exc, DeezerTransportError):
        return should_retry(error=None, status_code=exc.status_code, attempt=0)
    return False


class SyncTransport:
    """Sync wrapper around :class:`httpx.Client` with throttling + retries."""

    def __init__(
        self,
        *,
        base_url: str = API_BASE_URL,
        access_token: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        user_agent: str = DEFAULT_USER_AGENT,
        client: httpx.Client | None = None,
        rate_limiter: SyncRateLimiter | None | bool = None,
        max_retries: int = 3,
        retry_base: float = 0.5,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token
        self.max_retries = max_retries
        self.retry_base = retry_base
        if rate_limiter is None or rate_limiter is True:
            rate_limiter = SyncRateLimiter()
        elif rate_limiter is False:
            rate_limiter = SyncRateLimiter(max_calls=None)
        self.rate_limiter = rate_limiter
        self._owns_client = client is None
        self.client = client or httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers={"Accept": "application/json", "User-Agent": user_agent},
        )

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    # -- low level verbs -------------------------------------------------
    def _params(self, params: dict[str, Any] | None) -> dict[str, Any]:
        merged: dict[str, Any] = dict(params or {})
        if self.access_token and "access_token" not in merged:
            merged["access_token"] = self.access_token
        return merged

    def _send(
        self,
        method: str,
        endpoint: str,
        *,
        params: dict[str, Any] | None,
        data: dict[str, Any] | None,
    ) -> Any:
        try:
            response = self.client.request(
                method.upper(), f"/{endpoint}", params=self._params(params), data=data
            )
        except httpx.HTTPError as exc:
            raise DeezerTransportError(f"HTTP request failed for {endpoint}: {exc}") from exc
        return _decode(response, endpoint=endpoint)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> Any:
        endpoint = path.lstrip("/")
        attempt = 0
        while True:
            self.rate_limiter.acquire()
            try:
                return self._send(method, endpoint, params=params, data=data)
            except (DeezerAPIError, DeezerTransportError) as exc:
                status = (
                    exc.code
                    if isinstance(exc, DeezerAPIError)
                    else exc.status_code
                )
                retryable = (
                    should_retry(error=exc, attempt=attempt, max_retries=self.max_retries)
                    if isinstance(exc, DeezerAPIError)
                    else should_retry(
                        error=None,
                        status_code=status,
                        attempt=attempt,
                        max_retries=self.max_retries,
                    )
                )
                if not retryable or not _is_retryable(exc):
                    raise
                time.sleep(retry_delay(attempt, base=self.retry_base))
                attempt += 1

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return self.request("GET", path, params=params)

    def post(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> Any:
        return self.request("POST", path, params=params, data=data)

    def delete(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return self.request("DELETE", path, params=params)


class AsyncTransport:
    """Async wrapper around :class:`httpx.AsyncClient` with throttling + retries."""

    def __init__(
        self,
        *,
        base_url: str = API_BASE_URL,
        access_token: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        user_agent: str = DEFAULT_USER_AGENT,
        client: httpx.AsyncClient | None = None,
        rate_limiter: AsyncRateLimiter | None | bool = None,
        max_retries: int = 3,
        retry_base: float = 0.5,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token
        self.max_retries = max_retries
        self.retry_base = retry_base
        if rate_limiter is None or rate_limiter is True:
            rate_limiter = AsyncRateLimiter()
        elif rate_limiter is False:
            rate_limiter = AsyncRateLimiter(max_calls=None)
        self.rate_limiter = rate_limiter
        self._owns_client = client is None
        self.client = client or httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers={"Accept": "application/json", "User-Agent": user_agent},
        )

    async def close(self) -> None:
        if self._owns_client:
            await self.client.aclose()

    def _params(self, params: dict[str, Any] | None) -> dict[str, Any]:
        merged: dict[str, Any] = dict(params or {})
        if self.access_token and "access_token" not in merged:
            merged["access_token"] = self.access_token
        return merged

    async def _send(
        self,
        method: str,
        endpoint: str,
        *,
        params: dict[str, Any] | None,
        data: dict[str, Any] | None,
    ) -> Any:
        try:
            response = await self.client.request(
                method.upper(), f"/{endpoint}", params=self._params(params), data=data
            )
        except httpx.HTTPError as exc:
            raise DeezerTransportError(f"HTTP request failed for {endpoint}: {exc}") from exc
        return _decode(response, endpoint=endpoint)

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> Any:
        endpoint = path.lstrip("/")
        attempt = 0
        while True:
            await self.rate_limiter.acquire()
            try:
                return await self._send(method, endpoint, params=params, data=data)
            except (DeezerAPIError, DeezerTransportError) as exc:
                status = (
                    exc.code
                    if isinstance(exc, DeezerAPIError)
                    else exc.status_code
                )
                retryable = (
                    should_retry(error=exc, attempt=attempt, max_retries=self.max_retries)
                    if isinstance(exc, DeezerAPIError)
                    else should_retry(
                        error=None,
                        status_code=status,
                        attempt=attempt,
                        max_retries=self.max_retries,
                    )
                )
                if not retryable or not _is_retryable(exc):
                    raise
                await asyncio.sleep(retry_delay(attempt, base=self.retry_base))
                attempt += 1

    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return await self.request("GET", path, params=params)

    async def post(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> Any:
        return await self.request("POST", path, params=params, data=data)

    async def delete(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return await self.request("DELETE", path, params=params)

