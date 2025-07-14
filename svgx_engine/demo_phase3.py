#!/usr/bin/env python3
"""
SVGX Engine Phase 3 Demo - Showcasing Linter, Web IDE, and Compilers.

This demo demonstrates the complete Phase 3 feature set including:
- SVGX Linter with comprehensive validation
- Schema validation
- Multi-format compilation (SVG, JSON, IFC, GLTF)
- Web IDE functionality
- Error handling and reporting
"""

import sys
import json
import tempfile
import os
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from svgx_engine.tools.svgx_linter import SVGXLinter
from svgx_engine.schema.svgx_schema import SVGXSchemaValidator
from svgx_engine.compiler.svgx_to_svg import SVGXToSVGCompiler
from svgx_engine.compiler.svgx_to_json import SVGXToJSONCompiler
from svgx_engine.compiler.svgx_to_ifc import SVGXToIFCCompiler
from svgx_engine.compiler.svgx_to_gltf import SVGXToGLTFCompiler


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def print_section(title: str):
    """Print a formatted section."""
    print(f"\n--- {title} ---")


def demo_linter():
    """Demonstrate the SVGX Linter functionality."""
    print_header("SVGX LINTER DEMO")
    
    linter = SVGXLinter()
    
    # Test cases
    test_cases = [
        {
            "name": "Valid SVGX",
            "content": '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
  <arx:object id="rm201" type="architecture.room" system="architecture">
    <arx:geometry x="0" y="0" width="3000mm" height="4000mm"/>
  </arx:object>
  <path d="M0,0 L3000,0 L3000,4000 L0,4000 Z"
        style="stroke:black;fill:none;stroke-width:2"
        arx:layer="walls"
        arx:precision="1mm"/>
</svg>''',
            "expected": True
        },
        {
            "name": "Missing Namespace",
            "content": '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg">
  <arx:object id="test" type="electrical.light_fixture"/>
</svg>''',
            "expected": False
        },
        {
            "name": "Invalid Precision",
            "content": '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
  <path d="M0,0 L100,100" arx:precision="invalid"/>
</svg>''',
            "expected": False
        },
        {
            "name": "Missing Required Attributes",
            "content": '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
  <arx:object type="electrical.light_fixture"/>
</svg>''',
            "expected": False
        }
    ]
    
    for test_case in test_cases:
        print_section(f"Testing: {test_case['name']}")
        
        is_valid = linter.lint_content(test_case['content'])
        
        print(f"Expected: {test_case['expected']}")
        print(f"Actual: {is_valid}")
        print(f"Status: {'✅ PASS' if is_valid == test_case['expected'] else '❌ FAIL'}")
        
        if linter.errors:
            print("Errors:")
            for error in linter.errors:
                print(f"  ❌ {error}")
        
        if linter.warnings:
            print("Warnings:")
            for warning in linter.warnings:
                print(f"  ⚠️  {warning}")
        
        if linter.info:
            print("Info:")
            for info in linter.info:
                print(f"  ℹ️  {info}")


def demo_schema_validator():
    """Demonstrate the SVGX Schema Validator."""
    print_header("SVGX SCHEMA VALIDATOR DEMO")
    
    validator = SVGXSchemaValidator()
    
    valid_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
  <arx:object id="rm201" type="architecture.room" system="architecture">
    <arx:geometry x="0" y="0" width="3000mm" height="4000mm"/>
  </arx:object>
  <path d="M0,0 L3000,0 L3000,4000 L0,4000 Z"
        style="stroke:black;fill:none;stroke-width:2"
        arx:layer="walls"
        arx:precision="1mm"/>
</svg>'''
    
    invalid_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg">
  <arx:object id="test" type="invalid_type"/>
</svg>'''
    
    print_section("Valid SVGX Schema Validation")
    results = validator.validate_schema(valid_content)
    print(f"Valid: {results['valid']}")
    if results['errors']:
        print("Errors:", results['errors'])
    if results['warnings']:
        print("Warnings:", results['warnings'])
    
    print_section("Invalid SVGX Schema Validation")
    results = validator.validate_schema(invalid_content)
    print(f"Valid: {results['valid']}")
    if results['errors']:
        print("Errors:", results['errors'])
    if results['warnings']:
        print("Warnings:", results['warnings'])


def demo_compilers():
    """Demonstrate the SVGX Compilers."""
    print_header("SVGX COMPILERS DEMO")
    
    # Sample SVGX content
    svgx_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
  <arx:object id="rm201" type="architecture.room" system="architecture">
    <arx:geometry x="0" y="0" width="3000mm" height="4000mm"/>
    <arx:tags>
      <tag>classroom</tag>
      <tag>first_floor</tag>
    </arx:tags>
  </arx:object>

  <path d="M0,0 L3000,0 L3000,4000 L0,4000 Z"
        style="stroke:black;fill:none;stroke-width:2"
        arx:layer="walls"
        arx:precision="1mm"/>
        
  <arx:object id="lf01" type="electrical.light_fixture" system="electrical">
    <arx:geometry x="1500" y="2000"/>
    <arx:behavior>
      <variables>
        <voltage unit="V">120</voltage>
        <power unit="W">20</power>
      </variables>
      <calculations>
        <current formula="power / voltage"/>
      </calculations>
    </arx:behavior>
  </arx:object>
  
  <circle cx="1500" cy="2000" r="50" 
          style="fill:yellow;stroke:black;stroke-width:2"
          arx:layer="electrical"/>
</svg>'''
    
    compilers = [
        ("SVG Compiler", SVGXToSVGCompiler()),
        ("JSON Compiler", SVGXToJSONCompiler()),
        ("IFC Compiler", SVGXToIFCCompiler()),
        ("GLTF Compiler", SVGXToGLTFCompiler())
    ]
    
    for name, compiler in compilers:
        print_section(f"{name}")
        try:
            output = compiler.compile(svgx_content)
            print(f"✅ Successfully compiled to {name}")
            print(f"Output length: {len(output)} characters")
            
            # Show first 200 characters of output
            preview = output[:200] + "..." if len(output) > 200 else output
            print(f"Preview: {preview}")
            
        except Exception as e:
            print(f"❌ Failed to compile: {e}")


def demo_file_operations():
    """Demonstrate file operations with the linter."""
    print_header("FILE OPERATIONS DEMO")
    
    linter = SVGXLinter()
    
    # Create a temporary SVGX file
    temp_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
  <arx:object id="test" type="electrical.light_fixture" system="electrical">
    <arx:geometry x="100" y="100"/>
  </arx:object>
  <circle cx="100" cy="100" r="20" style="fill:yellow"/>
</svg>'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.svgx', delete=False) as f:
        f.write(temp_content)
        temp_file = f.name
    
    try:
        print_section("Linting File")
        is_valid = linter.lint_file(temp_file)
        print(f"File valid: {is_valid}")
        
        if linter.errors:
            print("Errors:")
            for error in linter.errors:
                print(f"  ❌ {error}")
        
        if linter.warnings:
            print("Warnings:")
            for warning in linter.warnings:
                print(f"  ⚠️  {warning}")
        
        print_section("Testing Nonexistent File")
        is_valid = linter.lint_file("nonexistent_file.svgx")
        print(f"File valid: {is_valid}")
        if linter.errors:
            print(f"Error: {linter.errors[0]}")
    
    finally:
        # Clean up
        os.unlink(temp_file)


def demo_web_ide_features():
    """Demonstrate Web IDE features."""
    print_header("WEB IDE FEATURES DEMO")
    
    print_section("Available Features")
    features = [
        "✅ Real-time SVGX editing",
        "✅ Live preview of SVGX content",
        "✅ Syntax validation and error reporting",
        "✅ Compilation to multiple formats",
        "✅ Built-in examples (Basic Room, Electrical System, Mechanical System)",
        "✅ Export functionality (SVG, JSON)",
        "✅ RESTful API endpoints (/api/parse, /api/compile, /api/lint)"
    ]
    
    for feature in features:
        print(f"  {feature}")
    
    print_section("Starting Web IDE")
    print("To start the Web IDE, run:")
    print("  python tools/web_ide.py --port 8080")
    print("Then open http://localhost:8080 in your browser")
    
    print_section("API Endpoints")
    endpoints = [
        ("POST /api/parse", "Parse SVGX content and return element count"),
        ("POST /api/compile", "Compile SVGX to SVG and return result"),
        ("POST /api/lint", "Lint SVGX content and return validation results")
    ]
    
    for endpoint, description in endpoints:
        print(f"  {endpoint}: {description}")


def demo_error_handling():
    """Demonstrate error handling capabilities."""
    print_header("ERROR HANDLING DEMO")
    
    linter = SVGXLinter()
    
    error_cases = [
        {
            "name": "Malformed XML",
            "content": "<svg><arx:object>",
            "expected_error": "XML parsing"
        },
        {
            "name": "Invalid Object Type",
            "content": '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
  <arx:object id="test" type="invalid.type"/>
</svg>''',
            "expected_error": "Unknown object type"
        },
        {
            "name": "Missing Behavior Variables",
            "content": '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
  <arx:object id="test" type="electrical.light_fixture" system="electrical">
    <arx:behavior>
      <variables>
        <variable>120</variable>
      </variables>
    </arx:behavior>
  </arx:object>
</svg>''',
            "expected_error": "Variable missing 'name' attribute"
        }
    ]
    
    for case in error_cases:
        print_section(f"Testing: {case['name']}")
        
        is_valid = linter.lint_content(case['content'])
        print(f"Valid: {is_valid}")
        
        if linter.errors:
            print("Errors detected:")
            for error in linter.errors:
                print(f"  ❌ {error}")
                if case['expected_error'] in error:
                    print(f"  ✅ Expected error pattern found")
        else:
            print("  ⚠️  No errors detected (unexpected)")


def main():
    """Run the complete Phase 3 demo."""
    print("🚀 SVGX Engine Phase 3 Demo")
    print("Demonstrating Linter, Web IDE, and Compilers")
    
    try:
        demo_linter()
        demo_schema_validator()
        demo_compilers()
        demo_file_operations()
        demo_web_ide_features()
        demo_error_handling()
        
        print_header("DEMO COMPLETE")
        print("✅ All Phase 3 features demonstrated successfully!")
        print("\nNext steps:")
        print("  1. Run tests: python -m pytest tests/test_phase3.py")
        print("  2. Start Web IDE: python tools/web_ide.py")
        print("  3. Lint a file: python tools/svgx_linter.py examples/basic_room.svgx")
        print("  4. Continue to Phase 4: Advanced Features")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 