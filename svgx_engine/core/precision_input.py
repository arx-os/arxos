"""
Precision Input Methods for CAD Applications

This module provides precision-aware input handling for CAD applications,
including coordinate input validation, mouse/touch input, keyboard input,
and precision feedback systems.
"""

import math
import time
import logging
from typing import Dict, List, Tuple, Optional, Union, Callable, Any
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
import numpy as np

from .precision_coordinate import PrecisionCoordinate
from .precision_math import PrecisionMath, PrecisionSettings
from .precision_validator import PrecisionValidator, ValidationResult


class InputType(Enum):
    """Types of input methods."""

    MOUSE = "mouse"
    TOUCH = "touch"
    KEYBOARD = "keyboard"
    PEN = "pen"
    VOICE = "voice"


class InputMode(Enum):
    """Input modes for precision handling."""

    FREEHAND = "freehand"
    GRID_SNAP = "grid_snap"
    OBJECT_SNAP = "object_snap"
    ANGLE_SNAP = "angle_snap"
    PRECISION_MODE = "precision_mode"


class InputEvent:
    """Base class for input events."""

    def __init__(
        self,
        event_type: str,
        timestamp: float,
        coordinates: Tuple[float, float, float],
        input_type: InputType,
        input_mode: InputMode,
    ):
        self.event_type = event_type
        self.timestamp = timestamp
        self.coordinates = coordinates
        self.input_type = input_type
        self.input_mode = input_mode
        self.precision_coordinate: Optional[PrecisionCoordinate] = None
        self.validation_results: List[ValidationResult] = []
        self.is_valid = False


@dataclass
class InputSettings:
    """Configuration for precision input handling."""

    # Precision settings
    default_precision: Decimal = Decimal("0.001")  # 1mm precision
    grid_snap_precision: Decimal = Decimal("1.000")  # 1mm grid
    angle_snap_precision: Decimal = Decimal("15.0")  # 15 degrees

    # Input sensitivity
    mouse_sensitivity: float = 1.0
    touch_sensitivity: float = 1.0
    keyboard_precision: Decimal = Decimal("0.001")

    # Validation settings
    validate_input: bool = True
    strict_mode: bool = True
    log_input_errors: bool = True

    # Feedback settings
    provide_visual_feedback: bool = True
    provide_audio_feedback: bool = False
    feedback_delay: float = 0.1  # seconds

    # Snap settings
    enable_grid_snap: bool = True
    enable_object_snap: bool = True
    enable_angle_snap: bool = True
    snap_tolerance: Decimal = Decimal("0.5")  # 0.5mm tolerance

    def __post_init__(self):
        """Validate input settings."""
        if self.default_precision <= 0:
            raise ValueError("Default precision must be positive")
        if self.grid_snap_precision <= 0:
            raise ValueError("Grid snap precision must be positive")
        if self.angle_snap_precision <= 0:
            raise ValueError("Angle snap precision must be positive")


class PrecisionInputHandler:
    """
    Precision-aware input handler for CAD applications.

    Provides coordinate input validation, mouse/touch input handling,
    keyboard input for exact coordinates, and precision feedback.
    """

    def __init__(self, settings: Optional[InputSettings] = None):
        """
        Initialize precision input handler.

        Args:
            settings: Input configuration (default: standard CAD settings)
        """
        self.settings = settings or InputSettings()
        self.precision_math = PrecisionMath()
        self.validator = PrecisionValidator()
        self.logger = logging.getLogger(__name__)

        # Input state
        self.current_mode = InputMode.FREEHAND
        self.last_input_event: Optional[InputEvent] = None
        self.input_history: List[InputEvent] = []

        # Callbacks
        self.on_coordinate_input: Optional[Callable[[PrecisionCoordinate], None]] = None
        self.on_input_validation: Optional[Callable[[InputEvent], None]] = None
        self.on_precision_feedback: Optional[Callable[[str, Any], None]] = None

        # Setup logging
        self._setup_logging()

    def _setup_logging(self):
        """Setup logging for input operations."""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def set_input_mode(self, mode: InputMode):
        """Set the current input mode."""
        self.current_mode = mode
        self.logger.info(f"Input mode changed to: {mode.value}")

    def set_coordinate_callback(self, callback: Callable[[PrecisionCoordinate], None]):
        """Set callback for coordinate input events."""
        self.on_coordinate_input = callback

    def set_validation_callback(self, callback: Callable[[InputEvent], None]):
        """Set callback for input validation events."""
        self.on_input_validation = callback

    def set_feedback_callback(self, callback: Callable[[str, Any], None]):
        """Set callback for precision feedback events."""
        self.on_precision_feedback = callback

    def handle_mouse_input(
        self, x: float, y: float, z: float = 0.0, event_type: str = "move"
    ) -> Optional[PrecisionCoordinate]:
        """
        Handle mouse input with precision validation.

        Args:
            x, y, z: Mouse coordinates
            event_type: Type of mouse event (move, click, drag, etc.)
            z: Z coordinate (default: 0.0)

        Returns:
            PrecisionCoordinate: Validated coordinate or None if invalid
        """
        # Create input event
        event = InputEvent(
            event_type=event_type,
            timestamp=time.time(),
            coordinates=(x, y, z),
            input_type=InputType.MOUSE,
            input_mode=self.current_mode,
        )

        # Apply input mode processing
        processed_coordinates = self._process_input_coordinates(x, y, z)

        # Create precision coordinate
        try:
            precision_coord = PrecisionCoordinate(*processed_coordinates)
            event.precision_coordinate = precision_coord

            # Validate coordinate
            validation_results = self.validator.validate_coordinate(precision_coord)
            event.validation_results = validation_results
            event.is_valid = all(result.is_valid for result in validation_results)

            # Store event
            self.last_input_event = event
            self.input_history.append(event)

            # Provide feedback
            if event.is_valid:
                self._provide_precision_feedback(
                    "mouse_input_valid",
                    {"coordinate": precision_coord, "mode": self.current_mode.value},
                )

                # Call coordinate callback
                if self.on_coordinate_input:
                    self.on_coordinate_input(precision_coord)

                return precision_coord
            else:
                self._provide_precision_feedback(
                    "mouse_input_invalid",
                    {
                        "coordinate": precision_coord,
                        "validation_results": validation_results,
                    },
                )

                if self.settings.strict_mode:
                    self.logger.warning(f"Invalid mouse input: {precision_coord}")

                return None

        except Exception as e:
            self.logger.error(f"Error processing mouse input: {e}")
            return None

    def handle_touch_input(
        self, x: float, y: float, z: float = 0.0, event_type: str = "touch"
    ) -> Optional[PrecisionCoordinate]:
        """
        Handle touch input with precision validation.

        Args:
            x, y, z: Touch coordinates
            event_type: Type of touch event (touch, drag, etc.)
            z: Z coordinate (default: 0.0)

        Returns:
            PrecisionCoordinate: Validated coordinate or None if invalid
        """
        # Apply touch sensitivity
        x *= self.settings.touch_sensitivity
        y *= self.settings.touch_sensitivity

        # Create input event
        event = InputEvent(
            event_type=event_type,
            timestamp=time.time(),
            coordinates=(x, y, z),
            input_type=InputType.TOUCH,
            input_mode=self.current_mode,
        )

        # Apply input mode processing
        processed_coordinates = self._process_input_coordinates(x, y, z)

        # Create precision coordinate
        try:
            precision_coord = PrecisionCoordinate(*processed_coordinates)
            event.precision_coordinate = precision_coord

            # Validate coordinate
            validation_results = self.validator.validate_coordinate(precision_coord)
            event.validation_results = validation_results
            event.is_valid = all(result.is_valid for result in validation_results)

            # Store event
            self.last_input_event = event
            self.input_history.append(event)

            # Provide feedback
            if event.is_valid:
                self._provide_precision_feedback(
                    "touch_input_valid",
                    {"coordinate": precision_coord, "mode": self.current_mode.value},
                )

                # Call coordinate callback
                if self.on_coordinate_input:
                    self.on_coordinate_input(precision_coord)

                return precision_coord
            else:
                self._provide_precision_feedback(
                    "touch_input_invalid",
                    {
                        "coordinate": precision_coord,
                        "validation_results": validation_results,
                    },
                )

                if self.settings.strict_mode:
                    self.logger.warning(f"Invalid touch input: {precision_coord}")

                return None

        except Exception as e:
            self.logger.error(f"Error processing touch input: {e}")
            return None

    def handle_keyboard_input(
        self, x_str: str, y_str: str, z_str: str = "0.0"
    ) -> Optional[PrecisionCoordinate]:
        """
        Handle keyboard input for exact coordinates.

        Args:
            x_str: X coordinate as string
            y_str: Y coordinate as string
            z_str: Z coordinate as string (default: "0.0")

        Returns:
            PrecisionCoordinate: Validated coordinate or None if invalid
        """
        try:
            # Parse coordinate strings
            x = float(x_str)
            y = float(y_str)
            z = float(z_str)

            # Create input event
            event = InputEvent(
                event_type="keyboard",
                timestamp=time.time(),
                coordinates=(x, y, z),
                input_type=InputType.KEYBOARD,
                input_mode=self.current_mode,
            )

            # Apply keyboard precision
            x = self.precision_math.round_to_precision(
                x, self.settings.keyboard_precision
            )
            y = self.precision_math.round_to_precision(
                y, self.settings.keyboard_precision
            )
            z = self.precision_math.round_to_precision(
                z, self.settings.keyboard_precision
            )

            # Create precision coordinate
            precision_coord = PrecisionCoordinate(x, y, z)
            event.precision_coordinate = precision_coord

            # Validate coordinate
            validation_results = self.validator.validate_coordinate(precision_coord)
            event.validation_results = validation_results
            event.is_valid = all(result.is_valid for result in validation_results)

            # Store event
            self.last_input_event = event
            self.input_history.append(event)

            # Provide feedback
            if event.is_valid:
                self._provide_precision_feedback(
                    "keyboard_input_valid",
                    {
                        "coordinate": precision_coord,
                        "precision": self.settings.keyboard_precision,
                    },
                )

                # Call coordinate callback
                if self.on_coordinate_input:
                    self.on_coordinate_input(precision_coord)

                return precision_coord
            else:
                self._provide_precision_feedback(
                    "keyboard_input_invalid",
                    {
                        "coordinate": precision_coord,
                        "validation_results": validation_results,
                    },
                )

                if self.settings.strict_mode:
                    self.logger.warning(f"Invalid keyboard input: {precision_coord}")

                return None

        except ValueError as e:
            self.logger.error(f"Invalid keyboard input format: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error processing keyboard input: {e}")
            return None

    def _process_input_coordinates(
        self, x: float, y: float, z: float
    ) -> Tuple[float, float, float]:
        """
        Process input coordinates based on current input mode.

        Args:
            x, y, z: Raw input coordinates

        Returns:
            Tuple[float, float, float]: Processed coordinates
        """
        if self.current_mode == InputMode.FREEHAND:
            # No processing for freehand mode
            return (x, y, z)

        elif self.current_mode == InputMode.GRID_SNAP:
            # Snap to grid
            if self.settings.enable_grid_snap:
                x = self._snap_to_grid(x, self.settings.grid_snap_precision)
                y = self._snap_to_grid(y, self.settings.grid_snap_precision)
                z = self._snap_to_grid(z, self.settings.grid_snap_precision)
            return (x, y, z)

        elif self.current_mode == InputMode.ANGLE_SNAP:
            # Snap to angle
            if self.settings.enable_angle_snap:
                angle = math.atan2(y, x)
                snapped_angle = self._snap_to_angle(
                    angle, self.settings.angle_snap_precision
                )
                distance = math.sqrt(x**2 + y**2)
                x = distance * math.cos(snapped_angle)
                y = distance * math.sin(snapped_angle)
            return (x, y, z)

        elif self.current_mode == InputMode.PRECISION_MODE:
            # Apply precision rounding
            x = self.precision_math.round_to_precision(
                x, self.settings.default_precision
            )
            y = self.precision_math.round_to_precision(
                y, self.settings.default_precision
            )
            z = self.precision_math.round_to_precision(
                z, self.settings.default_precision
            )
            return (x, y, z)

        else:
            # Default to freehand
            return (x, y, z)

    def _snap_to_grid(self, value: float, grid_spacing: Decimal) -> float:
        """
        Snap value to grid.

        Args:
            value: Value to snap
            grid_spacing: Grid spacing

        Returns:
            float: Snapped value
        """
        grid_spacing_float = float(grid_spacing)
        return round(value / grid_spacing_float) * grid_spacing_float

    def _snap_to_angle(self, angle: float, angle_snap: Decimal) -> float:
        """
        Snap angle to nearest snap angle.

        Args:
            angle: Angle in radians
            angle_snap: Snap angle in degrees

        Returns:
            float: Snapped angle in radians
        """
        angle_degrees = math.degrees(angle)
        snap_degrees = float(angle_snap)
        snapped_degrees = round(angle_degrees / snap_degrees) * snap_degrees
        return math.radians(snapped_degrees)

    def _provide_precision_feedback(self, feedback_type: str, data: Dict[str, Any]):
        """
        Provide precision feedback to user.

        Args:
            feedback_type: Type of feedback
            data: Feedback data
        """
        if not self.settings.provide_visual_feedback:
            return

        # Call feedback callback if set
        if self.on_precision_feedback:
            self.on_precision_feedback(feedback_type, data)

        # Log feedback
        if self.settings.log_input_errors:
            if "invalid" in feedback_type:
                self.logger.warning(f"Precision feedback: {feedback_type} - {data}")
            else:
                self.logger.info(f"Precision feedback: {feedback_type} - {data}")

    def get_input_statistics(self) -> Dict[str, Any]:
        """Get input statistics and analysis."""
        if not self.input_history:
            return {"total_inputs": 0}

        total_inputs = len(self.input_history)
        valid_inputs = sum(1 for event in self.input_history if event.is_valid)
        invalid_inputs = total_inputs - valid_inputs

        # Group by input type
        by_input_type = {}
        for event in self.input_history:
            input_type = event.input_type.value
            if input_type not in by_input_type:
                by_input_type[input_type] = {"total": 0, "valid": 0, "invalid": 0}

            by_input_type[input_type]["total"] += 1
            if event.is_valid:
                by_input_type[input_type]["valid"] += 1
            else:
                by_input_type[input_type]["invalid"] += 1

        # Group by input mode
        by_input_mode = {}
        for event in self.input_history:
            input_mode = event.input_mode.value
            if input_mode not in by_input_mode:
                by_input_mode[input_mode] = {"total": 0, "valid": 0, "invalid": 0}

            by_input_mode[input_mode]["total"] += 1
            if event.is_valid:
                by_input_mode[input_mode]["valid"] += 1
            else:
                by_input_mode[input_mode]["invalid"] += 1

        return {
            "total_inputs": total_inputs,
            "valid_inputs": valid_inputs,
            "invalid_inputs": invalid_inputs,
            "success_rate": valid_inputs / total_inputs if total_inputs > 0 else 0,
            "by_input_type": by_input_type,
            "by_input_mode": by_input_mode,
            "current_mode": self.current_mode.value,
            "settings": {
                "default_precision": str(self.settings.default_precision),
                "grid_snap_precision": str(self.settings.grid_snap_precision),
                "angle_snap_precision": str(self.settings.angle_snap_precision),
                "validate_input": self.settings.validate_input,
                "strict_mode": self.settings.strict_mode,
            },
        }

    def clear_input_history(self):
        """Clear input history."""
        self.input_history.clear()
        self.last_input_event = None
        self.logger.info("Input history cleared")

    def export_input_report(self, filename: str):
        """Export input statistics to a JSON file."""
        import json

        report = {
            "input_statistics": self.get_input_statistics(),
            "input_history": [
                {
                    "event_type": event.event_type,
                    "timestamp": event.timestamp,
                    "coordinates": event.coordinates,
                    "input_type": event.input_type.value,
                    "input_mode": event.input_mode.value,
                    "precision_coordinate": (
                        str(event.precision_coordinate)
                        if event.precision_coordinate
                        else None
                    ),
                    "is_valid": event.is_valid,
                    "validation_results": [
                        result.to_dict() for result in event.validation_results
                    ],
                }
                for event in self.input_history
            ],
        }

        with open(filename, "w") as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"Input report exported to: {filename}")


class PrecisionInputValidator:
    """
    Specialized validator for precision input operations.
    """

    def __init__(self, precision_math: Optional[PrecisionMath] = None):
        """
        Initialize precision input validator.

        Args:
            precision_math: Precision math instance (default: new instance)
        """
        self.precision_math = precision_math or PrecisionMath()

    def validate_input_coordinates(
        self, x: float, y: float, z: float = 0.0, precision: Optional[Decimal] = None
    ) -> bool:
        """
        Validate input coordinates for precision requirements.

        Args:
            x, y, z: Input coordinates
            precision: Required precision (default: millimeter precision)

        Returns:
            bool: True if coordinates meet precision requirements
        """
        if precision is None:
            precision = self.precision_math.settings.default_precision

        return (
            self.precision_math.validate_precision(x, precision)
            and self.precision_math.validate_precision(y, precision)
            and self.precision_math.validate_precision(z, precision)
        )

    def validate_input_range(
        self, x: float, y: float, z: float = 0.0, max_range: float = 1e6
    ) -> bool:
        """
        Validate input coordinates are within acceptable range.

        Args:
            x, y, z: Input coordinates
            max_range: Maximum allowed coordinate value

        Returns:
            bool: True if coordinates are within range
        """
        return abs(x) <= max_range and abs(y) <= max_range and abs(z) <= max_range

    def validate_input_format(self, x_str: str, y_str: str, z_str: str = "0.0") -> bool:
        """
        Validate input string format for keyboard input.

        Args:
            x_str, y_str, z_str: Coordinate strings

        Returns:
            bool: True if strings are valid coordinate format
        """
        try:
            float(x_str)
            float(y_str)
            float(z_str)
            return True
        except ValueError:
            return False


# Example usage and testing
if __name__ == "__main__":
    # Create precision input handler
    handler = PrecisionInputHandler()

    # Set up callbacks
    def on_coordinate_input(coordinate):
        print(f"Coordinate input: {coordinate}")

    def on_precision_feedback(feedback_type, data):
        print(f"Precision feedback: {feedback_type} - {data}")

    handler.set_coordinate_callback(on_coordinate_input)
    handler.set_feedback_callback(on_precision_feedback)

    # Test mouse input
    print("Testing mouse input...")
    coordinate = handler.handle_mouse_input(1.000, 2.000, 3.000, "click")
    print(f"Mouse input result: {coordinate}")

    # Test touch input
    print("\nTesting touch input...")
    coordinate = handler.handle_touch_input(4.000, 5.000, 6.000, "touch")
    print(f"Touch input result: {coordinate}")

    # Test keyboard input
    print("\nTesting keyboard input...")
    coordinate = handler.handle_keyboard_input("7.000", "8.000", "9.000")
    print(f"Keyboard input result: {coordinate}")

    # Test grid snap mode
    print("\nTesting grid snap mode...")
    handler.set_input_mode(InputMode.GRID_SNAP)
    coordinate = handler.handle_mouse_input(1.234, 2.567, 3.890, "move")
    print(f"Grid snap result: {coordinate}")

    # Get input statistics
    stats = handler.get_input_statistics()
    print(f"\nInput statistics: {stats}")
