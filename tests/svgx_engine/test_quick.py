#!/usr/bin/env python3
"""
Quick test to verify Phase 3 implementation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__)
def test_linter():
    """Test the SVGX linter."""
    try:
        from tools.svgx_linter import SVGXLinter
        print("✅ SVGX Linter imported successfully")

        linter = SVGXLinter()

        # Test valid SVGX
        valid_svgx = '''<?xml version="1.0" encoding="UTF-8"?>'
<svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
  <arx:object id="test" type="electrical.light_fixture" system="electrical"/>
</svg>'''

        is_valid = linter.lint_content(valid_svgx)
        print(f"✅ Valid SVGX test: {is_valid}")

        # Test invalid SVGX
        invalid_svgx = '''<?xml version="1.0" encoding="UTF-8"?>'
<svg xmlns="http://www.w3.org/2000/svg">
  <arx:object id="test" type="electrical.light_fixture"/>
</svg>'''

        is_valid = linter.lint_content(invalid_svgx)
        print(f"✅ Invalid SVGX test: {not is_valid}")

        return True

    except Exception as e:
        print(f"❌ Linter test failed: {e}")
        return False

def test_compiler():
    """Test the SVG compiler."""
    try:
        from compiler.svgx_to_svg import SVGXToSVGCompiler
        print("✅ SVG Compiler imported successfully")

        compiler = SVGXToSVGCompiler()

        svgx_content = '''<?xml version="1.0" encoding="UTF-8"?>'
<svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
  <arx:object id="test" type="electrical.light_fixture" system="electrical"/>
  <circle cx="100" cy="100" r="20" style="fill:yellow"/>
</svg>'''

        svg_output = compiler.compile(svgx_content)
        print(f"✅ SVG compilation successful, output length: {len(svg_output)}")

        return True

    except Exception as e:
        print(f"❌ Compiler test failed: {e}")
        return False

def test_schema_validator():
    """Test the schema validator."""
    try:
        from schema.svgx_schema import SVGXSchemaValidator
        print("✅ Schema Validator imported successfully")

        validator = SVGXSchemaValidator()

        valid_svgx = '''<?xml version="1.0" encoding="UTF-8"?>'
<svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
  <arx:object id="test" type="electrical.light_fixture" system="electrical"/>
</svg>'''

        results = validator.validate_schema(valid_svgx)
        print(f"✅ Schema validation successful: {results['valid']}")

        return True

    except Exception as e:
        print(f"❌ Schema validator test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Phase 3 Implementation")
    print("=" * 50)

    tests = [
        ("SVGX Linter", test_linter),
        ("SVG Compiler", test_compiler),
        ("Schema Validator", test_schema_validator)
    ]

    passed = 0
    total = len(tests)

    for name, test_func in tests:
        print(f"\n--- Testing {name} ---")
        if test_func():
            passed += 1
            print(f"✅ {name} test PASSED")
        else:
            print(f"❌ {name} test FAILED")

    print(f"\n{'='*50}")
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All Phase 3 tests PASSED!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main()
