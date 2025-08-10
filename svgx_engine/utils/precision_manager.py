"""
SVGX Engine - Precision Manager

Implements CTO tiered precision requirements:
- UI: 0.1mm precision (for display and interaction)
- Edit: 0.01mm precision (for editing operations)
- Compute: 0.001mm precision (for calculations and simulation)

Uses fixed-point math for UI state to avoid float precision issues.
"""

import math
import decimal
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PrecisionLevel(Enum):
    """Precision levels as defined by CTO."""
    UI = "ui"           # 0.1mm precision
    EDIT = "edit"       # 0.01mm precision
    COMPUTE = "compute" # 0.001mm precision


@dataclass
class PrecisionConfig:
    """Configuration for precision management."""
    ui_precision_mm: float = 0.1
    edit_precision_mm: float = 0.01
    compute_precision_mm: float = 0.001
    use_fixed_point: bool = True
    fixed_point_scale: int = 1000  # Scale for fixed-point arithmetic


class FixedPointNumber:
    """Fixed-point number implementation to avoid float precision issues."""

    def __init__(self, value: Union[int, float, str], scale: int = 1000):
    """
    Perform __init__ operation

Args:
        value: Description of value
        scale: Description of scale

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        self.scale = scale
        if isinstance(value, str):
            # Parse string value
            self.value = int(float(value) * scale)
        elif isinstance(value, float):
            self.value = int(value * scale)
        else:
    """
    Perform __add__ operation

Args:
        other: Description of other

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __add__(param)
        print(result)
    """
            self.value = int(value * scale)

    def __add__(self, other):
        """Add another FixedPointNumber or numeric value"""
        if isinstance(other, FixedPointNumber):
            return FixedPointNumber(self.value + other.value, self.scale)
        else:
            return FixedPointNumber(self.value + int(other * self.scale), self.scale)

    def __sub__(self, other):
        """Subtract another FixedPointNumber or numeric value"""
        if isinstance(other, FixedPointNumber):
            return FixedPointNumber(self.value - other.value, self.scale)
        else:
            return FixedPointNumber(self.value - int(other * self.scale), self.scale)

    def __mul__(self, other):
        """Multiply by another FixedPointNumber or numeric value"""
        if isinstance(other, FixedPointNumber):
            return FixedPointNumber(self.value * other.value // self.scale, self.scale)
        else:
            return FixedPointNumber(self.value * int(other), self.scale)

    def __truediv__(self, other):
        """Divide by another FixedPointNumber or numeric value"""
        if isinstance(other, FixedPointNumber):
            return FixedPointNumber(self.value * self.scale // other.value, self.scale)
        else:
            return FixedPointNumber(self.value // int(other), self.scale)

    def __lt__(self, other):
        """Check if this value is less than another"""
        if isinstance(other, FixedPointNumber):
            return self.value < other.value
        else:
            return self.value < int(other * self.scale)

    def __le__(self, other):
        if isinstance(other, FixedPointNumber):
            return self.value <= other.value
        else:
            return self.value <= int(other * self.scale)

    def __eq__(self, other):
        if isinstance(other, FixedPointNumber):
            return self.value == other.value
        else:
            return self.value == int(other * self.scale)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __gt__(self, other):
        if isinstance(other, FixedPointNumber):
            return self.value > other.value
        else:
    """
    Perform __str__ operation

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __str__(param)
        print(result)
    """
            return self.value > int(other * self.scale)

    def __ge__(self, other):
        if isinstance(other, FixedPointNumber):
            return self.value >= other.value
        else:
            return self.value >= int(other * self.scale)

    def to_float(self) -> float:
        """Convert to float."""
        return self.value / self.scale

    def to_int(self) -> int:
        """Convert to integer."""
        return self.value // self.scale

    def round_to_precision(self, precision_level: PrecisionLevel) -> 'FixedPointNumber':
        """Round to specified precision level."""
        if precision_level == PrecisionLevel.UI:
            precision = 0.1
        elif precision_level == PrecisionLevel.EDIT:
            precision = 0.01
        else:  # COMPUTE
            precision = 0.001

        precision_scale = int(1 / precision)
        rounded_value = round(self.value / precision_scale) * precision_scale
        return FixedPointNumber(rounded_value / self.scale, self.scale)

    def __str__(self):
        return f"{self.to_float():.3f}"

    def __repr__(self):
        return f"FixedPointNumber({self.to_float():.3f}, scale={self.scale})
class SVGXPrecisionManager:
    """
    SVGX Precision Manager.

    Manages tiered precision operations according to CTO requirements.
    """

    def __init__(self, config: Optional[PrecisionConfig] = None):
        """Initialize the precision manager."""
        self.config = config or PrecisionConfig()
        self.current_level = PrecisionLevel.UI
        self.precision_values = {
            PrecisionLevel.UI: self.config.ui_precision_mm,
            PrecisionLevel.EDIT: self.config.edit_precision_mm,
            PrecisionLevel.COMPUTE: self.config.compute_precision_mm
        }

        logger.info(f"SVGX Precision Manager initialized with config: {self.config}")

    def set_precision_level(self, level: PrecisionLevel):
        """Set the current precision level."""
        self.current_level = level
        logger.info(f"Precision level set to: {level.value}")

    def get_precision_value(self, level: Optional[PrecisionLevel] = None) -> float:
        """Get precision value for the specified level."""
        target_level = level or self.current_level
        return self.precision_values[target_level]

    def round_coordinates(self, coordinates: Dict[str, float],
                         level: Optional[PrecisionLevel] = None) -> Dict[str, float]:
        """
        Round coordinates to the specified precision level.

        Args:
            coordinates: Dictionary with x, y, z coordinates
            level: Precision level (defaults to current level)

        Returns:
            Rounded coordinates
        """
        target_level = level or self.current_level
        precision = self.get_precision_value(target_level)

        rounded_coords = {}
        for axis, value in coordinates.items():
            if self.config.use_fixed_point:
                # Use fixed-point arithmetic
                fp_value = FixedPointNumber(value, self.config.fixed_point_scale)
                rounded_fp = fp_value.round_to_precision(target_level)
                rounded_coords[axis] = rounded_fp.to_float()
            else:
                # Use decimal arithmetic for high precision
                decimal_value = decimal.Decimal(str(value)
                rounded_coords[axis] = float(round(decimal_value / precision) * precision)

        return rounded_coords

    def snap_to_grid(self, coordinates: Dict[str, float],
                     grid_size: Optional[float] = None) -> Dict[str, float]:
        """
        Snap coordinates to a grid.

        Args:
            coordinates: Dictionary with x, y, z coordinates
            grid_size: Grid size in mm (defaults to current precision)

        Returns:
            Snapped coordinates
        """
        if grid_size is None:
            grid_size = self.get_precision_value()

        snapped_coords = {}
        for axis, value in coordinates.items():
            if self.config.use_fixed_point:
                fp_value = FixedPointNumber(value, self.config.fixed_point_scale)
                grid_scale = int(1 / grid_size)
                snapped_value = round(fp_value.value / grid_scale) * grid_scale
                snapped_coords[axis] = snapped_value / self.config.fixed_point_scale
            else:
                snapped_coords[axis] = round(value / grid_size) * grid_size

        return snapped_coords

    def calculate_distance(self, point1: Dict[str, float],
                          point2: Dict[str, float]) -> float:
        """
        Calculate distance between two points with appropriate precision.

        Args:
            point1: First point coordinates
            point2: Second point coordinates

        Returns:
            Distance in mm
        """
        dx = point2.get('x', 0) - point1.get('x', 0)
        dy = point2.get('y', 0) - point1.get('y', 0)
        dz = point2.get('z', 0) - point1.get('z', 0)

        if self.config.use_fixed_point:
            fp_dx = FixedPointNumber(dx, self.config.fixed_point_scale)
            fp_dy = FixedPointNumber(dy, self.config.fixed_point_scale)
            fp_dz = FixedPointNumber(dz, self.config.fixed_point_scale)

            # Calculate distance using fixed-point arithmetic
            distance_squared = fp_dx * fp_dx + fp_dy * fp_dy + fp_dz * fp_dz
            distance = math.sqrt(distance_squared.to_float()
        else:
            distance = math.sqrt(dx*dx + dy*dy + dz*dz)

        # Round to current precision
        return self.round_value(distance)

    def round_value(self, value: float, level: Optional[PrecisionLevel] = None) -> float:
        """
        Round a value to the specified precision level.

        Args:
            value: Value to round
            level: Precision level (defaults to current level)

        Returns:
            Rounded value
        """
        target_level = level or self.current_level
        precision = self.get_precision_value(target_level)

        if self.config.use_fixed_point:
            fp_value = FixedPointNumber(value, self.config.fixed_point_scale)
            rounded_fp = fp_value.round_to_precision(target_level)
            return rounded_fp.to_float()
        else:
            return round(value / precision) * precision

    def validate_precision(self, value: float, level: Optional[PrecisionLevel] = None) -> bool:
        """
        Validate that a value meets precision requirements.

        Args:
            value: Value to validate
            level: Precision level to check against

        Returns:
            True if value meets precision requirements
        """
        target_level = level or self.current_level
        precision = self.get_precision_value(target_level)

        # Check if value is a multiple of the precision
        remainder = abs(value) % precision
        return remainder < precision / 2 or abs(remainder - precision) < precision / 2

    def convert_precision(self, value: float, from_level: PrecisionLevel,
                         to_level: PrecisionLevel) -> float:
        """
        Convert a value from one precision level to another.

        Args:
            value: Value to convert
            from_level: Source precision level
            to_level: Target precision level

        Returns:
            Converted value
        """
        # First round to source precision
        source_precision = self.get_precision_value(from_level)
        rounded_value = round(value / source_precision) * source_precision

        # Then round to target precision
        target_precision = self.get_precision_value(to_level)
        converted_value = round(rounded_value / target_precision) * target_precision

        return converted_value

    def get_precision_info(self) -> Dict[str, Any]:
        """Get information about current precision settings."""
        return {
            "current_level": self.current_level.value,
            "precision_values": {
                level.value: value for level, value in self.precision_values.items()
            },
            "use_fixed_point": self.config.use_fixed_point,
            "fixed_point_scale": self.config.fixed_point_scale
        }


def create_precision_manager(config: Optional[PrecisionConfig] = None) -> SVGXPrecisionManager:
    """Create and return a configured SVGX Precision Manager."""
    return SVGXPrecisionManager(config)
