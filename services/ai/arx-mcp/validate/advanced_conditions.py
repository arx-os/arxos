"""
Advanced Condition Types Engine for MCP Rule Validation

This module provides advanced condition evaluation capabilities for the MCP rule engine,
including temporal conditions, dynamic conditions, statistical conditions, and complex
logical expressions.

Key Features:
- Temporal conditions with time-based evaluation
- Dynamic conditions with runtime value resolution
- Statistical conditions with aggregation functions
- Complex logical expressions with nested conditions
- Pattern matching and regex conditions
- Range and set-based conditions
- Context-aware condition evaluation
"""

import re
import math
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from functools import reduce
import json

from services.models.mcp_models import BuildingObject, RuleCondition, RuleExecutionContext

logger = logging.getLogger(__name__)


class TemporalOperator(Enum):
    """Temporal condition operators"""
    BEFORE = "before"
    AFTER = "after"
    DURING = "during"
    WITHIN = "within"
    OVERLAPS = "overlaps"
    CONTAINS = "contains"
    EQUALS = "equals"


class StatisticalFunction(Enum):
    """Statistical aggregation functions"""
    COUNT = "count"
    SUM = "sum"
    AVERAGE = "average"
    MEAN = "mean"
    MEDIAN = "median"
    MIN = "min"
    MAX = "max"
    STD_DEV = "std_dev"
    VARIANCE = "variance"
    PERCENTILE = "percentile"


class LogicalOperator(Enum):
    """Logical operators for complex expressions"""
    AND = "and"
    OR = "or"
    NOT = "not"
    XOR = "xor"
    NAND = "nand"
    NOR = "nor"


@dataclass
class TemporalRange:
    """Temporal range for time-based conditions"""
    start: datetime
    end: datetime

    def contains(self, timestamp: datetime) -> bool:
        """Check if timestamp is within range"""
        return self.start <= timestamp <= self.end

    def overlaps(self, other: 'TemporalRange') -> bool:
        """Check if ranges overlap"""
        return self.start <= other.end and other.start <= self.end

    def duration(self) -> timedelta:
        """Get duration of range"""
        return self.end - self.start


@dataclass
class StatisticalContext:
    """Context for statistical calculations"""
    values: List[float]
    weights: Optional[List[float]] = None

    def calculate(self, function: StatisticalFunction, **kwargs) -> float:
        """Calculate statistical value"""
        if not self.values:
            return 0.0

        if function == StatisticalFunction.COUNT:
            return len(self.values)
        elif function == StatisticalFunction.SUM:
            return sum(self.values)
        elif function == StatisticalFunction.AVERAGE:
            return sum(self.values) / len(self.values)
        elif function == StatisticalFunction.MEAN:
            return statistics.mean(self.values)
        elif function == StatisticalFunction.MEDIAN:
            return statistics.median(self.values)
        elif function == StatisticalFunction.MIN:
            return min(self.values)
        elif function == StatisticalFunction.MAX:
            return max(self.values)
        elif function == StatisticalFunction.STD_DEV:
            return statistics.stdev(self.values) if len(self.values) > 1 else 0.0
        elif function == StatisticalFunction.VARIANCE:
            return statistics.variance(self.values) if len(self.values) > 1 else 0.0
        elif function == StatisticalFunction.PERCENTILE:
            percentile = kwargs.get('percentile', 50)
            return statistics.quantiles(self.values, n=100)[int(percentile/100)]
        else:
            return 0.0


class AdvancedConditionEvaluator:
    """
    Advanced condition evaluator for complex rule conditions.

    Provides temporal, dynamic, statistical, and logical condition evaluation
    with support for complex expressions and pattern matching.
    """

    def __init__(self):
        """Initialize the advanced condition evaluator"""
        self.logger = logging.getLogger(__name__)
        self.temporal_context = {}
        self.dynamic_resolvers = {}
        self.statistical_cache = {}

        # Register default dynamic resolvers
        self._register_default_resolvers()

    def evaluate_temporal_condition(self, condition: RuleCondition,
                                  objects: List[BuildingObject]) -> List[BuildingObject]:
        """
        Evaluate temporal condition based on time constraints.

        Args:
            condition: Rule condition with temporal parameters
            objects: Building objects to evaluate

        Returns:
            List of objects that match temporal condition
        """
        if not condition.temporal_params:
            return []

        matched_objects = []
        operator = TemporalOperator(condition.temporal_params.get('operator', 'during'))

        # Parse temporal range
        start_time = self._parse_temporal_value(condition.temporal_params.get('start'))
        end_time = self._parse_temporal_value(condition.temporal_params.get('end'))

        if not start_time or not end_time:
            return []

        temporal_range = TemporalRange(start_time, end_time)

        for obj in objects:
            if obj.object_type != condition.element_type:
                continue

            # Get object temporal data
            object_time = self._get_object_temporal_data(obj, condition.temporal_params)
            if not object_time:
                continue

            # Evaluate temporal condition
            if self._evaluate_temporal_operator(operator, object_time, temporal_range):
                matched_objects.append(obj)

        return matched_objects

    def evaluate_dynamic_condition(self, condition: RuleCondition,
                                 objects: List[BuildingObject],
                                 context: Optional[RuleExecutionContext] = None) -> List[BuildingObject]:
        """
        Evaluate dynamic condition with runtime value resolution.

        Args:
            condition: Rule condition with dynamic parameters
            objects: Building objects to evaluate
            context: Rule execution context

        Returns:
            List of objects that match dynamic condition
        """
        if not condition.dynamic_params:
            return []

        matched_objects = []
        resolver_name = condition.dynamic_params.get('resolver')
        resolver = self.dynamic_resolvers.get(resolver_name)

        if not resolver:
            self.logger.warning(f"Unknown dynamic resolver: {resolver_name}")
            return []

        for obj in objects:
            if obj.object_type != condition.element_type:
                continue

            # Resolve dynamic value
            try:
                dynamic_value = resolver(obj, context)
                if dynamic_value is not None:
                    # Evaluate condition with resolved value
                    if self._evaluate_dynamic_value(dynamic_value, condition):
                        matched_objects.append(obj)
            except Exception as e:
                self.logger.warning(f"Error resolving dynamic value for {obj.object_id}: {e}")
                continue

        return matched_objects

    def evaluate_statistical_condition(self, condition: RuleCondition,
                                    objects: List[BuildingObject]) -> List[BuildingObject]:
        """
        Evaluate statistical condition with aggregation functions.

        Args:
            condition: Rule condition with statistical parameters
            objects: Building objects to evaluate

        Returns:
            List of objects that match statistical condition
        """
        if not condition.statistical_params:
            return []

        matched_objects = []
        function = StatisticalFunction(condition.statistical_params.get('function', 'count'))
        property_name = condition.statistical_params.get('property')
        operator = condition.statistical_params.get('operator', '>=')
        threshold = condition.statistical_params.get('threshold', 0)

        # Group objects by specified criteria
        groups = self._group_objects_for_statistics(objects, condition.statistical_params)

        for group_key, group_objects in groups.items():
            # Extract values for statistical calculation
            values = []
            for obj in group_objects:
                if property_name in obj.properties:
                    try:
                        value = float(obj.properties[property_name])
                        values.append(value)
                    except (ValueError, TypeError):
                        continue

            if not values:
                continue

            # Calculate statistical value
            stat_context = StatisticalContext(values)
            stat_value = stat_context.calculate(function)

            # Evaluate condition
            if self._evaluate_statistical_condition(stat_value, operator, threshold):
                matched_objects.extend(group_objects)

        return matched_objects

    def evaluate_pattern_condition(self, condition: RuleCondition,
                                objects: List[BuildingObject]) -> List[BuildingObject]:
        """
        Evaluate pattern matching condition with regex support.

        Args:
            condition: Rule condition with pattern parameters
            objects: Building objects to evaluate

        Returns:
            List of objects that match pattern condition
        """
        if not condition.pattern_params:
            return []

        matched_objects = []
        pattern = condition.pattern_params.get('pattern')
        property_name = condition.pattern_params.get('property')
        case_sensitive = condition.pattern_params.get('case_sensitive', True)

        if not pattern or not property_name:
            return []

        try:
            regex = re.compile(pattern, flags=0 if case_sensitive else re.IGNORECASE)
        except re.error as e:
            self.logger.warning(f"Invalid regex pattern '{pattern}': {e}")
            return []

        for obj in objects:
            if obj.object_type != condition.element_type:
                continue

            # Get property value
            property_value = obj.properties.get(property_name)
            if property_value is None:
                continue

            # Convert to string for pattern matching
            value_str = str(property_value)

            # Check if pattern matches
            if regex.search(value_str):
                matched_objects.append(obj)

        return matched_objects

    def evaluate_range_condition(self, condition: RuleCondition,
                              objects: List[BuildingObject]) -> List[BuildingObject]:
        """
        Evaluate range-based condition with set operations.

        Args:
            condition: Rule condition with range parameters
            objects: Building objects to evaluate

        Returns:
            List of objects that match range condition
        """
        if not condition.range_params:
            return []

        matched_objects = []
        property_name = condition.range_params.get('property')
        ranges = condition.range_params.get('ranges', [])
        operation = condition.range_params.get('operation', 'any')  # any, all, none

        if not property_name or not ranges:
            return []

        for obj in objects:
            if obj.object_type != condition.element_type:
                continue

            # Get property value
            property_value = obj.properties.get(property_name)
            if property_value is None:
                continue

            # Check if value falls within any range
            in_ranges = []
            for range_def in ranges:
                min_val = range_def.get('min')
                max_val = range_def.get('max')

                if min_val is not None and max_val is not None:
                    in_range = min_val <= property_value <= max_val
                elif min_val is not None:
                    in_range = property_value >= min_val
                elif max_val is not None:
                    in_range = property_value <= max_val
                else:
                    in_range = False

                in_ranges.append(in_range)

            # Apply operation
            if operation == 'any' and any(in_ranges):
                matched_objects.append(obj)
            elif operation == 'all' and all(in_ranges):
                matched_objects.append(obj)
            elif operation == 'none' and not any(in_ranges):
                matched_objects.append(obj)

        return matched_objects

    def evaluate_complex_logical_condition(self, condition: RuleCondition,
                                        objects: List[BuildingObject],
                                        context: Optional[RuleExecutionContext] = None) -> List[BuildingObject]:
        """
        Evaluate complex logical expression with nested conditions.

        Args:
            condition: Rule condition with logical expression
            objects: Building objects to evaluate
            context: Rule execution context

        Returns:
            List of objects that match logical condition
        """
        if not condition.logical_params:
            return []

        expression = condition.logical_params.get('expression')
        if not expression:
            return []

        # Parse and evaluate logical expression
        try:
            result_objects = self._evaluate_logical_expression(expression, objects, context)
            return result_objects
        except Exception as e:
            self.logger.error(f"Error evaluating logical expression: {e}")
            return []

    def _evaluate_temporal_operator(self, operator: TemporalOperator,
                                  object_time: Union[datetime, TemporalRange],
                                  condition_range: TemporalRange) -> bool:
        """Evaluate temporal operator"""
        if operator == TemporalOperator.BEFORE:
            if isinstance(object_time, datetime):
                return object_time < condition_range.start
            else:
                return object_time.end < condition_range.start

        elif operator == TemporalOperator.AFTER:
            if isinstance(object_time, datetime):
                return object_time > condition_range.end
            else:
                return object_time.start > condition_range.end

        elif operator == TemporalOperator.DURING:
            if isinstance(object_time, datetime):
                return condition_range.contains(object_time)
            else:
                return condition_range.contains(object_time.start) and condition_range.contains(object_time.end)

        elif operator == TemporalOperator.WITHIN:
            if isinstance(object_time, datetime):
                return condition_range.contains(object_time)
            else:
                return object_time.start >= condition_range.start and object_time.end <= condition_range.end

        elif operator == TemporalOperator.OVERLAPS:
            if isinstance(object_time, datetime):
                return condition_range.contains(object_time)
            else:
                return object_time.overlaps(condition_range)

        elif operator == TemporalOperator.CONTAINS:
            if isinstance(object_time, datetime):
                return False  # Single timestamp cannot contain a range
            else:
                return object_time.contains(condition_range.start) and object_time.contains(condition_range.end)

        elif operator == TemporalOperator.EQUALS:
            if isinstance(object_time, datetime):
                return object_time == condition_range.start
            else:
                return object_time.start == condition_range.start and object_time.end == condition_range.end

        return False

    def _evaluate_dynamic_value(self, dynamic_value: Any, condition: RuleCondition) -> bool:
        """Evaluate condition with dynamic value"""
        operator = condition.dynamic_params.get('operator', '==')
        expected_value = condition.dynamic_params.get('value')

        # Simple comparison for now - can be extended
        if operator == '==':
            return dynamic_value == expected_value
        elif operator == '!=':
            return dynamic_value != expected_value
        elif operator == '>':
            return dynamic_value > expected_value
        elif operator == '>=':
            return dynamic_value >= expected_value
        elif operator == '<':
            return dynamic_value < expected_value
        elif operator == '<=':
            return dynamic_value <= expected_value
        elif operator == 'in':
            return dynamic_value in expected_value
        elif operator == 'not_in':
            return dynamic_value not in expected_value

        return False

    def _evaluate_statistical_condition(self, stat_value: float, operator: str, threshold: float) -> bool:
        """Evaluate statistical condition"""
        if operator == '==':
            return abs(stat_value - threshold) < 0.001
        elif operator == '!=':
            return abs(stat_value - threshold) >= 0.001
        elif operator == '>':
            return stat_value > threshold
        elif operator == '>=':
            return stat_value >= threshold
        elif operator == '<':
            return stat_value < threshold
        elif operator == '<=':
            return stat_value <= threshold

        return False

    def _evaluate_logical_expression(self, expression: Dict[str, Any],
                                   objects: List[BuildingObject],
                                   context: Optional[RuleExecutionContext] = None) -> List[BuildingObject]:
        """Evaluate complex logical expression"""
        operator = expression.get('operator')
        operands = expression.get('operands', [])

        if operator == LogicalOperator.AND.value:
            # Intersection of all operand results
            result_sets = []
            for operand in operands:
                operand_objects = self._evaluate_logical_operand(operand, objects, context)
                result_sets.append(set(obj.object_id for obj in operand_objects))

            if result_sets:
                intersection = result_sets[0]
                for result_set in result_sets[1:]:
                    intersection = intersection.intersection(result_set)

                return [obj for obj in objects if obj.object_id in intersection]
            return []

        elif operator == LogicalOperator.OR.value:
            # Union of all operand results
            result_objects = []
            for operand in operands:
                operand_objects = self._evaluate_logical_operand(operand, objects, context)
                result_objects.extend(operand_objects)

            # Remove duplicates
            seen_ids = set()
            unique_objects = []
            for obj in result_objects:
                if obj.object_id not in seen_ids:
                    seen_ids.add(obj.object_id)
                    unique_objects.append(obj)

            return unique_objects

        elif operator == LogicalOperator.NOT.value:
            # Negation of operand result
            if len(operands) != 1:
                return []

            operand_objects = self._evaluate_logical_operand(operands[0], objects, context)
            operand_ids = set(obj.object_id for obj in operand_objects)

            return [obj for obj in objects if obj.object_id not in operand_ids]

        elif operator == LogicalOperator.XOR.value:
            # Exclusive OR - objects that match exactly one operand
            if len(operands) != 2:
                return []

            operand1_objects = self._evaluate_logical_operand(operands[0], objects, context)
            operand2_objects = self._evaluate_logical_operand(operands[1], objects, context)

            operand1_ids = set(obj.object_id for obj in operand1_objects)
            operand2_ids = set(obj.object_id for obj in operand2_objects)

            # Objects in operand1 but not operand2, or operand2 but not operand1
            xor_ids = operand1_ids.symmetric_difference(operand2_ids)

            return [obj for obj in objects if obj.object_id in xor_ids]

        return []

    def _evaluate_logical_operand(self, operand: Union[Dict[str, Any], str],
                                 objects: List[BuildingObject],
                                 context: Optional[RuleExecutionContext] = None) -> List[BuildingObject]:
        """Evaluate a single logical operand"""
        if isinstance(operand, dict):
            # Recursive evaluation
            return self._evaluate_logical_expression(operand, objects, context)
        elif isinstance(operand, str):
            # Simple condition evaluation
            # This would need to be implemented based on your condition evaluation logic
            return []
        else:
            return []

    def _parse_temporal_value(self, value: Any) -> Optional[datetime]:
        """Parse temporal value from various formats"""
        if value is None:
            return None

        if isinstance(value, datetime):
            return value
        elif isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return None
        elif isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(value)
            except (ValueError, OSError):
                return None

        return None

    def _get_object_temporal_data(self, obj: BuildingObject, temporal_params: Dict[str, Any]) -> Optional[Union[datetime, TemporalRange]]:
        """Get temporal data for object"""
        property_name = temporal_params.get('property', 'timestamp')

        if property_name in obj.properties:
            value = obj.properties[property_name]
            if isinstance(value, dict) and 'start' in value and 'end' in value:
                start = self._parse_temporal_value(value['start'])
                end = self._parse_temporal_value(value['end'])
                if start and end:
                    return TemporalRange(start, end)
            else:
                return self._parse_temporal_value(value)

        return None

    def _group_objects_for_statistics(self, objects: List[BuildingObject],
                                    statistical_params: Dict[str, Any]) -> Dict[str, List[BuildingObject]]:
        """Group objects for statistical calculations"""
        group_by = statistical_params.get('group_by')

        if not group_by:
            # No grouping - all objects in one group
            return {'all': objects}

        groups = {}
        for obj in objects:
            if group_by in obj.properties:
                group_key = str(obj.properties[group_by])
                if group_key not in groups:
                    groups[group_key] = []
                groups[group_key].append(obj)
            else:
                # Objects without grouping property go to default group
                if 'default' not in groups:
                    groups['default'] = []
                groups['default'].append(obj)

        return groups

    def _register_default_resolvers(self):
        """Register default dynamic value resolvers"""
        self.dynamic_resolvers = {
            'area_calculator': self._resolve_area,
            'volume_calculator': self._resolve_volume,
            'load_calculator': self._resolve_load,
            'efficiency_calculator': self._resolve_efficiency,
            'cost_calculator': self._resolve_cost,
            'safety_factor': self._resolve_safety_factor,
            'compliance_score': self._resolve_compliance_score
        }

    def _resolve_area(self, obj: BuildingObject, context: Optional[RuleExecutionContext] = None) -> Optional[float]:
        """Resolve dynamic area value"""
        if 'area' in obj.properties:
            return float(obj.properties['area'])
        elif obj.location and 'width' in obj.location and 'height' in obj.location:
            return obj.location['width'] * obj.location['height']
        return None

    def _resolve_volume(self, obj: BuildingObject, context: Optional[RuleExecutionContext] = None) -> Optional[float]:
        """Resolve dynamic volume value"""
        if 'volume' in obj.properties:
            return float(obj.properties['volume'])
        elif obj.location and all(dim in obj.location for dim in ['width', 'height', 'depth']):
            return obj.location['width'] * obj.location['height'] * obj.location['depth']
        return None

    def _resolve_load(self, obj: BuildingObject, context: Optional[RuleExecutionContext] = None) -> Optional[float]:
        """Resolve dynamic load value"""
        if 'load' in obj.properties:
            return float(obj.properties['load'])
        elif 'area' in obj.properties and 'load_per_area' in obj.properties:
            return float(obj.properties['area']) * float(obj.properties['load_per_area'])
        return None

    def _resolve_efficiency(self, obj: BuildingObject, context: Optional[RuleExecutionContext] = None) -> Optional[float]:
        """Resolve dynamic efficiency value"""
        if 'efficiency' in obj.properties:
            return float(obj.properties['efficiency'])
        elif 'energy_consumption' in obj.properties and 'energy_output' in obj.properties:
            consumption = float(obj.properties['energy_consumption'])
            output = float(obj.properties['energy_output'])
            if consumption > 0:
                return output / consumption
        return None

    def _resolve_cost(self, obj: BuildingObject, context: Optional[RuleExecutionContext] = None) -> Optional[float]:
        """Resolve dynamic cost value"""
        if 'cost' in obj.properties:
            return float(obj.properties['cost'])
        elif 'area' in obj.properties and 'cost_per_area' in obj.properties:
            return float(obj.properties['area']) * float(obj.properties['cost_per_area'])
        return None

    def _resolve_safety_factor(self, obj: BuildingObject, context: Optional[RuleExecutionContext] = None) -> Optional[float]:
        """Resolve dynamic safety factor"""
        if 'safety_factor' in obj.properties:
            return float(obj.properties['safety_factor'])
        elif 'design_load' in obj.properties and 'actual_load' in obj.properties:
            design_load = float(obj.properties['design_load'])
            actual_load = float(obj.properties['actual_load'])
            if actual_load > 0:
                return design_load / actual_load
        return None

    def _resolve_compliance_score(self, obj: BuildingObject, context: Optional[RuleExecutionContext] = None) -> Optional[float]:
        """Resolve dynamic compliance score"""
        if 'compliance_score' in obj.properties:
            return float(obj.properties['compliance_score'])
        elif context and context.calculations:
            # Calculate compliance score based on context calculations
            total_violations = len([v for v in context.calculations.get('violations', []) if v.get('object_id') == obj.object_id])
            if total_violations == 0:
                return 100.0
            else:
                return max(0.0, 100.0 - (total_violations * 10.0))
        return None


class AdvancedConditionError(Exception):
    """Exception raised when advanced condition evaluation fails"""
    pass
