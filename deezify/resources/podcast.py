"""Podcast + episode resources.

- https://developers.deezer.com/api/podcast
- https://developers.deezer.com/api/episode
"""

from __future__ import annotations

from typing import Any

from .base import Resource
from ..paginator import PaginatedList
from ..types import Bookmark, Episode, Podcast, WriteResult


class PodcastResource(Resource):
    """Read podcasts and manage podcast favorites."""

    def get(self, podcast_id: int, **params: Any) -> Podcast:
        """Fetch one podcast by id (``GET /podcast/{id}``)."""
        return self._get(f"podcast/{podcast_id}", params=params or None)

    def episodes(
        self, podcast_id: int, *, index: int | None = None, limit: int | None = None
    ) -> PaginatedList[Episode]:
        """Episodes of the podcast (``GET /podcast/{id}/episodes``)."""
        return self._paginated(
            f"podcast/{podcast_id}/episodes", params=self._page(None, index, limit)
        )

    def add_favorite(self, user_id: int | str, podcast_id: int) -> WriteResult:
        """Add a podcast to favorites (``POST /user/{id}/podcasts``)."""
        return bool(
            self._post(
                f"user/{user_id}/podcasts", data={"podcast_id": str(podcast_id)}
            )
        )

    def remove_favorite(self, user_id: int | str, podcast_id: int) -> WriteResult:
        """Remove a podcast from favorites (``DELETE /user/{id}/podcasts``)."""
        return bool(
            self._delete(
                f"user/{user_id}/podcasts", params={"podcast_id": podcast_id}
            )
        )


class EpisodeResource(Resource):
    """Read episodes and manage bookmarks (offset 0–100)."""

    def get(self, episode_id: int, **params: Any) -> Episode:
        """Fetch one episode by id (``GET /episode/{id}``)."""
        return self._get(f"episode/{episode_id}", params=params or None)

    def bookmark_info(self, episode_id: int) -> Bookmark:
        """Current bookmark (``GET /episode/{id}/bookmark``)."""
        return self._get(f"episode/{episode_id}/bookmark")

    def set_bookmark(self, episode_id: int, offset: int) -> WriteResult:
        """Set a bookmark (``POST /episode/{id}/bookmark``, offset 0–100)."""
        if not 0 <= offset <= 100:
            raise ValueError("offset must be between 0 and 100")
        return bool(
            self._post(f"episode/{episode_id}/bookmark", data={"offset": str(offset)})
        )

    def remove_bookmark(self, episode_id: int) -> WriteResult:
        """Remove the bookmark (``DELETE /episode/{id}/bookmark``)."""
        return bool(self._delete(f"episode/{episode_id}/bookmark"))
