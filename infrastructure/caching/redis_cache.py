"""
Redis Caching System for MCP Engineering

This module provides Redis-based caching for the MCP Engineering API,
including result caching, session storage, and performance optimization.
"""

import json
import hashlib
import time
from typing import Any, Optional, Dict, List, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from functools import wraps
import redis
from redis.exceptions import RedisError


@dataclass
class CacheConfig:
    """Configuration for Redis caching."""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    max_connections: int = 20
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    health_check_interval: int = 30


class RedisCache:
    """Redis-based caching system."""

    def __init__(self, config: CacheConfig):
        """
        Initialize Redis cache.

        Args:
            config: Cache configuration
        """
        self.config = config
        self.redis_client = redis.Redis(
            host=config.host,
            port=config.port,
            db=config.db,
            password=config.password,
            max_connections=config.max_connections,
            socket_timeout=config.socket_timeout,
            socket_connect_timeout=config.socket_connect_timeout,
            retry_on_timeout=config.retry_on_timeout,
            health_check_interval=config.health_check_interval,
            decode_responses=True,
        )

        # Cache statistics
        self.hits = 0
        self.misses = 0
        self.errors = 0

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate a cache key.

        Args:
            prefix: Key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Generated cache key
        """
        # Create a hash of the arguments
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _serialize_value(self, value: Any) -> str:
        """
        Serialize a value for caching.

        Args:
            value: Value to serialize

        Returns:
            Serialized value
        """
        if isinstance(value, (dict, list, tuple, set)):
            return json.dumps(value, default=str)
        elif hasattr(value, "__dict__"):
            return json.dumps(asdict(value), default=str)
        else:
            return str(value)

    def _deserialize_value(self, value: str) -> Any:
        """
        Deserialize a cached value.

        Args:
            value: Serialized value

        Returns:
            Deserialized value
        """
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            value = self.redis_client.get(key)
            if value is not None:
                self.hits += 1
                return self._deserialize_value(value)
            else:
                self.misses += 1
                return None
        except RedisError as e:
            self.errors += 1
            print(f"Redis get error: {e}")
            return None

    def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """
        Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            serialized_value = self._serialize_value(value)
            return bool(self.redis_client.setex(key, expire, serialized_value))
        except RedisError as e:
            self.errors += 1
            print(f"Redis set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete a value from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            return bool(self.redis_client.delete(key))
        except RedisError as e:
            self.errors += 1
            print(f"Redis delete error: {e}")
            return False

    def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists, False otherwise
        """
        try:
            return bool(self.redis_client.exists(key))
        except RedisError as e:
            self.errors += 1
            print(f"Redis exists error: {e}")
            return False

    def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration time for a key.

        Args:
            key: Cache key
            seconds: Expiration time in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            return bool(self.redis_client.expire(key, seconds))
        except RedisError as e:
            self.errors += 1
            print(f"Redis expire error: {e}")
            return False

    def ttl(self, key: str) -> int:
        """
        Get time to live for a key.

        Args:
            key: Cache key

        Returns:
            Time to live in seconds, -1 if no expiration, -2 if key doesn't exist
        """
        try:
            return self.redis_client.ttl(key)
        except RedisError as e:
            self.errors += 1
            print(f"Redis ttl error: {e}")
            return -2

    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching a pattern.

        Args:
            pattern: Redis pattern (e.g., "user:*")

        Returns:
            Number of keys deleted
        """
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except RedisError as e:
            self.errors += 1
            print(f"Redis clear pattern error: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.hits + self.misses
        hit_ratio = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "errors": self.errors,
            "total_requests": total_requests,
            "hit_ratio": hit_ratio,
            "error_rate": (
                (self.errors / total_requests * 100) if total_requests > 0 else 0
            ),
        }

    def health_check(self) -> bool:
        """
        Check Redis connection health.

        Returns:
            True if healthy, False otherwise
        """
        try:
            self.redis_client.ping()
            return True
        except RedisError:
            return False


def cache_result(expire: int = 3600, key_prefix: str = "cache"):
    """
    Decorator to cache function results.

    Args:
        expire: Cache expiration time in seconds
        key_prefix: Prefix for cache keys

    Returns:
        Decorated function
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

            # Try to get from cache
            cache = RedisCache(CacheConfig())
            cached_result = cache.get(cache_key)

            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, expire)

            return result

        return wrapper

    return decorator


class SessionCache:
    """Session storage using Redis."""

    def __init__(self, cache: RedisCache):
        """
        Initialize session cache.

        Args:
            cache: Redis cache instance
        """
        self.cache = cache
        self.session_prefix = "session"

    def create_session(
        self, user_id: str, data: Dict[str, Any], expire: int = 3600
    ) -> str:
        """
        Create a new session.

        Args:
            user_id: User identifier
            data: Session data
            expire: Session expiration time in seconds

        Returns:
            Session ID
        """
        session_id = f"{self.session_prefix}:{user_id}:{int(time.time())}"
        session_data = {
            "user_id": user_id,
            "data": data,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(seconds=expire)).isoformat(),
        }

        self.cache.set(session_id, session_data, expire)
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data.

        Args:
            session_id: Session identifier

        Returns:
            Session data or None if not found
        """
        return self.cache.get(session_id)

    def update_session(
        self, session_id: str, data: Dict[str, Any], expire: int = 3600
    ) -> bool:
        """
        Update session data.

        Args:
            session_id: Session identifier
            data: New session data
            expire: Session expiration time in seconds

        Returns:
            True if successful, False otherwise
        """
        session_data = self.cache.get(session_id)
        if session_data:
            session_data["data"] = data
            session_data["updated_at"] = datetime.utcnow().isoformat()
            return self.cache.set(session_id, session_data, expire)
        return False

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session identifier

        Returns:
            True if successful, False otherwise
        """
        return self.cache.delete(session_id)

    def clear_user_sessions(self, user_id: str) -> int:
        """
        Clear all sessions for a user.

        Args:
            user_id: User identifier

        Returns:
            Number of sessions deleted
        """
        pattern = f"{self.session_prefix}:{user_id}:*"
        return self.cache.clear_pattern(pattern)


# Global cache instance
cache_config = CacheConfig()
cache = RedisCache(cache_config)
session_cache = SessionCache(cache)
