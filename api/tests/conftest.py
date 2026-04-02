# Top-level conftest: shared fakes available to all test tiers.
from __future__ import annotations

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

    def upload(self, key: str, data: bytes, content_type: str) -> None:
        self._store[key] = data

    def download(self, key: str) -> Optional[bytes]:
        return self._store.get(key)

    def exists(self, key: str) -> bool:
        return key in self._store


class FakeCacheService:
    """In-memory event list cache — no Redis required."""

    def __init__(self) -> None:
        self._store: Dict[str, List[CameraEvent]] = {}
        self.bust_count: int = 0

    def key(self, params: CameraEventQueryParams) -> str:
        import hashlib
        items = sorted(params.model_dump().items())
        return "events:" + hashlib.md5(str(items).encode()).hexdigest()

    def get_cached_events(self, params: CameraEventQueryParams) -> Optional[List[CameraEvent]]:
        return self._store.get(self.key(params))

    def cache_events(self, params: CameraEventQueryParams, events: List[CameraEvent]) -> bool:
        self._store[self.key(params)] = events
        return True

    def bust_cache(self, params: Optional[CameraEventQueryParams] = None) -> int:
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

    def set_temporary_image_token(self, snapshot_id: str, expire: int = 86400) -> str:
        import uuid
        token = str(uuid.uuid4())
        self._store[token] = snapshot_id
        return token

    def get_snapshot_id(self, image_token: str) -> str:
        return self._store.get(image_token, "")


# ---------------------------------------------------------------------------
# Shared pytest fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def fake_media() -> FakeMediaService:
    return FakeMediaService()


@pytest.fixture()
def fake_cache() -> FakeCacheService:
    return FakeCacheService()


@pytest.fixture()
def fake_datastore() -> FakeRedisDatastore:
    return FakeRedisDatastore()


@pytest.fixture()
def sample_event() -> CameraEvent:
    return CameraEvent(
        id="evt-001",
        camera="garage",
        label="person",
        has_clip=True,
        has_snapshot=True,
        retain_indefinitely=False,
        start_time=1_700_000_000.0,
    )


@pytest.fixture()
def sample_events(sample_event: CameraEvent) -> List[CameraEvent]:
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
