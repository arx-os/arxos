"""
Comprehensive tests for ConditionEvaluator

This module tests all condition evaluation scenarios including:
- Property conditions
- Spatial conditions
- Relationship conditions
- System conditions
- Composite conditions
- Edge cases and error handling
"""

import pytest
from typing import List, Dict, Any
from datetime import datetime

from validate.rule_engine import ConditionEvaluator
from models.mcp_models import (
    BuildingObject,
    RuleCondition,
    ConditionType,
    RuleSeverity,
    RuleCategory,
)


class TestConditionEvaluator:
    """Comprehensive test suite for ConditionEvaluator"""

    def setup_method(self):
        """Set up test fixtures"""
        self.evaluator = ConditionEvaluator()

        # Create test building objects
        self.test_objects = [
            BuildingObject(
                object_id="outlet_001",
                object_type="electrical_outlet",
                properties={
                    "location": "bathroom",
                    "load": 15.0,
                    "gfci_protected": False,
                    "voltage": 120,
                    "circuit": "circuit_001",
                },
                location={"x": 100, "y": 200, "width": 10, "height": 10},
            ),
            BuildingObject(
                object_id="outlet_002",
                object_type="electrical_outlet",
                properties={
                    "location": "kitchen",
                    "load": 20.0,
                    "gfci_protected": True,
                    "voltage": 120,
                    "circuit": "circuit_002",
                },
                location={"x": 150, "y": 250, "width": 10, "height": 10},
            ),
            BuildingObject(
                object_id="room_001",
                object_type="room",
                properties={
                    "type": "bathroom",
                    "area": 80.0,
                    "occupancy": 2,
                    "height": 8.0,
                },
                location={"x": 50, "y": 150, "width": 100, "height": 80},
            ),
            BuildingObject(
                object_id="hvac_001",
                object_type="hvac_unit",
                properties={
                    "type": "air_handler",
                    "capacity": 5000.0,
                    "system_type": "heating_cooling",
                },
                location={"x": 300, "y": 100, "width": 60, "height": 40},
            ),
            BuildingObject(
                object_id="wall_001",
                object_type="wall",
                properties={"material": "concrete", "load": 1000.0, "fire_rating": 2},
                location={"x": 0, "y": 0, "width": 200, "height": 8},
            ),
        ]

    def test_property_condition_equals(self):
        """Test property condition with equals operator"""
        condition = RuleCondition(
            type=ConditionType.PROPERTY,
            element_type="electrical_outlet",
            property="location",
            operator="==",
            value="bathroom",
        )

        matched = self.evaluator.evaluate_condition(condition, self.test_objects)

        assert len(matched) == 1
        assert matched[0].object_id == "outlet_001"

    def test_property_condition_in_list(self):
        """Test property condition with 'in' operator"""
        condition = RuleCondition(
            type=ConditionType.PROPERTY,
            element_type="electrical_outlet",
            property="location",
            operator="in",
            value=["bathroom", "kitchen"],
        )

        matched = self.evaluator.evaluate_condition(condition, self.test_objects)

        assert len(matched) == 2
        assert any(obj.object_id == "outlet_001" for obj in matched)
        assert any(obj.object_id == "outlet_002" for obj in matched)

    def test_property_condition_numeric_comparison(self):
        """Test property condition with numeric comparison"""
        condition = RuleCondition(
            type=ConditionType.PROPERTY,
            element_type="electrical_outlet",
            property="load",
            operator=">=",
            value=15.0,
        )

        matched = self.evaluator.evaluate_condition(condition, self.test_objects)

        assert len(matched) == 2
        assert any(obj.object_id == "outlet_001" for obj in matched)
        assert any(obj.object_id == "outlet_002" for obj in matched)

    def test_property_condition_boolean(self):
        """Test property condition with boolean values"""
        condition = RuleCondition(
            type=ConditionType.PROPERTY,
            element_type="electrical_outlet",
            property="gfci_protected",
            operator="==",
            value=True,
        )

        matched = self.evaluator.evaluate_condition(condition, self.test_objects)

        assert len(matched) == 1
        assert matched[0].object_id == "outlet_002"

    def test_spatial_condition_area(self):
        """Test spatial condition with area calculation"""
        condition = RuleCondition(
            type=ConditionType.SPATIAL,
            element_type="room",
            property="area",
            operator=">=",
            value=50.0,
        )

        matched = self.evaluator.evaluate_condition(condition, self.test_objects)

        assert len(matched) == 1
        assert matched[0].object_id == "room_001"

    def test_spatial_condition_height(self):
        """Test spatial condition with height"""
        condition = RuleCondition(
            type=ConditionType.SPATIAL,
            element_type="room",
            property="height",
            operator="==",
            value=8.0,
        )

        matched = self.evaluator.evaluate_condition(condition, self.test_objects)

        assert len(matched) == 1
        assert matched[0].object_id == "room_001"

    def test_relationship_condition(self):
        """Test relationship condition"""
        # Add connections to test objects
        self.test_objects[0].connections = [
            "room_001"
        ]  # outlet_001 connected to room_001

        condition = RuleCondition(
            type=ConditionType.RELATIONSHIP,
            element_type="electrical_outlet",
            relationship="located_in",
            target_type="room",
        )

        matched = self.evaluator.evaluate_condition(condition, self.test_objects)

        assert len(matched) == 1
        assert matched[0].object_id == "outlet_001"

    def test_system_condition(self):
        """Test system condition"""
        condition = RuleCondition(
            type=ConditionType.SYSTEM, element_type="hvac_unit", value="heating_cooling"
        )

        matched = self.evaluator.evaluate_condition(condition, self.test_objects)

        assert len(matched) == 1
        assert matched[0].object_id == "hvac_001"

    def test_composite_condition_and(self):
        """Test composite condition with AND operator"""
        condition = RuleCondition(
            type=ConditionType.COMPOSITE,
            composite_operator="AND",
            conditions=[
                RuleCondition(
                    type=ConditionType.PROPERTY,
                    element_type="electrical_outlet",
                    property="location",
                    operator="==",
                    value="bathroom",
                ),
                RuleCondition(
                    type=ConditionType.PROPERTY,
                    element_type="electrical_outlet",
                    property="gfci_protected",
                    operator="==",
                    value=False,
                ),
            ],
        )

        matched = self.evaluator.evaluate_condition(condition, self.test_objects)

        assert len(matched) == 1
        assert matched[0].object_id == "outlet_001"

    def test_composite_condition_or(self):
        """Test composite condition with OR operator"""
        condition = RuleCondition(
            type=ConditionType.COMPOSITE,
            composite_operator="OR",
            conditions=[
                RuleCondition(
                    type=ConditionType.PROPERTY,
                    element_type="electrical_outlet",
                    property="location",
                    operator="==",
                    value="bathroom",
                ),
                RuleCondition(
                    type=ConditionType.PROPERTY,
                    element_type="electrical_outlet",
                    property="location",
                    operator="==",
                    value="kitchen",
                ),
            ],
        )

        matched = self.evaluator.evaluate_condition(condition, self.test_objects)

        assert len(matched) == 2
        assert any(obj.object_id == "outlet_001" for obj in matched)
        assert any(obj.object_id == "outlet_002" for obj in matched)

    def test_unknown_condition_type(self):
        """Test handling of unknown condition type"""
        condition = RuleCondition(
            type="UNKNOWN_TYPE",
            element_type="electrical_outlet",
            property="location",
            operator="==",
            value="bathroom",
        )

        matched = self.evaluator.evaluate_condition(condition, self.test_objects)

        assert len(matched) == 0

    def test_unknown_operator(self):
        """Test handling of unknown operator"""
        condition = RuleCondition(
            type=ConditionType.PROPERTY,
            element_type="electrical_outlet",
            property="location",
            operator="UNKNOWN_OP",
            value="bathroom",
        )

        matched = self.evaluator.evaluate_condition(condition, self.test_objects)

        assert len(matched) == 0

    def test_missing_property(self):
        """Test condition with missing property"""
        condition = RuleCondition(
            type=ConditionType.PROPERTY,
            element_type="electrical_outlet",
            property="nonexistent_property",
            operator="==",
            value="bathroom",
        )

        matched = self.evaluator.evaluate_condition(condition, self.test_objects)

        assert len(matched) == 0

    def test_type_error_in_evaluation(self):
        """Test handling of type errors during evaluation"""
        condition = RuleCondition(
            type=ConditionType.PROPERTY,
            element_type="electrical_outlet",
            property="load",
            operator=">",
            value="not_a_number",
        )

        matched = self.evaluator.evaluate_condition(condition, self.test_objects)

        assert len(matched) == 0

    def test_regex_operator(self):
        """Test regex operator"""
        condition = RuleCondition(
            type=ConditionType.PROPERTY,
            element_type="electrical_outlet",
            property="location",
            operator="regex",
            value="bath.*",
        )

        matched = self.evaluator.evaluate_condition(condition, self.test_objects)

        assert len(matched) == 1
        assert matched[0].object_id == "outlet_001"

    def test_starts_with_operator(self):
        """Test starts_with operator"""
        condition = RuleCondition(
            type=ConditionType.PROPERTY,
            element_type="electrical_outlet",
            property="location",
            operator="starts_with",
            value="bath",
        )

        matched = self.evaluator.evaluate_condition(condition, self.test_objects)

        assert len(matched) == 1
        assert matched[0].object_id == "outlet_001"

    def test_ends_with_operator(self):
        """Test ends_with operator"""
        condition = RuleCondition(
            type=ConditionType.PROPERTY,
            element_type="electrical_outlet",
            property="location",
            operator="ends_with",
            value="room",
        )

        matched = self.evaluator.evaluate_condition(condition, self.test_objects)

        assert len(matched) == 1
        assert matched[0].object_id == "outlet_001"

    def test_contains_operator(self):
        """Test contains operator"""
        condition = RuleCondition(
            type=ConditionType.PROPERTY,
            element_type="electrical_outlet",
            property="location",
            operator="contains",
            value="room",
        )

        matched = self.evaluator.evaluate_condition(condition, self.test_objects)

        assert len(matched) == 1
        assert matched[0].object_id == "outlet_001"

    def test_not_in_operator(self):
        """Test not_in operator"""
        condition = RuleCondition(
            type=ConditionType.PROPERTY,
            element_type="electrical_outlet",
            property="location",
            operator="not_in",
            value=["kitchen", "office"],
        )

        matched = self.evaluator.evaluate_condition(condition, self.test_objects)

        assert len(matched) == 1
        assert matched[0].object_id == "outlet_001"

    def test_empty_objects_list(self):
        """Test evaluation with empty objects list"""
        condition = RuleCondition(
            type=ConditionType.PROPERTY,
            element_type="electrical_outlet",
            property="location",
            operator="==",
            value="bathroom",
        )

        matched = self.evaluator.evaluate_condition(condition, [])

        assert len(matched) == 0

    def test_none_condition(self):
        """Test evaluation with None condition"""
        matched = self.evaluator.evaluate_condition(None, self.test_objects)

        assert len(matched) == 0

    def test_empty_composite_condition(self):
        """Test composite condition with no sub-conditions"""
        condition = RuleCondition(
            type=ConditionType.COMPOSITE, composite_operator="AND", conditions=[]
        )

        matched = self.evaluator.evaluate_condition(condition, self.test_objects)

        assert len(matched) == 0

    def test_unknown_composite_operator(self):
        """Test composite condition with unknown operator"""
        condition = RuleCondition(
            type=ConditionType.COMPOSITE,
            composite_operator="UNKNOWN",
            conditions=[
                RuleCondition(
                    type=ConditionType.PROPERTY,
                    element_type="electrical_outlet",
                    property="location",
                    operator="==",
                    value="bathroom",
                )
            ],
        )

        matched = self.evaluator.evaluate_condition(condition, self.test_objects)

        assert len(matched) == 0
