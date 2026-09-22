# deezify

A complete, typed Python SDK for the [Deezer API](https://developers.deezer.com/api) — every documented object, connection, search mode, write action, and the OAuth 2.0 login flows. Sync **and** async clients included.

```bash
pip install deezify
```

```python
from deezify import DeezerClient

client = DeezerClient()
track = client.track.get(3135556)   # "Harder, Better, Faster, Stronger"
print(track["title"], "-", track["artist"]["name"])
print(client.find_track("Daft Punk", limit=3)[0]["title"])
```

- **No API key** needed for public catalogue endpoints.
- Built-in **rate limiting** (50 requests / 5 s) with automatic retry on quota/busy.
- **Typed responses** (`Track`, `Album`, `Chart`, …) and **str-compatible enums** (`SearchOrder`, `Permission`, …).
- **High-level shortcuts** on both clients (`find_track`, `top_tracks`, `full_track`, `my_playlists`, …).
- Sync (`DeezerClient`) and async (`AsyncDeezerClient`) with identical APIs.

Start with [Quickstart](quickstart.md), then [Authentication](auth.md) for user-private actions.
Browse the full [API reference](api/client.md). API data belongs to Deezer — see the [official docs](https://developers.deezer.com/api).

