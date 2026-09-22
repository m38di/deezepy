"""Shared base class for resource namespaces (sync + async aware)."""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any

from ..paginator import PaginatedList

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..client import BaseClient


def _run(value: Any) -> Any:
    """Return ``value`` directly if sync, else an awaitable resolving it.

    Resource methods stay plain ``def`` so the sync client works unchanged.
    On the async client the proxy awaits the returned coroutine (see
    ``AsyncDeezerClient``), which lets the *same* code serve both clients.
    """
    if inspect.isawaitable(value):

        async def _resolve() -> Any:
            return await value

        return _resolve()
    return value


class Resource:
    """Namespace bound to a client (``client.album.get(...)``)."""

    def __init__(self, client: "BaseClient") -> None:
        self._client = client

    # -- low-level passthrough -------------------------------------------
    def _get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return _run(self._client._get(path, params=params))

    def _post(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> Any:
        return _run(self._client._post(path, params=params, data=data))

    def _delete(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return _run(self._client._delete(path, params=params))

    # -- pagination helpers ----------------------------------------------
    @staticmethod
    def _page(params: dict[str, Any] | None, index: int | None, limit: int | None) -> dict:
        merged: dict[str, Any] = dict(params or {})
        if index is not None:
            merged["index"] = index
        if limit is not None:
            merged["limit"] = limit
        return merged

    def _paginated(
        self, path: str, *, params: dict[str, Any] | None = None
    ) -> Any:
        result = self._client._get(path, params=params)
        if inspect.isawaitable(result):

            async def _resolve() -> PaginatedList:
                payload = await result
                return PaginatedList(payload, fetch=self._client._fetch_url)

            return _resolve()
        return PaginatedList(result, fetch=self._client._fetch_url)
