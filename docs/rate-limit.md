# Rate limiting

Deezer documents a quota of **50 requests per 5 seconds**. Exceeding it returns error
code 4 (`QUOTA`); an overloaded backend returns code 700 (`SERVICE_BUSY`).

The SDK throttles automatically with a sliding-window limiter and retries quota/busy
failures with exponential backoff + jitter:

```python
from deezify import DeezerClient, AsyncDeezerClient
from deezify.ratelimit import SyncRateLimiter, AsyncRateLimiter

DeezerClient()                                              # 50 / 5 s + 3 retries
DeezerClient(rate_limit=False)                              # opt out entirely
DeezerClient(rate_limit=SyncRateLimiter(max_calls=10, period=5.0))
DeezerClient(max_retries=5, retry_base=1.0)                 # retry tuning
AsyncDeezerClient(rate_limit=AsyncRateLimiter(max_calls=10, period=5.0))
```

- The sync limiter is thread-safe; the async one uses an `asyncio.Lock`.
- `acquire()` blocks just long enough to fit the budget — no requests are dropped.
- Retries cover API codes 4/700 and HTTP 429/502/503/504 only; other errors (e.g. 800
  not-found, 200 permission) raise immediately.
- `PaginatedList.iter_all_items()` benefits automatically — long walks stay in budget.

::: deezify.ratelimit

