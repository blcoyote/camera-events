"""HTTP router for authenticated file download endpoints."""
from __future__ import annotations

import io

from fastapi import APIRouter, Depends
from starlette.responses import StreamingResponse

from application.event.service import EventService
from infrastructure.firebase.auth import verify_url_token
from interfaces.http.dependencies import get_event_service

router = APIRouter(
    prefix="/api/v2/downloads",
    tags=["v2/downloads"],
    dependencies=[Depends(verify_url_token)],
    responses={404: {"description": "Not found"}},
)


@router.get("/{event_id}/snapshot.jpg", status_code=200)
async def read_event_snapshot(
    event_id: str,
    service: EventService = Depends(get_event_service),
) -> StreamingResponse:
    """Download a snapshot JPEG with a ``Content-Disposition: attachment`` header."""
    return StreamingResponse(
        io.BytesIO(service.get_snapshot_cached(event_id)),
        media_type="image/jpg",
        headers={
            "Content-Disposition": f"attachment; filename=snapshot-{event_id}.jpg",
        },
    )


@router.get("/{camera}/latest.jpg", status_code=200)
async def read_event_latest(
    camera: str,
    service: EventService = Depends(get_event_service),
) -> StreamingResponse:
    """Download the latest frame JPEG for *camera* with a ``Content-Disposition: attachment`` header.
    """
    return StreamingResponse(
        io.BytesIO(service.get_latest(camera)),
        media_type="image/jpg",
        headers={
            "Content-Disposition": f"attachment; filename=latest-{camera}.jpg",
        },
    )


@router.get("/{event_id}/clip.mp4", status_code=200)
async def read_event_clip(
    event_id: str,
    service: EventService = Depends(get_event_service),
) -> StreamingResponse:
    """Download a clip MP4 with a ``Content-Disposition: attachment`` header."""
    return StreamingResponse(
        io.BytesIO(service.get_clip_cached(event_id)),
        media_type="video/mp4",
        headers={
            "Content-Disposition": f"attachment; filename=clip-{event_id}.mp4",
        },
    )
