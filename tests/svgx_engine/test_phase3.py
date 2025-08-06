#!/usr/bin/env python3
"""
Comprehensive tests for Phase 3 features: Linter, Web IDE, and Compilers.
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from svgx_engine.tools.svgx_linter import SVGXLinter
from svgx_engine.schema.svgx_schema import SVGXSchemaValidator
from svgx_engine.compiler.svgx_to_svg import SVGXToSVGCompiler
from svgx_engine.compiler.svgx_to_json import SVGXToJSONCompiler
from svgx_engine.compiler.svgx_to_ifc import SVGXToIFCCompiler
from svgx_engine.compiler.svgx_to_gltf import SVGXToGLTFCompiler


class TestPhase3Features(unittest.TestCase):
    """Test Phase 3 features: Linter, Web IDE, and Compilers."""

    def setUp(self):
        """Set up test fixtures."""
        self.linter = SVGXLinter()
        self.validator = SVGXSchemaValidator()
        self.svg_compiler = SVGXToSVGCompiler()
        self.json_compiler = SVGXToJSONCompiler()
        self.ifc_compiler = SVGXToIFCCompiler()
        self.gltf_compiler = SVGXToGLTFCompiler()

        self.valid_svgx = """<?xml version="1.0" encoding="UTF-8"?>
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
</svg>"""

        self.invalid_svgx = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg">
  <arx:object id="test" type="invalid_type">
    <arx:behavior>
      <variables>
        <variable name="test">value</variable>
      </variables>
    </arx:behavior>
  </arx:object>
</svg>"""

    def test_linter_valid_svgx(self):
        """Test linter with valid SVGX content."""
        is_valid = self.linter.lint_content(self.valid_svgx)
        self.assertTrue(is_valid)
        self.assertEqual(len(self.linter.errors), 0)

    def test_linter_invalid_svgx(self):
        """Test linter with invalid SVGX content."""
        is_valid = self.linter.lint_content(self.invalid_svgx)
        self.assertFalse(is_valid)
        self.assertGreater(len(self.linter.errors), 0)

    def test_linter_missing_namespace(self):
        """Test linter with missing arx namespace."""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg">
  <arx:object id="test" type="electrical.light_fixture"/>
</svg>"""

        is_valid = self.linter.lint_content(content)
        self.assertFalse(is_valid)
        self.assertIn("Missing arx namespace declaration", self.linter.errors[0])

    def test_linter_missing_required_attributes(self):
        """Test linter with missing required attributes."""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
  <arx:object type="electrical.light_fixture"/>
</svg>"""

        is_valid = self.linter.lint_content(content)
        self.assertFalse(is_valid)
        self.assertIn("missing required 'id' attribute", self.linter.errors[0])

    def test_linter_invalid_precision(self):
        """Test linter with invalid precision values."""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
  <path d="M0,0 L100,100" arx:precision="invalid"/>
</svg>"""

        is_valid = self.linter.lint_content(content)
        self.assertFalse(is_valid)
        self.assertIn("Invalid arx:precision value", self.linter.errors[0])

    def test_schema_validator_valid_svgx(self):
        """Test schema validator with valid SVGX content."""
        results = self.validator.validate_schema(self.valid_svgx)
        self.assertTrue(results["valid"])
        self.assertEqual(len(results["errors"]), 0)

    def test_schema_validator_invalid_svgx(self):
        """Test schema validator with invalid SVGX content."""
        results = self.validator.validate_schema(self.invalid_svgx)
        self.assertFalse(results["valid"])
        self.assertGreater(len(results["errors"]), 0)

    def test_svg_compiler(self):
        """Test SVGX to SVG compiler."""
        try:
            svg_output = self.svg_compiler.compile(self.valid_svgx)
            self.assertIsInstance(svg_output, str)
            self.assertIn("<svg", svg_output)
            self.assertIn('xmlns="http://www.w3.org/2000/svg"', svg_output)
        except Exception as e:
            self.fail(f"SVG compiler failed: {e}")

    def test_json_compiler(self):
        """Test SVGX to JSON compiler."""
        try:
            json_output = self.json_compiler.compile(self.valid_svgx)
            self.assertIsInstance(json_output, str)
            # Verify it's valid JSON
            import json as json_module

            parsed = json_module.loads(json_output)
            self.assertIsInstance(parsed, dict)
        except Exception as e:
            self.fail(f"JSON compiler failed: {e}")

    def test_ifc_compiler(self):
        """Test SVGX to IFC compiler."""
        try:
            ifc_output = self.ifc_compiler.compile(self.valid_svgx)
            self.assertIsInstance(ifc_output, str)
            self.assertIn("IFC", ifc_output)
        except Exception as e:
            self.fail(f"IFC compiler failed: {e}")

    def test_gltf_compiler(self):
        """Test SVGX to GLTF compiler."""
        try:
            gltf_output = self.gltf_compiler.compile(self.valid_svgx)
            self.assertIsInstance(gltf_output, str)
            # Verify it's valid JSON (GLTF is JSON-based)
            import json as json_module

            parsed = json_module.loads(gltf_output)
            self.assertIsInstance(parsed, dict)
        except Exception as e:
            self.fail(f"GLTF compiler failed: {e}")

    def test_linter_file_operations(self):
        """Test linter file operations."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".svgx", delete=False) as f:
            f.write(self.valid_svgx)
            temp_file = f.name

        try:
            is_valid = self.linter.lint_file(temp_file)
            self.assertTrue(is_valid)
        finally:
            os.unlink(temp_file)

    def test_linter_nonexistent_file(self):
        """Test linter with nonexistent file."""
        is_valid = self.linter.lint_file("nonexistent_file.svgx")
        self.assertFalse(is_valid)
        self.assertIn("File not found", self.linter.errors[0])

    def test_common_issues_detection(self):
        """Test detection of common SVGX issues."""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
  <arx:object id="test" type="electrical.light_fixture" system="electrical"/>
  <path d="M0,0 L100,100" arx:precision="5"/>
</svg>"""

        is_valid = self.linter.lint_content(content)
        self.assertTrue(is_valid)  # Should be valid
        # Should have warnings about missing units and behavior
        self.assertGreater(len(self.linter.warnings), 0)

    def test_behavior_validation(self):
        """Test behavior element validation."""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
  <arx:object id="test" type="electrical.light_fixture" system="electrical">
    <arx:behavior>
      <variables>
        <variable name="voltage" unit="V">120</variable>
      </variables>
      <calculations>
        <calculation name="current" formula="voltage / resistance"/>
      </calculations>
    </arx:behavior>
  </arx:object>
</svg>"""

        is_valid = self.linter.lint_content(content)
        self.assertTrue(is_valid)

    def test_physics_validation(self):
        """Test physics element validation."""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
  <arx:object id="test" type="electrical.light_fixture" system="electrical">
    <arx:physics>
      <mass unit="kg">2.5</mass>
      <forces>
        <force type="gravity" value="9.81"/>
      </forces>
    </arx:physics>
  </arx:object>
</svg>"""

        is_valid = self.linter.lint_content(content)
        self.assertTrue(is_valid)

    def test_layer_validation(self):
        """Test layer attribute validation."""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
  <path d="M0,0 L100,100" arx:layer="electrical"/>
  <path d="M0,0 L100,100" arx:layer="invalid_layer"/>
</svg>"""

        is_valid = self.linter.lint_content(content)
        self.assertTrue(is_valid)  # Should be valid
        # Should have warning about invalid layer
        self.assertGreater(len(self.linter.warnings), 0)

    def test_compiler_error_handling(self):
        """Test compiler error handling."""
        invalid_content = "This is not valid SVGX"

        # Test SVG compiler
        with self.assertRaises(Exception):
            self.svg_compiler.compile(invalid_content)

        # Test JSON compiler
        with self.assertRaises(Exception):
            self.json_compiler.compile(invalid_content)

    def test_compiler_preserves_structure(self):
        """Test that compilers preserve SVGX structure."""
        svg_output = self.svg_compiler.compile(self.valid_svgx)

        # Should preserve SVG structure
        self.assertIn("<svg", svg_output)
        self.assertIn('xmlns="http://www.w3.org/2000/svg"', svg_output)

        # Should preserve visual elements
        self.assertIn("<path", svg_output)
        self.assertIn("<circle", svg_output)

    def test_json_compiler_structure(self):
        """Test JSON compiler output structure."""
        import json

        json_output = self.json_compiler.compile(self.valid_svgx)
        parsed = json.loads(json_output)

        # Should have expected structure
        self.assertIn("objects", parsed)
        self.assertIn("elements", parsed)
        self.assertIn("metadata", parsed)

        # Should have parsed objects
        self.assertGreater(len(parsed["objects"]), 0)

    def test_ifc_compiler_structure(self):
        """Test IFC compiler output structure."""
        ifc_output = self.ifc_compiler.compile(self.valid_svgx)

        # Should have IFC header
        self.assertIn("IFC", ifc_output)
        self.assertIn("FILE_SCHEMA", ifc_output)

    def test_gltf_compiler_structure(self):
        """Test GLTF compiler output structure."""
        import json

        gltf_output = self.gltf_compiler.compile(self.valid_svgx)
        parsed = json.loads(gltf_output)

        # Should have GLTF structure
        self.assertIn("asset", parsed)
        self.assertIn("version", parsed["asset"])
        self.assertEqual(parsed["asset"]["version"], "2.0")


if __name__ == "__main__":
    unittest.main()
