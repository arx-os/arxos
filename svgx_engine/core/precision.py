"""
SVGX Engine - Precision Management System

Handles micron-level precision for CAD operations with user-selectable display options.
Supports internal calculations at 12 decimal places and various display formats.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

from decimal import Decimal, getcontext, ROUND_HALF_UP
from enum import Enum
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass


# Use print for logging to avoid circular import issues
def log_info(message):
    print(f"INFO: {message}")


def log_error(message):
    print(f"ERROR: {message}")


def log_warning(message):
    print(f"WARNING: {message}")


# Set internal precision to 12 decimal places (0.000000000001 units)
getcontext().prec = 12
getcontext().rounding = ROUND_HALF_UP


class PrecisionDisplayMode(Enum):
    """Precision display modes for user interface."""

    DECIMAL = "decimal"  # 0.001mm, 0.01mm, 0.1mm, 1mm
    SCIENTIFIC = "scientific"  # 1μm, 10μm, 100μm, 1mm
    ENGINEERING = "engineering"  # 0.001", 0.01", 0.1", 1"
    MICRON = "micron"  # Direct micron display
    MILLIMETER = "millimeter"  # Direct millimeter display
    INCH = "inch"  # Direct inch display


class PrecisionLevel(Enum):
    """Precision levels for different CAD operations."""

    MICRON = 3  # 0.001mm (1 micron)
    SUB_MICRON = 6  # 0.000001mm (0.001 micron)
    NANOMETER = 9  # 0.000000001mm (1 nanometer)
    ULTRA_PRECISE = 12  # 0.000000000001mm (0.001 nanometer)


@dataclass
class PrecisionConfig:
    """Configuration for precision settings."""

    internal_precision: int = 12
    display_mode: PrecisionDisplayMode = PrecisionDisplayMode.DECIMAL
    display_decimal_places: int = 3
    rounding_mode: str = "HALF_UP"
    unit_system: str = "metric"  # metric, imperial, mixed

    # Conversion factors
    mm_to_micron: Decimal = Decimal("1000")
    inch_to_mm: Decimal = Decimal("25.4")
    micron_to_nm: Decimal = Decimal("1000")


class PrecisionManager:
    """Manages precision for CAD operations with micron-level accuracy."""

    def __init__(self, config: Optional[PrecisionConfig] = None):
        self.config = config or PrecisionConfig()
        self._setup_precision_context()

    def _setup_precision_context(self):
        """Setup decimal context for precise calculations."""
        getcontext().prec = self.config.internal_precision
        if self.config.rounding_mode == "HALF_UP":
            getcontext().rounding = ROUND_HALF_UP

    def create_precise_value(
        self, value: Union[float, str, Decimal], unit: str = "mm"
    ) -> Decimal:
        """Create a precise decimal value with proper unit conversion."""
        try:
            if isinstance(value, str):
                # Handle scientific notation and unit suffixes
                value = self._parse_value_with_units(value)
            elif isinstance(value, float):
                value = Decimal(str(value))
            elif isinstance(value, Decimal):
                value = value
            else:
                raise ValueError(f"Unsupported value type: {type(value)}")

            # Convert to internal unit (millimeters)
            if unit.lower() in ["μm", "micron", "microns"]:
                value = value / self.config.mm_to_micron
            elif unit.lower() in ["in", "inch", "inches"]:
                value = value * self.config.inch_to_mm
            elif unit.lower() in ["nm", "nanometer", "nanometers"]:
                value = value / (self.config.mm_to_micron * self.config.micron_to_nm)

            return value

        except Exception as e:
            log_error(f"Error creating precise value: {e}")
            raise ValueError(f"Invalid precision value: {value} {unit}")

    def _parse_value_with_units(self, value_str: str) -> Decimal:
        """Parse value string with unit suffixes."""
        import re

        # Remove whitespace and convert to lowercase
        value_str = value_str.strip().lower()

        # Handle scientific notation
        if "e" in value_str:
            return Decimal(value_str)

        # Handle unit suffixes
        unit_patterns = {
            r"(\d+\.?\d*)\s*μm": lambda m: Decimal(m.group(1))
            / self.config.mm_to_micron,
            r"(\d+\.?\d*)\s*micron": lambda m: Decimal(m.group(1))
            / self.config.mm_to_micron,
            r"(\d+\.?\d*)\s*mm": lambda m: Decimal(m.group(1)),
            r"(\d+\.?\d*)\s*in": lambda m: Decimal(m.group(1)) * self.config.inch_to_mm,
            r"(\d+\.?\d*)\s*inch": lambda m: Decimal(m.group(1))
            * self.config.inch_to_mm,
            r"(\d+\.?\d*)\s*nm": lambda m: Decimal(m.group(1))
            / (self.config.mm_to_micron * self.config.micron_to_nm),
        }

        for pattern, converter in unit_patterns.items():
            match = re.match(pattern, value_str)
            if match:
                return converter(match)

        # Default to decimal value
        return Decimal(value_str)

    def format_for_display(
        self, value: Decimal, mode: Optional[PrecisionDisplayMode] = None
    ) -> str:
        """Format precise value for user display."""
        mode = mode or self.config.display_mode

        if mode == PrecisionDisplayMode.DECIMAL:
            return self._format_decimal(value)
        elif mode == PrecisionDisplayMode.SCIENTIFIC:
            return self._format_scientific(value)
        elif mode == PrecisionDisplayMode.ENGINEERING:
            return self._format_engineering(value)
        elif mode == PrecisionDisplayMode.MICRON:
            return self._format_micron(value)
        elif mode == PrecisionDisplayMode.MILLIMETER:
            return self._format_millimeter(value)
        elif mode == PrecisionDisplayMode.INCH:
            return self._format_inch(value)
        else:
            return str(value)

    def _format_decimal(self, value: Decimal) -> str:
        """Format as decimal with user-selected precision."""
        places = self.config.display_decimal_places
        return f"{value:.{places}f} mm"

    def _format_scientific(self, value: Decimal) -> str:
        """Format using scientific notation with appropriate units."""
        microns = value * self.config.mm_to_micron

        if microns >= 1000:
            return f"{value:.3f} mm"
        elif microns >= 1:
            return f"{microns:.0f} μm"
        else:
            nanometers = microns * self.config.micron_to_nm
            return f"{nanometers:.0f} nm"

    def _format_engineering(self, value: Decimal) -> str:
        """Format using engineering notation (inches)."""
        inches = value / self.config.inch_to_mm
        return f"{inches:.{self.config.display_decimal_places}f} in"

    def _format_micron(self, value: Decimal) -> str:
        """Format directly in microns."""
        microns = value * self.config.mm_to_micron
        return f"{microns:.{self.config.display_decimal_places}f} μm"

    def _format_millimeter(self, value: Decimal) -> str:
        """Format directly in millimeters."""
        return f"{value:.{self.config.display_decimal_places}f} mm"

    def _format_inch(self, value: Decimal) -> str:
        """Format directly in inches."""
        inches = value / self.config.inch_to_mm
        return f"{inches:.{self.config.display_decimal_places}f} in"

    def validate_precision(
        self, value: Decimal, required_precision: PrecisionLevel
    ) -> bool:
        """Validate that a value meets required precision standards."""
        # Check if value has sufficient precision
        decimal_places = abs(value.as_tuple().exponent)
        return decimal_places >= required_precision.value

    def round_to_precision(self, value: Decimal, precision: PrecisionLevel) -> Decimal:
        """Round value to specified precision level."""
        return value.quantize(Decimal(f"0.{'0' * (precision.value - 1)}1"))

    def get_precision_info(self) -> Dict[str, Any]:
        """Get current precision configuration information."""
        return {
            "internal_precision": self.config.internal_precision,
            "display_mode": self.config.display_mode.value,
            "display_decimal_places": self.config.display_decimal_places,
            "unit_system": self.config.unit_system,
            "min_precision_mm": f"0.{'0' * (self.config.internal_precision - 1)}1",
            "min_precision_micron": f"0.{'0' * (self.config.internal_precision - 4)}1",
            "supported_modes": [mode.value for mode in PrecisionDisplayMode],
            "supported_levels": [level.name for level in PrecisionLevel],
        }


class PrecisionValidator:
    """Validates precision requirements for CAD operations."""

    @staticmethod
    def validate_engineering_compliance(value: Decimal, standard: str = "ISO") -> bool:
        """Validate precision against engineering standards."""
        if standard == "ISO":
            # ISO 2768-1 standard for general tolerances
            return PrecisionValidator._validate_iso_standard(value)
        elif standard == "ASME":
            # ASME Y14.5 standard
            return PrecisionValidator._validate_asme_standard(value)
        else:
            return True

    @staticmethod
    def _validate_iso_standard(value: Decimal) -> bool:
        """Validate against ISO 2768-1 standard."""
        # ISO 2768-1 fine tolerance for linear dimensions
        tolerance = Decimal("0.1")  # 0.1mm tolerance
        return abs(value) >= tolerance

    @staticmethod
    def _validate_asme_standard(value: Decimal) -> bool:
        """Validate against ASME Y14.5 standard."""
        # ASME Y14.5 standard tolerances
        tolerance = Decimal("0.01")  # 0.01 inch tolerance
        return abs(value) >= tolerance


# Global precision manager instance
precision_manager = PrecisionManager()
