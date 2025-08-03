"""
Spatial Analysis Engine Demonstration

This script demonstrates the capabilities of the new SpatialAnalyzer
with various 3D spatial calculations, volume analysis, and relationship detection.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.ai.arx_mcp.validate.spatial_analyzer import (
    SpatialAnalyzer, SpatialAnalysisError, SpatialRelation, BoundingBox
)
from services.models.mcp_models import BuildingObject


def create_demo_building():
    """Create a demo building with various 3D objects"""
    objects = [
        # Main building structure
        BuildingObject(
            object_id="main_building",
            object_type="building",
            properties={"stories": 3, "height": 30},
            location={"x": 0, "y": 0, "z": 0, "width": 100, "height": 30, "depth": 50}
        ),
        
        # Floors
        BuildingObject(
            object_id="floor_1",
            object_type="floor",
            properties={"level": 1, "material": "concrete"},
            location={"x": 0, "y": 0, "z": 0, "width": 100, "height": 0.3, "depth": 50}
        ),
        BuildingObject(
            object_id="floor_2",
            object_type="floor",
            properties={"level": 2, "material": "concrete"},
            location={"x": 0, "y": 0, "z": 10, "width": 100, "height": 0.3, "depth": 50}
        ),
        BuildingObject(
            object_id="floor_3",
            object_type="floor",
            properties={"level": 3, "material": "concrete"},
            location={"x": 0, "y": 0, "z": 20, "width": 100, "height": 0.3, "depth": 50}
        ),
        
        # Rooms on first floor
        BuildingObject(
            object_id="lobby",
            object_type="room",
            properties={"area": 500, "occupancy": 20, "type": "public"},
            location={"x": 0, "y": 0, "z": 0.3, "width": 25, "height": 9.7, "depth": 20}
        ),
        BuildingObject(
            object_id="office_1",
            object_type="room",
            properties={"area": 200, "occupancy": 4, "type": "private"},
            location={"x": 25, "y": 0, "z": 0.3, "width": 20, "height": 9.7, "depth": 10}
        ),
        BuildingObject(
            object_id="office_2",
            object_type="room",
            properties={"area": 200, "occupancy": 4, "type": "private"},
            location={"x": 45, "y": 0, "z": 0.3, "width": 20, "height": 9.7, "depth": 10}
        ),
        BuildingObject(
            object_id="conference_room",
            object_type="room",
            properties={"area": 300, "occupancy": 12, "type": "meeting"},
            location={"x": 65, "y": 0, "z": 0.3, "width": 35, "height": 9.7, "depth": 20}
        ),
        
        # Structural elements
        BuildingObject(
            object_id="wall_exterior_north",
            object_type="wall",
            properties={"thickness": 0.3, "material": "concrete", "type": "exterior"},
            location={"x": 0, "y": 0, "z": 0, "width": 100, "height": 30, "depth": 0.3}
        ),
        BuildingObject(
            object_id="wall_exterior_south",
            object_type="wall",
            properties={"thickness": 0.3, "material": "concrete", "type": "exterior"},
            location={"x": 0, "y": 49.7, "z": 0, "width": 100, "height": 30, "depth": 0.3}
        ),
        BuildingObject(
            object_id="wall_exterior_east",
            object_type="wall",
            properties={"thickness": 0.3, "material": "concrete", "type": "exterior"},
            location={"x": 99.7, "y": 0, "z": 0, "width": 0.3, "height": 30, "depth": 50}
        ),
        BuildingObject(
            object_id="wall_exterior_west",
            object_type="wall",
            properties={"thickness": 0.3, "material": "concrete", "type": "exterior"},
            location={"x": 0, "y": 0, "z": 0, "width": 0.3, "height": 30, "depth": 50}
        ),
        
        # HVAC systems
        BuildingObject(
            object_id="hvac_main",
            object_type="hvac_unit",
            properties={"capacity": 50000, "efficiency": 0.85, "type": "rooftop"},
            location={"x": 80, "y": 40, "z": 30, "width": 10, "height": 5, "depth": 8}
        ),
        BuildingObject(
            object_id="duct_main",
            object_type="duct",
            properties={"diameter": 1.0, "flow_rate": 2000, "type": "supply"},
            location={"x": 50, "y": 25, "z": 10, "width": 1.0, "height": 1.0, "depth": 50}
        ),
        
        # Electrical systems
        BuildingObject(
            object_id="electrical_panel",
            object_type="electrical_panel",
            properties={"capacity": 400, "voltage": 480, "type": "main"},
            location={"x": 5, "y": 45, "z": 0, "width": 2, "height": 6, "depth": 1}
        ),
        BuildingObject(
            object_id="outlet_1",
            object_type="electrical_outlet",
            properties={"load": 500, "voltage": 120, "circuit": "A"},
            location={"x": 10, "y": 5, "z": 1}
        ),
        BuildingObject(
            object_id="outlet_2",
            object_type="electrical_outlet",
            properties={"load": 800, "voltage": 120, "circuit": "A"},
            location={"x": 30, "y": 5, "z": 1}
        ),
        
        # Plumbing systems
        BuildingObject(
            object_id="water_main",
            object_type="pipe",
            properties={"diameter": 0.2, "flow_rate": 100, "type": "supply"},
            location={"x": 0, "y": 25, "z": 0, "width": 0.2, "height": 0.2, "depth": 30}
        ),
        BuildingObject(
            object_id="sink_1",
            object_type="sink",
            properties={"flow_rate": 2.5, "hot_water": True},
            location={"x": 15, "y": 8, "z": 1}
        ),
        BuildingObject(
            object_id="toilet_1",
            object_type="toilet",
            properties={"flow_rate": 1.6, "tank_volume": 1.28},
            location={"x": 20, "y": 8, "z": 1}
        ),
        
        # Furniture and fixtures
        BuildingObject(
            object_id="desk_1",
            object_type="furniture",
            properties={"type": "desk", "material": "wood"},
            location={"x": 26, "y": 2, "z": 0.3, "width": 6, "height": 2.5, "depth": 3}
        ),
        BuildingObject(
            object_id="chair_1",
            object_type="furniture",
            properties={"type": "chair", "material": "fabric"},
            location={"x": 28, "y": 1, "z": 0.3, "width": 2, "height": 3, "depth": 2}
        )
    ]
    
    return objects


def demonstrate_3d_calculations(analyzer, objects):
    """Demonstrate 3D spatial calculations"""
    print("\n=== 3D Spatial Calculations ===")
    
    # Calculate total volume and area
    total_volume = analyzer.get_total_volume(objects)
    total_area = analyzer.get_total_area(objects)
    
    print(f"Total Building Volume: {total_volume:.2f} cubic units")
    print(f"Total Building Area: {total_area:.2f} square units")
    
    # Calculate individual object volumes
    print("\nIndividual Object Volumes:")
    for obj in objects[:5]:  # Show first 5 objects
        volume = analyzer.calculate_volume(obj)
        area = analyzer.calculate_area(obj)
        print(f"  {obj.object_id:20} | Volume: {volume:8.2f} | Area: {area:8.2f}")
    
    # 3D distance calculations
    print("\n3D Distance Calculations:")
    obj1 = objects[4]  # lobby
    obj2 = objects[5]  # office_1
    distance = analyzer.calculate_3d_distance(obj1, obj2)
    print(f"  Distance between {obj1.object_id} and {obj2.object_id}: {distance:.2f} units")


def demonstrate_spatial_relationships(analyzer, objects):
    """Demonstrate spatial relationship detection"""
    print("\n=== Spatial Relationship Detection ===")
    
    # Test containment relationships
    building = objects[0]  # main_building
    lobby = objects[4]     # lobby
    
    relationships = analyzer.calculate_spatial_relationships(building, lobby)
    print(f"Relationship between {building.object_id} and {lobby.object_id}:")
    for rel in relationships:
        print(f"  - {rel.value}")
    
    # Test adjacency relationships
    office1 = objects[5]   # office_1
    office2 = objects[6]   # office_2
    
    relationships = analyzer.calculate_spatial_relationships(office1, office2)
    print(f"\nRelationship between {office1.object_id} and {office2.object_id}:")
    for rel in relationships:
        print(f"  - {rel.value}")
    
    # Test vertical relationships
    floor1 = objects[1]    # floor_1
    floor2 = objects[2]    # floor_2
    
    relationships = analyzer.calculate_spatial_relationships(floor1, floor2)
    print(f"\nRelationship between {floor1.object_id} and {floor2.object_id}:")
    for rel in relationships:
        print(f"  - {rel.value}")


def demonstrate_intersection_detection(analyzer, objects):
    """Demonstrate intersection detection"""
    print("\n=== Intersection Detection ===")
    
    intersections = analyzer.find_intersections(objects)
    
    if intersections:
        print(f"Found {len(intersections)} intersecting object pairs:")
        for obj1, obj2 in intersections[:5]:  # Show first 5 intersections
            print(f"  - {obj1.object_id} intersects with {obj2.object_id}")
    else:
        print("No intersections found in the building model")


def demonstrate_nearby_objects(analyzer, objects):
    """Demonstrate nearby object detection"""
    print("\n=== Nearby Object Detection ===")
    
    # Find objects near the electrical panel
    target_obj = objects[11]  # electrical_panel
    nearby_objects = analyzer.find_nearby_objects(target_obj, objects, 10.0)
    
    print(f"Objects within 10 units of {target_obj.object_id}:")
    for obj in nearby_objects:
        distance = analyzer.calculate_3d_distance(target_obj, obj)
        print(f"  - {obj.object_id} (distance: {distance:.2f})")


def demonstrate_volume_search(analyzer, objects):
    """Demonstrate volume-based object search"""
    print("\n=== Volume-Based Object Search ===")
    
    # Search for objects in the first floor area
    objects_in_volume = analyzer.find_objects_in_volume(
        objects, 0, 0, 0, 100, 50, 10
    )
    
    print(f"Objects in first floor volume (0,0,0 to 100,50,10):")
    for obj in objects_in_volume:
        print(f"  - {obj.object_id} ({obj.object_type})")


def demonstrate_spatial_statistics(analyzer, objects):
    """Demonstrate comprehensive spatial statistics"""
    print("\n=== Spatial Statistics ===")
    
    stats = analyzer.get_spatial_statistics(objects)
    
    print("Building Statistics:")
    print(f"  Total Volume: {stats['total_volume']:.2f}")
    print(f"  Total Area: {stats['total_area']:.2f}")
    print(f"  Object Count: {stats['object_count']}")
    print(f"  Intersection Count: {stats['intersection_count']}")
    
    print(f"\nOverall Bounding Box:")
    bbox = stats['bounding_box']
    print(f"  Width: {bbox['width']:.2f}")
    print(f"  Height: {bbox['height']:.2f}")
    print(f"  Depth: {bbox['depth']:.2f}")
    print(f"  Volume: {bbox['volume']:.2f}")
    print(f"  Area: {bbox['area']:.2f}")


def demonstrate_performance_optimization(analyzer, objects):
    """Demonstrate performance optimization features"""
    print("\n=== Performance Optimization ===")
    
    import time
    
    # Test spatial index building performance
    start_time = time.time()
    analyzer.build_spatial_index(objects)
    index_time = time.time() - start_time
    
    print(f"Spatial index built for {len(objects)} objects in {index_time:.4f} seconds")
    
    # Test spatial analysis performance
    start_time = time.time()
    analyzer.analyze_building_objects(objects)
    analysis_time = time.time() - start_time
    
    print(f"Spatial analysis completed in {analysis_time:.4f} seconds")
    
    # Test relationship calculation performance
    start_time = time.time()
    for i, obj1 in enumerate(objects[:5]):
        for obj2 in objects[i+1:6]:
            analyzer.calculate_spatial_relationships(obj1, obj2)
    relationship_time = time.time() - start_time
    
    print(f"Relationship calculations completed in {relationship_time:.4f} seconds")


def main():
    """Run the spatial analyzer demonstration"""
    print("Spatial Analysis Engine Demonstration")
    print("=" * 50)
    
    # Create demo building
    objects = create_demo_building()
    print(f"Created demo building with {len(objects)} objects")
    
    # Create spatial analyzer
    analyzer = SpatialAnalyzer()
    
    # Run demonstrations
    demonstrate_3d_calculations(analyzer, objects)
    demonstrate_spatial_relationships(analyzer, objects)
    demonstrate_intersection_detection(analyzer, objects)
    demonstrate_nearby_objects(analyzer, objects)
    demonstrate_volume_search(analyzer, objects)
    demonstrate_spatial_statistics(analyzer, objects)
    demonstrate_performance_optimization(analyzer, objects)
    
    print("\n" + "=" * 50)
    print("Demonstration Complete!")
    print("\nKey Features Demonstrated:")
    print("✅ 3D spatial calculations and measurements")
    print("✅ Volume and area computations")
    print("✅ Spatial relationship detection")
    print("✅ Intersection analysis")
    print("✅ Spatial indexing for performance")
    print("✅ Volume-based object search")
    print("✅ Comprehensive spatial statistics")
    print("✅ Performance optimization")


if __name__ == "__main__":
    main() 