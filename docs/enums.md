# Enums

All enums are `str`-based: members compare equal to and serialize exactly like their raw
API strings, so plain strings keep working everywhere.

```python
from deezify import SearchOrder, Permission, RecommendationKind

SearchOrder.RANKING == "RANKING"          # True
str(SearchOrder.TRACK_ASC)                # "TRACK_ASC"

client.search.tracks("eminem", order=SearchOrder.RANKING, limit=5)
client.search.tracks("eminem", order="RANKING", limit=5)   # identical
client.user.recommendations("me", RecommendationKind.TRACKS)
authorization_url(APP_ID, REDIRECT, perms=[Permission.EMAIL])
```

| Enum | Values |
|---|---|
| `SearchOrder` | `RANKING TRACK_ASC TRACK_DESC ARTIST_ASC ARTIST_DESC ALBUM_ASC ALBUM_DESC RATING_ASC RATING_DESC DURATION_ASC DURATION_DESC` |
| `SearchField` | `artist album track label dur_min dur_max bpm_min bpm_max` |
| `Permission` | `basic_access email offline_access manage_library manage_community delete_library listening_history` |
| `RecommendationKind` | `albums artists playlists tracks radios releases` |
| `UserChartKind` | `albums playlists tracks` |
| `OEmbedFormat` | `json xml` (only `json` is decoded) |
| `EntityType` | `track album artist playlist user podcast episode radio genre editorial options chart` |
| `Gender` / `RecordType` / `ExplicitContentLevel` | typing helpers for `user`/`album` fields |

::: deezify.enums

