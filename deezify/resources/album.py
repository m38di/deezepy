"""Album resource — https://developers.deezer.com/api/album."""

from __future__ import annotations

from typing import Any

from .base import Resource
from ..paginator import PaginatedList
from ..types import Album, AlbumTrack, User, WriteResult


class AlbumResource(Resource):
    """Read an album and its connections; manage it in the user library."""

    def get(self, album_id: int, **params: Any) -> Album:
        """Fetch one album by id (``GET /album/{id}``)."""
        return self._get(f"album/{album_id}", params=params or None)

    def fans(
        self, album_id: int, *, index: int | None = None, limit: int | None = None
    ) -> PaginatedList[User]:
        """Fans of the album (``GET /album/{id}/fans``)."""
        return self._paginated(
            f"album/{album_id}/fans", params=self._page(None, index, limit)
        )

    def tracks(
        self, album_id: int, *, index: int | None = None, limit: int | None = None
    ) -> PaginatedList[AlbumTrack]:
        """Tracks of the album (``GET /album/{id}/tracks``)."""
        return self._paginated(
            f"album/{album_id}/tracks", params=self._page(None, index, limit)
        )

    # -- library actions (need ``manage_library`` / ``delete_library``) ----
    def add_to_library(self, user_id: int | str, album_ids: list[int] | int) -> WriteResult:
        """Add album(s) to a user's library (``POST /user/{id}/albums``)."""
        ids = album_ids if isinstance(album_ids, list) else [album_ids]
        return bool(
            self._post(
                f"user/{user_id}/albums", data={"album_id": ",".join(map(str, ids))}
            )
        )

    def remove_from_library(self, user_id: int | str, album_id: int) -> WriteResult:
        """Remove an album from a user's library (``DELETE /user/{id}/albums``)."""
        return bool(
            self._delete(f"user/{user_id}/albums", params={"album_id": album_id})
        )
