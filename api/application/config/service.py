"""
Configuration use-case service.

Re-exports :func:`get_app_config` from :mod:`lib.app_config` so that the
interfaces layer always imports from the application layer, keeping the
dependency direction inward.
"""
from lib.app_config import get_app_config  # noqa: F401

__all__ = ["get_app_config"]
