"""Rate limiting + typed responses."""

import asyncio

from deezify import AsyncDeezerClient, DeezerClient, Track


def main() -> None:
    # Default: 50 requests / 5 s sliding window + retries on quota/busy.
    # Disable with rate_limit=False; tune with max_retries=/retry_base=.
    # A custom budget: from deezify.ratelimit import SyncRateLimiter
    # DeezerClient(rate_limit=SyncRateLimiter(max_calls=10, period=5.0))
    with DeezerClient() as client:
        track: Track = client.track.get(3135556)
        print(f"Track: {track['title']} — {track['artist']['name']}")

        # Collections are typed too: PaginatedList[Track], ...
        top = client.artist.top(27, limit=3)
        first = top[0]
        print(f"Top: {first['title']} (rank {first.get('rank')})")

        bundle = client.chart.get()
        print("Chart tracks:", bundle["tracks"]["data"][0]["title"])


async def amain() -> None:
    async with AsyncDeezerClient() as client:
        track = await client.track.get(3135556)
        print(f"Async track: {track['title']}")


if __name__ == "__main__":
    main()
    asyncio.run(amain())

