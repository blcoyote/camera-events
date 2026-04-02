"""
Event use-case service.

Orchestrates Frigate NVR fetches, MinIO caching, and the event list cache.
All infrastructure dependencies are injected via the constructor so this
class is fully unit-testable without real network or storage.
"""
from __future__ import annotations

from loguru import logger

from domain.event.models import CameraEvent, CameraEventQueryParams
from domain.event.repository import (
    CacheServiceProtocol,
    FrigateClientProtocol,
    MediaServiceProtocol,
)


class EventService:
    """
    Orchestrates event retrieval, media caching, and event list caching.

    Args:
        frigate: Frigate NVR HTTP client (or any :class:`FrigateClientProtocol`).
        media: Object-storage client (or any :class:`MediaServiceProtocol`).
        cache: Redis-backed event list cache.
    """

    def __init__(
        self,
        frigate: FrigateClientProtocol,
        media: MediaServiceProtocol,
        cache: CacheServiceProtocol,
    ) -> None:
        self._frigate = frigate
        self._media = media
        self._cache = cache

    # ------------------------------------------------------------------
    # Frigate pass-through
    # ------------------------------------------------------------------

    def get_events(
        self, params: CameraEventQueryParams | None = None
    ) -> list[CameraEvent]:
        """Fetch events from Frigate matching *params*."""
        return self._frigate.get_events(params)

    def get_event(self, id: str) -> CameraEvent:
        """Fetch a single event by *id* from Frigate."""
        return self._frigate.get_event(id)

    def get_snapshot(self, id: str) -> bytes:
        """Fetch snapshot JPEG bytes for event *id* directly from Frigate."""
        return self._frigate.get_snapshot(id)

    def get_clip(self, id: str) -> bytes:
        """Fetch clip MP4 bytes for event *id* directly from Frigate."""
        return self._frigate.get_clip(id)

    def get_latest(self, camera: str) -> bytes:
        """Fetch the latest frame JPEG bytes for *camera* from Frigate."""
        return self._frigate.get_latest(camera)

    # ------------------------------------------------------------------
    # MinIO-cached media
    # ------------------------------------------------------------------

    def get_snapshot_cached(self, id: str) -> bytes:
        """
        Return snapshot bytes from MinIO when available, falling back to Frigate.

        Args:
            id: Event ID.
        """
        data = self._media.download(f"{id}/snapshot.jpg")
        if data is not None:
            return data
        logger.debug(f"MinIO cache miss for snapshot {id}, fetching from Frigate")
        return self._frigate.get_snapshot(id)

    def get_clip_cached(self, id: str) -> bytes:
        """
        Return clip bytes from MinIO when available, falling back to Frigate.

        Args:
            id: Event ID.
        """
        data = self._media.download(f"{id}/clip.mp4")
        if data is not None:
            return data
        logger.debug(f"MinIO cache miss for clip {id}, fetching from Frigate")
        return self._frigate.get_clip(id)

    @staticmethod
    def get_placeholder() -> bytes:
        """Return the placeholder PNG bytes used as a fallback notification image."""
        with open("pwa-192x192.png", "rb") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # Event list cache delegation
    # ------------------------------------------------------------------

    def get_cached_events(
        self, params: CameraEventQueryParams
    ) -> list[CameraEvent] | None:
        """Return cached event list for *params*, or ``None`` on a miss."""
        return self._cache.get_cached_events(params)

    def cache_events(
        self, params: CameraEventQueryParams, events: list[CameraEvent]
    ) -> bool:
        """Store *events* in the cache under the key for *params*."""
        return self._cache.cache_events(params, events)

    def bust_cache(
        self, params: CameraEventQueryParams | None = None
    ) -> int:
        """Delete cache entries; return the count of keys removed."""
        return self._cache.bust_cache(params)
