import hashlib
from typing import Any

from redis.asyncio import Redis

_INCREMENT_WITH_EXPIRY = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return count
"""


def rate_limit_key(client_ip: str, normalized_email: str) -> str:
    identity = hashlib.sha256(f"{client_ip}:{normalized_email}".encode()).hexdigest()
    return f"motorscope:login-rate:{identity}"


class LoginRateLimiter:
    def __init__(self, redis: Redis, limit: int, window_seconds: int) -> None:
        self.redis = redis
        self.limit = limit
        self.window_seconds = window_seconds

    async def check(self, client_ip: str, normalized_email: str) -> bool:
        result: Any = await self.redis.eval(
            _INCREMENT_WITH_EXPIRY,
            1,
            rate_limit_key(client_ip, normalized_email),
            self.window_seconds,
        )
        return int(result) <= self.limit
