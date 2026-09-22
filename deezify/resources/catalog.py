"""Radio, genre, chart, editorial, infos and options resources."""

from __future__ import annotations

from typing import Any

from .base import Resource
from ..paginator import PaginatedList
from ..types import (
    Album, Artist, Chart, ChartTrack, Editorial, EditorialCharts, Genre, Infos, Options,
    Playlist, Podcast, Radio, Track, User, WriteResult,
)


class RadioResource(Resource):
    """Radios — https://developers.deezer.com/api/radio."""

    def get(self, radio_id: int, **params: Any) -> Radio:
        return self._get(f"radio/{radio_id}", params=params or None)

    def list(self, **params: Any) -> PaginatedList[Radio]:
        """All radios (``GET /radio``)."""
        return self._paginated("radio", params=params or None)

    def genres(
        self, radio_id: int, *, index: int | None = None, limit: int | None = None
    ) -> PaginatedList[Radio]:
        return self._paginated(
            f"radio/{radio_id}/genres", params=self._page(None, index, limit)
        )

    def top(
        self, radio_id: int = 0, *, index: int | None = None, limit: int | None = None
    ) -> PaginatedList[Radio]:
        """Top radios (``GET /radio/top``; default 25)."""
        path = "radio/top" if not radio_id else f"radio/{radio_id}/top"
        return self._paginated(path, params=self._page(None, index, limit))

    def tracks(
        self, radio_id: int, *, index: int | None = None, limit: int | None = None
    ) -> PaginatedList[Track]:
        """First tracks of a radio (``GET /radio/{id}/tracks``)."""
        return self._paginated(
            f"radio/{radio_id}/tracks", params=self._page(None, index, limit)
        )

    def lists(
        self, radio_id: int = 0, *, index: int | None = None, limit: int | None = None
    ) -> PaginatedList[Radio]:
        """Personal (MIX) radios (``GET /radio/lists``)."""
        path = "radio/lists" if not radio_id else f"radio/{radio_id}/lists"
        return self._paginated(path, params=self._page(None, index, limit))

    def add_favorite(self, user_id: int | str, radio_id: int) -> WriteResult:
        return bool(
            self._post(f"user/{user_id}/radios", data={"radio_id": str(radio_id)})
        )

    def remove_favorite(self, user_id: int | str, radio_id: int) -> WriteResult:
        return bool(
            self._delete(f"user/{user_id}/radios", params={"radio_id": radio_id})
        )


class GenreResource(Resource):
    """Genres — https://developers.deezer.com/api/genre."""

    def get(self, genre_id: int, **params: Any) -> Genre:
        return self._get(f"genre/{genre_id}", params=params or None)

    def list(self, **params: Any) -> PaginatedList[Genre]:
        """All genres (``GET /genre``)."""
        return self._paginated("genre", params=params or None)

    def artists(
        self, genre_id: int, *, index: int | None = None, limit: int | None = None
    ) -> PaginatedList[Artist]:
        return self._paginated(
            f"genre/{genre_id}/artists", params=self._page(None, index, limit)
        )

    def podcasts(
        self, genre_id: int, *, index: int | None = None, limit: int | None = None
    ) -> PaginatedList[Podcast]:
        return self._paginated(
            f"genre/{genre_id}/podcasts", params=self._page(None, index, limit)
        )

    def radios(
        self, genre_id: int, *, index: int | None = None, limit: int | None = None
    ) -> PaginatedList[Radio]:
        return self._paginated(
            f"genre/{genre_id}/radios", params=self._page(None, index, limit)
        )


class ChartResource(Resource):
    """Charts — https://developers.deezer.com/api/chart.

    Note: ``/chart`` and ``/chart/{id}`` return a *bundle* dict with
    ``tracks``/``albums``/``artists``/``playlists``/``podcasts`` sub-objects
    (each holding ``data``/``total``), not a flat list. The ``tracks()`` /
    ``albums()`` / ... helpers below therefore fetch the bundle once and
    return the corresponding sub-list as a :class:`PaginatedList`, so
    ``client.chart.tracks(limit=10)`` behaves like every other collection.
    """

    def get(self, chart_id: int = 0, **params: Any) -> Chart:
        """Global chart bundle (``GET /chart``) or genre bundle
        (``GET /chart/{id}``)."""
        path = "chart" if not chart_id else f"chart/{chart_id}"
        return self._get(path, params=params or None)

    def _sublist(
        self, chart_id: int, name: str, *, index: int | None, limit: int | None
    ) -> Any:
        import inspect

        path = "chart" if not chart_id else f"chart/{chart_id}"
        bundle = self._get(path, params=self._page(None, index, limit) or None)
        if inspect.isawaitable(bundle):
            return self._asublist(bundle, path, name, index=index, limit=limit)
        if isinstance(bundle, dict) and isinstance(bundle.get(name), dict):
            return PaginatedList(bundle[name])
        # Fallback: some deployments expose /chart/<kind> list endpoints.
        kind_path = f"{path}/{name}"
        try:
            return self._paginated(kind_path, params=self._page(None, index, limit))
        except Exception:
            return PaginatedList(bundle.get(name, []) if isinstance(bundle, dict) else [])

    async def _asublist(
        self, bundle: Any, path: str, name: str, *, index: int | None, limit: int | None
    ) -> PaginatedList[Any]:
        import inspect

        if inspect.isawaitable(bundle):
            bundle = await bundle
        if isinstance(bundle, dict) and isinstance(bundle.get(name), dict):
            return PaginatedList(bundle[name])
        kind_path = f"{path}/{name}"
        try:
            result = self._paginated(kind_path, params=self._page(None, index, limit))
            return await result if inspect.isawaitable(result) else result
        except Exception:
            return PaginatedList(bundle.get(name, []) if isinstance(bundle, dict) else [])

    def tracks(
        self, chart_id: int = 0, *, index: int | None = None, limit: int | None = None
    ) -> PaginatedList[ChartTrack]:
        """Top tracks (from the chart bundle's ``tracks`` sub-list)."""
        return self._sublist(chart_id, "tracks", index=index, limit=limit)

    def albums(
        self, chart_id: int = 0, *, index: int | None = None, limit: int | None = None
    ) -> PaginatedList[Album]:
        """Top albums (from the chart bundle's ``albums`` sub-list)."""
        return self._sublist(chart_id, "albums", index=index, limit=limit)

    def artists(
        self, chart_id: int = 0, *, index: int | None = None, limit: int | None = None
    ) -> PaginatedList[Artist]:
        """Top artists (from the chart bundle's ``artists`` sub-list)."""
        return self._sublist(chart_id, "artists", index=index, limit=limit)

    def playlists(
        self, chart_id: int = 0, *, index: int | None = None, limit: int | None = None
    ) -> PaginatedList[Playlist]:
        """Top playlists (from the chart bundle's ``playlists`` sub-list)."""
        return self._sublist(chart_id, "playlists", index=index, limit=limit)

    def podcasts(
        self, chart_id: int = 0, *, index: int | None = None, limit: int | None = None
    ) -> PaginatedList[Podcast]:
        """Top podcasts (from the chart bundle's ``podcasts`` sub-list)."""
        return self._sublist(chart_id, "podcasts", index=index, limit=limit)


class EditorialResource(Resource):
    """Editorial picks — https://developers.deezer.com/api/editorial."""

    def get(self, editorial_id: int = 0, **params: Any) -> Editorial:
        path = "editorial" if not editorial_id else f"editorial/{editorial_id}"
        return self._get(path, params=params or None)

    def list(self, **params: Any) -> PaginatedList[Editorial]:
        """All editorial choices (``GET /editorial``)."""
        return self._paginated("editorial", params=params or None)

    def selection(
        self, editorial_id: int = 0, *, index: int | None = None, limit: int | None = None
    ) -> PaginatedList[Album]:
        path = (
            "editorial/selection"
            if not editorial_id
            else f"editorial/{editorial_id}/selection"
        )
        return self._paginated(path, params=self._page(None, index, limit))

    def charts(
        self, editorial_id: int = 0, *, index: int | None = None, limit: int | None = None
    ) -> EditorialCharts:
        """Top track/album/artist/playlist bundle for an editorial."""
        path = (
            "editorial/charts" if not editorial_id else f"editorial/{editorial_id}/charts"
        )
        return self._get(path, params=self._page(None, index, limit) or None)

    def releases(
        self, editorial_id: int = 0, *, index: int | None = None, limit: int | None = None
    ) -> PaginatedList[Album]:
        """New releases per genre (``GET /editorial/{id}/releases``)."""
        path = (
            "editorial/releases"
            if not editorial_id
            else f"editorial/{editorial_id}/releases"
        )
        return self._paginated(path, params=self._page(None, index, limit))


class InfosResource(Resource):
    """Country/API information — https://developers.deezer.com/api/infos."""

    def get(self, **params: Any) -> Infos:
        return self._get("infos", params=params or None)


class OptionsResource(Resource):
    """Current-user streaming options — https://developers.deezer.com/api/options."""

    def get(self, **params: Any) -> Options:
        return self._get("options", params=params or None)
