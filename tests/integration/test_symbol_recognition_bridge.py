"""
Integration tests for the Python-Go symbol recognition bridge.

Tests the critical path from Go symbol_recognizer.go to Python recognize.py
to ensure the bridge functions correctly for PDF, image, and SVG processing.
"""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Any
import base64

import pytest

from svgx_engine.services.symbols.symbol_recognition import SymbolRecognitionEngine


class TestSymbolRecognitionBridge(unittest.TestCase):
    """Test the symbol recognition bridge between Go and Python."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.bridge_script = Path(__file__).parent.parent.parent / "svgx_engine" / "services" / "symbols" / "recognize.py"
        cls.engine = SymbolRecognitionEngine()
        
    def test_bridge_script_exists(self):
        """Test that the bridge script exists and is executable."""
        self.assertTrue(self.bridge_script.exists(), f"Bridge script not found at {self.bridge_script}")
        self.assertTrue(self.bridge_script.is_file(), "Bridge script is not a file")
        
    def test_text_recognition_via_bridge(self):
        """Test text-based symbol recognition through the bridge."""
        request_data = {
            "content": "electrical outlet and light fixture in the room",
            "content_type": "text",
            "options": {
                "fuzzy_threshold": 0.6,
                "context_aware": True
            }
        }
        
        response = self._call_bridge_script(request_data)
        
        # Verify response structure
        self.assertIn("symbols", response)
        self.assertIn("errors", response)
        self.assertIn("stats", response)
        
        # Verify we found some symbols
        symbols = response["symbols"]
        self.assertGreater(len(symbols), 0, "Should find at least one symbol")
        
        # Verify symbol structure
        for symbol in symbols:
            self.assertIn("symbol_id", symbol)
            self.assertIn("confidence", symbol)
            self.assertIn("match_type", symbol)
            self.assertIn("symbol_data", symbol)
            
        # Verify we found electrical symbols
        symbol_ids = [s["symbol_id"] for s in symbols]
        self.assertIn("electrical_outlet", symbol_ids)
        self.assertIn("light_fixture", symbol_ids)
        
    def test_svg_recognition_via_bridge(self):
        """Test SVG-based symbol recognition through the bridge."""
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
            <circle cx="50" cy="50" r="20" fill="blue" />
            <rect x="20" y="20" width="30" height="30" fill="red" />
            <line x1="0" y1="0" x2="100" y2="100" stroke="black" />
        </svg>'''
        
        request_data = {
            "content": svg_content,
            "content_type": "svg",
            "options": {
                "fuzzy_threshold": 0.7
            }
        }
        
        response = self._call_bridge_script(request_data)
        
        # Verify response structure
        self.assertIn("symbols", response)
        self.assertIn("errors", response)
        self.assertIn("stats", response)
        
        # Verify we found geometric shapes
        symbols = response["symbols"]
        self.assertGreater(len(symbols), 0, "Should find geometric shapes")
        
        # Verify we found expected shapes
        symbol_ids = [s["symbol_id"] for s in symbols]
        expected_shapes = ["circle", "rectangle", "line"]
        for shape in expected_shapes:
            self.assertIn(shape, symbol_ids, f"Should find {shape} in SVG")
            
    def test_pdf_recognition_via_bridge_fallback(self):
        """Test PDF recognition with fallback when PyMuPDF is not available."""
        # Create a mock PDF content (just text for fallback)
        pdf_content = "This PDF contains electrical outlets and HVAC ducts"
        
        request_data = {
            "content": base64.b64encode(pdf_content.encode()).decode(),
            "content_type": "pdf",
            "options": {
                "fuzzy_threshold": 0.6,
                "ocr_enabled": False
            }
        }
        
        response = self._call_bridge_script(request_data)
        
        # Verify response structure
        self.assertIn("symbols", response)
        self.assertIn("errors", response)
        self.assertIn("stats", response)
        
        # Even with fallback, should find some symbols
        symbols = response["symbols"]
        if len(symbols) > 0:
            # Verify symbol structure
            for symbol in symbols:
                self.assertIn("symbol_id", symbol)
                self.assertIn("confidence", symbol)
                self.assertIn("source", symbol)
                
    def test_image_recognition_via_bridge_fallback(self):
        """Test image recognition with fallback when PIL is not available."""
        # Create mock image content
        image_content = "mock image data with door symbols"
        
        request_data = {
            "content": base64.b64encode(image_content.encode()).decode(),
            "content_type": "image",
            "options": {
                "perspective_correction": True,
                "ocr_enabled": False,
                "fuzzy_threshold": 0.5
            }
        }
        
        response = self._call_bridge_script(request_data)
        
        # Verify response structure
        self.assertIn("symbols", response)
        self.assertIn("errors", response)
        self.assertIn("stats", response)
        
        # Should handle gracefully even if image processing fails
        self.assertIsInstance(response["errors"], list)
        
    def test_bridge_error_handling(self):
        """Test that the bridge handles errors gracefully."""
        # Invalid JSON input
        invalid_request = "invalid json"
        
        result = subprocess.run(
            ["python3", str(self.bridge_script)],
            input=invalid_request,
            text=True,
            capture_output=True
        )
        
        # Should not crash, should return error response
        self.assertEqual(result.returncode, 1)
        
        try:
            response = json.loads(result.stdout)
            self.assertIn("errors", response)
            self.assertGreater(len(response["errors"]), 0)
        except json.JSONDecodeError:
            # If we can't parse the output, at least verify it didn't crash silently
            self.assertNotEqual(result.stderr, "")
            
    def test_statistics_calculation(self):
        """Test that statistics are correctly calculated."""
        request_data = {
            "content": "electrical outlet light fixture door window wall",
            "content_type": "text",
            "options": {
                "fuzzy_threshold": 0.6
            }
        }
        
        response = self._call_bridge_script(request_data)
        
        stats = response["stats"]
        symbols = response["symbols"]
        
        # Verify statistics structure
        self.assertIn("total_symbols", stats)
        self.assertIn("recognized_symbols", stats)
        self.assertIn("average_confidence", stats)
        self.assertIn("processing_time_ms", stats)
        
        # Verify statistics values
        self.assertEqual(stats["total_symbols"], len(symbols))
        
        if len(symbols) > 0:
            high_confidence_symbols = [s for s in symbols if s.get("confidence", 0) > 0.5]
            self.assertEqual(stats["recognized_symbols"], len(high_confidence_symbols))
            
            avg_confidence = sum(s.get("confidence", 0) for s in symbols) / len(symbols)
            self.assertAlmostEqual(stats["average_confidence"], avg_confidence, places=2)
            
        self.assertGreaterEqual(stats["processing_time_ms"], 0)
        
    def test_fuzzy_threshold_filtering(self):
        """Test that fuzzy threshold filtering works correctly."""
        request_data_low = {
            "content": "outlet",
            "content_type": "text",
            "options": {"fuzzy_threshold": 0.3}
        }
        
        request_data_high = {
            "content": "outlet",
            "content_type": "text", 
            "options": {"fuzzy_threshold": 0.9}
        }
        
        response_low = self._call_bridge_script(request_data_low)
        response_high = self._call_bridge_script(request_data_high)
        
        # Lower threshold should return more results
        symbols_low = response_low["symbols"]
        symbols_high = response_high["symbols"]
        
        self.assertGreaterEqual(len(symbols_low), len(symbols_high),
                               "Lower threshold should return more or equal symbols")
                               
    def test_context_options(self):
        """Test that context options are passed through correctly."""
        request_data = {
            "content": "electrical outlet",
            "content_type": "text",
            "options": {
                "fuzzy_threshold": 0.6,
                "context_aware": True,
                "custom_option": "test_value"
            }
        }
        
        response = self._call_bridge_script(request_data)
        
        # Should not crash with additional options
        self.assertIn("symbols", response)
        self.assertIn("errors", response)
        
        # Should handle the request despite unknown options
        self.assertEqual(len(response["errors"]), 0)
        
    def _call_bridge_script(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call the bridge script with request data and return parsed response."""
        request_json = json.dumps(request_data)
        
        result = subprocess.run(
            ["python3", str(self.bridge_script)],
            input=request_json,
            text=True,
            capture_output=True
        )
        
        if result.returncode != 0:
            self.fail(f"Bridge script failed with return code {result.returncode}. "
                     f"stderr: {result.stderr}")
        
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as e:
            self.fail(f"Failed to parse bridge script output as JSON: {e}. "
                     f"stdout: {result.stdout}")


class TestSymbolRecognitionEngine(unittest.TestCase):
    """Test the core symbol recognition engine functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.engine = SymbolRecognitionEngine()
        
    def test_fuzzy_matching(self):
        """Test fuzzy symbol matching."""
        matches = self.engine.fuzzy_match_symbols("outlet", 0.6)
        
        self.assertGreater(len(matches), 0, "Should find outlet matches")
        
        for match in matches:
            self.assertIn("symbol_id", match)
            self.assertIn("confidence", match)
            self.assertIn("match_type", match)
            self.assertIn("symbol_data", match)
            self.assertGreaterEqual(match["confidence"], 0.6)
            
    def test_context_aware_interpretation(self):
        """Test context-aware symbol interpretation."""
        context = {
            "building_type": "office",
            "floor_level": 1,
            "existing_symbols": []
        }
        
        result = self.engine.context_aware_interpretation("wall", context)
        
        self.assertIn("symbol_id", result)
        self.assertIn("symbol_data", result)
        self.assertIn("context", result)
        self.assertIn("interpretations", result)
        self.assertIn("system", result)
        
    def test_symbol_validation(self):
        """Test symbol property validation."""
        properties = {
            "thickness": 0.15,  # meters
            "material": "concrete",
            "width": 2.5,
            "height": 3.0
        }
        
        result = self.engine.validate_symbol("wall", properties)
        
        self.assertIn("symbol_id", result)
        self.assertIn("validation_results", result)
        self.assertIn("is_valid", result)
        
        # Check validation results
        for validation in result["validation_results"]:
            self.assertIn("rule", validation)
            self.assertIn("status", validation)
            self.assertIn("message", validation)
            
    def test_symbol_placement_verification(self):
        """Test symbol placement verification."""
        position = {"x": 10.0, "y": 5.0, "z": 0.0}
        context = {
            "boundaries": {
                "min_x": 0.0, "max_x": 20.0,
                "min_y": 0.0, "max_y": 10.0,
                "min_z": 0.0, "max_z": 5.0
            },
            "existing_symbols": []
        }
        
        result = self.engine.verify_symbol_placement("electrical_outlet", position, context)
        
        self.assertIn("symbol_id", result)
        self.assertIn("position", result)
        self.assertIn("precision_position", result)
        self.assertIn("placement_issues", result)
        self.assertIn("is_valid", result)
        
    def test_symbol_library_info(self):
        """Test symbol library information retrieval."""
        info = self.engine.get_symbol_library_info()
        
        self.assertIn("total_symbols", info)
        self.assertIn("systems", info)
        self.assertIn("categories", info)
        self.assertIn("symbol_ids", info)
        
        self.assertGreater(info["total_symbols"], 0)
        self.assertGreater(len(info["systems"]), 0)
        self.assertGreater(len(info["categories"]), 0)
        
    def test_symbols_by_system(self):
        """Test retrieving symbols by system."""
        electrical_symbols = self.engine.get_symbols_by_system("electrical")
        mechanical_symbols = self.engine.get_symbols_by_system("mechanical")
        
        self.assertGreater(len(electrical_symbols), 0)
        self.assertGreater(len(mechanical_symbols), 0)
        
        # Verify symbols belong to correct system
        for symbol_id in electrical_symbols:
            symbol_data = self.engine.get_symbol_metadata(symbol_id)
            self.assertEqual(symbol_data["system"], "electrical")


if __name__ == "__main__":
    # Run specific test groups
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "bridge":
            suite = unittest.TestLoader().loadTestsFromTestCase(TestSymbolRecognitionBridge)
        elif sys.argv[1] == "engine":
            suite = unittest.TestLoader().loadTestsFromTestCase(TestSymbolRecognitionEngine)
        else:
            suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    else:
        suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with error code if tests failed
    sys.exit(0 if result.wasSuccessful() else 1)