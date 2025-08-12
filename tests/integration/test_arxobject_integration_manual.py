#!/usr/bin/env python3
"""
Manual test script for ArxObject-SVGX integration.

This script tests the integration without requiring pytest.
Run this to verify the ArxObject engine and SVGX rendering work together.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from svgx_engine.integration.arxobject_bridge import ArxObjectToSVGXBridge
from svgx_engine.compiler.enhanced_compiler import EnhancedSVGXCompiler
from svgx_engine.models.enhanced_svgx import EnhancedSVGXDocument
from services.arxobject.client.python_client import ArxObjectClient, ArxObjectGeometry


async def test_basic_integration():
    """Test basic ArxObject to SVGX conversion."""
    print("\n=== Testing Basic ArxObject to SVGX Integration ===\n")
    
    try:
        # Create clients
        print("1. Connecting to ArxObject engine...")
        arxobject_client = ArxObjectClient()
        await arxobject_client.connect()
        print("   ✓ Connected to ArxObject engine")
        
        # Create bridge
        print("\n2. Creating ArxObject-SVGX bridge...")
        bridge = ArxObjectToSVGXBridge()
        await bridge.connect()
        print("   ✓ Bridge connected")
        
        # Create test ArxObject
        print("\n3. Creating test ArxObject (electrical outlet)...")
        obj = await arxobject_client.create_object(
            object_type='ELECTRICAL_OUTLET',
            geometry=ArxObjectGeometry(x=100, y=200, z=48),
            properties={'voltage': 120, 'amperage': 20}
        )
        print(f"   ✓ Created ArxObject with ID: {obj.id}")
        
        # Convert to SVGX
        print("\n4. Converting ArxObject to SVGX element...")
        svgx_element = await bridge.arxobject_to_svgx(obj.id)
        print(f"   ✓ Converted to SVGX element: {svgx_element.tag}")
        print(f"   - Position: {svgx_element.position}")
        print(f"   - Attributes: {list(svgx_element.attributes.keys())}")
        
        # Verify ArxObject data
        print("\n5. Verifying ArxObject data in SVGX element...")
        assert svgx_element.arx_object is not None
        assert svgx_element.arx_object.properties['voltage'] == 120
        print("   ✓ ArxObject data preserved in SVGX element")
        
        # Clean up
        await arxobject_client.close()
        
        print("\n✅ Basic integration test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error in basic integration test: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_region_compilation():
    """Test compiling a region with multiple ArxObjects."""
    print("\n=== Testing Region Compilation ===\n")
    
    try:
        # Create clients
        print("1. Setting up clients and compiler...")
        arxobject_client = ArxObjectClient()
        await arxobject_client.connect()
        
        compiler = EnhancedSVGXCompiler()
        await compiler.initialize()
        print("   ✓ Clients initialized")
        
        # Create multiple test objects
        print("\n2. Creating test building section...")
        objects_created = []
        
        # Create structural columns
        for x in [0, 200, 400]:
            obj = await arxobject_client.create_object(
                object_type='STRUCTURAL_COLUMN',
                geometry=ArxObjectGeometry(
                    x=x, y=100, z=0,
                    width=50, height=50, length=300
                )
            )
            objects_created.append(obj)
            print(f"   ✓ Created column at x={x}")
        
        # Create electrical outlets
        for x in [100, 300]:
            obj = await arxobject_client.create_object(
                object_type='ELECTRICAL_OUTLET',
                geometry=ArxObjectGeometry(x=x, y=100, z=48),
                properties={'voltage': 120}
            )
            objects_created.append(obj)
            print(f"   ✓ Created outlet at x={x}")
        
        # Compile region to SVG
        print("\n3. Compiling region to SVG...")
        svg = await compiler.compile_region(
            min_x=-50, min_y=0,
            max_x=450, max_y=200,
            output_format='svg',
            options={'show_labels': True}
        )
        
        print(f"   ✓ Generated SVG ({len(svg)} characters)")
        
        # Verify all objects are in SVG
        print("\n4. Verifying objects in SVG output...")
        for obj in objects_created:
            assert f'arx-{obj.id}' in svg or str(obj.id) in svg
            print(f"   ✓ Found object {obj.id} in SVG")
        
        # Save SVG to file for inspection
        output_file = Path('/tmp/arxobject_test_output.svg')
        output_file.write_text(svg)
        print(f"\n   💾 SVG saved to: {output_file}")
        
        # Clean up
        await arxobject_client.close()
        
        print("\n✅ Region compilation test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error in region compilation test: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_validation():
    """Test constraint validation integration."""
    print("\n=== Testing Constraint Validation ===\n")
    
    try:
        # Create clients
        print("1. Setting up clients...")
        arxobject_client = ArxObjectClient()
        await arxobject_client.connect()
        
        compiler = EnhancedSVGXCompiler()
        await compiler.initialize()
        print("   ✓ Clients initialized")
        
        # Create potentially conflicting objects
        print("\n2. Creating objects with potential conflicts...")
        
        # Create column
        col = await arxobject_client.create_object(
            object_type='STRUCTURAL_COLUMN',
            geometry=ArxObjectGeometry(x=100, y=100, z=0, width=50, height=50)
        )
        print(f"   ✓ Created column at (100, 100)")
        
        # Create outlet at same position (conflict!)
        outlet = await arxobject_client.create_object(
            object_type='ELECTRICAL_OUTLET',
            geometry=ArxObjectGeometry(x=100, y=100, z=48)
        )
        print(f"   ✓ Created outlet at (100, 100) - potential conflict")
        
        # Compile with validation
        print("\n3. Compiling with validation...")
        result = await compiler.compile_with_validation(
            min_x=0, min_y=0,
            max_x=200, max_y=200
        )
        
        print(f"   ✓ Compilation complete")
        print(f"   - Valid: {result['validation']['valid']}")
        print(f"   - Violations: {len(result['validation']['violations'])}")
        
        if result['validation']['violations']:
            print("\n   ⚠️  Violations detected:")
            for v in result['validation']['violations']:
                print(f"      - Object {v['object_id']}: {v['type']}")
        
        # Clean up
        await arxobject_client.close()
        
        print("\n✅ Validation test completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error in validation test: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all integration tests."""
    print("=" * 60)
    print("ArxObject-SVGX Integration Test Suite")
    print("=" * 60)
    
    # Check if ArxObject service is running
    print("\nChecking ArxObject service availability...")
    try:
        client = ArxObjectClient()
        await client.connect()
        await client.close()
        print("✓ ArxObject service is running")
    except Exception as e:
        print(f"❌ ArxObject service not available: {e}")
        print("\nPlease start the ArxObject service:")
        print("  cd /Users/joelpate/repos/arxos")
        print("  go run services/arxobject/service.go")
        return
    
    # Run tests
    tests = [
        ("Basic Integration", test_basic_integration),
        ("Region Compilation", test_region_compilation),
        ("Constraint Validation", test_validation)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {name}")
        print('='*60)
        success = await test_func()
        results.append((name, success))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{name:30} {status}")
    
    total = len(results)
    passed = sum(1 for _, s in results if s)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All integration tests passed!")
    else:
        print(f"\n⚠️  {total - passed} tests failed")


if __name__ == "__main__":
    asyncio.run(main())