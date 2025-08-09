"""
Comprehensive Test Suite for CAD Components

This module tests all CAD components including:
- Precision Drawing System
- Constraint System
- Grid and Snap System
- Dimensioning System

Tests cover functionality, accuracy, and integration between components.
"""

import unittest
import decimal
import math
from typing import List, Dict, Any

# Import CAD components
from svgx_engine.services.cad.precision_drawing import (
    PrecisionDrawingSystem, PrecisionPoint, PrecisionVector, PrecisionLevel,
    create_precision_drawing_system, create_point, create_vector
)

from svgx_engine.services.cad.constraint_system import (
    ConstraintSystem, DistanceConstraint, AngleConstraint, ParallelConstraint,
    PerpendicularConstraint, CoincidentConstraint, TangentConstraint, SymmetricConstraint,
    create_constraint_system, create_constraint_solver
)

from svgx_engine.services.cad.grid_snap_system import (
    GridSnapSystem, GridSettings, SnapSettings, SnapType,
    create_grid_snap_system, create_grid_settings, create_snap_settings
)

from svgx_engine.services.cad.dimensioning_system import (
    DimensioningSystem, LinearDimension, RadialDimension, AngularDimension,
    AlignedDimension, OrdinateDimension, DimensionStyle, DimensionType,
    create_dimensioning_system, create_dimension_style
)


class TestPrecisionDrawingSystem(unittest.TestCase):
    """Test precision drawing system functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.precision_system = create_precision_drawing_system(PrecisionLevel.MICRO)

    def test_precision_point_creation(self):
        """Test precision point creation and validation."""
        point = create_point(10.5, 20.75, PrecisionLevel.MICRO)

        self.assertEqual(point.x, decimal.Decimal('10.500')
        self.assertEqual(point.y, decimal.Decimal('20.750')
        self.assertEqual(point.precision, PrecisionLevel.MICRO)

    def test_precision_vector_creation(self):
        """Test precision vector creation and operations."""
        vector = create_vector(3.0, 4.0, PrecisionLevel.MICRO)

        self.assertEqual(vector.dx, decimal.Decimal('3.000')
        self.assertEqual(vector.dy, decimal.Decimal('4.000')
        self.assertEqual(vector.magnitude(), decimal.Decimal('5.000')
    def test_distance_calculation(self):
        """Test distance calculation with high precision."""
        point1 = create_point(0, 0, PrecisionLevel.MICRO)
        point2 = create_point(3, 4, PrecisionLevel.MICRO)

        distance = self.precision_system.calculate_distance(point1, point2)
        self.assertEqual(distance, decimal.Decimal('5.000')
    def test_angle_calculation(self):
        """Test angle calculation with high precision."""
        point1 = create_point(0, 0, PrecisionLevel.MICRO)
        point2 = create_point(1, 0, PrecisionLevel.MICRO)
        point3 = create_point(0, 1, PrecisionLevel.MICRO)

        angle = self.precision_system.calculate_angle(point1, point2, point3)
        expected_angle = decimal.Decimal(str(math.pi / 2)
        self.assertAlmostEqual(float(angle), float(expected_angle), places=3)

    def test_grid_snapping(self):
        """Test grid snapping functionality."""
        point = create_point(10.7, 20.3, PrecisionLevel.MICRO)
        grid_spacing = decimal.Decimal('5.0')

        snapped_point = self.precision_system.snap_to_grid(point, grid_spacing)

        # Should snap to nearest grid intersection
        self.assertEqual(snapped_point.x, decimal.Decimal('10.000')
        self.assertEqual(snapped_point.y, decimal.Decimal('20.000')
    def test_point_transformation(self):
        """Test point transformation with translation, rotation, and scale."""
        point = create_point(10, 20, PrecisionLevel.MICRO)
        translation = create_vector(5, 10, PrecisionLevel.MICRO)
        rotation = decimal.Decimal(str(math.pi / 2))  # 90 degrees
        scale = decimal.Decimal('2.0')

        transformed = self.precision_system.transform_point(
            point, translation, rotation, scale
        )

        # Verify transformation (simplified check)
        self.assertIsInstance(transformed, PrecisionPoint)
        self.assertEqual(transformed.precision, PrecisionLevel.MICRO)


class TestConstraintSystem(unittest.TestCase):
    """Test constraint system functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.constraint_system = create_constraint_system()

        # Create test entities
        self.point1 = create_point(0, 0, PrecisionLevel.MICRO)
        self.point2 = create_point(10, 0, PrecisionLevel.MICRO)
        self.point3 = create_point(0, 10, PrecisionLevel.MICRO)
        self.point4 = create_point(10, 10, PrecisionLevel.MICRO)

    def test_distance_constraint(self):
        """Test distance constraint creation and validation."""
        constraint = self.constraint_system.add_distance_constraint(
            self.point1, self.point2, 10.0
        )

        self.assertIsInstance(constraint, DistanceConstraint)
        self.assertTrue(constraint.validate()
    def test_angle_constraint(self):
        """Test angle constraint creation and validation."""
        # Create vectors for angle constraint
        vector1 = create_vector(1, 0, PrecisionLevel.MICRO)
        vector2 = create_vector(0, 1, PrecisionLevel.MICRO)

        constraint = self.constraint_system.add_angle_constraint(
            vector1, vector2, math.pi / 2
        )

        self.assertIsInstance(constraint, AngleConstraint)
        self.assertTrue(constraint.validate()
    def test_parallel_constraint(self):
        """Test parallel constraint creation and validation."""
        vector1 = create_vector(1, 0, PrecisionLevel.MICRO)
        vector2 = create_vector(2, 0, PrecisionLevel.MICRO)

        constraint = self.constraint_system.add_parallel_constraint(vector1, vector2)

        self.assertIsInstance(constraint, ParallelConstraint)
        self.assertTrue(constraint.validate()
    def test_perpendicular_constraint(self):
        """Test perpendicular constraint creation and validation."""
        vector1 = create_vector(1, 0, PrecisionLevel.MICRO)
        vector2 = create_vector(0, 1, PrecisionLevel.MICRO)

        constraint = self.constraint_system.add_perpendicular_constraint(vector1, vector2)

        self.assertIsInstance(constraint, PerpendicularConstraint)
        self.assertTrue(constraint.validate()
    def test_coincident_constraint(self):
        """Test coincident constraint creation and validation."""
        point1 = create_point(10, 10, PrecisionLevel.MICRO)
        point2 = create_point(10.001, 10.001, PrecisionLevel.MICRO)  # Very close

        constraint = self.constraint_system.add_coincident_constraint(point1, point2)

        self.assertIsInstance(constraint, CoincidentConstraint)
        # Should be satisfied due to tolerance
        self.assertTrue(constraint.validate()
    def test_constraint_solving(self):
        """Test constraint solving functionality."""
        # Add multiple constraints
        self.constraint_system.add_distance_constraint(self.point1, self.point2, 10.0)
        self.constraint_system.add_distance_constraint(self.point2, self.point3, 10.0)

        # Solve constraints
        success = self.constraint_system.solve_constraints()
        self.assertTrue(success)

    def test_constraint_status(self):
        """Test constraint status reporting."""
        self.constraint_system.add_distance_constraint(self.point1, self.point2, 10.0)

        status = self.constraint_system.get_constraint_status()

        self.assertIn('total_constraints', status)
        self.assertIn('satisfied_constraints', status)
        self.assertEqual(status['total_constraints'], 1)


class TestGridSnapSystem(unittest.TestCase):
    """Test grid and snap system functionality."""

    def setUp(self):
        """Set up test fixtures."""
        grid_settings = create_grid_settings(spacing=10.0, enabled=True, visible=True)
        snap_settings = create_snap_settings(enabled=True, tolerance=5.0)
        self.grid_snap_system = create_grid_snap_system(grid_settings, snap_settings)

    def test_grid_snapping(self):
        """Test grid snapping functionality."""
        point = create_point(12.5, 17.3, PrecisionLevel.MICRO)

        snapped_point = self.grid_snap_system.snap_point(
            point, snap_to_grid=True, snap_to_objects=False
        )

        # Should snap to nearest grid intersection
        self.assertEqual(snapped_point.x, decimal.Decimal('10.000')
        self.assertEqual(snapped_point.y, decimal.Decimal('20.000')
    def test_object_snapping(self):
        """Test object snapping functionality."""
        # Create test entities
class MockLine:
            def __init__(self, start, end):
                self.start = start
                self.end = end

        line = MockLine(
            create_point(0, 0, PrecisionLevel.MICRO),
            create_point(10, 0, PrecisionLevel.MICRO)
        self.grid_snap_system.add_entity(line)

        # Test snapping to endpoint
        cursor_point = create_point(0.1, 0.1, PrecisionLevel.MICRO)
        snapped_point = self.grid_snap_system.snap_point(
            cursor_point, snap_to_grid=False, snap_to_objects=True
        )

        # Should snap to endpoint
        self.assertEqual(snapped_point.x, decimal.Decimal('0.000')
        self.assertEqual(snapped_point.y, decimal.Decimal('0.000')
    def test_snap_feedback(self):
        """Test snap feedback functionality."""
        cursor_point = create_point(5, 5, PrecisionLevel.MICRO)

        feedback = self.grid_snap_system.get_snap_feedback(cursor_point)

        self.assertIn('snap_points', feedback)
        self.assertIn('grid_lines', feedback)
        self.assertIn('snap_type', feedback)
        self.assertIn('snap_position', feedback)
        self.assertIn('magnetic', feedback)

    def test_grid_settings_update(self):
        """Test grid settings update functionality."""
        new_settings = create_grid_settings(spacing=5.0, enabled=True, visible=True)

        self.grid_snap_system.update_grid_settings(new_settings)

        # Test with new spacing
        point = create_point(7.5, 7.5, PrecisionLevel.MICRO)
        snapped_point = self.grid_snap_system.snap_point(
            point, snap_to_grid=True, snap_to_objects=False
        )

        self.assertEqual(snapped_point.x, decimal.Decimal('5.000')
        self.assertEqual(snapped_point.y, decimal.Decimal('5.000')
    def test_snap_statistics(self):
        """Test snap statistics reporting."""
        statistics = self.grid_snap_system.get_snap_statistics()

        self.assertIn('total_entities', statistics)
        self.assertIn('snap_history_count', statistics)
        self.assertIn('grid_enabled', statistics)
        self.assertIn('snap_enabled', statistics)
        self.assertIn('active_snap_types', statistics)


class TestDimensioningSystem(unittest.TestCase):
    """Test dimensioning system functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.dimensioning_system = create_dimensioning_system()

        # Create test points
        self.point1 = create_point(0, 0, PrecisionLevel.MICRO)
        self.point2 = create_point(10, 0, PrecisionLevel.MICRO)
        self.point3 = create_point(0, 10, PrecisionLevel.MICRO)
        self.center_point = create_point(5, 5, PrecisionLevel.MICRO)

    def test_linear_dimension_creation(self):
        """Test linear dimension creation."""
        dimension = self.dimensioning_system.create_linear_dimension(
            self.point1, self.point2
        )

        self.assertIsInstance(dimension, LinearDimension)
        self.assertEqual(dimension.measurement, decimal.Decimal('10.000')
        self.assertEqual(dimension.dimension_type, DimensionType.LINEAR)

    def test_radial_dimension_creation(self):
        """Test radial dimension creation."""
        radius = decimal.Decimal('5.0')
        dimension = self.dimensioning_system.create_radial_dimension(
            self.center_point, radius
        )

        self.assertIsInstance(dimension, RadialDimension)
        self.assertEqual(dimension.measurement, radius)
        self.assertEqual(dimension.dimension_type, DimensionType.RADIAL)

    def test_angular_dimension_creation(self):
        """Test angular dimension creation."""
        dimension = self.dimensioning_system.create_angular_dimension(
            self.center_point, self.point1, self.point3
        )

        self.assertIsInstance(dimension, AngularDimension)
        self.assertEqual(dimension.dimension_type, DimensionType.ANGULAR)
        # Should be 90 degrees
        expected_angle = decimal.Decimal(str(math.pi / 2)
        self.assertAlmostEqual(float(dimension.measurement), float(expected_angle), places=3)

    def test_aligned_dimension_creation(self):
        """Test aligned dimension creation."""
        dimension = self.dimensioning_system.create_aligned_dimension(
            self.point1, self.point2
        )

        self.assertIsInstance(dimension, AlignedDimension)
        self.assertEqual(dimension.measurement, decimal.Decimal('10.000')
        self.assertEqual(dimension.dimension_type, DimensionType.ALIGNED)

    def test_ordinate_dimension_creation(self):
        """Test ordinate dimension creation."""
        dimension = self.dimensioning_system.create_ordinate_dimension(
            self.point1, self.point2, is_x_coordinate=True
        )

        self.assertIsInstance(dimension, OrdinateDimension)
        self.assertEqual(dimension.measurement, decimal.Decimal('10.000')
        self.assertEqual(dimension.dimension_type, DimensionType.ORDINATE)

    def test_dimension_line_points(self):
        """Test dimension line point calculation."""
        dimension = self.dimensioning_system.create_linear_dimension(
            self.point1, self.point2
        )

        line_points = dimension.get_dimension_line_points()

        self.assertIsInstance(line_points, list)
        self.assertEqual(len(line_points), 2)
        self.assertIsInstance(line_points[0], PrecisionPoint)
        self.assertIsInstance(line_points[1], PrecisionPoint)

    def test_extension_lines(self):
        """Test extension line calculation."""
        dimension = self.dimensioning_system.create_linear_dimension(
            self.point1, self.point2
        )

        extension_lines = dimension.get_extension_lines()

        self.assertIsInstance(extension_lines, list)
        self.assertEqual(len(extension_lines), 2)
        for line in extension_lines:
            self.assertIsInstance(line, tuple)
            self.assertEqual(len(line), 2)
            self.assertIsInstance(line[0], PrecisionPoint)
            self.assertIsInstance(line[1], PrecisionPoint)

    def test_auto_dimension_rectangle(self):
        """Test automatic rectangle dimensioning."""
        points = [
            create_point(0, 0, PrecisionLevel.MICRO),
            create_point(10, 0, PrecisionLevel.MICRO),
            create_point(10, 5, PrecisionLevel.MICRO),
            create_point(0, 5, PrecisionLevel.MICRO)
        ]

        dimensions = self.dimensioning_system.auto_dimension_rectangle(points)

        self.assertIsInstance(dimensions, list)
        self.assertEqual(len(dimensions), 2)
        self.assertIsInstance(dimensions[0], LinearDimension)
        self.assertIsInstance(dimensions[1], LinearDimension)

    def test_auto_dimension_circle(self):
        """Test automatic circle dimensioning."""
        radius = decimal.Decimal('5.0')

        dimensions = self.dimensioning_system.auto_dimension_circle(
            self.center_point, radius
        )

        self.assertIsInstance(dimensions, list)
        self.assertEqual(len(dimensions), 1)
        self.assertIsInstance(dimensions[0], RadialDimension)

    def test_dimension_style_management(self):
        """Test dimension style management."""
        # Create custom style
        custom_style = create_dimension_style(
            name="custom", text_height=3.0, precision=1, units="cm"
        )

        self.dimensioning_system.add_style(custom_style)

        # Verify style was added
        styles = self.dimensioning_system.get_all_styles()
        self.assertIn("custom", styles)

        # Get style
        retrieved_style = self.dimensioning_system.get_style("custom")
        self.assertIsInstance(retrieved_style, DimensionStyle)
        self.assertEqual(retrieved_style.name, "custom")

    def test_dimension_statistics(self):
        """Test dimension statistics reporting."""
        # Create some dimensions
        self.dimensioning_system.create_linear_dimension(self.point1, self.point2)
        self.dimensioning_system.create_radial_dimension(self.center_point, decimal.Decimal('5.0')
        statistics = self.dimensioning_system.get_dimension_statistics()

        self.assertIn('total_dimensions', statistics)
        self.assertIn('dimension_types', statistics)
        self.assertIn('available_styles', statistics)
        self.assertIn('style_names', statistics)
        self.assertEqual(statistics['total_dimensions'], 2)


class TestCADComponentsIntegration(unittest.TestCase):
    """Test integration between CAD components."""

    def setUp(self):
        """Set up test fixtures."""
        self.precision_system = create_precision_drawing_system(PrecisionLevel.MICRO)
        self.constraint_system = create_constraint_system()
        self.grid_snap_system = create_grid_snap_system()
        self.dimensioning_system = create_dimensioning_system()

    def test_precision_with_constraints(self):
        """Test precision system integration with constraints."""
        # Create precise points
        point1 = create_point(0, 0, PrecisionLevel.MICRO)
        point2 = create_point(10, 0, PrecisionLevel.MICRO)

        # Add distance constraint
        constraint = self.constraint_system.add_distance_constraint(point1, point2, 10.0)

        # Verify constraint works with precise points
        self.assertTrue(constraint.validate()
        # Test constraint solving
        success = self.constraint_system.solve_constraints()
        self.assertTrue(success)

    def test_grid_snap_with_precision(self):
        """Test grid snap system integration with precision system."""
        # Create precise point
        point = create_point(12.5, 17.3, PrecisionLevel.MICRO)

        # Snap to grid
        snapped_point = self.grid_snap_system.snap_point(
            point, snap_to_grid=True, snap_to_objects=False
        )

        # Verify precision is maintained
        self.assertEqual(snapped_point.precision, PrecisionLevel.MICRO)
        self.assertEqual(snapped_point.x, decimal.Decimal('10.000')
        self.assertEqual(snapped_point.y, decimal.Decimal('20.000')
    def test_dimensioning_with_precision(self):
        """Test dimensioning system integration with precision system."""
        # Create precise points
        point1 = create_point(0, 0, PrecisionLevel.MICRO)
        point2 = create_point(10, 0, PrecisionLevel.MICRO)

        # Create dimension
        dimension = self.dimensioning_system.create_linear_dimension(point1, point2)

        # Verify precision is maintained
        self.assertEqual(dimension.measurement, decimal.Decimal('10.000')
        self.assertEqual(dimension.precision, PrecisionLevel.MICRO)

    def test_complete_workflow(self):
        """Test complete CAD workflow integration."""
        # 1. Create precise geometry
        point1 = create_point(0, 0, PrecisionLevel.MICRO)
        point2 = create_point(10, 0, PrecisionLevel.MICRO)
        point3 = create_point(10, 10, PrecisionLevel.MICRO)

        # 2. Add constraints
        self.constraint_system.add_distance_constraint(point1, point2, 10.0)
        self.constraint_system.add_distance_constraint(point2, point3, 10.0)
        self.constraint_system.add_perpendicular_constraint(
            create_vector(10, 0, PrecisionLevel.MICRO),
            create_vector(0, 10, PrecisionLevel.MICRO)
        # 3. Solve constraints
        constraint_success = self.constraint_system.solve_constraints()
        self.assertTrue(constraint_success)

        # 4. Snap to grid
        snapped_point1 = self.grid_snap_system.snap_point(point1)
        snapped_point2 = self.grid_snap_system.snap_point(point2)
        snapped_point3 = self.grid_snap_system.snap_point(point3)

        # 5. Create dimensions
        dim1 = self.dimensioning_system.create_linear_dimension(snapped_point1, snapped_point2)
        dim2 = self.dimensioning_system.create_linear_dimension(snapped_point2, snapped_point3)

        # 6. Verify results
        self.assertEqual(dim1.measurement, decimal.Decimal('10.000')
        self.assertEqual(dim2.measurement, decimal.Decimal('10.000')
        # Check statistics
        constraint_status = self.constraint_system.get_constraint_status()
        snap_statistics = self.grid_snap_system.get_snap_statistics()
        dimension_statistics = self.dimensioning_system.get_dimension_statistics()

        self.assertGreater(constraint_status['satisfied_constraints'], 0)
        self.assertGreater(dimension_statistics['total_dimensions'], 0)


class TestCADComponentsPerformance(unittest.TestCase):
    """Test performance characteristics of CAD components."""

    def setUp(self):
        """Set up test fixtures."""
        self.precision_system = create_precision_drawing_system(PrecisionLevel.MICRO)
        self.constraint_system = create_constraint_system()
        self.grid_snap_system = create_grid_snap_system()
        self.dimensioning_system = create_dimensioning_system()

    def test_precision_performance(self):
        """Test precision system performance with many operations."""
        import time

        start_time = time.time()

        # Create many points and vectors
        points = []
        vectors = []

        for i in range(1000):
            point = create_point(i * 0.1, i * 0.2, PrecisionLevel.MICRO)
            vector = create_vector(i * 0.01, i * 0.02, PrecisionLevel.MICRO)
            points.append(point)
            vectors.append(vector)

        # Perform operations
        for i in range(100):
            if i + 1 < len(points):
                distance = self.precision_system.calculate_distance(points[i], points[i + 1])
                angle = self.precision_system.calculate_angle(points[i], points[i + 1], points[i + 2] if i + 2 < len(points) else points[0])

        end_time = time.time()
        execution_time = end_time - start_time

        # Performance should be reasonable (less than 1 second for 1000 operations)
        self.assertLess(execution_time, 1.0)

    def test_constraint_performance(self):
        """Test constraint system performance with many constraints."""
        import time

        start_time = time.time()

        # Create many constraints
        for i in range(100):
            point1 = create_point(i, i, PrecisionLevel.MICRO)
            point2 = create_point(i + 10, i, PrecisionLevel.MICRO)
            self.constraint_system.add_distance_constraint(point1, point2, 10.0)

        # Solve constraints
        success = self.constraint_system.solve_constraints()

        end_time = time.time()
        execution_time = end_time - start_time

        self.assertTrue(success)
        # Performance should be reasonable
        self.assertLess(execution_time, 1.0)

    def test_grid_snap_performance(self):
        """Test grid snap system performance with many entities."""
        import time

        start_time = time.time()

        # Add many entities
        for i in range(100):
            class MockEntity:
                def __init__(self, x, y):
                    self.start = create_point(x, y, PrecisionLevel.MICRO)
                    self.end = create_point(x + 10, y + 10, PrecisionLevel.MICRO)

            entity = MockEntity(i * 5, i * 5)
            self.grid_snap_system.add_entity(entity)

        # Test snapping
        for i in range(50):
            cursor_point = create_point(i * 2, i * 2, PrecisionLevel.MICRO)
            self.grid_snap_system.snap_point(cursor_point)

        end_time = time.time()
        execution_time = end_time - start_time

        # Performance should be reasonable
        self.assertLess(execution_time, 1.0)

    def test_dimensioning_performance(self):
        """Test dimensioning system performance with many dimensions."""
        import time

        start_time = time.time()

        # Create many dimensions
        for i in range(100):
            point1 = create_point(i, i, PrecisionLevel.MICRO)
            point2 = create_point(i + 10, i, PrecisionLevel.MICRO)
            self.dimensioning_system.create_linear_dimension(point1, point2)

        # Get statistics
        statistics = self.dimensioning_system.get_dimension_statistics()

        end_time = time.time()
        execution_time = end_time - start_time

        self.assertEqual(statistics['total_dimensions'], 100)
        # Performance should be reasonable
        self.assertLess(execution_time, 1.0)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)
