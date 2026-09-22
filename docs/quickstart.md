# Quickstart

Install (Python ≥ 3.9):

```bash
pip install deezify
```

## Sync — public catalogue, no auth

```python
from deezify import DeezerClient, SearchOrder

with DeezerClient() as client:
    track = client.track.get(3135556)
    print(track["title"], "-", track["artist"]["name"])

    for t in client.search.tracks("eminem", order=SearchOrder.RANKING, limit=5):
        print(t["title"], t.get("rank"))

    print([t["title"] for t in client.top_tracks(limit=5)])
    print([g["name"] for g in client.genres(limit=5)])
```

## Async — identical API with `await`

```python
import asyncio
from deezify import AsyncDeezerClient

async def main():
    async with AsyncDeezerClient() as client:
        print(await client.find_track("Daft Punk", limit=2))
        print(await client.top_artists(limit=3))

asyncio.run(main())
```

## Pagination

List endpoints return a [`PaginatedList`](api/paginator.md):

```python
page = client.playlist.tracks(908622995, index=0, limit=10)
print(page.total)
first = page[0]

for track in page.iter_all_items():   # walks every page via `next`
    ...
```

## Rate limiting

On by default (50 requests / 5 s sliding window, retries on quota/busy):

```python
DeezerClient()                                        # default budget
DeezerClient(rate_limit=False)                        # opt out
from deezify.ratelimit import SyncRateLimiter
DeezerClient(rate_limit=SyncRateLimiter(max_calls=10, period=5.0))
```

Details: [Rate limiting](rate-limit.md).

## Next steps

- [Authentication (OAuth)](auth.md) — favorites, playlists, history
- [Enums](enums.md) — `SearchOrder`, `Permission`, …
- [High-level helpers](high-level.md) — `find_*`, `top_*`, `full_track`, …

