"""
Integration test fixtures.

These fixtures start real Redis and MinIO containers via testcontainers,
override FastAPI dependencies so the app uses them, and provide an HTTPX
async test client.

All fixtures in this file are session-scoped so containers start once per
test run and are shared across every integration test.
"""
from __future__ import annotations

import os
from typing import AsyncGenerator
from unittest.mock import patch

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient



# ---------------------------------------------------------------------------
# Override app settings before importing main app
# ---------------------------------------------------------------------------

os.environ.setdefault("UVICORN_APP_VERSION", "0.0.0-test")
os.environ.setdefault("UVICORN_FRIGATE_BASEURL", "http://frigate-unreachable")
os.environ.setdefault("UVICORN_BASEURL", "http://localhost")
os.environ.setdefault("UVICORN_REDIS_URL", "localhost")
os.environ.setdefault("UVICORN_REDIS_PASSWORD", "")
os.environ.setdefault("MINIO_ENDPOINT", "localhost:9000")
os.environ.setdefault("MINIO_ROOT_USER", "minioadmin")
os.environ.setdefault("MINIO_ROOT_PASSWORD", "minioadmin")
os.environ.setdefault("MINIO_BUCKET", "test-bucket")
# Provide a dummy Firebase credential so firebase.py does not crash on import.
# Auth calls are patched in individual tests.
_DUMMY_CREDS = (
    "eyJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsICJwcm9qZWN0X2lkIjogInRlc3QiLCAicHJpdmF0ZV9rZXlfaWQiOiAi"
    "dGVzdCIsICJwcml2YXRlX2tleSI6ICItLS0tLUJFR0lOIFJTQSBQUklWQVRFIEtFWS0tLS0tXG4tLS0tLUVORCBSU0Eg"
    "UFJJVkFURSBLRVktLS0tLVxuIiwgImNsaWVudF9lbWFpbCI6ICJ0ZXN0QHRlc3QuaWFtLmdzZXJ2aWNlYWNjb3VudC5j"
    "b20iLCAiY2xpZW50X2lkIjogIjEyMyIsICJhdXRoX3VyaSI6ICJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20vby9v"
    "YXV0aDIvYXV0aCIsICJ0b2tlbl91cmkiOiAiaHR0cHM6Ly9vYXV0aDIuZ29vZ2xlYXBpcy5jb20vdG9rZW4ifQ=="
)
os.environ.setdefault("UVICORN_FIREBASE_CREDENTIALS", _DUMMY_CREDS)


# ---------------------------------------------------------------------------
# Redis container fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def redis_container():
    """Start a Redis container for the session. Yields (host, port)."""
    try:
        from testcontainers.redis import RedisContainer  # pylint: disable=import-outside-toplevel
        with RedisContainer() as container:
            yield container.get_container_host_ip(), container.get_exposed_port(6379)
    except ImportError:
        pytest.skip("testcontainers not installed — skipping integration tests")


# ---------------------------------------------------------------------------
# MinIO container fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def minio_container():
    """Start a MinIO container for the session. Yields the endpoint string."""
    try:
        from testcontainers.minio import MinioContainer  # pylint: disable=import-outside-toplevel
        with MinioContainer() as container:
            host = container.get_container_host_ip()
            port = container.get_exposed_port(9000)
            yield f"{host}:{port}"
    except ImportError:
        pytest.skip("testcontainers[minio] not installed — skipping integration tests")


# ---------------------------------------------------------------------------
# FastAPI app with overridden dependencies
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def app(redis_container: tuple[str, int], minio_container: str) -> FastAPI:  # pylint: disable=redefined-outer-name
    """Return the FastAPI app wired to test containers."""
    # pylint: disable=import-outside-toplevel
    redis_host, redis_port = redis_container

    # Point settings at the test containers
    os.environ["UVICORN_REDIS_URL"] = redis_host
    os.environ["UVICORN_REDIS_PORT"] = str(redis_port)
    os.environ["UVICORN_REDIS_PASSWORD"] = ""
    os.environ["MINIO_ENDPOINT"] = minio_container

    # Clear settings cache so changes take effect
    from lib.settings import get_settings
    get_settings.cache_clear()

    # Clear service singletons
    from infrastructure.redis.cache import get_event_cache_service
    from infrastructure.minio.client import get_minio_service
    get_event_cache_service.cache_clear()
    get_minio_service.cache_clear()

    # Clear application-layer dependency caches so they are rebuilt with the
    # updated settings (Redis URL / MinIO endpoint).
    from interfaces.http.dependencies import (
        get_frigate_client,
        get_event_service,
        get_attachment_service,
    )
    get_frigate_client.cache_clear()
    get_event_service.cache_clear()
    get_attachment_service.cache_clear()

    # Clear Firebase app singleton so it is rebuilt with the (mocked) initialiser.
    from infrastructure.firebase.app import get_firebase_app
    get_firebase_app.cache_clear()

    # Patch get_firebase_app so main.py can be imported without real Firebase
    # credentials.  The patch only needs to last for the duration of the import;
    # the returned MagicMock is stored in main.firebase_App and never used again.
    with patch("infrastructure.firebase.app.get_firebase_app"):
        import main as app_module
    return app_module.app


# ---------------------------------------------------------------------------
# HTTPX async client (per test — fast, no overhead)
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture()  # type: ignore[misc]
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:  # pylint: disable=redefined-outer-name
    """Async HTTPX client that speaks directly to the FastAPI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# Auth mock helper — patches firebase_admin.auth.verify_id_token for a test
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_auth():
    """Patch Firebase token verification to always succeed."""
    fake_claims = {"uid": "test-user", "email": "test@test.com"}
    with patch("infrastructure.firebase.auth.auth.verify_id_token", return_value=fake_claims):
        yield fake_claims
