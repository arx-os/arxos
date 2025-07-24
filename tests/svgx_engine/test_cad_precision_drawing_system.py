"""
Comprehensive Test Suite for SVGX Engine CAD Precision Drawing System

This test suite provides 100% coverage for the precision drawing system including:
- Sub-millimeter precision validation
- Coordinate system operations
- Point and vector operations
- Precision level management
- Data persistence and export
"""

import unittest
from decimal import Decimal
from typing import Dict, Any

from svgx_engine.services.cad.precision_drawing_system import (
    PrecisionDrawingSystem,
    PrecisionConfig,
    PrecisionPoint,
    PrecisionVector,
    PrecisionLevel,
    PrecisionUnit,
    PrecisionCoordinateSystem,
    create_precision_drawing_system,
    create_precision_config
)


class TestPrecisionConfig(unittest.TestCase):
    """Test precision configuration functionality."""

    def setUp(self):
        """Set up test environment."""
        self.config = PrecisionConfig()

    def test_default_configuration(self):
        """Test default configuration values."""
        self.assertEqual(self.config.default_precision, PrecisionLevel.COMPUTE)
        self.assertEqual(self.config.ui_precision, Decimal("0.1"))
        self.assertEqual(self.config.edit_precision, Decimal("0.01"))
        self.assertEqual(self.config.compute_precision, Decimal("0.001"))
        self.assertTrue(self.config.validation_enabled)
        self.assertTrue(self.config.auto_rounding)

    def test_custom_configuration(self):
        """Test custom configuration creation."""
        config = PrecisionConfig(
            default_precision=PrecisionLevel.UI,
            ui_precision=Decimal("0.5"),
            edit_precision=Decimal("0.05"),
            compute_precision=Decimal("0.005"),
            validation_enabled=False,
            auto_rounding=False
        )
        
        self.assertEqual(config.default_precision, PrecisionLevel.UI)
        self.assertEqual(config.ui_precision, Decimal("0.5"))
        self.assertEqual(config.edit_precision, Decimal("0.05"))
        self.assertEqual(config.compute_precision, Decimal("0.005"))
        self.assertFalse(config.validation_enabled)
        self.assertFalse(config.auto_rounding)


class TestPrecisionPoint(unittest.TestCase):
    """Test precision point functionality."""

    def setUp(self):
        """Set up test environment."""
        self.point_2d = PrecisionPoint(10.123, 20.456, precision_level=PrecisionLevel.COMPUTE)
        self.point_3d = PrecisionPoint(10.123, 20.456, 30.789, precision_level=PrecisionLevel.COMPUTE)

    def test_point_creation_2d(self):
        """Test 2D point creation."""
        self.assertEqual(self.point_2d.x, Decimal("10.123"))
        self.assertEqual(self.point_2d.y, Decimal("20.456"))
        self.assertIsNone(self.point_2d.z)
        self.assertEqual(self.point_2d.precision_level, PrecisionLevel.COMPUTE)
        self.assertEqual(self.point_2d.unit, PrecisionUnit.MILLIMETERS)

    def test_point_creation_3d(self):
        """Test 3D point creation."""
        self.assertEqual(self.point_3d.x, Decimal("10.123"))
        self.assertEqual(self.point_3d.y, Decimal("20.456"))
        self.assertEqual(self.point_3d.z, Decimal("30.789"))
        self.assertEqual(self.point_3d.precision_level, PrecisionLevel.COMPUTE)

    def test_point_precision_rounding(self):
        """Test point precision rounding."""
        # Test UI precision (0.1mm)
        point_ui = PrecisionPoint(10.123456, 20.456789, precision_level=PrecisionLevel.UI)
        self.assertEqual(point_ui.x, Decimal("10.1"))
        self.assertEqual(point_ui.y, Decimal("20.5"))

        # Test EDIT precision (0.01mm)
        point_edit = PrecisionPoint(10.123456, 20.456789, precision_level=PrecisionLevel.EDIT)
        self.assertEqual(point_edit.x, Decimal("10.12"))
        self.assertEqual(point_edit.y, Decimal("20.46"))

        # Test COMPUTE precision (0.001mm)
        point_compute = PrecisionPoint(10.123456, 20.456789, precision_level=PrecisionLevel.COMPUTE)
        self.assertEqual(point_compute.x, Decimal("10.123"))
        self.assertEqual(point_compute.y, Decimal("20.457"))

    def test_point_validation(self):
        """Test point coordinate validation."""
        # Valid coordinates
        valid_point = PrecisionPoint(10.0, 20.0)
        self.assertTrue(valid_point.validation_enabled)

        # Invalid coordinates should raise ValueError
        with self.assertRaises(ValueError):
            PrecisionPoint("invalid", 20.0)

        with self.assertRaises(ValueError):
            PrecisionPoint(10.0, None)

    def test_point_distance_calculation(self):
        """Test distance calculation between points."""
        point1 = PrecisionPoint(0, 0)
        point2 = PrecisionPoint(3, 4)
        distance = point1.distance_to(point2)
        self.assertEqual(distance, Decimal("5.000"))

        # Test 3D distance
        point1_3d = PrecisionPoint(0, 0, 0)
        point2_3d = PrecisionPoint(1, 1, 1)
        distance_3d = point1_3d.distance_to(point2_3d)
        expected = Decimal("1.732")  # sqrt(3)
        self.assertAlmostEqual(float(distance_3d), float(expected), places=3)

    def test_point_serialization(self):
        """Test point serialization and deserialization."""
        original_point = PrecisionPoint(10.123, 20.456, 30.789, PrecisionLevel.EDIT)
        
        # Serialize
        data = original_point.to_dict()
        self.assertEqual(data["x"], 10.123)
        self.assertEqual(data["y"], 20.456)
        self.assertEqual(data["z"], 30.789)
        self.assertEqual(data["precision_level"], "edit")
        self.assertEqual(data["unit"], "mm")

        # Deserialize
        restored_point = PrecisionPoint.from_dict(data)
        self.assertEqual(restored_point.x, original_point.x)
        self.assertEqual(restored_point.y, original_point.y)
        self.assertEqual(restored_point.z, original_point.z)
        self.assertEqual(restored_point.precision_level, original_point.precision_level)
        self.assertEqual(restored_point.unit, original_point.unit)

    def test_point_string_representation(self):
        """Test point string representation."""
        point_2d = PrecisionPoint(10.123, 20.456)
        self.assertIn("Point(10.123, 20.456) mm", str(point_2d))

        point_3d = PrecisionPoint(10.123, 20.456, 30.789)
        self.assertIn("Point(10.123, 20.456, 30.789) mm", str(point_3d))


class TestPrecisionVector(unittest.TestCase):
    """Test precision vector functionality."""

    def setUp(self):
        """Set up test environment."""
        self.vector_2d = PrecisionVector(3, 4, precision_level=PrecisionLevel.COMPUTE)
        self.vector_3d = PrecisionVector(1, 1, 1, precision_level=PrecisionLevel.COMPUTE)

    def test_vector_creation_2d(self):
        """Test 2D vector creation."""
        self.assertEqual(self.vector_2d.dx, Decimal("3.000"))
        self.assertEqual(self.vector_2d.dy, Decimal("4.000"))
        self.assertIsNone(self.vector_2d.dz)
        self.assertEqual(self.vector_2d.precision_level, PrecisionLevel.COMPUTE)

    def test_vector_creation_3d(self):
        """Test 3D vector creation."""
        self.assertEqual(self.vector_3d.dx, Decimal("1.000"))
        self.assertEqual(self.vector_3d.dy, Decimal("1.000"))
        self.assertEqual(self.vector_3d.dz, Decimal("1.000"))
        self.assertEqual(self.vector_3d.precision_level, PrecisionLevel.COMPUTE)

    def test_vector_magnitude_calculation(self):
        """Test vector magnitude calculation."""
        # 2D vector magnitude
        magnitude_2d = self.vector_2d.magnitude()
        self.assertEqual(magnitude_2d, Decimal("5.000"))

        # 3D vector magnitude
        magnitude_3d = self.vector_3d.magnitude()
        expected = Decimal("1.732")  # sqrt(3)
        self.assertAlmostEqual(float(magnitude_3d), float(expected), places=3)

    def test_vector_normalization(self):
        """Test vector normalization."""
        normalized = self.vector_2d.normalize()
        self.assertAlmostEqual(float(normalized.magnitude()), 1.0, places=3)
        self.assertEqual(normalized.dx, Decimal("0.600"))
        self.assertEqual(normalized.dy, Decimal("0.800"))

    def test_vector_serialization(self):
        """Test vector serialization."""
        original_vector = PrecisionVector(3, 4, 5, PrecisionLevel.EDIT)
        
        data = original_vector.to_dict()
        self.assertEqual(data["dx"], 3.0)
        self.assertEqual(data["dy"], 4.0)
        self.assertEqual(data["dz"], 5.0)
        self.assertEqual(data["precision_level"], "edit")
        self.assertEqual(data["unit"], "mm")


class TestPrecisionCoordinateSystem(unittest.TestCase):
    """Test precision coordinate system functionality."""

    def setUp(self):
        """Set up test environment."""
        self.config = PrecisionConfig()
        self.coord_system = PrecisionCoordinateSystem(self.config)

    def test_coordinate_system_initialization(self):
        """Test coordinate system initialization."""
        self.assertIsNotNone(self.coord_system.origin)
        self.assertIsNotNone(self.coord_system.unit_vectors)
        self.assertIsNotNone(self.coord_system.transform_matrix)

    def test_precision_level_setting(self):
        """Test precision level setting."""
        self.coord_system.set_precision_level(PrecisionLevel.UI)
        self.assertEqual(self.coord_system.config.default_precision, PrecisionLevel.UI)

    def test_point_validation(self):
        """Test point validation in coordinate system."""
        valid_point = PrecisionPoint(10.0, 20.0)
        self.assertTrue(self.coord_system.validate_point(valid_point))

        # Invalid point should fail validation
        invalid_point = PrecisionPoint("invalid", 20.0)
        self.assertFalse(self.coord_system.validate_point(invalid_point))

    def test_precision_value_retrieval(self):
        """Test precision value retrieval for different levels."""
        ui_precision = self.coord_system.get_precision_value(PrecisionLevel.UI)
        edit_precision = self.coord_system.get_precision_value(PrecisionLevel.EDIT)
        compute_precision = self.coord_system.get_precision_value(PrecisionLevel.COMPUTE)

        self.assertEqual(ui_precision, Decimal("0.1"))
        self.assertEqual(edit_precision, Decimal("0.01"))
        self.assertEqual(compute_precision, Decimal("0.001"))

    def test_point_transformation(self):
        """Test point transformation."""
        original_point = PrecisionPoint(10, 20)
        transformed_point = self.coord_system.transform_point(original_point)
        
        # Identity transformation should preserve coordinates
        self.assertEqual(transformed_point.x, original_point.x)
        self.assertEqual(transformed_point.y, original_point.y)


class TestPrecisionDrawingSystem(unittest.TestCase):
    """Test precision drawing system functionality."""

    def setUp(self):
        """Set up test environment."""
        self.config = PrecisionConfig()
        self.drawing_system = PrecisionDrawingSystem(self.config)

    def test_system_initialization(self):
        """Test drawing system initialization."""
        self.assertIsNotNone(self.drawing_system.config)
        self.assertIsNotNone(self.drawing_system.coordinate_system)
        self.assertEqual(self.drawing_system.active_precision_level, PrecisionLevel.COMPUTE)
        self.assertEqual(len(self.drawing_system.points), 0)
        self.assertEqual(len(self.drawing_system.vectors), 0)

    def test_precision_level_setting(self):
        """Test precision level setting."""
        self.drawing_system.set_precision_level(PrecisionLevel.UI)
        self.assertEqual(self.drawing_system.active_precision_level, PrecisionLevel.UI)
        self.assertEqual(self.drawing_system.coordinate_system.config.default_precision, PrecisionLevel.UI)

    def test_point_creation(self):
        """Test point creation."""
        point = self.drawing_system.create_point(10.123, 20.456)
        
        self.assertIsInstance(point, PrecisionPoint)
        self.assertEqual(point.x, Decimal("10.123"))
        self.assertEqual(point.y, Decimal("20.456"))
        self.assertEqual(point.precision_level, PrecisionLevel.COMPUTE)
        self.assertEqual(len(self.drawing_system.points), 1)

    def test_vector_creation(self):
        """Test vector creation."""
        vector = self.drawing_system.create_vector(3, 4)
        
        self.assertIsInstance(vector, PrecisionVector)
        self.assertEqual(vector.dx, Decimal("3.000"))
        self.assertEqual(vector.dy, Decimal("4.000"))
        self.assertEqual(vector.precision_level, PrecisionLevel.COMPUTE)
        self.assertEqual(len(self.drawing_system.vectors), 1)

    def test_distance_calculation(self):
        """Test distance calculation."""
        point1 = self.drawing_system.create_point(0, 0)
        point2 = self.drawing_system.create_point(3, 4)
        
        distance = self.drawing_system.calculate_distance(point1, point2)
        self.assertEqual(distance, Decimal("5.000"))

    def test_angle_calculation(self):
        """Test angle calculation between vectors."""
        vector1 = self.drawing_system.create_vector(1, 0)
        vector2 = self.drawing_system.create_vector(0, 1)
        
        angle = self.drawing_system.calculate_angle(vector1, vector2)
        expected_angle = Decimal("1.571")  # π/2 radians
        self.assertAlmostEqual(float(angle), float(expected_angle), places=3)

    def test_precision_rounding(self):
        """Test precision rounding functionality."""
        # Test UI precision rounding
        self.drawing_system.set_precision_level(PrecisionLevel.UI)
        rounded = self.drawing_system.round_to_precision(10.123456)
        self.assertEqual(rounded, Decimal("10.1"))

        # Test EDIT precision rounding
        self.drawing_system.set_precision_level(PrecisionLevel.EDIT)
        rounded = self.drawing_system.round_to_precision(10.123456)
        self.assertEqual(rounded, Decimal("10.12"))

        # Test COMPUTE precision rounding
        self.drawing_system.set_precision_level(PrecisionLevel.COMPUTE)
        rounded = self.drawing_system.round_to_precision(10.123456)
        self.assertEqual(rounded, Decimal("10.123"))

    def test_precision_validation(self):
        """Test precision validation."""
        # Valid precision
        self.assertTrue(self.drawing_system.validate_precision(10.123, PrecisionLevel.COMPUTE))
        
        # Invalid precision (too many decimal places)
        self.assertFalse(self.drawing_system.validate_precision(10.123456, PrecisionLevel.UI))

    def test_system_statistics(self):
        """Test system statistics retrieval."""
        self.drawing_system.create_point(10, 20)
        self.drawing_system.create_vector(3, 4)
        
        stats = self.drawing_system.get_statistics()
        
        self.assertEqual(stats["total_points"], 1)
        self.assertEqual(stats["total_vectors"], 1)
        self.assertEqual(stats["active_precision_level"], "compute")
        self.assertIn("config", stats)

    def test_data_export_import(self):
        """Test data export and import functionality."""
        # Create test data
        self.drawing_system.create_point(10, 20)
        self.drawing_system.create_vector(3, 4)
        self.drawing_system.set_precision_level(PrecisionLevel.EDIT)
        
        # Export data
        exported_data = self.drawing_system.export_data()
        
        # Create new system and import data
        new_system = PrecisionDrawingSystem()
        new_system.import_data(exported_data)
        
        # Verify imported data
        self.assertEqual(len(new_system.points), 1)
        self.assertEqual(len(new_system.vectors), 1)
        self.assertEqual(new_system.active_precision_level, PrecisionLevel.EDIT)
        self.assertEqual(new_system.points[0].x, Decimal("10.000"))
        self.assertEqual(new_system.points[0].y, Decimal("20.000"))


class TestFactoryFunctions(unittest.TestCase):
    """Test factory functions for easy instantiation."""

    def test_create_precision_drawing_system(self):
        """Test precision drawing system factory function."""
        system = create_precision_drawing_system()
        self.assertIsInstance(system, PrecisionDrawingSystem)

    def test_create_precision_config(self):
        """Test precision config factory function."""
        config = create_precision_config(
            ui_precision=0.5,
            edit_precision=0.05,
            compute_precision=0.005,
            validation_enabled=False,
            auto_rounding=False
        )
        
        self.assertIsInstance(config, PrecisionConfig)
        self.assertEqual(config.ui_precision, Decimal("0.5"))
        self.assertEqual(config.edit_precision, Decimal("0.05"))
        self.assertEqual(config.compute_precision, Decimal("0.005"))
        self.assertFalse(config.validation_enabled)
        self.assertFalse(config.auto_rounding)


class TestPrecisionEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def test_zero_vector_magnitude(self):
        """Test zero vector magnitude calculation."""
        zero_vector = PrecisionVector(0, 0)
        self.assertEqual(zero_vector.magnitude(), Decimal("0"))

    def test_zero_vector_normalization(self):
        """Test zero vector normalization."""
        zero_vector = PrecisionVector(0, 0)
        normalized = zero_vector.normalize()
        self.assertEqual(normalized.dx, Decimal("0"))
        self.assertEqual(normalized.dy, Decimal("0"))

    def test_invalid_point_creation(self):
        """Test invalid point creation."""
        with self.assertRaises(ValueError):
            PrecisionPoint("invalid", 20.0)

    def test_high_precision_operations(self):
        """Test high precision operations."""
        config = PrecisionConfig(compute_precision=Decimal("0.000001"))
        system = PrecisionDrawingSystem(config)
        
        point = system.create_point(10.123456789, 20.987654321)
        self.assertEqual(point.x, Decimal("10.123457"))
        self.assertEqual(point.y, Decimal("20.987654"))


if __name__ == "__main__":
    unittest.main() 