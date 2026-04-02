"""HTTP router for camera event endpoints."""
from __future__ import annotations

import io

from fastapi import APIRouter, Depends
from starlette.responses import StreamingResponse

from application.event.service import EventService
from domain.event.models import CameraEvent, CameraEventQueryParams
from infrastructure.firebase.auth import verify_user_check
from interfaces.http.dependencies import get_event_service
from lib.settings import get_settings

router = APIRouter(
    prefix="/api/v2/events",
    tags=["v2/events"],
    dependencies=[Depends(verify_user_check)],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[CameraEvent], status_code=200)
async def read_events(
    params: CameraEventQueryParams = Depends(),
    service: EventService = Depends(get_event_service),
) -> list[CameraEvent]:
    """
    Retrieve camera events, served from the Redis cache when available.

    Args:
        params: Query parameters for filtering events.
        service: Injected event service.

    Returns:
        List of camera events.
    """
    cached = service.get_cached_events(params)
    if cached is not None:
        return cached
    events = service.get_events(params)
    service.cache_events(params, events)
    return events


@router.delete("/cache", status_code=200)
async def bust_events_cache(
    service: EventService = Depends(get_event_service),
) -> dict[str, int | str]:
    """
    Invalidate all cached event list entries.

    Returns:
        ``{"message": ..., "deleted_entries": <count>}``
    """
    deleted = service.bust_cache()
    return {"message": "Cache busted successfully", "deleted_entries": deleted}


@router.get("/cameras", response_model=list[str], status_code=200)
async def read_camera_list() -> list[str]:
    """Return the configured list of camera names."""
    return get_settings().cameras


@router.get("/{event_id}", response_model=CameraEvent, status_code=200)
async def read_event(
    event_id: str,
    service: EventService = Depends(get_event_service),
) -> CameraEvent:
    """Retrieve a single event by *event_id*."""
    return service.get_event(event_id)


@router.get("/{event_id}/snapshot.jpg", status_code=200)
async def read_event_snapshot(
    event_id: str,
    service: EventService = Depends(get_event_service),
) -> StreamingResponse:
    """Stream a snapshot JPEG for *event_id*, served from MinIO when cached."""
    return StreamingResponse(
        io.BytesIO(service.get_snapshot_cached(event_id)), media_type="image/jpg"
    )


@router.get("/{camera}/latest.jpg", status_code=200)
async def read_event_latest(
    camera: str,
    service: EventService = Depends(get_event_service),
) -> StreamingResponse:
    """Stream the latest frame JPEG for *camera*."""
    return StreamingResponse(
        io.BytesIO(service.get_latest(camera)), media_type="image/jpg"
    )


@router.get("/{event_id}/clip.mp4", status_code=200)
async def read_event_clip(
    event_id: str,
    service: EventService = Depends(get_event_service),
) -> StreamingResponse:
    """Stream a clip MP4 for *event_id*, served from MinIO when cached."""
    return StreamingResponse(
        io.BytesIO(service.get_clip_cached(event_id)), media_type="video/mp4"
    )
