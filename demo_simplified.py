#!/usr/bin/env python3
"""
Simplified 14KB Streaming Architecture Demo.

Demonstrates the core 14KB principle implementation with basic functionality.
"""

import asyncio
import time
import json
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.spatial import (
    SpatialConflictEngine, ArxObject, ArxObjectType, ArxObjectPrecision, 
    ArxObjectGeometry, ArxObjectMetadata, BoundingBox3D
)
from core.streaming import (
    StreamingEngine, UserRole, StreamingConfig,
    ProgressiveDisclosure, LODLevel,
    ViewportBounds
)

print("🚀 Simplified 14KB Streaming Architecture Demo")
print("=" * 50)


def create_simple_building():
    """Create simple building data for demo."""
    
    print("\n📦 Creating simple building data...")
    
    # Initialize spatial engine
    world_bounds = BoundingBox3D(-100.0, 100.0, -100.0, 100.0, -10.0, 20.0)
    spatial_engine = SpatialConflictEngine(world_bounds)
    
    # Create a few representative objects
    objects = []
    
    # Structural beam
    beam_geometry = ArxObjectGeometry(
        x=10.0, y=5.0, z=12.0,
        length=20.0, width=1.0, height=2.0,
        shape_type="rectangular"
    )
    beam_metadata = ArxObjectMetadata(
        name="Main Support Beam",
        material="steel",
        manufacturer="SteelCorp"
    )
    beam = ArxObject(
        arxobject_type=ArxObjectType.STRUCTURAL_BEAM,
        geometry=beam_geometry,
        metadata=beam_metadata,
        precision=ArxObjectPrecision.COARSE
    )
    beam.id = "beam_1"
    objects.append(beam)
    
    # Electrical outlet  
    outlet_geometry = ArxObjectGeometry(
        x=15.0, y=3.0, z=1.0,
        length=0.3, width=0.1, height=0.2,
        shape_type="rectangular"
    )
    outlet_metadata = ArxObjectMetadata(
        name="Wall Outlet",
        material="plastic",
        manufacturer="ElectricCorp",
        custom_attributes={
            "voltage": "120V",
            "amperage": "20A"
        }
    )
    outlet = ArxObject(
        arxobject_type=ArxObjectType.ELECTRICAL_OUTLET,
        geometry=outlet_geometry,
        metadata=outlet_metadata,
        precision=ArxObjectPrecision.FINE
    )
    outlet.id = "outlet_1"
    objects.append(outlet)
    
    # HVAC duct
    duct_geometry = ArxObjectGeometry(
        x=12.0, y=8.0, z=13.0,
        length=15.0, width=1.0, height=0.8,
        shape_type="rectangular"
    )
    duct_metadata = ArxObjectMetadata(
        name="Supply Duct",
        material="galvanized_steel",
        custom_attributes={
            "airflow_cfm": "1200",
            "insulation": "R6"
        }
    )
    duct = ArxObject(
        arxobject_type=ArxObjectType.HVAC_DUCT,
        geometry=duct_geometry,
        metadata=duct_metadata,
        precision=ArxObjectPrecision.STANDARD
    )
    duct.id = "duct_1"
    objects.append(duct)
    
    print(f"✅ Created {len(objects)} building objects")
    
    # Add objects to spatial engine
    for obj in objects:
        spatial_engine.add_arxobject(obj)
    
    return spatial_engine, objects


async def demo_progressive_disclosure_simple():
    """Simple progressive disclosure demo."""
    
    print("\n🎯 Progressive Disclosure Demo")
    print("-" * 30)
    
    spatial_engine, objects = create_simple_building()
    disclosure = ProgressiveDisclosure()
    
    # Test different LOD levels
    test_levels = [LODLevel.BUILDING_OUTLINE, LODLevel.ROOM_LAYOUT, LODLevel.DETAILED_COMPONENTS]
    
    for lod_level in test_levels:
        print(f"\n📊 LOD Level {lod_level.value}: {lod_level.name}")
        
        # Convert objects to dictionaries
        object_dicts = [obj.to_dict() for obj in objects]
        
        # Filter for this LOD level
        filtered = disclosure.filter_objects_for_level(object_dicts, lod_level)
        
        # Estimate bundle size
        size_info = disclosure.estimate_level_size(object_dicts, lod_level)
        
        print(f"   Objects included: {len(filtered)}")
        print(f"   Estimated size: {size_info['total_size_bytes']} bytes")
        print(f"   Within budget: {'✅' if size_info['fits_in_budget'] else '❌'}")


async def demo_streaming_engine_simple():
    """Simple streaming engine demo."""
    
    print("\n🔄 Streaming Engine Demo")
    print("-" * 25)
    
    spatial_engine, objects = create_simple_building()
    
    # Test with architect role (14KB limit)
    config = StreamingConfig()
    engine = StreamingEngine(spatial_engine, config, UserRole.ARCHITECT)
    
    await engine.initialize()
    
    # Create viewport
    viewport = ViewportBounds(
        center_x=15.0, center_y=6.0, center_z=8.0,
        width=30.0, height=20.0, depth=10.0,
        zoom_level=3
    )
    
    print("📺 Loading viewport...")
    
    start_time = time.time()
    result = await engine.set_viewport(viewport)
    load_time = (time.time() - start_time) * 1000
    
    print(f"⏱️  Load time: {load_time:.1f}ms")
    print(f"📦 Objects loaded: {result['object_count']}")
    print(f"📏 Bundle size: {result['bundle_size_estimate']} bytes") 
    print(f"🎚️  LOD Level: {result['lod_level']}")
    
    # Get bundle status
    status = engine.get_bundle_status()
    print(f"📊 Bundle utilization: {status['utilization_percent']:.1f}%")
    print(f"🎭 User role: {status['user_role']}")
    print(f"📝 Bundle limit: {status['bundle_limit_bytes']} bytes")
    
    await engine.shutdown()


async def demo_user_roles():
    """Demo different user roles with bundle limits."""
    
    print("\n👥 User Role Bundle Limits Demo")
    print("-" * 33)
    
    spatial_engine, objects = create_simple_building()
    
    user_roles = [
        (UserRole.CONSTRUCTION_WORKER, "Construction Worker"),
        (UserRole.SUPERINTENDENT, "Superintendent"),  
        (UserRole.ARCHITECT, "Architect")
    ]
    
    for user_role, role_name in user_roles:
        config = StreamingConfig()
        bundle_limit = config.bundle_limits[user_role]
        
        print(f"\n👤 {role_name}")
        print(f"   Bundle limit: {bundle_limit} bytes")
        
        if bundle_limit == float('inf'):
            print("   Mode: Unlimited streaming")
        else:
            print(f"   Mode: {bundle_limit // 1024}KB bundle")


async def main():
    """Run simplified 14KB streaming demo."""
    
    print("🎬 Starting simplified 14KB streaming demo...")
    
    await demo_progressive_disclosure_simple()
    await demo_streaming_engine_simple() 
    await demo_user_roles()
    
    print("\n🎉 Demo completed successfully!")
    print("\n📋 14KB Streaming Architecture Features Demonstrated:")
    print("   ✅ Progressive disclosure with LOD levels")
    print("   ✅ User role-based bundle optimization")
    print("   ✅ Viewport-based streaming")
    print("   ✅ Spatial indexing integration")
    print("   ✅ Bundle size estimation and tracking")
    
    print(f"\n🚀 14KB principle successfully implemented!")


if __name__ == "__main__":
    asyncio.run(main())