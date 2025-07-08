#!/usr/bin/env python3
"""
Enhanced Spatial & Topological Reasoning Demo

This script demonstrates the enhanced spatial reasoning capabilities:
- Spatial indexing (R-tree and grid-based)
- Topological validation (enclosure, adjacency, connectivity)
- Zone & area calculation with spatial hierarchies
- Advanced spatial queries and analysis
"""

import sys
import os
import logging
import time
from datetime import datetime, timezone

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.enhanced_spatial_reasoning import (
    EnhancedSpatialReasoningEngine, SpatialIndexType, TopologyType,
    SpatialHierarchyLevel
)
from models.bim import (
    BIMModel, Room, Wall, Door, Window, Device, SystemType, DeviceCategory,
    Geometry, GeometryType, RoomType
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_sample_building():
    """Create a sample building for demonstration."""
    logger.info("Creating sample building...")
    
    model = BIMModel()
    
    # Add rooms
    room1 = Room(
        id="conference-room-1",
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
        id="conference-room-2",
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
    
    room3 = Room(
        id="lobby",
        name="Main Lobby",
        geometry=Geometry(
            type=GeometryType.POLYGON,
            coordinates=[[0, 15], [45, 15], [45, 25], [0, 25], [0, 15]]
        ),
        room_type=RoomType.LOBBY,
        room_number="100",
        floor_level=1,
        ceiling_height=4.0
    )
    model.add_element(room3)
    
    # Add walls
    walls = [
        # Exterior walls
        Wall(id="wall-ext-1", name="Exterior Wall 1", 
             geometry=Geometry(type=GeometryType.LINESTRING, coordinates=[[0, 0], [0, 25]]),
             wall_type="exterior", thickness=0.3, height=4.0),
        Wall(id="wall-ext-2", name="Exterior Wall 2", 
             geometry=Geometry(type=GeometryType.LINESTRING, coordinates=[[0, 25], [45, 25]]),
             wall_type="exterior", thickness=0.3, height=4.0),
        Wall(id="wall-ext-3", name="Exterior Wall 3", 
             geometry=Geometry(type=GeometryType.LINESTRING, coordinates=[[45, 25], [45, 0]]),
             wall_type="exterior", thickness=0.3, height=4.0),
        Wall(id="wall-ext-4", name="Exterior Wall 4", 
             geometry=Geometry(type=GeometryType.LINESTRING, coordinates=[[45, 0], [0, 0]]),
             wall_type="exterior", thickness=0.3, height=4.0),
        
        # Interior walls
        Wall(id="wall-int-1", name="Interior Wall 1", 
             geometry=Geometry(type=GeometryType.LINESTRING, coordinates=[[20, 0], [20, 15]]),
             wall_type="interior", thickness=0.15, height=3.0),
        Wall(id="wall-int-2", name="Interior Wall 2", 
             geometry=Geometry(type=GeometryType.LINESTRING, coordinates=[[25, 0], [25, 15]]),
             wall_type="interior", thickness=0.15, height=3.0),
    ]
    
    for wall in walls:
        model.add_element(wall)
    
    # Add doors
    doors = [
        Door(id="door-1", name="Door 1", 
             geometry=Geometry(type=GeometryType.LINESTRING, coordinates=[[10, 0], [10, 2]]),
             door_type="swing", width=2.0, height=2.4),
        Door(id="door-2", name="Door 2", 
             geometry=Geometry(type=GeometryType.LINESTRING, coordinates=[[35, 0], [35, 2]]),
             door_type="swing", width=2.0, height=2.4),
        Door(id="door-3", name="Lobby Door", 
             geometry=Geometry(type=GeometryType.LINESTRING, coordinates=[[22.5, 15], [22.5, 17]]),
             door_type="swing", width=2.0, height=2.4),
    ]
    
    for door in doors:
        model.add_element(door)
    
    # Add devices
    devices = [
        Device(id="ahu-1", name="Air Handler Unit 1", 
               geometry=Geometry(type=GeometryType.POINT, coordinates=[5, 5]),
               system_type=SystemType.HVAC, category=DeviceCategory.AHU),
        Device(id="ahu-2", name="Air Handler Unit 2", 
               geometry=Geometry(type=GeometryType.POINT, coordinates=[30, 5]),
               system_type=SystemType.HVAC, category=DeviceCategory.AHU),
        Device(id="panel-1", name="Electrical Panel 1", 
               geometry=Geometry(type=GeometryType.POINT, coordinates=[15, 20]),
               system_type=SystemType.ELECTRICAL, category=DeviceCategory.PANEL),
        Device(id="outlet-1", name="Electrical Outlet 1", 
               geometry=Geometry(type=GeometryType.POINT, coordinates=[2, 2]),
               system_type=SystemType.ELECTRICAL, category=DeviceCategory.OUTLET),
        Device(id="outlet-2", name="Electrical Outlet 2", 
               geometry=Geometry(type=GeometryType.POINT, coordinates=[27, 2]),
               system_type=SystemType.ELECTRICAL, category=DeviceCategory.OUTLET),
    ]
    
    for device in devices:
        model.add_element(device)
    
    logger.info(f"Created building with {len(model.rooms)} rooms, {len(model.walls)} walls, {len(model.doors)} doors, {len(model.devices)} devices")
    return model


def demonstrate_spatial_indexing(spatial_engine):
    """Demonstrate spatial indexing capabilities."""
    logger.info("\n=== Spatial Indexing Demo ===")
    
    # Build R-tree index
    logger.info("Building R-tree spatial index...")
    start_time = time.time()
    r_tree_index = spatial_engine.build_spatial_index(SpatialIndexType.R_TREE)
    r_tree_build_time = time.time() - start_time
    
    logger.info(f"R-tree index built in {r_tree_build_time:.4f} seconds")
    logger.info(f"Indexed {len(r_tree_index.elements)} elements")
    logger.info(f"Bounds: {r_tree_index.bounds}")
    
    # Build grid index
    logger.info("Building grid spatial index...")
    start_time = time.time()
    grid_index = spatial_engine.build_spatial_index(SpatialIndexType.GRID)
    grid_build_time = time.time() - start_time
    
    logger.info(f"Grid index built in {grid_build_time:.4f} seconds")
    logger.info(f"Grid cells: {len(grid_index.grid_cells)}")
    
    # Test spatial queries
    from shapely.geometry import box
    
    # Query around room 1
    query_box = box(0, 0, 20, 15)
    logger.info("Testing spatial query around room 1...")
    
    start_time = time.time()
    r_tree_results = spatial_engine.spatial_query(query_box, SpatialIndexType.R_TREE)
    r_tree_query_time = time.time() - start_time
    
    start_time = time.time()
    grid_results = spatial_engine.spatial_query(query_box, SpatialIndexType.GRID)
    grid_query_time = time.time() - start_time
    
    logger.info(f"R-tree query found {len(r_tree_results)} elements in {r_tree_query_time:.4f} seconds")
    logger.info(f"Grid query found {len(grid_results)} elements in {grid_query_time:.4f} seconds")
    
    # Show query results
    logger.info("R-tree query results:")
    for element_id in r_tree_results:
        logger.info(f"  - {element_id}")
    
    logger.info("Grid query results:")
    for element_id in grid_results:
        logger.info(f"  - {element_id}")


def demonstrate_topological_validation(spatial_engine):
    """Demonstrate topological validation capabilities."""
    logger.info("\n=== Topological Validation Demo ===")
    
    # Validate room topology
    logger.info("Validating room topology...")
    room_validation = spatial_engine.validate_topology("conference-room-1")
    
    logger.info(f"Room validation - Valid: {room_validation.is_valid}")
    logger.info(f"Score: {room_validation.score:.2f}")
    logger.info("Violations:")
    for violation in room_validation.violations:
        logger.info(f"  - {violation}")
    logger.info("Suggestions:")
    for suggestion in room_validation.suggestions:
        logger.info(f"  - {suggestion}")
    
    # Validate door topology
    logger.info("\nValidating door topology...")
    door_validation = spatial_engine.validate_topology("door-1")
    
    logger.info(f"Door validation - Valid: {door_validation.is_valid}")
    logger.info(f"Score: {door_validation.score:.2f}")
    logger.info("Violations:")
    for violation in door_validation.violations:
        logger.info(f"  - {violation}")
    
    # Validate wall topology
    logger.info("\nValidating wall topology...")
    wall_validation = spatial_engine.validate_topology("wall-int-1")
    
    logger.info(f"Wall validation - Valid: {wall_validation.is_valid}")
    logger.info(f"Score: {wall_validation.score:.2f}")
    
    # Validate device topology
    logger.info("\nValidating device topology...")
    device_validation = spatial_engine.validate_topology("ahu-1")
    
    logger.info(f"Device validation - Valid: {device_validation.is_valid}")
    logger.info(f"Score: {device_validation.score:.2f}")


def demonstrate_zone_calculation(spatial_engine):
    """Demonstrate zone and area calculation capabilities."""
    logger.info("\n=== Zone & Area Calculation Demo ===")
    
    # Calculate zones and areas
    logger.info("Calculating zones and areas...")
    start_time = time.time()
    zone_calculations = spatial_engine.calculate_zones_and_areas()
    calculation_time = time.time() - start_time
    
    logger.info(f"Zone calculation completed in {calculation_time:.4f} seconds")
    logger.info(f"Calculated {len(zone_calculations)} zones")
    
    # Display room zones
    logger.info("\nRoom Zones:")
    for zone_id, zone_calc in zone_calculations.items():
        if zone_calc.zone_type == "room":
            logger.info(f"  {zone_id}:")
            logger.info(f"    Area: {zone_calc.area:.2f} sq units")
            logger.info(f"    Volume: {zone_calc.volume:.2f} cubic units")
            logger.info(f"    Elements: {len(zone_calc.elements)}")
            logger.info(f"    Parent: {zone_calc.parent_zone}")
    
    # Display floor zones
    logger.info("\nFloor Zones:")
    for zone_id, zone_calc in zone_calculations.items():
        if zone_calc.zone_type == "floor":
            logger.info(f"  {zone_id}:")
            logger.info(f"    Area: {zone_calc.area:.2f} sq units")
            logger.info(f"    Volume: {zone_calc.volume:.2f} cubic units")
            logger.info(f"    Rooms: {len(zone_calc.elements)}")
            logger.info(f"    Child zones: {zone_calc.child_zones}")
    
    # Display building zone
    logger.info("\nBuilding Zone:")
    for zone_id, zone_calc in zone_calculations.items():
        if zone_calc.zone_type == "building":
            logger.info(f"  {zone_id}:")
            logger.info(f"    Total Area: {zone_calc.area:.2f} sq units")
            logger.info(f"    Total Volume: {zone_calc.volume:.2f} cubic units")
            logger.info(f"    Total Elements: {len(zone_calc.elements)}")
            logger.info(f"    Floors: {zone_calc.child_zones}")


def demonstrate_spatial_hierarchy(spatial_engine):
    """Demonstrate spatial hierarchy capabilities."""
    logger.info("\n=== Spatial Hierarchy Demo ===")
    
    # Get hierarchy
    hierarchy = spatial_engine.hierarchy_cache.get("building")
    if hierarchy:
        logger.info("Building Spatial Hierarchy:")
        logger.info(f"  Building: {hierarchy['id']}")
        
        for floor_id, floor_data in hierarchy['children'].items():
            logger.info(f"    Floor {floor_data['level']}: {floor_id}")
            logger.info(f"      Rooms: {len(floor_data['children'])}")
            
            for room_id, room_data in floor_data['children'].items():
                logger.info(f"        Room: {room_id} ({room_data['room_type']})")
                logger.info(f"          Area: {room_data['area']:.2f} sq units")


def demonstrate_performance_analysis(spatial_engine):
    """Demonstrate performance analysis capabilities."""
    logger.info("\n=== Performance Analysis Demo ===")
    
    # Get spatial statistics
    stats = spatial_engine.get_spatial_statistics()
    
    logger.info("Spatial Reasoning Statistics:")
    logger.info(f"  Spatial Indices: {stats['spatial_indices']}")
    logger.info(f"  Topology Cache Size: {stats['topology_cache_size']}")
    logger.info(f"  Zone Calculations: {stats['zone_calculations']}")
    logger.info(f"  Hierarchy Levels: {stats['hierarchy_levels']}")
    
    logger.info("\nPerformance Stats:")
    performance_stats = stats['stats']
    logger.info(f"  Spatial Queries: {performance_stats['spatial_queries']}")
    logger.info(f"  Topology Validations: {performance_stats['topology_validations']}")
    logger.info(f"  Zone Calculations: {performance_stats['zone_calculations']}")
    logger.info(f"  Index Updates: {performance_stats['index_updates']}")
    logger.info(f"  Average Query Time: {performance_stats['query_time_avg']:.4f} seconds")


def main():
    """Main demonstration function."""
    logger.info("Enhanced Spatial & Topological Reasoning Demo")
    logger.info("=" * 60)
    
    # Create sample building
    bim_model = create_sample_building()
    
    # Create spatial reasoning engine
    spatial_engine = EnhancedSpatialReasoningEngine(bim_model)
    logger.info("Created enhanced spatial reasoning engine")
    
    # Run demonstrations
    demonstrate_spatial_indexing(spatial_engine)
    demonstrate_topological_validation(spatial_engine)
    demonstrate_zone_calculation(spatial_engine)
    demonstrate_spatial_hierarchy(spatial_engine)
    demonstrate_performance_analysis(spatial_engine)
    
    logger.info("\n" + "=" * 60)
    logger.info("Enhanced Spatial & Topological Reasoning Demo Complete!")
    logger.info("Key features demonstrated:")
    logger.info("  ✓ Spatial indexing (R-tree and grid-based)")
    logger.info("  ✓ Topological validation (enclosure, adjacency, connectivity)")
    logger.info("  ✓ Zone & area calculation with spatial hierarchies")
    logger.info("  ✓ Advanced spatial queries and performance analysis")


if __name__ == "__main__":
    main() 