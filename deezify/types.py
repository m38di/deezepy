"""Typed hints for every Deezer API object.

Field coverage below was verified against live ``https://api.deezer.com``
responses (not just the docs tables), so nested shapes — e.g. the ``artist``
inside a :class:`Track`, or the per-kind sub-lists of :class:`Chart` — match
what the API actually returns.

Runtime behavior is unchanged: the client returns plain ``dict`` objects (and
:class:`~deezify.paginator.PaginatedList` for collections). These
``TypedDict`` classes exist for static typing, IDE autocompletion and
documentation. Every class has ``total=False`` because the API only ever
returns a *subset* of fields depending on context (a track inside an album
carries fewer keys than a full ``track.get()``).

Generic aliases at the bottom describe the shapes of paginated envelopes and
write-action results:

- ``PaginatedTracks`` etc. — what ``client.*.<connection>()`` items look like
  once iterated (each item is the corresponding object type).
- ``ChartBundle`` — the dict returned by ``client.chart.get()``.
"""

from __future__ import annotations

from typing import Any, Generic, TypedDict, TypeVar

T = TypeVar("T")


class _Partial(TypedDict, total=False):
    id: int  # noqa: A003 - mirrors the API field name


class _Entity(_Partial):
    #: Object discriminator returned by the API (``"track"``, ``"album"``...).
    type: str


# ---------------------------------------------------------------------------
# Shared nested shapes
# ---------------------------------------------------------------------------


class Contributor(_Entity):
    """An artist contributor entry (``track.contributors[]``)."""

    name: str
    link: str
    share: str
    picture: str
    picture_small: str
    picture_medium: str
    picture_big: str
    picture_xl: str
    radio: bool
    tracklist: str
    role: str


class GenreRef(_Entity):
    """Genre entry inside ``album.genres.data[]``."""

    name: str
    picture: str


class GenresEnvelope(TypedDict, total=False):
    data: list[GenreRef]
    checksum: str


# ---------------------------------------------------------------------------
# Artist — https://developers.deezer.com/api/artist
# ---------------------------------------------------------------------------


class ArtistRef(_Entity):
    """Compact artist nested in tracks/albums/charts."""

    name: str
    link: str
    share: str
    picture: str
    picture_small: str
    picture_medium: str
    picture_big: str
    picture_xl: str
    nb_album: int
    nb_fan: int
    radio: bool
    tracklist: str
    role: str


class Artist(ArtistRef):
    """Full artist object (``GET /artist/{id}``)."""


# ---------------------------------------------------------------------------
# Album — https://developers.deezer.com/api/album
# ---------------------------------------------------------------------------


class AlbumRef(_Entity):
    """Compact album nested in tracks/charts."""

    title: str
    upc: str
    link: str
    cover: str
    cover_small: str
    cover_medium: str
    cover_big: str
    cover_xl: str
    md5_image: str
    genre_id: int
    release_date: str
    tracklist: str


class AlbumTrack(_Entity):
    """Track entry inside ``album.tracks.data[]`` / playlist listings."""

    readable: bool
    title: str
    title_short: str
    title_version: str
    isrc: str
    link: str
    duration: int
    rank: int
    explicit_lyrics: bool
    explicit_content_lyrics: int
    explicit_content_cover: int
    preview: str
    md5_image: str
    time_add: str
    artist: ArtistRef
    album: AlbumRef


class AlbumTracksEnvelope(TypedDict, total=False):
    data: list[AlbumTrack]
    checksum: str


class Album(AlbumRef):
    """Full album object (``GET /album/{id}``)."""

    share: str
    genres: GenresEnvelope
    label: str
    provider: str
    nb_tracks: int
    duration: int
    fans: int
    record_type: str
    available: bool
    alternative: AlbumRef
    explicit_lyrics: bool
    explicit_content_lyrics: int
    explicit_content_cover: int
    contributors: list[Contributor]
    fallback: dict[str, Any]
    artist: ArtistRef
    tracks: AlbumTracksEnvelope


# ---------------------------------------------------------------------------
# Track — https://developers.deezer.com/api/track
# ---------------------------------------------------------------------------


class Track(_Entity):
    """Full track object (``GET /track/{id}``)."""

    readable: bool
    title: str
    title_short: str
    title_version: str
    unseen: bool
    isrc: str
    link: str
    share: str
    duration: int
    track_position: int
    disk_number: int
    rank: int
    release_date: str
    explicit_lyrics: bool
    explicit_content_lyrics: int
    explicit_content_cover: int
    preview: str
    bpm: float
    gain: float
    available_countries: list[str]
    alternative: Track
    contributors: list[Contributor]
    md5_image: str
    track_token: str
    time_add: str
    position: int
    artist: ArtistRef
    album: AlbumRef


class ChartTrack(Track, total=False):
    """Track entry inside chart listings (adds ``position``)."""

    position: int


# ---------------------------------------------------------------------------
# Playlist — https://developers.deezer.com/api/playlist
# ---------------------------------------------------------------------------


class CreatorRef(_Entity):
    """Playlist creator (``playlist.creator``)."""

    name: str
    tracklist: str


class PlaylistRef(_Entity):
    """Compact playlist nested in charts / user listings."""

    title: str
    description: str
    duration: int
    public: bool
    is_loved_track: bool
    collaborative: bool
    nb_tracks: int
    unseen_track_count: int
    fans: int
    link: str
    share: str
    picture: str
    picture_small: str
    picture_medium: str
    picture_big: str
    picture_xl: str
    checksum: str
    position: int
    creator: CreatorRef
    user: UserRef  # noqa: F821 - defined below; resolved lazily


class Playlist(PlaylistRef):
    """Full playlist object (``GET /playlist/{id}``)."""

    tracklist: str
    creation_date: str
    add_date: str
    mod_date: str
    md5_image: str
    picture_type: str
    tracks: AlbumTracksEnvelope


# ---------------------------------------------------------------------------
# User — https://developers.deezer.com/api/user
# ---------------------------------------------------------------------------


class UserRef(_Entity):
    """Public user nested in fans/creators (``GET /user/{id}`` unauthenticated)."""

    name: str
    lastname: str
    firstname: str
    link: str
    picture: str
    picture_small: str
    picture_medium: str
    picture_big: str
    picture_xl: str
    country: str
    tracklist: str


class User(UserRef):
    """Full user object (extra fields need an access token)."""

    email: str
    status: int
    birthday: str
    inscription_date: str
    gender: str
    lang: str
    is_kid: bool
    explicit_content_level: str
    explicit_content_levels_available: list[str]


# Fix forward reference: PlaylistRef.user -> UserRef
PlaylistRef.__annotations__["user"] = UserRef


# ---------------------------------------------------------------------------
# Podcast / Episode
# ---------------------------------------------------------------------------


class PodcastRef(_Entity):
    """Compact podcast nested in charts / episode payloads."""

    title: str
    description: str
    available: bool
    fans: int
    link: str
    share: str
    picture: str
    picture_small: str
    picture_medium: str
    picture_big: str
    picture_xl: str
    position: int


class Podcast(PodcastRef):
    """Full podcast object (``GET /podcast/{id}``)."""


class EpisodeRef(_Entity):
    """Compact episode inside ``podcast.episodes`` listings."""

    title: str
    release_date: str
    duration: int
    picture: str
    picture_small: str
    picture_medium: str
    picture_big: str
    picture_xl: str


class Episode(EpisodeRef):
    """Full episode object (``GET /episode/{id}``)."""

    description: str
    available: bool
    link: str
    share: str
    picture: str
    track_token: str
    podcast: PodcastRef


class Bookmark(TypedDict, total=False):
    #: Bookmark offset 0–100.
    offset: int


# ---------------------------------------------------------------------------
# Radio / Genre / Editorial
# ---------------------------------------------------------------------------


class Radio(_Entity):
    """Radio object (``GET /radio`` / ``GET /radio/{id}``)."""

    title: str
    description: str
    share: str
    picture: str
    picture_small: str
    picture_medium: str
    picture_big: str
    picture_xl: str
    tracklist: str
    md5_image: str


class Genre(_Entity):
    """Genre object (``GET /genre`` / ``GET /genre/{id}``)."""

    name: str
    picture: str
    picture_small: str
    picture_medium: str
    picture_big: str
    picture_xl: str


class Editorial(_Entity):
    """Editorial object (``GET /editorial``)."""

    name: str
    picture: str
    picture_small: str
    picture_medium: str
    picture_big: str
    picture_xl: str


# ---------------------------------------------------------------------------
# Chart bundle — https://developers.deezer.com/api/chart
# ---------------------------------------------------------------------------


class ChartTracks(TypedDict, total=False):
    data: list[ChartTrack]
    total: int


class ChartAlbums(TypedDict, total=False):
    data: list[AlbumRef]
    total: int


class ChartArtists(TypedDict, total=False):
    data: list[ArtistRef]
    total: int


class ChartPlaylists(TypedDict, total=False):
    data: list[PlaylistRef]
    total: int


class ChartPodcasts(TypedDict, total=False):
    data: list[PodcastRef]
    total: int


class Chart(TypedDict, total=False):
    """Bundle returned by ``GET /chart`` and ``GET /chart/{genre_id}``."""

    tracks: ChartTracks
    albums: ChartAlbums
    artists: ChartArtists
    playlists: ChartPlaylists
    podcasts: ChartPodcasts


class EditorialCharts(TypedDict, total=False):
    """Bundle returned by ``GET /editorial/{id}/charts``."""

    tracks: ChartTracks
    albums: ChartAlbums
    artists: ChartArtists
    playlists: ChartPlaylists


# ---------------------------------------------------------------------------
# Infos / Options / oEmbed
# ---------------------------------------------------------------------------


class InfosHosts(TypedDict, total=False):
    stream: str
    images: str


class Offer(TypedDict, total=False):
    id: int
    name: str


class Infos(TypedDict, total=False):
    """``GET /infos`` — country/API information."""

    country_iso: str
    country: str
    open: bool
    pop: str
    upload_token: str
    upload_token_lifetime: int
    user_token: str | None
    hosts: InfosHosts
    ads: dict[str, Any]
    has_podcasts: bool
    offers: list[Offer]


class Options(TypedDict, total=False):
    """``GET /options`` — current-user streaming capabilities."""

    streaming: bool
    streaming_duration: int
    offline: bool
    hq: bool
    ads_display: bool
    ads_audio: bool
    too_many_devices: bool
    can_subscribe: bool
    radio_skips: int
    lossless: bool
    preview: bool
    radio: bool
    type: str


class OEmbed(TypedDict, total=False):
    """``GET /oembed?url=...`` — widget metadata."""

    version: str
    type: str
    cache_age: int
    provider_name: str
    provider_url: str
    entity: str
    id: int
    url: str
    author_name: str
    title: str
    thumbnail_url: str
    thumbnail_width: int
    thumbnail_height: int
    width: int
    height: int
    html: str


# ---------------------------------------------------------------------------
# Write-action results
# ---------------------------------------------------------------------------


class CreatePlaylistResult(_Entity):
    """Created playlist id returned by ``POST /user/{id}/playlists``."""

    title: str


#: Write actions return ``True``/``False`` bodies — plain ``bool``.
WriteResult = bool


# ---------------------------------------------------------------------------
# Collection item aliases (what you get when iterating a PaginatedList)
# ---------------------------------------------------------------------------

PaginatedTracks = list[Track]
PaginatedAlbums = list[Album]
PaginatedArtists = list[Artist]
PaginatedPlaylists = list[Playlist]
PaginatedPodcasts = list[Podcast]
PaginatedEpisodes = list[Episode]
PaginatedRadios = list[Radio]
PaginatedGenres = list[Genre]
PaginatedEditorials = list[Editorial]
PaginatedUsers = list[User]


class PaginatedEnvelope(TypedDict, Generic[T], total=False):
    """Raw shape of a list envelope (``data``/``total``/``next``/``prev``)."""

    data: list[T]
    total: int
    prev: str
    next: str
    checksum: str

