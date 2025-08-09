"""
SVGX Geometry module for geometric calculations and transformations.
"""

import math
import logging
from typing import Dict, Any, List, Optional, Tuple
import time

# Import precision system modules
from ..core.precision_coordinate import PrecisionCoordinate, CoordinateValidator
from ..core.precision_math import PrecisionMath
from ..core.precision_validator import PrecisionValidator, ValidationLevel, ValidationType
from ..core.precision_config import PrecisionConfig, config_manager
from ..core.precision_undo_redo import PrecisionUndoRedo, OperationType, StateType

from svgx_engine.core.precision_hooks import hook_manager, HookType, HookContext
from svgx_engine.core.precision_errors import handle_precision_error, PrecisionErrorType, PrecisionErrorSeverity

logger = logging.getLogger(__name__)


class SVGXGeometry:
    """Handles geometric calculations for SVGX elements with precision support."""

    def __init__(self, config: Optional[PrecisionConfig] = None):
    """
    Perform __init__ operation

Args:
        config: Description of config

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        self.config = config or config_manager.get_default_config()
        self.precision_math = PrecisionMath()
        self.coordinate_validator = CoordinateValidator()
        self.precision_validator = PrecisionValidator()

        # Initialize precision undo/redo system
        self.undo_redo = PrecisionUndoRedo(self.config)

        # Legacy precision setting for backward compatibility
        self.precision = self.config.get_precision_value()

        # State tracking for geometry objects
        self.geometry_objects: Dict[str, Dict[str, Any]] = {}

    def calculate_area(self, element) -> float:
        """Calculate area of an element with precision."""

        try:
            # Capture before state for undo/redo
            before_state = self._capture_element_state(element, "area_calculation")

            if element.tag == 'rect':
                width = self._get_precision_value(element.attributes.get('width', 0)
                height = self._get_precision_value(element.attributes.get('height', 0)
                area = self.precision_math.multiply(width, height)

                # Create hook context for rectangle area calculation
                area_data = {
                    'element_type': 'rect',
                    'width': width,
                    'height': height,
                    'calculation_type': 'area'
                }

                context = HookContext(
                    operation_name="rectangle_area_calculation",
                    coordinates=[],
                    constraint_data=area_data
                )

                # Execute geometric constraint hooks
                context = hook_manager.execute_hooks(HookType.GEOMETRIC_CONSTRAINT, context)

                # Validate area
                if self.config.enable_geometric_validation:
                    validation_result = self._validate_area(area)
                    if not validation_result['is_valid']:
                        handle_precision_error(
                            error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                            message=f"Rectangle area validation warning: {validation_result['message']}",
                            operation="rectangle_area_calculation",
                            coordinates=[],
                            context=area_data,
                            severity=PrecisionErrorSeverity.WARNING
                        )

                # Execute precision validation hooks
                hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)

                # Capture after state
                after_state = self._capture_element_state(element, "area_calculation")
                self._record_operation(OperationType.MODIFY, f"Calculated area for {element.tag}", before_state, after_state)

                return area

            elif element.tag == 'circle':
                radius = self._get_precision_value(element.attributes.get('r', 0)
                radius_squared = self.precision_math.multiply(radius, radius)
                area = self.precision_math.multiply(radius_squared, self.precision_math.pi()
                # Create hook context for circle area calculation
                area_data = {
                    'element_type': 'circle',
                    'radius': radius,
                    'calculation_type': 'area'
                }

                context = HookContext(
                    operation_name="circle_area_calculation",
                    coordinates=[],
                    constraint_data=area_data
                )

                # Execute geometric constraint hooks
                context = hook_manager.execute_hooks(HookType.GEOMETRIC_CONSTRAINT, context)

                # Validate area
                if self.config.enable_geometric_validation:
                    validation_result = self._validate_area(area)
                    if not validation_result['is_valid']:
                        handle_precision_error(
                            error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                            message=f"Circle area validation warning: {validation_result['message']}",
                            operation="circle_area_calculation",
                            coordinates=[],
                            context=area_data,
                            severity=PrecisionErrorSeverity.WARNING
                        )

                # Execute precision validation hooks
                hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)

                # Capture after state
                after_state = self._capture_element_state(element, "area_calculation")
                self._record_operation(OperationType.MODIFY, f"Calculated area for {element.tag}", before_state, after_state)

                return area

            elif element.tag == 'ellipse':
                rx = self._get_precision_value(element.attributes.get('rx', 0)
                ry = self._get_precision_value(element.attributes.get('ry', 0)
                area = self.precision_math.multiply(
                    self.precision_math.multiply(rx, ry),
                    self.precision_math.pi()
                # Create hook context for ellipse area calculation
                area_data = {
                    'element_type': 'ellipse',
                    'rx': rx,
                    'ry': ry,
                    'calculation_type': 'area'
                }

                context = HookContext(
                    operation_name="ellipse_area_calculation",
                    coordinates=[],
                    constraint_data=area_data
                )

                # Execute geometric constraint hooks
                context = hook_manager.execute_hooks(HookType.GEOMETRIC_CONSTRAINT, context)

                # Validate area
                if self.config.enable_geometric_validation:
                    validation_result = self._validate_area(area)
                    if not validation_result['is_valid']:
                        handle_precision_error(
                            error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                            message=f"Ellipse area validation warning: {validation_result['message']}",
                            operation="ellipse_area_calculation",
                            coordinates=[],
                            context=area_data,
                            severity=PrecisionErrorSeverity.WARNING
                        )

                # Execute precision validation hooks
                hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)

                # Capture after state
                after_state = self._capture_element_state(element, "area_calculation")
                self._record_operation(OperationType.MODIFY, f"Calculated area for {element.tag}", before_state, after_state)

                return area
            else:
                return 0.0
        except Exception as e:
            # Handle area calculation error
            handle_precision_error(
                error_type=PrecisionErrorType.CALCULATION_ERROR,
                message=f"Area calculation failed: {str(e)}",
                operation="area_calculation",
                coordinates=[],
                context={'element_tag': element.tag},
                severity=PrecisionErrorSeverity.ERROR
            )
            logger.error(f"Failed to calculate area: {e}")
            return 0.0

    def calculate_perimeter(self, element) -> float:
        """Calculate perimeter of an element with precision."""
        try:
            # Capture before state for undo/redo
            before_state = self._capture_element_state(element, "perimeter_calculation")

            if element.tag == 'rect':
                width = self._get_precision_value(element.attributes.get('width', 0)
                height = self._get_precision_value(element.attributes.get('height', 0)
                perimeter = self.precision_math.multiply(
                    self.precision_math.add(width, height),
                    2
                )

                # Create hook context for rectangle perimeter calculation
                perimeter_data = {
                    'element_type': 'rect',
                    'width': width,
                    'height': height,
                    'calculation_type': 'perimeter'
                }

                context = HookContext(
                    operation_name="rectangle_perimeter_calculation",
                    coordinates=[],
                    constraint_data=perimeter_data
                )

                # Execute geometric constraint hooks
                context = hook_manager.execute_hooks(HookType.GEOMETRIC_CONSTRAINT, context)

                # Validate perimeter
                if self.config.enable_geometric_validation:
                    validation_result = self._validate_perimeter(perimeter)
                    if not validation_result['is_valid']:
                        handle_precision_error(
                            error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                            message=f"Rectangle perimeter validation warning: {validation_result['message']}",
                            operation="rectangle_perimeter_calculation",
                            coordinates=[],
                            context=perimeter_data,
                            severity=PrecisionErrorSeverity.WARNING
                        )

                # Execute precision validation hooks
                hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)

                # Capture after state
                after_state = self._capture_element_state(element, "perimeter_calculation")
                self._record_operation(OperationType.MODIFY, f"Calculated perimeter for {element.tag}", before_state, after_state)

                return perimeter

            elif element.tag == 'circle':
                radius = self._get_precision_value(element.attributes.get('r', 0)
                diameter = self.precision_math.multiply(radius, 2)
                perimeter = self.precision_math.multiply(diameter, self.precision_math.pi()
                # Create hook context for circle perimeter calculation
                perimeter_data = {
                    'element_type': 'circle',
                    'radius': radius,
                    'calculation_type': 'perimeter'
                }

                context = HookContext(
                    operation_name="circle_perimeter_calculation",
                    coordinates=[],
                    constraint_data=perimeter_data
                )

                # Execute geometric constraint hooks
                context = hook_manager.execute_hooks(HookType.GEOMETRIC_CONSTRAINT, context)

                # Validate perimeter
                if self.config.enable_geometric_validation:
                    validation_result = self._validate_perimeter(perimeter)
                    if not validation_result['is_valid']:
                        handle_precision_error(
                            error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                            message=f"Circle perimeter validation warning: {validation_result['message']}",
                            operation="circle_perimeter_calculation",
                            coordinates=[],
                            context=perimeter_data,
                            severity=PrecisionErrorSeverity.WARNING
                        )

                # Execute precision validation hooks
                hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)

                # Capture after state
                after_state = self._capture_element_state(element, "perimeter_calculation")
                self._record_operation(OperationType.MODIFY, f"Calculated perimeter for {element.tag}", before_state, after_state)

                return perimeter

            elif element.tag == 'ellipse':
                rx = self._get_precision_value(element.attributes.get('rx', 0)
                ry = self._get_precision_value(element.attributes.get('ry', 0)
                # Approximation for ellipse perimeter using Ramanujan's formula'
                a = max(rx, ry)
                b = min(rx, ry)
                h = self.precision_math.divide(
                    self.precision_math.subtract(a, b),
                    self.precision_math.add(a, b)
                h_squared = self.precision_math.multiply(h, h)

                # Ramanujan's approximation'
                perimeter = self.precision_math.multiply(
                    self.precision_math.multiply(
                        self.precision_math.add(a, b),
                        self.precision_math.pi()
                    ),
                    self.precision_math.add(
                        1,
                        self.precision_math.divide(
                            self.precision_math.multiply(3, h_squared),
                            self.precision_math.add(10, self.precision_math.sqrt(
                                self.precision_math.subtract(4, self.precision_math.multiply(3, h_squared)
                            ))
                        )
                    )
                )

                # Create hook context for ellipse perimeter calculation
                perimeter_data = {
                    'element_type': 'ellipse',
                    'rx': rx,
                    'ry': ry,
                    'calculation_type': 'perimeter'
                }

                context = HookContext(
                    operation_name="ellipse_perimeter_calculation",
                    coordinates=[],
                    constraint_data=perimeter_data
                )

                # Execute geometric constraint hooks
                context = hook_manager.execute_hooks(HookType.GEOMETRIC_CONSTRAINT, context)

                # Validate perimeter
                if self.config.enable_geometric_validation:
                    validation_result = self._validate_perimeter(perimeter)
                    if not validation_result['is_valid']:
                        handle_precision_error(
                            error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                            message=f"Ellipse perimeter validation warning: {validation_result['message']}",
                            operation="ellipse_perimeter_calculation",
                            coordinates=[],
                            context=perimeter_data,
                            severity=PrecisionErrorSeverity.WARNING
                        )

                # Execute precision validation hooks
                hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)

                # Capture after state
                after_state = self._capture_element_state(element, "perimeter_calculation")
                self._record_operation(OperationType.MODIFY, f"Calculated perimeter for {element.tag}", before_state, after_state)

                return perimeter
            else:
                return 0.0
        except Exception as e:
            # Handle perimeter calculation error
            handle_precision_error(
                error_type=PrecisionErrorType.CALCULATION_ERROR,
                message=f"Perimeter calculation failed: {str(e)}",
                operation="perimeter_calculation",
                coordinates=[],
                context={'element_tag': element.tag},
                severity=PrecisionErrorSeverity.ERROR
            )
            logger.error(f"Failed to calculate perimeter: {e}")
            return 0.0

    def get_bounding_box(self, element) -> Tuple[float, float, float, float]:
        """Get bounding box of an element with precision."""
        try:
            # Capture before state for undo/redo
            before_state = self._capture_element_state(element, "bounding_box_calculation")

            if element.tag == 'rect':
                x = self._get_precision_value(element.attributes.get('x', 0)
                y = self._get_precision_value(element.attributes.get('y', 0)
                width = self._get_precision_value(element.attributes.get('width', 0)
                height = self._get_precision_value(element.attributes.get('height', 0)
                # Create precision coordinates for bounding box
                min_x = x
                min_y = y
                max_x = self.precision_math.add(x, width)
                max_y = self.precision_math.add(y, height)

                # Create hook context for rectangle bounding box calculation
                bbox_data = {
                    'element_type': 'rect',
                    'x': x,
                    'y': y,
                    'width': width,
                    'height': height,
                    'calculation_type': 'bounding_box'
                }

                context = HookContext(
                    operation_name="rectangle_bounding_box_calculation",
                    coordinates=[],
                    constraint_data=bbox_data
                )

                # Execute geometric constraint hooks
                context = hook_manager.execute_hooks(HookType.GEOMETRIC_CONSTRAINT, context)

                # Execute precision validation hooks
                hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)

                # Capture after state
                after_state = self._capture_element_state(element, "bounding_box_calculation")
                self._record_operation(OperationType.MODIFY, f"Calculated bounding box for {element.tag}", before_state, after_state)

                return (min_x, min_y, max_x, max_y)

            elif element.tag == 'circle':
                cx = self._get_precision_value(element.attributes.get('cx', 0)
                cy = self._get_precision_value(element.attributes.get('cy', 0)
                r = self._get_precision_value(element.attributes.get('r', 0)
                # Create precision coordinates for bounding box
                min_x = self.precision_math.subtract(cx, r)
                min_y = self.precision_math.subtract(cy, r)
                max_x = self.precision_math.add(cx, r)
                max_y = self.precision_math.add(cy, r)

                # Create hook context for circle bounding box calculation
                bbox_data = {
                    'element_type': 'circle',
                    'cx': cx,
                    'cy': cy,
                    'radius': r,
                    'calculation_type': 'bounding_box'
                }

                context = HookContext(
                    operation_name="circle_bounding_box_calculation",
                    coordinates=[],
                    constraint_data=bbox_data
                )

                # Execute geometric constraint hooks
                context = hook_manager.execute_hooks(HookType.GEOMETRIC_CONSTRAINT, context)

                # Execute precision validation hooks
                hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)

                # Capture after state
                after_state = self._capture_element_state(element, "bounding_box_calculation")
                self._record_operation(OperationType.MODIFY, f"Calculated bounding box for {element.tag}", before_state, after_state)

                return (min_x, min_y, max_x, max_y)
            else:
                return (0, 0, 0, 0)
        except Exception as e:
            # Handle bounding box calculation error
            handle_precision_error(
                error_type=PrecisionErrorType.CALCULATION_ERROR,
                message=f"Bounding box calculation failed: {str(e)}",
                operation="bounding_box_calculation",
                coordinates=[],
                context={'element_tag': element.tag},
                severity=PrecisionErrorSeverity.ERROR
            )
            logger.error(f"Failed to get bounding box: {e}")
            return (0, 0, 0, 0)

    def convert_units(self, value: str, from_unit: str, to_unit: str) -> float:
        """Convert between different units with precision validation."""
        from svgx_engine.core.precision_hooks import hook_manager, HookType, HookContext
        from svgx_engine.core.precision_errors import handle_precision_error, PrecisionErrorType, PrecisionErrorSeverity

        # Create hook context for unit conversion
        conversion_data = {
            'value': value,
            'from_unit': from_unit,
            'to_unit': to_unit,
            'operation_type': 'unit_conversion'
        }

        context = HookContext(
            operation_name="unit_conversion",
            coordinates=[],
            constraint_data=conversion_data
        )

        # Execute geometric constraint hooks
        context = hook_manager.execute_hooks(HookType.GEOMETRIC_CONSTRAINT, context)

        try:
            # Parse value with precision
            if isinstance(value, str):
                # Remove unit from string and parse numeric value
                numeric_str = value.replace(from_unit, '').strip()
                numeric_value = self._get_precision_value(numeric_str)
            else:
                numeric_value = self._get_precision_value(value)

            # Validate input value
            if self.config.enable_geometric_validation:
                if numeric_value < 0:
                    handle_precision_error(
                        error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                        message=f"Negative value in unit conversion: {numeric_value}",
                        operation="unit_conversion",
                        coordinates=[],
                        context=conversion_data,
                        severity=PrecisionErrorSeverity.WARNING
                    )

                max_value = self.config.validation_rules.get('max_unit_value', 1e9)
                if abs(numeric_value) > max_value:
                    handle_precision_error(
                        error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                        message=f"Value {numeric_value} exceeds maximum allowed {max_value}",
                        operation="unit_conversion",
                        coordinates=[],
                        context=conversion_data,
                        severity=PrecisionErrorSeverity.ERROR
                    )
                    raise ValueError(f"Value {numeric_value} exceeds maximum allowed {max_value}")

            # Conversion factors (to mm) with precision
            unit_factors = {
                'mm': 1.0,
                'cm': 10.0,
                'm': 1000.0,
                'km': 1000000.0,
                'in': 25.4,
                'ft': 304.8,
                'yd': 914.4,
                'mi': 1609344.0,
                'px': 0.264583,  # Assuming 96 DPI
                'pt': 0.352778,
                'pc': 4.233333
            }

            # Validate units
            if from_unit not in unit_factors:
                handle_precision_error(
                    error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                    message=f"Unknown source unit: {from_unit}",
                    operation="unit_conversion",
                    coordinates=[],
                    context=conversion_data,
                    severity=PrecisionErrorSeverity.ERROR
                )
                raise ValueError(f"Unknown source unit: {from_unit}")

            if to_unit not in unit_factors:
                handle_precision_error(
                    error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                    message=f"Unknown target unit: {to_unit}",
                    operation="unit_conversion",
                    coordinates=[],
                    context=conversion_data,
                    severity=PrecisionErrorSeverity.ERROR
                )
                raise ValueError(f"Unknown target unit: {to_unit}")

            # Convert to mm first with precision math
            from_factor = unit_factors.get(from_unit, 1.0)
            mm_value = self.precision_math.multiply(numeric_value, from_factor)

            # Convert from mm to target unit with precision math
            to_factor = unit_factors.get(to_unit, 1.0)
            result = self.precision_math.divide(mm_value, to_factor)

            # Validate result
            if self.config.enable_geometric_validation:
                min_result = self.config.validation_rules.get('min_unit_result', 1e-12)
                max_result = self.config.validation_rules.get('max_unit_result', 1e12)

                if abs(result) < min_result:
                    handle_precision_error(
                        error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                        message=f"Conversion result {result} is below minimum threshold {min_result}",
                        operation="unit_conversion",
                        coordinates=[],
                        context=conversion_data,
                        severity=PrecisionErrorSeverity.WARNING
                    )

                if abs(result) > max_result:
                    handle_precision_error(
                        error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                        message=f"Conversion result {result} is above maximum threshold {max_result}",
                        operation="unit_conversion",
                        coordinates=[],
                        context=conversion_data,
                        severity=PrecisionErrorSeverity.WARNING
                    )

            # Execute precision validation hooks
            hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)

            return result

        except Exception as e:
            # Handle unit conversion error
            handle_precision_error(
                error_type=PrecisionErrorType.CALCULATION_ERROR,
                message=f"Unit conversion failed: {str(e)}",
                operation="unit_conversion",
                coordinates=[],
                context=conversion_data,
                severity=PrecisionErrorSeverity.ERROR
            )
            logger.error(f"Failed to convert units: {e}")
            return 0.0

    def create_precision_coordinate(self, x: float, y: float, z: float = 0.0) -> PrecisionCoordinate:
        """Create a precision coordinate with validation."""
        try:
            coord = PrecisionCoordinate(x, y, z)

            # Validate coordinate
            if self.config.enable_coordinate_validation:
                validation_result = self.coordinate_validator.validate_coordinate(coord)
                if not validation_result.is_valid:
                    if self.config.should_fail_on_violation():
                        raise ValueError(f"Invalid coordinate: {validation_result.errors}")
                    elif self.config.auto_correct_precision_errors:
                        coord = self._correct_coordinate(coord)

            return coord
        except Exception as e:
            logger.error(f"Failed to create precision coordinate: {e}")
            raise

    def transform_element(self, element, translation: List[float] = None,
                         scale: float = 1.0, rotation: float = 0.0) -> bool:
        """Transform an element with precision and undo/redo support."""
        try:
            # Capture before state
            before_state = self._capture_element_state(element, "transform")

            # Apply transformation
            success = self._apply_transformation(element, translation, scale, rotation)

            if success:
                # Capture after state
                after_state = self._capture_element_state(element, "transform")
                self._record_operation(OperationType.TRANSFORM, f"Transformed {element.tag}", before_state, after_state)

            return success

        except Exception as e:
            logger.error(f"Failed to transform element: {e}")
            return False

    def _apply_transformation(self, element, translation: List[float] = None,
                            scale: float = 1.0, rotation: float = 0.0) -> bool:
        """Apply transformation to an element with precision."""
        try:
            if translation is None:
                translation = [0, 0]

            # Get current coordinates
            if element.tag == 'rect':
                x = self._get_precision_value(element.attributes.get('x', 0)
                y = self._get_precision_value(element.attributes.get('y', 0)
                width = self._get_precision_value(element.attributes.get('width', 0)
                height = self._get_precision_value(element.attributes.get('height', 0)
                # Apply translation
                new_x = self.precision_math.add(x, translation[0])
                new_y = self.precision_math.add(y, translation[1])

                # Apply scale
                new_width = self.precision_math.multiply(width, scale)
                new_height = self.precision_math.multiply(height, scale)

                # Apply rotation (simplified for rectangles)
                if rotation != 0:
                    # For rectangles, rotation might require more complex handling
                    # This is a simplified implementation
                    pass

                # Update element attributes
                element.attributes['x'] = str(new_x)
                element.attributes['y'] = str(new_y)
                element.attributes['width'] = str(new_width)
                element.attributes['height'] = str(new_height)

            elif element.tag == 'circle':
                cx = self._get_precision_value(element.attributes.get('cx', 0)
                cy = self._get_precision_value(element.attributes.get('cy', 0)
                r = self._get_precision_value(element.attributes.get('r', 0)
                # Apply translation
                new_cx = self.precision_math.add(cx, translation[0])
                new_cy = self.precision_math.add(cy, translation[1])

                # Apply scale
                new_r = self.precision_math.multiply(r, scale)

                # Update element attributes
                element.attributes['cx'] = str(new_cx)
                element.attributes['cy'] = str(new_cy)
                element.attributes['r'] = str(new_r)

            return True

        except Exception as e:
            logger.error(f"Failed to apply transformation: {e}")
            return False

    def _capture_element_state(self, element, operation: str) -> Optional[Any]:
        """Capture the current state of an element for undo/redo."""
        try:
            element_id = getattr(element, 'id', f"{element.tag}_{id(element)}")

            # Create state data
            state_data = {
                'tag': element.tag,
                'attributes': dict(element.attributes) if hasattr(element, 'attributes') else {},
                'operation': operation,
                'timestamp': time.time()
            }

            # Create precision state
            return self.undo_redo.create_state(
                object_id=element_id,
                data=state_data,
                operation_type=OperationType.MODIFY,
                state_type=StateType.GEOMETRY
            )

        except Exception as e:
            logger.error(f"Failed to capture element state: {e}")
            return None

    def _record_operation(self, operation_type: OperationType, description: str,
                         before_state: Optional[Any] = None, after_state: Optional[Any] = None):
        """Record an operation for undo/redo."""
        try:
            self.undo_redo.push_operation(operation_type, description, before_state, after_state)
        except Exception as e:
            logger.error(f"Failed to record operation: {e}")

    def undo(self) -> bool:
        """Undo the last operation."""
        try:
            entry = self.undo_redo.undo()
            if entry:
                logger.info(f"Undid operation: {entry.description}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to undo operation: {e}")
            return False

    def redo(self) -> bool:
        """Redo the last undone operation."""
        try:
            entry = self.undo_redo.redo()
            if entry:
                logger.info(f"Redid operation: {entry.description}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to redo operation: {e}")
            return False

    def can_undo(self) -> bool:
        """Check if undo is possible."""
        return self.undo_redo.can_undo()

    def can_redo(self) -> bool:
        """Check if redo is possible."""
        return self.undo_redo.can_redo()

    def get_undo_description(self) -> Optional[str]:
        """Get description of the next undo operation."""
        return self.undo_redo.get_undo_description()

    def get_redo_description(self) -> Optional[str]:
        """Get description of the next redo operation."""
        return self.undo_redo.get_redo_description()

    def clear_history(self):
        """Clear all undo/redo history."""
        self.undo_redo.clear_history()

    def get_statistics(self) -> Dict[str, Any]:
        """Get undo/redo system statistics."""
        return self.undo_redo.get_statistics()

    def _get_precision_value(self, value) -> float:
        """Convert value to precision-aware float."""
        try:
            float_value = float(value)

            # Round to precision level if auto-correction is enabled
            if self.config.auto_correct_precision_errors:
                precision_value = self.config.get_precision_value()
                float_value = round(float_value / precision_value) * precision_value

            return float_value
        except (ValueError, TypeError):
            return 0.0

    def _validate_area(self, area: float) -> Dict[str, Any]:
        """Validate area value against configuration rules."""
        rules = self.config.validation_rules
        min_area = rules.get('min_area', 0.000001)
        max_area = rules.get('max_area', 1e12)

        if area < min_area:
            return {
                'is_valid': False,
                'message': f"Area {area} is below minimum {min_area}"
            }
        elif area > max_area:
            return {
                'is_valid': False,
                'message': f"Area {area} is above maximum {max_area}"
            }

        return {'is_valid': True, 'message': ''}

    def _validate_perimeter(self, perimeter: float) -> Dict[str, Any]:
        """Validate perimeter value against configuration rules."""
        rules = self.config.validation_rules
        min_perimeter = rules.get('min_perimeter', 0.001)
        max_perimeter = rules.get('max_perimeter', 1e6)

        if perimeter < min_perimeter:
            return {
                'is_valid': False,
                'message': f"Perimeter {perimeter} is below minimum {min_perimeter}"
            }
        elif perimeter > max_perimeter:
            return {
                'is_valid': False,
                'message': f"Perimeter {perimeter} is above maximum {max_perimeter}"
            }

        return {'is_valid': True, 'message': ''}

    def _correct_coordinate(self, coord: PrecisionCoordinate) -> PrecisionCoordinate:
        """Correct coordinate based on precision level."""
        precision_value = self.config.get_precision_value()
        corrected_x = round(coord.x / precision_value) * precision_value
        corrected_y = round(coord.y / precision_value) * precision_value
        corrected_z = round(coord.z / precision_value) * precision_value

        return PrecisionCoordinate(corrected_x, corrected_y, corrected_z)

    def calculate_distance(self, coord1: PrecisionCoordinate, coord2: PrecisionCoordinate) -> float:
        """Calculate distance between two precision coordinates."""
        return self.precision_math.distance(coord1, coord2)

    def calculate_centroid(self, coordinates: List[PrecisionCoordinate]) -> PrecisionCoordinate:
        """Calculate centroid of precision coordinates."""
        if not coordinates:
            return PrecisionCoordinate(0, 0, 0)

        x_sum = 0.0
        y_sum = 0.0
        z_sum = 0.0
        count = len(coordinates)

        for coord in coordinates:
            x_sum = self.precision_math.add(x_sum, coord.x)
            y_sum = self.precision_math.add(y_sum, coord.y)
            z_sum = self.precision_math.add(z_sum, coord.z)

        if count == 0:
            return PrecisionCoordinate(0, 0, 0)

        avg_x = self.precision_math.divide(x_sum, count)
        avg_y = self.precision_math.divide(y_sum, count)
        avg_z = self.precision_math.divide(z_sum, count)

        return PrecisionCoordinate(avg_x, avg_y, avg_z)
