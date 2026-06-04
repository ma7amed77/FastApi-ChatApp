import redis.asyncio as aioredis
from .config import Config

class RateLimiter():
    def __init__(self):
        self.redis = aioredis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=2)
        self.window = Config.RATE_WINDOW
        self.limit = Config.RATE_LIMIT
    async def __call__(self, key:str):
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, self.window) 
        return count <= self.limit