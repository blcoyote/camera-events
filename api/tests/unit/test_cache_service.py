"""Unit tests for services/cache_service.py."""
from __future__ import annotations



from domain.event.models import CameraEvent, CameraEventQueryParams
from tests.conftest import FakeCacheService


# ---------------------------------------------------------------------------
# Cache key generation
# ---------------------------------------------------------------------------


class TestGenerateCacheKey:
    def test_same_params_produce_same_key(self) -> None:
        svc = FakeCacheService()
        p1 = CameraEventQueryParams(limit=20)
        p2 = CameraEventQueryParams(limit=20)
        assert svc.key(p1) == svc.key(p2)

    def test_different_params_produce_different_keys(self) -> None:
        svc = FakeCacheService()
        p1 = CameraEventQueryParams(limit=20)
        p2 = CameraEventQueryParams(limit=5)
        assert svc.key(p1) != svc.key(p2)

    def test_key_includes_prefix(self) -> None:
        svc = FakeCacheService()
        key = svc.key(CameraEventQueryParams())
        assert key.startswith("events:")


# ---------------------------------------------------------------------------
# FakeCacheService behaviour (mirrors EventCacheService contract)
# ---------------------------------------------------------------------------


class TestFakeCacheService:
    def test_cache_miss_returns_none(self) -> None:
        svc = FakeCacheService()
        result = svc.get_cached_events(CameraEventQueryParams())
        assert result is None

    def test_cache_hit_returns_events(self, sample_event: CameraEvent) -> None:
        svc = FakeCacheService()
        params = CameraEventQueryParams()
        svc.cache_events(params, [sample_event])
        result = svc.get_cached_events(params)
        assert result is not None
        assert len(result) == 1
        assert result[0].id == sample_event.id

    def test_bust_cache_clears_all(self, sample_event: CameraEvent) -> None:
        svc = FakeCacheService()
        svc.cache_events(CameraEventQueryParams(limit=10), [sample_event])
        svc.cache_events(CameraEventQueryParams(limit=5), [sample_event])
        deleted = svc.bust_cache()
        assert deleted == 2
        assert svc.get_cached_events(CameraEventQueryParams(limit=10)) is None

    def test_bust_cache_specific_params(self, sample_event: CameraEvent) -> None:
        svc = FakeCacheService()
        params_a = CameraEventQueryParams(limit=10)
        params_b = CameraEventQueryParams(limit=5)
        svc.cache_events(params_a, [sample_event])
        svc.cache_events(params_b, [sample_event])

        svc.bust_cache(params_a)

        assert svc.get_cached_events(params_a) is None
        assert svc.get_cached_events(params_b) is not None
