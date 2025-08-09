"""
Precision Validation System for CAD Applications

This module provides comprehensive validation for precision requirements in CAD applications,
including coordinate validation, geometric constraint validation, and precision error reporting.
"""

import logging
import json
import time
from typing import Dict, List, Tuple, Optional, Union, Any, Callable
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
import numpy as np

from .precision_math import PrecisionMath, PrecisionSettings, PrecisionError
from .precision_coordinate import PrecisionCoordinate


class ValidationLevel(Enum):
    """Validation levels for precision requirements."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


class ValidationType(Enum):
    """Types of validation operations."""
    COORDINATE = "coordinate"
    GEOMETRIC = "geometric"
    CONSTRAINT = "constraint"
    PRECISION = "precision"
    PERFORMANCE = "performance"


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    is_valid: bool
    validation_type: ValidationType
    validation_level: ValidationLevel
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    precision_used: Optional[Decimal] = None
    actual_value: Optional[Union[float, Decimal]] = None
    expected_value: Optional[Union[float, Decimal]] = None
    tolerance: Optional[Decimal] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to dictionary."""
        return {
            'is_valid': self.is_valid,
            'validation_type': self.validation_type.value,
            'validation_level': self.validation_level.value,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp,
            'precision_used': str(self.precision_used) if self.precision_used else None,
            'actual_value': str(self.actual_value) if self.actual_value else None,
            'expected_value': str(self.expected_value) if self.expected_value else None,
            'tolerance': str(self.tolerance) if self.tolerance else None
        }

    def to_json(self) -> str:
        """Convert validation result to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class ValidationRule:
    """Definition of a validation rule."""

    name: str
    validation_type: ValidationType
    validation_level: ValidationLevel
    rule_function: Callable
    description: str
    required_precision: Optional[Decimal] = None
    tolerance: Optional[Decimal] = None
    enabled: bool = True

    def execute(self, *args, **kwargs) -> ValidationResult:
        """Execute the validation rule."""
        if not self.enabled:
            return ValidationResult(
                is_valid=True,
                validation_type=self.validation_type,
                validation_level=self.validation_level,
                message=f"Rule '{self.name}' is disabled"
            )

        try:
            result = self.rule_function(*args, **kwargs)
            return ValidationResult(
                is_valid=result,
                validation_type=self.validation_type,
                validation_level=self.validation_level,
                message=f"Rule '{self.name}' validation {'passed' if result else 'failed'}",
                details={'rule_name': self.name, 'description': self.description}
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                validation_type=self.validation_type,
                validation_level=ValidationLevel.CRITICAL,
                message=f"Rule '{self.name}' execution failed: {str(e)}",
                details={'rule_name': self.name, 'error': str(e)}
            )


class PrecisionValidator:
    """
    Comprehensive precision validation system for CAD applications.

    Provides coordinate validation, geometric constraint validation,
    precision error reporting, and testing framework.
    """

    def __init__(self, precision_math: Optional[PrecisionMath] = None,
                 settings: Optional[PrecisionSettings] = None):
        """
        Initialize precision validator.

        Args:
            precision_math: Precision math instance (default: new instance)
            settings: Precision settings (default: standard CAD settings)
        """
        self.precision_math = precision_math or PrecisionMath(settings)
        self.settings = settings or PrecisionSettings()
        self.validation_rules: Dict[str, ValidationRule] = {}
        self.validation_history: List[ValidationResult] = []
        self.logger = logging.getLogger(__name__)

        # Setup logging
        self._setup_logging()

        # Register default validation rules
        self._register_default_rules()

    def _setup_logging(self):
        """Setup logging for validation operations."""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _register_default_rules(self):
        """Register default validation rules."""
        # Coordinate validation rules
        self.register_rule(ValidationRule(
            name="coordinate_range_check",
            validation_type=ValidationType.COORDINATE,
            validation_level=ValidationLevel.CRITICAL,
            rule_function=self._validate_coordinate_range,
            description="Validate coordinate values are within acceptable range",
            required_precision=self.settings.default_precision
        )
        self.register_rule(ValidationRule(
            name="coordinate_precision_check",
            validation_type=ValidationType.PRECISION,
            validation_level=ValidationLevel.CRITICAL,
            rule_function=self._validate_coordinate_precision,
            description="Validate coordinate precision meets requirements",
            required_precision=self.settings.default_precision
        )
        self.register_rule(ValidationRule(
            name="coordinate_nan_check",
            validation_type=ValidationType.COORDINATE,
            validation_level=ValidationLevel.CRITICAL,
            rule_function=self._validate_coordinate_nan,
            description="Validate coordinates are not NaN or infinite",
            required_precision=self.settings.default_precision
        )
        # Geometric validation rules
        self.register_rule(ValidationRule(
            name="distance_precision_check",
            validation_type=ValidationType.GEOMETRIC,
            validation_level=ValidationLevel.CRITICAL,
            rule_function=self._validate_distance_precision,
            description="Validate distance calculation precision",
            required_precision=self.settings.default_precision
        )
        self.register_rule(ValidationRule(
            name="angle_precision_check",
            validation_type=ValidationType.GEOMETRIC,
            validation_level=ValidationLevel.CRITICAL,
            rule_function=self._validate_angle_precision,
            description="Validate angle calculation precision",
            required_precision=self.settings.default_precision
        )
        # Constraint validation rules
        self.register_rule(ValidationRule(
            name="constraint_precision_check",
            validation_type=ValidationType.CONSTRAINT,
            validation_level=ValidationLevel.WARNING,
            rule_function=self._validate_constraint_precision,
            description="Validate geometric constraint precision",
            required_precision=self.settings.default_precision
        )
        # Performance validation rules
        self.register_rule(ValidationRule(
            name="calculation_performance_check",
            validation_type=ValidationType.PERFORMANCE,
            validation_level=ValidationLevel.INFO,
            rule_function=self._validate_calculation_performance,
            description="Validate calculation performance",
            required_precision=self.settings.default_precision
        )
    def register_rule(self, rule: ValidationRule):
        """Register a validation rule."""
        self.validation_rules[rule.name] = rule
        self.logger.info(f"Registered validation rule: {rule.name}")

    def unregister_rule(self, rule_name: str):
        """Unregister a validation rule."""
        if rule_name in self.validation_rules:
            del self.validation_rules[rule_name]
            self.logger.info(f"Unregistered validation rule: {rule_name}")

    def enable_rule(self, rule_name: str):
        """Enable a validation rule."""
        if rule_name in self.validation_rules:
            self.validation_rules[rule_name].enabled = True
            self.logger.info(f"Enabled validation rule: {rule_name}")

    def disable_rule(self, rule_name: str):
        """Disable a validation rule."""
        if rule_name in self.validation_rules:
            self.validation_rules[rule_name].enabled = False
            self.logger.info(f"Disabled validation rule: {rule_name}")

    def validate_coordinate(self, coordinate: PrecisionCoordinate,
                          precision: Optional[Decimal] = None) -> List[ValidationResult]:
        """
        Validate a coordinate using all applicable rules.

        Args:
            coordinate: Coordinate to validate
            precision: Required precision (default: millimeter precision)

        Returns:
            List[ValidationResult]: Validation results
        """
        if precision is None:
            precision = self.settings.default_precision

        results = []

        # Execute coordinate validation rules
        for rule_name, rule in self.validation_rules.items():
            if rule.validation_type == ValidationType.COORDINATE:
                result = rule.execute(coordinate, precision)
                results.append(result)
                self.validation_history.append(result)

                if not result.is_valid and rule.validation_level == ValidationLevel.CRITICAL:
                    self.logger.error(f"Critical validation failed: {result.message}")

        return results

    def validate_geometric_operation(self, operation_name: str,
                                   operation_result: Union[float, Decimal],
                                   expected_precision: Optional[Decimal] = None) -> List[ValidationResult]:
        """
        Validate a geometric operation result.

        Args:
            operation_name: Name of the geometric operation
            operation_result: Result of the operation
            expected_precision: Expected precision for validation

        Returns:
            List[ValidationResult]: Validation results
        """
        if expected_precision is None:
            expected_precision = self.settings.default_precision

        results = []

        # Execute geometric validation rules
        for rule_name, rule in self.validation_rules.items():
            if rule.validation_type == ValidationType.GEOMETRIC:
                result = rule.execute(operation_name, operation_result, expected_precision)
                results.append(result)
                self.validation_history.append(result)

                if not result.is_valid and rule.validation_level == ValidationLevel.CRITICAL:
                    self.logger.error(f"Critical geometric validation failed: {result.message}")

        return results

    def validate_constraint(self, constraint_name: str,
                          constraint_data: Dict[str, Any],
                          precision: Optional[Decimal] = None) -> List[ValidationResult]:
        """
        Validate a geometric constraint.

        Args:
            constraint_name: Name of the constraint
            constraint_data: Constraint data dictionary
            precision: Required precision (default: millimeter precision)

        Returns:
            List[ValidationResult]: Validation results
        """
        if precision is None:
            precision = self.settings.default_precision

        results = []

        # Execute constraint validation rules
        for rule_name, rule in self.validation_rules.items():
            if rule.validation_type == ValidationType.CONSTRAINT:
                result = rule.execute(constraint_name, constraint_data, precision)
                results.append(result)
                self.validation_history.append(result)

                if not result.is_valid and rule.validation_level == ValidationLevel.CRITICAL:
                    self.logger.error(f"Critical constraint validation failed: {result.message}")

        return results

    def validate_batch(self, validation_data: List[Dict[str, Any]]) -> List[ValidationResult]:
        """
        Validate a batch of operations.

        Args:
            validation_data: List of validation data dictionaries

        Returns:
            List[ValidationResult]: All validation results
        """
        all_results = []

        for data in validation_data:
            validation_type = data.get('type')
            if validation_type == 'coordinate':
                coordinate = data['coordinate']
                precision = data.get('precision')
                results = self.validate_coordinate(coordinate, precision)
            elif validation_type == 'geometric':
                operation_name = data['operation_name']
                operation_result = data['operation_result']
                expected_precision = data.get('expected_precision')
                results = self.validate_geometric_operation(operation_name, operation_result, expected_precision)
            elif validation_type == 'constraint':
                constraint_name = data['constraint_name']
                constraint_data = data['constraint_data']
                precision = data.get('precision')
                results = self.validate_constraint(constraint_name, constraint_data, precision)
            else:
                self.logger.warning(f"Unknown validation type: {validation_type}")
                continue

            all_results.extend(results)

        return all_results

    # Coordinate validation rule implementations
def _validate_coordinate_range(self, coordinate: PrecisionCoordinate,
                                 precision: Optional[Decimal] = None) -> bool:
        """Validate coordinate values are within acceptable range."""
        if precision is None:
            precision = self.settings.default_precision

        max_coordinate = 1e6  # 1 million units
        return (abs(coordinate.x) <= max_coordinate and
                abs(coordinate.y) <= max_coordinate and
                abs(coordinate.z) <= max_coordinate)

    def _validate_coordinate_precision(self, coordinate: PrecisionCoordinate,
                                     precision: Optional[Decimal] = None) -> bool:
        """Validate coordinate precision meets requirements."""
        if precision is None:
            precision = self.settings.default_precision

        return (self.precision_math.validate_precision(coordinate.x, precision) and
                self.precision_math.validate_precision(coordinate.y, precision) and
                self.precision_math.validate_precision(coordinate.z, precision)
    def _validate_coordinate_nan(self, coordinate: PrecisionCoordinate,
                               precision: Optional[Decimal] = None) -> bool:
        """Validate coordinates are not NaN or infinite."""
        import math

        return (not math.isnan(coordinate.x) and not math.isnan(coordinate.y) and not math.isnan(coordinate.z) and
                not math.isinf(coordinate.x) and not math.isinf(coordinate.y) and not math.isinf(coordinate.z)
    # Geometric validation rule implementations
def _validate_distance_precision(self, operation_name: str,
                                   operation_result: Union[float, Decimal],
                                   expected_precision: Optional[Decimal] = None) -> bool:
        """Validate distance calculation precision."""
        if expected_precision is None:
            expected_precision = self.settings.default_precision

        return self.precision_math.validate_precision(operation_result, expected_precision)

    def _validate_angle_precision(self, operation_name: str,
                                operation_result: Union[float, Decimal],
                                expected_precision: Optional[Decimal] = None) -> bool:
        """Validate angle calculation precision."""
        if expected_precision is None:
            expected_precision = self.settings.default_precision

        return self.precision_math.validate_precision(operation_result, expected_precision)

    # Constraint validation rule implementations
def _validate_constraint_precision(self, constraint_name: str,
                                    constraint_data: Dict[str, Any],
                                    precision: Optional[Decimal] = None) -> bool:
        """Validate geometric constraint precision."""
        if precision is None:
            precision = self.settings.default_precision

        # Extract constraint values and validate precision
        constraint_values = constraint_data.get('values', [])
        for value in constraint_values:
            if isinstance(value, (int, float, Decimal)):
                if not self.precision_math.validate_precision(value, precision):
                    return False

        return True

    # Performance validation rule implementations
def _validate_calculation_performance(self, operation_name: str,
                                       operation_result: Union[float, Decimal],
                                       expected_precision: Optional[Decimal] = None) -> bool:
        """Validate calculation performance."""
        # This is a placeholder for performance validation
        # In a real implementation, this would check calculation time, memory usage, etc.
        return True

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get a summary of validation results."""
        total_validations = len(self.validation_history)
        passed_validations = sum(1 for result in self.validation_history if result.is_valid)
        failed_validations = total_validations - passed_validations

        # Group by validation type
        by_type = {}
        for result in self.validation_history:
            validation_type = result.validation_type.value
            if validation_type not in by_type:
                by_type[validation_type] = {'passed': 0, 'failed': 0}

            if result.is_valid:
                by_type[validation_type]['passed'] += 1
            else:
                by_type[validation_type]['failed'] += 1

        # Group by validation level
        by_level = {}
        for result in self.validation_history:
            validation_level = result.validation_level.value
            if validation_level not in by_level:
                by_level[validation_level] = {'passed': 0, 'failed': 0}

            if result.is_valid:
                by_level[validation_level]['passed'] += 1
            else:
                by_level[validation_level]['failed'] += 1

        return {
            'total_validations': total_validations,
            'passed_validations': passed_validations,
            'failed_validations': failed_validations,
            'success_rate': passed_validations / total_validations if total_validations > 0 else 0,
            'by_type': by_type,
            'by_level': by_level,
            'recent_validations': [result.to_dict() for result in self.validation_history[-10:]]
        }

    def export_validation_report(self, filename: str):
        """Export validation results to a JSON file."""
        report = {
            'validation_summary': self.get_validation_summary(),
            'validation_history': [result.to_dict() for result in self.validation_history],
            'validation_rules': {
                name: {
                    'name': rule.name,
                    'validation_type': rule.validation_type.value,
                    'validation_level': rule.validation_level.value,
                    'description': rule.description,
                    'enabled': rule.enabled
                }
                for name, rule in self.validation_rules.items()
            }
        }

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"Validation report exported to: {filename}")

    def clear_validation_history(self):
        """Clear validation history."""
        self.validation_history.clear()
        self.logger.info("Validation history cleared")

    def get_failed_validations(self) -> List[ValidationResult]:
        """Get all failed validations."""
        return [result for result in self.validation_history if not result.is_valid]

    def get_critical_failures(self) -> List[ValidationResult]:
        """Get all critical validation failures."""
        return [result for result in self.validation_history
                if not result.is_valid and result.validation_level == ValidationLevel.CRITICAL]


class PrecisionTestingFramework:
    """
    Testing framework for precision validation.

    Provides comprehensive testing capabilities for precision validation
    including unit tests, integration tests, and performance tests.
    """

    def __init__(self, validator: Optional[PrecisionValidator] = None):
        """
        Initialize precision testing framework.

        Args:
            validator: Precision validator instance (default: new instance)
        """
        self.validator = validator or PrecisionValidator()
        self.test_results: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)

    def run_coordinate_tests(self) -> List[Dict[str, Any]]:
        """Run coordinate validation tests."""
        test_results = []

        # Test valid coordinates
        valid_coordinate = PrecisionCoordinate(1.000, 2.000, 3.000)
        results = self.validator.validate_coordinate(valid_coordinate)
        test_results.append({
            'test_name': 'valid_coordinate_test',
            'coordinate': valid_coordinate,
            'results': [result.to_dict() for result in results],
            'passed': all(result.is_valid for result in results)
        })

        # Test invalid coordinates (out of range)
        invalid_coordinate = PrecisionCoordinate(1e7, 1e7, 1e7)
        results = self.validator.validate_coordinate(invalid_coordinate)
        test_results.append({
            'test_name': 'invalid_coordinate_range_test',
            'coordinate': invalid_coordinate,
            'results': [result.to_dict() for result in results],
            'passed': not all(result.is_valid for result in results)
        })

        # Test precision validation
        precise_coordinate = PrecisionCoordinate(1.000001, 2.000001, 3.000001)
        results = self.validator.validate_coordinate(precise_coordinate)
        test_results.append({
            'test_name': 'coordinate_precision_test',
            'coordinate': precise_coordinate,
            'results': [result.to_dict() for result in results],
            'passed': all(result.is_valid for result in results)
        })

        self.test_results.extend(test_results)
        return test_results

    def run_geometric_tests(self) -> List[Dict[str, Any]]:
        """Run geometric validation tests."""
        test_results = []

        # Test distance calculation validation
        distance_result = self.validator.precision_math.distance_2d(0, 0, 3, 4)
        results = self.validator.validate_geometric_operation("distance_2d", distance_result)
        test_results.append({
            'test_name': 'distance_calculation_test',
            'operation': 'distance_2d',
            'result': distance_result,
            'results': [result.to_dict() for result in results],
            'passed': all(result.is_valid for result in results)
        })

        # Test angle calculation validation
        angle_result = self.validator.precision_math.angle_between_points(0, 0, 1, 1)
        results = self.validator.validate_geometric_operation("angle_calculation", angle_result)
        test_results.append({
            'test_name': 'angle_calculation_test',
            'operation': 'angle_calculation',
            'result': angle_result,
            'results': [result.to_dict() for result in results],
            'passed': all(result.is_valid for result in results)
        })

        self.test_results.extend(test_results)
        return test_results

    def run_constraint_tests(self) -> List[Dict[str, Any]]:
        """Run constraint validation tests."""
        test_results = []

        # Test valid constraint
        valid_constraint = {
            'type': 'distance',
            'values': [5.000, 5.000],
            'tolerance': 0.001
        }
        results = self.validator.validate_constraint("distance_constraint", valid_constraint)
        test_results.append({
            'test_name': 'valid_constraint_test',
            'constraint': valid_constraint,
            'results': [result.to_dict() for result in results],
            'passed': all(result.is_valid for result in results)
        })

        # Test invalid constraint (precision violation)
        invalid_constraint = {
            'type': 'distance',
            'values': [5.123456, 5.123456],
            'tolerance': 0.001
        }
        results = self.validator.validate_constraint("invalid_constraint", invalid_constraint)
        test_results.append({
            'test_name': 'invalid_constraint_test',
            'constraint': invalid_constraint,
            'results': [result.to_dict() for result in results],
            'passed': not all(result.is_valid for result in results)
        })

        self.test_results.extend(test_results)
        return test_results

    def run_performance_tests(self) -> List[Dict[str, Any]]:
        """Run performance validation tests."""
        test_results = []

        # Test batch validation performance
        import time

        start_time = time.time()
        validation_data = []
        for i in range(100):
            coordinate = PrecisionCoordinate(i * 0.001, i * 0.001, i * 0.001)
            validation_data.append({
                'type': 'coordinate',
                'coordinate': coordinate
            })

        results = self.validator.validate_batch(validation_data)
        end_time = time.time()

        test_results.append({
            'test_name': 'batch_validation_performance_test',
            'num_validations': len(validation_data),
            'execution_time': end_time - start_time,
            'results': [result.to_dict() for result in results],
            'passed': all(result.is_valid for result in results)
        })

        self.test_results.extend(test_results)
        return test_results

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all precision validation tests."""
        self.logger.info("Starting precision validation tests...")

        test_suites = {
            'coordinate_tests': self.run_coordinate_tests(),
            'geometric_tests': self.run_geometric_tests(),
            'constraint_tests': self.run_constraint_tests(),
            'performance_tests': self.run_performance_tests()
        }

        # Calculate overall test statistics
        total_tests = sum(len(suite) for suite in test_suites.values()
        passed_tests = sum(
            sum(1 for test in suite if test['passed'])
            for suite in test_suites.values()
        test_summary = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': passed_tests / total_tests if total_tests > 0 else 0,
            'test_suites': test_suites
        }

        self.logger.info(f"Precision validation tests completed: {passed_tests}/{total_tests} passed")
        return test_summary

    def export_test_report(self, filename: str):
        """Export test results to a JSON file."""
        report = {
            'test_summary': self.run_all_tests(),
            'validation_summary': self.validator.get_validation_summary()
        }

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"Test report exported to: {filename}")


# Example usage and testing
if __name__ == "__main__":
    # Create precision validator
    validator = PrecisionValidator()

    # Test coordinate validation
    coordinate = PrecisionCoordinate(1.000, 2.000, 3.000)
    results = validator.validate_coordinate(coordinate)

    print("Coordinate validation results:")
    for result in results:
        print(f"  {result.validation_type.value}: {result.is_valid} - {result.message}")

    # Test geometric operation validation
    distance = validator.precision_math.distance_2d(0, 0, 3, 4)
    results = validator.validate_geometric_operation("distance_2d", distance)

    print("\nGeometric validation results:")
    for result in results:
        print(f"  {result.validation_type.value}: {result.is_valid} - {result.message}")

    # Get validation summary
    summary = validator.get_validation_summary()
    print(f"\nValidation summary: {summary['passed_validations']}/{summary['total_validations']} passed")

    # Run testing framework
    test_framework = PrecisionTestingFramework(validator)
    test_summary = test_framework.run_all_tests()
    print(f"\nTest summary: {test_summary['passed_tests']}/{test_summary['total_tests']} passed")
