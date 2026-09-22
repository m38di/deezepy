# Authentication (OAuth 2.0)

Public catalogue endpoints need **no login**. An `access_token` is only required for
user-private actions (favorites, playlists, flow, history, `user/me`).

## Server-side flow (recommended when you own a server)

```python
from deezify import DeezerClient, Permission, authorization_url

url = authorization_url(
    app_id="YOUR_APP_ID",
    redirect_uri="https://your-app.example/callback",
    perms=[Permission.BASIC_ACCESS, Permission.EMAIL, Permission.OFFLINE_ACCESS],
    state="random-csrf-token",   # always verify it on return
)
# 1. Send the user to `url`.
# 2. Deezer redirects back to your redirect_uri with `?code=...`.

client = DeezerClient()
token = client.exchange_code_for_token("YOUR_APP_ID", "YOUR_APP_SECRET", code)
client.set_access_token(token["access_token"])

print(client.user.me()["name"])
client.playlist.add_tracks(playlist_id=123, track_ids=[3135556])
```

## Client-side (implicit) flow

For browser/mobile apps with no server secret:

```python
from deezify import implicit_authorization_url, parse_implicit_callback_fragment

url = implicit_authorization_url("YOUR_APP_ID", "https://your-app.example/cb")
# After approval Deezer redirects with #access_token=...&expires=...
token = parse_implicit_callback_fragment(fragment)
```

## Permissions

| Enum | Value | Grants |
|---|---|---|
| `Permission.BASIC_ACCESS` | `basic_access` | name, profile picture |
| `Permission.EMAIL` | `email` | user's email |
| `Permission.OFFLINE_ACCESS` | `offline_access` | non-expiring token (`expires=0`) |
| `Permission.MANAGE_LIBRARY` | `manage_library` | add/order playlists & favorites |
| `Permission.MANAGE_COMMUNITY` | `manage_community` | follow/unfollow users |
| `Permission.DELETE_LIBRARY` | `delete_library` | delete library items |
| `Permission.LISTENING_HISTORY` | `listening_history` | recently-played tracks |

!!! warning "Keep your app secret server-side"
    Never ship `YOUR_APP_SECRET` in distributed/client-side code — use the implicit flow there.

