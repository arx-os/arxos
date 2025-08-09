"""
Unit tests for the PrecisionMath class and related utilities.

Tests all functionality including decimal precision, mathematical operations,
validation, and error handling for the sub-millimeter precision system.
"""

import unittest
import math
import decimal
from decimal import Decimal, getcontext
from typing import List

# Import the module to test
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgx_engine.core.precision_math import (
    PrecisionMath,
    PrecisionSettings,
    PrecisionValidator,
    PrecisionError,
    MILLIMETER_PRECISION,
    MICRON_PRECISION,
    NANOMETER_PRECISION
)


class TestPrecisionSettings(unittest.TestCase):
    """Test cases for the PrecisionSettings class."""

    def test_default_settings(self):
        """Test default precision settings."""
        settings = PrecisionSettings()

        self.assertEqual(settings.millimeter_precision, MILLIMETER_PRECISION)
        self.assertEqual(settings.micron_precision, MICRON_PRECISION)
        self.assertEqual(settings.nanometer_precision, NANOMETER_PRECISION)
        self.assertEqual(settings.default_precision, MILLIMETER_PRECISION)
        self.assertEqual(settings.rounding_mode, 'HALF_UP')
        self.assertTrue(settings.strict_mode)
        self.assertTrue(settings.log_precision_errors)

    def test_custom_settings(self):
        """Test custom precision settings."""
        custom_precision = Decimal('0.0005')  # 0.5mm precision
        settings = PrecisionSettings(
            default_precision=custom_precision,
            rounding_mode='DOWN',
            strict_mode=False,
            log_precision_errors=False
        )

        self.assertEqual(settings.default_precision, custom_precision)
        self.assertEqual(settings.rounding_mode, 'DOWN')
        self.assertFalse(settings.strict_mode)
        self.assertFalse(settings.log_precision_errors)

    def test_invalid_precision_settings(self):
        """Test validation of precision settings."""
        # Test negative precision
        with self.assertRaises(ValueError):
            PrecisionSettings(millimeter_precision=Decimal('-0.001'))

        # Test invalid precision hierarchy
        with self.assertRaises(ValueError):
            PrecisionSettings(
                millimeter_precision=Decimal('0.001'),
                micron_precision=Decimal('0.002')  # Greater than millimeter
            )

        # Test invalid rounding mode
        with self.assertRaises(ValueError):
            PrecisionSettings(rounding_mode='INVALID')

    def test_precision_hierarchy(self):
        """Test that precision levels are properly ordered."""
        settings = PrecisionSettings()

        # Millimeter should be greater than micron
        self.assertGreater(settings.millimeter_precision, settings.micron_precision)

        # Micron should be greater than nanometer
        self.assertGreater(settings.micron_precision, settings.nanometer_precision)


class TestPrecisionMath(unittest.TestCase):
    """Test cases for the PrecisionMath class."""

    def setUp(self):
        """Set up test fixtures."""
        self.pm = PrecisionMath()
        self.high_precision_pm = PrecisionMath(PrecisionSettings(
            default_precision=MICRON_PRECISION
        ))

    def test_to_decimal_conversion(self):
        """Test conversion to Decimal."""
        # Test float conversion
        decimal_float = self.pm.to_decimal(1.234567)
        self.assertIsInstance(decimal_float, Decimal)
        self.assertEqual(decimal_float, Decimal('1.234567'))

        # Test int conversion
        decimal_int = self.pm.to_decimal(123)
        self.assertIsInstance(decimal_int, Decimal)
        self.assertEqual(decimal_int, Decimal('123'))

        # Test string conversion
        decimal_str = self.pm.to_decimal('1.234567')
        self.assertIsInstance(decimal_str, Decimal)
        self.assertEqual(decimal_str, Decimal('1.234567'))

        # Test Decimal conversion
        original_decimal = Decimal('1.234567')
        decimal_result = self.pm.to_decimal(original_decimal)
        self.assertEqual(decimal_result, original_decimal)

        # Test invalid conversion
        with self.assertRaises(ValueError):
            self.pm.to_decimal('invalid')

    def test_round_to_precision(self):
        """Test rounding to specified precision."""
        value = 1.23456789

        # Round to millimeter precision
        rounded_mm = self.pm.round_to_precision(value, MILLIMETER_PRECISION)
        self.assertEqual(rounded_mm, Decimal('1.235'))

        # Round to micron precision
        rounded_micron = self.pm.round_to_precision(value, MICRON_PRECISION)
        self.assertEqual(rounded_micron, Decimal('1.234568'))

        # Round to nanometer precision
        rounded_nano = self.pm.round_to_precision(value, NANOMETER_PRECISION)
        self.assertEqual(rounded_nano, Decimal('1.234567890'))

    def test_validate_precision(self):
        """Test precision validation."""
        # Test valid precision
        valid_value = 1.235
        self.assertTrue(self.pm.validate_precision(valid_value, MILLIMETER_PRECISION))

        # Test invalid precision
        invalid_value = 1.23456789
        self.assertFalse(self.pm.validate_precision(invalid_value, MILLIMETER_PRECISION))

        # Test with default precision
        self.assertTrue(self.pm.validate_precision(1.235))
        self.assertFalse(self.pm.validate_precision(1.23456789))

    def test_basic_arithmetic_operations(self):
        """Test basic arithmetic operations with precision."""
        a, b = 1.000001, 2.000001

        # Test addition
        sum_result = self.pm.add(a, b)
        self.assertEqual(sum_result, Decimal('3.000'))

        # Test subtraction
        diff_result = self.pm.subtract(b, a)
        self.assertEqual(diff_result, Decimal('1.000'))

        # Test multiplication
        product_result = self.pm.multiply(a, b)
        self.assertEqual(product_result, Decimal('2.000'))

        # Test division
        quotient_result = self.pm.divide(b, a)
        self.assertEqual(quotient_result, Decimal('2.000'))

    def test_division_by_zero(self):
        """Test division by zero error handling."""
        with self.assertRaises(ZeroDivisionError):
            self.pm.divide(1.0, 0.0)

    def test_square_root(self):
        """Test precision-aware square root."""
        # Test normal square root
        sqrt_result = self.pm.sqrt(4.0)
        self.assertEqual(sqrt_result, Decimal('2.000'))

        # Test square root with precision
        sqrt_precise = self.pm.sqrt(2.0, MICRON_PRECISION)
        expected = Decimal('1.414214')
        self.assertEqual(sqrt_precise, expected)

        # Test negative square root
        with self.assertRaises(ValueError):
            self.pm.sqrt(-1.0)

    def test_power_operation(self):
        """Test precision-aware power operation."""
        # Test square
        square_result = self.pm.power(2.0, 2.0)
        self.assertEqual(square_result, Decimal('4.000'))

        # Test cube
        cube_result = self.pm.power(2.0, 3.0)
        self.assertEqual(cube_result, Decimal('8.000'))

        # Test square root using power
        sqrt_power = self.pm.power(4.0, 0.5)
        self.assertEqual(sqrt_power, Decimal('2.000'))

    def test_distance_calculations(self):
        """Test precision-aware distance calculations."""
        # Test 2D distance
        distance_2d = self.pm.distance_2d(0, 0, 3, 4)
        self.assertEqual(distance_2d, Decimal('5.000'))

        # Test 3D distance
        distance_3d = self.pm.distance_3d(0, 0, 0, 1, 1, 1)
        expected_3d = Decimal('1.732')  # sqrt(3)
        self.assertEqual(distance_3d, expected_3d)

        # Test with high precision
        precise_distance = self.high_precision_pm.distance_2d(0, 0, 1, 1)
        expected_precise = Decimal('1.414214')  # sqrt(2)
        self.assertEqual(precise_distance, expected_precise)

    def test_angle_calculations(self):
        """Test precision-aware angle calculations."""
        # Test angle between points
        angle = self.pm.angle_between_points(0, 0, 1, 1)
        expected_angle = Decimal('0.785')  # pi/4 radians
        self.assertEqual(angle, expected_angle)

        # Test angle with high precision
        precise_angle = self.high_precision_pm.angle_between_points(0, 0, 1, 0)
        expected_precise = Decimal('0.000000')  # 0 radians
        self.assertEqual(precise_angle, expected_precise)

    def test_comparison_operations(self):
        """Test precision-aware comparison operations."""
        a, b = 1.000001, 1.000002

        # Test equality
        self.assertTrue(self.pm.is_equal(a, b))
        self.assertFalse(self.pm.is_equal(a, 2.0))

        # Test greater than
        self.assertFalse(self.pm.is_greater_than(a, b))
        self.assertTrue(self.pm.is_greater_than(2.0, a))

        # Test less than
        self.assertFalse(self.pm.is_less_than(a, b))
        self.assertTrue(self.pm.is_less_than(a, 2.0))

        # Test with custom tolerance
        self.assertFalse(self.pm.is_equal(a, b, tolerance=MICRON_PRECISION))

    def test_statistical_operations(self):
        """Test precision-aware statistical operations."""
        values = [1.000001, 2.000001, 3.000001, 4.000001, 5.000001]

        # Test minimum
        min_result = self.pm.min(values)
        self.assertEqual(min_result, Decimal('1.000'))

        # Test maximum
        max_result = self.pm.max(values)
        self.assertEqual(max_result, Decimal('5.000'))

        # Test sum
        sum_result = self.pm.sum(values)
        self.assertEqual(sum_result, Decimal('15.000'))

        # Test mean
        mean_result = self.pm.mean(values)
        self.assertEqual(mean_result, Decimal('3.000'))

        # Test empty list
        with self.assertRaises(ValueError):
            self.pm.min([])

        with self.assertRaises(ValueError):
            self.pm.max([])

        with self.assertRaises(ValueError):
            self.pm.mean([])

    def test_geometric_calculation_validation(self):
        """Test geometric calculation validation."""
        # Test valid calculation
        valid_result = self.pm.validate_geometric_calculation(
            "distance", Decimal('5.000'), MILLIMETER_PRECISION
        )
        self.assertTrue(valid_result)

        # Test invalid calculation with strict mode
        with self.assertRaises(PrecisionError):
            self.pm.validate_geometric_calculation(
                "distance", Decimal('5.123456'), MILLIMETER_PRECISION
            )

        # Test with non-strict mode
        non_strict_pm = PrecisionMath(PrecisionSettings(strict_mode=False))
        invalid_result = non_strict_pm.validate_geometric_calculation(
            "distance", Decimal('5.123456'), MILLIMETER_PRECISION
        )
        self.assertFalse(invalid_result)

    def test_precision_error_handling(self):
        """Test precision error handling."""
        # Test error handling with logging
        self.pm.handle_precision_error("test_operation", 1.23456789, MILLIMETER_PRECISION)

        # Test error handling with strict mode
        with self.assertRaises(PrecisionError):
            self.pm.handle_precision_error("test_operation", 1.23456789, MILLIMETER_PRECISION)

        # Test error handling without strict mode
        non_strict_pm = PrecisionMath(PrecisionSettings(strict_mode=False))
        # Should not raise exception
        non_strict_pm.handle_precision_error("test_operation", 1.23456789, MILLIMETER_PRECISION)


class TestPrecisionValidator(unittest.TestCase):
    """Test cases for the PrecisionValidator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = PrecisionValidator()
        self.high_precision_validator = PrecisionValidator(
            PrecisionMath(PrecisionSettings(default_precision=MICRON_PRECISION))
        )

    def test_coordinate_precision_validation(self):
        """Test coordinate precision validation."""
        # Test valid coordinates
        self.assertTrue(self.validator.validate_coordinate_precision(1.000, 2.000, 3.000))

        # Test invalid coordinates
        self.assertFalse(self.validator.validate_coordinate_precision(1.000001, 2.000001, 3.000001))

        # Test with custom precision
        self.assertTrue(self.validator.validate_coordinate_precision(
            1.000001, 2.000001, 3.000001, MICRON_PRECISION
        ))

        # Test with high precision validator
        self.assertTrue(self.high_precision_validator.validate_coordinate_precision(
            1.000001, 2.000001, 3.000001
        ))

    def test_distance_precision_validation(self):
        """Test distance precision validation."""
        # Test valid distance
        self.assertTrue(self.validator.validate_distance_precision(5.000))

        # Test invalid distance
        self.assertFalse(self.validator.validate_distance_precision(5.123456))

        # Test with custom precision
        self.assertTrue(self.validator.validate_distance_precision(5.123456, MICRON_PRECISION))

    def test_angle_precision_validation(self):
        """Test angle precision validation."""
        # Test valid angle
        self.assertTrue(self.validator.validate_angle_precision(1.570796))  # pi/2

        # Test invalid angle
        self.assertFalse(self.validator.validate_angle_precision(1.570796123))

        # Test with custom precision
        self.assertTrue(self.validator.validate_angle_precision(1.570796123, MICRON_PRECISION))


class TestPrecisionMathIntegration(unittest.TestCase):
    """Integration tests for the precision math system."""

    def setUp(self):
        """Set up test fixtures."""
        self.pm = PrecisionMath()
        self.high_precision_pm = PrecisionMath(PrecisionSettings(
            default_precision=MICRON_PRECISION
        ))

    def test_precision_accuracy_maintenance(self):
        """Test that precision accuracy is maintained through operations."""
        # Test that sub-millimeter precision is maintained
        a = 1.000001
        b = 2.000001

        # Addition should maintain precision
        sum_result = self.pm.add(a, b)
        self.assertTrue(self.pm.validate_precision(sum_result))

        # Multiplication should maintain precision
        product_result = self.pm.multiply(a, b)
        self.assertTrue(self.pm.validate_precision(product_result))

        # Distance calculation should maintain precision
        distance_result = self.pm.distance_2d(0, 0, a, b)
        self.assertTrue(self.pm.validate_precision(distance_result))

    def test_precision_propagation(self):
        """Test that precision propagates through complex calculations."""
        # Complex geometric calculation
        x1, y1 = 1.000001, 2.000001
        x2, y2 = 3.000001, 4.000001

        # Calculate distance
        distance = self.pm.distance_2d(x1, y1, x2, y2)

        # Calculate angle
        angle = self.pm.angle_between_points(x1, y1, x2, y2)

        # Both results should maintain precision
        self.assertTrue(self.pm.validate_precision(distance))
        self.assertTrue(self.pm.validate_precision(angle))

    def test_high_precision_operations(self):
        """Test operations with micron-level precision."""
        # Test micron precision operations
        a = 1.000001
        b = 2.000001

        sum_result = self.high_precision_pm.add(a, b)
        self.assertTrue(self.high_precision_pm.validate_precision(sum_result, MICRON_PRECISION))

        distance_result = self.high_precision_pm.distance_2d(0, 0, a, b)
        self.assertTrue(self.high_precision_pm.validate_precision(distance_result, MICRON_PRECISION))

    def test_precision_error_recovery(self):
        """Test precision error recovery and handling."""
        # Test that precision errors are properly handled
        invalid_value = 1.23456789

        # Should not raise exception in non-strict mode
        non_strict_pm = PrecisionMath(PrecisionSettings(strict_mode=False))
        is_valid = non_strict_pm.validate_precision(invalid_value, MILLIMETER_PRECISION)
        self.assertFalse(is_valid)

        # Should raise exception in strict mode
        with self.assertRaises(PrecisionError):
            non_strict_pm.validate_geometric_calculation(
                "test", Decimal(str(invalid_value)), MILLIMETER_PRECISION
            )

    def test_performance_with_large_numbers(self):
        """Test performance with large coordinate values."""
        # Test that the system handles large numbers correctly
        large_value = 1e6

        # Test basic operations with large numbers
        scaled = self.pm.multiply(large_value, 0.001)
        self.assertEqual(scaled, Decimal('1000.000'))

        # Test distance calculations with large numbers
        distance = self.pm.distance_2d(0, 0, large_value, large_value)
        expected_distance = Decimal('1414213.562')  # sqrt(2) * 1e6
        self.assertEqual(distance, expected_distance)

    def test_serialization_compatibility(self):
        """Test that precision values are compatible with serialization."""
        # Test that precision values can be converted to standard types
        precise_value = self.pm.add(1.000001, 2.000001)

        # Convert to float for serialization
        float_value = float(precise_value)
        self.assertIsInstance(float_value, float)

        # Convert back to Decimal
        decimal_value = self.pm.to_decimal(float_value)
        self.assertIsInstance(decimal_value, Decimal)

        # Should be equal within precision
        self.assertTrue(self.pm.is_equal(precise_value, decimal_value))


class TestPrecisionMathEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions for precision math."""

    def setUp(self):
        """Set up test fixtures."""
        self.pm = PrecisionMath()

    def test_extreme_precision_values(self):
        """Test operations with extreme precision values."""
        # Test with very small values
        tiny_value = 0.000001
        result = self.pm.add(tiny_value, tiny_value)
        self.assertTrue(self.pm.validate_precision(result, MICRON_PRECISION))

        # Test with very large values
        large_value = 999999.999999
        result = self.pm.multiply(large_value, 0.001)
        self.assertTrue(self.pm.validate_precision(result))

    def test_precision_boundary_conditions(self):
        """Test precision boundary conditions."""
        # Test values at precision boundaries
        boundary_value = 1.000  # Exactly at millimeter precision

        # Should be valid
        self.assertTrue(self.pm.validate_precision(boundary_value, MILLIMETER_PRECISION))

        # Test value just below precision
        below_precision = 1.0000001
        self.assertFalse(self.pm.validate_precision(below_precision, MILLIMETER_PRECISION))

        # Test value just above precision
        above_precision = 1.0009999
        self.assertTrue(self.pm.validate_precision(above_precision, MILLIMETER_PRECISION))

    def test_rounding_edge_cases(self):
        """Test rounding edge cases."""
        # Test rounding at 0.5 boundary
        half_value = 1.0005
        rounded = self.pm.round_to_precision(half_value, MILLIMETER_PRECISION)
        self.assertEqual(rounded, Decimal('1.001'))  # Rounds up with HALF_UP

        # Test rounding below 0.5 boundary
        below_half = 1.0004
        rounded = self.pm.round_to_precision(below_half, MILLIMETER_PRECISION)
        self.assertEqual(rounded, Decimal('1.000'))  # Rounds down

    def test_numerical_stability(self):
        """Test numerical stability of precision operations."""
        # Test repeated operations maintain precision
        value = 1.000001
        result = value

        for _ in range(100):
            result = self.pm.add(result, 0.000001)

        # Final result should still be valid
        self.assertTrue(self.pm.validate_precision(result, MILLIMETER_PRECISION))

        # Test that precision is not lost in complex calculations
        complex_result = self.pm.sqrt(
            self.pm.add(
                self.pm.multiply(value, value),
                self.pm.multiply(value, value)
            )
        )
        self.assertTrue(self.pm.validate_precision(complex_result))


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
