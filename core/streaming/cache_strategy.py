"""
Smart Caching Strategy for 14KB Architecture.

Implements hierarchical cache with intelligent eviction based on
the 14KB principle's caching strategy for optimal memory usage.
"""

import time
import logging
from typing import Dict, Any, Optional, List, Set, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import threading
from collections import defaultdict, OrderedDict
import weakref

logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """Hierarchical cache levels based on 14KB principle."""
    
    CRITICAL = "critical"    # Never evict: structural grid, major systems
    ACTIVE = "active"        # Current viewport objects
    NEARBY = "nearby"        # Adjacent spaces (small cache)
    TEMPORARY = "temporary"  # Short-term cache for streaming


@dataclass
class CacheEntry:
    """Cache entry with metadata for intelligent eviction."""
    
    key: str
    value: Any
    level: CacheLevel
    size_bytes: int
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    
    def update_access(self) -> None:
        """Update access statistics."""
        self.access_count += 1
        self.last_accessed = time.time()
    
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        return self.expires_at is not None and time.time() > self.expires_at
    
    def get_age_seconds(self) -> float:
        """Get entry age in seconds."""
        return time.time() - self.created_at
    
    def get_idle_time_seconds(self) -> float:
        """Get time since last access."""
        return time.time() - self.last_accessed


class EvictionPolicy(Enum):
    """Cache eviction policies."""
    
    LRU = "lru"              # Least Recently Used
    LFU = "lfu"              # Least Frequently Used  
    TTL = "ttl"              # Time To Live
    SIZE_AWARE = "size_aware" # Size-aware LRU
    ADAPTIVE = "adaptive"     # Adaptive policy based on usage patterns


class SmartCache:
    """
    Smart hierarchical cache for 14KB streaming architecture.
    
    Implements the caching strategy from the 14KB principle:
    - Critical: Never evict structural grid, major systems
    - Active: Current viewport objects
    - Nearby: Adjacent spaces with intelligent eviction
    - Temporary: Short-term streaming cache
    """
    
    def __init__(self, 
                 total_size_mb: int = 64,
                 eviction_threshold: float = 0.8,
                 eviction_policy: EvictionPolicy = EvictionPolicy.ADAPTIVE):
        """
        Initialize smart cache system.
        
        Args:
            total_size_mb: Total cache size in megabytes
            eviction_threshold: Eviction threshold (0.8 = 80% full)
            eviction_policy: Default eviction policy
        """
        self.total_size_bytes = total_size_mb * 1024 * 1024
        self.eviction_threshold = eviction_threshold
        self.eviction_policy = eviction_policy
        
        # Cache storage by level
        self.cache_levels: Dict[CacheLevel, Dict[str, CacheEntry]] = {
            level: OrderedDict() for level in CacheLevel
        }
        
        # Size limits by level (percentage of total)
        self.level_size_limits = {
            CacheLevel.CRITICAL: 0.3,    # 30% for critical objects
            CacheLevel.ACTIVE: 0.4,      # 40% for active viewport
            CacheLevel.NEARBY: 0.2,      # 20% for nearby objects
            CacheLevel.TEMPORARY: 0.1    # 10% for temporary streaming
        }
        
        # Current size tracking
        self.current_size_by_level: Dict[CacheLevel, int] = defaultdict(int)
        self.total_current_size = 0
        
        # Access pattern tracking for adaptive eviction
        self.access_patterns: Dict[str, List[float]] = defaultdict(list)
        self.pattern_window_size = 10  # Track last 10 accesses
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Performance metrics
        self.metrics = {
            'cache_hits': 0,
            'cache_misses': 0,
            'evictions': 0,
            'total_entries': 0,
            'size_utilization': 0.0,
            'hit_rate': 0.0
        }
        
        # Weak references for automatic cleanup
        self.weak_refs: Dict[str, weakref.ref] = {}
        
        logger.info(f"Initialized SmartCache: {total_size_mb}MB, "
                   f"eviction threshold: {eviction_threshold}, "
                   f"policy: {eviction_policy.value}")
    
    def put(self, 
            key: str, 
            value: Any, 
            level: CacheLevel,
            ttl_seconds: Optional[float] = None) -> bool:
        """
        Store value in cache at specified level.
        
        Args:
            key: Cache key
            value: Value to cache
            level: Cache level
            ttl_seconds: Time to live in seconds
            
        Returns:
            True if stored successfully
        """
        with self._lock:
            # Calculate size
            size_bytes = self._estimate_size(value)
            
            # Check if we need to evict
            if self._should_evict(level, size_bytes):
                self._evict_for_space(level, size_bytes)
            
            # Create cache entry
            expires_at = time.time() + ttl_seconds if ttl_seconds else None
            entry = CacheEntry(
                key=key,
                value=value,
                level=level,
                size_bytes=size_bytes,
                expires_at=expires_at
            )
            
            # Remove existing entry if it exists
            self._remove_entry(key)
            
            # Store entry
            self.cache_levels[level][key] = entry
            self.current_size_by_level[level] += size_bytes
            self.total_current_size += size_bytes
            
            # Update metrics
            self.metrics['total_entries'] += 1
            self._update_size_utilization()
            
            # Store weak reference if applicable
            if hasattr(value, '__weakref__'):
                try:
                    self.weak_refs[key] = weakref.ref(value, self._weak_ref_callback(key))
                except TypeError:
                    pass  # Object doesn't support weak references
            
            logger.debug(f"Cached {key} at level {level.value}, size: {size_bytes} bytes")
            return True
    
    def get(self, key: str, level: Optional[CacheLevel] = None) -> Optional[Any]:
        """
        Retrieve value from cache.
        
        Args:
            key: Cache key
            level: Optional level to search (searches all if None)
            
        Returns:
            Cached value or None if not found
        """
        with self._lock:
            # Search specified level or all levels
            levels_to_search = [level] if level else list(CacheLevel)
            
            for search_level in levels_to_search:
                cache = self.cache_levels[search_level]
                
                if key in cache:
                    entry = cache[key]
                    
                    # Check expiration
                    if entry.is_expired():
                        self._remove_entry(key)
                        continue
                    
                    # Update access patterns
                    entry.update_access()
                    self._update_access_pattern(key)
                    
                    # Move to end for LRU (OrderedDict behavior)
                    cache.move_to_end(key)
                    
                    # Update metrics
                    self.metrics['cache_hits'] += 1
                    self._update_hit_rate()
                    
                    logger.debug(f"Cache hit: {key} from level {search_level.value}")
                    return entry.value
            
            # Cache miss
            self.metrics['cache_misses'] += 1
            self._update_hit_rate()
            
            logger.debug(f"Cache miss: {key}")
            return None
    
    def remove(self, key: str) -> bool:
        """
        Remove entry from cache.
        
        Args:
            key: Cache key to remove
            
        Returns:
            True if entry was removed
        """
        with self._lock:
            return self._remove_entry(key)
    
    def _remove_entry(self, key: str) -> bool:
        """Internal method to remove entry from cache."""
        for level, cache in self.cache_levels.items():
            if key in cache:
                entry = cache[key]
                del cache[key]
                
                self.current_size_by_level[level] -= entry.size_bytes
                self.total_current_size -= entry.size_bytes
                self.metrics['total_entries'] -= 1
                
                # Clean up weak reference
                if key in self.weak_refs:
                    del self.weak_refs[key]
                
                # Clean up access patterns
                if key in self.access_patterns:
                    del self.access_patterns[key]
                
                self._update_size_utilization()
                
                logger.debug(f"Removed {key} from cache level {level.value}")
                return True
        
        return False
    
    def _should_evict(self, level: CacheLevel, new_entry_size: int) -> bool:
        """Determine if eviction is needed for new entry."""
        
        # Check total cache size
        total_after_add = self.total_current_size + new_entry_size
        if total_after_add > (self.total_size_bytes * self.eviction_threshold):
            return True
        
        # Check level-specific limits
        level_limit = int(self.total_size_bytes * self.level_size_limits[level])
        level_after_add = self.current_size_by_level[level] + new_entry_size
        
        return level_after_add > level_limit
    
    def _evict_for_space(self, target_level: CacheLevel, required_space: int) -> None:
        """Evict entries to make space for new entry."""
        
        # Never evict from CRITICAL level
        evictable_levels = [lvl for lvl in CacheLevel if lvl != CacheLevel.CRITICAL]
        
        # Start with temporary level, then nearby, then active
        eviction_order = [CacheLevel.TEMPORARY, CacheLevel.NEARBY, CacheLevel.ACTIVE]
        eviction_order = [lvl for lvl in eviction_order if lvl in evictable_levels]
        
        space_freed = 0
        
        for level in eviction_order:
            if space_freed >= required_space:
                break
            
            space_freed += self._evict_from_level(level, required_space - space_freed)
        
        logger.info(f"Evicted {space_freed} bytes to make space for {required_space} bytes")
    
    def _evict_from_level(self, level: CacheLevel, target_space: int) -> int:
        """Evict entries from specific level."""
        
        cache = self.cache_levels[level]
        if not cache:
            return 0
        
        space_freed = 0
        entries_to_remove = []
        
        if self.eviction_policy == EvictionPolicy.LRU:
            # Remove oldest entries first (OrderedDict maintains insertion order)
            for key, entry in cache.items():
                entries_to_remove.append(key)
                space_freed += entry.size_bytes
                if space_freed >= target_space:
                    break
        
        elif self.eviction_policy == EvictionPolicy.LFU:
            # Sort by access count (ascending)
            sorted_entries = sorted(cache.items(), key=lambda x: x[1].access_count)
            for key, entry in sorted_entries:
                entries_to_remove.append(key)
                space_freed += entry.size_bytes
                if space_freed >= target_space:
                    break
        
        elif self.eviction_policy == EvictionPolicy.SIZE_AWARE:
            # Prioritize larger, less frequently accessed entries
            def eviction_score(entry):
                return entry.size_bytes / max(entry.access_count, 1)
            
            sorted_entries = sorted(cache.items(), key=lambda x: eviction_score(x[1]), reverse=True)
            for key, entry in sorted_entries:
                entries_to_remove.append(key)
                space_freed += entry.size_bytes
                if space_freed >= target_space:
                    break
        
        elif self.eviction_policy == EvictionPolicy.ADAPTIVE:
            # Use adaptive strategy based on access patterns
            entries_with_scores = []
            for key, entry in cache.items():
                score = self._calculate_adaptive_score(key, entry)
                entries_with_scores.append((key, entry, score))
            
            # Sort by score (lower score = higher eviction priority)
            entries_with_scores.sort(key=lambda x: x[2])
            
            for key, entry, score in entries_with_scores:
                entries_to_remove.append(key)
                space_freed += entry.size_bytes
                if space_freed >= target_space:
                    break
        
        # Remove selected entries
        for key in entries_to_remove:
            self._remove_entry(key)
            self.metrics['evictions'] += 1
        
        logger.debug(f"Evicted {len(entries_to_remove)} entries from level {level.value}, "
                    f"freed {space_freed} bytes")
        
        return space_freed
    
    def _calculate_adaptive_score(self, key: str, entry: CacheEntry) -> float:
        """Calculate adaptive eviction score (lower = higher eviction priority)."""
        
        # Base factors
        age_weight = 0.3
        access_weight = 0.4
        size_weight = 0.2
        pattern_weight = 0.1
        
        # Age factor (older = higher eviction priority)
        age_seconds = entry.get_age_seconds()
        max_age = 3600  # 1 hour reference
        age_factor = min(age_seconds / max_age, 1.0)
        
        # Access frequency factor (less accessed = higher eviction priority)
        access_factor = 1.0 / (entry.access_count + 1)
        
        # Size factor (larger = higher eviction priority for same access pattern)
        avg_entry_size = self.total_current_size / max(self.metrics['total_entries'], 1)
        size_factor = entry.size_bytes / max(avg_entry_size, 1)
        
        # Access pattern factor (irregular access = higher eviction priority)
        pattern_factor = 1.0
        if key in self.access_patterns and len(self.access_patterns[key]) > 1:
            times = self.access_patterns[key]
            intervals = [times[i] - times[i-1] for i in range(1, len(times))]
            if intervals:
                # Calculate coefficient of variation for access intervals
                mean_interval = sum(intervals) / len(intervals)
                variance = sum((x - mean_interval)**2 for x in intervals) / len(intervals)
                cv = (variance**0.5) / mean_interval if mean_interval > 0 else 1.0
                pattern_factor = min(cv, 2.0)  # Cap at 2.0
        
        # Combine factors (lower score = higher eviction priority)
        score = (
            age_factor * age_weight +
            access_factor * access_weight + 
            size_factor * size_weight +
            pattern_factor * pattern_weight
        )
        
        return score
    
    def _update_access_pattern(self, key: str) -> None:
        """Update access pattern for adaptive eviction."""
        current_time = time.time()
        
        if key not in self.access_patterns:
            self.access_patterns[key] = []
        
        pattern = self.access_patterns[key]
        pattern.append(current_time)
        
        # Keep only recent accesses
        if len(pattern) > self.pattern_window_size:
            pattern.pop(0)
    
    def evict_level(self, level: CacheLevel) -> int:
        """
        Evict all entries from specified level.
        
        Args:
            level: Cache level to evict
            
        Returns:
            Number of entries evicted
        """
        if level == CacheLevel.CRITICAL:
            logger.warning("Cannot evict CRITICAL cache level")
            return 0
        
        with self._lock:
            cache = self.cache_levels[level]
            evicted_count = len(cache)
            
            # Clear all entries
            for key in list(cache.keys()):
                self._remove_entry(key)
                self.metrics['evictions'] += 1
            
            logger.info(f"Evicted all {evicted_count} entries from level {level.value}")
            return evicted_count
    
    def clear(self) -> None:
        """Clear entire cache."""
        with self._lock:
            for level in CacheLevel:
                if level != CacheLevel.CRITICAL:  # Preserve critical entries
                    self.cache_levels[level].clear()
                    self.current_size_by_level[level] = 0
            
            # Clear critical level separately (if needed)
            # self.cache_levels[CacheLevel.CRITICAL].clear()
            # self.current_size_by_level[CacheLevel.CRITICAL] = 0
            
            self.total_current_size = sum(self.current_size_by_level.values())
            self.access_patterns.clear()
            self.weak_refs.clear()
            
            self.metrics['total_entries'] = sum(len(cache) for cache in self.cache_levels.values())
            self._update_size_utilization()
            
            logger.info("Cache cleared (preserved CRITICAL level)")
    
    def cleanup_expired(self) -> int:
        """Remove expired entries from cache."""
        with self._lock:
            expired_keys = []
            
            for level, cache in self.cache_levels.items():
                for key, entry in cache.items():
                    if entry.is_expired():
                        expired_keys.append(key)
            
            for key in expired_keys:
                self._remove_entry(key)
            
            logger.debug(f"Cleaned up {len(expired_keys)} expired entries")
            return len(expired_keys)
    
    def _estimate_size(self, value: Any) -> int:
        """Estimate size of cached value in bytes."""
        try:
            if isinstance(value, (str, bytes)):
                return len(value.encode('utf-8')) if isinstance(value, str) else len(value)
            elif isinstance(value, (dict, list)):
                return len(json.dumps(value).encode('utf-8'))
            else:
                # Rough estimate based on string representation
                return len(str(value).encode('utf-8'))
        except Exception:
            return 1024  # Default estimate: 1KB
    
    def _update_size_utilization(self) -> None:
        """Update size utilization metric."""
        self.metrics['size_utilization'] = self.total_current_size / self.total_size_bytes
    
    def _update_hit_rate(self) -> None:
        """Update cache hit rate metric."""
        total_requests = self.metrics['cache_hits'] + self.metrics['cache_misses']
        if total_requests > 0:
            self.metrics['hit_rate'] = self.metrics['cache_hits'] / total_requests
    
    def _weak_ref_callback(self, key: str):
        """Create weak reference callback for automatic cleanup."""
        def callback(ref):
            with self._lock:
                if key in self.weak_refs and self.weak_refs[key] is ref:
                    del self.weak_refs[key]
                    # Optionally remove from cache if object is garbage collected
                    # self._remove_entry(key)
        return callback
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive cache status."""
        with self._lock:
            level_stats = {}
            
            for level, cache in self.cache_levels.items():
                level_limit = int(self.total_size_bytes * self.level_size_limits[level])
                current_size = self.current_size_by_level[level]
                
                level_stats[level.value] = {
                    'entries': len(cache),
                    'size_bytes': current_size,
                    'size_limit_bytes': level_limit,
                    'utilization_percent': (current_size / level_limit * 100) if level_limit > 0 else 0
                }
            
            return {
                'total_size_bytes': self.total_size_bytes,
                'current_size_bytes': self.total_current_size,
                'utilization_percent': self.metrics['size_utilization'] * 100,
                'eviction_threshold_percent': self.eviction_threshold * 100,
                'level_statistics': level_stats,
                'performance_metrics': self.metrics.copy(),
                'eviction_policy': self.eviction_policy.value,
                'weak_references': len(self.weak_refs)
            }