"""
SVGX Engine - Parametric Modeling System

This module implements the parametric modeling system for CAD-parity functionality,
providing parameter-driven design with parameter relationships and expressions.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import math
import logging
import re
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from abc import ABC, abstractmethod

from .precision_drawing_system import PrecisionPoint, PrecisionVector, PrecisionLevel

logger = logging.getLogger(__name__)


class ParameterType(Enum):
    """Types of parameters."""

    LENGTH = "length"
    ANGLE = "angle"
    RADIUS = "radius"
    DIAMETER = "diameter"
    AREA = "area"
    VOLUME = "volume"
    COUNT = "count"
    BOOLEAN = "boolean"
    STRING = "string"
    EXPRESSION = "expression"


class ParameterStatus(Enum):
    """Parameter status."""

    VALID = "valid"
    INVALID = "invalid"
    CIRCULAR = "circular"
    UNDEFINED = "undefined"


@dataclass
class Parameter:
    """A parameter with name, value, and metadata."""

    name: str
    value: Union[Decimal, str, bool]
    parameter_type: ParameterType
    unit: str = ""
    description: str = ""
    status: ParameterStatus = ParameterStatus.VALID
    dependencies: Set[str] = field(default_factory=set)
    expressions: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate parameter after initialization."""
        self._validate_parameter()

    def _validate_parameter(self) -> None:
        """Validate parameter values."""
        if not self.name:
            raise ValueError("Parameter name cannot be empty")

        if self.parameter_type == ParameterType.BOOLEAN and not isinstance(
            self.value, bool
        ):
            raise ValueError("Boolean parameter must have boolean value")

        if self.parameter_type == ParameterType.STRING and not isinstance(
            self.value, str
        ):
            raise ValueError("String parameter must have string value")

    def get_numeric_value(self) -> Optional[Decimal]:
        """Get numeric value if parameter is numeric."""
        if isinstance(self.value, (int, float, Decimal)):
            return Decimal(str(self.value))
        return None

    def set_value(self, value: Union[Decimal, str, bool]) -> None:
        """Set parameter value."""
        if self.parameter_type == ParameterType.BOOLEAN and not isinstance(value, bool):
            raise ValueError("Boolean parameter must have boolean value")

        if self.parameter_type == ParameterType.STRING and not isinstance(value, str):
            raise ValueError("String parameter must have string value")

        self.value = value
        self.status = ParameterStatus.VALID

    def to_dict(self) -> Dict[str, Any]:
        """Convert parameter to dictionary representation."""
        result = {
            "name": self.name,
            "parameter_type": self.parameter_type.value,
            "unit": self.unit,
            "description": self.description,
            "status": self.status.value,
            "dependencies": list(self.dependencies),
            "expressions": self.expressions,
        }

        if isinstance(self.value, Decimal):
            result["value"] = float(self.value)
        else:
            result["value"] = self.value

        return result


class ExpressionEvaluator:
    """Evaluates mathematical expressions with parameter substitution."""

    def __init__(self):
        """Initialize expression evaluator."""
        self.operators = {
            "+": lambda x, y: x + y,
            "-": lambda x, y: x - y,
            "*": lambda x, y: x * y,
            "/": lambda x, y: x / y if y != 0 else float("inf"),
            "^": lambda x, y: x**y,
            "sin": lambda x: Decimal(str(math.sin(float(x)))),
            "cos": lambda x: Decimal(str(math.cos(float(x)))),
            "tan": lambda x: Decimal(str(math.tan(float(x)))),
            "sqrt": lambda x: x.sqrt(),
            "abs": lambda x: abs(x),
            "round": lambda x: round(x),
            "floor": lambda x: math.floor(float(x)),
            "ceil": lambda x: math.ceil(float(x)),
        }

    def evaluate_expression(
        self, expression: str, parameters: Dict[str, Parameter]
    ) -> Optional[Decimal]:
        """Evaluate a mathematical expression with parameter substitution."""
        try:
            # Replace parameter names with their values
            processed_expression = self._substitute_parameters(expression, parameters)

            # Evaluate the expression
            result = self._evaluate_math_expression(processed_expression)
            return result
        except Exception as e:
            logger.error(f"Error evaluating expression '{expression}': {e}")
            return None

    def _substitute_parameters(
        self, expression: str, parameters: Dict[str, Parameter]
    ) -> str:
        """Substitute parameter names with their values in the expression."""
        processed_expression = expression

        for param_name, parameter in parameters.items():
            if parameter.status == ParameterStatus.VALID:
                numeric_value = parameter.get_numeric_value()
                if numeric_value is not None:
                    # Replace parameter name with its value
                    pattern = r"\b" + re.escape(param_name) + r"\b"
                    processed_expression = re.sub(
                        pattern, str(numeric_value), processed_expression
                    )

        return processed_expression

    def _evaluate_math_expression(self, expression: str) -> Decimal:
        """Evaluate a mathematical expression."""
        # This is a simplified implementation
        # In a full CAD system, this would use a proper mathematical expression parser

        # Remove whitespace
        expression = expression.replace(" ", "")

        # Handle basic arithmetic operations
        if "+" in expression:
            parts = expression.split("+", 1)
            return self._evaluate_math_expression(
                parts[0]
            ) + self._evaluate_math_expression(parts[1])
        elif "-" in expression:
            parts = expression.split("-", 1)
            return self._evaluate_math_expression(
                parts[0]
            ) - self._evaluate_math_expression(parts[1])
        elif "*" in expression:
            parts = expression.split("*", 1)
            return self._evaluate_math_expression(
                parts[0]
            ) * self._evaluate_math_expression(parts[1])
        elif "/" in expression:
            parts = expression.split("/", 1)
            divisor = self._evaluate_math_expression(parts[1])
            if divisor == 0:
                raise ValueError("Division by zero")
            return self._evaluate_math_expression(parts[0]) / divisor
        elif "^" in expression:
            parts = expression.split("^", 1)
            return self._evaluate_math_expression(
                parts[0]
            ) ** self._evaluate_math_expression(parts[1])
        else:
            # Try to convert to Decimal
            try:
                return Decimal(expression)
            except ValueError:
                raise ValueError(f"Invalid expression: {expression}")


class ParameterRelationship:
    """A relationship between parameters."""

    def __init__(
        self,
        name: str,
        expression: str,
        target_parameter: str,
        source_parameters: List[str],
    ):
        """Initialize parameter relationship."""
        self.name = name
        self.expression = expression
        self.target_parameter = target_parameter
        self.source_parameters = source_parameters
        self.evaluator = ExpressionEvaluator()
        self.status = ParameterStatus.VALID

    def evaluate(self, parameters: Dict[str, Parameter]) -> Optional[Decimal]:
        """Evaluate the relationship and return the result."""
        try:
            # Check if all source parameters are available
            for source_param in self.source_parameters:
                if source_param not in parameters:
                    self.status = ParameterStatus.UNDEFINED
                    return None

                if parameters[source_param].status != ParameterStatus.VALID:
                    self.status = ParameterStatus.INVALID
                    return None

            # Evaluate the expression
            result = self.evaluator.evaluate_expression(self.expression, parameters)

            if result is not None:
                self.status = ParameterStatus.VALID
            else:
                self.status = ParameterStatus.INVALID

            return result
        except Exception as e:
            logger.error(f"Error evaluating relationship '{self.name}': {e}")
            self.status = ParameterStatus.INVALID
            return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert relationship to dictionary representation."""
        return {
            "name": self.name,
            "expression": self.expression,
            "target_parameter": self.target_parameter,
            "source_parameters": self.source_parameters,
            "status": self.status.value,
        }


class ParametricModel:
    """A parametric model with parameters and relationships."""

    def __init__(self, name: str):
        """Initialize parametric model."""
        self.name = name
        self.parameters: Dict[str, Parameter] = {}
        self.relationships: Dict[str, ParameterRelationship] = {}
        self.evaluator = ExpressionEvaluator()
        logger.info(f"Parametric model '{name}' initialized")

    def add_parameter(self, parameter: Parameter) -> None:
        """Add a parameter to the model."""
        self.parameters[parameter.name] = parameter
        logger.debug(f"Added parameter '{parameter.name}' to model '{self.name}'")

    def remove_parameter(self, parameter_name: str) -> bool:
        """Remove a parameter from the model."""
        if parameter_name in self.parameters:
            del self.parameters[parameter_name]
            logger.debug(
                f"Removed parameter '{parameter_name}' from model '{self.name}'"
            )
            return True
        return False

    def get_parameter(self, parameter_name: str) -> Optional[Parameter]:
        """Get a parameter by name."""
        return self.parameters.get(parameter_name)

    def set_parameter_value(
        self, parameter_name: str, value: Union[Decimal, str, bool]
    ) -> bool:
        """Set the value of a parameter."""
        parameter = self.parameters.get(parameter_name)
        if parameter:
            parameter.set_value(value)
            self._update_dependent_parameters(parameter_name)
            logger.debug(f"Set parameter '{parameter_name}' value to {value}")
            return True
        return False

    def add_relationship(self, relationship: ParameterRelationship) -> None:
        """Add a relationship to the model."""
        self.relationships[relationship.name] = relationship
        logger.debug(f"Added relationship '{relationship.name}' to model '{self.name}'")

    def remove_relationship(self, relationship_name: str) -> bool:
        """Remove a relationship from the model."""
        if relationship_name in self.relationships:
            del self.relationships[relationship_name]
            logger.debug(
                f"Removed relationship '{relationship_name}' from model '{self.name}'"
            )
            return True
        return False

    def _update_dependent_parameters(self, changed_parameter: str) -> None:
        """Update parameters that depend on the changed parameter."""
        for relationship in self.relationships.values():
            if changed_parameter in relationship.source_parameters:
                # Evaluate the relationship
                result = relationship.evaluate(self.parameters)

                if result is not None:
                    # Update the target parameter
                    target_param = self.parameters.get(relationship.target_parameter)
                    if target_param and target_param.parameter_type in [
                        ParameterType.LENGTH,
                        ParameterType.ANGLE,
                        ParameterType.RADIUS,
                        ParameterType.DIAMETER,
                        ParameterType.AREA,
                        ParameterType.VOLUME,
                        ParameterType.COUNT,
                    ]:
                        target_param.set_value(result)
                        logger.debug(
                            f"Updated dependent parameter '{target_param.name}' to {result}"
                        )

    def evaluate_all_relationships(self) -> Dict[str, Decimal]:
        """Evaluate all relationships and return results."""
        results = {}

        for relationship in self.relationships.values():
            result = relationship.evaluate(self.parameters)
            if result is not None:
                results[relationship.target_parameter] = result

        return results

    def get_model_statistics(self) -> Dict[str, Any]:
        """Get model statistics."""
        parameter_types = {}
        for parameter in self.parameters.values():
            param_type = parameter.parameter_type.value
            parameter_types[param_type] = parameter_types.get(param_type, 0) + 1

        valid_parameters = sum(
            1 for p in self.parameters.values() if p.status == ParameterStatus.VALID
        )
        valid_relationships = sum(
            1 for r in self.relationships.values() if r.status == ParameterStatus.VALID
        )

        return {
            "name": self.name,
            "total_parameters": len(self.parameters),
            "valid_parameters": valid_parameters,
            "parameter_types": parameter_types,
            "total_relationships": len(self.relationships),
            "valid_relationships": valid_relationships,
        }

    def export_data(self) -> Dict[str, Any]:
        """Export model data."""
        return {
            "name": self.name,
            "parameters": {
                param_name: parameter.to_dict()
                for param_name, parameter in self.parameters.items()
            },
            "relationships": {
                rel_name: relationship.to_dict()
                for rel_name, relationship in self.relationships.items()
            },
        }


class ParametricModelingSystem:
    """Main parametric modeling system for CAD operations."""

    def __init__(self):
        """Initialize parametric modeling system."""
        self.models: Dict[str, ParametricModel] = {}
        self.evaluator = ExpressionEvaluator()
        logger.info("Parametric modeling system initialized")

    def create_model(self, name: str) -> str:
        """Create a new parametric model."""
        if name in self.models:
            raise ValueError(f"Model '{name}' already exists")

        model = ParametricModel(name)
        self.models[name] = model
        logger.info(f"Created parametric model: {name}")
        return name

    def get_model(self, name: str) -> Optional[ParametricModel]:
        """Get a model by name."""
        return self.models.get(name)

    def remove_model(self, name: str) -> bool:
        """Remove a model."""
        if name in self.models:
            del self.models[name]
            logger.info(f"Removed parametric model: {name}")
            return True
        return False

    def add_parameter_to_model(self, model_name: str, parameter: Parameter) -> bool:
        """Add a parameter to a model."""
        model = self.models.get(model_name)
        if model:
            model.add_parameter(parameter)
            return True
        return False

    def add_relationship_to_model(
        self, model_name: str, relationship: ParameterRelationship
    ) -> bool:
        """Add a relationship to a model."""
        model = self.models.get(model_name)
        if model:
            model.add_relationship(relationship)
            return True
        return False

    def evaluate_model(self, model_name: str) -> Optional[Dict[str, Decimal]]:
        """Evaluate all relationships in a model."""
        model = self.models.get(model_name)
        if model:
            return model.evaluate_all_relationships()
        return None

    def get_system_statistics(self) -> Dict[str, Any]:
        """Get system statistics."""
        total_parameters = sum(len(model.parameters) for model in self.models.values())
        total_relationships = sum(
            len(model.relationships) for model in self.models.values()
        )

        return {
            "total_models": len(self.models),
            "total_parameters": total_parameters,
            "total_relationships": total_relationships,
            "models": {
                model_name: model.get_model_statistics()
                for model_name, model in self.models.items()
            },
        }

    def export_data(self) -> Dict[str, Any]:
        """Export system data."""
        return {
            "models": {
                model_name: model.export_data()
                for model_name, model in self.models.items()
            }
        }


# Factory functions for easy instantiation
def create_parameter(
    name: str,
    value: Union[float, str, bool],
    parameter_type: ParameterType,
    unit: str = "",
    description: str = "",
) -> Parameter:
    """Create a parameter."""
    if isinstance(value, (int, float)):
        value = Decimal(str(value))

    return Parameter(
        name=name,
        value=value,
        parameter_type=parameter_type,
        unit=unit,
        description=description,
    )


def create_parameter_relationship(
    name: str, expression: str, target_parameter: str, source_parameters: List[str]
) -> ParameterRelationship:
    """Create a parameter relationship."""
    return ParameterRelationship(
        name=name,
        expression=expression,
        target_parameter=target_parameter,
        source_parameters=source_parameters,
    )


def create_parametric_model(name: str) -> ParametricModel:
    """Create a new parametric model."""
    return ParametricModel(name)


def create_parametric_modeling_system() -> ParametricModelingSystem:
    """Create a new parametric modeling system."""
    return ParametricModelingSystem()
