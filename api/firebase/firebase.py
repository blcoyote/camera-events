from functools import lru_cache
import json
import os
import base64
from typing import List
from urllib.parse import urljoin
from firebase_admin import credentials, messaging, initialize_app
from loguru import logger
from database.redis_datastore import set_temporary_image_token
from lib.settings import get_settings

from models.event_model import CameraEvent

firebase_app = None
firebase_creds_env = os.getenv("UVICORN_FIREBASE_CREDENTIALS")
if firebase_creds_env is None:
    raise ValueError("Environment variable 'UVICORN_FIREBASE_CREDENTIALS' is not set.")
creds_dict = json.loads(base64.b64decode(firebase_creds_env))

firebase_cred = credentials.Certificate(creds_dict)
topic = "cameraevents"

@lru_cache()
def get_firebase_app():
    firebase_app = initialize_app(firebase_cred)
    return firebase_app


def subscribe_topic(tokens): # tokens is a list of registration tokens
    response = messaging.subscribe_to_topic(tokens, topic)
    if response.failure_count > 0:
        logger.error(
            f"Failed to subscribe to topic {topic} due to {list(map(lambda e: e.reason, response.errors))}"
        )

def unsubscribe_topic(tokens): # tokens is a list of registration tokens
    response = messaging.unsubscribe_from_topic(tokens, topic)
    if response.failure_count > 0:
        logger.error(
            f"Failed to subscribe to topic {topic} due to {list(map(lambda e: e.reason, response.errors))}"
        )

@logger.catch()
def send_topic_push(event: CameraEvent):
    image_token = set_temporary_image_token(event.id)
    logger.info(f"Sending push notification for event {event.id} with image token {image_token}")
    message = messaging.Message(
        topic=topic,
        webpush=messaging.WebpushConfig(
            notification=messaging.WebpushNotification(
                title=f"Person set i {event.camera}",
                body=f"id: {event.id}",
                icon=f"{get_settings().base_url}/pwa-64x64.png",
                image=f"{get_settings().base_url}/api/v2/attachments/notification/{image_token}"
            ),
            fcm_options=messaging.WebpushFCMOptions(
                link=urljoin(get_settings().base_url, f"/eventnotification/{event.id}")
            ),
            headers={"Urgency": "high", "TTL": "3600"},
            
        ),
        android=messaging.AndroidConfig(
            notification=messaging.AndroidNotification(
                title=f"Person set i {event.camera}", body=f"id: {event.id}",
                icon=f"{get_settings().base_url}/pwa-64x64.png"
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
def send_multiple_topic_push(events: List[CameraEvent]):
    cameras = set(event.camera for event in events)
    message = messaging.Message(
        topic="cameraevents",
        webpush=messaging.WebpushConfig(
            notification=messaging.WebpushNotification(
                title=f"{len(events)} kamera events modtaget", 
                body=",".join(cameras),
                icon=f"{get_settings().base_url}/pwa-64x64.png",
            ),
            fcm_options=messaging.WebpushFCMOptions(
                link=f"{get_settings().base_url}/events",
            ),
            headers={"Urgency": "high"},
        ),
        android=messaging.AndroidConfig(
            notification=messaging.AndroidNotification(
                title=f"{len(events)} kamera events modtaget", 
                body=",".join(cameras),
                icon=f"{get_settings().base_url}/pwa-64x64.png"
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


def send_token_push(title, body, tokens):
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
        title=title,
        body=body
        ),
        tokens=tokens
    )
    messaging.send_multicast(message)
