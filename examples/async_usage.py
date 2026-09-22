"""Async usage — mirrors the sync client method-for-method."""

import asyncio

from deezify import AsyncDeezerClient


async def main() -> None:
    async with AsyncDeezerClient() as client:
        track = await client.track.get(3135556)
        print(f"Track: {track['title']} — {track['artist']['name']}")

        results = await client.search.all("Daft Punk", limit=5)
        for t in results:
            print(f"  - {t['title']}")

        chart = await client.chart.tracks(limit=5)
        print(f"Chart tracks: {len(chart)} (total={chart.total})")


if __name__ == "__main__":
    asyncio.run(main())

