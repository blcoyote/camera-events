"""
Notification domain models.

Re-exports ``CameraNotification`` and ``WebsocketEvent`` from the event domain
so that notification-specific code can import from a dedicated namespace.
"""
from domain.event.models import CameraNotification, WebsocketEvent

__all__ = ["CameraNotification", "WebsocketEvent"]
