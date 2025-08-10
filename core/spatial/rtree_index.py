"""
2D R-tree Spatial Indexing Implementation.

High-performance R-tree implementation for 2D plan view queries of ArxObjects,
optimized for floor plan operations and cross-system spatial analysis.
"""

import time
import math
from typing import List, Tuple, Optional, Set, Dict, Any, Union
from dataclasses import dataclass
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class BoundingBox2D:
    """2D bounding box representation for plan view operations."""
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if point is within bounding box."""
        return (self.min_x <= x <= self.max_x and 
                self.min_y <= y <= self.max_y)
    
    def intersects(self, other: 'BoundingBox2D') -> bool:
        """Check if this bounding box intersects with another."""
        return not (self.max_x < other.min_x or self.min_x > other.max_x or
                   self.max_y < other.min_y or self.min_y > other.max_y)
    
    def area(self) -> float:
        """Calculate bounding box area."""
        return (self.max_x - self.min_x) * (self.max_y - self.min_y)
    
    def perimeter(self) -> float:
        """Calculate bounding box perimeter."""
        return 2.0 * ((self.max_x - self.min_x) + (self.max_y - self.min_y))
    
    def center(self) -> Tuple[float, float]:
        """Get center point of bounding box."""
        return ((self.min_x + self.max_x) / 2, (self.min_y + self.max_y) / 2)
    
    def expand_to_include(self, other: 'BoundingBox2D') -> 'BoundingBox2D':
        """Expand this bounding box to include another."""
        return BoundingBox2D(
            min(self.min_x, other.min_x),
            min(self.min_y, other.min_y),
            max(self.max_x, other.max_x),
            max(self.max_y, other.max_y)
        )
    
    def expand_by_distance(self, distance: float) -> 'BoundingBox2D':
        """Expand bounding box by given distance."""
        return BoundingBox2D(
            self.min_x - distance,
            self.min_y - distance,
            self.max_x + distance,
            self.max_y + distance
        )
    
    def distance_to_point(self, x: float, y: float) -> float:
        """Calculate minimum distance from point to bounding box."""
        dx = max(0, max(self.min_x - x, x - self.max_x))
        dy = max(0, max(self.min_y - y, y - self.max_y))
        return math.sqrt(dx * dx + dy * dy)


@dataclass
class RTreeEntry:
    """Entry in R-tree node."""
    bounds: BoundingBox2D
    child_node: Optional['RTreeNode'] = None
    arxobject: Optional[Any] = None  # Leaf entry contains ArxObject
    
    def is_leaf_entry(self) -> bool:
        """Check if this is a leaf entry containing an ArxObject."""
        return self.arxobject is not None
    
    def area_enlargement(self, new_bounds: BoundingBox2D) -> float:
        """Calculate area enlargement needed to include new bounds."""
        expanded = self.bounds.expand_to_include(new_bounds)
        return expanded.area() - self.bounds.area()


class RTreeNode:
    """Node in R-tree structure."""
    
    def __init__(self, is_leaf: bool = False, max_entries: int = 10):
        self.is_leaf = is_leaf
        self.entries: List[RTreeEntry] = []
        self.max_entries = max_entries
        self.min_entries = max_entries // 2
        self.lock = threading.RLock()
    
    def is_full(self) -> bool:
        """Check if node is full."""
        return len(self.entries) >= self.max_entries
    
    def add_entry(self, entry: RTreeEntry) -> None:
        """Add entry to node."""
        with self.lock:
            self.entries.append(entry)
    
    def remove_entry(self, entry: RTreeEntry) -> bool:
        """Remove entry from node."""
        with self.lock:
            try:
                self.entries.remove(entry)
                return True
            except ValueError:
                return False
    
    def get_bounds(self) -> Optional[BoundingBox2D]:
        """Get bounding box encompassing all entries."""
        if not self.entries:
            return None
        
        bounds = self.entries[0].bounds
        for entry in self.entries[1:]:
            bounds = bounds.expand_to_include(entry.bounds)
        
        return bounds
    
    def choose_subtree(self, new_bounds: BoundingBox2D) -> RTreeEntry:
        """Choose best subtree for insertion using least enlargement strategy."""
        if self.is_leaf:
            raise ValueError("Cannot choose subtree on leaf node")
        
        best_entry = None
        min_enlargement = float('inf')
        min_area = float('inf')
        
        for entry in self.entries:
            enlargement = entry.area_enlargement(new_bounds)
            area = entry.bounds.area()
            
            # Choose entry with least area enlargement, ties broken by smallest area
            if (enlargement < min_enlargement or 
                (enlargement == min_enlargement and area < min_area)):
                best_entry = entry
                min_enlargement = enlargement
                min_area = area
        
        return best_entry
    
    def split(self) -> Tuple['RTreeNode', RTreeEntry]:
        """Split overfull node using quadratic algorithm."""
        # Find pair of entries with maximum waste of area
        max_waste = -1
        seed1_idx, seed2_idx = 0, 1
        
        for i in range(len(self.entries)):
            for j in range(i + 1, len(self.entries)):
                combined_bounds = self.entries[i].bounds.expand_to_include(self.entries[j].bounds)
                waste = (combined_bounds.area() - 
                        self.entries[i].bounds.area() - 
                        self.entries[j].bounds.area())
                
                if waste > max_waste:
                    max_waste = waste
                    seed1_idx, seed2_idx = i, j
        
        # Create new node and distribute entries
        new_node = RTreeNode(self.is_leaf, self.max_entries)
        
        # Start with seed entries
        seed1 = self.entries[seed1_idx]
        seed2 = self.entries[seed2_idx]
        
        # Remove seeds from current entries
        remaining_entries = [e for i, e in enumerate(self.entries) 
                           if i not in (seed1_idx, seed2_idx)]
        
        # Clear current entries and add seed1
        self.entries = [seed1]
        new_node.entries = [seed2]
        
        # Distribute remaining entries
        for entry in remaining_entries:
            # Choose node that needs least enlargement
            enlargement1 = seed1.bounds.area() if self.entries else 0
            current_bounds1 = self.get_bounds()
            if current_bounds1:
                enlarged1 = current_bounds1.expand_to_include(entry.bounds)
                enlargement1 = enlarged1.area() - current_bounds1.area()
            
            enlargement2 = seed2.bounds.area() if new_node.entries else 0
            current_bounds2 = new_node.get_bounds()
            if current_bounds2:
                enlarged2 = current_bounds2.expand_to_include(entry.bounds)
                enlargement2 = enlarged2.area() - current_bounds2.area()
            
            # Add to node with less enlargement
            if enlargement1 < enlargement2:
                self.entries.append(entry)
            else:
                new_node.entries.append(entry)
        
        # Create entry for new node
        new_node_bounds = new_node.get_bounds()
        new_entry = RTreeEntry(bounds=new_node_bounds, child_node=new_node)
        
        return new_node, new_entry


class RTreeIndex:
    """
    High-performance 2D R-tree spatial index for ArxObjects.
    
    Optimized for plan view queries, floor plan operations, and 
    cross-system spatial analysis with million-scale performance.
    """
    
    def __init__(self, max_entries: int = 10):
        """
        Initialize R-tree spatial index.
        
        Args:
            max_entries: Maximum entries per node before splitting
        """
        self.max_entries = max_entries
        self.root = RTreeNode(is_leaf=True, max_entries=max_entries)
        self.object_count = 0
        self.height = 1
        
        # Performance tracking
        self.query_stats = {
            'total_queries': 0,
            'average_query_time': 0.0,
            'nodes_visited': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._lock = threading.RLock()
        
        logger.info(f"Initialized RTreeIndex with max_entries={max_entries}")
    
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
            # Get 2D bounding box (plan view projection)
            bbox_2d = arxobject.get_plan_view_bounds()
            entry = RTreeEntry(bounds=bbox_2d, arxobject=arxobject)
            
            with self._lock:
                new_root_entry = self._insert_entry(self.root, entry)
                
                # Handle root split
                if new_root_entry:
                    new_root = RTreeNode(is_leaf=False, max_entries=self.max_entries)
                    
                    # Create entry for old root
                    old_root_bounds = self.root.get_bounds()
                    old_root_entry = RTreeEntry(bounds=old_root_bounds, child_node=self.root)
                    
                    new_root.add_entry(old_root_entry)
                    new_root.add_entry(new_root_entry)
                    
                    self.root = new_root
                    self.height += 1
                
                self.object_count += 1
            
            elapsed = time.time() - start_time
            logger.debug(f"Inserted object {arxobject.id} in {elapsed:.4f}s")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert object {arxobject.id}: {e}")
            return False
    
    def _insert_entry(self, node: RTreeNode, entry: RTreeEntry) -> Optional[RTreeEntry]:
        """Insert entry into node, returning new node entry if split occurred."""
        if node.is_leaf:
            # Add to leaf node
            node.add_entry(entry)
            
            # Split if overfull
            if node.is_full():
                new_node, new_entry = node.split()
                return new_entry
            
            return None
        else:
            # Choose best subtree
            best_subtree = node.choose_subtree(entry.bounds)
            new_entry = self._insert_entry(best_subtree.child_node, entry)
            
            # Update bounds of subtree entry
            best_subtree.bounds = best_subtree.child_node.get_bounds()
            
            # Handle child split
            if new_entry:
                node.add_entry(new_entry)
                
                # Split this node if overfull
                if node.is_full():
                    new_node, split_entry = node.split()
                    return split_entry
            
            return None
    
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
        
        # Sort objects by Hilbert curve for better spatial locality
        sorted_objects = self._sort_by_spatial_locality(arxobjects)
        
        for obj in sorted_objects:
            if self.insert(obj):
                successful += 1
        
        elapsed = time.time() - start_time
        logger.info(f"Batch inserted {successful}/{len(arxobjects)} objects "
                   f"in {elapsed:.2f}s ({successful/elapsed:.0f} objects/sec)")
        
        return successful
    
    def _sort_by_spatial_locality(self, objects: List[Any]) -> List[Any]:
        """Sort objects by spatial locality using simplified Hilbert ordering."""
        # Get center points
        centers = [(obj, obj.get_plan_view_bounds().center()) for obj in objects]
        
        # Sort by Hilbert-like curve approximation (Z-order curve)
        def hilbert_distance(point):
            x, y = point[1]
            # Simple bit interleaving for Z-order curve
            x_int = int(x * 1000) & 0xFFFF
            y_int = int(y * 1000) & 0xFFFF
            z = 0
            for i in range(16):
                z |= (x_int & 1 << i) << i | (y_int & 1 << i) << (i + 1)
            return z
        
        sorted_centers = sorted(centers, key=hilbert_distance)
        return [obj for obj, _ in sorted_centers]
    
    def remove(self, arxobject: Any) -> bool:
        """
        Remove ArxObject from spatial index.
        
        Args:
            arxobject: ArxObject to remove
            
        Returns:
            bool: True if removal successful
        """
        try:
            bbox_2d = arxobject.get_plan_view_bounds()
            
            with self._lock:
                removed = self._remove_entry(self.root, arxobject, bbox_2d)
                if removed:
                    self.object_count -= 1
                    
                    # Handle root underflow
                    if not self.root.is_leaf and len(self.root.entries) == 1:
                        self.root = self.root.entries[0].child_node
                        self.height -= 1
                
                return removed
            
        except Exception as e:
            logger.error(f"Failed to remove object {arxobject.id}: {e}")
            return False
    
    def _remove_entry(self, node: RTreeNode, arxobject: Any, bounds: BoundingBox2D) -> bool:
        """Remove entry from node."""
        if node.is_leaf:
            # Find and remove matching entry
            for entry in node.entries[:]:  # Copy list to avoid modification during iteration
                if entry.arxobject and entry.arxobject.id == arxobject.id:
                    node.remove_entry(entry)
                    return True
            return False
        else:
            # Search subtrees that could contain the object
            removed = False
            for entry in node.entries:
                if entry.bounds.intersects(bounds):
                    if self._remove_entry(entry.child_node, arxobject, bounds):
                        # Update bounds after removal
                        entry.bounds = entry.child_node.get_bounds()
                        removed = True
                        break
            
            return removed
    
    def query_range(self, bounds: BoundingBox2D) -> List[Any]:
        """
        Query all objects within 2D bounding box.
        
        Args:
            bounds: 2D bounding box to query
            
        Returns:
            List of ArxObjects within bounds
        """
        start_time = time.time()
        results = []
        nodes_visited = 0
        
        try:
            self._query_range_recursive(self.root, bounds, results, nodes_visited)
            
            elapsed = time.time() - start_time
            self._update_query_stats(elapsed, nodes_visited)
            
            logger.debug(f"Range query returned {len(results)} objects in {elapsed:.4f}s, "
                        f"visited {nodes_visited} nodes")
            return results
            
        except Exception as e:
            logger.error(f"Range query failed: {e}")
            return []
    
    def _query_range_recursive(self, node: RTreeNode, bounds: BoundingBox2D, 
                              results: List[Any], nodes_visited: int) -> None:
        """Recursive range query implementation."""
        nodes_visited += 1
        
        if node.is_leaf:
            # Check leaf entries
            for entry in node.entries:
                if bounds.intersects(entry.bounds) and entry.arxobject:
                    results.append(entry.arxobject)
        else:
            # Check internal node entries
            for entry in node.entries:
                if bounds.intersects(entry.bounds):
                    self._query_range_recursive(entry.child_node, bounds, results, nodes_visited)
    
    def query_point(self, x: float, y: float) -> List[Any]:
        """
        Query all objects containing a 2D point.
        
        Args:
            x, y: 2D coordinates to query
            
        Returns:
            List of ArxObjects containing the point
        """
        start_time = time.time()
        results = []
        nodes_visited = 0
        
        try:
            self._query_point_recursive(self.root, x, y, results, nodes_visited)
            
            elapsed = time.time() - start_time
            self._update_query_stats(elapsed, nodes_visited)
            
            logger.debug(f"Point query at ({x}, {y}) returned {len(results)} objects "
                        f"in {elapsed:.4f}s, visited {nodes_visited} nodes")
            return results
            
        except Exception as e:
            logger.error(f"Point query failed: {e}")
            return []
    
    def _query_point_recursive(self, node: RTreeNode, x: float, y: float, 
                              results: List[Any], nodes_visited: int) -> None:
        """Recursive point query implementation."""
        nodes_visited += 1
        
        if node.is_leaf:
            # Check leaf entries
            for entry in node.entries:
                if entry.bounds.contains_point(x, y) and entry.arxobject:
                    # Additional precise point-in-object test
                    if entry.arxobject.contains_point_2d(x, y):
                        results.append(entry.arxobject)
        else:
            # Check internal node entries
            for entry in node.entries:
                if entry.bounds.contains_point(x, y):
                    self._query_point_recursive(entry.child_node, x, y, results, nodes_visited)
    
    def nearest_neighbors(self, x: float, y: float, k: int = 5, 
                         max_distance: float = float('inf')) -> List[Tuple[Any, float]]:
        """
        Find k nearest neighbors to a point.
        
        Args:
            x, y: Query point coordinates
            k: Number of neighbors to find
            max_distance: Maximum search distance
            
        Returns:
            List of (object, distance) tuples sorted by distance
        """
        import heapq
        
        start_time = time.time()
        candidates = []  # Max heap of (-distance, object)
        
        try:
            # Expand search area progressively
            search_radius = 10.0  # Start with small radius
            while len(candidates) < k and search_radius <= max_distance:
                search_bounds = BoundingBox2D(
                    x - search_radius, y - search_radius,
                    x + search_radius, y + search_radius
                )
                
                objects = self.query_range(search_bounds)
                
                for obj in objects:
                    distance = obj.distance_to_point_2d(x, y)
                    if distance <= max_distance:
                        if len(candidates) < k:
                            heapq.heappush(candidates, (-distance, obj))
                        elif distance < -candidates[0][0]:
                            heapq.heapreplace(candidates, (-distance, obj))
                
                search_radius *= 2.0
            
            # Convert to sorted list
            results = [(obj, -dist) for dist, obj in candidates]
            results.sort(key=lambda x: x[1])
            
            elapsed = time.time() - start_time
            logger.debug(f"Nearest neighbor search found {len(results)} objects "
                        f"in {elapsed:.4f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"Nearest neighbor search failed: {e}")
            return []
    
    def find_plan_view_conflicts(self, arxobject: Any, tolerance: float = 0.001) -> List[Tuple[Any, str]]:
        """
        Find 2D plan view conflicts with given ArxObject.
        
        Args:
            arxobject: ArxObject to check for conflicts
            tolerance: Minimum distance tolerance for conflicts
            
        Returns:
            List of (conflicting_object, conflict_type) tuples
        """
        start_time = time.time()
        conflicts = []
        
        try:
            # Get plan view bounds and expand by tolerance
            obj_bounds = arxobject.get_plan_view_bounds()
            expanded_bounds = obj_bounds.expand_by_distance(tolerance)
            
            # Query potential conflicts
            candidates = self.query_range(expanded_bounds)
            
            # Detailed conflict analysis
            for candidate in candidates:
                if candidate.id == arxobject.id:
                    continue
                
                conflict_type = self._analyze_plan_view_conflict(arxobject, candidate, tolerance)
                if conflict_type:
                    conflicts.append((candidate, conflict_type))
            
            elapsed = time.time() - start_time
            logger.debug(f"Plan view conflict detection for {arxobject.id} found "
                        f"{len(conflicts)} conflicts in {elapsed:.4f}s")
            
            return conflicts
            
        except Exception as e:
            logger.error(f"Plan view conflict detection failed: {e}")
            return []
    
    def _analyze_plan_view_conflict(self, obj1: Any, obj2: Any, tolerance: float) -> Optional[str]:
        """Analyze plan view conflict type between two objects."""
        # Check if objects are on same floor
        if obj1.floor_id != obj2.floor_id:
            return None
        
        bounds1 = obj1.get_plan_view_bounds()
        bounds2 = obj2.get_plan_view_bounds()
        
        if bounds1.intersects(bounds2):
            # Determine conflict type based on system types
            system1 = obj1.get_system_type()
            system2 = obj2.get_system_type()
            
            if system1 == system2:
                return "same_system_overlap"
            else:
                return f"{system1}_{system2}_conflict"
        
        # Check proximity conflicts
        center1 = bounds1.center()
        center2 = bounds2.center()
        distance = math.sqrt((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)
        
        if distance < tolerance:
            return "proximity_conflict"
        
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get spatial index statistics."""
        def count_nodes_and_entries(node: RTreeNode) -> Tuple[int, int, int]:
            """Count nodes, entries, and calculate depth."""
            if node.is_leaf:
                return 1, len(node.entries), 1
            else:
                total_nodes = 1
                total_entries = len(node.entries)
                max_depth = 1
                
                for entry in node.entries:
                    child_nodes, child_entries, child_depth = count_nodes_and_entries(entry.child_node)
                    total_nodes += child_nodes
                    total_entries += child_entries
                    max_depth = max(max_depth, child_depth + 1)
                
                return total_nodes, total_entries, max_depth
        
        total_nodes, total_entries, max_depth = count_nodes_and_entries(self.root)
        
        return {
            'object_count': self.object_count,
            'total_nodes': total_nodes,
            'total_entries': total_entries,
            'tree_height': self.height,
            'max_depth_measured': max_depth,
            'max_entries_per_node': self.max_entries,
            'query_stats': self.query_stats.copy(),
            'average_entries_per_node': total_entries / total_nodes if total_nodes > 0 else 0,
            'fill_factor': (total_entries / (total_nodes * self.max_entries)) if total_nodes > 0 else 0
        }
    
    def _update_query_stats(self, elapsed_time: float, nodes_visited: int) -> None:
        """Update query performance statistics."""
        self.query_stats['total_queries'] += 1
        self.query_stats['nodes_visited'] += nodes_visited
        
        # Update average query time
        total_time = (self.query_stats['average_query_time'] * 
                     (self.query_stats['total_queries'] - 1) + elapsed_time)
        self.query_stats['average_query_time'] = total_time / self.query_stats['total_queries']
    
    def optimize(self) -> None:
        """Optimize R-tree by rebuilding with better spatial locality."""
        logger.info("Starting R-tree optimization...")
        start_time = time.time()
        
        # Collect all objects
        all_objects = []
        self._collect_all_objects(self.root, all_objects)
        
        # Rebuild tree
        self.root = RTreeNode(is_leaf=True, max_entries=self.max_entries)
        self.object_count = 0
        self.height = 1
        
        # Reinsert with spatial sorting
        self.batch_insert(all_objects)
        
        elapsed = time.time() - start_time
        logger.info(f"R-tree optimization completed in {elapsed:.2f}s")
    
    def _collect_all_objects(self, node: RTreeNode, objects: List[Any]) -> None:
        """Recursively collect all objects from tree."""
        if node.is_leaf:
            for entry in node.entries:
                if entry.arxobject:
                    objects.append(entry.arxobject)
        else:
            for entry in node.entries:
                self._collect_all_objects(entry.child_node, objects)
    
    def clear(self) -> None:
        """Clear all objects from spatial index."""
        with self._lock:
            self.root = RTreeNode(is_leaf=True, max_entries=self.max_entries)
            self.object_count = 0
            self.height = 1
            self.query_stats = {
                'total_queries': 0,
                'average_query_time': 0.0,
                'nodes_visited': 0,
                'cache_hits': 0,
                'cache_misses': 0
            }
        
        logger.info("Cleared R-tree spatial index")
    
    def __len__(self) -> int:
        """Return number of objects in spatial index."""
        return self.object_count
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)