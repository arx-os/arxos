"""
Advanced wall merging with proper endpoint connection and room detection
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from collections import defaultdict
import math
import numpy as np

class AdvancedWallMerger:
    """
    Intelligently connects wall segments into continuous paths and detects rooms
    """
    
    def __init__(self, 
                 snap_distance: float = 10.0,  # Distance to snap endpoints together
                 angle_tolerance: float = 5.0,  # Degrees
                 min_wall_length: float = 50.0):
        self.snap_distance = snap_distance
        self.angle_tolerance = angle_tolerance
        self.min_wall_length = min_wall_length
        
    def merge_walls(self, walls: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Merge wall segments into continuous paths and detect rooms
        
        Returns:
            Tuple of (merged_walls, detected_rooms)
        """
        print(f"Starting advanced wall merge with {len(walls)} walls")
        
        # Step 1: Snap nearby endpoints together
        walls = self._snap_endpoints(walls)
        
        # Step 2: Build connectivity graph
        graph = self._build_connectivity_graph(walls)
        
        # Step 3: Find continuous wall paths
        wall_paths = self._extract_wall_paths(graph, walls)
        
        # Step 4: Find closed loops (rooms)
        rooms = self._detect_rooms_from_paths(wall_paths)
        
        # Step 5: Convert paths to wall objects
        merged_walls = self._paths_to_walls(wall_paths)
        
        print(f"Result: {len(merged_walls)} merged walls, {len(rooms)} rooms detected")
        
        return merged_walls, rooms
    
    def _snap_endpoints(self, walls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Snap nearby wall endpoints together to ensure connectivity"""
        # Create endpoint index
        endpoint_map = {}  # Maps endpoint to list of walls using it
        
        for wall in walls:
            coords = self._get_coordinates(wall)
            if coords:
                start = tuple(coords[0])
                end = tuple(coords[-1])
                
                # Find nearby endpoints to snap to
                snapped_start = self._find_snap_point(start, endpoint_map.keys())
                snapped_end = self._find_snap_point(end, endpoint_map.keys())
                
                # Update wall coordinates with snapped points
                if snapped_start != start or snapped_end != end:
                    coords[0] = list(snapped_start)
                    coords[-1] = list(snapped_end)
                    self._update_coordinates(wall, coords)
                
                # Update endpoint map
                if snapped_start not in endpoint_map:
                    endpoint_map[snapped_start] = []
                if snapped_end not in endpoint_map:
                    endpoint_map[snapped_end] = []
                    
                endpoint_map[snapped_start].append(wall)
                endpoint_map[snapped_end].append(wall)
        
        return walls
    
    def _find_snap_point(self, point: Tuple[float, float], 
                        existing_points: List[Tuple[float, float]]) -> Tuple[float, float]:
        """Find existing point within snap distance or return original"""
        for existing in existing_points:
            dist = math.sqrt((point[0] - existing[0])**2 + (point[1] - existing[1])**2)
            if dist <= self.snap_distance:
                return existing
        return point
    
    def _build_connectivity_graph(self, walls: List[Dict[str, Any]]) -> Dict:
        """Build graph showing how walls connect at endpoints"""
        graph = {
            'nodes': {},  # endpoint -> connected walls
            'edges': {},  # wall -> (start_point, end_point)
        }
        
        for wall in walls:
            coords = self._get_coordinates(wall)
            if coords:
                start = tuple(coords[0])
                end = tuple(coords[-1])
                
                # Store edge info
                wall_id = wall.get('id', str(id(wall)))
                graph['edges'][wall_id] = (start, end, wall)
                
                # Update nodes
                if start not in graph['nodes']:
                    graph['nodes'][start] = []
                if end not in graph['nodes']:
                    graph['nodes'][end] = []
                    
                graph['nodes'][start].append(wall_id)
                graph['nodes'][end].append(wall_id)
        
        return graph
    
    def _extract_wall_paths(self, graph: Dict, walls: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Extract continuous wall paths from the connectivity graph"""
        paths = []
        visited_edges = set()
        
        # Start from each unvisited edge
        for wall_id, (start, end, wall) in graph['edges'].items():
            if wall_id in visited_edges:
                continue
            
            # Try to extend path in both directions
            path = self._extend_path(graph, wall_id, visited_edges)
            if path:
                paths.append(path)
        
        return paths
    
    def _extend_path(self, graph: Dict, start_wall_id: str, visited: Set[str]) -> List[Dict[str, Any]]:
        """Extend a path from a starting wall in both directions"""
        if start_wall_id in visited:
            return []
        
        path = []
        current_walls = [start_wall_id]
        
        # Keep extending until we can't anymore or find a loop
        while current_walls:
            wall_id = current_walls.pop(0)
            if wall_id in visited:
                continue
                
            visited.add(wall_id)
            start, end, wall = graph['edges'][wall_id]
            path.append(wall)
            
            # Find connected walls that continue the path
            for next_wall_id in graph['nodes'].get(end, []):
                if next_wall_id not in visited:
                    # Check if angle is reasonable (not a sharp turn)
                    if self._is_reasonable_continuation(graph, wall_id, next_wall_id):
                        current_walls.append(next_wall_id)
        
        return path if len(path) > 1 else [graph['edges'][start_wall_id][2]] if start_wall_id not in visited else []
    
    def _is_reasonable_continuation(self, graph: Dict, wall1_id: str, wall2_id: str) -> bool:
        """Check if wall2 is a reasonable continuation of wall1"""
        _, _, wall1 = graph['edges'][wall1_id]
        _, _, wall2 = graph['edges'][wall2_id]
        
        coords1 = self._get_coordinates(wall1)
        coords2 = self._get_coordinates(wall2)
        
        if not coords1 or not coords2:
            return False
        
        # Calculate angles
        angle1 = math.atan2(coords1[-1][1] - coords1[0][1], coords1[-1][0] - coords1[0][0])
        angle2 = math.atan2(coords2[-1][1] - coords2[0][1], coords2[-1][0] - coords2[0][0])
        
        angle_diff = abs(math.degrees(angle1 - angle2))
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
        
        # Allow straight lines or perpendicular turns (common in buildings)
        return angle_diff < self.angle_tolerance or abs(angle_diff - 90) < self.angle_tolerance
    
    def _detect_rooms_from_paths(self, wall_paths: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Detect closed rooms from wall paths"""
        rooms = []
        
        for i, path in enumerate(wall_paths):
            # Check if path forms a closed loop
            if len(path) >= 3:  # Need at least 3 walls for a room
                first_coords = self._get_coordinates(path[0])
                last_coords = self._get_coordinates(path[-1])
                
                if first_coords and last_coords:
                    # Check if endpoints connect
                    start_point = first_coords[0]
                    end_point = last_coords[-1]
                    
                    dist = math.sqrt((start_point[0] - end_point[0])**2 + 
                                   (start_point[1] - end_point[1])**2)
                    
                    if dist <= self.snap_distance * 2:  # Closed loop
                        room = self._create_room_from_walls(path, i)
                        if room:
                            rooms.append(room)
        
        return rooms
    
    def _create_room_from_walls(self, walls: List[Dict[str, Any]], room_id: int) -> Optional[Dict[str, Any]]:
        """Create a room object from a list of walls forming a closed loop"""
        # Collect all points
        points = []
        for wall in walls:
            coords = self._get_coordinates(wall)
            if coords:
                points.extend(coords)
        
        if len(points) < 3:
            return None
        
        # Remove duplicates while preserving order
        unique_points = []
        seen = set()
        for p in points:
            p_tuple = tuple(p)
            if p_tuple not in seen:
                unique_points.append(p)
                seen.add(p_tuple)
        
        # Ensure closed polygon
        if unique_points[0] != unique_points[-1]:
            unique_points.append(unique_points[0])
        
        return {
            'id': f"room_{room_id}",
            'type': 'room',
            'geometry': {
                'type': 'Polygon',
                'coordinates': [unique_points]
            },
            'confidence': {
                'overall': 0.85,
                'classification': 0.9,
                'position': 0.85,
                'properties': 0.8
            },
            'data': {
                'wall_count': len(walls),
                'area': self._calculate_area(unique_points),
                'perimeter': self._calculate_perimeter(unique_points)
            },
            'metadata': {
                'source': 'advanced_wall_merger',
                'detection_method': 'closed_loop'
            }
        }
    
    def _paths_to_walls(self, wall_paths: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Convert wall paths to merged wall objects"""
        merged_walls = []
        
        for path_id, path in enumerate(wall_paths):
            if len(path) == 1:
                # Single wall, no merging needed
                merged_walls.append(path[0])
            else:
                # Merge multiple walls into continuous path
                merged_wall = self._merge_path_to_wall(path, path_id)
                if merged_wall:
                    merged_walls.append(merged_wall)
        
        return merged_walls
    
    def _merge_path_to_wall(self, path: List[Dict[str, Any]], path_id: int) -> Optional[Dict[str, Any]]:
        """Merge a path of walls into a single multi-segment wall"""
        # Collect all points in order
        all_points = []
        total_confidence = 0
        
        for wall in path:
            coords = self._get_coordinates(wall)
            if coords:
                # Add points, avoiding duplicates at connections
                if not all_points:
                    all_points.extend(coords)
                else:
                    # Check if first point matches last point of previous
                    if coords[0] == all_points[-1]:
                        all_points.extend(coords[1:])
                    else:
                        all_points.extend(coords)
                
                # Accumulate confidence
                conf = wall.get('confidence', {})
                if isinstance(conf, dict):
                    total_confidence += conf.get('overall', 0.7)
                else:
                    total_confidence += 0.7
        
        if len(all_points) < 2:
            return None
        
        return {
            'id': f"merged_path_{path_id}",
            'type': 'wall',
            'geometry': {
                'type': 'LineString',
                'coordinates': all_points
            },
            'confidence': {
                'overall': total_confidence / len(path),
                'classification': 0.9,
                'position': 0.85,
                'properties': 0.8
            },
            'data': {
                'merged_from': len(path),
                'length': self._calculate_path_length(all_points),
                'segments': len(all_points) - 1
            },
            'metadata': {
                'source': 'advanced_wall_merger',
                'merge_type': 'continuous_path'
            }
        }
    
    def _get_coordinates(self, wall: Dict[str, Any]) -> Optional[List[List[float]]]:
        """Extract coordinates from wall object"""
        geom = wall.get('geometry', {})
        if geom.get('type') == 'LineString':
            return geom.get('coordinates', [])
        return None
    
    def _update_coordinates(self, wall: Dict[str, Any], coords: List[List[float]]) -> None:
        """Update wall coordinates"""
        if 'geometry' in wall:
            wall['geometry']['coordinates'] = coords
    
    def _calculate_area(self, points: List[List[float]]) -> float:
        """Calculate polygon area using shoelace formula"""
        if len(points) < 3:
            return 0
        
        area = 0
        for i in range(len(points) - 1):
            area += points[i][0] * points[i+1][1]
            area -= points[i+1][0] * points[i][1]
        
        return abs(area) / 2
    
    def _calculate_perimeter(self, points: List[List[float]]) -> float:
        """Calculate polygon perimeter"""
        perimeter = 0
        for i in range(len(points) - 1):
            dist = math.sqrt((points[i+1][0] - points[i][0])**2 + 
                           (points[i+1][1] - points[i][1])**2)
            perimeter += dist
        return perimeter
    
    def _calculate_path_length(self, points: List[List[float]]) -> float:
        """Calculate total length of a path"""
        length = 0
        for i in range(len(points) - 1):
            dist = math.sqrt((points[i+1][0] - points[i][0])**2 + 
                           (points[i+1][1] - points[i][1])**2)
            length += dist
        return length