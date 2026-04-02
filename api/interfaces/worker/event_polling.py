"""
Background worker: periodic Frigate event polling.

The :class:`EventPoller` class receives all its dependencies via the
constructor so it is fully unit-testable without real network or storage.
The module-level :func:`poll_for_new_events` wires up real infrastructure
and is called from the FastAPI ``lifespan`` context.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import List, Protocol, runtime_checkable

from loguru import logger

from domain.event.models import CameraEvent, CameraEventQueryParams
from domain.event.repository import FrigateClientProtocol

POLLING_INTERVAL = 30


# ---------------------------------------------------------------------------
# Dependency protocols (structural typing — no inheritance required)
# ---------------------------------------------------------------------------


@runtime_checkable
class _NotifierProtocol(Protocol):
    def send_topic_push(self, event: CameraEvent) -> None:
        """Send a push notification for a single event."""

    def send_multiple_topic_push(self, events: List[CameraEvent]) -> None:
        """Send a push notification for multiple events."""


@runtime_checkable
class _MediaProtocol(Protocol):
    def exists(self, key: str) -> bool:
        """Return True if the object identified by *key* exists in storage."""

    def upload(self, key: str, data: bytes, content_type: str) -> None:
        """Upload *data* to storage under *key* with the given *content_type*."""


@runtime_checkable
class _CacheProtocol(Protocol):
    def bust_cache(self) -> int:
        """Invalidate the event list cache and return the number of deleted entries."""


# ---------------------------------------------------------------------------
# EventPoller — all dependencies injected, fully unit-testable
# ---------------------------------------------------------------------------


class EventPoller:
    """Periodically fetches new events, mirrors media to MinIO, and triggers FCM pushes."""

    def __init__(
        self,
        frigate: FrigateClientProtocol,
        media: _MediaProtocol,
        notifier: _NotifierProtocol,
        cache: _CacheProtocol,
        polling_interval: int = POLLING_INTERVAL,
    ) -> None:
        self._frigate = frigate
        self._media = media
        self._notifier = notifier
        self._cache = cache
        self._interval = polling_interval

    @logger.catch()
    async def run(self) -> None:
        """Entry-point coroutine; loops forever until cancelled."""
        while True:
            await self._fetch_and_process()
            await asyncio.sleep(self._interval)

    async def _fetch_and_process(self) -> None:
        """Fetch new events from Frigate, mirror media, and dispatch FCM notifications."""
        aftertime = datetime.now() - timedelta(seconds=self._interval)
        params = CameraEventQueryParams()
        params.after = int(aftertime.timestamp())
        params.limit = 20

        events: List[CameraEvent] = []
        try:
            events = self._frigate.get_events(params)
            await self.mirror_to_media(events)
            await self.process_events(events)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"Error fetching/processing events: {e}")

    async def mirror_to_media(self, events: List[CameraEvent]) -> None:
        """Mirror snapshot and clip media for *events* to object storage if not already present."""
        if not events:
            return
        for event in events:
            if event.has_snapshot:
                key = f"{event.id}/snapshot.jpg"
                if not self._media.exists(key):
                    try:
                        data = self._frigate.get_snapshot(event.id)
                        self._media.upload(key, data, "image/jpeg")
                        logger.info(f"MinIO: mirrored snapshot for event {event.id}")
                    except Exception as e:  # pylint: disable=broad-exception-caught
                        logger.error(
                            f"MinIO: failed to mirror snapshot for {event.id}: {e}"
                        )

            if event.has_clip:
                key = f"{event.id}/clip.mp4"
                if not self._media.exists(key):
                    try:
                        data = self._frigate.get_clip(event.id)
                        self._media.upload(key, data, "video/mp4")
                        logger.info(f"MinIO: mirrored clip for event {event.id}")
                    except Exception as e:  # pylint: disable=broad-exception-caught
                        logger.error(
                            f"MinIO: failed to mirror clip for {event.id}: {e}"
                        )

    async def process_events(self, events: List[CameraEvent]) -> None:
        """Send FCM push notifications for *events* and bust the event list cache."""
        try:
            if len(events) == 1:
                self._notifier.send_topic_push(events[0])
            elif len(events) > 1:
                logger.info(f"Found {len(events)} events. Pushing to clients")
                self._notifier.send_multiple_topic_push(events)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"Error sending FCM push: {e}")

        if events:
            deleted = self._cache.bust_cache()
            logger.info(f"Cache busted, deleted entries: {deleted}")


# ---------------------------------------------------------------------------
# Module-level entry point used by main.py lifespan
# ---------------------------------------------------------------------------


async def poll_for_new_events() -> None:
    """Wire up real dependencies and start the polling loop."""
    from infrastructure.firebase.app import send_topic_push, send_multiple_topic_push  # pylint: disable=import-outside-toplevel
    from infrastructure.frigate.client import FrigateClient  # pylint: disable=import-outside-toplevel
    from infrastructure.minio.client import get_minio_service  # pylint: disable=import-outside-toplevel
    from infrastructure.redis.cache import get_event_cache_service  # pylint: disable=import-outside-toplevel

    class _Notifier:  # pylint: disable=too-few-public-methods
        def send_topic_push(self, event: CameraEvent) -> None:
            """Delegate to the module-level FCM send function."""
            send_topic_push(event)

        def send_multiple_topic_push(self, events: List[CameraEvent]) -> None:
            """Delegate to the module-level FCM multi-send function."""
            send_multiple_topic_push(events)

    poller = EventPoller(
        frigate=FrigateClient(),  # FrigateClient satisfies FrigateClientProtocol
        media=get_minio_service(),
        notifier=_Notifier(),
        cache=get_event_cache_service(),
    )
    await poller.run()
