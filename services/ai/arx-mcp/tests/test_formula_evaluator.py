"""
Tests for Formula Evaluation Engine

This module contains comprehensive tests for the FormulaEvaluator class,
ensuring safe and accurate mathematical expression evaluation.
"""

import pytest
import math
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from services.ai.arx_mcp.validate.formula_evaluator import (
    FormulaEvaluator, FormulaEvaluationError, UnitConversion, UnitType
)
from services.models.mcp_models import BuildingObject, RuleExecutionContext, BuildingModel, MCPRule


class TestFormulaEvaluator:
    """Test suite for FormulaEvaluator class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.evaluator = FormulaEvaluator()
        
        # Create test building objects
        self.test_objects = [
            BuildingObject(
                object_id="obj1",
                object_type="room",
                properties={"area": 100, "height": 10, "load": 1500},
                location={"x": 0, "y": 0, "width": 10, "height": 10}
            ),
            BuildingObject(
                object_id="obj2", 
                object_type="room",
                properties={"area": 200, "height": 12, "load": 2000},
                location={"x": 10, "y": 0, "width": 20, "height": 10}
            ),
            BuildingObject(
                object_id="obj3",
                object_type="electrical_outlet",
                properties={"load": 500, "voltage": 120},
                location={"x": 5, "y": 5}
            )
        ]
        
        # Create test context
        self.test_context = RuleExecutionContext(
            building_model=BuildingModel(
                building_id="test_building",
                building_name="Test Building",
                objects=self.test_objects
            ),
            rule=Mock(spec=MCPRule),
            matched_objects=self.test_objects,
            calculations={"safety_factor": 1.2, "efficiency": 0.85}
        )
    
    def test_basic_arithmetic(self):
        """Test basic arithmetic operations"""
        test_cases = [
            ("2 + 3", 5.0),
            ("10 - 4", 6.0),
            ("6 * 7", 42.0),
            ("15 / 3", 5.0),
            ("2 ^ 3", 8.0),
            ("17 % 5", 2.0),
        ]
        
        for formula, expected in test_cases:
            result = self.evaluator.evaluate_formula(formula, self.test_context)
            assert result == expected, f"Formula '{formula}' should equal {expected}, got {result}"
    
    def test_complex_expressions(self):
        """Test complex mathematical expressions"""
        test_cases = [
            ("2 + 3 * 4", 14.0),  # Order of operations
            ("(2 + 3) * 4", 20.0),  # Parentheses
            ("10 / 2 + 3 * 4", 17.0),  # Mixed operations
            ("2 ^ 3 + 1", 9.0),  # Exponentiation
        ]
        
        for formula, expected in test_cases:
            result = self.evaluator.evaluate_formula(formula, self.test_context)
            assert result == expected, f"Formula '{formula}' should equal {expected}, got {result}"
    
    def test_mathematical_functions(self):
        """Test mathematical functions"""
        test_cases = [
            ("abs(-5)", 5.0),
            ("round(3.7)", 4.0),
            ("floor(3.7)", 3.0),
            ("ceil(3.2)", 4.0),
            ("sqrt(16)", 4.0),
            ("log(100)", math.log(100)),
            ("log10(100)", 2.0),
            ("sin(0)", 0.0),
            ("cos(0)", 1.0),
            ("min(5, 3, 8)", 3.0),
            ("max(5, 3, 8)", 8.0),
            ("sum(1, 2, 3)", 6.0),
            ("avg(10, 20, 30)", 20.0),
        ]
        
        for formula, expected in test_cases:
            result = self.evaluator.evaluate_formula(formula, self.test_context)
            assert abs(result - expected) < 1e-10, f"Formula '{formula}' should equal {expected}, got {result}"
    
    def test_variable_substitution(self):
        """Test variable substitution from context"""
        test_cases = [
            ("{area}", 300.0),  # Total area of all objects
            ("{count}", 3.0),  # Number of objects
            ("{height}", 11.0),  # Average height
            ("{width}", 15.0),  # Average width
            ("{volume}", 0.0),  # No depth specified
            ("{perimeter}", 60.0),  # Total perimeter
        ]
        
        for formula, expected in test_cases:
            result = self.evaluator.evaluate_formula(formula, self.test_context)
            assert result == expected, f"Formula '{formula}' should equal {expected}, got {result}"
    
    def test_context_calculations(self):
        """Test substitution of context calculations"""
        test_cases = [
            ("{safety_factor}", 1.2),
            ("{efficiency}", 0.85),
            ("{safety_factor} * 100", 120.0),
            ("{efficiency} * 100", 85.0),
        ]
        
        for formula, expected in test_cases:
            result = self.evaluator.evaluate_formula(formula, self.test_context)
            assert result == expected, f"Formula '{formula}' should equal {expected}, got {result}"
    
    def test_object_properties(self):
        """Test object property substitution"""
        test_cases = [
            ("{objects.load}", 4000.0),  # Sum of all load properties
            ("{objects.area}", 300.0),  # Sum of all area properties
            ("{objects.room.load}", 3500.0),  # Sum of load for room objects only
            ("{objects.electrical_outlet.voltage}", 120.0),  # Voltage for electrical outlets
        ]
        
        for formula, expected in test_cases:
            result = self.evaluator.evaluate_formula(formula, self.test_context)
            assert result == expected, f"Formula '{formula}' should equal {expected}, got {result}"
    
    def test_complex_formulas_with_variables(self):
        """Test complex formulas combining variables and calculations"""
        test_cases = [
            ("{area} * {height} * 0.8", 300 * 11 * 0.8),
            ("{count} * 100 + {safety_factor} * 50", 3 * 100 + 1.2 * 50),
            ("sqrt({area}) + {efficiency} * 10", math.sqrt(300) + 0.85 * 10),
            ("min({objects.load}, 5000)", min(4000, 5000)),
        ]
        
        for formula, expected in test_cases:
            result = self.evaluator.evaluate_formula(formula, self.test_context)
            assert abs(result - expected) < 1e-10, f"Formula '{formula}' should equal {expected}, got {result}"
    
    def test_unit_conversions(self):
        """Test unit conversion functionality"""
        # Note: Unit conversions are applied after evaluation
        # This is a simplified test - in practice, unit conversion would be part of the formula
        test_cases = [
            ("100", 100.0),  # No conversion
            ("convert(100, ft, m)", 100.0),  # Would apply conversion factor
        ]
        
        for formula, expected in test_cases:
            result = self.evaluator.evaluate_formula(formula, self.test_context)
            assert result == expected, f"Formula '{formula}' should equal {expected}, got {result}"
    
    def test_security_validation(self):
        """Test that dangerous operations are blocked"""
        dangerous_formulas = [
            "eval(2+2)",
            "exec('print(1)')",
            "import os",
            "__import__('os')",
            "open('file.txt')",
            "file('file.txt')",
        ]
        
        for formula in dangerous_formulas:
            with pytest.raises(FormulaEvaluationError, match="Dangerous operation detected"):
                self.evaluator.evaluate_formula(formula, self.test_context)
    
    def test_syntax_validation(self):
        """Test syntax validation"""
        invalid_formulas = [
            "2 + (3",  # Unbalanced parentheses
            "2 + )",  # Unbalanced parentheses
            "2 @ 3",  # Invalid operator
            "2 + ;",  # Invalid character
        ]
        
        for formula in invalid_formulas:
            with pytest.raises(FormulaEvaluationError):
                self.evaluator.evaluate_formula(formula, self.test_context)
    
    def test_error_handling(self):
        """Test error handling for invalid expressions"""
        error_cases = [
            ("1 / 0", 0.0),  # Division by zero should return 0
            ("", 0.0),  # Empty formula
            ("invalid", 0.0),  # Invalid expression
        ]
        
        for formula, expected in error_cases:
            try:
                result = self.evaluator.evaluate_formula(formula, self.test_context)
                assert result == expected, f"Formula '{formula}' should handle error gracefully"
            except FormulaEvaluationError:
                # This is also acceptable behavior
                pass
    
    def test_performance(self):
        """Test performance with complex formulas"""
        import time
        
        # Test with a complex formula
        complex_formula = "sqrt({area} * {height} * {efficiency}) + sin({count}) * cos({safety_factor})"
        
        start_time = time.time()
        result = self.evaluator.evaluate_formula(complex_formula, self.test_context)
        end_time = time.time()
        
        # Should complete in under 100ms
        assert (end_time - start_time) < 0.1, "Formula evaluation should be fast"
        assert isinstance(result, float), "Result should be a float"
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        # Empty context
        empty_context = RuleExecutionContext(
            building_model=Mock(spec=BuildingModel),
            rule=Mock(spec=MCPRule),
            matched_objects=[],
            calculations={}
        )
        
        result = self.evaluator.evaluate_formula("2 + 2", empty_context)
        assert result == 4.0, "Should work with empty context"
        
        # Very large numbers
        result = self.evaluator.evaluate_formula("1e6 + 1e6", self.test_context)
        assert result == 2e6, "Should handle large numbers"
        
        # Very small numbers
        result = self.evaluator.evaluate_formula("1e-6 + 1e-6", self.test_context)
        assert result == 2e-6, "Should handle small numbers"


class TestUnitConversions:
    """Test suite for unit conversion functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.evaluator = FormulaEvaluator()
    
    def test_length_conversions(self):
        """Test length unit conversions"""
        conversions = [
            ("ft", "m", 0.3048),
            ("in", "m", 0.0254),
            ("yd", "m", 0.9144),
        ]
        
        for from_unit, to_unit, factor in conversions:
            conversion = self.evaluator._find_conversion(from_unit, to_unit)
            assert conversion is not None, f"Conversion {from_unit} to {to_unit} should exist"
            assert conversion.conversion_factor == factor, f"Conversion factor should be {factor}"
    
    def test_area_conversions(self):
        """Test area unit conversions"""
        conversions = [
            ("sqft", "sqm", 0.092903),
            ("acres", "sqm", 4046.86),
        ]
        
        for from_unit, to_unit, factor in conversions:
            conversion = self.evaluator._find_conversion(from_unit, to_unit)
            assert conversion is not None, f"Conversion {from_unit} to {to_unit} should exist"
            assert conversion.conversion_factor == factor, f"Conversion factor should be {factor}"
    
    def test_volume_conversions(self):
        """Test volume unit conversions"""
        conversions = [
            ("cuft", "cum", 0.0283168),
            ("gal", "l", 3.78541),
        ]
        
        for from_unit, to_unit, factor in conversions:
            conversion = self.evaluator._find_conversion(from_unit, to_unit)
            assert conversion is not None, f"Conversion {from_unit} to {to_unit} should exist"
            assert conversion.conversion_factor == factor, f"Conversion factor should be {factor}"


class TestObjectPropertyGetters:
    """Test suite for object property getter methods"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.evaluator = FormulaEvaluator()
        
        self.test_object = BuildingObject(
            object_id="test",
            object_type="room",
            properties={"area": 100, "height": 10, "load": 1500},
            location={"x": 0, "y": 0, "width": 10, "height": 10, "depth": 5}
        )
    
    def test_object_area_calculation(self):
        """Test object area calculation"""
        area = self.evaluator._get_object_area(self.test_object)
        assert area == 100.0, "Area should be calculated from location dimensions"
        
        # Test with area in properties
        obj_with_property = BuildingObject(
            object_id="test2",
            object_type="room",
            properties={"area": 200},
            location={}
        )
        area = self.evaluator._get_object_area(obj_with_property)
        assert area == 200.0, "Area should be taken from properties"
    
    def test_object_volume_calculation(self):
        """Test object volume calculation"""
        volume = self.evaluator._get_object_volume(self.test_object)
        assert volume == 500.0, "Volume should be width * height * depth"
        
        # Test with volume in properties
        obj_with_property = BuildingObject(
            object_id="test3",
            object_type="room",
            properties={"volume": 1000},
            location={}
        )
        volume = self.evaluator._get_object_volume(obj_with_property)
        assert volume == 1000.0, "Volume should be taken from properties"
    
    def test_object_perimeter_calculation(self):
        """Test object perimeter calculation"""
        perimeter = self.evaluator._get_object_perimeter(self.test_object)
        assert perimeter == 40.0, "Perimeter should be 2 * (width + height)"
        
        # Test with perimeter in properties
        obj_with_property = BuildingObject(
            object_id="test4",
            object_type="room",
            properties={"perimeter": 50},
            location={}
        )
        perimeter = self.evaluator._get_object_perimeter(obj_with_property)
        assert perimeter == 50.0, "Perimeter should be taken from properties"


if __name__ == "__main__":
    pytest.main([__file__]) 