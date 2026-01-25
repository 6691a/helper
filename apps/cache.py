"""Redis 캐시 연결 관리"""

import json
from typing import Any

import redis.asyncio as redis

from apps.types.redis import RedisConfig


class RedisCache:
    """Redis 캐시 클라이언트 래퍼"""

    def __init__(self, config: RedisConfig):
        self.config = config
        self._client: redis.Redis | None = None

    async def get_client(self) -> redis.Redis:
        """Redis 클라이언트를 가져옵니다 (지연 로딩)"""
        if self._client is None:
            self._client = redis.from_url(
                f"redis://{self.config.host}:{self.config.port}/{self.config.db}",
                password=self.config.password,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._client

    async def close(self) -> None:
        """Redis 연결을 종료합니다"""
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def get(self, key: str) -> str | None:
        """캐시에서 값을 가져옵니다"""
        client = await self.get_client()
        result: str | None = await client.get(key)
        return result

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        """캐시에 값을 저장합니다

        Args:
            key: 캐시 키
            value: 저장할 값
            ex: 만료 시간(초). None이면 만료하지 않음
        """
        client = await self.get_client()
        await client.set(key, value, ex=ex)

    async def delete(self, key: str) -> None:
        """캐시에서 값을 삭제합니다"""
        client = await self.get_client()
        await client.delete(key)

    async def get_json(self, key: str) -> Any | None:
        """JSON으로 저장된 캐시 값을 가져옵니다"""
        value = await self.get(key)
        if value is None:
            return None
        return json.loads(value)

    async def set_json(self, key: str, value: Any, ex: int | None = None) -> None:
        """값을 JSON으로 직렬화하여 캐시에 저장합니다"""
        json_str = json.dumps(value, ensure_ascii=False)
        await self.set(key, json_str, ex=ex)
