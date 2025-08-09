"""
Constraint System for Arxos CAD Components

This module provides geometric and dimensional constraints for CAD-parity functionality.
It implements distance constraints, angle constraints, parallel and perpendicular
constraints, horizontal and vertical constraints, coincident constraints, tangent
constraints, symmetric constraints, and constraint solver and validation with precision support.
"""

import math
import decimal
from typing import List, Dict, Optional, Union, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

# Import precision system components
from svgx_engine.core.precision_coordinate import PrecisionCoordinate, CoordinateValidator
from svgx_engine.core.precision_math import PrecisionMath
from svgx_engine.core.precision_validator import PrecisionValidator, ValidationLevel, ValidationType
from svgx_engine.core.precision_config import PrecisionConfig, config_manager
from svgx_engine.core.precision_hooks import hook_manager, HookType, HookContext
from svgx_engine.core.precision_errors import handle_precision_error, PrecisionErrorType, PrecisionErrorSeverity

logger = logging.getLogger(__name__)


class ConstraintType(Enum):
    """Types of geometric and dimensional constraints."""
    # Distance constraints
    DISTANCE = "distance"
    RADIAL_DISTANCE = "radial_distance"

    # Angle constraints
    ANGLE = "angle"
    PARALLEL = "parallel"
    PERPENDICULAR = "perpendicular"
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"

    # Geometric constraints
    COINCIDENT = "coincident"
    TANGENT = "tangent"
    SYMMETRIC = "symmetric"
    EQUAL = "equal"

    # Advanced constraints
    FIXED = "fixed"
    ALIGNED = "aligned"
    OFFSET = "offset"


class ConstraintStatus(Enum):
    """Status of constraint satisfaction."""
    SATISFIED = "satisfied"
    VIOLATED = "violated"
    OVER_CONSTRAINED = "over_constrained"
    UNDER_CONSTRAINED = "under_constrained"
    INCONSISTENT = "inconsistent"


@dataclass
class Constraint:
    """Base constraint class with precision support."""
    constraint_type: ConstraintType
    entities: List[Any] = field(default_factory=list)
    parameters: Dict[str, Union[float, decimal.Decimal]] = field(default_factory=dict)
    tolerance: float = 0.001  # Precision tolerance for constraint evaluation
    status: ConstraintStatus = ConstraintStatus.SATISFIED
    is_active: bool = True

    def __post_init__(self):
        """Initialize precision components"""
        self.config = config_manager.get_default_config()
        self.precision_math = PrecisionMath()
        self.coordinate_validator = CoordinateValidator()
        self.precision_validator = PrecisionValidator()

    def validate(self) -> bool:
        """Validate constraint satisfaction with precision validation."""
        try:
            # Create hook context for constraint validation
            validation_data = {
                'constraint_type': self.constraint_type.value,
                'entity_count': len(self.entities),
                'tolerance': self.tolerance,
                'operation_type': 'constraint_validation'
            }

            context = HookContext(
                operation_name="constraint_validation",
                coordinates=[],
                constraint_data=validation_data
            )

            # Execute geometric constraint hooks
            context = hook_manager.execute_hooks(HookType.GEOMETRIC_CONSTRAINT, context)

            # Perform validation
            result = self._validate_impl()

            # Execute precision validation hooks
            hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)

            return result

        except Exception as e:
            # Handle validation error
            handle_precision_error(
                error_type=PrecisionErrorType.VALIDATION_ERROR,
                message=f"Constraint validation failed: {str(e)}",
                operation="constraint_validation",
                coordinates=[],
                context={'constraint_type': self.constraint_type.value},
                severity=PrecisionErrorSeverity.ERROR
            )
            return False

    def _validate_impl(self) -> bool:
        """Implementation of constraint validation - to be overridden"""
        raise NotImplementedError("Subclasses must implement _validate_impl()")

    def solve(self) -> bool:
        """Solve constraint by adjusting entities with precision validation."""
        try:
            # Create hook context for constraint solving
            solving_data = {
                'constraint_type': self.constraint_type.value,
                'entity_count': len(self.entities),
                'tolerance': self.tolerance,
                'operation_type': 'constraint_solving'
            }

            context = HookContext(
                operation_name="constraint_solving",
                coordinates=[],
                constraint_data=solving_data
            )

            # Execute geometric constraint hooks
            context = hook_manager.execute_hooks(HookType.GEOMETRIC_CONSTRAINT, context)

            # Perform solving
            result = self._solve_impl()

            # Execute precision validation hooks
            hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)

            return result

        except Exception as e:
            # Handle solving error
            handle_precision_error(
                error_type=PrecisionErrorType.CALCULATION_ERROR,
                message=f"Constraint solving failed: {str(e)}",
                operation="constraint_solving",
                coordinates=[],
                context={'constraint_type': self.constraint_type.value},
                severity=PrecisionErrorSeverity.ERROR
            )
            return False

    def _solve_impl(self) -> bool:
        """Implementation of constraint solving - to be overridden"""
        raise NotImplementedError("Subclasses must implement _solve_impl()")


@dataclass
class DistanceConstraint(Constraint):
    """Distance constraint between two points or entities with precision support."""

    def __init__(self, entity1: Any, entity2: Any, distance: Union[float, decimal.Decimal],
                 tolerance: float = 0.001):
        super().__init__(ConstraintType.DISTANCE, [entity1, entity2],
                        {"distance": distance}, tolerance)

    def _validate_impl(self) -> bool:
        """Validate distance constraint with precision."""
        if len(self.entities) != 2:
            return False

        entity1, entity2 = self.entities
        actual_distance = self._calculate_distance(entity1, entity2)
        target_distance = float(self.parameters["distance"])

        # Validate target distance
        if self.config.enable_geometric_validation:
            if target_distance < 0:
                handle_precision_error(
                    error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                    message=f"Invalid target distance: {target_distance} (must be non-negative)",
                    operation="distance_constraint_validation",
                    coordinates=[],
                    context={'target_distance': target_distance},
                    severity=PrecisionErrorSeverity.ERROR
                )
                return False

        difference = abs(actual_distance - target_distance)
        self.status = ConstraintStatus.SATISFIED if difference <= self.tolerance else ConstraintStatus.VIOLATED

        return self.status == ConstraintStatus.SATISFIED

    def _solve_impl(self) -> bool:
        """Solve distance constraint by adjusting entities with precision math."""
        if not self.validate():
            return self._adjust_entities()
        return True

    def _calculate_distance(self, entity1: Any, entity2: Any) -> float:
        """Calculate distance between two entities using precision math."""
        if hasattr(entity1, 'precision_position') and hasattr(entity2, 'precision_position'):
            return self.precision_math.distance(entity1.precision_position, entity2.precision_position)
        elif hasattr(entity1, 'distance_to') and hasattr(entity2, 'distance_to'):
            return float(entity1.distance_to(entity2)
        elif hasattr(entity1, 'x') and hasattr(entity1, 'y') and hasattr(entity2, 'x') and hasattr(entity2, 'y'):
            dx = entity1.x - entity2.x
            dy = entity1.y - entity2.y
            return self.precision_math.sqrt(dx * dx + dy * dy)
        else:
            return 0.0

    def _adjust_entities(self) -> bool:
        """Adjust entities to satisfy constraint using precision math."""
        # Simplified adjustment - real CAD systems have sophisticated solvers
        entity1, entity2 = self.entities
        target_distance = float(self.parameters["distance"])
        current_distance = self._calculate_distance(entity1, entity2)

        if current_distance == 0:
            return False

        # Calculate adjustment factor using precision math
        adjustment_factor = self.precision_math.divide(target_distance, current_distance)

        # Apply adjustment (simplified)
        if hasattr(entity1, 'x') and hasattr(entity1, 'y'):
            entity1.x = self.precision_math.multiply(entity1.x, adjustment_factor)
            entity1.y = self.precision_math.multiply(entity1.y, adjustment_factor)

        return True


@dataclass
class AngleConstraint(Constraint):
    """Angle constraint between two lines or vectors with precision support."""

    def __init__(self, entity1: Any, entity2: Any, angle: Union[float, decimal.Decimal],
                 tolerance: float = 0.001):
        super().__init__(ConstraintType.ANGLE, [entity1, entity2],
                        {"angle": angle}, tolerance)

    def _validate_impl(self) -> bool:
        """Validate angle constraint with precision."""
        if len(self.entities) != 2:
            return False

        entity1, entity2 = self.entities
        actual_angle = self._calculate_angle(entity1, entity2)
        target_angle = float(self.parameters["angle"])

        # Validate target angle
        if self.config.enable_geometric_validation:
            if target_angle < 0 or target_angle > 2 * math.pi:
                handle_precision_error(
                    error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                    message=f"Invalid target angle: {target_angle} (must be in [0, 2π])",
                    operation="angle_constraint_validation",
                    coordinates=[],
                    context={'target_angle': target_angle},
                    severity=PrecisionErrorSeverity.ERROR
                )
                return False

        # Normalize angles to [0, 2π]
        actual_angle = actual_angle % (2 * math.pi)
        target_angle = target_angle % (2 * math.pi)

        difference = abs(actual_angle - target_angle)
        # Handle angle wrap-around
        if difference > math.pi:
            difference = 2 * math.pi - difference

        self.status = ConstraintStatus.SATISFIED if difference <= self.tolerance else ConstraintStatus.VIOLATED

        return self.status == ConstraintStatus.SATISFIED

    def _solve_impl(self) -> bool:
        """Solve angle constraint by adjusting entities with precision math."""
        if not self.validate():
            return self._adjust_entities()
        return True

    def _calculate_angle(self, entity1: Any, entity2: Any) -> float:
        """Calculate angle between two entities using precision math."""
        if hasattr(entity1, 'angle_to') and hasattr(entity2, 'angle_to'):
            return float(entity1.angle_to(entity2)
        else:
            # Calculate angle from vectors using precision math
            vector1 = self._get_vector(entity1)
            vector2 = self._get_vector(entity2)

            if vector1 and vector2:
                return self.precision_math.angle_between_vectors(vector1, vector2)
            else:
                return 0.0

    def _get_vector(self, entity: Any) -> Optional[PrecisionCoordinate]:
        """Extract vector from entity as PrecisionCoordinate."""
        if hasattr(entity, 'dx') and hasattr(entity, 'dy'):
            return PrecisionCoordinate(entity.dx, entity.dy, 0.0)
        elif hasattr(entity, 'start') and hasattr(entity, 'end'):
            return PrecisionCoordinate(
                entity.end.x - entity.start.x,
                entity.end.y - entity.start.y,
                0.0
            )
        return None

    def _adjust_entities(self) -> bool:
        """Adjust entities to satisfy angle constraint using precision math."""
        target_angle = float(self.parameters["angle"])
        entity1, entity2 = self.entities

        # Apply rotation to second entity using precision math
        if hasattr(entity2, 'rotate'):
            entity2.rotate(target_angle)
            return True

        return False


@dataclass
class ParallelConstraint(Constraint):
    """Parallel constraint between two lines or vectors."""

    def __init__(self, entity1: Any, entity2: Any, tolerance: float = 0.001):
    """
    Perform __init__ operation

Args:
        entity1: Description of entity1
        entity2: Description of entity2
        tolerance: Description of tolerance

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        super().__init__(ConstraintType.PARALLEL, [entity1, entity2], {}, tolerance)

    def _validate_impl(self) -> bool:
        """Validate parallel constraint with precision."""
        if len(self.entities) != 2:
            return False

        entity1, entity2 = self.entities
        actual_angle = self._calculate_angle(entity1, entity2)

        # Check if angle is close to 0 or π
        normalized_angle = actual_angle % (math.pi)
        is_parallel = normalized_angle <= self.tolerance or abs(normalized_angle - math.pi) <= self.tolerance

        self.status = ConstraintStatus.SATISFIED if is_parallel else ConstraintStatus.VIOLATED

        return self.status == ConstraintStatus.SATISFIED

    def _solve_impl(self) -> bool:
        """Solve parallel constraint by adjusting entities."""
        if not self.validate():
            return self._adjust_entities()
        return True

    def _calculate_angle(self, entity1: Any, entity2: Any) -> float:
        """Calculate angle between two entities using precision math."""
        vector1 = self._get_vector(entity1)
        vector2 = self._get_vector(entity2)

        if vector1 and vector2:
            return self.precision_math.angle_between_vectors(vector1, vector2)
        return 0.0

    def _get_vector(self, entity: Any) -> Optional[PrecisionCoordinate]:
        """Extract vector from entity as PrecisionCoordinate."""
        if hasattr(entity, 'dx') and hasattr(entity, 'dy'):
            return PrecisionCoordinate(entity.dx, entity.dy, 0.0)
        elif hasattr(entity, 'start') and hasattr(entity, 'end'):
            return PrecisionCoordinate(
                entity.end.x - entity.start.x,
                entity.end.y - entity.start.y,
                0.0
            )
        return None

    def _adjust_entities(self) -> bool:
        """Adjust entities to satisfy parallel constraint."""
        entity1, entity2 = self.entities
        vector1 = self._get_vector(entity1)

        if vector1 and hasattr(entity2, 'set_direction'):
            entity2.set_direction(vector1)
            return True

        return False


@dataclass
class PerpendicularConstraint(Constraint):
    """
    Perform __init__ operation

Args:
        entity1: Description of entity1
        entity2: Description of entity2
        tolerance: Description of tolerance

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
    """Perpendicular constraint between two lines or vectors."""

    def __init__(self, entity1: Any, entity2: Any, tolerance: float = 0.001):
        super().__init__(ConstraintType.PERPENDICULAR, [entity1, entity2], {}, tolerance)

    def _validate_impl(self) -> bool:
        """Validate perpendicular constraint with precision."""
        if len(self.entities) != 2:
            return False

        entity1, entity2 = self.entities
        actual_angle = self._calculate_angle(entity1, entity2)

        # Check if angle is close to π/2 or 3π/2
        target_angle = math.pi / 2
        difference = abs(actual_angle - target_angle)
        is_perpendicular = difference <= self.tolerance or abs(difference - math.pi) <= self.tolerance

        self.status = ConstraintStatus.SATISFIED if is_perpendicular else ConstraintStatus.VIOLATED

        return self.status == ConstraintStatus.SATISFIED

    def _solve_impl(self) -> bool:
        """Solve perpendicular constraint by adjusting entities."""
        if not self.validate():
            return self._adjust_entities()
        return True

    def _calculate_angle(self, entity1: Any, entity2: Any) -> float:
        """Calculate angle between two entities using precision math."""
        vector1 = self._get_vector(entity1)
        vector2 = self._get_vector(entity2)

        if vector1 and vector2:
            return self.precision_math.angle_between_vectors(vector1, vector2)
        return 0.0

    def _get_vector(self, entity: Any) -> Optional[PrecisionCoordinate]:
        """Extract vector from entity as PrecisionCoordinate."""
        if hasattr(entity, 'dx') and hasattr(entity, 'dy'):
            return PrecisionCoordinate(entity.dx, entity.dy, 0.0)
        elif hasattr(entity, 'start') and hasattr(entity, 'end'):
            return PrecisionCoordinate(
                entity.end.x - entity.start.x,
                entity.end.y - entity.start.y,
                0.0
            )
        return None

    def _adjust_entities(self) -> bool:
        """Adjust entities to satisfy perpendicular constraint."""
        entity1, entity2 = self.entities
        vector1 = self._get_vector(entity1)

        if vector1 and hasattr(entity2, 'set_perpendicular'):
            entity2.set_perpendicular(vector1)
            return True

        return False


@dataclass
class CoincidentConstraint(Constraint):
    """Coincident constraint between two points or entities."""

    def __init__(self, entity1: Any, entity2: Any, tolerance: float = 0.001):
        super().__init__(ConstraintType.COINCIDENT, [entity1, entity2], {}, tolerance)

    def _validate_impl(self) -> bool:
        """Validate coincident constraint with precision."""
        if len(self.entities) != 2:
            return False

        entity1, entity2 = self.entities
        actual_distance = self._calculate_distance(entity1, entity2)

        self.status = ConstraintStatus.SATISFIED if actual_distance <= self.tolerance else ConstraintStatus.VIOLATED

        return self.status == ConstraintStatus.SATISFIED

    def _solve_impl(self) -> bool:
        """Solve coincident constraint by adjusting entities."""
        if not self.validate():
            return self._adjust_entities()
        return True

    def _calculate_distance(self, entity1: Any, entity2: Any) -> float:
        """Calculate distance between two entities using precision math."""
        if hasattr(entity1, 'distance_to'):
            return float(entity1.distance_to(entity2)
        elif hasattr(entity1, 'x') and hasattr(entity1, 'y') and hasattr(entity2, 'x') and hasattr(entity2, 'y'):
            dx = entity1.x - entity2.x
            dy = entity1.y - entity2.y
            return self.precision_math.sqrt(dx * dx + dy * dy)
        return 0.0

    def _adjust_entities(self) -> bool:
        """Adjust entities to satisfy coincident constraint."""
        entity1, entity2 = self.entities

        # Move second entity to first entity's position'
        if hasattr(entity1, 'x') and hasattr(entity1, 'y') and hasattr(entity2, 'set_position'):
            entity2.set_position(entity1.x, entity1.y)
            return True

        return False


@dataclass
class TangentConstraint(Constraint):
    """Tangent constraint between two curves or circles."""

    def __init__(self, entity1: Any, entity2: Any, tolerance: float = 0.001):
        super().__init__(ConstraintType.TANGENT, [entity1, entity2], {}, tolerance)

    def _validate_impl(self) -> bool:
        """Validate tangent constraint with precision."""
        if len(self.entities) != 2:
            return False

        entity1, entity2 = self.entities
        actual_distance = self._calculate_tangent_distance(entity1, entity2)

        self.status = ConstraintStatus.SATISFIED if actual_distance <= self.tolerance else ConstraintStatus.VIOLATED

        return self.status == ConstraintStatus.SATISFIED

    def _solve_impl(self) -> bool:
        """Solve tangent constraint by adjusting entities."""
        if not self.validate():
            return self._adjust_entities()
        return True

    def _calculate_tangent_distance(self, entity1: Any, entity2: Any) -> float:
        """Calculate distance for tangent constraint."""
        # Simplified calculation - real CAD systems have complex curve intersection
        if hasattr(entity1, 'radius') and hasattr(entity2, 'radius'):
            # For circles
            center_distance = self._calculate_distance(entity1, entity2)
            radius_sum = entity1.radius + entity2.radius
            return abs(center_distance - radius_sum)
        else:
            # For other curves, use minimum distance
            return self._calculate_distance(entity1, entity2)

    def _calculate_distance(self, entity1: Any, entity2: Any) -> float:
        """Calculate distance between two entities using precision math."""
        if hasattr(entity1, 'distance_to'):
            return float(entity1.distance_to(entity2)
        elif hasattr(entity1, 'x') and hasattr(entity1, 'y') and hasattr(entity2, 'x') and hasattr(entity2, 'y'):
            dx = entity1.x - entity2.x
            dy = entity1.y - entity2.y
            return self.precision_math.sqrt(dx * dx + dy * dy)
        return 0.0

    def _adjust_entities(self) -> bool:
        """Adjust entities to satisfy tangent constraint."""
        # Simplified adjustment - real CAD systems have sophisticated solvers
        entity1, entity2 = self.entities

        if hasattr(entity1, 'radius') and hasattr(entity2, 'radius'):
            # For circles, adjust position to make them tangent
            radius_sum = entity1.radius + entity2.radius
            if hasattr(entity2, 'set_position'):
                # Move second entity to tangent position
                direction = self._get_direction(entity1, entity2)
                if direction:
                    new_x = entity1.x + direction.dx * radius_sum
                    new_y = entity1.y + direction.dy * radius_sum
                    entity2.set_position(new_x, new_y)
                    return True

        return False

    def _get_direction(self, entity1: Any, entity2: Any) -> Optional[PrecisionCoordinate]:
        """Get direction vector between entities."""
        if hasattr(entity1, 'x') and hasattr(entity1, 'y') and hasattr(entity2, 'x') and hasattr(entity2, 'y'):
            dx = entity2.x - entity1.x
            dy = entity2.y - entity1.y
            magnitude = self.precision_math.sqrt(dx * dx + dy * dy)
            if magnitude > 0:
                return PrecisionCoordinate(dx / magnitude, dy / magnitude, 0.0)
        return None


@dataclass
class SymmetricConstraint(Constraint):
    """Symmetric constraint between two entities about a line or point."""

    def __init__(self, entity1: Any, entity2: Any, symmetry_line: Any,
                 tolerance: float = 0.001):
        super().__init__(ConstraintType.SYMMETRIC, [entity1, entity2, symmetry_line], {}, tolerance)

    def _validate_impl(self) -> bool:
        """Validate symmetric constraint with precision."""
        if len(self.entities) != 3:
            return False

        entity1, entity2, symmetry_line = self.entities
        is_symmetric = self._check_symmetry(entity1, entity2, symmetry_line)

        self.status = ConstraintStatus.SATISFIED if is_symmetric else ConstraintStatus.VIOLATED

        return self.status == ConstraintStatus.SATISFIED

    def _solve_impl(self) -> bool:
        """Solve symmetric constraint by adjusting entities."""
        if not self.validate():
            return self._adjust_entities()
        return True

    def _check_symmetry(self, entity1: Any, entity2: Any, symmetry_line: Any) -> bool:
        """Check if entities are symmetric about the symmetry line."""
        # Simplified symmetry check - real CAD systems have complex symmetry detection
        if hasattr(entity1, 'x') and hasattr(entity1, 'y') and hasattr(entity2, 'x') and hasattr(entity2, 'y'):
            # Check if points are symmetric about line
            mid_point = PrecisionCoordinate(
                (entity1.x + entity2.x) / 2,
                (entity1.y + entity2.y) / 2,
                0.0
            )

            # Check if mid-point lies on symmetry line
            distance_to_line = self._distance_to_line(mid_point, symmetry_line)
            return distance_to_line <= self.tolerance

        return False

    def _distance_to_line(self, point: PrecisionCoordinate, line: Any) -> float:
        """Calculate distance from point to line."""
        # Simplified line distance calculation
        if hasattr(line, 'start') and hasattr(line, 'end'):
            # Line defined by start and end points
            line_vector = PrecisionCoordinate(
                line.end.x - line.start.x,
                line.end.y - line.start.y,
                0.0
            )
            point_vector = PrecisionCoordinate(
                point.x - line.start.x,
                point.y - line.start.y,
                0.0
            )

            # Distance = |point_vector × line_vector| / |line_vector|
            cross_product = point_vector.cross(line_vector)
            line_magnitude = line_vector.magnitude()

            if line_magnitude > 0:
                return abs(cross_product) / line_magnitude

        return 0.0

    def _adjust_entities(self) -> bool:
        """Adjust entities to satisfy symmetric constraint."""
        entity1, entity2, symmetry_line = self.entities

        # Calculate symmetric position of entity1
        if hasattr(entity1, 'x') and hasattr(entity1, 'y') and hasattr(entity2, 'set_position'):
            symmetric_position = self._calculate_symmetric_position(entity1, symmetry_line)
            if symmetric_position:
                entity2.set_position(symmetric_position.x, symmetric_position.y)
                return True

        return False

    def _calculate_symmetric_position(self, entity: Any, symmetry_line: Any) -> Optional[PrecisionCoordinate]:
        """Calculate symmetric position of entity about symmetry line."""
        # Simplified symmetry calculation - real CAD systems have complex symmetry algorithms
        if hasattr(entity, 'x') and hasattr(entity, 'y') and hasattr(symmetry_line, 'start') and hasattr(symmetry_line, 'end'):
            # Reflect point about line
            line_start = PrecisionCoordinate(symmetry_line.start.x, symmetry_line.start.y, 0.0)
            line_end = PrecisionCoordinate(symmetry_line.end.x, symmetry_line.end.y, 0.0)
            point = PrecisionCoordinate(entity.x, entity.y, 0.0)

            # Calculate reflection
            line_vector = PrecisionCoordinate(line_end.x - line_start.x, line_end.y - line_start.y, 0.0)
            point_vector = PrecisionCoordinate(point.x - line_start.x, point.y - line_start.y, 0.0)

            # Project point onto line
            line_magnitude_sq = line_vector.dx * line_vector.dx + line_vector.dy * line_vector.dy
            if line_magnitude_sq > 0:
                projection = point_vector.dot(line_vector) / line_magnitude_sq
                projected_point = PrecisionCoordinate(
                    line_start.x + projection * line_vector.dx,
                    line_start.y + projection * line_vector.dy,
                    0.0
                )

                # Calculate reflection
                reflection_vector = PrecisionCoordinate(
                    projected_point.x - point.x,
                    projected_point.y - point.y,
                    0.0
                )

                reflected_point = PrecisionCoordinate(
                    projected_point.x + reflection_vector.dx,
                    projected_point.y + reflection_vector.dy,
                    0.0
                )

                return reflected_point

        return None


class ConstraintSolver:
    """
    Constraint solver for geometric constraints with precision support.

    Provides comprehensive constraint solving capabilities including:
    - Precision-aware constraint solving
    - Iterative constraint resolution
    - Constraint validation and error handling
    - Precision validation hooks integration
    """

    def __init__(self, config: Optional[PrecisionConfig] = None):
        self.config = config or config_manager.get_default_config()
        self.precision_math = PrecisionMath()
        self.coordinate_validator = CoordinateValidator()
        self.precision_validator = PrecisionValidator()

        self.constraints: List[Constraint] = []
        self.entities: Dict[str, Any] = {}
        self.max_iterations = 100
        self.convergence_tolerance = 0.001

        logger.info("Precision-aware constraint solver initialized")

    def add_constraint(self, constraint: Constraint):
        """Add constraint to solver with precision validation"""
        try:
            # Create hook context for constraint addition
            addition_data = {
                'constraint_type': constraint.constraint_type.value,
                'entity_count': len(constraint.entities),
                'operation_type': 'constraint_addition'
            }

            context = HookContext(
                operation_name="constraint_addition",
                coordinates=[],
                constraint_data=addition_data
            )

            # Execute geometric constraint hooks
            context = hook_manager.execute_hooks(HookType.GEOMETRIC_CONSTRAINT, context)

            # Validate constraint
            if constraint.validate():
                self.constraints.append(constraint)
                logger.info(f"Added precision constraint: {constraint.constraint_type.value}")

                # Execute precision validation hooks
                hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)

            else:
                logger.error(f"Invalid precision constraint: {constraint.constraint_type.value}")

        except Exception as e:
            # Handle constraint addition error
            handle_precision_error(
                error_type=PrecisionErrorType.VALIDATION_ERROR,
                message=f"Constraint addition failed: {str(e)}",
                operation="constraint_addition",
                coordinates=[],
                context={'constraint_type': constraint.constraint_type.value},
                severity=PrecisionErrorSeverity.ERROR
            )

    def remove_constraint(self, constraint: Constraint):
        """Remove constraint from solver"""
        if constraint in self.constraints:
            self.constraints.remove(constraint)
            logger.info(f"Removed precision constraint: {constraint.constraint_type.value}")

    def solve_all(self) -> bool:
        """Solve all constraints with precision validation"""
        try:
            logger.info(f"Solving {len(self.constraints)} precision constraints")

            # Create hook context for constraint solving
            solving_data = {
                'constraint_count': len(self.constraints),
                'entity_count': len(self.entities),
                'max_iterations': self.max_iterations,
                'convergence_tolerance': self.convergence_tolerance,
                'operation_type': 'constraint_solving'
            }

            context = HookContext(
                operation_name="constraint_solving",
                coordinates=[],
                constraint_data=solving_data
            )

            # Execute geometric constraint hooks
            context = hook_manager.execute_hooks(HookType.GEOMETRIC_CONSTRAINT, context)

            # Iterative constraint solving with precision
            for iteration in range(self.max_iterations):
                total_error = 0.0
                constraints_satisfied = 0

                for constraint in self.constraints:
                    if constraint.is_active and constraint.solve():
                        error = self._calculate_violation(constraint)
                        total_error += abs(error)

                        if error <= self.convergence_tolerance:
                            constraint.status = ConstraintStatus.SATISFIED
                            constraints_satisfied += 1
                        else:
                            constraint.status = ConstraintStatus.VIOLATED
                    else:
                        constraint.status = ConstraintStatus.VIOLATED

                # Check convergence
                if constraints_satisfied == len(self.constraints):
                    logger.info(f"All precision constraints satisfied after {iteration + 1} iterations")

                    # Execute precision validation hooks
                    hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)

                    return True

                if total_error < self.convergence_tolerance:
                    logger.info(f"Precision constraints converged after {iteration + 1} iterations")

                    # Execute precision validation hooks
                    hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)

                    return True

            logger.warning(f"Precision constraint solving did not converge after {self.max_iterations} iterations")
            return False

        except Exception as e:
            # Handle constraint solving error
            handle_precision_error(
                error_type=PrecisionErrorType.CALCULATION_ERROR,
                message=f"Precision constraint solving failed: {str(e)}",
                operation="constraint_solving",
                coordinates=[],
                context={'constraint_count': len(self.constraints)},
                severity=PrecisionErrorSeverity.ERROR
            )
            return False

    def _calculate_violation(self, constraint: Constraint) -> float:
        """Calculate constraint violation using precision math"""
        try:
            if constraint.constraint_type == ConstraintType.DISTANCE:
                return self._calculate_distance_violation(constraint)
            elif constraint.constraint_type == ConstraintType.ANGLE:
                return self._calculate_angle_violation(constraint)
            elif constraint.constraint_type == ConstraintType.PARALLEL:
                return self._calculate_parallel_violation(constraint)
            elif constraint.constraint_type == ConstraintType.PERPENDICULAR:
                return self._calculate_perpendicular_violation(constraint)
            else:
                return 0.0

        except Exception as e:
            # Handle violation calculation error
            handle_precision_error(
                error_type=PrecisionErrorType.CALCULATION_ERROR,
                message=f"Violation calculation failed: {str(e)}",
                operation="violation_calculation",
                coordinates=[],
                context={'constraint_type': constraint.constraint_type.value},
                severity=PrecisionErrorSeverity.ERROR
            )
            return float('inf')

    def _calculate_distance_violation(self, constraint: Constraint) -> float:
        """Calculate distance constraint violation using precision math"""
        if len(constraint.entities) != 2:
            return float('inf')

        entity1, entity2 = constraint.entities
        actual_distance = self._calculate_distance(entity1, entity2)
        target_distance = float(constraint.parameters.get('distance', 0.0)
        return abs(actual_distance - target_distance)

    def _calculate_angle_violation(self, constraint: Constraint) -> float:
        """Calculate angle constraint violation using precision math"""
        if len(constraint.entities) != 2:
            return float('inf')

        entity1, entity2 = constraint.entities
        actual_angle = self._calculate_angle(entity1, entity2)
        target_angle = float(constraint.parameters.get('angle', 0.0)
        # Normalize angles and handle wrap-around
        actual_angle = actual_angle % (2 * math.pi)
        target_angle = target_angle % (2 * math.pi)

        difference = abs(actual_angle - target_angle)
        if difference > math.pi:
            difference = 2 * math.pi - difference

        return difference

    def _calculate_parallel_violation(self, constraint: Constraint) -> float:
        """Calculate parallel constraint violation using precision math"""
        if len(constraint.entities) != 2:
            return float('inf')

        entity1, entity2 = constraint.entities
        angle = self._calculate_angle(entity1, entity2)

        # Check if angle is close to 0 or π
        normalized_angle = angle % math.pi
        return min(normalized_angle, abs(normalized_angle - math.pi)
    def _calculate_perpendicular_violation(self, constraint: Constraint) -> float:
        """Calculate perpendicular constraint violation using precision math"""
        if len(constraint.entities) != 2:
            return float('inf')

        entity1, entity2 = constraint.entities
        angle = self._calculate_angle(entity1, entity2)

        # Check if angle is close to π/2 or 3π/2
        target_angle = math.pi / 2
        difference = abs(angle - target_angle)
        return min(difference, abs(difference - math.pi)
    def _calculate_distance(self, entity1: Any, entity2: Any) -> float:
        """Calculate distance between two entities using precision math"""
        if hasattr(entity1, 'precision_position') and hasattr(entity2, 'precision_position'):
            return self.precision_math.distance(entity1.precision_position, entity2.precision_position)
        elif hasattr(entity1, 'distance_to') and hasattr(entity2, 'distance_to'):
            return float(entity1.distance_to(entity2)
        elif hasattr(entity1, 'x') and hasattr(entity1, 'y') and hasattr(entity2, 'x') and hasattr(entity2, 'y'):
            dx = entity1.x - entity2.x
            dy = entity1.y - entity2.y
            return self.precision_math.sqrt(dx * dx + dy * dy)
        else:
            return 0.0

    def _calculate_angle(self, entity1: Any, entity2: Any) -> float:
        """Calculate angle between two entities using precision math"""
        if hasattr(entity1, 'angle_to') and hasattr(entity2, 'angle_to'):
            return float(entity1.angle_to(entity2)
        else:
            # Calculate angle from vectors using precision math
            vector1 = self._get_vector(entity1)
            vector2 = self._get_vector(entity2)

            if vector1 and vector2:
                return self.precision_math.angle_between_vectors(vector1, vector2)
            else:
                return 0.0

    def _get_vector(self, entity: Any) -> Optional[PrecisionCoordinate]:
        """Extract vector from entity as PrecisionCoordinate"""
        if hasattr(entity, 'dx') and hasattr(entity, 'dy'):
            return PrecisionCoordinate(entity.dx, entity.dy, 0.0)
        elif hasattr(entity, 'start') and hasattr(entity, 'end'):
            return PrecisionCoordinate(
                entity.end.x - entity.start.x,
                entity.end.y - entity.start.y,
                0.0
            )
        return None

    def get_constraint_status(self) -> Dict[str, Any]:
        """Get constraint solver status with precision information"""
        status_counts = {}
        for status in ConstraintStatus:
            status_counts[status.value] = 0

        for constraint in self.constraints:
            status_counts[constraint.status.value] += 1

        return {
            'total_constraints': len(self.constraints),
            'status_counts': status_counts,
            'total_entities': len(self.entities),
            'precision_tolerance': self.convergence_tolerance,
            'max_iterations': self.max_iterations
        }


class ConstraintSystem:
    """
    Complete constraint system for CAD geometry with precision support.

    Provides comprehensive constraint management including:
    - Precision-aware constraint creation and management
    - Constraint solving and validation with precision math
    - Constraint status monitoring with precision validation
    - Constraint visualization with precision feedback
    """

    def __init__(self, config: Optional[PrecisionConfig] = None):
        self.config = config or config_manager.get_default_config()
        self.solver = ConstraintSolver(self.config)
        self.constraints: List[Constraint] = []
        self.constraint_factory = ConstraintFactory()

        logger.info("Precision constraint system initialized")

    def add_distance_constraint(self, entity1: Any, entity2: Any,
                               distance: Union[float, decimal.Decimal]) -> DistanceConstraint:
        """Add a distance constraint with precision validation"""
        try:
            constraint = DistanceConstraint(entity1, entity2, distance)
            self.constraints.append(constraint)
            self.solver.add_constraint(constraint)

            logger.info(f"Added precision distance constraint: {distance}")
            return constraint

        except Exception as e:
            # Handle constraint creation error
            handle_precision_error(
                error_type=PrecisionErrorType.VALIDATION_ERROR,
                message=f"Distance constraint creation failed: {str(e)}",
                operation="distance_constraint_creation",
                coordinates=[],
                context={'distance': distance},
                severity=PrecisionErrorSeverity.ERROR
            )
            raise

    def add_angle_constraint(self, entity1: Any, entity2: Any,
                            angle: Union[float, decimal.Decimal]) -> AngleConstraint:
        """Add an angle constraint with precision validation"""
        try:
            constraint = AngleConstraint(entity1, entity2, angle)
            self.constraints.append(constraint)
            self.solver.add_constraint(constraint)

            logger.info(f"Added precision angle constraint: {angle}")
            return constraint

        except Exception as e:
            # Handle constraint creation error
            handle_precision_error(
                error_type=PrecisionErrorType.VALIDATION_ERROR,
                message=f"Angle constraint creation failed: {str(e)}",
                operation="angle_constraint_creation",
                coordinates=[],
                context={'angle': angle},
                severity=PrecisionErrorSeverity.ERROR
            )
            raise

    def add_parallel_constraint(self, entity1: Any, entity2: Any) -> ParallelConstraint:
        """Add a parallel constraint with precision validation"""
        try:
            constraint = ParallelConstraint(entity1, entity2)
            self.constraints.append(constraint)
            self.solver.add_constraint(constraint)

            logger.info("Added precision parallel constraint")
            return constraint

        except Exception as e:
            # Handle constraint creation error
            handle_precision_error(
                error_type=PrecisionErrorType.VALIDATION_ERROR,
                message=f"Parallel constraint creation failed: {str(e)}",
                operation="parallel_constraint_creation",
                coordinates=[],
                context={},
                severity=PrecisionErrorSeverity.ERROR
            )
            raise

    def add_perpendicular_constraint(self, entity1: Any, entity2: Any) -> PerpendicularConstraint:
        """Add a perpendicular constraint with precision validation"""
        try:
            constraint = PerpendicularConstraint(entity1, entity2)
            self.constraints.append(constraint)
            self.solver.add_constraint(constraint)

            logger.info("Added precision perpendicular constraint")
            return constraint

        except Exception as e:
            # Handle constraint creation error
            handle_precision_error(
                error_type=PrecisionErrorType.VALIDATION_ERROR,
                message=f"Perpendicular constraint creation failed: {str(e)}",
                operation="perpendicular_constraint_creation",
                coordinates=[],
                context={},
                severity=PrecisionErrorSeverity.ERROR
            )
            raise

    def add_coincident_constraint(self, entity1: Any, entity2: Any) -> CoincidentConstraint:
        """Add a coincident constraint with precision validation"""
        try:
            constraint = CoincidentConstraint(entity1, entity2)
            self.constraints.append(constraint)
            self.solver.add_constraint(constraint)

            logger.info("Added precision coincident constraint")
            return constraint

        except Exception as e:
            # Handle constraint creation error
            handle_precision_error(
                error_type=PrecisionErrorType.VALIDATION_ERROR,
                message=f"Coincident constraint creation failed: {str(e)}",
                operation="coincident_constraint_creation",
                coordinates=[],
                context={},
                severity=PrecisionErrorSeverity.ERROR
            )
            raise

    def add_tangent_constraint(self, entity1: Any, entity2: Any) -> TangentConstraint:
        """Add a tangent constraint with precision validation"""
        try:
            constraint = TangentConstraint(entity1, entity2)
            self.constraints.append(constraint)
            self.solver.add_constraint(constraint)

            logger.info("Added precision tangent constraint")
            return constraint

        except Exception as e:
            # Handle constraint creation error
            handle_precision_error(
                error_type=PrecisionErrorType.VALIDATION_ERROR,
                message=f"Tangent constraint creation failed: {str(e)}",
                operation="tangent_constraint_creation",
                coordinates=[],
                context={},
                severity=PrecisionErrorSeverity.ERROR
            )
            raise

    def add_symmetric_constraint(self, entity1: Any, entity2: Any,
                                symmetry_line: Any) -> SymmetricConstraint:
        """Add a symmetric constraint with precision validation"""
        try:
            constraint = SymmetricConstraint(entity1, entity2, symmetry_line)
            self.constraints.append(constraint)
            self.solver.add_constraint(constraint)

            logger.info("Added precision symmetric constraint")
            return constraint

        except Exception as e:
            # Handle constraint creation error
            handle_precision_error(
                error_type=PrecisionErrorType.VALIDATION_ERROR,
                message=f"Symmetric constraint creation failed: {str(e)}",
                operation="symmetric_constraint_creation",
                coordinates=[],
                context={},
                severity=PrecisionErrorSeverity.ERROR
            )
            raise

    def solve_constraints(self) -> bool:
        """Solve all constraints with precision validation"""
        return self.solver.solve_all()

    def validate_constraints(self) -> bool:
        """Validate all constraints with precision validation"""
        try:
            # Create hook context for constraint validation
            validation_data = {
                'constraint_count': len(self.constraints),
                'operation_type': 'constraint_validation'
            }

            context = HookContext(
                operation_name="constraint_validation",
                coordinates=[],
                constraint_data=validation_data
            )

            # Execute geometric constraint hooks
            context = hook_manager.execute_hooks(HookType.GEOMETRIC_CONSTRAINT, context)

            # Validate all constraints
            for constraint in self.constraints:
                if not constraint.validate():
                    logger.error(f"Invalid precision constraint: {constraint.constraint_type.value}")
                    return False

            # Execute precision validation hooks
            hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)

            logger.info("All precision constraints validated successfully")
            return True

        except Exception as e:
            # Handle validation error
            handle_precision_error(
                error_type=PrecisionErrorType.VALIDATION_ERROR,
                message=f"Constraint validation failed: {str(e)}",
                operation="constraint_validation",
                coordinates=[],
                context={'constraint_count': len(self.constraints)},
                severity=PrecisionErrorSeverity.ERROR
            )
            return False

    def get_constraint_status(self) -> Dict[str, Any]:
        """Get constraint system status with precision information"""
        return self.solver.get_constraint_status()

    def remove_constraint(self, constraint: Constraint):
        """Remove constraint from system"""
        if constraint in self.constraints:
            self.constraints.remove(constraint)
            self.solver.remove_constraint(constraint)
            logger.info(f"Removed precision constraint: {constraint.constraint_type.value}")


class ConstraintFactory:
    """Factory for creating constraints with precision support"""

    def create_constraint(self, constraint_type: ConstraintType,
                         entities: List[Any], **kwargs) -> Constraint:
        """Create constraint by type with precision validation"""
        try:
            if constraint_type == ConstraintType.DISTANCE:
                if len(entities) != 2:
                    raise ValueError("Distance constraint requires exactly 2 entities")
                distance = kwargs.get('distance', 0.0)
                return DistanceConstraint(entities[0], entities[1], distance)

            elif constraint_type == ConstraintType.ANGLE:
                if len(entities) != 2:
                    raise ValueError("Angle constraint requires exactly 2 entities")
                angle = kwargs.get('angle', 0.0)
                return AngleConstraint(entities[0], entities[1], angle)

            elif constraint_type == ConstraintType.PARALLEL:
                if len(entities) != 2:
                    raise ValueError("Parallel constraint requires exactly 2 entities")
                return ParallelConstraint(entities[0], entities[1])

            elif constraint_type == ConstraintType.PERPENDICULAR:
                if len(entities) != 2:
                    raise ValueError("Perpendicular constraint requires exactly 2 entities")
                return PerpendicularConstraint(entities[0], entities[1])

            elif constraint_type == ConstraintType.COINCIDENT:
                if len(entities) != 2:
                    raise ValueError("Coincident constraint requires exactly 2 entities")
                return CoincidentConstraint(entities[0], entities[1])

            elif constraint_type == ConstraintType.TANGENT:
                if len(entities) != 2:
                    raise ValueError("Tangent constraint requires exactly 2 entities")
                return TangentConstraint(entities[0], entities[1])

            elif constraint_type == ConstraintType.SYMMETRIC:
                if len(entities) != 3:
                    raise ValueError("Symmetric constraint requires exactly 3 entities")
                return SymmetricConstraint(entities[0], entities[1], entities[2])

            else:
                raise ValueError(f"Unknown constraint type: {constraint_type}")

        except Exception as e:
            # Handle constraint creation error
            handle_precision_error(
                error_type=PrecisionErrorType.VALIDATION_ERROR,
                message=f"Constraint factory creation failed: {str(e)}",
                operation="constraint_factory_creation",
                coordinates=[],
                context={'constraint_type': constraint_type.value},
                severity=PrecisionErrorSeverity.ERROR
            )
            raise


def create_constraint_system(config: Optional[PrecisionConfig] = None) -> ConstraintSystem:
    """Create a precision-aware constraint system"""
    return ConstraintSystem(config)


def create_constraint_solver(config: Optional[PrecisionConfig] = None) -> ConstraintSolver:
    """Create a precision-aware constraint solver"""
    return ConstraintSolver(config)
