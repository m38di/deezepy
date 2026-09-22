"""oEmbed resource — https://developers.deezer.com/api/oembed."""

from __future__ import annotations

from typing import Any

from .base import Resource
from ..enums import OEmbedFormat, coerce_optional_enum
from ..types import OEmbed


class OEmbedResource(Resource):
    """Embedded-player metadata for public Deezer URLs.

    Compatible URLs: ``deezer.com`` album / episode / playlist / show /
    track pages and ``deezer.page.link`` short links.
    """

    def get(
        self,
        url: str,
        *,
        maxwidth: int | None = None,
        maxheight: int | None = None,
        autoplay: bool | None = None,
        radius: bool | None = None,
        tracklist: bool | None = None,
        format: str | OEmbedFormat = "json",  # noqa: A002 - mirrors the API param name
    ) -> OEmbed:
        """Fetch the oEmbed document (``GET /oembed?url=...``)."""
        if not url or not url.strip():
            raise ValueError("url must be a non-empty Deezer URL")
        fmt = OEmbedFormat.coerce(format, label="format")
        params: dict[str, Any] = {"url": url, "format": fmt}
        if maxwidth is not None:
            params["maxwidth"] = maxwidth
        if maxheight is not None:
            params["maxheight"] = maxheight
        if autoplay is not None:
            params["autoplay"] = str(bool(autoplay)).lower()
        if radius is not None:
            params["radius"] = str(bool(radius)).lower()
        if tracklist is not None:
            params["tracklist"] = str(bool(tracklist)).lower()
        result = self._get("oembed", params=params)
        if fmt == "xml":
            from ..errors import DeezerTransportError

            raise DeezerTransportError(
                "oEmbed format='xml' is not decoded by this SDK; use format='json'"
            )
        return result
