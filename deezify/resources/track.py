"""Track resource — https://developers.deezer.com/api/track."""

from __future__ import annotations

from typing import Any

from .base import Resource


class TrackResource(Resource):
    """Read tracks and manage personal tracks / playlist membership."""

    def get(self, track_id: int, **params: Any) -> Track:
        """Fetch one track by id (``GET /track/{id}``)."""
        return self._get(f"track/{track_id}", params=params or None)

    # -- personal tracks -------------------------------------------------
    def update_personal(self, track_id: int, **fields: Any) -> WriteResult:
        """Update a personal (uploaded) track (``POST /track/{id}``)."""
        return bool(self._post(f"track/{track_id}", data=fields or None))

    def delete_personal(self, track_id: int) -> WriteResult:
        """Delete a personal track (``DELETE /track/{id}``)."""
        return bool(self._delete(f"track/{track_id}"))

    # -- favorites -------------------------------------------------------
    def add_favorite(self, user_id: int | str, track_ids: list[int] | int) -> WriteResult:
        """Add track(s) to favorites (``POST /user/{id}/tracks``)."""
        ids = track_ids if isinstance(track_ids, list) else [track_ids]
        return bool(
            self._post(
                f"user/{user_id}/tracks", data={"track_id": ",".join(map(str, ids))}
            )
        )

    def remove_favorite(self, user_id: int | str, track_id: int) -> WriteResult:
        """Remove a track from favorites (``DELETE /user/{id}/tracks``)."""
        return bool(
            self._delete(f"user/{user_id}/tracks", params={"track_id": track_id})
        )
