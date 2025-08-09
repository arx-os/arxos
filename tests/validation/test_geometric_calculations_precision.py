"""
Test suite for precision-aware geometric calculations.

This module tests the updated geometric calculation functions that now include
precision validation hooks and error handling.
"""

import pytest
import math
from typing import List, Tuple
from decimal import Decimal

from svgx_engine.core.precision_config import PrecisionConfig, config_manager
from svgx_engine.core.precision_math import PrecisionMath
from svgx_engine.core.precision_coordinate import PrecisionCoordinate
from svgx_engine.core.precision_hooks import hook_manager, HookType, HookContext
from svgx_engine.core.precision_errors import PrecisionErrorHandler, PrecisionErrorType, PrecisionErrorSeverity

# Import the functions we're testing'
from core.svg_parser.utils.geometry_utils import (
    calculate_area,
    calculate_perimeter,
    calculate_distance,
    calculate_bounding_box,
    calculate_box_intersection
)


class TestPrecisionAreaCalculations:
    """Test precision-aware area calculations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = config_manager.get_default_config()
        self.precision_math = PrecisionMath()

        # Test coordinates for a simple rectangle
        self.rectangle_coords = [
            [0.0, 0.0],
            [5.0, 0.0],
            [5.0, 3.0],
            [0.0, 3.0]
        ]

        # Test coordinates for a triangle
        self.triangle_coords = [
            [0.0, 0.0],
            [4.0, 0.0],
            [2.0, 3.0]
        ]

    def test_polygon_area_calculation(self):
        """Test polygon area calculation with precision."""
        # Test rectangle area (should be 15.0)
        area = calculate_area(self.rectangle_coords, self.config)
        expected_area = 15.0
        assert abs(area - expected_area) < 1e-10

        # Test triangle area (should be 6.0)
        area = calculate_area(self.triangle_coords, self.config)
        expected_area = 6.0
        assert abs(area - expected_area) < 1e-10

    def test_area_calculation_with_hooks(self):
        """Test area calculation with precision validation hooks."""
        # Register a test hook to verify it's called'
        hook_called = False

        def test_hook(context: HookContext) -> HookContext:
            nonlocal hook_called
            hook_called = True
            assert context.operation_name == "area_calculation"
            assert len(context.coordinates) == 4
            assert context.constraint_data['geometry_type'] == 'polygon'
            return context

        # Register the hook
        hook_manager.register_hook(
            hook_id="test_area_hook",
            hook_type=HookType.GEOMETRIC_CONSTRAINT,
            function=test_hook,
            priority=0
        )

        try:
            area = calculate_area(self.rectangle_coords, self.config)
            assert hook_called
            assert area == 15.0
        finally:
            # Clean up
            hook_manager.unregister_hook("test_area_hook")

    def test_area_calculation_error_handling(self):
        """Test area calculation error handling."""
        # Test with invalid coordinates (less than 3 points)
        invalid_coords = [[0.0, 0.0], [1.0, 1.0]]
        area = calculate_area(invalid_coords, self.config)
        assert area == 0.0

    def test_area_validation_thresholds(self):
        """Test area validation with minimum thresholds."""
        # Create a very small polygon
        small_coords = [
            [0.0, 0.0],
            [0.001, 0.0],
            [0.001, 0.001],
            [0.0, 0.001]
        ]

        # This should trigger a warning due to small area
        area = calculate_area(small_coords, self.config)
        assert area > 0.0


class TestPrecisionPerimeterCalculations:
    """Test precision-aware perimeter calculations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = config_manager.get_default_config()
        self.precision_math = PrecisionMath()

        # Test coordinates for a rectangle
        self.rectangle_coords = [
            [0.0, 0.0],
            [5.0, 0.0],
            [5.0, 3.0],
            [0.0, 3.0]
        ]

    def test_polygon_perimeter_calculation(self):
        """Test polygon perimeter calculation with precision."""
        perimeter = calculate_perimeter(self.rectangle_coords, self.config)
        expected_perimeter = 16.0  # 2 * (5 + 3)
        assert abs(perimeter - expected_perimeter) < 1e-10

    def test_perimeter_calculation_with_hooks(self):
        """Test perimeter calculation with precision validation hooks."""
        # Register a test hook to verify it's called'
        hook_called = False

        def test_hook(context: HookContext) -> HookContext:
            nonlocal hook_called
            hook_called = True
            assert context.operation_name == "perimeter_calculation"
            assert len(context.coordinates) == 4
            assert context.constraint_data['geometry_type'] == 'polygon'
            return context

        # Register the hook
        hook_manager.register_hook(
            hook_id="test_perimeter_hook",
            hook_type=HookType.GEOMETRIC_CONSTRAINT,
            function=test_hook,
            priority=0
        )

        try:
            perimeter = calculate_perimeter(self.rectangle_coords, self.config)
            assert hook_called
            assert perimeter == 16.0
        finally:
            # Clean up
            hook_manager.unregister_hook("test_perimeter_hook")

    def test_perimeter_calculation_error_handling(self):
        """Test perimeter calculation error handling."""
        # Test with insufficient coordinates
        invalid_coords = [[0.0, 0.0]]
        perimeter = calculate_perimeter(invalid_coords, self.config)
        assert perimeter == 0.0


class TestPrecisionDistanceCalculations:
    """Test precision-aware distance calculations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = config_manager.get_default_config()
        self.precision_math = PrecisionMath()

    def test_distance_calculation(self):
        """Test distance calculation with precision."""
        coord1 = [0.0, 0.0]
        coord2 = [3.0, 4.0]

        distance = calculate_distance(coord1, coord2, self.config)
        expected_distance = 5.0  # sqrt(3^2 + 4^2)
        assert abs(distance - expected_distance) < 1e-10

    def test_distance_calculation_3d(self):
        """Test 3D distance calculation with precision."""
        coord1 = [0.0, 0.0, 0.0]
        coord2 = [1.0, 1.0, 1.0]

        distance = calculate_distance(coord1, coord2, self.config)
        expected_distance = math.sqrt(3)  # sqrt(1^2 + 1^2 + 1^2)
        assert abs(distance - expected_distance) < 1e-10

    def test_distance_calculation_with_hooks(self):
        """Test distance calculation with precision validation hooks."""
        # Register a test hook to verify it's called'
        hook_called = False

        def test_hook(context: HookContext) -> HookContext:
            nonlocal hook_called
            hook_called = True
            assert context.operation_name == "distance_calculation"
            assert len(context.coordinates) == 2
            assert context.constraint_data['calculation_type'] == 'distance'
            return context

        # Register the hook
        hook_manager.register_hook(
            hook_id="test_distance_hook",
            hook_type=HookType.GEOMETRIC_CONSTRAINT,
            function=test_hook,
            priority=0
        )

        try:
            coord1 = [0.0, 0.0]
            coord2 = [3.0, 4.0]
            distance = calculate_distance(coord1, coord2, self.config)
            assert hook_called
            assert distance == 5.0
        finally:
            # Clean up
            hook_manager.unregister_hook("test_distance_hook")

    def test_distance_calculation_error_handling(self):
        """Test distance calculation error handling."""
        # Test with invalid coordinates
        with pytest.raises(ValueError):
            calculate_distance([0.0], [1.0, 1.0], self.config)

        with pytest.raises(ValueError):
            calculate_distance([0.0, 0.0], [1.0], self.config)


class TestPrecisionBoundingBoxCalculations:
    """Test precision-aware bounding box calculations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = config_manager.get_default_config()
        self.precision_math = PrecisionMath()

        # Test coordinates
        self.test_coords = [
            [1.0, 2.0],
            [5.0, 3.0],
            [3.0, 6.0],
            [0.0, 1.0]
        ]

    def test_bounding_box_calculation(self):
        """Test bounding box calculation with precision."""
        bbox = calculate_bounding_box(self.test_coords, self.config)
        expected_bbox = (0.0, 1.0, 5.0, 6.0)

        assert len(bbox) == 4
        for i in range(4):
            assert abs(bbox[i] - expected_bbox[i]) < 1e-10

    def test_bounding_box_calculation_with_hooks(self):
        """Test bounding box calculation with precision validation hooks."""
        # Register a test hook to verify it's called'
        hook_called = False

        def test_hook(context: HookContext) -> HookContext:
            nonlocal hook_called
            hook_called = True
            assert context.operation_name == "bounding_box_calculation"
            assert len(context.coordinates) == 4
            assert context.constraint_data['calculation_type'] == 'bounding_box'
            return context

        # Register the hook
        hook_manager.register_hook(
            hook_id="test_bbox_hook",
            hook_type=HookType.GEOMETRIC_CONSTRAINT,
            function=test_hook,
            priority=0
        )

        try:
            bbox = calculate_bounding_box(self.test_coords, self.config)
            assert hook_called
            assert bbox == (0.0, 1.0, 5.0, 6.0)
        finally:
            # Clean up
            hook_manager.unregister_hook("test_bbox_hook")

    def test_bounding_box_calculation_empty_input(self):
        """Test bounding box calculation with empty input."""
        bbox = calculate_bounding_box([], self.config)
        assert bbox == (0, 0, 0, 0)


class TestPrecisionBoxIntersectionCalculations:
    """Test precision-aware box intersection calculations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = config_manager.get_default_config()
        self.precision_math = PrecisionMath()

    def test_box_intersection_overlapping(self):
        """Test box intersection with overlapping boxes."""
        bbox1 = (0.0, 0.0, 5.0, 5.0)
        bbox2 = (2.0, 2.0, 7.0, 7.0)

        intersects, intersection_bbox = calculate_box_intersection(bbox1, bbox2, self.config)

        assert intersects
        assert intersection_bbox == (2.0, 2.0, 5.0, 5.0)

    def test_box_intersection_non_overlapping(self):
        """Test box intersection with non-overlapping boxes."""
        bbox1 = (0.0, 0.0, 3.0, 3.0)
        bbox2 = (5.0, 5.0, 8.0, 8.0)

        intersects, intersection_bbox = calculate_box_intersection(bbox1, bbox2, self.config)

        assert not intersects
        assert intersection_bbox is None

    def test_box_intersection_touching(self):
        """Test box intersection with touching boxes."""
        bbox1 = (0.0, 0.0, 3.0, 3.0)
        bbox2 = (3.0, 0.0, 6.0, 3.0)

        intersects, intersection_bbox = calculate_box_intersection(bbox1, bbox2, self.config)

        assert intersects
        assert intersection_bbox == (3.0, 0.0, 3.0, 3.0)

    def test_box_intersection_with_hooks(self):
        """Test box intersection with precision validation hooks."""
        # Register a test hook to verify it's called'
        hook_called = False

        def test_hook(context: HookContext) -> HookContext:
            nonlocal hook_called
            hook_called = True
            assert context.operation_name == "box_intersection_calculation"
            assert len(context.coordinates) == 4
            assert context.constraint_data['calculation_type'] == 'box_intersection'
            return context

        # Register the hook
        hook_manager.register_hook(
            hook_id="test_intersection_hook",
            hook_type=HookType.GEOMETRIC_CONSTRAINT,
            function=test_hook,
            priority=0
        )

        try:
            bbox1 = (0.0, 0.0, 5.0, 5.0)
            bbox2 = (2.0, 2.0, 7.0, 7.0)
            intersects, intersection_bbox = calculate_box_intersection(bbox1, bbox2, self.config)
            assert hook_called
            assert intersects
            assert intersection_bbox == (2.0, 2.0, 5.0, 5.0)
        finally:
            # Clean up
            hook_manager.unregister_hook("test_intersection_hook")


class TestGeometricCalculationsIntegration:
    """Integration tests for geometric calculations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = config_manager.get_default_config()
        self.error_handler = PrecisionErrorHandler()

    def test_comprehensive_geometric_workflow(self):
        """Test a comprehensive geometric calculation workflow."""
        # Create a complex polygon
        polygon_coords = [
            [0.0, 0.0],
            [4.0, 0.0],
            [4.0, 3.0],
            [2.0, 5.0],
            [0.0, 3.0]
        ]

        # Calculate area
        area = calculate_area(polygon_coords, self.config)
        assert area > 0.0

        # Calculate perimeter
        perimeter = calculate_perimeter(polygon_coords, self.config)
        assert perimeter > 0.0

        # Calculate bounding box
        bbox = calculate_bounding_box(polygon_coords, self.config)
        assert len(bbox) == 4
        assert bbox[0] <= bbox[2]  # min_x <= max_x
        assert bbox[1] <= bbox[3]  # min_y <= max_y

        # Calculate distances between points
        for i in range(len(polygon_coords) - 1):
            distance = calculate_distance(polygon_coords[i], polygon_coords[i + 1], self.config)
            assert distance > 0.0

    def test_error_recovery_in_geometric_calculations(self):
        """Test error recovery in geometric calculations."""
        # Test with problematic coordinates that might cause precision issues
        problematic_coords = [
            [0.0, 0.0],
            [0.000001, 0.0],
            [0.000001, 0.000001],
            [0.0, 0.000001]
        ]

        # These should still work but might trigger warnings
        area = calculate_area(problematic_coords, self.config)
        assert area >= 0.0

        perimeter = calculate_perimeter(problematic_coords, self.config)
        assert perimeter >= 0.0

    def test_precision_validation_integration(self):
        """Test that precision validation is properly integrated."""
        # Create coordinates that might trigger precision validation
        small_coords = [
            [0.0, 0.0],
            [0.0001, 0.0],
            [0.0001, 0.0001],
            [0.0, 0.0001]
        ]

        # These calculations should work but may trigger validation warnings
        area = calculate_area(small_coords, self.config)
        perimeter = calculate_perimeter(small_coords, self.config)
        bbox = calculate_bounding_box(small_coords, self.config)

        # All results should be valid
        assert area >= 0.0
        assert perimeter >= 0.0
        assert len(bbox) == 4


if __name__ == "__main__":
    pytest.main([__file__])
