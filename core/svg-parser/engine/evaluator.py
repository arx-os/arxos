"""
Behavior Profile Evaluator
Evaluate expressions with input bindings and validate outputs
"""

import os
import json
import math
import re
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime
import ast
import operator

from behavior_loader import BehaviorLoader, BehaviorProfile, Variable, Calculation, CalculationType, VariableType

logger = logging.getLogger(__name__)


class EvaluationError(Exception):
    """Exception for evaluation errors"""
    pass


class EvaluationResult(Enum):
    """Evaluation result types"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INVALID_INPUT = "invalid_input"
    DIVISION_BY_ZERO = "division_by_zero"
    INVALID_EXPRESSION = "invalid_expression"
    MISSING_VARIABLE = "missing_variable"
    TYPE_MISMATCH = "type_mismatch"


@dataclass
class EvaluationContext:
    """Context for expression evaluation"""
    variables: Dict[str, Any]
    profile: BehaviorProfile
    calculation: Calculation
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class EvaluationOutput:
    """Output from expression evaluation"""
    result: EvaluationResult
    value: Any
    error_message: Optional[str]
    warnings: List[str]
    execution_time: float
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}


class BehaviorEvaluator:
    """Evaluator for behavior profile expressions"""
    
    def __init__(self, behavior_loader: Optional[BehaviorLoader] = None):
        self.behavior_loader = behavior_loader or BehaviorLoader()
        self.safe_operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
            ast.Eq: operator.eq,
            ast.NotEq: operator.ne,
            ast.Lt: operator.lt,
            ast.LtE: operator.le,
            ast.Gt: operator.gt,
            ast.GtE: operator.ge,
            ast.And: operator.and_,
            ast.Or: operator.or_,
            ast.Not: operator.not_
        }
        
        self.logger = logging.getLogger(__name__)
    
    def evaluate_profile(self, profile_id: str, input_values: Dict[str, Any] = None) -> Dict[str, EvaluationOutput]:
        """Evaluate all calculations in a behavior profile"""
        
        profile = self.behavior_loader.get_profile(profile_id)
        if not profile:
            raise EvaluationError(f"Profile {profile_id} not found")
        
        # Prepare input values
        if input_values is None:
            input_values = {}
        
        # Set default values for variables
        for var_name, variable in profile.variables.items():
            if var_name not in input_values and variable.default_value is not None:
                input_values[var_name] = variable.default_value
        
        results = {}
        
        # Evaluate each calculation
        for calc_name, calculation in profile.calculations.items():
            try:
                result = self.evaluate_calculation(calculation, input_values, profile)
                results[calc_name] = result
                
                # Update input values with calculation results
                if result.result == EvaluationResult.SUCCESS:
                    input_values[calculation.output_variable] = result.value
                    
            except Exception as e:
                self.logger.error(f"Failed to evaluate calculation {calc_name}: {e}")
                results[calc_name] = EvaluationOutput(
                    result=EvaluationResult.ERROR,
                    value=None,
                    error_message=str(e),
                    warnings=[],
                    execution_time=0.0,
                    metadata={}
                )
        
        return results
    
    def evaluate_calculation(self, calculation: Calculation, input_values: Dict[str, Any], 
                           profile: BehaviorProfile) -> EvaluationOutput:
        """Evaluate a single calculation"""
        
        start_time = datetime.utcnow()
        
        try:
            # Validate input variables
            missing_vars = []
            for var_name in calculation.input_variables:
                if var_name not in input_values:
                    missing_vars.append(var_name)
            
            if missing_vars:
                return EvaluationOutput(
                    result=EvaluationResult.MISSING_VARIABLE,
                    value=None,
                    error_message=f"Missing input variables: {missing_vars}",
                    warnings=[],
                    execution_time=(datetime.utcnow() - start_time).total_seconds(),
                    metadata={}
                )
            
            # Create evaluation context
            context = EvaluationContext(
                variables=input_values,
                profile=profile,
                calculation=calculation,
                metadata={}
            )
            
            # Evaluate based on calculation type
            if calculation.type == CalculationType.ARITHMETIC:
                result = self._evaluate_arithmetic(calculation, context)
            elif calculation.type == CalculationType.PHYSICS:
                result = self._evaluate_physics(calculation, context)
            elif calculation.type == CalculationType.LOGIC:
                result = self._evaluate_logic(calculation, context)
            elif calculation.type == CalculationType.CONDITIONAL:
                result = self._evaluate_conditional(calculation, context)
            elif calculation.type == CalculationType.LOOKUP:
                result = self._evaluate_lookup(calculation, context)
            elif calculation.type == CalculationType.CUSTOM:
                result = self._evaluate_custom(calculation, context)
            else:
                result = self._evaluate_generic(calculation, context)
            
            # Validate output
            self._validate_output(result, calculation, profile)
            
            return result
            
        except Exception as e:
            return EvaluationOutput(
                result=EvaluationResult.ERROR,
                value=None,
                error_message=str(e),
                warnings=[],
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
                metadata={}
            )
    
    def _evaluate_arithmetic(self, calculation: Calculation, context: EvaluationContext) -> EvaluationOutput:
        """Evaluate arithmetic expressions"""
        
        try:
            # Replace variable names with values in expression
            expression = calculation.expression
            for var_name in calculation.input_variables:
                value = context.variables[var_name]
                expression = expression.replace(var_name, str(value))
            
            # Evaluate the expression safely
            result_value = self._safe_eval(expression)
            
            return EvaluationOutput(
                result=EvaluationResult.SUCCESS,
                value=result_value,
                error_message=None,
                warnings=[],
                execution_time=0.0,
                metadata={'expression': expression}
            )
            
        except ZeroDivisionError:
            return EvaluationOutput(
                result=EvaluationResult.DIVISION_BY_ZERO,
                value=None,
                error_message="Division by zero",
                warnings=[],
                execution_time=0.0,
                metadata={}
            )
        except Exception as e:
            return EvaluationOutput(
                result=EvaluationResult.INVALID_EXPRESSION,
                value=None,
                error_message=str(e),
                warnings=[],
                execution_time=0.0,
                metadata={}
            )
    
    def _evaluate_physics(self, calculation: Calculation, context: EvaluationContext) -> EvaluationOutput:
        """Evaluate physics calculations"""
        
        try:
            # Common physics formulas
            if "ohms_law" in calculation.expression.lower():
                # V = I * R
                voltage = context.variables.get('voltage')
                current = context.variables.get('current')
                resistance = context.variables.get('resistance')
                
                if voltage is not None and current is not None:
                    result_value = voltage / current
                elif voltage is not None and resistance is not None:
                    result_value = voltage / resistance
                elif current is not None and resistance is not None:
                    result_value = current * resistance
                else:
                    raise EvaluationError("Insufficient variables for Ohm's Law")
                    
            elif "power" in calculation.expression.lower():
                # P = V * I
                voltage = context.variables.get('voltage')
                current = context.variables.get('current')
                
                if voltage is not None and current is not None:
                    result_value = voltage * current
                else:
                    raise EvaluationError("Missing voltage or current for power calculation")
                    
            elif "energy" in calculation.expression.lower():
                # E = P * t
                power = context.variables.get('power')
                time = context.variables.get('time')
                
                if power is not None and time is not None:
                    result_value = power * time
                else:
                    raise EvaluationError("Missing power or time for energy calculation")
                    
            else:
                # Fall back to generic evaluation
                return self._evaluate_generic(calculation, context)
            
            return EvaluationOutput(
                result=EvaluationResult.SUCCESS,
                value=result_value,
                error_message=None,
                warnings=[],
                execution_time=0.0,
                metadata={'formula': calculation.expression}
            )
            
        except Exception as e:
            return EvaluationOutput(
                result=EvaluationResult.ERROR,
                value=None,
                error_message=str(e),
                warnings=[],
                execution_time=0.0,
                metadata={}
            )
    
    def _evaluate_logic(self, calculation: Calculation, context: EvaluationContext) -> EvaluationOutput:
        """Evaluate logical expressions"""
        
        try:
            # Replace variable names with boolean values
            expression = calculation.expression
            for var_name in calculation.input_variables:
                value = context.variables[var_name]
                # Convert to boolean
                bool_value = bool(value) if value is not None else False
                expression = expression.replace(var_name, str(bool_value))
            
            # Evaluate the logical expression
            result_value = self._safe_eval(expression)
            
            return EvaluationOutput(
                result=EvaluationResult.SUCCESS,
                value=bool(result_value),
                error_message=None,
                warnings=[],
                execution_time=0.0,
                metadata={'expression': expression}
            )
            
        except Exception as e:
            return EvaluationOutput(
                result=EvaluationResult.ERROR,
                value=None,
                error_message=str(e),
                warnings=[],
                execution_time=0.0,
                metadata={}
            )
    
    def _evaluate_conditional(self, calculation: Calculation, context: EvaluationContext) -> EvaluationOutput:
        """Evaluate conditional expressions"""
        
        try:
            result_value = None
            
            # Check conditions in order
            for condition in calculation.conditions:
                if self._evaluate_condition(condition, context):
                    result_value = condition.get('result')
                    break
            
            if result_value is None:
                result_value = calculation.metadata.get('default_result')
            
            return EvaluationOutput(
                result=EvaluationResult.SUCCESS,
                value=result_value,
                error_message=None,
                warnings=[],
                execution_time=0.0,
                metadata={'conditions_evaluated': len(calculation.conditions)}
            )
            
        except Exception as e:
            return EvaluationOutput(
                result=EvaluationResult.ERROR,
                value=None,
                error_message=str(e),
                warnings=[],
                execution_time=0.0,
                metadata={}
            )
    
    def _evaluate_lookup(self, calculation: Calculation, context: EvaluationContext) -> EvaluationOutput:
        """Evaluate lookup table calculations"""
        
        try:
            lookup_table = calculation.metadata.get('lookup_table', {})
            input_key = None
            
            # Determine input key based on input variables
            for var_name in calculation.input_variables:
                if var_name in context.variables:
                    input_key = context.variables[var_name]
                    break
            
            if input_key is None:
                raise EvaluationError("No input key found for lookup")
            
            result_value = lookup_table.get(input_key)
            
            if result_value is None:
                result_value = calculation.metadata.get('default_value')
            
            return EvaluationOutput(
                result=EvaluationResult.SUCCESS,
                value=result_value,
                error_message=None,
                warnings=[],
                execution_time=0.0,
                metadata={'lookup_key': input_key}
            )
            
        except Exception as e:
            return EvaluationOutput(
                result=EvaluationResult.ERROR,
                value=None,
                error_message=str(e),
                warnings=[],
                execution_time=0.0,
                metadata={}
            )
    
    def _evaluate_custom(self, calculation: Calculation, context: EvaluationContext) -> EvaluationOutput:
        """Evaluate custom function calculations"""
        
        try:
            # Get custom function from metadata
            custom_function = calculation.metadata.get('function')
            if not custom_function:
                raise EvaluationError("No custom function defined")
            
            # Prepare arguments
            args = []
            for var_name in calculation.input_variables:
                if var_name in context.variables:
                    args.append(context.variables[var_name])
            
            # Execute custom function (in a safe environment)
            result_value = self._execute_custom_function(custom_function, args)
            
            return EvaluationOutput(
                result=EvaluationResult.SUCCESS,
                value=result_value,
                error_message=None,
                warnings=[],
                execution_time=0.0,
                metadata={'function': custom_function}
            )
            
        except Exception as e:
            return EvaluationOutput(
                result=EvaluationResult.ERROR,
                value=None,
                error_message=str(e),
                warnings=[],
                execution_time=0.0,
                metadata={}
            )
    
    def _evaluate_generic(self, calculation: Calculation, context: EvaluationContext) -> EvaluationOutput:
        """Evaluate generic expressions"""
        
        try:
            # Replace variables in expression
            expression = calculation.expression
            for var_name in calculation.input_variables:
                value = context.variables[var_name]
                expression = expression.replace(var_name, str(value))
            
            # Evaluate expression
            result_value = self._safe_eval(expression)
            
            return EvaluationOutput(
                result=EvaluationResult.SUCCESS,
                value=result_value,
                error_message=None,
                warnings=[],
                execution_time=0.0,
                metadata={'expression': expression}
            )
            
        except Exception as e:
            return EvaluationOutput(
                result=EvaluationResult.ERROR,
                value=None,
                error_message=str(e),
                warnings=[],
                execution_time=0.0,
                metadata={}
            )
    
    def _safe_eval(self, expression: str) -> Any:
        """Safely evaluate an expression"""
        
        # Parse the expression
        tree = ast.parse(expression, mode='eval')
        
        # Check for unsafe operations
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                raise EvaluationError("Function calls not allowed")
            elif isinstance(node, ast.Attribute):
                raise EvaluationError("Attribute access not allowed")
            elif isinstance(node, ast.Subscript):
                raise EvaluationError("Subscript operations not allowed")
        
        # Evaluate the expression
        def eval_node(node):
            if isinstance(node, ast.Expression):
                return eval_node(node.body)
            elif isinstance(node, ast.BinOp):
                return self.safe_operators[type(node.op)](eval_node(node.left), eval_node(node.right))
            elif isinstance(node, ast.UnaryOp):
                return self.safe_operators[type(node.op)](eval_node(node.operand))
            elif isinstance(node, ast.Compare):
                left = eval_node(node.left)
                for op, right in zip(node.ops, node.comparators):
                    left = self.safe_operators[type(op)](left, eval_node(right))
                return left
            elif isinstance(node, ast.BoolOp):
                values = [eval_node(val) for val in node.values]
                return self.safe_operators[type(node.op)](*values)
            elif isinstance(node, ast.Name):
                raise EvaluationError(f"Variable {node.id} not found in expression")
            elif isinstance(node, ast.Constant):
                return node.value
            else:
                raise EvaluationError(f"Unsupported operation: {type(node)}")
        
        return eval_node(tree)
    
    def _evaluate_condition(self, condition: Dict[str, Any], context: EvaluationContext) -> bool:
        """Evaluate a single condition"""
        
        try:
            operator = condition.get('operator', '==')
            left_var = condition.get('left_variable')
            right_value = condition.get('right_value')
            
            if left_var not in context.variables:
                return False
            
            left_value = context.variables[left_var]
            
            if operator == '==':
                return left_value == right_value
            elif operator == '!=':
                return left_value != right_value
            elif operator == '<':
                return left_value < right_value
            elif operator == '<=':
                return left_value <= right_value
            elif operator == '>':
                return left_value > right_value
            elif operator == '>=':
                return left_value >= right_value
            else:
                return False
                
        except Exception:
            return False
    
    def _execute_custom_function(self, function_name: str, args: List[Any]) -> Any:
        """Execute a custom function safely"""
        
        # Define safe custom functions
        safe_functions = {
            'sqrt': math.sqrt,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'log': math.log,
            'log10': math.log10,
            'exp': math.exp,
            'abs': abs,
            'round': round,
            'floor': math.floor,
            'ceil': math.ceil,
            'min': min,
            'max': max,
            'sum': sum,
            'len': len
        }
        
        if function_name not in safe_functions:
            raise EvaluationError(f"Custom function {function_name} not allowed")
        
        return safe_functions[function_name](*args)
    
    def _validate_output(self, output: EvaluationOutput, calculation: Calculation, profile: BehaviorProfile):
        """Validate calculation output"""
        
        if output.result != EvaluationResult.SUCCESS:
            return
        
        # Check if output variable exists
        if calculation.output_variable not in profile.variables:
            output.result = EvaluationResult.ERROR
            output.error_message = f"Output variable {calculation.output_variable} not found"
            return
        
        output_variable = profile.variables[calculation.output_variable]
        
        # Check type compatibility
        if not self._validate_type(output.value, output_variable.type):
            output.result = EvaluationResult.TYPE_MISMATCH
            output.error_message = f"Output type {type(output.value)} does not match variable type {output_variable.type}"
            return
        
        # Check value range
        if output_variable.min_value is not None and output.value < output_variable.min_value:
            output.warnings.append(f"Output value {output.value} is below minimum {output_variable.min_value}")
        
        if output_variable.max_value is not None and output.value > output_variable.max_value:
            output.warnings.append(f"Output value {output.value} is above maximum {output_variable.max_value}")
    
    def _validate_type(self, value: Any, expected_type: VariableType) -> bool:
        """Validate value type"""
        
        if expected_type == VariableType.SCALAR:
            return isinstance(value, (int, float))
        elif expected_type == VariableType.VECTOR:
            return isinstance(value, list) and all(isinstance(x, (int, float)) for x in value)
        elif expected_type == VariableType.STRING:
            return isinstance(value, str)
        elif expected_type == VariableType.BOOLEAN:
            return isinstance(value, bool)
        elif expected_type == VariableType.OBJECT:
            return isinstance(value, dict)
        elif expected_type == VariableType.ARRAY:
            return isinstance(value, list)
        else:
            return True
    
    def get_evaluation_statistics(self) -> Dict[str, Any]:
        """Get evaluation statistics"""
        
        # This would track evaluation performance and success rates
        # For now, return basic structure
        return {
            'total_evaluations': 0,
            'successful_evaluations': 0,
            'failed_evaluations': 0,
            'average_execution_time': 0.0,
            'most_common_errors': [],
            'evaluation_cache_hits': 0,
            'evaluation_cache_misses': 0
        }


# Global behavior evaluator instance
behavior_evaluator = BehaviorEvaluator() 