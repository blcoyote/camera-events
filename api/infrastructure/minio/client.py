"""MinIO (S3-compatible) object storage adapter."""
from __future__ import annotations

import io
from functools import lru_cache

from loguru import logger
from minio import Minio
from minio.error import S3Error

from lib.settings import get_settings


class MinIOService:
    """
    Abstraction layer over MinIO object storage.

    Handles bucket initialisation, uploading, downloading, and existence checks
    for event media objects (snapshots and clips).
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._bucket = settings.minio_bucket
        self._client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=False,
        )
        self._ensure_bucket()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_bucket(self) -> None:
        """Create the configured bucket if it does not already exist."""
        try:
            if not self._client.bucket_exists(self._bucket):
                self._client.make_bucket(self._bucket)
                logger.info(f"MinIO: created bucket '{self._bucket}'")
            else:
                logger.debug(f"MinIO: bucket '{self._bucket}' already exists")
        except S3Error as e:
            logger.error(f"MinIO: failed to ensure bucket '{self._bucket}': {e}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def upload(self, key: str, data: bytes, content_type: str) -> None:
        """
        Upload *data* to the configured bucket under *key*.

        Args:
            key: Object key, e.g. ``"{event_id}/snapshot.jpg"``.
            data: Raw bytes to store.
            content_type: MIME type, e.g. ``"image/jpeg"`` or ``"video/mp4"``.
        """
        try:
            self._client.put_object(
                self._bucket,
                key,
                io.BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
            logger.debug(f"MinIO: uploaded '{key}' ({len(data)} bytes)")
        except S3Error as e:
            logger.error(f"MinIO: failed to upload '{key}': {e}")
            raise

    def download(self, key: str) -> bytes | None:
        """
        Download an object from the configured bucket.

        Args:
            key: Object key to retrieve.

        Returns:
            Raw bytes if the object exists, ``None`` otherwise.
        """
        try:
            response = self._client.get_object(self._bucket, key)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            if e.code == "NoSuchKey":
                return None
            logger.error(f"MinIO: failed to download '{key}': {e}")
            return None

    def exists(self, key: str) -> bool:
        """Return ``True`` if *key* exists in the configured bucket."""
        try:
            self._client.stat_object(self._bucket, key)
            return True
        except S3Error:
            return False


@lru_cache()
def get_minio_service() -> MinIOService:
    """Return the process-level :class:`MinIOService` singleton."""
    return MinIOService()
