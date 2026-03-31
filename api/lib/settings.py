from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings
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
    redis_port: int = int(os.getenv("UVICORN_REDIS_PORT", "6379"))
    redis_password: str = os.getenv("UVICORN_REDIS_PASSWORD", "")
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "camera-events-minio:9000")
    minio_access_key: str = os.getenv("MINIO_ROOT_USER", "")
    minio_secret_key: str = os.getenv("MINIO_ROOT_PASSWORD", "")
    minio_bucket: str = os.getenv("MINIO_BUCKET", "camera-events")
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
