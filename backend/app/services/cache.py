import json
from typing import Any

import redis.asyncio as redis

from app.config.settings import get_settings

settings = get_settings()


class CacheService:
    def __init__(self):
        self._redis: redis.Redis | None = None

    async def connect(self):
        self._redis = redis.from_url(settings.redis_url, decode_responses=True)

    async def disconnect(self):
        if self._redis:
            await self._redis.close()

    async def get(self, key: str) -> Any | None:
        if not self._redis:
            return None
        value = await self._redis.get(key)
        return json.loads(value) if value else None

    async def set(self, key: str, value: Any, ttl: int = 60):
        if not self._redis:
            return
        await self._redis.set(key, json.dumps(value, default=str), ex=ttl)

    async def delete(self, key: str):
        if self._redis:
            await self._redis.delete(key)

    async def publish(self, channel: str, message: dict):
        if self._redis:
            await self._redis.publish(channel, json.dumps(message, default=str))


cache_service = CacheService()
