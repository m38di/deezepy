"""Basic sync usage — public endpoints, no auth needed."""

from deezify import DeezerClient


def main() -> None:
    with DeezerClient() as client:
        track = client.track.get(3135556)
        print(f"Track: {track['title']} — {track['artist']['name']}")

        album = client.album.get(302127)
        print(f"Album: {album['title']} ({album['release_date']})")

        artist = client.artist.get(27)
        print(f"Artist: {artist['name']} — {artist['nb_fan']} fans")

        print("\nTop tracks:")
        for t in client.artist.top(27, limit=5):
            print(f"  - {t['title']}")

        print("\nSearch 'Daft Punk':")
        for t in client.search.all("Daft Punk", limit=5):
            print(f"  - {t['title']} — {t['artist']['name']}")

        print("\nGlobal chart tracks:")
        for t in client.chart.tracks(limit=5):
            print(f"  - {t['title']}")

        print("\nCountry:", client.infos.get().get("country"))
        print("Genres:", [g["name"] for g in client.genre.list(limit=5)])


if __name__ == "__main__":
    main()

