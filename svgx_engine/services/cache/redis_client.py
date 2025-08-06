"""
SVGX Engine - Redis Cache Client

Provides Redis caching functionality for SVGX Engine with proper
error handling, connection pooling, and performance monitoring.
"""

import redis
import json
import logging
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
import pickle

from svgx_engine.utils.errors import CacheError

logger = logging.getLogger(__name__)

# Global cache client instance
_cache_client = None


class RedisCacheClient:
    """Redis cache client for SVGX Engine."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        max_connections: int = 10,
    ):
        """Initialize Redis cache client."""
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.max_connections = max_connections
        self.redis_client = None
        self._connect()

    def _connect(self):
        """Establish Redis connection."""
        try:
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                max_connections=self.max_connections,
                decode_responses=True,
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise CacheError(f"Redis connection failed: {e}") from e

    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set a value in cache."""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            elif not isinstance(value, (str, int, float, bool)):
                value = pickle.dumps(value)

            result = self.redis_client.set(key, value, ex=expire)
            logger.debug(f"Set cache key: {key}")
            return result
        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {e}")
            raise CacheError(f"Cache set failed: {e}") from e

    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None

            # Try to parse as JSON first
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Try to unpickle
                try:
                    return pickle.loads(value.encode())
                except:
                    return value
        except Exception as e:
            logger.error(f"Failed to get cache key {key}: {e}")
            raise CacheError(f"Cache get failed: {e}") from e

    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        try:
            result = self.redis_client.delete(key)
            logger.debug(f"Deleted cache key: {key}")
            return result > 0
        except Exception as e:
            logger.error(f"Failed to delete cache key {key}: {e}")
            raise CacheError(f"Cache delete failed: {e}") from e

    def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Failed to check cache key {key}: {e}")
            raise CacheError(f"Cache exists check failed: {e}") from e

    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for a key."""
        try:
            return bool(self.redis_client.expire(key, seconds))
        except Exception as e:
            logger.error(f"Failed to set expiration for cache key {key}: {e}")
            raise CacheError(f"Cache expire failed: {e}") from e

    def close(self):
        """Close Redis connection."""
        if self.redis_client:
            self.redis_client.close()
            logger.info("Redis connection closed")


def get_cache_client() -> RedisCacheClient:
    """Get the global cache client instance."""
    global _cache_client
    if _cache_client is None:
        _cache_client = RedisCacheClient()
    return _cache_client


def initialize_cache(
    host: str = "localhost",
    port: int = 6379,
    db: int = 0,
    password: Optional[str] = None,
) -> RedisCacheClient:
    """Initialize the global cache client."""
    global _cache_client
    _cache_client = RedisCacheClient(host, port, db, password)
    return _cache_client


def close_cache():
    """Close the global cache client."""
    global _cache_client
    if _cache_client:
        _cache_client.close()
        _cache_client = None
