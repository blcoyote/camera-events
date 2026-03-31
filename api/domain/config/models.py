"""Domain model for the Firebase web-app configuration served to the frontend."""
from pydantic import BaseModel


class AppConfigModel(BaseModel):
    """Firebase client-side SDK configuration keys returned by the config endpoint."""

    apiKey: str
    authDomain: str
    projectId: str
    storageBucket: str
    messagingSenderId: str
    appId: str
    measurementId: str
    messagingKey: str
