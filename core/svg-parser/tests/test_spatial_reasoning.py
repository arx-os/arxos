"""
Tests for Spatial Reasoning System

This module tests the comprehensive spatial reasoning capabilities including
geometric analysis, spatial relationships, collision detection, and accessibility analysis.
"""

import pytest
import math
from typing import Dict, List, Any

from ..models.bim import (
    BIMModel, Room, Device, SystemType, DeviceCategory, Geometry, GeometryType,
    RoomType, Wall, Door, Window
)
from core.services.spatial_reasoning
    SpatialReasoningEngine, SpatialRelation, AccessibilityType, SpatialConstraint,
    SpatialAnalysis
)

class TestSpatialReasoningEngine:
    """Test cases for the SpatialReasoningEngine class."""
    
    @pytest.fixture
    def sample_bim_model(self):
        """Create a sample BIM model for testing."""
        model = BIMModel()
        
        # Add rooms
        room1 = Room(
            id="room-1",
            name="Office 1",
            geometry=Geometry(
                type=GeometryType.POLYGON,
                coordinates=[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]
            ),
            room_type=RoomType.OFFICE,
            room_number="101",
            area=100.0
        )
        model.add_element(room1)
        
        room2 = Room(
            id="room-2",
            name="Office 2",
            geometry=Geometry(
                type=GeometryType.POLYGON,
                coordinates=[[10, 0], [20, 0], [20, 10], [10, 10], [10, 0]]
            ),
            room_type=RoomType.OFFICE,
            room_number="102",
            area=100.0
        )
        model.add_element(room2)
        
        # Add walls
        wall1 = Wall(
            id="wall-1",
            name="Wall 1",
            geometry=Geometry(
                type=GeometryType.LINESTRING,
                coordinates=[[10, 0], [10, 10]]
            ),
            wall_type="interior"
        )
        model.add_element(wall1)
        
        # Add doors
        door1 = Door(
            id="door-1",
            name="Door 1",
            geometry=Geometry(
                type=GeometryType.LINESTRING,
                coordinates=[[10, 4], [10, 6]]
            ),
            door_type="swing",
            width=2.0,
            height=2.4,
            is_emergency_exit=True
        )
        model.add_element(door1)
        
        # Add windows
        window1 = Window(
            id="window-1",
            name="Window 1",
            geometry=Geometry(
                type=GeometryType.LINESTRING,
                coordinates=[[0, 8], [2, 8]]
            ),
            window_type="fixed",
            width=2.0,
            height=1.2
        )
        model.add_element(window1)
        
        # Add devices
        device1 = Device(
            id="device-1",
            name="Device 1",
            geometry=Geometry(
                type=GeometryType.POINT,
                coordinates=[5, 5]
            ),
            system_type=SystemType.HVAC,
            category=DeviceCategory.AHU
        )
        model.add_element(device1)
        
        device2 = Device(
            id="device-2",
            name="Device 2",
            geometry=Geometry(
                type=GeometryType.POINT,
                coordinates=[15, 5]
            ),
            system_type=SystemType.ELECTRICAL,
            category=DeviceCategory.PANEL
        )
        model.add_element(device2)
        
        return model
    
    @pytest.fixture
    def spatial_engine(self, sample_bim_model):
        """Create a spatial reasoning engine with the sample BIM model."""
        return SpatialReasoningEngine(sample_bim_model)
    
    def test_create_spatial_engine(self, spatial_engine):
        """Test creating a spatial reasoning engine."""
        assert spatial_engine is not None
        assert spatial_engine.bim_model is not None
        assert len(spatial_engine.geometry_cache) == 0
        assert spatial_engine.stats['analyses_performed'] == 0
    
    def test_convert_to_shapely(self, spatial_engine):
        """Test conversion of BIM geometry to Shapely geometry."""
        # Test point geometry
        point_geom = Geometry(
            type=GeometryType.POINT,
            coordinates=[5, 5]
        )
        shapely_point = spatial_engine._convert_to_shapely(point_geom)
        assert shapely_point is not None
        assert shapely_point.x == 5
        assert shapely_point.y == 5
        
        # Test polygon geometry
        poly_geom = Geometry(
            type=GeometryType.POLYGON,
            coordinates=[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]
        )
        shapely_poly = spatial_engine._convert_to_shapely(poly_geom)
        assert shapely_poly is not None
        assert shapely_poly.area == 100.0
    
    def test_get_element_geometry(self, spatial_engine):
        """Test getting Shapely geometry for an element."""
        # Test with existing element
        geom = spatial_engine._get_element_geometry("room-1")
        assert geom is not None
        assert geom.area == 100.0
        
        # Test caching
        geom2 = spatial_engine._get_element_geometry("room-1")
        assert geom is geom2  # Should be cached
        
        # Test with non-existent element
        geom3 = spatial_engine._get_element_geometry("non-existent")
        assert geom3 is None
    
    def test_analyze_spatial_relationships(self, spatial_engine):
        """Test spatial relationship analysis."""
        relationships = spatial_engine.analyze_spatial_relationships("room-1")
        
        assert isinstance(relationships, dict)
        assert spatial_engine.stats['spatial_queries'] == 1
        
        # Should have relationships with other elements
        assert len(relationships) > 0
    
    def test_determine_spatial_relationship(self, spatial_engine):
        """Test spatial relationship determination."""
        # Get geometries
        room1_geom = spatial_engine._get_element_geometry("room-1")
        room2_geom = spatial_engine._get_element_geometry("room-2")
        device1_geom = spatial_engine._get_element_geometry("device-1")
        
        # Test adjacent relationship
        relation = spatial_engine._determine_spatial_relationship(room1_geom, room2_geom)
        assert relation in [SpatialRelation.ADJACENT, SpatialRelation.TOUCHES]
        
        # Test contains relationship
        relation = spatial_engine._determine_spatial_relationship(room1_geom, device1_geom)
        assert relation == SpatialRelation.CONTAINS
    
    def test_detect_collisions(self, spatial_engine):
        """Test collision detection."""
        collisions = spatial_engine.detect_collisions("room-1")
        
        assert isinstance(collisions, list)
        assert spatial_engine.stats['collision_detections'] == 1
        
        # Should detect collision with device inside room
        device_collisions = [c for c in collisions if c['collision_with'] == 'device-1']
        assert len(device_collisions) > 0
    
    def test_calculate_room_metrics(self, spatial_engine):
        """Test room metrics calculation."""
        metrics = spatial_engine.calculate_room_metrics("room-1")
        
        assert isinstance(metrics, dict)
        assert 'area' in metrics
        assert 'perimeter' in metrics
        assert 'centroid' in metrics
        assert 'bounding_box' in metrics
        assert 'compactness' in metrics
        assert 'device_count' in metrics
        assert 'device_density' in metrics
        assert 'accessibility_score' in metrics
        
        assert metrics['area'] == 100.0
        assert metrics['device_count'] == 1  # device-1 is inside room-1
        assert metrics['device_density'] == 0.01  # 1 device / 100 area
    
    def test_calculate_compactness(self, spatial_engine):
        """Test compactness calculation."""
        # Create a square polygon
        square_geom = spatial_engine._convert_to_shapely(Geometry(
            type=GeometryType.POLYGON,
            coordinates=[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]
        ))
        
        compactness = spatial_engine._calculate_compactness(square_geom)
        assert compactness > 0
        assert compactness <= 1.0  # Should be normalized
    
    def test_calculate_accessibility_score(self, spatial_engine):
        """Test accessibility score calculation."""
        score = spatial_engine._calculate_accessibility_score("room-1")
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 100.0
    
    def test_analyze_building_layout(self, spatial_engine):
        """Test building layout analysis."""
        layout_analysis = spatial_engine.analyze_building_layout()
        
        assert isinstance(layout_analysis, dict)
        assert 'total_rooms' in layout_analysis
        assert 'total_area' in layout_analysis
        assert 'room_distribution' in layout_analysis
        assert 'circulation_analysis' in layout_analysis
        assert 'efficiency_metrics' in layout_analysis
        assert 'spatial_hierarchy' in layout_analysis
        
        assert layout_analysis['total_rooms'] == 2
        assert layout_analysis['total_area'] == 200.0  # 100 + 100
    
    def test_analyze_circulation(self, spatial_engine):
        """Test circulation analysis."""
        circulation = spatial_engine._analyze_circulation()
        
        assert isinstance(circulation, dict)
        assert 'main_circulation_areas' in circulation
        assert 'dead_ends' in circulation
        assert 'circulation_efficiency' in circulation
        assert 'accessibility_issues' in circulation
    
    def test_calculate_efficiency_metrics(self, spatial_engine):
        """Test efficiency metrics calculation."""
        metrics = spatial_engine._calculate_efficiency_metrics()
        
        assert isinstance(metrics, dict)
        assert 'space_utilization' in metrics
        assert 'circulation_ratio' in metrics
        assert 'compactness' in metrics
        
        assert 0.0 <= metrics['space_utilization'] <= 1.0
    
    def test_analyze_spatial_hierarchy(self, spatial_engine):
        """Test spatial hierarchy analysis."""
        hierarchy = spatial_engine._analyze_spatial_hierarchy()
        
        assert isinstance(hierarchy, dict)
        assert 'floors' in hierarchy
        assert 'zones' in hierarchy
        assert 'functional_groups' in hierarchy
    
    def test_determine_zone_type(self, spatial_engine):
        """Test zone type determination."""
        room = spatial_engine.bim_model.get_element_by_id("room-1")
        zone_type = spatial_engine._determine_zone_type(room)
        
        assert isinstance(zone_type, str)
        assert zone_type in ['work', 'support', 'technical', 'circulation', 'general']
    
    def test_check_accessibility(self, spatial_engine):
        """Test accessibility checking."""
        # Test wheelchair accessibility
        wheelchair_check = spatial_engine.check_accessibility("room-1", AccessibilityType.WHEELCHAIR)
        
        assert isinstance(wheelchair_check, dict)
        assert 'accessible' in wheelchair_check
        assert 'issues' in wheelchair_check
        assert 'recommendations' in wheelchair_check
        assert 'score' in wheelchair_check
        
        assert spatial_engine.stats['accessibility_checks'] == 1
        
        # Test emergency exit accessibility
        emergency_check = spatial_engine.check_accessibility("room-1", AccessibilityType.EMERGENCY_EXIT)
        assert isinstance(emergency_check, dict)
    
    def test_check_wheelchair_accessibility(self, spatial_engine):
        """Test wheelchair accessibility checking."""
        room = spatial_engine.bim_model.get_element_by_id("room-1")
        room_geom = spatial_engine._get_element_geometry("room-1")
        
        result = spatial_engine._check_wheelchair_accessibility(room, room_geom)
        
        assert isinstance(result, dict)
        assert 'issues' in result
        assert 'recommendations' in result
        assert 'score' in result
        
        assert 0.0 <= result['score'] <= 100.0
    
    def test_check_emergency_exit_accessibility(self, spatial_engine):
        """Test emergency exit accessibility checking."""
        room = spatial_engine.bim_model.get_element_by_id("room-1")
        room_geom = spatial_engine._get_element_geometry("room-1")
        
        result = spatial_engine._check_emergency_exit_accessibility(room, room_geom)
        
        assert isinstance(result, dict)
        assert 'issues' in result
        assert 'recommendations' in result
        assert 'score' in result
    
    def test_check_fire_escape_accessibility(self, spatial_engine):
        """Test fire escape accessibility checking."""
        room = spatial_engine.bim_model.get_element_by_id("room-1")
        room_geom = spatial_engine._get_element_geometry("room-1")
        
        result = spatial_engine._check_fire_escape_accessibility(room, room_geom)
        
        assert isinstance(result, dict)
        assert 'issues' in result
        assert 'recommendations' in result
        assert 'score' in result
    
    def test_optimize_spatial_layout(self, spatial_engine):
        """Test spatial layout optimization."""
        constraints = SpatialConstraint(
            min_area=50.0,
            max_area=150.0,
            accessibility_requirements=[AccessibilityType.WHEELCHAIR]
        )
        
        optimization = spatial_engine.optimize_spatial_layout(constraints)
        
        assert isinstance(optimization, dict)
        assert 'suggestions' in optimization
        assert 'improvements' in optimization
        assert 'constraint_violations' in optimization
        assert 'optimization_score' in optimization
        
        assert 0.0 <= optimization['optimization_score'] <= 100.0
    
    def test_analyze_area_constraints(self, spatial_engine):
        """Test area constraint analysis."""
        constraints = SpatialConstraint(
            min_area=50.0,
            max_area=150.0
        )
        
        analysis = spatial_engine._analyze_area_constraints(constraints)
        
        assert isinstance(analysis, dict)
        assert 'suggestions' in analysis
        assert 'violations' in analysis
    
    def test_analyze_accessibility_constraints(self, spatial_engine):
        """Test accessibility constraint analysis."""
        constraints = SpatialConstraint(
            accessibility_requirements=[AccessibilityType.WHEELCHAIR]
        )
        
        analysis = spatial_engine._analyze_accessibility_constraints(constraints)
        
        assert isinstance(analysis, dict)
        assert 'suggestions' in analysis
        assert 'violations' in analysis
    
    def test_generate_spatial_report(self, spatial_engine):
        """Test spatial report generation."""
        report = spatial_engine.generate_spatial_report()
        
        assert isinstance(report, dict)
        assert 'building_overview' in report
        assert 'room_analyses' in report
        assert 'collision_report' in report
        assert 'accessibility_report' in report
        assert 'optimization_recommendations' in report
        assert 'statistics' in report
        
        # Check room analyses
        assert 'room-1' in report['room_analyses']
        assert 'room-2' in report['room_analyses']
        
        # Check statistics
        assert 'analyses_performed' in report['statistics']
        assert 'spatial_queries' in report['statistics']
        assert 'collision_detections' in report['statistics']
        assert 'accessibility_checks' in report['statistics']

class TestSpatialConstraint:
    """Test cases for the SpatialConstraint class."""
    
    def test_create_spatial_constraint(self):
        """Test creating a spatial constraint."""
        constraint = SpatialConstraint(
            min_distance=1.0,
            max_distance=10.0,
            min_area=50.0,
            max_area=150.0,
            clearance_required=0.8,
            accessibility_requirements=[AccessibilityType.WHEELCHAIR]
        )
        
        assert constraint.min_distance == 1.0
        assert constraint.max_distance == 10.0
        assert constraint.min_area == 50.0
        assert constraint.max_area == 150.0
        assert constraint.clearance_required == 0.8
        assert AccessibilityType.WHEELCHAIR in constraint.accessibility_requirements
    
    def test_spatial_constraint_defaults(self):
        """Test spatial constraint defaults."""
        constraint = SpatialConstraint()
        
        assert constraint.min_distance is None
        assert constraint.max_distance is None
        assert constraint.min_area is None
        assert constraint.max_area is None
        assert constraint.clearance_required is None
        assert constraint.accessibility_requirements is None

class TestSpatialAnalysis:
    """Test cases for the SpatialAnalysis class."""
    
    def test_create_spatial_analysis(self):
        """Test creating a spatial analysis."""
        analysis = SpatialAnalysis(
            element_id="room-1",
            analysis_type="accessibility",
            results={"score": 85.0},
            violations=["Door too narrow"],
            recommendations=["Widen door to 0.8m"]
        )
        
        assert analysis.element_id == "room-1"
        assert analysis.analysis_type == "accessibility"
        assert analysis.results["score"] == 85.0
        assert "Door too narrow" in analysis.violations
        assert "Widen door to 0.8m" in analysis.recommendations

if __name__ == "__main__":
    pytest.main([__file__]) 