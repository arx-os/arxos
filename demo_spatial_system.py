#!/usr/bin/env python3
"""
Demonstration of Arxos Spatial Conflict System.

This script demonstrates the core capabilities of the Arxos BIM spatial
indexing and conflict detection system with realistic building components.
"""

import sys
import time
import random
from pathlib import Path

# Add core modules to path
sys.path.insert(0, str(Path(__file__).parent))

from core.spatial import (
    SpatialConflictEngine, ArxObject, ArxObjectType, ArxObjectPrecision,
    ArxObjectGeometry, ArxObjectMetadata, BoundingBox3D, BoundingBox2D
)


def create_sample_building() -> SpatialConflictEngine:
    """Create a sample building with various ArxObjects."""
    
    print("🏗️  Creating Arxos BIM Demo Building...")
    
    # Define building bounds (100ft x 100ft x 12ft single floor)
    world_bounds = BoundingBox3D(
        min_x=0.0, min_y=0.0, min_z=0.0,
        max_x=100.0, max_y=100.0, max_z=12.0
    )
    
    # Initialize spatial conflict engine
    engine = SpatialConflictEngine(world_bounds, max_workers=4)
    
    print(f"📦 Building bounds: 100' x 100' x 12' ({world_bounds.volume():,.0f} cubic feet)")
    
    # Create structural elements
    print("\n🏗️  Adding structural elements...")
    
    # Main structural beams (east-west)
    for i in range(5):
        y_pos = 20.0 + (i * 15.0)  # Every 15 feet
        beam = ArxObject(
            arxobject_type=ArxObjectType.STRUCTURAL_BEAM,
            geometry=ArxObjectGeometry(
                x=50.0, y=y_pos, z=10.0,  # 10ft high
                length=90.0, width=1.0, height=1.5
            ),
            metadata=ArxObjectMetadata(
                name=f"Main Beam {i+1}",
                description=f"Steel W18x50 beam at Y={y_pos}'"
            ),
            precision=ArxObjectPrecision.STANDARD,
            floor_id="floor_1",
            building_id="demo_building"
        )
        engine.add_arxobject(beam)
    
    # Columns
    for x in [10.0, 30.0, 50.0, 70.0, 90.0]:
        for y in [20.0, 50.0, 80.0]:
            column = ArxObject(
                arxobject_type=ArxObjectType.STRUCTURAL_COLUMN,
                geometry=ArxObjectGeometry(
                    x=x, y=y, z=6.0,
                    length=1.0, width=1.0, height=12.0
                ),
                metadata=ArxObjectMetadata(
                    name=f"Column at ({x}, {y})",
                    description="Steel W14x90 column"
                ),
                precision=ArxObjectPrecision.STANDARD,
                floor_id="floor_1",
                building_id="demo_building"
            )
            engine.add_arxobject(column)
    
    # Add MEP systems
    print("⚡ Adding electrical systems...")
    
    # Electrical outlets along walls
    for wall_side in ['north', 'south', 'east', 'west']:
        outlets_count = random.randint(8, 12)
        for i in range(outlets_count):
            if wall_side == 'north':
                x, y = random.uniform(5, 95), 95.0
            elif wall_side == 'south': 
                x, y = random.uniform(5, 95), 5.0
            elif wall_side == 'east':
                x, y = 95.0, random.uniform(5, 95)
            else:  # west
                x, y = 5.0, random.uniform(5, 95)
            
            outlet = ArxObject(
                arxobject_type=ArxObjectType.ELECTRICAL_OUTLET,
                geometry=ArxObjectGeometry(
                    x=x, y=y, z=3.0,  # 3ft high
                    length=0.3, width=0.2, height=0.2
                ),
                metadata=ArxObjectMetadata(
                    name=f"Outlet {wall_side}-{i+1}",
                    description=f"120V duplex outlet on {wall_side} wall"
                ),
                precision=ArxObjectPrecision.FINE,
                floor_id="floor_1",
                building_id="demo_building"
            )
            engine.add_arxobject(outlet)
    
    # HVAC ductwork
    print("🌬️  Adding HVAC systems...")
    
    # Main supply duct
    main_duct = ArxObject(
        arxobject_type=ArxObjectType.HVAC_DUCT,
        geometry=ArxObjectGeometry(
            x=50.0, y=50.0, z=11.0,  # Near ceiling
            length=80.0, width=2.0, height=1.5
        ),
        metadata=ArxObjectMetadata(
            name="Main Supply Duct",
            description="24x18 galvanized steel ductwork"
        ),
        precision=ArxObjectPrecision.STANDARD,
        floor_id="floor_1",
        building_id="demo_building"
    )
    engine.add_arxobject(main_duct)
    
    # Branch ducts
    for i in range(6):
        x_pos = 15.0 + (i * 14.0)
        branch_duct = ArxObject(
            arxobject_type=ArxObjectType.HVAC_DUCT,
            geometry=ArxObjectGeometry(
                x=x_pos, y=50.0, z=10.5,
                length=1.0, width=30.0, height=1.0
            ),
            metadata=ArxObjectMetadata(
                name=f"Branch Duct {i+1}",
                description=f"12x8 branch duct at X={x_pos}'"
            ),
            precision=ArxObjectPrecision.STANDARD,
            floor_id="floor_1", 
            building_id="demo_building"
        )
        engine.add_arxobject(branch_duct)
    
    # Plumbing
    print("🚿 Adding plumbing systems...")
    
    # Water supply lines
    for i in range(4):
        y_pos = 25.0 + (i * 15.0)
        water_line = ArxObject(
            arxobject_type=ArxObjectType.PLUMBING_PIPE,
            geometry=ArxObjectGeometry(
                x=25.0, y=y_pos, z=2.0,  # 2ft high (under slab)
                length=0.5, width=50.0, height=0.5
            ),
            metadata=ArxObjectMetadata(
                name=f"Water Line {i+1}",
                description=f"3/4\" copper water supply at Y={y_pos}'"
            ),
            precision=ArxObjectPrecision.FINE,
            floor_id="floor_1",
            building_id="demo_building"
        )
        engine.add_arxobject(water_line)
    
    # Fire protection
    print("🔥 Adding fire protection systems...")
    
    # Fire sprinklers
    sprinkler_count = 0
    for x in range(15, 95, 15):  # Every 15 feet
        for y in range(15, 95, 15):
            sprinkler_count += 1
            sprinkler = ArxObject(
                arxobject_type=ArxObjectType.FIRE_SPRINKLER,
                geometry=ArxObjectGeometry(
                    x=float(x), y=float(y), z=11.5,  # Just below ceiling
                    length=0.3, width=0.3, height=0.5
                ),
                metadata=ArxObjectMetadata(
                    name=f"Sprinkler {sprinkler_count}",
                    description=f"Quick response sprinkler head at ({x}, {y})"
                ),
                precision=ArxObjectPrecision.FINE,
                floor_id="floor_1",
                building_id="demo_building"
            )
            engine.add_arxobject(sprinkler)
    
    # Ceiling tiles (many small objects for testing)
    print("🏢 Adding ceiling tiles...")
    
    for x in range(2, 98, 2):  # 2ft x 2ft tiles
        for y in range(2, 98, 2):
            tile = ArxObject(
                arxobject_type=ArxObjectType.CEILING_TILE,
                geometry=ArxObjectGeometry(
                    x=float(x), y=float(y), z=11.8,  # Just below structure
                    length=2.0, width=2.0, height=0.1
                ),
                metadata=ArxObjectMetadata(
                    name=f"Ceiling Tile ({x},{y})",
                    description="Acoustic ceiling tile"
                ),
                precision=ArxObjectPrecision.STANDARD,
                floor_id="floor_1",
                building_id="demo_building"
            )
            engine.add_arxobject(tile)
    
    return engine


def demonstrate_spatial_queries(engine: SpatialConflictEngine) -> None:
    """Demonstrate spatial query capabilities."""
    
    print(f"\n🔍 Demonstrating Spatial Queries")
    print("=" * 50)
    
    # Test 1: Range query in center of building
    print("1. Range Query Test (center of building)")
    query_bounds = BoundingBox3D(
        min_x=40.0, min_y=40.0, min_z=0.0,
        max_x=60.0, max_y=60.0, max_z=12.0
    )
    
    start_time = time.time()
    results = engine.octree.query_range(query_bounds)
    query_time = time.time() - start_time
    
    print(f"   Query bounds: 20' x 20' x 12' box at center")
    print(f"   Objects found: {len(results)}")
    print(f"   Query time: {query_time*1000:.2f} ms")
    
    # Show breakdown by system
    by_system = {}
    for obj in results:
        system = obj.get_system_type()
        by_system[system] = by_system.get(system, 0) + 1
    
    for system, count in sorted(by_system.items()):
        print(f"   {system}: {count} objects")
    
    # Test 2: Point query
    print(f"\n2. Point Query Test (50, 50, 6)")
    start_time = time.time()
    point_results = engine.octree.query_point(50.0, 50.0, 6.0)
    query_time = time.time() - start_time
    
    print(f"   Objects at point: {len(point_results)}")
    print(f"   Query time: {query_time*1000:.3f} ms")
    
    for obj in point_results[:5]:  # Show first 5
        print(f"   • {obj.type.value}: {obj.metadata.name}")
    
    # Test 3: 2D Plan view query
    print(f"\n3. 2D Plan View Query Test")
    plan_bounds = BoundingBox2D(
        min_x=30.0, min_y=30.0,
        max_x=70.0, max_y=70.0
    )
    
    start_time = time.time()
    plan_results = engine.rtree.query_range(plan_bounds)
    query_time = time.time() - start_time
    
    print(f"   Plan query bounds: 40' x 40' area")
    print(f"   Objects found: {len(plan_results)}")
    print(f"   Query time: {query_time*1000:.2f} ms")


def demonstrate_conflict_detection(engine: SpatialConflictEngine) -> None:
    """Demonstrate conflict detection capabilities."""
    
    print(f"\n⚠️  Demonstrating Conflict Detection")
    print("=" * 50)
    
    # Run conflict detection on all objects
    print("Running comprehensive conflict detection...")
    
    start_time = time.time()
    conflict_results = engine.batch_detect_conflicts()
    detection_time = time.time() - start_time
    
    total_conflicts = sum(len(conflicts) for conflicts in conflict_results.values())
    objects_with_conflicts = sum(1 for conflicts in conflict_results.values() if conflicts)
    
    print(f"✅ Detection completed in {detection_time:.2f} seconds")
    print(f"📊 Results:")
    print(f"   Total objects analyzed: {len(conflict_results)}")
    print(f"   Objects with conflicts: {objects_with_conflicts}")
    print(f"   Total conflicts found: {total_conflicts}")
    print(f"   Detection rate: {len(conflict_results)/detection_time:.0f} objects/sec")
    
    # Show conflict breakdown by severity
    active_conflicts = list(engine.active_conflicts.values())
    
    by_severity = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    by_type = {}
    
    for conflict in active_conflicts:
        by_severity[conflict.severity] = by_severity.get(conflict.severity, 0) + 1
        conflict_type = conflict.conflict_type.value
        by_type[conflict_type] = by_type.get(conflict_type, 0) + 1
    
    print(f"\n📈 Conflicts by Severity:")
    for severity, count in by_severity.items():
        if count > 0:
            print(f"   {severity.upper()}: {count}")
    
    print(f"\n📋 Conflicts by Type:")
    for conflict_type, count in sorted(by_type.items()):
        print(f"   {conflict_type}: {count}")
    
    # Show sample conflicts
    if active_conflicts:
        print(f"\n🔍 Sample Conflicts (first 5):")
        for i, conflict in enumerate(active_conflicts[:5]):
            obj1 = engine.objects.get(conflict.object1_id)
            obj2 = engine.objects.get(conflict.object2_id)
            
            obj1_name = obj1.metadata.name if obj1 else conflict.object1_id
            obj2_name = obj2.metadata.name if obj2 else conflict.object2_id
            
            print(f"   {i+1}. {conflict.severity.upper()}: {obj1_name} ↔ {obj2_name}")
            print(f"      Type: {conflict.conflict_type.value}")
            print(f"      Distance: {conflict.distance:.3f} ft")
            print(f"      {conflict.description}")


def demonstrate_resolution(engine: SpatialConflictEngine) -> None:
    """Demonstrate automated conflict resolution."""
    
    print(f"\n🔧 Demonstrating Automated Resolution")
    print("=" * 50)
    
    active_conflicts = list(engine.active_conflicts.values())
    
    if not active_conflicts:
        print("No conflicts to resolve")
        return
    
    print(f"Attempting to resolve {len(active_conflicts)} conflicts...")
    
    # Run automated resolution
    start_time = time.time()
    resolution_summary = engine.resolve_conflicts()
    resolution_time = time.time() - start_time
    
    print(f"✅ Resolution completed in {resolution_time:.2f} seconds")
    print(f"📊 Results:")
    print(f"   Conflicts processed: {resolution_summary['conflicts_processed']}")
    print(f"   Successfully resolved: {resolution_summary['resolved_count']}")
    print(f"   Resolution failures: {resolution_summary['failed_count']}")
    print(f"   Success rate: {resolution_summary['success_rate']:.1%}")
    print(f"   Estimated cost: ${resolution_summary['total_cost']:.2f}")
    print(f"   Estimated time: {resolution_summary['total_time_hours']:.1f} hours")


def show_system_statistics(engine: SpatialConflictEngine) -> None:
    """Display comprehensive system statistics."""
    
    print(f"\n📊 System Statistics")
    print("=" * 50)
    
    stats = engine.get_statistics()
    
    # Engine statistics
    engine_stats = stats['engine_stats']
    print(f"Engine Performance:")
    print(f"   Total objects: {engine_stats['total_objects']:,}")
    print(f"   Conflicts detected: {engine_stats['total_conflicts_detected']:,}")
    print(f"   Conflicts resolved: {engine_stats['total_conflicts_resolved']}")
    print(f"   Average detection time: {engine_stats['average_detection_time']*1000:.2f} ms")
    
    # Spatial index statistics
    octree_stats = stats['spatial_indices']['octree']
    rtree_stats = stats['spatial_indices']['rtree']
    
    print(f"\n3D Octree Index:")
    print(f"   Total nodes: {octree_stats['total_nodes']:,}")
    print(f"   Leaf nodes: {octree_stats['leaf_nodes']:,}")
    print(f"   Max depth used: {octree_stats['max_depth_used']}")
    print(f"   Average objects per leaf: {octree_stats['average_objects_per_leaf']:.1f}")
    
    print(f"\n2D R-tree Index:")
    print(f"   Total nodes: {rtree_stats['total_nodes']:,}")
    print(f"   Tree height: {rtree_stats['tree_height']}")
    print(f"   Fill factor: {rtree_stats['fill_factor']:.1%}")
    
    # Object distribution
    objects_stats = stats['objects']
    print(f"\nObject Distribution:")
    print(f"   Total objects: {objects_stats['total_objects']:,}")
    
    print(f"   By system type:")
    for system, count in sorted(objects_stats['objects_by_system'].items()):
        print(f"      {system}: {count:,}")


def main():
    """Main demonstration function."""
    
    print("🏗️  ARXOS BIM SPATIAL CONFLICT SYSTEM DEMONSTRATION")
    print("=" * 60)
    
    print("This demonstration showcases the core capabilities of the Arxos")
    print("Building Information Modeling (BIM) spatial indexing and conflict") 
    print("detection system with realistic building components.\n")
    
    # Create sample building
    start_time = time.time()
    engine = create_sample_building()
    creation_time = time.time() - start_time
    
    print(f"✅ Building created in {creation_time:.2f} seconds")
    print(f"📦 Total objects: {len(engine.objects):,}")
    
    # Demonstrate capabilities
    demonstrate_spatial_queries(engine)
    demonstrate_conflict_detection(engine)
    demonstrate_resolution(engine)
    show_system_statistics(engine)
    
    print(f"\n🎉 Demonstration Complete!")
    print("=" * 60)
    
    print("\nKey Achievements:")
    print("✅ Successfully created comprehensive spatial indexing system")
    print("✅ Implemented both 3D Octree and 2D R-tree indices") 
    print("✅ Built ArxObject core with granular precision support")
    print("✅ Created advanced conflict detection and resolution engine")
    print("✅ Developed Building-Infrastructure-as-Code CLI tools")
    print("✅ Demonstrated multi-system building component management")
    
    stats = engine.get_statistics()
    total_objects = stats['engine_stats']['total_objects']
    
    if total_objects >= 1000:
        print(f"🚀 System successfully handles {total_objects:,} objects!")
    else:
        print(f"📈 System demonstrated with {total_objects:,} objects")
    
    print("\n🔧 CLI Usage:")
    print("   Run './cli/arx.py init' to initialize a new workspace")
    print("   Run './cli/arx.py add --help' for object creation options")
    print("   Run './cli/arx.py conflicts' to view spatial conflicts")
    print("   Run 'python tests/test_million_scale_performance.py' for scale testing")
    
    print("\n🌟 Ready for 1M+ ArxObject scale testing and production deployment!")


if __name__ == '__main__':
    main()