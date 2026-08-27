import time
from fastapi import HTTPException
from redis.asyncio import Redis

class RateLimiter:
    def __init__(self, redis: Redis, requests: int, window: int):
        self.redis = redis
        self.requests = requests
        self.window = window

    async def check(self, key: str):
        """
        Atomically check and increment a rate limit counter using a Redis pipeline.
        Returns True if allowed, False if exceeded.
        """
        # Create a pipeline to execute INCR and EXPIRE atomically
        pipe = self.redis.pipeline()
        
        # We don't want to use time.time() as key, we just increment the key.
        # But we want a sliding or fixed window. 
        # Using a simple fixed window based on the current timestamp window block:
        current_window = int(time.time() // self.window)
        redis_key = f"rate_limit:{key}:{current_window}"
        
        pipe.incr(redis_key)
        pipe.expire(redis_key, self.window * 2) # keep around a bit longer
        results = await pipe.execute()
        
        count = results[0]
        
        if count > self.requests:
            return False
            
        return True

# Singleton initialization placeholder (populated in lifespan)
redis_client: Redis | None = None

async def rate_limit_auth(ip: str):
    """
    Dependency helper for rate limiting auth endpoints.
    5 requests per minute.
    """
    if not redis_client:
        return # Rate limiting disabled if redis is not connected
        
    limiter = RateLimiter(redis_client, requests=5, window=60)
    allowed = await limiter.check(f"auth:{ip}")
    
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many requests")
