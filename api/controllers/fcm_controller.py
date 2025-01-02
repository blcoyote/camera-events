from fastapi import APIRouter, Depends
from loguru import logger

from database.redis_client import RedisSetClient
from firebase.auth import verify_user_check
from firebase.firebase import subscribe_topic

router = APIRouter(
    prefix="/api/v2",
    tags=["v2/fcm"],
    dependencies=[Depends(verify_user_check)],
    responses={404: {"description": "Not found"}},
)


@router.get("/fcm", status_code=200)
async def register_fcm(
    fcm_token: str,
):
    try:
        redis_client = RedisSetClient()
        redis_client.add_to_set("fcm_tokens", fcm_token)
        subscribe_topic(fcm_token)

    except Exception as e:
        logger.error(f"Failed to handle fcm token: {e}")
