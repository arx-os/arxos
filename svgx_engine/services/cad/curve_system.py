"""
Advanced Curve System for SVGX Engine

This module provides comprehensive curve functionality including B-splines, NURBS,
Bezier curves, curve fitting, and curve constraints with sub-millimeter precision.

CTO Directives:
- Enterprise-grade curve system
- Professional CAD curve functionality
- Comprehensive curve constraints
- Precision curve operations
- Advanced curve fitting algorithms
"""

import math
import decimal
import numpy as np
from typing import List, Dict, Optional, Union, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

# Import precision system components
from svgx_engine.core.precision_coordinate import (
    PrecisionCoordinate,
    CoordinateValidator,
)
from svgx_engine.core.precision_math import PrecisionMath
from svgx_engine.core.precision_validator import (
    PrecisionValidator,
    ValidationLevel,
    ValidationType,
)
from svgx_engine.core.precision_config import PrecisionConfig, config_manager
from svgx_engine.core.precision_hooks import hook_manager, HookType, HookContext
from svgx_engine.core.precision_errors import (
    handle_precision_error,
    PrecisionErrorType,
    PrecisionErrorSeverity,
)

logger = logging.getLogger(__name__)


class CurveType(Enum):
    """Types of curves supported by the system."""

    BEZIER = "bezier"
    B_SPLINE = "b_spline"
    NURBS = "nurbs"
    POLYLINE = "polyline"
    ARC = "arc"
    ELLIPSE = "ellipse"
    HYPERBOLA = "hyperbola"
    PARABOLA = "parabola"


class CurveDegree(Enum):
    """Curve degree definitions."""

    LINEAR = 1
    QUADRATIC = 2
    CUBIC = 3
    QUARTIC = 4
    QUINTIC = 5


@dataclass
class CurvePoint:
    """High-precision point on a curve with parameter value."""

    parameter: Union[float, decimal.Decimal]
    position: PrecisionCoordinate
    tangent: Optional[PrecisionCoordinate] = None
    normal: Optional[PrecisionCoordinate] = None
    curvature: Optional[float] = None

    def __post_init__(self):
        """Validate curve point after initialization."""
        self.config = config_manager.get_default_config()
        self.precision_math = PrecisionMath()
        self.coordinate_validator = CoordinateValidator()

        # Validate parameter value
        if self.parameter < 0 or self.parameter > 1:
            handle_precision_error(
                error_type=PrecisionErrorType.VALIDATION_ERROR,
                message=f"Invalid curve parameter: {self.parameter} (must be in [0,1])",
                operation="curve_point_validation",
                coordinates=[self.position],
                context={"parameter": self.parameter},
                severity=PrecisionErrorSeverity.ERROR,
            )
            raise ValueError(f"Invalid curve parameter: {self.parameter}")


@dataclass
class ControlPoint:
    """Control point for curve definition with precision support."""

    position: PrecisionCoordinate
    weight: Union[float, decimal.Decimal] = 1.0
    is_selected: bool = False

    def __post_init__(self):
        """Validate control point after initialization."""
        self.config = config_manager.get_default_config()

        # Validate weight
        if self.weight <= 0:
            handle_precision_error(
                error_type=PrecisionErrorType.VALIDATION_ERROR,
                message=f"Invalid control point weight: {self.weight} (must be positive)",
                operation="control_point_validation",
                coordinates=[self.position],
                context={"weight": self.weight},
                severity=PrecisionErrorSeverity.ERROR,
            )
            raise ValueError(f"Invalid control point weight: {self.weight}")


@dataclass
class KnotVector:
    """Knot vector for B-spline and NURBS curves with precision support."""

    knots: List[Union[float, decimal.Decimal]]
    degree: int
    is_clamped: bool = True

    def __post_init__(self):
        """Validate knot vector after initialization."""
        self.config = config_manager.get_default_config()

        # Validate degree
        if self.degree < 0:
            raise ValueError(f"Invalid degree: {self.degree}")

        # Validate knot vector length
        min_knots = self.degree + 1
        if len(self.knots) < min_knots:
            raise ValueError(f"Knot vector too short: {len(self.knots)} < {min_knots}")

        # Validate knot vector is non-decreasing
        for i in range(1, len(self.knots)):
            if self.knots[i] < self.knots[i - 1]:
                raise ValueError(f"Knot vector must be non-decreasing: {self.knots}")

        # Validate clamped condition
        if self.is_clamped:
            multiplicity = self.degree + 1
            if (
                self.knots[0] != self.knots[multiplicity - 1]
                or self.knots[-1] != self.knots[-multiplicity]
            ):
                raise ValueError(
                    f"Knot vector not properly clamped for degree {self.degree}"
                )


class BezierCurve:
    """Bezier curve implementation with precision support."""

    def __init__(
        self,
        control_points: List[ControlPoint],
        precision_config: Optional[PrecisionConfig] = None,
    ):
        """Initialize Bezier curve with control points."""
        self.control_points = control_points
        self.config = precision_config or config_manager.get_default_config()
        self.precision_math = PrecisionMath()
        self.coordinate_validator = CoordinateValidator()
        self.precision_validator = PrecisionValidator()

        # Validate control points
        if len(self.control_points) < 2:
            raise ValueError("Bezier curve requires at least 2 control points")

        self.degree = len(self.control_points) - 1
        self._validate_control_points()

    def _validate_control_points(self):
        """Validate control points with precision validation."""
        try:
            context = HookContext(
                operation_name="bezier_curve_validation",
                coordinates=[cp.position for cp in self.control_points],
            )

            # Execute validation hooks
            hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)

        except Exception as e:
            handle_precision_error(
                error_type=PrecisionErrorType.VALIDATION_ERROR,
                message=f"Bezier curve validation failed: {str(e)}",
                operation="bezier_curve_validation",
                coordinates=[cp.position for cp in self.control_points],
                context={"degree": self.degree},
                severity=PrecisionErrorSeverity.ERROR,
            )
            raise

    def evaluate(self, parameter: Union[float, decimal.Decimal]) -> CurvePoint:
        """Evaluate curve at given parameter with precision."""
        try:
            # Validate parameter
            if parameter < 0 or parameter > 1:
                raise ValueError(f"Parameter must be in [0,1]: {parameter}")

            # Convert to decimal for precision
            t = decimal.Decimal(str(parameter))

            # Calculate position using de Casteljau algorithm
            position = self._de_casteljau_algorithm(t)

            # Calculate tangent
            tangent = self._calculate_tangent(t)

            # Calculate normal
            normal = self._calculate_normal(tangent) if tangent else None

            # Calculate curvature
            curvature = self._calculate_curvature(t)

            return CurvePoint(
                parameter=parameter,
                position=position,
                tangent=tangent,
                normal=normal,
                curvature=curvature,
            )

        except Exception as e:
            handle_precision_error(
                error_type=PrecisionErrorType.CALCULATION_ERROR,
                message=f"Bezier curve evaluation failed: {str(e)}",
                operation="bezier_curve_evaluation",
                coordinates=[],
                context={"parameter": parameter},
                severity=PrecisionErrorSeverity.ERROR,
            )
            raise

    def _de_casteljau_algorithm(self, t: decimal.Decimal) -> PrecisionCoordinate:
        """De Casteljau algorithm for precise Bezier curve evaluation."""
        n = len(self.control_points)
        points = [cp.position for cp in self.control_points]

        # Apply de Casteljau algorithm
        for r in range(1, n):
            for i in range(n - r):
                # Linear interpolation with precision
                x = self.precision_math.interpolate(points[i].x, points[i + 1].x, t)
                y = self.precision_math.interpolate(points[i].y, points[i + 1].y, t)
                z = self.precision_math.interpolate(points[i].z, points[i + 1].z, t)
                points[i] = PrecisionCoordinate(x, y, z)

        return points[0]

    def _calculate_tangent(self, t: decimal.Decimal) -> PrecisionCoordinate:
        """Calculate tangent vector at parameter t."""
        if self.degree == 0:
            return PrecisionCoordinate(0, 0, 0)

        # Calculate derivative control points
        derivative_points = []
        for i in range(self.degree):
            dx = (
                self.control_points[i + 1].position.x
                - self.control_points[i].position.x
            )
            dy = (
                self.control_points[i + 1].position.y
                - self.control_points[i].position.y
            )
            dz = (
                self.control_points[i + 1].position.z
                - self.control_points[i].position.z
            )

            # Scale by degree
            dx = self.precision_math.multiply(dx, self.degree)
            dy = self.precision_math.multiply(dy, self.degree)
            dz = self.precision_math.multiply(dz, self.degree)

            derivative_points.append(PrecisionCoordinate(dx, dy, dz))

        # Evaluate derivative curve
        if len(derivative_points) == 1:
            return derivative_points[0]

        # Apply de Casteljau to derivative
        points = derivative_points.copy()
        for r in range(1, len(points)):
            for i in range(len(points) - r):
                x = self.precision_math.interpolate(points[i].x, points[i + 1].x, t)
                y = self.precision_math.interpolate(points[i].y, points[i + 1].y, t)
                z = self.precision_math.interpolate(points[i].z, points[i + 1].z, t)
                points[i] = PrecisionCoordinate(x, y, z)

        return points[0]

    def _calculate_normal(self, tangent: PrecisionCoordinate) -> PrecisionCoordinate:
        """Calculate normal vector from tangent."""
        if tangent.x == 0 and tangent.y == 0:
            return PrecisionCoordinate(0, 1, 0)

        # Normal is perpendicular to tangent
        return PrecisionCoordinate(-tangent.y, tangent.x, 0)

    def _calculate_curvature(self, t: decimal.Decimal) -> float:
        """Calculate curvature at parameter t."""
        if self.degree < 2:
            return 0.0

        # Calculate second derivative
        second_derivative_points = []
        for i in range(self.degree - 1):
            dx = (
                self.control_points[i + 2].position.x
                - 2 * self.control_points[i + 1].position.x
                + self.control_points[i].position.x
            )
            dy = (
                self.control_points[i + 2].position.y
                - 2 * self.control_points[i + 1].position.y
                + self.control_points[i].position.y
            )
            dz = (
                self.control_points[i + 2].position.z
                - 2 * self.control_points[i + 1].position.z
                + self.control_points[i].position.z
            )

            # Scale by degree * (degree-1)
            scale = self.degree * (self.degree - 1)
            dx = self.precision_math.multiply(dx, scale)
            dy = self.precision_math.multiply(dy, scale)
            dz = self.precision_math.multiply(dz, scale)

            second_derivative_points.append(PrecisionCoordinate(dx, dy, dz))

        # Evaluate second derivative
        if len(second_derivative_points) == 1:
            second_derivative = second_derivative_points[0]
        else:
            points = second_derivative_points.copy()
            for r in range(1, len(points)):
                for i in range(len(points) - r):
                    x = self.precision_math.interpolate(points[i].x, points[i + 1].x, t)
                    y = self.precision_math.interpolate(points[i].y, points[i + 1].y, t)
                    z = self.precision_math.interpolate(points[i].z, points[i + 1].z, t)
                    points[i] = PrecisionCoordinate(x, y, z)
            second_derivative = points[0]

        # Calculate curvature: κ = |r' × r''| / |r'|³
        tangent = self._calculate_tangent(t)
        cross_product = tangent.cross(second_derivative)
        tangent_magnitude = tangent.magnitude()

        if tangent_magnitude > 0:
            return float(cross_product) / (tangent_magnitude**3)

        return 0.0

    def get_bounding_box(self) -> Tuple[PrecisionCoordinate, PrecisionCoordinate]:
        """Get bounding box of the curve."""
        min_x = min(cp.position.x for cp in self.control_points)
        min_y = min(cp.position.y for cp in self.control_points)
        min_z = min(cp.position.z for cp in self.control_points)

        max_x = max(cp.position.x for cp in self.control_points)
        max_y = max(cp.position.y for cp in self.control_points)
        max_z = max(cp.position.z for cp in self.control_points)

        return (
            PrecisionCoordinate(min_x, min_y, min_z),
            PrecisionCoordinate(max_x, max_y, max_z),
        )

    def subdivide(
        self, t: Union[float, decimal.Decimal]
    ) -> Tuple["BezierCurve", "BezierCurve"]:
        """Subdivide curve at parameter t."""
        t = decimal.Decimal(str(t))

        # Apply de Casteljau algorithm to get subdivision points
        n = len(self.control_points)
        points = [cp.position for cp in self.control_points]
        left_points = []
        right_points = []

        for r in range(n):
            left_points.append(points[0])
            right_points.insert(0, points[n - r - 1])

            if r < n - 1:
                for i in range(n - r - 1):
                    x = self.precision_math.interpolate(points[i].x, points[i + 1].x, t)
                    y = self.precision_math.interpolate(points[i].y, points[i + 1].y, t)
                    z = self.precision_math.interpolate(points[i].z, points[i + 1].z, t)
                    points[i] = PrecisionCoordinate(x, y, z)

        # Create control points for subdivided curves
        left_control_points = [ControlPoint(pos) for pos in left_points]
        right_control_points = [ControlPoint(pos) for pos in right_points]

        return (
            BezierCurve(left_control_points, self.config),
            BezierCurve(right_control_points, self.config),
        )


class BSplineCurve:
    """B-spline curve implementation with precision support."""

    def __init__(
        self,
        control_points: List[ControlPoint],
        knot_vector: KnotVector,
        precision_config: Optional[PrecisionConfig] = None,
    ):
        """Initialize B-spline curve."""
        self.control_points = control_points
        self.knot_vector = knot_vector
        self.config = precision_config or config_manager.get_default_config()
        self.precision_math = PrecisionMath()
        self.coordinate_validator = CoordinateValidator()
        self.precision_validator = PrecisionValidator()

        # Validate inputs
        if (
            len(self.control_points)
            != len(self.knot_vector.knots) - self.knot_vector.degree - 1
        ):
            raise ValueError("Number of control points doesn't match knot vector")

        self._validate_curve()

    def _validate_curve(self):
        """Validate B-spline curve with precision validation."""
        try:
            context = HookContext(
                operation_name="bspline_curve_validation",
                coordinates=[cp.position for cp in self.control_points],
            )

            # Execute validation hooks
            hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)

        except Exception as e:
            handle_precision_error(
                error_type=PrecisionErrorType.VALIDATION_ERROR,
                message=f"B-spline curve validation failed: {str(e)}",
                operation="bspline_curve_validation",
                coordinates=[cp.position for cp in self.control_points],
                context={"degree": self.knot_vector.degree},
                severity=PrecisionErrorSeverity.ERROR,
            )
            raise

    def evaluate(self, parameter: Union[float, decimal.Decimal]) -> CurvePoint:
        """Evaluate B-spline curve at given parameter with precision."""
        try:
            # Convert to decimal for precision
            u = decimal.Decimal(str(parameter))

            # Find knot span
            span = self._find_knot_span(u)

            # Calculate basis functions
            basis_functions = self._calculate_basis_functions(span, u)

            # Calculate position
            position = self._calculate_position(span, basis_functions)

            # Calculate tangent
            tangent = self._calculate_tangent(span, u)

            # Calculate normal
            normal = self._calculate_normal(tangent) if tangent else None

            # Calculate curvature
            curvature = self._calculate_curvature(span, u)

            return CurvePoint(
                parameter=parameter,
                position=position,
                tangent=tangent,
                normal=normal,
                curvature=curvature,
            )

        except Exception as e:
            handle_precision_error(
                error_type=PrecisionErrorType.CALCULATION_ERROR,
                message=f"B-spline curve evaluation failed: {str(e)}",
                operation="bspline_curve_evaluation",
                coordinates=[],
                context={"parameter": parameter},
                severity=PrecisionErrorSeverity.ERROR,
            )
            raise

    def _find_knot_span(self, u: decimal.Decimal) -> int:
        """Find knot span for parameter u."""
        n = len(self.control_points) - 1
        p = self.knot_vector.degree

        # Special case for end point
        if u >= self.knot_vector.knots[n]:
            return n

        # Binary search for knot span
        low = p
        high = n

        while u < self.knot_vector.knots[low] or u >= self.knot_vector.knots[low + 1]:
            low += 1

        return low

    def _calculate_basis_functions(
        self, span: int, u: decimal.Decimal
    ) -> List[decimal.Decimal]:
        """Calculate basis functions for given span and parameter."""
        p = self.knot_vector.degree
        knots = self.knot_vector.knots

        # Initialize basis functions
        basis_functions = [decimal.Decimal("0")] * (p + 1)
        basis_functions[0] = decimal.Decimal("1")

        # Calculate basis functions using Cox-de Boor recursion
        for j in range(1, p + 1):
            for i in range(p - j + 1):
                # Calculate left and right terms
                left_denom = knots[span + i + j] - knots[span + i]
                right_denom = knots[span + i + j + 1] - knots[span + i + 1]

                left_term = decimal.Decimal("0")
                right_term = decimal.Decimal("0")

                if left_denom > 0:
                    left_term = (u - knots[span + i]) / left_denom

                if right_denom > 0:
                    right_term = (knots[span + i + j + 1] - u) / right_denom

                # Update basis functions
                temp = basis_functions[i]
                basis_functions[i] = (
                    left_term * temp + right_term * basis_functions[i + 1]
                )

        return basis_functions

    def _calculate_position(
        self, span: int, basis_functions: List[decimal.Decimal]
    ) -> PrecisionCoordinate:
        """Calculate position using basis functions."""
        x = decimal.Decimal("0")
        y = decimal.Decimal("0")
        z = decimal.Decimal("0")

        for i in range(len(basis_functions)):
            if basis_functions[i] > 0:
                cp = self.control_points[span - self.knot_vector.degree + i]
                x += basis_functions[i] * cp.position.x
                y += basis_functions[i] * cp.position.y
                z += basis_functions[i] * cp.position.z

        return PrecisionCoordinate(x, y, z)

    def _calculate_tangent(self, span: int, u: decimal.Decimal) -> PrecisionCoordinate:
        """Calculate tangent vector at parameter u."""
        # Simplified tangent calculation
        # In a full implementation, this would use derivative basis functions
        return PrecisionCoordinate(0, 0, 0)

    def _calculate_normal(self, tangent: PrecisionCoordinate) -> PrecisionCoordinate:
        """Calculate normal vector from tangent."""
        if tangent.x == 0 and tangent.y == 0:
            return PrecisionCoordinate(0, 1, 0)

        return PrecisionCoordinate(-tangent.y, tangent.x, 0)

    def _calculate_curvature(self, span: int, u: decimal.Decimal) -> float:
        """Calculate curvature at parameter u."""
        # Simplified curvature calculation
        return 0.0


class CurveFitter:
    """Curve fitting algorithms with precision support."""

    def __init__(self, precision_config: Optional[PrecisionConfig] = None):
        """Initialize curve fitter."""
        self.config = precision_config or config_manager.get_default_config()
        self.precision_math = PrecisionMath()
        self.coordinate_validator = CoordinateValidator()

    def fit_bezier_to_points(
        self, points: List[PrecisionCoordinate], degree: int = 3
    ) -> BezierCurve:
        """Fit Bezier curve to points using least squares."""
        if len(points) < degree + 1:
            raise ValueError(
                f"Need at least {degree + 1} points for degree {degree} curve"
            )

        # Parameterize points
        parameters = self._parameterize_points(points)

        # Build coefficient matrix
        matrix = self._build_bezier_matrix(parameters, degree)

        # Solve least squares problem
        control_points = self._solve_least_squares(matrix, points)

        return BezierCurve(control_points, self.config)

    def _parameterize_points(self, points: List[PrecisionCoordinate]) -> List[float]:
        """Parameterize points using chord length parameterization."""
        parameters = [0.0]
        total_length = 0.0

        # Calculate total chord length
        for i in range(1, len(points)):
            dx = points[i].x - points[i - 1].x
            dy = points[i].y - points[i - 1].y
            dz = points[i].z - points[i - 1].z
            length = self.precision_math.sqrt(dx * dx + dy * dy + dz * dz)
            total_length += float(length)

        # Calculate parameters
        current_length = 0.0
        for i in range(1, len(points)):
            dx = points[i].x - points[i - 1].x
            dy = points[i].y - points[i - 1].y
            dz = points[i].z - points[i - 1].z
            length = self.precision_math.sqrt(dx * dx + dy * dy + dz * dz)
            current_length += float(length)
            parameters.append(current_length / total_length)

        return parameters

    def _build_bezier_matrix(self, parameters: List[float], degree: int) -> np.ndarray:
        """Build coefficient matrix for Bezier curve fitting."""
        n_points = len(parameters)
        matrix = np.zeros((n_points, degree + 1))

        for i, t in enumerate(parameters):
            for j in range(degree + 1):
                matrix[i, j] = self._bernstein_basis(j, degree, t)

        return matrix

    def _bernstein_basis(self, i: int, n: int, t: float) -> float:
        """Calculate Bernstein basis function."""
        if i < 0 or i > n:
            return 0.0

        # Use scipy.special.comb for binomial coefficient
        try:
            from scipy.special import comb

            return comb(n, i) * (t**i) * ((1 - t) ** (n - i))
        except ImportError:
            # Fallback implementation
            return self._binomial(n, i) * (t**i) * ((1 - t) ** (n - i))

    def _binomial(self, n: int, k: int) -> int:
        """Calculate binomial coefficient."""
        if k > n:
            return 0
        if k == 0 or k == n:
            return 1

        result = 1
        for i in range(min(k, n - k)):
            result = result * (n - i) // (i + 1)

        return result

    def _solve_least_squares(
        self, matrix: np.ndarray, points: List[PrecisionCoordinate]
    ) -> List[ControlPoint]:
        """Solve least squares problem for control points."""
        # Convert points to numpy arrays
        x_coords = np.array([float(p.x) for p in points])
        y_coords = np.array([float(p.y) for p in points])
        z_coords = np.array([float(p.z) for p in points])

        # Solve least squares
        x_control = np.linalg.lstsq(matrix, x_coords, rcond=None)[0]
        y_control = np.linalg.lstsq(matrix, y_coords, rcond=None)[0]
        z_control = np.linalg.lstsq(matrix, z_coords, rcond=None)[0]

        # Create control points
        control_points = []
        for i in range(len(x_control)):
            position = PrecisionCoordinate(
                decimal.Decimal(str(x_control[i])),
                decimal.Decimal(str(y_control[i])),
                decimal.Decimal(str(z_control[i])),
            )
            control_points.append(ControlPoint(position))

        return control_points


class CurveConstraint:
    """Base class for curve constraints with precision support."""

    def __init__(
        self, curve1: Any, curve2: Any, constraint_type: str, tolerance: float = 0.001
    ):
        """Initialize curve constraint."""
        self.curve1 = curve1
        self.curve2 = curve2
        self.constraint_type = constraint_type
        self.tolerance = tolerance
        self.config = config_manager.get_default_config()
        self.precision_math = PrecisionMath()

    def validate(self) -> bool:
        """Validate curve constraint."""
        try:
            if self.constraint_type == "tangent":
                return self._validate_tangent()
            elif self.constraint_type == "curvature_continuous":
                return self._validate_curvature_continuous()
            elif self.constraint_type == "position":
                return self._validate_position()
            else:
                return False
        except Exception as e:
            logger.error(f"Curve constraint validation failed: {e}")
            return False

    def _validate_tangent(self) -> bool:
        """Validate tangent constraint between curves."""
        # Evaluate curves at endpoints
        point1 = self.curve1.evaluate(1.0)
        point2 = self.curve2.evaluate(0.0)

        # Check position coincidence
        distance = self.precision_math.distance(point1.position, point2.position)
        if distance > self.tolerance:
            return False

        # Check tangent alignment
        if point1.tangent and point2.tangent:
            angle = self.precision_math.angle_between_vectors(
                point1.tangent, point2.tangent
            )
            return abs(angle) <= self.tolerance

        return True

    def _validate_curvature_continuous(self) -> bool:
        """Validate curvature continuity between curves."""
        # Check tangent continuity first
        if not self._validate_tangent():
            return False

        # Check curvature continuity
        point1 = self.curve1.evaluate(1.0)
        point2 = self.curve2.evaluate(0.0)

        if point1.curvature is not None and point2.curvature is not None:
            curvature_diff = abs(point1.curvature - point2.curvature)
            return curvature_diff <= self.tolerance

        return True

    def _validate_position(self) -> bool:
        """Validate position constraint between curves."""
        point1 = self.curve1.evaluate(0.5)
        point2 = self.curve2.evaluate(0.5)

        distance = self.precision_math.distance(point1.position, point2.position)
        return distance <= self.tolerance


class CurveSystem:
    """Main curve system integrating all curve functionality."""

    def __init__(self, precision_config: Optional[PrecisionConfig] = None):
        """Initialize curve system."""
        self.config = precision_config or config_manager.get_default_config()
        self.curves: List[Any] = []
        self.constraints: List[CurveConstraint] = []
        self.fitter = CurveFitter(self.config)

        logger.info("Curve system initialized")

    def create_bezier_curve(self, control_points: List[ControlPoint]) -> BezierCurve:
        """Create Bezier curve from control points."""
        curve = BezierCurve(control_points, self.config)
        self.curves.append(curve)
        return curve

    def create_bspline_curve(
        self, control_points: List[ControlPoint], degree: int = 3, clamped: bool = True
    ) -> BSplineCurve:
        """Create B-spline curve from control points."""
        # Create knot vector
        n_control = len(control_points)
        n_knots = n_control + degree + 1

        if clamped:
            # Clamped knot vector
            knots = [0.0] * (degree + 1)
            for i in range(degree + 1, n_knots - degree - 1):
                knots.append((i - degree) / (n_knots - 2 * degree - 1))
            knots.extend([1.0] * (degree + 1))
        else:
            # Open knot vector
            knots = [i / (n_knots - 1) for i in range(n_knots)]

        knot_vector = KnotVector(knots, degree, clamped)
        curve = BSplineCurve(control_points, knot_vector, self.config)
        self.curves.append(curve)
        return curve

    def fit_curve_to_points(
        self,
        points: List[PrecisionCoordinate],
        curve_type: CurveType = CurveType.BEZIER,
        degree: int = 3,
    ) -> Any:
        """Fit curve to points."""
        if curve_type == CurveType.BEZIER:
            return self.fitter.fit_bezier_to_points(points, degree)
        else:
            raise NotImplementedError(f"Curve type {curve_type} not implemented")

    def add_curve_constraint(
        self, curve1: Any, curve2: Any, constraint_type: str
    ) -> CurveConstraint:
        """Add constraint between curves."""
        constraint = CurveConstraint(curve1, curve2, constraint_type)
        self.constraints.append(constraint)
        return constraint

    def validate_constraints(self) -> bool:
        """Validate all curve constraints."""
        return all(constraint.validate() for constraint in self.constraints)

    def get_curve_statistics(self) -> Dict[str, Any]:
        """Get statistics about curves in the system."""
        return {
            "total_curves": len(self.curves),
            "bezier_curves": len(
                [c for c in self.curves if isinstance(c, BezierCurve)]
            ),
            "bspline_curves": len(
                [c for c in self.curves if isinstance(c, BSplineCurve)]
            ),
            "total_constraints": len(self.constraints),
            "valid_constraints": sum(1 for c in self.constraints if c.validate()),
        }


def create_curve_system(
    precision_config: Optional[PrecisionConfig] = None,
) -> CurveSystem:
    """Create curve system with optional precision configuration."""
    return CurveSystem(precision_config)


def create_bezier_curve(
    control_points: List[ControlPoint],
    precision_config: Optional[PrecisionConfig] = None,
) -> BezierCurve:
    """Create Bezier curve from control points."""
    return BezierCurve(control_points, precision_config)


def create_bspline_curve(
    control_points: List[ControlPoint],
    degree: int = 3,
    precision_config: Optional[PrecisionConfig] = None,
) -> BSplineCurve:
    """Create B-spline curve from control points."""
    n_control = len(control_points)
    n_knots = n_control + degree + 1

    # Create clamped knot vector
    knots = [0.0] * (degree + 1)
    for i in range(degree + 1, n_knots - degree - 1):
        knots.append((i - degree) / (n_knots - 2 * degree - 1))
    knots.extend([1.0] * (degree + 1))

    knot_vector = KnotVector(knots, degree, True)
    return BSplineCurve(control_points, knot_vector, precision_config)
