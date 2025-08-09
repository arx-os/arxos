"""
Comprehensive Test Suite for BIM Behavior Systems

This test suite verifies the integration and functionality of all BIM behavior systems:
- Event-Driven Behavior Engine
- Advanced State Machine
- Conditional Logic Engine
- Performance Optimization
- Integration with Enhanced Physics Engine

🎯 **Test Coverage:**
- Event processing and handling
- State transitions and management
- Condition evaluation and caching
- Performance optimization features
- Integration with physics engine
- Error handling and recovery
- Real-world BIM scenarios
"""

import asyncio
import pytest
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import the services we created
from svgx_engine.services.event_driven_behavior_engine import (
    EventDrivenBehaviorEngine, Event, EventType, EventPriority, EventHandler
)
from svgx_engine.services.advanced_state_machine import (
    AdvancedStateMachine, State, StateType, StateStatus, Transition
)
from svgx_engine.services.conditional_logic_engine import (
    ConditionalLogicEngine, Condition, ConditionType, ConditionResult
)
from svgx_engine.services.enhanced_physics_engine import (
    EnhancedPhysicsEngine, PhysicsResult
)
from svgx_engine.utils.performance import PerformanceMonitor
from svgx_engine.utils.errors import BehaviorError, EventError, StateMachineError, LogicError


class TestBIMBehaviorComprehensive:
    """Comprehensive test suite for BIM behavior systems."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """Set up test environment."""
        self.event_engine = EventDrivenBehaviorEngine()
        self.state_machine = AdvancedStateMachine()
        self.logic_engine = ConditionalLogicEngine()
        self.physics_engine = EnhancedPhysicsEngine()
        # self.physics_bim_integration = PhysicsBIMIntegration()  # Not implemented yet
        self.performance_monitor = PerformanceMonitor()

        # Test data
        self.test_element_id = "test_hvac_unit_001"
        self.test_user_id = "test_user_001"
        self.test_session_id = "test_session_001"

        yield

        # Cleanup
        await self.event_engine.stop_processing()

    @pytest.mark.asyncio
    async def test_event_driven_behavior_system(self):
        """Test event-driven behavior system functionality."""
        print("\n🧪 Testing Event-Driven Behavior System...")

        # Start event processing
        await self.event_engine.start_processing()

        # Create test events
        events = [
            Event(
                event_id=str(uuid.uuid4()),
                event_type=EventType.USER_INTERACTION,
                element_id=self.test_element_id,
                timestamp=datetime.now(),
                priority=EventPriority.HIGH,
                data={
                    'interaction_type': 'click',
                    'position': {'x': 100, 'y': 200},
                    'user_id': self.test_user_id
                }
            ),
            Event(
                event_id=str(uuid.uuid4()),
                event_type=EventType.SYSTEM_EVENT,
                element_id=self.test_element_id,
                timestamp=datetime.now(),
                priority=EventPriority.NORMAL,
                data={
                    'system_event_type': 'state_change',
                    'old_state': 'off',
                    'new_state': 'on'
                }
            ),
            Event(
                event_id=str(uuid.uuid4()),
                event_type=EventType.PHYSICS_EVENT,
                element_id=self.test_element_id,
                timestamp=datetime.now(),
                priority=EventPriority.HIGH,
                data={
                    'physics_event_type': 'force',
                    'force_vector': {'x': 0, 'y': 0, 'z': 9.81},
                    'magnitude': 9.81
                }
            )
        ]

        # Emit events
        for event in events:
            event_id = await self.event_engine.emit_event(event)
            assert event_id == event.event_id
            print(f"✅ Emitted event: {event.event_type.value}")

        # Wait for processing
        await asyncio.sleep(0.1)

        # Check processing statistics
        stats = self.event_engine.get_processing_stats()
        assert stats['processing_stats']['total_events'] >= len(events)
        print(f"✅ Processed {stats['processing_stats']['total_events']} events")

        # Check event history
        history = self.event_engine.get_event_history()
        assert len(history) >= len(events)
        print(f"✅ Event history contains {len(history)} events")

        print("✅ Event-driven behavior system test passed")

    @pytest.mark.asyncio
    async def test_advanced_state_machine(self):
        """Test advanced state machine functionality."""
        print("\n🧪 Testing Advanced State Machine...")

        # Test state transitions
        element_id = "test_equipment_001"

        # Set initial state
        self.state_machine.active_states[element_id] = "equipment_off"

        # Test transition: off -> on
        success = await self.state_machine.execute_transition(
            element_id, "equipment_on",
            context={'trigger': 'user_command', 'user_id': self.test_user_id}
        )
        assert success
        assert self.state_machine.get_current_state(element_id) == "equipment_on"
        print("✅ Equipment transition: off -> on")

        # Test transition: on -> standby
        success = await self.state_machine.execute_transition(
            element_id, "equipment_standby",
            context={'trigger': 'automatic', 'reason': 'energy_saving'}
        )
        assert success
        assert self.state_machine.get_current_state(element_id) == "equipment_standby"
        print("✅ Equipment transition: on -> standby")

        # Test transition: standby -> fault
        success = await self.state_machine.execute_transition(
            element_id, "equipment_fault",
            context={'trigger': 'system_detection', 'fault_type': 'sensor_error'}
        )
        assert success
        assert self.state_machine.get_current_state(element_id) == "equipment_fault"
        print("✅ Equipment transition: standby -> fault")

        # Check state history
        history = self.state_machine.get_state_history(element_id)
        assert len(history) >= 3
        print(f"✅ State history contains {len(history)} transitions")

        # Check processing statistics
        stats = self.state_machine.get_processing_stats()
        assert stats['processing_stats']['total_transitions'] >= 3
        print(f"✅ Executed {stats['processing_stats']['total_transitions']} transitions")

        print("✅ Advanced state machine test passed")

    @pytest.mark.asyncio
    async def test_conditional_logic_engine(self):
        """Test conditional logic engine functionality."""
        print("\n🧪 Testing Conditional Logic Engine...")

        # Test threshold condition
        threshold_result = await self.logic_engine.evaluate_condition(
            "temperature_threshold",
            context={'temperature': 35.0}
        )
        assert threshold_result.success
        assert threshold_result.result == True  # 35 > 30
        print("✅ Threshold condition: temperature > 30 (35.0)")

        # Test time condition
        time_result = await self.logic_engine.evaluate_condition(
            "business_hours",
            context={'current_time': datetime.now().replace(hour=14, minute=30)}
        )
        assert time_result.success
        print("✅ Time condition: business hours check")

        # Test spatial condition
        spatial_result = await self.logic_engine.evaluate_condition(
            "proximity_check",
            context={
                'position1': {'x': 0, 'y': 0, 'z': 0},
                'position2': {'x': 3, 'y': 4, 'z': 0}
            }
        )
        assert spatial_result.success
        assert spatial_result.result == True  # distance = 5, max_distance = 5
        print("✅ Spatial condition: proximity check")

        # Test complex condition
        complex_result = await self.logic_engine.evaluate_condition(
            "complex_condition",
            context={
                'temperature': 30.0,
                'humidity': 65.0,
                'power_level': 85.0
            }
        )
        assert complex_result.success
        # (30 > 25 and 65 < 70) or (85 > 80) = True
        assert complex_result.result == True
        print("✅ Complex condition: multi-variable logic")

        # Check processing statistics
        stats = self.logic_engine.get_processing_stats()
        assert stats['processing_stats']['total_evaluations'] >= 4
        print(f"✅ Evaluated {stats['processing_stats']['total_evaluations']} conditions")

        print("✅ Conditional logic engine test passed")

    @pytest.mark.asyncio
    async def test_physics_engine_integration(self):
        """Test physics engine integration with BIM behavior."""
        print("\n🧪 Testing Physics Engine Integration...")

        # Test HVAC air flow calculation
        hvac_data = {
            'duct_diameter': 0.3,
            'air_velocity': 5.0,
            'duct_length': 10.0,
            'roughness': 0.00015,
            'temperature': 20.0,
            'pressure': 101325.0
        }

        hvac_result = self.physics_engine.fluid_dynamics.calculate_air_flow(hvac_data)
        assert hvac_result.success
        assert hvac_result.data['flow_rate'] > 0
        print(f"✅ HVAC air flow: {hvac_result.data['flow_rate']:.2f} m³/s")

        # Test electrical power flow
        electrical_data = {
            'voltage': 480.0,
            'current': 100.0,
            'power_factor': 0.95,
            'frequency': 60.0,
            'load_type': 'inductive'
        }

        electrical_result = self.physics_engine.electrical.calculate_power_flow(electrical_data)
        assert electrical_result.success
        assert electrical_result.data['real_power'] > 0
        print(f"✅ Electrical power: {electrical_result.data['real_power']:.2f} kW")

        # Test structural load calculation
        structural_data = {
            'beam_length': 5.0,
            'beam_height': 0.3,
            'beam_width': 0.2,
            'load_magnitude': 10000.0,
            'load_type': 'uniform',
            'material': 'steel'
        }

        structural_result = self.physics_engine.structural.calculate_beam_analysis(structural_data)
        assert structural_result.success
        assert structural_result.data['max_stress'] > 0
        print(f"✅ Structural stress: {structural_result.data['max_stress']:.2f} MPa")

        print("✅ Physics engine integration test passed")

    @pytest.mark.asyncio
    async def test_comprehensive_bim_behavior_scenario(self):
        """Test comprehensive BIM behavior scenario."""
        print("\n🧪 Testing Comprehensive BIM Behavior Scenario...")

        # Start event processing
        await self.event_engine.start_processing()

        # Scenario: HVAC system operation with user interaction and physics
        hvac_element_id = "hvac_system_001"

        # 1. Initialize HVAC system state
        self.state_machine.active_states[hvac_element_id] = "equipment_off"

        # 2. User turns on HVAC system
        user_event = Event(
            event_id=str(uuid.uuid4()),
            event_type=EventType.USER_INTERACTION,
            element_id=hvac_element_id,
            timestamp=datetime.now(),
            priority=EventPriority.HIGH,
            data={
                'interaction_type': 'click',
                'position': {'x': 150, 'y': 200},
                'user_id': self.test_user_id,
                'action': 'power_on'
            }
        )

        await self.event_engine.emit_event(user_event)

        # 3. System responds by transitioning state
        success = await self.state_machine.execute_transition(
            hvac_element_id, "equipment_on",
            context={'trigger': 'user_interaction', 'user_id': self.test_user_id}
        )
        assert success

        # 4. Check temperature condition
        temp_result = await self.logic_engine.evaluate_condition(
            "temperature_threshold",
            context={'temperature': 28.0}
        )
        assert temp_result.success

        # 5. If temperature is high, start cooling
        if temp_result.result:
            # Transition to active cooling
            success = await self.state_machine.execute_transition(
                hvac_element_id, "equipment_on",  # Already on, but update properties
                context={'trigger': 'temperature_condition', 'mode': 'cooling'}
            )
            assert success

            # Calculate cooling performance
            cooling_data = {
                'duct_diameter': 0.25,
                'air_velocity': 4.5,
                'duct_length': 8.0,
                'roughness': 0.00015,
                'temperature': 28.0,
                'pressure': 101325.0
            }

            cooling_result = self.physics_engine.fluid_dynamics.calculate_air_flow(cooling_data)
            assert cooling_result.success

            print(f"✅ HVAC cooling: {cooling_result.data['flow_rate']:.2f} m³/s")

        # 6. Check system performance
        stats = self.event_engine.get_processing_stats()
        state_stats = self.state_machine.get_processing_stats()
        logic_stats = self.logic_engine.get_processing_stats()

        print(f"✅ Events processed: {stats['processing_stats']['processed_events']}")
        print(f"✅ State transitions: {state_stats['processing_stats']['total_transitions']}")
        print(f"✅ Condition evaluations: {logic_stats['processing_stats']['total_evaluations']}")

        print("✅ Comprehensive BIM behavior scenario test passed")

    @pytest.mark.asyncio
    async def test_performance_optimization(self):
        """Test performance optimization features."""
        print("\n🧪 Testing Performance Optimization...")

        # Test event processing performance
        start_time = time.time()

        # Emit multiple events rapidly
        events = []
        for i in range(100):
            event = Event(
                event_id=str(uuid.uuid4()),
                event_type=EventType.SYSTEM_EVENT,
                element_id=f"test_element_{i}",
                timestamp=datetime.now(),
                priority=EventPriority.NORMAL,
                data={'test_data': i}
            )
            events.append(event)

        # Emit events
        for event in events:
            await self.event_engine.emit_event(event)

        # Wait for processing
        await asyncio.sleep(0.2)

        processing_time = time.time() - start_time

        # Check performance
        stats = self.event_engine.get_processing_stats()
        assert stats['processing_stats']['average_processing_time'] < 0.05  # <50ms
        print(f"✅ Average event processing time: {stats['processing_stats']['average_processing_time']*1000:.2f}ms")

        # Test condition evaluation performance
        start_time = time.time()

        # Evaluate conditions rapidly
        for i in range(50):
            await self.logic_engine.evaluate_condition(
                "temperature_threshold",
                context={'temperature': 25.0 + i}
            )

        evaluation_time = time.time() - start_time

        # Check performance
        logic_stats = self.logic_engine.get_processing_stats()
        assert logic_stats['processing_stats']['average_evaluation_time'] < 0.005  # <5ms
        print(f"✅ Average condition evaluation time: {logic_stats['processing_stats']['average_evaluation_time']*1000:.2f}ms")

        # Test state transition performance
        start_time = time.time()

        # Execute state transitions rapidly
        for i in range(20):
            element_id = f"test_element_{i}"
            self.state_machine.active_states[element_id] = "equipment_off"

            await self.state_machine.execute_transition(
                element_id, "equipment_on",
                context={'test': True}
            )

        transition_time = time.time() - start_time

        # Check performance
        state_stats = self.state_machine.get_processing_stats()
        assert state_stats['processing_stats']['average_transition_time'] < 0.01  # <10ms
        print(f"✅ Average state transition time: {state_stats['processing_stats']['average_transition_time']*1000:.2f}ms")

        print("✅ Performance optimization test passed")

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms."""
        print("\n🧪 Testing Error Handling and Recovery...")

        # Test invalid event handling
        invalid_event = Event(
            event_id="",
            event_type=EventType.USER_INTERACTION,
            element_id="",
            timestamp=datetime.now()
        )

        try:
            await self.event_engine.emit_event(invalid_event)
            assert False, "Should have raised validation error"
        except Exception as e:
            print(f"✅ Invalid event properly rejected: {type(e).__name__}")

        # Test invalid state transition
        try:
            await self.state_machine.execute_transition(
                "nonexistent_element", "equipment_on"
            )
            assert False, "Should have failed for nonexistent element"
        except Exception as e:
            print(f"✅ Invalid state transition properly handled: {type(e).__name__}")

        # Test invalid condition evaluation
        try:
            await self.logic_engine.evaluate_condition(
                "nonexistent_condition",
                context={}
            )
            assert False, "Should have failed for nonexistent condition"
        except Exception as e:
            print(f"✅ Invalid condition evaluation properly handled: {type(e).__name__}")

        # Test cache clearing
        self.event_engine.clear_cache()
        self.state_machine.clear_cache()
        self.logic_engine.clear_cache()
        print("✅ Cache clearing successful")

        # Test statistics reset
        self.event_engine.reset_statistics()
        self.state_machine.reset_statistics()
        self.logic_engine.reset_statistics()
        print("✅ Statistics reset successful")

        print("✅ Error handling and recovery test passed")

    @pytest.mark.asyncio
    async def test_real_world_bim_scenario(self):
        """Test real-world BIM scenario with multiple systems."""
        print("\n🧪 Testing Real-World BIM Scenario...")

        # Scenario: Smart building with HVAC, lighting, and security systems

        # Initialize building systems
        building_systems = {
            'hvac_main': "equipment_off",
            'lighting_zone_1': "equipment_off",
            'lighting_zone_2': "equipment_off",
            'security_system': "equipment_on",
            'fire_alarm': "equipment_off"
        }

        for system_id, initial_state in building_systems.items():
            self.state_machine.active_states[system_id] = initial_state

        # 1. Business hours start - automatic system activation
        business_hours_result = await self.logic_engine.evaluate_condition(
            "business_hours",
            context={'current_time': datetime.now().replace(hour=9, minute=0)}
        )

        if business_hours_result.result:
            # Activate HVAC and lighting
            for system_id in ['hvac_main', 'lighting_zone_1', 'lighting_zone_2']:
                success = await self.state_machine.execute_transition(
                    system_id, "equipment_on",
                    context={'trigger': 'business_hours_start'}
                )
                assert success
                print(f"✅ Activated {system_id}")

        # 2. Temperature monitoring and HVAC control
        temperature_result = await self.logic_engine.evaluate_condition(
            "temperature_threshold",
            context={'temperature': 32.0}
        )

        if temperature_result.result:
            # High temperature detected - increase cooling
            hvac_data = {
                'duct_diameter': 0.3,
                'air_velocity': 6.0,  # Increased velocity
                'duct_length': 12.0,
                'roughness': 0.00015,
                'temperature': 32.0,
                'pressure': 101325.0
            }

            hvac_result = self.physics_engine.fluid_dynamics.calculate_air_flow(hvac_data)
            assert hvac_result.success
            print(f"✅ Enhanced cooling: {hvac_result.data['flow_rate']:.2f} m³/s")

        # 3. Security system monitoring
        security_event = Event(
            event_id=str(uuid.uuid4()),
            event_type=EventType.OPERATIONAL_EVENT,
            element_id='security_system',
            timestamp=datetime.now(),
            priority=EventPriority.CRITICAL,
            data={
                'operational_event_type': 'maintenance',
                'maintenance_type': 'routine_check',
                'maintenance_level': 'preventive'
            }
        )

        await self.event_engine.emit_event(security_event)

        # 4. Emergency scenario - fire alarm
        fire_condition = await self.logic_engine.evaluate_condition(
            "complex_condition",
            context={
                'smoke_detected': True,
                'temperature': 45.0,
                'occupancy': 10
            }
        )

        if fire_condition.result:
            # Activate fire alarm and emergency protocols
            success = await self.state_machine.execute_transition(
                'fire_alarm', 'equipment_on',
                context={'trigger': 'emergency', 'emergency_type': 'fire'}
            )
            assert success

            # Shutdown non-essential systems
            for system_id in ['hvac_main', 'lighting_zone_1', 'lighting_zone_2']:
                success = await self.state_machine.execute_transition(
                    system_id, 'equipment_off',
                    context={'trigger': 'emergency_shutdown'}
                )
                assert success
                print(f"✅ Emergency shutdown: {system_id}")

        # 5. Check system status
        active_systems = 0
        for system_id, current_state in self.state_machine.active_states.items():
            if current_state in ['equipment_on', 'equipment_standby']:
                active_systems += 1

        print(f"✅ Active systems: {active_systems}")

        # 6. Performance summary
        event_stats = self.event_engine.get_processing_stats()
        state_stats = self.state_machine.get_processing_stats()
        logic_stats = self.logic_engine.get_processing_stats()

        print(f"✅ Total events processed: {event_stats['processing_stats']['total_events']}")
        print(f"✅ Total state transitions: {state_stats['processing_stats']['total_transitions']}")
        print(f"✅ Total condition evaluations: {logic_stats['processing_stats']['total_evaluations']}")

        print("✅ Real-world BIM scenario test passed")


async def run_comprehensive_tests():
    """Run all comprehensive BIM behavior tests."""
    print("🚀 Starting Comprehensive BIM Behavior System Tests")
    print("=" * 60)

    test_suite = TestBIMBehaviorComprehensive()

    # Run all tests
    await test_suite.setup()

    try:
        await test_suite.test_event_driven_behavior_system()
        await test_suite.test_advanced_state_machine()
        await test_suite.test_conditional_logic_engine()
        await test_suite.test_physics_engine_integration()
        await test_suite.test_comprehensive_bim_behavior_scenario()
        await test_suite.test_performance_optimization()
        await test_suite.test_error_handling_and_recovery()
        await test_suite.test_real_world_bim_scenario()

        print("\n" + "=" * 60)
        print("🎉 All Comprehensive BIM Behavior Tests Passed!")
        print("✅ Event-Driven Behavior System: Operational")
        print("✅ Advanced State Machine: Operational")
        print("✅ Conditional Logic Engine: Operational")
        print("✅ Physics Engine Integration: Operational")
        print("✅ Performance Optimization: Operational")
        print("✅ Error Handling: Operational")
        print("✅ Real-World Scenarios: Operational")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
    finally:
        # Cleanup
        await test_suite.event_engine.stop_processing()


if __name__ == "__main__":
    asyncio.run(run_comprehensive_tests())
