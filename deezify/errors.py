"""Deezer API exceptions.

Mirrors the `error` envelope returned by https://api.deezer.com plus
transport-level failures. See https://developers.deezer.com/api/errors.
"""

from __future__ import annotations


class DeezerError(Exception):
    """Base class for every error raised by this SDK."""


class DeezerAPIError(DeezerError):
    """The Deezer API answered with an ``{"error": {...}}`` envelope."""

    #: Human readable mapping of documented error codes.
    #: https://developers.deezer.com/api/errors
    CODE_DESCRIPTIONS = {
        4: "Quota exceeded (QUOTA)",
        100: "Items limit exceeded (ITEMS_LIMIT_EXCEEDED)",
        200: "Missing/insufficient permission (PERMISSION)",
        300: "Invalid or expired access token (TOKEN_INVALID)",
        500: "Invalid parameter value (PARAMETER)",
        501: "Missing required parameter (PARAMETER_MISSING)",
        600: "Invalid query (QUERY_INVALID)",
        700: "Service busy, retry later (SERVICE_BUSY)",
        800: "Requested data not found (DATA_NOT_FOUND)",
        901: "Operation not allowed on an individual account "
        "(INDIVIDUAL_ACCOUNT_NOT_ALLOWED)",
    }

    def __init__(
        self,
        error_type: str,
        message: str,
        code: int,
        *,
        status_code: int | None = None,
        endpoint: str | None = None,
    ) -> None:
        self.type = error_type
        self.message = message
        self.code = code
        self.status_code = status_code
        self.endpoint = endpoint
        detail = self.CODE_DESCRIPTIONS.get(code, "")
        hint = f" — {detail}" if detail else ""
        where = f" [{endpoint}]" if endpoint else ""
        super().__init__(f"Deezer API error {code} ({error_type}){where}: {message}{hint}")

    @classmethod
    def from_payload(
        cls, payload: dict, *, status_code: int | None = None, endpoint: str | None = None
    ) -> "DeezerAPIError":
        err = payload.get("error") or {}
        return cls(
            str(err.get("type", "Exception")),
            str(err.get("message", "Unknown Deezer API error")),
            int(err.get("code", 0)),
            status_code=status_code,
            endpoint=endpoint,
        )


class DeezerTransportError(DeezerError):
    """Network / HTTP / decoding failure (no usable API envelope)."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        self.message = message
        self.status_code = status_code
        suffix = f" (HTTP {status_code})" if status_code is not None else ""
        super().__init__(f"{message}{suffix}")


class DeezerAuthError(DeezerError):
    """OAuth helper misuse (missing app_id/secret, bad callback payload...)."""
