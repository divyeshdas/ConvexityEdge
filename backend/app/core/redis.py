import redis.asyncio as aioredis
from app.core.config import settings
import hashlib
import json
import orjson
from typing import Any, Optional


_redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis():
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None


def make_cache_key(prefix: str, **kwargs) -> str:
    payload = json.dumps(kwargs, sort_keys=True, default=str)
    digest = hashlib.sha256(payload.encode()).hexdigest()[:16]
    return f"convexity:{prefix}:{digest}"


async def cache_get(key: str) -> Optional[Any]:
    r = await get_redis()
    val = await r.get(key)
    if val is None:
        return None
    return orjson.loads(val)


async def cache_set(key: str, value: Any, ttl: int = None) -> None:
    r = await get_redis()
    ttl = ttl or settings.cache_ttl
    await r.setex(key, ttl, orjson.dumps(value))


async def cache_delete(key: str) -> None:
    r = await get_redis()
    await r.delete(key)
