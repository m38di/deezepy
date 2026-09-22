"""Offline unit tests — mocked HTTP, no network needed."""

from __future__ import annotations

import httpx
import pytest

from deezify import (
    DeezerAPIError,
    DeezerClient,
    DeezerTransportError,
    PaginatedList,
    authorization_url,
    implicit_authorization_url,
    parse_implicit_callback_fragment,
    parse_token_response,
    token_exchange_url,
)
from deezify.resources.search import ORDER_VALUES, build_advanced_query


def make_client(handler) -> DeezerClient:
    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, base_url="https://api.deezer.com")
    return DeezerClient(http_client=http_client)


def json_response(payload, status_code=200) -> httpx.Response:
    return httpx.Response(status_code, json=payload)


# -- catalogue reads -------------------------------------------------------

def test_track_get():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/track/3135556"
        return json_response({"id": 3135556, "title": "Harder, Better, Faster, Stronger"})

    client = make_client(handler)
    track = client.track.get(3135556)
    assert track["title"] == "Harder, Better, Faster, Stronger"


def test_artist_top_pagination_params():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["query"] = dict(request.url.params)
        return json_response({"data": [{"id": 1}], "total": 1, "next": None})

    client = make_client(handler)
    page = client.artist.top(27, index=5, limit=2)
    assert seen["query"] == {"index": "5", "limit": "2"}
    assert isinstance(page, PaginatedList)
    assert page.total == 1


def test_paginated_walk_follows_next():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        if "index=2" in str(request.url):
            return json_response({"data": [{"id": 3}], "total": 3})
        return json_response(
            {
                "data": [{"id": 1}, {"id": 2}],
                "total": 3,
                "next": "https://api.deezer.com/playlist/1/tracks?index=2&limit=2",
            }
        )

    client = make_client(handler)
    page = client.playlist.tracks(1, limit=2)
    ids = [t["id"] for t in page.iter_all_items()]
    assert ids == [1, 2, 3]
    assert len(calls) == 2


def test_api_error_envelope_raises_structured_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(
            {"error": {"type": "DataException", "message": "no data", "code": 800}}
        )

    client = make_client(handler)
    with pytest.raises(DeezerAPIError) as excinfo:
        client.track.get(0)
    assert excinfo.value.code == 800
    assert "DATA_NOT_FOUND" in str(excinfo.value)


def test_http_error_without_envelope_raises_transport_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    client = make_client(handler)
    with pytest.raises(DeezerTransportError):
        client.track.get(1)


# -- search -----------------------------------------------------------------

def test_search_all_sends_query():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["query"] = dict(request.url.params)
        return json_response({"data": [], "total": 0})

    client = make_client(handler)
    client.search.all("Daft Punk", limit=5)
    assert seen["path"] == "/search"
    assert seen["query"]["q"] == "Daft Punk"
    assert seen["query"]["limit"] == "5"


def test_search_type_paths():
    paths = {
        "tracks": "/search/track",
        "albums": "/search/album",
        "artists": "/search/artist",
        "playlists": "/search/playlist",
        "podcasts": "/search/podcast",
        "radios": "/search/radio",
        "users": "/search/user",
    }
    for method, path in paths.items():
        seen = {}

        def handler(request: httpx.Request, _p=path) -> httpx.Response:
            seen["path"] = request.url.path
            return json_response({"data": [], "total": 0})

        client = make_client(handler)
        getattr(client.search, method)("x")
        assert seen["path"] == path, method


def test_search_rejects_empty_query_and_bad_order():
    client = make_client(lambda request: json_response({"data": [], "total": 0}))
    with pytest.raises(ValueError):
        client.search.all("   ")
    with pytest.raises(ValueError):
        client.search.tracks("x", order="NOPE")
    # every documented order value is accepted at validation time
    for order in ORDER_VALUES:
        client.search.tracks("x", order=order)


def test_build_advanced_query_quotes_and_validates():
    q = build_advanced_query(artist="Aloe Blacc", track="I Need A Dollar")
    assert q == 'artist:"Aloe Blacc" track:"I Need A Dollar"'
    assert build_advanced_query(dur_min=300, bpm_min=120) == "dur_min:300 bpm_min:120"
    with pytest.raises(ValueError):
        build_advanced_query(nope="x")


# -- write actions ------------------------------------------------------------

def test_playlist_add_tracks_posts_songs():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["body"] = request.read().decode()
        return json_response(True)

    client = make_client(handler)
    assert client.playlist.add_tracks(1, [10, 20]) is True
    assert seen["method"] == "POST"
    assert "songs=10%2C20" in seen["body"] or "songs=10,20" in seen["body"]


def test_episode_bookmark_offset_validated():
    client = make_client(lambda request: json_response(True))
    with pytest.raises(ValueError):
        client.episode.set_bookmark(1, 101)
    with pytest.raises(ValueError):
        client.episode.set_bookmark(1, -1)


def test_user_create_playlist_validates_title():
    client = make_client(lambda request: json_response({"id": 9}))
    with pytest.raises(ValueError):
        client.user.create_playlist("me", "  ")


# -- oauth helpers --------------------------------------------------------------

def test_authorization_url_server_flow():
    url = authorization_url("123", "https://app.example/cb", perms="basic_access,email")
    assert url.startswith("https://connect.deezer.com/oauth/auth.php?")
    assert "app_id=123" in url
    assert "response_type" not in url


def test_implicit_flow_helpers():
    url = implicit_authorization_url("123", "https://app.example/cb")
    assert "response_type=token" in url
    frag = parse_implicit_callback_fragment("#access_token=ABC&expires=3600")
    assert frag == {"access_token": "ABC", "expires": "3600"}
    assert "access_token.php" in token_exchange_url("1", "s", "code")
    assert parse_token_response("access_token=ABC&expires=0")["access_token"] == "ABC"
    assert parse_token_response('{"access_token":"ABC"}')["access_token"] == "ABC"


# -- misc endpoints ---------------------------------------------------------------

def test_chart_genre_and_editorial_paths():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.path)
        if request.url.path.startswith("/chart"):
            return json_response({"data": [], "total": 0})
        return json_response({"id": 0})

    client = make_client(handler)
    client.chart.tracks(132)
    client.chart.get(0)
    assert "/chart/132/tracks" in seen
    assert "/chart" in seen


def test_oembed_validates_and_sends_url():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["query"] = dict(request.url.params)
        return json_response({"title": "Discovery"})

    client = make_client(handler)
    doc = client.oembed.get("https://www.deezer.com/album/302127")
    assert doc["title"] == "Discovery"
    assert seen["query"]["url"] == "https://www.deezer.com/album/302127"
    with pytest.raises(ValueError):
        client.oembed.get("  ")

