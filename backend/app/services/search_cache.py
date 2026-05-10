from __future__ import annotations

import hashlib
import json
import threading
import time
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

_DEFAULT_TTL_SECONDS = 300.0


@dataclass(slots=True)
class _CacheEntry:
    value: Any
    expires_at: float


_CACHE: dict[str, _CacheEntry] = {}
_CACHE_LOCK = threading.RLock()


def _now() -> float:
    return time.monotonic()


def _purge_expired_unlocked() -> None:
    now = _now()
    expired = [key for key, entry in _CACHE.items() if entry.expires_at <= now]
    for key in expired:
        _CACHE.pop(key, None)


def make_cache_key(namespace: str, payload: Any) -> str:
    """Create a deterministic cache key from structured search inputs."""
    serialized = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return f"{namespace}:{digest}"


def get_cached(key: str, default: Any = None) -> Any:
    with _CACHE_LOCK:
        entry = _CACHE.get(key)
        if entry is None:
            return default
        if entry.expires_at <= _now():
            _CACHE.pop(key, None)
            return default
        return deepcopy(entry.value)


def set_cached(key: str, value: Any, ttl_seconds: float = _DEFAULT_TTL_SECONDS) -> None:
    ttl = max(float(ttl_seconds), 1.0)
    with _CACHE_LOCK:
        _CACHE[key] = _CacheEntry(value=deepcopy(value), expires_at=_now() + ttl)
        _purge_expired_unlocked()


def invalidate_cache(key: str | None = None, *, prefix: str | None = None) -> None:
    with _CACHE_LOCK:
        if key is not None:
            _CACHE.pop(key, None)
            return
        if prefix is None:
            _CACHE.clear()
            return
        for cache_key in list(_CACHE):
            if cache_key.startswith(prefix):
                _CACHE.pop(cache_key, None)


def cache_size() -> int:
    with _CACHE_LOCK:
        _purge_expired_unlocked()
        return len(_CACHE)

