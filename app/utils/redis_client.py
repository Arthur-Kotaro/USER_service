# app/utils/redis_client.py
import redis.asyncio as aioredis
from app.config import settings


redis_client: aioredis.Redis = aioredis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_BLACKLIST_DB,
    decode_responses=True,
)
