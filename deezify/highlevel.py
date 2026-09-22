"""High-level convenience methods shared by both clients.

Sync client: helpers run directly and return values.
Async client: ``AsyncDeezerClient`` overrides every helper with an async
variant (see ``client.py``), so ``await client.find_track(...)`` works while
the sync ``client.find_track(...)`` stays sync. This module holds the sync
implementations plus the small pieces the async overrides reuse.
"""

from __future__ import annotations

from typing import Any

from .paginator import PaginatedList

UserId = int | str


class HighLevelMixin:
    """Friendly shortcuts combining several low-level calls (sync)."""

    # -- search shortcuts ----------------------------------------------------
    def find_track(self, query: str, *, limit: int = 5) -> list:
        """Top ``limit`` tracks for ``query`` as a plain list."""
        return list(self.search.tracks(query, limit=limit))[:limit]

    def find_album(self, query: str, *, limit: int = 5) -> list:
        """Top ``limit`` albums for ``query`` as a plain list."""
        return list(self.search.albums(query, limit=limit))[:limit]

    def find_artist(self, query: str, *, limit: int = 5) -> list:
        """Top ``limit`` artists for ``query`` as a plain list."""
        return list(self.search.artists(query, limit=limit))[:limit]

    def find_playlist(self, query: str, *, limit: int = 5) -> list:
        """Top ``limit`` playlists for ``query`` as a plain list."""
        return list(self.search.playlists(query, limit=limit))[:limit]

    def find_podcast(self, query: str, *, limit: int = 5) -> list:
        """Top ``limit`` podcasts for ``query`` as a plain list."""
        return list(self.search.podcasts(query, limit=limit))[:limit]

    def best_track_match(self, query: str) -> dict | None:
        """First track result for ``query`` (``None`` when empty)."""
        items = self.find_track(query, limit=1)
        return items[0] if items else None

    def best_album_match(self, query: str) -> dict | None:
        """First album result for ``query`` (``None`` when empty)."""
        items = self.find_album(query, limit=1)
        return items[0] if items else None

    def best_artist_match(self, query: str) -> dict | None:
        """First artist result for ``query`` (``None`` when empty)."""
        items = self.find_artist(query, limit=1)
        return items[0] if items else None

    # -- artist shortcuts ------------------------------------------------------
    def artist_top_tracks(self, artist_id: int, *, limit: int = 10) -> list:
        """Top tracks of an artist as a plain list."""
        return list(self.artist.top(artist_id, limit=limit))[:limit]

    def artist_albums(self, artist_id: int, *, limit: int = 25) -> list:
        """Albums of an artist as a plain list."""
        return list(self.artist.albums(artist_id, limit=limit))[:limit]

    def artist_related(self, artist_id: int, *, limit: int = 10) -> list:
        """Related artists as a plain list."""
        return list(self.artist.related(artist_id, limit=limit))[:limit]

    def artist_radio_tracks(self, artist_id: int, *, limit: int = 25) -> list:
        """Artist radio tracks as a plain list."""
        return list(self.artist.radio(artist_id, limit=limit))[:limit]

    # -- album / playlist / radio shortcuts --------------------------------------
    def album_tracks(self, album_id: int) -> list:
        """Every track of an album (albums fit on one page)."""
        return list(self.album.tracks(album_id))

    def playlist_tracks(self, playlist_id: int, *, limit: int | None = None) -> list:
        """Tracks of a playlist as a plain list (``limit`` caps the result)."""
        items = list(self.playlist.tracks(playlist_id, limit=limit or 100))
        return items if limit is None else items[:limit]

    def playlist_all_tracks(self, playlist_id: int) -> list:
        """Every track of a playlist, walking all pages."""
        return list(self.playlist.tracks(playlist_id).iter_all_items())

    def radio_tracks(self, radio_id: int, *, limit: int = 25) -> list:
        """Tracks of a radio as a plain list."""
        return list(self.radio.tracks(radio_id, limit=limit))[:limit]

    def podcast_episodes(self, podcast_id: int, *, limit: int = 25) -> list:
        """Latest episodes of a podcast as a plain list."""
        return list(self.podcast.episodes(podcast_id, limit=limit))[:limit]

    # -- chart / editorial / genre shortcuts ---------------------------------------
    def top_tracks(self, *, limit: int = 10) -> list:
        """Global top tracks as a plain list."""
        return list(self.chart.tracks(limit=limit))[:limit]

    def top_albums(self, *, limit: int = 10) -> list:
        """Global top albums as a plain list."""
        return list(self.chart.albums(limit=limit))[:limit]

    def top_artists(self, *, limit: int = 10) -> list:
        """Global top artists as a plain list."""
        return list(self.chart.artists(limit=limit))[:limit]

    def top_playlists(self, *, limit: int = 10) -> list:
        """Global top playlists as a plain list."""
        return list(self.chart.playlists(limit=limit))[:limit]

    def top_podcasts(self, *, limit: int = 10) -> list:
        """Global top podcasts as a plain list."""
        return list(self.chart.podcasts(limit=limit))[:limit]

    def genre_top_tracks(self, genre_id: int, *, limit: int = 10) -> list:
        """Top tracks of a genre as a plain list."""
        return list(self.chart.tracks(genre_id, limit=limit))[:limit]

    def genres(self, *, limit: int = 50) -> list:
        """All genres as a plain list."""
        return list(self.genre.list(limit=limit))[:limit]

    def new_releases(self, *, limit: int = 10) -> list:
        """Editorial new releases as a plain list."""
        return list(self.editorial.releases(limit=limit))[:limit]

    def editorial_selection(self, *, limit: int = 10) -> list:
        """Weekly editorial album picks as a plain list."""
        return list(self.editorial.selection(limit=limit))[:limit]

    # -- track enrichment ------------------------------------------------------------
    def full_track(self, track_id: int) -> dict:
        """Track plus its full album and artist objects in one dict."""
        track = self.track.get(track_id)
        out: dict[str, Any] = {"track": track}
        album = (track.get("album") or {}) if isinstance(track, dict) else {}
        artist = (track.get("artist") or {}) if isinstance(track, dict) else {}
        if album.get("id"):
            try:
                out["album"] = self.album.get(album["id"])
            except Exception:
                out["album"] = album
        if artist.get("id"):
            try:
                out["artist"] = self.artist.get(artist["id"])
            except Exception:
                out["artist"] = artist
        return out

    def full_album(self, album_id: int) -> dict:
        """Album plus its artist object: ``{"album": ..., "artist": ...}``."""
        album = self.album.get(album_id)
        out: dict[str, Any] = {"album": album}
        artist = (album.get("artist") or {}) if isinstance(album, dict) else {}
        if artist.get("id"):
            try:
                out["artist"] = self.artist.get(artist["id"])
            except Exception:
                out["artist"] = artist
        return out

    def track_preview_url(self, track_id: int) -> str | None:
        """30-second preview MP3 URL of a track (``None`` when absent)."""
        track = self.track.get(track_id)
        return track.get("preview") if isinstance(track, dict) else None

    # -- user shortcuts (need access token) ----------------------------------------------
    def me(self) -> dict:
        """Authenticated user's profile (``GET /user/me``)."""
        return self.user.me()

    def my_playlists(self, *, limit: int = 25) -> list:
        """Authenticated user's playlists as a plain list."""
        return list(self.user.playlists("me", limit=limit))[:limit]

    def my_favorite_tracks(self, *, limit: int = 25) -> list:
        """Authenticated user's favorite tracks as a plain list."""
        return list(self.user.tracks("me", limit=limit))[:limit]

    def my_favorite_albums(self, *, limit: int = 25) -> list:
        """Authenticated user's favorite albums as a plain list."""
        return list(self.user.albums("me", limit=limit))[:limit]

    def my_favorite_artists(self, *, limit: int = 25) -> list:
        """Authenticated user's favorite artists as a plain list."""
        return list(self.user.artists("me", limit=limit))[:limit]

    def my_flow(self, *, limit: int = 25) -> list:
        """Authenticated user's Flow tracks as a plain list."""
        return list(self.user.flow("me", limit=limit))[:limit]

    def create_playlist(self, title: str, user_id: UserId = "me") -> dict:
        """Create a playlist for ``user_id`` (default: token owner)."""
        return self.user.create_playlist(user_id, title)

    def add_to_playlist(self, playlist_id: int, track_ids: list[int] | int) -> bool:
        """Append track(s) to a playlist."""
        return self.playlist.add_tracks(playlist_id, track_ids)
