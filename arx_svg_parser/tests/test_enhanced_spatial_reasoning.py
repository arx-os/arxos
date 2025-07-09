"""
Enhanced Spatial Reasoning Tests

This module tests the enhanced spatial reasoning system including:
- Spatial indexing (R-tree and grid-based)
- Topological validation
- Zone and area calculation
- Spatial hierarchy building
"""

import pytest
import time
from datetime import datetime, timezone
from typing import Dict, List, Any

from ..services.enhanced_spatial_reasoning import (
    EnhancedSpatialReasoningEngine, SpatialIndexType, TopologyType,
    SpatialHierarchyLevel, TopologyValidation, ZoneCalculation
)
from ..models.bim import (
    BIMModel, Room, Wall, Door, Window, Device, SystemType, DeviceCategory,
    Geometry, GeometryType, RoomType
)


class TestEnhancedSpatialReasoning:
    """Test enhanced spatial reasoning features."""
    
    @pytest.fixture
    def sample_bim_model(self):
        """Create a sample BIM model for testing."""
        model = BIMModel()
        
        # Add rooms
        room1 = Room(
            id="room-1",
            name="Conference Room 1",
            geometry=Geometry(
                type=GeometryType.POLYGON,
                coordinates=[[0, 0], [20, 0], [20, 15], [0, 15], [0, 0]]
            ),
            room_type=RoomType.CONFERENCE,
            room_number="101",
            floor_level=1,
            ceiling_height=3.0
        )
        model.add_element(room1)
        
        room2 = Room(
            id="room-2",
            name="Conference Room 2",
            geometry=Geometry(
                type=GeometryType.POLYGON,
                coordinates=[[25, 0], [45, 0], [45, 15], [25, 15], [25, 0]]
            ),
            room_type=RoomType.CONFERENCE,
            room_number="102",
            floor_level=1,
            ceiling_height=3.0
        )
        model.add_element(room2)
        
        # Add walls
        wall1 = Wall(
            id="wall-1",
            name="Wall 1",
            geometry=Geometry(
                type=GeometryType.LINESTRING,
                coordinates=[[0, 0], [0, 15]]
            ),
            wall_type="exterior",
            thickness=0.2,
            height=3.0
        )
        model.add_element(wall1)
        
        wall2 = Wall(
            id="wall-2",
            name="Wall 2",
            geometry=Geometry(
                type=GeometryType.LINESTRING,
                coordinates=[[20, 0], [20, 15]]
            ),
            wall_type="interior",
            thickness=0.15,
            height=3.0
        )
        model.add_element(wall2)
        
        # Add doors
        door1 = Door(
            id="door-1",
            name="Door 1",
            geometry=Geometry(
                type=GeometryType.LINESTRING,
                coordinates=[[10, 0], [10, 2]]
            ),
            door_type="swing",
            width=2.0,
            height=2.4
        )
        model.add_element(door1)
        
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
                coordinates=[30, 5]
            ),
            system_type=SystemType.ELECTRICAL,
            category=DeviceCategory.PANEL
        )
        model.add_element(device2)
        
        return model
    
    @pytest.fixture
    def spatial_engine(self, sample_bim_model):
        """Create a spatial reasoning engine with the sample BIM model."""
        return EnhancedSpatialReasoningEngine(sample_bim_model)
    
    def test_create_spatial_engine(self, spatial_engine):
        """Test creating a spatial reasoning engine."""
        assert spatial_engine is not None
        assert spatial_engine.bim_model is not None
        assert len(spatial_engine.spatial_indices) == 0
        assert len(spatial_engine.topology_cache) == 0
        assert len(spatial_engine.zone_calculations) == 0
    
    def test_build_r_tree_index(self, spatial_engine):
        """Test building R-tree spatial index."""
        spatial_index = spatial_engine.build_spatial_index(SpatialIndexType.R_TREE)
        
        assert spatial_index is not None
        assert spatial_index.index_type == SpatialIndexType.R_TREE
        assert len(spatial_index.elements) > 0
        assert spatial_index.tree is not None
        assert spatial_index.bounds is not None
        
        # Check that all elements are indexed
        assert len(spatial_index.elements) == 6  # 2 rooms + 2 walls + 1 door + 2 devices
    
    def test_build_grid_index(self, spatial_engine):
        """Test building grid-based spatial index."""
        spatial_index = spatial_engine.build_spatial_index(SpatialIndexType.GRID)
        
        assert spatial_index is not None
        assert spatial_index.index_type == SpatialIndexType.GRID
        assert len(spatial_index.elements) > 0
        assert spatial_index.grid_cells is not None
        assert spatial_index.bounds is not None
        
        # Check that grid cells are populated
        assert len(spatial_index.grid_cells) > 0
    
    def test_spatial_query_r_tree(self, spatial_engine):
        """Test spatial queries using R-tree index."""
        # Build R-tree index
        spatial_index = spatial_engine.build_spatial_index(SpatialIndexType.R_TREE)
        
        # Create query geometry (box around room 1)
        from shapely.geometry import box
        query_box = box(0, 0, 20, 15)
        
        # Perform spatial query
        results = spatial_engine.spatial_query(query_box, SpatialIndexType.R_TREE)
        
        assert len(results) > 0
        assert "room-1" in results
        assert "wall-1" in results
        assert "wall-2" in results
        assert "device-1" in results
    
    def test_spatial_query_grid(self, spatial_engine):
        """Test spatial queries using grid index."""
        # Build grid index
        spatial_index = spatial_engine.build_spatial_index(SpatialIndexType.GRID)
        
        # Create query geometry
        from shapely.geometry import box
        query_box = box(0, 0, 20, 15)
        
        # Perform spatial query
        results = spatial_engine.spatial_query(query_box, SpatialIndexType.GRID)
        
        assert len(results) > 0
        assert "room-1" in results
        assert "device-1" in results
    
    def test_validate_room_topology(self, spatial_engine):
        """Test room topology validation."""
        validation = spatial_engine.validate_topology("room-1")
        
        assert isinstance(validation, TopologyValidation)
        assert validation.is_valid is False  # Room should have violations (no proper enclosure)
        assert len(validation.violations) > 0
        assert len(validation.suggestions) > 0
        assert 0.0 <= validation.score <= 1.0
    
    def test_validate_door_topology(self, spatial_engine):
        """Test door topology validation."""
        validation = spatial_engine.validate_topology("door-1")
        
        assert isinstance(validation, TopologyValidation)
        assert len(validation.violations) >= 0
        assert len(validation.suggestions) >= 0
        assert 0.0 <= validation.score <= 1.0
    
    def test_validate_wall_topology(self, spatial_engine):
        """Test wall topology validation."""
        validation = spatial_engine.validate_topology("wall-1")
        
        assert isinstance(validation, TopologyValidation)
        assert len(validation.violations) >= 0
        assert len(validation.suggestions) >= 0
        assert 0.0 <= validation.score <= 1.0
    
    def test_validate_device_topology(self, spatial_engine):
        """Test device topology validation."""
        validation = spatial_engine.validate_topology("device-1")
        
        assert isinstance(validation, TopologyValidation)
        assert len(validation.violations) >= 0
        assert len(validation.suggestions) >= 0
        assert 0.0 <= validation.score <= 1.0
    
    def test_calculate_zones_and_areas(self, spatial_engine):
        """Test zone and area calculation."""
        zone_calculations = spatial_engine.calculate_zones_and_areas()
        
        assert len(zone_calculations) > 0
        
        # Check room zones
        room1_zone = zone_calculations.get("room-1")
        assert room1_zone is not None
        assert room1_zone.zone_type == "room"
        assert room1_zone.area == 300.0  # 20 * 15
        assert room1_zone.volume == 900.0  # 300 * 3
        assert room1_zone.hierarchy_level == SpatialHierarchyLevel.ROOM
        
        # Check building zone
        building_zone = zone_calculations.get("building_main")
        assert building_zone is not None
        assert building_zone.zone_type == "building"
        assert building_zone.hierarchy_level == SpatialHierarchyLevel.BUILDING
        
        # Check floor zone
        floor_zone = zone_calculations.get("floor_1")
        assert floor_zone is not None
        assert floor_zone.zone_type == "floor"
        assert floor_zone.hierarchy_level == SpatialHierarchyLevel.FLOOR
    
    def test_spatial_hierarchy(self, spatial_engine):
        """Test spatial hierarchy building."""
        # Calculate zones first
        spatial_engine.calculate_zones_and_areas()
        
        # Check hierarchy cache
        hierarchy = spatial_engine.hierarchy_cache.get("building")
        assert hierarchy is not None
        assert hierarchy['id'] == "building_main"
        assert hierarchy['type'] == "building"
        assert "floor_1" in hierarchy['children']
        
        floor_hierarchy = hierarchy['children']['floor_1']
        assert floor_hierarchy['type'] == "floor"
        assert floor_hierarchy['level'] == 1
        assert "room-1" in floor_hierarchy['children']
        assert "room-2" in floor_hierarchy['children']
    
    def test_spatial_statistics(self, spatial_engine):
        """Test spatial statistics."""
        # Build index and perform some operations
        spatial_engine.build_spatial_index(SpatialIndexType.R_TREE)
        spatial_engine.validate_topology("room-1")
        spatial_engine.calculate_zones_and_areas()
        
        stats = spatial_engine.get_spatial_statistics()
        
        assert stats['spatial_indices'] == 1
        assert stats['topology_cache_size'] >= 1
        assert stats['zone_calculations'] >= 1
        assert stats['hierarchy_levels'] >= 1
        assert 'stats' in stats
    
    def test_performance_comparison(self, spatial_engine):
        """Test performance comparison between index types."""
        # Test R-tree performance
        start_time = time.time()
        spatial_engine.build_spatial_index(SpatialIndexType.R_TREE)
        r_tree_build_time = time.time() - start_time
        
        # Test grid performance
        start_time = time.time()
        spatial_engine.build_spatial_index(SpatialIndexType.GRID)
        grid_build_time = time.time() - start_time
        
        # Both should be reasonably fast
        assert r_tree_build_time < 1.0
        assert grid_build_time < 1.0
    
    def test_query_performance(self, spatial_engine):
        """Test query performance."""
        # Build both index types
        spatial_engine.build_spatial_index(SpatialIndexType.R_TREE)
        spatial_engine.build_spatial_index(SpatialIndexType.GRID)
        
        # Create query geometry
        from shapely.geometry import box
        query_box = box(0, 0, 50, 50)
        
        # Test R-tree query performance
        start_time = time.time()
        r_tree_results = spatial_engine.spatial_query(query_box, SpatialIndexType.R_TREE)
        r_tree_query_time = time.time() - start_time
        
        # Test grid query performance
        start_time = time.time()
        grid_results = spatial_engine.spatial_query(query_box, SpatialIndexType.GRID)
        grid_query_time = time.time() - start_time
        
        # Both should return similar results
        assert len(r_tree_results) > 0
        assert len(grid_results) > 0
        
        # Both should be fast
        assert r_tree_query_time < 0.1
        assert grid_query_time < 0.1
    
    def test_topology_cache(self, spatial_engine):
        """Test topology validation caching."""
        # First validation
        validation1 = spatial_engine.validate_topology("room-1")
        
        # Second validation (should be cached)
        validation2 = spatial_engine.validate_topology("room-1")
        
        # Results should be identical
        assert validation1.is_valid == validation2.is_valid
        assert validation1.violations == validation2.violations
        assert validation1.score == validation2.score
        
        # Cache should be populated
        assert "room-1" in spatial_engine.topology_cache
    
    def test_zone_calculation_accuracy(self, spatial_engine):
        """Test accuracy of zone calculations."""
        zone_calculations = spatial_engine.calculate_zones_and_areas()
        
        # Check room 1 calculations
        room1_zone = zone_calculations.get("room-1")
        assert room1_zone is not None
        assert abs(room1_zone.area - 300.0) < 0.01  # 20 * 15
        assert abs(room1_zone.volume - 900.0) < 0.01  # 300 * 3
        
        # Check room 2 calculations
        room2_zone = zone_calculations.get("room-2")
        assert room2_zone is not None
        assert abs(room2_zone.area - 300.0) < 0.01  # 20 * 15
        
        # Check building total
        building_zone = zone_calculations.get("building_main")
        assert building_zone is not None
        assert abs(building_zone.area - 600.0) < 0.01  # 300 + 300
    
    def test_hierarchy_relationships(self, spatial_engine):
        """Test spatial hierarchy relationships."""
        zone_calculations = spatial_engine.calculate_zones_and_areas()
        
        # Check parent-child relationships
        room1_zone = zone_calculations.get("room-1")
        floor_zone = zone_calculations.get("floor_1")
        building_zone = zone_calculations.get("building_main")
        
        assert room1_zone.parent_zone == "floor_1"
        assert floor_zone.parent_zone == "building_main"
        assert building_zone.parent_zone is None
        
        assert "room-1" in floor_zone.child_zones
        assert "room-2" in floor_zone.child_zones
        assert "floor_1" in building_zone.child_zones


if __name__ == "__main__":
    pytest.main([__file__]) 