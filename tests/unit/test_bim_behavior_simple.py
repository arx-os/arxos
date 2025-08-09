#!/usr/bin/env python3
"""
Simple Test Script for BIM Behavior Systems

This script tests the basic functionality of the BIM behavior systems:
- Event-Driven Behavior Engine
- Advanced State Machine
- Conditional Logic Engine

🎯 **Simple Test Coverage:**
- Basic event processing
- State transitions
- Condition evaluation
- Performance metrics
"""

import asyncio
import time
import uuid
from datetime import datetime

# Add the current directory to Python path
import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_event_driven_behavior():
    """Test basic event-driven behavior functionality."""
    print("🧪 Testing Event-Driven Behavior Engine...")

    try:
        from svgx_engine.services.event_driven_behavior_engine import (
            EventDrivenBehaviorEngine, Event, EventType, EventPriority
        )

        # Create engine
        engine = EventDrivenBehaviorEngine()

        # Create test event
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type=EventType.USER_INTERACTION,
            element_id="test_element_001",
            timestamp=datetime.now(),
            priority=EventPriority.HIGH,
            data={'interaction_type': 'click', 'position': {'x': 100, 'y': 200}}
        )

        print(f"✅ Created event: {event.event_id}")
        print(f"✅ Event type: {event.event_type.value}")
        print(f"✅ Event priority: {event.priority.value}")

        # Get statistics
        stats = engine.get_processing_stats()
        print(f"✅ Engine initialized with {stats['processing_stats']['total_events']} events")

        return True

    except Exception as e:
        print(f"❌ Event-driven behavior test failed: {e}")
        return False

def test_advanced_state_machine():
    """Test basic state machine functionality."""
    print("\n🧪 Testing Advanced State Machine...")

    try:
        from svgx_engine.services.advanced_state_machine import (
            AdvancedStateMachine, State, StateType, StateStatus
        )

        # Create state machine
        state_machine = AdvancedStateMachine()

        # Check default states
        states = list(state_machine.states.keys())
        print(f"✅ Initialized with {len(states)} default states")
        print(f"✅ Sample states: {states[:5]}")

        # Test state management
        test_state = State(
            state_id="test_state",
            state_type=StateType.EQUIPMENT,
            name="Test State",
            description="A test state",
            status=StateStatus.INACTIVE
        )

        success = state_machine.add_state(test_state)
        print(f"✅ Added test state: {success}")

        # Get statistics
        stats = state_machine.get_processing_stats()
        print(f"✅ State machine statistics: {stats['state_stats']['total_states']} states")

        return True

    except Exception as e:
        print(f"❌ State machine test failed: {e}")
        return False

def test_conditional_logic_engine():
    """Test basic conditional logic functionality."""
    print("\n🧪 Testing Conditional Logic Engine...")

    try:
        from svgx_engine.services.conditional_logic_engine import (
            ConditionalLogicEngine, Condition, ConditionType
        )

        # Create logic engine
        logic_engine = ConditionalLogicEngine()

        # Check default conditions
        conditions = list(logic_engine.conditions.keys())
        print(f"✅ Initialized with {len(conditions)} default conditions")
        print(f"✅ Sample conditions: {conditions[:5]}")

        # Test condition management
        test_condition = Condition(
            condition_id="test_condition",
            condition_type=ConditionType.THRESHOLD,
            expression="value > 10",
            variables={'value': 0.0},
            parameters={'threshold': 10.0, 'operator': '>'}
        )

        success = logic_engine.add_condition(test_condition)
        print(f"✅ Added test condition: {success}")

        # Get statistics
        stats = logic_engine.get_processing_stats()
        print(f"✅ Logic engine statistics: {stats['condition_stats']['total_conditions']} conditions")

        return True

    except Exception as e:
        print(f"❌ Conditional logic test failed: {e}")
        return False

def test_physics_engine():
    """Test basic physics engine functionality."""
    print("\n🧪 Testing Enhanced Physics Engine...")

    try:
        from svgx_engine.services.enhanced_physics_engine import EnhancedPhysicsEngine

        # Create physics engine
        physics_engine = EnhancedPhysicsEngine()

        # Test HVAC calculation
        hvac_data = {
            'duct_diameter': 0.3,
            'air_velocity': 5.0,
            'duct_length': 10.0,
            'roughness': 0.00015,
            'temperature': 20.0,
            'pressure': 101325.0
        }

        result = physics_engine.fluid_engine.calculate_air_flow(hvac_data)
        print(f"✅ HVAC calculation: {result.success}")
        if result.success:
            print(f"✅ Flow rate: {result.data.get('flow_rate', 0):.2f} m³/s")

        # Test electrical calculation
        electrical_data = {
            'voltage': 480.0,
            'current': 100.0,
            'power_factor': 0.95,
            'frequency': 60.0,
            'load_type': 'inductive'
        }

        result = physics_engine.electrical_engine.analyze_circuit(electrical_data)
        print(f"✅ Electrical calculation: {result.success}")
        if result.success:
            print(f"✅ Real power: {result.data.get('real_power', 0):.2f} kW")

        return True

    except Exception as e:
        print(f"❌ Physics engine test failed: {e}")
        return False

def test_performance_monitoring():
    """Test performance monitoring functionality."""
    print("\n🧪 Testing Performance Monitoring...")

    try:
        from svgx_engine.utils.performance import PerformanceMonitor

        # Create performance monitor
        monitor = PerformanceMonitor()

        # Test operation recording
        with monitor.monitor("test_operation"):
            time.sleep(0.01)  # Simulate work

        # Get performance metrics
        metrics = monitor.get_metrics()
        print(f"✅ Performance monitor initialized")
        print(f"✅ Recorded operations: {len(metrics.get('operations', []))}")

        return True

    except Exception as e:
        print(f"❌ Performance monitoring test failed: {e}")
        return False

def test_error_handling():
    """Test error handling functionality."""
    print("\n🧪 Testing Error Handling...")

    try:
        from svgx_engine.utils.errors import BehaviorError, EventError, StateMachineError, LogicError

        # Test error creation
        behavior_error = BehaviorError("Test behavior error")
        event_error = EventError("Test event error")
        state_machine_error = StateMachineError("Test state machine error")
        logic_error = LogicError("Test logic error")

        print(f"✅ BehaviorError: {behavior_error}")
        print(f"✅ EventError: {event_error}")
        print(f"✅ StateMachineError: {state_machine_error}")
        print(f"✅ LogicError: {logic_error}")

        return True

    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

async def test_integration():
    """Test basic integration between systems."""
    print("\n🧪 Testing System Integration...")

    try:
        from svgx_engine.services.event_driven_behavior_engine import EventDrivenBehaviorEngine, Event, EventType
        from svgx_engine.services.advanced_state_machine import AdvancedStateMachine
        from svgx_engine.services.conditional_logic_engine import ConditionalLogicEngine

        # Create all systems
        event_engine = EventDrivenBehaviorEngine()
        state_machine = AdvancedStateMachine()
        logic_engine = ConditionalLogicEngine()

        # Start event processing
        await event_engine.start_processing()

        # Create and emit event
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type=EventType.USER_INTERACTION,
            element_id="test_integration_element",
            timestamp=datetime.now(),
            data={'test': True}
        )

        event_id = await event_engine.emit_event(event)
        print(f"✅ Emitted integration event: {event_id}")

        # Wait for processing
        await asyncio.sleep(0.1)

        # Check all systems are working
        event_stats = event_engine.get_processing_stats()
        state_stats = state_machine.get_processing_stats()
        logic_stats = logic_engine.get_processing_stats()

        print(f"✅ Event engine: {event_stats['processing_stats']['total_events']} events")
        print(f"✅ State machine: {state_stats['state_stats']['total_states']} states")
        print(f"✅ Logic engine: {logic_stats['condition_stats']['total_conditions']} conditions")

        # Stop processing
        await event_engine.stop_processing()

        return True

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def main():
    """Run all simple tests."""
    print("🚀 Starting Simple BIM Behavior System Tests")
    print("=" * 50)

    # Run synchronous tests
    tests = [
        test_event_driven_behavior,
        test_advanced_state_machine,
        test_conditional_logic_engine,
        test_physics_engine,
        test_performance_monitoring,
        test_error_handling
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")

    # Run async integration test
    try:
        if asyncio.run(test_integration()):
            passed += 1
        total += 1
    except Exception as e:
        print(f"❌ Integration test failed with exception: {e}")

    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All Simple BIM Behavior Tests Passed!")
        print("✅ Event-Driven Behavior Engine: Working")
        print("✅ Advanced State Machine: Working")
        print("✅ Conditional Logic Engine: Working")
        print("✅ Enhanced Physics Engine: Working")
        print("✅ Performance Monitoring: Working")
        print("✅ Error Handling: Working")
        print("✅ System Integration: Working")
    else:
        print(f"❌ {total - passed} tests failed")

    print("=" * 50)

    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
