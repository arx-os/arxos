"""
Spatial Reasoning System for BIM Models

This module provides advanced spatial reasoning capabilities including:
- Geometric analysis and calculations
- Spatial relationship detection
- Building layout analysis
- Spatial optimization
- Collision detection
- Accessibility analysis
"""

import logging
import math
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Set, Any, Union
from enum import Enum
from dataclasses import dataclass
from collections import defaultdict
import numpy as np
from shapely.geometry import Point, Polygon, LineString, MultiPolygon
from shapely.ops import unary_union
from shapely.validation import make_valid

from pydantic import BaseModel, Field, field_validator, model_validator

from ..models.bim import (
    BIMElementBase, BIMModel, Geometry, GeometryType,
    Room, Wall, Door, Window, Device, SystemType
)

# Configure logging
logger = logging.getLogger(__name__)

class SpatialRelation(str, Enum):
    """Types of spatial relationships."""
    CONTAINS = "contains"
    INTERSECTS = "intersects"
    ADJACENT = "adjacent"
    NEAR = "near"
    ABOVE = "above"
    BELOW = "below"
    INSIDE = "inside"
    OUTSIDE = "outside"
    TOUCHES = "touches"
    DISJOINT = "disjoint"

class AccessibilityType(str, Enum):
    """Types of accessibility analysis."""
    WHEELCHAIR = "wheelchair"
    EMERGENCY_EXIT = "emergency_exit"
    FIRE_ESCAPE = "fire_escape"
    SERVICE_ACCESS = "service_access"
    PUBLIC_ACCESS = "public_access"

@dataclass
class SpatialConstraint:
    """Spatial constraints for analysis."""
    min_distance: Optional[float] = None
    max_distance: Optional[float] = None
    min_area: Optional[float] = None
    max_area: Optional[float] = None
    clearance_required: Optional[float] = None
    accessibility_requirements: List[AccessibilityType] = None

class SpatialAnalysis(BaseModel):
    """Results of spatial analysis."""
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    element_id: str
    analysis_type: str
    results: Dict[str, Any] = Field(default_factory=dict)
    constraints: Optional[SpatialConstraint] = None
    violations: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SpatialReasoningEngine:
    """Advanced spatial reasoning engine for BIM models."""
    
    def __init__(self, bim_model: Optional[BIMModel] = None):
        self.bim_model = bim_model
        self.spatial_index: Dict[str, Any] = {}
        self.analysis_cache: Dict[str, SpatialAnalysis] = {}
        self.geometry_cache: Dict[str, Any] = {}
        
        # Performance tracking
        self.stats = {
            'analyses_performed': 0,
            'spatial_queries': 0,
            'collision_detections': 0,
            'accessibility_checks': 0
        }
    
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
    
    def _get_element_geometry(self, element_id: str) -> Any:
        """Get Shapely geometry for an element."""
        if element_id in self.geometry_cache:
            return self.geometry_cache[element_id]
        
        element = self.bim_model.get_element_by_id(element_id)
        if element and element.geometry:
            shapely_geom = self._convert_to_shapely(element.geometry)
            if shapely_geom:
                self.geometry_cache[element_id] = shapely_geom
                return shapely_geom
        
        return None
    
    def analyze_spatial_relationships(self, elements: List[BIMElementBase]) -> Dict[str, Any]:
        """Analyze spatial relationships for a list of elements."""
        if not elements:
            return {
                "spatial_groups": [],
                "collisions": [],
                "accessibility_score": 0.0,
                "analysis_time": 0.0
            }
        
        start_time = time.time()
        
        # Convert elements to geometries
        geometries = {}
        for element in elements:
            if hasattr(element, 'geometry') and element.geometry:
                shapely_geom = self._convert_to_shapely(element.geometry)
                if shapely_geom:
                    geometries[element.id] = shapely_geom
        
        # Analyze spatial relationships
        spatial_groups = []
        collisions = []
        
        # Group elements by proximity
        processed = set()
        for element_id, geom in geometries.items():
            if element_id in processed:
                continue
            
            group = [element_id]
            processed.add(element_id)
            
            for other_id, other_geom in geometries.items():
                if other_id in processed:
                    continue
                
                try:
                    distance = geom.distance(other_geom)
                    if distance < 5.0:  # Within 5 units
                        group.append(other_id)
                        processed.add(other_id)
                except Exception:
                    continue
            
            if len(group) > 1:
                spatial_groups.append(group)
        
        # Detect collisions
        for i, (id1, geom1) in enumerate(geometries.items()):
            for j, (id2, geom2) in enumerate(geometries.items()):
                if i >= j:
                    continue
                
                try:
                    if geom1.intersects(geom2):
                        collisions.append({
                            "element1": id1,
                            "element2": id2,
                            "intersection_area": geom1.intersection(geom2).area
                        })
                except Exception:
                    continue
        
        # Calculate accessibility score
        accessibility_score = self._calculate_accessibility_score(elements)
        
        analysis_time = time.time() - start_time
        
        return {
            "spatial_groups": spatial_groups,
            "collisions": collisions,
            "accessibility_score": accessibility_score,
            "analysis_time": analysis_time
        }
    
    def _determine_spatial_relationship(self, geom1: Any, geom2: Any) -> Optional[SpatialRelation]:
        """Determine the spatial relationship between two geometries."""
        try:
            if geom1.intersects(geom2):
                if geom1.contains(geom2):
                    return SpatialRelation.CONTAINS
                elif geom2.contains(geom1):
                    return SpatialRelation.INSIDE
                elif geom1.touches(geom2):
                    return SpatialRelation.TOUCHES
                else:
                    return SpatialRelation.INTERSECTS
            else:
                distance = geom1.distance(geom2)
                if distance < 0.1:  # Very close
                    return SpatialRelation.ADJACENT
                elif distance < 5.0:  # Near
                    return SpatialRelation.NEAR
                else:
                    return SpatialRelation.DISJOINT
        except Exception as e:
            logger.warning(f"Error determining spatial relationship: {e}")
            return None
    
    def detect_collisions(self, element_id: str) -> List[Dict[str, Any]]:
        """Detect spatial collisions for an element."""
        element_geom = self._get_element_geometry(element_id)
        if not element_geom:
            return []
        
        collisions = []
        
        # Check against all other elements
        all_elements = (
            self.bim_model.rooms + self.bim_model.walls + 
            self.bim_model.doors + self.bim_model.windows +
            self.bim_model.devices
        )
        
        for other_element in all_elements:
            if other_element.id == element_id:
                continue
            
            other_geom = self._get_element_geometry(other_element.id)
            if not other_geom:
                continue
            
            # Check for intersection
            if element_geom.intersects(other_geom):
                intersection = element_geom.intersection(other_geom)
                collision_info = {
                    'collision_with': other_element.id,
                    'collision_type': 'intersection',
                    'intersection_area': intersection.area if hasattr(intersection, 'area') else 0,
                    'severity': 'high' if intersection.area > 1.0 else 'medium'
                }
                collisions.append(collision_info)
        
        self.stats['collision_detections'] += 1
        return collisions
    
    def calculate_room_metrics(self, room_id: str) -> Dict[str, Any]:
        """Calculate comprehensive metrics for a room."""
        room = self.bim_model.get_element_by_id(room_id)
        if not room or not isinstance(room, Room):
            return {}
        
        room_geom = self._get_element_geometry(room_id)
        if not room_geom:
            return {}
        
        metrics = {
            'area': room_geom.area,
            'perimeter': room_geom.length if hasattr(room_geom, 'length') else 0,
            'centroid': (room_geom.centroid.x, room_geom.centroid.y),
            'bounding_box': room_geom.bounds,
            'compactness': self._calculate_compactness(room_geom),
            'device_count': 0,
            'device_density': 0,
            'accessibility_score': 0
        }
        
        # Count devices in room
        devices_in_room = []
        for device in self.bim_model.devices:
            device_geom = self._get_element_geometry(device.id)
            if device_geom and room_geom.contains(device_geom):
                devices_in_room.append(device)
        
        metrics['device_count'] = len(devices_in_room)
        metrics['device_density'] = len(devices_in_room) / metrics['area'] if metrics['area'] > 0 else 0
        
        # Calculate accessibility score
        metrics['accessibility_score'] = self._calculate_accessibility_score(room_id)
        
        return metrics
    
    def _calculate_compactness(self, geometry: Any) -> float:
        """Calculate compactness ratio (area/perimeter^2)."""
        if hasattr(geometry, 'area') and hasattr(geometry, 'length'):
            perimeter = geometry.length
            if perimeter > 0:
                return (4 * math.pi * geometry.area) / (perimeter ** 2)
        return 0.0
    
    def _calculate_accessibility_score(self, elements: List[BIMElementBase]) -> float:
        """Calculate accessibility score for elements."""
        if not elements:
            return 0.0
        
        # Simple accessibility calculation based on element types
        door_count = sum(1 for e in elements if hasattr(e, 'bim_type') and e.bim_type == 'door')
        window_count = sum(1 for e in elements if hasattr(e, 'bim_type') and e.bim_type == 'window')
        wall_count = sum(1 for e in elements if hasattr(e, 'bim_type') and e.bim_type == 'wall')
        
        total_elements = len(elements)
        if total_elements == 0:
            return 0.0
        
        # Accessibility score based on openings vs walls
        if wall_count > 0:
            opening_ratio = (door_count + window_count) / wall_count
            return min(opening_ratio * 100, 100.0)
        else:
            return 50.0  # Neutral score if no walls
    
    def analyze_building_layout(self) -> Dict[str, Any]:
        """Analyze the overall building layout."""
        layout_analysis = {
            'total_rooms': len(self.bim_model.rooms),
            'total_area': 0.0,
            'room_distribution': {},
            'circulation_analysis': {},
            'efficiency_metrics': {},
            'spatial_hierarchy': {}
        }
        
        # Calculate total area and room distribution
        for room in self.bim_model.rooms:
            room_geom = self._get_element_geometry(room.id)
            if room_geom and hasattr(room_geom, 'area'):
                layout_analysis['total_area'] += room_geom.area
                
                room_type = room.room_type.value
                if room_type not in layout_analysis['room_distribution']:
                    layout_analysis['room_distribution'][room_type] = {
                        'count': 0,
                        'total_area': 0.0
                    }
                layout_analysis['room_distribution'][room_type]['count'] += 1
                layout_analysis['room_distribution'][room_type]['total_area'] += room_geom.area
        
        # Analyze circulation
        layout_analysis['circulation_analysis'] = self._analyze_circulation()
        
        # Calculate efficiency metrics
        layout_analysis['efficiency_metrics'] = self._calculate_efficiency_metrics()
        
        # Analyze spatial hierarchy
        layout_analysis['spatial_hierarchy'] = self._analyze_spatial_hierarchy()
        
        return layout_analysis
    
    def _analyze_circulation(self) -> Dict[str, Any]:
        """Analyze building circulation patterns."""
        circulation = {
            'main_circulation_areas': [],
            'dead_ends': [],
            'circulation_efficiency': 0.0,
            'accessibility_issues': []
        }
        
        # Find main circulation areas (lobbies, corridors)
        for room in self.bim_model.rooms:
            if room.room_type.value in ['lobby', 'circulation']:
                room_geom = self._get_element_geometry(room.id)
                if room_geom:
                    circulation['main_circulation_areas'].append({
                        'room_id': room.id,
                        'area': room_geom.area,
                        'name': room.name
                    })
        
        # Calculate circulation efficiency
        total_circulation_area = sum(area['area'] for area in circulation['main_circulation_areas'])
        total_building_area = sum(
            self._get_element_geometry(room.id).area 
            for room in self.bim_model.rooms 
            if self._get_element_geometry(room.id)
        )
        
        if total_building_area > 0:
            circulation['circulation_efficiency'] = total_circulation_area / total_building_area
        
        return circulation
    
    def _calculate_efficiency_metrics(self) -> Dict[str, float]:
        """Calculate building efficiency metrics."""
        metrics = {
            'space_utilization': 0.0,
            'circulation_ratio': 0.0,
            'compactness': 0.0
        }
        
        # Calculate space utilization
        total_area = 0.0
        occupied_area = 0.0
        
        for room in self.bim_model.rooms:
            room_geom = self._get_element_geometry(room.id)
            if room_geom and hasattr(room_geom, 'area'):
                total_area += room_geom.area
                if room.room_type.value not in ['circulation', 'mechanical']:
                    occupied_area += room_geom.area
        
        if total_area > 0:
            metrics['space_utilization'] = occupied_area / total_area
        
        return metrics
    
    def _analyze_spatial_hierarchy(self) -> Dict[str, Any]:
        """Analyze spatial hierarchy of the building."""
        hierarchy = {
            'floors': {},
            'zones': {},
            'functional_groups': {}
        }
        
        # Group rooms by floor level
        for room in self.bim_model.rooms:
            floor_level = room.floor_level or 0
            if floor_level not in hierarchy['floors']:
                hierarchy['floors'][floor_level] = []
            hierarchy['floors'][floor_level].append(room.id)
        
        # Group by functional zones
        for room in self.bim_model.rooms:
            zone_type = self._determine_zone_type(room)
            if zone_type not in hierarchy['zones']:
                hierarchy['zones'][zone_type] = []
            hierarchy['zones'][zone_type].append(room.id)
        
        return hierarchy
    
    def _determine_zone_type(self, room: Room) -> str:
        """Determine the zone type for a room."""
        room_type = room.room_type.value
        
        if room_type in ['office', 'conference']:
            return 'work'
        elif room_type in ['bathroom', 'break_room']:
            return 'support'
        elif room_type in ['mechanical', 'electrical']:
            return 'technical'
        elif room_type in ['lobby', 'circulation']:
            return 'circulation'
        else:
            return 'general'
    
    def check_accessibility(self, room_id: str, accessibility_type: AccessibilityType) -> Dict[str, Any]:
        """Check accessibility for a specific room."""
        room = self.bim_model.get_element_by_id(room_id)
        if not room or not isinstance(room, Room):
            return {'accessible': False, 'issues': ['Room not found']}
        
        room_geom = self._get_element_geometry(room_id)
        if not room_geom:
            return {'accessible': False, 'issues': ['Invalid geometry']}
        
        accessibility_check = {
            'accessible': True,
            'issues': [],
            'recommendations': [],
            'score': 0.0
        }
        
        if accessibility_type == AccessibilityType.WHEELCHAIR:
            accessibility_check.update(self._check_wheelchair_accessibility(room, room_geom))
        elif accessibility_type == AccessibilityType.EMERGENCY_EXIT:
            accessibility_check.update(self._check_emergency_exit_accessibility(room, room_geom))
        elif accessibility_type == AccessibilityType.FIRE_ESCAPE:
            accessibility_check.update(self._check_fire_escape_accessibility(room, room_geom))
        
        self.stats['accessibility_checks'] += 1
        return accessibility_check
    
    def _check_wheelchair_accessibility(self, room: Room, room_geom: Any) -> Dict[str, Any]:
        """Check wheelchair accessibility for a room."""
        issues = []
        recommendations = []
        score = 100.0
        
        # Check room size
        if hasattr(room_geom, 'area'):
            if room_geom.area < 15.0:  # Minimum area for wheelchair
                issues.append("Room too small for wheelchair access")
                score -= 30.0
                recommendations.append("Increase room size to at least 15 sqm")
        
        # Check for doors
        doors = [d for d in self.bim_model.doors if d.parent_id == room.id]
        if not doors:
            issues.append("No doors found for room access")
            score -= 50.0
        else:
            # Check door width
            for door in doors:
                if door.width and door.width < 0.8:  # Minimum wheelchair door width
                    issues.append(f"Door {door.id} too narrow for wheelchair")
                    score -= 20.0
                    recommendations.append(f"Widen door {door.id} to at least 0.8m")
        
        return {
            'issues': issues,
            'recommendations': recommendations,
            'score': max(score, 0.0)
        }
    
    def _check_emergency_exit_accessibility(self, room: Room, room_geom: Any) -> Dict[str, Any]:
        """Check emergency exit accessibility for a room."""
        issues = []
        recommendations = []
        score = 100.0
        
        # Check for emergency exits
        emergency_doors = [d for d in self.bim_model.doors if d.parent_id == room.id and d.is_emergency_exit]
        if not emergency_doors:
            issues.append("No emergency exit found")
            score -= 60.0
            recommendations.append("Add emergency exit door")
        
        # Check distance to emergency exit
        # This would require more complex path finding in a full implementation
        
        return {
            'issues': issues,
            'recommendations': recommendations,
            'score': max(score, 0.0)
        }
    
    def _check_fire_escape_accessibility(self, room: Room, room_geom: Any) -> Dict[str, Any]:
        """Check fire escape accessibility for a room."""
        issues = []
        recommendations = []
        score = 100.0
        
        # Check for windows (potential fire escape)
        windows = [w for w in self.bim_model.windows if w.parent_id == room.id]
        if not windows:
            issues.append("No windows found for fire escape")
            score -= 40.0
            recommendations.append("Add operable windows for fire escape")
        
        # Check window size for escape
        for window in windows:
            if window.width and window.width < 0.6:  # Minimum escape width
                issues.append(f"Window {window.id} too small for fire escape")
                score -= 20.0
                recommendations.append(f"Enlarge window {window.id} to at least 0.6m width")
        
        return {
            'issues': issues,
            'recommendations': recommendations,
            'score': max(score, 0.0)
        }
    
    def optimize_spatial_layout(self, constraints: SpatialConstraint) -> Dict[str, Any]:
        """Optimize spatial layout based on constraints."""
        optimization_results = {
            'suggestions': [],
            'improvements': [],
            'constraint_violations': [],
            'optimization_score': 0.0
        }
        
        # Check distance constraints
        if constraints.min_distance or constraints.max_distance:
            distance_analysis = self._analyze_distance_constraints(constraints)
            optimization_results['suggestions'].extend(distance_analysis['suggestions'])
            optimization_results['constraint_violations'].extend(distance_analysis['violations'])
        
        # Check area constraints
        if constraints.min_area or constraints.max_area:
            area_analysis = self._analyze_area_constraints(constraints)
            optimization_results['suggestions'].extend(area_analysis['suggestions'])
            optimization_results['constraint_violations'].extend(area_analysis['violations'])
        
        # Check accessibility constraints
        if constraints.accessibility_requirements:
            accessibility_analysis = self._analyze_accessibility_constraints(constraints)
            optimization_results['suggestions'].extend(accessibility_analysis['suggestions'])
            optimization_results['constraint_violations'].extend(accessibility_analysis['violations'])
        
        # Calculate optimization score
        total_violations = len(optimization_results['constraint_violations'])
        total_suggestions = len(optimization_results['suggestions'])
        
        if total_violations == 0:
            optimization_results['optimization_score'] = 100.0
        else:
            optimization_results['optimization_score'] = max(0.0, 100.0 - (total_violations * 10.0))
        
        return optimization_results
    
    def _analyze_distance_constraints(self, constraints: SpatialConstraint) -> Dict[str, List[str]]:
        """Analyze distance constraints."""
        analysis = {'suggestions': [], 'violations': []}
        
        # This would implement distance checking between elements
        # For now, return empty analysis
        return analysis
    
    def _analyze_area_constraints(self, constraints: SpatialConstraint) -> Dict[str, List[str]]:
        """Analyze area constraints."""
        analysis = {'suggestions': [], 'violations': []}
        
        for room in self.bim_model.rooms:
            room_geom = self._get_element_geometry(room.id)
            if room_geom and hasattr(room_geom, 'area'):
                area = room_geom.area
                
                if constraints.min_area and area < constraints.min_area:
                    analysis['violations'].append(f"Room {room.id} area ({area:.2f}) below minimum ({constraints.min_area})")
                    analysis['suggestions'].append(f"Increase room {room.id} area to at least {constraints.min_area}")
                
                if constraints.max_area and area > constraints.max_area:
                    analysis['violations'].append(f"Room {room.id} area ({area:.2f}) above maximum ({constraints.max_area})")
                    analysis['suggestions'].append(f"Reduce room {room.id} area to at most {constraints.max_area}")
        
        return analysis
    
    def _analyze_accessibility_constraints(self, constraints: SpatialConstraint) -> Dict[str, List[str]]:
        """Analyze accessibility constraints."""
        analysis = {'suggestions': [], 'violations': []}
        
        for room in self.bim_model.rooms:
            for accessibility_type in constraints.accessibility_requirements:
                accessibility_check = self.check_accessibility(room.id, accessibility_type)
                if not accessibility_check['accessible']:
                    analysis['violations'].append(f"Room {room.id} not accessible for {accessibility_type}")
                    analysis['suggestions'].extend(accessibility_check['recommendations'])
        
        return analysis
    
    def generate_spatial_report(self) -> Dict[str, Any]:
        """Generate comprehensive spatial analysis report."""
        report = {
            'building_overview': self.analyze_building_layout(),
            'room_analyses': {},
            'collision_report': {},
            'accessibility_report': {},
            'optimization_recommendations': {},
            'statistics': self.stats
        }
        
        # Analyze each room
        for room in self.bim_model.rooms:
            room_analysis = {
                'metrics': self.calculate_room_metrics(room.id),
                'spatial_relationships': self.analyze_spatial_relationships(room.id),
                'collisions': self.detect_collisions(room.id),
                'accessibility': {}
            }
            
            # Check accessibility for different types
            for accessibility_type in AccessibilityType:
                room_analysis['accessibility'][accessibility_type.value] = self.check_accessibility(room.id, accessibility_type)
            
            report['room_analyses'][room.id] = room_analysis
        
        # Generate optimization recommendations
        constraints = SpatialConstraint(
            min_area=10.0,
            accessibility_requirements=[AccessibilityType.WHEELCHAIR, AccessibilityType.EMERGENCY_EXIT]
        )
        report['optimization_recommendations'] = self.optimize_spatial_layout(constraints)
        
        return report 