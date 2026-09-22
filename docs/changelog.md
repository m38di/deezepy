# Changelog

## 1.0.0 — 2026-09-22

Initial public release.

- Full Deezer API coverage: track, album, artist, playlist, podcast, episode, user,
  search, chart, editorial, genre, radio, infos, options, oEmbed, all write actions.
- Sync (`DeezerClient`) + async (`AsyncDeezerClient`) clients.
- Sliding-window rate limiting (50 requests / 5 s) with quota/busy retries.
- `str`-compatible enums (`SearchOrder`, `Permission`, …).
- Typed responses (`Track`, `Album`, `Chart`, …) with `PaginatedList[T]`.
- ~35 high-level shortcuts (`find_*`, `top_*`, `full_track`, `my_*`, …).
- OAuth server-side + implicit flows.
