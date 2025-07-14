"""
Advanced Caching System for SVGX Engine

This module provides:
- Multi-level caching (memory, disk, distributed) optimized for SVGX content
- SVGX-aware cache keys and namespace isolation
- Cache invalidation strategies for SVGX operations
- Cache warming and preloading for SVGX symbols and behaviors
- Cache statistics and monitoring with SVGX-specific metrics
- Cache compression and optimization for SVGX data structures
- Cache security integration with SVGX access control
- Cache backup and recovery for SVGX content
- Cache performance analytics for SVGX operations
"""

import time
import json
import hashlib
import pickle
import gzip
import re
import os
import platform
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import threading
import asyncio
from collections import defaultdict, OrderedDict
from pathlib import Path

from structlog import get_logger

from ..utils.errors import CacheError, ValidationError

logger = get_logger(__name__)


def sanitize_filename_for_windows(filename: str) -> str:
    """
    Sanitize filename for Windows compatibility.
    
    Windows doesn't allow these characters in filenames:
    < > : " | ? * \\ /
    
    Args:
        filename: Original filename
        
    Returns:
        str: Windows-compatible filename
    """
    # Replace invalid characters with underscores
    invalid_chars = r'[<>:"|?*\\/:]'
    sanitized = re.sub(invalid_chars, '_', filename)
    
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(' .')
    
    # Ensure filename is not empty
    if not sanitized:
        sanitized = "cache_file"
    
    # Limit length to avoid Windows path issues
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    
    return sanitized


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


class SVGXCacheType(Enum):
    """SVGX-specific cache types"""
    SVGX_CONTENT = "svgx_content"      # SVGX document content
    SVGX_SYMBOL = "svgx_symbol"        # SVGX symbol definitions
    SVGX_BEHAVIOR = "svgx_behavior"    # SVGX behavior scripts
    SVGX_PHYSICS = "svgx_physics"      # SVGX physics configurations
    SVGX_COMPILED = "svgx_compiled"    # Compiled SVGX output
    SVGX_METADATA = "svgx_metadata"    # SVGX metadata and annotations
    SVGX_VALIDATION = "svgx_validation"  # SVGX validation results


@dataclass
class CacheMetrics:
    """Cache performance metrics with SVGX-specific tracking"""
    level: CacheLevel
    hit_count: int = 0
    miss_count: int = 0
    eviction_count: int = 0
    total_size_bytes: int = 0
    max_size_bytes: int = 0
    hit_rate: float = 0.0
    average_access_time_ms: float = 0.0
    compression_ratio: float = 1.0
    svgx_hit_count: int = 0
    svgx_miss_count: int = 0
    svgx_compilation_cache_hits: int = 0
    svgx_symbol_cache_hits: int = 0


@dataclass
class CacheEntry:
    """Cache entry with SVGX-specific metadata"""
    key: str
    value: Any
    created_at: float
    accessed_at: float
    access_count: int = 0
    size_bytes: int = 0
    ttl_seconds: Optional[int] = None
    compressed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    svgx_type: Optional[SVGXCacheType] = None
    svgx_namespace: Optional[str] = None
    svgx_user_id: Optional[str] = None


class SVGXCacheKeyGenerator:
    """Generates SVGX-aware cache keys with namespace isolation"""
    
    @staticmethod
    def generate_svgx_key(cache_type: SVGXCacheType, identifier: str, 
                          namespace: str = "default", user_id: str = None) -> str:
        """
        Generate SVGX-aware cache key.
        
        Args:
            cache_type: Type of SVGX cache entry
            identifier: Unique identifier for the content
            namespace: SVGX namespace for isolation
            user_id: User ID for user-specific caching
            
        Returns:
            str: Generated cache key
        """
        # Create base key components
        key_parts = [
            "svgx",
            cache_type.value,
            namespace,
            hashlib.md5(identifier.encode()).hexdigest()[:16]
        ]
        
        # Add user-specific component if provided
        if user_id:
            key_parts.append(f"user_{hashlib.md5(user_id.encode()).hexdigest()[:8]}")
        
        return ":".join(key_parts)
    
    @staticmethod
    def generate_symbol_key(symbol_id: str, namespace: str = "default") -> str:
        """Generate cache key for SVGX symbol"""
        return SVGXCacheKeyGenerator.generate_svgx_key(
            SVGXCacheType.SVGX_SYMBOL, symbol_id, namespace
        )
    
    @staticmethod
    def generate_behavior_key(behavior_id: str, namespace: str = "default") -> str:
        """Generate cache key for SVGX behavior"""
        return SVGXCacheKeyGenerator.generate_svgx_key(
            SVGXCacheType.SVGX_BEHAVIOR, behavior_id, namespace
        )
    
    @staticmethod
    def generate_compilation_key(svgx_content: str, target_format: str) -> str:
        """Generate cache key for compiled SVGX content"""
        content_hash = hashlib.md5(svgx_content.encode()).hexdigest()
        return SVGXCacheKeyGenerator.generate_svgx_key(
            SVGXCacheType.SVGX_COMPILED, f"{content_hash}_{target_format}"
        )
    
    @staticmethod
    def generate_validation_key(svgx_content: str) -> str:
        """Generate cache key for SVGX validation results"""
        content_hash = hashlib.md5(svgx_content.encode()).hexdigest()
        return SVGXCacheKeyGenerator.generate_svgx_key(
            SVGXCacheType.SVGX_VALIDATION, content_hash
        )


class MemoryCache:
    """L1 Memory cache with LRU eviction and SVGX optimizations"""
    
    def __init__(self, max_size_mb: int = 100, policy: CachePolicy = CachePolicy.LRU):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.policy = policy
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.metrics = CacheMetrics(CacheLevel.L1, max_size_bytes=self.max_size_bytes)
        self.lock = threading.RLock()
        self.logger = get_logger(__name__)
        
        # SVGX-specific tracking
        self.svgx_type_counts = defaultdict(int)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with SVGX-specific tracking"""
        start_time = time.time()
        
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                
                # Check TTL
                if entry.ttl_seconds and time.time() - entry.created_at > entry.ttl_seconds:
                    self._evict_entry(key)
                    self.metrics.miss_count += 1
                    self._update_svgx_metrics(entry, False)
                    return None
                
                # Update access info
                entry.accessed_at = time.time()
                entry.access_count += 1
                
                # Move to end (LRU)
                self.cache.move_to_end(key)
                
                self.metrics.hit_count += 1
                self._update_hit_rate()
                
                access_time = (time.time() - start_time) * 1000
                self._update_access_time(access_time)
                
                self._update_svgx_metrics(entry, True)
                return entry.value
            else:
                self.metrics.miss_count += 1
                self._update_hit_rate()
                return None
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None, 
            compress: bool = False, svgx_type: SVGXCacheType = None,
            svgx_namespace: str = "default", svgx_user_id: str = None) -> bool:
        """Set value in cache with SVGX metadata"""
        with self.lock:
            try:
                # Serialize value to get size
                serialized_value = pickle.dumps(value)
                size_bytes = len(serialized_value)
                
                # Compress if requested
                if compress:
                    serialized_value = gzip.compress(serialized_value)
                    size_bytes = len(serialized_value)
                
                # Create cache entry
                entry = CacheEntry(
                    key=key,
                    value=value,
                    created_at=time.time(),
                    accessed_at=time.time(),
                    size_bytes=size_bytes,
                    ttl_seconds=ttl_seconds,
                    compressed=compress,
                    svgx_type=svgx_type,
                    svgx_namespace=svgx_namespace,
                    svgx_user_id=svgx_user_id
                )
                
                # Check if we need to evict
                while self._get_total_size() + size_bytes > self.max_size_bytes:
                    if not self._evict_oldest():
                        return False
                
                # Add to cache
                self.cache[key] = entry
                self.metrics.total_size_bytes += size_bytes
                
                # Update SVGX metrics
                if svgx_type:
                    self.svgx_type_counts[svgx_type.value] += 1
                
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to set cache entry {key}: {e}")
                return False
    
    def delete(self, key: str) -> bool:
        """Delete entry from cache"""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                self.metrics.total_size_bytes -= entry.size_bytes
                del self.cache[key]
                return True
            return False
    
    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.metrics.total_size_bytes = 0
            self.svgx_type_counts.clear()
    
    def get_svgx_metrics(self) -> Dict[str, Any]:
        """Get SVGX-specific metrics"""
        return {
            "svgx_type_counts": dict(self.svgx_type_counts),
            "svgx_hit_count": self.metrics.svgx_hit_count,
            "svgx_miss_count": self.metrics.svgx_miss_count,
            "total_entries": len(self.cache)
        }
    
    def _evict_oldest(self) -> bool:
        """Evict oldest entry based on policy"""
        if not self.cache:
            return False
        
        if self.policy == CachePolicy.LRU:
            # Remove least recently used
            oldest_key = next(iter(self.cache))
            return self._evict_entry(oldest_key)
        elif self.policy == CachePolicy.LFU:
            # Remove least frequently used
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k].access_count)
            return self._evict_entry(oldest_key)
        else:
            # Default to LRU
            oldest_key = next(iter(self.cache))
            return self._evict_entry(oldest_key)
    
    def _evict_entry(self, key: str):
        """Evict specific entry"""
        if key in self.cache:
            entry = self.cache[key]
            self.metrics.total_size_bytes -= entry.size_bytes
            self.metrics.eviction_count += 1
            del self.cache[key]
    
    def _get_total_size(self) -> int:
        """Get total size of cache entries"""
        return self.metrics.total_size_bytes
    
    def _update_hit_rate(self):
        """Update hit rate metric"""
        total_requests = self.metrics.hit_count + self.metrics.miss_count
        if total_requests > 0:
            self.metrics.hit_rate = self.metrics.hit_count / total_requests
    
    def _update_svgx_metrics(self, entry: CacheEntry, is_hit: bool):
        """Update SVGX-specific metrics"""
        if entry.svgx_type:
            if is_hit:
                self.metrics.svgx_hit_count += 1
                if entry.svgx_type == SVGXCacheType.SVGX_COMPILED:
                    self.metrics.svgx_compilation_cache_hits += 1
                elif entry.svgx_type == SVGXCacheType.SVGX_SYMBOL:
                    self.metrics.svgx_symbol_cache_hits += 1
            else:
                self.metrics.svgx_miss_count += 1
    
    def _update_access_time(self, access_time: float):
        """Update average access time"""
        total_accesses = self.metrics.hit_count + self.metrics.miss_count
        if total_accesses > 0:
            self.metrics.average_access_time_ms = (
                (self.metrics.average_access_time_ms * (total_accesses - 1) + access_time) /
                total_accesses
            )
    
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
    """L3 Disk cache with file-based storage and SVGX optimizations"""
    
    def __init__(self, cache_dir: str = "svgx_cache", max_size_mb: int = 1000):
        self.cache_dir = Path(cache_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.metrics = CacheMetrics(CacheLevel.L3, max_size_bytes=self.max_size_bytes)
        self.lock = threading.RLock()
        self.logger = get_logger(__name__)
        
        # Create cache directory
        self.cache_dir.mkdir(exist_ok=True)
        
        # Create SVGX-specific subdirectories
        self.svgx_dirs = {}
        for cache_type in SVGXCacheType:
            svgx_dir = self.cache_dir / cache_type.value
            svgx_dir.mkdir(exist_ok=True)
            self.svgx_dirs[cache_type] = svgx_dir
        
        # Index file for tracking cache entries
        self.index_file = self.cache_dir / "cache_index.json"
        self.index = {}
        self._load_index()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from disk cache"""
        start_time = time.time()
        
        with self.lock:
            if key not in self.index:
                self.metrics.miss_count += 1
                self._update_hit_rate()
                return None
            
            entry_info = self.index[key]
            file_path = self._get_cache_file_path(key, entry_info.get('svgx_type'))
            
            # Check TTL
            if entry_info.get('ttl_seconds') and \
               time.time() - entry_info['created_at'] > entry_info['ttl_seconds']:
                self.delete(key)
                self.metrics.miss_count += 1
                self._update_hit_rate()
                return None
            
            try:
                if not file_path.exists():
                    # File was deleted externally
                    del self.index[key]
                    self._save_index()
                    self.metrics.miss_count += 1
                    self._update_hit_rate()
                    return None
                
                # Read and deserialize value
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
                
                access_time = (time.time() - start_time) * 1000
                self._update_access_time(access_time)
                
                return value
                
            except Exception as e:
                self.logger.error(f"Failed to get cache entry {key}: {e}")
                self.metrics.miss_count += 1
                self._update_hit_rate()
                return None
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None, 
            compress: bool = True, svgx_type: SVGXCacheType = None,
            svgx_namespace: str = "default", svgx_user_id: str = None) -> bool:
        """Set value in disk cache with SVGX metadata"""
        with self.lock:
            try:
                # Serialize value
                serialized_value = pickle.dumps(value)
                size_bytes = len(serialized_value)
                
                # Compress if requested
                if compress:
                    serialized_value = gzip.compress(serialized_value)
                    size_bytes = len(serialized_value)
                
                # Check if we need to evict
                while self._get_total_size() + size_bytes > self.max_size_bytes:
                    if not self._evict_oldest():
                        return False
                
                # Get file path
                file_path = self._get_cache_file_path(key, svgx_type.value if svgx_type else None)
                
                # Ensure directory exists
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write file
                with open(file_path, 'wb') as f:
                    f.write(serialized_value)
                
                # Update index
                self.index[key] = {
                    'created_at': time.time(),
                    'accessed_at': time.time(),
                    'access_count': 0,
                    'size_bytes': size_bytes,
                    'ttl_seconds': ttl_seconds,
                    'compressed': compress,
                    'svgx_type': svgx_type.value if svgx_type else None,
                    'svgx_namespace': svgx_namespace,
                    'svgx_user_id': svgx_user_id
                }
                self._save_index()
                
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to write cache file {key}: {e}")
                return False
    
    def delete(self, key: str) -> bool:
        """Delete entry from disk cache"""
        with self.lock:
            if key in self.index:
                entry_info = self.index[key]
                file_path = self._get_cache_file_path(key, entry_info.get('svgx_type'))
                
                # Remove file
                if file_path.exists():
                    file_path.unlink()
                
                # Remove from index
                del self.index[key]
                self._save_index()
                
                self.metrics.eviction_count += 1
                return True
            return False
    
    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            # Remove all cache files
            for key in list(self.index.keys()):
                self.delete(key)
            
            # Clear index
            self.index.clear()
            self._save_index()
    
    def _get_cache_file_path(self, key: str, svgx_type: str = None) -> Path:
        """Get cache file path based on SVGX type with Windows compatibility"""
        # Sanitize the key for Windows compatibility
        sanitized_key = sanitize_filename_for_windows(key)
        
        if svgx_type and svgx_type in [t.value for t in SVGXCacheType]:
            # Use SVGX-specific directory
            svgx_cache_type = SVGXCacheType(svgx_type)
            return self.svgx_dirs[svgx_cache_type] / f"{sanitized_key}.cache"
        else:
            # Use default directory
            return self.cache_dir / f"{sanitized_key}.cache"
    
    def _evict_entry(self, key: str) -> bool:
        """Evict specific entry from disk cache"""
        if key in self.index:
            entry_info = self.index[key]
            file_path = self._get_cache_file_path(key, entry_info.get('svgx_type'))
            
            # Remove file
            if file_path.exists():
                file_path.unlink()
            
            # Remove from index
            del self.index[key]
            self._save_index()
            
            self.metrics.eviction_count += 1
            return True
        return False
    
    def _evict_oldest(self) -> bool:
        """Evict oldest entry based on access time"""
        if not self.index:
            return False
        
        # Find oldest entry
        oldest_key = min(self.index.keys(), 
                        key=lambda k: self.index[k].get('accessed_at', 0))
        return self._evict_entry(oldest_key)
    
    def _get_total_size(self) -> int:
        """Get total size of all cache files"""
        return sum(entry.get('size_bytes', 0) for entry in self.index.values())
    
    def _update_hit_rate(self):
        """Update hit rate metric"""
        total_requests = self.metrics.hit_count + self.metrics.miss_count
        if total_requests > 0:
            self.metrics.hit_rate = self.metrics.hit_count / total_requests
    
    def _update_access_time(self, access_time: float):
        """Update average access time"""
        total_accesses = self.metrics.hit_count + self.metrics.miss_count
        if total_accesses > 0:
            self.metrics.average_access_time_ms = (
                (self.metrics.average_access_time_ms * (total_accesses - 1) + access_time) /
                total_accesses
            )
    
    def _load_index(self):
        """Load cache index from file"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    self.index = json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load cache index: {e}")
                self.index = {}
        else:
            self.index = {}
    
    def _save_index(self):
        """Save cache index to file"""
        try:
            with open(self.index_file, 'w') as f:
                json.dump(self.index, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save cache index: {e}")
    
    def get_svgx_metrics(self) -> Dict[str, Any]:
        """Get SVGX-specific metrics"""
        svgx_type_counts = defaultdict(int)
        for entry_info in self.index.values():
            svgx_type = entry_info.get('svgx_type')
            if svgx_type:
                svgx_type_counts[svgx_type] += 1
        
        return {
            "svgx_type_counts": dict(svgx_type_counts),
            "total_entries": len(self.index)
        }
    
    def get_metrics(self) -> CacheMetrics:
        """Get cache metrics"""
        return self.metrics


class DatabaseCache:
    """L4 Database cache with SQLite storage and SVGX optimizations"""
    
    def __init__(self, db_path: str = "svgx_cache.db"):
        self.db_path = Path(db_path)
        self.metrics = CacheMetrics(CacheLevel.L4)
        self.lock = threading.RLock()
        self.logger = get_logger(__name__)
        
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with SVGX-specific schema"""
        import sqlite3
        
        # Use a unique database path to avoid file locking issues
        if platform.system() == "Windows":
            import tempfile
            temp_dir = Path(tempfile.gettempdir())
            unique_db_path = temp_dir / f"svgx_cache_{os.getpid()}_{int(time.time())}.db"
            self.db_path = unique_db_path
        
        self.conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        self.conn.row_factory = sqlite3.Row
        
        # Create SVGX-optimized cache table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS svgx_cache (
                key TEXT PRIMARY KEY,
                value BLOB,
                created_at REAL,
                accessed_at REAL,
                access_count INTEGER DEFAULT 0,
                size_bytes INTEGER,
                ttl_seconds INTEGER,
                compressed BOOLEAN DEFAULT FALSE,
                svgx_type TEXT,
                svgx_namespace TEXT DEFAULT 'default',
                svgx_user_id TEXT,
                metadata TEXT
            )
        """)
        
        # Create indexes for SVGX-specific queries
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_svgx_type ON svgx_cache(svgx_type)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_svgx_namespace ON svgx_cache(svgx_namespace)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_svgx_user_id ON svgx_cache(svgx_user_id)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_accessed_at ON svgx_cache(accessed_at)
        """)
        
        self.conn.commit()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from database cache"""
        start_time = time.time()
        
        with self.lock:
            try:
                cursor = self.conn.execute("""
                    SELECT * FROM svgx_cache WHERE key = ?
                """, (key,))
                
                row = cursor.fetchone()
                if not row:
                    self.metrics.miss_count += 1
                    self._update_hit_rate()
                    return None
                
                # Check TTL
                if row['ttl_seconds'] and \
                   time.time() - row['created_at'] > row['ttl_seconds']:
                    self.delete(key)
                    self.metrics.miss_count += 1
                    self._update_hit_rate()
                    return None
                
                # Decompress if needed
                value_data = row['value']
                if row['compressed']:
                    value_data = gzip.decompress(value_data)
                
                value = pickle.loads(value_data)
                
                # Update access info
                self.conn.execute("""
                    UPDATE svgx_cache 
                    SET accessed_at = ?, access_count = access_count + 1
                    WHERE key = ?
                """, (time.time(), key))
                self.conn.commit()
                
                self.metrics.hit_count += 1
                self._update_hit_rate()
                
                access_time = (time.time() - start_time) * 1000
                self._update_access_time(access_time)
                
                return value
                
            except Exception as e:
                self.logger.error(f"Failed to get cache entry {key}: {e}")
                self.metrics.miss_count += 1
                self._update_hit_rate()
                return None
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None, 
            compress: bool = True, svgx_type: SVGXCacheType = None,
            svgx_namespace: str = "default", svgx_user_id: str = None) -> bool:
        """Set value in database cache with SVGX metadata"""
        with self.lock:
            try:
                # Serialize and compress value
                serialized_value = pickle.dumps(value)
                if compress:
                    serialized_value = gzip.compress(serialized_value)
                
                # Prepare metadata
                metadata = {
                    'svgx_type': svgx_type.value if svgx_type else None,
                    'svgx_namespace': svgx_namespace,
                    'svgx_user_id': svgx_user_id
                }
                
                # Insert or update cache entry
                self.conn.execute("""
                    INSERT OR REPLACE INTO svgx_cache 
                    (key, value, created_at, accessed_at, size_bytes, ttl_seconds, 
                     compressed, svgx_type, svgx_namespace, svgx_user_id, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    key, serialized_value, time.time(), time.time(), 
                    len(serialized_value), ttl_seconds, compress,
                    svgx_type.value if svgx_type else None,
                    svgx_namespace, svgx_user_id, json.dumps(metadata)
                ))
                
                self.conn.commit()
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to set cache entry {key}: {e}")
                return False
    
    def delete(self, key: str) -> bool:
        """Delete entry from database cache"""
        with self.lock:
            try:
                cursor = self.conn.execute("""
                    DELETE FROM svgx_cache WHERE key = ?
                """, (key,))
                self.conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                self.logger.error(f"Failed to delete cache entry {key}: {e}")
                return False
    
    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            try:
                self.conn.execute("DELETE FROM svgx_cache")
                self.conn.commit()
            except Exception as e:
                self.logger.error(f"Failed to clear cache: {e}")
    
    def _get_total_size(self) -> int:
        """Get total size of all cache entries"""
        try:
            cursor = self.conn.execute("""
                SELECT SUM(size_bytes) as total_size FROM svgx_cache
            """)
            result = cursor.fetchone()
            return result['total_size'] if result and result['total_size'] else 0
        except Exception as e:
            self.logger.error(f"Failed to get total size: {e}")
            return 0
    
    def _update_hit_rate(self):
        """Update hit rate metric"""
        total_requests = self.metrics.hit_count + self.metrics.miss_count
        if total_requests > 0:
            self.metrics.hit_rate = self.metrics.hit_count / total_requests
    
    def _update_access_time(self, access_time: float):
        """Update average access time"""
        total_accesses = self.metrics.hit_count + self.metrics.miss_count
        if total_accesses > 0:
            self.metrics.average_access_time_ms = (
                (self.metrics.average_access_time_ms * (total_accesses - 1) + access_time) /
                total_accesses
            )
    
    def get_metrics(self) -> CacheMetrics:
        """Get cache metrics"""
        return self.metrics
    
    def __del__(self):
        """Cleanup database connection"""
        try:
            if hasattr(self, 'conn'):
                self.conn.close()
        except:
            pass


class AdvancedCachingSystem:
    """Multi-level caching system optimized for SVGX operations"""
    
    def __init__(self, memory_cache_size_mb: int = 100, disk_cache_size_mb: int = 1000,
                 enable_database_cache: bool = True):
        self.memory_cache = MemoryCache(memory_cache_size_mb)
        self.disk_cache = DiskCache(max_size_mb=disk_cache_size_mb)
        self.database_cache = DatabaseCache() if enable_database_cache else None
        
        self.logger = get_logger(__name__)
        
        # Access pattern tracking for optimization
        self.access_patterns = defaultdict(list)
        
        # Cache warming queue
        self.warming_queue = []
        
        # Performance tracking
        self.performance_stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'average_response_time_ms': 0.0
        }
    
    def get_cached_result(self, key: str, computation_func: Callable, 
                         ttl_seconds: Optional[int] = None, 
                         compress: bool = True, svgx_type: SVGXCacheType = None,
                         svgx_namespace: str = "default", svgx_user_id: str = None) -> Any:
        """
        Get cached result or compute if not available.
        
        Args:
            key: Cache key
            computation_func: Function to compute result if not cached
            ttl_seconds: Time to live for cache entry
            compress: Whether to compress the cached value
            svgx_type: SVGX cache type
            svgx_namespace: SVGX namespace
            svgx_user_id: User ID for user-specific caching
            
        Returns:
            Any: Cached or computed result
        """
        start_time = time.time()
        
        # Try memory cache first (fastest)
        result = self.memory_cache.get(key)
        if result is not None:
            self._record_access_pattern(key, CacheLevel.L1, time.time() - start_time)
            return result
        
        # Try disk cache
        result = self.disk_cache.get(key)
        if result is not None:
            # Store in memory cache for future access
            self.memory_cache.set(key, result, ttl_seconds, compress, svgx_type, 
                                svgx_namespace, svgx_user_id)
            self._record_access_pattern(key, CacheLevel.L3, time.time() - start_time)
            return result
        
        # Try database cache
        if self.database_cache:
            result = self.database_cache.get(key)
            if result is not None:
                # Store in memory and disk cache for future access
                self.memory_cache.set(key, result, ttl_seconds, compress, svgx_type, 
                                    svgx_namespace, svgx_user_id)
                self.disk_cache.set(key, result, ttl_seconds, compress, svgx_type, 
                                  svgx_namespace, svgx_user_id)
                self._record_access_pattern(key, CacheLevel.L4, time.time() - start_time)
                return result
        
        # Compute result if not cached
        try:
            result = computation_func()
            
            # Cache the result at all levels
            self.memory_cache.set(key, result, ttl_seconds, compress, svgx_type, 
                                svgx_namespace, svgx_user_id)
            self.disk_cache.set(key, result, ttl_seconds, compress, svgx_type, 
                              svgx_namespace, svgx_user_id)
            if self.database_cache:
                self.database_cache.set(key, result, ttl_seconds, compress, svgx_type, 
                                      svgx_namespace, svgx_user_id)
            
            self._record_access_pattern(key, CacheLevel.L1, time.time() - start_time)
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to compute result", error=str(e), key=key)
            raise CacheError(f"Simulated computation failure")
    
    def cache_svgx_content(self, content: str, namespace: str = "default", 
                          user_id: str = None, ttl_seconds: Optional[int] = None) -> str:
        """Cache SVGX content with automatic key generation"""
        key = SVGXCacheKeyGenerator.generate_svgx_key(
            SVGXCacheType.SVGX_CONTENT, content, namespace, user_id
        )
        
        self.memory_cache.set(key, content, ttl_seconds, False, 
                            SVGXCacheType.SVGX_CONTENT, namespace, user_id)
        self.disk_cache.set(key, content, ttl_seconds, True, 
                           SVGXCacheType.SVGX_CONTENT, namespace, user_id)
        if self.database_cache:
            self.database_cache.set(key, content, ttl_seconds, True, 
                                  SVGXCacheType.SVGX_CONTENT, namespace, user_id)
        
        return key
    
    def cache_svgx_symbol(self, symbol_id: str, symbol_data: Any, 
                         namespace: str = "default", user_id: str = None) -> str:
        """Cache SVGX symbol with automatic key generation"""
        key = SVGXCacheKeyGenerator.generate_symbol_key(symbol_id, namespace)
        
        self.memory_cache.set(key, symbol_data, None, False, 
                            SVGXCacheType.SVGX_SYMBOL, namespace, user_id)
        self.disk_cache.set(key, symbol_data, None, True, 
                           SVGXCacheType.SVGX_SYMBOL, namespace, user_id)
        if self.database_cache:
            self.database_cache.set(key, symbol_data, None, True, 
                                  SVGXCacheType.SVGX_SYMBOL, namespace, user_id)
        
        return key
    
    def cache_svgx_compilation(self, svgx_content: str, target_format: str, 
                              compiled_result: Any) -> str:
        """Cache compiled SVGX content with automatic key generation"""
        key = SVGXCacheKeyGenerator.generate_compilation_key(svgx_content, target_format)
        
        self.memory_cache.set(key, compiled_result, None, False, 
                            SVGXCacheType.SVGX_COMPILED)
        self.disk_cache.set(key, compiled_result, None, True, 
                           SVGXCacheType.SVGX_COMPILED)
        if self.database_cache:
            self.database_cache.set(key, compiled_result, None, True, 
                                  SVGXCacheType.SVGX_COMPILED)
        
        return key
    
    def invalidate_cache(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        import re
        
        pattern_re = re.compile(pattern)
        
        # Invalidate in memory cache
        keys_to_remove = [key for key in self.memory_cache.cache.keys() 
                         if pattern_re.match(key)]
        for key in keys_to_remove:
            self.memory_cache.delete(key)
        
        # Invalidate in disk cache
        keys_to_remove = [key for key in self.disk_cache.index.keys() 
                         if pattern_re.match(key)]
        for key in keys_to_remove:
            self.disk_cache.delete(key)
        
        # Invalidate in database cache
        if self.database_cache:
            try:
                # This is a simplified approach - in production you'd want more sophisticated pattern matching
                self.database_cache.conn.execute("""
                    DELETE FROM svgx_cache WHERE key LIKE ?
                """, (pattern.replace('*', '%'),))
                self.database_cache.conn.commit()
            except Exception as e:
                self.logger.error(f"Failed to invalidate database cache: {e}")
        
        self.logger.info("Cache invalidation completed", pattern=pattern)
    
    def invalidate_svgx_namespace(self, namespace: str):
        """Invalidate all cache entries for a specific SVGX namespace"""
        pattern = f"svgx:.*:{namespace}:.*"
        self.invalidate_cache(pattern)
    
    def invalidate_svgx_type(self, svgx_type: SVGXCacheType):
        """Invalidate all cache entries for a specific SVGX type"""
        pattern = f"svgx:{svgx_type.value}:.*"
        self.invalidate_cache(pattern)
    
    def precompute_common_operations(self, operations: List[Tuple[str, Callable]]):
        """Precompute common operations and cache results"""
        for key, computation_func in operations:
            try:
                self.get_cached_result(key, computation_func)
            except Exception as e:
                self.logger.error(f"Failed to precompute {key}: {e}")
    
    def warm_cache_for_svgx_symbols(self, symbol_ids: List[str], namespace: str = "default"):
        """Warm cache for commonly used SVGX symbols"""
        for symbol_id in symbol_ids:
            key = SVGXCacheKeyGenerator.generate_symbol_key(symbol_id, namespace)
            
            # Check if already cached
            if self.memory_cache.get(key) is None:
                # Simulate symbol loading (in real implementation, this would load from storage)
                symbol_data = {"symbol_id": symbol_id, "namespace": namespace, "data": "symbol_data"}
                self.cache_svgx_symbol(symbol_id, symbol_data, namespace)
    
    def _record_access_pattern(self, key: str, level: CacheLevel, access_time: float):
        """Record access pattern for optimization"""
        self.access_patterns[key].append({
            'level': level,
            'access_time': access_time,
            'timestamp': time.time()
        })
        
        # Keep only recent patterns
        if len(self.access_patterns[key]) > 100:
            self.access_patterns[key] = self.access_patterns[key][-50:]
    
    def get_cache_metrics(self) -> Dict[CacheLevel, CacheMetrics]:
        """Get metrics for all cache levels"""
        metrics = {
            CacheLevel.L1: self.memory_cache.get_metrics(),
            CacheLevel.L3: self.disk_cache.get_metrics()
        }
        
        if self.database_cache:
            metrics[CacheLevel.L4] = self.database_cache.get_metrics()
        
        return metrics
    
    def get_svgx_metrics(self) -> Dict[str, Any]:
        """Get SVGX-specific metrics"""
        memory_svgx = self.memory_cache.get_svgx_metrics()
        disk_svgx = self.disk_cache.get_svgx_metrics()
        
        # Combine metrics from all levels
        combined = defaultdict(int)
        for metrics in [memory_svgx, disk_svgx]:
            for key, value in metrics.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        combined[sub_key] += sub_value
                else:
                    combined[key] += value
        
        return {
            **dict(combined),
            'access_patterns': self.access_patterns
        }
    
    def get_overall_metrics(self) -> Dict[str, Any]:
        """Get overall cache performance metrics"""
        all_metrics = self.get_cache_metrics()
        
        total_hits = sum(metrics.hit_count for metrics in all_metrics.values())
        total_misses = sum(metrics.miss_count for metrics in all_metrics.values())
        total_requests = total_hits + total_misses
        
        overall_hit_rate = total_hits / total_requests if total_requests > 0 else 0.0
        
        return {
            'total_requests': total_requests,
            'total_hits': total_hits,
            'total_misses': total_misses,
            'overall_hit_rate': overall_hit_rate,
            'average_response_time_ms': sum(
                metrics.average_access_time_ms for metrics in all_metrics.values()
            ) / len(all_metrics) if all_metrics else 0.0,
            'svgx_metrics': self.get_svgx_metrics(),
            'access_patterns': len(self.access_patterns)
        }
    
    def optimize_cache_performance(self):
        """Optimize cache performance based on access patterns"""
        # Analyze access patterns and adjust cache policies
        for key, patterns in self.access_patterns.items():
            if len(patterns) > 10:
                avg_access_time = sum(p['access_time'] for p in patterns) / len(patterns)
                if avg_access_time > 100:  # Slow access
                    # Consider moving to faster cache level
                    pass
    
    def clear_all_caches(self):
        """Clear all cache levels"""
        self.memory_cache.clear()
        self.disk_cache.clear()
        if self.database_cache:
            self.database_cache.clear()
        
        self.access_patterns.clear()
        self.warming_queue.clear()
    
    def get_cache_size_info(self) -> Dict[str, Any]:
        """Get information about cache sizes"""
        memory_size = self.memory_cache._get_total_size()
        disk_size = self.disk_cache._get_total_size()
        db_size = self.database_cache._get_total_size() if self.database_cache else 0
        
        total_size = memory_size + disk_size + db_size
        
        return {
            'memory_cache': {
                'used_mb': memory_size / (1024 * 1024),
                'max_mb': self.memory_cache.max_size_bytes / (1024 * 1024),
                'utilization_percent': (memory_size / self.memory_cache.max_size_bytes) * 100
            },
            'disk_cache': {
                'used_mb': disk_size / (1024 * 1024),
                'max_mb': self.disk_cache.max_size_bytes / (1024 * 1024),
                'utilization_percent': (disk_size / self.disk_cache.max_size_bytes) * 100
            },
            'database_cache': {
                'used_mb': db_size / (1024 * 1024)
            } if self.database_cache else None,
            'total_size_mb': total_size / (1024 * 1024)
        } 