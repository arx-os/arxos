"""
Test suite for Symbol Library Zoom Integration

This module tests all aspects of the zoom integration system including:
- Symbol scaling at different zoom levels
- Consistency validation
- Performance testing
- Issue detection and fixing
"""

import unittest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to the path to import the service
import sys
sys.path.append(str(Path(__file__).parent.parent))

from services.symbol_zoom_integration import (
    SymbolZoomIntegration, 
    ZoomLevel, 
    SymbolScaleData
)


class TestSymbolZoomIntegration(unittest.TestCase):
    """Test cases for SymbolZoomIntegration class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test symbol library
        self.test_dir = tempfile.mkdtemp()
        self.symbol_library_path = Path(self.test_dir) / "test-symbol-library"
        self.symbol_library_path.mkdir()
        
        # Create test symbols
        self.create_test_symbols()
        
        # Initialize the integration service
        self.integration = SymbolZoomIntegration(str(self.symbol_library_path))
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def create_test_symbols(self):
        """Create test symbol files for testing."""
        test_symbols = {
            "ahu": {
                "symbol_id": "ahu",
                "system": "mechanical",
                "display_name": "Air Handling Unit",
                "svg": '<g id="ahu"><rect x="0" y="0" width="40" height="20" fill="#ccc" stroke="#000"/><text x="20" y="15" font-size="10" text-anchor="middle">AHU</text></g>',
                "dimensions": {"width": 40, "height": 20},
                "default_scale": 1.0
            },
            "receptacle": {
                "symbol_id": "receptacle",
                "system": "electrical",
                "display_name": "Receptacle",
                "svg": '<g id="receptacle"><circle cx="10" cy="10" r="7" fill="#fff" stroke="#000"/><text x="10" y="14" font-size="8" text-anchor="middle">R</text></g>',
                "dimensions": {"width": 20, "height": 20},
                "default_scale": 1.0
            },
            "invalid_symbol": {
                "symbol_id": "invalid_symbol",
                "system": "test",
                "display_name": "Invalid Symbol",
                # Missing SVG and dimensions
            }
        }
        
        for symbol_id, symbol_data in test_symbols.items():
            file_path = self.symbol_library_path / f"{symbol_id}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(symbol_data, f, indent=4)
    
    def test_initialization(self):
        """Test that the integration service initializes correctly."""
        self.assertIsNotNone(self.integration)
        self.assertEqual(len(self.integration.zoom_levels), 8)
        self.assertEqual(self.integration.consistency_threshold, 0.1)
        self.assertTrue(self.integration.enable_lod)
    
    def test_zoom_levels_initialization(self):
        """Test that zoom levels are initialized with correct values."""
        zoom_levels = self.integration.zoom_levels
        
        # Check that zoom levels are in ascending order
        for i in range(len(zoom_levels) - 1):
            self.assertLess(zoom_levels[i].level, zoom_levels[i + 1].level)
        
        # Check specific zoom levels
        normal_zoom = next(z for z in zoom_levels if z.name == "normal")
        self.assertEqual(normal_zoom.level, 1.0)
        self.assertEqual(normal_zoom.scale_factor, 1.0)
        self.assertEqual(normal_zoom.lod_level, 3)
    
    def test_load_symbol_library(self):
        """Test loading symbols from the library."""
        symbols = self.integration.load_symbol_library()
        
        self.assertIn("ahu", symbols)
        self.assertIn("receptacle", symbols)
        self.assertIn("invalid_symbol", symbols)
        
        # Check symbol data
        ahu_symbol = symbols["ahu"]
        self.assertEqual(ahu_symbol["display_name"], "Air Handling Unit")
        self.assertEqual(ahu_symbol["system"], "mechanical")
        self.assertIn("svg", ahu_symbol)
    
    def test_calculate_optimal_scale(self):
        """Test optimal scale calculation for different zoom levels."""
        # Test normal zoom level
        scale = self.integration.calculate_optimal_scale(1.0)
        self.assertGreater(scale, 0)  # Should be positive
        
        # Test zoom out
        scale = self.integration.calculate_optimal_scale(0.5)
        self.assertGreater(scale, 0)  # Should be positive
        
        # Test zoom in
        scale = self.integration.calculate_optimal_scale(2.0)
        self.assertGreater(scale, 0)  # Should be positive
        
        # Test with base scale
        scale = self.integration.calculate_optimal_scale(1.0, 2.0)
        self.assertGreater(scale, 0)  # Should be positive
        
        # Test extreme zoom levels (should be clamped)
        scale = self.integration.calculate_optimal_scale(0.01)  # Very small
        self.assertGreater(scale, 0)
        
        scale = self.integration.calculate_optimal_scale(100.0)  # Very large
        self.assertLess(scale, 10.0)  # Should be reasonable
    
    def test_get_zoom_level_info(self):
        """Test getting zoom level information."""
        # Test exact match
        zoom_info = self.integration.get_zoom_level_info(1.0)
        self.assertEqual(zoom_info.name, "normal")
        
        # Test closest match
        zoom_info = self.integration.get_zoom_level_info(1.5)
        self.assertIn(zoom_info.name, ["normal", "large"])  # Should be closest to either 1.0 or 2.0
        
        # Test extreme values
        zoom_info = self.integration.get_zoom_level_info(0.01)
        self.assertEqual(zoom_info.name, "micro")
        
        zoom_info = self.integration.get_zoom_level_info(100.0)
        self.assertEqual(zoom_info.name, "extreme")
    
    def test_scale_symbol_svg(self):
        """Test SVG symbol scaling."""
        original_svg = '<g id="test"><rect x="0" y="0" width="10" height="10"/></g>'
        
        # Test no scaling
        scaled = self.integration.scale_symbol_svg(original_svg, 1.0)
        self.assertEqual(scaled, original_svg)
        
        # Test scaling up
        scaled = self.integration.scale_symbol_svg(original_svg, 2.0)
        self.assertIn('transform="scale(2.0)"', scaled)
        
        # Test scaling down
        scaled = self.integration.scale_symbol_svg(original_svg, 0.5)
        self.assertIn('transform="scale(0.5)"', scaled)
        
        # Test with existing transform
        svg_with_transform = '<g id="test" transform="translate(10,10)"><rect x="0" y="0" width="10" height="10"/></g>'
        scaled = self.integration.scale_symbol_svg(svg_with_transform, 2.0)
        self.assertIn('transform="translate(10,10) scale(2.0)"', scaled)
        
        # Test invalid SVG
        scaled = self.integration.scale_symbol_svg("", 2.0)
        self.assertEqual(scaled, "")
    
    def test_validate_symbol_consistency(self):
        """Test symbol consistency validation across zoom levels."""
        zoom_levels = [0.5, 1.0, 2.0]
        scale_data = self.integration.validate_symbol_consistency("ahu", zoom_levels)
        
        self.assertEqual(len(scale_data), 3)
        
        for data in scale_data:
            self.assertEqual(data.symbol_id, "ahu")
            self.assertEqual(data.base_width, 40)
            self.assertEqual(data.base_height, 20)
            self.assertIn(data.zoom_level, zoom_levels)
            self.assertGreater(data.current_scale, 0)
            self.assertGreater(data.actual_width, 0)
            self.assertGreater(data.actual_height, 0)
    
    def test_validate_symbol_consistency_invalid_symbol(self):
        """Test consistency validation with invalid symbol."""
        scale_data = self.integration.validate_symbol_consistency("nonexistent", [1.0])
        self.assertEqual(len(scale_data), 0)
    
    def test_test_symbol_placement(self):
        """Test symbol placement testing."""
        test_positions = [(100, 100), (200, 200)]
        zoom_levels = [0.5, 1.0, 2.0]
        
        results = self.integration.test_symbol_placement("ahu", test_positions, zoom_levels)
        
        self.assertEqual(results["symbol_id"], "ahu")
        self.assertEqual(results["test_positions"], 2)
        self.assertEqual(results["zoom_levels"], 3)
        self.assertEqual(len(results["placement_tests"]), 6)  # 2 positions * 3 zoom levels
        self.assertEqual(len(results["scaling_tests"]), 6)
        
        # Check performance metrics
        metrics = results["performance_metrics"]
        self.assertEqual(metrics["total_tests"], 6)
        self.assertEqual(metrics["successful_placements"], 6)
        self.assertGreater(metrics["average_scale_factor"], 0)
    
    def test_test_symbol_placement_invalid_symbol(self):
        """Test placement testing with invalid symbol."""
        results = self.integration.test_symbol_placement("nonexistent", [(100, 100)], [1.0])
        self.assertIn("error", results)
    
    def test_fix_symbol_scaling_issues(self):
        """Test fixing symbol scaling issues."""
        # Test with invalid symbol
        results = self.integration.fix_symbol_scaling_issues("invalid_symbol")
        
        self.assertEqual(results["symbol_id"], "invalid_symbol")
        self.assertGreater(results["issues_found"], 0)
        self.assertIn("Missing dimensions", results["issues"])
        self.assertIsNotNone(results["fixed_data"])
        
        # Test with valid symbol
        results = self.integration.fix_symbol_scaling_issues("ahu")
        self.assertEqual(results["issues_found"], 0)
        self.assertIsNone(results["fixed_data"])
    
    def test_fix_symbol_scaling_issues_nonexistent(self):
        """Test fixing issues with nonexistent symbol."""
        results = self.integration.fix_symbol_scaling_issues("nonexistent")
        self.assertIn("error", results)
    
    def test_validate_symbol_library(self):
        """Test entire symbol library validation."""
        results = self.integration.validate_symbol_library()
        
        self.assertEqual(results["total_symbols"], 3)
        # At least some symbols should be valid or invalid
        self.assertGreaterEqual(results["valid_symbols"] + results["invalid_symbols"], 1)
        
        # Check that invalid symbols are identified (if any)
        if results["invalid_symbols"] > 0:
            self.assertIn("invalid_symbol", results["symbol_issues"])
        
        # Check recommendations (if any issues found)
        if results["invalid_symbols"] > 0:
            self.assertGreater(len(results["recommendations"]), 0)
    
    def test_generate_zoom_test_report(self):
        """Test generation of zoom test report."""
        report = self.integration.generate_zoom_test_report()
        
        # Check that report is HTML
        self.assertIn("<!DOCTYPE html>", report)
        self.assertIn("<title>Symbol Library Zoom Integration Test Report</title>", report)
        
        # Check that report contains expected sections
        self.assertIn("Summary", report)
        self.assertIn("Zoom Level Configuration", report)
        self.assertIn("Symbol Issues", report)
    
    def test_cache_management(self):
        """Test that the scale cache is properly managed."""
        # Fill cache
        for i in range(100):
            self.integration.calculate_optimal_scale(1.0 + i * 0.1, 1.0)
        
        # Check cache size is limited
        self.assertLessEqual(len(self.integration.scale_cache), self.integration.max_cache_size)
    
    def test_performance_with_large_scale_cache(self):
        """Test performance with large scale cache."""
        # Test that cache doesn't grow indefinitely
        initial_cache_size = len(self.integration.scale_cache)
        
        # Generate many scale calculations
        for i in range(2000):
            self.integration.calculate_optimal_scale(0.1 + (i % 100) * 0.1, 0.5 + (i % 10) * 0.1)
        
        # Cache should be limited
        self.assertLessEqual(len(self.integration.scale_cache), self.integration.max_cache_size)
        
        # Performance should not degrade significantly
        import time
        start_time = time.time()
        for i in range(100):
            self.integration.calculate_optimal_scale(1.0, 1.0)
        end_time = time.time()
        
        # Should complete quickly (less than 1 second for 100 calculations)
        self.assertLess(end_time - start_time, 1.0)


class TestZoomLevel(unittest.TestCase):
    """Test cases for ZoomLevel dataclass."""
    
    def test_zoom_level_creation(self):
        """Test ZoomLevel creation and attributes."""
        zoom = ZoomLevel(1.0, "normal", 16, 32, 1.0, 3)
        
        self.assertEqual(zoom.level, 1.0)
        self.assertEqual(zoom.name, "normal")
        self.assertEqual(zoom.min_symbol_size, 16)
        self.assertEqual(zoom.max_symbol_size, 32)
        self.assertEqual(zoom.scale_factor, 1.0)
        self.assertEqual(zoom.lod_level, 3)


class TestSymbolScaleData(unittest.TestCase):
    """Test cases for SymbolScaleData dataclass."""
    
    def test_symbol_scale_data_creation(self):
        """Test SymbolScaleData creation and attributes."""
        data = SymbolScaleData(
            symbol_id="test",
            base_width=40,
            base_height=20,
            current_scale=1.5,
            zoom_level=2.0,
            actual_width=60,
            actual_height=30,
            is_consistent=True
        )
        
        self.assertEqual(data.symbol_id, "test")
        self.assertEqual(data.base_width, 40)
        self.assertEqual(data.base_height, 20)
        self.assertEqual(data.current_scale, 1.5)
        self.assertEqual(data.zoom_level, 2.0)
        self.assertEqual(data.actual_width, 60)
        self.assertEqual(data.actual_height, 30)
        self.assertTrue(data.is_consistent)


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2) 