"""Frigate NVR HTTP API adapter."""
from __future__ import annotations

import pydantic
import requests
from loguru import logger

from domain.event.models import CameraEvent, CameraEventQueryParams
from lib.settings import get_settings


class FrigateClient:
    """
    HTTP client for the Frigate NVR REST API.

    All methods communicate with the Frigate base URL configured in settings.
    """

    def get_events(
        self, params: CameraEventQueryParams | None = None
    ) -> list[CameraEvent]:
        """Fetch a list of events from Frigate, optionally filtered by *params*."""
        if params is None:
            params = CameraEventQueryParams()
        url = f"{get_settings().frigate_baseurl}/api/events"
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.get(
                url,
                params=params.model_dump(exclude_none=True),
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            adapter = pydantic.TypeAdapter(list[CameraEvent])
            return adapter.validate_python(response.json())
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"Error fetching events from Frigate: {e}")
            raise

    def get_event(self, event_id: str) -> CameraEvent:
        """Fetch a single event by *event_id* from Frigate."""
        url = f"{get_settings().frigate_baseurl}/api/events/{event_id}"
        response = requests.get(url, headers={"Content-Type": "application/json"}, timeout=10)
        response.raise_for_status()
        adapter = pydantic.TypeAdapter(CameraEvent)
        return adapter.validate_python(response.json())

    def get_snapshot(self, event_id: str) -> bytes:
        """Fetch snapshot JPEG bytes for event *event_id* directly from Frigate."""
        url = f"{get_settings().frigate_baseurl}/api/events/{event_id}/snapshot.jpg"
        return requests.get(url, timeout=10).content

    def get_latest(self, camera: str) -> bytes:
        """Fetch the latest frame JPEG bytes for *camera* directly from Frigate."""
        url = f"{get_settings().frigate_baseurl}/api/{camera}/latest.jpg"
        return requests.get(url, timeout=10).content

    def get_clip(self, event_id: str) -> bytes:
        """Fetch clip MP4 bytes for event *event_id* directly from Frigate."""
        url = f"{get_settings().frigate_baseurl}/api/events/{event_id}/clip.mp4"
        return requests.get(url, timeout=30).content
