"""HTTP router for notification attachment (image token) endpoints."""
from __future__ import annotations

import io

from fastapi import APIRouter, Depends
from loguru import logger
from starlette.responses import StreamingResponse

from application.attachment.service import AttachmentService
from interfaces.http.dependencies import get_attachment_service

router = APIRouter(
    prefix="/api/v2/attachments",
    tags=["v2/attachments"],
    responses={404: {"description": "Not found"}},
)


@router.get("/notification/{image_token}", status_code=200)
async def read_notification_image(
    image_token: str,
    service: AttachmentService = Depends(get_attachment_service),
) -> StreamingResponse:
    """
    Resolve *image_token* to a snapshot JPEG, falling back to a placeholder PNG.

    This endpoint is intentionally public so that FCM notification images can be
    loaded by the device without an authenticated session.

    Args:
        image_token: Short-lived UUID token generated at notification dispatch.
        service: Injected attachment service.
    """
    try:
        data = service.get_snapshot_for_token(image_token)
        if data is not None:
            return StreamingResponse(io.BytesIO(data), media_type="image/jpg")
        return StreamingResponse(
            io.BytesIO(service.get_placeholder()), media_type="image/png"
        )
    except Exception as e:
        logger.error(f"Error serving notification image: {e}")
        return StreamingResponse(
            io.BytesIO(service.get_placeholder()), media_type="image/png"
        )
