"""
SVGX Engine - Metadata Service

Provides metadata management with Redis caching for SVGX Engine:
- SVGX object metadata lookups
- SVGX symbol metadata retrieval
- User metadata management
- Export metadata handling
- Cache invalidation and updates
- SVGX-specific metadata optimizations
"""

import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import structlog

try:
    from svgx_engine.utils.errors import MetadataError, CacheError, DatabaseError
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.errors import MetadataError, CacheError, DatabaseError

from svgx_engine.models.svgx import SVGXDocument, SVGXElement
from svgx_engine.models.bim import BIMElement, BIMSystem, BIMSpace

logger = structlog.get_logger(__name__)


@dataclass
class SVGXObjectMetadata:
    """Metadata for SVGX objects in the system."""
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
    svgx_namespace: str = "http://svgx.engine/metadata"


@dataclass
class SVGXSymbolMetadata:
    """Metadata for SVGX symbols."""
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
    svgx_optimized: bool = True


@dataclass
class SVGXUserMetadata:
    """Metadata for SVGX users."""
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
    svgx_access_level: str = "standard"


@dataclass
class SVGXExportMetadata:
    """Metadata for SVGX export operations."""
    export_id: str
    document_id: str
    export_format: str
    export_version: str
    created_at: str
    created_by: str
    file_size: int
    compression_ratio: float
    svgx_optimizations: List[str] = None
    metadata_embedded: bool = True


class SVGXMetadataService:
    """
    SVGX Engine Metadata service with Redis caching for high-performance lookups.
    
    Features:
    - Redis caching for frequently accessed SVGX metadata
    - Automatic cache invalidation on updates
    - Structured logging for cache operations
    - Graceful fallback to database on cache miss
    - Cache statistics and performance monitoring
    - SVGX-specific metadata optimizations
    """
    
    def __init__(self, cache_ttl: int = 300):
        """
        Initialize SVGX metadata service.
        
        Args:
            cache_ttl: Cache TTL in seconds for metadata
        """
        self.cache_ttl = cache_ttl
        
        # Initialize cache client
        try:
            from svgx_engine.advanced_caching import AdvancedCachingService
            self.cache = AdvancedCachingService()
        except ImportError:
            # Fallback if caching service not available
            self.cache = None
        
        logger.info("svgx_metadata_service_initialized",
                   cache_ttl=cache_ttl)
    
    async def get_svgx_object_metadata(self, object_id: str) -> Optional[SVGXObjectMetadata]:
        """
        Get SVGX object metadata with Redis caching.
        
        Args:
            object_id: SVGX object identifier
            
        Returns:
            SVGX object metadata or None if not found
        """
        cache_key = f"svgx:object:{object_id}:metadata"
        
        try:
            # Try cache first
            if self.cache:
                cached_metadata = await self.cache.get(cache_key)
                
                if cached_metadata:
                    logger.info("svgx_metadata_cache_hit",
                               object_id=object_id,
                               cache_key=cache_key)
                    
                    return SVGXObjectMetadata(**cached_metadata)
            
            # Cache miss - query database
            logger.info("svgx_metadata_cache_miss",
                       object_id=object_id,
                       cache_key=cache_key)
            
            metadata = await self._query_svgx_object_metadata_from_db(object_id)
            
            if metadata and self.cache:
                # Cache the result
                await self.cache.set(cache_key, asdict(metadata), ttl=self.cache_ttl)
                
                logger.info("svgx_metadata_cached",
                           object_id=object_id,
                           cache_key=cache_key,
                           ttl=self.cache_ttl)
            
            return metadata
            
        except Exception as e:
            logger.error("svgx_metadata_retrieval_failed",
                        object_id=object_id,
                        error=str(e),
                        error_type=type(e).__name__)
            
            # Fallback to database only
            return await self._query_svgx_object_metadata_from_db(object_id)
    
    async def get_svgx_symbol_metadata(self, symbol_id: str) -> Optional[SVGXSymbolMetadata]:
        """
        Get SVGX symbol metadata with Redis caching.
        
        Args:
            symbol_id: SVGX symbol identifier
            
        Returns:
            SVGX symbol metadata or None if not found
        """
        cache_key = f"svgx:symbol:{symbol_id}:metadata"
        
        try:
            # Try cache first
            if self.cache:
                cached_metadata = await self.cache.get(cache_key)
                
                if cached_metadata:
                    logger.info("svgx_symbol_metadata_cache_hit",
                               symbol_id=symbol_id,
                               cache_key=cache_key)
                    
                    return SVGXSymbolMetadata(**cached_metadata)
            
            # Cache miss - query database
            logger.info("svgx_symbol_metadata_cache_miss",
                       symbol_id=symbol_id,
                       cache_key=cache_key)
            
            metadata = await self._query_svgx_symbol_metadata_from_db(symbol_id)
            
            if metadata and self.cache:
                # Cache the result
                await self.cache.set(cache_key, asdict(metadata), ttl=self.cache_ttl)
                
                logger.info("svgx_symbol_metadata_cached",
                           symbol_id=symbol_id,
                           cache_key=cache_key,
                           ttl=self.cache_ttl)
            
            return metadata
            
        except Exception as e:
            logger.error("svgx_symbol_metadata_retrieval_failed",
                        symbol_id=symbol_id,
                        error=str(e),
                        error_type=type(e).__name__)
            
            # Fallback to database only
            return await self._query_svgx_symbol_metadata_from_db(symbol_id)
    
    async def get_svgx_user_metadata(self, user_id: str) -> Optional[SVGXUserMetadata]:
        """
        Get SVGX user metadata with Redis caching.
        
        Args:
            user_id: SVGX user identifier
            
        Returns:
            SVGX user metadata or None if not found
        """
        cache_key = f"svgx:user:{user_id}:metadata"
        
        try:
            # Try cache first
            if self.cache:
                cached_metadata = await self.cache.get(cache_key)
                
                if cached_metadata:
                    logger.info("svgx_user_metadata_cache_hit",
                               user_id=user_id,
                               cache_key=cache_key)
                    
                    return SVGXUserMetadata(**cached_metadata)
            
            # Cache miss - query database
            logger.info("svgx_user_metadata_cache_miss",
                       user_id=user_id,
                       cache_key=cache_key)
            
            metadata = await self._query_svgx_user_metadata_from_db(user_id)
            
            if metadata and self.cache:
                # Cache the result
                await self.cache.set(cache_key, asdict(metadata), ttl=self.cache_ttl)
                
                logger.info("svgx_user_metadata_cached",
                           user_id=user_id,
                           cache_key=cache_key,
                           ttl=self.cache_ttl)
            
            return metadata
            
        except Exception as e:
            logger.error("svgx_user_metadata_retrieval_failed",
                        user_id=user_id,
                        error=str(e),
                        error_type=type(e).__name__)
            
            # Fallback to database only
            return await self._query_svgx_user_metadata_from_db(user_id)
    
    async def update_svgx_object_metadata(self, object_id: str, metadata: SVGXObjectMetadata) -> bool:
        """
        Update SVGX object metadata and invalidate cache.
        
        Args:
            object_id: SVGX object identifier
            metadata: Updated metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update database
            success = await self._update_svgx_object_metadata_in_db(object_id, metadata)
            
            if success:
                # Invalidate cache
                cache_key = f"svgx:object:{object_id}:metadata"
                if self.cache:
                    await self.cache.delete(cache_key)
                
                logger.info("svgx_object_metadata_updated",
                           object_id=object_id,
                           cache_invalidated=True)
            
            return success
            
        except Exception as e:
            logger.error("svgx_object_metadata_update_failed",
                        object_id=object_id,
                        error=str(e),
                        error_type=type(e).__name__)
            return False
    
    async def update_svgx_symbol_metadata(self, symbol_id: str, metadata: SVGXSymbolMetadata) -> bool:
        """
        Update SVGX symbol metadata and invalidate cache.
        
        Args:
            symbol_id: SVGX symbol identifier
            metadata: Updated metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update database
            success = await self._update_svgx_symbol_metadata_in_db(symbol_id, metadata)
            
            if success:
                # Invalidate cache
                cache_key = f"svgx:symbol:{symbol_id}:metadata"
                if self.cache:
                    await self.cache.delete(cache_key)
                
                logger.info("svgx_symbol_metadata_updated",
                           symbol_id=symbol_id,
                           cache_invalidated=True)
            
            return success
            
        except Exception as e:
            logger.error("svgx_symbol_metadata_update_failed",
                        symbol_id=symbol_id,
                        error=str(e),
                        error_type=type(e).__name__)
            return False
    
    async def invalidate_svgx_metadata_cache(self, object_id: str) -> bool:
        """
        Invalidate SVGX metadata cache for specific object.
        
        Args:
            object_id: SVGX object identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.cache:
                cache_key = f"svgx:object:{object_id}:metadata"
                await self.cache.delete(cache_key)
                
                logger.info("svgx_metadata_cache_invalidated",
                           object_id=object_id,
                           cache_key=cache_key)
                return True
            return False
            
        except Exception as e:
            logger.error("svgx_metadata_cache_invalidation_failed",
                        object_id=object_id,
                        error=str(e),
                        error_type=type(e).__name__)
            return False
    
    async def invalidate_svgx_pattern_cache(self, pattern: str) -> int:
        """
        Invalidate SVGX metadata cache for pattern matching.
        
        Args:
            pattern: Cache key pattern to match
            
        Returns:
            Number of cache entries invalidated
        """
        try:
            if self.cache:
                # This would require pattern-based cache invalidation
                # Implementation depends on cache backend capabilities
                invalidated_count = await self.cache.delete_pattern(f"svgx:*{pattern}*")
                
                logger.info("svgx_pattern_cache_invalidated",
                           pattern=pattern,
                           invalidated_count=invalidated_count)
                return invalidated_count
            return 0
            
        except Exception as e:
            logger.error("svgx_pattern_cache_invalidation_failed",
                        pattern=pattern,
                        error=str(e),
                        error_type=type(e).__name__)
            return 0
    
    async def get_svgx_cache_stats(self) -> Dict[str, Any]:
        """
        Get SVGX metadata cache statistics.
        
        Returns:
            Cache statistics dictionary
        """
        try:
            if self.cache:
                stats = await self.cache.get_stats()
                return {
                    "cache_enabled": True,
                    "cache_stats": stats,
                    "cache_ttl": self.cache_ttl
                }
            else:
                return {
                    "cache_enabled": False,
                    "cache_stats": {},
                    "cache_ttl": self.cache_ttl
                }
                
        except Exception as e:
            logger.error("svgx_cache_stats_retrieval_failed",
                        error=str(e),
                        error_type=type(e).__name__)
            return {
                "cache_enabled": False,
                "cache_stats": {},
                "cache_ttl": self.cache_ttl,
                "error": str(e)
            }
    
    async def svgx_health_check(self) -> Dict[str, Any]:
        """
        Perform SVGX metadata service health check.
        
        Returns:
            Health check results
        """
        try:
            health_results = {
                "service": "svgx_metadata_service",
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "cache_enabled": self.cache is not None,
                "cache_ttl": self.cache_ttl
            }
            
            # Check database connectivity
            db_health = await self._check_svgx_database_health()
            health_results["database"] = db_health
            
            # Check cache connectivity if available
            if self.cache:
                cache_health = await self.cache.health_check()
                health_results["cache"] = cache_health
            
            logger.info("svgx_metadata_service_health_check",
                       health_results=health_results)
            
            return health_results
            
        except Exception as e:
            logger.error("svgx_metadata_service_health_check_failed",
                        error=str(e),
                        error_type=type(e).__name__)
            
            return {
                "service": "svgx_metadata_service",
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def _query_svgx_object_metadata_from_db(self, object_id: str) -> Optional[SVGXObjectMetadata]:
        """Query SVGX object metadata from database."""
        # Implementation would query database for SVGX object metadata
        # This is a placeholder implementation
        try:
            # Simulate database query
            await asyncio.sleep(0.01)  # Simulate DB latency
            
            return SVGXObjectMetadata(
                object_id=object_id,
                object_type="svgx_element",
                name=f"SVGX Object {object_id}",
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                created_by="system",
                tags=["svgx", "element"],
                properties={"svgx_optimized": True},
                relationships=[],
                status="active"
            )
        except Exception as e:
            logger.error("svgx_object_metadata_db_query_failed",
                        object_id=object_id,
                        error=str(e))
            return None
    
    async def _query_svgx_symbol_metadata_from_db(self, symbol_id: str) -> Optional[SVGXSymbolMetadata]:
        """Query SVGX symbol metadata from database."""
        # Implementation would query database for SVGX symbol metadata
        # This is a placeholder implementation
        try:
            # Simulate database query
            await asyncio.sleep(0.01)  # Simulate DB latency
            
            return SVGXSymbolMetadata(
                symbol_id=symbol_id,
                symbol_name=f"SVGX Symbol {symbol_id}",
                category="electrical",
                system="svgx",
                version="1.0",
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                author="system",
                tags=["svgx", "symbol"],
                properties={"svgx_optimized": True},
                usage_count=0,
                rating=0.0,
                status="active",
                svgx_optimized=True
            )
        except Exception as e:
            logger.error("svgx_symbol_metadata_db_query_failed",
                        symbol_id=symbol_id,
                        error=str(e))
            return None
    
    async def _query_svgx_user_metadata_from_db(self, user_id: str) -> Optional[SVGXUserMetadata]:
        """Query SVGX user metadata from database."""
        # Implementation would query database for SVGX user metadata
        # This is a placeholder implementation
        try:
            # Simulate database query
            await asyncio.sleep(0.01)  # Simulate DB latency
            
            return SVGXUserMetadata(
                user_id=user_id,
                username=f"user_{user_id}",
                email=f"user_{user_id}@svgx.engine",
                roles=["user"],
                permissions=["read", "write"],
                created_at=datetime.now().isoformat(),
                profile={},
                preferences={"svgx_theme": "default"},
                status="active",
                svgx_access_level="standard"
            )
        except Exception as e:
            logger.error("svgx_user_metadata_db_query_failed",
                        user_id=user_id,
                        error=str(e))
            return None
    
    async def _update_svgx_object_metadata_in_db(self, object_id: str, metadata: SVGXObjectMetadata) -> bool:
        """Update SVGX object metadata in database."""
        # Implementation would update database for SVGX object metadata
        # This is a placeholder implementation
        try:
            # Simulate database update
            await asyncio.sleep(0.01)  # Simulate DB latency
            return True
        except Exception as e:
            logger.error("svgx_object_metadata_db_update_failed",
                        object_id=object_id,
                        error=str(e))
            return False
    
    async def _update_svgx_symbol_metadata_in_db(self, symbol_id: str, metadata: SVGXSymbolMetadata) -> bool:
        """Update SVGX symbol metadata in database."""
        # Implementation would update database for SVGX symbol metadata
        # This is a placeholder implementation
        try:
            # Simulate database update
            await asyncio.sleep(0.01)  # Simulate DB latency
            return True
        except Exception as e:
            logger.error("svgx_symbol_metadata_db_update_failed",
                        symbol_id=symbol_id,
                        error=str(e))
            return False
    
    async def _check_svgx_database_health(self) -> Dict[str, Any]:
        """Check SVGX database health."""
        # Implementation would check database connectivity
        # This is a placeholder implementation
        try:
            # Simulate database health check
            await asyncio.sleep(0.01)  # Simulate DB latency
            
            return {
                "status": "healthy",
                "response_time": 0.01,
                "connection_pool": "active"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "error_type": type(e).__name__
            } 