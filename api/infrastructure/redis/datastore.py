"""Redis-backed image-token datastore for notification attachments."""
from __future__ import annotations

import uuid
from functools import lru_cache

import redis
from loguru import logger

from lib.settings import get_settings


@lru_cache()
def _get_redis_client() -> redis.Redis:  # type: ignore[type-arg]
    """Return a lazily-initialised Redis client (cached for the process lifetime)."""
    settings = get_settings()
    return redis.Redis(
        host=settings.redis_host,
        password=settings.redis_password,
        port=6379,
        decode_responses=True,
    )


def set_temporary_image_token(
    snapshot_id: str,
    expire: int = 60 * 60 * 24,
    *,
    client: redis.Redis | None = None,  # type: ignore[type-arg]
) -> str:
    """
    Store *snapshot_id* under a new UUID token in Redis.

    Args:
        snapshot_id: The event ID whose snapshot will be looked up later.
        expire: TTL in seconds (default: 24 h).
        client: Optional Redis client override (used in tests).

    Returns:
        The generated UUID token string.
    """
    rdb = client or _get_redis_client()
    token = str(uuid.uuid4())
    try:
        rdb.set(token, snapshot_id, ex=expire)
        logger.info(f"Image token set for snapshot {snapshot_id}")
    except Exception as e:
        logger.error(f"Failed to set image token for snapshot {snapshot_id}: {e}")
        raise
    return token


def get_snapshot_id(
    image_token: str,
    *,
    client: redis.Redis | None = None,  # type: ignore[type-arg]
) -> str:
    """
    Resolve *image_token* to its snapshot ID.

    Args:
        image_token: The UUID token previously created by :func:`set_temporary_image_token`.
        client: Optional Redis client override (used in tests).

    Returns:
        The snapshot ID, or an empty string if the token has expired or is unknown.
    """
    rdb = client or _get_redis_client()
    try:
        stored = rdb.get(image_token)
        return str(stored) if stored is not None else ""
    except Exception as e:
        logger.error(f"Failed to get snapshot id for token {image_token}: {e}")
        return ""
