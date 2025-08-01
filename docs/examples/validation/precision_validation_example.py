#!/usr/bin/env python3
"""
Precision Validation System Example

This example demonstrates the comprehensive precision validation system
for CAD applications, including coordinate validation, geometric validation,
constraint validation, and testing framework.
"""

import sys
import os
import json
import time
from decimal import Decimal

# Add the parent directory to the path to import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from svgx_engine.core.precision_validator import (
    PrecisionValidator,
    PrecisionTestingFramework,
    ValidationLevel,
    ValidationType,
    ValidationRule
)
from svgx_engine.core.precision_coordinate import PrecisionCoordinate
from svgx_engine.core.precision_math import PrecisionMath, PrecisionSettings


def demonstrate_coordinate_validation():
    """Demonstrate coordinate validation functionality."""
    print("\n" + "="*60)
    print("COORDINATE VALIDATION DEMONSTRATION")
    print("="*60)
    
    # Create precision validator
    validator = PrecisionValidator()
    
    # Test valid coordinates
    print("\n1. Testing Valid Coordinates:")
    valid_coordinates = [
        PrecisionCoordinate(1.000, 2.000, 3.000),
        PrecisionCoordinate(10.500, 20.750, 30.250),
        PrecisionCoordinate(0.001, 0.002, 0.003)  # Sub-millimeter precision
    ]
    
    for i, coord in enumerate(valid_coordinates, 1):
        print(f"\n   Coordinate {i}: {coord}")
        results = validator.validate_coordinate(coord)
        
        for result in results:
            status = "✓ PASS" if result.is_valid else "✗ FAIL"
            print(f"     {result.validation_type.value}: {status} - {result.message}")
    
    # Test invalid coordinates
    print("\n2. Testing Invalid Coordinates:")
    invalid_coordinates = [
        PrecisionCoordinate(1e7, 1e7, 1e7),  # Out of range
        PrecisionCoordinate(1.000001, 2.000001, 3.000001),  # Precision violation
        PrecisionCoordinate(1.000, float('nan'), 3.000)  # NaN value
    ]
    
    for i, coord in enumerate(invalid_coordinates, 1):
        print(f"\n   Invalid Coordinate {i}: {coord}")
        results = validator.validate_coordinate(coord)
        
        for result in results:
            status = "✓ PASS" if result.is_valid else "✗ FAIL"
            print(f"     {result.validation_type.value}: {status} - {result.message}")


def demonstrate_geometric_validation():
    """Demonstrate geometric validation functionality."""
    print("\n" + "="*60)
    print("GEOMETRIC VALIDATION DEMONSTRATION")
    print("="*60)
    
    # Create precision validator
    validator = PrecisionValidator()
    
    # Test distance calculations
    print("\n1. Testing Distance Calculations:")
    distance_tests = [
        {"name": "2D Distance", "points": (0, 0, 3, 4), "expected": 5.000},
        {"name": "3D Distance", "points": (0, 0, 0, 1, 1, 1), "expected": 1.732},
        {"name": "Precise Distance", "points": (1.000001, 2.000001, 3.000001, 4.000001), "expected": 3.606}
    ]
    
    for test in distance_tests:
        print(f"\n   {test['name']}:")
        if len(test['points']) == 4:  # 2D distance
            distance = validator.precision_math.distance_2d(*test['points'])
        else:  # 3D distance
            distance = validator.precision_math.distance_3d(*test['points'])
        
        print(f"     Calculated: {distance}")
        print(f"     Expected: {test['expected']}")
        
        results = validator.validate_geometric_operation(test['name'].lower().replace(' ', '_'), distance)
        
        for result in results:
            status = "✓ PASS" if result.is_valid else "✗ FAIL"
            print(f"     {result.validation_type.value}: {status} - {result.message}")
    
    # Test angle calculations
    print("\n2. Testing Angle Calculations:")
    angle_tests = [
        {"name": "45° Angle", "points": (0, 0, 1, 1), "expected": 0.785},
        {"name": "90° Angle", "points": (0, 0, 1, 0), "expected": 0.000},
        {"name": "180° Angle", "points": (0, 0, -1, 0), "expected": 3.142}
    ]
    
    for test in angle_tests:
        print(f"\n   {test['name']}:")
        angle = validator.precision_math.angle_between_points(*test['points'])
        
        print(f"     Calculated: {angle}")
        print(f"     Expected: {test['expected']}")
        
        results = validator.validate_geometric_operation("angle_calculation", angle)
        
        for result in results:
            status = "✓ PASS" if result.is_valid else "✗ FAIL"
            print(f"     {result.validation_type.value}: {status} - {result.message}")


def demonstrate_constraint_validation():
    """Demonstrate constraint validation functionality."""
    print("\n" + "="*60)
    print("CONSTRAINT VALIDATION DEMONSTRATION")
    print("="*60)
    
    # Create precision validator
    validator = PrecisionValidator()
    
    # Test valid constraints
    print("\n1. Testing Valid Constraints:")
    valid_constraints = [
        {
            "name": "Distance Constraint",
            "data": {"type": "distance", "values": [5.000, 5.000], "tolerance": 0.001}
        },
        {
            "name": "Angle Constraint",
            "data": {"type": "angle", "values": [1.570796], "tolerance": 0.001}  # 90°
        },
        {
            "name": "Parallel Constraint",
            "data": {"type": "parallel", "values": [0.000, 0.000], "tolerance": 0.001}
        }
    ]
    
    for constraint in valid_constraints:
        print(f"\n   {constraint['name']}:")
        print(f"     Data: {constraint['data']}")
        
        results = validator.validate_constraint(constraint['name'].lower().replace(' ', '_'), constraint['data'])
        
        for result in results:
            status = "✓ PASS" if result.is_valid else "✗ FAIL"
            print(f"     {result.validation_type.value}: {status} - {result.message}")
    
    # Test invalid constraints
    print("\n2. Testing Invalid Constraints:")
    invalid_constraints = [
        {
            "name": "Precision Violation",
            "data": {"type": "distance", "values": [5.123456, 5.123456], "tolerance": 0.001}
        },
        {
            "name": "Invalid Type",
            "data": {"type": "invalid", "values": [1.000], "tolerance": 0.001}
        }
    ]
    
    for constraint in invalid_constraints:
        print(f"\n   {constraint['name']}:")
        print(f"     Data: {constraint['data']}")
        
        results = validator.validate_constraint(constraint['name'].lower().replace(' ', '_'), constraint['data'])
        
        for result in results:
            status = "✓ PASS" if result.is_valid else "✗ FAIL"
            print(f"     {result.validation_type.value}: {status} - {result.message}")


def demonstrate_custom_validation_rules():
    """Demonstrate custom validation rule creation."""
    print("\n" + "="*60)
    print("CUSTOM VALIDATION RULES DEMONSTRATION")
    print("="*60)
    
    # Create precision validator
    validator = PrecisionValidator()
    
    # Create custom validation rules
    def validate_first_quadrant(coordinate, precision):
        """Validate that coordinate is in first quadrant."""
        return coordinate.x >= 0 and coordinate.y >= 0 and coordinate.z >= 0
    
    def validate_magnitude_limit(coordinate, precision):
        """Validate that coordinate magnitude is within limit."""
        magnitude = coordinate.magnitude
        max_magnitude = 1000.0
        return magnitude <= max_magnitude
    
    def validate_precision_accuracy(coordinate, precision):
        """Validate coordinate precision accuracy."""
        # Check if coordinate values are within precision tolerance
        x_valid = abs(coordinate.x - round(coordinate.x / float(precision)) * float(precision)) <= float(precision)
        y_valid = abs(coordinate.y - round(coordinate.y / float(precision)) * float(precision)) <= float(precision)
        z_valid = abs(coordinate.z - round(coordinate.z / float(precision)) * float(precision)) <= float(precision)
        return x_valid and y_valid and z_valid
    
    # Register custom rules
    custom_rules = [
        ValidationRule(
            name="first_quadrant_check",
            validation_type=ValidationType.COORDINATE,
            validation_level=ValidationLevel.WARNING,
            rule_function=validate_first_quadrant,
            description="Ensure coordinate is in first quadrant"
        ),
        ValidationRule(
            name="magnitude_limit_check",
            validation_type=ValidationType.COORDINATE,
            validation_level=ValidationLevel.CRITICAL,
            rule_function=validate_magnitude_limit,
            description="Ensure coordinate magnitude is within limit"
        ),
        ValidationRule(
            name="precision_accuracy_check",
            validation_type=ValidationType.PRECISION,
            validation_level=ValidationLevel.CRITICAL,
            rule_function=validate_precision_accuracy,
            description="Validate coordinate precision accuracy"
        )
    ]
    
    for rule in custom_rules:
        validator.register_rule(rule)
        print(f"\n   Registered custom rule: {rule.name}")
        print(f"     Type: {rule.validation_type.value}")
        print(f"     Level: {rule.validation_level.value}")
        print(f"     Description: {rule.description}")
    
    # Test custom rules
    print("\n2. Testing Custom Rules:")
    test_coordinates = [
        PrecisionCoordinate(1.000, 2.000, 3.000),  # Valid
        PrecisionCoordinate(-1.000, 2.000, 3.000),  # Invalid (not in first quadrant)
        PrecisionCoordinate(500.000, 500.000, 500.000),  # Valid magnitude
        PrecisionCoordinate(1000.000, 1000.000, 1000.000)  # Invalid magnitude
    ]
    
    for i, coord in enumerate(test_coordinates, 1):
        print(f"\n   Test Coordinate {i}: {coord}")
        results = validator.validate_coordinate(coord)
        
        # Find custom rule results
        custom_results = [r for r in results if any(rule.name in r.message for rule in custom_rules)]
        
        for result in custom_results:
            status = "✓ PASS" if result.is_valid else "✗ FAIL"
            print(f"     {result.message}: {status}")


def demonstrate_batch_validation():
    """Demonstrate batch validation functionality."""
    print("\n" + "="*60)
    print("BATCH VALIDATION DEMONSTRATION")
    print("="*60)
    
    # Create precision validator
    validator = PrecisionValidator()
    
    # Create batch validation data
    validation_data = []
    
    # Add coordinate validations
    for i in range(5):
        coordinate = PrecisionCoordinate(i * 0.001, i * 0.001, i * 0.001)
        validation_data.append({
            'type': 'coordinate',
            'coordinate': coordinate
        })
    
    # Add geometric validations
    geometric_operations = [
        {"name": "distance_2d", "result": 5.000},
        {"name": "angle_calculation", "result": 0.785},
        {"name": "distance_3d", "result": 1.732}
    ]
    
    for op in geometric_operations:
        validation_data.append({
            'type': 'geometric',
            'operation_name': op['name'],
            'operation_result': op['result']
        })
    
    # Add constraint validations
    constraints = [
        {"name": "distance_constraint", "data": {"type": "distance", "values": [5.000]}},
        {"name": "angle_constraint", "data": {"type": "angle", "values": [1.570796]}}
    ]
    
    for constraint in constraints:
        validation_data.append({
            'type': 'constraint',
            'constraint_name': constraint['name'],
            'constraint_data': constraint['data']
        })
    
    print(f"\n   Batch validation data: {len(validation_data)} items")
    
    # Perform batch validation
    start_time = time.time()
    batch_results = validator.validate_batch(validation_data)
    end_time = time.time()
    
    print(f"\n   Batch validation completed in {end_time - start_time:.4f} seconds")
    print(f"   Total results: {len(batch_results)}")
    
    # Analyze results
    passed_results = [r for r in batch_results if r.is_valid]
    failed_results = [r for r in batch_results if not r.is_valid]
    
    print(f"   Passed validations: {len(passed_results)}")
    print(f"   Failed validations: {len(failed_results)}")
    print(f"   Success rate: {len(passed_results) / len(batch_results) * 100:.1f}%")
    
    # Show validation summary
    summary = validator.get_validation_summary()
    print(f"\n   Validation Summary:")
    print(f"     Total validations: {summary['total_validations']}")
    print(f"     Passed validations: {summary['passed_validations']}")
    print(f"     Failed validations: {summary['failed_validations']}")
    print(f"     Success rate: {summary['success_rate'] * 100:.1f}%")


def demonstrate_testing_framework():
    """Demonstrate testing framework functionality."""
    print("\n" + "="*60)
    print("TESTING FRAMEWORK DEMONSTRATION")
    print("="*60)
    
    # Create testing framework
    test_framework = PrecisionTestingFramework()
    
    print("\n1. Running Coordinate Tests:")
    coordinate_tests = test_framework.run_coordinate_tests()
    print(f"   Coordinate tests completed: {len(coordinate_tests)} tests")
    
    for test in coordinate_tests:
        status = "✓ PASS" if test['passed'] else "✗ FAIL"
        print(f"     {test['test_name']}: {status}")
    
    print("\n2. Running Geometric Tests:")
    geometric_tests = test_framework.run_geometric_tests()
    print(f"   Geometric tests completed: {len(geometric_tests)} tests")
    
    for test in geometric_tests:
        status = "✓ PASS" if test['passed'] else "✗ FAIL"
        print(f"     {test['test_name']}: {status}")
    
    print("\n3. Running Constraint Tests:")
    constraint_tests = test_framework.run_constraint_tests()
    print(f"   Constraint tests completed: {len(constraint_tests)} tests")
    
    for test in constraint_tests:
        status = "✓ PASS" if test['passed'] else "✗ FAIL"
        print(f"     {test['test_name']}: {status}")
    
    print("\n4. Running Performance Tests:")
    performance_tests = test_framework.run_performance_tests()
    print(f"   Performance tests completed: {len(performance_tests)} tests")
    
    for test in performance_tests:
        status = "✓ PASS" if test['passed'] else "✗ FAIL"
        print(f"     {test['test_name']}: {status}")
        if 'execution_time' in test:
            print(f"       Execution time: {test['execution_time']:.4f} seconds")
    
    print("\n5. Running All Tests:")
    test_summary = test_framework.run_all_tests()
    
    print(f"   Total tests: {test_summary['total_tests']}")
    print(f"   Passed tests: {test_summary['passed_tests']}")
    print(f"   Failed tests: {test_summary['failed_tests']}")
    print(f"   Success rate: {test_summary['success_rate'] * 100:.1f}%")


def demonstrate_error_handling():
    """Demonstrate error handling and reporting."""
    print("\n" + "="*60)
    print("ERROR HANDLING AND REPORTING DEMONSTRATION")
    print("="*60)
    
    # Create precision validator
    validator = PrecisionValidator()
    
    # Test various error conditions
    print("\n1. Testing Error Conditions:")
    
    # Test with invalid coordinates
    invalid_coordinates = [
        PrecisionCoordinate(1e7, 1e7, 1e7),  # Out of range
        PrecisionCoordinate(1.000001, 2.000001, 3.000001),  # Precision violation
        PrecisionCoordinate(1.000, float('nan'), 3.000)  # NaN value
    ]
    
    for i, coord in enumerate(invalid_coordinates, 1):
        print(f"\n   Error Test {i}: {coord}")
        results = validator.validate_coordinate(coord)
        
        failed_results = [r for r in results if not r.is_valid]
        print(f"     Failed validations: {len(failed_results)}")
        
        for result in failed_results:
            print(f"       {result.validation_level.value}: {result.message}")
    
    # Test critical failures
    print("\n2. Critical Failures:")
    critical_failures = validator.get_critical_failures()
    print(f"   Critical failures: {len(critical_failures)}")
    
    for failure in critical_failures[:3]:  # Show first 3
        print(f"     {failure.validation_type.value}: {failure.message}")
    
    # Test validation summary
    print("\n3. Validation Summary:")
    summary = validator.get_validation_summary()
    
    print(f"   Total validations: {summary['total_validations']}")
    print(f"   Passed validations: {summary['passed_validations']}")
    print(f"   Failed validations: {summary['failed_validations']}")
    print(f"   Success rate: {summary['success_rate'] * 100:.1f}%")
    
    # Show results by type
    print(f"\n   Results by type:")
    for validation_type, stats in summary['by_type'].items():
        print(f"     {validation_type}: {stats['passed']} passed, {stats['failed']} failed")
    
    # Show results by level
    print(f"\n   Results by level:")
    for validation_level, stats in summary['by_level'].items():
        print(f"     {validation_level}: {stats['passed']} passed, {stats['failed']} failed")


def main():
    """Main demonstration function."""
    print("PRECISION VALIDATION SYSTEM DEMONSTRATION")
    print("="*60)
    print("This demonstration shows the comprehensive precision validation")
    print("system for CAD applications with sub-millimeter accuracy.")
    print("="*60)
    
    try:
        # Run all demonstrations
        demonstrate_coordinate_validation()
        demonstrate_geometric_validation()
        demonstrate_constraint_validation()
        demonstrate_custom_validation_rules()
        demonstrate_batch_validation()
        demonstrate_testing_framework()
        demonstrate_error_handling()
        
        print("\n" + "="*60)
        print("DEMONSTRATION COMPLETED SUCCESSFULLY")
        print("="*60)
        print("The precision validation system provides comprehensive")
        print("validation capabilities for CAD applications with")
        print("sub-millimeter accuracy and robust error handling.")
        print("="*60)
        
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 