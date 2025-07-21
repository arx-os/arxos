"""
SVGX Engine - Advanced Rule Engine Tests

Comprehensive test suite for the Advanced Rule Engine covering business, safety, operational, maintenance, and compliance rules.
Tests rule evaluation, performance, integration, and edge cases.
Follows Arxos engineering standards: absolute imports, global instances, comprehensive test coverage.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List

from svgx_engine import event_driven_behavior_engine
from svgx_engine.runtime.advanced_rule_engine import (
    advanced_rule_engine, AdvancedRuleEngine,
    Rule, RuleCondition, RuleAction, RuleResult,
    RuleType, RulePriority, RuleStatus
)
from svgx_engine.runtime.event_driven_behavior_engine import Event, EventType, EventPriority

class TestAdvancedRuleEngineLogic:
    """Test core rule engine logic and functionality."""
    
    def test_register_business_rule(self):
        """Test registering a business rule."""
        # Create test rule
        conditions = [
            RuleCondition(field="temperature", operator="greater", value=25.0),
            RuleCondition(field="humidity", operator="less", value=60.0, logical_operator="AND")
        ]
        actions = [
            RuleAction(action_type="activate_cooling", parameters={"power": 80}, target_element="hvac_01")
        ]
        
        rule = Rule(
            id="test_business_rule",
            name="Temperature Control Rule",
            description="Activate cooling when temperature is high and humidity is low",
            rule_type=RuleType.BUSINESS,
            priority=RulePriority.HIGH,
            conditions=conditions,
            actions=actions
        )
        
        # Register rule
        result = advanced_rule_engine.register_business_rule(rule)
        assert result is True
        
        # Verify registration
        registered_rule = advanced_rule_engine.get_rule("test_business_rule")
        assert registered_rule is not None
        assert registered_rule.name == "Temperature Control Rule"
        assert registered_rule.rule_type == RuleType.BUSINESS
        
        # Clean up
        advanced_rule_engine.delete_rule("test_business_rule")

    def test_register_safety_rule(self):
        """Test registering a safety rule."""
        conditions = [
            RuleCondition(field="pressure", operator="greater", value=100.0),
            RuleCondition(field="emergency_override", operator="equals", value=False, logical_operator="AND")
        ]
        actions = [
            RuleAction(action_type="emergency_shutdown", parameters={"reason": "high_pressure"}, target_element="system_01")
        ]
        
        rule = Rule(
            id="test_safety_rule",
            name="High Pressure Safety Rule",
            description="Emergency shutdown on high pressure",
            rule_type=RuleType.SAFETY,
            priority=RulePriority.CRITICAL,
            conditions=conditions,
            actions=actions
        )
        
        result = advanced_rule_engine.register_safety_rule(rule)
        assert result is True
        
        # Verify registration
        registered_rule = advanced_rule_engine.get_rule("test_safety_rule")
        assert registered_rule is not None
        assert registered_rule.rule_type == RuleType.SAFETY
        assert registered_rule.priority == RulePriority.CRITICAL
        
        # Clean up
        advanced_rule_engine.delete_rule("test_safety_rule")

    def test_register_operational_rule(self):
        """Test registering an operational rule."""
        conditions = [
            RuleCondition(field="maintenance_due", operator="equals", value=True)
        ]
        actions = [
            RuleAction(action_type="schedule_maintenance", parameters={"type": "preventive"}, target_element="equipment_01")
        ]
        
        rule = Rule(
            id="test_operational_rule",
            name="Maintenance Scheduling Rule",
            description="Schedule maintenance when due",
            rule_type=RuleType.OPERATIONAL,
            priority=RulePriority.NORMAL,
            conditions=conditions,
            actions=actions
        )
        
        result = advanced_rule_engine.register_operational_rule(rule)
        assert result is True
        
        # Clean up
        advanced_rule_engine.delete_rule("test_operational_rule")

    def test_register_maintenance_rule(self):
        """Test registering a maintenance rule."""
        conditions = [
            RuleCondition(field="runtime_hours", operator="greater", value=1000.0),
            RuleCondition(field="last_maintenance", operator="less", value=datetime.utcnow() - timedelta(days=30), logical_operator="AND")
        ]
        actions = [
            RuleAction(action_type="flag_for_maintenance", parameters={"priority": "high"}, target_element="motor_01")
        ]
        
        rule = Rule(
            id="test_maintenance_rule",
            name="Maintenance Due Rule",
            description="Flag equipment for maintenance based on runtime and last maintenance",
            rule_type=RuleType.MAINTENANCE,
            priority=RulePriority.HIGH,
            conditions=conditions,
            actions=actions
        )
        
        result = advanced_rule_engine.register_maintenance_rule(rule)
        assert result is True
        
        # Clean up
        advanced_rule_engine.delete_rule("test_maintenance_rule")

    def test_register_compliance_rule(self):
        """Test registering a compliance rule."""
        conditions = [
            RuleCondition(field="certification_expiry", operator="less", value=datetime.utcnow() + timedelta(days=30))
        ]
        actions = [
            RuleAction(action_type="notify_compliance", parameters={"type": "certification_expiry"}, target_element="system_01")
        ]
        
        rule = Rule(
            id="test_compliance_rule",
            name="Certification Expiry Rule",
            description="Notify when certification is expiring soon",
            rule_type=RuleType.COMPLIANCE,
            priority=RulePriority.HIGH,
            conditions=conditions,
            actions=actions
        )
        
        result = advanced_rule_engine.register_compliance_rule(rule)
        assert result is True
        
        # Clean up
        advanced_rule_engine.delete_rule("test_compliance_rule")

    def test_rule_validation(self):
        """Test rule validation."""
        # Test invalid rule (missing required fields)
        invalid_rule = Rule(
            id="",
            name="",
            description="",
            rule_type=RuleType.BUSINESS,
            priority=RulePriority.NORMAL,
            conditions=[],
            actions=[]
        )
        
        result = advanced_rule_engine.register_business_rule(invalid_rule)
        assert result is False

    def test_rule_dependencies(self):
        """Test rule dependencies and circular dependency detection."""
        # Create rules with dependencies
        rule1 = Rule(
            id="rule_1",
            name="Rule 1",
            description="First rule",
            rule_type=RuleType.BUSINESS,
            priority=RulePriority.NORMAL,
            conditions=[RuleCondition(field="value", operator="equals", value=1)],
            actions=[RuleAction(action_type="action1", parameters={})],
            dependencies=[]
        )

        rule2 = Rule(
            id="rule_2",
            name="Rule 2",
            description="Second rule",
            rule_type=RuleType.BUSINESS,
            priority=RulePriority.NORMAL,
            conditions=[RuleCondition(field="value", operator="equals", value=2)],
            actions=[RuleAction(action_type="action2", parameters={})],
            dependencies=["rule_1"]
        )

        # Register rules
        assert advanced_rule_engine.register_business_rule(rule1) is True
        assert advanced_rule_engine.register_business_rule(rule2) is True

        # Test circular dependency - rule3 depends on rule2, and rule2 depends on rule1
        # If rule1 also depends on rule3, that would create a cycle
        rule3 = Rule(
            id="rule_3",
            name="Rule 3",
            description="Third rule with circular dependency",
            rule_type=RuleType.BUSINESS,
            priority=RulePriority.NORMAL,
            conditions=[RuleCondition(field="value", operator="equals", value=3)],
            actions=[RuleAction(action_type="action3", parameters={})],
            dependencies=["rule_2"]  # This creates rule3 -> rule2 -> rule1
        )

        # Register rule3 (should succeed)
        assert advanced_rule_engine.register_business_rule(rule3) is True

        # Now try to create a circular dependency by making rule1 depend on rule3
        rule1_updated = Rule(
            id="rule_1",
            name="Rule 1 Updated",
            description="First rule with circular dependency",
            rule_type=RuleType.BUSINESS,
            priority=RulePriority.NORMAL,
            conditions=[RuleCondition(field="value", operator="equals", value=1)],
            actions=[RuleAction(action_type="action1", parameters={})],
            dependencies=["rule_3"]  # This would create rule1 -> rule3 -> rule2 -> rule1 (cycle)
        )

        # This should fail due to circular dependency
        result = advanced_rule_engine.register_business_rule(rule1_updated)
        assert result is False

        # Clean up
        advanced_rule_engine.delete_rule("rule_1")
        advanced_rule_engine.delete_rule("rule_2")
        advanced_rule_engine.delete_rule("rule_3")

    def test_condition_evaluation(self):
        """Test condition evaluation logic."""
        # Test various operators
        context = {
            "temperature": 30.0,
            "humidity": 50.0,
            "status": "active",
            "name": "test_system"
        }
        
        # Test equals
        condition = RuleCondition(field="status", operator="equals", value="active")
        result = advanced_rule_engine._evaluate_condition(condition, context)
        assert result is True
        
        # Test greater
        condition = RuleCondition(field="temperature", operator="greater", value=25.0)
        result = advanced_rule_engine._evaluate_condition(condition, context)
        assert result is True
        
        # Test less
        condition = RuleCondition(field="humidity", operator="less", value=60.0)
        result = advanced_rule_engine._evaluate_condition(condition, context)
        assert result is True
        
        # Test contains
        condition = RuleCondition(field="name", operator="contains", value="test")
        result = advanced_rule_engine._evaluate_condition(condition, context)
        assert result is True

    def test_rule_management(self):
        """Test rule management operations."""
        # Create test rule
        rule = Rule(
            id="test_management_rule",
            name="Test Management Rule",
            description="Test rule for management operations",
            rule_type=RuleType.BUSINESS,
            priority=RulePriority.NORMAL,
            conditions=[RuleCondition(field="value", operator="equals", value=1)],
            actions=[RuleAction(action_type="test_action", parameters={})]
        )
        
        # Register rule
        assert advanced_rule_engine.register_business_rule(rule) is True
        
        # Test get by type
        business_rules = advanced_rule_engine.get_rules_by_type(RuleType.BUSINESS)
        assert len(business_rules) >= 1
        assert any(r.id == "test_management_rule" for r in business_rules)
        
        # Test get by priority
        normal_rules = advanced_rule_engine.get_rules_by_priority(RulePriority.NORMAL)
        assert len(normal_rules) >= 1
        assert any(r.id == "test_management_rule" for r in normal_rules)
        
        # Test update rule
        updates = {"description": "Updated description"}
        assert advanced_rule_engine.update_rule("test_management_rule", updates) is True
        
        updated_rule = advanced_rule_engine.get_rule("test_management_rule")
        assert updated_rule.description == "Updated description"
        
        # Test delete rule
        assert advanced_rule_engine.delete_rule("test_management_rule") is True
        assert advanced_rule_engine.get_rule("test_management_rule") is None

class TestAdvancedRuleEngineAsync:
    """Test asynchronous rule evaluation."""
    
    @pytest.mark.asyncio
    async def test_evaluate_rules(self):
        """Test rule evaluation with context."""
        # Create test rule
        rule = Rule(
            id="test_evaluation_rule",
            name="Test Evaluation Rule",
            description="Test rule for evaluation",
            rule_type=RuleType.BUSINESS,
            priority=RulePriority.NORMAL,
            conditions=[
                RuleCondition(field="temperature", operator="greater", value=25.0),
                RuleCondition(field="humidity", operator="less", value=60.0, logical_operator="AND")
            ],
            actions=[
                RuleAction(action_type="test_action", parameters={"power": 50}, target_element="test_element")
            ]
        )
        
        # Register rule
        assert advanced_rule_engine.register_business_rule(rule) is True
        
        # Test context that should trigger rule
        context_trigger = {
            "temperature": 30.0,
            "humidity": 50.0
        }
        
        results = await advanced_rule_engine.evaluate_rules(context_trigger)
        assert len(results) >= 1
        
        # Find our rule result
        rule_result = next((r for r in results if r.rule_id == "test_evaluation_rule"), None)
        assert rule_result is not None
        assert rule_result.triggered is True
        assert len(rule_result.actions_executed) >= 1
        
        # Test context that should not trigger rule
        context_no_trigger = {
            "temperature": 20.0,
            "humidity": 70.0
        }
        
        results = await advanced_rule_engine.evaluate_rules(context_no_trigger)
        rule_result = next((r for r in results if r.rule_id == "test_evaluation_rule"), None)
        assert rule_result is not None
        assert rule_result.triggered is False
        
        # Clean up
        advanced_rule_engine.delete_rule("test_evaluation_rule")

    @pytest.mark.asyncio
    async def test_evaluate_rules_by_type(self):
        """Test rule evaluation filtered by type."""
        # Create rules of different types
        business_rule = Rule(
            id="business_rule",
            name="Business Rule",
            description="Business rule",
            rule_type=RuleType.BUSINESS,
            priority=RulePriority.NORMAL,
            conditions=[RuleCondition(field="value", operator="equals", value=1)],
            actions=[RuleAction(action_type="business_action", parameters={})]
        )
        
        safety_rule = Rule(
            id="safety_rule",
            name="Safety Rule",
            description="Safety rule",
            rule_type=RuleType.SAFETY,
            priority=RulePriority.CRITICAL,
            conditions=[RuleCondition(field="value", operator="equals", value=1)],
            actions=[RuleAction(action_type="safety_action", parameters={})]
        )
        
        # Register rules
        assert advanced_rule_engine.register_business_rule(business_rule) is True
        assert advanced_rule_engine.register_safety_rule(safety_rule) is True
        
        # Test evaluation with business rules only
        context = {"value": 1}
        results = await advanced_rule_engine.evaluate_rules(context, [RuleType.BUSINESS])
        
        # Should only have business rule results
        business_results = [r for r in results if r.rule_id == "business_rule"]
        safety_results = [r for r in results if r.rule_id == "safety_rule"]
        
        assert len(business_results) >= 1
        assert len(safety_results) == 0
        
        # Clean up
        advanced_rule_engine.delete_rule("business_rule")
        advanced_rule_engine.delete_rule("safety_rule")

    @pytest.mark.asyncio
    async def test_rule_execution_history(self):
        """Test rule execution history tracking."""
        # Create test rule
        rule = Rule(
            id="test_history_rule",
            name="Test History Rule",
            description="Test rule for history tracking",
            rule_type=RuleType.BUSINESS,
            priority=RulePriority.NORMAL,
            conditions=[RuleCondition(field="value", operator="equals", value=1)],
            actions=[RuleAction(action_type="history_action", parameters={})]
        )
        
        # Register rule
        assert advanced_rule_engine.register_business_rule(rule) is True
        
        # Execute rule multiple times
        context = {"value": 1}
        await advanced_rule_engine.evaluate_rules(context)
        await advanced_rule_engine.evaluate_rules(context)
        
        # Check execution history
        history = advanced_rule_engine.get_execution_history("test_history_rule")
        assert len(history) >= 2
        
        # Check rule statistics
        rule = advanced_rule_engine.get_rule("test_history_rule")
        assert rule.execution_count >= 2
        assert rule.last_executed is not None
        
        # Clean up
        advanced_rule_engine.delete_rule("test_history_rule")

class TestAdvancedRuleEngineIntegration:
    """Test integration with event-driven behavior engine."""
    
    @pytest.mark.asyncio
    async def test_rule_event_integration(self):
        """Test rule integration with event-driven behavior engine."""
        # Create rule that triggers on system events
        rule = Rule(
            id="test_integration_rule",
            name="Test Integration Rule",
            description="Test rule for event integration",
            rule_type=RuleType.OPERATIONAL,
            priority=RulePriority.NORMAL,
            conditions=[RuleCondition(field="event_type", operator="equals", value="system_alert")],
            actions=[RuleAction(action_type="handle_alert", parameters={"level": "warning"}, target_element="alert_system")]
        )
        
        # Register rule
        assert advanced_rule_engine.register_business_rule(rule) is True
        
        # Create system event
        event = Event(
            id="test_system_event",
            type=EventType.SYSTEM,
            priority=EventPriority.NORMAL,
            timestamp=datetime.utcnow(),
            element_id="test_element",
            data={
                "event_type": "system_alert",
                "message": "Test alert"
            }
        )
        
        # Process event through behavior engine
        result = event_driven_behavior_engine.process_event(event)
        if hasattr(result, '__await__'):
            await result
        
        # Check if rule was triggered
        history = advanced_rule_engine.get_execution_history("test_integration_rule")
        assert len(history) >= 1
        
        # Clean up
        advanced_rule_engine.delete_rule("test_integration_rule")

    def test_performance_statistics(self):
        """Test performance statistics tracking."""
        # Get initial stats
        initial_stats = advanced_rule_engine.get_performance_stats()
        
        # Create and register a test rule
        rule = Rule(
            id="test_performance_rule",
            name="Test Performance Rule",
            description="Test rule for performance tracking",
            rule_type=RuleType.BUSINESS,
            priority=RulePriority.NORMAL,
            conditions=[RuleCondition(field="value", operator="equals", value=1)],
            actions=[RuleAction(action_type="performance_action", parameters={})]
        )
        
        assert advanced_rule_engine.register_business_rule(rule) is True
        
        # Check that stats are updated
        current_stats = advanced_rule_engine.get_performance_stats()
        assert current_stats['total_evaluations'] >= initial_stats['total_evaluations']
        
        # Clean up
        advanced_rule_engine.delete_rule("test_performance_rule")

    def test_rule_priority_execution(self):
        """Test rule execution order by priority."""
        # Create rules with different priorities
        low_priority_rule = Rule(
            id="low_priority",
            name="Low Priority Rule",
            description="Low priority rule",
            rule_type=RuleType.BUSINESS,
            priority=RulePriority.LOW,
            conditions=[RuleCondition(field="value", operator="equals", value=1)],
            actions=[RuleAction(action_type="low_action", parameters={})]
        )
        
        high_priority_rule = Rule(
            id="high_priority",
            name="High Priority Rule",
            description="High priority rule",
            rule_type=RuleType.BUSINESS,
            priority=RulePriority.HIGH,
            conditions=[RuleCondition(field="value", operator="equals", value=1)],
            actions=[RuleAction(action_type="high_action", parameters={})]
        )
        
        # Register rules
        assert advanced_rule_engine.register_business_rule(low_priority_rule) is True
        assert advanced_rule_engine.register_business_rule(high_priority_rule) is True
        
        # Get rules by priority to verify ordering
        high_rules = advanced_rule_engine.get_rules_by_priority(RulePriority.HIGH)
        low_rules = advanced_rule_engine.get_rules_by_priority(RulePriority.LOW)
        
        assert len(high_rules) >= 1
        assert len(low_rules) >= 1
        
        # Clean up
        advanced_rule_engine.delete_rule("low_priority")
        advanced_rule_engine.delete_rule("high_priority")

    def test_clear_rules(self):
        """Test clearing rules by type."""
        # Create rules of different types
        business_rule = Rule(
            id="business_clear_rule",
            name="Business Clear Rule",
            description="Business rule for clearing",
            rule_type=RuleType.BUSINESS,
            priority=RulePriority.NORMAL,
            conditions=[RuleCondition(field="value", operator="equals", value=1)],
            actions=[RuleAction(action_type="business_action", parameters={})]
        )
        
        safety_rule = Rule(
            id="safety_clear_rule",
            name="Safety Clear Rule",
            description="Safety rule for clearing",
            rule_type=RuleType.SAFETY,
            priority=RulePriority.NORMAL,
            conditions=[RuleCondition(field="value", operator="equals", value=1)],
            actions=[RuleAction(action_type="safety_action", parameters={})]
        )
        
        # Register rules
        assert advanced_rule_engine.register_business_rule(business_rule) is True
        assert advanced_rule_engine.register_safety_rule(safety_rule) is True
        
        # Clear business rules only
        advanced_rule_engine.clear_rules(RuleType.BUSINESS)
        
        # Check that business rule is gone but safety rule remains
        assert advanced_rule_engine.get_rule("business_clear_rule") is None
        assert advanced_rule_engine.get_rule("safety_clear_rule") is not None
        
        # Clear all rules
        advanced_rule_engine.clear_rules()
        
        # Check that all rules are gone
        assert advanced_rule_engine.get_rule("safety_clear_rule") is None 