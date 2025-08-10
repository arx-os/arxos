"""
14KB Streaming Engine Core.

Main orchestrator for the 14KB principle implementation, managing
progressive loading, viewport-based queries, and intelligent caching
for ultra-lightweight BIM experience.
"""

import asyncio
import time
import json
import logging
from typing import Dict, Any, List, Optional, Set, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor
import weakref

# Import from our Phase 1 foundation
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.spatial import SpatialConflictEngine, ArxObject, BoundingBox3D, BoundingBox2D
from .progressive_disclosure import ProgressiveDisclosure, LODLevel
from .viewport_manager import ViewportManager, ViewportBounds
from .cache_strategy import SmartCache, CacheLevel
from .differential_compression import DifferentialCompression
from .binary_optimization import BinaryOptimizer

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """User roles for code splitting optimization."""
    CONSTRUCTION_WORKER = "construction_worker"     # 8KB bundle
    SUPERINTENDENT = "superintendent"               # 12KB bundle  
    ARCHITECT = "architect"                        # 14KB bundle
    FULL_FEATURED = "full_featured"                # Unlimited, streaming


@dataclass
class StreamingConfig:
    """Configuration for 14KB streaming engine."""
    
    # Bundle size limits by user role (in bytes)
    bundle_limits: Dict[UserRole, int] = field(default_factory=lambda: {
        UserRole.CONSTRUCTION_WORKER: 8 * 1024,   # 8KB
        UserRole.SUPERINTENDENT: 12 * 1024,       # 12KB
        UserRole.ARCHITECT: 14 * 1024,            # 14KB
        UserRole.FULL_FEATURED: float('inf')      # No limit
    })
    
    # Viewport buffer zones (Level of Detail)
    viewport_buffer_lod: float = 1.5  # 1.5x viewport size
    
    # Progressive disclosure levels
    max_lod_levels: int = 4
    base_lod_size: int = 2048  # 2KB for Level 0
    
    # Cache configuration
    cache_total_size_mb: int = 64  # 64MB total cache
    cache_eviction_threshold: float = 0.8  # Evict when 80% full
    
    # Network optimization
    chunk_size_bytes: int = 4096  # 4KB chunks
    max_concurrent_requests: int = 6
    request_timeout_seconds: int = 30
    
    # Compression settings
    enable_differential_compression: bool = True
    enable_binary_optimization: bool = True
    compression_threshold_bytes: int = 512  # Compress objects > 512 bytes


class StreamingEngine:
    """
    14KB Streaming Engine for ultra-lightweight BIM experience.
    
    Orchestrates progressive loading, viewport management, differential
    compression, and intelligent caching to maintain 14KB bundle limits
    while providing full BIM functionality through streaming.
    """
    
    def __init__(self, 
                 spatial_engine: SpatialConflictEngine,
                 config: Optional[StreamingConfig] = None,
                 user_role: UserRole = UserRole.ARCHITECT):
        """
        Initialize 14KB streaming engine.
        
        Args:
            spatial_engine: Phase 1 spatial conflict engine
            config: Streaming configuration
            user_role: User role for bundle optimization
        """
        self.spatial_engine = spatial_engine
        self.config = config or StreamingConfig()
        self.user_role = user_role
        
        # Core components
        self.progressive_disclosure = ProgressiveDisclosure(
            max_levels=self.config.max_lod_levels,
            base_size=self.config.base_lod_size
        )
        
        self.viewport_manager = ViewportManager(
            buffer_factor=self.config.viewport_buffer_lod
        )
        
        self.cache = SmartCache(
            total_size_mb=self.config.cache_total_size_mb,
            eviction_threshold=self.config.cache_eviction_threshold
        )
        
        self.diff_compression = DifferentialCompression()
        
        self.binary_optimizer = BinaryOptimizer(
            compression_level=6,
            enable_quantization=True
        )
        
        # Streaming state
        self.active_viewport: Optional[ViewportBounds] = None
        self.loaded_objects: Set[str] = set()
        self.streaming_objects: Set[str] = set()  # Currently loading
        self.object_references: Dict[str, weakref.ref] = {}
        
        # Performance tracking
        self.metrics = {
            'bundle_size_bytes': 0,
            'cache_hit_rate': 0.0,
            'average_load_time_ms': 0.0,
            'objects_streamed': 0,
            'compression_ratio': 0.0,
            'viewport_queries': 0
        }
        
        # Async infrastructure  
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_requests)
        self.event_loop = None
        self._shutdown_event = asyncio.Event()
        
        # Network simulation (in production, this would be real HTTP client)
        self._network_delay_ms = 50  # Simulate 50ms network latency
        
        logger.info(f"Initialized StreamingEngine for role: {user_role.value}, "
                   f"bundle limit: {self.config.bundle_limits[user_role]} bytes")
    
    async def initialize(self) -> None:
        """Initialize async components."""
        self.event_loop = asyncio.get_event_loop()
        
        # Pre-load critical objects based on user role
        await self._preload_critical_objects()
        
        logger.info("StreamingEngine initialized with async components")
    
    async def set_viewport(self, viewport: ViewportBounds) -> Dict[str, Any]:
        """
        Set active viewport and trigger progressive loading.
        
        Args:
            viewport: New viewport bounds
            
        Returns:
            Dictionary with loaded objects and metadata
        """
        start_time = time.time()
        
        self.active_viewport = viewport
        self.metrics['viewport_queries'] += 1
        
        # Determine required LOD level based on viewport size and zoom
        lod_level = self._calculate_lod_level(viewport)
        
        # Get spatial query bounds (viewport + buffer)
        query_bounds = self.viewport_manager.get_query_bounds(viewport)
        
        # Check cache first
        cache_key = self.viewport_manager.get_cache_key(viewport, lod_level)
        cached_result = self.cache.get(cache_key, CacheLevel.ACTIVE)
        
        if cached_result:
            self.metrics['cache_hit_rate'] = (self.metrics['cache_hit_rate'] + 1.0) / 2
            logger.debug(f"Viewport cache hit for {cache_key}")
            return cached_result
        
        # Progressive disclosure: load by LOD level
        result = await self._load_viewport_progressive(query_bounds, lod_level)
        
        # Cache the result
        self.cache.put(cache_key, result, CacheLevel.ACTIVE)
        
        # Update metrics
        elapsed_ms = (time.time() - start_time) * 1000
        self.metrics['average_load_time_ms'] = (
            (self.metrics['average_load_time_ms'] + elapsed_ms) / 2
        )
        
        logger.info(f"Set viewport {viewport.width}x{viewport.height} at LOD {lod_level.value}, "
                   f"loaded {len(result.get('objects', []))} objects in {elapsed_ms:.1f}ms")
        
        return result
    
    async def _load_viewport_progressive(self, 
                                       query_bounds: BoundingBox3D, 
                                       lod_level: LODLevel) -> Dict[str, Any]:
        """Load viewport objects progressively by LOD level."""
        
        # Level 0: Critical objects (structural grid, major systems)
        level_0_objects = await self._load_lod_level(query_bounds, LODLevel.BUILDING_OUTLINE)
        
        if lod_level == LODLevel.BUILDING_OUTLINE:
            return self._format_viewport_result(level_0_objects, LODLevel.BUILDING_OUTLINE)
        
        # Level 1: Room layouts + primary MEP
        level_1_objects = await self._load_lod_level(query_bounds, LODLevel.ROOM_LAYOUT)
        all_objects = level_0_objects + level_1_objects
        
        if lod_level == LODLevel.ROOM_LAYOUT:
            return self._format_viewport_result(all_objects, LODLevel.ROOM_LAYOUT)
        
        # Level 2: Detailed components
        level_2_objects = await self._load_lod_level(query_bounds, LODLevel.DETAILED_COMPONENTS)
        all_objects.extend(level_2_objects)
        
        if lod_level == LODLevel.DETAILED_COMPONENTS:
            return self._format_viewport_result(all_objects, LODLevel.DETAILED_COMPONENTS)
        
        # Level 3+: Conflict zones + full details
        level_3_objects = await self._load_lod_level(query_bounds, LODLevel.CONFLICT_ZONES)
        all_objects.extend(level_3_objects)
        
        return self._format_viewport_result(all_objects, LODLevel.CONFLICT_ZONES)
    
    async def _load_lod_level(self, 
                             bounds: BoundingBox3D, 
                             lod_level: LODLevel) -> List[Dict[str, Any]]:
        """Load objects for specific LOD level."""
        
        # Query spatial engine for objects in bounds
        candidate_objects = self.spatial_engine.octree.query_range(bounds)
        
        # Filter objects by LOD level criteria
        filtered_objects = self._filter_objects_by_lod(candidate_objects, lod_level)
        
        # Load objects with differential compression
        loaded_objects = []
        
        for arxobject in filtered_objects:
            if arxobject.id not in self.loaded_objects:
                # Simulate async loading with compression
                compressed_obj = await self._load_object_compressed(arxobject)
                loaded_objects.append(compressed_obj)
                self.loaded_objects.add(arxobject.id)
                self.metrics['objects_streamed'] += 1
            else:
                # Object already loaded, use reference
                cached_obj = self.cache.get(arxobject.id, CacheLevel.NEARBY)
                if cached_obj:
                    loaded_objects.append(cached_obj)
        
        logger.debug(f"Loaded {len(loaded_objects)} objects for LOD {lod_level.value}")
        return loaded_objects
    
    def _filter_objects_by_lod(self, objects: List[ArxObject], lod_level: LODLevel) -> List[ArxObject]:
        """Filter objects based on LOD level criteria."""
        
        if lod_level == LODLevel.BUILDING_OUTLINE:
            # Only structural grid and major systems
            return [obj for obj in objects if obj.get_system_priority() <= 2]
        
        elif lod_level == LODLevel.ROOM_LAYOUT:
            # Add primary MEP systems
            return [obj for obj in objects if obj.get_system_priority() <= 3]
        
        elif lod_level == LODLevel.DETAILED_COMPONENTS:
            # Include all systems except finishes
            return [obj for obj in objects if obj.get_system_priority() <= 4]
        
        else:  # CONFLICT_ZONES and above
            # All objects
            return objects
    
    async def _load_object_compressed(self, arxobject: ArxObject) -> Dict[str, Any]:
        """Load object with differential compression."""
        
        # Simulate network delay
        await asyncio.sleep(self._network_delay_ms / 1000.0)
        
        # Convert ArxObject to dictionary
        object_dict = arxobject.to_dict()
        
        # Apply binary optimization first
        if self.config.enable_binary_optimization:
            object_dict = self.binary_optimizer.optimize_arxobject(object_dict)
        
        # Apply differential compression
        if self.config.enable_differential_compression:
            compressed_data = self.diff_compression.compress_object(object_dict)
            
            # Update compression metrics
            original_size = len(json.dumps(arxobject.to_dict()).encode())
            compressed_size = len(json.dumps(compressed_data).encode())
            
            if original_size > 0:
                ratio = compressed_size / original_size
                self.metrics['compression_ratio'] = (
                    (self.metrics['compression_ratio'] + ratio) / 2
                )
        else:
            compressed_data = object_dict
        
        # Store weak reference for memory management
        self.object_references[arxobject.id] = weakref.ref(arxobject)
        
        return compressed_data
    
    def _calculate_lod_level(self, viewport: ViewportBounds) -> LODLevel:
        """Calculate required LOD level based on viewport characteristics."""
        
        # Simple heuristic: smaller viewport = higher detail
        viewport_area = viewport.width * viewport.height
        
        if viewport_area < 100:  # Very detailed view
            return LODLevel.CONFLICT_ZONES
        elif viewport_area < 1000:  # Moderate detail
            return LODLevel.DETAILED_COMPONENTS  
        elif viewport_area < 10000:  # Room level
            return LODLevel.ROOM_LAYOUT
        else:  # Building overview
            return LODLevel.BUILDING_OUTLINE
    
    def _format_viewport_result(self, objects: List[Dict[str, Any]], 
                              lod_level: LODLevel) -> Dict[str, Any]:
        """Format viewport loading result."""
        
        return {
            'lod_level': lod_level.value,
            'objects': objects,
            'object_count': len(objects),
            'bundle_size_estimate': self._estimate_bundle_size(objects),
            'viewport_bounds': self.active_viewport.to_dict() if self.active_viewport else None,
            'loaded_at': time.time(),
            'streaming_metadata': {
                'compression_enabled': self.config.enable_differential_compression,
                'cache_status': self.cache.get_status(),
                'user_role': self.user_role.value
            }
        }
    
    def _estimate_bundle_size(self, objects: List[Dict[str, Any]]) -> int:
        """Estimate bundle size for objects."""
        total_size = 0
        
        for obj in objects:
            obj_size = len(json.dumps(obj).encode('utf-8'))
            total_size += obj_size
        
        self.metrics['bundle_size_bytes'] = total_size
        return total_size
    
    async def _preload_critical_objects(self) -> None:
        """Pre-load critical objects based on user role."""
        
        # Get all objects from spatial engine
        all_objects = list(self.spatial_engine.objects.values())
        
        # Filter critical objects based on user role
        critical_objects = []
        
        if self.user_role == UserRole.CONSTRUCTION_WORKER:
            # Only structural and life safety
            critical_objects = [obj for obj in all_objects if obj.get_system_priority() <= 2]
        
        elif self.user_role == UserRole.SUPERINTENDENT:
            # Add MEP systems
            critical_objects = [obj for obj in all_objects if obj.get_system_priority() <= 3]
        
        else:  # ARCHITECT and FULL_FEATURED
            # All systems except finishes
            critical_objects = [obj for obj in all_objects if obj.get_system_priority() <= 4]
        
        # Load critical objects into cache
        for obj in critical_objects[:50]:  # Limit to first 50 for demo
            compressed_obj = await self._load_object_compressed(obj)
            self.cache.put(obj.id, compressed_obj, CacheLevel.CRITICAL)
        
        logger.info(f"Pre-loaded {len(critical_objects)} critical objects for {self.user_role.value}")
    
    async def stream_object(self, object_id: str) -> Optional[Dict[str, Any]]:
        """Stream individual object on-demand."""
        
        if object_id in self.loaded_objects:
            # Return cached object
            cached_obj = self.cache.get(object_id, CacheLevel.NEARBY)
            if cached_obj:
                return cached_obj
        
        # Check if object exists in spatial engine
        if object_id not in self.spatial_engine.objects:
            logger.warning(f"Object {object_id} not found in spatial engine")
            return None
        
        # Load object
        arxobject = self.spatial_engine.objects[object_id]
        compressed_obj = await self._load_object_compressed(arxobject)
        
        # Cache object
        self.cache.put(object_id, compressed_obj, CacheLevel.NEARBY)
        self.loaded_objects.add(object_id)
        
        logger.debug(f"Streamed object {object_id}")
        return compressed_obj
    
    async def detect_conflicts_streaming(self, viewport: ViewportBounds) -> Dict[str, Any]:
        """Detect conflicts in viewport with streaming optimization."""
        
        start_time = time.time()
        
        # Get objects in viewport
        query_bounds = self.viewport_manager.get_query_bounds(viewport)
        viewport_objects = self.spatial_engine.octree.query_range(query_bounds)
        
        if not viewport_objects:
            return {'conflicts': [], 'processing_time_ms': 0}
        
        # Run conflict detection on subset
        conflicts = []
        for obj in viewport_objects[:100]:  # Limit for streaming performance
            obj_conflicts = self.spatial_engine.detect_conflicts(obj)
            conflicts.extend(obj_conflicts)
        
        # Format conflicts for streaming
        streaming_conflicts = []
        for conflict in conflicts[:20]:  # Limit response size
            streaming_conflicts.append({
                'id': f"{conflict.object1_id}_{conflict.object2_id}",
                'type': conflict.conflict_type.value,
                'severity': conflict.severity,
                'description': conflict.description,
                'distance': conflict.distance,
                'resolution_available': bool(conflict.resolution_strategy)
            })
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        return {
            'conflicts': streaming_conflicts,
            'total_conflicts': len(conflicts),
            'viewport_objects': len(viewport_objects),
            'processing_time_ms': elapsed_ms,
            'streaming_metadata': {
                'limited_response': len(conflicts) > 20,
                'full_analysis_available': True
            }
        }
    
    def get_bundle_status(self) -> Dict[str, Any]:
        """Get current bundle size status and optimization metrics."""
        
        role_limit = self.config.bundle_limits[self.user_role]
        current_size = self.metrics['bundle_size_bytes']
        
        return {
            'user_role': self.user_role.value,
            'bundle_limit_bytes': role_limit,
            'current_bundle_size': current_size,
            'utilization_percent': (current_size / role_limit) * 100 if role_limit != float('inf') else 0,
            'objects_loaded': len(self.loaded_objects),
            'objects_streaming': len(self.streaming_objects),
            'cache_status': self.cache.get_status(),
            'performance_metrics': self.metrics.copy(),
            'optimization_suggestions': self._get_optimization_suggestions()
        }
    
    def _get_optimization_suggestions(self) -> List[str]:
        """Get optimization suggestions based on current state."""
        suggestions = []
        
        role_limit = self.config.bundle_limits[self.user_role]
        current_size = self.metrics['bundle_size_bytes']
        utilization = (current_size / role_limit) if role_limit != float('inf') else 0
        
        if utilization > 0.8:
            suggestions.append("Bundle size approaching limit - consider reducing LOD level")
        
        if self.metrics['cache_hit_rate'] < 0.5:
            suggestions.append("Low cache hit rate - consider adjusting viewport navigation patterns")
        
        if self.metrics['compression_ratio'] > 0.8:
            suggestions.append("Poor compression ratio - check for object similarity optimization")
        
        if len(self.loaded_objects) > 1000:
            suggestions.append("Many objects loaded - consider implementing object eviction")
        
        return suggestions
    
    async def optimize_bundle(self) -> Dict[str, Any]:
        """Optimize current bundle size and performance."""
        
        start_time = time.time()
        optimization_actions = []
        
        # 1. Evict non-critical cached objects
        evicted_count = self.cache.evict_level(CacheLevel.NEARBY)
        if evicted_count > 0:
            optimization_actions.append(f"Evicted {evicted_count} nearby objects from cache")
        
        # 2. Compress loaded objects if not already compressed
        if not self.config.enable_differential_compression:
            self.config.enable_differential_compression = True
            optimization_actions.append("Enabled differential compression")
        
        # 3. Clear loaded objects not in current viewport
        if self.active_viewport:
            query_bounds = self.viewport_manager.get_query_bounds(self.active_viewport)
            viewport_objects = self.spatial_engine.octree.query_range(query_bounds)
            viewport_ids = {obj.id for obj in viewport_objects}
            
            objects_to_unload = self.loaded_objects - viewport_ids
            for obj_id in objects_to_unload:
                self.loaded_objects.discard(obj_id)
                if obj_id in self.object_references:
                    del self.object_references[obj_id]
            
            if objects_to_unload:
                optimization_actions.append(f"Unloaded {len(objects_to_unload)} objects outside viewport")
        
        # 4. Force garbage collection of weak references
        import gc
        gc.collect()
        optimization_actions.append("Performed garbage collection")
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        return {
            'optimization_completed': True,
            'actions_taken': optimization_actions,
            'processing_time_ms': elapsed_ms,
            'bundle_status_after': self.get_bundle_status()
        }
    
    async def shutdown(self) -> None:
        """Shutdown streaming engine gracefully."""
        logger.info("Shutting down StreamingEngine...")
        
        self._shutdown_event.set()
        
        # Clear caches and references
        self.cache.clear()
        self.loaded_objects.clear()
        self.streaming_objects.clear()
        self.object_references.clear()
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        logger.info("StreamingEngine shutdown complete")
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)