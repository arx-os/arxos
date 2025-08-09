"""
Precision Validation Hooks System

This module provides precision validation hooks that integrate with all coordinate
creation points, transformation operations, and geometric constraint operations.
It ensures sub-millimeter precision (0.001mm) is maintained throughout the CAD workflow.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import logging
import functools
from typing import Callable, Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from decimal import Decimal
import time

from .precision_validator import PrecisionValidator, ValidationResult, ValidationLevel, ValidationType
from .precision_coordinate import PrecisionCoordinate
from .precision_math import PrecisionMath
from .precision_config import PrecisionConfig, config_manager

logger = logging.getLogger(__name__)


class HookType(Enum):
    """Types of precision validation hooks."""
    COORDINATE_CREATION = "coordinate_creation"
    COORDINATE_TRANSFORMATION = "coordinate_transformation"
    GEOMETRIC_CONSTRAINT = "geometric_constraint"
    PRECISION_VALIDATION = "precision_validation"
    ERROR_HANDLING = "error_handling"
    RECOVERY_MECHANISM = "recovery_mechanism"


@dataclass
class PrecisionHook:
    """Precision validation hook definition."""
    hook_id: str
    hook_type: HookType
    function: Callable
    priority: int = 0
    enabled: bool = True
    description: str = ""
    validation_level: ValidationLevel = ValidationLevel.CRITICAL
    error_handling: bool = True
    recovery_enabled: bool = True


@dataclass
class HookContext:
    """Context information for precision hooks."""
    operation_name: str
    coordinates: List[PrecisionCoordinate]
    transformation_data: Optional[Dict[str, Any]] = None
    constraint_data: Optional[Dict[str, Any]] = None
    precision_config: Optional[PrecisionConfig] = None
    validation_results: List[ValidationResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    execution_time: float = 0.0


class PrecisionHookManager:
    """Manager for precision validation hooks."""

    def __init__(self, config: Optional[PrecisionConfig] = None):
        """Initialize precision hook manager."""
        self.config = config or config_manager.get_default_config()
        self.hooks: Dict[HookType, List[PrecisionHook]] = {
            hook_type: [] for hook_type in HookType
        }
        self.precision_validator = PrecisionValidator()
        self.precision_math = PrecisionMath()
        self.logger = logging.getLogger(__name__)

        # Register default hooks
        self._register_default_hooks()

    def register_hook(self, hook: PrecisionHook) -> None:
        """Register a precision validation hook."""
        if hook.hook_type not in self.hooks:
            self.hooks[hook.hook_type] = []

        # Insert hook based on priority (higher priority first)
        hooks = self.hooks[hook.hook_type]
        for i, existing_hook in enumerate(hooks):
            if hook.priority > existing_hook.priority:
                hooks.insert(i, hook)
                break
        else:
            hooks.append(hook)

        self.logger.info(f"Registered precision hook: {hook.hook_id} ({hook.hook_type.value})")

    def unregister_hook(self, hook_id: str) -> bool:
        """Unregister a precision validation hook."""
        for hook_type, hooks in self.hooks.items():
            for i, hook in enumerate(hooks):
                if hook.hook_id == hook_id:
                    hooks.pop(i)
                    self.logger.info(f"Unregistered precision hook: {hook_id}")
                    return True
        return False

    def execute_hooks(self, hook_type: HookType, context: HookContext) -> HookContext:
        """Execute all hooks of a specific type."""
        start_time = time.time()

        if hook_type not in self.hooks:
            return context

        for hook in self.hooks[hook_type]:
            if not hook.enabled:
                continue

            try:
                # Execute hook
                hook_result = hook.function(context)
                if hook_result:
                    context = hook_result

                # Validate results if validation is enabled
                if hook.validation_level != ValidationLevel.DEBUG:
                    validation_result = self._validate_hook_result(hook, context)
                    if validation_result:
                        context.validation_results.append(validation_result)

            except Exception as e:
                error_msg = f"Hook {hook.hook_id} failed: {str(e)}"
                context.errors.append(error_msg)
                self.logger.error(error_msg, exc_info=True)

                # Execute error handling if enabled
                if hook.error_handling:
                    self._handle_hook_error(hook, context, e)

                # Execute recovery mechanism if enabled
                if hook.recovery_enabled:
                    self._execute_recovery_mechanism(hook, context, e)

        context.execution_time = time.time() - start_time
        return context

    def _validate_hook_result(self, hook: PrecisionHook, context: HookContext) -> Optional[ValidationResult]:
        """Validate hook execution result."""
        try:
            # Basic validation based on hook type
            if hook.hook_type == HookType.COORDINATE_CREATION:
                return self._validate_coordinate_creation(context)
            elif hook.hook_type == HookType.COORDINATE_TRANSFORMATION:
                return self._validate_coordinate_transformation(context)
            elif hook.hook_type == HookType.GEOMETRIC_CONSTRAINT:
                return self._validate_geometric_constraint(context)
            elif hook.hook_type == HookType.PRECISION_VALIDATION:
                return self._validate_precision_validation(context)

        except Exception as e:
            self.logger.error(f"Validation failed for hook {hook.hook_id}: {e}")

        return None

    def _validate_coordinate_creation(self, context: HookContext) -> ValidationResult:
        """Validate coordinate creation results."""
        validation_results = []

        for coord in context.coordinates:
            # Validate coordinate range
            if not self.precision_validator._validate_coordinate_range(coord):
                validation_results.append(f"Coordinate {coord} out of valid range")

            # Validate coordinate precision
            if not self.precision_validator._validate_coordinate_precision(coord):
                validation_results.append(f"Coordinate {coord} precision violation")

            # Validate coordinate NaN
            if not self.precision_validator._validate_coordinate_nan(coord):
                validation_results.append(f"Coordinate {coord} contains NaN or infinite values")

        is_valid = len(validation_results) == 0
        return ValidationResult(
            validation_type=ValidationType.COORDINATE,
            validation_level=ValidationLevel.CRITICAL,
            is_valid=is_valid,
            errors=validation_results,
            context=context.operation_name
        )

    def _validate_coordinate_transformation(self, context: HookContext) -> ValidationResult:
        """Validate coordinate transformation results."""
        validation_results = []

        if not context.transformation_data:
            return ValidationResult(
                validation_type=ValidationType.COORDINATE,
                validation_level=ValidationLevel.WARNING,
                is_valid=False,
                errors=["No transformation data provided"],
                context=context.operation_name
            )

        # Validate transformation matrix
        matrix = context.transformation_data.get('matrix')
        if matrix is not None:
            # Check for valid transformation matrix
            if not self._validate_transformation_matrix(matrix):
                validation_results.append("Invalid transformation matrix")

        # Validate transformed coordinates
        for coord in context.coordinates:
            if not self.precision_validator._validate_coordinate_range(coord):
                validation_results.append(f"Transformed coordinate {coord} out of valid range")

        is_valid = len(validation_results) == 0
        return ValidationResult(
            validation_type=ValidationType.GEOMETRIC,
            validation_level=ValidationLevel.CRITICAL,
            is_valid=is_valid,
            errors=validation_results,
            context=context.operation_name
        )

    def _validate_geometric_constraint(self, context: HookContext) -> ValidationResult:
        """Validate geometric constraint results."""
        validation_results = []

        if not context.constraint_data:
            return ValidationResult(
                validation_type=ValidationType.CONSTRAINT,
                validation_level=ValidationLevel.WARNING,
                is_valid=False,
                errors=["No constraint data provided"],
                context=context.operation_name
            )

        # Validate constraint satisfaction
        constraint_type = context.constraint_data.get('type')
        if constraint_type == 'distance':
            validation_results.extend(self._validate_distance_constraint(context)
        elif constraint_type == 'angle':
            validation_results.extend(self._validate_angle_constraint(context)
        elif constraint_type == 'parallel':
            validation_results.extend(self._validate_parallel_constraint(context)
        elif constraint_type == 'perpendicular':
            validation_results.extend(self._validate_perpendicular_constraint(context)
        is_valid = len(validation_results) == 0
        return ValidationResult(
            validation_type=ValidationType.CONSTRAINT,
            validation_level=ValidationLevel.CRITICAL,
            is_valid=is_valid,
            errors=validation_results,
            context=context.operation_name
        )

    def _validate_precision_validation(self, context: HookContext) -> ValidationResult:
        """Validate precision validation results."""
        validation_results = []

        # Check for precision violations
        for coord in context.coordinates:
            precision_error = self._calculate_precision_error(coord)
            if precision_error > self.config.max_precision_error:
                validation_results.append(f"Precision error {precision_error} exceeds threshold")

        is_valid = len(validation_results) == 0
        return ValidationResult(
            validation_type=ValidationType.PRECISION,
            validation_level=ValidationLevel.CRITICAL,
            is_valid=is_valid,
            errors=validation_results,
            context=context.operation_name
        )

    def _validate_transformation_matrix(self, matrix) -> bool:
        """Validate transformation matrix."""
        try:
            import numpy as np
            matrix = np.array(matrix)

            # Check matrix dimensions
            if matrix.shape != (4, 4):
                return False

            # Check for valid transformation matrix properties
            det = np.linalg.det(matrix)
            if abs(det) < 1e-10:  # Singular matrix
                return False

            return True
        except Exception:
            return False

    def _validate_distance_constraint(self, context: HookContext) -> List[str]:
        """Validate distance constraint."""
        errors = []
        constraint_data = context.constraint_data

        if len(context.coordinates) < 2:
            errors.append("Distance constraint requires at least 2 coordinates")
            return errors

        target_distance = constraint_data.get('target_distance', 0.0)
        tolerance = constraint_data.get('tolerance', 0.001)

        actual_distance = context.coordinates[0].distance_to(context.coordinates[1])
        distance_error = abs(actual_distance - target_distance)

        if distance_error > tolerance:
            errors.append(f"Distance constraint violation: error={distance_error}, tolerance={tolerance}")

        return errors

    def _validate_angle_constraint(self, context: HookContext) -> List[str]:
        """Validate angle constraint."""
        errors = []
        constraint_data = context.constraint_data

        if len(context.coordinates) < 3:
            errors.append("Angle constraint requires at least 3 coordinates")
            return errors

        target_angle = constraint_data.get('target_angle', 0.0)
        tolerance = constraint_data.get('tolerance', 0.001)

        # Calculate angle between three points
        angle = self._calculate_angle_between_points(
            context.coordinates[0],
            context.coordinates[1],
            context.coordinates[2]
        )

        angle_error = abs(angle - target_angle)
        if angle_error > tolerance:
            errors.append(f"Angle constraint violation: error={angle_error}, tolerance={tolerance}")

        return errors

    def _validate_parallel_constraint(self, context: HookContext) -> List[str]:
        """Validate parallel constraint."""
        errors = []
        constraint_data = context.constraint_data

        if len(context.coordinates) < 4:
            errors.append("Parallel constraint requires at least 4 coordinates")
            return errors

        tolerance = constraint_data.get('tolerance', 0.001)

        # Calculate angles of two lines
        angle1 = self._calculate_line_angle(context.coordinates[0], context.coordinates[1])
        angle2 = self._calculate_line_angle(context.coordinates[2], context.coordinates[3])

        angle_diff = abs(angle1 - angle2)
        if angle_diff > tolerance and abs(angle_diff - 180) > tolerance:
            errors.append(f"Parallel constraint violation: angle difference={angle_diff}")

        return errors

    def _validate_perpendicular_constraint(self, context: HookContext) -> List[str]:
        """Validate perpendicular constraint."""
        errors = []
        constraint_data = context.constraint_data

        if len(context.coordinates) < 4:
            errors.append("Perpendicular constraint requires at least 4 coordinates")
            return errors

        tolerance = constraint_data.get('tolerance', 0.001)

        # Calculate angles of two lines
        angle1 = self._calculate_line_angle(context.coordinates[0], context.coordinates[1])
        angle2 = self._calculate_line_angle(context.coordinates[2], context.coordinates[3])

        angle_diff = abs(angle1 - angle2)
        if abs(angle_diff - 90) > tolerance and abs(angle_diff - 270) > tolerance:
            errors.append(f"Perpendicular constraint violation: angle difference={angle_diff}")

        return errors

    def _calculate_angle_between_points(self, p1: PrecisionCoordinate,
                                      p2: PrecisionCoordinate,
                                      p3: PrecisionCoordinate) -> float:
        """Calculate angle between three points."""
        import math

        # Calculate vectors
        v1_x = p1.x - p2.x
        v1_y = p1.y - p2.y
        v2_x = p3.x - p2.x
        v2_y = p3.y - p2.y

        # Calculate dot product
        dot_product = v1_x * v2_x + v1_y * v2_y

        # Calculate magnitudes
        mag1 = math.sqrt(v1_x**2 + v1_y**2)
        mag2 = math.sqrt(v2_x**2 + v2_y**2)

        # Calculate angle
        if mag1 == 0 or mag2 == 0:
            return 0.0

        cos_angle = dot_product / (mag1 * mag2)
        cos_angle = max(-1.0, min(1.0, cos_angle))  # Clamp to [-1, 1]

        return math.acos(cos_angle)

    def _calculate_line_angle(self, p1: PrecisionCoordinate, p2: PrecisionCoordinate) -> float:
        """Calculate angle of line between two points."""
        import math

        dx = p2.x - p1.x
        dy = p2.y - p1.y

        return math.atan2(dy, dx)

    def _calculate_precision_error(self, coord: PrecisionCoordinate) -> float:
        """Calculate precision error for a coordinate."""
        precision_value = self.config.get_precision_value()

        x_error = abs(coord.x - round(coord.x / precision_value) * precision_value)
        y_error = abs(coord.y - round(coord.y / precision_value) * precision_value)
        z_error = abs(coord.z - round(coord.z / precision_value) * precision_value)

        return max(x_error, y_error, z_error)

    def _handle_hook_error(self, hook: PrecisionHook, context: HookContext, error: Exception) -> None:
        """Handle hook execution errors."""
        error_msg = f"Hook {hook.hook_id} error: {str(error)}"
        context.errors.append(error_msg)

        # Log error with context
        self.logger.error(error_msg, extra={
            'hook_id': hook.hook_id,
            'hook_type': hook.hook_type.value,
            'operation': context.operation_name,
            'coordinates_count': len(context.coordinates)
        })

    def _execute_recovery_mechanism(self, hook: PrecisionHook, context: HookContext, error: Exception) -> None:
        """Execute recovery mechanism for failed hooks."""
        try:
            # Attempt to recover based on hook type
            if hook.hook_type == HookType.COORDINATE_CREATION:
                self._recover_coordinate_creation(context)
            elif hook.hook_type == HookType.COORDINATE_TRANSFORMATION:
                self._recover_coordinate_transformation(context)
            elif hook.hook_type == HookType.GEOMETRIC_CONSTRAINT:
                self._recover_geometric_constraint(context)

            self.logger.info(f"Recovery mechanism executed for hook {hook.hook_id}")

        except Exception as recovery_error:
            self.logger.error(f"Recovery mechanism failed for hook {hook.hook_id}: {recovery_error}")

    def _recover_coordinate_creation(self, context: HookContext) -> None:
        """Recover from coordinate creation errors."""
        if not context.coordinates:
            return

        # Attempt to correct coordinates
        corrected_coordinates = []
        for coord in context.coordinates:
            try:
                corrected_coord = self._correct_coordinate(coord)
                corrected_coordinates.append(corrected_coord)
            except Exception as e:
                self.logger.warning(f"Failed to correct coordinate {coord}: {e}")
                corrected_coordinates.append(coord)

        context.coordinates = corrected_coordinates

    def _recover_coordinate_transformation(self, context: HookContext) -> None:
        """Recover from coordinate transformation errors."""
        if not context.coordinates:
            return

        # Attempt to correct transformed coordinates
        corrected_coordinates = []
        for coord in context.coordinates:
            try:
                corrected_coord = self._correct_coordinate(coord)
                corrected_coordinates.append(corrected_coord)
            except Exception as e:
                self.logger.warning(f"Failed to correct transformed coordinate {coord}: {e}")
                corrected_coordinates.append(coord)

        context.coordinates = corrected_coordinates

    def _recover_geometric_constraint(self, context: HookContext) -> None:
        """Recover from geometric constraint errors."""
        # For constraint violations, we might need to adjust coordinates
        # This is a simplified recovery - in practice, this would be more complex
        if context.constraint_data and context.coordinates:
            self.logger.info("Geometric constraint recovery attempted")

    def _correct_coordinate(self, coord: PrecisionCoordinate) -> PrecisionCoordinate:
        """Correct coordinate based on precision level."""
        precision_value = self.config.get_precision_value()

        corrected_x = round(coord.x / precision_value) * precision_value
        corrected_y = round(coord.y / precision_value) * precision_value
        corrected_z = round(coord.z / precision_value) * precision_value

        return PrecisionCoordinate(corrected_x, corrected_y, corrected_z)

    def _register_default_hooks(self) -> None:
        """Register default precision validation hooks."""

        # Coordinate creation hooks
        self.register_hook(PrecisionHook(
            hook_id="coordinate_creation_validation",
            hook_type=HookType.COORDINATE_CREATION,
            function=self._coordinate_creation_hook,
            priority=10,
            description="Validate coordinate creation",
            validation_level=ValidationLevel.CRITICAL
        )
        # Coordinate transformation hooks
        self.register_hook(PrecisionHook(
            hook_id="coordinate_transformation_validation",
            hook_type=HookType.COORDINATE_TRANSFORMATION,
            function=self._coordinate_transformation_hook,
            priority=10,
            description="Validate coordinate transformation",
            validation_level=ValidationLevel.CRITICAL
        )
        # Geometric constraint hooks
        self.register_hook(PrecisionHook(
            hook_id="geometric_constraint_validation",
            hook_type=HookType.GEOMETRIC_CONSTRAINT,
            function=self._geometric_constraint_hook,
            priority=10,
            description="Validate geometric constraints",
            validation_level=ValidationLevel.CRITICAL
        )
        # Precision validation hooks
        self.register_hook(PrecisionHook(
            hook_id="precision_validation_check",
            hook_type=HookType.PRECISION_VALIDATION,
            function=self._precision_validation_hook,
            priority=5,
            description="Check precision requirements",
            validation_level=ValidationLevel.CRITICAL
        )
        # Error handling hooks
        self.register_hook(PrecisionHook(
            hook_id="error_handling_hook",
            hook_type=HookType.ERROR_HANDLING,
            function=self._error_handling_hook,
            priority=1,
            description="Handle precision errors",
            validation_level=ValidationLevel.WARNING
        )
        # Recovery mechanism hooks
        self.register_hook(PrecisionHook(
            hook_id="recovery_mechanism_hook",
            hook_type=HookType.RECOVERY_MECHANISM,
            function=self._recovery_mechanism_hook,
            priority=1,
            description="Execute recovery mechanisms",
            validation_level=ValidationLevel.INFO
        )
    def _coordinate_creation_hook(self, context: HookContext) -> HookContext:
        """Hook for coordinate creation validation."""
        self.logger.debug(f"Coordinate creation hook executed for {context.operation_name}")
        return context

    def _coordinate_transformation_hook(self, context: HookContext) -> HookContext:
        """Hook for coordinate transformation validation."""
        self.logger.debug(f"Coordinate transformation hook executed for {context.operation_name}")
        return context

    def _geometric_constraint_hook(self, context: HookContext) -> HookContext:
        """Hook for geometric constraint validation."""
        self.logger.debug(f"Geometric constraint hook executed for {context.operation_name}")
        return context

    def _precision_validation_hook(self, context: HookContext) -> HookContext:
        """Hook for precision validation."""
        self.logger.debug(f"Precision validation hook executed for {context.operation_name}")
        return context

    def _error_handling_hook(self, context: HookContext) -> HookContext:
        """Hook for error handling."""
        if context.errors:
            self.logger.warning(f"Errors detected in {context.operation_name}: {context.errors}")
        return context

    def _recovery_mechanism_hook(self, context: HookContext) -> HookContext:
        """Hook for recovery mechanisms."""
        if context.errors:
            self.logger.info(f"Recovery mechanism executed for {context.operation_name}")
        return context


# Global hook manager instance
hook_manager = PrecisionHookManager()


def precision_hook(hook_type: HookType, priority: int = 0, enabled: bool = True):
    """Decorator for registering precision validation hooks."""
def decorator(func: Callable) -> Callable:
    """
    Perform decorator operation

Args:
        func: Description of func

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = decorator(param)
        print(result)
    """
        hook = PrecisionHook(
            hook_id=f"{func.__module__}.{func.__name__}",
            hook_type=hook_type,
            function=func,
            priority=priority,
            enabled=enabled,
            description=func.__doc__ or ""
        )
        hook_manager.register_hook(hook)

        @functools.wraps(func)
def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper
    return decorator
