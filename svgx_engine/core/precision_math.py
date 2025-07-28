"""
Sub-Millimeter Float Precision System for CAD Applications

This module provides precision-aware mathematical operations using Decimal arithmetic
for sub-millimeter accuracy (0.001mm) required for professional CAD functionality.
"""

import math
import decimal
from decimal import Decimal, getcontext, ROUND_HALF_UP, ROUND_DOWN, ROUND_UP
from typing import Union, Tuple, Optional, List, Callable
from dataclasses import dataclass
import numpy as np
import logging

# Configure logging for precision operations
logger = logging.getLogger(__name__)

# Configure decimal precision for sub-millimeter accuracy
getcontext().prec = 12  # 12 decimal places for 0.001mm precision
getcontext().rounding = ROUND_HALF_UP  # Standard rounding for CAD applications

# Precision constants
MILLIMETER_PRECISION = Decimal('0.001')  # 0.001mm precision
MICRON_PRECISION = Decimal('0.000001')   # 1 micron precision
NANOMETER_PRECISION = Decimal('0.000000001')  # 1 nanometer precision

# Default precision for CAD operations
DEFAULT_PRECISION = MILLIMETER_PRECISION


@dataclass
class PrecisionSettings:
    """Configuration for precision-aware mathematical operations."""
    
    # Precision levels
    millimeter_precision: Decimal = MILLIMETER_PRECISION
    micron_precision: Decimal = MICRON_PRECISION
    nanometer_precision: Decimal = NANOMETER_PRECISION
    
    # Default precision for operations
    default_precision: Decimal = DEFAULT_PRECISION
    
    # Rounding modes
    rounding_mode: str = 'HALF_UP'  # HALF_UP, DOWN, UP
    
    # Error handling
    strict_mode: bool = True  # Raise errors for precision violations
    log_precision_errors: bool = True  # Log precision errors
    
    # Performance settings
    use_numpy_for_large_arrays: bool = True  # Use numpy for large calculations
    numpy_precision_threshold: int = 1000  # Use numpy for arrays larger than this
    
    def __post_init__(self):
        """Validate and configure precision settings."""
        self._validate_precision_settings()
        self._configure_rounding()
    
    def _validate_precision_settings(self):
        """Validate precision settings."""
        if self.millimeter_precision <= 0:
            raise ValueError("Millimeter precision must be positive")
        if self.micron_precision <= 0:
            raise ValueError("Micron precision must be positive")
        if self.nanometer_precision <= 0:
            raise ValueError("Nanometer precision must be positive")
        
        # Ensure precision hierarchy
        if self.millimeter_precision <= self.micron_precision:
            raise ValueError("Millimeter precision must be greater than micron precision")
        if self.micron_precision <= self.nanometer_precision:
            raise ValueError("Micron precision must be greater than nanometer precision")
    
    def _configure_rounding(self):
        """Configure rounding mode."""
        rounding_map = {
            'HALF_UP': ROUND_HALF_UP,
            'DOWN': ROUND_DOWN,
            'UP': ROUND_UP
        }
        
        if self.rounding_mode not in rounding_map:
            raise ValueError(f"Invalid rounding mode: {self.rounding_mode}")
        
        getcontext().rounding = rounding_map[self.rounding_mode]


class PrecisionMath:
    """
    Precision-aware mathematical operations for CAD applications.
    
    Provides sub-millimeter accuracy using Decimal arithmetic with
    comprehensive error handling and validation.
    """
    
    def __init__(self, settings: Optional[PrecisionSettings] = None):
        """
        Initialize precision math system.
        
        Args:
            settings: Precision configuration (default: standard CAD settings)
        """
        self.settings = settings or PrecisionSettings()
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging for precision operations."""
        if self.settings.log_precision_errors:
            logging.basicConfig(level=logging.INFO)
    
    def to_decimal(self, value: Union[float, int, str, Decimal]) -> Decimal:
        """
        Convert value to Decimal with precision validation.
        
        Args:
            value: Value to convert
            
        Returns:
            Decimal: Precision-aware decimal value
        """
        try:
            if isinstance(value, Decimal):
                return value
            elif isinstance(value, (int, float)):
                return Decimal(str(value))
            elif isinstance(value, str):
                return Decimal(value)
            else:
                raise TypeError(f"Cannot convert {type(value)} to Decimal")
        except (ValueError, decimal.InvalidOperation) as e:
            raise ValueError(f"Invalid value for Decimal conversion: {value}") from e
    
    def round_to_precision(self, value: Union[float, Decimal], 
                          precision: Optional[Decimal] = None) -> Decimal:
        """
        Round value to specified precision.
        
        Args:
            value: Value to round
            precision: Precision level (default: millimeter precision)
            
        Returns:
            Decimal: Rounded value
        """
        if precision is None:
            precision = self.settings.default_precision
        
        decimal_value = self.to_decimal(value)
        return decimal_value.quantize(precision)
    
    def validate_precision(self, value: Union[float, Decimal], 
                          precision: Optional[Decimal] = None) -> bool:
        """
        Validate that value meets precision requirements.
        
        Args:
            value: Value to validate
            precision: Required precision (default: millimeter precision)
            
        Returns:
            bool: True if value meets precision requirements
        """
        if precision is None:
            precision = self.settings.default_precision
        
        decimal_value = self.to_decimal(value)
        rounded_value = self.round_to_precision(decimal_value, precision)
        
        # Check if the difference is within precision tolerance
        difference = abs(decimal_value - rounded_value)
        return difference <= precision
    
    def add(self, a: Union[float, Decimal], b: Union[float, Decimal], 
            precision: Optional[Decimal] = None) -> Decimal:
        """
        Precision-aware addition.
        
        Args:
            a: First operand
            b: Second operand
            precision: Result precision (default: millimeter precision)
            
        Returns:
            Decimal: Precision-aware sum
        """
        if precision is None:
            precision = self.settings.default_precision
        
        decimal_a = self.to_decimal(a)
        decimal_b = self.to_decimal(b)
        
        result = decimal_a + decimal_b
        return self.round_to_precision(result, precision)
    
    def subtract(self, a: Union[float, Decimal], b: Union[float, Decimal], 
                precision: Optional[Decimal] = None) -> Decimal:
        """
        Precision-aware subtraction.
        
        Args:
            a: First operand
            b: Second operand
            precision: Result precision (default: millimeter precision)
            
        Returns:
            Decimal: Precision-aware difference
        """
        if precision is None:
            precision = self.settings.default_precision
        
        decimal_a = self.to_decimal(a)
        decimal_b = self.to_decimal(b)
        
        result = decimal_a - decimal_b
        return self.round_to_precision(result, precision)
    
    def multiply(self, a: Union[float, Decimal], b: Union[float, Decimal], 
                precision: Optional[Decimal] = None) -> Decimal:
        """
        Precision-aware multiplication.
        
        Args:
            a: First operand
            b: Second operand
            precision: Result precision (default: millimeter precision)
            
        Returns:
            Decimal: Precision-aware product
        """
        if precision is None:
            precision = self.settings.default_precision
        
        decimal_a = self.to_decimal(a)
        decimal_b = self.to_decimal(b)
        
        result = decimal_a * decimal_b
        return self.round_to_precision(result, precision)
    
    def divide(self, a: Union[float, Decimal], b: Union[float, Decimal], 
              precision: Optional[Decimal] = None) -> Decimal:
        """
        Precision-aware division.
        
        Args:
            a: Numerator
            b: Denominator
            precision: Result precision (default: millimeter precision)
            
        Returns:
            Decimal: Precision-aware quotient
            
        Raises:
            ZeroDivisionError: If denominator is zero
        """
        if precision is None:
            precision = self.settings.default_precision
        
        decimal_a = self.to_decimal(a)
        decimal_b = self.to_decimal(b)
        
        if decimal_b == 0:
            raise ZeroDivisionError("Division by zero")
        
        result = decimal_a / decimal_b
        return self.round_to_precision(result, precision)
    
    def sqrt(self, value: Union[float, Decimal], 
             precision: Optional[Decimal] = None) -> Decimal:
        """
        Precision-aware square root.
        
        Args:
            value: Value to take square root of
            precision: Result precision (default: millimeter precision)
            
        Returns:
            Decimal: Precision-aware square root
            
        Raises:
            ValueError: If value is negative
        """
        if precision is None:
            precision = self.settings.default_precision
        
        decimal_value = self.to_decimal(value)
        
        if decimal_value < 0:
            raise ValueError("Cannot take square root of negative number")
        
        result = decimal_value.sqrt()
        return self.round_to_precision(result, precision)
    
    def power(self, base: Union[float, Decimal], exponent: Union[float, Decimal], 
              precision: Optional[Decimal] = None) -> Decimal:
        """
        Precision-aware power operation.
        
        Args:
            base: Base value
            exponent: Exponent
            precision: Result precision (default: millimeter precision)
            
        Returns:
            Decimal: Precision-aware power result
        """
        if precision is None:
            precision = self.settings.default_precision
        
        decimal_base = self.to_decimal(base)
        decimal_exponent = self.to_decimal(exponent)
        
        result = decimal_base ** decimal_exponent
        return self.round_to_precision(result, precision)
    
    def distance_2d(self, x1: Union[float, Decimal], y1: Union[float, Decimal],
                    x2: Union[float, Decimal], y2: Union[float, Decimal],
                    precision: Optional[Decimal] = None) -> Decimal:
        """
        Calculate 2D distance with precision.
        
        Args:
            x1, y1: First point coordinates
            x2, y2: Second point coordinates
            precision: Result precision (default: millimeter precision)
            
        Returns:
            Decimal: Precision-aware distance
        """
        if precision is None:
            precision = self.settings.default_precision
        
        dx = self.subtract(x2, x1, precision)
        dy = self.subtract(y2, y1, precision)
        
        dx_squared = self.multiply(dx, dx, precision)
        dy_squared = self.multiply(dy, dy, precision)
        
        sum_squared = self.add(dx_squared, dy_squared, precision)
        return self.sqrt(sum_squared, precision)
    
    def distance_3d(self, x1: Union[float, Decimal], y1: Union[float, Decimal], z1: Union[float, Decimal],
                    x2: Union[float, Decimal], y2: Union[float, Decimal], z2: Union[float, Decimal],
                    precision: Optional[Decimal] = None) -> Decimal:
        """
        Calculate 3D distance with precision.
        
        Args:
            x1, y1, z1: First point coordinates
            x2, y2, z2: Second point coordinates
            precision: Result precision (default: millimeter precision)
            
        Returns:
            Decimal: Precision-aware 3D distance
        """
        if precision is None:
            precision = self.settings.default_precision
        
        dx = self.subtract(x2, x1, precision)
        dy = self.subtract(y2, y1, precision)
        dz = self.subtract(z2, z1, precision)
        
        dx_squared = self.multiply(dx, dx, precision)
        dy_squared = self.multiply(dy, dy, precision)
        dz_squared = self.multiply(dz, dz, precision)
        
        sum_squared = self.add(dx_squared, self.add(dy_squared, dz_squared, precision), precision)
        return self.sqrt(sum_squared, precision)
    
    def angle_between_points(self, x1: Union[float, Decimal], y1: Union[float, Decimal],
                            x2: Union[float, Decimal], y2: Union[float, Decimal],
                            precision: Optional[Decimal] = None) -> Decimal:
        """
        Calculate angle between two points with precision.
        
        Args:
            x1, y1: First point coordinates
            x2, y2: Second point coordinates
            precision: Result precision (default: millimeter precision)
            
        Returns:
            Decimal: Angle in radians with precision
        """
        if precision is None:
            precision = self.settings.default_precision
        
        dx = self.subtract(x2, x1, precision)
        dy = self.subtract(y2, y1, precision)
        
        # Use atan2 for proper quadrant handling
        angle = Decimal(str(math.atan2(float(dy), float(dx))))
        return self.round_to_precision(angle, precision)
    
    def is_equal(self, a: Union[float, Decimal], b: Union[float, Decimal], 
                tolerance: Optional[Decimal] = None) -> bool:
        """
        Precision-aware equality comparison.
        
        Args:
            a: First value
            b: Second value
            tolerance: Comparison tolerance (default: millimeter precision)
            
        Returns:
            bool: True if values are equal within tolerance
        """
        if tolerance is None:
            tolerance = self.settings.default_precision
        
        decimal_a = self.to_decimal(a)
        decimal_b = self.to_decimal(b)
        
        difference = abs(decimal_a - decimal_b)
        return difference <= tolerance
    
    def is_greater_than(self, a: Union[float, Decimal], b: Union[float, Decimal], 
                       tolerance: Optional[Decimal] = None) -> bool:
        """
        Precision-aware greater than comparison.
        
        Args:
            a: First value
            b: Second value
            tolerance: Comparison tolerance (default: millimeter precision)
            
        Returns:
            bool: True if a is greater than b by more than tolerance
        """
        if tolerance is None:
            tolerance = self.settings.default_precision
        
        decimal_a = self.to_decimal(a)
        decimal_b = self.to_decimal(b)
        
        difference = decimal_a - decimal_b
        return difference > tolerance
    
    def is_less_than(self, a: Union[float, Decimal], b: Union[float, Decimal], 
                    tolerance: Optional[Decimal] = None) -> bool:
        """
        Precision-aware less than comparison.
        
        Args:
            a: First value
            b: Second value
            tolerance: Comparison tolerance (default: millimeter precision)
            
        Returns:
            bool: True if a is less than b by more than tolerance
        """
        if tolerance is None:
            tolerance = self.settings.default_precision
        
        decimal_a = self.to_decimal(a)
        decimal_b = self.to_decimal(b)
        
        difference = decimal_b - decimal_a
        return difference > tolerance
    
    def min(self, values: List[Union[float, Decimal]], 
            precision: Optional[Decimal] = None) -> Decimal:
        """
        Find minimum value with precision.
        
        Args:
            values: List of values
            precision: Result precision (default: millimeter precision)
            
        Returns:
            Decimal: Minimum value with precision
        """
        if not values:
            raise ValueError("Cannot find minimum of empty list")
        
        if precision is None:
            precision = self.settings.default_precision
        
        decimal_values = [self.to_decimal(v) for v in values]
        min_value = min(decimal_values)
        return self.round_to_precision(min_value, precision)
    
    def max(self, values: List[Union[float, Decimal]], 
            precision: Optional[Decimal] = None) -> Decimal:
        """
        Find maximum value with precision.
        
        Args:
            values: List of values
            precision: Result precision (default: millimeter precision)
            
        Returns:
            Decimal: Maximum value with precision
        """
        if not values:
            raise ValueError("Cannot find maximum of empty list")
        
        if precision is None:
            precision = self.settings.default_precision
        
        decimal_values = [self.to_decimal(v) for v in values]
        max_value = max(decimal_values)
        return self.round_to_precision(max_value, precision)
    
    def sum(self, values: List[Union[float, Decimal]], 
            precision: Optional[Decimal] = None) -> Decimal:
        """
        Calculate sum with precision.
        
        Args:
            values: List of values to sum
            precision: Result precision (default: millimeter precision)
            
        Returns:
            Decimal: Sum with precision
        """
        if precision is None:
            precision = self.settings.default_precision
        
        decimal_values = [self.to_decimal(v) for v in values]
        total = sum(decimal_values)
        return self.round_to_precision(total, precision)
    
    def mean(self, values: List[Union[float, Decimal]], 
             precision: Optional[Decimal] = None) -> Decimal:
        """
        Calculate mean with precision.
        
        Args:
            values: List of values
            precision: Result precision (default: millimeter precision)
            
        Returns:
            Decimal: Mean with precision
        """
        if not values:
            raise ValueError("Cannot calculate mean of empty list")
        
        if precision is None:
            precision = self.settings.default_precision
        
        total = self.sum(values, precision)
        count = self.to_decimal(len(values))
        return self.divide(total, count, precision)
    
    def validate_geometric_calculation(self, operation: str, result: Decimal, 
                                     expected_precision: Optional[Decimal] = None) -> bool:
        """
        Validate geometric calculation result.
        
        Args:
            operation: Name of the geometric operation
            result: Calculation result
            expected_precision: Expected precision for validation
            
        Returns:
            bool: True if calculation meets precision requirements
        """
        if expected_precision is None:
            expected_precision = self.settings.default_precision
        
        is_valid = self.validate_precision(result, expected_precision)
        
        if not is_valid and self.settings.strict_mode:
            error_msg = f"Geometric calculation '{operation}' failed precision validation"
            if self.settings.log_precision_errors:
                logger.error(error_msg)
            raise PrecisionError(error_msg)
        
        return is_valid
    
    def handle_precision_error(self, operation: str, value: Union[float, Decimal], 
                             expected_precision: Optional[Decimal] = None) -> None:
        """
        Handle precision errors with logging and optional exceptions.
        
        Args:
            operation: Name of the operation that failed
            value: Value that failed precision validation
            expected_precision: Expected precision level
        """
        if expected_precision is None:
            expected_precision = self.settings.default_precision
        
        error_msg = f"Precision error in '{operation}': value {value} does not meet precision {expected_precision}"
        
        if self.settings.log_precision_errors:
            logger.warning(error_msg)
        
        if self.settings.strict_mode:
            raise PrecisionError(error_msg)


class PrecisionError(Exception):
    """Exception raised for precision-related errors."""
    pass


class PrecisionValidator:
    """
    Utility class for precision validation operations.
    """
    
    def __init__(self, precision_math: Optional[PrecisionMath] = None):
        """
        Initialize precision validator.
        
        Args:
            precision_math: Precision math instance (default: new instance)
        """
        self.precision_math = precision_math or PrecisionMath()
    
    def validate_coordinate_precision(self, x: Union[float, Decimal], y: Union[float, Decimal], 
                                    z: Union[float, Decimal] = 0, 
                                    precision: Optional[Decimal] = None) -> bool:
        """
        Validate coordinate precision.
        
        Args:
            x, y, z: Coordinate values
            precision: Required precision (default: millimeter precision)
            
        Returns:
            bool: True if coordinates meet precision requirements
        """
        if precision is None:
            precision = self.precision_math.settings.default_precision
        
        x_valid = self.precision_math.validate_precision(x, precision)
        y_valid = self.precision_math.validate_precision(y, precision)
        z_valid = self.precision_math.validate_precision(z, precision)
        
        return x_valid and y_valid and z_valid
    
    def validate_distance_precision(self, distance: Union[float, Decimal], 
                                  precision: Optional[Decimal] = None) -> bool:
        """
        Validate distance calculation precision.
        
        Args:
            distance: Distance value
            precision: Required precision (default: millimeter precision)
            
        Returns:
            bool: True if distance meets precision requirements
        """
        if precision is None:
            precision = self.precision_math.settings.default_precision
        
        return self.precision_math.validate_precision(distance, precision)
    
    def validate_angle_precision(self, angle: Union[float, Decimal], 
                               precision: Optional[Decimal] = None) -> bool:
        """
        Validate angle calculation precision.
        
        Args:
            angle: Angle value in radians
            precision: Required precision (default: millimeter precision)
            
        Returns:
            bool: True if angle meets precision requirements
        """
        if precision is None:
            precision = self.precision_math.settings.default_precision
        
        return self.precision_math.validate_precision(angle, precision)


# Global precision math instance for convenience
default_precision_math = PrecisionMath()


# Example usage and testing
if __name__ == "__main__":
    # Test precision math operations
    pm = PrecisionMath()
    
    # Test basic operations
    result1 = pm.add(1.000001, 2.000001)
    print(f"Precision addition: {result1}")
    
    result2 = pm.multiply(1.000001, 2.000001)
    print(f"Precision multiplication: {result2}")
    
    result3 = pm.distance_2d(0, 0, 3, 4)
    print(f"Precision 2D distance: {result3}")
    
    # Test precision validation
    validator = PrecisionValidator(pm)
    is_valid = validator.validate_coordinate_precision(1.000001, 2.000001, 3.000001)
    print(f"Coordinate precision valid: {is_valid}")
    
    # Test comparison
    is_equal = pm.is_equal(1.000001, 1.000002)
    print(f"Precision equality: {is_equal}") 