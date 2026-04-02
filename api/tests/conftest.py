"""Shared in-memory fakes and pytest fixtures available to all test tiers."""
from __future__ import annotations

import hashlib
import uuid
from typing import Dict, List, Optional
import pytest

from domain.event.models import CameraEvent, CameraEventQueryParams


# ---------------------------------------------------------------------------
# In-memory fakes (implement the same interface as production services)
# ---------------------------------------------------------------------------


class FakeMediaService:
    """In-memory media store — no MinIO required."""

    def __init__(self) -> None:
        self._store: Dict[str, bytes] = {}

    def upload(self, key: str, data: bytes, _content_type: str) -> None:
        """Store *data* under *key*; *_content_type* is ignored."""
        self._store[key] = data

    def download(self, key: str) -> Optional[bytes]:
        """Return bytes for *key*, or ``None`` if not stored."""
        return self._store.get(key)

    def exists(self, key: str) -> bool:
        """Return ``True`` if *key* has been uploaded."""
        return key in self._store


class FakeCacheService:
    """In-memory event list cache — no Redis required."""

    def __init__(self) -> None:
        self._store: Dict[str, List[CameraEvent]] = {}
        self.bust_count: int = 0

    def key(self, params: CameraEventQueryParams) -> str:
        """Return a deterministic cache key for *params*."""
        items = sorted(params.model_dump().items())
        return "events:" + hashlib.md5(str(items).encode()).hexdigest()

    def get_cached_events(self, params: CameraEventQueryParams) -> Optional[List[CameraEvent]]:
        """Return cached events for *params*, or ``None`` on a miss."""
        return self._store.get(self.key(params))

    def cache_events(self, params: CameraEventQueryParams, events: List[CameraEvent]) -> bool:
        """Store *events* under *params* key and return ``True``."""
        self._store[self.key(params)] = events
        return True

    def bust_cache(self, params: Optional[CameraEventQueryParams] = None) -> int:
        """Delete cached entries; returns the number of keys removed."""
        if params:
            k = self.key(params)
            removed = int(k in self._store)
            self._store.pop(k, None)
        else:
            removed = len(self._store)
            self._store.clear()
        self.bust_count += removed
        return removed


class FakeRedisDatastore:
    """In-memory image-token store — no Redis required."""

    def __init__(self) -> None:
        self._store: Dict[str, str] = {}

    def set_temporary_image_token(self, snapshot_id: str, _expire: int = 86400) -> str:
        """Create and return a random token mapped to *snapshot_id*."""
        token = str(uuid.uuid4())
        self._store[token] = snapshot_id
        return token

    def get_snapshot_id(self, image_token: str) -> str:
        """Return the snapshot ID for *image_token*, or empty string."""
        return self._store.get(image_token, "")


# ---------------------------------------------------------------------------
# Shared pytest fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def fake_media() -> FakeMediaService:
    """Provide an in-memory :class:`FakeMediaService` instance."""
    return FakeMediaService()


@pytest.fixture()
def fake_cache() -> FakeCacheService:
    """Provide an in-memory :class:`FakeCacheService` instance."""
    return FakeCacheService()


@pytest.fixture()
def fake_datastore() -> FakeRedisDatastore:
    """Provide an in-memory :class:`FakeRedisDatastore` instance."""
    return FakeRedisDatastore()


@pytest.fixture()
def sample_event() -> CameraEvent:
    """Return a single stub :class:`CameraEvent`."""
    return CameraEvent(
        id="evt-001",
        camera="garage",
        label="person",
        has_clip=True,
        has_snapshot=True,
        retain_indefinitely=False,
        start_time=1_700_000_000.0,
    )


@pytest.fixture()  # pylint: disable=redefined-outer-name
def sample_events(sample_event: CameraEvent) -> List[CameraEvent]:  # pylint: disable=redefined-outer-name
    """Return a list of two stub :class:`CameraEvent` objects."""
    second = CameraEvent(
        id="evt-002",
        camera="gavl_vest",
        label="person",
        has_clip=False,
        has_snapshot=True,
        retain_indefinitely=False,
        start_time=1_700_000_060.0,
    )
    return [sample_event, second]
