"""
Enhanced Spatial & Topological Reasoning System for BIM Models

This module provides comprehensive spatial reasoning capabilities including:
- Spatial indexing (R-tree and grid-based)
- Topological validation (enclosure, adjacency, connectivity)
- Zone & area calculation with spatial hierarchies
- Advanced spatial queries and analysis
"""

import math
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Set, Any, Union
from enum import Enum
from dataclasses import dataclass
from collections import defaultdict, deque
import numpy as np
from shapely.geometry import Point, Polygon, LineString, MultiPolygon, box
from shapely.ops import unary_union
from shapely.validation import make_valid
from shapely.strtree import STRtree
from shapely.prepared import prep

from structlog import get_logger

from pydantic import BaseModel, Field, field_validator, model_validator

from ..models.bim import (
    BIMElementBase, BIMModel, Geometry, GeometryType, SystemType,
    Room, Wall, Door, Window, Device, RoomType
)

logger = get_logger()

class SpatialIndexType(str, Enum):
    """Types of spatial indexing."""
    R_TREE = "r_tree"
    GRID = "grid"
    QUAD_TREE = "quad_tree"

class TopologyType(str, Enum):
    """Types of topological relationships."""
    ENCLOSURE = "enclosure"      # Room enclosed by walls
    ADJACENCY = "adjacency"      # Doors connecting rooms
    CONNECTIVITY = "connectivity" # Pipes, ducts, electrical
    CONTAINMENT = "containment"  # Elements inside rooms
    OVERLAP = "overlap"          # Elements overlapping
    DISJOINT = "disjoint"        # No spatial relationship

class SpatialHierarchyLevel(str, Enum):
    """Levels in spatial hierarchy."""
    BUILDING = "building"
    FLOOR = "floor"
    ZONE = "zone"
    ROOM = "room"
    SUBZONE = "subzone"

@dataclass
class SpatialIndex:
    """Spatial index for fast spatial queries."""
    index_type: SpatialIndexType
    bounds: Tuple[float, float, float, float]  # (min_x, min_y, max_x, max_y)
    elements: Dict[str, Any]  # element_id -> geometry
    tree: Optional[Any] = None  # R-tree or grid structure
    grid_cells: Optional[Dict[Tuple[int, int], Set[str]]] = None  # Grid cell -> element_ids

@dataclass
class TopologyValidation:
    """Topology validation result."""
    is_valid: bool
    violations: List[str]
    suggestions: List[str]
    score: float  # 0.0 to 1.0

@dataclass
class ZoneCalculation:
    """Zone calculation result."""
    zone_id: str
    zone_type: str
    area: float
    volume: Optional[float]
    elements: List[str]
    hierarchy_level: SpatialHierarchyLevel
    parent_zone: Optional[str]
    child_zones: List[str]

class EnhancedSpatialReasoningEngine:
    """Enhanced spatial reasoning engine with indexing and topology."""
    
    def __init__(self, bim_model: Optional[BIMModel] = None):
        self.bim_model = bim_model
        self.spatial_indices: Dict[SpatialIndexType, SpatialIndex] = {}
        self.topology_cache: Dict[str, TopologyValidation] = {}
        self.zone_calculations: Dict[str, ZoneCalculation] = {}
        self.hierarchy_cache: Dict[str, Dict] = {}
        
        # Performance tracking
        self.stats = {
            'spatial_queries': 0,
            'topology_validations': 0,
            'zone_calculations': 0,
            'index_updates': 0,
            'query_time_avg': 0.0
        }
    
    def build_spatial_index(self, index_type: SpatialIndexType = SpatialIndexType.R_TREE) -> SpatialIndex:
        """Build a spatial index for fast spatial queries."""
        logger.info(f"Building {index_type} spatial index...")
        
        # Collect all geometries
        elements = {}
        bounds = None
        
        # Get all spatial elements
        all_elements = []
        if self.bim_model:
            all_elements.extend(self.bim_model.rooms)
            all_elements.extend(self.bim_model.walls)
            all_elements.extend(self.bim_model.doors)
            all_elements.extend(self.bim_model.windows)
            all_elements.extend(self.bim_model.devices)
        
        for element in all_elements:
            if hasattr(element, 'geometry') and element.geometry:
                shapely_geom = self._convert_to_shapely(element.geometry)
                if shapely_geom:
                    elements[element.id] = shapely_geom
                    
                    # Update bounds
                    if bounds is None:
                        bounds = shapely_geom.bounds
                    else:
                        min_x = min(bounds[0], shapely_geom.bounds[0])
                        min_y = min(bounds[1], shapely_geom.bounds[1])
                        max_x = max(bounds[2], shapely_geom.bounds[2])
                        max_y = max(bounds[3], shapely_geom.bounds[3])
                        bounds = (min_x, min_y, max_x, max_y)
        
        if not bounds:
            bounds = (0, 0, 100, 100)  # Default bounds
        
        # Create index based on type
        if index_type == SpatialIndexType.R_TREE:
            tree = STRtree(list(elements.values()))
            spatial_index = SpatialIndex(
                index_type=index_type,
                bounds=bounds,
                elements=elements,
                tree=tree
            )
        elif index_type == SpatialIndexType.GRID:
            grid_cells = self._build_grid_index(elements, bounds)
            spatial_index = SpatialIndex(
                index_type=index_type,
                bounds=bounds,
                elements=elements,
                grid_cells=grid_cells
            )
        else:
            raise ValueError(f"Unsupported index type: {index_type}")
        
        self.spatial_indices[index_type] = spatial_index
        self.stats['index_updates'] += 1
        
        logger.info(f"Built {index_type} index with {len(elements)} elements")
        return spatial_index
    
    def _build_grid_index(self, elements: Dict[str, Any], bounds: Tuple[float, float, float, float]) -> Dict[Tuple[int, int], Set[str]]:
        """Build a grid-based spatial index."""
        grid_cells = defaultdict(set)
        cell_size = 10.0  # 10 unit grid cells
        
        min_x, min_y, max_x, max_y = bounds
        grid_width = int((max_x - min_x) / cell_size) + 1
        grid_height = int((max_y - min_y) / cell_size) + 1
        
        for element_id, geometry in elements.items():
            # Find all grid cells that intersect with this geometry
            geom_bounds = geometry.bounds
            min_cell_x = max(0, int((geom_bounds[0] - min_x) / cell_size))
            max_cell_x = min(grid_width - 1, int((geom_bounds[2] - min_x) / cell_size))
            min_cell_y = max(0, int((geom_bounds[1] - min_y) / cell_size))
            max_cell_y = min(grid_height - 1, int((geom_bounds[3] - min_y) / cell_size))
            
            for cell_x in range(min_cell_x, max_cell_x + 1):
                for cell_y in range(min_cell_y, max_cell_y + 1):
                    grid_cells[(cell_x, cell_y)].add(element_id)
        
        return dict(grid_cells)
    
    def spatial_query(self, query_geometry: Any, index_type: SpatialIndexType = SpatialIndexType.R_TREE) -> List[str]:
        """Perform a spatial query using the specified index."""
        if index_type not in self.spatial_indices:
            self.build_spatial_index(index_type)
        
        spatial_index = self.spatial_indices[index_type]
        start_time = time.time()
        
        if index_type == SpatialIndexType.R_TREE:
            # Use R-tree for intersection queries
            results = []
            for element_id, geometry in spatial_index.elements.items():
                if query_geometry.intersects(geometry):
                    results.append(element_id)
        elif index_type == SpatialIndexType.GRID:
            # Use grid for proximity queries
            results = self._grid_query(query_geometry, spatial_index)
        else:
            results = []
        
        query_time = time.time() - start_time
        self.stats['spatial_queries'] += 1
        self.stats['query_time_avg'] = (
            (self.stats['query_time_avg'] * (self.stats['spatial_queries'] - 1) + query_time) / 
            self.stats['spatial_queries']
        )
        
        return results
    
    def _grid_query(self, query_geometry: Any, spatial_index: SpatialIndex) -> List[str]:
        """Perform a query using the grid index."""
        if not spatial_index.grid_cells:
            return []
        
        results = set()
        query_bounds = query_geometry.bounds
        cell_size = 10.0
        
        # Find grid cells that intersect with query
        min_x, min_y, max_x, max_y = spatial_index.bounds
        min_cell_x = max(0, int((query_bounds[0] - min_x) / cell_size))
        max_cell_x = min(len(spatial_index.grid_cells), int((query_bounds[2] - min_x) / cell_size))
        min_cell_y = max(0, int((query_bounds[1] - min_y) / cell_size))
        max_cell_y = min(len(spatial_index.grid_cells), int((query_bounds[3] - min_y) / cell_size))
        
        for cell_x in range(min_cell_x, max_cell_x + 1):
            for cell_y in range(min_cell_y, max_cell_y + 1):
                cell_key = (cell_x, cell_y)
                if cell_key in spatial_index.grid_cells:
                    results.update(spatial_index.grid_cells[cell_key])
        
        return list(results)
    
    def validate_topology(self, element_id: str) -> TopologyValidation:
        """Validate topological relationships for an element."""
        if element_id in self.topology_cache:
            return self.topology_cache[element_id]
        
        element = self.bim_model.get_element_by_id(element_id) if self.bim_model else None
        if not element:
            return TopologyValidation(False, ["Element not found"], [], 0.0)
        
        violations = []
        suggestions = []
        score = 1.0
        
        # Validate based on element type
        if isinstance(element, Room):
            room_validation = self._validate_room_topology(element)
            violations.extend(room_validation['violations'])
            suggestions.extend(room_validation['suggestions'])
            score = min(score, room_validation['score'])
        
        elif isinstance(element, Door):
            door_validation = self._validate_door_topology(element)
            violations.extend(door_validation['violations'])
            suggestions.extend(door_validation['suggestions'])
            score = min(score, door_validation['score'])
        
        elif isinstance(element, Wall):
            wall_validation = self._validate_wall_topology(element)
            violations.extend(wall_validation['violations'])
            suggestions.extend(wall_validation['suggestions'])
            score = min(score, wall_validation['score'])
        
        elif isinstance(element, Device):
            device_validation = self._validate_device_topology(element)
            violations.extend(device_validation['violations'])
            suggestions.extend(device_validation['suggestions'])
            score = min(score, device_validation['score'])
        
        validation = TopologyValidation(
            is_valid=len(violations) == 0,
            violations=violations,
            suggestions=suggestions,
            score=score
        )
        
        self.topology_cache[element_id] = validation
        self.stats['topology_validations'] += 1
        
        return validation
    
    def _validate_room_topology(self, room: Room) -> Dict[str, Any]:
        """Validate room topology (enclosure by walls, proper doors)."""
        violations = []
        suggestions = []
        score = 1.0
        
        room_geom = self._convert_to_shapely(room.geometry)
        if not room_geom:
            return {'violations': ["Invalid room geometry"], 'suggestions': [], 'score': 0.0}
        
        # Check if room is enclosed by walls
        walls_around_room = []
        for wall in self.bim_model.walls:
            wall_geom = self._convert_to_shapely(wall.geometry)
            if wall_geom and room_geom.touches(wall_geom):
                walls_around_room.append(wall)
        
        if len(walls_around_room) < 3:  # Need at least 3 walls for enclosure
            violations.append(f"Room {room.id} is not properly enclosed by walls")
            suggestions.append(f"Add more walls around room {room.id}")
            score = 0.5
        
        # Check for doors
        doors_in_room = []
        for door in self.bim_model.doors:
            door_geom = self._convert_to_shapely(door.geometry)
            if door_geom and room_geom.contains(door_geom):
                doors_in_room.append(door)
        
        if len(doors_in_room) == 0:
            violations.append(f"Room {room.id} has no doors")
            suggestions.append(f"Add at least one door to room {room.id}")
            score = 0.7
        
        return {'violations': violations, 'suggestions': suggestions, 'score': score}
    
    def _validate_door_topology(self, door: Door) -> Dict[str, Any]:
        """Validate door topology (connects rooms, proper placement)."""
        violations = []
        suggestions = []
        score = 1.0
        
        door_geom = self._convert_to_shapely(door.geometry)
        if not door_geom:
            return {'violations': ["Invalid door geometry"], 'suggestions': [], 'score': 0.0}
        
        # Check if door connects rooms
        connected_rooms = []
        for room in self.bim_model.rooms:
            room_geom = self._convert_to_shapely(room.geometry)
            if room_geom and door_geom.touches(room_geom):
                connected_rooms.append(room)
        
        if len(connected_rooms) < 2:
            violations.append(f"Door {door.id} does not properly connect rooms")
            suggestions.append(f"Ensure door {door.id} connects at least two rooms")
            score = 0.6
        
        return {'violations': violations, 'suggestions': suggestions, 'score': score}
    
    def _validate_wall_topology(self, wall: Wall) -> Dict[str, Any]:
        """Validate wall topology (proper connections, no gaps)."""
        violations = []
        suggestions = []
        score = 1.0
        
        wall_geom = self._convert_to_shapely(wall.geometry)
        if not wall_geom:
            return {'violations': ["Invalid wall geometry"], 'suggestions': [], 'score': 0.0}
        
        # Check wall connections
        connected_walls = []
        for other_wall in self.bim_model.walls:
            if other_wall.id == wall.id:
                continue
            other_geom = self._convert_to_shapely(other_wall.geometry)
            if other_geom and wall_geom.touches(other_geom):
                connected_walls.append(other_wall)
        
        if len(connected_walls) == 0:
            violations.append(f"Wall {wall.id} is not connected to other walls")
            suggestions.append(f"Connect wall {wall.id} to adjacent walls")
            score = 0.8
        
        return {'violations': violations, 'suggestions': suggestions, 'score': score}
    
    def _validate_device_topology(self, device: Device) -> Dict[str, Any]:
        """Validate device topology (proper placement, accessibility)."""
        violations = []
        suggestions = []
        score = 1.0
        
        device_geom = self._convert_to_shapely(device.geometry)
        if not device_geom:
            return {'violations': ["Invalid device geometry"], 'suggestions': [], 'score': 0.0}
        
        # Check if device is inside a room
        device_in_room = False
        for room in self.bim_model.rooms:
            room_geom = self._convert_to_shapely(room.geometry)
            if room_geom and room_geom.contains(device_geom):
                device_in_room = True
                break
        
        if not device_in_room:
            violations.append(f"Device {device.id} is not inside any room")
            suggestions.append(f"Place device {device.id} inside a room")
            score = 0.9
        
        return {'violations': violations, 'suggestions': suggestions, 'score': score}
    
    def calculate_zones_and_areas(self) -> Dict[str, ZoneCalculation]:
        """Calculate zones, areas, and spatial hierarchies."""
        logger.info("Calculating zones and areas...")
        
        if not self.bim_model:
            return {}
        
        # Calculate room areas and volumes
        for room in self.bim_model.rooms:
            zone_calc = self._calculate_room_zone(room)
            self.zone_calculations[room.id] = zone_calc
        
        # Calculate building-level zones
        building_zones = self._calculate_building_zones()
        for zone_id, zone_calc in building_zones.items():
            self.zone_calculations[zone_id] = zone_calc
        
        # Calculate floor-level zones
        floor_zones = self._calculate_floor_zones()
        for zone_id, zone_calc in floor_zones.items():
            self.zone_calculations[zone_id] = zone_calc
        
        # Build spatial hierarchy
        hierarchy = self._build_spatial_hierarchy()
        self.hierarchy_cache['building'] = hierarchy
        
        self.stats['zone_calculations'] += 1
        logger.info(f"Calculated {len(self.zone_calculations)} zones")
        
        return self.zone_calculations
    
    def _calculate_room_zone(self, room: Room) -> ZoneCalculation:
        """Calculate zone information for a room."""
        room_geom = self._convert_to_shapely(room.geometry)
        
        area = room_geom.area if room_geom else 0.0
        volume = area * (room.ceiling_height or 3.0) if room.ceiling_height else None
        
        # Find elements in this room
        elements_in_room = []
        for device in self.bim_model.devices:
            device_geom = self._convert_to_shapely(device.geometry)
            if device_geom and room_geom and room_geom.contains(device_geom):
                elements_in_room.append(device.id)
        
        # Update room area if not set
        if not room.area:
            room.area = area
        
        return ZoneCalculation(
            zone_id=room.id,
            zone_type="room",
            area=area,
            volume=volume,
            elements=elements_in_room,
            hierarchy_level=SpatialHierarchyLevel.ROOM,
            parent_zone=f"floor_{room.floor_level or 0}",
            child_zones=[]
        )
    
    def _calculate_building_zones(self) -> Dict[str, ZoneCalculation]:
        """Calculate building-level zones."""
        building_area = 0.0
        building_volume = 0.0
        all_elements = []
        
        for room in self.bim_model.rooms:
            room_geom = self._convert_to_shapely(room.geometry)
            if room_geom:
                building_area += room_geom.area
                building_volume += room_geom.area * (room.ceiling_height or 3.0)
            all_elements.append(room.id)
        
        return {
            "building_main": ZoneCalculation(
                zone_id="building_main",
                zone_type="building",
                area=building_area,
                volume=building_volume,
                elements=all_elements,
                hierarchy_level=SpatialHierarchyLevel.BUILDING,
                parent_zone=None,
                child_zones=[f"floor_{level}" for level in set(room.floor_level or 0 for room in self.bim_model.rooms)]
            )
        }
    
    def _calculate_floor_zones(self) -> Dict[str, ZoneCalculation]:
        """Calculate floor-level zones."""
        floor_zones = {}
        
        # Group rooms by floor level
        floors = defaultdict(list)
        for room in self.bim_model.rooms:
            floor_level = room.floor_level or 0
            floors[floor_level].append(room)
        
        for floor_level, rooms in floors.items():
            floor_area = 0.0
            floor_volume = 0.0
            floor_elements = []
            
            for room in rooms:
                room_geom = self._convert_to_shapely(room.geometry)
                if room_geom:
                    floor_area += room_geom.area
                    floor_volume += room_geom.area * (room.ceiling_height or 3.0)
                floor_elements.append(room.id)
            
            floor_zones[f"floor_{floor_level}"] = ZoneCalculation(
                zone_id=f"floor_{floor_level}",
                zone_type="floor",
                area=floor_area,
                volume=floor_volume,
                elements=floor_elements,
                hierarchy_level=SpatialHierarchyLevel.FLOOR,
                parent_zone="building_main",
                child_zones=[room.id for room in rooms]
            )
        
        return floor_zones
    
    def _build_spatial_hierarchy(self) -> Dict[str, Any]:
        """Build spatial hierarchy (building > floor > room > zone)."""
        hierarchy = {
            'building': {
                'id': 'building_main',
                'type': 'building',
                'children': {}
            }
        }
        
        # Group by floor
        floors = defaultdict(list)
        for room in self.bim_model.rooms:
            floor_level = room.floor_level or 0
            floors[floor_level].append(room)
        
        for floor_level, rooms in floors.items():
            floor_id = f"floor_{floor_level}"
            hierarchy['building']['children'][floor_id] = {
                'id': floor_id,
                'type': 'floor',
                'level': floor_level,
                'children': {}
            }
            
            # Add rooms to floor
            for room in rooms:
                hierarchy['building']['children'][floor_id]['children'][room.id] = {
                    'id': room.id,
                    'type': 'room',
                    'room_type': room.room_type.value,
                    'area': room.area,
                    'children': {}
                }
        
        return hierarchy
    
    def _convert_to_shapely(self, geometry: Geometry) -> Any:
        """Convert BIM geometry to Shapely geometry."""
        if geometry.type == GeometryType.POINT:
            coords = geometry.coordinates
            if len(coords) >= 2:
                return Point(coords[0], coords[1])
        
        elif geometry.type == GeometryType.LINESTRING:
            coords = geometry.coordinates
            if len(coords) >= 2:
                return LineString(coords)
        
        elif geometry.type == GeometryType.POLYGON:
            coords = geometry.coordinates
            if len(coords) >= 3:
                return Polygon(coords)
        
        elif geometry.type == GeometryType.MULTIPOLYGON:
            polygons = []
            for poly_coords in geometry.coordinates:
                if len(poly_coords) >= 3:
                    polygons.append(Polygon(poly_coords))
            return MultiPolygon(polygons)
        
        return None
    
    def get_spatial_statistics(self) -> Dict[str, Any]:
        """Get spatial reasoning statistics."""
        return {
            'spatial_indices': len(self.spatial_indices),
            'topology_cache_size': len(self.topology_cache),
            'zone_calculations': len(self.zone_calculations),
            'hierarchy_levels': len(self.hierarchy_cache),
            'stats': self.stats
        } 