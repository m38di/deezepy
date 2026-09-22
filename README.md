# deezify

A complete, typed Python SDK for the [Deezer API](https://developers.deezer.com/api) — every documented object, connection, search mode, write action, and the OAuth 2.0 login flows. Sync **and** async clients included.

- Base URL `https://api.deezer.com`, quota `50 requests / 5 seconds`
- No API key or login needed for public catalogue endpoints (track/album/artist/…)
- `access_token` (OAuth) only for user-private actions (favorites, playlists, history…)
- Paginated collections with `index`/`limit`, `next`/`prev` walking, and `iter_all_items()`
- Built-in rate limiting (50 requests / 5 s sliding window) with automatic
  retry on quota/busy responses — disable with `DeezerClient(rate_limit=False)`
- Typed responses: `Track`, `Album`, `Artist`, `Playlist`, `User`, `Chart`,
  … with `PaginatedList[Track]` collections and IDE autocompletion
- Typed dicts for every object, structured `DeezerAPIError` with documented codes

## Install

```bash
pip install deezify
```

Requires Python ≥ 3.9 and [httpx](https://www.python-httpx.org/).

## Quick start (no auth)

```python
from deezify import DeezerClient

client = DeezerClient()

track = client.track.get(3135556)          # "Harder, Better, Faster, Stronger"
print(track["title"], track["artist"]["name"])

results = client.search.all("Daft Punk", limit=5)
for t in results:
    print(t["title"], "-", t["artist"]["name"])

top = client.artist.top(27)                # top tracks of an artist
albums = client.chart.albums(limit=10)     # global chart albums
print(client.infos.get()["country"])       # country info
```

Async works the same way:

```python
import asyncio
from deezify import AsyncDeezerClient

async def main():
    async with AsyncDeezerClient() as client:
        track = await client.track.get(3135556)
        print(track["title"])

asyncio.run(main())
```

## Authenticated usage (OAuth)

```python
from deezify import DeezerClient, authorization_url

# 1. Send the user to this URL (server-side flow)
url = authorization_url(
    app_id="YOUR_APP_ID",
    redirect_uri="https://your-app.example/callback",
    perms="basic_access,email,offline_access",
    state="random-csrf-token",
)

# 2. Deezer redirects back with ?code=... — exchange it:
client = DeezerClient()
token = client.exchange_code_for_token("YOUR_APP_ID", "YOUR_APP_SECRET", code)
client.set_access_token(token["access_token"])

me = client.user.me()
print(me["name"])
client.playlist.add_tracks(playlist_id=123, track_ids=[3135556])
```

For browser/mobile apps without a server secret, use the implicit flow:

```python
from deezify import implicit_authorization_url, parse_implicit_callback_fragment

url = implicit_authorization_url("YOUR_APP_ID", "https://your-app.example/cb")
# ...after redirect, fragment looks like "access_token=...&expires=...":
token = parse_implicit_callback_fragment(fragment)
```

Needed permissions per action are documented on each method; the permission
names are `basic_access, email, offline_access, manage_library,
manage_community, delete_library, listening_history`.

## Coverage

| Area | Methods |
|---|---|
| Track | `get`, `update_personal`, `delete_personal`, favorites add/remove |
| Album | `get`, `fans`, `tracks`, library add/remove |
| Artist | `get`, `top`, `albums`, `fans`, `related`, `radio`, `playlists`, favorites add/remove |
| Playlist | `get`, `fans`, `tracks`, `radio`, `update`, `delete`, `mark_seen`, `add_tracks`, `reorder_tracks`, `remove_tracks`, favorites add/remove |
| Podcast / Episode | `get`, `episodes`, bookmark get/set/remove, favorites add/remove |
| User | `get`/`me`, `albums`, `artists`, `tracks`, `playlists`, `podcasts`, `radios`, `followings`, `followers`, `flow`, `history`, `personal_songs`, `charts_*`, `recommendations/*`, `permissions`, `options`, `create_playlist`, `follow`/`unfollow`, `add_notification` |
| Search | `all`, `tracks`, `albums`, `artists`, `playlists`, `podcasts`, `radios`, `users`, `advanced(...)` field search, `history` |
| Chart | `get` (+ genre charts), `tracks`, `albums`, `artists`, `playlists`, `podcasts` |
| Editorial | `get`/`list`, `selection`, `charts`, `releases` |
| Genre | `get`/`list`, `artists`, `podcasts`, `radios` |
| Radio | `get`/`list`, `genres`, `top`, `tracks`, `lists`, favorites add/remove |
| Infos / Options | `get` |
| oEmbed | `get` (widget metadata for public Deezer URLs) |

Advanced search example:

```python
page = client.search.advanced("search", artist="Aloe Blacc", track="I Need A Dollar")
page = client.search.tracks("eminem", strict=True, order="RANKING", limit=10)
```

Pagination:

```python
page = client.playlist.tracks(908622995, index=0, limit=10)
print(page.total)
for track in page.iter_all_items():   # walks every page via `next`
    ...
```

Rate limiting:

```python
# default: 50 requests / 5 s + retries on quota (code 4) / busy (code 700)
client = DeezerClient()

# opt out (you run your own throttling)
client = DeezerClient(rate_limit=False)

# custom budget
from deezify.ratelimit import SyncRateLimiter
client = DeezerClient(rate_limit=SyncRateLimiter(max_calls=10, period=5.0))
```

Typed responses:

High-level shortcuts (same names on the async client with `await`):

```python
client.find_track("Daft Punk", limit=5)   # plain lists, no paging needed
client.best_artist_match("Daft Punk")      # first hit or None
client.top_tracks(limit=10)                  # global charts
client.genres(limit=10)                      # genre list
client.album_tracks(302127)                  # every album track
client.playlist_all_tracks(908622995)        # walks all pages
client.full_track(3135556)                   # track + full album + artist
client.track_preview_url(3135556)            # 30s mp3 or None
client.my_playlists()                        # needs access token
```

Enums (all `str`-compatible — plain strings keep working too):

```python
from deezify import SearchOrder, Permission, RecommendationKind

client.search.tracks("eminem", order=SearchOrder.RANKING)
client.search.tracks("eminem", order="RANKING")  # same thing
client.user.recommendations("me", RecommendationKind.TRACKS)
authorization_url(APP_ID, REDIRECT, perms=[Permission.EMAIL])
```

```python
from deezify import Track
from deezify.types import Chart, Playlist

track: Track = client.track.get(3135556)
bundle: Chart = client.chart.get()
top_track = client.artist.top(27, limit=1)[0]  # inferred as Track
```

Raw escape hatch for anything new/experimental:

```python
client.raw("GET", "track/3135556")
```

## Error handling

```python
from deezify import DeezerAPIError, DeezerTransportError

try:
    client.track.get(0)
except DeezerAPIError as e:
    print(e.code, e.type, e.message)   # e.g. 800 DataException ...
except DeezerTransportError as e:
    print("network problem:", e)
```

Documented codes: `4` quota, `100` items limit, `200` permission,
`300` bad token, `500`/`501` parameters, `600` bad query, `700` busy,
`800` not found, `901` individual-account restriction.

## Docs & links

- API reference: https://developers.deezer.com/api
- OAuth: https://developers.deezer.com/api/oauth
- Permissions: https://developers.deezer.com/api/permissions
- Errors: https://developers.deezer.com/api/errors

## License

MIT

