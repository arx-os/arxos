#!/usr/bin/env python3
"""
Redis Manager for MCP Caching

This module provides advanced caching capabilities using Redis for
performance optimization of validation results, building models,
and frequently accessed data.
"""

import redis
import json
import pickle
import logging
from typing import Optional, Any, Dict, List
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class CacheType(str, Enum):
    """Cache type enumeration"""

    VALIDATION_RESULT = "validation_result"
    BUILDING_MODEL = "building_model"
    MCP_FILE = "mcp_file"
    JURISDICTION_MATCH = "jurisdiction_match"
    COMPLIANCE_SCORE = "compliance_score"
    PERFORMANCE_METRIC = "performance_metric"


@dataclass
class CacheEntry:
    """Cache entry structure"""

    key: str
    value: Any
    cache_type: CacheType
    created_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class RedisManager:
    """Manages Redis caching for performance optimization"""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        default_ttl: int = 3600,
        max_connections: int = 10,
    ):
        """
        Initialize Redis manager

        Args:
            redis_url: Redis connection URL
            default_ttl: Default cache TTL in seconds
            max_connections: Maximum Redis connections
        """
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.max_connections = max_connections

        # Initialize Redis connection pool
        self.redis_client = redis.from_url(
            redis_url,
            max_connections=max_connections,
            decode_responses=False,  # Keep as bytes for pickle
        )

        # Test connection
        try:
            self.redis_client.ping()
            logger.info(f"Redis connection established: {redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def get_cached_validation(self, building_id: str) -> Optional[dict]:
        """Get cached validation results for a building"""
        try:
            key = f"validation:{building_id}"
            cached_data = self.redis_client.get(key)

            if cached_data:
                entry = pickle.loads(cached_data)
                if isinstance(entry, CacheEntry):
                    # Check if expired
                    if entry.expires_at and datetime.now() > entry.expires_at:
                        await self.invalidate_cache(building_id)
                        return None
                    return entry.value
                else:
                    # Legacy format
                    return entry

            return None

        except Exception as e:
            logger.error(f"Error getting cached validation for {building_id}: {e}")
            return None

    async def cache_validation(
        self, building_id: str, validation_data: dict, ttl: Optional[int] = None
    ) -> bool:
        """Cache validation results for a building"""
        try:
            key = f"validation:{building_id}"
            ttl = ttl or self.default_ttl

            entry = CacheEntry(
                key=key,
                value=validation_data,
                cache_type=CacheType.VALIDATION_RESULT,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(seconds=ttl),
                metadata={
                    "building_id": building_id,
                    "validation_timestamp": datetime.now().isoformat(),
                    "total_violations": len(validation_data.get("violations", [])),
                    "compliance_score": validation_data.get(
                        "overall_compliance_score", 0
                    ),
                },
            )

            self.redis_client.setex(key, ttl, pickle.dumps(entry))

            logger.info(
                f"Cached validation results for building {building_id} (TTL: {ttl}s)"
            )
            return True

        except Exception as e:
            logger.error(f"Error caching validation for {building_id}: {e}")
            return False

    async def cache_building_model(
        self, building_id: str, building_model: dict, ttl: Optional[int] = None
    ) -> bool:
        """Cache building model data"""
        try:
            key = f"building_model:{building_id}"
            ttl = ttl or self.default_ttl

            entry = CacheEntry(
                key=key,
                value=building_model,
                cache_type=CacheType.BUILDING_MODEL,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(seconds=ttl),
                metadata={
                    "building_id": building_id,
                    "object_count": len(building_model.get("objects", [])),
                    "model_size": len(str(building_model)),
                },
            )

            self.redis_client.setex(key, ttl, pickle.dumps(entry))

            logger.info(f"Cached building model for {building_id}")
            return True

        except Exception as e:
            logger.error(f"Error caching building model for {building_id}: {e}")
            return False

    async def get_cached_building_model(self, building_id: str) -> Optional[dict]:
        """Get cached building model"""
        try:
            key = f"building_model:{building_id}"
            cached_data = self.redis_client.get(key)

            if cached_data:
                entry = pickle.loads(cached_data)
                if isinstance(entry, CacheEntry):
                    if entry.expires_at and datetime.now() > entry.expires_at:
                        await self.invalidate_cache(building_id, "building_model")
                        return None
                    return entry.value
                else:
                    return entry

            return None

        except Exception as e:
            logger.error(f"Error getting cached building model for {building_id}: {e}")
            return None

    async def cache_mcp_file(
        self, mcp_id: str, mcp_data: dict, ttl: Optional[int] = None
    ) -> bool:
        """Cache MCP file data"""
        try:
            key = f"mcp_file:{mcp_id}"
            ttl = ttl or (self.default_ttl * 24)  # Longer TTL for MCP files

            entry = CacheEntry(
                key=key,
                value=mcp_data,
                cache_type=CacheType.MCP_FILE,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(seconds=ttl),
                metadata={
                    "mcp_id": mcp_id,
                    "rule_count": len(mcp_data.get("rules", [])),
                    "file_size": len(str(mcp_data)),
                },
            )

            self.redis_client.setex(key, ttl, pickle.dumps(entry))

            logger.info(f"Cached MCP file {mcp_id}")
            return True

        except Exception as e:
            logger.error(f"Error caching MCP file {mcp_id}: {e}")
            return False

    async def get_cached_mcp_file(self, mcp_id: str) -> Optional[dict]:
        """Get cached MCP file"""
        try:
            key = f"mcp_file:{mcp_id}"
            cached_data = self.redis_client.get(key)

            if cached_data:
                entry = pickle.loads(cached_data)
                if isinstance(entry, CacheEntry):
                    if entry.expires_at and datetime.now() > entry.expires_at:
                        await self.invalidate_cache(mcp_id, "mcp_file")
                        return None
                    return entry.value
                else:
                    return entry

            return None

        except Exception as e:
            logger.error(f"Error getting cached MCP file {mcp_id}: {e}")
            return None

    async def cache_jurisdiction_match(
        self, building_id: str, jurisdiction_data: dict, ttl: Optional[int] = None
    ) -> bool:
        """Cache jurisdiction matching results"""
        try:
            key = f"jurisdiction:{building_id}"
            ttl = ttl or (self.default_ttl * 2)  # Longer TTL for jurisdiction data

            entry = CacheEntry(
                key=key,
                value=jurisdiction_data,
                cache_type=CacheType.JURISDICTION_MATCH,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(seconds=ttl),
                metadata={
                    "building_id": building_id,
                    "applicable_codes": len(
                        jurisdiction_data.get("applicable_codes", [])
                    ),
                    "jurisdiction_level": jurisdiction_data.get(
                        "jurisdiction_level", "unknown"
                    ),
                },
            )

            self.redis_client.setex(key, ttl, pickle.dumps(entry))

            logger.info(f"Cached jurisdiction match for building {building_id}")
            return True

        except Exception as e:
            logger.error(f"Error caching jurisdiction match for {building_id}: {e}")
            return False

    async def get_cached_jurisdiction_match(self, building_id: str) -> Optional[dict]:
        """Get cached jurisdiction matching results"""
        try:
            key = f"jurisdiction:{building_id}"
            cached_data = self.redis_client.get(key)

            if cached_data:
                entry = pickle.loads(cached_data)
                if isinstance(entry, CacheEntry):
                    if entry.expires_at and datetime.now() > entry.expires_at:
                        await self.invalidate_cache(building_id, "jurisdiction")
                        return None
                    return entry.value
                else:
                    return entry

            return None

        except Exception as e:
            logger.error(
                f"Error getting cached jurisdiction match for {building_id}: {e}"
            )
            return None

    async def invalidate_cache(
        self, identifier: str, cache_type: str = "validation"
    ) -> bool:
        """Invalidate cache entries"""
        try:
            if cache_type == "validation":
                key = f"validation:{identifier}"
            elif cache_type == "building_model":
                key = f"building_model:{identifier}"
            elif cache_type == "mcp_file":
                key = f"mcp_file:{identifier}"
            elif cache_type == "jurisdiction":
                key = f"jurisdiction:{identifier}"
            else:
                key = f"{cache_type}:{identifier}"

            result = self.redis_client.delete(key)
            logger.info(f"Invalidated cache for {identifier} ({cache_type})")
            return result > 0

        except Exception as e:
            logger.error(f"Error invalidating cache for {identifier}: {e}")
            return False

    async def invalidate_building_cache(self, building_id: str) -> bool:
        """Invalidate all cache entries for a building"""
        try:
            keys_to_delete = []

            # Find all keys related to this building
            pattern = f"*:{building_id}"
            for key in self.redis_client.scan_iter(match=pattern):
                keys_to_delete.append(key)

            if keys_to_delete:
                result = self.redis_client.delete(*keys_to_delete)
                logger.info(
                    f"Invalidated {result} cache entries for building {building_id}"
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Error invalidating building cache for {building_id}: {e}")
            return False

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get Redis performance metrics"""
        try:
            info = self.redis_client.info()

            # Calculate cache hit ratio
            keyspace_hits = info.get("keyspace_hits", 0)
            keyspace_misses = info.get("keyspace_misses", 0)
            total_requests = keyspace_hits + keyspace_misses
            hit_ratio = (
                (keyspace_hits / total_requests * 100) if total_requests > 0 else 0
            )

            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": keyspace_hits,
                "keyspace_misses": keyspace_misses,
                "hit_ratio_percent": round(hit_ratio, 2),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace": info.get("db0", {}),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
                "uptime_days": info.get("uptime_in_days", 0),
            }

        except Exception as e:
            logger.error(f"Error getting Redis performance metrics: {e}")
            return {"error": str(e)}

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            stats = {
                "total_keys": 0,
                "cache_types": {},
                "memory_usage": 0,
                "oldest_entry": None,
                "newest_entry": None,
            }

            # Scan all keys and analyze
            for key in self.redis_client.scan_iter():
                try:
                    cached_data = self.redis_client.get(key)
                    if cached_data:
                        entry = pickle.loads(cached_data)
                        if isinstance(entry, CacheEntry):
                            cache_type = entry.cache_type.value
                            if cache_type not in stats["cache_types"]:
                                stats["cache_types"][cache_type] = 0
                            stats["cache_types"][cache_type] += 1

                            # Track oldest/newest entries
                            if (
                                not stats["oldest_entry"]
                                or entry.created_at < stats["oldest_entry"]
                            ):
                                stats["oldest_entry"] = entry.created_at
                            if (
                                not stats["newest_entry"]
                                or entry.created_at > stats["newest_entry"]
                            ):
                                stats["newest_entry"] = entry.created_at

                        stats["total_keys"] += 1
                        stats["memory_usage"] += len(cached_data)

                except Exception as e:
                    logger.warning(f"Error analyzing cache key {key}: {e}")

            # Convert timestamps to ISO format
            if stats["oldest_entry"]:
                stats["oldest_entry"] = stats["oldest_entry"].isoformat()
            if stats["newest_entry"]:
                stats["newest_entry"] = stats["newest_entry"].isoformat()

            return stats

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}

    async def clear_all_cache(self) -> bool:
        """Clear all cache entries"""
        try:
            result = self.redis_client.flushdb()
            logger.info("Cleared all cache entries")
            return True

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    async def warm_cache(self, building_ids: List[str]) -> Dict[str, bool]:
        """Warm cache with frequently accessed data"""
        results = {}

        for building_id in building_ids:
            try:
                # Try to get and cache building model
                # This would typically involve loading from database
                logger.info(f"Warming cache for building {building_id}")
                results[building_id] = True

            except Exception as e:
                logger.error(f"Error warming cache for building {building_id}: {e}")
                results[building_id] = False

        return results

    async def health_check(self) -> Dict[str, Any]:
        """Perform Redis health check"""
        try:
            # Test basic operations
            test_key = "health_check_test"
            test_value = {"timestamp": datetime.now().isoformat()}

            # Set test value
            self.redis_client.setex(test_key, 10, pickle.dumps(test_value))

            # Get test value
            retrieved = self.redis_client.get(test_key)
            if retrieved:
                retrieved_value = pickle.loads(retrieved)
                success = retrieved_value == test_value
            else:
                success = False

            # Clean up
            self.redis_client.delete(test_key)

            return {
                "status": "healthy" if success else "unhealthy",
                "connection": "connected",
                "read_write": success,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }


# Global Redis manager instance
redis_manager = RedisManager()
