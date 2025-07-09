"""
Advanced Caching System for AHJ API Integration

Provides intelligent caching mechanisms for AHJ API operations including:
- Multi-level caching (memory, Redis, database)
- Cache invalidation strategies
- Performance optimization
- Cache warming and preloading
"""

import json
import time
import hashlib
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import uuid
import logging
from functools import wraps
import pickle
import zlib
from collections import OrderedDict, defaultdict
from pathlib import Path
import sqlite3
import gzip

from utils.logger import get_logger

logger = get_logger(__name__)


class CacheLevel(Enum):
    """Cache levels in the multi-layer system"""
    L1 = "L1"  # Memory cache (fastest, limited size)
    L2 = "L2"  # Redis cache (fast, larger size)
    L3 = "L3"  # Disk cache (slower, unlimited size)
    L4 = "L4"  # Database cache (persistent, queryable)


class CachePolicy(Enum):
    """Cache eviction policies"""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    FIFO = "fifo"  # First In First Out


@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    level: CacheLevel
    hit_count: int = 0
    miss_count: int = 0
    eviction_count: int = 0
    total_size_bytes: int = 0
    max_size_bytes: int = 0
    hit_rate: float = 0.0
    average_access_time_ms: float = 0.0
    compression_ratio: float = 1.0


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: float
    accessed_at: float
    access_count: int = 0
    size_bytes: int = 0
    ttl_seconds: Optional[int] = None
    compressed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class MemoryCache:
    """L1 Memory cache with LRU eviction"""
    
    def __init__(self, max_size_mb: int = 100, policy: CachePolicy = CachePolicy.LRU):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.policy = policy
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.metrics = CacheMetrics(CacheLevel.L1, max_size_bytes=self.max_size_bytes)
        self.lock = threading.RLock()
        self.logger = get_logger(__name__)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                
                # Check TTL
                if entry.ttl_seconds and time.time() - entry.created_at > entry.ttl_seconds:
                    self._evict_entry(key)
                    self.metrics.miss_count += 1
                    return None
                
                # Update access info
                entry.accessed_at = time.time()
                entry.access_count += 1
                
                # Move to end (LRU)
                self.cache.move_to_end(key)
                
                self.metrics.hit_count += 1
                self._update_hit_rate()
                return entry.value
            else:
                self.metrics.miss_count += 1
                self._update_hit_rate()
                return None
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None, 
            compress: bool = False) -> bool:
        """Set value in cache"""
        with self.lock:
            # Serialize and compress if needed
            serialized_value = self._serialize_value(value)
            if compress:
                serialized_value = self._compress_data(serialized_value)
            
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                accessed_at=time.time(),
                size_bytes=len(serialized_value),
                ttl_seconds=ttl_seconds,
                compressed=compress
            )
            
            # Check if we need to evict entries
            while self._get_total_size() + entry.size_bytes > self.max_size_bytes:
                if not self._evict_oldest():
                    return False  # Cannot fit even after eviction
            
            self.cache[key] = entry
            self.metrics.total_size_bytes = self._get_total_size()
            
            return True
    
    def delete(self, key: str) -> bool:
        """Delete entry from cache"""
        with self.lock:
            if key in self.cache:
                entry = self.cache.pop(key)
                self.metrics.total_size_bytes -= entry.size_bytes
                return True
            return False
    
    def clear(self):
        """Clear all entries"""
        with self.lock:
            self.cache.clear()
            self.metrics.total_size_bytes = 0
    
    def _evict_oldest(self) -> bool:
        """Evict oldest entry based on policy"""
        if not self.cache:
            return False
        
        if self.policy == CachePolicy.LRU:
            # Remove least recently used
            key = next(iter(self.cache))
        elif self.policy == CachePolicy.LFU:
            # Remove least frequently used
            key = min(self.cache.keys(), key=lambda k: self.cache[k].access_count)
        elif self.policy == CachePolicy.FIFO:
            # Remove first in
            key = next(iter(self.cache))
        else:
            # Default to LRU
            key = next(iter(self.cache))
        
        self._evict_entry(key)
        return True
    
    def _evict_entry(self, key: str):
        """Evict specific entry"""
        if key in self.cache:
            entry = self.cache.pop(key)
            self.metrics.total_size_bytes -= entry.size_bytes
            self.metrics.eviction_count += 1
    
    def _get_total_size(self) -> int:
        """Get total size of all entries"""
        return sum(entry.size_bytes for entry in self.cache.values())
    
    def _update_hit_rate(self):
        """Update hit rate metric"""
        total_requests = self.metrics.hit_count + self.metrics.miss_count
        if total_requests > 0:
            self.metrics.hit_rate = self.metrics.hit_count / total_requests
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value to bytes"""
        return pickle.dumps(value)
    
    def _compress_data(self, data: bytes) -> bytes:
        """Compress data using gzip"""
        return gzip.compress(data)
    
    def get_metrics(self) -> CacheMetrics:
        """Get cache metrics"""
        return self.metrics


class DiskCache:
    """L3 Disk cache with file-based storage"""
    
    def __init__(self, cache_dir: str = "cache", max_size_mb: int = 1000):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.metrics = CacheMetrics(CacheLevel.L3, max_size_bytes=self.max_size_bytes)
        self.lock = threading.RLock()
        self.logger = get_logger(__name__)
        
        # Create index file
        self.index_file = self.cache_dir / "index.json"
        self._load_index()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from disk cache"""
        with self.lock:
            if key not in self.index:
                self.metrics.miss_count += 1
                self._update_hit_rate()
                return None
            
            entry_info = self.index[key]
            file_path = self.cache_dir / f"{key}.cache"
            
            if not file_path.exists():
                # Clean up stale index entry
                del self.index[key]
                self._save_index()
                self.metrics.miss_count += 1
                self._update_hit_rate()
                return None
            
            # Check TTL
            if entry_info.get('ttl_seconds') and \
               time.time() - entry_info['created_at'] > entry_info['ttl_seconds']:
                self._evict_entry(key)
                self.metrics.miss_count += 1
                self._update_hit_rate()
                return None
            
            try:
                # Read and deserialize
                with open(file_path, 'rb') as f:
                    data = f.read()
                
                if entry_info.get('compressed', False):
                    data = gzip.decompress(data)
                
                value = pickle.loads(data)
                
                # Update access info
                entry_info['accessed_at'] = time.time()
                entry_info['access_count'] = entry_info.get('access_count', 0) + 1
                self._save_index()
                
                self.metrics.hit_count += 1
                self._update_hit_rate()
                return value
                
            except Exception as e:
                self.logger.error(f"Error reading cache file {file_path}: {e}")
                self._evict_entry(key)
                self.metrics.miss_count += 1
                self._update_hit_rate()
                return None
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None, 
            compress: bool = True) -> bool:
        """Set value in disk cache"""
        with self.lock:
            try:
                # Serialize value
                data = pickle.dumps(value)
                
                # Compress if requested
                if compress:
                    data = gzip.compress(data)
                
                # Check size limit
                if len(data) > self.max_size_bytes:
                    return False
                
                # Write to file
                file_path = self.cache_dir / f"{key}.cache"
                with open(file_path, 'wb') as f:
                    f.write(data)
                
                # Update index
                self.index[key] = {
                    'created_at': time.time(),
                    'accessed_at': time.time(),
                    'access_count': 0,
                    'size_bytes': len(data),
                    'ttl_seconds': ttl_seconds,
                    'compressed': compress
                }
                
                self._save_index()
                self.metrics.total_size_bytes = self._get_total_size()
                
                return True
                
            except Exception as e:
                self.logger.error(f"Error writing cache file: {e}")
                return False
    
    def delete(self, key: str) -> bool:
        """Delete entry from disk cache"""
        with self.lock:
            return self._evict_entry(key)
    
    def clear(self):
        """Clear all entries"""
        with self.lock:
            for file_path in self.cache_dir.glob("*.cache"):
                file_path.unlink()
            self.index.clear()
            self._save_index()
            self.metrics.total_size_bytes = 0
    
    def _evict_entry(self, key: str) -> bool:
        """Evict specific entry"""
        if key in self.index:
            file_path = self.cache_dir / f"{key}.cache"
            if file_path.exists():
                file_path.unlink()
            
            entry_info = self.index.pop(key)
            self._save_index()
            self.metrics.eviction_count += 1
            return True
        return False
    
    def _get_total_size(self) -> int:
        """Get total size of all entries"""
        return sum(entry_info.get('size_bytes', 0) for entry_info in self.index.values())
    
    def _update_hit_rate(self):
        """Update hit rate metric"""
        total_requests = self.metrics.hit_count + self.metrics.miss_count
        if total_requests > 0:
            self.metrics.hit_rate = self.metrics.hit_count / total_requests
    
    def _load_index(self):
        """Load cache index from disk"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    self.index = json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading cache index: {e}")
                self.index = {}
        else:
            self.index = {}
    
    def _save_index(self):
        """Save cache index to disk"""
        try:
            with open(self.index_file, 'w') as f:
                json.dump(self.index, f)
        except Exception as e:
            self.logger.error(f"Error saving cache index: {e}")
    
    def get_metrics(self) -> CacheMetrics:
        """Get cache metrics"""
        return self.metrics


class DatabaseCache:
    """L4 Database cache with SQLite backend"""
    
    def __init__(self, db_path: str = "cache.db"):
        self.db_path = db_path
        self.metrics = CacheMetrics(CacheLevel.L4)
        self.lock = threading.RLock()
        self.logger = get_logger(__name__)
        
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    created_at REAL,
                    accessed_at REAL,
                    access_count INTEGER DEFAULT 0,
                    size_bytes INTEGER,
                    ttl_seconds INTEGER,
                    compressed BOOLEAN DEFAULT 0,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_accessed_at 
                ON cache_entries(accessed_at)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_access_count 
                ON cache_entries(access_count)
            """)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from database cache"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT value, created_at, ttl_seconds, compressed
                        FROM cache_entries WHERE key = ?
                    """, (key,))
                    
                    row = cursor.fetchone()
                    if not row:
                        self.metrics.miss_count += 1
                        self._update_hit_rate()
                        return None
                    
                    value_blob, created_at, ttl_seconds, compressed = row
                    
                    # Check TTL
                    if ttl_seconds and time.time() - created_at > ttl_seconds:
                        self.delete(key)
                        self.metrics.miss_count += 1
                        self._update_hit_rate()
                        return None
                    
                    # Decompress if needed
                    if compressed:
                        value_blob = gzip.decompress(value_blob)
                    
                    value = pickle.loads(value_blob)
                    
                    # Update access info
                    conn.execute("""
                        UPDATE cache_entries 
                        SET accessed_at = ?, access_count = access_count + 1
                        WHERE key = ?
                    """, (time.time(), key))
                    
                    self.metrics.hit_count += 1
                    self._update_hit_rate()
                    return value
                    
            except Exception as e:
                self.logger.error(f"Error reading from database cache: {e}")
                self.metrics.miss_count += 1
                self._update_hit_rate()
                return None
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None, 
            compress: bool = True) -> bool:
        """Set value in database cache"""
        with self.lock:
            try:
                # Serialize value
                data = pickle.dumps(value)
                
                # Compress if requested
                if compress:
                    data = gzip.compress(data)
                
                metadata = json.dumps({})
                
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO cache_entries 
                        (key, value, created_at, accessed_at, size_bytes, ttl_seconds, compressed, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (key, data, time.time(), time.time(), len(data), ttl_seconds, compress, metadata))
                
                return True
                
            except Exception as e:
                self.logger.error(f"Error writing to database cache: {e}")
                return False
    
    def delete(self, key: str) -> bool:
        """Delete entry from database cache"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                    return cursor.rowcount > 0
            except Exception as e:
                self.logger.error(f"Error deleting from database cache: {e}")
                return False
    
    def clear(self):
        """Clear all entries"""
        with self.lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM cache_entries")
            except Exception as e:
                self.logger.error(f"Error clearing database cache: {e}")
    
    def _update_hit_rate(self):
        """Update hit rate metric"""
        total_requests = self.metrics.hit_count + self.metrics.miss_count
        if total_requests > 0:
            self.metrics.hit_rate = self.metrics.hit_count / total_requests
    
    def get_metrics(self) -> CacheMetrics:
        """Get cache metrics"""
        return self.metrics


class AdvancedCachingSystem:
    """
    Multi-layer caching system with intelligent cache management.
    
    Features:
    - Multi-layer caching (Memory, Disk, Database)
    - Intelligent cache invalidation
    - Predictive caching
    - Cache warming
    - Performance monitoring
    - Compression optimization
    """
    
    def __init__(self, memory_cache_size_mb: int = 100, disk_cache_size_mb: int = 1000):
        self.logger = get_logger(__name__)
        
        # Initialize cache layers
        self.layers = {
            CacheLevel.L1: MemoryCache(memory_cache_size_mb),
            CacheLevel.L3: DiskCache(max_size_mb=disk_cache_size_mb),
            CacheLevel.L4: DatabaseCache()
        }
        
        # Cache warming and prediction
        self.access_patterns = defaultdict(int)
        self.prediction_model = None
        
        # Performance tracking
        self.performance_metrics = []
    
    def get_cached_result(self, key: str, computation_func: Callable, 
                         ttl_seconds: Optional[int] = None, 
                         compress: bool = True) -> Any:
        """
        Get cached result or compute if not cached.
        
        Args:
            key: Cache key
            computation_func: Function to compute if not cached
            ttl_seconds: Time to live in seconds
            compress: Whether to compress the result
            
        Returns:
            Cached or computed result
        """
        start_time = time.time()
        
        # Try each cache layer
        for level in [CacheLevel.L1, CacheLevel.L3, CacheLevel.L4]:
            cache = self.layers[level]
            result = cache.get(key)
            
            if result is not None:
                # Cache hit
                access_time = (time.time() - start_time) * 1000
                self._record_access_pattern(key, level, access_time)
                return result
        
        # Cache miss - compute result
        self.logger.debug(f"Cache miss for key: {key}")
        result = computation_func()
        
        # Store in all cache layers
        for level in [CacheLevel.L1, CacheLevel.L3, CacheLevel.L4]:
            cache = self.layers[level]
            cache.set(key, result, ttl_seconds, compress)
        
        # Record access pattern
        access_time = (time.time() - start_time) * 1000
        self._record_access_pattern(key, CacheLevel.L1, access_time)
        
        return result
    
    def invalidate_cache(self, pattern: str):
        """
        Invalidate cache entries matching pattern.
        
        Args:
            pattern: Pattern to match keys (supports wildcards)
        """
        self.logger.info(f"Invalidating cache entries matching pattern: {pattern}")
        
        # Convert pattern to regex-like matching
        import fnmatch
        
        for level, cache in self.layers.items():
            if hasattr(cache, 'cache'):  # Memory cache
                keys_to_delete = [key for key in cache.cache.keys() 
                                if fnmatch.fnmatch(key, pattern)]
                for key in keys_to_delete:
                    cache.delete(key)
            elif hasattr(cache, 'index'):  # Disk cache
                keys_to_delete = [key for key in cache.index.keys() 
                                if fnmatch.fnmatch(key, pattern)]
                for key in keys_to_delete:
                    cache.delete(key)
            else:  # Database cache - more complex
                # For database, we'd need to implement pattern matching
                # This is a simplified version
                pass
    
    def precompute_common_operations(self, operations: List[Tuple[str, Callable]]):
        """
        Precompute common operations for cache warming.
        
        Args:
            operations: List of (key, computation_func) tuples
        """
        self.logger.info(f"Precomputing {len(operations)} common operations")
        
        for key, computation_func in operations:
            try:
                # Check if already cached
                cached_result = None
                for cache in self.layers.values():
                    result = cache.get(key)
                    if result is not None:
                        cached_result = result
                        break
                
                if cached_result is None:
                    # Compute and cache
                    result = computation_func()
                    for cache in self.layers.values():
                        cache.set(key, result)
                    
                    self.logger.debug(f"Precomputed: {key}")
                    
            except Exception as e:
                self.logger.error(f"Error precomputing {key}: {e}")
    
    def _record_access_pattern(self, key: str, level: CacheLevel, access_time: float):
        """Record access pattern for prediction"""
        self.access_patterns[key] += 1
        
        # Update performance metrics
        self.performance_metrics.append({
            'key': key,
            'level': level.value,
            'access_time_ms': access_time,
            'timestamp': time.time()
        })
    
    def get_cache_metrics(self) -> Dict[CacheLevel, CacheMetrics]:
        """Get metrics for all cache layers"""
        return {level: cache.get_metrics() for level, cache in self.layers.items()}
    
    def get_overall_metrics(self) -> Dict[str, Any]:
        """Get overall caching system metrics"""
        metrics = self.get_cache_metrics()
        
        total_hits = sum(m.hit_count for m in metrics.values())
        total_misses = sum(m.miss_count for m in metrics.values())
        total_requests = total_hits + total_misses
        
        overall_hit_rate = total_hits / total_requests if total_requests > 0 else 0.0
        
        return {
            'overall_hit_rate': overall_hit_rate,
            'total_requests': total_requests,
            'total_hits': total_hits,
            'total_misses': total_misses,
            'layer_metrics': {level.value: m.__dict__ for level, m in metrics.items()},
            'access_patterns': dict(self.access_patterns)
        }
    
    def optimize_cache_performance(self):
        """Optimize cache performance based on usage patterns"""
        metrics = self.get_overall_metrics()
        
        # Adjust cache sizes based on hit rates
        for level, cache in self.layers.items():
            layer_metrics = metrics['layer_metrics'][level.value]
            hit_rate = layer_metrics['hit_rate']
            
            if hit_rate < 0.5:  # Low hit rate
                # Consider reducing cache size or changing eviction policy
                self.logger.info(f"Low hit rate for {level.value}: {hit_rate:.2%}")
            elif hit_rate > 0.9:  # High hit rate
                # Consider increasing cache size
                self.logger.info(f"High hit rate for {level.value}: {hit_rate:.2%}")
    
    def warm_cache_for_building(self, building_id: str, common_operations: List[Callable]):
        """Warm cache for specific building operations"""
        self.logger.info(f"Warming cache for building: {building_id}")
        
        operations = []
        for i, operation in enumerate(common_operations):
            key = f"building_{building_id}_operation_{i}"
            operations.append((key, operation))
        
        self.precompute_common_operations(operations)
    
    def clear_all_caches(self):
        """Clear all cache layers"""
        for cache in self.layers.values():
            cache.clear()
        
        self.logger.info("All cache layers cleared")
    
    def get_cache_size_info(self) -> Dict[str, Any]:
        """Get information about cache sizes and usage"""
        size_info = {}
        
        for level, cache in self.layers.items():
            metrics = cache.get_metrics()
            size_info[level.value] = {
                'used_size_mb': metrics.total_size_bytes / (1024 * 1024),
                'max_size_mb': metrics.max_size_bytes / (1024 * 1024),
                'usage_percent': (metrics.total_size_bytes / metrics.max_size_bytes * 100) 
                                if metrics.max_size_bytes > 0 else 0
            }
        
        return size_info 