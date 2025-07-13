"""
Metadata Service for Arxos Platform

Provides metadata management with Redis caching for:
- Object metadata lookups
- Symbol metadata retrieval
- User metadata management
- Export metadata handling
- Cache invalidation and updates
"""

import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import structlog

from utils.cache import redis_cache, generate_metadata_cache_key

logger = structlog.get_logger(__name__)

@dataclass
class ObjectMetadata:
    """Metadata for objects in the system."""
    object_id: str
    object_type: str
    name: str
    description: Optional[str] = None
    created_at: str = None
    updated_at: str = None
    created_by: str = None
    version: str = "1.0"
    tags: List[str] = None
    properties: Dict[str, Any] = None
    relationships: List[str] = None
    location: Optional[Dict[str, Any]] = None
    status: str = "active"
    metadata_hash: Optional[str] = None

@dataclass
class SymbolMetadata:
    """Metadata for symbols."""
    symbol_id: str
    symbol_name: str
    category: str
    system: str
    version: str
    created_at: str
    updated_at: str
    author: str
    description: Optional[str] = None
    tags: List[str] = None
    properties: Dict[str, Any] = None
    usage_count: int = 0
    rating: float = 0.0
    status: str = "active"

@dataclass
class UserMetadata:
    """Metadata for users."""
    user_id: str
    username: str
    email: str
    roles: List[str]
    permissions: List[str]
    created_at: str
    last_login: Optional[str] = None
    profile: Dict[str, Any] = None
    preferences: Dict[str, Any] = None
    status: str = "active"

class MetadataService:
    """
    Metadata service with Redis caching for high-performance lookups.
    
    Features:
    - Redis caching for frequently accessed metadata
    - Automatic cache invalidation on updates
    - Structured logging for cache operations
    - Graceful fallback to database on cache miss
    - Cache statistics and performance monitoring
    """
    
    def __init__(self, cache_ttl: int = 300):
        """
        Initialize metadata service.
        
        Args:
            cache_ttl: Cache TTL in seconds for metadata
        """
        self.cache_ttl = cache_ttl
        self.cache = redis_cache
        
        logger.info("metadata_service_initialized",
                   cache_ttl=cache_ttl)
    
    async def get_object_metadata(self, object_id: str) -> Optional[ObjectMetadata]:
        """
        Get object metadata with Redis caching.
        
        Args:
            object_id: Object identifier
            
        Returns:
            Object metadata or None if not found
        """
        cache_key = generate_metadata_cache_key(object_id)
        
        try:
            # Try cache first
            cached_metadata = await self.cache.get(cache_key)
            
            if cached_metadata:
                logger.info("metadata_cache_hit",
                           object_id=object_id,
                           cache_key=cache_key)
                
                return ObjectMetadata(**cached_metadata)
            
            # Cache miss - query database
            logger.info("metadata_cache_miss",
                       object_id=object_id,
                       cache_key=cache_key)
            
            metadata = await self._query_object_metadata_from_db(object_id)
            
            if metadata:
                # Cache the result
                await self.cache.set(cache_key, asdict(metadata), ttl=self.cache_ttl)
                
                logger.info("metadata_cached",
                           object_id=object_id,
                           cache_key=cache_key,
                           ttl=self.cache_ttl)
            
            return metadata
            
        except Exception as e:
            logger.error("metadata_retrieval_failed",
                        object_id=object_id,
                        error=str(e),
                        error_type=type(e).__name__)
            
            # Fallback to database only
            return await self._query_object_metadata_from_db(object_id)
    
    async def get_symbol_metadata(self, symbol_id: str) -> Optional[SymbolMetadata]:
        """
        Get symbol metadata with Redis caching.
        
        Args:
            symbol_id: Symbol identifier
            
        Returns:
            Symbol metadata or None if not found
        """
        cache_key = f"symbol:{symbol_id}:metadata"
        
        try:
            # Try cache first
            cached_metadata = await self.cache.get(cache_key)
            
            if cached_metadata:
                logger.info("symbol_metadata_cache_hit",
                           symbol_id=symbol_id,
                           cache_key=cache_key)
                
                return SymbolMetadata(**cached_metadata)
            
            # Cache miss - query database
            logger.info("symbol_metadata_cache_miss",
                       symbol_id=symbol_id,
                       cache_key=cache_key)
            
            metadata = await self._query_symbol_metadata_from_db(symbol_id)
            
            if metadata:
                # Cache the result
                await self.cache.set(cache_key, asdict(metadata), ttl=self.cache_ttl)
                
                logger.info("symbol_metadata_cached",
                           symbol_id=symbol_id,
                           cache_key=cache_key,
                           ttl=self.cache_ttl)
            
            return metadata
            
        except Exception as e:
            logger.error("symbol_metadata_retrieval_failed",
                        symbol_id=symbol_id,
                        error=str(e),
                        error_type=type(e).__name__)
            
            # Fallback to database only
            return await self._query_symbol_metadata_from_db(symbol_id)
    
    async def get_user_metadata(self, user_id: str) -> Optional[UserMetadata]:
        """
        Get user metadata with Redis caching.
        
        Args:
            user_id: User identifier
            
        Returns:
            User metadata or None if not found
        """
        cache_key = f"user:{user_id}:metadata"
        
        try:
            # Try cache first
            cached_metadata = await self.cache.get(cache_key)
            
            if cached_metadata:
                logger.info("user_metadata_cache_hit",
                           user_id=user_id,
                           cache_key=cache_key)
                
                return UserMetadata(**cached_metadata)
            
            # Cache miss - query database
            logger.info("user_metadata_cache_miss",
                       user_id=user_id,
                       cache_key=cache_key)
            
            metadata = await self._query_user_metadata_from_db(user_id)
            
            if metadata:
                # Cache the result
                await self.cache.set(cache_key, asdict(metadata), ttl=self.cache_ttl)
                
                logger.info("user_metadata_cached",
                           user_id=user_id,
                           cache_key=cache_key,
                           ttl=self.cache_ttl)
            
            return metadata
            
        except Exception as e:
            logger.error("user_metadata_retrieval_failed",
                        user_id=user_id,
                        error=str(e),
                        error_type=type(e).__name__)
            
            # Fallback to database only
            return await self._query_user_metadata_from_db(user_id)
    
    async def update_object_metadata(self, object_id: str, metadata: ObjectMetadata) -> bool:
        """
        Update object metadata and invalidate cache.
        
        Args:
            object_id: Object identifier
            metadata: Updated metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update database
            success = await self._update_object_metadata_in_db(object_id, metadata)
            
            if success:
                # Invalidate cache
                cache_key = generate_metadata_cache_key(object_id)
                await self.cache.delete(cache_key)
                
                logger.info("object_metadata_updated",
                           object_id=object_id,
                           cache_key=cache_key)
                
                return True
            else:
                logger.warning("object_metadata_update_failed",
                             object_id=object_id)
                return False
                
        except Exception as e:
            logger.error("object_metadata_update_error",
                        object_id=object_id,
                        error=str(e),
                        error_type=type(e).__name__)
            return False
    
    async def update_symbol_metadata(self, symbol_id: str, metadata: SymbolMetadata) -> bool:
        """
        Update symbol metadata and invalidate cache.
        
        Args:
            symbol_id: Symbol identifier
            metadata: Updated metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update database
            success = await self._update_symbol_metadata_in_db(symbol_id, metadata)
            
            if success:
                # Invalidate cache
                cache_key = f"symbol:{symbol_id}:metadata"
                await self.cache.delete(cache_key)
                
                logger.info("symbol_metadata_updated",
                           symbol_id=symbol_id,
                           cache_key=cache_key)
                
                return True
            else:
                logger.warning("symbol_metadata_update_failed",
                             symbol_id=symbol_id)
                return False
                
        except Exception as e:
            logger.error("symbol_metadata_update_error",
                        symbol_id=symbol_id,
                        error=str(e),
                        error_type=type(e).__name__)
            return False
    
    async def invalidate_metadata_cache(self, object_id: str) -> bool:
        """
        Invalidate metadata cache for an object.
        
        Args:
            object_id: Object identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_key = generate_metadata_cache_key(object_id)
            success = await self.cache.delete(cache_key)
            
            if success:
                logger.info("metadata_cache_invalidated",
                           object_id=object_id,
                           cache_key=cache_key)
            else:
                logger.warning("metadata_cache_invalidation_failed",
                             object_id=object_id,
                             cache_key=cache_key)
            
            return success
            
        except Exception as e:
            logger.error("metadata_cache_invalidation_error",
                        object_id=object_id,
                        error=str(e),
                        error_type=type(e).__name__)
            return False
    
    async def invalidate_pattern_cache(self, pattern: str) -> int:
        """
        Invalidate cache for all keys matching pattern.
        
        Args:
            pattern: Redis pattern (e.g., "object:*:metadata")
            
        Returns:
            Number of keys deleted
        """
        try:
            deleted_count = await self.cache.invalidate_pattern(pattern)
            
            logger.info("pattern_cache_invalidated",
                       pattern=pattern,
                       deleted_count=deleted_count)
            
            return deleted_count
            
        except Exception as e:
            logger.error("pattern_cache_invalidation_error",
                        pattern=pattern,
                        error=str(e),
                        error_type=type(e).__name__)
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for metadata operations.
        
        Returns:
            Cache statistics
        """
        try:
            stats = self.cache.get_stats()
            
            logger.info("metadata_cache_stats",
                       **stats)
            
            return stats
            
        except Exception as e:
            logger.error("metadata_cache_stats_error",
                        error=str(e),
                        error_type=type(e).__name__)
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform metadata service health check.
        
        Returns:
            Health check results
        """
        try:
            # Check cache health
            cache_health = await self.cache.health_check()
            
            # Check database connectivity
            db_health = await self._check_database_health()
            
            health_status = {
                'service': 'metadata',
                'cache_healthy': cache_health.get('overall_healthy', False),
                'database_healthy': db_health.get('connected', False),
                'overall_healthy': cache_health.get('overall_healthy', False) and db_health.get('connected', False)
            }
            
            logger.info("metadata_service_health_check",
                       **health_status)
            
            return health_status
            
        except Exception as e:
            health_status = {
                'service': 'metadata',
                'cache_healthy': False,
                'database_healthy': False,
                'overall_healthy': False,
                'error': str(e)
            }
            
            logger.error("metadata_service_health_check_failed",
                        error=str(e),
                        error_type=type(e).__name__)
            
            return health_status
    
    # Database fallback methods (implement based on your database)
    async def _query_object_metadata_from_db(self, object_id: str) -> Optional[ObjectMetadata]:
        """Query object metadata from database."""
        # Implementation depends on your database
        # This is a placeholder implementation
        try:
            # Simulate database query
            await asyncio.sleep(0.01)  # Simulate DB latency
            
            # Return mock data for demonstration
            return ObjectMetadata(
                object_id=object_id,
                object_type="symbol",
                name=f"Object {object_id}",
                description=f"Description for object {object_id}",
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
                created_by="system",
                tags=["tag1", "tag2"],
                properties={"property1": "value1"},
                relationships=["rel1", "rel2"]
            )
        except Exception as e:
            logger.error("database_query_failed",
                        object_id=object_id,
                        error=str(e),
                        error_type=type(e).__name__)
            return None
    
    async def _query_symbol_metadata_from_db(self, symbol_id: str) -> Optional[SymbolMetadata]:
        """Query symbol metadata from database."""
        # Implementation depends on your database
        try:
            # Simulate database query
            await asyncio.sleep(0.01)  # Simulate DB latency
            
            # Return mock data for demonstration
            return SymbolMetadata(
                symbol_id=symbol_id,
                symbol_name=f"Symbol {symbol_id}",
                category="electrical",
                system="E",
                version="1.0",
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
                author="system",
                description=f"Description for symbol {symbol_id}",
                tags=["electrical", "outlet"],
                properties={"voltage": "120V", "amperage": "15A"},
                usage_count=10,
                rating=4.5
            )
        except Exception as e:
            logger.error("symbol_database_query_failed",
                        symbol_id=symbol_id,
                        error=str(e),
                        error_type=type(e).__name__)
            return None
    
    async def _query_user_metadata_from_db(self, user_id: str) -> Optional[UserMetadata]:
        """Query user metadata from database."""
        # Implementation depends on your database
        try:
            # Simulate database query
            await asyncio.sleep(0.01)  # Simulate DB latency
            
            # Return mock data for demonstration
            return UserMetadata(
                user_id=user_id,
                username=f"user_{user_id}",
                email=f"user_{user_id}@example.com",
                roles=["user"],
                permissions=["read", "write"],
                created_at=datetime.utcnow().isoformat(),
                last_login=datetime.utcnow().isoformat(),
                profile={"department": "engineering"},
                preferences={"theme": "dark"}
            )
        except Exception as e:
            logger.error("user_database_query_failed",
                        user_id=user_id,
                        error=str(e),
                        error_type=type(e).__name__)
            return None
    
    async def _update_object_metadata_in_db(self, object_id: str, metadata: ObjectMetadata) -> bool:
        """Update object metadata in database."""
        # Implementation depends on your database
        try:
            # Simulate database update
            await asyncio.sleep(0.01)  # Simulate DB latency
            return True
        except Exception as e:
            logger.error("object_database_update_failed",
                        object_id=object_id,
                        error=str(e),
                        error_type=type(e).__name__)
            return False
    
    async def _update_symbol_metadata_in_db(self, symbol_id: str, metadata: SymbolMetadata) -> bool:
        """Update symbol metadata in database."""
        # Implementation depends on your database
        try:
            # Simulate database update
            await asyncio.sleep(0.01)  # Simulate DB latency
            return True
        except Exception as e:
            logger.error("symbol_database_update_failed",
                        symbol_id=symbol_id,
                        error=str(e),
                        error_type=type(e).__name__)
            return False
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity."""
        # Implementation depends on your database
        try:
            # Simulate database health check
            await asyncio.sleep(0.01)  # Simulate DB latency
            return {"connected": True}
        except Exception as e:
            return {"connected": False, "error": str(e)}

# Global metadata service instance
metadata_service = MetadataService() 