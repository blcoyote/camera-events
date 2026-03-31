"""
Background worker: periodic Frigate event polling.

The :class:`EventPoller` class receives all its dependencies via the
constructor so it is fully unit-testable without real network or storage.
The module-level :func:`poll_for_new_events` wires up real infrastructure
and is called from the FastAPI ``lifespan`` context.
"""
from __future__ import annotations

import asyncio
from typing import List, Protocol, runtime_checkable

from loguru import logger
from datetime import datetime, timedelta

from domain.event.models import CameraEvent, CameraEventQueryParams
from domain.event.repository import FrigateClientProtocol

POLLING_INTERVAL = 30


# ---------------------------------------------------------------------------
# Dependency protocols (structural typing — no inheritance required)
# ---------------------------------------------------------------------------


@runtime_checkable
class _NotifierProtocol(Protocol):
    def send_topic_push(self, event: CameraEvent) -> None: ...
    def send_multiple_topic_push(self, events: List[CameraEvent]) -> None: ...


@runtime_checkable
class _MediaProtocol(Protocol):
    def exists(self, key: str) -> bool: ...
    def upload(self, key: str, data: bytes, content_type: str) -> None: ...


@runtime_checkable
class _CacheProtocol(Protocol):
    def bust_cache(self) -> int: ...


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
        aftertime = datetime.now() - timedelta(seconds=self._interval)
        params = CameraEventQueryParams()
        params.after = int(aftertime.timestamp())
        params.limit = 20

        events: List[CameraEvent] = []
        try:
            events = self._frigate.get_events(params)
            await self.mirror_to_media(events)
            await self.process_events(events)
        except Exception as e:
            logger.error(f"Error fetching/processing events: {e}")

    async def mirror_to_media(self, events: List[CameraEvent]) -> None:
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
                    except Exception as e:
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
                    except Exception as e:
                        logger.error(
                            f"MinIO: failed to mirror clip for {event.id}: {e}"
                        )

    async def process_events(self, events: List[CameraEvent]) -> None:
        try:
            if len(events) == 1:
                self._notifier.send_topic_push(events[0])
            elif len(events) > 1:
                logger.info(f"Found {len(events)} events. Pushing to clients")
                self._notifier.send_multiple_topic_push(events)
        except Exception as e:
            logger.error(f"Error sending FCM push: {e}")

        if events:
            deleted = self._cache.bust_cache()
            logger.info(f"Cache busted, deleted entries: {deleted}")


# ---------------------------------------------------------------------------
# Module-level entry point used by main.py lifespan
# ---------------------------------------------------------------------------


async def poll_for_new_events() -> None:
    """Wire up real dependencies and start the polling loop."""
    from infrastructure.firebase.app import send_topic_push, send_multiple_topic_push
    from infrastructure.frigate.client import FrigateClient
    from infrastructure.minio.client import get_minio_service
    from infrastructure.redis.cache import get_event_cache_service

    class _Notifier:
        def send_topic_push(self, event: CameraEvent) -> None:
            send_topic_push(event)

        def send_multiple_topic_push(self, events: List[CameraEvent]) -> None:
            send_multiple_topic_push(events)

    poller = EventPoller(
        frigate=FrigateClient(),  # FrigateClient satisfies FrigateClientProtocol
        media=get_minio_service(),
        notifier=_Notifier(),
        cache=get_event_cache_service(),
    )
    await poller.run()
