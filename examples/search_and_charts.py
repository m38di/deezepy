"""Advanced search, pagination, charts/editorial, oEmbed."""

from deezify import DeezerClient


def main() -> None:
    with DeezerClient() as client:
        print("Advanced search (artist + track):")
        page = client.search.advanced(
            "search", artist="Aloe Blacc", track="I Need A Dollar"
        )
        for t in page:
            print(f"  - {t['title']} — {t['artist']['name']}")

        print("\nOrdered track search:")
        for t in client.search.tracks("eminem", order="RANKING", limit=3):
            print(f"  - {t['title']} (rank {t.get('rank')})")

        print("\nPlaylist tracks with pagination:")
        tracks = client.playlist.tracks(908622995, limit=3)
        print(f"  total={tracks.total}, first page={len(tracks)}")

        print("\nChart albums:")
        for a in client.chart.albums(limit=3):
            print(f"  - {a['title']} — {a['artist']['name']}")

        print("\nEditorial selection:")
        for a in client.editorial.selection(limit=3):
            print(f"  - {a['title']}")

        print("\noEmbed:")
        embed = client.oembed.get("https://www.deezer.com/album/302127")
        print(f"  {embed['title']} by {embed['author_name']}")


if __name__ == "__main__":
    main()

