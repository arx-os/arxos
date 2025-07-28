"""
Test Precision Validation Integration

This module provides comprehensive tests for the precision validation integration
system, including hooks, error handling, and recovery mechanisms.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import unittest
import logging
import tempfile
import os
from typing import List, Dict, Any
from decimal import Decimal
import math

from svgx_engine.core.precision_hooks import (
    PrecisionHookManager, HookType, HookContext, PrecisionHook, hook_manager
)
from svgx_engine.core.precision_errors import (
    PrecisionErrorHandler, PrecisionErrorType, PrecisionErrorSeverity,
    PrecisionError, PrecisionErrorReport, error_handler
)
from svgx_engine.core.precision_coordinate import PrecisionCoordinate
from svgx_engine.core.precision_validator import ValidationResult, ValidationLevel, ValidationType
from svgx_engine.core.precision_config import PrecisionConfig


class TestPrecisionValidationIntegration(unittest.TestCase):
    """Test precision validation integration system."""
    
    def setUp(self):
        """Set up test environment."""
        self.hook_manager = PrecisionHookManager()
        self.error_handler = PrecisionErrorHandler()
        self.config = PrecisionConfig()
        
        # Create test coordinates
        self.test_coordinates = [
            PrecisionCoordinate(1.0, 2.0, 3.0),
            PrecisionCoordinate(4.0, 5.0, 6.0),
            PrecisionCoordinate(7.0, 8.0, 9.0)
        ]
        
        # Create test transformation data
        self.test_transformation_data = {
            'scale': 2.0,
            'rotation': math.pi / 4,
            'translation': [10.0, 20.0, 30.0]
        }
        
        # Create test constraint data
        self.test_constraint_data = {
            'type': 'distance',
            'target_distance': 5.0,
            'tolerance': 0.001
        }
    
    def test_hook_manager_initialization(self):
        """Test hook manager initialization."""
        self.assertIsNotNone(self.hook_manager)
        self.assertIsNotNone(self.hook_manager.hooks)
        self.assertEqual(len(self.hook_manager.hooks), len(HookType))
    
    def test_hook_registration(self):
        """Test hook registration."""
        def test_hook(context: HookContext) -> HookContext:
            return context
        
        hook = PrecisionHook(
            hook_id="test_hook",
            hook_type=HookType.COORDINATE_CREATION,
            function=test_hook,
            priority=5,
            description="Test hook"
        )
        
        self.hook_manager.register_hook(hook)
        
        # Check if hook was registered
        hooks = self.hook_manager.hooks[HookType.COORDINATE_CREATION]
        self.assertIn(hook, hooks)
    
    def test_hook_execution(self):
        """Test hook execution."""
        execution_count = 0
        
        def test_hook(context: HookContext) -> HookContext:
            nonlocal execution_count
            execution_count += 1
            return context
        
        hook = PrecisionHook(
            hook_id="test_execution_hook",
            hook_type=HookType.COORDINATE_CREATION,
            function=test_hook,
            priority=10
        )
        
        self.hook_manager.register_hook(hook)
        
        context = HookContext(
            operation_name="test_operation",
            coordinates=self.test_coordinates
        )
        
        self.hook_manager.execute_hooks(HookType.COORDINATE_CREATION, context)
        
        self.assertEqual(execution_count, 1)
    
    def test_coordinate_creation_hooks(self):
        """Test coordinate creation hooks."""
        context = HookContext(
            operation_name="coordinate_creation_test",
            coordinates=self.test_coordinates
        )
        
        # Execute coordinate creation hooks
        result_context = self.hook_manager.execute_hooks(HookType.COORDINATE_CREATION, context)
        
        self.assertIsNotNone(result_context)
        self.assertEqual(len(result_context.coordinates), 3)
        self.assertEqual(result_context.operation_name, "coordinate_creation_test")
    
    def test_coordinate_transformation_hooks(self):
        """Test coordinate transformation hooks."""
        context = HookContext(
            operation_name="coordinate_transformation_test",
            coordinates=self.test_coordinates,
            transformation_data=self.test_transformation_data
        )
        
        # Execute coordinate transformation hooks
        result_context = self.hook_manager.execute_hooks(HookType.COORDINATE_TRANSFORMATION, context)
        
        self.assertIsNotNone(result_context)
        self.assertEqual(len(result_context.coordinates), 3)
        self.assertEqual(result_context.transformation_data, self.test_transformation_data)
    
    def test_geometric_constraint_hooks(self):
        """Test geometric constraint hooks."""
        context = HookContext(
            operation_name="geometric_constraint_test",
            coordinates=self.test_coordinates,
            constraint_data=self.test_constraint_data
        )
        
        # Execute geometric constraint hooks
        result_context = self.hook_manager.execute_hooks(HookType.GEOMETRIC_CONSTRAINT, context)
        
        self.assertIsNotNone(result_context)
        self.assertEqual(len(result_context.coordinates), 3)
        self.assertEqual(result_context.constraint_data, self.test_constraint_data)
    
    def test_precision_validation_hooks(self):
        """Test precision validation hooks."""
        context = HookContext(
            operation_name="precision_validation_test",
            coordinates=self.test_coordinates
        )
        
        # Execute precision validation hooks
        result_context = self.hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)
        
        self.assertIsNotNone(result_context)
        self.assertEqual(len(result_context.coordinates), 3)
    
    def test_error_handling_hooks(self):
        """Test error handling hooks."""
        context = HookContext(
            operation_name="error_handling_test",
            coordinates=self.test_coordinates,
            errors=["Test error 1", "Test error 2"]
        )
        
        # Execute error handling hooks
        result_context = self.hook_manager.execute_hooks(HookType.ERROR_HANDLING, context)
        
        self.assertIsNotNone(result_context)
        self.assertEqual(len(result_context.errors), 2)
    
    def test_recovery_mechanism_hooks(self):
        """Test recovery mechanism hooks."""
        context = HookContext(
            operation_name="recovery_mechanism_test",
            coordinates=self.test_coordinates,
            errors=["Test error"]
        )
        
        # Execute recovery mechanism hooks
        result_context = self.hook_manager.execute_hooks(HookType.RECOVERY_MECHANISM, context)
        
        self.assertIsNotNone(result_context)
        self.assertEqual(len(result_context.coordinates), 3)
    
    def test_error_handler_initialization(self):
        """Test error handler initialization."""
        self.assertIsNotNone(self.error_handler)
        self.assertIsNotNone(self.error_handler.error_reports)
        self.assertIsNotNone(self.error_handler.recovery_strategies)
    
    def test_error_handling(self):
        """Test error handling."""
        error = self.error_handler.handle_error(
            error_type=PrecisionErrorType.COORDINATE_RANGE_VIOLATION,
            message="Test coordinate range violation",
            operation="test_operation",
            coordinates=self.test_coordinates,
            severity=PrecisionErrorSeverity.ERROR
        )
        
        self.assertIsNotNone(error)
        self.assertEqual(error.error_type, PrecisionErrorType.COORDINATE_RANGE_VIOLATION)
        self.assertEqual(error.severity, PrecisionErrorSeverity.ERROR)
        self.assertEqual(error.operation, "test_operation")
        self.assertEqual(len(error.coordinates), 3)
    
    def test_error_report_creation(self):
        """Test error report creation."""
        report = self.error_handler.start_error_report("test_report")
        
        self.assertIsNotNone(report)
        self.assertEqual(report.report_id, "test_report")
        
        # Add some errors
        error1 = self.error_handler.handle_error(
            PrecisionErrorType.COORDINATE_RANGE_VIOLATION,
            "Error 1",
            "operation1",
            severity=PrecisionErrorSeverity.ERROR
        )
        
        error2 = self.error_handler.handle_error(
            PrecisionErrorType.COORDINATE_PRECISION_VIOLATION,
            "Error 2",
            "operation2",
            severity=PrecisionErrorSeverity.WARNING
        )
        
        # End report
        final_report = self.error_handler.end_error_report()
        
        self.assertIsNotNone(final_report)
        self.assertEqual(len(final_report.errors), 1)
        self.assertEqual(len(final_report.warnings), 1)
    
    def test_error_recovery_strategies(self):
        """Test error recovery strategies."""
        # Test coordinate range violation recovery
        error = PrecisionError(
            error_id="test_error",
            error_type=PrecisionErrorType.COORDINATE_RANGE_VIOLATION,
            severity=PrecisionErrorSeverity.ERROR,
            message="Test error",
            operation="test_operation",
            coordinates=[PrecisionCoordinate(1e7, 1e7, 1e7)]  # Out of range
        )
        
        recovery_result = self.error_handler.recovery_strategies[
            PrecisionErrorType.COORDINATE_RANGE_VIOLATION
        ](error)
        
        self.assertTrue(recovery_result)
        self.assertEqual(len(error.corrected_coordinates), 1)
        
        # Check that coordinates were clamped
        corrected_coord = error.corrected_coordinates[0]
        self.assertLessEqual(abs(corrected_coord.x), 1e6)
        self.assertLessEqual(abs(corrected_coord.y), 1e6)
        self.assertLessEqual(abs(corrected_coord.z), 1e6)
    
    def test_coordinate_precision_recovery(self):
        """Test coordinate precision violation recovery."""
        # Create coordinate with precision violation
        coord = PrecisionCoordinate(1.23456789, 2.34567891, 3.45678912)
        
        error = PrecisionError(
            error_id="test_error",
            error_type=PrecisionErrorType.COORDINATE_PRECISION_VIOLATION,
            severity=PrecisionErrorSeverity.ERROR,
            message="Test precision error",
            operation="test_operation",
            coordinates=[coord]
        )
        
        recovery_result = self.error_handler.recovery_strategies[
            PrecisionErrorType.COORDINATE_PRECISION_VIOLATION
        ](error)
        
        self.assertTrue(recovery_result)
        self.assertEqual(len(error.corrected_coordinates), 1)
        
        # Check that coordinates were rounded to precision
        corrected_coord = error.corrected_coordinates[0]
        self.assertNotEqual(corrected_coord.x, coord.x)
        self.assertNotEqual(corrected_coord.y, coord.y)
        self.assertNotEqual(corrected_coord.z, coord.z)
    
    def test_coordinate_nan_recovery(self):
        """Test coordinate NaN violation recovery."""
        import math
        
        # Create coordinate with NaN values
        coord = PrecisionCoordinate(float('nan'), 2.0, float('inf'))
        
        error = PrecisionError(
            error_id="test_error",
            error_type=PrecisionErrorType.COORDINATE_NAN_VIOLATION,
            severity=PrecisionErrorSeverity.ERROR,
            message="Test NaN error",
            operation="test_operation",
            coordinates=[coord]
        )
        
        recovery_result = self.error_handler.recovery_strategies[
            PrecisionErrorType.COORDINATE_NAN_VIOLATION
        ](error)
        
        self.assertTrue(recovery_result)
        self.assertEqual(len(error.corrected_coordinates), 1)
        
        # Check that NaN and infinite values were replaced
        corrected_coord = error.corrected_coordinates[0]
        self.assertFalse(math.isnan(corrected_coord.x))
        self.assertFalse(math.isinf(corrected_coord.z))
        self.assertEqual(corrected_coord.x, 0.0)
        self.assertEqual(corrected_coord.z, 0.0)
    
    def test_transformation_error_recovery(self):
        """Test transformation error recovery."""
        error = PrecisionError(
            error_id="test_error",
            error_type=PrecisionErrorType.TRANSFORMATION_ERROR,
            severity=PrecisionErrorSeverity.ERROR,
            message="Test transformation error",
            operation="test_operation",
            coordinates=self.test_coordinates
        )
        
        recovery_result = self.error_handler.recovery_strategies[
            PrecisionErrorType.TRANSFORMATION_ERROR
        ](error)
        
        self.assertTrue(recovery_result)
        self.assertEqual(len(error.corrected_coordinates), 3)
    
    def test_constraint_violation_recovery(self):
        """Test constraint violation recovery."""
        error = PrecisionError(
            error_id="test_error",
            error_type=PrecisionErrorType.CONSTRAINT_VIOLATION,
            severity=PrecisionErrorSeverity.ERROR,
            message="Test constraint violation",
            operation="test_operation",
            coordinates=self.test_coordinates
        )
        
        recovery_result = self.error_handler.recovery_strategies[
            PrecisionErrorType.CONSTRAINT_VIOLATION
        ](error)
        
        self.assertTrue(recovery_result)
        self.assertEqual(len(error.corrected_coordinates), 3)
    
    def test_hook_priority_ordering(self):
        """Test hook priority ordering."""
        execution_order = []
        
        def high_priority_hook(context: HookContext) -> HookContext:
            execution_order.append("high")
            return context
        
        def low_priority_hook(context: HookContext) -> HookContext:
            execution_order.append("low")
            return context
        
        # Register hooks with different priorities
        high_hook = PrecisionHook(
            hook_id="high_priority",
            hook_type=HookType.COORDINATE_CREATION,
            function=high_priority_hook,
            priority=10
        )
        
        low_hook = PrecisionHook(
            hook_id="low_priority",
            hook_type=HookType.COORDINATE_CREATION,
            function=low_priority_hook,
            priority=1
        )
        
        self.hook_manager.register_hook(high_hook)
        self.hook_manager.register_hook(low_hook)
        
        context = HookContext(
            operation_name="priority_test",
            coordinates=self.test_coordinates
        )
        
        self.hook_manager.execute_hooks(HookType.COORDINATE_CREATION, context)
        
        # High priority should execute first
        self.assertEqual(execution_order[0], "high")
        self.assertEqual(execution_order[1], "low")
    
    def test_hook_error_handling(self):
        """Test hook error handling."""
        def failing_hook(context: HookContext) -> HookContext:
            raise ValueError("Hook execution failed")
        
        hook = PrecisionHook(
            hook_id="failing_hook",
            hook_type=HookType.COORDINATE_CREATION,
            function=failing_hook,
            priority=10
        )
        
        self.hook_manager.register_hook(hook)
        
        context = HookContext(
            operation_name="error_test",
            coordinates=self.test_coordinates
        )
        
        # Should not raise exception, should handle error gracefully
        result_context = self.hook_manager.execute_hooks(HookType.COORDINATE_CREATION, context)
        
        self.assertIsNotNone(result_context)
        self.assertGreater(len(result_context.errors), 0)
    
    def test_hook_disabling(self):
        """Test hook disabling."""
        execution_count = 0
        
        def test_hook(context: HookContext) -> HookContext:
            nonlocal execution_count
            execution_count += 1
            return context
        
        hook = PrecisionHook(
            hook_id="disabled_hook",
            hook_type=HookType.COORDINATE_CREATION,
            function=test_hook,
            priority=10,
            enabled=False  # Disabled
        )
        
        self.hook_manager.register_hook(hook)
        
        context = HookContext(
            operation_name="disable_test",
            coordinates=self.test_coordinates
        )
        
        self.hook_manager.execute_hooks(HookType.COORDINATE_CREATION, context)
        
        # Hook should not execute because it's disabled
        self.assertEqual(execution_count, 0)
    
    def test_error_report_summary(self):
        """Test error report summary generation."""
        report = PrecisionErrorReport(report_id="test_summary")
        
        # Add various types of errors
        error1 = PrecisionError(
            error_id="error1",
            error_type=PrecisionErrorType.COORDINATE_RANGE_VIOLATION,
            severity=PrecisionErrorSeverity.ERROR,
            message="Error 1",
            operation="operation1"
        )
        
        error2 = PrecisionError(
            error_id="error2",
            error_type=PrecisionErrorType.COORDINATE_PRECISION_VIOLATION,
            severity=PrecisionErrorSeverity.WARNING,
            message="Error 2",
            operation="operation2"
        )
        
        error3 = PrecisionError(
            error_id="error3",
            error_type=PrecisionErrorType.TRANSFORMATION_ERROR,
            severity=PrecisionErrorSeverity.INFO,
            message="Error 3",
            operation="operation3"
        )
        
        report.add_error(error1)
        report.add_warning(error2)
        report.add_info(error3)
        
        summary = report.generate_summary()
        
        self.assertEqual(summary['total_errors'], 1)
        self.assertEqual(summary['total_warnings'], 1)
        self.assertEqual(summary['total_info'], 1)
        self.assertIn('coordinate_range_violation', summary['error_types'])
        self.assertIn('error', summary['severity_counts'])
        self.assertIn('warning', summary['severity_counts'])
    
    def test_error_serialization(self):
        """Test error serialization."""
        error = PrecisionError(
            error_id="test_serialization",
            error_type=PrecisionErrorType.COORDINATE_RANGE_VIOLATION,
            severity=PrecisionErrorSeverity.ERROR,
            message="Test serialization",
            operation="test_operation",
            coordinates=self.test_coordinates
        )
        
        error_dict = error.to_dict()
        
        self.assertIsInstance(error_dict, dict)
        self.assertEqual(error_dict['error_id'], "test_serialization")
        self.assertEqual(error_dict['error_type'], "coordinate_range_violation")
        self.assertEqual(error_dict['severity'], "error")
        self.assertEqual(error_dict['message'], "Test serialization")
        self.assertEqual(error_dict['operation'], "test_operation")
        self.assertEqual(len(error_dict['coordinates']), 3)
    
    def test_report_serialization(self):
        """Test report serialization."""
        report = PrecisionErrorReport(report_id="test_serialization")
        
        error = PrecisionError(
            error_id="test_error",
            error_type=PrecisionErrorType.COORDINATE_RANGE_VIOLATION,
            severity=PrecisionErrorSeverity.ERROR,
            message="Test error",
            operation="test_operation"
        )
        
        report.add_error(error)
        
        report_dict = report.to_dict()
        
        self.assertIsInstance(report_dict, dict)
        self.assertEqual(report_dict['report_id'], "test_serialization")
        self.assertEqual(len(report_dict['errors']), 1)
        self.assertIn('summary', report_dict)
    
    def test_global_hook_manager(self):
        """Test global hook manager functionality."""
        execution_count = 0
        
        def test_hook(context: HookContext) -> HookContext:
            nonlocal execution_count
            execution_count += 1
            return context
        
        # Use global hook manager
        hook = PrecisionHook(
            hook_id="global_test_hook",
            hook_type=HookType.COORDINATE_CREATION,
            function=test_hook,
            priority=10
        )
        
        hook_manager.register_hook(hook)
        
        context = HookContext(
            operation_name="global_test",
            coordinates=self.test_coordinates
        )
        
        hook_manager.execute_hooks(HookType.COORDINATE_CREATION, context)
        
        self.assertEqual(execution_count, 1)
    
    def test_global_error_handler(self):
        """Test global error handler functionality."""
        error = error_handler.handle_error(
            error_type=PrecisionErrorType.COORDINATE_RANGE_VIOLATION,
            message="Global test error",
            operation="global_test_operation",
            coordinates=self.test_coordinates
        )
        
        self.assertIsNotNone(error)
        self.assertEqual(error.error_type, PrecisionErrorType.COORDINATE_RANGE_VIOLATION)
        self.assertEqual(error.operation, "global_test_operation")


if __name__ == '__main__':
    # Set up logging for tests
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    unittest.main(verbosity=2) 