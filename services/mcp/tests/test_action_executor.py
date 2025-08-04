"""
Comprehensive tests for ActionExecutor

This module tests all action execution scenarios including:
- Validation actions
- Calculation actions
- Warning actions
- Error actions
- Formula evaluation
- Edge cases and error handling
"""

import pytest
from typing import List, Dict, Any
from datetime import datetime

from validate.rule_engine import ActionExecutor, RuleExecutionContext
from models.mcp_models import (
    BuildingObject, RuleAction, ActionType, RuleSeverity, RuleCategory,
    MCPRule, RuleCondition, ConditionType
)


class TestActionExecutor:
    """Comprehensive test suite for ActionExecutor"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.executor = ActionExecutor()
        
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
                    "circuit": "circuit_001"
                },
                location={"x": 100, "y": 200, "width": 10, "height": 10}
            ),
            BuildingObject(
                object_id="outlet_002",
                object_type="electrical_outlet",
                properties={
                    "location": "kitchen",
                    "load": 20.0,
                    "gfci_protected": True,
                    "voltage": 120,
                    "circuit": "circuit_002"
                },
                location={"x": 150, "y": 250, "width": 10, "height": 10}
            ),
            BuildingObject(
                object_id="hvac_001",
                object_type="hvac_unit",
                properties={
                    "type": "air_handler",
                    "capacity": 5000.0,
                    "system_type": "heating_cooling"
                },
                location={"x": 300, "y": 100, "width": 60, "height": 40}
            ),
            BuildingObject(
                object_id="sink_001",
                object_type="sink",
                properties={
                    "type": "kitchen_sink",
                    "flow_rate": 2.5,
                    "hot_water": True
                },
                location={"x": 200, "y": 300, "width": 30, "height": 20}
            ),
            BuildingObject(
                object_id="toilet_001",
                object_type="toilet",
                properties={
                    "type": "water_closet",
                    "flow_rate": 1.6,
                    "flush_type": "gravity"
                },
                location={"x": 250, "y": 350, "width": 20, "height": 25}
            )
        ]
        
        # Create test rule
        self.test_rule = MCPRule(
            rule_id="test_rule_001",
            name="Test Rule",
            description="Test rule for validation",
            category=RuleCategory.ELECTRICAL_SAFETY,
            conditions=[
                RuleCondition(
                    type=ConditionType.PROPERTY,
                    element_type="electrical_outlet",
                    property="location",
                    operator="==",
                    value="bathroom"
                )
            ],
            actions=[]
        )
        
        # Create test context
        self.context = RuleExecutionContext(
            building_model=None,  # Will be set in individual tests
            rule=self.test_rule,
            matched_objects=self.test_objects[:2],  # First two objects
            calculations={},
            metadata={}
        )
    
    def test_validation_action_execution(self):
        """Test validation action execution"""
        action = RuleAction(
            type=ActionType.VALIDATION,
            message="GFCI protection required for bathroom outlets",
            severity=RuleSeverity.ERROR,
            code_reference="NEC 210.8(A)(1)"
        )
        
        self.context.rule.actions = [action]
        
        violations, calculations = self.executor.execute_actions(self.context)
        
        # Should have one violation per matched object
        assert len(violations) == 2
        assert all(v.severity == RuleSeverity.ERROR for v in violations)
        assert all("GFCI protection required" in v.message for v in violations)
        assert len(calculations) == 0
    
    def test_calculation_action_execution(self):
        """Test calculation action execution"""
        action = RuleAction(
            type=ActionType.CALCULATION,
            formula="area * 0.1",
            unit="sqft",
            description="Calculate required area"
        )
        
        self.context.rule.actions = [action]
        
        violations, calculations = self.executor.execute_actions(self.context)
        
        assert len(violations) == 0
        assert len(calculations) == 1
        assert "area * 0.1" in calculations
        assert calculations["area * 0.1"]["unit"] == "sqft"
    
    def test_warning_action_execution(self):
        """Test warning action execution"""
        action = RuleAction(
            type=ActionType.WARNING,
            message="Consider upgrading to GFCI protection",
            severity=RuleSeverity.WARNING,
            code_reference="NEC 210.8(A)(1)"
        )
        
        self.context.rule.actions = [action]
        
        violations, calculations = self.executor.execute_actions(self.context)
        
        assert len(violations) == 2
        assert all(v.severity == RuleSeverity.WARNING for v in violations)
        assert all("Consider upgrading" in v.message for v in violations)
    
    def test_error_action_execution(self):
        """Test error action execution"""
        action = RuleAction(
            type=ActionType.ERROR,
            message="Critical safety violation",
            severity=RuleSeverity.ERROR,
            code_reference="NEC 210.8(A)(1)"
        )
        
        self.context.rule.actions = [action]
        
        violations, calculations = self.executor.execute_actions(self.context)
        
        assert len(violations) == 2
        assert all(v.severity == RuleSeverity.ERROR for v in violations)
        assert all("Critical safety violation" in v.message for v in violations)
    
    def test_multiple_actions_execution(self):
        """Test execution of multiple actions"""
        actions = [
            RuleAction(
                type=ActionType.VALIDATION,
                message="GFCI protection required",
                severity=RuleSeverity.ERROR
            ),
            RuleAction(
                type=ActionType.CALCULATION,
                formula="count * 15",
                unit="watts",
                description="Total load calculation"
            )
        ]
        
        self.context.rule.actions = actions
        
        violations, calculations = self.executor.execute_actions(self.context)
        
        assert len(violations) == 2
        assert len(calculations) == 1
        assert "count * 15" in calculations
    
    def test_formula_evaluation_simple(self):
        """Test simple formula evaluation"""
        action = RuleAction(
            type=ActionType.CALCULATION,
            formula="area + 10",
            unit="sqft"
        )
        
        self.context.rule.actions = [action]
        
        violations, calculations = self.executor.execute_actions(self.context)
        
        assert len(calculations) == 1
        result = calculations["area + 10"]["result"]
        assert isinstance(result, (int, float))
    
    def test_formula_evaluation_with_variables(self):
        """Test formula evaluation with variables"""
        action = RuleAction(
            type=ActionType.CALCULATION,
            formula="area * count",
            unit="sqft"
        )
        
        self.context.rule.actions = [action]
        
        violations, calculations = self.executor.execute_actions(self.context)
        
        assert len(calculations) == 1
        result = calculations["area * count"]["result"]
        assert isinstance(result, (int, float))
    
    def test_formula_evaluation_with_calculations(self):
        """Test formula evaluation using previous calculations"""
        actions = [
            RuleAction(
                type=ActionType.CALCULATION,
                formula="area",
                unit="sqft",
                description="Calculate area"
            ),
            RuleAction(
                type=ActionType.CALCULATION,
                formula="area * 0.1",
                unit="sqft",
                description="Calculate 10% of area"
            )
        ]
        
        self.context.rule.actions = actions
        
        violations, calculations = self.executor.execute_actions(self.context)
        
        assert len(calculations) == 2
        assert "area" in calculations
        assert "area * 0.1" in calculations
    
    def test_formula_evaluation_error_handling(self):
        """Test formula evaluation error handling"""
        action = RuleAction(
            type=ActionType.CALCULATION,
            formula="invalid_formula",
            unit="units"
        )
        
        self.context.rule.actions = [action]
        
        violations, calculations = self.executor.execute_actions(self.context)
        
        # Should handle error gracefully - return empty calculations
        assert len(calculations) == 0
    
    def test_no_matched_objects(self):
        """Test execution with no matched objects"""
        self.context.matched_objects = []
        
        action = RuleAction(
            type=ActionType.VALIDATION,
            message="Test message",
            severity=RuleSeverity.ERROR
        )
        
        self.context.rule.actions = [action]
        
        violations, calculations = self.executor.execute_actions(self.context)
        
        # Should not generate violations when no objects match
        assert len(violations) == 0
    
    def test_empty_actions_list(self):
        """Test execution with empty actions list"""
        self.context.rule.actions = []
        
        violations, calculations = self.executor.execute_actions(self.context)
        
        assert len(violations) == 0
        assert len(calculations) == 0
    
    def test_none_action(self):
        """Test execution with None action"""
        self.context.rule.actions = [None]
        
        violations, calculations = self.executor.execute_actions(self.context)
        
        # Should handle None gracefully
        assert len(violations) == 0
        assert len(calculations) == 0
    
    def test_action_without_required_fields(self):
        """Test action without required fields"""
        action = RuleAction(
            type=ActionType.VALIDATION,
            # Missing message and severity
        )
        
        self.context.rule.actions = [action]
        
        violations, calculations = self.executor.execute_actions(self.context)
        
        # Should handle missing fields gracefully
        assert len(violations) == 0
    
    def test_calculation_action_without_formula(self):
        """Test calculation action without formula"""
        action = RuleAction(
            type=ActionType.CALCULATION,
            unit="units"
            # Missing formula
        )
        
        self.context.rule.actions = [action]
        
        violations, calculations = self.executor.execute_actions(self.context)
        
        # Should handle missing formula gracefully
        assert len(calculations) == 0
    
    def test_electrical_load_calculation(self):
        """Test electrical load calculation"""
        action = RuleAction(
            type=ActionType.CALCULATION,
            formula="electrical_load",
            unit="watts",
            description="Calculate total electrical load"
        )
        
        self.context.rule.actions = [action]
        
        violations, calculations = self.executor.execute_actions(self.context)
        
        assert len(calculations) == 1
        result = calculations["electrical_load"]["result"]
        assert isinstance(result, (int, float))
        assert result > 0
    
    def test_plumbing_flow_calculation(self):
        """Test plumbing flow calculation"""
        action = RuleAction(
            type=ActionType.CALCULATION,
            formula="plumbing_flow",
            unit="gpm",
            description="Calculate total plumbing flow"
        )
        
        # Use objects with plumbing fixtures
        self.context.matched_objects = self.test_objects[3:5]  # sink and toilet
        self.context.rule.actions = [action]
        
        violations, calculations = self.executor.execute_actions(self.context)
        
        assert len(calculations) == 1
        result = calculations["plumbing_flow"]["result"]
        assert isinstance(result, (int, float))
        assert result > 0
    
    def test_hvac_capacity_calculation(self):
        """Test HVAC capacity calculation"""
        action = RuleAction(
            type=ActionType.CALCULATION,
            formula="hvac_capacity",
            unit="btu/hr",
            description="Calculate total HVAC capacity"
        )
        
        # Use HVAC unit object
        self.context.matched_objects = [self.test_objects[2]]  # hvac_unit
        self.context.rule.actions = [action]
        
        violations, calculations = self.executor.execute_actions(self.context)
        
        assert len(calculations) == 1
        result = calculations["hvac_capacity"]["result"]
        assert isinstance(result, (int, float))
        assert result > 0
    
    def test_structural_load_calculation(self):
        """Test structural load calculation"""
        action = RuleAction(
            type=ActionType.CALCULATION,
            formula="structural_load",
            unit="lbs",
            description="Calculate total structural load"
        )
        
        # Use all objects (some might have structural properties)
        self.context.matched_objects = self.test_objects
        self.context.rule.actions = [action]
        
        violations, calculations = self.executor.execute_actions(self.context)
        
        assert len(calculations) == 1
        result = calculations["structural_load"]["result"]
        assert isinstance(result, (int, float))
        # Note: May be 0 if no structural objects are present
    
    def test_fire_egress_calculation(self):
        """Test fire egress calculation"""
        action = RuleAction(
            type=ActionType.CALCULATION,
            formula="fire_egress",
            unit="inches",
            description="Calculate fire egress requirements"
        )
        
        self.context.rule.actions = [action]
        
        violations, calculations = self.executor.execute_actions(self.context)
        
        assert len(calculations) == 1
        result = calculations["fire_egress"]["result"]
        assert isinstance(result, (int, float))
        assert result >= 0
    
    def test_area_calculation(self):
        """Test area calculation"""
        action = RuleAction(
            type=ActionType.CALCULATION,
            formula="area",
            unit="sqft",
            description="Calculate total area"
        )
        
        self.context.rule.actions = [action]
        
        violations, calculations = self.executor.execute_actions(self.context)
        
        assert len(calculations) == 1
        result = calculations["area"]["result"]
        assert isinstance(result, (int, float))
        assert result > 0
    
    def test_count_calculation(self):
        """Test count calculation"""
        action = RuleAction(
            type=ActionType.CALCULATION,
            formula="count",
            unit="units",
            description="Count matched objects"
        )
        
        self.context.rule.actions = [action]
        
        violations, calculations = self.executor.execute_actions(self.context)
        
        assert len(calculations) == 1
        result = calculations["count"]["result"]
        assert isinstance(result, int)
        assert result == 2  # Two matched objects
    
    def test_complex_formula_evaluation(self):
        """Test complex formula evaluation"""
        action = RuleAction(
            type=ActionType.CALCULATION,
            formula="(area * 0.1) + (count * 5)",
            unit="units",
            description="Complex calculation"
        )
        
        self.context.rule.actions = [action]
        
        violations, calculations = self.executor.execute_actions(self.context)
        
        assert len(calculations) == 1
        result = calculations["(area * 0.1) + (count * 5)"]["result"]
        assert isinstance(result, (int, float))
    
    def test_formula_with_division_by_zero(self):
        """Test formula with division by zero"""
        action = RuleAction(
            type=ActionType.CALCULATION,
            formula="area / 0",
            unit="units"
        )
        
        self.context.rule.actions = [action]
        
        violations, calculations = self.executor.execute_actions(self.context)
        
        # Should handle division by zero gracefully - return empty calculations
        assert len(calculations) == 0
    
    def test_formula_with_invalid_syntax(self):
        """Test formula with invalid syntax"""
        action = RuleAction(
            type=ActionType.CALCULATION,
            formula="area +",
            unit="units"
        )
        
        self.context.rule.actions = [action]
        
        violations, calculations = self.executor.execute_actions(self.context)
        
        # Should handle invalid syntax gracefully - return empty calculations
        assert len(calculations) == 0
    
    def test_action_with_metadata(self):
        """Test action execution with metadata"""
        self.context.metadata = {"test_key": "test_value"}
        
        action = RuleAction(
            type=ActionType.VALIDATION,
            message="Test message",
            severity=RuleSeverity.ERROR
        )
        
        self.context.rule.actions = [action]
        
        violations, calculations = self.executor.execute_actions(self.context)
        
        assert len(violations) == 2
        # Metadata should be preserved in context
        assert self.context.metadata["test_key"] == "test_value" 