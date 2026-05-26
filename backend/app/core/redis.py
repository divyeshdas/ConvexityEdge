import redis.asyncio as aioredis
from redis.exceptions import ConnectionError as RedisConnectionError, RedisError
from app.core.config import settings
import hashlib
import json
import orjson
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

_redis_client: Optional[aioredis.Redis] = None
_redis_available: bool = True   # flips to False on first connection failure


async def get_redis() -> Optional[aioredis.Redis]:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
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
    """Return cached value or None — never raises, Redis failure = cache miss."""
    try:
        r = await get_redis()
        val = await r.get(key)
        if val is None:
            return None
        return orjson.loads(val)
    except (RedisConnectionError, RedisError, OSError):
        return None
    except Exception:
        return None


async def cache_set(key: str, value: Any, ttl: int = None) -> None:
    """Write to cache — silently swallows Redis errors."""
    try:
        r = await get_redis()
        ttl = ttl or settings.cache_ttl
        await r.setex(key, ttl, orjson.dumps(value))
    except (RedisConnectionError, RedisError, OSError):
        pass
    except Exception:
        pass


async def cache_delete(key: str) -> None:
    try:
        r = await get_redis()
        await r.delete(key)
    except Exception:
        pass
