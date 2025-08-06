"""
Intelligent Caching System for MCP Rule Validation

This module provides intelligent caching capabilities:
- MD5 hashing for cache keys
- Pickle serialization for complex objects
- LRU cache eviction
- Cache performance monitoring
- Automatic cache invalidation
"""

import hashlib
import pickle
import time
import threading
import os
import tempfile
from typing import Dict, Any, Optional, Tuple, List
from collections import OrderedDict
import logging
import json


class CacheEntry:
    """Cache entry with metadata"""

    def __init__(self, key: str, value: Any, timestamp: float, size: int):
        self.key = key
        self.value = value
        self.timestamp = timestamp
        self.size = size
        self.access_count = 0
        self.last_access = timestamp

    def access(self):
        """Record cache access"""
        self.access_count += 1
        self.last_access = time.time()


class CacheManager:
    """
    Intelligent caching system for MCP validation

    Features:
    - MD5 hashing for cache keys
    - Pickle serialization
    - LRU eviction
    - Performance monitoring
    - Automatic cleanup
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize cache manager

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Cache settings
        self.max_cache_size = self.config.get("max_cache_size", 1000)
        self.max_cache_memory_mb = self.config.get("max_cache_memory_mb", 512)
        self.cache_ttl_seconds = self.config.get("cache_ttl_seconds", 3600)  # 1 hour
        self.enable_persistence = self.config.get("enable_persistence", False)
        self.cache_directory = self.config.get("cache_directory", tempfile.gettempdir())

        # Cache storage
        self.memory_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.disk_cache_enabled = self.enable_persistence and os.path.exists(
            self.cache_directory
        )

        # Performance metrics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.total_size = 0

        # Thread safety
        self._lock = threading.Lock()

        # Load persistent cache if enabled
        if self.disk_cache_enabled:
            self._load_persistent_cache()

        self.logger.info(
            f"Cache Manager initialized (memory: {self.max_cache_size} entries, "
            f"disk: {self.disk_cache_enabled})"
        )

    def _generate_cache_key(self, *args, **kwargs) -> str:
        """Generate MD5 hash for cache key"""
        # Create a deterministic string representation
        key_data = {"args": args, "kwargs": sorted(kwargs.items())}

        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode("utf-8")).hexdigest()

    def _serialize_value(self, value: Any) -> Tuple[bytes, int]:
        """Serialize value using pickle"""
        serialized = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
        size = len(serialized)
        return serialized, size

    def _deserialize_value(self, serialized: bytes) -> Any:
        """Deserialize value using pickle"""
        return pickle.loads(serialized)

    def _get_cache_file_path(self, key: str) -> str:
        """Get file path for disk cache entry"""
        return os.path.join(self.cache_directory, f"mcp_cache_{key}.pkl")

    def _save_to_disk(self, key: str, value: Any):
        """Save cache entry to disk"""
        if not self.disk_cache_enabled:
            return

        try:
            file_path = self._get_cache_file_path(key)
            serialized, size = self._serialize_value(value)

            with open(file_path, "wb") as f:
                f.write(serialized)

            # Save metadata
            metadata = {"timestamp": time.time(), "size": size, "access_count": 0}

            metadata_path = file_path.replace(".pkl", ".meta")
            with open(metadata_path, "w") as f:
                json.dump(metadata, f)

        except Exception as e:
            self.logger.error(f"Failed to save cache entry to disk: {e}")

    def _load_from_disk(self, key: str) -> Optional[Any]:
        """Load cache entry from disk"""
        if not self.disk_cache_enabled:
            return None

        try:
            file_path = self._get_cache_file_path(key)
            if not os.path.exists(file_path):
                return None

            with open(file_path, "rb") as f:
                serialized = f.read()

            return self._deserialize_value(serialized)

        except Exception as e:
            self.logger.error(f"Failed to load cache entry from disk: {e}")
            return None

    def _load_persistent_cache(self):
        """Load persistent cache entries"""
        if not self.disk_cache_enabled:
            return

        try:
            cache_files = [
                f
                for f in os.listdir(self.cache_directory)
                if f.startswith("mcp_cache_") and f.endswith(".pkl")
            ]

            for cache_file in cache_files:
                key = cache_file.replace("mcp_cache_", "").replace(".pkl", "")

                # Check if entry is still valid
                metadata_path = os.path.join(
                    self.cache_directory, cache_file.replace(".pkl", ".meta")
                )
                if os.path.exists(metadata_path):
                    with open(metadata_path, "r") as f:
                        metadata = json.load(f)

                    # Check TTL
                    if time.time() - metadata["timestamp"] > self.cache_ttl_seconds:
                        self._remove_from_disk(key)
                        continue

                # Load into memory cache
                value = self._load_from_disk(key)
                if value is not None:
                    self._add_to_memory_cache(key, value, metadata.get("size", 0))

            self.logger.info(f"Loaded {len(cache_files)} persistent cache entries")

        except Exception as e:
            self.logger.error(f"Failed to load persistent cache: {e}")

    def _remove_from_disk(self, key: str):
        """Remove cache entry from disk"""
        if not self.disk_cache_enabled:
            return

        try:
            file_path = self._get_cache_file_path(key)
            metadata_path = file_path.replace(".pkl", ".meta")

            if os.path.exists(file_path):
                os.remove(file_path)
            if os.path.exists(metadata_path):
                os.remove(metadata_path)

        except Exception as e:
            self.logger.error(f"Failed to remove cache entry from disk: {e}")

    def _add_to_memory_cache(self, key: str, value: Any, size: int):
        """Add entry to memory cache with LRU eviction"""
        with self._lock:
            # Check if we need to evict entries
            while (
                len(self.memory_cache) >= self.max_cache_size
                or self.total_size + size > self.max_cache_memory_mb * 1024 * 1024
            ):
                self._evict_lru_entry()

            # Add new entry
            entry = CacheEntry(key, value, time.time(), size)
            self.memory_cache[key] = entry
            self.total_size += size

    def _evict_lru_entry(self):
        """Evict least recently used cache entry"""
        if not self.memory_cache:
            return

        # Find LRU entry
        lru_key = None
        lru_time = float("inf")

        for key, entry in self.memory_cache.items():
            if entry.last_access < lru_time:
                lru_time = entry.last_access
                lru_key = key

        if lru_key:
            entry = self.memory_cache.pop(lru_key)
            self.total_size -= entry.size
            self.evictions += 1

            # Remove from disk if persistent
            if self.disk_cache_enabled:
                self._remove_from_disk(lru_key)

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        # Try memory cache first
        with self._lock:
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                entry.access()

                # Move to end (most recently used)
                self.memory_cache.move_to_end(key)

                self.hits += 1
                return entry.value

        # Try disk cache
        if self.disk_cache_enabled:
            value = self._load_from_disk(key)
            if value is not None:
                # Add to memory cache
                serialized, size = self._serialize_value(value)
                self._add_to_memory_cache(key, value, size)

                self.hits += 1
                return value

        self.misses += 1
        return default

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache"""
        serialized, size = self._serialize_value(value)

        # Add to memory cache
        self._add_to_memory_cache(key, value, size)

        # Save to disk if persistent
        if self.disk_cache_enabled:
            self._save_to_disk(key, value)

    def delete(self, key: str):
        """Delete cache entry"""
        with self._lock:
            if key in self.memory_cache:
                entry = self.memory_cache.pop(key)
                self.total_size -= entry.size

        if self.disk_cache_enabled:
            self._remove_from_disk(key)

    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self.memory_cache.clear()
            self.total_size = 0

        if self.disk_cache_enabled:
            # Clear disk cache
            try:
                cache_files = [
                    f
                    for f in os.listdir(self.cache_directory)
                    if f.startswith("mcp_cache_")
                ]

                for cache_file in cache_files:
                    file_path = os.path.join(self.cache_directory, cache_file)
                    os.remove(file_path)

            except Exception as e:
                self.logger.error(f"Failed to clear disk cache: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            hit_rate = self.hits / max(1, self.hits + self.misses)

            return {
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "evictions": self.evictions,
                "memory_entries": len(self.memory_cache),
                "memory_size_mb": self.total_size / 1024 / 1024,
                "max_memory_mb": self.max_cache_memory_mb,
                "disk_cache_enabled": self.disk_cache_enabled,
            }

    def optimize_cache_settings(self) -> Dict[str, Any]:
        """Dynamically optimize cache settings based on usage patterns"""
        stats = self.get_cache_stats()
        recommendations = []

        # Check hit rate
        if stats["hit_rate"] < 0.5:
            recommendations.append(
                "Low cache hit rate - consider increasing cache size"
            )
            self.max_cache_size = min(10000, self.max_cache_size * 2)

        # Check memory usage
        if stats["memory_size_mb"] > self.max_cache_memory_mb * 0.8:
            recommendations.append("High memory usage - consider reducing cache size")
            self.max_cache_size = max(100, self.max_cache_size // 2)

        # Check eviction rate
        if stats["evictions"] > stats["hits"] * 0.1:
            recommendations.append(
                "High eviction rate - consider increasing cache size"
            )
            self.max_cache_size = min(10000, self.max_cache_size * 2)

        return {
            "recommendations": recommendations,
            "optimized_settings": {
                "max_cache_size": self.max_cache_size,
                "max_cache_memory_mb": self.max_cache_memory_mb,
            },
            "current_stats": stats,
        }


class CachedRuleEngine:
    """Cache-optimized wrapper for MCP rule engine"""

    def __init__(self, base_engine, cache_manager: CacheManager):
        self.base_engine = base_engine
        self.cache_manager = cache_manager
        self.logger = logging.getLogger(__name__)

    def validate_building_model(self, building_model, mcp_files):
        """Validate building model with caching"""
        # Generate cache key
        cache_key = self.cache_manager._generate_cache_key(
            building_model.building_id,
            len(building_model.objects),
            [f.path for f in mcp_files] if hasattr(mcp_files[0], "path") else mcp_files,
        )

        # Try to get from cache
        cached_result = self.cache_manager.get(cache_key)
        if cached_result is not None:
            self.logger.info(f"Cache hit for building {building_model.building_id}")
            return cached_result

        # Perform validation
        self.logger.info(
            f"Cache miss for building {building_model.building_id}, performing validation"
        )
        result = self.base_engine.validate_building_model(building_model, mcp_files)

        # Cache result
        self.cache_manager.set(cache_key, result)

        return result

    def get_cache_metrics(self):
        """Get cache performance metrics"""
        return self.cache_manager.get_cache_stats()
