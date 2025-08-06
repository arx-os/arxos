#!/usr/bin/env python3
"""
Demo script for SVGX Engine.

This script demonstrates the basic functionality of the SVGX Engine
including parsing, simulation, and compilation.
"""

import sys
import os

# Add the current directory to the path so we can import svgx_engine
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from svgx_engine.parser import SVGXParser
from svgx_engine.runtime import SVGXRuntime
from svgx_engine.compiler import SVGXCompiler


def main():
    """Main demo function."""
    print("SVGX Engine Demo")
    print("=" * 50)

    # Example SVGX content
    svgx_content = """
    <svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx" width="400" height="300">
        <arx:object id="light1" type="electrical.light_fixture" system="electrical">
            <arx:behavior>
                <variables>
                    <variable name="voltage" unit="V">120</variable>
                    <variable name="resistance" unit="ohm">720</variable>
                </variables>
                <calculations>
                    <calculation name="current" formula="voltage / resistance"/>
                    <calculation name="power" formula="voltage * current"/>
                </calculations>
            </arx:behavior>
            <arx:physics>
                <mass unit="kg">2.5</mass>
                <anchor>ceiling</anchor>
                <forces>
                    <force type="gravity" direction="down" value="9.81"/>
                </forces>
            </arx:physics>
        </arx:object>
        <rect x="100" y="100" width="50" height="30" style="fill:yellow;stroke:black"/>
    </svg>
    """

    print("1. Parsing SVGX content...")
    parser = SVGXParser()
    elements = parser.parse(svgx_content)
    print(f"   Parsed {len(elements)} elements")

    # Find objects with behavior
    objects_with_behavior = [elem for elem in elements if elem.arx_behavior]
    print(f"   Found {len(objects_with_behavior)} objects with behavior")

    print("\n2. Running simulation...")
    runtime = SVGXRuntime()

    # Simulate behavior for each object
    for element in objects_with_behavior:
        if element.arx_behavior:
            print(f"   Simulating {element.arx_object.object_id}...")

            # Extract behavior data
            behavior_data = {
                "variables": element.arx_behavior.variables,
                "calculations": element.arx_behavior.calculations,
                "triggers": element.arx_behavior.triggers,
            }

            # Evaluate behavior
            results = runtime.evaluator.evaluate_behavior(behavior_data)
            print(f"     Variables: {results.get('variables', {})}")
            print(f"     Calculations: {results.get('calculations', {})}")

    print("\n3. Compiling to different formats...")
    compiler = SVGXCompiler()

    # Compile to SVG
    try:
        svg_content = compiler.compile(svgx_content, target_format="svg")
        print("   ✓ Compiled to SVG (backward compatible)")
    except Exception as e:
        print(f"   ✗ Failed to compile to SVG: {e}")

    # Compile to JSON
    try:
        json_content = compiler.compile(svgx_content, target_format="json")
        print("   ✓ Compiled to JSON (logic export)")
    except Exception as e:
        print(f"   ✗ Failed to compile to JSON: {e}")

    # Compile to IFC
    try:
        ifc_content = compiler.compile(svgx_content, target_format="ifc")
        print("   ✓ Compiled to IFC (BIM export)")
    except Exception as e:
        print(f"   ✗ Failed to compile to IFC: {e}")

    print("\n4. Validation...")
    is_valid = parser.validate_svgx(svgx_content)
    print(f"   SVGX content is {'valid' if is_valid else 'invalid'}")

    print("\nDemo completed successfully!")
    print("\nNext steps:")
    print("- Create more complex SVGX files with multiple objects")
    print("- Add more sophisticated behavior calculations")
    print("- Implement physics simulation")
    print("- Build visualization tools")


if __name__ == "__main__":
    main()
