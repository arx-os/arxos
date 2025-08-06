"""
SVGX Engine - Conditional Logic Engine

Handles complex conditional logic evaluation for behavior systems.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class LogicType(Enum):
    """Types of logic operations."""

    AND = "and"
    OR = "or"
    NOT = "not"
    XOR = "xor"
    NAND = "nand"
    NOR = "nor"


class ComparisonOperator(Enum):
    """Types of comparison operators."""

    EQUAL = "=="
    NOT_EQUAL = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"


class ConditionType(Enum):
    """Types of conditions."""

    THRESHOLD = "threshold"
    TIME = "time"
    SPATIAL = "spatial"
    RELATIONAL = "relational"
    COMPLEX = "complex"
    SIMPLE = "simple"


@dataclass
class Condition:
    """Represents a condition for evaluation."""

    condition_id: str
    condition_type: ConditionType
    expression: str
    parameters: Dict[str, Any]
    operators: List[str] = field(default_factory=list)
    enabled: bool = True
    priority: int = 1


class ConditionalLogicEngine:
    """Engine for evaluating complex conditional logic."""

    def __init__(self):
        self.conditions: Dict[str, Condition] = {}
        self.evaluators: Dict[ConditionType, Callable] = {}
        self._setup_default_evaluators()

    def _setup_default_evaluators(self):
        """Setup default condition evaluators."""
        self.evaluators[ConditionType.THRESHOLD] = self._evaluate_threshold
        self.evaluators[ConditionType.TIME] = self._evaluate_time
        self.evaluators[ConditionType.SPATIAL] = self._evaluate_spatial
        self.evaluators[ConditionType.RELATIONAL] = self._evaluate_relational
        self.evaluators[ConditionType.COMPLEX] = self._evaluate_complex
        self.evaluators[ConditionType.SIMPLE] = self._evaluate_simple

    def register_condition(self, condition: Condition):
        """Register a condition for evaluation."""
        self.conditions[condition.condition_id] = condition
        logger.info(
            f"Registered condition {condition.condition_id} of type {condition.condition_type.value}"
        )

    def evaluate_condition(self, condition_id: str, context: Dict[str, Any]) -> bool:
        """Evaluate a specific condition."""
        if condition_id not in self.conditions:
            logger.warning(f"Condition {condition_id} not found")
            return False

        condition = self.conditions[condition_id]
        if not condition.enabled:
            return False

        evaluator = self.evaluators.get(condition.condition_type)
        if not evaluator:
            logger.warning(
                f"No evaluator for condition type {condition.condition_type}"
            )
            return False

        try:
            result = evaluator(condition, context)
            logger.debug(f"Condition {condition_id} evaluated to {result}")
            return result
        except Exception as e:
            logger.error(f"Error evaluating condition {condition_id}: {e}")
            return False

    def evaluate_all_conditions(self, context: Dict[str, Any]) -> Dict[str, bool]:
        """Evaluate all registered conditions."""
        results = {}
        for condition_id in self.conditions:
            results[condition_id] = self.evaluate_condition(condition_id, context)
        return results

    def _evaluate_threshold(
        self, condition: Condition, context: Dict[str, Any]
    ) -> bool:
        """Evaluate threshold condition."""
        try:
            value = context.get(condition.parameters.get("field", ""), 0)
            threshold = condition.parameters.get("threshold", 0)
            operator = condition.parameters.get("operator", ">=")

            if operator == ">=":
                return value >= threshold
            elif operator == "<=":
                return value <= threshold
            elif operator == ">":
                return value > threshold
            elif operator == "<":
                return value < threshold
            elif operator == "==":
                return value == threshold
            elif operator == "!=":
                return value != threshold
            else:
                logger.warning(f"Unknown operator: {operator}")
                return False
        except Exception as e:
            logger.error(f"Error evaluating threshold condition: {e}")
            return False

    def _evaluate_time(self, condition: Condition, context: Dict[str, Any]) -> bool:
        """Evaluate time-based condition."""
        try:
            current_time = context.get("current_time", datetime.now())
            start_time = condition.parameters.get("start_time")
            end_time = condition.parameters.get("end_time")

            if start_time and end_time:
                return start_time <= current_time <= end_time
            elif start_time:
                return current_time >= start_time
            elif end_time:
                return current_time <= end_time
            else:
                return True
        except Exception as e:
            logger.error(f"Error evaluating time condition: {e}")
            return False

    def _evaluate_spatial(self, condition: Condition, context: Dict[str, Any]) -> bool:
        """Evaluate spatial condition."""
        try:
            position = context.get("position", {"x": 0, "y": 0, "z": 0})
            bounds = condition.parameters.get("bounds", {})

            x, y, z = position.get("x", 0), position.get("y", 0), position.get("z", 0)
            min_x, max_x = bounds.get("min_x", float("-inf")), bounds.get(
                "max_x", float("inf")
            )
            min_y, max_y = bounds.get("min_y", float("-inf")), bounds.get(
                "max_y", float("inf")
            )
            min_z, max_z = bounds.get("min_z", float("-inf")), bounds.get(
                "max_z", float("inf")
            )

            return min_x <= x <= max_x and min_y <= y <= max_y and min_z <= z <= max_z
        except Exception as e:
            logger.error(f"Error evaluating spatial condition: {e}")
            return False

    def _evaluate_relational(
        self, condition: Condition, context: Dict[str, Any]
    ) -> bool:
        """Evaluate relational condition."""
        try:
            field1 = condition.parameters.get("field1", "")
            field2 = condition.parameters.get("field2", "")
            operator = condition.parameters.get("operator", "==")

            value1 = context.get(field1, 0)
            value2 = context.get(field2, 0)

            if operator == "==":
                return value1 == value2
            elif operator == "!=":
                return value1 != value2
            elif operator == ">":
                return value1 > value2
            elif operator == "<":
                return value1 < value2
            elif operator == ">=":
                return value1 >= value2
            elif operator == "<=":
                return value1 <= value2
            else:
                logger.warning(f"Unknown relational operator: {operator}")
                return False
        except Exception as e:
            logger.error(f"Error evaluating relational condition: {e}")
            return False

    def _evaluate_complex(self, condition: Condition, context: Dict[str, Any]) -> bool:
        """Evaluate complex condition with multiple sub-conditions."""
        try:
            sub_conditions = condition.parameters.get("sub_conditions", [])
            logic_type = condition.parameters.get("logic_type", LogicType.AND)

            results = []
            for sub_condition in sub_conditions:
                result = self.evaluate_condition(sub_condition, context)
                results.append(result)

            if logic_type == LogicType.AND:
                return all(results)
            elif logic_type == LogicType.OR:
                return any(results)
            elif logic_type == LogicType.NOT:
                return not results[0] if results else True
            else:
                return all(results)  # Default to AND
        except Exception as e:
            logger.error(f"Error evaluating complex condition: {e}")
            return False

    def _evaluate_simple(self, condition: Condition, context: Dict[str, Any]) -> bool:
        """Evaluate simple condition."""
        try:
            field = condition.parameters.get("field", "")
            value = context.get(field, None)
            expected = condition.parameters.get("expected", None)

            return value == expected
        except Exception as e:
            logger.error(f"Error evaluating simple condition: {e}")
            return False

    def get_condition(self, condition_id: str) -> Optional[Condition]:
        """Get a specific condition."""
        return self.conditions.get(condition_id)

    def get_all_conditions(self) -> List[Condition]:
        """Get all registered conditions."""
        return list(self.conditions.values())

    def remove_condition(self, condition_id: str) -> bool:
        """Remove a condition."""
        if condition_id in self.conditions:
            del self.conditions[condition_id]
            logger.info(f"Removed condition {condition_id}")
            return True
        return False

    def clear_conditions(self):
        """Clear all conditions."""
        self.conditions.clear()
        logger.info("Cleared all conditions")


# Global instance
conditional_logic_engine = ConditionalLogicEngine()
