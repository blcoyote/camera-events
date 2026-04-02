"""
Integration tests for /api/v2/events/* endpoints.

These tests run against a real Redis container (via testcontainers) and mock
the upstream Frigate HTTP calls so the app exercises the full request/response
cycle including caching.
"""# pylint: disable=unused-argument  # mock_auth fixtures are used for their side-effects onlyfrom __future__ import annotations

from unittest.mock import patch

import pytest
from httpx import AsyncClient

from domain.event.models import CameraEvent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FAKE_EVENT_DICT = {
    "id": "abc123",
    "camera": "front-door",
    "label": "person",
    "start_time": 1700000000.0,
    "end_time": 1700000010.0,
    "has_snapshot": True,
    "has_clip": True,
    "retain_indefinitely": False,
    "zones": [],
    "thumbnail": None,
    "data": None,
}
_FAKE_EVENT = CameraEvent.model_validate(_FAKE_EVENT_DICT)

_AUTH_HEADER = {"X-Token": "test-token"}


# ---------------------------------------------------------------------------
# GET /api/v2/events/
# ---------------------------------------------------------------------------

class TestReadEvents:
    """Tests for the event listing endpoint."""

    @pytest.mark.asyncio
    async def test_returns_events_from_frigate(self, client: AsyncClient, mock_auth: dict[str, str]) -> None:
        """On a cache miss the app fetches from Frigate and stores in Redis."""
        with patch("infrastructure.frigate.client.FrigateClient.get_events", return_value=[_FAKE_EVENT]):
            resp = await client.get("/api/v2/events/", headers=_AUTH_HEADER)

        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert body[0]["id"] == "abc123"

    @pytest.mark.asyncio
    async def test_second_request_served_from_cache(self, client: AsyncClient, mock_auth: dict[str, str]) -> None:
        """A second identical request should hit the cache (Frigate called once)."""
        # Ensure a clean cache state — a prior test may have populated the same key.
        await client.delete("/api/v2/events/cache", headers=_AUTH_HEADER)
        with patch("infrastructure.frigate.client.FrigateClient.get_events", return_value=[_FAKE_EVENT]) as mock_get:
            await client.get("/api/v2/events/", headers=_AUTH_HEADER)
            await client.get("/api/v2/events/", headers=_AUTH_HEADER)
            # Frigate was contacted exactly once — second hit came from Redis
            assert mock_get.call_count == 1

    @pytest.mark.asyncio
    async def test_unauthorized_without_header(self, client: AsyncClient) -> None:
        """Requests without the X-Token header must be rejected."""
        resp = await client.get("/api/v2/events/")
        assert resp.status_code in (401, 403, 422)


# ---------------------------------------------------------------------------
# DELETE /api/v2/events/cache
# ---------------------------------------------------------------------------

class TestBustEventsCache:
    """Tests for the cache-busting endpoint."""

    @pytest.mark.asyncio
    async def test_bust_cache_returns_200(self, client: AsyncClient, mock_auth: dict[str, str]) -> None:
        """Bust-cache endpoint must return HTTP 200 with a deleted_entries key."""
        resp = await client.delete("/api/v2/events/cache", headers=_AUTH_HEADER)
        assert resp.status_code == 200
        body = resp.json()
        assert "deleted_entries" in body

    @pytest.mark.asyncio
    async def test_bust_then_refetch(self, client: AsyncClient, mock_auth: dict[str, str]) -> None:
        """After busting the cache the next GET should call Frigate again."""
        with patch("infrastructure.frigate.client.FrigateClient.get_events", return_value=[_FAKE_EVENT]) as mock_get:
            # Populate cache
            await client.get("/api/v2/events/", headers=_AUTH_HEADER)
            # Bust it
            await client.delete("/api/v2/events/cache", headers=_AUTH_HEADER)
            # Next GET must hit Frigate again
            await client.get("/api/v2/events/", headers=_AUTH_HEADER)
            assert mock_get.call_count == 2

    @pytest.mark.asyncio
    async def test_unauthorized_without_header(self, client: AsyncClient) -> None:
        """Requests without the X-Token header must be rejected."""
        resp = await client.delete("/api/v2/events/cache")
        assert resp.status_code in (401, 403, 422)


# ---------------------------------------------------------------------------
# GET /api/v2/events/cameras
# ---------------------------------------------------------------------------

class TestReadCameraList:
    """Tests for the static camera-list endpoint."""

    @pytest.mark.asyncio
    async def test_returns_list(self, client: AsyncClient, mock_auth: dict[str, str]) -> None:
        """Endpoint must return an HTTP 200 with a JSON list."""
        resp = await client.get("/api/v2/events/cameras", headers=_AUTH_HEADER)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_unauthorized_without_header(self, client: AsyncClient) -> None:
        """Requests without the X-Token header must be rejected."""
        resp = await client.get("/api/v2/events/cameras")
        assert resp.status_code in (401, 403, 422)


# ---------------------------------------------------------------------------
# GET /api/v2/events/{id}/snapshot.jpg
# ---------------------------------------------------------------------------

class TestReadEventSnapshot:
    """Tests for the snapshot streaming endpoint."""

    @pytest.mark.asyncio
    async def test_returns_image_bytes(self, client: AsyncClient, mock_auth: dict[str, str]) -> None:
        """Endpoint must return JPEG bytes with image/* content-type."""
        fake_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 16  # minimal JPEG-like bytes
        with patch("application.event.service.EventService.get_snapshot_cached", return_value=fake_bytes):
            resp = await client.get(
                "/api/v2/events/abc123/snapshot.jpg", headers=_AUTH_HEADER
            )
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("image/")

    @pytest.mark.asyncio
    async def test_unauthorized_without_header(self, client: AsyncClient) -> None:
        """Requests without the X-Token header must be rejected."""
        resp = await client.get("/api/v2/events/abc123/snapshot.jpg")
        assert resp.status_code in (401, 403, 422)
