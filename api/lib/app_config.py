from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import  Field
import os

@lru_cache()
def get_app_config():
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