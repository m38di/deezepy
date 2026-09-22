"""User resource — https://developers.deezer.com/api/user.

``user_id`` may be a numeric id or ``"me"`` (the access-token owner).
"""

from __future__ import annotations

from typing import Any

from .base import Resource
from ..enums import RecommendationKind, UserChartKind
from ..paginator import PaginatedList
from ..types import (
    Album, Artist, CreatePlaylistResult, Options, Playlist, Podcast, Radio,
    Track, User, WriteResult,
)

UserId = int | str


class UserResource(Resource):
    """Read profiles, favorites, flow, history and manage relationships."""

    def get(self, user_id: UserId = "me", **params: Any) -> User:
        """Fetch a user profile (``GET /user/{id}``)."""
        return self._get(f"user/{user_id}", params=params or None)

    def me(self, **params: Any) -> User:
        """Fetch the access-token owner's profile (``GET /user/me``)."""
        return self.get("me", **params)

    # -- generic connection helper --------------------------------------
    def _conn(
        self, user_id: UserId, name: str, *, index: int | None, limit: int | None
    ) -> PaginatedList[Any]:
        return self._paginated(
            f"user/{user_id}/{name}", params=self._page(None, index, limit)
        )

    def albums(self, user_id: UserId = "me", *, index=None, limit=None) -> PaginatedList[Album]:
        """Favorite albums (``GET /user/{id}/albums``)."""
        return self._conn(user_id, "albums", index=index, limit=limit)

    def artists(self, user_id: UserId = "me", *, index=None, limit=None) -> PaginatedList[Artist]:
        """Favorite artists (``GET /user/{id}/artists``)."""
        return self._conn(user_id, "artists", index=index, limit=limit)

    def tracks(self, user_id: UserId = "me", *, index=None, limit=None) -> PaginatedList[Track]:
        """Favorite tracks (``GET /user/{id}/tracks``)."""
        return self._conn(user_id, "tracks", index=index, limit=limit)

    def playlists(self, user_id: UserId = "me", *, index=None, limit=None) -> PaginatedList[Playlist]:
        """Playlists incl. private ones with permission (``GET /user/{id}/playlists``)."""
        return self._conn(user_id, "playlists", index=index, limit=limit)

    def podcasts(self, user_id: UserId = "me", *, index=None, limit=None) -> PaginatedList[Podcast]:
        """Favorite podcasts (``GET /user/{id}/podcasts``)."""
        return self._conn(user_id, "podcasts", index=index, limit=limit)

    def radios(self, user_id: UserId = "me", *, index=None, limit=None) -> PaginatedList[Radio]:
        """Favorite radios (``GET /user/{id}/radios``)."""
        return self._conn(user_id, "radios", index=index, limit=limit)

    def followings(self, user_id: UserId = "me", *, index=None, limit=None) -> PaginatedList[User]:
        """Users this user follows (``GET /user/{id}/followings``)."""
        return self._conn(user_id, "followings", index=index, limit=limit)

    def followers(self, user_id: UserId = "me", *, index=None, limit=None) -> PaginatedList[User]:
        """Followers of this user (``GET /user/{id}/followers``)."""
        return self._conn(user_id, "followers", index=index, limit=limit)

    def flow(self, user_id: UserId = "me", *, index=None, limit=None) -> PaginatedList[Track]:
        """Flow tracks (``GET /user/{id}/flow``)."""
        return self._conn(user_id, "flow", index=index, limit=limit)

    def history(self, user_id: UserId = "me", *, index=None, limit=None) -> PaginatedList[Track]:
        """Recently played tracks, needs ``listening_history``
        (``GET /user/{id}/history``)."""
        return self._conn(user_id, "history", index=index, limit=limit)

    def personal_songs(
        self, user_id: UserId = "me", *, index=None, limit=None
    ) -> PaginatedList[Track]:
        """Uploaded personal songs (``GET /user/{id}/personal_songs``)."""
        return self._conn(user_id, "personal_songs", index=index, limit=limit)

    def charts_albums(self, user_id: UserId = "me", **params: Any) -> Any:
        """``GET /user/{id}/charts/albums``."""
        return self._get(f"user/{user_id}/charts/albums", params=params or None)

    def charts_playlists(self, user_id: UserId = "me", **params: Any) -> Any:
        """``GET /user/{id}/charts/playlists``."""
        return self._get(f"user/{user_id}/charts/playlists", params=params or None)

    def charts_tracks(self, user_id: UserId = "me", **params: Any) -> Any:
        """``GET /user/{id}/charts/tracks``."""
        return self._get(f"user/{user_id}/charts/tracks", params=params or None)

    def recommendations(self, user_id: UserId = "me", kind: str | RecommendationKind = "tracks", **params: Any) -> Any:
        """Recommendations feed (``GET /user/{id}/recommendations/{kind}``).

        ``kind`` accepts a raw string or :class:`~deezify.enums.RecommendationKind`.
        """
        kind_str = RecommendationKind.coerce(kind, label="recommendation kind")
        return self._get(f"user/{user_id}/recommendations/{kind_str}", params=params or None)

    def user_chart(self, user_id: UserId = "me", kind: str | UserChartKind = "tracks", **params: Any) -> Any:
        """User chart feed (``GET /user/{id}/charts/{kind}``).

        ``kind`` accepts a raw string or :class:`~deezify.enums.UserChartKind`.
        """
        kind_str = UserChartKind.coerce(kind, label="user chart kind")
        return self._get(f"user/{user_id}/charts/{kind_str}", params=params or None)

    def permissions(self, user_id: UserId = "me") -> Any:
        """Permissions granted to the app (``GET /user/{id}/permissions``)."""
        return self._get(f"user/{user_id}/permissions")

    def options(self, user_id: UserId = "me", **params: Any) -> Options:
        """Alias of ``/options`` (``GET /user/{id}/options``)."""
        return self._get(f"user/{user_id}/options", params=params or None)

    # -- write actions ----------------------------------------------------
    def create_playlist(self, user_id: UserId, title: str) -> CreatePlaylistResult:
        """Create a playlist (``POST /user/{id}/playlists``, ``title=...``)."""
        if not title or not title.strip():
            raise ValueError("title must be a non-empty string")
        return self._post(f"user/{user_id}/playlists", data={"title": title})

    def follow(self, user_id: UserId, target_user_id: int) -> WriteResult:
        """Follow a user (``POST /user/{id}/followings``)."""
        return bool(
            self._post(
                f"user/{user_id}/followings", data={"user_id": str(target_user_id)}
            )
        )

    def unfollow(self, user_id: UserId, target_user_id: int) -> WriteResult:
        """Unfollow a user (``DELETE /user/{id}/followings``)."""
        return bool(
            self._delete(
                f"user/{user_id}/followings", params={"user_id": target_user_id}
            )
        )

    def add_notification(self, user_id: UserId, message: str) -> Any:
        """Push a notification into the user feed
        (``POST /user/{id}/notifications``)."""
        return self._post(f"user/{user_id}/notifications", data={"message": message})

