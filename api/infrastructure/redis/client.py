"""Redis set and cache client wrapper."""
from __future__ import annotations

import json
from typing import Any, Set

import redis

from lib.settings import get_settings

# Default TTLs
THIRTY_DAYS_SECONDS = 30 * 24 * 60 * 60
TEN_MINUTES_SECONDS = 10 * 60


class RedisSetClient:
    """
    Redis client wrapper providing set operations and JSON-serialised key caching.

    When *host* and *password* are omitted they are read from settings at
    construction time (not at import time), keeping tests easy to configure.
    """

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        db: int = 0,
        password: str | None = None,
    ) -> None:
        settings = get_settings()
        resolved_host = host if host is not None else settings.redis_host
        resolved_port = port if port is not None else settings.redis_port
        resolved_password = (
            password if password is not None else settings.redis_password
        )
        self.client = redis.Redis(
            host=resolved_host,
            port=resolved_port,
            db=db,
            decode_responses=True,
            password=resolved_password,
        )

    # ------------------------------------------------------------------
    # Set operations
    # ------------------------------------------------------------------

    def add_to_set(self, set_name: str, value: str) -> bool:
        """
        Add *value* to a Redis set, resetting its 30-day expiration.

        Returns:
            ``True`` if the value was newly added, ``False`` if already present.
        """
        added = bool(self.client.sadd(set_name, value))
        self.client.expire(set_name, THIRTY_DAYS_SECONDS)
        return added

    def get_set(self, set_name: str) -> Set[str]:
        """Return all members of *set_name* as a Python ``set``."""
        return set(self.client.smembers(set_name))  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Generic key cache
    # ------------------------------------------------------------------

    def set_cache(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = TEN_MINUTES_SECONDS,
    ) -> bool:
        """
        Serialise *value* as JSON and store it under *key* with *ttl_seconds* TTL.

        Returns:
            ``True`` if stored successfully.
        """
        try:
            serialized = json.dumps(value, default=str)
            return bool(self.client.setex(key, ttl_seconds, serialized))
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    def get_cache(self, key: str) -> Any | None:
        """Return the deserialised cached value for *key*, or ``None``."""
        try:
            raw = self.client.get(key)
            if raw:
                # redis sync client returns str with decode_responses=True
                return json.loads(raw)  # type: ignore[arg-type]
            return None
        except Exception:  # pylint: disable=broad-exception-caught
            return None

    def delete_cache(self, key: str) -> bool:
        """Delete *key* from the cache. Returns ``True`` if it existed."""
        return bool(self.client.delete(key))

    def delete_cache_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching *pattern*.

        Returns:
            Number of keys deleted.
        """
        keys = self.client.keys(pattern)
        if keys:
            return int(self.client.delete(*keys))  # type: ignore[arg-type, return-value]  # redis stubs
        return 0
