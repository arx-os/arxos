"""
SVGX Engine - Comprehensive Export System Tests

This module provides comprehensive tests for the complete Advanced Export System,
ensuring all export formats (IFC, GLTF, DXF, STEP, IGES) work correctly with proper validation.

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
    create_advanced_export_system,
    create_export_config,
    IFCExportService,
    GLTFExportService,
    DXFExportService,
    STEPExportService,
    IGESExportService,
)


class TestComprehensiveExportSystem(unittest.TestCase):
    """Comprehensive test cases for the Advanced Export System."""

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

    def test_all_export_formats(self):
        """Test all supported export formats."""
        formats = [
            ExportFormat.IFC,
            ExportFormat.GLTF,
            ExportFormat.DXF,
            ExportFormat.STEP,
            ExportFormat.IGES,
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            for format in formats:
                output_path = Path(temp_dir) / f"test.{format.value}"

                result = self.export_system.export_data(
                    self.test_data, output_path, format
                )

                self.assertTrue(
                    result.success,
                    f"Export to {format.value} failed: {result.error_message}",
                )
                self.assertIsNotNone(result.output_path)
                self.assertTrue(result.output_path.exists())
                self.assertGreater(result.file_size, 0)
                self.assertGreater(result.export_time, 0)
                self.assertEqual(result.metadata["format"], format.value)

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

    def test_export_configurations(self):
        """Test different export configurations."""
        configs = [
            create_export_config(
                ExportFormat.IFC, ExportQuality.STANDARD, True, True, True, True
            ),
            create_export_config(
                ExportFormat.IFC, ExportQuality.STANDARD, False, True, True, True
            ),
            create_export_config(
                ExportFormat.IFC, ExportQuality.STANDARD, True, False, True, True
            ),
            create_export_config(
                ExportFormat.IFC, ExportQuality.STANDARD, True, True, False, True
            ),
            create_export_config(
                ExportFormat.IFC, ExportQuality.STANDARD, True, True, True, False
            ),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            for i, config in enumerate(configs):
                output_path = Path(temp_dir) / f"test_config_{i}.ifc"

                result = self.export_system.export_data(
                    self.test_data, output_path, ExportFormat.IFC, config
                )

                self.assertTrue(result.success)
                self.assertEqual(
                    result.metadata["export_config"]["include_metadata"],
                    config.include_metadata,
                )
                self.assertEqual(
                    result.metadata["export_config"]["include_properties"],
                    config.include_properties,
                )
                self.assertEqual(
                    result.metadata["export_config"]["include_materials"],
                    config.include_materials,
                )
                self.assertEqual(
                    result.metadata["export_config"]["include_dimensions"],
                    config.include_dimensions,
                )

    def test_export_validation(self):
        """Test export data validation."""
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

    def test_export_statistics(self):
        """Test export statistics functionality."""
        # Perform exports to generate statistics
        with tempfile.TemporaryDirectory() as temp_dir:
            formats = [
                ExportFormat.IFC,
                ExportFormat.GLTF,
                ExportFormat.DXF,
                ExportFormat.STEP,
                ExportFormat.IGES,
            ]

            for format in formats:
                output_path = Path(temp_dir) / f"test_stats.{format.value}"
                self.export_system.export_data(self.test_data, output_path, format)

        stats = self.export_system.get_export_statistics()

        self.assertGreater(stats["total_exports"], 0)
        self.assertGreater(stats["successful_exports"], 0)
        self.assertEqual(stats["failed_exports"], 0)
        self.assertEqual(stats["success_rate"], 1.0)

        # Check that all formats are represented in statistics
        expected_formats = ["ifc", "gltf", "dxf", "step", "iges"]
        for format_name in expected_formats:
            self.assertIn(format_name, stats["format_statistics"])
            self.assertGreater(stats["format_statistics"][format_name], 0)

        self.assertGreater(stats["average_export_time"], 0)

    def test_export_error_handling(self):
        """Test export error handling."""
        # Test with invalid format
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.invalid"

            result = self.export_system.export_data(
                self.test_data, output_path, "invalid_format"  # type: ignore
            )

            self.assertFalse(result.success)
            self.assertIsNotNone(result.error_message)
            self.assertIn("Unsupported export format", result.error_message)

        # Test with invalid output path
        invalid_path = "/invalid/path/test.ifc"

        result = self.export_system.export_data(
            self.test_data, invalid_path, ExportFormat.IFC
        )

        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_message)

    def test_export_history_tracking(self):
        """Test export history tracking."""
        initial_history_length = len(self.export_system.export_history)

        with tempfile.TemporaryDirectory() as temp_dir:
            # Perform multiple exports
            for i in range(3):
                output_path = Path(temp_dir) / f"test_history_{i}.ifc"
                self.export_system.export_data(
                    self.test_data, output_path, ExportFormat.IFC
                )

        self.assertEqual(
            len(self.export_system.export_history), initial_history_length + 3
        )

        # Check that all results are tracked
        for result in self.export_system.export_history[-3:]:
            self.assertTrue(result.success)
            self.assertIsNotNone(result.output_path)
            self.assertGreater(result.file_size, 0)
            self.assertGreater(result.export_time, 0)

    def test_individual_export_services(self):
        """Test individual export services."""
        # Test IFC service
        ifc_service = IFCExportService()
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_ifc.ifc"
            result_path = ifc_service.export_to_ifc(self.test_data, output_path)
            self.assertTrue(result_path.exists())

        # Test GLTF service
        gltf_service = GLTFExportService()
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_gltf.gltf"
            result_path = gltf_service.export_to_gltf(self.test_data, output_path)
            self.assertTrue(result_path.exists())

        # Test DXF service
        dxf_service = DXFExportService()
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_dxf.dxf"
            result_path = dxf_service.export_to_dxf(self.test_data, output_path)
            self.assertTrue(result_path.exists())

        # Test STEP service
        step_service = STEPExportService()
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_step.step"
            result_path = step_service.export_to_step(self.test_data, output_path)
            self.assertTrue(result_path.exists())

        # Test IGES service
        iges_service = IGESExportService()
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_iges.iges"
            result_path = iges_service.export_to_iges(self.test_data, output_path)
            self.assertTrue(result_path.exists())

    def test_export_with_empty_data(self):
        """Test export with empty data."""
        empty_data = {"elements": []}

        with tempfile.TemporaryDirectory() as temp_dir:
            for format in [
                ExportFormat.IFC,
                ExportFormat.GLTF,
                ExportFormat.DXF,
                ExportFormat.STEP,
                ExportFormat.IGES,
            ]:
                output_path = Path(temp_dir) / f"test_empty.{format.value}"

                result = self.export_system.export_data(empty_data, output_path, format)

                self.assertTrue(result.success)
                self.assertEqual(result.metadata["elements_count"], 0)

    def test_export_with_malformed_data(self):
        """Test export with malformed data."""
        malformed_data = {"invalid_key": "invalid_value"}

        with tempfile.TemporaryDirectory() as temp_dir:
            for format in [
                ExportFormat.IFC,
                ExportFormat.GLTF,
                ExportFormat.DXF,
                ExportFormat.STEP,
                ExportFormat.IGES,
            ]:
                output_path = Path(temp_dir) / f"test_malformed.{format.value}"

                result = self.export_system.export_data(
                    malformed_data, output_path, format
                )

                # Should still succeed but with warnings
                self.assertTrue(result.success)
                self.assertEqual(result.metadata["elements_count"], 0)

    def test_export_file_formats(self):
        """Test that exported files have correct formats."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test IFC format
            output_path = Path(temp_dir) / "test.ifc"
            result = self.export_system.export_data(
                self.test_data, output_path, ExportFormat.IFC
            )
            self.assertTrue(result.success)

            with open(output_path, "r") as f:
                content = f.read()
                self.assertIn("ISO-10303-21", content)
                self.assertIn("HEADER", content)
                self.assertIn("DATA", content)

            # Test GLTF format
            output_path = Path(temp_dir) / "test.gltf"
            result = self.export_system.export_data(
                self.test_data, output_path, ExportFormat.GLTF
            )
            self.assertTrue(result.success)

            with open(output_path, "r") as f:
                content = f.read()
                gltf_data = json.loads(content)
                self.assertIn("asset", gltf_data)
                self.assertIn("version", gltf_data["asset"])
                self.assertIn("scene", gltf_data)

            # Test DXF format
            output_path = Path(temp_dir) / "test.dxf"
            result = self.export_system.export_data(
                self.test_data, output_path, ExportFormat.DXF
            )
            self.assertTrue(result.success)

            with open(output_path, "r") as f:
                content = f.read()
                self.assertIn("SECTION", content)
                self.assertIn("HEADER", content)
                self.assertIn("ENTITIES", content)

    def test_export_performance(self):
        """Test export performance with larger datasets."""
        # Create larger test dataset
        large_data = {"elements": []}

        # Add 100 elements
        for i in range(100):
            element = {
                "type": (
                    "wall"
                    if i % 4 == 0
                    else "window" if i % 4 == 1 else "door" if i % 4 == 2 else "column"
                ),
                "name": f"Element_{i}",
                "x": float(i),
                "y": float(i * 2),
                "z": 0.0,
                "width": 0.2 + (i % 3) * 0.1,
                "height": 3.0 + (i % 2) * 0.5,
                "depth": 0.2,
            }
            large_data["elements"].append(element)

        with tempfile.TemporaryDirectory() as temp_dir:
            for format in [ExportFormat.IFC, ExportFormat.GLTF, ExportFormat.DXF]:
                output_path = Path(temp_dir) / f"test_performance.{format.value}"

                result = self.export_system.export_data(large_data, output_path, format)

                self.assertTrue(result.success)
                self.assertGreater(result.file_size, 0)
                self.assertLess(
                    result.export_time, 10.0
                )  # Should complete within 10 seconds
                self.assertEqual(result.metadata["elements_count"], 100)


if __name__ == "__main__":
    unittest.main()
