"""
Unit tests for the PrecisionValidator class and related utilities.

Tests all functionality including coordinate validation, geometric validation,
constraint validation, error reporting, and testing framework.
"""

import unittest
import json
import time
import math
from decimal import Decimal
from typing import List, Dict, Any

# Import the module to test
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgx_engine.core.precision_validator import (
    PrecisionValidator,
    PrecisionTestingFramework,
    ValidationLevel,
    ValidationType,
    ValidationResult,
    ValidationRule,
)
from svgx_engine.core.precision_coordinate import PrecisionCoordinate
from svgx_engine.core.precision_math import PrecisionMath, PrecisionSettings


class TestValidationLevel(unittest.TestCase):
    """Test cases for ValidationLevel enum."""

    def test_validation_levels(self):
        """Test validation level enum values."""
        self.assertEqual(ValidationLevel.CRITICAL.value, "critical")
        self.assertEqual(ValidationLevel.WARNING.value, "warning")
        self.assertEqual(ValidationLevel.INFO.value, "info")
        self.assertEqual(ValidationLevel.DEBUG.value, "debug")


class TestValidationType(unittest.TestCase):
    """Test cases for ValidationType enum."""

    def test_validation_types(self):
        """Test validation type enum values."""
        self.assertEqual(ValidationType.COORDINATE.value, "coordinate")
        self.assertEqual(ValidationType.GEOMETRIC.value, "geometric")
        self.assertEqual(ValidationType.CONSTRAINT.value, "constraint")
        self.assertEqual(ValidationType.PRECISION.value, "precision")
        self.assertEqual(ValidationType.PERFORMANCE.value, "performance")


class TestValidationResult(unittest.TestCase):
    """Test cases for ValidationResult class."""

    def test_validation_result_creation(self):
        """Test validation result creation."""
        result = ValidationResult(
            is_valid=True,
            validation_type=ValidationType.COORDINATE,
            validation_level=ValidationLevel.CRITICAL,
            message="Test validation passed",
            details={"test": "data"},
            precision_used=Decimal("0.001"),
            actual_value=1.000,
            expected_value=1.000,
            tolerance=Decimal("0.001"),
        )

        self.assertTrue(result.is_valid)
        self.assertEqual(result.validation_type, ValidationType.COORDINATE)
        self.assertEqual(result.validation_level, ValidationLevel.CRITICAL)
        self.assertEqual(result.message, "Test validation passed")
        self.assertEqual(result.details, {"test": "data"})
        self.assertEqual(result.precision_used, Decimal("0.001"))
        self.assertEqual(result.actual_value, 1.000)
        self.assertEqual(result.expected_value, 1.000)
        self.assertEqual(result.tolerance, Decimal("0.001"))

    def test_validation_result_to_dict(self):
        """Test validation result to dictionary conversion."""
        result = ValidationResult(
            is_valid=True,
            validation_type=ValidationType.COORDINATE,
            validation_level=ValidationLevel.CRITICAL,
            message="Test validation",
            precision_used=Decimal("0.001"),
            actual_value=1.000,
            expected_value=1.000,
            tolerance=Decimal("0.001"),
        )

        result_dict = result.to_dict()

        self.assertEqual(result_dict["is_valid"], True)
        self.assertEqual(result_dict["validation_type"], "coordinate")
        self.assertEqual(result_dict["validation_level"], "critical")
        self.assertEqual(result_dict["message"], "Test validation")
        self.assertEqual(result_dict["precision_used"], "0.001")
        self.assertEqual(result_dict["actual_value"], "1.0")
        self.assertEqual(result_dict["expected_value"], "1.0")
        self.assertEqual(result_dict["tolerance"], "0.001")

    def test_validation_result_to_json(self):
        """Test validation result to JSON conversion."""
        result = ValidationResult(
            is_valid=True,
            validation_type=ValidationType.COORDINATE,
            validation_level=ValidationLevel.CRITICAL,
            message="Test validation",
        )

        json_str = result.to_json()
        result_dict = json.loads(json_str)

        self.assertEqual(result_dict["is_valid"], True)
        self.assertEqual(result_dict["validation_type"], "coordinate")
        self.assertEqual(result_dict["validation_level"], "critical")


class TestValidationRule(unittest.TestCase):
    """Test cases for ValidationRule class."""

    def test_validation_rule_creation(self):
        """Test validation rule creation."""

        def test_rule_function(*args, **kwargs):
            return True

        rule = ValidationRule(
            name="test_rule",
            validation_type=ValidationType.COORDINATE,
            validation_level=ValidationLevel.CRITICAL,
            rule_function=test_rule_function,
            description="Test validation rule",
            required_precision=Decimal("0.001"),
            tolerance=Decimal("0.001"),
            enabled=True,
        )

        self.assertEqual(rule.name, "test_rule")
        self.assertEqual(rule.validation_type, ValidationType.COORDINATE)
        self.assertEqual(rule.validation_level, ValidationLevel.CRITICAL)
        self.assertEqual(rule.description, "Test validation rule")
        self.assertEqual(rule.required_precision, Decimal("0.001"))
        self.assertEqual(rule.tolerance, Decimal("0.001"))
        self.assertTrue(rule.enabled)

    def test_validation_rule_execution(self):
        """Test validation rule execution."""

        def test_rule_function(*args, **kwargs):
            return True

        rule = ValidationRule(
            name="test_rule",
            validation_type=ValidationType.COORDINATE,
            validation_level=ValidationLevel.CRITICAL,
            rule_function=test_rule_function,
            description="Test validation rule",
        )

        result = rule.execute("test_arg")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.validation_type, ValidationType.COORDINATE)
        self.assertEqual(result.validation_level, ValidationLevel.CRITICAL)

    def test_validation_rule_execution_failure(self):
        """Test validation rule execution with failure."""

        def failing_rule_function(*args, **kwargs):
            raise ValueError("Test error")

        rule = ValidationRule(
            name="failing_rule",
            validation_type=ValidationType.COORDINATE,
            validation_level=ValidationType.CRITICAL,
            rule_function=failing_rule_function,
            description="Failing validation rule",
        )

        result = rule.execute("test_arg")
        self.assertFalse(result.is_valid)
        self.assertEqual(result.validation_level, ValidationLevel.CRITICAL)
        self.assertIn("execution failed", result.message)

    def test_disabled_validation_rule(self):
        """Test disabled validation rule execution."""

        def test_rule_function(*args, **kwargs):
            return True

        rule = ValidationRule(
            name="disabled_rule",
            validation_type=ValidationType.COORDINATE,
            validation_level=ValidationLevel.CRITICAL,
            rule_function=test_rule_function,
            description="Disabled validation rule",
            enabled=False,
        )

        result = rule.execute("test_arg")
        self.assertTrue(result.is_valid)
        self.assertIn("disabled", result.message)


class TestPrecisionValidator(unittest.TestCase):
    """Test cases for PrecisionValidator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = PrecisionValidator()

    def test_validator_initialization(self):
        """Test validator initialization."""
        self.assertIsNotNone(self.validator.precision_math)
        self.assertIsNotNone(self.validator.settings)
        self.assertIsInstance(self.validator.validation_rules, dict)
        self.assertIsInstance(self.validator.validation_history, list)
        self.assertIsNotNone(self.validator.logger)

    def test_default_rules_registration(self):
        """Test that default rules are registered."""
        expected_rules = [
            "coordinate_range_check",
            "coordinate_precision_check",
            "coordinate_nan_check",
            "distance_precision_check",
            "angle_precision_check",
            "constraint_precision_check",
            "calculation_performance_check",
        ]

        for rule_name in expected_rules:
            self.assertIn(rule_name, self.validator.validation_rules)

    def test_register_and_unregister_rule(self):
        """Test rule registration and unregistration."""

        def test_rule_function(*args, **kwargs):
            return True

        rule = ValidationRule(
            name="custom_rule",
            validation_type=ValidationType.COORDINATE,
            validation_level=ValidationLevel.INFO,
            rule_function=test_rule_function,
            description="Custom test rule",
        )

        # Register rule
        self.validator.register_rule(rule)
        self.assertIn("custom_rule", self.validator.validation_rules)

        # Unregister rule
        self.validator.unregister_rule("custom_rule")
        self.assertNotIn("custom_rule", self.validator.validation_rules)

    def test_enable_and_disable_rule(self):
        """Test rule enabling and disabling."""
        rule_name = "coordinate_range_check"

        # Disable rule
        self.validator.disable_rule(rule_name)
        self.assertFalse(self.validator.validation_rules[rule_name].enabled)

        # Enable rule
        self.validator.enable_rule(rule_name)
        self.assertTrue(self.validator.validation_rules[rule_name].enabled)

    def test_validate_coordinate(self):
        """Test coordinate validation."""
        # Test valid coordinate
        valid_coordinate = PrecisionCoordinate(1.000, 2.000, 3.000)
        results = self.validator.validate_coordinate(valid_coordinate)

        self.assertIsInstance(results, list)
        self.assertTrue(all(isinstance(result, ValidationResult) for result in results))

        # All coordinate validation rules should pass for valid coordinate
        coordinate_results = [
            r for r in results if r.validation_type == ValidationType.COORDINATE
        ]
        self.assertTrue(all(r.is_valid for r in coordinate_results))

    def test_validate_invalid_coordinate(self):
        """Test validation of invalid coordinates."""
        # Test coordinate with NaN values
        import math

        nan_coordinate = PrecisionCoordinate(1.000, float("nan"), 3.000)
        results = self.validator.validate_coordinate(nan_coordinate)

        # Should have validation failures
        self.assertTrue(any(not result.is_valid for result in results))

    def test_validate_geometric_operation(self):
        """Test geometric operation validation."""
        # Test valid distance calculation
        distance_result = self.validator.precision_math.distance_2d(0, 0, 3, 4)
        results = self.validator.validate_geometric_operation(
            "distance_2d", distance_result
        )

        self.assertIsInstance(results, list)
        self.assertTrue(all(isinstance(result, ValidationResult) for result in results))

        # All geometric validation rules should pass for valid operation
        geometric_results = [
            r for r in results if r.validation_type == ValidationType.GEOMETRIC
        ]
        self.assertTrue(all(r.is_valid for r in geometric_results))

    def test_validate_constraint(self):
        """Test constraint validation."""
        # Test valid constraint
        valid_constraint = {
            "type": "distance",
            "values": [5.000, 5.000],
            "tolerance": 0.001,
        }
        results = self.validator.validate_constraint(
            "distance_constraint", valid_constraint
        )

        self.assertIsInstance(results, list)
        self.assertTrue(all(isinstance(result, ValidationResult) for result in results))

        # All constraint validation rules should pass for valid constraint
        constraint_results = [
            r for r in results if r.validation_type == ValidationType.CONSTRAINT
        ]
        self.assertTrue(all(r.is_valid for r in constraint_results))

    def test_validate_batch(self):
        """Test batch validation."""
        validation_data = [
            {
                "type": "coordinate",
                "coordinate": PrecisionCoordinate(1.000, 2.000, 3.000),
            },
            {
                "type": "geometric",
                "operation_name": "distance_2d",
                "operation_result": 5.000,
            },
            {
                "type": "constraint",
                "constraint_name": "distance_constraint",
                "constraint_data": {"type": "distance", "values": [5.000]},
            },
        ]

        results = self.validator.validate_batch(validation_data)

        self.assertIsInstance(results, list)
        self.assertTrue(all(isinstance(result, ValidationResult) for result in results))
        self.assertEqual(len(results), 3)  # One result per validation data item

    def test_get_validation_summary(self):
        """Test validation summary generation."""
        # Run some validations first
        coordinate = PrecisionCoordinate(1.000, 2.000, 3.000)
        self.validator.validate_coordinate(coordinate)

        summary = self.validator.get_validation_summary()

        self.assertIn("total_validations", summary)
        self.assertIn("passed_validations", summary)
        self.assertIn("failed_validations", summary)
        self.assertIn("success_rate", summary)
        self.assertIn("by_type", summary)
        self.assertIn("by_level", summary)
        self.assertIn("recent_validations", summary)

        self.assertIsInstance(summary["total_validations"], int)
        self.assertIsInstance(summary["passed_validations"], int)
        self.assertIsInstance(summary["failed_validations"], int)
        self.assertIsInstance(summary["success_rate"], float)

    def test_export_validation_report(self):
        """Test validation report export."""
        import tempfile
        import os

        # Run some validations first
        coordinate = PrecisionCoordinate(1.000, 2.000, 3.000)
        self.validator.validate_coordinate(coordinate)

        # Export report to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            report_filename = f.name

        try:
            self.validator.export_validation_report(report_filename)

            # Verify file was created and contains valid JSON
            self.assertTrue(os.path.exists(report_filename))

            with open(report_filename, "r") as f:
                report_data = json.load(f)

            self.assertIn("validation_summary", report_data)
            self.assertIn("validation_history", report_data)
            self.assertIn("validation_rules", report_data)

        finally:
            # Clean up temporary file
            if os.path.exists(report_filename):
                os.unlink(report_filename)

    def test_clear_validation_history(self):
        """Test validation history clearing."""
        # Run some validations first
        coordinate = PrecisionCoordinate(1.000, 2.000, 3.000)
        self.validator.validate_coordinate(coordinate)

        # Verify history has entries
        self.assertGreater(len(self.validator.validation_history), 0)

        # Clear history
        self.validator.clear_validation_history()

        # Verify history is empty
        self.assertEqual(len(self.validator.validation_history), 0)

    def test_get_failed_validations(self):
        """Test getting failed validations."""
        # Run some validations including invalid ones
        valid_coordinate = PrecisionCoordinate(1.000, 2.000, 3.000)
        self.validator.validate_coordinate(valid_coordinate)

        # Create an invalid coordinate (out of range)
        invalid_coordinate = PrecisionCoordinate(1e7, 1e7, 1e7)
        self.validator.validate_coordinate(invalid_coordinate)

        failed_validations = self.validator.get_failed_validations()

        self.assertIsInstance(failed_validations, list)
        self.assertTrue(
            all(isinstance(result, ValidationResult) for result in failed_validations)
        )
        self.assertTrue(all(not result.is_valid for result in failed_validations))

    def test_get_critical_failures(self):
        """Test getting critical validation failures."""
        # Run some validations including invalid ones
        valid_coordinate = PrecisionCoordinate(1.000, 2.000, 3.000)
        self.validator.validate_coordinate(valid_coordinate)

        # Create an invalid coordinate (out of range)
        invalid_coordinate = PrecisionCoordinate(1e7, 1e7, 1e7)
        self.validator.validate_coordinate(invalid_coordinate)

        critical_failures = self.validator.get_critical_failures()

        self.assertIsInstance(critical_failures, list)
        self.assertTrue(
            all(isinstance(result, ValidationResult) for result in critical_failures)
        )
        self.assertTrue(all(not result.is_valid for result in critical_failures))
        self.assertTrue(
            all(
                result.validation_level == ValidationLevel.CRITICAL
                for result in critical_failures
            )
        )


class TestPrecisionTestingFramework(unittest.TestCase):
    """Test cases for PrecisionTestingFramework class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_framework = PrecisionTestingFramework()

    def test_testing_framework_initialization(self):
        """Test testing framework initialization."""
        self.assertIsNotNone(self.test_framework.validator)
        self.assertIsInstance(self.test_framework.test_results, list)
        self.assertIsNotNone(self.test_framework.logger)

    def test_run_coordinate_tests(self):
        """Test coordinate validation tests."""
        test_results = self.test_framework.run_coordinate_tests()

        self.assertIsInstance(test_results, list)
        self.assertGreater(len(test_results), 0)

        for test_result in test_results:
            self.assertIn("test_name", test_result)
            self.assertIn("results", test_result)
            self.assertIn("passed", test_result)
            self.assertIsInstance(test_result["passed"], bool)

    def test_run_geometric_tests(self):
        """Test geometric validation tests."""
        test_results = self.test_framework.run_geometric_tests()

        self.assertIsInstance(test_results, list)
        self.assertGreater(len(test_results), 0)

        for test_result in test_results:
            self.assertIn("test_name", test_result)
            self.assertIn("operation", test_result)
            self.assertIn("result", test_result)
            self.assertIn("results", test_result)
            self.assertIn("passed", test_result)
            self.assertIsInstance(test_result["passed"], bool)

    def test_run_constraint_tests(self):
        """Test constraint validation tests."""
        test_results = self.test_framework.run_constraint_tests()

        self.assertIsInstance(test_results, list)
        self.assertGreater(len(test_results), 0)

        for test_result in test_results:
            self.assertIn("test_name", test_result)
            self.assertIn("constraint", test_result)
            self.assertIn("results", test_result)
            self.assertIn("passed", test_result)
            self.assertIsInstance(test_result["passed"], bool)

    def test_run_performance_tests(self):
        """Test performance validation tests."""
        test_results = self.test_framework.run_performance_tests()

        self.assertIsInstance(test_results, list)
        self.assertGreater(len(test_results), 0)

        for test_result in test_results:
            self.assertIn("test_name", test_result)
            self.assertIn("num_validations", test_result)
            self.assertIn("execution_time", test_result)
            self.assertIn("results", test_result)
            self.assertIn("passed", test_result)
            self.assertIsInstance(test_result["passed"], bool)
            self.assertIsInstance(test_result["execution_time"], float)

    def test_run_all_tests(self):
        """Test running all validation tests."""
        test_summary = self.test_framework.run_all_tests()

        self.assertIn("total_tests", test_summary)
        self.assertIn("passed_tests", test_summary)
        self.assertIn("failed_tests", test_summary)
        self.assertIn("success_rate", test_summary)
        self.assertIn("test_suites", test_summary)

        self.assertIsInstance(test_summary["total_tests"], int)
        self.assertIsInstance(test_summary["passed_tests"], int)
        self.assertIsInstance(test_summary["failed_tests"], int)
        self.assertIsInstance(test_summary["success_rate"], float)
        self.assertIsInstance(test_summary["test_suites"], dict)

        # Verify test suites
        expected_suites = [
            "coordinate_tests",
            "geometric_tests",
            "constraint_tests",
            "performance_tests",
        ]
        for suite_name in expected_suites:
            self.assertIn(suite_name, test_summary["test_suites"])

    def test_export_test_report(self):
        """Test test report export."""
        import tempfile
        import os

        # Export report to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            report_filename = f.name

        try:
            self.test_framework.export_test_report(report_filename)

            # Verify file was created and contains valid JSON
            self.assertTrue(os.path.exists(report_filename))

            with open(report_filename, "r") as f:
                report_data = json.load(f)

            self.assertIn("test_summary", report_data)
            self.assertIn("validation_summary", report_data)

        finally:
            # Clean up temporary file
            if os.path.exists(report_filename):
                os.unlink(report_filename)


class TestPrecisionValidatorIntegration(unittest.TestCase):
    """Integration tests for the precision validation system."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = PrecisionValidator()
        self.test_framework = PrecisionTestingFramework(self.validator)

    def test_end_to_end_validation_workflow(self):
        """Test complete validation workflow."""
        # Step 1: Validate coordinates
        coordinate = PrecisionCoordinate(1.000, 2.000, 3.000)
        coordinate_results = self.validator.validate_coordinate(coordinate)

        # Step 2: Validate geometric operation
        distance = self.validator.precision_math.distance_2d(0, 0, 3, 4)
        geometric_results = self.validator.validate_geometric_operation(
            "distance_2d", distance
        )

        # Step 3: Validate constraint
        constraint_data = {"type": "distance", "values": [5.000]}
        constraint_results = self.validator.validate_constraint(
            "distance_constraint", constraint_data
        )

        # Step 4: Get validation summary
        summary = self.validator.get_validation_summary()

        # Verify all steps completed successfully
        self.assertGreater(len(coordinate_results), 0)
        self.assertGreater(len(geometric_results), 0)
        self.assertGreater(len(constraint_results), 0)
        self.assertIn("total_validations", summary)
        self.assertGreater(summary["total_validations"], 0)

    def test_validation_error_handling(self):
        """Test validation error handling."""
        # Test with invalid coordinate (NaN values)
        import math

        invalid_coordinate = PrecisionCoordinate(1.000, float("nan"), 3.000)

        # This should not raise an exception but return validation results
        results = self.validator.validate_coordinate(invalid_coordinate)

        self.assertIsInstance(results, list)
        self.assertTrue(all(isinstance(result, ValidationResult) for result in results))

        # Should have some failed validations
        failed_results = [r for r in results if not r.is_valid]
        self.assertGreater(len(failed_results), 0)

    def test_validation_performance(self):
        """Test validation performance with large datasets."""
        import time

        # Test with multiple coordinates
        start_time = time.time()

        validation_data = []
        for i in range(100):
            coordinate = PrecisionCoordinate(i * 0.001, i * 0.001, i * 0.001)
            validation_data.append({"type": "coordinate", "coordinate": coordinate})

        results = self.validator.validate_batch(validation_data)
        end_time = time.time()

        # Verify performance is reasonable (should complete within 1 second)
        execution_time = end_time - start_time
        self.assertLess(execution_time, 1.0)

        # Verify all validations completed
        self.assertEqual(len(results), 100)
        self.assertTrue(all(isinstance(result, ValidationResult) for result in results))

    def test_validation_rule_customization(self):
        """Test custom validation rule creation and usage."""

        # Create custom validation rule
        def custom_rule_function(coordinate, precision):
            # Custom rule: check if coordinate is in first quadrant
            return coordinate.x >= 0 and coordinate.y >= 0 and coordinate.z >= 0

        custom_rule = ValidationRule(
            name="first_quadrant_check",
            validation_type=ValidationType.COORDINATE,
            validation_level=ValidationLevel.WARNING,
            rule_function=custom_rule_function,
            description="Check if coordinate is in first quadrant",
        )

        # Register custom rule
        self.validator.register_rule(custom_rule)

        # Test with valid coordinate (first quadrant)
        valid_coordinate = PrecisionCoordinate(1.000, 2.000, 3.000)
        results = self.validator.validate_coordinate(valid_coordinate)

        # Find custom rule result
        custom_results = [r for r in results if "first_quadrant_check" in r.message]
        self.assertGreater(len(custom_results), 0)

        # Test with invalid coordinate (not in first quadrant)
        invalid_coordinate = PrecisionCoordinate(-1.000, 2.000, 3.000)
        results = self.validator.validate_coordinate(invalid_coordinate)

        # Find custom rule result for invalid coordinate
        custom_results = [r for r in results if "first_quadrant_check" in r.message]
        self.assertGreater(len(custom_results), 0)
        self.assertFalse(custom_results[0].is_valid)


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
