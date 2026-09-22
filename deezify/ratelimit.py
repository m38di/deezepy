"""Sliding-window rate limiter (50 requests / 5 s by default) + retry.

Deezer documents a quota of **50 requests per 5 seconds**
(https://developers.deezer.com/api). Exceeding it answers with error code 4
(``QUOTA``); an overloaded backend answers with code 700 (``SERVICE_BUSY``).

This module provides:

- :class:`SyncRateLimiter` — thread-safe sliding-window throttle used by the
  sync client. ``acquire()`` blocks just long enough to stay inside the
  budget instead of failing.
- :class:`AsyncRateLimiter` — same contract for ``asyncio`` code, using an
  ``asyncio.Lock`` instead of threads.
- :func:`should_retry` / :func:`retry_delay` — helpers deciding whether a
  failed call deserves another attempt and how long to wait.

Both limiters are no-ops when constructed with ``max_calls=None`` (or
``max_calls <= 0``), so users running their own throttling can fully opt out
via ``DeezerClient(rate_limit=False)``.
"""

from __future__ import annotations

import asyncio
import random
import threading
import time
from collections import deque
from typing import Any

#: Deezer's documented quota: 50 requests per 5 seconds.
DEFAULT_MAX_CALLS = 50
DEFAULT_PERIOD = 5.0

#: How many times a quota/busy failure is retried (after the first attempt).
DEFAULT_MAX_RETRIES = 3
#: Base backoff in seconds; actual sleep is ``base * 2**attempt + jitter``.
DEFAULT_RETRY_BASE = 0.5
#: Upper bound for a single backoff sleep.
DEFAULT_RETRY_MAX = 8.0

#: API error codes worth retrying (quota exceeded / service busy).
RETRYABLE_CODES = frozenset({4, 700})
#: HTTP statuses worth retrying (rate limited / transient server errors).
RETRYABLE_STATUSES = frozenset({429, 502, 503, 504})


def should_retry(
    *,
    error: Any | None = None,
    status_code: int | None = None,
    attempt: int = 0,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> bool:
    """Return True when a failed attempt should be retried.

    Args:
        error: A :class:`~deezify.errors.DeezerAPIError`, or None for pure
            HTTP failures.
        status_code: HTTP status of the failed response, if known.
        attempt: Zero-based number of the attempt that just failed.
        max_retries: Maximum number of *retries* (not total attempts).
    """
    if attempt >= max_retries:
        return False
    code = getattr(error, "code", None)
    if isinstance(code, int) and code in RETRYABLE_CODES:
        return True
    if error is None and status_code in RETRYABLE_STATUSES:
        return True
    return False


def retry_delay(
    attempt: int,
    *,
    base: float = DEFAULT_RETRY_BASE,
    cap: float = DEFAULT_RETRY_MAX,
    jitter: float = 0.25,
) -> float:
    """Exponential backoff with jitter for retry ``attempt`` (0-based)."""
    delay = min(cap, base * (2.0**attempt))
    if jitter > 0:
        delay += random.uniform(0, jitter)
    return delay


class SyncRateLimiter:
    """Thread-safe sliding-window throttle.

    Args:
        max_calls: Max requests per ``period`` seconds. ``None``/``<= 0``
            disables throttling.
        period: Window length in seconds.
    """

    def __init__(
        self, max_calls: int | None = DEFAULT_MAX_CALLS, period: float = DEFAULT_PERIOD
    ) -> None:
        self.max_calls = max_calls
        self.period = float(period)
        self._lock = threading.Lock()
        self._hits: deque[float] = deque()

    @property
    def enabled(self) -> bool:
        return bool(self.max_calls) and (self.max_calls or 0) > 0 and self.period > 0

    def _prune(self, now: float) -> None:
        assert self.max_calls
        cutoff = now - self.period
        hits = self._hits
        while hits and hits[0] <= cutoff:
            hits.popleft()

    def acquire(self) -> None:
        """Block until the call fits inside the budget, then record it."""
        if not self.enabled:
            return
        assert self.max_calls
        while True:
            with self._lock:
                now = time.monotonic()
                self._prune(now)
                if len(self._hits) < self.max_calls:
                    self._hits.append(now)
                    return
                wait = self._hits[0] + self.period - now
            time.sleep(max(wait, 0.001))

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"SyncRateLimiter(max_calls={self.max_calls}, period={self.period})"


class AsyncRateLimiter:
    """``asyncio`` sliding-window throttle with the same contract."""

    def __init__(
        self, max_calls: int | None = DEFAULT_MAX_CALLS, period: float = DEFAULT_PERIOD
    ) -> None:
        self.max_calls = max_calls
        self.period = float(period)
        self._lock = asyncio.Lock()
        self._hits: deque[float] = deque()

    @property
    def enabled(self) -> bool:
        return bool(self.max_calls) and (self.max_calls or 0) > 0 and self.period > 0

    async def acquire(self) -> None:
        if not self.enabled:
            return
        assert self.max_calls
        loop = asyncio.get_running_loop()
        while True:
            async with self._lock:
                now = loop.time()
                cutoff = now - self.period
                while self._hits and self._hits[0] <= cutoff:
                    self._hits.popleft()
                if len(self._hits) < self.max_calls:
                    self._hits.append(now)
                    return
                wait = self._hits[0] + self.period - now
            await asyncio.sleep(max(wait, 0.001))

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"AsyncRateLimiter(max_calls={self.max_calls}, period={self.period})"

