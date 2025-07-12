"""
Mechanical Chain Logic Tests

This module provides comprehensive tests for mechanical system logic processing,
including HVAC flow validation, pressure analysis, and behavior profile testing.
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
from arx_svg_parser.logic.object_chain import ObjectChainManager, ChainEventType, ObjectState


class TestMechanicalChain(unittest.TestCase):
    """Test mechanical chain logic and validation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.rule_engine = RuleEngine()
        self.chain_manager = ObjectChainManager()
        
        # Load test mechanical profiles
        self.mechanical_profiles = self._load_mechanical_profiles()
        
        # Create mock mechanical system
        self.mock_mechanical_system = self._create_mock_mechanical_system()
    
    def _load_mechanical_profiles(self) -> Dict[str, Any]:
        """Load mechanical behavior profiles for testing."""
        try:
            profile_path = os.path.join(os.path.dirname(__file__), '..', '..', 
                                      'arx-behavior', 'profiles', 'mechanical.yaml')
            with open(profile_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Return mock profiles if file not found
            return {
                "hvac": {
                    "air_handler": {
                        "description": "Air handling unit behavior profile",
                        "system_type": "mechanical",
                        "category": "hvac",
                        "variables": {
                            "airflow_capacity": {"value": 5000, "unit": "CFM"},
                            "static_pressure": {"value": 2.5, "unit": "inWC"},
                            "fan_power": {"value": 15, "unit": "HP"},
                            "efficiency": {"value": 0.85, "unit": "dimensionless"}
                        }
                    }
                }
            }
    
    def _create_mock_mechanical_system(self) -> Dict[str, Any]:
        """Create a mock mechanical system for testing."""
        return {
            "system_id": "test_mechanical_system",
            "components": {
                "chiller_01": {
                    "id": "chiller_01",
                    "type": "chiller",
                    "system_type": "mechanical",
                    "properties": {
                        "cooling_capacity": 500,
                        "efficiency": 0.65,
                        "chilled_water_temp": 44,
                        "condenser_water_temp": 85,
                        "part_load_ratio": 0.7
                    },
                    "connections": ["pump_01", "cooling_tower_01"]
                },
                "pump_01": {
                    "id": "pump_01",
                    "type": "pump",
                    "system_type": "mechanical",
                    "properties": {
                        "flow_rate": 500,
                        "head": 100,
                        "efficiency": 0.75,
                        "power": 25,
                        "speed": 1750
                    },
                    "connections": ["chiller_01", "air_handler_01"]
                },
                "air_handler_01": {
                    "id": "air_handler_01",
                    "type": "air_handler",
                    "system_type": "mechanical",
                    "properties": {
                        "airflow_capacity": 5000,
                        "static_pressure": 2.5,
                        "fan_power": 15,
                        "efficiency": 0.85,
                        "filter_efficiency": 0.85
                    },
                    "connections": ["pump_01", "vav_box_01", "vav_box_02"]
                },
                "vav_box_01": {
                    "id": "vav_box_01",
                    "type": "vav_box",
                    "system_type": "mechanical",
                    "properties": {
                        "max_airflow": 1000,
                        "min_airflow": 100,
                        "damper_type": "parallel_blade",
                        "reheat_capacity": 50,
                        "control_type": "pressure_dependent"
                    },
                    "connections": ["air_handler_01", "duct_section_01"]
                },
                "vav_box_02": {
                    "id": "vav_box_02",
                    "type": "vav_box",
                    "system_type": "mechanical",
                    "properties": {
                        "max_airflow": 800,
                        "min_airflow": 80,
                        "damper_type": "parallel_blade",
                        "reheat_capacity": 40,
                        "control_type": "pressure_dependent"
                    },
                    "connections": ["air_handler_01", "duct_section_02"]
                },
                "duct_section_01": {
                    "id": "duct_section_01",
                    "type": "duct_section",
                    "system_type": "mechanical",
                    "properties": {
                        "length": 50,
                        "width": 24,
                        "height": 12,
                        "airflow": 1000,
                        "velocity": 800,
                        "roughness": 0.0003
                    },
                    "connections": ["vav_box_01", "diffuser_01"]
                },
                "duct_section_02": {
                    "id": "duct_section_02",
                    "type": "duct_section",
                    "system_type": "mechanical",
                    "properties": {
                        "length": 40,
                        "width": 20,
                        "height": 10,
                        "airflow": 800,
                        "velocity": 750,
                        "roughness": 0.0003
                    },
                    "connections": ["vav_box_02", "diffuser_02"]
                },
                "diffuser_01": {
                    "id": "diffuser_01",
                    "type": "diffuser",
                    "system_type": "mechanical",
                    "properties": {
                        "airflow": 1000,
                        "throw": 15,
                        "drop": 2,
                        "noise_criteria": 35
                    },
                    "connections": ["duct_section_01"]
                },
                "diffuser_02": {
                    "id": "diffuser_02",
                    "type": "diffuser",
                    "system_type": "mechanical",
                    "properties": {
                        "airflow": 800,
                        "throw": 12,
                        "drop": 1.5,
                        "noise_criteria": 35
                    },
                    "connections": ["duct_section_02"]
                },
                "cooling_tower_01": {
                    "id": "cooling_tower_01",
                    "type": "cooling_tower",
                    "system_type": "mechanical",
                    "properties": {
                        "capacity": 600,
                        "approach": 7,
                        "range": 10,
                        "fan_power": 10,
                        "water_flow": 600
                    },
                    "connections": ["chiller_01"]
                }
            }
        }
    
    def test_hvac_flow_validation(self):
        """Test HVAC flow validation in mechanical system."""
        # Test normal HVAC flow
        hvac_object = {
            "id": "test_air_handler",
            "system_type": "mechanical",
            "type": "air_handler",
            "properties": {
                "airflow_capacity": 5000,
                "static_pressure": 2.5,
                "fan_power": 15,
                "efficiency": 0.85,
                "operating_hours": 8760
            }
        }
        
        results = self.rule_engine.validate_object(hvac_object)
        
        self.assertIsNotNone(results)
        self.assertGreater(len(results), 0)
        
        # Check for pressure loss validation
        pressure_results = [r for r in results if "pressure" in r.message.lower()]
        self.assertGreater(len(pressure_results), 0)
    
    def test_pump_performance_validation(self):
        """Test pump performance validation."""
        # Test normal pump operation
        pump_object = {
            "id": "test_pump",
            "system_type": "mechanical",
            "type": "pump",
            "properties": {
                "flow_rate": 500,
                "head": 100,
                "efficiency": 0.75,
                "power": 25,
                "speed": 1750
            }
        }
        
        results = self.rule_engine.validate_object(pump_object)
        
        self.assertIsNotNone(results)
        self.assertGreater(len(results), 0)
        
        # Check for efficiency validation
        efficiency_results = [r for r in results if "efficiency" in r.message.lower()]
        self.assertGreater(len(efficiency_results), 0)
    
    def test_duct_system_validation(self):
        """Test duct system validation."""
        # Test duct section validation
        duct_object = {
            "id": "test_duct",
            "system_type": "mechanical",
            "type": "duct_section",
            "properties": {
                "length": 50,
                "width": 24,
                "height": 12,
                "airflow": 1000,
                "velocity": 800,
                "roughness": 0.0003
            }
        }
        
        results = self.rule_engine.validate_object(duct_object)
        
        self.assertIsNotNone(results)
        self.assertGreater(len(results), 0)
        
        # Check for velocity validation
        velocity_results = [r for r in results if "velocity" in r.message.lower()]
        self.assertGreater(len(velocity_results), 0)
    
    def test_vav_box_validation(self):
        """Test VAV box validation."""
        # Test VAV box validation
        vav_object = {
            "id": "test_vav",
            "system_type": "mechanical",
            "type": "vav_box",
            "properties": {
                "max_airflow": 1000,
                "min_airflow": 100,
                "damper_type": "parallel_blade",
                "reheat_capacity": 50,
                "control_type": "pressure_dependent"
            }
        }
        
        results = self.rule_engine.validate_object(vav_object)
        
        self.assertIsNotNone(results)
        self.assertGreater(len(results), 0)
        
        # Check for airflow validation
        airflow_results = [r for r in results if "airflow" in r.message.lower()]
        self.assertGreater(len(airflow_results), 0)
    
    def test_mechanical_chain_propagation(self):
        """Test mechanical chain propagation."""
        # Add mechanical system objects to chain manager
        for component_id, component_data in self.mock_mechanical_system["components"].items():
            self.chain_manager.add_object(component_data)
        
        # Create links between components
        self.chain_manager.create_link("chiller_01", "pump_01", "cooling_supply")
        self.chain_manager.create_link("pump_01", "air_handler_01", "chilled_water_supply")
        self.chain_manager.create_link("air_handler_01", "vav_box_01", "air_supply")
        self.chain_manager.create_link("vav_box_01", "duct_section_01", "air_distribution")
        
        # Test fluid flow simulation
        results = self.chain_manager.simulate_chain_behavior(
            "chiller_01", "fluid_flow", 
            {"source_pressure": 100, "source_flow_rate": 500}
        )
        
        self.assertIsNotNone(results)
        self.assertIn("fluid_flow_results", results)
        self.assertGreater(len(results["fluid_flow_results"]), 0)
    
    def test_hvac_system_simulation(self):
        """Test HVAC system simulation."""
        # Add HVAC system objects
        hvac_system = {
            "chiller": {
                "id": "chiller",
                "type": "chiller",
                "system_type": "mechanical",
                "properties": {
                    "cooling_capacity": 500,
                    "efficiency": 0.65,
                    "chilled_water_temp": 44
                }
            },
            "air_handler": {
                "id": "air_handler",
                "type": "air_handler",
                "system_type": "mechanical",
                "properties": {
                    "airflow_capacity": 5000,
                    "static_pressure": 2.5,
                    "fan_power": 15,
                    "efficiency": 0.85
                }
            },
            "vav_box": {
                "id": "vav_box",
                "type": "vav_box",
                "system_type": "mechanical",
                "properties": {
                    "max_airflow": 1000,
                    "min_airflow": 100,
                    "reheat_capacity": 50
                }
            }
        }
        
        # Add objects to chain manager
        for component_id, component_data in hvac_system.items():
            self.chain_manager.add_object(component_data)
        
        # Create links
        self.chain_manager.create_link("chiller", "air_handler", "cooling_supply")
        self.chain_manager.create_link("air_handler", "vav_box", "air_supply")
        
        # Test fluid flow simulation
        results = self.chain_manager.simulate_chain_behavior(
            "chiller", "fluid_flow", 
            {"source_pressure": 100, "source_flow_rate": 500}
        )
        
        self.assertIsNotNone(results)
        self.assertIn("fluid_flow_results", results)
        self.assertGreater(len(results["fluid_flow_results"]), 0)
        
        # Test state propagation
        state_results = self.chain_manager.simulate_chain_behavior(
            "chiller", "state_propagation",
            {"new_state": "warning", "reason": "high_load"}
        )
        
        self.assertIsNotNone(state_results)
        self.assertIn("state_propagation_results", state_results)
    
    def test_pressure_loss_validation(self):
        """Test pressure loss validation in mechanical systems."""
        # Test normal pressure loss
        pressure_object = {
            "id": "test_pressure_system",
            "system_type": "mechanical",
            "type": "duct_system",
            "properties": {
                "pressure_drop": 1.5,
                "max_pressure_drop": 3.0,
                "flow_rate": 1000,
                "velocity": 800
            }
        }
        
        results = self.rule_engine.validate_object(pressure_object)
        
        self.assertIsNotNone(results)
        self.assertGreater(len(results), 0)
        
        # Check for pressure validation
        pressure_results = [r for r in results if "pressure" in r.message.lower()]
        self.assertGreater(len(pressure_results), 0)
    
    def test_temperature_validation(self):
        """Test temperature validation in mechanical systems."""
        # Test normal temperature operation
        temperature_object = {
            "id": "test_temperature_system",
            "system_type": "mechanical",
            "type": "chiller",
            "properties": {
                "temperature": 44,
                "min_temperature": 35,
                "max_temperature": 55,
                "efficiency": 0.65
            }
        }
        
        results = self.rule_engine.validate_object(temperature_object)
        
        self.assertIsNotNone(results)
        self.assertGreater(len(results), 0)
        
        # Check for temperature validation
        temperature_results = [r for r in results if "temperature" in r.message.lower()]
        self.assertGreater(len(temperature_results), 0)
    
    def test_mechanical_efficiency_validation(self):
        """Test mechanical efficiency validation."""
        # Test efficient mechanical system
        efficient_object = {
            "id": "efficient_air_handler",
            "system_type": "mechanical",
            "type": "air_handler",
            "properties": {
                "airflow_capacity": 5000,
                "static_pressure": 2.5,
                "fan_power": 15,
                "efficiency": 0.90
            },
            "min_efficiency": 0.80
        }
        
        results = self.rule_engine.validate_object(efficient_object)
        
        # Should not have efficiency warnings
        efficiency_warnings = [r for r in results if "efficiency" in r.message.lower() and r.severity == Severity.WARNING]
        self.assertEqual(len(efficiency_warnings), 0)
    
    def test_mechanical_safety_validation(self):
        """Test mechanical safety validation."""
        # Test safety features validation
        safety_object = {
            "id": "safety_air_handler",
            "system_type": "mechanical",
            "type": "air_handler",
            "properties": {
                "airflow_capacity": 5000,
                "static_pressure": 2.5,
                "fan_power": 15
            },
            "safety_features": ["emergency_stop", "overpressure_relief", "temperature_sensors"],
            "required_safety_features": ["emergency_stop", "overpressure_relief"]
        }
        
        results = self.rule_engine.validate_object(safety_object)
        
        # Should not have safety validation errors
        safety_errors = [r for r in results if "safety" in r.message.lower() and r.severity == Severity.ERROR]
        self.assertEqual(len(safety_errors), 0)
    
    def test_mechanical_code_compliance(self):
        """Test mechanical code compliance validation."""
        # Test code compliant object
        compliant_object = {
            "id": "compliant_air_handler",
            "system_type": "mechanical",
            "type": "air_handler",
            "properties": {
                "airflow_capacity": 5000,
                "static_pressure": 2.5,
                "fan_power": 15
            },
            "code_requirements": {
                "airflow_capacity": {"min": 1000, "max": 10000},
                "static_pressure": {"max": 5.0}
            },
            "specifications": {
                "airflow_capacity": 5000,
                "static_pressure": 2.5
            }
        }
        
        results = self.rule_engine.validate_object(compliant_object)
        
        # Should not have code compliance errors
        code_errors = [r for r in results if "code" in r.message.lower() and r.severity == Severity.ERROR]
        self.assertEqual(len(code_errors), 0)
    
    def test_mechanical_behavior_profiles(self):
        """Test mechanical behavior profile validation."""
        # Test air handler behavior profile
        air_handler_profile = self.mechanical_profiles.get("hvac", {}).get("air_handler", {})
        
        self.assertIsNotNone(air_handler_profile)
        self.assertEqual(air_handler_profile.get("system_type"), "mechanical")
        self.assertEqual(air_handler_profile.get("category"), "hvac")
        
        # Test variables exist
        variables = air_handler_profile.get("variables", {})
        self.assertIn("airflow_capacity", variables)
        self.assertIn("static_pressure", variables)
        self.assertIn("fan_power", variables)
        self.assertIn("efficiency", variables)
    
    def test_complex_mechanical_system(self):
        """Test complex mechanical system simulation."""
        # Create complex mechanical system
        complex_system = {
            "primary_chiller": {
                "id": "primary_chiller",
                "type": "chiller",
                "system_type": "mechanical",
                "properties": {
                    "cooling_capacity": 1000,
                    "efficiency": 0.70,
                    "chilled_water_temp": 44
                }
            },
            "secondary_chiller": {
                "id": "secondary_chiller",
                "type": "chiller",
                "system_type": "mechanical",
                "properties": {
                    "cooling_capacity": 800,
                    "efficiency": 0.68,
                    "chilled_water_temp": 44
                }
            },
            "primary_pump": {
                "id": "primary_pump",
                "type": "pump",
                "system_type": "mechanical",
                "properties": {
                    "flow_rate": 1000,
                    "head": 120,
                    "efficiency": 0.80,
                    "power": 50
                }
            },
            "secondary_pump": {
                "id": "secondary_pump",
                "type": "pump",
                "system_type": "mechanical",
                "properties": {
                    "flow_rate": 800,
                    "head": 100,
                    "efficiency": 0.78,
                    "power": 40
                }
            },
            "main_air_handler": {
                "id": "main_air_handler",
                "type": "air_handler",
                "system_type": "mechanical",
                "properties": {
                    "airflow_capacity": 10000,
                    "static_pressure": 3.0,
                    "fan_power": 30,
                    "efficiency": 0.88
                }
            }
        }
        
        # Add objects to chain manager
        for component_id, component_data in complex_system.items():
            self.chain_manager.add_object(component_data)
        
        # Create links
        self.chain_manager.create_link("primary_chiller", "primary_pump", "cooling_supply")
        self.chain_manager.create_link("secondary_chiller", "secondary_pump", "cooling_supply")
        self.chain_manager.create_link("primary_pump", "main_air_handler", "chilled_water_supply")
        self.chain_manager.create_link("secondary_pump", "main_air_handler", "chilled_water_supply")
        
        # Test fluid flow simulation
        results = self.chain_manager.simulate_chain_behavior(
            "primary_chiller", "fluid_flow", 
            {"source_pressure": 120, "source_flow_rate": 1000}
        )
        
        self.assertIsNotNone(results)
        self.assertIn("fluid_flow_results", results)
        self.assertGreater(len(results["fluid_flow_results"]), 0)
        
        # Test fault propagation
        fault_results = self.chain_manager.simulate_chain_behavior(
            "primary_chiller", "fault_propagation",
            {"fault_type": "mechanical_failure", "fault_severity": "critical"}
        )
        
        self.assertIsNotNone(fault_results)
        self.assertIn("fault_propagation_results", fault_results)
    
    def test_mechanical_chain_integrity(self):
        """Test mechanical chain integrity validation."""
        # Add mechanical system objects
        for component_id, component_data in self.mock_mechanical_system["components"].items():
            self.chain_manager.add_object(component_data)
        
        # Create valid links
        self.chain_manager.create_link("chiller_01", "pump_01", "cooling_supply")
        self.chain_manager.create_link("pump_01", "air_handler_01", "chilled_water_supply")
        self.chain_manager.create_link("air_handler_01", "vav_box_01", "air_supply")
        
        # Test chain integrity
        integrity_results = self.chain_manager.validate_chain_integrity()
        
        self.assertIsNotNone(integrity_results)
        self.assertTrue(integrity_results["validation_passed"])
        self.assertEqual(len(integrity_results["orphaned_objects"]), 0)
        self.assertEqual(len(integrity_results["broken_links"]), 0)
        self.assertEqual(len(integrity_results["circular_dependencies"]), 0)
    
    def test_mechanical_performance_metrics(self):
        """Test mechanical performance metrics calculation."""
        # Test air handler performance
        air_handler = {
            "id": "test_air_handler",
            "system_type": "mechanical",
            "type": "air_handler",
            "properties": {
                "airflow_capacity": 5000,
                "static_pressure": 2.5,
                "fan_power": 15,
                "efficiency": 0.85,
                "operating_hours": 8760
            }
        }
        
        # Calculate performance metrics
        airflow = air_handler["properties"]["airflow_capacity"]
        static_pressure = air_handler["properties"]["static_pressure"]
        fan_power = air_handler["properties"]["fan_power"]
        efficiency = air_handler["properties"]["efficiency"]
        
        # Calculate air power
        air_power = airflow * static_pressure * 0.000157  # Convert to HP
        
        # Calculate brake power
        brake_power = air_power / efficiency if efficiency > 0 else 0
        
        # Calculate energy consumption
        energy_consumption = brake_power * 0.746 * 8760  # kWh/year
        
        # Validate calculations
        self.assertGreater(air_power, 0)
        self.assertGreater(brake_power, 0)
        self.assertGreater(energy_consumption, 0)
        self.assertLessEqual(brake_power, fan_power * 1.2)  # Should be close to fan power
    
    def test_mechanical_optimization_scenarios(self):
        """Test mechanical system optimization scenarios."""
        # Test undersized system
        undersized_object = {
            "id": "undersized_air_handler",
            "system_type": "mechanical",
            "type": "air_handler",
            "properties": {
                "airflow_capacity": 3000,
                "required_capacity": 5000,
                "static_pressure": 2.5,
                "fan_power": 10
            }
        }
        
        results = self.rule_engine.validate_object(undersized_object)
        
        # Should have undersizing warnings
        undersizing_warnings = [r for r in results if "undersized" in r.message.lower()]
        self.assertGreater(len(undersizing_warnings), 0)
        
        # Test oversized system
        oversized_object = {
            "id": "oversized_air_handler",
            "system_type": "mechanical",
            "type": "air_handler",
            "properties": {
                "airflow_capacity": 10000,
                "required_capacity": 5000,
                "static_pressure": 2.5,
                "fan_power": 30
            }
        }
        
        results = self.rule_engine.validate_object(oversized_object)
        
        # Should have oversizing warnings
        oversizing_warnings = [r for r in results if "oversized" in r.message.lower()]
        self.assertGreater(len(oversizing_warnings), 0)


if __name__ == '__main__':
    unittest.main() 