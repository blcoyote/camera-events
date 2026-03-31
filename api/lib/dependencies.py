"""
Centralised FastAPI dependency providers.

Import these with ``Depends()`` in route handlers instead of constructing
services inline or referencing module-level singletons. This makes it trivial
to override dependencies in tests via ``app.dependency_overrides``.
"""
from __future__ import annotations

from database.redis_client import RedisSetClient
from services.cache_service import EventCacheService, get_event_cache_service
from services.minio_service import MinIOService, get_minio_service


def get_cache_service() -> EventCacheService:
    """FastAPI dependency that returns the EventCacheService singleton."""
    return get_event_cache_service()


def get_media_service() -> MinIOService:
    """FastAPI dependency that returns the MinIOService singleton."""
    return get_minio_service()


def get_redis_client() -> RedisSetClient:
    """FastAPI dependency that returns a RedisSetClient for the current request."""
    return RedisSetClient()
