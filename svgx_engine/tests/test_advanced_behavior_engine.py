"""
Test suite for SVGX Advanced Behavior Engine.

This module tests the advanced behavior engine features including:
- Rule engines with complex logic evaluation
- State machines with transition management
- Time-based triggers and scheduling
- Advanced condition evaluation
- CAD-parity behaviors
- Infrastructure simulation behaviors
"""

import pytest
import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add the parent directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from runtime.advanced_behavior_engine import (
    AdvancedBehaviorEngine,
    BehaviorRule,
    BehaviorState,
    TimeTrigger,
    Condition,
    BehaviorType,
    StateType,
    RuleType,
    TriggerType
)
from svgx_engine.runtime.behavior.ui_event_schemas import (
    SelectionEvent, EditingEvent, NavigationEvent, AnnotationEvent, SelectionPayload, EditingPayload, NavigationPayload, AnnotationPayload
)

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestAdvancedBehaviorEngine:
    """Test suite for AdvancedBehaviorEngine."""
    
    @pytest.fixture
    def behavior_engine(self):
        """Create a behavior engine instance for testing."""
        return AdvancedBehaviorEngine()
    
    @pytest.fixture
    def sample_context(self):
        """Create sample context for testing."""
        return {
            'element_id': 'test_element',
            'position': {'x': 10, 'y': 20, 'z': 0},
            'temperature': 25.5,
            'pressure': 101.3,
            'status': 'active',
            'timestamp': datetime.now(),
            'dependencies': {'parent_element': 'active'},
            'connections': ['connection1', 'connection2'],
            'parent': 'parent_element'
        }
    
    @pytest.fixture
    def sample_rule(self):
        """Create a sample behavior rule."""
        return BehaviorRule(
            rule_id='test_rule_1',
            rule_type=RuleType.SAFETY,
            conditions=[
                {
                    'type': 'threshold',
                    'variable': 'temperature',
                    'operator': '>',
                    'threshold': 30.0
                },
                {
                    'type': 'simple',
                    'variable': 'status',
                    'operator': '==',
                    'value': 'active'
                }
            ],
            actions=[
                {
                    'type': 'update',
                    'target_property': 'alert_level',
                    'value': 'high'
                },
                {
                    'type': 'log',
                    'message': 'Temperature threshold exceeded',
                    'level': 'warning'
                }
            ],
            priority=2,
            metadata={'target_elements': ['test_element']}
        )
    
    @pytest.fixture
    def sample_state_machine(self):
        """Create a sample state machine."""
        states = [
            BehaviorState(
                state_id='off',
                state_type=StateType.EQUIPMENT,
                properties={'power': False, 'status': 'inactive'},
                transitions=[
                    {
                        'target_state': 'on',
                        'conditions': [
                            {
                                'type': 'simple',
                                'variable': 'power_command',
                                'operator': '==',
                                'value': 'start'
                            }
                        ]
                    }
                ],
                entry_actions=[
                    {
                        'type': 'update',
                        'target_property': 'power_status',
                        'value': 'off'
                    }
                ],
                exit_actions=[
                    {
                        'type': 'log',
                        'message': 'Equipment shutting down',
                        'level': 'info'
                    }
                ]
            ),
            BehaviorState(
                state_id='on',
                state_type=StateType.EQUIPMENT,
                properties={'power': True, 'status': 'active'},
                transitions=[
                    {
                        'target_state': 'off',
                        'conditions': [
                            {
                                'type': 'simple',
                                'variable': 'power_command',
                                'operator': '==',
                                'value': 'stop'
                            }
                        ]
                    },
                    {
                        'target_state': 'error',
                        'conditions': [
                            {
                                'type': 'threshold',
                                'variable': 'temperature',
                                'operator': '>',
                                'threshold': 80.0
                            }
                        ]
                    }
                ],
                entry_actions=[
                    {
                        'type': 'update',
                        'target_property': 'power_status',
                        'value': 'on'
                    },
                    {
                        'type': 'log',
                        'message': 'Equipment starting up',
                        'level': 'info'
                    }
                ],
                exit_actions=[
                    {
                        'type': 'log',
                        'message': 'Equipment stopping',
                        'level': 'info'
                    }
                ]
            ),
            BehaviorState(
                state_id='error',
                state_type=StateType.EQUIPMENT,
                properties={'power': False, 'status': 'error'},
                transitions=[
                    {
                        'target_state': 'off',
                        'conditions': [
                            {
                                'type': 'simple',
                                'variable': 'reset_command',
                                'operator': '==',
                                'value': 'reset'
                            }
                        ]
                    }
                ],
                entry_actions=[
                    {
                        'type': 'update',
                        'target_property': 'power_status',
                        'value': 'error'
                    },
                    {
                        'type': 'log',
                        'message': 'Equipment error detected',
                        'level': 'error'
                    }
                ]
            )
        ]
        return states
    
    @pytest.fixture
    def sample_time_trigger(self):
        """Create a sample time trigger."""
        return TimeTrigger(
            trigger_id='test_trigger_1',
            schedule_type='cyclic',
            schedule_data={
                'interval': 3600,  # 1 hour
                'start_time': datetime.now()
            },
            actions=[
                {
                    'type': 'update',
                    'target_property': 'last_maintenance_check',
                    'value': datetime.now().isoformat()
                },
                {
                    'type': 'log',
                    'message': 'Scheduled maintenance check',
                    'level': 'info'
                }
            ]
        )
    
    @pytest.fixture
    def sample_condition(self):
        """Create a sample complex condition."""
        return Condition(
            condition_id='test_condition_1',
            condition_type='complex',
            expression='temperature > 30 and pressure < 95',
            parameters={'temperature': 35, 'pressure': 90},
            operators=['and', 'or']
        )

    def test_behavior_engine_initialization(self, behavior_engine):
        """Test behavior engine initialization."""
        assert behavior_engine is not None
        assert len(behavior_engine.rules) == 0
        assert len(behavior_engine.state_machines) == 0
        assert len(behavior_engine.time_triggers) == 0
        assert len(behavior_engine.conditions) == 0
        assert not behavior_engine.running

    def test_register_rule(self, behavior_engine, sample_rule):
        """Test rule registration."""
        behavior_engine.register_rule(sample_rule)
        
        assert 'test_rule_1' in behavior_engine.rules
        assert behavior_engine.rules['test_rule_1'] == sample_rule
        assert len(behavior_engine.get_registered_rules()) == 1

    def test_register_state_machine(self, behavior_engine, sample_state_machine):
        """Test state machine registration."""
        element_id = 'test_equipment'
        initial_state = 'off'
        
        behavior_engine.register_state_machine(element_id, sample_state_machine, initial_state)
        
        assert element_id in behavior_engine.state_machines
        assert len(behavior_engine.state_machines[element_id]) == 3
        assert behavior_engine.get_element_state(element_id) == initial_state
        assert len(behavior_engine.get_registered_state_machines()) == 1

    def test_register_time_trigger(self, behavior_engine, sample_time_trigger):
        """Test time trigger registration."""
        behavior_engine.register_time_trigger(sample_time_trigger)
        
        assert 'test_trigger_1' in behavior_engine.time_triggers
        assert behavior_engine.time_triggers['test_trigger_1'] == sample_time_trigger
        assert len(behavior_engine.get_registered_time_triggers()) == 1

    def test_register_condition(self, behavior_engine, sample_condition):
        """Test condition registration."""
        behavior_engine.register_condition(sample_condition)
        
        assert 'test_condition_1' in behavior_engine.conditions
        assert behavior_engine.conditions['test_condition_1'] == sample_condition

    @pytest.mark.asyncio
    async def test_evaluate_rules_simple(self, behavior_engine, sample_rule, sample_context):
        """Test simple rule evaluation."""
        behavior_engine.register_rule(sample_rule)
        
        # Test with conditions that should match
        sample_context['temperature'] = 35.0
        sample_context['status'] = 'active'
        
        applicable_rules = await behavior_engine.evaluate_rules('test_element', sample_context)
        
        assert len(applicable_rules) == 1
        assert applicable_rules[0]['rule_id'] == 'test_rule_1'
        assert applicable_rules[0]['rule_type'] == 'safety'
        assert applicable_rules[0]['priority'] == 2

    @pytest.mark.asyncio
    async def test_evaluate_rules_no_match(self, behavior_engine, sample_rule, sample_context):
        """Test rule evaluation when conditions don't match."""
        behavior_engine.register_rule(sample_rule)
        
        # Test with conditions that shouldn't match
        sample_context['temperature'] = 25.0  # Below threshold
        sample_context['status'] = 'active'
        
        applicable_rules = await behavior_engine.evaluate_rules('test_element', sample_context)
        
        assert len(applicable_rules) == 0

    @pytest.mark.asyncio
    async def test_evaluate_rules_priority(self, behavior_engine, sample_context):
        """Test rule evaluation with priority ordering."""
        # Create multiple rules with different priorities
        rule1 = BehaviorRule(
            rule_id='low_priority',
            rule_type=RuleType.BUSINESS,
            conditions=[{'type': 'simple', 'variable': 'status', 'operator': '==', 'value': 'active'}],
            actions=[{'type': 'log', 'message': 'Low priority action', 'level': 'info'}],
            priority=1
        )
        
        rule2 = BehaviorRule(
            rule_id='high_priority',
            rule_type=RuleType.SAFETY,
            conditions=[{'type': 'simple', 'variable': 'status', 'operator': '==', 'value': 'active'}],
            actions=[{'type': 'log', 'message': 'High priority action', 'level': 'warning'}],
            priority=3
        )
        
        behavior_engine.register_rule(rule1)
        behavior_engine.register_rule(rule2)
        
        applicable_rules = await behavior_engine.evaluate_rules('test_element', sample_context)
        
        assert len(applicable_rules) == 2
        assert applicable_rules[0]['rule_id'] == 'high_priority'  # Higher priority first
        assert applicable_rules[1]['rule_id'] == 'low_priority'

    @pytest.mark.asyncio
    async def test_state_transition_valid(self, behavior_engine, sample_state_machine):
        """Test valid state transition."""
        element_id = 'test_equipment'
        behavior_engine.register_state_machine(element_id, sample_state_machine, 'off')
        
        # Test transition from 'off' to 'on'
        context = {'power_command': 'start'}
        await behavior_engine.execute_state_transition(element_id, 'on', context)
        
        assert behavior_engine.get_element_state(element_id) == 'on'

    @pytest.mark.asyncio
    async def test_state_transition_invalid(self, behavior_engine, sample_state_machine):
        """Test invalid state transition."""
        element_id = 'test_equipment'
        behavior_engine.register_state_machine(element_id, sample_state_machine, 'off')
        
        # Test transition that doesn't meet conditions
        context = {'power_command': 'invalid'}
        await behavior_engine.execute_state_transition(element_id, 'on', context)
        
        # State should remain unchanged
        assert behavior_engine.get_element_state(element_id) == 'off'

    @pytest.mark.asyncio
    async def test_state_transition_with_actions(self, behavior_engine, sample_state_machine):
        """Test state transition with entry/exit actions."""
        element_id = 'test_equipment'
        behavior_engine.register_state_machine(element_id, sample_state_machine, 'off')
        
        # Mock the action execution by capturing log messages
        with pytest.MonkeyPatch().context() as m:
            log_messages = []
            def mock_log(level, message):
                log_messages.append(f"{level}: {message}")
            
            m.setattr(behavior_engine, '_execute_actions', mock_log)
            
            # Execute transition
            context = {'power_command': 'start'}
            await behavior_engine.execute_state_transition(element_id, 'on', context)
            
            # Check that actions were executed
            assert behavior_engine.get_element_state(element_id) == 'on'

    @pytest.mark.asyncio
    async def test_time_trigger_execution(self, behavior_engine, sample_time_trigger):
        """Test time trigger execution."""
        behavior_engine.register_time_trigger(sample_time_trigger)
        
        # Set next execution to now
        sample_time_trigger.next_execution = datetime.now()
        
        await behavior_engine.execute_time_triggers()
        
        # Check that trigger was executed
        assert sample_time_trigger.last_execution is not None

    def test_threshold_condition_evaluation(self, behavior_engine, sample_context):
        """Test threshold condition evaluation."""
        condition = {
            'type': 'threshold',
            'variable': 'temperature',
            'operator': '>',
            'threshold': 30.0
        }
        
        # Test condition that should be true
        sample_context['temperature'] = 35.0
        assert behavior_engine._evaluate_single_condition(condition, sample_context) is True
        
        # Test condition that should be false
        sample_context['temperature'] = 25.0
        assert behavior_engine._evaluate_single_condition(condition, sample_context) is False

    def test_time_condition_evaluation(self, behavior_engine, sample_context):
        """Test time condition evaluation."""
        current_time = datetime.now()
        condition = {
            'type': 'time',
            'time_type': 'current',
            'start_time': current_time - timedelta(hours=1),
            'end_time': current_time + timedelta(hours=1)
        }
        
        assert behavior_engine._evaluate_single_condition(condition, sample_context) is True
        
        # Test condition outside time range
        condition['start_time'] = current_time + timedelta(hours=1)
        assert behavior_engine._evaluate_single_condition(condition, sample_context) is False

    def test_spatial_condition_evaluation(self, behavior_engine, sample_context):
        """Test spatial condition evaluation."""
        condition = {
            'type': 'spatial',
            'spatial_type': 'proximity',
            'target_position': {'x': 10, 'y': 20, 'z': 0},
            'max_distance': 5.0
        }
        
        # Test condition that should be true (positions are the same)
        assert behavior_engine._evaluate_single_condition(condition, sample_context) is True
        
        # Test condition that should be false (positions are far apart)
        sample_context['position'] = {'x': 100, 'y': 200, 'z': 0}
        assert behavior_engine._evaluate_single_condition(condition, sample_context) is False

    def test_relational_condition_evaluation(self, behavior_engine, sample_context):
        """Test relational condition evaluation."""
        condition = {
            'type': 'relational',
            'relation_type': 'dependency',
            'dependent_element': 'parent_element',
            'required_status': 'active'
        }
        
        # Test condition that should be true
        assert behavior_engine._evaluate_single_condition(condition, sample_context) is True
        
        # Test condition that should be false
        sample_context['dependencies']['parent_element'] = 'inactive'
        assert behavior_engine._evaluate_single_condition(condition, sample_context) is False

    def test_complex_condition_evaluation(self, behavior_engine, sample_context):
        """Test complex condition evaluation."""
        condition = {
            'type': 'complex',
            'expression': 'temperature > 30 and pressure < 95',
            'variables': {'temperature': 35, 'pressure': 90}
        }
        
        # Test condition that should be true
        sample_context['temperature'] = 35
        sample_context['pressure'] = 90
        assert behavior_engine._evaluate_single_condition(condition, sample_context) is True
        
        # Test condition that should be false
        sample_context['temperature'] = 25
        assert behavior_engine._evaluate_single_condition(condition, sample_context) is False

    def test_simple_condition_evaluation(self, behavior_engine, sample_context):
        """Test simple condition evaluation."""
        condition = {
            'type': 'simple',
            'variable': 'status',
            'operator': '==',
            'value': 'active'
        }
        
        # Test condition that should be true
        assert behavior_engine._evaluate_single_condition(condition, sample_context) is True
        
        # Test condition that should be false
        sample_context['status'] = 'inactive'
        assert behavior_engine._evaluate_single_condition(condition, sample_context) is False

    def test_cad_parity_action_execution(self, behavior_engine):
        """Test CAD-parity action execution."""
        action = {
            'type': 'cad_parity',
            'cad_action_type': 'dimension',
            'dimension_type': 'linear'
        }
        
        # Mock the action execution
        with pytest.MonkeyPatch().context() as m:
            executed_actions = []
            def mock_execute(action_type, element_id, context):
                executed_actions.append(action_type)
            
            m.setattr(behavior_engine, '_execute_dimension_action', mock_execute)
            
            # Execute action
            asyncio.run(behavior_engine._execute_cad_parity_action(action, 'test_element', {}))
            
            # Check that action was executed
            assert 'dimension' in executed_actions

    def test_infrastructure_action_execution(self, behavior_engine):
        """Test infrastructure action execution."""
        action = {
            'type': 'infrastructure',
            'system_type': 'hvac',
            'hvac_action': 'temperature_control'
        }
        
        # Mock the action execution
        with pytest.MonkeyPatch().context() as m:
            executed_actions = []
            def mock_execute(action_type, element_id, context):
                executed_actions.append(action_type)
            
            m.setattr(behavior_engine, '_execute_hvac_action', mock_execute)
            
            # Execute action
            asyncio.run(behavior_engine._execute_infrastructure_action(action, 'test_element', {}))
            
            # Check that action was executed
            assert 'temperature_control' in executed_actions

    def test_utility_methods(self, behavior_engine):
        """Test utility methods."""
        # Test distance calculation
        pos1 = {'x': 0, 'y': 0, 'z': 0}
        pos2 = {'x': 3, 'y': 4, 'z': 0}
        distance = behavior_engine._calculate_distance(pos1, pos2)
        assert distance == 5.0
        
        # Test point in boundary
        point = {'x': 5, 'y': 5}
        boundary = {'min_x': 0, 'max_x': 10, 'min_y': 0, 'max_y': 10}
        assert behavior_engine._is_point_in_boundary(point, boundary) is True
        
        # Test bounds intersection
        bounds1 = {'min_x': 0, 'max_x': 5, 'min_y': 0, 'max_y': 5}
        bounds2 = {'min_x': 3, 'max_x': 8, 'min_y': 3, 'max_y': 8}
        assert behavior_engine._do_bounds_intersect(bounds1, bounds2) is True

    def test_behavior_engine_lifecycle(self, behavior_engine):
        """Test behavior engine start/stop lifecycle."""
        assert not behavior_engine.running
        
        behavior_engine.start()
        assert behavior_engine.running
        
        behavior_engine.stop()
        assert not behavior_engine.running

    @pytest.mark.asyncio
    async def test_event_handling(self, behavior_engine):
        """Test event handling."""
        # Register a rule that responds to user interaction
        rule = BehaviorRule(
            rule_id='interaction_rule',
            rule_type=RuleType.OPERATIONAL,
            conditions=[{'type': 'simple', 'variable': 'event_type', 'operator': '==', 'value': 'user_interaction'}],
            actions=[{'type': 'log', 'message': 'User interaction detected', 'level': 'info'}]
        )
        behavior_engine.register_rule(rule)
        
        # Handle a user interaction event
        event_data = {'type': 'click', 'position': {'x': 100, 'y': 200}}
        await behavior_engine._handle_event('test_element', 'user_interaction', event_data)
        
        # Verify rule was evaluated (would need to mock action execution to verify)

    def test_condition_registration_and_retrieval(self, behavior_engine, sample_condition):
        """Test condition registration and retrieval."""
        behavior_engine.register_condition(sample_condition)
        
        assert 'test_condition_1' in behavior_engine.conditions
        retrieved_condition = behavior_engine.conditions['test_condition_1']
        assert retrieved_condition.condition_id == 'test_condition_1'
        assert retrieved_condition.condition_type == 'complex'
        assert retrieved_condition.expression == 'temperature > 30 and pressure < 95'

    def test_rule_metadata_handling(self, behavior_engine):
        """Test rule metadata handling."""
        rule = BehaviorRule(
            rule_id='metadata_test',
            rule_type=RuleType.BUSINESS,
            conditions=[],
            actions=[],
            metadata={
                'target_elements': ['element1', 'element2'],
                'element_types': ['equipment', 'sensor'],
                'description': 'Test rule with metadata'
            }
        )
        
        behavior_engine.register_rule(rule)
        
        # Test element targeting
        context = {'element_id': 'element1', 'element_type': 'equipment'}
        assert behavior_engine._rule_applies_to_element(rule, 'element1', context) is True
        assert behavior_engine._rule_applies_to_element(rule, 'element3', context) is False

    def test_time_trigger_scheduling(self, behavior_engine):
        """Test time trigger scheduling calculations."""
        trigger = TimeTrigger(
            trigger_id='schedule_test',
            schedule_type='cyclic',
            schedule_data={'interval': 3600},  # 1 hour
            actions=[]
        )
        
        behavior_engine.register_time_trigger(trigger)
        
        # Verify next execution was calculated
        assert trigger.next_execution is not None
        assert trigger.next_execution > datetime.now()

    def test_state_machine_properties(self, behavior_engine, sample_state_machine):
        """Test state machine property handling."""
        element_id = 'test_equipment'
        behavior_engine.register_state_machine(element_id, sample_state_machine, 'off')
        
        # Get current state properties
        current_state_id = behavior_engine.get_element_state(element_id)
        current_state = behavior_engine.state_machines[element_id][current_state_id]
        
        assert current_state.properties['power'] is False
        assert current_state.properties['status'] == 'inactive'

    def test_behavior_engine_error_handling(self, behavior_engine):
        """Test error handling in behavior engine."""
        # Test invalid rule registration
        invalid_rule = None
        behavior_engine.register_rule(invalid_rule)  # Should handle gracefully
        
        # Test invalid state machine registration
        behavior_engine.register_state_machine('test', [], 'invalid_state')  # Should handle gracefully
        
        # Test invalid condition evaluation
        invalid_condition = {'type': 'invalid_type'}
        result = behavior_engine._evaluate_single_condition(invalid_condition, {})
        assert result is False  # Should return False for invalid conditions

    def test_comprehensive_behavior_scenario(self, behavior_engine):
        """Test a comprehensive behavior scenario."""
        # Create a complex scenario with multiple rules, states, and triggers
        element_id = 'complex_equipment'
        
        # Register multiple rules
        safety_rule = BehaviorRule(
            rule_id='safety_rule',
            rule_type=RuleType.SAFETY,
            conditions=[{'type': 'threshold', 'variable': 'temperature', 'operator': '>', 'threshold': 80}],
            actions=[{'type': 'update', 'target_property': 'alert', 'value': 'critical'}],
            priority=3
        )
        
        operational_rule = BehaviorRule(
            rule_id='operational_rule',
            rule_type=RuleType.OPERATIONAL,
            conditions=[{'type': 'simple', 'variable': 'status', 'operator': '==', 'value': 'active'}],
            actions=[{'type': 'log', 'message': 'Equipment operational', 'level': 'info'}],
            priority=1
        )
        
        behavior_engine.register_rule(safety_rule)
        behavior_engine.register_rule(operational_rule)
        
        # Test scenario with high temperature
        context = {
            'element_id': element_id,
            'temperature': 85,
            'status': 'active'
        }
        
        # Evaluate rules
        applicable_rules = asyncio.run(behavior_engine.evaluate_rules(element_id, context))
        
        # Should have both rules applicable, safety rule first due to priority
        assert len(applicable_rules) == 2
        assert applicable_rules[0]['rule_id'] == 'safety_rule'
        assert applicable_rules[1]['rule_id'] == 'operational_rule'


@pytest.fixture
def engine():
    return AdvancedBehaviorEngine()

def test_handle_selection_event(engine):
    event = SelectionEvent(
        event_type="selection",
        timestamp=datetime.utcnow(),
        session_id="s1",
        user_id="u1",
        canvas_id="c1",
        payload=SelectionPayload(selection_mode="single", selected_ids=["obj1"], selection_origin=None, modifiers=None)
    )
    feedback = engine._handle_selection_event(event)
    assert feedback["status"] == "updated"
    assert engine.get_selection_state("c1") == ["obj1"]

def test_handle_editing_event(engine):
    event = EditingEvent(
        event_type="editing",
        timestamp=datetime.utcnow(),
        session_id="s1",
        user_id="u1",
        canvas_id="c1",
        payload=EditingPayload(target_id="obj1", edit_type="move", before={"position": {"x": 0, "y": 0}}, after={"position": {"x": 1, "y": 2}}, property_changed=None)
    )
    feedback = engine._handle_editing_event(event)
    assert feedback["status"] == "edited"
    assert engine.edit_history["c1"][-1]["edit_type"] == "move"

def test_handle_navigation_event(engine):
    event = NavigationEvent(
        event_type="navigation",
        timestamp=datetime.utcnow(),
        session_id="s1",
        user_id="u1",
        canvas_id="c1",
        payload=NavigationPayload(action="zoom", zoom_level=2.0, camera_position=None, target_object_id=None, floor_id=None)
    )
    feedback = engine._handle_navigation_event(event)
    assert feedback["status"] == "navigation_updated"
    assert engine.get_navigation_state("c1")["zoom_level"] == 2.0

def test_handle_annotation_event(engine):
    event = AnnotationEvent(
        event_type="annotation",
        timestamp=datetime.utcnow(),
        session_id="s1",
        user_id="u1",
        canvas_id="c1",
        payload=AnnotationPayload(target_id="obj2", annotation_type="note", content="Test", location={"x": 1, "y": 2}, media=None, tag=["t"])
    )
    feedback = engine._handle_annotation_event(event)
    assert feedback["status"] == "annotation_added"
    ann = engine.get_annotations("c1")["obj2"]
    assert ann[-1]["type"] == "note"
    assert ann[-1]["content"] == "Test"


if __name__ == '__main__':
    pytest.main([__file__]) 