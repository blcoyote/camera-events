"""Frontend Firebase configuration loaded from environment variables."""
import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


@lru_cache()
def get_app_config() -> "FrontEndConfig":
    """Return the cached :class:`FrontEndConfig` singleton."""
    return FrontEndConfig()


class FrontEndConfig(BaseSettings):
    """
    Configuration for the frontend Firebase integration, loaded from environment variables.
    """

    apiKey: str = Field(default_factory=lambda: os.getenv("UVICORN_FIREBASE_APIKEY", ""))
    authDomain: str = Field(default_factory=lambda: os.getenv("UVICORN_AUTHDOMAIN", ""))
    projectId: str = Field(default_factory=lambda: os.getenv("UVICORN_PROJECTID", ""))
    storageBucket: str = Field(default_factory=lambda: os.getenv("UVICORN_STORAGEBUCKET", ""))
    messagingSenderId: str = Field(default_factory=lambda: os.getenv("UVICORN_MESSAGESENDERID", ""))
    appId: str = Field(default_factory=lambda: os.getenv("UVICORN_APPID", ""))
    measurementId: str = Field(default_factory=lambda: os.getenv("UVICORN_MEASUREMENTID", ""))
    messagingKey: str = Field(default_factory=lambda: os.getenv("UVICORN_MESSAGINGKEY", ""))
