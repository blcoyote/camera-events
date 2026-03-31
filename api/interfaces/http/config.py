"""HTTP router for the public application-configuration endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from application.config.service import get_app_config
from domain.config.models import AppConfigModel

router = APIRouter(
    prefix="/api/v1",
    tags=["v1/application-configuration"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/application-configuration",
    status_code=200,
    response_model=AppConfigModel,
)
async def get_application_configuration() -> AppConfigModel:
    """
    Return the Firebase web-app configuration for the frontend.

    This endpoint is intentionally unauthenticated — the browser needs these
    values before a user session exists.
    """
    return get_app_config()
