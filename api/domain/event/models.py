"""Domain models for camera events (Frigate NVR schema)."""
from enum import Enum

from pydantic import BaseModel


class DataModel(BaseModel):
    """Bounding-box and score data attached to a detected object."""

    box: list[float] = []
    region: list[float] = []
    score: float | None = None
    top_score: float | None = None
    type: str


class CameraEvent(BaseModel):
    """A single detection event as returned by the Frigate NVR HTTP API."""

    data: DataModel | None = None
    camera: str
    end_time: float | None = None
    false_positive: bool | None = None
    has_clip: bool
    has_snapshot: bool
    id: str
    label: str
    plus_id: str | None = None
    retain_indefinitely: bool
    start_time: float
    sub_label: str | None = None
    thumbnail: str | None = None
    zones: list[str] = []


class CameraEventQueryParams(BaseModel):
    """Query parameters used to filter events from the Frigate NVR API."""

    before: int | None = None  # Epoch time
    after: int | None = None  # Epoch time
    cameras: str | None = None  # Comma-separated list of camera names
    labels: str | None = None  # Comma-separated list of labels
    zones: str | None = None  # Comma-separated list of zones
    limit: int | None = 20
    has_snapshot: int | None = None  # 0 or 1
    has_clip: int | None = None  # 0 or 1
    include_thumbnails: int | None = None  # 0 or 1
    in_progress: int | None = None  # 0 or 1


class WsEventType(Enum):
    """WebSocket event type discriminator."""

    MOVEMENT = "movement"
    ADDMORE = "here"


class CameraNotification(BaseModel):
    """Minimal event reference used in push notification payloads."""

    id: str
    camera: str


class WebsocketEvent(BaseModel):
    """Envelope for WebSocket messages pushed to connected clients."""

    type: WsEventType
    content: CameraNotification
