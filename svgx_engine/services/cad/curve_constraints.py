"""
Curve Constraints for SVGX Engine

This module provides curve-specific constraints including tangent, curvature,
position, and length constraints with precision support.

CTO Directives:
- Enterprise-grade curve constraints
- Professional CAD curve constraint functionality
- Precision curve constraint operations
- Advanced curve constraint algorithms
"""

import math
import decimal
from typing import List, Dict, Optional, Union, Tuple, Any
from dataclasses import dataclass
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


@dataclass
class CurveTangentConstraint:
    """Tangent constraint between curves with precision support."""

    def __init__(self, curve1: Any, curve2: Any, tolerance: float = 0.001):
        self.curve1 = curve1
        self.curve2 = curve2
        self.tolerance = tolerance
        self.config = config_manager.get_default_config()
        self.precision_math = PrecisionMath()

    def validate(self) -> bool:
        """Validate curve tangent constraint with precision."""
        try:
            # Evaluate curves at endpoints
            point1 = self.curve1.evaluate(1.0)
            point2 = self.curve2.evaluate(0.0)

            # Check position coincidence
            distance = self._calculate_distance(point1.position, point2.position)
            if distance > self.tolerance:
                return False

            # Check tangent alignment
            if point1.tangent and point2.tangent:
                angle = self._calculate_angle_between_vectors(
                    point1.tangent, point2.tangent
                )
                return abs(angle) <= self.tolerance

            return True
        except Exception as e:
            logger.error(f"Curve tangent constraint validation failed: {e}")
            return False

    def solve(self) -> bool:
        """Solve curve tangent constraint by adjusting curves."""
        if not self.validate():
            return self._adjust_curves()
        return True

    def _calculate_distance(self, pos1: Any, pos2: Any) -> float:
        """Calculate distance between positions."""
        if hasattr(pos1, "distance_to"):
            return float(pos1.distance_to(pos2))
        elif (
            hasattr(pos1, "x")
            and hasattr(pos1, "y")
            and hasattr(pos2, "x")
            and hasattr(pos2, "y")
        ):
            dx = pos1.x - pos2.x
            dy = pos1.y - pos2.y
            return self.precision_math.sqrt(dx * dx + dy * dy)
        return 0.0

    def _calculate_angle_between_vectors(self, vec1: Any, vec2: Any) -> float:
        """Calculate angle between vectors."""
        if hasattr(vec1, "angle_to") and hasattr(vec2, "angle_to"):
            return float(vec1.angle_to(vec2))
        else:
            # Calculate angle from dot product
            dot_product = vec1.x * vec2.x + vec1.y * vec2.y + vec1.z * vec2.z
            mag1 = self.precision_math.sqrt(
                vec1.x * vec1.x + vec1.y * vec1.y + vec1.z * vec1.z
            )
            mag2 = self.precision_math.sqrt(
                vec2.x * vec2.x + vec2.y * vec2.y + vec2.z * vec2.z
            )

            if mag1 > 0 and mag2 > 0:
                cos_angle = dot_product / (mag1 * mag2)
                cos_angle = max(-1, min(1, cos_angle))  # Clamp to [-1, 1]
                return math.acos(cos_angle)

            return 0.0

    def _adjust_curves(self) -> bool:
        """Adjust curves to satisfy tangent constraint."""
        # Simplified adjustment - real CAD systems have sophisticated curve solvers
        curve1, curve2 = self.curve1, self.curve2

        # Move second curve to match position of first curve
        point1 = curve1.evaluate(1.0)
        point2 = curve2.evaluate(0.0)

        if hasattr(curve2, "translate"):
            translation = PrecisionCoordinate(
                point1.position.x - point2.position.x,
                point1.position.y - point2.position.y,
                point1.position.z - point2.position.z,
            )
            curve2.translate(translation)
            return True

        return False


@dataclass
class CurvatureContinuousConstraint:
    """Curvature continuity constraint between curves with precision support."""

    def __init__(self, curve1: Any, curve2: Any, tolerance: float = 0.001):
        self.curve1 = curve1
        self.curve2 = curve2
        self.tolerance = tolerance
        self.config = config_manager.get_default_config()
        self.precision_math = PrecisionMath()

    def validate(self) -> bool:
        """Validate curvature continuity constraint with precision."""
        try:
            # Check tangent continuity first
            tangent_constraint = CurveTangentConstraint(
                self.curve1, self.curve2, self.tolerance
            )
            if not tangent_constraint.validate():
                return False

            # Check curvature continuity
            point1 = self.curve1.evaluate(1.0)
            point2 = self.curve2.evaluate(0.0)

            if point1.curvature is not None and point2.curvature is not None:
                curvature_diff = abs(point1.curvature - point2.curvature)
                return curvature_diff <= self.tolerance

            return True
        except Exception as e:
            logger.error(f"Curvature continuous constraint validation failed: {e}")
            return False

    def solve(self) -> bool:
        """Solve curvature continuity constraint by adjusting curves."""
        if not self.validate():
            return self._adjust_curves()
        return True

    def _adjust_curves(self) -> bool:
        """Adjust curves to satisfy curvature continuity constraint."""
        # Simplified adjustment - real CAD systems have sophisticated curve solvers
        curve1, curve2 = self.curve1, self.curve2

        # First ensure tangent continuity
        tangent_constraint = CurveTangentConstraint(curve1, curve2, self.tolerance)
        if not tangent_constraint.solve():
            return False

        # Adjust curvature (simplified)
        point1 = curve1.evaluate(1.0)
        point2 = curve2.evaluate(0.0)

        if hasattr(curve2, "adjust_curvature"):
            curve2.adjust_curvature(point1.curvature)
            return True

        return False


@dataclass
class CurvePositionConstraint:
    """Position constraint for curves with precision support."""

    def __init__(self, curve: Any, target_position: Any, tolerance: float = 0.001):
        self.curve = curve
        self.target_position = target_position
        self.tolerance = tolerance
        self.config = config_manager.get_default_config()
        self.precision_math = PrecisionMath()

    def validate(self) -> bool:
        """Validate curve position constraint with precision."""
        try:
            # Evaluate curve at midpoint
            curve_point = self.curve.evaluate(0.5)

            # Check distance to target position
            distance = self._calculate_distance(
                curve_point.position, self.target_position
            )
            return distance <= self.tolerance
        except Exception as e:
            logger.error(f"Curve position constraint validation failed: {e}")
            return False

    def solve(self) -> bool:
        """Solve curve position constraint by adjusting curve."""
        if not self.validate():
            return self._adjust_curve()
        return True

    def _calculate_distance(self, pos1: Any, pos2: Any) -> float:
        """Calculate distance between positions."""
        if hasattr(pos1, "distance_to"):
            return float(pos1.distance_to(pos2))
        elif (
            hasattr(pos1, "x")
            and hasattr(pos1, "y")
            and hasattr(pos2, "x")
            and hasattr(pos2, "y")
        ):
            dx = pos1.x - pos2.x
            dy = pos1.y - pos2.y
            return self.precision_math.sqrt(dx * dx + dy * dy)
        return 0.0

    def _adjust_curve(self) -> bool:
        """Adjust curve to satisfy position constraint."""
        if hasattr(self.curve, "translate") and self.target_position:
            current_point = self.curve.evaluate(0.5)
            translation = PrecisionCoordinate(
                self.target_position.x - current_point.position.x,
                self.target_position.y - current_point.position.y,
                self.target_position.z - current_point.position.z,
            )
            self.curve.translate(translation)
            return True

        return False


@dataclass
class CurveLengthConstraint:
    """Length constraint for curves with precision support."""

    def __init__(
        self,
        curve: Any,
        target_length: Union[float, decimal.Decimal],
        tolerance: float = 0.001,
    ):
        self.curve = curve
        self.target_length = target_length
        self.tolerance = tolerance
        self.config = config_manager.get_default_config()
        self.precision_math = PrecisionMath()

    def validate(self) -> bool:
        """Validate curve length constraint with precision."""
        try:
            # Calculate actual curve length
            actual_length = self._calculate_curve_length(self.curve)

            # Check length difference
            length_diff = abs(actual_length - float(self.target_length))
            return length_diff <= self.tolerance
        except Exception as e:
            logger.error(f"Curve length constraint validation failed: {e}")
            return False

    def solve(self) -> bool:
        """Solve curve length constraint by adjusting curve."""
        if not self.validate():
            return self._adjust_curve_length()
        return True

    def _calculate_curve_length(self, curve: Any) -> float:
        """Calculate curve length using numerical integration."""
        # Simplified length calculation using point sampling
        num_samples = 100
        total_length = 0.0

        for i in range(num_samples):
            t1 = i / num_samples
            t2 = (i + 1) / num_samples

            point1 = curve.evaluate(t1)
            point2 = curve.evaluate(t2)

            dx = point2.position.x - point1.position.x
            dy = point2.position.y - point1.position.y
            dz = point2.position.z - point1.position.z

            segment_length = self.precision_math.sqrt(dx * dx + dy * dy + dz * dz)
            total_length += float(segment_length)

        return total_length

    def _adjust_curve_length(self) -> bool:
        """Adjust curve to satisfy length constraint."""
        target_length = float(self.target_length)

        if hasattr(self.curve, "scale"):
            current_length = self._calculate_curve_length(self.curve)
            if current_length > 0:
                scale_factor = target_length / current_length
                self.curve.scale(scale_factor)
                return True

        return False
