"""
Advanced Caching Service
Implements Redis caching for floor data, intelligent preloading, and cache invalidation strategies
"""

import json
import time
import hashlib
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)

class CacheStrategy(Enum):
    """Cache strategies for different data types"""
    FLOOR_DATA = "floor_data"
    OBJECT_DATA = "object_data"
    ROUTE_DATA = "route_data"
    ANALYTICS_DATA = "analytics_data"
    GRID_CALIBRATION = "grid_calibration"
    USER_SESSION = "user_session"
    SEARCH_RESULTS = "search_results"

class CachePriority(Enum):
    """Cache priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class CacheConfig:
    """Cache configuration for different data types"""
    strategy: CacheStrategy
    ttl: int  # Time to live in seconds
    priority: CachePriority
    max_size: int  # Maximum number of items
    preload_enabled: bool = True
    invalidation_patterns: List[str] = field(default_factory=list)

@dataclass
class CacheItem:
    """Cache item with metadata"""
    key: str
    value: Any
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    size: int = 0
    priority: CachePriority = CachePriority.MEDIUM
    tags: List[str] = field(default_factory=list)

class RedisCacheManager:
    """Redis-based cache manager with advanced features"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.cache_configs = self._initialize_cache_configs()
        self.local_cache: Dict[str, CacheItem] = {}  # Fallback local cache
        self.preload_queue = asyncio.Queue()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "preloads": 0
        }
    
    def _initialize_cache_configs(self) -> Dict[CacheStrategy, CacheConfig]:
        """Initialize cache configurations"""
        return {
            CacheStrategy.FLOOR_DATA: CacheConfig(
                strategy=CacheStrategy.FLOOR_DATA,
                ttl=3600,  # 1 hour
                priority=CachePriority.HIGH,
                max_size=1000,
                preload_enabled=True,
                invalidation_patterns=["floor:*", "building:*"]
            ),
            CacheStrategy.OBJECT_DATA: CacheConfig(
                strategy=CacheStrategy.OBJECT_DATA,
                ttl=1800,  # 30 minutes
                priority=CachePriority.MEDIUM,
                max_size=5000,
                preload_enabled=True,
                invalidation_patterns=["object:*", "floor:*"]
            ),
            CacheStrategy.ROUTE_DATA: CacheConfig(
                strategy=CacheStrategy.ROUTE_DATA,
                ttl=1800,  # 30 minutes
                priority=CachePriority.MEDIUM,
                max_size=2000,
                preload_enabled=True,
                invalidation_patterns=["route:*", "floor:*"]
            ),
            CacheStrategy.ANALYTICS_DATA: CacheConfig(
                strategy=CacheStrategy.ANALYTICS_DATA,
                ttl=7200,  # 2 hours
                priority=CachePriority.LOW,
                max_size=500,
                preload_enabled=False,
                invalidation_patterns=["analytics:*"]
            ),
            CacheStrategy.GRID_CALIBRATION: CacheConfig(
                strategy=CacheStrategy.GRID_CALIBRATION,
                ttl=3600,  # 1 hour
                priority=CachePriority.HIGH,
                max_size=100,
                preload_enabled=True,
                invalidation_patterns=["grid:*", "floor:*"]
            ),
            CacheStrategy.USER_SESSION: CacheConfig(
                strategy=CacheStrategy.USER_SESSION,
                ttl=1800,  # 30 minutes
                priority=CachePriority.CRITICAL,
                max_size=1000,
                preload_enabled=False,
                invalidation_patterns=["session:*", "user:*"]
            ),
            CacheStrategy.SEARCH_RESULTS: CacheConfig(
                strategy=CacheStrategy.SEARCH_RESULTS,
                ttl=900,  # 15 minutes
                priority=CachePriority.LOW,
                max_size=2000,
                preload_enabled=False,
                invalidation_patterns=["search:*"]
            )
        }
    
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            import redis.asyncio as redis
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Redis cache manager initialized successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed, using local cache: {e}")
            self.redis_client = None
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
    
    def _generate_key(self, strategy: CacheStrategy, *args) -> str:
        """Generate cache key from strategy and arguments"""
        key_parts = [strategy.value] + [str(arg) for arg in args]
        return ":".join(key_parts)
    
    def _serialize_value(self, value: Any) -> str:
        """Serialize value for storage"""
        return json.dumps(value, default=str)
    
    def _deserialize_value(self, value: str) -> Any:
        """Deserialize value from storage"""
        return json.loads(value)
    
    async def get(self, strategy: CacheStrategy, *args) -> Optional[Any]:
        """Get value from cache"""
        key = self._generate_key(strategy, *args)
        
        try:
            if self.redis_client:
                # Try Redis first
                value = await self.redis_client.get(key)
                if value:
                    self.stats["hits"] += 1
                    # Update access metadata
                    await self._update_access_metadata(key)
                    return self._deserialize_value(value)
            
            # Fallback to local cache
            if key in self.local_cache:
                item = self.local_cache[key]
                if datetime.utcnow() - item.created_at < timedelta(seconds=self.cache_configs[strategy].ttl):
                    item.accessed_at = datetime.utcnow()
                    item.access_count += 1
                    self.stats["hits"] += 1
                    return item.value
            
            self.stats["misses"] += 1
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(self, strategy: CacheStrategy, value: Any, *args, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        key = self._generate_key(strategy, *args)
        config = self.cache_configs[strategy]
        
        try:
            serialized_value = self._serialize_value(value)
            
            if self.redis_client:
                # Store in Redis
                cache_ttl = ttl or config.ttl
                await self.redis_client.setex(key, cache_ttl, serialized_value)
                
                # Store metadata
                metadata = {
                    "created_at": datetime.utcnow().isoformat(),
                    "accessed_at": datetime.utcnow().isoformat(),
                    "access_count": 0,
                    "priority": config.priority.value,
                    "strategy": strategy.value
                }
                await self.redis_client.hset(f"{key}:metadata", mapping=metadata)
            
            # Also store in local cache as backup
            cache_item = CacheItem(
                key=key,
                value=value,
                created_at=datetime.utcnow(),
                accessed_at=datetime.utcnow(),
                priority=config.priority,
                size=len(serialized_value)
            )
            
            # Manage local cache size
            await self._manage_local_cache_size(strategy)
            self.local_cache[key] = cache_item
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def delete(self, strategy: CacheStrategy, *args) -> bool:
        """Delete value from cache"""
        key = self._generate_key(strategy, *args)
        
        try:
            if self.redis_client:
                await self.redis_client.delete(key)
                await self.redis_client.delete(f"{key}:metadata")
            
            if key in self.local_cache:
                del self.local_cache[key]
            
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        try:
            count = 0
            
            if self.redis_client:
                # Get all keys matching pattern
                keys = await self.redis_client.keys(pattern)
                if keys:
                    # Delete keys and their metadata
                    for key in keys:
                        await self.redis_client.delete(key)
                        await self.redis_client.delete(f"{key}:metadata")
                    count += len(keys)
            
            # Invalidate local cache
            local_keys = [k for k in self.local_cache.keys() if pattern.replace("*", "") in k]
            for key in local_keys:
                del self.local_cache[key]
            count += len(local_keys)
            
            logger.info(f"Invalidated {count} cache entries for pattern: {pattern}")
            return count
            
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return 0
    
    async def invalidate_floor_data(self, floor_id: str) -> int:
        """Invalidate all cache entries related to a floor"""
        patterns = [
            f"floor_data:{floor_id}",
            f"object_data:floor:{floor_id}*",
            f"route_data:floor:{floor_id}*",
            f"grid_calibration:floor:{floor_id}",
            f"analytics_data:floor:{floor_id}"
        ]
        
        total_count = 0
        for pattern in patterns:
            count = await self.invalidate_pattern(pattern)
            total_count += count
        
        logger.info(f"Invalidated {total_count} cache entries for floor: {floor_id}")
        return total_count
    
    async def _update_access_metadata(self, key: str):
        """Update access metadata for a cache key"""
        try:
            if self.redis_client:
                metadata = {
                    "accessed_at": datetime.utcnow().isoformat(),
                    "access_count": await self.redis_client.hincrby(f"{key}:metadata", "access_count", 1)
                }
                await self.redis_client.hset(f"{key}:metadata", mapping=metadata)
        except Exception as e:
            logger.error(f"Error updating access metadata: {e}")
    
    async def _manage_local_cache_size(self, strategy: CacheStrategy):
        """Manage local cache size by evicting least important items"""
        config = self.cache_configs[strategy]
        
        if len(self.local_cache) >= config.max_size:
            # Find items to evict (LRU + priority based)
            items_to_evict = []
            
            for key, item in self.local_cache.items():
                if key.startswith(strategy.value):
                    # Calculate eviction score (lower is better)
                    time_factor = (datetime.utcnow() - item.accessed_at).total_seconds()
                    priority_factor = {"low": 1, "medium": 2, "high": 3, "critical": 4}[item.priority.value]
                    access_factor = 1 / (item.access_count + 1)
                    
                    eviction_score = time_factor * access_factor / priority_factor
                    items_to_evict.append((key, eviction_score))
            
            # Sort by eviction score and remove worst items
            items_to_evict.sort(key=lambda x: x[1])
            items_to_remove = min(len(items_to_evict), len(self.local_cache) - config.max_size + 10)
            
            for i in range(items_to_remove):
                key, _ = items_to_evict[i]
                del self.local_cache[key]
                self.stats["evictions"] += 1
    
    async def preload_floor_data(self, floor_id: str):
        """Preload floor data into cache"""
        try:
            # Add to preload queue
            await self.preload_queue.put({
                "type": "floor_data",
                "floor_id": floor_id,
                "timestamp": datetime.utcnow()
            })
            
            self.stats["preloads"] += 1
            logger.info(f"Queued floor data preload for: {floor_id}")
            
        except Exception as e:
            logger.error(f"Error queuing floor preload: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": self.stats["hits"] / (self.stats["hits"] + self.stats["misses"]) if (self.stats["hits"] + self.stats["misses"]) > 0 else 0,
            "evictions": self.stats["evictions"],
            "preloads": self.stats["preloads"],
            "local_cache_size": len(self.local_cache),
            "redis_connected": self.redis_client is not None
        }

class CacheDecorator:
    """Decorator for automatic caching"""
    
    def __init__(self, cache_manager: RedisCacheManager, strategy: CacheStrategy, ttl: Optional[int] = None):
        self.cache_manager = cache_manager
        self.strategy = strategy
        self.ttl = ttl
    
    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [func.__name__] + [str(arg) for arg in args] + [f"{k}:{v}" for k, v in sorted(kwargs.items())]
            cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            # Try to get from cache
            cached_result = await self.cache_manager.get(self.strategy, cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await self.cache_manager.set(self.strategy, result, cache_key, ttl=self.ttl)
            
            return result
        
        return wrapper

class IntelligentPreloader:
    """Intelligent preloading system"""
    
    def __init__(self, cache_manager: RedisCacheManager):
        self.cache_manager = cache_manager
        self.preload_patterns = {
            "user_activity": {
                "floor_access": ["floor_data", "object_data", "route_data"],
                "analytics_view": ["analytics_data"],
                "grid_calibration": ["grid_calibration"]
            },
            "data_relationships": {
                "floor_objects": ["object_data"],
                "floor_routes": ["route_data"],
                "building_floors": ["floor_data"]
            }
        }
        self.preload_history: Dict[str, List[datetime]] = {}
    
    async def preload_related_data(self, floor_id: str, data_type: str):
        """Preload data related to the accessed floor"""
        try:
            if data_type in self.preload_patterns["user_activity"]:
                strategies = self.preload_patterns["user_activity"][data_type]
                
                for strategy_name in strategies:
                    strategy = CacheStrategy(strategy_name)
                    if self.cache_manager.cache_configs[strategy].preload_enabled:
                        await self.cache_manager.preload_floor_data(floor_id)
            
            # Update preload history
            if floor_id not in self.preload_history:
                self.preload_history[floor_id] = []
            self.preload_history[floor_id].append(datetime.utcnow())
            
            # Keep only recent history
            self.preload_history[floor_id] = [
                dt for dt in self.preload_history[floor_id]
                if datetime.utcnow() - dt < timedelta(hours=24)
            ]
            
        except Exception as e:
            logger.error(f"Error in intelligent preloading: {e}")
    
    async def predict_and_preload(self, user_id: str, current_floor_id: str):
        """Predict user's next actions and preload data"""
        try:
            # Simple prediction based on user patterns
            # In production, this could use ML models
            
            # Preload adjacent floors if they exist
            building_id = current_floor_id.split('-')[0] if '-' in current_floor_id else current_floor_id
            
            # Preload common data types
            await self.preload_related_data(current_floor_id, "floor_access")
            await self.preload_related_data(current_floor_id, "analytics_view")
            
        except Exception as e:
            logger.error(f"Error in prediction and preload: {e}")

class CacheService:
    """Main cache service that coordinates all caching features"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.cache_manager = RedisCacheManager(redis_url)
        self.preloader = IntelligentPreloader(self.cache_manager)
        self.preload_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the cache service"""
        await self.cache_manager.initialize()
        self.preload_task = asyncio.create_task(self._preload_worker())
        logger.info("Cache service started")
    
    async def stop(self):
        """Stop the cache service"""
        if self.preload_task:
            self.preload_task.cancel()
        await self.cache_manager.close()
        logger.info("Cache service stopped")
    
    async def _preload_worker(self):
        """Background worker for processing preload requests"""
        while True:
            try:
                preload_request = await self.cache_manager.preload_queue.get()
                
                if preload_request["type"] == "floor_data":
                    floor_id = preload_request["floor_id"]
                    # In production, load actual floor data here
                    logger.info(f"Preloading floor data for: {floor_id}")
                
                self.cache_manager.preload_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in preload worker: {e}")
    
    def cache(self, strategy: CacheStrategy, ttl: Optional[int] = None):
        """Decorator for caching function results"""
        return CacheDecorator(self.cache_manager, strategy, ttl)
    
    async def get_floor_data(self, floor_id: str) -> Optional[Any]:
        """Get floor data with caching"""
        return await self.cache_manager.get(CacheStrategy.FLOOR_DATA, floor_id)
    
    async def set_floor_data(self, floor_id: str, data: Any) -> bool:
        """Set floor data with caching"""
        return await self.cache_manager.set(CacheStrategy.FLOOR_DATA, data, floor_id)
    
    async def invalidate_floor(self, floor_id: str) -> int:
        """Invalidate all cache entries for a floor"""
        return await self.cache_manager.invalidate_floor_data(floor_id)
    
    async def preload_floor(self, floor_id: str):
        """Preload floor data"""
        await self.preloader.preload_related_data(floor_id, "floor_access")
    
    async def predict_and_preload(self, user_id: str, floor_id: str):
        """Predict and preload data for user"""
        await self.preloader.predict_and_preload(user_id, floor_id)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return await self.cache_manager.get_cache_stats()

# Global cache service instance
cache_service = CacheService() 