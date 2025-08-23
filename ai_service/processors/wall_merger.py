"""
Wall merging algorithm for connecting fragmented wall segments
Implements intelligent line merging based on proximity and angle
"""

import math
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from collections import defaultdict

class WallMerger:
    """
    Merges fragmented wall segments into continuous walls
    Uses proximity and angle-based algorithms
    """
    
    def __init__(self, 
                 angle_tolerance: float = 5.0,  # degrees
                 distance_tolerance: float = 50.0,  # mm
                 min_wall_length: float = 100.0):  # mm
        self.angle_tolerance = angle_tolerance
        self.distance_tolerance = distance_tolerance
        self.min_wall_length = min_wall_length
        
    def merge_walls(self, arxobjects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Main entry point for wall merging
        
        Args:
            arxobjects: List of ArxObject dictionaries
            
        Returns:
            List of ArxObjects with merged walls
        """
        # Separate walls from other objects
        walls = []
        other_objects = []
        
        for obj in arxobjects:
            if self._is_wall(obj):
                walls.append(obj)
            else:
                other_objects.append(obj)
        
        # Group walls by proximity and angle
        wall_groups = self._group_collinear_walls(walls)
        
        # Merge each group into continuous segments
        merged_walls = []
        for group in wall_groups:
            merged = self._merge_wall_group(group)
            if merged:
                merged_walls.append(merged)
        
        # Combine merged walls with other objects
        return merged_walls + other_objects
    
    def _is_wall(self, obj: Dict[str, Any]) -> bool:
        """Check if object is a wall"""
        obj_type = obj.get('type', '').lower()
        return 'wall' in obj_type or 'line' in obj_type
    
    def _get_wall_endpoints(self, wall: Dict[str, Any]) -> Optional[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """Extract start and end points from wall object"""
        geometry = wall.get('geometry', {})
        
        # Handle LineString geometry
        if geometry.get('type') == 'LineString':
            coords = geometry.get('coordinates', [])
            if len(coords) >= 2:
                return (tuple(coords[0][:2]), tuple(coords[-1][:2]))
        
        # Handle position-based walls
        if 'position' in wall:
            pos = wall['position']
            x, y = pos.get('x', 0), pos.get('y', 0)
            
            # Try to get dimensions
            dims = wall.get('dimensions', {})
            width = dims.get('width', 100)
            height = dims.get('height', 10)
            
            # Assume horizontal wall by default
            if width > height:
                return ((x, y), (x + width, y))
            else:
                return ((x, y), (x, y + height))
        
        return None
    
    def _calculate_angle(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculate angle between two points in degrees"""
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        return math.degrees(math.atan2(dy, dx))
    
    def _distance_between_points(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two points"""
        return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
    
    def _are_collinear(self, wall1: Dict[str, Any], wall2: Dict[str, Any]) -> bool:
        """Check if two walls are collinear (on the same line)"""
        endpoints1 = self._get_wall_endpoints(wall1)
        endpoints2 = self._get_wall_endpoints(wall2)
        
        if not endpoints1 or not endpoints2:
            return False
        
        # Calculate angles
        angle1 = self._calculate_angle(endpoints1[0], endpoints1[1])
        angle2 = self._calculate_angle(endpoints2[0], endpoints2[1])
        
        # Normalize angle difference
        angle_diff = abs(angle1 - angle2)
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
        
        # Check if angles are similar
        if angle_diff > self.angle_tolerance and angle_diff < (180 - self.angle_tolerance):
            return False
        
        # Check if walls are close enough
        min_distance = float('inf')
        for p1 in endpoints1:
            for p2 in endpoints2:
                dist = self._distance_between_points(p1, p2)
                min_distance = min(min_distance, dist)
        
        return min_distance <= self.distance_tolerance
    
    def _group_collinear_walls(self, walls: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Group walls that are collinear and close to each other"""
        groups = []
        used = set()
        
        for i, wall1 in enumerate(walls):
            if i in used:
                continue
            
            group = [wall1]
            used.add(i)
            
            # Find all walls collinear with this one
            for j, wall2 in enumerate(walls):
                if j in used:
                    continue
                
                # Check if wall2 is collinear with any wall in the group
                for wall_in_group in group:
                    if self._are_collinear(wall_in_group, wall2):
                        group.append(wall2)
                        used.add(j)
                        break
            
            groups.append(group)
        
        return groups
    
    def _merge_wall_group(self, group: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Merge a group of collinear walls into a single wall"""
        if len(group) == 0:
            return None
        
        if len(group) == 1:
            return group[0]
        
        # Collect all endpoints
        all_points = []
        total_confidence = 0.0
        
        for wall in group:
            endpoints = self._get_wall_endpoints(wall)
            if endpoints:
                all_points.extend(endpoints)
            
            # Track confidence
            confidence = wall.get('confidence', {})
            if isinstance(confidence, dict):
                total_confidence += confidence.get('overall', 0.5)
            else:
                total_confidence += float(confidence) if confidence else 0.5
        
        if len(all_points) < 2:
            return group[0]
        
        # Find the extreme points (furthest apart)
        max_dist = 0
        best_start = all_points[0]
        best_end = all_points[1]
        
        for i, p1 in enumerate(all_points):
            for j, p2 in enumerate(all_points[i+1:], i+1):
                dist = self._distance_between_points(p1, p2)
                if dist > max_dist:
                    max_dist = dist
                    best_start = p1
                    best_end = p2
        
        # Check minimum wall length
        if max_dist < self.min_wall_length:
            return None
        
        # Create merged wall
        merged_wall = {
            'id': f"merged_wall_{hash(str(group))}",
            'type': 'wall',
            'geometry': {
                'type': 'LineString',
                'coordinates': [
                    [best_start[0], best_start[1]],
                    [best_end[0], best_end[1]]
                ]
            },
            'confidence': {
                'overall': total_confidence / len(group),
                'classification': 0.9,  # High confidence it's a wall after merging
                'position': 0.8,
                'properties': 0.7
            },
            'data': {
                'merged_from': len(group),
                'length': max_dist,
                'thickness': 10,  # Default wall thickness
                'material': 'unknown'
            },
            'metadata': {
                'source': 'wall_merger',
                'merged_count': len(group)
            }
        }
        
        return merged_wall
    
    def detect_rooms(self, walls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect rooms from closed wall loops
        
        Args:
            walls: List of wall ArxObjects
            
        Returns:
            List of room ArxObjects
        """
        rooms = []
        
        # Build a graph of wall connections
        wall_graph = self._build_wall_graph(walls)
        
        # Find closed loops in the graph
        closed_loops = self._find_closed_loops(wall_graph)
        
        # Convert loops to room objects
        for i, loop in enumerate(closed_loops):
            room = self._create_room_from_loop(loop, i)
            if room:
                rooms.append(room)
        
        return rooms
    
    def _build_wall_graph(self, walls: List[Dict[str, Any]]) -> Dict[Tuple[float, float], List[Tuple[float, float]]]:
        """Build adjacency graph from wall endpoints"""
        graph = defaultdict(list)
        
        for wall in walls:
            endpoints = self._get_wall_endpoints(wall)
            if endpoints:
                start, end = endpoints
                # Round coordinates to avoid floating point issues
                start = (round(start[0], 1), round(start[1], 1))
                end = (round(end[0], 1), round(end[1], 1))
                
                graph[start].append(end)
                graph[end].append(start)
        
        return graph
    
    def _find_closed_loops(self, graph: Dict) -> List[List[Tuple[float, float]]]:
        """Find closed loops in the wall graph using DFS"""
        closed_loops = []
        visited_edges = set()
        
        def dfs_cycle(start, current, path, visited_in_path):
            if len(path) > 2 and current == start:
                # Found a cycle
                return [path[:]]
            
            if len(path) > 20:  # Limit search depth
                return []
            
            cycles = []
            for neighbor in graph.get(current, []):
                edge = tuple(sorted([current, neighbor]))
                if edge not in visited_in_path:
                    new_visited = visited_in_path.copy()
                    new_visited.add(edge)
                    cycles.extend(dfs_cycle(start, neighbor, path + [neighbor], new_visited))
            
            return cycles
        
        # Try to find cycles starting from each node
        for node in graph:
            cycles = dfs_cycle(node, node, [node], set())
            for cycle in cycles:
                # Normalize cycle (remove duplicates, ensure clockwise)
                if len(cycle) >= 4:  # Minimum 4 points for a room
                    cycle_tuple = tuple(sorted(cycle))
                    if cycle_tuple not in visited_edges:
                        closed_loops.append(cycle)
                        visited_edges.add(cycle_tuple)
        
        return closed_loops
    
    def _create_room_from_loop(self, loop: List[Tuple[float, float]], room_id: int) -> Optional[Dict[str, Any]]:
        """Create a room ArxObject from a closed loop of points"""
        if len(loop) < 4:
            return None
        
        # Calculate room area (using shoelace formula)
        area = 0
        for i in range(len(loop)):
            j = (i + 1) % len(loop)
            area += loop[i][0] * loop[j][1]
            area -= loop[j][0] * loop[i][1]
        area = abs(area) / 2.0
        
        # Filter out very small or very large areas
        if area < 1000000 or area > 100000000:  # 1m² to 100m²
            return None
        
        # Calculate centroid
        cx = sum(p[0] for p in loop) / len(loop)
        cy = sum(p[1] for p in loop) / len(loop)
        
        room = {
            'id': f"room_{room_id}",
            'type': 'room',
            'geometry': {
                'type': 'Polygon',
                'coordinates': [loop]
            },
            'confidence': {
                'overall': 0.7,  # Moderate confidence for detected rooms
                'classification': 0.8,
                'position': 0.7,
                'properties': 0.6
            },
            'data': {
                'area': area / 1000000,  # Convert to m²
                'perimeter': sum(self._distance_between_points(loop[i], loop[(i+1)%len(loop)]) 
                               for i in range(len(loop))),
                'centroid': [cx, cy],
                'vertex_count': len(loop)
            },
            'metadata': {
                'source': 'room_detection',
                'detection_method': 'closed_loop'
            }
        }
        
        return room