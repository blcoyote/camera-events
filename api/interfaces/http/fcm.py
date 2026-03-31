"""HTTP router for FCM device token registration."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from loguru import logger

from application.fcm.service import FcmService
from infrastructure.firebase.auth import verify_user_check
from interfaces.http.dependencies import get_fcm_service

router = APIRouter(
    prefix="/api/v2",
    tags=["v2/fcm"],
    dependencies=[Depends(verify_user_check)],
    responses={404: {"description": "Not found"}},
)


@router.get("/fcm", status_code=200)
async def register_fcm(
    fcm_token: str,
    service: FcmService = Depends(get_fcm_service),
) -> dict:
    """
    Register a device FCM token and subscribe it to the cameraevents topic.

    Args:
        fcm_token: The FCM registration token from the client device.
        service: Injected FCM service.
    """
    try:
        service.register_token(fcm_token)
    except Exception as e:
        logger.error(f"Failed to handle FCM token: {e}")
    return {}
