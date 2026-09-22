"""deezify — a complete, typed Python SDK for the Deezer API.

- https://developers.deezer.com/api
- Base URL: ``https://api.deezer.com``
- No login or API key needed for public catalogue endpoints; OAuth
  (:mod:`deezify.oauth`) only for user-private actions.
"""

from __future__ import annotations

from .client import AsyncDeezerClient, DeezerClient
from .enums import (
    EntityType,
    ExplicitContentLevel,
    Gender,
    OEmbedFormat,
    Permission,
    RecommendationKind,
    RecordType,
    SearchField,
    SearchOrder,
    UserChartKind,
)
from .errors import (
    DeezerAPIError,
    DeezerAuthError,
    DeezerError,
    DeezerTransportError,
)
from .http import API_BASE_URL
from .oauth import (
    PERMISSIONS,
    authorization_url,
    implicit_authorization_url,
    parse_implicit_callback_fragment,
    parse_token_response,
    token_exchange_url,
)
from .paginator import PaginatedList

__version__ = "1.0.0"

__all__ = [
    "__version__",
    "API_BASE_URL",
    "PERMISSIONS",
    "AsyncDeezerClient",
    "DeezerClient",
    "DeezerError",
    "DeezerAPIError",
    "DeezerAuthError",
    "DeezerTransportError",
    "EntityType",
    "ExplicitContentLevel",
    "Gender",
    "OEmbedFormat",
    "PaginatedList",
    "Permission",
    "RecommendationKind",
    "RecordType",
    "SearchField",
    "SearchOrder",
    "UserChartKind",
    "authorization_url",
    "implicit_authorization_url",
    "parse_implicit_callback_fragment",
    "parse_token_response",
    "token_exchange_url",
]

