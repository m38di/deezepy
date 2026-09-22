"""Playlist resource — https://developers.deezer.com/api/playlist."""

from __future__ import annotations

from typing import Any

from .base import Resource
from ..paginator import PaginatedList
from ..types import AlbumTrack, Playlist, User, WriteResult

_ORDER_MODES = ("track_asc", "track_desc")


class PlaylistResource(Resource):
    """Read playlists and manage their tracks."""

    def get(self, playlist_id: int, **params: Any) -> Playlist:
        """Fetch one playlist by id (``GET /playlist/{id}``)."""
        return self._get(f"playlist/{playlist_id}", params=params or None)

    def fans(
        self, playlist_id: int, *, index: int | None = None, limit: int | None = None
    ) -> PaginatedList[User]:
        """Fans of the playlist (``GET /playlist/{id}/fans``)."""
        return self._paginated(
            f"playlist/{playlist_id}/fans", params=self._page(None, index, limit)
        )

    def tracks(
        self, playlist_id: int, *, index: int | None = None, limit: int | None = None
    ) -> PaginatedList[AlbumTrack]:
        """Tracks of the playlist (``GET /playlist/{id}/tracks``)."""
        return self._paginated(
            f"playlist/{playlist_id}/tracks", params=self._page(None, index, limit)
        )

    def radio(
        self, playlist_id: int, *, index: int | None = None, limit: int | None = None
    ) -> PaginatedList[Track]:
        """Recommended tracks for the playlist (``GET /playlist/{id}/radio``)."""
        return self._paginated(
            f"playlist/{playlist_id}/radio", params=self._page(None, index, limit)
        )

    # -- write actions (need ``manage_library`` / ``delete_library``) ------
    def update(self, playlist_id: int, **fields: Any) -> WriteResult:
        """Update playlist attributes such as title/description
        (``POST /playlist/{id}``)."""
        return bool(self._post(f"playlist/{playlist_id}", data=fields or None))

    def delete(self, playlist_id: int) -> WriteResult:
        """Delete a playlist (``DELETE /playlist/{id}``)."""
        return bool(self._delete(f"playlist/{playlist_id}"))

    def mark_seen(self, playlist_id: int) -> WriteResult:
        """Mark a playlist as seen (``POST /playlist/{id}/seen``)."""
        return bool(self._post(f"playlist/{playlist_id}/seen"))

    def add_tracks(self, playlist_id: int, track_ids: list[int] | int) -> WriteResult:
        """Append tracks (``POST /playlist/{id}/tracks``, ``songs=...``)."""
        ids = track_ids if isinstance(track_ids, list) else [track_ids]
        return bool(
            self._post(
                f"playlist/{playlist_id}/tracks",
                data={"songs": ",".join(map(str, ids))},
            )
        )

    def reorder_tracks(self, playlist_id: int, track_ids: list[int]) -> WriteResult:
        """Reorder tracks (``POST /playlist/{id}/tracks``, ``order=...``)."""
        return bool(
            self._post(
                f"playlist/{playlist_id}/tracks",
                data={"order": ",".join(map(str, track_ids))},
            )
        )

    def remove_tracks(self, playlist_id: int, track_ids: list[int] | int) -> WriteResult:
        """Remove tracks (``DELETE /playlist/{id}/tracks``, ``songs=...``)."""
        ids = track_ids if isinstance(track_ids, list) else [track_ids]
        return bool(
            self._delete(
                f"playlist/{playlist_id}/tracks",
                params={"songs": ",".join(map(str, ids))},
            )
        )

    # -- favorite playlists ------------------------------------------------
    def add_favorite(self, user_id: int | str, playlist_ids: list[int] | int) -> WriteResult:
        """Add playlist(s) to favorites (``POST /user/{id}/playlists``)."""
        ids = playlist_ids if isinstance(playlist_ids, list) else [playlist_ids]
        return bool(
            self._post(
                f"user/{user_id}/playlists",
                data={"playlist_id": ",".join(map(str, ids))},
            )
        )

    def remove_favorite(self, user_id: int | str, playlist_id: int) -> WriteResult:
        """Remove a playlist from favorites (``DELETE /user/{id}/playlists``)."""
        return bool(
            self._delete(
                f"user/{user_id}/playlists", params={"playlist_id": playlist_id}
            )
        )

    def order(self, *args: Any, **kwargs: Any) -> bool:  # pragma: no cover
        raise NotImplementedError(
            "Use reorder_tracks(playlist_id, track_ids) instead."
        )

    order_modes = tuple(_ORDER_MODES)
