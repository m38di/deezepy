"""Enum tests — str-compat, coercion, and resource wiring (offline)."""

from __future__ import annotations

import httpx
import pytest

from deezify import (
    DeezerClient,
    OEmbedFormat,
    Permission,
    RecommendationKind,
    SearchField,
    SearchOrder,
    UserChartKind,
)


def make_client(handler, **kwargs) -> DeezerClient:
    kwargs.setdefault("rate_limit", False)
    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, base_url="https://api.deezer.com")
    return DeezerClient(http_client=http_client, **kwargs)


def test_str_enum_compat():
    assert SearchOrder.RANKING == "RANKING"
    assert str(SearchOrder.TRACK_ASC) == "TRACK_ASC"
    assert Permission.EMAIL == "email"
    assert SearchField.coerce("artist", label="f") == "artist"
    with pytest.raises(ValueError):
        SearchOrder.coerce("NOPE", label="order")


def test_search_accepts_enum_and_string():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(dict(request.url.params))
        return httpx.Response(200, json={"data": [], "total": 0})

    client = make_client(handler)
    client.search.tracks("x", order=SearchOrder.RATING_DESC)
    assert seen["order"] == "RATING_DESC"
    client.search.tracks("x", order="RANKING")
    assert seen["order"] == "RANKING"
    with pytest.raises(ValueError):
        client.search.tracks("x", order="NOPE")


def test_oauth_perms_accept_enums():
    from deezify.oauth import authorization_url

    url = authorization_url("1", "https://x.example/cb", perms=[Permission.EMAIL])
    assert "perms=email" in url
    url = authorization_url("1", "https://x.example/cb", perms="basic_access,email")
    assert "basic_access" in url
    with pytest.raises(ValueError):
        authorization_url("1", "https://x.example/cb", perms="nope")


def test_oembed_and_user_kinds():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["params"] = dict(request.url.params)
        return httpx.Response(200, json={"title": "ok"})

    client = make_client(handler)
    client.oembed.get("https://www.deezer.com/album/1", format=OEmbedFormat.JSON)
    assert seen["path"] == "/oembed"
    assert seen["params"]["format"] == "json"
    with pytest.raises(ValueError):
        client.oembed.get("https://www.deezer.com/album/1", format="yaml")
    client.user.recommendations("me", RecommendationKind.ALBUMS)
    assert seen["path"] == "/user/me/recommendations/albums"
    client.user.user_chart("me", UserChartKind.PLAYLISTS)
    assert seen["path"] == "/user/me/charts/playlists"
    with pytest.raises(ValueError):
        client.user.recommendations("me", "nope")

