#!/usr/bin/env python3
"""
Test script for SVGX BIM Extractor Migration

This script validates the migration of bim_extractor.py from arx_svg_parser import arx_svg_parser
to svgx_engine with SVGX-specific enhancements.
"""

import sys
import os
import time
import tempfile
import shutil
from pathlib import Path

# Add the svgx_engine to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_bim_extractor_migration():
    """Test the BIM extractor migration."""
    print("🔧 Testing SVGX BIM Extractor Migration")
    print("=" * 60)

    test_results = []

    try:
        # Test 1: Import the BIM extractor
        print("\n1. Testing imports...")
        from svgx_engine.services.bim_extractor import (
            SVGXBIMExtractor,
            SVGXElementType,
            SVGXGeometryType,
            SVGXElementMetadata,
            extract_bim_from_svg
        )
        print("✅ All BIM extractor imports successful")
        test_results.append(("Imports", True, "All classes and functions imported successfully"))
        # Test 2: Test SVGX Element Types
        print("\n2. Testing SVGX Element Types...")
        assert SVGXElementType.ELECTRICAL.value == "electrical"
        assert SVGXElementType.PLUMBING.value == "plumbing"
        assert SVGXElementType.FIRE_ALARM.value == "fire_alarm"
        assert SVGXElementType.STRUCTURAL.value == "structural"
        assert SVGXElementType.UNKNOWN.value == "unknown"

        print("✅ SVGX Element Types working correctly")
        test_results.append(("SVGX Element Types", True, "All element types defined correctly"))
        # Test 3: Test SVGX Geometry Types
        print("\n3. Testing SVGX Geometry Types...")
        assert SVGXGeometryType.CIRCLE.value == "circle"
        assert SVGXGeometryType.RECTANGLE.value == "rectangle"
        assert SVGXGeometryType.PATH.value == "path"
        assert SVGXGeometryType.TEXT.value == "text"
        assert SVGXGeometryType.GROUP.value == "group"
        assert SVGXGeometryType.UNKNOWN.value == "unknown"

        print("✅ SVGX Geometry Types working correctly")
        test_results.append(("SVGX Geometry Types", True, "All geometry types defined correctly"))
        # Test 4: Test SVGX Element Metadata
        print("\n4. Testing SVGX Element Metadata...")
        metadata = SVGXElementMetadata(
            namespace="svgx.core",
            component_type="interactive",
            properties={"physics": "enabled", "behavior": "clickable"},
            attributes={"id": "test-element", "class": "svgx-component"},
            parent_id="parent-group",
            layer="main"
        )

        assert metadata.namespace == "svgx.core"
        assert metadata.component_type == "interactive"
        assert metadata.properties["physics"] == "enabled"
        assert metadata.attributes["id"] == "test-element"
        assert metadata.parent_id == "parent-group"
        assert metadata.layer == "main"

        print("✅ SVGX Element Metadata working correctly")
        test_results.append(("SVGX Element Metadata", True, "Metadata creation and access working"))
        # Test 5: Test SVGX BIM Extractor Initialization
        print("\n5. Testing SVGX BIM Extractor Initialization...")
        extractor = SVGXBIMExtractor()

        # Test system mappings
        assert extractor.group_to_system['electrical'] == 'E'
        assert extractor.group_to_system['plumbing'] == 'P'
        assert extractor.group_to_system['fire'] == 'FA'
        assert extractor.group_to_system['svgx'] == 'SVGX'

        # Test label patterns
        assert 'outlet' in extractor.label_patterns
        assert 'pipe' in extractor.label_patterns
        assert 'horn' in extractor.label_patterns
        assert 'svgx_element' in extractor.label_patterns

        print("✅ SVGX BIM Extractor initialization working correctly")
        test_results.append(("SVGX BIM Extractor Init", True, "Extractor initialization and mappings working"))
        # Test 6: Test SVGX Namespace Extraction
        print("\n6. Testing SVGX Namespace Extraction...")
        from lxml import etree as ET

        # Create test SVGX element
        svg_xml = '''
        <svg xmlns="http://www.w3.org/2000/svg">
            <g id="svgx-group" svgx-namespace="svgx.physics">
                <circle id="test-circle" cx="10" cy="20" r="5" svgx-component="interactive"/>
            </g>
        </svg>
        '''
        root = ET.fromstring(svg_xml)
        # Use XPath with local-name() to ignore namespaces
        circle_elems = root.xpath('.//*[local-name()="circle"]')
        circle_elem = circle_elems[0] if circle_elems else None
        print(f"[DEBUG] circle_elem attrib: {dict(circle_elem.attrib) if circle_elem is not None else None}")
        parent = circle_elem.getparent() if circle_elem is not None else None
        print(f"[DEBUG] parent attrib: {dict(parent.attrib) if parent is not None else None}")

        namespace = extractor.extract_svgx_namespace(circle_elem)
        print(f"[DEBUG] extracted namespace: {namespace}")
        assert namespace == "svgx.physics"

        print("✅ SVGX Namespace Extraction working correctly")
        test_results.append(("SVGX Namespace Extraction", True, "Namespace extraction from elements working"))
        # Test 7: Test SVGX System and Type Classification
        print("\n7. Testing SVGX System and Type Classification...")
        system, type_ = extractor.classify_svgx_system_and_type(
            circle_elem, circle_elem.getparent(), "test-circle", "svgx.physics"
        )
        assert system == "SVGX"
        assert type_ == "svgx_element"

        # Test electrical classification
        electrical_xml = '''
        <svg>
            <g id="electrical-group">
                <circle id="outlet-1" cx="10" cy="20" r="3" class="electrical-outlet"/>
            </g>
        </svg>
        '''
        root = ET.fromstring(electrical_xml)
        outlet_elem = root.find('.//circle')
        system, type_ = extractor.classify_svgx_system_and_type(
            outlet_elem, outlet_elem.getparent(), "electrical-outlet", ""
        )
        assert system == "E"
        assert type_ == "outlet"

        print("✅ SVGX System and Type Classification working correctly")
        test_results.append(("SVGX Classification", True, "System and type classification working"))
        # Test 8: Test SVGX Geometry Extraction
        print("\n8. Testing SVGX Geometry Extraction...")
        coords, geom_type = extractor.extract_svgx_geometry(circle_elem)
        assert coords == (10.0, 20.0)
        assert geom_type == SVGXGeometryType.CIRCLE

        # Test rectangle geometry
        rect_xml = '<rect x="5" y="15" width="10" height="8"/>'
        rect_elem = ET.fromstring(rect_xml)
        coords, geom_type = extractor.extract_svgx_geometry(rect_elem)
        assert coords == (5.0, 15.0)
        assert geom_type == SVGXGeometryType.RECTANGLE

        print("✅ SVGX Geometry Extraction working correctly")
        test_results.append(("SVGX Geometry Extraction", True, "Geometry extraction working for all types"))
        # Test 9: Test SVGX Metadata Extraction
        print("\n9. Testing SVGX Metadata Extraction...")
        metadata = extractor.extract_svgx_metadata(circle_elem, "svgx.physics")
        assert metadata.namespace == "svgx.physics"
        assert metadata.component_type == "interactive"
        assert metadata.properties["component"] == "interactive"
        assert metadata.attributes["id"] == "test-circle"

        print("✅ SVGX Metadata Extraction working correctly")
        test_results.append(("SVGX Metadata Extraction", True, "Metadata extraction working"))
        # Test 10: Test Full BIM Extraction
        print("\n10. Testing Full BIM Extraction...")
        test_svgx = '''
        <svg xmlns="http://www.w3.org/2000/svg">
            <g id="electrical-group">
                <circle id="outlet-1" cx="10" cy="20" r="3" class="electrical-outlet"/>
                <rect id="panel-1" x="50" y="30" width="20" height="15" class="electrical-panel"/>
            </g>
            <g id="plumbing-group">
                <circle id="pipe-1" cx="100" cy="40" r="2" class="plumbing-pipe"/>
            </g>
            <g id="svgx-group" svgx-namespace="svgx.physics">
                <circle id="svgx-element-1" cx="150" cy="60" r="4" svgx-component="interactive"/>
            </g>
        </svg>
        '''

        response = extractor.extract_bim_from_svgx(test_svgx, "building-1", "floor-1")

        assert response.building_id == "building-1"
        assert response.floor_id == "floor-1"
        assert len(response.elements) >= 3

        # Check for electrical elements
        electrical_elements = [e for e in response.elements if e.system == "E"]
        assert len(electrical_elements) >= 2

        # Check for plumbing elements
        plumbing_elements = [e for e in response.elements if e.system == "P"]
        assert len(plumbing_elements) >= 1

        # Check for SVGX elements (mapped to Structural)
        svgx_elements = [e for e in response.elements if "svgx" in e.type]
        assert len(svgx_elements) >= 1

        print("✅ Full BIM Extraction working correctly")
        test_results.append(("Full BIM Extraction", True, "Complete BIM extraction with SVGX support working"))
        # Test 11: Test Backward Compatibility
        print("\n11. Testing Backward Compatibility...")
        response = extract_bim_from_svg(test_svgx, "building-1", "floor-1")
        assert response.building_id == "building-1"
        assert response.floor_id == "floor-1"
        assert len(response.elements) >= 3

        print("✅ Backward Compatibility working correctly")
        test_results.append(("Backward Compatibility", True, "Backward compatibility function working"))
        # Test 12: Test Error Handling
        print("\n12. Testing Error Handling...")
        try:
            # Test with invalid SVG
            extractor.extract_bim_from_svgx("invalid svg content", "building-1", "floor-1")
            assert False, "Should have raised ParserError"
        except Exception as e:
            assert "Failed to parse SVGX content" in str(e)

        print("✅ Error Handling working correctly")
        test_results.append(("Error Handling", True, "Error handling for invalid input working"))
        # Test 13: Test Services Package Integration
        print("\n13. Testing Services Package Integration...")
        from svgx_engine.services import (
            SVGXBIMExtractor,
            SVGXElementType,
            SVGXGeometryType,
            SVGXElementMetadata,
            extract_bim_from_svg
        )

        # Test that all components are available
        extractor = SVGXBIMExtractor()
        element_type = SVGXElementType.ELECTRICAL
        geometry_type = SVGXGeometryType.CIRCLE
        metadata = SVGXElementMetadata()

        print("✅ Services Package Integration working correctly")
        test_results.append(("Services Integration", True, "All BIM extractor components available in services package"))
        # Summary
        print("\n" + "=" * 60)
        print("📊 BIM EXTRACTOR MIGRATION TEST RESULTS")
        print("=" * 60)

        passed_tests = sum(1 for _, passed, _ in test_results if passed)
        total_tests = len(test_results)

        for test_name, passed, details in test_results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} {test_name}: {details}")

        print(f"\n🎯 Overall Result: {passed_tests}/{total_tests} tests passed")

        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED - BIM Extractor Migration Successful!")
            return True
        else:
            print("❌ Some tests failed - BIM Extractor Migration needs attention")
            return False

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_bim_extractor_migration()
    sys.exit(0 if success else 1)
