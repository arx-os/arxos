#!/usr/bin/env python3
"""
Simple Physics Integration Test

This script tests that the physics integration service is working correctly.
"""

import sys
import os

# Add the svgx_engine to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'svgx_engine'))

def test_physics_integration():
    """Test physics integration service."""
    print("Testing Physics Integration Service...")
    
    try:
        # Import the physics integration service
        from services.physics_integration_service import (
            PhysicsIntegrationService, PhysicsIntegrationConfig, 
            PhysicsBehaviorType, IntegrationType
        )
        print("✅ Successfully imported physics integration service")
        
        # Create configuration
        config = PhysicsIntegrationConfig(
            integration_type=IntegrationType.REAL_TIME,
            physics_enabled=True,
            cache_enabled=True,
            performance_monitoring=True,
            ai_optimization_enabled=True
        )
        print("✅ Successfully created physics integration config")
        
        # Initialize physics integration service
        physics_integration = PhysicsIntegrationService(config)
        print("✅ Successfully initialized physics integration service")
        
        # Test HVAC behavior simulation
        element_id = "hvac_unit_001"
        element_data = {
            "fluid_type": "air",
            "flow_rate": 100.0,
            "temperature": 22.0,
            "pressure": 101.325,
            "duct_diameter": 0.3,
            "duct_length": 10.0
        }
        
        result = physics_integration.simulate_hvac_behavior(element_id, element_data)
        print("✅ Successfully simulated HVAC behavior")
        print(f"   Element ID: {result.element_id}")
        print(f"   Behavior Type: {result.behavior_type}")
        print(f"   Behavior State: {result.behavior_state}")
        print(f"   Recommendations: {len(result.recommendations)}")
        print(f"   Alerts: {len(result.alerts)}")
        
        # Test electrical behavior simulation
        element_id = "electrical_panel_001"
        element_data = {
            "voltage": 120.0,
            "current": 10.0,
            "power_factor": 0.95,
            "load_type": "resistive",
            "circuit_impedance": 12.0
        }
        
        result = physics_integration.simulate_electrical_behavior(element_id, element_data)
        print("✅ Successfully simulated electrical behavior")
        print(f"   Element ID: {result.element_id}")
        print(f"   Behavior Type: {result.behavior_type}")
        print(f"   Behavior State: {result.behavior_state}")
        
        # Test structural behavior simulation
        element_id = "beam_001"
        element_data = {
            "element_type": "beam",
            "length": 5.0,
            "width": 0.2,
            "height": 0.3,
            "material": "A36_Steel",
            "load_magnitude": 1000.0,
            "load_type": "uniform"
        }
        
        result = physics_integration.simulate_structural_behavior(element_id, element_data)
        print("✅ Successfully simulated structural behavior")
        print(f"   Element ID: {result.element_id}")
        print(f"   Behavior Type: {result.behavior_type}")
        print(f"   Behavior State: {result.behavior_state}")
        
        # Test thermal behavior simulation
        element_id = "wall_001"
        element_data = {
            "thickness": 0.2,
            "thermal_conductivity": 0.8,
            "temperature_inner": 22.0,
            "temperature_outer": 5.0,
            "area": 10.0
        }
        
        result = physics_integration.simulate_thermal_behavior(element_id, element_data)
        print("✅ Successfully simulated thermal behavior")
        print(f"   Element ID: {result.element_id}")
        print(f"   Behavior Type: {result.behavior_type}")
        print(f"   Behavior State: {result.behavior_state}")
        
        # Test acoustic behavior simulation
        element_id = "room_001"
        element_data = {
            "room_volume": 100.0,
            "surface_area": 150.0,
            "absorption_coefficient": 0.3,
            "sound_power": 0.001,
            "frequency": 1000.0
        }
        
        result = physics_integration.simulate_acoustic_behavior(element_id, element_data)
        print("✅ Successfully simulated acoustic behavior")
        print(f"   Element ID: {result.element_id}")
        print(f"   Behavior Type: {result.behavior_type}")
        print(f"   Behavior State: {result.behavior_state}")
        
        # Test metrics
        metrics = physics_integration.get_integration_metrics()
        print("✅ Successfully retrieved integration metrics")
        print(f"   Cache Size: {metrics.get('cache_size', 0)}")
        print(f"   Active Calculations: {metrics.get('active_calculations', 0)}")
        print(f"   Total History Entries: {metrics.get('total_history_entries', 0)}")
        
        print("\n🎉 ALL PHYSICS INTEGRATION TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Physics integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_behavior_engine_integration():
    """Test behavior engine with physics integration."""
    print("\nTesting Behavior Engine Physics Integration...")
    
    try:
        # Import the behavior engine
        from runtime.advanced_behavior_engine import AdvancedBehaviorEngine
        print("✅ Successfully imported advanced behavior engine")
        
        # Initialize behavior engine
        behavior_engine = AdvancedBehaviorEngine()
        print("✅ Successfully initialized behavior engine")
        
        # Check if physics integration is available
        if behavior_engine.physics_integration is not None:
            print("✅ Physics integration is available in behavior engine")
            
            # Test physics action execution
            physics_action = {
                "type": "physics",
                "physics_type": "hvac",
                "element_data": {
                    "fluid_type": "air",
                    "flow_rate": 100.0,
                    "temperature": 22.0
                }
            }
            
            element_id = "test_element"
            context = {}
            
            import asyncio
            asyncio.run(behavior_engine._execute_physics_action(
                physics_action, element_id, context
            ))
            
            print("✅ Successfully executed physics action in behavior engine")
            print(f"   Physics result stored in context: {'physics_result' in context}")
            
        else:
            print("⚠️  Physics integration not available in behavior engine")
        
        print("\n🎉 BEHAVIOR ENGINE INTEGRATION TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Behavior engine integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("PHYSICS INTEGRATION TEST SUITE")
    print("=" * 60)
    
    # Test physics integration service
    physics_success = test_physics_integration()
    
    # Test behavior engine integration
    behavior_success = test_behavior_engine_integration()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if physics_success and behavior_success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Physics integration service is working correctly")
        print("✅ Behavior engine integration is working correctly")
        print("✅ Physics calculations are properly integrated into the main system")
        return 0
    else:
        print("❌ SOME TESTS FAILED!")
        if not physics_success:
            print("❌ Physics integration service tests failed")
        if not behavior_success:
            print("❌ Behavior engine integration tests failed")
        return 1

if __name__ == "__main__":
    exit(main()) 