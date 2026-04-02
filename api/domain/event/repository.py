"""
Structural (Protocol) interfaces for the event domain.

Using ``typing.Protocol`` lets fakes/mocks in tests satisfy these contracts
without any inheritance.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from domain.event.models import CameraEvent, CameraEventQueryParams


@runtime_checkable
class CacheServiceProtocol(Protocol):
    """Abstraction over the event list cache (Redis)."""

    def get_cached_events(
        self, params: CameraEventQueryParams
    ) -> list[CameraEvent] | None:
        """Return cached events for *params*, or ``None`` on a cache miss."""
        ...

    def cache_events(
        self, params: CameraEventQueryParams, events: list[CameraEvent]
    ) -> bool:
        """Store *events* in cache. Returns ``True`` on success."""
        ...

    def bust_cache(
        self, params: CameraEventQueryParams | None = None
    ) -> int:
        """Delete cached entries. Returns the number of keys deleted."""
        ...


@runtime_checkable
class MediaServiceProtocol(Protocol):
    """Abstraction over object storage (MinIO / S3)."""

    def upload(self, key: str, data: bytes, content_type: str) -> None:
        """Upload *data* under *key* with the given *content_type*."""
        ...

    def download(self, key: str) -> bytes | None:
        """Return bytes for *key*, or ``None`` if not found."""
        ...

    def exists(self, key: str) -> bool:
        """Return ``True`` if *key* exists in the bucket."""
        ...


@runtime_checkable
class FrigateClientProtocol(Protocol):
    """Abstraction over the Frigate NVR HTTP API."""

    def get_events(
        self, params: CameraEventQueryParams | None = None
    ) -> list[CameraEvent]:
        """Return events matching *params*."""
        ...

    def get_event(self, event_id: str) -> CameraEvent:
        """Return a single event by ID."""
        ...

    def get_snapshot(self, event_id: str) -> bytes:
        """Return snapshot JPEG bytes for event *event_id*."""
        ...

    def get_clip(self, event_id: str) -> bytes:
        """Return clip MP4 bytes for event *event_id*."""
        ...

    def get_latest(self, camera: str) -> bytes:
        """Return the latest frame JPEG bytes for *camera*."""
        ...
