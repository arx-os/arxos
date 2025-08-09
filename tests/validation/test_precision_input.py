"""
Unit tests for the PrecisionInputHandler class and related utilities.

Tests all functionality including coordinate input validation, mouse/touch input,
keyboard input, precision feedback, and input mode processing.
"""

import unittest
import time
import json
import tempfile
import os
from decimal import Decimal
from typing import List, Dict, Any

# Import the module to test
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgx_engine.core.precision_input import (
    PrecisionInputHandler,
    PrecisionInputValidator,
    InputSettings,
    InputType,
    InputMode,
    InputEvent
)
from svgx_engine.core.precision_coordinate import PrecisionCoordinate
from svgx_engine.core.precision_math import PrecisionMath


class TestInputSettings(unittest.TestCase):
    """Test cases for the InputSettings class."""

    def test_default_settings(self):
        """Test default input settings."""
        settings = InputSettings()

        self.assertEqual(settings.default_precision, Decimal('0.001')
        self.assertEqual(settings.grid_snap_precision, Decimal('1.000')
        self.assertEqual(settings.angle_snap_precision, Decimal('15.0')
        self.assertEqual(settings.mouse_sensitivity, 1.0)
        self.assertEqual(settings.touch_sensitivity, 1.0)
        self.assertEqual(settings.keyboard_precision, Decimal('0.001')
        self.assertTrue(settings.validate_input)
        self.assertTrue(settings.strict_mode)
        self.assertTrue(settings.log_input_errors)
        self.assertTrue(settings.provide_visual_feedback)
        self.assertFalse(settings.provide_audio_feedback)
        self.assertEqual(settings.feedback_delay, 0.1)
        self.assertTrue(settings.enable_grid_snap)
        self.assertTrue(settings.enable_object_snap)
        self.assertTrue(settings.enable_angle_snap)
        self.assertEqual(settings.snap_tolerance, Decimal('0.5')
    def test_custom_settings(self):
        """Test custom input settings."""
        settings = InputSettings(
            default_precision=Decimal('0.0005'),
            grid_snap_precision=Decimal('0.5'),
            angle_snap_precision=Decimal('30.0'),
            mouse_sensitivity=2.0,
            touch_sensitivity=1.5,
            keyboard_precision=Decimal('0.0001'),
            validate_input=False,
            strict_mode=False,
            log_input_errors=False,
            provide_visual_feedback=False,
            provide_audio_feedback=True,
            feedback_delay=0.2,
            enable_grid_snap=False,
            enable_object_snap=False,
            enable_angle_snap=False,
            snap_tolerance=Decimal('1.0')
        self.assertEqual(settings.default_precision, Decimal('0.0005')
        self.assertEqual(settings.grid_snap_precision, Decimal('0.5')
        self.assertEqual(settings.angle_snap_precision, Decimal('30.0')
        self.assertEqual(settings.mouse_sensitivity, 2.0)
        self.assertEqual(settings.touch_sensitivity, 1.5)
        self.assertEqual(settings.keyboard_precision, Decimal('0.0001')
        self.assertFalse(settings.validate_input)
        self.assertFalse(settings.strict_mode)
        self.assertFalse(settings.log_input_errors)
        self.assertFalse(settings.provide_visual_feedback)
        self.assertTrue(settings.provide_audio_feedback)
        self.assertEqual(settings.feedback_delay, 0.2)
        self.assertFalse(settings.enable_grid_snap)
        self.assertFalse(settings.enable_object_snap)
        self.assertFalse(settings.enable_angle_snap)
        self.assertEqual(settings.snap_tolerance, Decimal('1.0')
    def test_invalid_settings(self):
        """Test validation of input settings."""
        # Test negative precision
        with self.assertRaises(ValueError):
            InputSettings(default_precision=Decimal('-0.001')
        # Test negative grid snap precision
        with self.assertRaises(ValueError):
            InputSettings(grid_snap_precision=Decimal('-1.000')
        # Test negative angle snap precision
        with self.assertRaises(ValueError):
            InputSettings(angle_snap_precision=Decimal('-15.0')
class TestInputEvent(unittest.TestCase):
    """Test cases for the InputEvent class."""

    def test_input_event_creation(self):
        """Test input event creation."""
        event = InputEvent(
            event_type="click",
            timestamp=time.time(),
            coordinates=(1.0, 2.0, 3.0),
            input_type=InputType.MOUSE,
            input_mode=InputMode.FREEHAND
        )

        self.assertEqual(event.event_type, "click")
        self.assertIsInstance(event.timestamp, float)
        self.assertEqual(event.coordinates, (1.0, 2.0, 3.0)
        self.assertEqual(event.input_type, InputType.MOUSE)
        self.assertEqual(event.input_mode, InputMode.FREEHAND)
        self.assertIsNone(event.precision_coordinate)
        self.assertEqual(event.validation_results, [])
        self.assertFalse(event.is_valid)

    def test_input_event_with_coordinate(self):
        """Test input event with precision coordinate."""
        coordinate = PrecisionCoordinate(1.000, 2.000, 3.000)
        event = InputEvent(
            event_type="move",
            timestamp=time.time(),
            coordinates=(1.0, 2.0, 3.0),
            input_type=InputType.TOUCH,
            input_mode=InputMode.GRID_SNAP
        )
        event.precision_coordinate = coordinate
        event.is_valid = True

        self.assertEqual(event.precision_coordinate, coordinate)
        self.assertTrue(event.is_valid)


class TestPrecisionInputHandler(unittest.TestCase):
    """Test cases for the PrecisionInputHandler class."""

    def setUp(self):
        """Set up test fixtures."""
        self.handler = PrecisionInputHandler()
        self.test_coordinates = []
        self.test_feedback = []

    def test_handler_initialization(self):
        """Test handler initialization."""
        self.assertIsNotNone(self.handler.precision_math)
        self.assertIsNotNone(self.handler.validator)
        self.assertIsNotNone(self.handler.logger)
        self.assertEqual(self.handler.current_mode, InputMode.FREEHAND)
        self.assertIsNone(self.handler.last_input_event)
        self.assertEqual(self.handler.input_history, [])
        self.assertIsNone(self.handler.on_coordinate_input)
        self.assertIsNone(self.handler.on_input_validation)
        self.assertIsNone(self.handler.on_precision_feedback)

    def test_set_input_mode(self):
        """Test setting input mode."""
        self.handler.set_input_mode(InputMode.GRID_SNAP)
        self.assertEqual(self.handler.current_mode, InputMode.GRID_SNAP)

        self.handler.set_input_mode(InputMode.ANGLE_SNAP)
        self.assertEqual(self.handler.current_mode, InputMode.ANGLE_SNAP)

    def test_set_callbacks(self):
        """Test setting callbacks."""
def test_callback(coordinate):
    """TODO: Implement this function."""
    pass
            pass

        def test_validation_callback(event):
            pass
    """TODO: Implement this function."""
    pass
            pass

        def test_feedback_callback(feedback_type, data):
            pass
    """TODO: Implement this function."""
    pass
            pass

        self.handler.set_coordinate_callback(test_callback)
        self.handler.set_validation_callback(test_validation_callback)
        self.handler.set_feedback_callback(test_feedback_callback)

        self.assertIsNotNone(self.handler.on_coordinate_input)
        self.assertIsNotNone(self.handler.on_input_validation)
        self.assertIsNotNone(self.handler.on_precision_feedback)

    def test_handle_mouse_input_valid(self):
        """Test valid mouse input handling."""
        coordinate = self.handler.handle_mouse_input(1.000, 2.000, 3.000, "click")

        self.assertIsInstance(coordinate, PrecisionCoordinate)
        self.assertEqual(coordinate.x, 1.000)
        self.assertEqual(coordinate.y, 2.000)
        self.assertEqual(coordinate.z, 3.000)

        # Check that event was stored
        self.assertIsNotNone(self.handler.last_input_event)
        self.assertEqual(len(self.handler.input_history), 1)
        self.assertTrue(self.handler.last_input_event.is_valid)

    def test_handle_mouse_input_invalid(self):
        """Test invalid mouse input handling."""
        # Test with out-of-range coordinates
        coordinate = self.handler.handle_mouse_input(1e7, 1e7, 1e7, "click")

        self.assertIsNone(coordinate)

        # Check that event was stored but marked as invalid
        self.assertIsNotNone(self.handler.last_input_event)
        self.assertEqual(len(self.handler.input_history), 1)
        self.assertFalse(self.handler.last_input_event.is_valid)

    def test_handle_touch_input_valid(self):
        """Test valid touch input handling."""
        coordinate = self.handler.handle_touch_input(4.000, 5.000, 6.000, "touch")

        self.assertIsInstance(coordinate, PrecisionCoordinate)
        self.assertEqual(coordinate.x, 4.000)
        self.assertEqual(coordinate.y, 5.000)
        self.assertEqual(coordinate.z, 6.000)

        # Check that event was stored
        self.assertIsNotNone(self.handler.last_input_event)
        self.assertEqual(len(self.handler.input_history), 2)  # After mouse test
        self.assertTrue(self.handler.last_input_event.is_valid)

    def test_handle_touch_input_with_sensitivity(self):
        """Test touch input with sensitivity adjustment."""
        # Set custom touch sensitivity
        self.handler.settings.touch_sensitivity = 2.0

        coordinate = self.handler.handle_touch_input(1.000, 2.000, 3.000, "touch")

        self.assertIsInstance(coordinate, PrecisionCoordinate)
        # Coordinates should be multiplied by sensitivity
        self.assertEqual(coordinate.x, 2.000)
        self.assertEqual(coordinate.y, 4.000)
        self.assertEqual(coordinate.z, 3.000)

    def test_handle_keyboard_input_valid(self):
        """Test valid keyboard input handling."""
        coordinate = self.handler.handle_keyboard_input("7.000", "8.000", "9.000")

        self.assertIsInstance(coordinate, PrecisionCoordinate)
        self.assertEqual(coordinate.x, 7.000)
        self.assertEqual(coordinate.y, 8.000)
        self.assertEqual(coordinate.z, 9.000)

        # Check that event was stored
        self.assertIsNotNone(self.handler.last_input_event)
        self.assertTrue(self.handler.last_input_event.is_valid)

    def test_handle_keyboard_input_invalid_format(self):
        """Test invalid keyboard input format."""
        coordinate = self.handler.handle_keyboard_input("invalid", "8.000", "9.000")

        self.assertIsNone(coordinate)

    def test_handle_keyboard_input_with_precision(self):
        """Test keyboard input with precision rounding."""
        # Set custom keyboard precision
        self.handler.settings.keyboard_precision = Decimal('0.1')

        coordinate = self.handler.handle_keyboard_input("7.123", "8.456", "9.789")

        self.assertIsInstance(coordinate, PrecisionCoordinate)
        # Should be rounded to 0.1 precision
        self.assertEqual(coordinate.x, 7.1)
        self.assertEqual(coordinate.y, 8.5)
        self.assertEqual(coordinate.z, 9.8)

    def test_input_mode_processing_freehand(self):
        """Test freehand input mode processing."""
        self.handler.set_input_mode(InputMode.FREEHAND)

        coordinate = self.handler.handle_mouse_input(1.234, 2.567, 3.890, "move")

        self.assertIsInstance(coordinate, PrecisionCoordinate)
        # Should not be modified in freehand mode
        self.assertEqual(coordinate.x, 1.234)
        self.assertEqual(coordinate.y, 2.567)
        self.assertEqual(coordinate.z, 3.890)

    def test_input_mode_processing_grid_snap(self):
        """Test grid snap input mode processing."""
        self.handler.set_input_mode(InputMode.GRID_SNAP)

        coordinate = self.handler.handle_mouse_input(1.234, 2.567, 3.890, "move")

        self.assertIsInstance(coordinate, PrecisionCoordinate)
        # Should be snapped to 1.0 grid
        self.assertEqual(coordinate.x, 1.0)
        self.assertEqual(coordinate.y, 3.0)
        self.assertEqual(coordinate.z, 4.0)

    def test_input_mode_processing_angle_snap(self):
        """Test angle snap input mode processing."""
        self.handler.set_input_mode(InputMode.ANGLE_SNAP)

        coordinate = self.handler.handle_mouse_input(1.000, 1.000, 0.000, "move")

        self.assertIsInstance(coordinate, PrecisionCoordinate)
        # Should be snapped to 15-degree increments
        # 45 degrees should snap to 45 degrees (15 * 3)
        expected_angle = 45.0  # degrees
        distance = math.sqrt(1.0**2 + 1.0**2)
        expected_x = distance * math.cos(math.radians(expected_angle)
        expected_y = distance * math.sin(math.radians(expected_angle)
        self.assertAlmostEqual(coordinate.x, expected_x, places=3)
        self.assertAlmostEqual(coordinate.y, expected_y, places=3)

    def test_input_mode_processing_precision_mode(self):
        """Test precision mode input processing."""
        self.handler.set_input_mode(InputMode.PRECISION_MODE)

        coordinate = self.handler.handle_mouse_input(1.234567, 2.567890, 3.890123, "move")

        self.assertIsInstance(coordinate, PrecisionCoordinate)
        # Should be rounded to 0.001 precision
        self.assertEqual(coordinate.x, 1.235)
        self.assertEqual(coordinate.y, 2.568)
        self.assertEqual(coordinate.z, 3.890)

    def test_coordinate_callback(self):
        """Test coordinate callback functionality."""
        received_coordinates = []

        def coordinate_callback(coordinate):
            received_coordinates.append(coordinate)

        self.handler.set_coordinate_callback(coordinate_callback)

        # Handle input
        self.handler.handle_mouse_input(1.000, 2.000, 3.000, "click")

        # Check that callback was called
        self.assertEqual(len(received_coordinates), 1)
        self.assertEqual(received_coordinates[0].x, 1.000)
        self.assertEqual(received_coordinates[0].y, 2.000)
        self.assertEqual(received_coordinates[0].z, 3.000)

    def test_feedback_callback(self):
        """Test feedback callback functionality."""
        received_feedback = []

        def feedback_callback(feedback_type, data):
            received_feedback.append((feedback_type, data)
        self.handler.set_feedback_callback(feedback_callback)

        # Handle input
        self.handler.handle_mouse_input(1.000, 2.000, 3.000, "click")

        # Check that feedback callback was called
        self.assertGreater(len(received_feedback), 0)
        self.assertEqual(received_feedback[0][0], "mouse_input_valid")

    def test_get_input_statistics(self):
        """Test input statistics generation."""
        # Handle some inputs
        self.handler.handle_mouse_input(1.000, 2.000, 3.000, "click")
        self.handler.handle_touch_input(4.000, 5.000, 6.000, "touch")
        self.handler.handle_keyboard_input("7.000", "8.000", "9.000")

        stats = self.handler.get_input_statistics()

        self.assertIn('total_inputs', stats)
        self.assertIn('valid_inputs', stats)
        self.assertIn('invalid_inputs', stats)
        self.assertIn('success_rate', stats)
        self.assertIn('by_input_type', stats)
        self.assertIn('by_input_mode', stats)
        self.assertIn('current_mode', stats)
        self.assertIn('settings', stats)

        self.assertEqual(stats['total_inputs'], 3)
        self.assertEqual(stats['valid_inputs'], 3)
        self.assertEqual(stats['invalid_inputs'], 0)
        self.assertEqual(stats['success_rate'], 1.0)

    def test_clear_input_history(self):
        """Test clearing input history."""
        # Handle some inputs
        self.handler.handle_mouse_input(1.000, 2.000, 3.000, "click")
        self.handler.handle_touch_input(4.000, 5.000, 6.000, "touch")

        # Verify history exists
        self.assertEqual(len(self.handler.input_history), 2)
        self.assertIsNotNone(self.handler.last_input_event)

        # Clear history
        self.handler.clear_input_history()

        # Verify history is cleared
        self.assertEqual(len(self.handler.input_history), 0)
        self.assertIsNone(self.handler.last_input_event)

    def test_export_input_report(self):
        """Test input report export."""
        # Handle some inputs
        self.handler.handle_mouse_input(1.000, 2.000, 3.000, "click")
        self.handler.handle_touch_input(4.000, 5.000, 6.000, "touch")

        # Export report to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            report_filename = f.name

        try:
            self.handler.export_input_report(report_filename)

            # Verify file was created and contains valid JSON
            self.assertTrue(os.path.exists(report_filename)
            with open(report_filename, 'r') as f:
                report_data = json.load(f)

            self.assertIn('input_statistics', report_data)
            self.assertIn('input_history', report_data)

        finally:
            # Clean up temporary file
            if os.path.exists(report_filename):
                os.unlink(report_filename)


class TestPrecisionInputValidator(unittest.TestCase):
    """Test cases for the PrecisionInputValidator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = PrecisionInputValidator()

    def test_validate_input_coordinates_valid(self):
        """Test valid input coordinate validation."""
        is_valid = self.validator.validate_input_coordinates(1.000, 2.000, 3.000)
        self.assertTrue(is_valid)

    def test_validate_input_coordinates_invalid(self):
        """Test invalid input coordinate validation."""
        # Test with precision violation
        is_valid = self.validator.validate_input_coordinates(1.000001, 2.000001, 3.000001)
        self.assertFalse(is_valid)

    def test_validate_input_coordinates_with_custom_precision(self):
        """Test input coordinate validation with custom precision."""
        is_valid = self.validator.validate_input_coordinates(
            1.000001, 2.000001, 3.000001,
            precision=Decimal('0.000001')
        self.assertTrue(is_valid)

    def test_validate_input_range_valid(self):
        """Test valid input range validation."""
        is_valid = self.validator.validate_input_range(1.0, 2.0, 3.0)
        self.assertTrue(is_valid)

    def test_validate_input_range_invalid(self):
        """Test invalid input range validation."""
        # Test with out-of-range coordinates
        is_valid = self.validator.validate_input_range(1e7, 1e7, 1e7)
        self.assertFalse(is_valid)

    def test_validate_input_range_with_custom_max(self):
        """Test input range validation with custom maximum."""
        is_valid = self.validator.validate_input_range(1.0, 2.0, 3.0, max_range=10.0)
        self.assertTrue(is_valid)

        is_valid = self.validator.validate_input_range(15.0, 15.0, 15.0, max_range=10.0)
        self.assertFalse(is_valid)

    def test_validate_input_format_valid(self):
        """Test valid input format validation."""
        is_valid = self.validator.validate_input_format("1.000", "2.000", "3.000")
        self.assertTrue(is_valid)

    def test_validate_input_format_invalid(self):
        """Test invalid input format validation."""
        # Test with invalid format
        is_valid = self.validator.validate_input_format("invalid", "2.000", "3.000")
        self.assertFalse(is_valid)

        # Test with empty string
        is_valid = self.validator.validate_input_format("", "2.000", "3.000")
        self.assertFalse(is_valid)

        # Test with non-numeric string
        is_valid = self.validator.validate_input_format("abc", "2.000", "3.000")
        self.assertFalse(is_valid)


class TestPrecisionInputIntegration(unittest.TestCase):
    """Integration tests for the precision input system."""

    def setUp(self):
        """Set up test fixtures."""
        self.handler = PrecisionInputHandler()
        self.validator = PrecisionInputValidator()

    def test_end_to_end_input_workflow(self):
        """Test complete input workflow."""
        received_coordinates = []
        received_feedback = []

        def coordinate_callback(coordinate):
            received_coordinates.append(coordinate)

        def feedback_callback(feedback_type, data):
            received_feedback.append((feedback_type, data)
        self.handler.set_coordinate_callback(coordinate_callback)
        self.handler.set_feedback_callback(feedback_callback)

        # Test mouse input
        coordinate1 = self.handler.handle_mouse_input(1.000, 2.000, 3.000, "click")

        # Test touch input
        coordinate2 = self.handler.handle_touch_input(4.000, 5.000, 6.000, "touch")

        # Test keyboard input
        coordinate3 = self.handler.handle_keyboard_input("7.000", "8.000", "9.000")

        # Verify all inputs were processed
        self.assertIsNotNone(coordinate1)
        self.assertIsNotNone(coordinate2)
        self.assertIsNotNone(coordinate3)

        # Verify callbacks were called
        self.assertEqual(len(received_coordinates), 3)
        self.assertGreater(len(received_feedback), 0)

        # Verify coordinate callback received correct coordinates
        self.assertEqual(received_coordinates[0].x, 1.000)
        self.assertEqual(received_coordinates[0].y, 2.000)
        self.assertEqual(received_coordinates[0].z, 3.000)

        self.assertEqual(received_coordinates[1].x, 4.000)
        self.assertEqual(received_coordinates[1].y, 5.000)
        self.assertEqual(received_coordinates[1].z, 6.000)

        self.assertEqual(received_coordinates[2].x, 7.000)
        self.assertEqual(received_coordinates[2].y, 8.000)
        self.assertEqual(received_coordinates[2].z, 9.000)

    def test_input_mode_transitions(self):
        """Test input mode transitions and processing."""
        # Test freehand mode
        self.handler.set_input_mode(InputMode.FREEHAND)
        coordinate1 = self.handler.handle_mouse_input(1.234, 2.567, 3.890, "move")

        # Test grid snap mode
        self.handler.set_input_mode(InputMode.GRID_SNAP)
        coordinate2 = self.handler.handle_mouse_input(1.234, 2.567, 3.890, "move")

        # Test precision mode
        self.handler.set_input_mode(InputMode.PRECISION_MODE)
        coordinate3 = self.handler.handle_mouse_input(1.234, 2.567, 3.890, "move")

        # Verify different processing for each mode
        self.assertEqual(coordinate1.x, 1.234)  # Freehand - no processing
        self.assertEqual(coordinate2.x, 1.0)    # Grid snap - snapped to grid
        self.assertEqual(coordinate3.x, 1.235)  # Precision mode - rounded

    def test_input_validation_integration(self):
        """Test input validation integration."""
        # Test valid input
        is_valid = self.validator.validate_input_coordinates(1.000, 2.000, 3.000)
        self.assertTrue(is_valid)

        # Test invalid input
        is_valid = self.validator.validate_input_coordinates(1.000001, 2.000001, 3.000001)
        self.assertFalse(is_valid)

        # Test range validation
        is_valid = self.validator.validate_input_range(1.0, 2.0, 3.0)
        self.assertTrue(is_valid)

        is_valid = self.validator.validate_input_range(1e7, 1e7, 1e7)
        self.assertFalse(is_valid)

        # Test format validation
        is_valid = self.validator.validate_input_format("1.000", "2.000", "3.000")
        self.assertTrue(is_valid)

        is_valid = self.validator.validate_input_format("invalid", "2.000", "3.000")
        self.assertFalse(is_valid)

    def test_error_handling(self):
        """Test error handling in input system."""
        # Test with invalid input format
        coordinate = self.handler.handle_keyboard_input("invalid", "2.000", "3.000")
        self.assertIsNone(coordinate)

        # Test with out-of-range coordinates
        coordinate = self.handler.handle_mouse_input(1e7, 1e7, 1e7, "click")
        self.assertIsNone(coordinate)

        # Verify error handling doesn't crash the system'
        coordinate = self.handler.handle_mouse_input(1.000, 2.000, 3.000, "click")
        self.assertIsNotNone(coordinate)

    def test_performance_with_large_input_sets(self):
        """Test performance with large input sets."""
        import time

        start_time = time.time()

        # Process many inputs
        for i in range(100):
            self.handler.handle_mouse_input(i * 0.001, i * 0.001, i * 0.001, "move")

        end_time = time.time()

        # Verify performance is reasonable (should complete within 1 second)
        execution_time = end_time - start_time
        self.assertLess(execution_time, 1.0)

        # Verify all inputs were processed
        stats = self.handler.get_input_statistics()
        self.assertEqual(stats['total_inputs'], 100)
        self.assertEqual(stats['valid_inputs'], 100)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
