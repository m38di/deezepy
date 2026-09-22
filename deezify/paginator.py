"""Pagination helpers.

List endpoints answer with an envelope like::

    {"data": [...], "total": 123, "prev": "...", "next": "..."}

:class:`PaginatedList` is a small immutable view over that envelope: ``list()``
gives the items, ``.total`` the advertised total, and :meth:`iter_all_pages`
walks ``next`` links until exhaustion.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class PaginatedList(Generic[T]):
    """A single page of a Deezer collection plus navigation helpers."""

    def __init__(
        self,
        payload: dict[str, Any] | list[Any],
        *,
        fetch: Callable[[str], dict[str, Any]] | None = None,
    ) -> None:
        if isinstance(payload, list):
            payload = {"data": payload, "total": len(payload)}
        self._payload = payload
        self._fetch = fetch

    # -- page content ----------------------------------------------------
    @property
    def data(self) -> list[T]:
        items = self._payload.get("data", [])
        return list(items) if isinstance(items, list) else []

    @property
    def total(self) -> int | None:
        total = self._payload.get("total")
        return int(total) if isinstance(total, (int, float)) else None

    @property
    def next_url(self) -> str | None:
        nxt = self._payload.get("next")
        return str(nxt) if nxt else None

    @property
    def prev_url(self) -> str | None:
        prev = self._payload.get("prev")
        return str(prev) if prev else None

    @property
    def checksum(self) -> str | None:
        checksum = self._payload.get("checksum")
        return str(checksum) if checksum else None

    @property
    def raw(self) -> dict[str, Any]:
        return self._payload

    # -- dunder sugar ----------------------------------------------------
    def __iter__(self) -> Iterator[T]:
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, index: int) -> T:
        return self.data[index]

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"PaginatedList(data={len(self)}, total={self.total})"

    # -- navigation ------------------------------------------------------
    def _require_fetch(self) -> Callable[[str], dict[str, Any]]:
        if self._fetch is None:
            raise TypeError("This PaginatedList has no fetcher; cannot walk pages.")
        return self._fetch

    def iter_all_pages(self) -> Iterator["PaginatedList[T]"]:
        """Yield this page, then every following page via ``next`` links."""
        fetch = self._require_fetch()
        page: PaginatedList[T] | None = self
        while page is not None:
            yield page
            nxt = page.next_url
            page = PaginatedList(fetch(nxt), fetch=fetch) if nxt else None

    def iter_all_items(self) -> Iterator[T]:
        """Yield every item across this and all following pages."""
        for page in self.iter_all_pages():
            yield from page

    def fetch_next(self) -> "PaginatedList[T] | None":
        """Fetch the page pointed at by ``next`` (``None`` when absent)."""
        nxt = self.next_url
        if not nxt:
            return None
        return PaginatedList(self._require_fetch()(nxt), fetch=self._fetch)

    def fetch_prev(self) -> "PaginatedList[T] | None":
        prev = self.prev_url
        if not prev:
            return None
        return PaginatedList(self._require_fetch()(prev), fetch=self._fetch)
