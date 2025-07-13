"""
Redis Cache Utility for Arxos Platform

Provides centralized caching functionality with:
- Async Redis operations
- Structured logging with structlog
- Comprehensive error handling
- Configurable TTL and key naming
- Cache hit/miss tracking
- Graceful fallback mechanisms
"""

import aioredis
import json
import structlog
from typing import Any, Optional, Dict, Union
from datetime import timedelta
import asyncio
from contextlib import asynccontextmanager

logger = structlog.get_logger(__name__)

class RedisCache:
    """
    Redis cache utility with async operations and structured logging.
    
    Features:
    - Async Redis operations with connection pooling
    - Structured logging for cache hits/misses
    - Comprehensive error handling with fallbacks
    - Configurable TTL and key naming conventions
    - Cache statistics and performance tracking
    """
    
    def __init__(self, 
                 url: str = "redis://localhost:6379", 
                 default_ttl: int = 300,
                 max_connections: int = 10,
                 retry_attempts: int = 3,
                 retry_delay: float = 0.1):
        """
        Initialize Redis cache utility.
        
        Args:
            url: Redis connection URL
            default_ttl: Default TTL in seconds
            max_connections: Maximum Redis connections
            retry_attempts: Number of retry attempts on failure
            retry_delay: Delay between retries in seconds
        """
        self.url = url
        self.default_ttl = default_ttl
        self.max_connections = max_connections
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.redis: Optional[aioredis.Redis] = None
        self.connected = False
        
        # Cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0,
            'fallbacks': 0
        }
        
        logger.info("redis_cache_initialized",
                   url=url,
                   default_ttl=default_ttl,
                   max_connections=max_connections)
    
    async def connect(self) -> None:
        """Establish Redis connection with error handling."""
        if self.connected and self.redis:
            return
        
        try:
            self.redis = await aioredis.from_url(
                self.url,
                decode_responses=True,
                max_connections=self.max_connections
            )
            
            # Test connection
            await self.redis.ping()
            self.connected = True
            
            logger.info("redis_connection_established",
                       url=self.url,
                       max_connections=self.max_connections)
            
        except Exception as e:
            self.connected = False
            self.stats['errors'] += 1
            
            logger.error("redis_connection_failed",
                        url=self.url,
                        error=str(e),
                        error_type=type(e).__name__)
            raise
    
    async def _execute_with_retry(self, operation: str, *args, **kwargs) -> Any:
        """
        Execute Redis operation with retry logic and error handling.
        
        Args:
            operation: Operation name for logging
            *args: Arguments for Redis operation
            **kwargs: Keyword arguments for Redis operation
            
        Returns:
            Operation result or None on failure
        """
        for attempt in range(self.retry_attempts):
            try:
                if not self.connected:
                    await self.connect()
                
                if operation == 'get':
                    result = await self.redis.get(*args, **kwargs)
                elif operation == 'set':
                    result = await self.redis.set(*args, **kwargs)
                elif operation == 'delete':
                    result = await self.redis.delete(*args, **kwargs)
                elif operation == 'exists':
                    result = await self.redis.exists(*args, **kwargs)
                else:
                    raise ValueError(f"Unknown operation: {operation}")
                
                return result
                
            except Exception as e:
                self.stats['errors'] += 1
                
                logger.warning("redis_operation_failed",
                              operation=operation,
                              attempt=attempt + 1,
                              max_attempts=self.retry_attempts,
                              error=str(e),
                              error_type=type(e).__name__)
                
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    self.connected = False  # Force reconnection
                else:
                    logger.error("redis_operation_failed_final",
                                operation=operation,
                                error=str(e),
                                error_type=type(e).__name__)
                    return None
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache with structured logging.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        result = await self._execute_with_retry('get', key)
        
        if result is not None:
            try:
                parsed_result = json.loads(result)
                self.stats['hits'] += 1
                
                logger.debug("cache_hit",
                           key=key,
                           cache_hits=self.stats['hits'])
                
                return parsed_result
                
            except json.JSONDecodeError as e:
                logger.warning("cache_value_invalid_json",
                             key=key,
                             error=str(e))
                return None
        else:
            self.stats['misses'] += 1
            
            logger.debug("cache_miss",
                        key=key,
                        cache_misses=self.stats['misses'])
            
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache with structured logging.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            serialized_value = json.dumps(value)
            actual_ttl = ttl if ttl is not None else self.default_ttl
            
            result = await self._execute_with_retry('set', key, serialized_value, ex=actual_ttl)
            
            if result:
                self.stats['sets'] += 1
                
                logger.debug("cache_set",
                           key=key,
                           ttl=actual_ttl,
                           cache_sets=self.stats['sets'])
                
                return True
            else:
                logger.warning("cache_set_failed",
                             key=key,
                             ttl=actual_ttl)
                return False
                
        except Exception as e:
            self.stats['errors'] += 1
            
            logger.error("cache_set_error",
                        key=key,
                        error=str(e),
                        error_type=type(e).__name__)
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache with structured logging.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful, False otherwise
        """
        result = await self._execute_with_retry('delete', key)
        
        if result:
            self.stats['deletes'] += 1
            
            logger.debug("cache_delete",
                       key=key,
                       cache_deletes=self.stats['deletes'])
            
            return True
        else:
            logger.warning("cache_delete_failed",
                         key=key)
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists, False otherwise
        """
        result = await self._execute_with_retry('exists', key)
        return bool(result)
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern.
        
        Args:
            pattern: Redis pattern (e.g., "export:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            if not self.connected:
                await self.connect()
            
            keys = await self.redis.keys(pattern)
            if keys:
                deleted = await self.redis.delete(*keys)
                
                logger.info("cache_invalidate_pattern",
                           pattern=pattern,
                           keys_found=len(keys),
                           keys_deleted=deleted)
                
                return deleted
            else:
                logger.debug("cache_invalidate_pattern_no_keys",
                           pattern=pattern)
                return 0
                
        except Exception as e:
            logger.error("cache_invalidate_pattern_error",
                        pattern=pattern,
                        error=str(e),
                        error_type=type(e).__name__)
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        hit_rate = 0
        if self.stats['hits'] + self.stats['misses'] > 0:
            hit_rate = self.stats['hits'] / (self.stats['hits'] + self.stats['misses'])
        
        stats = {
            **self.stats,
            'hit_rate': hit_rate,
            'connected': self.connected
        }
        
        logger.info("cache_stats",
                   **stats)
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform cache health check.
        
        Returns:
            Health check results
        """
        try:
            if not self.connected:
                await self.connect()
            
            # Test basic operations
            test_key = "_health_check"
            test_value = {"test": "value"}
            
            # Set test value
            set_success = await self.set(test_key, test_value, ttl=10)
            
            # Get test value
            get_result = await self.get(test_key)
            get_success = get_result == test_value
            
            # Clean up
            await self.delete(test_key)
            
            health_status = {
                'connected': self.connected,
                'set_operation': set_success,
                'get_operation': get_success,
                'overall_healthy': set_success and get_success
            }
            
            logger.info("cache_health_check",
                       **health_status)
            
            return health_status
            
        except Exception as e:
            health_status = {
                'connected': False,
                'set_operation': False,
                'get_operation': False,
                'overall_healthy': False,
                'error': str(e)
            }
            
            logger.error("cache_health_check_failed",
                        error=str(e),
                        error_type=type(e).__name__)
            
            return health_status
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            self.connected = False
            
            logger.info("redis_connection_closed")

@asynccontextmanager
async def redis_cache_context():
    """
    Context manager for Redis cache operations.
    
    Usage:
        async with redis_cache_context() as cache:
            result = await cache.get("my_key")
    """
    cache = RedisCache()
    try:
        await cache.connect()
        yield cache
    finally:
        await cache.close()

# Global cache instance
redis_cache = RedisCache()

# Cache key generators
def generate_export_cache_key(export_id: str) -> str:
    """Generate cache key for export results."""
    return f"export:{export_id}:result"

def generate_metadata_cache_key(object_id: str) -> str:
    """Generate cache key for object metadata."""
    return f"object:{object_id}:metadata"

def generate_user_cache_key(user_id: str) -> str:
    """Generate cache key for user data."""
    return f"user:{user_id}:data"

def generate_symbol_cache_key(symbol_id: str) -> str:
    """Generate cache key for symbol data."""
    return f"symbol:{symbol_id}:data" 