"""
Tests for Spatial Analysis Engine

This module contains comprehensive tests for the SpatialAnalyzer class,
ensuring accurate 3D spatial calculations, volume analysis, and relationship detection.
"""

import pytest
import math
from unittest.mock import Mock
from typing import List, Dict, Any

from services.ai.arx_mcp.validate.spatial_analyzer import (
    SpatialAnalyzer, SpatialAnalysisError, SpatialRelation, BoundingBox, SpatialObject
)
from services.models.mcp_models import BuildingObject


class TestSpatialAnalyzer:
    """Test suite for SpatialAnalyzer class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = SpatialAnalyzer()
        
        # Create test building objects with 3D locations
        self.test_objects = [
            BuildingObject(
                object_id="room_1",
                object_type="room",
                properties={"area": 200, "height": 10, "occupancy": 4},
                location={"x": 0, "y": 0, "z": 0, "width": 20, "height": 10, "depth": 10}
            ),
            BuildingObject(
                object_id="room_2",
                object_type="room", 
                properties={"area": 150, "height": 12, "occupancy": 3},
                location={"x": 20, "y": 0, "z": 0, "width": 15, "height": 10, "depth": 10}
            ),
            BuildingObject(
                object_id="wall_1",
                object_type="wall",
                properties={"thickness": 0.2, "material": "concrete"},
                location={"x": 0, "y": 0, "z": 0, "width": 35, "height": 10, "depth": 0.2}
            ),
            BuildingObject(
                object_id="column_1",
                object_type="column",
                properties={"thickness": 0.3, "material": "steel"},
                location={"x": 17.5, "y": 0, "z": 0, "width": 0.3, "height": 10, "depth": 0.3}
            ),
            BuildingObject(
                object_id="duct_1",
                object_type="duct",
                properties={"diameter": 0.5, "flow_rate": 100},
                location={"x": 10, "y": 5, "z": 8, "width": 0.5, "height": 0.5, "depth": 10}
            ),
            BuildingObject(
                object_id="pipe_1",
                object_type="pipe",
                properties={"diameter": 0.1, "flow_rate": 50},
                location={"x": 5, "y": 8, "z": 2, "width": 0.1, "height": 0.1, "depth": 15}
            )
        ]
    
    def test_create_spatial_object(self):
        """Test creation of spatial objects"""
        spatial_objects = self.analyzer.analyze_building_objects(self.test_objects)
        
        assert len(spatial_objects) == 6
        assert "room_1" in spatial_objects
        assert "wall_1" in spatial_objects
        
        # Test room spatial object
        room_spatial = spatial_objects["room_1"]
        assert room_spatial.volume == 2000.0  # 20 * 10 * 10
        assert room_spatial.area == 200.0  # 20 * 10
        assert room_spatial.centroid == (10.0, 5.0, 5.0)
        
        # Test wall spatial object
        wall_spatial = spatial_objects["wall_1"]
        assert wall_spatial.volume == 70.0  # 35 * 10 * 0.2
        assert wall_spatial.area == 350.0  # 35 * 10
    
    def test_calculate_3d_distance(self):
        """Test 3D distance calculation"""
        obj1 = self.test_objects[0]  # room_1 at (0,0,0)
        obj2 = self.test_objects[1]  # room_2 at (20,0,0)
        
        distance = self.analyzer.calculate_3d_distance(obj1, obj2)
        expected_distance = math.sqrt(15**2 + 0**2 + 0**2)  # Distance between centroids
        assert abs(distance - expected_distance) < 0.001
    
    def test_calculate_volume(self):
        """Test volume calculations for different object types"""
        # Test room volume
        room_obj = self.test_objects[0]
        volume = self.analyzer.calculate_volume(room_obj)
        assert volume == 2000.0  # 20 * 10 * 10
        
        # Test wall volume (with thickness)
        wall_obj = self.test_objects[2]
        volume = self.analyzer.calculate_volume(wall_obj)
        assert volume == 70.0  # 35 * 10 * 0.2
        
        # Test duct volume (cylinder approximation)
        duct_obj = self.test_objects[4]
        volume = self.analyzer.calculate_volume(duct_obj)
        expected_volume = math.pi * (0.5/2)**2 * 10  # π * r² * length
        assert abs(volume - expected_volume) < 0.1
    
    def test_calculate_area(self):
        """Test area calculations for different object types"""
        # Test room area
        room_obj = self.test_objects[0]
        area = self.analyzer.calculate_area(room_obj)
        assert area == 200.0  # 20 * 10
        
        # Test wall surface area
        wall_obj = self.test_objects[2]
        area = self.analyzer.calculate_area(wall_obj)
        thickness = 0.2
        expected_area = 2 * (35 * 10 + 35 * thickness + 10 * thickness)
        assert abs(area - expected_area) < 0.1
        
        # Test duct surface area (cylinder)
        duct_obj = self.test_objects[4]
        area = self.analyzer.calculate_area(duct_obj)
        expected_area = math.pi * 0.5 * 10  # π * diameter * length
        assert abs(area - expected_area) < 0.1
    
    def test_find_intersections(self):
        """Test intersection detection"""
        # Create overlapping objects
        overlapping_objects = [
            BuildingObject(
                object_id="obj1",
                object_type="room",
                properties={},
                location={"x": 0, "y": 0, "z": 0, "width": 10, "height": 10, "depth": 10}
            ),
            BuildingObject(
                object_id="obj2", 
                object_type="room",
                properties={},
                location={"x": 5, "y": 5, "z": 0, "width": 10, "height": 10, "depth": 10}
            ),
            BuildingObject(
                object_id="obj3",
                object_type="room", 
                properties={},
                location={"x": 20, "y": 20, "z": 0, "width": 10, "height": 10, "depth": 10}
            )
        ]
        
        self.analyzer.analyze_building_objects(overlapping_objects)
        intersections = self.analyzer.find_intersections(overlapping_objects)
        
        # obj1 and obj2 should intersect, obj3 should not
        assert len(intersections) == 1
        intersection_pair = intersections[0]
        assert (intersection_pair[0].object_id == "obj1" and intersection_pair[1].object_id == "obj2") or \
               (intersection_pair[0].object_id == "obj2" and intersection_pair[1].object_id == "obj1")
    
    def test_find_nearby_objects(self):
        """Test nearby object detection"""
        target_obj = self.test_objects[0]  # room_1
        nearby_objects = self.analyzer.find_nearby_objects(target_obj, self.test_objects, 15.0)
        
        # Should find objects within 15 units
        assert len(nearby_objects) > 0
        assert all(obj.object_id != target_obj.object_id for obj in nearby_objects)
    
    def test_find_objects_in_volume(self):
        """Test volume-based object search"""
        # Search in a volume that should contain room_1 and wall_1
        objects_in_volume = self.analyzer.find_objects_in_volume(
            self.test_objects, 0, 0, 0, 25, 15, 15
        )
        
        assert len(objects_in_volume) >= 2
        object_ids = [obj.object_id for obj in objects_in_volume]
        assert "room_1" in object_ids
        assert "wall_1" in object_ids
    
    def test_calculate_spatial_relationships(self):
        """Test spatial relationship detection"""
        # Create objects with known relationships
        obj1 = BuildingObject(
            object_id="container",
            object_type="room",
            properties={},
            location={"x": 0, "y": 0, "z": 0, "width": 20, "height": 20, "depth": 20}
        )
        obj2 = BuildingObject(
            object_id="contained",
            object_type="furniture", 
            properties={},
            location={"x": 5, "y": 5, "z": 5, "width": 5, "height": 5, "depth": 5}
        )
        obj3 = BuildingObject(
            object_id="adjacent",
            object_type="room",
            properties={},
            location={"x": 20, "y": 0, "z": 0, "width": 10, "height": 20, "depth": 20}
        )
        
        self.analyzer.analyze_building_objects([obj1, obj2, obj3])
        
        # Test containment
        relationships = self.analyzer.calculate_spatial_relationships(obj1, obj2)
        assert SpatialRelation.CONTAINS in relationships
        
        # Test adjacency
        relationships = self.analyzer.calculate_spatial_relationships(obj1, obj3)
        assert SpatialRelation.ADJACENT in relationships
    
    def test_get_spatial_statistics(self):
        """Test spatial statistics calculation"""
        stats = self.analyzer.get_spatial_statistics(self.test_objects)
        
        assert 'total_volume' in stats
        assert 'total_area' in stats
        assert 'object_count' in stats
        assert 'bounding_box' in stats
        assert 'intersection_count' in stats
        assert 'intersections' in stats
        
        assert stats['object_count'] == 6
        assert stats['total_volume'] > 0
        assert stats['total_area'] > 0
    
    def test_build_spatial_index(self):
        """Test spatial index building"""
        self.analyzer.build_spatial_index(self.test_objects)
        
        assert len(self.analyzer.spatial_objects) == 6
        assert all(obj_id in self.analyzer.spatial_objects for obj_id in ["room_1", "room_2", "wall_1"])
    
    def test_get_total_volume(self):
        """Test total volume calculation"""
        total_volume = self.analyzer.get_total_volume(self.test_objects)
        assert total_volume > 0
        
        # Should be sum of individual volumes
        expected_volume = sum(self.analyzer.calculate_volume(obj) for obj in self.test_objects)
        assert abs(total_volume - expected_volume) < 0.1
    
    def test_get_total_area(self):
        """Test total area calculation"""
        total_area = self.analyzer.get_total_area(self.test_objects)
        assert total_area > 0
        
        # Should be sum of individual areas
        expected_area = sum(self.analyzer.calculate_area(obj) for obj in self.test_objects)
        assert abs(total_area - expected_area) < 0.1


class TestBoundingBox:
    """Test suite for BoundingBox class"""
    
    def test_bounding_box_properties(self):
        """Test bounding box property calculations"""
        bbox = BoundingBox(0, 0, 0, 10, 20, 30)
        
        assert bbox.width == 10
        assert bbox.height == 20
        assert bbox.depth == 30
        assert bbox.volume == 6000  # 10 * 20 * 30
        assert bbox.area == 200  # 10 * 20
        assert bbox.center == (5, 10, 15)
    
    def test_bounding_box_center(self):
        """Test bounding box center calculation"""
        bbox = BoundingBox(1, 2, 3, 11, 22, 33)
        center = bbox.center
        
        assert center[0] == 6  # (1 + 11) / 2
        assert center[1] == 12  # (2 + 22) / 2
        assert center[2] == 18  # (3 + 33) / 2


class TestSpatialObject:
    """Test suite for SpatialObject class"""
    
    def test_spatial_object_creation(self):
        """Test spatial object creation"""
        building_obj = BuildingObject(
            object_id="test",
            object_type="room",
            properties={"area": 100},
            location={"x": 0, "y": 0, "z": 0, "width": 10, "height": 10, "depth": 10}
        )
        
        bbox = BoundingBox(0, 0, 0, 10, 10, 10)
        spatial_obj = SpatialObject(
            object=building_obj,
            bounding_box=bbox,
            volume=1000.0,
            area=100.0,
            centroid=(5, 5, 5)
        )
        
        assert spatial_obj.object.object_id == "test"
        assert spatial_obj.volume == 1000.0
        assert spatial_obj.area == 100.0
        assert spatial_obj.centroid == (5, 5, 5)


class TestSpatialRelation:
    """Test suite for SpatialRelation enum"""
    
    def test_spatial_relation_values(self):
        """Test spatial relation enum values"""
        assert SpatialRelation.CONTAINS.value == "contains"
        assert SpatialRelation.INTERSECTS.value == "intersects"
        assert SpatialRelation.ADJACENT.value == "adjacent"
        assert SpatialRelation.NEAR.value == "near"
        assert SpatialRelation.ABOVE.value == "above"
        assert SpatialRelation.BELOW.value == "below"
        assert SpatialRelation.INSIDE.value == "inside"
        assert SpatialRelation.OUTSIDE.value == "outside"


class TestErrorHandling:
    """Test suite for error handling"""
    
    def test_invalid_object_handling(self):
        """Test handling of objects without location data"""
        analyzer = SpatialAnalyzer()
        
        # Object without location
        invalid_obj = BuildingObject(
            object_id="invalid",
            object_type="room",
            properties={},
            location=None
        )
        
        # Should handle gracefully
        spatial_objects = analyzer.analyze_building_objects([invalid_obj])
        assert len(spatial_objects) == 0
        
        # Volume calculation should return 0
        volume = analyzer.calculate_volume(invalid_obj)
        assert volume == 0.0
        
        # Area calculation should return 0
        area = analyzer.calculate_area(invalid_obj)
        assert area == 0.0
    
    def test_distance_calculation_with_invalid_objects(self):
        """Test distance calculation with invalid objects"""
        analyzer = SpatialAnalyzer()
        
        obj1 = BuildingObject(
            object_id="obj1",
            object_type="room",
            properties={},
            location=None
        )
        obj2 = BuildingObject(
            object_id="obj2",
            object_type="room",
            properties={},
            location={"x": 0, "y": 0, "z": 0, "width": 10, "height": 10, "depth": 10}
        )
        
        # Should return infinity for invalid distance
        distance = analyzer.calculate_3d_distance(obj1, obj2)
        assert distance == float('inf')


if __name__ == "__main__":
    pytest.main([__file__]) 