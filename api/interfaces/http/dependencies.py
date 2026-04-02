"""
Centralised FastAPI dependency providers.

Import these with ``Depends()`` in route handlers instead of constructing
services inline. This makes it trivial to override dependencies in tests
via ``app.dependency_overrides``.
"""
from __future__ import annotations

from functools import lru_cache

from application.attachment.service import AttachmentService
from application.event.service import EventService
from application.fcm.service import FcmService
from infrastructure.frigate.client import FrigateClient
from infrastructure.minio.client import MinIOService, get_minio_service
from infrastructure.redis.cache import EventCacheService, get_event_cache_service
from infrastructure.redis.client import RedisSetClient


@lru_cache()
def get_frigate_client() -> FrigateClient:
    """Return the process-level :class:`FrigateClient` singleton."""
    return FrigateClient()


@lru_cache()
def get_event_service() -> EventService:
    """FastAPI dependency: returns the :class:`EventService` singleton."""
    return EventService(
        frigate=get_frigate_client(),
        media=get_minio_service(),
        cache=get_event_cache_service(),
    )


@lru_cache()
def get_attachment_service() -> AttachmentService:
    """FastAPI dependency: returns the :class:`AttachmentService` singleton."""
    return AttachmentService(event_service=get_event_service())


def get_fcm_service() -> FcmService:
    """FastAPI dependency: returns a :class:`FcmService` for the current request."""
    return FcmService(redis=RedisSetClient())


def get_cache_service() -> EventCacheService:
    """FastAPI dependency: returns the :class:`EventCacheService` singleton."""
    return get_event_cache_service()


def get_media_service() -> MinIOService:
    """FastAPI dependency: returns the :class:`MinIOService` singleton."""
    return get_minio_service()


def get_redis_client() -> RedisSetClient:
    """FastAPI dependency: returns a :class:`RedisSetClient` for the current request."""
    return RedisSetClient()
