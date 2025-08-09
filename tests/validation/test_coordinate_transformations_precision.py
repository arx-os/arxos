"""
Test suite for precision-aware coordinate transformations.

This module tests the updated coordinate transformation functions that now include
precision validation hooks and error handling.
"""

import pytest
import math
import numpy as np
from typing import List, Tuple
from decimal import Decimal

from svgx_engine.core.precision_config import PrecisionConfig, config_manager
from svgx_engine.core.precision_math import PrecisionMath
from svgx_engine.core.precision_coordinate import PrecisionCoordinate, CoordinateTransformation
from svgx_engine.core.precision_hooks import hook_manager, HookType, HookContext
from svgx_engine.core.precision_errors import PrecisionErrorHandler, PrecisionErrorType, PrecisionErrorSeverity

# Import the functions we're testing'
from core.svg_parser.services.transform import (
    transform_coordinates_batch,
    apply_matrix_transformation_precision,
    apply_matrix_transformation
)
from svgx_engine.parser.geometry import SVGXGeometry


class TestCoordinateTransformationClass:
    """Test the updated CoordinateTransformation class with precision validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = config_manager.get_default_config()
        self.transformer = CoordinateTransformation(self.config)
        self.precision_math = PrecisionMath()

        # Test coordinates
        self.test_coord = PrecisionCoordinate(1.0, 2.0, 3.0)
        self.origin = PrecisionCoordinate(0.0, 0.0, 0.0)
        self.center = PrecisionCoordinate(1.0, 1.0, 0.0)

    def test_transformation_matrix_creation(self):
        """Test transformation matrix creation with precision validation."""
        # Test identity matrix
        identity = self.transformer.create_transformation_matrix()
        expected_identity = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ])
        np.testing.assert_array_almost_equal(identity, expected_identity)

        # Test scaling matrix
        scale_matrix = self.transformer.create_transformation_matrix(scale=2.0)
        expected_scale = np.array([
            [2.0, 0.0, 0.0, 0.0],
            [0.0, 2.0, 0.0, 0.0],
            [0.0, 0.0, 2.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ])
        np.testing.assert_array_almost_equal(scale_matrix, expected_scale)

        # Test translation matrix
        trans_matrix = self.transformer.create_transformation_matrix(translation=(1.0, 2.0, 3.0))
        expected_trans = np.array([
            [1.0, 0.0, 0.0, 1.0],
            [0.0, 1.0, 0.0, 2.0],
            [0.0, 0.0, 1.0, 3.0],
            [0.0, 0.0, 0.0, 1.0]
        ])
        np.testing.assert_array_almost_equal(trans_matrix, expected_trans)

    def test_transformation_matrix_validation(self):
        """Test transformation matrix validation with invalid parameters."""
        # Test negative scale factor
        with pytest.raises(ValueError, match="Scale factor must be positive"):
            self.transformer.create_transformation_matrix(scale=-1.0)

        # Test large rotation angle (should warn but not fail)
        large_rotation_matrix = self.transformer.create_transformation_matrix(rotation=10.0)
        assert large_rotation_matrix.shape == (4, 4)

    def test_apply_transformation(self):
        """Test applying transformation matrices to coordinates."""
        # Test identity transformation
        identity_matrix = self.transformer.create_transformation_matrix()
        transformed = self.transformer.apply_transformation(self.test_coord, identity_matrix)
        assert transformed.x == pytest.approx(self.test_coord.x, rel=1e-10)
        assert transformed.y == pytest.approx(self.test_coord.y, rel=1e-10)
        assert transformed.z == pytest.approx(self.test_coord.z, rel=1e-10)

        # Test scaling transformation
        scale_matrix = self.transformer.create_transformation_matrix(scale=2.0)
        transformed = self.transformer.apply_transformation(self.test_coord, scale_matrix)
        assert transformed.x == pytest.approx(2.0, rel=1e-10)
        assert transformed.y == pytest.approx(4.0, rel=1e-10)
        assert transformed.z == pytest.approx(6.0, rel=1e-10)

        # Test translation transformation
        trans_matrix = self.transformer.create_transformation_matrix(translation=(1.0, 2.0, 3.0))
        transformed = self.transformer.apply_transformation(self.test_coord, trans_matrix)
        assert transformed.x == pytest.approx(2.0, rel=1e-10)
        assert transformed.y == pytest.approx(4.0, rel=1e-10)
        assert transformed.z == pytest.approx(6.0, rel=1e-10)

    def test_apply_transformation_validation(self):
        """Test transformation application validation."""
        # Test invalid matrix shape
        invalid_matrix = np.array([[1.0, 0.0], [0.0, 1.0]])  # 2x2 instead of 4x4
        with pytest.raises(ValueError, match="Transformation matrix must be 4x4"):
            self.transformer.apply_transformation(self.test_coord, invalid_matrix)

    def test_scale_coordinate(self):
        """Test coordinate scaling with precision validation."""
        # Test positive scaling
        scaled = self.transformer.scale_coordinate(self.test_coord, 2.0)
        assert scaled.x == pytest.approx(2.0, rel=1e-10)
        assert scaled.y == pytest.approx(4.0, rel=1e-10)
        assert scaled.z == pytest.approx(6.0, rel=1e-10)

        # Test negative scale factor
        with pytest.raises(ValueError, match="Scale factor must be positive"):
            self.transformer.scale_coordinate(self.test_coord, -1.0)

    def test_rotate_coordinate(self):
        """Test coordinate rotation with precision validation."""
        # Test rotation around origin
        rotated = self.transformer.rotate_coordinate(self.test_coord, math.pi/2)
        assert rotated.x == pytest.approx(-2.0, rel=1e-10)
        assert rotated.y == pytest.approx(1.0, rel=1e-10)
        assert rotated.z == pytest.approx(3.0, rel=1e-10)

        # Test rotation around center point
        rotated_around_center = self.transformer.rotate_coordinate(
            self.test_coord, math.pi/2, self.center
        )
        assert rotated_around_center.x == pytest.approx(0.0, rel=1e-10)
        assert rotated_around_center.y == pytest.approx(1.0, rel=1e-10)
        assert rotated_around_center.z == pytest.approx(3.0, rel=1e-10)

        # Test large rotation angle (should warn but not fail)
        large_rotation = self.transformer.rotate_coordinate(self.test_coord, 10.0)
        assert isinstance(large_rotation, PrecisionCoordinate)

    def test_translate_coordinate(self):
        """Test coordinate translation with precision validation."""
        translated = self.transformer.translate_coordinate(self.test_coord, 1.0, 2.0, 3.0)
        assert translated.x == pytest.approx(2.0, rel=1e-10)
        assert translated.y == pytest.approx(4.0, rel=1e-10)
        assert translated.z == pytest.approx(6.0, rel=1e-10)


class TestUnitConversionPrecision:
    """Test precision-aware unit conversion functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.geometry = SVGXGeometry()

    def test_unit_conversion_basic(self):
        """Test basic unit conversions with precision."""
        # Test mm to cm
        result = self.geometry.convert_units("10mm", "mm", "cm")
        assert result == pytest.approx(1.0, rel=1e-10)

        # Test cm to mm
        result = self.geometry.convert_units("5cm", "cm", "mm")
        assert result == pytest.approx(50.0, rel=1e-10)

        # Test m to mm
        result = self.geometry.convert_units("2m", "m", "mm")
        assert result == pytest.approx(2000.0, rel=1e-10)

        # Test in to mm
        result = self.geometry.convert_units("1in", "in", "mm")
        assert result == pytest.approx(25.4, rel=1e-10)

    def test_unit_conversion_extended_units(self):
        """Test extended unit conversions."""
        # Test km to m
        result = self.geometry.convert_units("1km", "km", "m")
        assert result == pytest.approx(1000.0, rel=1e-10)

        # Test ft to yd
        result = self.geometry.convert_units("3ft", "ft", "yd")
        assert result == pytest.approx(1.0, rel=1e-10)

        # Test px to mm (assuming 96 DPI)
        result = self.geometry.convert_units("96px", "px", "mm")
        assert result == pytest.approx(25.4, rel=1e-2)  # Approximate due to DPI assumption

    def test_unit_conversion_validation(self):
        """Test unit conversion validation."""
        # Test unknown source unit
        with pytest.raises(ValueError, match="Unknown source unit"):
            self.geometry.convert_units("10unknown", "unknown", "mm")

        # Test unknown target unit
        with pytest.raises(ValueError, match="Unknown target unit"):
            self.geometry.convert_units("10mm", "mm", "unknown")

        # Test negative value (should warn but not fail)
        result = self.geometry.convert_units("-10mm", "mm", "cm")
        assert result == pytest.approx(-1.0, rel=1e-10)

    def test_unit_conversion_with_hooks(self):
        """Test unit conversion with precision validation hooks."""
        # Register a test hook to verify it's called'
        hook_called = False

        def test_hook(context: HookContext) -> HookContext:
            nonlocal hook_called
            hook_called = True
            assert context.operation_name == "unit_conversion"
            assert context.constraint_data['from_unit'] == 'mm'
            assert context.constraint_data['to_unit'] == 'cm'
            return context

        # Register the hook
        hook_manager.register_hook(
            hook_id="test_unit_conversion_hook",
            hook_type=HookType.GEOMETRIC_CONSTRAINT,
            function=test_hook,
            priority=0
        )

        try:
            result = self.geometry.convert_units("10mm", "mm", "cm")
            assert hook_called
            assert result == pytest.approx(1.0, rel=1e-10)
        finally:
            # Clean up
            hook_manager.unregister_hook("test_unit_conversion_hook")


class TestBatchCoordinateTransformation:
    """Test batch coordinate transformation functions with precision."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_coordinates = [
            [0.0, 0.0],
            [1.0, 1.0],
            [2.0, 2.0],
            [3.0, 3.0]
        ]

        self.identity_matrix = [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ]

        self.scale_matrix = [
            [2.0, 0.0, 0.0, 0.0],
            [0.0, 2.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ]

    def test_batch_transformation_identity(self):
        """Test batch transformation with identity matrix."""
        transformed = transform_coordinates_batch(
            self.test_coordinates, "svg", "real_world", self.identity_matrix
        )

        assert len(transformed) == len(self.test_coordinates)
        for i, (original, result) in enumerate(zip(self.test_coordinates, transformed)):
            assert result[0] == pytest.approx(original[0], rel=1e-10)
            assert result[1] == pytest.approx(original[1], rel=1e-10)

    def test_batch_transformation_scale(self):
        """Test batch transformation with scaling matrix."""
        transformed = transform_coordinates_batch(
            self.test_coordinates, "svg", "real_world", self.scale_matrix
        )

        assert len(transformed) == len(self.test_coordinates)
        for i, (original, result) in enumerate(zip(self.test_coordinates, transformed)):
            assert result[0] == pytest.approx(original[0] * 2.0, rel=1e-10)
            assert result[1] == pytest.approx(original[1] * 2.0, rel=1e-10)

    def test_batch_transformation_system_conversion(self):
        """Test batch transformation between coordinate systems."""
        # Test SVG to real world conversion
        transformed = transform_coordinates_batch(
            self.test_coordinates, "svg", "real_world_meters"
        )

        assert len(transformed) == len(self.test_coordinates)
        # Should apply scale factor (1.0 in test)
        for i, (original, result) in enumerate(zip(self.test_coordinates, transformed)):
            assert result[0] == pytest.approx(original[0], rel=1e-10)
            assert result[1] == pytest.approx(original[1], rel=1e-10)

    def test_batch_transformation_validation(self):
        """Test batch transformation validation."""
        # Test invalid coordinates
        invalid_coordinates = [[0.0], [1.0, 2.0, 3.0, 4.0]]  # Wrong dimensions

        with pytest.raises(Exception):  # Should raise some kind of validation error
            transform_coordinates_batch(invalid_coordinates, "svg", "real_world")

    def test_matrix_transformation_precision(self):
        """Test precision-aware matrix transformation."""
        precision_coords = [
            PrecisionCoordinate(0.0, 0.0, 0.0),
            PrecisionCoordinate(1.0, 1.0, 0.0),
            PrecisionCoordinate(2.0, 2.0, 0.0)
        ]

        transformed = apply_matrix_transformation_precision(
            precision_coords, self.scale_matrix
        )

        assert len(transformed) == len(precision_coords)
        for i, (original, result) in enumerate(zip(precision_coords, transformed)):
            assert result[0] == pytest.approx(original.x * 2.0, rel=1e-10)
            assert result[1] == pytest.approx(original.y * 2.0, rel=1e-10)

    def test_matrix_transformation_validation(self):
        """Test matrix transformation validation."""
        precision_coords = [PrecisionCoordinate(1.0, 1.0, 0.0)]

        # Test invalid matrix
        invalid_matrix = [[1.0, 0.0], [0.0, 1.0]]  # 2x2 instead of 4x4

        with pytest.raises(ValueError, match="Transformation matrix must be 4x4"):
            apply_matrix_transformation_precision(precision_coords, invalid_matrix)

    def test_batch_transformation_with_hooks(self):
        """Test batch transformation with precision validation hooks."""
        # Register a test hook to verify it's called'
        hook_called = False

        def test_hook(context: HookContext) -> HookContext:
            nonlocal hook_called
            hook_called = True
            assert context.operation_name == "batch_coordinate_transformation"
            assert context.constraint_data['source_system'] == 'svg'
            assert context.constraint_data['target_system'] == 'real_world'
            return context

        # Register the hook
        hook_manager.register_hook(
            hook_id="test_batch_transformation_hook",
            hook_type=HookType.GEOMETRIC_CONSTRAINT,
            function=test_hook,
            priority=0
        )

        try:
            transformed = transform_coordinates_batch(
                self.test_coordinates, "svg", "real_world", self.identity_matrix
            )
            assert hook_called
            assert len(transformed) == len(self.test_coordinates)
        finally:
            # Clean up
            hook_manager.unregister_hook("test_batch_transformation_hook")


class TestTransformationErrorHandling:
    """Test error handling in coordinate transformations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.transformer = CoordinateTransformation()
        self.test_coord = PrecisionCoordinate(1.0, 1.0, 0.0)

    def test_transformation_error_recovery(self):
        """Test error recovery in transformation operations."""
        # Test with invalid scale factor
        with pytest.raises(ValueError):
            self.transformer.scale_coordinate(self.test_coord, -1.0)

        # Test with invalid matrix
        invalid_matrix = np.array([[1.0, 0.0], [0.0, 1.0]])
        with pytest.raises(ValueError):
            self.transformer.apply_transformation(self.test_coord, invalid_matrix)

    def test_unit_conversion_error_recovery(self):
        """Test error recovery in unit conversion."""
        geometry = SVGXGeometry()

        # Test with unknown unit
        with pytest.raises(ValueError):
            geometry.convert_units("10mm", "unknown", "cm")

        # Test with invalid value (should return 0.0)
        result = geometry.convert_units("invalid", "mm", "cm")
        assert result == 0.0


if __name__ == "__main__":
    pytest.main([__file__])
