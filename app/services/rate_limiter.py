"""
Rate Limiter Service using Redis sorted sets (sliding window).
"""
import time
import redis.asyncio as redis
from app.config import settings


class RateLimiter:
    """Per-organisation rate limiter using Redis sorted sets."""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self._redis = None
        self.limit = 100  # requests per window
        self.window = 900  # 15 minutes in seconds
    
    async def get_redis(self):
        if self._redis is None:
            self._redis = redis.from_url(self.redis_url)
        return self._redis
    
    async def is_allowed(self, org_id: str) -> tuple[bool, int]:
        """
        Check if request is allowed for the organisation.
        
        Returns:
            (allowed: bool, retry_after: int)
        """
        r = await self.get_redis()
        key = f"ratelimit:{org_id}"
        now = time.time()
        window_start = now - self.window
        
        try:
            # First, clean up old entries and count current requests
            pipe = r.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            results = await pipe.execute()
            
            request_count = results[1]
            
            # Check if under limit FIRST
            if request_count >= self.limit:
                # Over limit - calculate retry_after
                oldest = await r.zrange(key, 0, 0, withscores=True)
                if oldest:
                    retry_after = int(self.window - (now - oldest[0][1]))
                else:
                    retry_after = self.window
                return False, max(retry_after, 1)
            
            # Under limit - add the request
            await r.zadd(key, {str(now): now})
            await r.expire(key, self.window)
            
            return True, 0
            
        except Exception as e:
            print(f"Rate limiter error: {e}")
            # If Redis is down, allow the request (fail open)
            return True, 0
    
    async def get_current_count(self, org_id: str) -> int:
        """Get current request count for organisation."""
        r = await self.get_redis()
        key = f"ratelimit:{org_id}"
        now = time.time()
        window_start = now - self.window
        
        try:
            # Clean up old entries and count
            await r.zremrangebyscore(key, 0, window_start)
            count = await r.zcard(key)
            return count
        except:
            return 0


# Singleton instance
rate_limiter = RateLimiter()
