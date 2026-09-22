"""Search resource — https://developers.deezer.com/api/search.

Supports plain search, per-type search, advanced field syntax
(``artist:"..." album:"..." track:"..." label:"..." dur_min:...`` etc.),
``strict`` fuzzy toggle and ``order`` sorting.
"""

from __future__ import annotations

from typing import Any

from .base import Resource
from ..paginator import PaginatedList
from ..enums import SearchField, SearchOrder, coerce_optional_enum
from ..types import Album, Artist, Playlist, Podcast, Radio, Track, User

#: Back-compat tuple; prefer :class:`~deezify.enums.SearchOrder`.
ORDER_VALUES = tuple(SearchOrder.values())

#: Back-compat tuple; prefer :class:`~deezify.enums.SearchField`.
ADVANCED_FIELDS = tuple(SearchField.values())



def build_advanced_query(**fields: Any) -> str:
    """Build an advanced-search ``q`` string from field keywords.

    String values containing spaces are quoted, e.g.
    ``build_advanced_query(artist="Aloe Blacc", track="I Need A Dollar")`` →
    ``'artist:"Aloe Blacc" track:"I Need A Dollar"'``.
    """
    parts: list[str] = []
    for key, value in fields.items():
        if value is None:
            continue
        name = SearchField.coerce(key.lower(), label="advanced-search field")
        text = str(value)
        if isinstance(value, str) and (" " in text or '"' in text):
            text = '"{}"'.format(text.replace('"', ""))
        parts.append(f"{name}:{text}")
    return " ".join(parts)


class SearchResource(Resource):
    """Full-text and advanced search across the Deezer catalogue."""

    def _search(
        self,
        path: str,
        query: str,
        *,
        strict: bool | None = None,
        order: str | SearchOrder | None = None,
        index: int | None = None,
        limit: int | None = None,
    ) -> PaginatedList[Track]:
        if not query or not query.strip():
            raise ValueError("query must be a non-empty string")
        order_str = coerce_optional_enum(SearchOrder, order, label="order")
        params: dict[str, Any] = {"q": query}
        if strict is not None:
            params["strict"] = "on" if strict else "off"
        if order_str is not None:
            params["order"] = order_str
        return self._paginated(path, params=self._page(params, index, limit))

    def all(
        self, query: str, *, strict: bool | None = None,
        order: str | SearchOrder | None = None,
        index: int | None = None, limit: int | None = None,
    ) -> PaginatedList[Track]:
        """Cross-type search (``GET /search?q=...``)."""
        return self._search("search", query, strict=strict, order=order,
                            index=index, limit=limit)

    def tracks(self, query: str, **kwargs: Any) -> PaginatedList[Track]:
        """Search tracks (``GET /search/track?q=...``)."""
        return self._search("search/track", query, **kwargs)

    def albums(self, query: str, **kwargs: Any) -> PaginatedList[Album]:
        """Search albums (``GET /search/album?q=...``)."""
        return self._search("search/album", query, **kwargs)

    def artists(self, query: str, **kwargs: Any) -> PaginatedList[Artist]:
        """Search artists (``GET /search/artist?q=...``)."""
        return self._search("search/artist", query, **kwargs)

    def playlists(self, query: str, **kwargs: Any) -> PaginatedList[Playlist]:
        """Search playlists (``GET /search/playlist?q=...``)."""
        return self._search("search/playlist", query, **kwargs)

    def podcasts(self, query: str, **kwargs: Any) -> PaginatedList[Podcast]:
        """Search podcasts (``GET /search/podcast?q=...``)."""
        return self._search("search/podcast", query, **kwargs)

    def radios(self, query: str, **kwargs: Any) -> PaginatedList[Radio]:
        """Search radios (``GET /search/radio?q=...``)."""
        return self._search("search/radio", query, **kwargs)

    def users(self, query: str, **kwargs: Any) -> PaginatedList[User]:
        """Search users (``GET /search/user?q=...``)."""
        return self._search("search/user", query, **kwargs)

    def advanced(self, path: str = "search", *, strict: bool | None = None,
                 order: str | SearchOrder | None = None, index: int | None = None,
                 limit: int | None = None, **fields: Any) -> PaginatedList[Track]:
        """Advanced field search, e.g. ``advanced(artist="Daft Punk")``.

        ``path`` may be ``"search"`` or any ``"search/<type>"`` endpoint.
        """
        return self._search(path, build_advanced_query(**fields), strict=strict,
                            order=order, index=index, limit=limit)

    def history(
        self, *, index: int | None = None, limit: int | None = None
    ) -> PaginatedList[Track]:
        """Authenticated user's search history (``GET /search/history``)."""
        return self._paginated(
            "search/history", params=self._page(None, index, limit)
        )

