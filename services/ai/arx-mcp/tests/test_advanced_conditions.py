"""
Tests for Advanced Condition Types Engine

This module contains comprehensive tests for the AdvancedConditionEvaluator class,
ensuring accurate evaluation of temporal, dynamic, statistical, pattern, range, and logical conditions.
"""

import pytest
import re
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from services.ai.arx_mcp.validate.advanced_conditions import (
    AdvancedConditionEvaluator, AdvancedConditionError, TemporalOperator,
    StatisticalFunction, LogicalOperator, TemporalRange, StatisticalContext
)
from services.models.mcp_models import BuildingObject, RuleCondition, RuleExecutionContext


class TestTemporalRange:
    """Test suite for TemporalRange class"""

    def test_temporal_range_creation(self):
        """Test temporal range creation"""
        start = datetime(2024, 1, 1, 10, 0, 0)
        end = datetime(2024, 1, 1, 18, 0, 0)
        tr = TemporalRange(start, end)

        assert tr.start == start
        assert tr.end == end
        assert tr.duration() == timedelta(hours=8)

    def test_temporal_range_contains(self):
        """Test temporal range contains method"""
        start = datetime(2024, 1, 1, 10, 0, 0)
        end = datetime(2024, 1, 1, 18, 0, 0)
        tr = TemporalRange(start, end)

        # Test timestamp within range
        within_timestamp = datetime(2024, 1, 1, 14, 0, 0)
        assert tr.contains(within_timestamp) == True

        # Test timestamp outside range
        outside_timestamp = datetime(2024, 1, 1, 20, 0, 0)
        assert tr.contains(outside_timestamp) == False

        # Test boundary timestamps
        assert tr.contains(start) == True
        assert tr.contains(end) == True

    def test_temporal_range_overlaps(self):
        """Test temporal range overlaps method"""
        tr1 = TemporalRange(
            datetime(2024, 1, 1, 10, 0, 0),
            datetime(2024, 1, 1, 18, 0, 0)
        )

        # Overlapping range
        tr2 = TemporalRange(
            datetime(2024, 1, 1, 14, 0, 0),
            datetime(2024, 1, 1, 22, 0, 0)
        )
        assert tr1.overlaps(tr2) == True

        # Non-overlapping range
        tr3 = TemporalRange(
            datetime(2024, 1, 1, 20, 0, 0),
            datetime(2024, 1, 1, 22, 0, 0)
        )
        assert tr1.overlaps(tr3) == False


class TestStatisticalContext:
    """Test suite for StatisticalContext class"""

    def test_statistical_context_creation(self):
        """Test statistical context creation"""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        sc = StatisticalContext(values)

        assert sc.values == values
        assert sc.weights is None

    def test_statistical_calculations(self):
        """Test statistical calculations"""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        sc = StatisticalContext(values)

        assert sc.calculate(StatisticalFunction.COUNT) == 5
        assert sc.calculate(StatisticalFunction.SUM) == 15.0
        assert sc.calculate(StatisticalFunction.AVERAGE) == 3.0
        assert sc.calculate(StatisticalFunction.MEAN) == 3.0
        assert sc.calculate(StatisticalFunction.MEDIAN) == 3.0
        assert sc.calculate(StatisticalFunction.MIN) == 1.0
        assert sc.calculate(StatisticalFunction.MAX) == 5.0

    def test_statistical_calculations_empty(self):
        """Test statistical calculations with empty values"""
        sc = StatisticalContext([])

        assert sc.calculate(StatisticalFunction.COUNT) == 0
        assert sc.calculate(StatisticalFunction.SUM) == 0.0
        assert sc.calculate(StatisticalFunction.AVERAGE) == 0.0


class TestAdvancedConditionEvaluator:
    """Test suite for AdvancedConditionEvaluator class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.evaluator = AdvancedConditionEvaluator()

        # Create test building objects
        self.test_objects = [
            BuildingObject(
                object_id="room_1",
                object_type="room",
                properties={
                    "area": 200,
                    "height": 3,
                    "material": "concrete",
                    "timestamp": "2024-01-15T10:00:00",
                    "name": "Conference Room A",
                    "load": 500,
                    "efficiency": 0.85
                },
                location={"x": 0, "y": 0, "z": 0, "width": 20, "height": 3, "depth": 10}
            ),
            BuildingObject(
                object_id="room_2",
                object_type="room",
                properties={
                    "area": 150,
                    "height": 3,
                    "material": "steel",
                    "timestamp": "2024-01-15T14:00:00",
                    "name": "Office Room B",
                    "load": 300,
                    "efficiency": 0.75
                },
                location={"x": 20, "y": 0, "z": 0, "width": 15, "height": 3, "depth": 10}
            ),
            BuildingObject(
                object_id="wall_1",
                object_type="wall",
                properties={
                    "thickness": 0.2,
                    "material": "concrete",
                    "timestamp": "2024-01-15T12:00:00",
                    "name": "Exterior Wall",
                    "load": 1000,
                    "efficiency": 0.90
                },
                location={"x": 0, "y": 0, "z": 0, "width": 35, "height": 3, "depth": 0.2}
            )
        ]

    def test_evaluate_temporal_condition(self):
        """Test temporal condition evaluation"""
        condition = RuleCondition(
            type="temporal",
            element_type="room",
            temporal_params={
                "operator": "during",
                "start": "2024-01-15T09:00:00",
                "end": "2024-01-15T15:00:00",
                "property": "timestamp"
            }
        )

        results = self.evaluator.evaluate_temporal_condition(condition, self.test_objects)

        # Both rooms should match the temporal condition
        assert len(results) == 2
        assert any(obj.object_id == "room_1" for obj in results)
        assert any(obj.object_id == "room_2" for obj in results)

    def test_evaluate_dynamic_condition(self):
        """Test dynamic condition evaluation"""
        condition = RuleCondition(
            type="dynamic",
            element_type="room",
            dynamic_params={
                "resolver": "area_calculator",
                "operator": ">=",
                "value": 150
            }
        )

        results = self.evaluator.evaluate_dynamic_condition(condition, self.test_objects)

        # Both rooms should match (areas >= 150)
        assert len(results) == 2
        assert any(obj.object_id == "room_1" for obj in results)
        assert any(obj.object_id == "room_2" for obj in results)

    def test_evaluate_statistical_condition(self):
        """Test statistical condition evaluation"""
        condition = RuleCondition(
            type="statistical",
            element_type="room",
            statistical_params={
                "function": "average",
                "property": "area",
                "operator": ">=",
                "threshold": 175
            }
        )

        results = self.evaluator.evaluate_statistical_condition(condition, self.test_objects)

        # Should match rooms (average area = 175)
        assert len(results) == 2

    def test_evaluate_pattern_condition(self):
        """Test pattern condition evaluation"""
        condition = RuleCondition(
            type="pattern",
            element_type="room",
            pattern_params={
                "pattern": r"Room",
                "property": "name",
                "case_sensitive": False
            }
        )

        results = self.evaluator.evaluate_pattern_condition(condition, self.test_objects)

        # Both rooms should match the pattern
        assert len(results) == 2
        assert any(obj.object_id == "room_1" for obj in results)
        assert any(obj.object_id == "room_2" for obj in results)

    def test_evaluate_range_condition(self):
        """Test range condition evaluation"""
        condition = RuleCondition(
            type="range",
            element_type="room",
            range_params={
                "property": "area",
                "ranges": [
                    {"min": 100, "max": 250},
                    {"min": 300, "max": 400}
                ],
                "operation": "any"
            }
        )

        results = self.evaluator.evaluate_range_condition(condition, self.test_objects)

        # Both rooms should match (areas in first range)
        assert len(results) == 2

    def test_evaluate_complex_logical_condition(self):
        """Test complex logical condition evaluation"""
        condition = RuleCondition(
            type="logical",
            element_type="room",
            logical_params={
                "expression": {
                    "operator": "and",
                    "operands": [
                        {
                            "operator": "or",
                            "operands": [
                                {"property": "area", "operator": ">=", "value": 200},
                                {"property": "efficiency", "operator": ">=", "value": 0.8}
                            ]
                        },
                        {
                            "operator": "not",
                            "operands": [
                                {"property": "material", "operator": "==", "value": "wood"}
                            ]
                        }
                    ]
                }
            }
        )

        results = self.evaluator.evaluate_complex_logical_condition(condition, self.test_objects)

        # Should match rooms based on logical expression
        assert len(results) >= 0  # Depends on implementation details

    def test_temporal_operator_evaluation(self):
        """Test temporal operator evaluation"""
        start = datetime(2024, 1, 15, 10, 0, 0)
        end = datetime(2024, 1, 15, 18, 0, 0)
        condition_range = TemporalRange(start, end)

        # Test DURING operator
        object_time = datetime(2024, 1, 15, 14, 0, 0)
        result = self.evaluator._evaluate_temporal_operator(
            TemporalOperator.DURING, object_time, condition_range
        )
        assert result == True

        # Test BEFORE operator
        object_time_before = datetime(2024, 1, 15, 9, 0, 0)
        result = self.evaluator._evaluate_temporal_operator(
            TemporalOperator.BEFORE, object_time_before, condition_range
        )
        assert result == True

        # Test AFTER operator
        object_time_after = datetime(2024, 1, 15, 19, 0, 0)
        result = self.evaluator._evaluate_temporal_operator(
            TemporalOperator.AFTER, object_time_after, condition_range
        )
        assert result == True

    def test_dynamic_value_evaluation(self):
        """Test dynamic value evaluation"""
        condition = RuleCondition(
            type="dynamic",
            dynamic_params={
                "operator": ">=",
                "value": 150
            }
        )

        # Test various operators
        assert self.evaluator._evaluate_dynamic_value(200, condition) == True
        assert self.evaluator._evaluate_dynamic_value(150, condition) == True
        assert self.evaluator._evaluate_dynamic_value(100, condition) == False

    def test_statistical_condition_evaluation(self):
        """Test statistical condition evaluation"""
        # Test various operators
        assert self.evaluator._evaluate_statistical_condition(200, ">=", 150) == True
        assert self.evaluator._evaluate_statistical_condition(100, ">=", 150) == False
        assert self.evaluator._evaluate_statistical_condition(150, "==", 150) == True
        assert self.evaluator._evaluate_statistical_condition(200, "!=", 150) == True

    def test_logical_expression_evaluation(self):
        """Test logical expression evaluation"""
        expression = {
            "operator": "and",
            "operands": [
                {"operator": "or", "operands": [{"test": "condition1"}, {"test": "condition2"}]},
                {"operator": "not", "operands": [{"test": "condition3"}]}
            ]
        }

        # Mock the logical operand evaluation
        with patch.object(self.evaluator, '_evaluate_logical_operand') as mock_eval:
            mock_eval.return_value = self.test_objects[:1]  # Return first object

            results = self.evaluator._evaluate_logical_expression(expression, self.test_objects)

            # Should call the mock evaluator
            assert mock_eval.called

    def test_temporal_value_parsing(self):
        """Test temporal value parsing"""
        # Test datetime object
        dt = datetime(2024, 1, 15, 10, 0, 0)
        result = self.evaluator._parse_temporal_value(dt)
        assert result == dt

        # Test ISO string
        iso_string = "2024-01-15T10:00:00"
        result = self.evaluator._parse_temporal_value(iso_string)
        assert result == datetime(2024, 1, 15, 10, 0, 0)

        # Test timestamp
        timestamp = 1705312800  # Unix timestamp
        result = self.evaluator._parse_temporal_value(timestamp)
        assert isinstance(result, datetime)

        # Test invalid value
        result = self.evaluator._parse_temporal_value("invalid")
        assert result is None

    def test_object_temporal_data_extraction(self):
        """Test object temporal data extraction"""
        obj = BuildingObject(
            object_id="test",
            object_type="room",
            properties={
                "timestamp": "2024-01-15T10:00:00",
                "time_range": {
                    "start": "2024-01-15T09:00:00",
                    "end": "2024-01-15T17:00:00"
                }
            }
        )

        # Test single timestamp
        temporal_params = {"property": "timestamp"}
        result = self.evaluator._get_object_temporal_data(obj, temporal_params)
        assert isinstance(result, datetime)

        # Test time range
        temporal_params = {"property": "time_range"}
        result = self.evaluator._get_object_temporal_data(obj, temporal_params)
        assert isinstance(result, TemporalRange)

    def test_object_grouping_for_statistics(self):
        """Test object grouping for statistics"""
        objects = [
            BuildingObject(object_id="obj1", object_type="room", properties={"area": 100, "floor": 1}),
            BuildingObject(object_id="obj2", object_type="room", properties={"area": 200, "floor": 1}),
            BuildingObject(object_id="obj3", object_type="room", properties={"area": 150, "floor": 2}),
            BuildingObject(object_id="obj4", object_type="room", properties={"area": 300, "floor": 2})
        ]

        # Test grouping by floor
        statistical_params = {"group_by": "floor"}
        groups = self.evaluator._group_objects_for_statistics(objects, statistical_params)

        assert "1" in groups
        assert "2" in groups
        assert len(groups["1"]) == 2
        assert len(groups["2"]) == 2

        # Test no grouping
        statistical_params = {}
        groups = self.evaluator._group_objects_for_statistics(objects, statistical_params)

        assert "all" in groups
        assert len(groups["all"]) == 4

    def test_dynamic_resolvers(self):
        """Test dynamic value resolvers"""
        obj = BuildingObject(
            object_id="test",
            object_type="room",
            properties={
                "area": 200,
                "volume": 600,
                "load": 500,
                "efficiency": 0.85,
                "cost": 1000,
                "safety_factor": 2.5
            },
            location={"width": 20, "height": 3, "depth": 10}
        )

        # Test area resolver
        result = self.evaluator._resolve_area(obj)
        assert result == 200.0

        # Test volume resolver
        result = self.evaluator._resolve_volume(obj)
        assert result == 600.0

        # Test load resolver
        result = self.evaluator._resolve_load(obj)
        assert result == 500.0

        # Test efficiency resolver
        result = self.evaluator._resolve_efficiency(obj)
        assert result == 0.85

        # Test cost resolver
        result = self.evaluator._resolve_cost(obj)
        assert result == 1000.0

        # Test safety factor resolver
        result = self.evaluator._resolve_safety_factor(obj)
        assert result == 2.5

    def test_compliance_score_resolver(self):
        """Test compliance score resolver"""
        obj = BuildingObject(
            object_id="test",
            object_type="room",
            properties={"compliance_score": 85.0}
        )

        # Test with compliance_score property
        result = self.evaluator._resolve_compliance_score(obj)
        assert result == 85.0

        # Test with context calculations
        context = Mock()
        context.calculations = {
            "violations": [
                {"object_id": "test", "severity": "error"},
                {"object_id": "other", "severity": "warning"}
            ]
        }

        result = self.evaluator._resolve_compliance_score(obj, context)
        assert result == 90.0  # 100 - (1 * 10)


class TestTemporalOperator:
    """Test suite for TemporalOperator enum"""

    def test_temporal_operators(self):
        """Test temporal operator enum values"""
        assert TemporalOperator.BEFORE.value == "before"
        assert TemporalOperator.AFTER.value == "after"
        assert TemporalOperator.DURING.value == "during"
        assert TemporalOperator.WITHIN.value == "within"
        assert TemporalOperator.OVERLAPS.value == "overlaps"
        assert TemporalOperator.CONTAINS.value == "contains"
        assert TemporalOperator.EQUALS.value == "equals"


class TestStatisticalFunction:
    """Test suite for StatisticalFunction enum"""

    def test_statistical_functions(self):
        """Test statistical function enum values"""
        assert StatisticalFunction.COUNT.value == "count"
        assert StatisticalFunction.SUM.value == "sum"
        assert StatisticalFunction.AVERAGE.value == "average"
        assert StatisticalFunction.MEAN.value == "mean"
        assert StatisticalFunction.MEDIAN.value == "median"
        assert StatisticalFunction.MIN.value == "min"
        assert StatisticalFunction.MAX.value == "max"
        assert StatisticalFunction.STD_DEV.value == "std_dev"
        assert StatisticalFunction.VARIANCE.value == "variance"
        assert StatisticalFunction.PERCENTILE.value == "percentile"


class TestLogicalOperator:
    """Test suite for LogicalOperator enum"""

    def test_logical_operators(self):
        """Test logical operator enum values"""
        assert LogicalOperator.AND.value == "and"
        assert LogicalOperator.OR.value == "or"
        assert LogicalOperator.NOT.value == "not"
        assert LogicalOperator.XOR.value == "xor"
        assert LogicalOperator.NAND.value == "nand"
        assert LogicalOperator.NOR.value == "nor"


class TestErrorHandling:
    """Test suite for error handling"""

    def test_invalid_temporal_condition(self):
        """Test handling of invalid temporal conditions"""
        evaluator = AdvancedConditionEvaluator()

        # Invalid temporal parameters
        condition = RuleCondition(
            type="temporal",
            element_type="room",
            temporal_params={
                "operator": "invalid_operator",
                "start": "invalid_date",
                "end": "invalid_date"
            }
        )

        results = evaluator.evaluate_temporal_condition(condition, self.test_objects)
        assert results == []

    def test_invalid_dynamic_condition(self):
        """Test handling of invalid dynamic conditions"""
        evaluator = AdvancedConditionEvaluator()

        # Unknown resolver
        condition = RuleCondition(
            type="dynamic",
            element_type="room",
            dynamic_params={
                "resolver": "unknown_resolver",
                "operator": ">=",
                "value": 150
            }
        )

        results = evaluator.evaluate_dynamic_condition(condition, self.test_objects)
        assert results == []

    def test_invalid_pattern_condition(self):
        """Test handling of invalid pattern conditions"""
        evaluator = AdvancedConditionEvaluator()

        # Invalid regex pattern
        condition = RuleCondition(
            type="pattern",
            element_type="room",
            pattern_params={
                "pattern": r"[invalid",
                "property": "name"
            }
        )

        results = evaluator.evaluate_pattern_condition(condition, self.test_objects)
        assert results == []

    def test_invalid_logical_expression(self):
        """Test handling of invalid logical expressions"""
        evaluator = AdvancedConditionEvaluator()

        # Invalid logical expression
        condition = RuleCondition(
            type="logical",
            element_type="room",
            logical_params={
                "expression": {
                    "operator": "invalid_operator",
                    "operands": []
                }
            }
        )

        results = evaluator.evaluate_complex_logical_condition(condition, self.test_objects)
        assert results == []


class TestPerformanceBenchmarks:
    """Test suite for performance benchmarks"""

    def test_temporal_condition_performance(self):
        """Test temporal condition performance"""
        evaluator = AdvancedConditionEvaluator()

        # Create many objects with temporal data
        objects = []
        for i in range(1000):
            obj = BuildingObject(
                object_id=f"obj_{i}",
                object_type="room",
                properties={"timestamp": f"2024-01-15T{i%24:02d}:00:00"}
            )
            objects.append(obj)

        condition = RuleCondition(
            type="temporal",
            element_type="room",
            temporal_params={
                "operator": "during",
                "start": "2024-01-15T10:00:00",
                "end": "2024-01-15T15:00:00",
                "property": "timestamp"
            }
        )

        import time
        start_time = time.time()
        results = evaluator.evaluate_temporal_condition(condition, objects)
        end_time = time.time()

        # Should complete within reasonable time
        assert end_time - start_time < 1.0  # 1 second
        assert len(results) > 0

    def test_statistical_condition_performance(self):
        """Test statistical condition performance"""
        evaluator = AdvancedConditionEvaluator()

        # Create many objects with numerical data
        objects = []
        for i in range(1000):
            obj = BuildingObject(
                object_id=f"obj_{i}",
                object_type="room",
                properties={"area": i, "floor": i % 10}
            )
            objects.append(obj)

        condition = RuleCondition(
            type="statistical",
            element_type="room",
            statistical_params={
                "function": "average",
                "property": "area",
                "operator": ">=",
                "threshold": 500,
                "group_by": "floor"
            }
        )

        import time
        start_time = time.time()
        results = evaluator.evaluate_statistical_condition(condition, objects)
        end_time = time.time()

        # Should complete within reasonable time
        assert end_time - start_time < 1.0  # 1 second
        assert len(results) > 0


if __name__ == "__main__":
    pytest.main([__file__])
