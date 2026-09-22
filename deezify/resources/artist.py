"""Artist resource — https://developers.deezer.com/api/artist."""

from __future__ import annotations

from typing import Any

from .base import Resource
from ..paginator import PaginatedList
from ..types import Album, Artist, Playlist, Track, User, WriteResult


class ArtistResource(Resource):
    """Read an artist and every documented ``artist/*`` connection."""

    def get(self, artist_id: int, **params: Any) -> Artist:
        """Fetch one artist by id (``GET /artist/{id}``)."""
        return self._get(f"artist/{artist_id}", params=params or None)

    def top(
        self, artist_id: int, *, index: int | None = None, limit: int | None = None
    ) -> PaginatedList[Track]:
        """Top tracks of the artist (``GET /artist/{id}/top``)."""
        return self._paginated(
            f"artist/{artist_id}/top", params=self._page(None, index, limit)
        )

    def albums(
        self, artist_id: int, *, index: int | None = None, limit: int | None = None
    ) -> PaginatedList[Album]:
        """Albums of the artist (``GET /artist/{id}/albums``)."""
        return self._paginated(
            f"artist/{artist_id}/albums", params=self._page(None, index, limit)
        )

    def fans(
        self, artist_id: int, *, index: int | None = None, limit: int | None = None
    ) -> PaginatedList[User]:
        """Fans of the artist (``GET /artist/{id}/fans``)."""
        return self._paginated(
            f"artist/{artist_id}/fans", params=self._page(None, index, limit)
        )

    def related(
        self, artist_id: int, *, index: int | None = None, limit: int | None = None
    ) -> PaginatedList[Artist]:
        """Related artists (``GET /artist/{id}/related``)."""
        return self._paginated(
            f"artist/{artist_id}/related", params=self._page(None, index, limit)
        )

    def radio(
        self, artist_id: int, *, index: int | None = None, limit: int | None = None
    ) -> PaginatedList[Track]:
        """Artist radio tracks (``GET /artist/{id}/radio``)."""
        return self._paginated(
            f"artist/{artist_id}/radio", params=self._page(None, index, limit)
        )

    def playlists(
        self, artist_id: int, *, index: int | None = None, limit: int | None = None
    ) -> PaginatedList[Playlist]:
        """Playlists featuring the artist (``GET /artist/{id}/playlists``)."""
        return self._paginated(
            f"artist/{artist_id}/playlists", params=self._page(None, index, limit)
        )

    # -- favorites (need ``manage_library`` / ``delete_library``) -----------
    def add_favorite(self, user_id: int | str, artist_ids: list[int] | int) -> WriteResult:
        """Add artist(s) to favorites (``POST /user/{id}/artists``)."""
        ids = artist_ids if isinstance(artist_ids, list) else [artist_ids]
        return bool(
            self._post(
                f"user/{user_id}/artists", data={"artist_id": ",".join(map(str, ids))}
            )
        )

    def remove_favorite(self, user_id: int | str, artist_id: int) -> WriteResult:
        """Remove an artist from favorites (``DELETE /user/{id}/artists``)."""
        return bool(
            self._delete(f"user/{user_id}/artists", params={"artist_id": artist_id})
        )
