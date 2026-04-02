"""
Attachment use-case service.

Resolves short-lived image tokens stored in Redis to snapshot bytes so that
FCM notification images can be served without exposing authenticated endpoints.
"""
from __future__ import annotations

from loguru import logger

from application.event.service import EventService
from infrastructure.redis.datastore import get_snapshot_id


class AttachmentService:
    """
    Resolves notification image tokens to snapshot bytes.

    Args:
        event_service: Provides snapshot retrieval and placeholder fallback.
    """

    def __init__(self, event_service: EventService) -> None:
        self._events = event_service

    def get_snapshot_for_token(self, image_token: str) -> bytes | None:
        """
        Look up *image_token* in Redis and return the corresponding snapshot bytes.

        Args:
            image_token: Short-lived UUID token generated at notification dispatch.

        Returns:
            Snapshot JPEG bytes, or ``None`` if the token has expired or is unknown.
        """
        event_id = get_snapshot_id(image_token)
        logger.info(f"Getting snapshot for event {event_id!r} (token {image_token!r})")
        if not event_id:
            return None
        return self._events.get_snapshot_cached(event_id)

    def get_placeholder(self) -> bytes:
        """Return the fallback placeholder PNG bytes."""
        return self._events.get_placeholder()
