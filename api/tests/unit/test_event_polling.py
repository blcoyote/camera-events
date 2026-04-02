"""Unit tests for interfaces/worker/event_polling.py (EventPoller class)."""
from __future__ import annotations

from typing import List

import pytest

from domain.event.models import CameraEvent, CameraEventQueryParams
from interfaces.worker.event_polling import EventPoller
from tests.conftest import FakeCacheService, FakeMediaService


# ---------------------------------------------------------------------------
# Fake Frigate client
# ---------------------------------------------------------------------------


class FakeFrigateClient:
    """In-memory Frigate stub — no HTTP required."""

    def __init__(
        self,
        snapshot_data: bytes = b"snapshot-data",
        clip_data: bytes = b"clip-data",
    ) -> None:
        self._snapshot = snapshot_data
        self._clip = clip_data

    def get_events(
        self, _params: CameraEventQueryParams | None = None
    ) -> List[CameraEvent]:
        """Return an empty event list."""
        return []

    def get_event(self, _event_id: str) -> CameraEvent:  # pragma: no cover
        """Raise NotImplementedError — not used in tests."""
        raise NotImplementedError

    def get_snapshot(self, _event_id: str) -> bytes:
        """Return stub snapshot bytes."""
        return self._snapshot

    def get_clip(self, _event_id: str) -> bytes:  # pragma: no cover
        """Return stub clip bytes."""
        return self._clip

    def get_latest(self, _camera: str) -> bytes:  # pragma: no cover
        """Return empty bytes."""
        return b""


# ---------------------------------------------------------------------------
# Fake notifier
# ---------------------------------------------------------------------------


class FakeNotifier:
    """Stub notifier that records push calls without sending real FCM messages."""

    def __init__(self) -> None:
        self.singles: List[CameraEvent] = []
        self.multiples: List[List[CameraEvent]] = []

    def send_topic_push(self, event: CameraEvent) -> None:
        """Record a single-event push call."""
        self.singles.append(event)

    def send_multiple_topic_push(self, events: List[CameraEvent]) -> None:
        """Record a multi-event push call."""
        self.multiples.append(events)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_poller(
    fake_media: FakeMediaService,
    fake_cache: FakeCacheService,
    notifier: FakeNotifier | None = None,
    frigate: FakeFrigateClient | None = None,
) -> EventPoller:
    return EventPoller(
        frigate=frigate or FakeFrigateClient(),
        media=fake_media,
        notifier=notifier or FakeNotifier(),
        cache=fake_cache,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestEventPollerMirror:
    """Tests for EventPoller.mirror_to_media()."""

    @pytest.mark.asyncio
    async def test_mirrors_snapshot_when_not_exists(
        self,
        sample_event: CameraEvent,
        fake_media: FakeMediaService,
        fake_cache: FakeCacheService,
    ) -> None:
        """Snapshot must be uploaded to media storage when it doesn't exist yet."""
        snapshot_bytes = b"snapshot-data"
        frigate = FakeFrigateClient(snapshot_data=snapshot_bytes)
        poller = _make_poller(fake_media, fake_cache, frigate=frigate)

        await poller.mirror_to_media([sample_event])

        assert fake_media.exists(f"{sample_event.id}/snapshot.jpg")
        assert fake_media.download(f"{sample_event.id}/snapshot.jpg") == snapshot_bytes

    @pytest.mark.asyncio
    async def test_skips_mirror_when_already_exists(
        self,
        sample_event: CameraEvent,
        fake_media: FakeMediaService,
        fake_cache: FakeCacheService,
    ) -> None:
        """Existing media must not be overwritten on a subsequent mirror call."""
        existing = b"old-snapshot"
        fake_media.upload(f"{sample_event.id}/snapshot.jpg", existing, "image/jpeg")

        frigate = FakeFrigateClient(snapshot_data=b"new-data")
        poller = _make_poller(fake_media, fake_cache, frigate=frigate)

        await poller.mirror_to_media([sample_event])

        # Existing bytes must not be overwritten
        assert fake_media.download(f"{sample_event.id}/snapshot.jpg") == existing


class TestEventPollerNotify:
    """Tests for EventPoller.process_events()."""

    @pytest.mark.asyncio
    async def test_sends_single_push_for_one_event(
        self,
        sample_event: CameraEvent,
        fake_media: FakeMediaService,
        fake_cache: FakeCacheService,
    ) -> None:
        """A single new event must trigger one send_topic_push call."""
        notifier = FakeNotifier()
        poller = _make_poller(fake_media, fake_cache, notifier=notifier)

        await poller.process_events([sample_event])

        assert len(notifier.singles) == 1
        assert notifier.singles[0].id == sample_event.id
        assert len(notifier.multiples) == 0

    @pytest.mark.asyncio
    async def test_sends_multi_push_for_many_events(
        self,
        sample_events: List[CameraEvent],
        fake_media: FakeMediaService,
        fake_cache: FakeCacheService,
    ) -> None:
        """Multiple new events must trigger one send_multiple_topic_push call."""
        notifier = FakeNotifier()
        poller = _make_poller(fake_media, fake_cache, notifier=notifier)

        await poller.process_events(sample_events)

        assert len(notifier.multiples) == 1
        assert len(notifier.singles) == 0

    @pytest.mark.asyncio
    async def test_busts_cache_after_events(
        self,
        sample_event: CameraEvent,
        fake_media: FakeMediaService,
        fake_cache: FakeCacheService,
    ) -> None:
        """The cache must be busted after new events are processed."""
        notifier = FakeNotifier()
        poller = EventPoller(frigate=FakeFrigateClient(), media=fake_media, notifier=notifier, cache=fake_cache)
        # Seed one cache entry
        fake_cache.cache_events(CameraEventQueryParams(), [sample_event])

        await poller.process_events([sample_event])

        assert fake_cache.bust_count == 1

    @pytest.mark.asyncio
    async def test_no_bust_when_no_events(
        self,
        fake_media: FakeMediaService,
        fake_cache: FakeCacheService,
    ) -> None:
        """The cache must not be busted when there are no new events."""
        notifier = FakeNotifier()
        poller = EventPoller(frigate=FakeFrigateClient(), media=fake_media, notifier=notifier, cache=fake_cache)

        await poller.process_events([])

        assert fake_cache.bust_count == 0
