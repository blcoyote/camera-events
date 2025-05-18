from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field
import os


@lru_cache()
def get_settings():
    return Settings() 

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or defaults.
    """
    app_name: str = "Frigate API"
    docs_url: str = os.getenv("UVICORN_DOCS_URL", "")
    app_version: str = os.getenv("UVICORN_APP_VERSION", "")
    frigate_baseurl: str = os.getenv("UVICORN_FRIGATE_BASEURL", "")
    base_url: str = os.getenv("UVICORN_BASEURL", "")
    redis_host: str = os.getenv("UVICORN_REDIS_URL", "")
    redis_password: str = os.getenv("UVICORN_REDIS_PASSWORD", "")
    cameras: List[str] = [
        "gavl_vest",
        "garage",
        "gavl_oest",
        "have",
        "stuen",
        "koekken",
        "vaerksted",
    ]

    class Config:
        extra = "allow"
