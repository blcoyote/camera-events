"""Firebase Admin SDK adapter: app initialisation, FCM topic management, push dispatch."""
from __future__ import annotations

import base64
import json
import os
from functools import lru_cache
from typing import List
from urllib.parse import urljoin

from firebase_admin import App, credentials, initialize_app, messaging
from loguru import logger

from domain.event.models import CameraEvent
from infrastructure.redis.datastore import set_temporary_image_token
from lib.settings import get_settings

FCM_TOPIC = "cameraevents"


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------


def _load_firebase_credentials() -> credentials.Certificate:
    """Decode and return Firebase credentials from the environment variable."""
    creds_env = os.getenv("UVICORN_FIREBASE_CREDENTIALS")
    if creds_env is None:
        raise ValueError(
            "Environment variable 'UVICORN_FIREBASE_CREDENTIALS' is not set."
        )
    creds_dict = json.loads(base64.b64decode(creds_env))
    return credentials.Certificate(creds_dict)


@lru_cache()
def get_firebase_app() -> App:
    """Initialise and return the Firebase Admin SDK app (singleton)."""
    return initialize_app(_load_firebase_credentials())


# ---------------------------------------------------------------------------
# Topic management
# ---------------------------------------------------------------------------


def subscribe_topic(token: str) -> None:
    """Subscribe a single FCM registration token to the cameraevents topic."""
    response = messaging.subscribe_to_topic(token, FCM_TOPIC)
    if response.failure_count > 0:
        reasons = [e.reason for e in response.errors]
        logger.error(
            f"Failed to subscribe to topic {FCM_TOPIC}: {reasons}"
        )


def unsubscribe_topic(tokens: list[str]) -> None:
    """Unsubscribe a list of FCM registration tokens from the cameraevents topic."""
    response = messaging.unsubscribe_from_topic(tokens, FCM_TOPIC)
    if response.failure_count > 0:
        reasons = [e.reason for e in response.errors]
        logger.error(
            f"Failed to unsubscribe from topic {FCM_TOPIC}: {reasons}"
        )


# ---------------------------------------------------------------------------
# Push notification dispatch
# ---------------------------------------------------------------------------


@logger.catch()
def send_topic_push(event: CameraEvent) -> None:
    """Send a single-event FCM push to the cameraevents topic."""
    image_token = set_temporary_image_token(event.id)
    logger.info(
        f"Sending push notification for event {event.id} with image token {image_token}"
    )
    settings = get_settings()
    message = messaging.Message(
        topic=FCM_TOPIC,
        webpush=messaging.WebpushConfig(
            notification=messaging.WebpushNotification(
                title=f"Person set i {event.camera}",
                body=f"id: {event.id}",
                icon=f"{settings.base_url}/pwa-64x64.png",
                image=(
                    f"{settings.base_url}"
                    f"/api/v2/attachments/notification/{image_token}"
                ),
            ),
            fcm_options=messaging.WebpushFCMOptions(
                link=urljoin(settings.base_url, f"/eventnotification/{event.id}")
            ),
            headers={"Urgency": "high", "TTL": "3600"},
        ),
        android=messaging.AndroidConfig(
            notification=messaging.AndroidNotification(
                title=f"Person set i {event.camera}",
                body=f"id: {event.id}",
                icon=f"{settings.base_url}/pwa-64x64.png",
            ),
            ttl=36000,
            data={
                "click_action": "FLUTTER_NOTIFICATION_CLICK",
                "sound": "default",
                "status": "done",
                "path": "/eventnotification",
                "id": event.id,
            },
        ),
    )
    messaging.send(message)


@logger.catch()
def send_multiple_topic_push(events: List[CameraEvent]) -> None:
    """Send a multi-event summary FCM push to the cameraevents topic."""
    settings = get_settings()
    cameras = {event.camera for event in events}
    message = messaging.Message(
        topic=FCM_TOPIC,
        webpush=messaging.WebpushConfig(
            notification=messaging.WebpushNotification(
                title=f"{len(events)} kamera events modtaget",
                body=",".join(cameras),
                icon=f"{settings.base_url}/pwa-64x64.png",
            ),
            fcm_options=messaging.WebpushFCMOptions(
                link=f"{settings.base_url}/events",
            ),
        ),
        android=messaging.AndroidConfig(
            notification=messaging.AndroidNotification(
                title=f"{len(events)} kamera events modtaget",
                body=",".join(cameras),
                icon=f"{settings.base_url}/pwa-64x64.png",
            ),
            ttl=36000,
            data={
                "click_action": "FLUTTER_NOTIFICATION_CLICK",
                "sound": "default",
                "status": "done",
                "path": "/events",
                "id": events[0].id,
            },
        ),
    )
    messaging.send(message)


def send_token_push(title: str, body: str, tokens: list[str]) -> None:
    """Send a direct FCM push to a list of device tokens."""
    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        tokens=tokens,
    )
    messaging.send_multicast(message)
