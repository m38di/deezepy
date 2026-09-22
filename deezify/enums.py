"""Central enums for the Deezer SDK.

All enums are ``str``-based (``class X(str, Enum)``), so every member
compares equal to — and serializes exactly like — its raw API string::

    SearchOrder.RANKING == "RANKING"          # True
    f"{SearchOrder.TRACK_ASC}"                # "TRACK_ASC" (str Enum)
    json.dumps({"order": SearchOrder.RANKING})  # '{"order": "RANKING"}'

This means enums are purely additive convenience: anywhere the SDK accepts
a ``str`` you may pass either the plain string or the enum member.
Validation helpers accept both and always send the plain string value.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class _StrEnum(str, Enum):
    """``str`` enum with a clean ``str()`` (py3.9/3.10 compatible)."""

    def __str__(self) -> str:
        return str(self.value)

    @classmethod
    def values(cls) -> tuple[str, ...]:
        """All raw string values, e.g. for error messages."""
        return tuple(member.value for member in cls)

    @classmethod
    def coerce(cls, value: "str | _StrEnum", *, label: str) -> str:
        """Validate ``value`` (member or raw string) and return its string."""
        if isinstance(value, cls):
            return value.value
        try:
            return cls(value).value
        except ValueError:
            valid = ", ".join(cls.values())
            raise ValueError(
                f"Invalid {label} {value!r}. Choose from: {valid}"
            ) from None


class SearchOrder(_StrEnum):
    """Sort orders accepted by ``GET /search*`` (``order=...``)."""

    RANKING = "RANKING"
    TRACK_ASC = "TRACK_ASC"
    TRACK_DESC = "TRACK_DESC"
    ARTIST_ASC = "ARTIST_ASC"
    ARTIST_DESC = "ARTIST_DESC"
    ALBUM_ASC = "ALBUM_ASC"
    ALBUM_DESC = "ALBUM_DESC"
    RATING_ASC = "RATING_ASC"
    RATING_DESC = "RATING_DESC"
    DURATION_ASC = "DURATION_ASC"
    DURATION_DESC = "DURATION_DESC"


class SearchField(_StrEnum):
    """Field names for advanced search (``q=field:value``)."""

    ARTIST = "artist"
    ALBUM = "album"
    TRACK = "track"
    LABEL = "label"
    DUR_MIN = "dur_min"
    DUR_MAX = "dur_max"
    BPM_MIN = "bpm_min"
    BPM_MAX = "bpm_max"


class Permission(_StrEnum):
    """OAuth permission scopes (``perms=...``)."""

    BASIC_ACCESS = "basic_access"
    EMAIL = "email"
    OFFLINE_ACCESS = "offline_access"
    MANAGE_LIBRARY = "manage_library"
    MANAGE_COMMUNITY = "manage_community"
    DELETE_LIBRARY = "delete_library"
    LISTENING_HISTORY = "listening_history"


class RecommendationKind(_StrEnum):
    """Recommendation feeds (``GET /user/{id}/recommendations/{kind}``)."""

    ALBUMS = "albums"
    ARTISTS = "artists"
    PLAYLISTS = "playlists"
    TRACKS = "tracks"
    RADIOS = "radios"
    RELEASES = "releases"


class UserChartKind(_StrEnum):
    """User chart feeds (``GET /user/{id}/charts/{kind}``)."""

    ALBUMS = "albums"
    PLAYLISTS = "playlists"
    TRACKS = "tracks"


class ExplicitContentLevel(_StrEnum):
    """Values of ``user.explicit_content_levels_available[]``."""

    EXPLICIT_DISPLAY = "explicit_display"
    EXPLICIT_NO_RECOMMENDATION = "explicit_no_recommendation"
    EXPLICIT_HIDE = "explicit_hide"


class Gender(_StrEnum):
    """Values of ``user.gender``."""

    FEMALE = "F"
    MALE = "M"


class RecordType(_StrEnum):
    """Common values of ``album.record_type`` (open-ended at the API)."""

    EP = "EP"
    ALBUM = "ALBUM"
    SINGLE = "SINGLE"


class OEmbedFormat(_StrEnum):
    """Response formats for ``GET /oembed``."""

    JSON = "json"
    XML = "xml"


class EntityType(_StrEnum):
    """The ``type`` discriminator on API objects and oEmbed ``entity``."""

    TRACK = "track"
    ALBUM = "album"
    ARTIST = "artist"
    PLAYLIST = "playlist"
    USER = "user"
    PODCAST = "podcast"
    EPISODE = "episode"
    RADIO = "radio"
    GENRE = "genre"
    EDITORIAL = "editorial"
    OPTIONS = "options"
    CHART = "chart"


def coerce_optional_enum(
    enum_cls: type[_StrEnum], value: Any | None, *, label: str
) -> str | None:
    """Coerce an optional enum/str parameter to its wire string."""
    if value is None:
        return None
    return enum_cls.coerce(value, label=label)
