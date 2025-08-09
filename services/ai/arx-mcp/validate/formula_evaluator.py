"""
Formula Evaluation Engine for MCP Rule Validation

This module provides a safe and powerful formula evaluation system for the MCP rule engine.
It supports mathematical expressions, variable substitution, unit conversions, and context-aware calculations.

Key Features:
- Safe mathematical expression parsing
- Variable substitution from building context
- Unit conversion support
- Comprehensive error handling
- Performance optimization
"""

import re
import logging
import math
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass
from enum import Enum

from services.models.mcp_models import BuildingObject, RuleExecutionContext

logger = logging.getLogger(__name__)


class UnitType(Enum):
    """Supported unit types for conversion"""
    LENGTH = "length"
    AREA = "area"
    VOLUME = "volume"
    WEIGHT = "weight"
    POWER = "power"
    FLOW = "flow"
    TEMPERATURE = "temperature"


@dataclass
class UnitConversion:
    """Unit conversion definition"""
    from_unit: str
    to_unit: str
    conversion_factor: float
    unit_type: UnitType


class FormulaEvaluator:
    """
    Safe and powerful formula evaluation engine for MCP rule validation.

    Supports mathematical expressions, variable substitution, unit conversions,
    and context-aware calculations while maintaining security and performance.
    """

    def __init__(self):
        """Initialize the formula evaluator with supported operations and units"""
        self.logger = logging.getLogger(__name__)

        # Supported mathematical operations
        self.operators = {
            '+': lambda x, y: x + y,
            '-': lambda x, y: x - y,
            '*': lambda x, y: x * y,
            '/': lambda x, y: x / y if y != 0 else 0,
            '^': lambda x, y: x ** y,
            '%': lambda x, y: x % y if y != 0 else 0,
        }

        # Mathematical functions
        self.functions = {
            'abs': abs,
            'round': round,
            'floor': math.floor,
            'ceil': math.ceil,
            'sqrt': math.sqrt,
            'log': math.log,
            'log10': math.log10,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'min': min,
            'max': max,
            'sum': sum,
            'avg': lambda *args: sum(args) / len(args) if args else 0,
        }

        # Unit conversion table
        self.unit_conversions = self._initialize_unit_conversions()

        # Variable substitution patterns
        self.variable_patterns = {
            r'\{area\}': self._get_total_area,
            r'\{count\}': self._get_object_count,
            r'\{height\}': self._get_average_height,
            r'\{width\}': self._get_average_width,
            r'\{depth\}': self._get_average_depth,
            r'\{volume\}': self._get_total_volume,
            r'\{perimeter\}': self._get_total_perimeter,
        }

    def evaluate_formula(self, formula: str, context: RuleExecutionContext) -> float:
        """
        Evaluate a mathematical formula with variable substitution and unit conversion.

        Args:
            formula: Mathematical expression string (e.g., "area * height * 0.8")
            context: Rule execution context with building model and objects

        Returns:
            Calculated result as float

        Raises:
            FormulaEvaluationError: If formula cannot be evaluated safely
        """
        try:
            # Step 1: Preprocess formula with variable substitution
            processed_formula = self._substitute_variables(formula, context)

            # Step 2: Validate formula for security
            self._validate_formula(processed_formula)

            # Step 3: Parse and evaluate the formula
            result = self._evaluate_expression(processed_formula)

            # Step 4: Apply unit conversions if needed
            result = self._apply_unit_conversions(result, formula)

            self.logger.debug(f"Formula '{formula}' evaluated to {result}")
            return result

        except Exception as e:
            self.logger.error(f"Error evaluating formula '{formula}': {e}")
            raise FormulaEvaluationError(f"Failed to evaluate formula: {e}")

    def _substitute_variables(self, formula: str, context: RuleExecutionContext) -> str:
        """Substitute variables in formula with actual values from context"""
        processed_formula = formula

        # Substitute built-in variables
        for pattern, getter_func in self.variable_patterns.items():
            if re.search(pattern, processed_formula):
                value = getter_func(context.matched_objects)
                processed_formula = re.sub(pattern, str(value), processed_formula)

        # Substitute context calculations
        for key, value in context.calculations.items():
            placeholder = f"{{{key}}}"
            if placeholder in processed_formula:
                processed_formula = processed_formula.replace(placeholder, str(value)
        # Substitute object properties
        processed_formula = self._substitute_object_properties(processed_formula, context)

        return processed_formula

    def _substitute_object_properties(self, formula: str, context: RuleExecutionContext) -> str:
        """Substitute object property references in formula"""
        # Pattern: {objects.property_name} or {objects.object_type.property_name}
        property_pattern = r'\{objects\.([^}]+)\}'

        def replace_property(match):
            property_path = match.group(1)
            try:
                if '.' in property_path:
                    # Specific object type property
                    object_type, property_name = property_path.split('.', 1)
                    return str(self._get_property_sum(context.matched_objects, object_type, property_name)
                else:
                    # General property across all objects
                    return str(self._get_property_sum(context.matched_objects, None, property_path)
            except Exception as e:
                self.logger.warning(f"Failed to substitute property {property_path}: {e}")
                return "0"

        return re.sub(property_pattern, replace_property, formula)

    def _validate_formula(self, formula: str) -> None:
        """Validate formula for security and syntax"""
        # Check for dangerous operations
        dangerous_patterns = [
            r'eval\s*\(',
            r'exec\s*\(',
            r'import\s+',
            r'__\w+__',
            r'open\s*\(',
            r'file\s*\(',
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, formula, re.IGNORECASE):
                raise FormulaEvaluationError(f"Dangerous operation detected: {pattern}")

        # Check for balanced parentheses
        if formula.count('(') != formula.count(')'):
            raise FormulaEvaluationError("Unbalanced parentheses in formula")

        # Check for valid characters only
        valid_chars = r'[0-9a-zA-Z\s\+\-\*\/\^\%\(\)\.\,\{\}\[\]\<\>\=\!\&\|]'
        if not all(re.match(valid_chars, char) for char in formula):
            raise FormulaEvaluationError("Invalid characters in formula")

    def _evaluate_expression(self, expression: str) -> float:
        """Safely evaluate mathematical expression"""
        try:
            # Convert to postfix notation for safe evaluation
            tokens = self._tokenize(expression)
            postfix = self._infix_to_postfix(tokens)
            result = self._evaluate_postfix(postfix)

            if not isinstance(result, (int, float)):
                raise FormulaEvaluationError("Expression must evaluate to a number")

            return float(result)

        except Exception as e:
            raise FormulaEvaluationError(f"Expression evaluation failed: {e}")

    def _tokenize(self, expression: str) -> List[str]:
        """Tokenize mathematical expression"""
        # Remove whitespace
        expression = expression.replace(' ', '')

        # Split into tokens
        tokens = []
        current_token = ""

        for char in expression:
            if char.isdigit() or char == '.':
                current_token += char
            elif char in '+-*/^%()':
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
                tokens.append(char)
            elif char.isalpha():
                current_token += char
            else:
                if current_token:
                    tokens.append(current_token)
                    current_token = ""

        if current_token:
            tokens.append(current_token)

        return tokens

    def _infix_to_postfix(self, tokens: List[str]) -> List[str]:
        """Convert infix notation to postfix (Reverse Polish Notation)"""
        output = []
        operators = []
        precedence = {'^': 3, '*': 2, '/': 2, '%': 2, '+': 1, '-': 1}

        for token in tokens:
            if token.isdigit() or '.' in token:
                output.append(token)
            elif token in self.functions:
                operators.append(token)
            elif token == '(':
                operators.append(token)
            elif token == ')':
                while operators and operators[-1] != '(':
                    output.append(operators.pop()
                if operators and operators[-1] == '(':
                    operators.pop()
            elif token in precedence:
                while (operators and operators[-1] != '(' and
                       precedence.get(operators[-1], 0) >= precedence[token]):
                    output.append(operators.pop()
                operators.append(token)

        while operators:
            output.append(operators.pop()
        return output

    def _evaluate_postfix(self, postfix: List[str]) -> float:
        """Evaluate postfix expression"""
        stack = []

        for token in postfix:
            if token.isdigit() or '.' in token:
                stack.append(float(token)
            elif token in self.operators:
                if len(stack) < 2:
                    raise FormulaEvaluationError("Insufficient operands for operator")
                b, a = stack.pop(), stack.pop()
                result = self.operators[token](a, b)
                stack.append(result)
            elif token in self.functions:
                if len(stack) < 1:
                    raise FormulaEvaluationError("Insufficient operands for function")
                args = [stack.pop() for _ in range(self._get_function_arity(token))]
                result = self.functions[token](*args)
                stack.append(result)

        if len(stack) != 1:
            raise FormulaEvaluationError("Invalid expression")

        return stack[0]

    def _get_function_arity(self, func_name: str) -> int:
        """Get the number of arguments for a function"""
        if func_name in ['abs', 'floor', 'ceil', 'sqrt', 'log', 'log10', 'sin', 'cos', 'tan']:
            return 1
        elif func_name in ['min', 'max', 'sum', 'avg']:
            return -1  # Variable arity
        return 1

    def _apply_unit_conversions(self, result: float, original_formula: str) -> float:
        """Apply unit conversions if specified in formula"""
        # Look for unit conversion patterns in the original formula
        unit_pattern = r'convert\(([^,]+),\s*([^,]+),\s*([^)]+)\)
        match = re.search(unit_pattern, original_formula)

        if match:
            value, from_unit, to_unit = match.groups()
            try:
                conversion = self._find_conversion(from_unit, to_unit)
                if conversion:
                    return result * conversion.conversion_factor
            except Exception as e:
                self.logger.warning(f"Unit conversion failed: {e}")

        return result

    def _initialize_unit_conversions(self) -> List[UnitConversion]:
        """Initialize unit conversion table"""
        return [
            # Length conversions
            UnitConversion("ft", "m", 0.3048, UnitType.LENGTH),
            UnitConversion("in", "m", 0.0254, UnitType.LENGTH),
            UnitConversion("yd", "m", 0.9144, UnitType.LENGTH),

            # Area conversions
            UnitConversion("sqft", "sqm", 0.092903, UnitType.AREA),
            UnitConversion("acres", "sqm", 4046.86, UnitType.AREA),

            # Volume conversions
            UnitConversion("cuft", "cum", 0.0283168, UnitType.VOLUME),
            UnitConversion("gal", "l", 3.78541, UnitType.VOLUME),

            # Weight conversions
            UnitConversion("lb", "kg", 0.453592, UnitType.WEIGHT),
            UnitConversion("ton", "kg", 907.185, UnitType.WEIGHT),

            # Power conversions
            UnitConversion("hp", "w", 745.7, UnitType.POWER),
            UnitConversion("btu", "w", 0.293071, UnitType.POWER),
        ]

    def _find_conversion(self, from_unit: str, to_unit: str) -> Optional[UnitConversion]:
        """Find unit conversion between two units"""
        for conversion in self.unit_conversions:
            if conversion.from_unit == from_unit and conversion.to_unit == to_unit:
                return conversion
        return None

    # Context variable getters
def _get_total_area(self, objects: List[BuildingObject]) -> float:
        """Calculate total area of objects"""
        total = 0.0
        for obj in objects:
            area = self._get_object_area(obj)
            if area:
                total += area
        return total

    def _get_object_count(self, objects: List[BuildingObject]) -> int:
        """Get count of objects"""
        return len(objects)

    def _get_average_height(self, objects: List[BuildingObject]) -> float:
        """Calculate average height of objects"""
        heights = [self._get_object_height(obj) for obj in objects]
        valid_heights = [h for h in heights if h is not None]
        return sum(valid_heights) / len(valid_heights) if valid_heights else 0.0

    def _get_average_width(self, objects: List[BuildingObject]) -> float:
        """Calculate average width of objects"""
        widths = [self._get_object_width(obj) for obj in objects]
        valid_widths = [w for w in widths if w is not None]
        return sum(valid_widths) / len(valid_widths) if valid_widths else 0.0

    def _get_average_depth(self, objects: List[BuildingObject]) -> float:
        """Calculate average depth of objects"""
        depths = [self._get_object_depth(obj) for obj in objects]
        valid_depths = [d for d in depths if d is not None]
        return sum(valid_depths) / len(valid_depths) if valid_depths else 0.0

    def _get_total_volume(self, objects: List[BuildingObject]) -> float:
        """Calculate total volume of objects"""
        total = 0.0
        for obj in objects:
            volume = self._get_object_volume(obj)
            if volume:
                total += volume
        return total

    def _get_total_perimeter(self, objects: List[BuildingObject]) -> float:
        """Calculate total perimeter of objects"""
        total = 0.0
        for obj in objects:
            perimeter = self._get_object_perimeter(obj)
            if perimeter:
                total += perimeter
        return total

    def _get_property_sum(self, objects: List[BuildingObject], object_type: Optional[str], property_name: str) -> float:
        """Get sum of a property across objects, optionally filtered by type"""
        total = 0.0
        for obj in objects:
            if object_type is None or obj.object_type == object_type:
                value = obj.properties.get(property_name, 0)
                if isinstance(value, (int, float)):
                    total += value
        return total

    # Object property getters
def _get_object_area(self, obj: BuildingObject) -> Optional[float]:
        """Get object area"""
        if obj.location and 'width' in obj.location and 'height' in obj.location:
            return obj.location['width'] * obj.location['height']
        elif 'area' in obj.properties:
            return obj.properties['area']
        return None

    def _get_object_height(self, obj: BuildingObject) -> Optional[float]:
        """Get object height"""
        if obj.location and 'height' in obj.location:
            return obj.location['height']
        elif 'height' in obj.properties:
            return obj.properties['height']
        return None

    def _get_object_width(self, obj: BuildingObject) -> Optional[float]:
        """Get object width"""
        if obj.location and 'width' in obj.location:
            return obj.location['width']
        elif 'width' in obj.properties:
            return obj.properties['width']
        return None

    def _get_object_depth(self, obj: BuildingObject) -> Optional[float]:
        """Get object depth"""
        if obj.location and 'depth' in obj.location:
            return obj.location['depth']
        elif 'depth' in obj.properties:
            return obj.properties['depth']
        return None

    def _get_object_volume(self, obj: BuildingObject) -> Optional[float]:
        """Get object volume"""
        if obj.location and all(dim in obj.location for dim in ['width', 'height', 'depth']):
            return obj.location['width'] * obj.location['height'] * obj.location['depth']
        elif 'volume' in obj.properties:
            return obj.properties['volume']
        return None

    def _get_object_perimeter(self, obj: BuildingObject) -> Optional[float]:
        """Get object perimeter"""
        if obj.location and 'width' in obj.location and 'height' in obj.location:
            return 2 * (obj.location['width'] + obj.location['height'])
        elif 'perimeter' in obj.properties:
            return obj.properties['perimeter']
        return None


class FormulaEvaluationError(Exception):
    """Exception raised when formula evaluation fails"""
    pass ))))))
