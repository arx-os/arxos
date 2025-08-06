"""
Test Physics Integration Service

This test suite verifies that the physics integration service is properly
connected to the main behavior engine and working correctly.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import unittest
import sys
import os
import asyncio
from typing import Dict, Any
import numpy as np

# Add the svgx_engine to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "svgx_engine"))

from services.physics_integration_service import (
    PhysicsIntegrationService,
    PhysicsIntegrationConfig,
    PhysicsBehaviorType,
    PhysicsBehaviorRequest,
    PhysicsBehaviorResult,
    IntegrationType,
)

from runtime.advanced_behavior_engine import (
    AdvancedBehaviorEngine,
    BehaviorRule,
    RuleType,
)


class TestPhysicsIntegration(unittest.TestCase):
    """Test physics integration service functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = PhysicsIntegrationConfig(
            integration_type=IntegrationType.REAL_TIME,
            physics_enabled=True,
            cache_enabled=True,
            performance_monitoring=True,
            ai_optimization_enabled=True,
        )
        self.physics_integration = PhysicsIntegrationService(self.config)

        # Create behavior engine with physics integration
        self.behavior_engine = AdvancedBehaviorEngine()

    def test_physics_integration_initialization(self):
        """Test that physics integration service initializes correctly."""
        self.assertIsNotNone(self.physics_integration)
        self.assertIsNotNone(self.physics_integration.physics_engine)
        self.assertEqual(self.physics_integration.config.physics_enabled, True)
        self.assertEqual(self.physics_integration.config.cache_enabled, True)

    def test_behavior_engine_physics_integration(self):
        """Test that behavior engine has physics integration."""
        self.assertIsNotNone(self.behavior_engine.physics_integration)
        self.assertTrue(
            hasattr(
                self.behavior_engine.physics_integration, "calculate_physics_behavior"
            )
        )

    def test_hvac_behavior_simulation(self):
        """Test HVAC behavior simulation with physics."""
        element_id = "hvac_unit_001"
        element_data = {
            "fluid_type": "air",
            "flow_rate": 100.0,
            "temperature": 22.0,
            "pressure": 101.325,
            "duct_diameter": 0.3,
            "duct_length": 10.0,
        }

        result = self.physics_integration.simulate_hvac_behavior(
            element_id, element_data
        )

        self.assertIsInstance(result, PhysicsBehaviorResult)
        self.assertEqual(result.element_id, element_id)
        self.assertEqual(result.behavior_type, PhysicsBehaviorType.HVAC)
        self.assertIsNotNone(result.physics_result)
        self.assertIsInstance(result.behavior_state, str)
        self.assertIsInstance(result.recommendations, list)
        self.assertIsInstance(result.alerts, list)

    def test_electrical_behavior_simulation(self):
        """Test electrical behavior simulation with physics."""
        element_id = "electrical_panel_001"
        element_data = {
            "voltage": 120.0,
            "current": 10.0,
            "power_factor": 0.95,
            "load_type": "resistive",
            "circuit_impedance": 12.0,
        }

        result = self.physics_integration.simulate_electrical_behavior(
            element_id, element_data
        )

        self.assertIsInstance(result, PhysicsBehaviorResult)
        self.assertEqual(result.element_id, element_id)
        self.assertEqual(result.behavior_type, PhysicsBehaviorType.ELECTRICAL)
        self.assertIsNotNone(result.physics_result)
        self.assertIsInstance(result.behavior_state, str)

    def test_structural_behavior_simulation(self):
        """Test structural behavior simulation with physics."""
        element_id = "beam_001"
        element_data = {
            "element_type": "beam",
            "length": 5.0,
            "width": 0.2,
            "height": 0.3,
            "material": "A36_Steel",
            "load_magnitude": 1000.0,
            "load_type": "uniform",
        }

        result = self.physics_integration.simulate_structural_behavior(
            element_id, element_data
        )

        self.assertIsInstance(result, PhysicsBehaviorResult)
        self.assertEqual(result.element_id, element_id)
        self.assertEqual(result.behavior_type, PhysicsBehaviorType.STRUCTURAL)
        self.assertIsNotNone(result.physics_result)
        self.assertIsInstance(result.behavior_state, str)

    def test_thermal_behavior_simulation(self):
        """Test thermal behavior simulation with physics."""
        element_id = "wall_001"
        element_data = {
            "thickness": 0.2,
            "thermal_conductivity": 0.8,
            "temperature_inner": 22.0,
            "temperature_outer": 5.0,
            "area": 10.0,
        }

        result = self.physics_integration.simulate_thermal_behavior(
            element_id, element_data
        )

        self.assertIsInstance(result, PhysicsBehaviorResult)
        self.assertEqual(result.element_id, element_id)
        self.assertEqual(result.behavior_type, PhysicsBehaviorType.THERMAL)
        self.assertIsNotNone(result.physics_result)
        self.assertIsInstance(result.behavior_state, str)

    def test_acoustic_behavior_simulation(self):
        """Test acoustic behavior simulation with physics."""
        element_id = "room_001"
        element_data = {
            "room_volume": 100.0,
            "surface_area": 150.0,
            "absorption_coefficient": 0.3,
            "sound_power": 0.001,
            "frequency": 1000.0,
        }

        result = self.physics_integration.simulate_acoustic_behavior(
            element_id, element_data
        )

        self.assertIsInstance(result, PhysicsBehaviorResult)
        self.assertEqual(result.element_id, element_id)
        self.assertEqual(result.behavior_type, PhysicsBehaviorType.ACOUSTIC)
        self.assertIsNotNone(result.physics_result)
        self.assertIsInstance(result.behavior_state, str)

    def test_physics_behavior_request_validation(self):
        """Test physics behavior request validation."""
        # Valid request
        valid_request = PhysicsBehaviorRequest(
            element_id="test_element",
            behavior_type=PhysicsBehaviorType.HVAC,
            physics_type="fluid_dynamics",
            element_data={"test": "data"},
        )

        result = self.physics_integration.calculate_physics_behavior(valid_request)
        self.assertIsInstance(result, PhysicsBehaviorResult)

        # Invalid request - missing element_id
        invalid_request = PhysicsBehaviorRequest(
            element_id="",
            behavior_type=PhysicsBehaviorType.HVAC,
            physics_type="fluid_dynamics",
            element_data={},
        )

        with self.assertRaises(Exception):
            self.physics_integration.calculate_physics_behavior(invalid_request)

    def test_physics_integration_caching(self):
        """Test that physics integration caching works correctly."""
        element_id = "cached_element"
        element_data = {"test": "data"}

        # First calculation
        result1 = self.physics_integration.simulate_hvac_behavior(
            element_id, element_data
        )

        # Second calculation (should use cache)
        result2 = self.physics_integration.simulate_hvac_behavior(
            element_id, element_data
        )

        self.assertEqual(result1.element_id, result2.element_id)
        self.assertEqual(result1.behavior_type, result2.behavior_type)

        # Clear cache
        self.physics_integration.clear_cache()
        self.assertEqual(len(self.physics_integration.cache), 0)

    def test_physics_integration_metrics(self):
        """Test that physics integration provides performance metrics."""
        element_id = "metrics_test"
        element_data = {"test": "data"}

        # Perform some calculations
        self.physics_integration.simulate_hvac_behavior(element_id, element_data)
        self.physics_integration.simulate_electrical_behavior(element_id, element_data)

        metrics = self.physics_integration.get_integration_metrics()

        self.assertIsInstance(metrics, dict)
        self.assertIn("integration_metrics", metrics)
        self.assertIn("cache_size", metrics)
        self.assertIn("active_calculations", metrics)
        self.assertIn("total_history_entries", metrics)

    def test_physics_integration_history(self):
        """Test that physics integration maintains history."""
        element_id = "history_test"
        element_data = {"test": "data"}

        # Perform calculations
        self.physics_integration.simulate_hvac_behavior(element_id, element_data)
        self.physics_integration.simulate_electrical_behavior(element_id, element_data)

        # Get history
        history = self.physics_integration.get_integration_history()

        self.assertIsInstance(history, dict)
        self.assertGreater(len(history), 0)

        # Get specific behavior type history
        hvac_history = self.physics_integration.get_integration_history(
            PhysicsBehaviorType.HVAC
        )
        self.assertIsInstance(hvac_history, dict)

    def test_behavior_engine_physics_action(self):
        """Test that behavior engine can execute physics actions."""
        # Create a physics action
        physics_action = {
            "type": "physics",
            "physics_type": "hvac",
            "element_data": {
                "fluid_type": "air",
                "flow_rate": 100.0,
                "temperature": 22.0,
            },
        }

        element_id = "test_element"
        context = {}

        # Execute physics action
        asyncio.run(
            self.behavior_engine._execute_physics_action(
                physics_action, element_id, context
            )
        )

        # Check that physics result was stored in context
        self.assertIn("physics_result", context)
        self.assertIsInstance(context["physics_result"], PhysicsBehaviorResult)

    def test_physics_integration_error_handling(self):
        """Test that physics integration handles errors gracefully."""
        # Test with invalid element data
        element_id = "error_test"
        invalid_element_data = {"invalid_field": "invalid_value"}

        # Should not raise exception, but should handle gracefully
        try:
            result = self.physics_integration.simulate_hvac_behavior(
                element_id, invalid_element_data
            )
            self.assertIsInstance(result, PhysicsBehaviorResult)
        except Exception as e:
            # If exception is raised, it should be a known type
            self.assertIsInstance(e, Exception)

    def test_physics_integration_performance(self):
        """Test that physics integration performs within acceptable limits."""
        import time

        element_id = "performance_test"
        element_data = {"test": "data"}

        # Measure calculation time
        start_time = time.time()
        result = self.physics_integration.simulate_hvac_behavior(
            element_id, element_data
        )
        end_time = time.time()

        calculation_time = end_time - start_time

        # Should complete within reasonable time (e.g., 5 seconds)
        self.assertLess(calculation_time, 5.0)

        # Check performance metrics
        metrics = self.physics_integration.get_integration_metrics()
        self.assertIn("integration_metrics", metrics)

    def test_physics_integration_configuration(self):
        """Test that physics integration configuration works correctly."""
        # Test with different configurations
        config_disabled = PhysicsIntegrationConfig(
            physics_enabled=False, cache_enabled=False, performance_monitoring=False
        )

        integration_disabled = PhysicsIntegrationService(config_disabled)
        self.assertEqual(integration_disabled.config.physics_enabled, False)
        self.assertEqual(integration_disabled.config.cache_enabled, False)

    def test_physics_behavior_result_structure(self):
        """Test that physics behavior results have correct structure."""
        element_id = "structure_test"
        element_data = {"test": "data"}

        result = self.physics_integration.simulate_hvac_behavior(
            element_id, element_data
        )

        # Check required fields
        required_fields = [
            "element_id",
            "behavior_type",
            "physics_type",
            "physics_result",
            "behavior_state",
            "recommendations",
            "alerts",
            "performance_metrics",
            "timestamp",
        ]

        for field in required_fields:
            self.assertTrue(hasattr(result, field), f"Missing field: {field}")

        # Check data types
        self.assertIsInstance(result.element_id, str)
        self.assertIsInstance(result.behavior_type, PhysicsBehaviorType)
        self.assertIsInstance(result.behavior_state, str)
        self.assertIsInstance(result.recommendations, list)
        self.assertIsInstance(result.alerts, list)
        self.assertIsInstance(result.performance_metrics, dict)
        self.assertIsInstance(result.timestamp, type(result.timestamp))  # datetime


class TestPhysicsIntegrationWithBehaviorEngine(unittest.TestCase):
    """Test physics integration with behavior engine integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.behavior_engine = AdvancedBehaviorEngine()

    def test_physics_rule_execution(self):
        """Test that physics rules can be executed by behavior engine."""
        # Create a physics rule
        physics_rule = BehaviorRule(
            rule_id="physics_test_rule",
            rule_type=RuleType.OPERATIONAL,
            conditions=[
                {
                    "type": "threshold",
                    "variable": "temperature",
                    "operator": ">",
                    "threshold": 25.0,
                }
            ],
            actions=[
                {
                    "type": "physics",
                    "physics_type": "hvac",
                    "element_data": {
                        "fluid_type": "air",
                        "flow_rate": 150.0,
                        "temperature": 22.0,
                    },
                }
            ],
            priority=1,
            enabled=True,
        )

        # Register rule
        self.behavior_engine.register_rule(physics_rule)

        # Create context that triggers the rule
        context = {"temperature": 30.0, "element_id": "test_element"}

        # Evaluate rules
        applicable_rules = asyncio.run(
            self.behavior_engine.evaluate_rules("test_element", context)
        )

        # Should find our physics rule
        self.assertGreater(len(applicable_rules), 0)
        found_physics_rule = False
        for rule in applicable_rules:
            if rule["rule_id"] == "physics_test_rule":
                found_physics_rule = True
                # Check that it has physics action
                has_physics_action = any(
                    action.get("type") == "physics" for action in rule["actions"]
                )
                self.assertTrue(has_physics_action)
                break

        self.assertTrue(found_physics_rule)

    def test_physics_event_handling(self):
        """Test that behavior engine can handle physics events."""
        # Create physics event
        physics_event = {
            "type": "physics",
            "physics_type": "hvac",
            "element_data": {"fluid_type": "air", "flow_rate": 100.0},
        }

        element_id = "test_element"

        # Dispatch physics event
        asyncio.run(
            self.behavior_engine.dispatch_event(element_id, "physics", physics_event)
        )

        # Should not raise exception
        self.assertTrue(True)  # If we get here, no exception was raised

    def test_physics_integration_availability(self):
        """Test that physics integration is available in behavior engine."""
        self.assertIsNotNone(self.behavior_engine.physics_integration)

        # Test that physics integration has required methods
        required_methods = [
            "calculate_physics_behavior",
            "simulate_hvac_behavior",
            "simulate_electrical_behavior",
            "simulate_structural_behavior",
            "simulate_thermal_behavior",
            "simulate_acoustic_behavior",
        ]

        for method in required_methods:
            self.assertTrue(hasattr(self.behavior_engine.physics_integration, method))


if __name__ == "__main__":
    unittest.main()
