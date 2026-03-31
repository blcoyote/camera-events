import asyncio
from typing import List
from loguru import logger
from datetime import datetime, timedelta
from firebase.firebase import send_multiple_topic_push, send_topic_push
from tasks.event_tasks import get_clip, get_events, get_snapshot
from models.event_model import CameraEvent, CameraEventQueryParams
from services.cache_service import event_cache_service
from services.minio_service import get_minio_service

POLLING_INTERVAL = 30

@logger.catch()
async def poll_for_new_events():
    while True:
        await fetch_and_process_events()
        await asyncio.sleep(POLLING_INTERVAL)

async def fetch_and_process_events():
    aftertime = datetime.now() - timedelta(seconds=POLLING_INTERVAL)
    params = CameraEventQueryParams()
    params.after = int(aftertime.timestamp())
    params.limit = 20

    aftertime = datetime.now()  # next run
    events: List[CameraEvent] = []

    try:
        events = get_events(params)
        # logger.info(f"Got {len(events)} events from api")

        await mirror_events_to_minio(events)
        await process_events(events)
    except Exception as e:
        logger.error(f"Error getting events from api: {e}")

async def mirror_events_to_minio(events: List[CameraEvent]):
    """Mirror snapshot and clip for each new event into MinIO object storage."""
    if not events:
        return

    minio = get_minio_service()
    for event in events:
        if event.has_snapshot:
            snapshot_key = f"{event.id}/snapshot.jpg"
            if not minio.exists(snapshot_key):
                try:
                    data = get_snapshot(event.id)
                    minio.upload(snapshot_key, data, "image/jpeg")
                    logger.info(f"MinIO: mirrored snapshot for event {event.id}")
                except Exception as e:
                    logger.error(f"MinIO: failed to mirror snapshot for event {event.id}: {e}")

        if event.has_clip:
            clip_key = f"{event.id}/clip.mp4"
            if not minio.exists(clip_key):
                try:
                    data = get_clip(event.id)
                    minio.upload(clip_key, data, "video/mp4")
                    logger.info(f"MinIO: mirrored clip for event {event.id}")
                except Exception as e:
                    logger.error(f"MinIO: failed to mirror clip for event {event.id}: {e}")

async def process_events(events: List[CameraEvent]):
    try:
        if len(events) == 1:
            send_topic_push(events[0])
        elif len(events) > 1:
            logger.info(f"Found {len(events)} events. Pushing to clients")
            send_multiple_topic_push(events)
    except Exception as e:
        logger.error(f"Error sending event to firebase: {e}")
    if len(events) > 0:
        deleted_count = event_cache_service.bust_cache()
        logger.info(f"Cache busted successfully, deleted entries: {deleted_count}")

    