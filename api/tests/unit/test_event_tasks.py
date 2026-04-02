"""Unit tests for application/event/service.py — EventService media caching."""
from __future__ import annotations

from unittest.mock import MagicMock


from application.event.service import EventService
from tests.conftest import FakeCacheService, FakeMediaService


def _make_service(
    fake_media: FakeMediaService,
    frigate: MagicMock | None = None,
) -> EventService:
    """Build an :class:`EventService` with injected fakes."""
    if frigate is None:
        frigate = MagicMock()
    return EventService(
        frigate=frigate,
        media=fake_media,
        cache=FakeCacheService(),
    )


class TestGetSnapshotCached:
    """Tests for EventService.get_snapshot_cached()."""

    def test_returns_minio_data_on_hit(self, fake_media: FakeMediaService) -> None:
        """When MinIO has the file, it must be returned without querying Frigate."""
        fake_media.upload("evt-1/snapshot.jpg", b"jpeg-from-minio", "image/jpeg")
        service = _make_service(fake_media)

        result = service.get_snapshot_cached("evt-1")

        assert result == b"jpeg-from-minio"

    def test_falls_back_to_frigate_on_miss(self, fake_media: FakeMediaService) -> None:
        """When MinIO has no entry, the service delegates to the Frigate client."""
        frigate = MagicMock()
        frigate.get_snapshot.return_value = b"jpeg-from-frigate"
        service = _make_service(fake_media, frigate=frigate)

        result = service.get_snapshot_cached("evt-2")

        assert result == b"jpeg-from-frigate"
        frigate.get_snapshot.assert_called_once_with("evt-2")

    def test_minio_hit_does_not_call_frigate(self, fake_media: FakeMediaService) -> None:
        """When MinIO returns data, the Frigate client must never be called."""
        fake_media.upload("evt-3/snapshot.jpg", b"cached", "image/jpeg")
        frigate = MagicMock()
        service = _make_service(fake_media, frigate=frigate)

        result = service.get_snapshot_cached("evt-3")

        assert result == b"cached"
        frigate.get_snapshot.assert_not_called()


class TestGetClipCached:
    """Tests for EventService.get_clip_cached()."""

    def test_returns_minio_data_on_hit(self, fake_media: FakeMediaService) -> None:
        """When MinIO has the clip, it must be returned without querying Frigate."""
        fake_media.upload("evt-1/clip.mp4", b"mp4-from-minio", "video/mp4")
        service = _make_service(fake_media)

        result = service.get_clip_cached("evt-1")

        assert result == b"mp4-from-minio"

    def test_minio_hit_does_not_call_frigate(self, fake_media: FakeMediaService) -> None:
        """When MinIO returns data, the Frigate client must never be called."""
        fake_media.upload("evt-4/clip.mp4", b"cached-mp4", "video/mp4")
        frigate = MagicMock()
        service = _make_service(fake_media, frigate=frigate)

        result = service.get_clip_cached("evt-4")

        assert result == b"cached-mp4"
        frigate.get_clip.assert_not_called()
