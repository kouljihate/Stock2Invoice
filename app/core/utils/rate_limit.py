"""In-memory sliding-window rate limiting for unauthenticated endpoints.

Deliberately dependency-free: the app runs as a single process in development
and per-worker here, so counters live in process memory. If the app is ever
scaled across hosts, back this with a shared store (Redis, MongoDB) instead.

Note that ``request.remote_addr`` is the direct peer address; behind a reverse
proxy that is the proxy unless a trusted ``X-Forwarded-For`` is configured.
"""

import threading
import time
from collections import defaultdict, deque

from flask import request

_lock = threading.Lock()
_buckets = defaultdict(deque)  # key -> deque of monotonic timestamps
_MAX_BUCKETS = 20000


def client_ip():
    return request.remote_addr or 'unknown'


def check_rate_limit(key, limit, window_seconds):
    """Record one hit for ``key``. Returns True when the caller is over limit."""
    now = time.monotonic()
    cutoff = now - window_seconds
    with _lock:
        if len(_buckets) > _MAX_BUCKETS:
            _prune_locked(cutoff)
        hits = _buckets[key]
        while hits and hits[0] <= cutoff:
            hits.popleft()
        if len(hits) >= limit:
            return True
        hits.append(now)
        return False


def _prune_locked(cutoff):
    stale = [k for k, v in _buckets.items() if not v or v[-1] <= cutoff]
    for k in stale:
        _buckets.pop(k, None)


def reset_limits():
    """Drop all counters (used by tests)."""
    with _lock:
        _buckets.clear()
