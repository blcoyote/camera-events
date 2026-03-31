"""
Integration tests for /api/v2/downloads/* endpoints.

Download routes are protected by a URL-query token (verify_url_token).
These tests verify route wiring, auth enforcement, and content-disposition
headers — media bytes are patched so the suite has no MinIO dependency.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest
from httpx import AsyncClient


_FAKE_SNAPSHOT = b"\xff\xd8\xff\xe0" + b"\x00" * 16
_FAKE_CLIP = b"\x00\x00\x00\x18ftyp" + b"\x00" * 32  # minimal MP4-ish bytes
_TOKEN = "valid-token"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _auth_params() -> dict[str, str]:
    return {"token": _TOKEN}


# ---------------------------------------------------------------------------
# GET /api/v2/downloads/{event_id}/snapshot.jpg
# ---------------------------------------------------------------------------

class TestDownloadSnapshot:
    """Tests for the snapshot download endpoint."""

    @pytest.mark.asyncio
    async def test_returns_attachment_header(self, client: AsyncClient, mock_auth: dict[str, str]) -> None:
        """Response must carry a Content-Disposition attachment header."""
        with patch("application.event.service.EventService.get_snapshot_cached", return_value=_FAKE_SNAPSHOT):
            resp = await client.get(
                "/api/v2/downloads/abc123/snapshot.jpg", params=_auth_params()
            )
        assert resp.status_code == 200
        cd = resp.headers.get("content-disposition", "")
        assert "attachment" in cd
        assert "snapshot-abc123.jpg" in cd

    @pytest.mark.asyncio
    async def test_returns_image_content_type(self, client: AsyncClient, mock_auth: dict[str, str]) -> None:
        with patch("application.event.service.EventService.get_snapshot_cached", return_value=_FAKE_SNAPSHOT):
            resp = await client.get(
                "/api/v2/downloads/abc123/snapshot.jpg", params=_auth_params()
            )
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("image/")

    @pytest.mark.asyncio
    async def test_unauthorized_without_token(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v2/downloads/abc123/snapshot.jpg")
        assert resp.status_code in (401, 403, 422)


# ---------------------------------------------------------------------------
# GET /api/v2/downloads/{camera}/latest.jpg
# ---------------------------------------------------------------------------

class TestDownloadLatest:
    """Tests for the latest-frame download endpoint."""

    @pytest.mark.asyncio
    async def test_returns_attachment_header(self, client: AsyncClient, mock_auth: dict[str, str]) -> None:
        with patch("infrastructure.frigate.client.FrigateClient.get_latest", return_value=_FAKE_SNAPSHOT):
            resp = await client.get(
                "/api/v2/downloads/front-door/latest.jpg", params=_auth_params()
            )
        assert resp.status_code == 200
        cd = resp.headers.get("content-disposition", "")
        assert "attachment" in cd

    @pytest.mark.asyncio
    async def test_unauthorized_without_token(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v2/downloads/front-door/latest.jpg")
        assert resp.status_code in (401, 403, 422)


# ---------------------------------------------------------------------------
# GET /api/v2/downloads/{event_id}/clip.mp4
# ---------------------------------------------------------------------------

class TestDownloadClip:
    """Tests for the clip download endpoint."""

    @pytest.mark.asyncio
    async def test_returns_attachment_header(self, client: AsyncClient, mock_auth: dict[str, str]) -> None:
        with patch("application.event.service.EventService.get_clip_cached", return_value=_FAKE_CLIP):
            resp = await client.get(
                "/api/v2/downloads/abc123/clip.mp4", params=_auth_params()
            )
        assert resp.status_code == 200
        cd = resp.headers.get("content-disposition", "")
        assert "attachment" in cd
        assert "clip-abc123.mp4" in cd

    @pytest.mark.asyncio
    async def test_returns_video_content_type(self, client: AsyncClient, mock_auth: dict[str, str]) -> None:
        with patch("application.event.service.EventService.get_clip_cached", return_value=_FAKE_CLIP):
            resp = await client.get(
                "/api/v2/downloads/abc123/clip.mp4", params=_auth_params()
            )
        assert resp.headers["content-type"].startswith("video/")

    @pytest.mark.asyncio
    async def test_unauthorized_without_token(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v2/downloads/abc123/clip.mp4")
        assert resp.status_code in (401, 403, 422)
