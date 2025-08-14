import io
from typing import List
from fastapi import APIRouter, Depends
from firebase.auth import verify_user_check
from lib.settings import get_settings
from tasks.event_tasks import get_clip, get_events, get_latest, get_snapshot, get_event
from models.event_model import CameraEvent, CameraEventQueryParams
from services.cache_service import event_cache_service
from starlette.responses import StreamingResponse

router = APIRouter(
    prefix="/api/v2/events",
    tags=["v2/events"],
    dependencies=[Depends(verify_user_check)],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[CameraEvent], status_code=200)
async def read_events(params: CameraEventQueryParams = Depends()):
    """
    Retrieve camera events with Redis caching (10-minute TTL).
    
    Args:
        params: Query parameters for filtering events
        
    Returns:
        List of camera events
    """
    # Try to get events from cache first
    cached_events = event_cache_service.get_cached_events(params)
    
    if cached_events is not None:
        return cached_events
    
    # If not in cache, fetch from database
    events = get_events(params)
    
    # Cache the results
    event_cache_service.cache_events(params, events)
    
    return events

@router.delete("/cache", status_code=200)
async def bust_events_cache():
    """
    Bust all event caches.
    
    Returns:
        dict: Number of cache entries deleted
    """
    deleted_count = event_cache_service.bust_cache()
    return {"message": f"Cache busted successfully", "deleted_entries": deleted_count}

@router.get("/cameras", response_model=List[str], status_code=200)
async def read_camera_list():
    return get_settings().cameras


@router.get("/{event_id}", response_model=CameraEvent, status_code=200)
async def read_event(event_id: str):
    return get_event(id=event_id)


@router.get("/{event_id}/snapshot.jpg", status_code=200)
async def read_event_snapshot(event_id: str):
    return StreamingResponse(io.BytesIO(get_snapshot(event_id)), media_type="image/jpg")


@router.get("/{camera}/latest.jpg", status_code=200)
async def read_event_latest(camera: str):
    return StreamingResponse(io.BytesIO(get_latest(camera)), media_type="image/jpg")


@router.get("/{event_id}/clip.mp4", status_code=200)
async def read_event_clip(event_id: str):
    return StreamingResponse(io.BytesIO(get_clip(event_id)), media_type="video/mp4")
