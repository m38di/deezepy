# High-level helpers

Shortcuts available on **both** clients (sync returns values, async uses `await`).
They return plain `list`s / `dict`s — no paging boilerplate.

```python
client.find_track("Daft Punk", limit=5)
client.find_album("Discovery", limit=5)
client.find_artist("Daft Punk", limit=5)
client.find_playlist("workout", limit=5)
client.find_podcast("news", limit=5)
client.best_track_match("eminem")        # first hit or None
client.best_album_match("Discovery")
client.best_artist_match("Daft Punk")

client.top_tracks(limit=10)
client.top_albums(limit=10)
client.top_artists(limit=10)
client.top_playlists(limit=10)
client.top_podcasts(limit=10)
client.genre_top_tracks(132, limit=10)   # genre charts
client.genres(limit=50)
client.new_releases(limit=10)
client.editorial_selection(limit=10)

client.artist_top_tracks(27, limit=10)
client.artist_albums(27, limit=25)
client.artist_related(27, limit=10)
client.artist_radio_tracks(27, limit=25)
client.album_tracks(302127)
client.playlist_tracks(908622995, limit=10)
client.playlist_all_tracks(908622995)    # walks all pages
client.radio_tracks(38305, limit=25)
client.podcast_episodes(1523, limit=25)

client.full_track(3135556)               # {"track", "album", "artist"}
client.full_album(302127)                # {"album", "artist"}
client.track_preview_url(3135556)        # 30 s mp3 or None

# Needs an access token:
client.me()
client.my_playlists()
client.my_favorite_tracks()
client.my_favorite_albums()
client.my_favorite_artists()
client.my_flow()
client.create_playlist("My mix")
client.add_to_playlist(playlist_id, [3135556])
```

::: deezify.highlevel

