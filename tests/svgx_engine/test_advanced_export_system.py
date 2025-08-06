"""
SVGX Engine - Advanced Export System Tests

This module provides comprehensive tests for the Advanced Export System,
ensuring all export formats work correctly with proper validation and error handling.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from svgx_engine.services.export import (
    AdvancedExportSystem,
    ExportFormat,
    ExportQuality,
    ExportConfig,
    ExportResult,
    create_advanced_export_system,
    create_export_config,
)


class TestAdvancedExportSystem(unittest.TestCase):
    """Test cases for Advanced Export System."""

    def setUp(self):
        """Set up test fixtures."""
        self.export_system = create_advanced_export_system()
        self.test_data = {
            "elements": [
                {
                    "type": "wall",
                    "name": "Wall 1",
                    "x": 0.0,
                    "y": 0.0,
                    "z": 0.0,
                    "width": 0.2,
                    "height": 3.0,
                    "depth": 0.2,
                },
                {
                    "type": "window",
                    "name": "Window 1",
                    "x": 2.0,
                    "y": 0.0,
                    "z": 1.5,
                    "width": 1.2,
                    "height": 1.5,
                    "depth": 0.1,
                },
                {
                    "type": "door",
                    "name": "Door 1",
                    "x": 5.0,
                    "y": 0.0,
                    "z": 1.05,
                    "width": 0.9,
                    "height": 2.1,
                    "depth": 0.1,
                },
                {
                    "type": "column",
                    "name": "Column 1",
                    "x": 8.0,
                    "y": 0.0,
                    "z": 1.5,
                    "width": 0.3,
                    "height": 3.0,
                    "depth": 0.3,
                },
            ]
        }

    def test_create_advanced_export_system(self):
        """Test creating an advanced export system."""
        system = create_advanced_export_system()
        self.assertIsInstance(system, AdvancedExportSystem)
        self.assertIsNotNone(system.ifc_service)
        self.assertIsNotNone(system.gltf_service)
        self.assertIsNotNone(system.dxf_service)

    def test_create_export_config(self):
        """Test creating export configuration."""
        config = create_export_config(
            format=ExportFormat.IFC,
            quality=ExportQuality.HIGH,
            include_metadata=True,
            include_properties=True,
            include_materials=True,
            include_dimensions=True,
        )

        self.assertEqual(config.format, ExportFormat.IFC)
        self.assertEqual(config.quality, ExportQuality.HIGH)
        self.assertTrue(config.include_metadata)
        self.assertTrue(config.include_properties)
        self.assertTrue(config.include_materials)
        self.assertTrue(config.include_dimensions)

    def test_export_to_ifc(self):
        """Test IFC export functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.ifc"

            result = self.export_system.export_data(
                self.test_data, output_path, ExportFormat.IFC
            )

            self.assertTrue(result.success)
            self.assertIsNotNone(result.output_path)
            self.assertTrue(result.output_path.exists())
            self.assertGreater(result.file_size, 0)
            self.assertGreater(result.export_time, 0)
            self.assertEqual(result.metadata["format"], "ifc")

    def test_export_to_gltf(self):
        """Test GLTF export functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.gltf"

            result = self.export_system.export_data(
                self.test_data, output_path, ExportFormat.GLTF
            )

            self.assertTrue(result.success)
            self.assertIsNotNone(result.output_path)
            self.assertTrue(result.output_path.exists())
            self.assertGreater(result.file_size, 0)
            self.assertGreater(result.export_time, 0)
            self.assertEqual(result.metadata["format"], "gltf")

    def test_export_to_dxf(self):
        """Test DXF export functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.dxf"

            result = self.export_system.export_data(
                self.test_data, output_path, ExportFormat.DXF
            )

            self.assertTrue(result.success)
            self.assertIsNotNone(result.output_path)
            self.assertTrue(result.output_path.exists())
            self.assertGreater(result.file_size, 0)
            self.assertGreater(result.export_time, 0)
            self.assertEqual(result.metadata["format"], "dxf")

    def test_export_to_step(self):
        """Test STEP export functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.step"

            result = self.export_system.export_data(
                self.test_data, output_path, ExportFormat.STEP
            )

            self.assertTrue(result.success)
            self.assertIsNotNone(result.output_path)
            self.assertTrue(result.output_path.exists())
            self.assertGreater(result.file_size, 0)
            self.assertGreater(result.export_time, 0)
            self.assertEqual(result.metadata["format"], "step")

    def test_export_to_iges(self):
        """Test IGES export functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.iges"

            result = self.export_system.export_data(
                self.test_data, output_path, ExportFormat.IGES
            )

            self.assertTrue(result.success)
            self.assertIsNotNone(result.output_path)
            self.assertTrue(result.output_path.exists())
            self.assertGreater(result.file_size, 0)
            self.assertGreater(result.export_time, 0)
            self.assertEqual(result.metadata["format"], "iges")

    def test_export_to_parasolid(self):
        """Test Parasolid export functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.x_t"

            result = self.export_system.export_data(
                self.test_data, output_path, ExportFormat.PARASOLID
            )

            self.assertTrue(result.success)
            self.assertIsNotNone(result.output_path)
            self.assertTrue(result.output_path.exists())
            self.assertGreater(result.file_size, 0)
            self.assertGreater(result.export_time, 0)
            self.assertEqual(result.metadata["format"], "parasolid")

    def test_export_with_custom_config(self):
        """Test export with custom configuration."""
        config = create_export_config(
            format=ExportFormat.IFC,
            quality=ExportQuality.ULTRA,
            include_metadata=False,
            include_properties=True,
            include_materials=True,
            include_dimensions=False,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_custom.ifc"

            result = self.export_system.export_data(
                self.test_data, output_path, ExportFormat.IFC, config
            )

            self.assertTrue(result.success)
            self.assertEqual(result.metadata["quality"], "ultra")
            self.assertFalse(result.metadata["export_config"]["include_metadata"])
            self.assertTrue(result.metadata["export_config"]["include_properties"])
            self.assertTrue(result.metadata["export_config"]["include_materials"])
            self.assertFalse(result.metadata["export_config"]["include_dimensions"])

    def test_export_invalid_format(self):
        """Test export with invalid format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.invalid"

            result = self.export_system.export_data(
                self.test_data, output_path, "invalid_format"  # type: ignore
            )

            self.assertFalse(result.success)
            self.assertIsNotNone(result.error_message)
            self.assertIn("Unsupported export format", result.error_message)

    def test_export_empty_data(self):
        """Test export with empty data."""
        empty_data = {"elements": []}

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_empty.ifc"

            result = self.export_system.export_data(
                empty_data, output_path, ExportFormat.IFC
            )

            self.assertTrue(result.success)
            self.assertEqual(result.metadata["elements_count"], 0)

    def test_export_malformed_data(self):
        """Test export with malformed data."""
        malformed_data = {"invalid_key": "invalid_value"}

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_malformed.ifc"

            result = self.export_system.export_data(
                malformed_data, output_path, ExportFormat.IFC
            )

            # Should still succeed but with warnings
            self.assertTrue(result.success)
            self.assertEqual(result.metadata["elements_count"], 0)

    def test_validate_export_data(self):
        """Test data validation functionality."""
        # Test valid data
        validation_result = self.export_system.validate_export_data(self.test_data)
        self.assertTrue(validation_result["valid"])
        self.assertEqual(validation_result["element_count"], 4)
        self.assertGreater(len(validation_result["supported_formats"]), 0)

        # Test invalid data
        invalid_data = {"invalid_key": "invalid_value"}
        validation_result = self.export_system.validate_export_data(invalid_data)
        self.assertFalse(validation_result["valid"])
        self.assertIn("Missing 'elements' key", validation_result["errors"])

        # Test data with missing element fields
        incomplete_data = {
            "elements": [
                {"type": "wall"},  # Missing name
                {"name": "Window"},  # Missing type
                {"type": "door", "name": "Door 1"},  # Valid
            ]
        }
        validation_result = self.export_system.validate_export_data(incomplete_data)
        self.assertTrue(validation_result["valid"])
        self.assertEqual(len(validation_result["warnings"]), 2)

    def test_get_export_statistics(self):
        """Test export statistics functionality."""
        # Perform some exports first
        with tempfile.TemporaryDirectory() as temp_dir:
            for format in [ExportFormat.IFC, ExportFormat.GLTF, ExportFormat.DXF]:
                output_path = Path(temp_dir) / f"test_{format.value}.{format.value}"
                self.export_system.export_data(self.test_data, output_path, format)

        stats = self.export_system.get_export_statistics()

        self.assertGreater(stats["total_exports"], 0)
        self.assertGreater(stats["successful_exports"], 0)
        self.assertEqual(stats["failed_exports"], 0)
        self.assertEqual(stats["success_rate"], 1.0)
        self.assertIn("ifc", stats["format_statistics"])
        self.assertIn("gltf", stats["format_statistics"])
        self.assertIn("dxf", stats["format_statistics"])
        self.assertGreater(stats["average_export_time"], 0)

    def test_export_history(self):
        """Test export history tracking."""
        initial_history_length = len(self.export_system.export_history)

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_history.ifc"
            self.export_system.export_data(
                self.test_data, output_path, ExportFormat.IFC
            )

        self.assertEqual(
            len(self.export_system.export_history), initial_history_length + 1
        )

        last_result = self.export_system.export_history[-1]
        self.assertTrue(last_result.success)
        self.assertIsNotNone(last_result.output_path)
        self.assertGreater(last_result.file_size, 0)

    def test_export_error_handling(self):
        """Test export error handling."""
        # Test with invalid output path
        invalid_path = "/invalid/path/test.ifc"

        result = self.export_system.export_data(
            self.test_data, invalid_path, ExportFormat.IFC
        )

        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_message)

    def test_export_quality_levels(self):
        """Test different export quality levels."""
        quality_levels = [
            ExportQuality.DRAFT,
            ExportQuality.STANDARD,
            ExportQuality.HIGH,
            ExportQuality.ULTRA,
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            for quality in quality_levels:
                config = create_export_config(ExportFormat.IFC, quality)
                output_path = Path(temp_dir) / f"test_{quality.value}.ifc"

                result = self.export_system.export_data(
                    self.test_data, output_path, ExportFormat.IFC, config
                )

                self.assertTrue(result.success)
                self.assertEqual(result.metadata["quality"], quality.value)


if __name__ == "__main__":
    unittest.main()
