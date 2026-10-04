# app/services/event_publisher.py
import json
import logging
import redis.asyncio as aioredis
from app.config import settings

logger = logging.getLogger(__name__)

CHANNEL = "user.events"
REDIS_EVENTS_DB = 3

_publisher: aioredis.Redis = aioredis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=REDIS_EVENTS_DB,
    decode_responses=True,
)


async def publish_user_event(event_type: str, user_id: int, payload: dict = None):
    try:
        message = json.dumps({
            "type": event_type,
            "user_id": user_id,
            "payload": payload or {},
        })
        await _publisher.publish(CHANNEL, message)
        logger.info(f"Published {event_type} for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to publish {event_type}: {e}")
