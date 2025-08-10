"""
Viewport Manager for 14KB Streaming Architecture.

Manages viewport bounds, spatial queries, and lazy loading triggers
for progressive disclosure of building components based on user view.
"""

import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib
import json

# Import from Phase 1 foundation
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.spatial import BoundingBox3D, BoundingBox2D

logger = logging.getLogger(__name__)


@dataclass
class ViewportBounds:
    """3D viewport bounds for spatial queries."""
    
    center_x: float
    center_y: float
    center_z: float
    width: float
    height: float
    depth: float
    zoom_level: int = 1
    rotation_angle: float = 0.0  # Degrees
    
    def to_bounding_box_3d(self) -> BoundingBox3D:
        """Convert to BoundingBox3D for spatial queries."""
        half_width = self.width / 2
        half_height = self.height / 2
        half_depth = self.depth / 2
        
        return BoundingBox3D(
            min_x=self.center_x - half_width,
            max_x=self.center_x + half_width,
            min_y=self.center_y - half_height,
            max_y=self.center_y + half_height,
            min_z=self.center_z - half_depth,
            max_z=self.center_z + half_depth
        )
    
    def to_bounding_box_2d(self) -> BoundingBox2D:
        """Convert to BoundingBox2D for plan view queries."""
        half_width = self.width / 2
        half_height = self.height / 2
        
        return BoundingBox2D(
            min_x=self.center_x - half_width,
            max_x=self.center_x + half_width,
            min_y=self.center_y - half_height,
            max_y=self.center_y + half_height
        )
    
    def get_area(self) -> float:
        """Calculate viewport area."""
        return self.width * self.height
    
    def get_volume(self) -> float:
        """Calculate viewport volume."""
        return self.width * self.height * self.depth
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'center': {'x': self.center_x, 'y': self.center_y, 'z': self.center_z},
            'dimensions': {'width': self.width, 'height': self.height, 'depth': self.depth},
            'zoom_level': self.zoom_level,
            'rotation_angle': self.rotation_angle,
            'area': self.get_area(),
            'volume': self.get_volume()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ViewportBounds':
        """Create ViewportBounds from dictionary."""
        center = data.get('center', {})
        dimensions = data.get('dimensions', {})
        
        return cls(
            center_x=center.get('x', 0.0),
            center_y=center.get('y', 0.0), 
            center_z=center.get('z', 0.0),
            width=dimensions.get('width', 100.0),
            height=dimensions.get('height', 100.0),
            depth=dimensions.get('depth', 20.0),
            zoom_level=data.get('zoom_level', 1),
            rotation_angle=data.get('rotation_angle', 0.0)
        )


class ViewportQueryType(Enum):
    """Types of viewport-based queries."""
    
    EXACT = "exact"           # Exact viewport bounds
    BUFFERED = "buffered"     # Viewport + buffer zone
    HIERARCHICAL = "hierarchical"  # Multi-level LOD query
    PREDICTIVE = "predictive"      # Include predicted movement


class ViewportManager:
    """
    Viewport Manager for 14KB streaming architecture.
    
    Manages viewport-based spatial queries, buffer zones for progressive
    loading, and viewport-aware caching strategies.
    """
    
    def __init__(self, 
                 buffer_factor: float = 1.5,
                 prediction_enabled: bool = True,
                 cache_viewport_count: int = 5):
        """
        Initialize viewport manager.
        
        Args:
            buffer_factor: Buffer zone multiplier (1.5 = 50% larger than viewport)
            prediction_enabled: Enable movement prediction
            cache_viewport_count: Number of recent viewports to cache
        """
        self.buffer_factor = buffer_factor
        self.prediction_enabled = prediction_enabled
        self.cache_viewport_count = cache_viewport_count
        
        # Viewport history for prediction
        self.viewport_history: List[Tuple[float, ViewportBounds]] = []
        self.max_history_size = 10
        
        # Query cache
        self.query_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_timestamps: Dict[str, float] = {}
        self.cache_ttl_seconds = 30  # 30 second TTL for viewport queries
        
        # Movement prediction
        self.movement_vector: Optional[Tuple[float, float, float]] = None
        self.movement_speed: float = 0.0
        self.last_update_time: float = 0.0
        
        # Performance metrics
        self.metrics = {
            'viewport_changes': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'prediction_accuracy': 0.0,
            'average_query_time_ms': 0.0
        }
        
        logger.info(f"Initialized ViewportManager with buffer factor: {buffer_factor}")
    
    def update_viewport(self, viewport: ViewportBounds) -> Dict[str, Any]:
        """
        Update current viewport and calculate movement prediction.
        
        Args:
            viewport: New viewport bounds
            
        Returns:
            Viewport update information
        """
        current_time = time.time()
        
        # Update movement prediction
        if self.viewport_history and self.prediction_enabled:
            self._update_movement_prediction(viewport, current_time)
        
        # Add to history
        self.viewport_history.append((current_time, viewport))
        
        # Maintain history size limit
        if len(self.viewport_history) > self.max_history_size:
            self.viewport_history.pop(0)
        
        self.last_update_time = current_time
        self.metrics['viewport_changes'] += 1
        
        logger.debug(f"Updated viewport to {viewport.center_x:.1f},{viewport.center_y:.1f} "
                    f"({viewport.width}x{viewport.height})")
        
        return {
            'viewport_updated': True,
            'movement_detected': self.movement_speed > 0.1,
            'movement_speed': self.movement_speed,
            'prediction_available': self.movement_vector is not None,
            'timestamp': current_time
        }
    
    def _update_movement_prediction(self, new_viewport: ViewportBounds, current_time: float) -> None:
        """Update movement prediction based on viewport history."""
        
        if len(self.viewport_history) < 2:
            return
        
        # Get last viewport
        last_time, last_viewport = self.viewport_history[-1]
        time_delta = current_time - last_time
        
        if time_delta <= 0:
            return
        
        # Calculate movement vector
        dx = new_viewport.center_x - last_viewport.center_x
        dy = new_viewport.center_y - last_viewport.center_y
        dz = new_viewport.center_z - last_viewport.center_z
        
        # Calculate speed (units per second)
        distance = (dx**2 + dy**2 + dz**2)**0.5
        self.movement_speed = distance / time_delta
        
        # Update movement vector (normalized direction)
        if distance > 0:
            self.movement_vector = (dx / distance, dy / distance, dz / distance)
        else:
            self.movement_vector = None
    
    def get_query_bounds(self, 
                        viewport: ViewportBounds,
                        query_type: ViewportQueryType = ViewportQueryType.BUFFERED) -> BoundingBox3D:
        """
        Get spatial query bounds based on viewport and query type.
        
        Args:
            viewport: Base viewport
            query_type: Type of query bounds to calculate
            
        Returns:
            3D bounding box for spatial queries
        """
        if query_type == ViewportQueryType.EXACT:
            return viewport.to_bounding_box_3d()
        
        elif query_type == ViewportQueryType.BUFFERED:
            # Expand viewport by buffer factor
            buffered_width = viewport.width * self.buffer_factor
            buffered_height = viewport.height * self.buffer_factor
            buffered_depth = viewport.depth * self.buffer_factor
            
            half_width = buffered_width / 2
            half_height = buffered_height / 2
            half_depth = buffered_depth / 2
            
            return BoundingBox3D(
                min_x=viewport.center_x - half_width,
                max_x=viewport.center_x + half_width,
                min_y=viewport.center_y - half_height,
                max_y=viewport.center_y + half_height,
                min_z=viewport.center_z - half_depth,
                max_z=viewport.center_z + half_depth
            )
        
        elif query_type == ViewportQueryType.PREDICTIVE and self.movement_vector:
            # Include predicted future position
            prediction_distance = self.movement_speed * 2.0  # 2 second prediction
            
            predicted_x = viewport.center_x + (self.movement_vector[0] * prediction_distance)
            predicted_y = viewport.center_y + (self.movement_vector[1] * prediction_distance)
            predicted_z = viewport.center_z + (self.movement_vector[2] * prediction_distance)
            
            # Create bounding box that includes both current and predicted positions
            current_bounds = self.get_query_bounds(viewport, ViewportQueryType.BUFFERED)
            
            predicted_viewport = ViewportBounds(
                predicted_x, predicted_y, predicted_z,
                viewport.width, viewport.height, viewport.depth,
                viewport.zoom_level, viewport.rotation_angle
            )
            predicted_bounds = self.get_query_bounds(predicted_viewport, ViewportQueryType.BUFFERED)
            
            # Union of current and predicted bounds
            return BoundingBox3D(
                min_x=min(current_bounds.min_x, predicted_bounds.min_x),
                max_x=max(current_bounds.max_x, predicted_bounds.max_x),
                min_y=min(current_bounds.min_y, predicted_bounds.min_y),
                max_y=max(current_bounds.max_y, predicted_bounds.max_y),
                min_z=min(current_bounds.min_z, predicted_bounds.min_z),
                max_z=max(current_bounds.max_z, predicted_bounds.max_z)
            )
        
        else:
            # Default to buffered
            return self.get_query_bounds(viewport, ViewportQueryType.BUFFERED)
    
    def get_cache_key(self, viewport: ViewportBounds, lod_level: Any = None) -> str:
        """
        Generate cache key for viewport query.
        
        Args:
            viewport: Viewport bounds
            lod_level: Optional LOD level
            
        Returns:
            Cache key string
        """
        # Round viewport coordinates to reduce cache fragmentation
        rounded_viewport = {
            'center_x': round(viewport.center_x, 1),
            'center_y': round(viewport.center_y, 1),
            'center_z': round(viewport.center_z, 1),
            'width': round(viewport.width, 1),
            'height': round(viewport.height, 1),
            'depth': round(viewport.depth, 1),
            'zoom': viewport.zoom_level
        }
        
        if lod_level:
            rounded_viewport['lod'] = lod_level.value if hasattr(lod_level, 'value') else str(lod_level)
        
        # Create hash of viewport data
        viewport_str = json.dumps(rounded_viewport, sort_keys=True)
        viewport_hash = hashlib.md5(viewport_str.encode()).hexdigest()[:12]
        
        return f"viewport_{viewport_hash}"
    
    def is_viewport_similar(self, viewport1: ViewportBounds, viewport2: ViewportBounds, 
                           threshold: float = 0.1) -> bool:
        """
        Check if two viewports are similar (for cache optimization).
        
        Args:
            viewport1: First viewport
            viewport2: Second viewport  
            threshold: Similarity threshold (0.1 = 10% difference)
            
        Returns:
            True if viewports are similar
        """
        # Calculate center distance
        center_distance = (
            (viewport1.center_x - viewport2.center_x)**2 +
            (viewport1.center_y - viewport2.center_y)**2 +
            (viewport1.center_z - viewport2.center_z)**2
        )**0.5
        
        # Calculate size difference
        size1 = (viewport1.width + viewport1.height + viewport1.depth) / 3
        size2 = (viewport2.width + viewport2.height + viewport2.depth) / 3
        size_ratio = abs(size1 - size2) / max(size1, size2) if max(size1, size2) > 0 else 0
        
        # Check zoom level difference
        zoom_diff = abs(viewport1.zoom_level - viewport2.zoom_level)
        
        # Consider similar if center distance is small relative to viewport size
        # and zoom levels are close
        relative_distance = center_distance / max(size1, size2) if max(size1, size2) > 0 else 0
        
        return (relative_distance < threshold and 
                size_ratio < threshold and 
                zoom_diff <= 1)
    
    def should_trigger_loading(self, viewport: ViewportBounds) -> Dict[str, Any]:
        """
        Determine if viewport change should trigger progressive loading.
        
        Args:
            viewport: Current viewport
            
        Returns:
            Loading trigger analysis
        """
        trigger_info = {
            'should_load': False,
            'loading_priority': 'normal',
            'reasons': [],
            'predicted_objects': 0
        }
        
        # Check if viewport is significantly different from cached viewports
        cache_key = self.get_cache_key(viewport)
        
        if cache_key not in self.query_cache:
            trigger_info['should_load'] = True
            trigger_info['reasons'].append('new_viewport')
        else:
            # Check cache age
            cache_age = time.time() - self.cache_timestamps.get(cache_key, 0)
            if cache_age > self.cache_ttl_seconds:
                trigger_info['should_load'] = True
                trigger_info['reasons'].append('cache_expired')
        
        # Check movement speed for priority
        if self.movement_speed > 1.0:  # Fast movement
            trigger_info['loading_priority'] = 'high'
            trigger_info['reasons'].append('fast_movement')
        elif self.movement_speed > 0.1:  # Slow movement
            trigger_info['loading_priority'] = 'low'
            trigger_info['reasons'].append('slow_movement')
        
        # Estimate objects in viewport (rough calculation)
        viewport_area = viewport.get_area()
        object_density = 0.1  # 0.1 objects per square unit (estimate)
        trigger_info['predicted_objects'] = int(viewport_area * object_density)
        
        return trigger_info
    
    def get_adaptive_lod_level(self, viewport: ViewportBounds) -> int:
        """
        Calculate adaptive LOD level based on viewport characteristics.
        
        Args:
            viewport: Current viewport
            
        Returns:
            Recommended LOD level (0-4)
        """
        viewport_area = viewport.get_area()
        zoom_level = viewport.zoom_level
        
        # Base LOD on viewport area and zoom
        if viewport_area < 100 or zoom_level > 8:  # Very detailed view
            return 3  # CONFLICT_ZONES level
        elif viewport_area < 1000 or zoom_level > 4:  # Moderate detail
            return 2  # DETAILED_COMPONENTS level
        elif viewport_area < 10000 or zoom_level > 2:  # Room level
            return 1  # ROOM_LAYOUT level
        else:  # Building overview
            return 0  # BUILDING_OUTLINE level
    
    def clear_cache(self, older_than_seconds: Optional[float] = None) -> int:
        """
        Clear viewport query cache.
        
        Args:
            older_than_seconds: Only clear entries older than this
            
        Returns:
            Number of cache entries cleared
        """
        if older_than_seconds is None:
            # Clear all
            cleared_count = len(self.query_cache)
            self.query_cache.clear()
            self.cache_timestamps.clear()
        else:
            # Clear old entries
            current_time = time.time()
            keys_to_remove = []
            
            for key, timestamp in self.cache_timestamps.items():
                if current_time - timestamp > older_than_seconds:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                self.query_cache.pop(key, None)
                self.cache_timestamps.pop(key, None)
            
            cleared_count = len(keys_to_remove)
        
        logger.info(f"Cleared {cleared_count} viewport cache entries")
        return cleared_count
    
    def get_viewport_analytics(self) -> Dict[str, Any]:
        """Get viewport usage analytics."""
        
        # Calculate movement statistics
        if len(self.viewport_history) >= 2:
            total_distance = 0.0
            for i in range(1, len(self.viewport_history)):
                prev_time, prev_viewport = self.viewport_history[i-1]
                curr_time, curr_viewport = self.viewport_history[i]
                
                distance = (
                    (curr_viewport.center_x - prev_viewport.center_x)**2 +
                    (curr_viewport.center_y - prev_viewport.center_y)**2 +
                    (curr_viewport.center_z - prev_viewport.center_z)**2
                )**0.5
                
                total_distance += distance
            
            avg_distance_per_change = total_distance / (len(self.viewport_history) - 1)
        else:
            avg_distance_per_change = 0.0
        
        # Cache effectiveness
        total_queries = self.metrics['cache_hits'] + self.metrics['cache_misses']
        cache_hit_rate = self.metrics['cache_hits'] / total_queries if total_queries > 0 else 0
        
        return {
            'viewport_changes': self.metrics['viewport_changes'],
            'average_movement_distance': avg_distance_per_change,
            'current_movement_speed': self.movement_speed,
            'movement_prediction_active': self.movement_vector is not None,
            'cache_entries': len(self.query_cache),
            'cache_hit_rate': cache_hit_rate,
            'viewport_history_size': len(self.viewport_history),
            'performance_metrics': self.metrics.copy()
        }