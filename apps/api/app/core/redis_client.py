from redis.asyncio import Redis


class RedisClient:
    def __init__(self, redis_url: str) -> None:
        self.client: Redis = Redis.from_url(
            redis_url,
            decode_responses=False,
            socket_connect_timeout=2,
            socket_timeout=2,
            health_check_interval=30,
        )

    async def ping(self) -> None:
        result = await self.client.ping()
        if not result:
            raise ConnectionError("Redis ping failed")

    async def close(self) -> None:
        await self.client.aclose()
