"""Resource namespace exports."""

from .album import AlbumResource
from .artist import ArtistResource
from .base import Resource
from .catalog import (
    ChartResource,
    EditorialResource,
    GenreResource,
    InfosResource,
    OptionsResource,
    RadioResource,
)
from .oembed import OEmbedResource
from .playlist import PlaylistResource
from .podcast import EpisodeResource, PodcastResource
from .search import SearchResource
from .track import TrackResource
from .user import UserResource

__all__ = [
    "Resource",
    "AlbumResource",
    "ArtistResource",
    "ChartResource",
    "EditorialResource",
    "EpisodeResource",
    "GenreResource",
    "InfosResource",
    "OEmbedResource",
    "OptionsResource",
    "PlaylistResource",
    "PodcastResource",
    "RadioResource",
    "SearchResource",
    "TrackResource",
    "UserResource",
]
