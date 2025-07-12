"""
Electrical Flow Logic Tests

This module provides comprehensive tests for electrical system logic processing,
including power flow validation, circuit analysis, and behavior profile testing.
"""

import unittest
import json
import yaml
from typing import Dict, List, Any
from unittest.mock import Mock, patch
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'arx-behavior'))

from arx_behavior.engine.rule_engine import RuleEngine, RuleType, Severity
from arx_behavior.engine.checks.power_flow import PowerFlowValidator, PowerFlowStatus
from arx_svg_parser.logic.object_chain import ObjectChainManager, ChainEventType, ObjectState


class TestElectricalFlow(unittest.TestCase):
    """Test electrical flow logic and validation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.rule_engine = RuleEngine()
        self.power_validator = PowerFlowValidator()
        self.chain_manager = ObjectChainManager()
        
        # Load test electrical profiles
        self.electrical_profiles = self._load_electrical_profiles()
        
        # Create mock electrical system
        self.mock_electrical_system = self._create_mock_electrical_system()
    
    def _load_electrical_profiles(self) -> Dict[str, Any]:
        """Load electrical behavior profiles for testing."""
        try:
            profile_path = os.path.join(os.path.dirname(__file__), '..', '..', 
                                      'arx-behavior', 'profiles', 'electrical.yaml')
            with open(profile_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Return mock profiles if file not found
            return {
                "power_distribution": {
                    "panel": {
                        "description": "Electrical panel behavior profile",
                        "system_type": "electrical",
                        "category": "power_distribution",
                        "variables": {
                            "voltage": {"value": 208, "unit": "V"},
                            "current_capacity": {"value": 200, "unit": "A"},
                            "phase_count": {"value": 3, "unit": "phases"},
                            "breaker_count": {"value": 42, "unit": "breakers"}
                        }
                    }
                }
            }
    
    def _create_mock_electrical_system(self) -> Dict[str, Any]:
        """Create a mock electrical system for testing."""
        return {
            "system_id": "test_electrical_system",
            "components": {
                "main_panel": {
                    "id": "main_panel",
                    "type": "electrical_panel",
                    "system_type": "electrical",
                    "properties": {
                        "voltage": 208,
                        "current_capacity": 200,
                        "phase_count": 3,
                        "breaker_count": 42,
                        "efficiency": 0.95
                    },
                    "connections": ["transformer_01", "sub_panel_01"]
                },
                "transformer_01": {
                    "id": "transformer_01",
                    "type": "transformer",
                    "system_type": "electrical",
                    "properties": {
                        "primary_voltage": 480,
                        "secondary_voltage": 208,
                        "rated_power": 75,
                        "efficiency": 0.98
                    },
                    "connections": ["main_panel"]
                },
                "sub_panel_01": {
                    "id": "sub_panel_01",
                    "type": "electrical_panel",
                    "system_type": "electrical",
                    "properties": {
                        "voltage": 120,
                        "current_capacity": 100,
                        "phase_count": 1,
                        "breaker_count": 20,
                        "efficiency": 0.92
                    },
                    "connections": ["main_panel", "lighting_circuit_01", "outlet_circuit_01"]
                },
                "lighting_circuit_01": {
                    "id": "lighting_circuit_01",
                    "type": "circuit",
                    "system_type": "electrical",
                    "properties": {
                        "voltage": 120,
                        "current": 15,
                        "breaker_rating": 20,
                        "wire_size": 12
                    },
                    "connections": ["sub_panel_01", "light_fixture_01", "light_fixture_02"]
                },
                "outlet_circuit_01": {
                    "id": "outlet_circuit_01",
                    "type": "circuit",
                    "system_type": "electrical",
                    "properties": {
                        "voltage": 120,
                        "current": 12,
                        "breaker_rating": 20,
                        "wire_size": 12
                    },
                    "connections": ["sub_panel_01", "outlet_01", "outlet_02"]
                },
                "light_fixture_01": {
                    "id": "light_fixture_01",
                    "type": "light_fixture",
                    "system_type": "electrical",
                    "properties": {
                        "wattage": 32,
                        "voltage": 120,
                        "lumens": 3000,
                        "efficiency": 0.85
                    },
                    "connections": ["lighting_circuit_01"]
                },
                "light_fixture_02": {
                    "id": "light_fixture_02",
                    "type": "light_fixture",
                    "system_type": "electrical",
                    "properties": {
                        "wattage": 32,
                        "voltage": 120,
                        "lumens": 3000,
                        "efficiency": 0.85
                    },
                    "connections": ["lighting_circuit_01"]
                },
                "outlet_01": {
                    "id": "outlet_01",
                    "type": "outlet",
                    "system_type": "electrical",
                    "properties": {
                        "voltage": 120,
                        "current": 8,
                        "power": 960
                    },
                    "connections": ["outlet_circuit_01"]
                },
                "outlet_02": {
                    "id": "outlet_02",
                    "type": "outlet",
                    "system_type": "electrical",
                    "properties": {
                        "voltage": 120,
                        "current": 4,
                        "power": 480
                    },
                    "connections": ["outlet_circuit_01"]
                }
            }
        }
    
    def test_power_flow_validation(self):
        """Test power flow validation in electrical system."""
        # Test normal power flow
        circuit_data = {
            "circuit_id": "test_circuit",
            "nodes": [
                {
                    "node_id": "source",
                    "node_type": "source",
                    "voltage": 120,
                    "current": 0,
                    "power": 0,
                    "resistance": 0,
                    "connections": ["load1"]
                },
                {
                    "node_id": "load1",
                    "node_type": "load",
                    "voltage": 120,
                    "current": 10,
                    "power": 1200,
                    "resistance": 12,
                    "connections": ["source"]
                }
            ],
            "branches": [
                {
                    "branch_id": "source_load1",
                    "from_node": "source",
                    "to_node": "load1",
                    "resistance": 0.1,
                    "current": 10
                }
            ]
        }
        
        result = self.power_validator.validate_circuit(circuit_data)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.status, PowerFlowStatus.NORMAL)
        self.assertGreater(result.efficiency, 0.9)
    
    def test_overload_detection(self):
        """Test overload detection in electrical circuits."""
        # Create overloaded circuit
        overloaded_circuit = {
            "circuit_id": "overloaded_circuit",
            "nodes": [
                {
                    "node_id": "source",
                    "node_type": "source",
                    "voltage": 120,
                    "current": 0,
                    "power": 0,
                    "resistance": 0,
                    "connections": ["load1"]
                },
                {
                    "node_id": "load1",
                    "node_type": "load",
                    "voltage": 120,
                    "current": 25,  # Exceeds typical breaker rating
                    "power": 3000,
                    "resistance": 4.8,
                    "connections": ["source"]
                }
            ],
            "branches": [
                {
                    "branch_id": "source_load1",
                    "from_node": "source",
                    "to_node": "load1",
                    "resistance": 0.1,
                    "current": 25
                }
            ]
        }
        
        result = self.power_validator.validate_circuit(overloaded_circuit)
        
        self.assertIsNotNone(result)
        self.assertIn("overload", str(result.status).lower())
    
    def test_breaker_sizing_validation(self):
        """Test circuit breaker sizing validation."""
        # Test properly sized breaker
        result = self.power_validator.validate_breaker_sizing(15, 20)
        self.assertTrue(result["valid"])
        self.assertEqual(result["status"], "normal")
        
        # Test overloaded breaker
        result = self.power_validator.validate_breaker_sizing(25, 20)
        self.assertFalse(result["valid"])
        self.assertEqual(result["status"], "overloaded")
        
        # Test near capacity breaker
        result = self.power_validator.validate_breaker_sizing(18, 20)
        self.assertTrue(result["valid"])
        self.assertEqual(result["status"], "near_capacity")
    
    def test_wire_sizing_validation(self):
        """Test wire sizing validation."""
        # Test properly sized wire
        result = self.power_validator.validate_wire_sizing(15, 12)  # 15A on 12 AWG
        self.assertTrue(result["valid"])
        self.assertEqual(result["status"], "properly_sized")
        
        # Test undersized wire
        result = self.power_validator.validate_wire_sizing(25, 14)  # 25A on 14 AWG
        self.assertFalse(result["valid"])
        self.assertEqual(result["status"], "oversized")
    
    def test_voltage_drop_calculation(self):
        """Test voltage drop calculations."""
        # Test voltage drop calculation
        voltage_drop = self.power_validator.calculate_voltage_drop(10, 0.1)
        self.assertEqual(voltage_drop, 1.0)  # 10A * 0.1Ω = 1V
        
        # Test with zero current
        voltage_drop = self.power_validator.calculate_voltage_drop(0, 0.1)
        self.assertEqual(voltage_drop, 0.0)
    
    def test_conductor_resistance_calculation(self):
        """Test conductor resistance calculations."""
        # Test copper conductor resistance
        resistance = self.power_validator.calculate_conductor_resistance(100, 3.31)  # 12 AWG
        self.assertGreater(resistance, 0)
        
        # Test aluminum conductor resistance
        resistance_al = self.power_validator.calculate_conductor_resistance(100, 3.31, "aluminum")
        self.assertGreater(resistance_al, resistance)  # Aluminum has higher resistivity
    
    def test_power_factor_calculation(self):
        """Test power factor calculations."""
        # Test unity power factor
        pf = self.power_validator.calculate_power_factor(1000, 1000)
        self.assertEqual(pf, 1.0)
        
        # Test lagging power factor
        pf = self.power_validator.calculate_power_factor(800, 1000)
        self.assertEqual(pf, 0.8)
        
        # Test zero apparent power
        pf = self.power_validator.calculate_power_factor(1000, 0)
        self.assertEqual(pf, 0.0)
    
    def test_short_circuit_current_calculation(self):
        """Test short circuit current calculations."""
        # Test normal impedance
        scc = self.power_validator.calculate_short_circuit_current(120, 0.1)
        self.assertEqual(scc, 1200)  # 120V / 0.1Ω = 1200A
        
        # Test zero impedance (infinite current)
        scc = self.power_validator.calculate_short_circuit_current(120, 0)
        self.assertEqual(scc, float('inf'))
    
    def test_ground_fault_protection(self):
        """Test ground fault protection validation."""
        # Test normal ground fault current
        result = self.power_validator.validate_ground_fault_protection(5, 30)
        self.assertTrue(result["valid"])
        self.assertEqual(result["status"], "normal")
        
        # Test excessive ground fault current
        result = self.power_validator.validate_ground_fault_protection(50, 30)
        self.assertFalse(result["valid"])
        self.assertEqual(result["status"], "trip")
    
    def test_electrical_chain_propagation(self):
        """Test electrical chain propagation."""
        # Add electrical system objects to chain manager
        for component_id, component_data in self.mock_electrical_system["components"].items():
            self.chain_manager.add_object(component_data)
        
        # Create links between components
        self.chain_manager.create_link("transformer_01", "main_panel", "power_supply")
        self.chain_manager.create_link("main_panel", "sub_panel_01", "power_distribution")
        self.chain_manager.create_link("sub_panel_01", "lighting_circuit_01", "circuit_supply")
        self.chain_manager.create_link("lighting_circuit_01", "light_fixture_01", "load_connection")
        
        # Test power flow simulation
        results = self.chain_manager.simulate_chain_behavior(
            "transformer_01", "power_flow", {"source_voltage": 480, "source_current": 100}
        )
        
        self.assertIsNotNone(results)
        self.assertIn("power_flow_results", results)
        self.assertGreater(len(results["power_flow_results"]), 0)
    
    def test_fault_propagation(self):
        """Test fault propagation through electrical system."""
        # Add electrical system objects to chain manager
        for component_id, component_data in self.mock_electrical_system["components"].items():
            self.chain_manager.add_object(component_data)
        
        # Create links
        self.chain_manager.create_link("main_panel", "sub_panel_01", "power_distribution")
        self.chain_manager.create_link("sub_panel_01", "lighting_circuit_01", "circuit_supply")
        
        # Test fault propagation
        results = self.chain_manager.simulate_chain_behavior(
            "main_panel", "fault_propagation", 
            {"fault_type": "open_circuit", "fault_severity": "critical"}
        )
        
        self.assertIsNotNone(results)
        self.assertIn("fault_propagation_results", results)
        self.assertGreater(len(results["fault_propagation_results"]), 0)
    
    def test_rule_engine_electrical_validation(self):
        """Test rule engine electrical validation."""
        # Test electrical object validation
        electrical_object = {
            "id": "test_panel",
            "system_type": "electrical",
            "type": "panel",
            "properties": {
                "voltage": 208,
                "current": 150,
                "power": 31200,
                "efficiency": 0.95
            },
            "connections": ["circuit_01", "circuit_02"]
        }
        
        results = self.rule_engine.validate_object(electrical_object)
        
        self.assertIsNotNone(results)
        self.assertGreater(len(results), 0)
        
        # Check for power flow validation
        power_flow_results = [r for r in results if "power_flow" in r.message.lower()]
        self.assertGreater(len(power_flow_results), 0)
    
    def test_behavior_profile_validation(self):
        """Test behavior profile validation."""
        # Test panel behavior profile
        panel_profile = self.electrical_profiles.get("power_distribution", {}).get("panel", {})
        
        self.assertIsNotNone(panel_profile)
        self.assertEqual(panel_profile.get("system_type"), "electrical")
        self.assertEqual(panel_profile.get("category"), "power_distribution")
        
        # Test variables exist
        variables = panel_profile.get("variables", {})
        self.assertIn("voltage", variables)
        self.assertIn("current_capacity", variables)
        self.assertIn("phase_count", variables)
    
    def test_complex_electrical_system(self):
        """Test complex electrical system simulation."""
        # Create complex electrical system
        complex_system = {
            "main_service": {
                "id": "main_service",
                "type": "service_entrance",
                "system_type": "electrical",
                "properties": {
                    "voltage": 480,
                    "current": 200,
                    "power": 96000
                }
            },
            "transformer_bank": {
                "id": "transformer_bank",
                "type": "transformer",
                "system_type": "electrical",
                "properties": {
                    "primary_voltage": 480,
                    "secondary_voltage": 208,
                    "rated_power": 150,
                    "efficiency": 0.98
                }
            },
            "distribution_panel": {
                "id": "distribution_panel",
                "type": "panel",
                "system_type": "electrical",
                "properties": {
                    "voltage": 208,
                    "current": 150,
                    "power": 31200,
                    "efficiency": 0.95
                }
            }
        }
        
        # Add objects to chain manager
        for component_id, component_data in complex_system.items():
            self.chain_manager.add_object(component_data)
        
        # Create links
        self.chain_manager.create_link("main_service", "transformer_bank", "power_supply")
        self.chain_manager.create_link("transformer_bank", "distribution_panel", "power_distribution")
        
        # Test power flow simulation
        results = self.chain_manager.simulate_chain_behavior(
            "main_service", "power_flow", 
            {"source_voltage": 480, "source_current": 200}
        )
        
        self.assertIsNotNone(results)
        self.assertIn("power_flow_results", results)
        self.assertGreater(len(results["power_flow_results"]), 0)
        
        # Test state propagation
        state_results = self.chain_manager.simulate_chain_behavior(
            "main_service", "state_propagation",
            {"new_state": "warning", "reason": "high_load"}
        )
        
        self.assertIsNotNone(state_results)
        self.assertIn("state_propagation_results", state_results)
    
    def test_electrical_safety_validation(self):
        """Test electrical safety validation."""
        # Test safety features validation
        safety_object = {
            "id": "safety_panel",
            "system_type": "electrical",
            "type": "panel",
            "properties": {
                "voltage": 120,
                "current": 20,
                "power": 2400
            },
            "safety_features": ["ground_fault_protection", "overcurrent_protection"],
            "required_safety_features": ["ground_fault_protection", "overcurrent_protection"]
        }
        
        results = self.rule_engine.validate_object(safety_object)
        
        # Should not have safety validation errors
        safety_errors = [r for r in results if "safety" in r.message.lower() and r.severity == Severity.ERROR]
        self.assertEqual(len(safety_errors), 0)
    
    def test_electrical_code_compliance(self):
        """Test electrical code compliance validation."""
        # Test code compliant object
        compliant_object = {
            "id": "compliant_panel",
            "system_type": "electrical",
            "type": "panel",
            "properties": {
                "voltage": 120,
                "current": 20,
                "power": 2400
            },
            "code_requirements": {
                "voltage": {"max": 150, "min": 100},
                "current": {"max": 30, "min": 0}
            },
            "specifications": {
                "voltage": 120,
                "current": 20
            }
        }
        
        results = self.rule_engine.validate_object(compliant_object)
        
        # Should not have code compliance errors
        code_errors = [r for r in results if "code" in r.message.lower() and r.severity == Severity.ERROR]
        self.assertEqual(len(code_errors), 0)
    
    def test_electrical_efficiency_validation(self):
        """Test electrical efficiency validation."""
        # Test efficient system
        efficient_object = {
            "id": "efficient_panel",
            "system_type": "electrical",
            "type": "panel",
            "properties": {
                "voltage": 120,
                "current": 20,
                "power": 2400,
                "efficiency": 0.98
            },
            "min_efficiency": 0.95
        }
        
        results = self.rule_engine.validate_object(efficient_object)
        
        # Should not have efficiency warnings
        efficiency_warnings = [r for r in results if "efficiency" in r.message.lower() and r.severity == Severity.WARNING]
        self.assertEqual(len(efficiency_warnings), 0)
    
    def test_electrical_chain_integrity(self):
        """Test electrical chain integrity validation."""
        # Add electrical system objects
        for component_id, component_data in self.mock_electrical_system["components"].items():
            self.chain_manager.add_object(component_data)
        
        # Create valid links
        self.chain_manager.create_link("transformer_01", "main_panel", "power_supply")
        self.chain_manager.create_link("main_panel", "sub_panel_01", "power_distribution")
        
        # Test chain integrity
        integrity_results = self.chain_manager.validate_chain_integrity()
        
        self.assertIsNotNone(integrity_results)
        self.assertTrue(integrity_results["validation_passed"])
        self.assertEqual(len(integrity_results["orphaned_objects"]), 0)
        self.assertEqual(len(integrity_results["broken_links"]), 0)
        self.assertEqual(len(integrity_results["circular_dependencies"]), 0)


if __name__ == '__main__':
    unittest.main() 