"""FCM device registration use-case service."""
from __future__ import annotations

from loguru import logger

from infrastructure.firebase.app import subscribe_topic
from infrastructure.redis.client import RedisSetClient


class FcmService:
    """
    Registers FCM device tokens and subscribes them to the camera-events topic.

    Args:
        redis: Redis client used to persist the set of registered tokens.
    """

    def __init__(self, redis: RedisSetClient) -> None:
        self._redis = redis

    def register_token(self, fcm_token: str) -> None:
        """
        Persist *fcm_token* and subscribe it to the FCM cameraevents topic.

        Args:
            fcm_token: The device FCM registration token to register.
        """
        try:
            self._redis.add_to_set("fcm_tokens", fcm_token)
            subscribe_topic(fcm_token)
        except Exception as e:
            logger.error(f"Failed to register FCM token: {e}")
            raise
