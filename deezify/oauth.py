"""OAuth 2.0 helpers for the Deezer API.

Deezer supports a **server-side flow** and a **client-side (implicit) flow**::

    https://developers.deezer.com/api/oauth

Server-side (recommended when you own a web server):

1. Redirect the user to :func:`authorization_url`.
2. Deezer redirects back to your ``redirect_uri`` with ``?code=...``.
3. Exchange the code with :meth:`DeezerClient.exchange_code_for_token`.

Client-side (browser / mobile apps without a server secret):

1. Redirect the user to :func:`authorization_url` with
   ``response_type="token"``.
2. Deezer redirects back with the token in the URL fragment
   (``#access_token=...&expires=...``); parse it with
   :func:`parse_implicit_callback_fragment`.
"""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode

from .enums import Permission

AUTH_URL = "https://connect.deezer.com/oauth/auth.php"
TOKEN_URL = "https://connect.deezer.com/oauth/access_token.php"

#: Documented permissions — https://developers.deezer.com/api/permissions
#: Back-compat tuple; prefer :class:`~deezify.enums.Permission`.
PERMISSIONS = tuple(Permission.values())

#: Accepted type for ``perms`` arguments (raw string, enum member, or list).
PermsArg = str | Permission | list[str | Permission] | tuple[str | Permission, ...]


def _normalize_perms(
    perms: str | Permission | list[str | Permission] | tuple[str | Permission, ...],
) -> str:
    """Normalize ``perms`` to the comma-separated wire string, validating names."""
    if isinstance(perms, Permission):
        return perms.value
    if isinstance(perms, (list, tuple)):
        parts = [Permission.coerce(p, label="permission") for p in perms]
        return ",".join(parts) or "basic_access"
    text = (perms or "basic_access").strip() if isinstance(perms, str) else "basic_access"
    if not text:
        return "basic_access"
    return ",".join(
        Permission.coerce(part.strip(), label="permission")
        for part in text.split(",")
        if part.strip()
    ) or "basic_access"


def authorization_url(
    app_id: str | int,
    redirect_uri: str,
    perms: str | Permission | list[str | Permission] | tuple[str | Permission, ...] = "basic_access",
    *,
    response_type: str | None = None,
    state: str | None = None,
) -> str:
    """Build the URL that starts the OAuth login/consent dialog.

    Args:
        app_id: Your Deezer application id.
        redirect_uri: Where Deezer redirects the user afterwards. It must
            live under the domain registered for the application.
        perms: Permission names — a comma string, a list, or
            :class:`~deezify.enums.Permission` members, e.g.
            ``"basic_access,email"`` or ``[Permission.EMAIL]``.
        response_type: Pass ``"token"`` for the client-side (implicit) flow,
            omit it for the server-side (code) flow.
        state: Opaque CSRF token echoed back by Deezer; always verify it.
    """
    params: dict[str, str] = {
        "app_id": str(app_id),
        "redirect_uri": redirect_uri,
        "perms": _normalize_perms(perms),
    }
    if response_type:
        params["response_type"] = response_type
    if state:
        params["state"] = state
    return f"{AUTH_URL}?{urlencode(params)}"


def implicit_authorization_url(
    app_id: str | int,
    redirect_uri: str,
    perms: str | Permission | list[str | Permission] | tuple[str | Permission, ...] = "basic_access",
    *,
    state: str | None = None,
) -> str:
    """Shortcut for :func:`authorization_url` with ``response_type="token"``."""
    return authorization_url(
        app_id, redirect_uri, perms, response_type="token", state=state
    )


def token_exchange_url(app_id: str | int, secret: str, code: str) -> str:
    """Build the server-side ``access_token.php`` URL for a given code."""
    return (
        f"{TOKEN_URL}?{urlencode({'app_id': str(app_id), 'secret': secret, 'code': code})}"
    )


def parse_token_response(body: str) -> dict:
    """Parse the ``access_token.php`` response body.

    Without ``output=json`` Deezer answers with a query-string body
    (``access_token=...&expires=...``); with ``output=json`` it answers JSON.
    This helper accepts both and always returns a dict.
    """
    text = (body or "").strip()
    if not text:
        return {}
    if text.startswith("{"):
        import json

        try:
            data = json.loads(text)
        except ValueError:
            return {}
        return data if isinstance(data, dict) else {}
    if "=" not in text:
        return {"access_token": text}
    parsed = dict(parse_qsl(text, keep_blank_values=True))
    if "access_token" not in parsed and text:
        parsed.setdefault("access_token", text)
    return parsed


def parse_implicit_callback_fragment(fragment: str) -> dict:
    """Parse the ``#access_token=...&expires=...`` fragment of the
    client-side flow redirect into a dict."""
    fragment = (fragment or "").lstrip("#")
    return dict(parse_qsl(fragment, keep_blank_values=True))

