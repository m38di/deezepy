"""Sync + async Deezer clients exposing every documented resource."""

from __future__ import annotations

from typing import Any

import httpx

from .http import API_BASE_URL, DEFAULT_TIMEOUT, AsyncTransport, SyncTransport
from .ratelimit import AsyncRateLimiter, SyncRateLimiter
from .highlevel import HighLevelMixin
from .oauth import TOKEN_URL, parse_token_response
from .paginator import PaginatedList
from .resources import (
    AlbumResource,
    ArtistResource,
    ChartResource,
    EditorialResource,
    EpisodeResource,
    GenreResource,
    InfosResource,
    OEmbedResource,
    OptionsResource,
    PlaylistResource,
    PodcastResource,
    RadioResource,
    SearchResource,
    TrackResource,
    UserResource,
)


class BaseClient(HighLevelMixin):
    """Shared configuration for :class:`DeezerClient` / :class:`AsyncDeezerClient`."""

    def __init__(
        self,
        *,
        access_token: str | None = None,
        base_url: str = API_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        user_agent: str | None = None,
    ) -> None:
        self.access_token = access_token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.user_agent = user_agent

        self.album = AlbumResource(self)
        self.artist = ArtistResource(self)
        self.track = TrackResource(self)
        self.playlist = PlaylistResource(self)
        self.podcast = PodcastResource(self)
        self.episode = EpisodeResource(self)
        self.user = UserResource(self)
        self.chart = ChartResource(self)
        self.editorial = EditorialResource(self)
        self.genre = GenreResource(self)
        self.radio = RadioResource(self)
        self.search = SearchResource(self)
        self.oembed = OEmbedResource(self)
        self.infos = InfosResource(self)
        self.options = OptionsResource(self)

    # -- implemented by subclasses ---------------------------------------
    def _get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        raise NotImplementedError

    def _post(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> Any:
        raise NotImplementedError

    def _delete(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        raise NotImplementedError

    def _fetch_url(self, url: str) -> dict[str, Any]:
        raise NotImplementedError


class DeezerClient(BaseClient):
    """Synchronous client (context-manager aware).

    Example:
        >>> client = DeezerClient(access_token="...")
        >>> track = client.track.get(3135556)
        >>> top = client.artist.top(27)
        >>> client.close()
    """

    def __init__(
        self,
        access_token: str | None = None,
        *,
        base_url: str = API_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        user_agent: str | None = None,
        http_client: httpx.Client | None = None,
        rate_limit: SyncRateLimiter | bool | None = None,
        max_retries: int = 3,
        retry_base: float = 0.5,
    ) -> None:
        super().__init__(
            access_token=access_token,
            base_url=base_url,
            timeout=timeout,
            user_agent=user_agent,
        )
        from .http import DEFAULT_USER_AGENT

        self._transport = SyncTransport(
            base_url=self.base_url,
            access_token=access_token,
            timeout=timeout,
            user_agent=user_agent or DEFAULT_USER_AGENT,
            client=http_client,
            rate_limiter=True if rate_limit is None else rate_limit,
            max_retries=max_retries,
            retry_base=retry_base,
        )

    # -- context manager ---------------------------------------------------
    def __enter__(self) -> "DeezerClient":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def close(self) -> None:
        self._transport.close()

    def set_access_token(self, token: str | None) -> None:
        """Replace the token used for subsequent requests."""
        self.access_token = token
        self._transport.access_token = token

    # -- transport passthrough ---------------------------------------------
    def _get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return self._transport.get(path, params=params)

    def _post(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> Any:
        return self._transport.post(path, params=params, data=data)

    def _delete(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return self._transport.delete(path, params=params)

    def _fetch_url(self, url: str) -> dict[str, Any]:
        from urllib.parse import parse_qsl, urlsplit

        from .http import _decode

        if url.startswith(self.base_url):
            # Keep the query string! e.g. ".../tracks?index=2&limit=2".
            # Stripping it caused infinite next-page loops.
            split = urlsplit(url)
            path = split.path
            query = dict(parse_qsl(split.query, keep_blank_values=True))
            params = query or None
            if path.startswith(("http://", "https://")):
                response = self._transport.client.get(url)
                return _decode(response, endpoint=url)
            return self._transport.get(path, params=params)
        if url.startswith(("http://", "https://")):
            response = self._transport.client.get(url)
            return _decode(response, endpoint=url)
        return self._transport.get(url)

    # -- raw access ----------------------------------------------------------
    def raw(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> Any:
        """Escape hatch for undocumented/experimental endpoints."""
        return self._transport.request(method, path, params=params, data=data)

    def get_page(self, page: PaginatedList) -> PaginatedList | None:
        """Fetch the next page of a :class:`PaginatedList` (sync)."""
        return page.fetch_next()


    # -- OAuth ---------------------------------------------------------------
    def exchange_code_for_token(
        self, app_id: str | int, secret: str, code: str, *, output: str = "json"
    ) -> dict:
        """Exchange a server-side-flow ``code`` for an access token.

        Returns the parsed token dict (``access_token``, ``expires``...).
        """
        from urllib.parse import urlencode

        query = urlencode(
            {"app_id": str(app_id), "secret": secret, "code": code, "output": output}
        )
        response = self._transport.client.get(f"{TOKEN_URL}?{query}")
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if output == "json" or "json" in content_type:
            try:
                data = response.json()
            except ValueError:
                data = parse_token_response(response.text)
        else:
            data = parse_token_response(response.text)
        if isinstance(data, dict):
            return data
        return {"access_token": data}


class AsyncDeezerClient(BaseClient):
    """Async client (async context-manager aware).

    Example:
        >>> async with AsyncDeezerClient() as client:
        ...     track = await client.track.get(3135556)
    """

    def __init__(
        self,
        access_token: str | None = None,
        *,
        base_url: str = API_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        user_agent: str | None = None,
        http_client: httpx.AsyncClient | None = None,
        rate_limit: AsyncRateLimiter | bool | None = None,
        max_retries: int = 3,
        retry_base: float = 0.5,
    ) -> None:
        # NOTE: resources call the sync-named hooks which we implement as
        # coroutines; async use goes through ``Async*`` proxy methods below.
        super().__init__(
            access_token=access_token,
            base_url=base_url,
            timeout=timeout,
            user_agent=user_agent,
        )
        from .http import DEFAULT_USER_AGENT

        self._transport = AsyncTransport(
            base_url=self.base_url,
            access_token=access_token,
            timeout=timeout,
            user_agent=user_agent or DEFAULT_USER_AGENT,
            client=http_client,
            rate_limiter=True if rate_limit is None else rate_limit,
            max_retries=max_retries,
            retry_base=retry_base,
        )
        self._bind_async_resources()

    # -- context manager ---------------------------------------------------
    async def __aenter__(self) -> "AsyncDeezerClient":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()

    async def close(self) -> None:
        await self._transport.close()

    def set_access_token(self, token: str | None) -> None:
        self.access_token = token
        self._transport.access_token = token

    # -- transport passthrough (coroutines) ----------------------------------
    async def _get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:  # type: ignore[override]
        return await self._transport.get(path, params=params)

    async def _post(  # type: ignore[override]
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> Any:
        return await self._transport.post(path, params=params, data=data)

    async def _delete(  # type: ignore[override]
        self, path: str, *, params: dict[str, Any] | None = None
    ) -> Any:
        return await self._transport.delete(path, params=params)

    async def _fetch_url(self, url: str) -> dict[str, Any]:  # type: ignore[override]
        from urllib.parse import parse_qsl, urlsplit

        from .http import _decode

        if url.startswith(self.base_url):
            # Keep the query string (see sync _fetch_url).
            split = urlsplit(url)
            path = split.path
            query = dict(parse_qsl(split.query, keep_blank_values=True))
            params = query or None
            if path.startswith(("http://", "https://")):
                response = await self._transport.client.get(url)
                return _decode(response, endpoint=url)
            return await self._transport.get(path, params=params)
        if url.startswith(("http://", "https://")):
            response = await self._transport.client.get(url)
            return _decode(response, endpoint=url)
        return await self._transport.get(url)

    # -- resource proxying ----------------------------------------------------
    # Resource methods are written sync-style against ``_get``/``_post``.
    # For the async client each resource method must be awaited *inside* the
    # resource (so ``_paginated`` receives data, not a coroutine). The proxy
    # below rewrites the resource's ``_client`` reference to an async shim
    # whose _get/_post/_delete/_fetch_url are coroutine functions, then
    # awaits the resource method itself.
    def _bind_async_resources(self) -> None:
        for name in (
            "album", "artist", "track", "playlist", "podcast", "episode",
            "user", "chart", "editorial", "genre", "radio", "search",
            "oembed", "infos", "options",
        ):
            setattr(self, name, _AsyncResourceProxy(getattr(self, name)))

    async def raw(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> Any:
        return await self._transport.request(method, path, params=params, data=data)

    # -- high-level helpers (async mirrors of HighLevelMixin) --------------------
    async def find_track(self, query: str, *, limit: int = 5) -> list:  # type: ignore[override]
        return list(await self.search.tracks(query, limit=limit))[:limit]

    async def find_album(self, query: str, *, limit: int = 5) -> list:  # type: ignore[override]
        return list(await self.search.albums(query, limit=limit))[:limit]

    async def find_artist(self, query: str, *, limit: int = 5) -> list:  # type: ignore[override]
        return list(await self.search.artists(query, limit=limit))[:limit]

    async def find_playlist(self, query: str, *, limit: int = 5) -> list:  # type: ignore[override]
        return list(await self.search.playlists(query, limit=limit))[:limit]

    async def find_podcast(self, query: str, *, limit: int = 5) -> list:  # type: ignore[override]
        return list(await self.search.podcasts(query, limit=limit))[:limit]

    async def best_track_match(self, query: str) -> dict | None:  # type: ignore[override]
        items = await self.find_track(query, limit=1)
        return items[0] if items else None

    async def best_album_match(self, query: str) -> dict | None:  # type: ignore[override]
        items = await self.find_album(query, limit=1)
        return items[0] if items else None

    async def best_artist_match(self, query: str) -> dict | None:  # type: ignore[override]
        items = await self.find_artist(query, limit=1)
        return items[0] if items else None

    async def artist_top_tracks(self, artist_id: int, *, limit: int = 10) -> list:  # type: ignore[override]
        return list(await self.artist.top(artist_id, limit=limit))[:limit]

    async def artist_albums(self, artist_id: int, *, limit: int = 25) -> list:  # type: ignore[override]
        return list(await self.artist.albums(artist_id, limit=limit))[:limit]

    async def artist_related(self, artist_id: int, *, limit: int = 10) -> list:  # type: ignore[override]
        return list(await self.artist.related(artist_id, limit=limit))[:limit]

    async def artist_radio_tracks(self, artist_id: int, *, limit: int = 25) -> list:  # type: ignore[override]
        return list(await self.artist.radio(artist_id, limit=limit))[:limit]

    async def album_tracks(self, album_id: int) -> list:  # type: ignore[override]
        return list(await self.album.tracks(album_id))

    async def playlist_tracks(self, playlist_id: int, *, limit: int | None = None) -> list:  # type: ignore[override]
        items = list(await self.playlist.tracks(playlist_id, limit=limit or 100))
        return items if limit is None else items[:limit]

    async def radio_tracks(self, radio_id: int, *, limit: int = 25) -> list:  # type: ignore[override]
        return list(await self.radio.tracks(radio_id, limit=limit))[:limit]

    async def podcast_episodes(self, podcast_id: int, *, limit: int = 25) -> list:  # type: ignore[override]
        return list(await self.podcast.episodes(podcast_id, limit=limit))[:limit]

    async def top_tracks(self, *, limit: int = 10) -> list:  # type: ignore[override]
        return list(await self.chart.tracks(limit=limit))[:limit]

    async def top_albums(self, *, limit: int = 10) -> list:  # type: ignore[override]
        return list(await self.chart.albums(limit=limit))[:limit]

    async def top_artists(self, *, limit: int = 10) -> list:  # type: ignore[override]
        return list(await self.chart.artists(limit=limit))[:limit]

    async def top_playlists(self, *, limit: int = 10) -> list:  # type: ignore[override]
        return list(await self.chart.playlists(limit=limit))[:limit]

    async def top_podcasts(self, *, limit: int = 10) -> list:  # type: ignore[override]
        return list(await self.chart.podcasts(limit=limit))[:limit]

    async def genre_top_tracks(self, genre_id: int, *, limit: int = 10) -> list:  # type: ignore[override]
        return list(await self.chart.tracks(genre_id, limit=limit))[:limit]

    async def genres(self, *, limit: int = 50) -> list:  # type: ignore[override]
        return list(await self.genre.list(limit=limit))[:limit]

    async def new_releases(self, *, limit: int = 10) -> list:  # type: ignore[override]
        return list(await self.editorial.releases(limit=limit))[:limit]

    async def editorial_selection(self, *, limit: int = 10) -> list:  # type: ignore[override]
        return list(await self.editorial.selection(limit=limit))[:limit]

    async def track_preview_url(self, track_id: int) -> str | None:  # type: ignore[override]
        track = await self.track.get(track_id)
        return track.get("preview") if isinstance(track, dict) else None

    async def me(self) -> dict:  # type: ignore[override]
        return await self.user.me()

    async def my_playlists(self, *, limit: int = 25) -> list:  # type: ignore[override]
        return list(await self.user.playlists("me", limit=limit))[:limit]

    async def my_favorite_tracks(self, *, limit: int = 25) -> list:  # type: ignore[override]
        return list(await self.user.tracks("me", limit=limit))[:limit]

    async def my_favorite_albums(self, *, limit: int = 25) -> list:  # type: ignore[override]
        return list(await self.user.albums("me", limit=limit))[:limit]

    async def my_favorite_artists(self, *, limit: int = 25) -> list:  # type: ignore[override]
        return list(await self.user.artists("me", limit=limit))[:limit]

    async def my_flow(self, *, limit: int = 25) -> list:  # type: ignore[override]
        return list(await self.user.flow("me", limit=limit))[:limit]

    async def create_playlist(self, title: str, user_id: Any = "me") -> dict:  # type: ignore[override]
        return await self.user.create_playlist(user_id, title)

    async def add_to_playlist(self, playlist_id: int, track_ids: Any) -> bool:  # type: ignore[override]
        return await self.playlist.add_tracks(playlist_id, track_ids)

    async def full_track(self, track_id: int) -> dict:  # type: ignore[override]
        track = await self.track.get(track_id)
        out: dict[str, Any] = {"track": track}
        album = (track.get("album") or {}) if isinstance(track, dict) else {}
        artist = (track.get("artist") or {}) if isinstance(track, dict) else {}
        if album.get("id"):
            try:
                out["album"] = await self.album.get(album["id"])
            except Exception:
                out["album"] = album
        if artist.get("id"):
            try:
                out["artist"] = await self.artist.get(artist["id"])
            except Exception:
                out["artist"] = artist
        return out

    async def full_album(self, album_id: int) -> dict:  # type: ignore[override]
        album = await self.album.get(album_id)
        out: dict[str, Any] = {"album": album}
        artist = (album.get("artist") or {}) if isinstance(album, dict) else {}
        if artist.get("id"):
            try:
                out["artist"] = await self.artist.get(artist["id"])
            except Exception:
                out["artist"] = artist
        return out

    async def exchange_code_for_token(
        self, app_id: str | int, secret: str, code: str, *, output: str = "json"
    ) -> dict:
        from urllib.parse import urlencode

        query = urlencode(
            {"app_id": str(app_id), "secret": secret, "code": code, "output": output}
        )
        response = await self._transport.client.get(f"{TOKEN_URL}?{query}")
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if output == "json" or "json" in content_type:
            try:
                data = response.json()
            except ValueError:
                data = parse_token_response(response.text)
        else:
            data = parse_token_response(response.text)
        if isinstance(data, dict):
            return data
        return {"access_token": data}


class _AsyncResourceProxy:
    """Awaitable proxy: ``await client.track.get(...)`` just works."""

    def __init__(self, resource: Any) -> None:
        object.__setattr__(self, "_resource", resource)

    def __getattr__(self, name: str) -> Any:
        attr = getattr(object.__getattribute__(self, "_resource"), name)
        if not callable(attr):
            return attr

        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = attr(*args, **kwargs)
            import inspect

            if inspect.isawaitable(result):
                result = await result
            # PaginatedList built inside resources via the shim has no
            # usable sync fetcher; async paging goes through explicit
            # helpers, so detach it.
            if isinstance(result, PaginatedList):
                return PaginatedList(result.raw, fetch=None)
            return result

        return wrapper
