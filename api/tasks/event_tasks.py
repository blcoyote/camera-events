from typing import List, Optional
import pydantic
import requests
from lib.settings import get_settings
from models.event_model import CameraEvent, CameraEventQueryParams
from loguru import logger

def get_events(params: Optional[CameraEventQueryParams] = CameraEventQueryParams()) -> List[CameraEvent]: 
    url = f"{get_settings().frigate_baseurl}/api/events"
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.get(url, params=params.model_dump() if params else None, headers=headers)
        response.raise_for_status()
        adapter = pydantic.TypeAdapter(List[CameraEvent])
        data = adapter.validate_python(response.json())
        return data
    except Exception as e:
        logger.error(f"Error getting events from frigate: {e}")
        raise(e)


def get_event(id: str) -> CameraEvent: 
    url = f"{get_settings().frigate_baseurl}/api/events/{id}"
    headers = {"Content-Type": "application/json"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    adapter = pydantic.TypeAdapter(CameraEvent)
    data = adapter.validate_python(response.json())

    return data

def get_snapshot(id: str) -> bytes:
    url = f"{get_settings().frigate_baseurl}/api/events/{id}/snapshot.jpg"
    response = requests.get(url).content
    return response

def get_latest(camera: str) -> bytes:
    url = f"{get_settings().frigate_baseurl}/api/{camera}/latest.jpg"
    response = requests.get(url).content
    return response

def get_placeholder() -> bytes:
    with open("pwa-192x192.png", "rb") as image:
        f = image.read()
    return f


def get_clip(id: str) -> bytes:
    url = f"{get_settings().frigate_baseurl}/api/events/{id}/clip.mp4"
    response = requests.get(url).content
    return response


def get_snapshot_cached(id: str) -> bytes:
    """Return snapshot bytes, served from MinIO if available, else fetched from Frigate."""
    from services.minio_service import get_minio_service
    data = get_minio_service().download(f"{id}/snapshot.jpg")
    if data is not None:
        return data
    logger.debug(f"MinIO cache miss for snapshot {id}, fetching from Frigate")
    return get_snapshot(id)


def get_clip_cached(id: str) -> bytes:
    """Return clip bytes, served from MinIO if available, else fetched from Frigate."""
    from services.minio_service import get_minio_service
    data = get_minio_service().download(f"{id}/clip.mp4")
    if data is not None:
        return data
    logger.debug(f"MinIO cache miss for clip {id}, fetching from Frigate")
    return get_clip(id)
