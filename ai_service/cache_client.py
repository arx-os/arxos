"""
PostgreSQL Cache Client for AI Service
Connects to ARXOS core cache for result caching
"""

import os
import json
import hashlib
import logging
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
import asyncpg
import asyncio

logger = logging.getLogger(__name__)

class CacheClient:
    """
    PostgreSQL cache client for AI service
    Caches detection results to avoid reprocessing
    """
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.enabled = os.getenv("ENABLE_CACHE", "true").lower() == "true"
        self.default_ttl = int(os.getenv("CACHE_TTL_SECONDS", "300"))  # 5 minutes
        
    async def connect(self):
        """Connect to PostgreSQL cache database"""
        if not self.enabled:
            logger.info("Cache disabled")
            return
            
        try:
            # Get database connection from environment
            db_url = os.getenv(
                "DATABASE_URL",
                "postgresql://arxos:arxos_dev@localhost:5432/arxos"
            )
            
            self.pool = await asyncpg.create_pool(
                db_url,
                min_size=1,
                max_size=5,
                command_timeout=10
            )
            
            logger.info("Connected to PostgreSQL cache")
            
        except Exception as e:
            logger.error(f"Cache connection failed: {e}")
            self.enabled = False
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
    
    def _generate_key(self, prefix: str, data: Any) -> str:
        """Generate cache key from data"""
        # Create hash of input data
        if isinstance(data, bytes):
            hash_input = data
        else:
            hash_input = json.dumps(data, sort_keys=True).encode()
        
        hash_digest = hashlib.sha256(hash_input).hexdigest()[:16]
        return f"ai:{prefix}:{hash_digest}"
    
    async def get_detection(
        self, 
        image_data: bytes, 
        model: str = "yolo",
        threshold: float = 0.5
    ) -> Optional[Dict]:
        """
        Get cached detection results
        """
        if not self.enabled or not self.pool:
            return None
        
        # Generate cache key
        cache_data = {
            "model": model,
            "threshold": threshold,
            "image_hash": hashlib.md5(image_data).hexdigest()
        }
        key = self._generate_key("detect", cache_data)
        
        try:
            async with self.pool.acquire() as conn:
                # Check cache
                row = await conn.fetchrow(
                    """
                    SELECT cache_value 
                    FROM cache_entries 
                    WHERE cache_key = $1 
                    AND expires_at > CURRENT_TIMESTAMP
                    """,
                    key
                )
                
                if row:
                    # Update access count
                    await conn.execute(
                        """
                        UPDATE cache_entries 
                        SET access_count = access_count + 1,
                            last_accessed_at = CURRENT_TIMESTAMP
                        WHERE cache_key = $1
                        """,
                        key
                    )
                    
                    logger.debug(f"Cache hit: {key}")
                    return json.loads(row['cache_value'])
                
        except Exception as e:
            logger.error(f"Cache get failed: {e}")
        
        return None
    
    async def set_detection(
        self,
        image_data: bytes,
        results: Dict,
        model: str = "yolo",
        threshold: float = 0.5,
        ttl_seconds: Optional[int] = None
    ):
        """
        Cache detection results
        """
        if not self.enabled or not self.pool:
            return
        
        # Generate cache key
        cache_data = {
            "model": model,
            "threshold": threshold,
            "image_hash": hashlib.md5(image_data).hexdigest()
        }
        key = self._generate_key("detect", cache_data)
        
        ttl = ttl_seconds or self.default_ttl
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        
        try:
            async with self.pool.acquire() as conn:
                # Upsert cache entry
                await conn.execute(
                    """
                    INSERT INTO cache_entries (
                        cache_key, cache_value, cache_type, 
                        expires_at, created_at, updated_at,
                        last_accessed_at, access_count
                    ) VALUES ($1, $2, 'ai_detection', $3, $4, $4, $4, 1)
                    ON CONFLICT (cache_key) DO UPDATE SET
                        cache_value = $2,
                        expires_at = $3,
                        updated_at = $4,
                        last_accessed_at = $4,
                        access_count = cache_entries.access_count + 1
                    """,
                    key,
                    json.dumps(results),
                    expires_at,
                    datetime.utcnow()
                )
                
                logger.debug(f"Cached: {key} (TTL: {ttl}s)")
                
        except Exception as e:
            logger.error(f"Cache set failed: {e}")
    
    async def get_lidar_processing(
        self,
        point_cloud_hash: str,
        processing_params: Dict
    ) -> Optional[Dict]:
        """
        Get cached LiDAR processing results
        """
        if not self.enabled or not self.pool:
            return None
        
        cache_data = {
            "cloud_hash": point_cloud_hash,
            "params": processing_params
        }
        key = self._generate_key("lidar", cache_data)
        
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT cache_value 
                    FROM cache_entries 
                    WHERE cache_key = $1 
                    AND expires_at > CURRENT_TIMESTAMP
                    """,
                    key
                )
                
                if row:
                    logger.debug(f"LiDAR cache hit: {key}")
                    return json.loads(row['cache_value'])
                    
        except Exception as e:
            logger.error(f"LiDAR cache get failed: {e}")
        
        return None
    
    async def set_lidar_processing(
        self,
        point_cloud_hash: str,
        processing_params: Dict,
        results: Dict,
        ttl_seconds: Optional[int] = None
    ):
        """
        Cache LiDAR processing results
        """
        if not self.enabled or not self.pool:
            return
        
        cache_data = {
            "cloud_hash": point_cloud_hash,
            "params": processing_params
        }
        key = self._generate_key("lidar", cache_data)
        
        ttl = ttl_seconds or (self.default_ttl * 2)  # Longer TTL for expensive operations
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO cache_entries (
                        cache_key, cache_value, cache_type,
                        expires_at, created_at, updated_at,
                        last_accessed_at, access_count
                    ) VALUES ($1, $2, 'ai_lidar', $3, $4, $4, $4, 1)
                    ON CONFLICT (cache_key) DO UPDATE SET
                        cache_value = $2,
                        expires_at = $3,
                        updated_at = $4,
                        last_accessed_at = $4,
                        access_count = cache_entries.access_count + 1
                    """,
                    key,
                    json.dumps(results),
                    expires_at,
                    datetime.utcnow()
                )
                
                logger.debug(f"Cached LiDAR: {key} (TTL: {ttl}s)")
                
        except Exception as e:
            logger.error(f"LiDAR cache set failed: {e}")
    
    async def invalidate_pattern(self, pattern: str):
        """
        Invalidate cache entries matching pattern
        """
        if not self.enabled or not self.pool:
            return
        
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(
                    """
                    DELETE FROM cache_entries
                    WHERE cache_key LIKE $1
                    """,
                    f"ai:{pattern}%"
                )
                
                count = int(result.split()[-1])
                logger.info(f"Invalidated {count} cache entries matching: {pattern}")
                
        except Exception as e:
            logger.error(f"Pattern invalidation failed: {e}")


# Global cache instance
_cache_client: Optional[CacheClient] = None

async def get_cache() -> CacheClient:
    """Get or create cache client singleton"""
    global _cache_client
    
    if _cache_client is None:
        _cache_client = CacheClient()
        await _cache_client.connect()
    
    return _cache_client

async def close_cache():
    """Close cache connection"""
    global _cache_client
    
    if _cache_client:
        await _cache_client.close()
        _cache_client = None