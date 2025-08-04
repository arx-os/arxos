"""
Comprehensive Test Suite for Advanced Curve System

Tests all curve functionality including:
- Bezier curves with precision evaluation
- B-spline curves with knot vectors
- Curve constraints (tangent, curvature, position, length)
- Curve fitting algorithms
- Curve system integration

CTO Directives:
- Enterprise-grade curve testing
- Comprehensive curve functionality validation
- Professional CAD curve testing
- Complete curve system integration testing
"""

import unittest
import sys
import os
import math
import decimal
from decimal import Decimal
from typing import List, Dict, Any

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from svgx_engine.services.cad.curve_system import (
    CurveSystem, BezierCurve, BSplineCurve, CurveFitter,
    ControlPoint, CurvePoint, KnotVector, CurveType,
    create_curve_system, create_bezier_curve, create_bspline_curve
)
from svgx_engine.services.cad.constraint_system import (
    CurveTangentConstraint, CurvatureContinuousConstraint,
    CurvePositionConstraint, CurveLengthConstraint
)
from svgx_engine.core.precision_coordinate import PrecisionCoordinate
from svgx_engine.core.precision_config import PrecisionConfig, config_manager


class TestBezierCurve(unittest.TestCase):
    """Test Bezier curve functionality with precision support."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = config_manager.get_default_config()
        
        # Create control points for a cubic Bezier curve
        self.control_points = [
            ControlPoint(PrecisionCoordinate(0, 0, 0)),
            ControlPoint(PrecisionCoordinate(1, 1, 0)),
            ControlPoint(PrecisionCoordinate(2, 0, 0)),
            ControlPoint(PrecisionCoordinate(3, 1, 0))
        ]
        
        self.bezier_curve = BezierCurve(self.control_points, self.config)
    
    def test_bezier_curve_creation(self):
        """Test Bezier curve creation with validation."""
        self.assertIsNotNone(self.bezier_curve)
        self.assertEqual(self.bezier_curve.degree, 3)
        self.assertEqual(len(self.bezier_curve.control_points), 4)
        
        # Test that control points are properly stored
        for i, cp in enumerate(self.bezier_curve.control_points):
            self.assertEqual(cp.position.x, self.control_points[i].position.x)
            self.assertEqual(cp.position.y, self.control_points[i].position.y)
    
    def test_bezier_curve_evaluation(self):
        """Test Bezier curve evaluation at various parameters."""
        # Test at t = 0 (start point)
        point0 = self.bezier_curve.evaluate(0.0)
        self.assertIsInstance(point0, CurvePoint)
        self.assertEqual(point0.parameter, 0.0)
        self.assertAlmostEqual(float(point0.position.x), 0.0, places=6)
        self.assertAlmostEqual(float(point0.position.y), 0.0, places=6)
        
        # Test at t = 1 (end point)
        point1 = self.bezier_curve.evaluate(1.0)
        self.assertAlmostEqual(float(point1.position.x), 3.0, places=6)
        self.assertAlmostEqual(float(point1.position.y), 1.0, places=6)
        
        # Test at t = 0.5 (midpoint)
        point05 = self.bezier_curve.evaluate(0.5)
        self.assertAlmostEqual(float(point05.parameter), 0.5, places=6)
        
        # Verify tangent exists
        self.assertIsNotNone(point05.tangent)
        self.assertIsNotNone(point05.normal)
    
    def test_bezier_curve_tangent_calculation(self):
        """Test tangent calculation for Bezier curves."""
        # Test tangent at start point
        point0 = self.bezier_curve.evaluate(0.0)
        tangent0 = self.bezier_curve._calculate_tangent(Decimal('0'))
        
        # Tangent should point in the direction of the first control vector
        expected_dx = 3.0  # degree * (p1.x - p0.x)
        expected_dy = 3.0  # degree * (p1.y - p0.y)
        
        self.assertAlmostEqual(float(tangent0.x), expected_dx, places=6)
        self.assertAlmostEqual(float(tangent0.y), expected_dy, places=6)
    
    def test_bezier_curve_curvature_calculation(self):
        """Test curvature calculation for Bezier curves."""
        # Test curvature at midpoint
        curvature = self.bezier_curve._calculate_curvature(Decimal('0.5'))
        self.assertIsInstance(curvature, float)
        self.assertGreaterEqual(curvature, 0.0)  # Curvature should be non-negative
    
    def test_bezier_curve_bounding_box(self):
        """Test bounding box calculation for Bezier curves."""
        bbox_min, bbox_max = self.bezier_curve.get_bounding_box()
        
        self.assertIsInstance(bbox_min, PrecisionCoordinate)
        self.assertIsInstance(bbox_max, PrecisionCoordinate)
        
        # Bounding box should contain all control points
        for cp in self.control_points:
            self.assertGreaterEqual(cp.position.x, bbox_min.x)
            self.assertLessEqual(cp.position.x, bbox_max.x)
            self.assertGreaterEqual(cp.position.y, bbox_min.y)
            self.assertLessEqual(cp.position.y, bbox_max.y)
    
    def test_bezier_curve_subdivision(self):
        """Test Bezier curve subdivision."""
        left_curve, right_curve = self.bezier_curve.subdivide(0.5)
        
        self.assertIsInstance(left_curve, BezierCurve)
        self.assertIsInstance(right_curve, BezierCurve)
        
        # Left curve should start at original start point
        left_start = left_curve.evaluate(0.0)
        original_start = self.bezier_curve.evaluate(0.0)
        self.assertAlmostEqual(float(left_start.position.x), float(original_start.position.x), places=6)
        self.assertAlmostEqual(float(left_start.position.y), float(original_start.position.y), places=6)
        
        # Right curve should end at original end point
        right_end = right_curve.evaluate(1.0)
        original_end = self.bezier_curve.evaluate(1.0)
        self.assertAlmostEqual(float(right_end.position.x), float(original_end.position.x), places=6)
        self.assertAlmostEqual(float(right_end.position.y), float(original_end.position.y), places=6)
    
    def test_bezier_curve_invalid_parameters(self):
        """Test Bezier curve evaluation with invalid parameters."""
        with self.assertRaises(ValueError):
            self.bezier_curve.evaluate(-0.1)
        
        with self.assertRaises(ValueError):
            self.bezier_curve.evaluate(1.1)
    
    def test_bezier_curve_insufficient_control_points(self):
        """Test Bezier curve creation with insufficient control points."""
        with self.assertRaises(ValueError):
            BezierCurve([self.control_points[0]], self.config)


class TestBSplineCurve(unittest.TestCase):
    """Test B-spline curve functionality with precision support."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = config_manager.get_default_config()
        
        # Create control points for a cubic B-spline curve
        self.control_points = [
            ControlPoint(PrecisionCoordinate(0, 0, 0)),
            ControlPoint(PrecisionCoordinate(1, 1, 0)),
            ControlPoint(PrecisionCoordinate(2, 0, 0)),
            ControlPoint(PrecisionCoordinate(3, 1, 0)),
            ControlPoint(PrecisionCoordinate(4, 0, 0))
        ]
        
        # Create clamped knot vector for cubic curve
        self.knot_vector = KnotVector([0, 0, 0, 0, 0.5, 1, 1, 1, 1], 3, True)
        
        self.bspline_curve = BSplineCurve(self.control_points, self.knot_vector, self.config)
    
    def test_bspline_curve_creation(self):
        """Test B-spline curve creation with validation."""
        self.assertIsNotNone(self.bspline_curve)
        self.assertEqual(len(self.bspline_curve.control_points), 5)
        self.assertEqual(self.bspline_curve.knot_vector.degree, 3)
    
    def test_bspline_curve_evaluation(self):
        """Test B-spline curve evaluation at various parameters."""
        # Test at u = 0 (start point)
        point0 = self.bspline_curve.evaluate(0.0)
        self.assertIsInstance(point0, CurvePoint)
        self.assertEqual(point0.parameter, 0.0)
        
        # Test at u = 1 (end point)
        point1 = self.bspline_curve.evaluate(1.0)
        self.assertEqual(point1.parameter, 1.0)
        
        # Test at u = 0.5 (midpoint)
        point05 = self.bspline_curve.evaluate(0.5)
        self.assertAlmostEqual(float(point05.parameter), 0.5, places=6)
    
    def test_bspline_knot_span_finding(self):
        """Test knot span finding algorithm."""
        span = self.bspline_curve._find_knot_span(Decimal('0.5'))
        self.assertIsInstance(span, int)
        self.assertGreaterEqual(span, 0)
        self.assertLess(span, len(self.bspline_curve.control_points))
    
    def test_bspline_basis_functions(self):
        """Test B-spline basis function calculation."""
        span = self.bspline_curve._find_knot_span(Decimal('0.5'))
        basis_functions = self.bspline_curve._calculate_basis_functions(span, Decimal('0.5'))
        
        self.assertIsInstance(basis_functions, list)
        self.assertEqual(len(basis_functions), self.bspline_curve.knot_vector.degree + 1)
        
        # Basis functions should sum to 1
        basis_sum = sum(basis_functions)
        self.assertAlmostEqual(float(basis_sum), 1.0, places=6)
    
    def test_bspline_position_calculation(self):
        """Test B-spline position calculation."""
        span = self.bspline_curve._find_knot_span(Decimal('0.5'))
        basis_functions = self.bspline_curve._calculate_basis_functions(span, Decimal('0.5'))
        position = self.bspline_curve._calculate_position(span, basis_functions)
        
        self.assertIsInstance(position, PrecisionCoordinate)
        self.assertIsInstance(position.x, Decimal)
        self.assertIsInstance(position.y, Decimal)
    
    def test_bspline_invalid_control_points(self):
        """Test B-spline creation with invalid number of control points."""
        # Create knot vector that doesn't match control points
        invalid_knot_vector = KnotVector([0, 0, 0, 1, 1, 1], 2, True)
        
        with self.assertRaises(ValueError):
            BSplineCurve(self.control_points, invalid_knot_vector, self.config)


class TestCurveFitter(unittest.TestCase):
    """Test curve fitting algorithms."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = config_manager.get_default_config()
        self.fitter = CurveFitter(self.config)
        
        # Create test points for fitting
        self.test_points = [
            PrecisionCoordinate(0, 0, 0),
            PrecisionCoordinate(1, 1, 0),
            PrecisionCoordinate(2, 0, 0),
            PrecisionCoordinate(3, 1, 0),
            PrecisionCoordinate(4, 0, 0)
        ]
    
    def test_curve_fitter_creation(self):
        """Test curve fitter creation."""
        self.assertIsNotNone(self.fitter)
        self.assertIsNotNone(self.fitter.config)
    
    def test_bezier_curve_fitting(self):
        """Test Bezier curve fitting to points."""
        curve = self.fitter.fit_bezier_to_points(self.test_points, degree=3)
        
        self.assertIsInstance(curve, BezierCurve)
        self.assertEqual(curve.degree, 3)
        self.assertEqual(len(curve.control_points), 4)
    
    def test_curve_fitting_insufficient_points(self):
        """Test curve fitting with insufficient points."""
        with self.assertRaises(ValueError):
            self.fitter.fit_bezier_to_points(self.test_points[:2], degree=3)
    
    def test_parameterization(self):
        """Test point parameterization."""
        parameters = self.fitter._parameterize_points(self.test_points)
        
        self.assertIsInstance(parameters, list)
        self.assertEqual(len(parameters), len(self.test_points))
        self.assertEqual(parameters[0], 0.0)
        self.assertEqual(parameters[-1], 1.0)
        
        # Parameters should be monotonically increasing
        for i in range(1, len(parameters)):
            self.assertGreaterEqual(parameters[i], parameters[i-1])
    
    def test_bezier_matrix_building(self):
        """Test Bezier coefficient matrix building."""
        parameters = self.fitter._parameterize_points(self.test_points)
        matrix = self.fitter._build_bezier_matrix(parameters, 3)
        
        import numpy as np
        self.assertIsInstance(matrix, np.ndarray)
        self.assertEqual(matrix.shape, (len(self.test_points), 4))
    
    def test_bernstein_basis_functions(self):
        """Test Bernstein basis function calculation."""
        # Test for cubic curve (degree 3)
        for i in range(4):
            value = self.fitter._bernstein_basis(i, 3, 0.5)
            self.assertIsInstance(value, float)
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 1.0)
    
    def test_binomial_coefficient(self):
        """Test binomial coefficient calculation."""
        # Test some known values
        self.assertEqual(self.fitter._binomial(5, 2), 10)
        self.assertEqual(self.fitter._binomial(4, 0), 1)
        self.assertEqual(self.fitter._binomial(4, 4), 1)
        self.assertEqual(self.fitter._binomial(3, 5), 0)  # k > n
    
    def test_least_squares_solving(self):
        """Test least squares problem solving."""
        parameters = self.fitter._parameterize_points(self.test_points)
        matrix = self.fitter._build_bezier_matrix(parameters, 3)
        control_points = self.fitter._solve_least_squares(matrix, self.test_points)
        
        self.assertIsInstance(control_points, list)
        self.assertEqual(len(control_points), 4)
        
        for cp in control_points:
            self.assertIsInstance(cp, ControlPoint)
            self.assertIsInstance(cp.position, PrecisionCoordinate)


class TestCurveConstraints(unittest.TestCase):
    """Test curve constraint functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = config_manager.get_default_config()
        
        # Create two Bezier curves for testing constraints
        self.control_points1 = [
            ControlPoint(PrecisionCoordinate(0, 0, 0)),
            ControlPoint(PrecisionCoordinate(1, 1, 0)),
            ControlPoint(PrecisionCoordinate(2, 0, 0))
        ]
        
        self.control_points2 = [
            ControlPoint(PrecisionCoordinate(2, 0, 0)),  # Start where first curve ends
            ControlPoint(PrecisionCoordinate(3, 1, 0)),
            ControlPoint(PrecisionCoordinate(4, 0, 0))
        ]
        
        self.curve1 = BezierCurve(self.control_points1, self.config)
        self.curve2 = BezierCurve(self.control_points2, self.config)
    
    def test_curve_tangent_constraint_creation(self):
        """Test curve tangent constraint creation."""
        constraint = CurveTangentConstraint(self.curve1, self.curve2)
        
        self.assertIsInstance(constraint, CurveTangentConstraint)
        self.assertEqual(constraint.constraint_type.value, "curve_tangent")
        self.assertEqual(len(constraint.entities), 2)
    
    def test_curve_tangent_constraint_validation(self):
        """Test curve tangent constraint validation."""
        constraint = CurveTangentConstraint(self.curve1, self.curve2)
        
        # Should be valid since curves are positioned to be tangent
        self.assertTrue(constraint.validate())
    
    def test_curve_tangent_constraint_solving(self):
        """Test curve tangent constraint solving."""
        constraint = CurveTangentConstraint(self.curve1, self.curve2)
        
        # Should be able to solve the constraint
        self.assertTrue(constraint.solve())
    
    def test_curvature_continuous_constraint(self):
        """Test curvature continuous constraint."""
        constraint = CurvatureContinuousConstraint(self.curve1, self.curve2)
        
        self.assertIsInstance(constraint, CurvatureContinuousConstraint)
        self.assertEqual(constraint.constraint_type.value, "curvature_continuous")
        
        # Test validation
        self.assertTrue(constraint.validate())
    
    def test_curve_position_constraint(self):
        """Test curve position constraint."""
        target_position = PrecisionCoordinate(2.5, 0.5, 0)
        constraint = CurvePositionConstraint(self.curve1, target_position)
        
        self.assertIsInstance(constraint, CurvePositionConstraint)
        self.assertEqual(constraint.constraint_type.value, "curve_position")
        
        # Test validation
        result = constraint.validate()
        self.assertIsInstance(result, bool)
    
    def test_curve_length_constraint(self):
        """Test curve length constraint."""
        target_length = 2.0
        constraint = CurveLengthConstraint(self.curve1, target_length)
        
        self.assertIsInstance(constraint, CurveLengthConstraint)
        self.assertEqual(constraint.constraint_type.value, "curve_length")
        
        # Test validation
        result = constraint.validate()
        self.assertIsInstance(result, bool)
    
    def test_curve_length_calculation(self):
        """Test curve length calculation."""
        constraint = CurveLengthConstraint(self.curve1, 2.0)
        length = constraint._calculate_curve_length(self.curve1)
        
        self.assertIsInstance(length, float)
        self.assertGreater(length, 0.0)
    
    def test_curve_constraint_distance_calculation(self):
        """Test distance calculation in curve constraints."""
        constraint = CurveTangentConstraint(self.curve1, self.curve2)
        
        pos1 = PrecisionCoordinate(0, 0, 0)
        pos2 = PrecisionCoordinate(1, 1, 0)
        distance = constraint._calculate_distance(pos1, pos2)
        
        self.assertIsInstance(distance, float)
        self.assertGreater(distance, 0.0)
        self.assertAlmostEqual(distance, math.sqrt(2), places=6)
    
    def test_curve_constraint_angle_calculation(self):
        """Test angle calculation in curve constraints."""
        constraint = CurveTangentConstraint(self.curve1, self.curve2)
        
        vec1 = PrecisionCoordinate(1, 0, 0)
        vec2 = PrecisionCoordinate(0, 1, 0)
        angle = constraint._calculate_angle_between_vectors(vec1, vec2)
        
        self.assertIsInstance(angle, float)
        self.assertAlmostEqual(angle, math.pi/2, places=6)


class TestCurveSystem(unittest.TestCase):
    """Test curve system integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.curve_system = CurveSystem()
    
    def test_curve_system_creation(self):
        """Test curve system creation."""
        self.assertIsNotNone(self.curve_system)
        self.assertIsNotNone(self.curve_system.config)
        self.assertIsNotNone(self.curve_system.fitter)
        self.assertEqual(len(self.curve_system.curves), 0)
        self.assertEqual(len(self.curve_system.constraints), 0)
    
    def test_bezier_curve_creation(self):
        """Test Bezier curve creation through curve system."""
        control_points = [
            ControlPoint(PrecisionCoordinate(0, 0, 0)),
            ControlPoint(PrecisionCoordinate(1, 1, 0)),
            ControlPoint(PrecisionCoordinate(2, 0, 0))
        ]
        
        curve = self.curve_system.create_bezier_curve(control_points)
        
        self.assertIsInstance(curve, BezierCurve)
        self.assertIn(curve, self.curve_system.curves)
    
    def test_bspline_curve_creation(self):
        """Test B-spline curve creation through curve system."""
        control_points = [
            ControlPoint(PrecisionCoordinate(0, 0, 0)),
            ControlPoint(PrecisionCoordinate(1, 1, 0)),
            ControlPoint(PrecisionCoordinate(2, 0, 0)),
            ControlPoint(PrecisionCoordinate(3, 1, 0))
        ]
        
        curve = self.curve_system.create_bspline_curve(control_points, degree=3)
        
        self.assertIsInstance(curve, BSplineCurve)
        self.assertIn(curve, self.curve_system.curves)
    
    def test_curve_fitting(self):
        """Test curve fitting through curve system."""
        points = [
            PrecisionCoordinate(0, 0, 0),
            PrecisionCoordinate(1, 1, 0),
            PrecisionCoordinate(2, 0, 0),
            PrecisionCoordinate(3, 1, 0)
        ]
        
        curve = self.curve_system.fit_curve_to_points(points, CurveType.BEZIER, degree=3)
        
        self.assertIsInstance(curve, BezierCurve)
        self.assertIn(curve, self.curve_system.curves)
    
    def test_curve_constraint_creation(self):
        """Test curve constraint creation through curve system."""
        # Create two curves
        control_points1 = [
            ControlPoint(PrecisionCoordinate(0, 0, 0)),
            ControlPoint(PrecisionCoordinate(1, 1, 0)),
            ControlPoint(PrecisionCoordinate(2, 0, 0))
        ]
        
        control_points2 = [
            ControlPoint(PrecisionCoordinate(2, 0, 0)),
            ControlPoint(PrecisionCoordinate(3, 1, 0)),
            ControlPoint(PrecisionCoordinate(4, 0, 0))
        ]
        
        curve1 = self.curve_system.create_bezier_curve(control_points1)
        curve2 = self.curve_system.create_bezier_curve(control_points2)
        
        # Add tangent constraint
        constraint = self.curve_system.add_curve_constraint(curve1, curve2, "tangent")
        
        self.assertIsInstance(constraint, CurveTangentConstraint)
        self.assertIn(constraint, self.curve_system.constraints)
    
    def test_constraint_validation(self):
        """Test constraint validation in curve system."""
        # Create curves and constraints
        control_points1 = [
            ControlPoint(PrecisionCoordinate(0, 0, 0)),
            ControlPoint(PrecisionCoordinate(1, 1, 0)),
            ControlPoint(PrecisionCoordinate(2, 0, 0))
        ]
        
        control_points2 = [
            ControlPoint(PrecisionCoordinate(2, 0, 0)),
            ControlPoint(PrecisionCoordinate(3, 1, 0)),
            ControlPoint(PrecisionCoordinate(4, 0, 0))
        ]
        
        curve1 = self.curve_system.create_bezier_curve(control_points1)
        curve2 = self.curve_system.create_bezier_curve(control_points2)
        
        self.curve_system.add_curve_constraint(curve1, curve2, "tangent")
        
        # Validate constraints
        result = self.curve_system.validate_constraints()
        self.assertIsInstance(result, bool)
    
    def test_curve_system_statistics(self):
        """Test curve system statistics."""
        # Create some curves
        control_points = [
            ControlPoint(PrecisionCoordinate(0, 0, 0)),
            ControlPoint(PrecisionCoordinate(1, 1, 0)),
            ControlPoint(PrecisionCoordinate(2, 0, 0))
        ]
        
        self.curve_system.create_bezier_curve(control_points)
        self.curve_system.create_bspline_curve(control_points, degree=2)
        
        stats = self.curve_system.get_curve_statistics()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('total_curves', stats)
        self.assertIn('bezier_curves', stats)
        self.assertIn('bspline_curves', stats)
        self.assertIn('total_constraints', stats)
        self.assertIn('valid_constraints', stats)
        
        self.assertEqual(stats['total_curves'], 2)
        self.assertEqual(stats['bezier_curves'], 1)
        self.assertEqual(stats['bspline_curves'], 1)


class TestCurveSystemIntegration(unittest.TestCase):
    """Test integration between curve system and constraint system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.curve_system = CurveSystem()
        self.constraint_system = create_constraint_system()
    
    def test_curve_constraint_integration(self):
        """Test integration between curve and constraint systems."""
        # Create curves
        control_points1 = [
            ControlPoint(PrecisionCoordinate(0, 0, 0)),
            ControlPoint(PrecisionCoordinate(1, 1, 0)),
            ControlPoint(PrecisionCoordinate(2, 0, 0))
        ]
        
        control_points2 = [
            ControlPoint(PrecisionCoordinate(2, 0, 0)),
            ControlPoint(PrecisionCoordinate(3, 1, 0)),
            ControlPoint(PrecisionCoordinate(4, 0, 0))
        ]
        
        curve1 = self.curve_system.create_bezier_curve(control_points1)
        curve2 = self.curve_system.create_bezier_curve(control_points2)
        
        # Add curve constraints through constraint system
        tangent_constraint = self.constraint_system.add_curve_tangent_constraint(curve1, curve2)
        curvature_constraint = self.constraint_system.add_curvature_continuous_constraint(curve1, curve2)
        
        self.assertIsInstance(tangent_constraint, CurveTangentConstraint)
        self.assertIsInstance(curvature_constraint, CurvatureContinuousConstraint)
        
        # Validate constraints
        self.assertTrue(self.constraint_system.validate_constraints())
    
    def test_curve_fitting_with_constraints(self):
        """Test curve fitting with subsequent constraint application."""
        # Create points for fitting
        points = [
            PrecisionCoordinate(0, 0, 0),
            PrecisionCoordinate(1, 1, 0),
            PrecisionCoordinate(2, 0, 0),
            PrecisionCoordinate(3, 1, 0)
        ]
        
        # Fit curve
        curve = self.curve_system.fit_curve_to_points(points, CurveType.BEZIER, degree=3)
        
        # Add position constraint
        target_position = PrecisionCoordinate(1.5, 0.5, 0)
        position_constraint = self.constraint_system.add_curve_position_constraint(curve, target_position)
        
        self.assertIsInstance(position_constraint, CurvePositionConstraint)
        
        # Add length constraint
        length_constraint = self.constraint_system.add_curve_length_constraint(curve, 3.0)
        
        self.assertIsInstance(length_constraint, CurveLengthConstraint)
        
        # Solve constraints
        self.assertTrue(self.constraint_system.solve_constraints())


def run_curve_system_tests():
    """Run all curve system tests."""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestBezierCurve,
        TestBSplineCurve,
        TestCurveFitter,
        TestCurveConstraints,
        TestCurveSystem,
        TestCurveSystemIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_curve_system_tests()
    if success:
        print("\n✅ All curve system tests passed!")
    else:
        print("\n❌ Some curve system tests failed!") 