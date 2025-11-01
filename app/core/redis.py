"""
Redis Configuration

Redis Setup für Caching, Session Management und Rate Limiting.
"""

import json
import logging
import pickle
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, List, Optional, Union

import redis.asyncio as redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Redis connection pool
redis_pool: Optional[redis.ConnectionPool] = None
redis_client: Optional[redis.Redis] = None


async def init_redis():
    """Initialize Redis connection"""

    global redis_pool, redis_client

    try:
        logger.info("🔴 Initializing Redis connection...")

        # Redis URL from settings or default
        redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")

        # Create connection pool
        redis_pool = redis.ConnectionPool.from_url(
            redis_url,
            max_connections=20,
            retry_on_timeout=True,
            socket_keepalive=True,
            socket_keepalive_options={},
            health_check_interval=30,
        )

        # Create Redis client
        redis_client = redis.Redis(
            connection_pool=redis_pool,
            decode_responses=False,  # We'll handle encoding ourselves
        )

        # Test connection
        await redis_client.ping()

        logger.info("✅ Redis initialized successfully")

    except Exception as e:
        logger.warning(f"⚠️ Redis initialization failed: {e}")
        logger.info("📝 Falling back to in-memory caching")
        redis_client = None
        redis_pool = None


async def close_redis():
    """Close Redis connections"""

    global redis_client, redis_pool

    try:
        if redis_client:
            await redis_client.close()
            logger.info("✅ Redis connections closed")
    except Exception as e:
        logger.error(f"❌ Error closing Redis: {e}")
    finally:
        redis_client = None
        redis_pool = None


def get_redis_client() -> Optional[redis.Redis]:
    """Get Redis client instance"""
    return redis_client


# Cache Manager
class CacheManager:
    """Redis-based cache manager with fallback to in-memory"""

    def __init__(self):
        self.redis = get_redis_client()
        self.memory_cache = {}  # Fallback in-memory cache
        self.memory_cache_ttl = {}  # TTL tracking for memory cache

    def _clean_memory_cache(self):
        """Clean expired entries from memory cache"""
        current_time = datetime.utcnow()
        expired_keys = [
            key
            for key, ttl in self.memory_cache_ttl.items()
            if ttl and current_time > ttl
        ]
        for key in expired_keys:
            self.memory_cache.pop(key, None)
            self.memory_cache_ttl.pop(key, None)

    async def get(self, key: str, default=None) -> Any:
        """Get value from cache"""

        if self.redis:
            try:
                value = await self.redis.get(f"mindbridge:{key}")
                if value:
                    return pickle.loads(value)
                return default
            except Exception as e:
                logger.warning(f"Redis get failed for {key}: {e}")

        # Fallback to memory cache
        self._clean_memory_cache()
        return self.memory_cache.get(key, default)

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL"""

        if self.redis:
            try:
                serialized = pickle.dumps(value)
                await self.redis.setex(f"mindbridge:{key}", ttl, serialized)
                return True
            except Exception as e:
                logger.warning(f"Redis set failed for {key}: {e}")

        # Fallback to memory cache
        self.memory_cache[key] = value
        self.memory_cache_ttl[key] = datetime.utcnow() + timedelta(seconds=ttl)
        return True

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""

        if self.redis:
            try:
                await self.redis.delete(f"mindbridge:{key}")
                return True
            except Exception as e:
                logger.warning(f"Redis delete failed for {key}: {e}")

        # Fallback to memory cache
        self.memory_cache.pop(key, None)
        self.memory_cache_ttl.pop(key, None)
        return True

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""

        if self.redis:
            try:
                return bool(await self.redis.exists(f"mindbridge:{key}"))
            except Exception as e:
                logger.warning(f"Redis exists failed for {key}: {e}")

        # Fallback to memory cache
        self._clean_memory_cache()
        return key in self.memory_cache

    async def increment(self, key: str, amount: int = 1, ttl: int = 3600) -> int:
        """Increment counter in cache"""

        if self.redis:
            try:
                pipe = self.redis.pipeline()
                pipe.incr(f"mindbridge:{key}", amount)
                pipe.expire(f"mindbridge:{key}", ttl)
                results = await pipe.execute()
                return results[0]
            except Exception as e:
                logger.warning(f"Redis incr failed for {key}: {e}")

        # Fallback to memory cache
        self._clean_memory_cache()
        current = self.memory_cache.get(key, 0)
        new_value = current + amount
        self.memory_cache[key] = new_value
        self.memory_cache_ttl[key] = datetime.utcnow() + timedelta(seconds=ttl)
        return new_value

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache"""

        if self.redis:
            try:
                redis_keys = [f"mindbridge:{key}" for key in keys]
                values = await self.redis.mget(redis_keys)
                result = {}
                for i, value in enumerate(values):
                    if value:
                        result[keys[i]] = pickle.loads(value)
                return result
            except Exception as e:
                logger.warning(f"Redis mget failed: {e}")

        # Fallback to memory cache
        self._clean_memory_cache()
        return {
            key: self.memory_cache.get(key) for key in keys if key in self.memory_cache
        }

    async def set_many(self, mapping: Dict[str, Any], ttl: int = 3600) -> bool:
        """Set multiple values in cache"""

        if self.redis:
            try:
                pipe = self.redis.pipeline()
                for key, value in mapping.items():
                    serialized = pickle.dumps(value)
                    pipe.setex(f"mindbridge:{key}", ttl, serialized)
                await pipe.execute()
                return True
            except Exception as e:
                logger.warning(f"Redis mset failed: {e}")

        # Fallback to memory cache
        expiry = datetime.utcnow() + timedelta(seconds=ttl)
        for key, value in mapping.items():
            self.memory_cache[key] = value
            self.memory_cache_ttl[key] = expiry
        return True


# Global cache instance
cache = CacheManager()


# Rate Limiter using Redis
class RedisRateLimiter:
    """Redis-based rate limiter with sliding window"""

    def __init__(self):
        self.redis = get_redis_client()
        self.memory_requests = {}  # Fallback for in-memory rate limiting

    async def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        """Check if request is allowed under rate limit"""

        if self.redis:
            return await self._redis_rate_limit(key, limit, window_seconds)
        else:
            return await self._memory_rate_limit(key, limit, window_seconds)

    async def _redis_rate_limit(
        self, key: str, limit: int, window_seconds: int
    ) -> bool:
        """Redis-based sliding window rate limiting"""

        try:
            current_time = datetime.utcnow().timestamp()
            window_start = current_time - window_seconds

            pipe = self.redis.pipeline()

            # Remove expired entries
            pipe.zremrangebyscore(f"rl:{key}", 0, window_start)

            # Count current requests
            pipe.zcard(f"rl:{key}")

            # Add current request
            pipe.zadd(f"rl:{key}", {str(current_time): current_time})

            # Set expiry
            pipe.expire(f"rl:{key}", window_seconds + 1)

            results = await pipe.execute()
            current_requests = results[1]

            return current_requests < limit

        except Exception as e:
            logger.warning(f"Redis rate limit failed for {key}: {e}")
            return True  # Allow request if Redis fails

    async def _memory_rate_limit(
        self, key: str, limit: int, window_seconds: int
    ) -> bool:
        """Memory-based rate limiting fallback"""

        current_time = datetime.utcnow().timestamp()
        window_start = current_time - window_seconds

        # Initialize or get request history
        if key not in self.memory_requests:
            self.memory_requests[key] = []

        # Remove expired requests
        self.memory_requests[key] = [
            req_time
            for req_time in self.memory_requests[key]
            if req_time > window_start
        ]

        # Check limit
        if len(self.memory_requests[key]) >= limit:
            return False

        # Add current request
        self.memory_requests[key].append(current_time)
        return True

    async def get_remaining(self, key: str, limit: int, window_seconds: int) -> int:
        """Get remaining requests for rate limit"""

        if self.redis:
            try:
                current_time = datetime.utcnow().timestamp()
                window_start = current_time - window_seconds

                # Count current requests
                current_requests = await self.redis.zcount(
                    f"rl:{key}", window_start, current_time
                )
                return max(0, limit - current_requests)

            except Exception as e:
                logger.warning(f"Redis rate limit check failed for {key}: {e}")
                return limit

        # Memory fallback
        current_time = datetime.utcnow().timestamp()
        window_start = current_time - window_seconds

        if key not in self.memory_requests:
            return limit

        valid_requests = [
            req_time
            for req_time in self.memory_requests[key]
            if req_time > window_start
        ]

        return max(0, limit - len(valid_requests))


# Global rate limiter instance
rate_limiter = RedisRateLimiter()


# Session Manager
class SessionManager:
    """Redis-based session management"""

    def __init__(self):
        self.redis = get_redis_client()
        self.memory_sessions = {}  # Fallback

    async def create_session(
        self, session_id: str, user_data: Dict[str, Any], ttl: int = 3600
    ) -> bool:
        """Create user session"""

        session_data = {
            "user_data": user_data,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
        }

        if self.redis:
            try:
                serialized = json.dumps(session_data)
                await self.redis.setex(f"session:{session_id}", ttl, serialized)
                return True
            except Exception as e:
                logger.warning(f"Session creation failed: {e}")

        # Memory fallback
        self.memory_sessions[session_id] = {
            **session_data,
            "expires_at": datetime.utcnow() + timedelta(seconds=ttl),
        }
        return True

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""

        if self.redis:
            try:
                data = await self.redis.get(f"session:{session_id}")
                if data:
                    return json.loads(data)
                return None
            except Exception as e:
                logger.warning(f"Session retrieval failed: {e}")

        # Memory fallback
        session = self.memory_sessions.get(session_id)
        if session and session["expires_at"] > datetime.utcnow():
            return session
        elif session:
            # Expired session
            del self.memory_sessions[session_id]

        return None

    async def update_session(self, session_id: str, user_data: Dict[str, Any]) -> bool:
        """Update session data"""

        session = await self.get_session(session_id)
        if not session:
            return False

        session["user_data"] = user_data
        session["last_activity"] = datetime.utcnow().isoformat()

        if self.redis:
            try:
                serialized = json.dumps(session)
                ttl = await self.redis.ttl(f"session:{session_id}")
                if ttl > 0:
                    await self.redis.setex(f"session:{session_id}", ttl, serialized)
                    return True
            except Exception as e:
                logger.warning(f"Session update failed: {e}")

        # Memory fallback
        if session_id in self.memory_sessions:
            self.memory_sessions[session_id].update(session)
            return True

        return False

    async def delete_session(self, session_id: str) -> bool:
        """Delete session"""

        if self.redis:
            try:
                await self.redis.delete(f"session:{session_id}")
            except Exception as e:
                logger.warning(f"Session deletion failed: {e}")

        # Memory fallback
        self.memory_sessions.pop(session_id, None)
        return True


# Global session manager
session_manager = SessionManager()


# Decorators for caching
def cache_result(ttl: int = 3600, key_prefix: str = ""):
    """Decorator to cache function results"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"

            # Try to get from cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


# Redis health check
async def check_redis_health() -> dict:
    """Check Redis connection health"""

    if not redis_client:
        return {"status": "disabled", "message": "Redis not configured"}

    try:
        # Test basic operations
        await redis_client.ping()
        await redis_client.set("health_check", "ok", ex=60)
        value = await redis_client.get("health_check")
        await redis_client.delete("health_check")

        # Get Redis info
        info = await redis_client.info()

        return {
            "status": "healthy",
            "version": info.get("redis_version"),
            "connected_clients": info.get("connected_clients"),
            "used_memory_human": info.get("used_memory_human"),
            "keyspace": {
                db: info.get(f"db{db}", {}) for db in range(16) if f"db{db}" in info
            },
        }

    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


# Export instances
__all__ = [
    "init_redis",
    "close_redis",
    "get_redis_client",
    "cache",
    "rate_limiter",
    "session_manager",
    "cache_result",
    "check_redis_health",
]
