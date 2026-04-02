"""Redis-backed event list cache."""
from __future__ import annotations

import hashlib
from functools import lru_cache
from typing import Optional

from loguru import logger

from domain.event.models import CameraEvent, CameraEventQueryParams
from infrastructure.redis.client import RedisSetClient


class EventCacheService:
    """Cache for event list responses, backed by Redis with a 10-minute TTL."""

    _CACHE_PREFIX = "events"
    _TTL_SECONDS = 10 * 60

    def __init__(self) -> None:
        self._redis = RedisSetClient()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _generate_cache_key(self, params: CameraEventQueryParams) -> str:
        """Return a stable cache key derived from *params*."""
        param_dict = params.model_dump()
        sorted_items = sorted(param_dict.items())
        digest = hashlib.md5(str(sorted_items).encode()).hexdigest()
        return f"{self._CACHE_PREFIX}:{digest}"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_cached_events(
        self, params: CameraEventQueryParams
    ) -> list[CameraEvent] | None:
        """
        Return cached events for *params*, or ``None`` on a cache miss.

        Args:
            params: Query parameters used to look up the cache entry.
        """
        key = self._generate_cache_key(params)
        raw = self._redis.get_cache(key)
        if raw is not None:
            logger.info(f"Cache HIT for key: {key}")
            return [CameraEvent(**item) for item in raw]
        logger.info(f"Cache MISS for key: {key}")
        return None

    def cache_events(
        self, params: CameraEventQueryParams, events: list[CameraEvent]
    ) -> bool:
        """
        Store *events* in the cache under the key derived from *params*.

        Args:
            params: Query parameters used to generate the cache key.
            events: Events to serialise and store.

        Returns:
            ``True`` if the write succeeded.
        """
        key = self._generate_cache_key(params)
        payload = [event.model_dump() for event in events]
        success = self._redis.set_cache(key, payload, self._TTL_SECONDS)
        if success:
            logger.info(f"Cache SET for key: {key} with {len(events)} events")
        else:
            logger.error(f"Cache SET FAILED for key: {key}")
        return success

    def bust_cache(
        self, params: Optional[CameraEventQueryParams] = None
    ) -> int:
        """
        Delete cache entries.

        Args:
            params: When provided, only the entry for these params is deleted.
                    When ``None``, all entries under the cache prefix are removed.

        Returns:
            Number of keys deleted.
        """
        if params is not None:
            key = self._generate_cache_key(params)
            deleted = 1 if self._redis.delete_cache(key) else 0
            logger.info(f"Cache BUST for specific key: {key}")
            return deleted
        deleted = self._redis.delete_cache_pattern(f"{self._CACHE_PREFIX}:*")
        logger.info(f"Cache BUST ALL: {deleted} entries deleted")
        return deleted


@lru_cache()
def get_event_cache_service() -> EventCacheService:
    """Return the process-level :class:`EventCacheService` singleton."""
    return EventCacheService()
