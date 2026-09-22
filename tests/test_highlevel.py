"""High-level convenience method tests (offline, mocked HTTP)."""

from __future__ import annotations

import httpx
import pytest

from deezify import AsyncDeezerClient, DeezerClient


def make_client(handler, **kwargs) -> DeezerClient:
    kwargs.setdefault("rate_limit", False)
    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, base_url="https://api.deezer.com")
    return DeezerClient(http_client=http_client, **kwargs)


def route(mapping):
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        for prefix, payload in mapping.items():
            if path.startswith(prefix):
                return httpx.Response(200, json=payload)
        return httpx.Response(
            200,
            json={"error": {"type": "DataException", "message": "no", "code": 800}},
        )

    return handler


def test_find_and_best_match():
    handler = route(
        {
            "/search/track": {"data": [{"id": 1, "title": "One"}], "total": 1},
            "/search/album": {"data": [{"id": 2, "title": "Two"}], "total": 1},
            "/search/artist": {"data": [], "total": 0},
        }
    )
    client = make_client(handler)
    assert [t["title"] for t in client.find_track("x")] == ["One"]
    assert client.best_album_match("x")["id"] == 2
    assert client.best_artist_match("x") is None


def test_top_and_genre_shortcuts():
    handler = route(
        {
            "/chart": {
                "tracks": {"data": [{"id": 1, "title": "T"}], "total": 1},
                "albums": {"data": [{"id": 2, "title": "A"}], "total": 1},
                "artists": {"data": [{"id": 3, "name": "R"}], "total": 1},
                "playlists": {"data": [], "total": 0},
                "podcasts": {"data": [], "total": 0},
            },
            "/genre": {"data": [{"id": 0, "name": "All"}]},
        }
    )
    client = make_client(handler)
    assert client.top_tracks(limit=5)[0]["title"] == "T"
    assert client.top_albums(limit=5)[0]["title"] == "A"
    assert client.top_artists(limit=5)[0]["name"] == "R"
    assert [g["name"] for g in client.genres(limit=5)] == ["All"]


def test_full_track_enriches_album_and_artist():
    handler = route(
        {
            "/track/1": {
                "id": 1,
                "title": "T",
                "album": {"id": 10},
                "artist": {"id": 20},
            },
            "/album/10": {"id": 10, "title": "Full Album"},
            "/artist/20": {"id": 20, "name": "Full Artist"},
        }
    )
    client = make_client(handler)
    full = client.full_track(1)
    assert full["album"]["title"] == "Full Album"
    assert full["artist"]["name"] == "Full Artist"
    assert client.track_preview_url(1) is None


def test_playlist_all_tracks_walks_pages():
    def handler(request: httpx.Request) -> httpx.Response:
        if "index=2" in str(request.url):
            return httpx.Response(200, json={"data": [{"id": 3}], "total": 3})
        return httpx.Response(
            200,
            json={
                "data": [{"id": 1}, {"id": 2}],
                "total": 3,
                "next": "https://api.deezer.com/playlist/9/tracks?index=2&limit=2",
            },
        )

    client = make_client(handler)
    assert [t["id"] for t in client.playlist_all_tracks(9)] == [1, 2, 3]


@pytest.mark.asyncio
async def test_async_high_level():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/search/track":
            return httpx.Response(200, json={"data": [{"id": 1, "title": "T"}], "total": 1})
        if request.url.path == "/track/1":
            return httpx.Response(
                200, json={"id": 1, "title": "T", "preview": "http://x/y.mp3"}
            )
        return httpx.Response(200, json={"data": [], "total": 0})

    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(
        transport=transport, base_url="https://api.deezer.com"
    )
    async with AsyncDeezerClient(http_client=http_client, rate_limit=False) as client:
        assert [t["title"] for t in await client.find_track("x")] == ["T"]
        assert await client.track_preview_url(1) == "http://x/y.mp3"

