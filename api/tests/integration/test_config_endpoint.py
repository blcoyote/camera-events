"""
Integration tests for /api/v1/application-configuration.

This endpoint is unauthenticated and returns a JSON object describing
the Firebase web-app configuration.  We patch the underlying
``get_app_config`` function so tests are independent of real credentials.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest
from httpx import AsyncClient


_FAKE_CONFIG = {
    "apiKey": "test-api-key",
    "authDomain": "test.firebaseapp.com",
    "projectId": "test-project",
    "storageBucket": "test.appspot.com",
    "messagingSenderId": "123456789",
    "appId": "1:123456789:web:abc",
    "measurementId": "G-TEST",
    "messagingKey": "test-messaging-key",
}


class TestGetApplicationConfiguration:
    """Tests for the application-configuration endpoint."""

    @pytest.mark.asyncio
    async def test_returns_200(self, client: AsyncClient) -> None:
        """Endpoint must return HTTP 200."""
        with patch("interfaces.http.config.get_app_config", return_value=_FAKE_CONFIG):
            resp = await client.get("/api/v1/application-configuration")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_returns_all_required_fields(self, client: AsyncClient) -> None:
        """Response body must contain all Firebase config keys."""
        with patch("interfaces.http.config.get_app_config", return_value=_FAKE_CONFIG):
            resp = await client.get("/api/v1/application-configuration")
        body = resp.json()
        required_keys = {
            "apiKey",
            "authDomain",
            "projectId",
            "storageBucket",
            "messagingSenderId",
            "appId",
            "measurementId",
            "messagingKey",
        }
        assert required_keys.issubset(body.keys())

    @pytest.mark.asyncio
    async def test_no_auth_required(self, client: AsyncClient) -> None:
        """The endpoint must be accessible without any auth header or token."""
        with patch("interfaces.http.config.get_app_config", return_value=_FAKE_CONFIG):
            resp = await client.get("/api/v1/application-configuration")
        # Must never be a 401/403 regardless of headers
        assert resp.status_code not in (401, 403)

    @pytest.mark.asyncio
    async def test_content_type_is_json(self, client: AsyncClient) -> None:
        """Response Content-Type must be application/json."""
        with patch("interfaces.http.config.get_app_config", return_value=_FAKE_CONFIG):
            resp = await client.get("/api/v1/application-configuration")
        assert "application/json" in resp.headers["content-type"]
