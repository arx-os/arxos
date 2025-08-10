"""
3D Octree Spatial Indexing Implementation.

High-performance octree implementation for 3D spatial partitioning of ArxObjects,
optimized for million-scale building component conflict detection.
"""

import time
from typing import List, Tuple, Optional, Set, Dict, Any
from dataclasses import dataclass
import logging
from concurrent.futures import ThreadPoolExecutor
import threading
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class BoundingBox3D:
    """3D bounding box representation."""
    min_x: float
    min_y: float 
    min_z: float
    max_x: float
    max_y: float
    max_z: float
    
    def contains_point(self, x: float, y: float, z: float) -> bool:
        """Check if point is within bounding box."""
        return (self.min_x <= x <= self.max_x and 
                self.min_y <= y <= self.max_y and
                self.min_z <= z <= self.max_z)
    
    def intersects(self, other: 'BoundingBox3D') -> bool:
        """Check if this bounding box intersects with another."""
        return not (self.max_x < other.min_x or self.min_x > other.max_x or
                   self.max_y < other.min_y or self.min_y > other.max_y or
                   self.max_z < other.min_z or self.min_z > other.max_z)
    
    def volume(self) -> float:
        """Calculate bounding box volume."""
        return ((self.max_x - self.min_x) * 
                (self.max_y - self.min_y) * 
                (self.max_z - self.min_z))
    
    def center(self) -> Tuple[float, float, float]:
        """Get center point of bounding box."""
        return ((self.min_x + self.max_x) / 2,
                (self.min_y + self.max_y) / 2,
                (self.min_z + self.min_z) / 2)


@dataclass
class OctreeNode:
    """Single node in the octree structure."""
    bounds: BoundingBox3D
    objects: List[Any]  # ArxObjects stored in this node
    children: Optional[List['OctreeNode']]
    depth: int
    max_objects: int = 10
    max_depth: int = 10
    
    def __post_init__(self):
        self.children = None
        self.lock = threading.RLock()  # Thread-safe operations
    
    def is_leaf(self) -> bool:
        """Check if this is a leaf node."""
        return self.children is None
    
    def should_subdivide(self) -> bool:
        """Determine if node should be subdivided."""
        return (len(self.objects) > self.max_objects and 
                self.depth < self.max_depth and
                self.bounds.volume() > 1e-6)  # Prevent infinite subdivision
    
    def subdivide(self) -> None:
        """Subdivide node into 8 octants."""
        if not self.should_subdivide():
            return
            
        with self.lock:
            if self.children is not None:  # Double-check after acquiring lock
                return
                
            # Calculate octant boundaries
            center_x, center_y, center_z = self.bounds.center()
            
            self.children = []
            
            # Create 8 octants
            for i in range(8):
                # Determine octant bounds based on binary representation of i
                min_x = self.bounds.min_x if (i & 1) == 0 else center_x
                max_x = center_x if (i & 1) == 0 else self.bounds.max_x
                
                min_y = self.bounds.min_y if (i & 2) == 0 else center_y
                max_y = center_y if (i & 2) == 0 else self.bounds.max_y
                
                min_z = self.bounds.min_z if (i & 4) == 0 else center_z
                max_z = center_z if (i & 4) == 0 else self.bounds.max_z
                
                octant_bounds = BoundingBox3D(min_x, min_y, min_z, max_x, max_y, max_z)
                child = OctreeNode(
                    bounds=octant_bounds,
                    objects=[],
                    children=None,
                    depth=self.depth + 1,
                    max_objects=self.max_objects,
                    max_depth=self.max_depth
                )
                self.children.append(child)
            
            # Redistribute objects to children
            for obj in self.objects:
                obj_bounds = obj.get_bounding_box()
                for child in self.children:
                    if child.bounds.intersects(obj_bounds):
                        child.objects.append(obj)
            
            # Clear objects from parent after redistribution
            self.objects.clear()
    
    def insert(self, obj: Any) -> bool:
        """Insert object into appropriate node."""
        obj_bounds = obj.get_bounding_box()
        
        if not self.bounds.intersects(obj_bounds):
            return False
        
        with self.lock:
            if self.is_leaf():
                self.objects.append(obj)
                if self.should_subdivide():
                    self.subdivide()
                return True
            else:
                # Insert into appropriate children
                inserted = False
                for child in self.children:
                    if child.insert(obj):
                        inserted = True
                return inserted
    
    def remove(self, obj: Any) -> bool:
        """Remove object from node."""
        with self.lock:
            if self.is_leaf():
                try:
                    self.objects.remove(obj)
                    return True
                except ValueError:
                    return False
            else:
                removed = False
                for child in self.children:
                    if child.remove(obj):
                        removed = True
                return removed
    
    def query_range(self, bounds: BoundingBox3D, results: List[Any]) -> None:
        """Query objects within given bounds."""
        if not self.bounds.intersects(bounds):
            return
        
        if self.is_leaf():
            for obj in self.objects:
                if bounds.intersects(obj.get_bounding_box()):
                    results.append(obj)
        else:
            for child in self.children:
                child.query_range(bounds, results)
    
    def query_point(self, x: float, y: float, z: float, results: List[Any]) -> None:
        """Query objects containing a point."""
        if not self.bounds.contains_point(x, y, z):
            return
        
        if self.is_leaf():
            for obj in self.objects:
                if obj.contains_point(x, y, z):
                    results.append(obj)
        else:
            for child in self.children:
                child.query_point(x, y, z, results)


class OctreeIndex:
    """
    High-performance 3D Octree spatial index for ArxObjects.
    
    Optimized for million-scale building component conflict detection
    with thread-safe operations and efficient spatial queries.
    """
    
    def __init__(self, world_bounds: BoundingBox3D, max_objects: int = 10, 
                 max_depth: int = 15):
        """
        Initialize octree with world boundaries.
        
        Args:
            world_bounds: 3D bounding box for the entire building space
            max_objects: Maximum objects per node before subdivision
            max_depth: Maximum tree depth to prevent infinite subdivision
        """
        self.world_bounds = world_bounds
        self.max_objects = max_objects
        self.max_depth = max_depth
        self.root = OctreeNode(
            bounds=world_bounds,
            objects=[],
            children=None,
            depth=0,
            max_objects=max_objects,
            max_depth=max_depth
        )
        self.object_count = 0
        self.query_stats = {
            'total_queries': 0,
            'average_query_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._lock = threading.RLock()
        
        logger.info(f"Initialized OctreeIndex with bounds {world_bounds}, "
                   f"max_objects={max_objects}, max_depth={max_depth}")
    
    def insert(self, arxobject: Any) -> bool:
        """
        Insert ArxObject into spatial index.
        
        Args:
            arxobject: ArxObject to insert
            
        Returns:
            bool: True if insertion successful
        """
        start_time = time.time()
        
        try:
            with self._lock:
                success = self.root.insert(arxobject)
                if success:
                    self.object_count += 1
                    
            elapsed = time.time() - start_time
            logger.debug(f"Inserted object {arxobject.id} in {elapsed:.4f}s")
            return success
            
        except Exception as e:
            logger.error(f"Failed to insert object {arxobject.id}: {e}")
            return False
    
    def batch_insert(self, arxobjects: List[Any]) -> int:
        """
        Insert multiple ArxObjects efficiently.
        
        Args:
            arxobjects: List of ArxObjects to insert
            
        Returns:
            int: Number of objects successfully inserted
        """
        start_time = time.time()
        successful = 0
        
        # Sort objects by spatial locality for better cache performance
        sorted_objects = sorted(arxobjects, key=lambda obj: obj.get_center())
        
        for obj in sorted_objects:
            if self.insert(obj):
                successful += 1
        
        elapsed = time.time() - start_time
        logger.info(f"Batch inserted {successful}/{len(arxobjects)} objects "
                   f"in {elapsed:.2f}s ({successful/elapsed:.0f} objects/sec)")
        
        return successful
    
    def remove(self, arxobject: Any) -> bool:
        """
        Remove ArxObject from spatial index.
        
        Args:
            arxobject: ArxObject to remove
            
        Returns:
            bool: True if removal successful
        """
        try:
            with self._lock:
                success = self.root.remove(arxobject)
                if success:
                    self.object_count -= 1
            return success
        except Exception as e:
            logger.error(f"Failed to remove object {arxobject.id}: {e}")
            return False
    
    def query_range(self, bounds: BoundingBox3D) -> List[Any]:
        """
        Query all objects within bounding box.
        
        Args:
            bounds: 3D bounding box to query
            
        Returns:
            List of ArxObjects within bounds
        """
        start_time = time.time()
        results = []
        
        try:
            self.root.query_range(bounds, results)
            
            elapsed = time.time() - start_time
            self._update_query_stats(elapsed)
            
            logger.debug(f"Range query returned {len(results)} objects in {elapsed:.4f}s")
            return results
            
        except Exception as e:
            logger.error(f"Range query failed: {e}")
            return []
    
    def query_point(self, x: float, y: float, z: float) -> List[Any]:
        """
        Query all objects containing a point.
        
        Args:
            x, y, z: 3D coordinates to query
            
        Returns:
            List of ArxObjects containing the point
        """
        start_time = time.time()
        results = []
        
        try:
            self.root.query_point(x, y, z, results)
            
            elapsed = time.time() - start_time
            self._update_query_stats(elapsed)
            
            logger.debug(f"Point query at ({x}, {y}, {z}) returned "
                        f"{len(results)} objects in {elapsed:.4f}s")
            return results
            
        except Exception as e:
            logger.error(f"Point query failed: {e}")
            return []
    
    def find_conflicts(self, arxobject: Any, tolerance: float = 0.001) -> List[Tuple[Any, str]]:
        """
        Find spatial conflicts with given ArxObject.
        
        Args:
            arxobject: ArxObject to check for conflicts
            tolerance: Minimum distance tolerance for conflicts
            
        Returns:
            List of (conflicting_object, conflict_type) tuples
        """
        start_time = time.time()
        conflicts = []
        
        try:
            # Expand bounding box by tolerance for conflict detection
            obj_bounds = arxobject.get_bounding_box()
            expanded_bounds = BoundingBox3D(
                obj_bounds.min_x - tolerance,
                obj_bounds.min_y - tolerance,
                obj_bounds.min_z - tolerance,
                obj_bounds.max_x + tolerance,
                obj_bounds.max_y + tolerance,
                obj_bounds.max_z + tolerance
            )
            
            # Query potential conflicts
            candidates = self.query_range(expanded_bounds)
            
            # Detailed conflict analysis
            for candidate in candidates:
                if candidate.id == arxobject.id:
                    continue
                    
                conflict_type = self._analyze_conflict(arxobject, candidate, tolerance)
                if conflict_type:
                    conflicts.append((candidate, conflict_type))
            
            elapsed = time.time() - start_time
            logger.debug(f"Conflict detection for {arxobject.id} found "
                        f"{len(conflicts)} conflicts in {elapsed:.4f}s")
            
            return conflicts
            
        except Exception as e:
            logger.error(f"Conflict detection failed for {arxobject.id}: {e}")
            return []
    
    def _analyze_conflict(self, obj1: Any, obj2: Any, tolerance: float) -> Optional[str]:
        """Analyze conflict type between two objects."""
        # Get system priorities for conflict resolution
        priority1 = obj1.get_system_priority()
        priority2 = obj2.get_system_priority()
        
        # Check geometric intersection
        if obj1.get_bounding_box().intersects(obj2.get_bounding_box()):
            # Determine conflict type based on system priorities
            if priority1 == priority2:
                return "same_system_conflict"
            elif priority1 > priority2:
                return "higher_priority_conflict" 
            else:
                return "lower_priority_conflict"
        
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get spatial index statistics."""
        def count_nodes(node: OctreeNode) -> Tuple[int, int, int]:
            """Count nodes, leaf nodes, and max depth."""
            if node.is_leaf():
                return 1, 1, node.depth
            else:
                total_nodes = 1
                leaf_nodes = 0
                max_depth = node.depth
                
                for child in node.children:
                    child_total, child_leaf, child_depth = count_nodes(child)
                    total_nodes += child_total
                    leaf_nodes += child_leaf
                    max_depth = max(max_depth, child_depth)
                
                return total_nodes, leaf_nodes, max_depth
        
        total_nodes, leaf_nodes, max_depth = count_nodes(self.root)
        
        return {
            'object_count': self.object_count,
            'total_nodes': total_nodes,
            'leaf_nodes': leaf_nodes,
            'max_depth_used': max_depth,
            'max_depth_configured': self.max_depth,
            'world_bounds_volume': self.world_bounds.volume(),
            'query_stats': self.query_stats.copy(),
            'average_objects_per_leaf': (self.object_count / leaf_nodes) if leaf_nodes > 0 else 0
        }
    
    def _update_query_stats(self, elapsed_time: float) -> None:
        """Update query performance statistics."""
        self.query_stats['total_queries'] += 1
        total_time = (self.query_stats['average_query_time'] * 
                     (self.query_stats['total_queries'] - 1) + elapsed_time)
        self.query_stats['average_query_time'] = total_time / self.query_stats['total_queries']
    
    def optimize(self) -> None:
        """Optimize spatial index by rebalancing tree."""
        logger.info("Starting octree optimization...")
        start_time = time.time()
        
        # Collect all objects
        all_objects = []
        self._collect_all_objects(self.root, all_objects)
        
        # Rebuild with better spatial locality
        self.root = OctreeNode(
            bounds=self.world_bounds,
            objects=[],
            children=None,
            depth=0,
            max_objects=self.max_objects,
            max_depth=self.max_depth
        )
        self.object_count = 0
        
        # Reinsert objects with spatial sorting
        self.batch_insert(all_objects)
        
        elapsed = time.time() - start_time
        logger.info(f"Octree optimization completed in {elapsed:.2f}s")
    
    def _collect_all_objects(self, node: OctreeNode, objects: List[Any]) -> None:
        """Recursively collect all objects from tree."""
        if node.is_leaf():
            objects.extend(node.objects)
        else:
            for child in node.children:
                self._collect_all_objects(child, objects)
    
    def clear(self) -> None:
        """Clear all objects from spatial index."""
        with self._lock:
            self.root = OctreeNode(
                bounds=self.world_bounds,
                objects=[],
                children=None,
                depth=0,
                max_objects=self.max_objects,
                max_depth=self.max_depth
            )
            self.object_count = 0
            self.query_stats = {
                'total_queries': 0,
                'average_query_time': 0.0,
                'cache_hits': 0,
                'cache_misses': 0
            }
        
        logger.info("Cleared octree spatial index")
    
    def __len__(self) -> int:
        """Return number of objects in spatial index."""
        return self.object_count
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)