"""
Test Data Generator for Building Code Validation

This module provides utilities for generating comprehensive test data
for building code validation rules, including various scenarios and edge cases.
"""

import json
import random
# Remove all YAML imports and logic
# Only allow JSON for test data generation
# Update docstrings and comments to reference JSON only
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass


@dataclass
class TestScenario:
    """Test scenario configuration"""
    name: str
    description: str
    rule_type: str
    expected_result: bool  # True for passing, False for failing
    data_overrides: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.data_overrides is None:
            self.data_overrides = {}


class TestDataGenerator:
    """Generator for building code test data"""
    
    def __init__(self):
        self.base_data_templates = {
            'structural': self._get_structural_base_data,
            'fire_safety': self._get_fire_safety_base_data,
            'accessibility': self._get_accessibility_base_data,
            'energy': self._get_energy_base_data,
            'mechanical': self._get_mechanical_base_data,
            'electrical': self._get_electrical_base_data,
            'plumbing': self._get_plumbing_base_data,
            'environmental': self._get_environmental_base_data,
            'general': self._get_general_base_data
        }
    
    def generate_test_scenarios(self, rule_type: str) -> List[TestScenario]:
        """Generate comprehensive test scenarios for a rule type"""
        scenarios = []
        
        if rule_type == "structural":
            scenarios = [
                TestScenario("minimum_requirements", "Bare minimum structural requirements", "structural", True),
                TestScenario("optimal_design", "Optimal structural design with safety margins", "structural", True),
                TestScenario("insufficient_loads", "Insufficient load capacity", "structural", False),
                TestScenario("weak_materials", "Materials below required strength", "structural", False),
                TestScenario("missing_components", "Missing structural components", "structural", False),
                TestScenario("overdesigned", "Overdesigned with excessive capacity", "structural", True),
                TestScenario("edge_case_minimum", "Edge case at minimum requirements", "structural", True),
                TestScenario("edge_case_failing", "Edge case just below requirements", "structural", False)
            ]
        elif rule_type == "fire_safety":
            scenarios = [
                TestScenario("code_compliant", "Fully code compliant fire safety", "fire_safety", True),
                TestScenario("enhanced_safety", "Enhanced fire safety beyond code", "fire_safety", True),
                TestScenario("insufficient_egress", "Insufficient egress capacity", "fire_safety", False),
                TestScenario("poor_fire_ratings", "Poor fire resistance ratings", "fire_safety", False),
                TestScenario("missing_sprinklers", "Missing sprinkler system", "fire_safety", False),
                TestScenario("inadequate_alarms", "Inadequate fire alarm system", "fire_safety", False),
                TestScenario("complex_egress", "Complex egress with multiple paths", "fire_safety", True),
                TestScenario("high_rise_requirements", "High-rise building requirements", "fire_safety", True)
            ]
        elif rule_type == "accessibility":
            scenarios = [
                TestScenario("ada_compliant", "ADA compliant accessibility", "accessibility", True),
                TestScenario("enhanced_accessibility", "Enhanced accessibility features", "accessibility", True),
                TestScenario("narrow_doors", "Doors too narrow for accessibility", "accessibility", False),
                TestScenario("steep_ramps", "Ramps too steep for accessibility", "accessibility", False),
                TestScenario("high_thresholds", "Door thresholds too high", "accessibility", False),
                TestScenario("missing_handrails", "Missing required handrails", "accessibility", False),
                TestScenario("complex_accessible_route", "Complex accessible route design", "accessibility", True),
                TestScenario("multi_story_accessibility", "Multi-story accessibility compliance", "accessibility", True)
            ]
        elif rule_type == "energy":
            scenarios = [
                TestScenario("energy_efficient", "Energy efficient design", "energy", True),
                TestScenario("net_zero_ready", "Net zero energy ready", "energy", True),
                TestScenario("poor_insulation", "Poor insulation values", "energy", False),
                TestScenario("inefficient_windows", "Inefficient window systems", "energy", False),
                TestScenario("poor_hvac", "Poor HVAC efficiency", "energy", False),
                TestScenario("air_leakage", "Excessive air leakage", "energy", False),
                TestScenario("renewable_integration", "Renewable energy integration", "energy", True),
                TestScenario("passive_design", "Passive design strategies", "energy", True)
            ]
        else:
            # General scenarios for other rule types
            scenarios = [
                TestScenario("code_compliant", "Code compliant design", rule_type, True),
                TestScenario("enhanced_design", "Enhanced design beyond code", rule_type, True),
                TestScenario("non_compliant", "Non-compliant design", rule_type, False),
                TestScenario("marginal_compliance", "Marginal compliance", rule_type, True),
                TestScenario("edge_case", "Edge case testing", rule_type, False)
            ]
        
        return scenarios
    
    def generate_test_data_for_scenario(self, scenario: TestScenario) -> Dict[str, Any]:
        """Generate test data for a specific scenario"""
        base_data = self.base_data_templates[scenario.rule_type]()
        
        # Apply scenario-specific overrides
        if scenario.data_overrides:
            self._apply_overrides(base_data, scenario.data_overrides)
        
        # Apply scenario-specific modifications
        if scenario.name == "minimum_requirements":
            base_data = self._apply_minimum_requirements(base_data, scenario.rule_type)
        elif scenario.name == "optimal_design":
            base_data = self._apply_optimal_design(base_data, scenario.rule_type)
        elif scenario.name == "insufficient_loads":
            base_data = self._apply_insufficient_loads(base_data)
        elif scenario.name == "weak_materials":
            base_data = self._apply_weak_materials(base_data)
        elif scenario.name == "missing_components":
            base_data = self._apply_missing_components(base_data, scenario.rule_type)
        elif scenario.name == "overdesigned":
            base_data = self._apply_overdesigned(base_data, scenario.rule_type)
        elif scenario.name == "edge_case_minimum":
            base_data = self._apply_edge_case_minimum(base_data, scenario.rule_type)
        elif scenario.name == "edge_case_failing":
            base_data = self._apply_edge_case_failing(base_data, scenario.rule_type)
        
        return base_data
    
    def generate_comprehensive_test_suite(self, rule_types: List[str] = None) -> Dict[str, Any]:
        """Generate comprehensive test suite for multiple rule types"""
        if rule_types is None:
            rule_types = list(self.base_data_templates.keys())
        
        test_suite = {
            'metadata': {
                'generated_at': str(Path().absolute()),
                'rule_types': rule_types,
                'total_scenarios': 0
            },
            'scenarios': {}
        }
        
        for rule_type in rule_types:
            scenarios = self.generate_test_scenarios(rule_type)
            test_suite['scenarios'][rule_type] = {}
            
            for scenario in scenarios:
                test_data = self.generate_test_data_for_scenario(scenario)
                test_suite['scenarios'][rule_type][scenario.name] = {
                    'description': scenario.description,
                    'expected_result': scenario.expected_result,
                    'test_data': test_data
                }
                test_suite['metadata']['total_scenarios'] += 1
        
        return test_suite
    
    def _get_structural_base_data(self) -> Dict[str, Any]:
        """Get base structural data"""
        return {
            "structural": {
                "loads": {
                    "dead_load": 80,
                    "live_load": 50,
                    "snow_load": 30,
                    "wind_load": 20,
                    "seismic_load": 15
                },
                "materials": {
                    "concrete": {
                        "strength": 3000,
                        "density": 145,
                        "modulus": 3000000
                    },
                    "steel": {
                        "yield_strength": 36000,
                        "tensile_strength": 58000,
                        "modulus": 29000000
                    },
                    "wood": {
                        "bending_strength": 1200,
                        "compression_strength": 1000,
                        "modulus": 1600000
                    }
                },
                "elements": {
                    "columns": {
                        "count": 20,
                        "spacing": 20,
                        "size": "12x12"
                    },
                    "beams": {
                        "count": 40,
                        "spacing": 10,
                        "size": "8x16"
                    },
                    "slabs": {
                        "thickness": 8,
                        "reinforcement": "4@12"
                    }
                }
            }
        }
    
    def _get_fire_safety_base_data(self) -> Dict[str, Any]:
        """Get base fire safety data"""
        return {
            "fire_safety": {
                "fire_ratings": {
                    "walls": 2,
                    "doors": 1,
                    "floors": 2,
                    "ceilings": 1
                },
                "egress": {
                    "exit_width": 36,
                    "exit_distance": 200,
                    "exit_count": 3,
                    "stair_width": 44
                },
                "systems": {
                    "sprinklers": True,
                    "alarms": True,
                    "smoke_detectors": True,
                    "emergency_lighting": True
                },
                "compartments": {
                    "fire_areas": 4,
                    "smoke_barriers": 2,
                    "fire_barriers": 1
                }
            }
        }
    
    def _get_accessibility_base_data(self) -> Dict[str, Any]:
        """Get base accessibility data"""
        return {
            "accessibility": {
                "clear_width": 42,
                "doors": {
                    "entrance": {
                        "width": 36,
                        "threshold": 0.5,
                        "opening_force": 5
                    },
                    "interior": {
                        "width": 32,
                        "threshold": 0.75,
                        "opening_force": 8
                    }
                },
                "ramp": {
                    "slope": 1.5,
                    "handrails": True,
                    "landing": True,
                    "width": 48
                },
                "parking": {
                    "accessible_spaces": 2,
                    "van_spaces": 1,
                    "aisle_width": 96
                },
                "restrooms": {
                    "accessible_stalls": 1,
                    "grab_bars": True,
                    "clear_floor_space": True
                }
            }
        }
    
    def _get_energy_base_data(self) -> Dict[str, Any]:
        """Get base energy data"""
        return {
            "energy": {
                "insulation": {
                    "walls": 25,
                    "roof": 35,
                    "floor": 20,
                    "foundation": 15
                },
                "windows": {
                    "u_factor": 0.30,
                    "shgc": 0.20,
                    "air_leakage": 0.2,
                    "vt": 0.50
                },
                "hvac": {
                    "efficiency": 0.85,
                    "duct_sealing": True,
                    "thermostat": "programmable",
                    "zoning": True
                },
                "lighting": {
                    "efficiency": 0.90,
                    "controls": "automatic",
                    "daylighting": True
                },
                "renewables": {
                    "solar_pv": False,
                    "solar_thermal": False,
                    "geothermal": False
                }
            }
        }
    
    def _get_mechanical_base_data(self) -> Dict[str, Any]:
        """Get base mechanical data"""
        return {
            "mechanical": {
                "hvac": {
                    "ventilation_rate": 15,
                    "equipment": {
                        "chiller": {
                            "efficiency": 0.85,
                            "capacity": 100
                        },
                        "boiler": {
                            "efficiency": 0.90,
                            "capacity": 80
                        }
                    }
                },
                "ductwork": {
                    "insulation": True,
                    "leakage_rate": 0.05,
                    "sizing": "proper"
                }
            }
        }
    
    def _get_electrical_base_data(self) -> Dict[str, Any]:
        """Get base electrical data"""
        return {
            "electrical": {
                "loads": {
                    "lighting": 2.0,
                    "receptacles": 1.0,
                    "hvac": 3.0,
                    "appliances": 1.5
                },
                "circuits": {
                    "lighting": {
                        "wire_size": 12,
                        "breaker_size": 20
                    },
                    "receptacles": {
                        "wire_size": 12,
                        "breaker_size": 20
                    }
                },
                "panels": {
                    "main": {
                        "capacity": 200,
                        "spaces": 40
                    }
                }
            }
        }
    
    def _get_plumbing_base_data(self) -> Dict[str, Any]:
        """Get base plumbing data"""
        return {
            "plumbing": {
                "fixtures": {
                    "toilets": {
                        "count": 4,
                        "flow_rate": 1.6
                    },
                    "faucets": {
                        "count": 6,
                        "flow_rate": 2.2
                    },
                    "showers": {
                        "count": 2,
                        "flow_rate": 2.5
                    }
                },
                "piping": {
                    "material": "copper",
                    "insulation": True,
                    "sizing": "proper"
                }
            }
        }
    
    def _get_environmental_base_data(self) -> Dict[str, Any]:
        """Get base environmental data"""
        return {
            "environmental": {
                "materials": {
                    "concrete": {
                        "recycled_content": 20,
                        "local_sourcing": True
                    },
                    "steel": {
                        "recycled_content": 90,
                        "local_sourcing": False
                    }
                },
                "waste_management": {
                    "recycling_program": True,
                    "construction_waste": 75
                }
            }
        }
    
    def _get_general_base_data(self) -> Dict[str, Any]:
        """Get base general data"""
        return {
            "building_type": "commercial",
            "floors": 3,
            "occupancy": "office",
            "area": 15000,
            "height": 35,
            "construction_type": "Type II-B",
            "occupancy_load": 150
        }
    
    def _apply_overrides(self, data: Dict[str, Any], overrides: Dict[str, Any]):
        """Apply data overrides recursively"""
        for key, value in overrides.items():
            if key in data and isinstance(data[key], dict) and isinstance(value, dict):
                self._apply_overrides(data[key], value)
            else:
                data[key] = value
    
    def _apply_minimum_requirements(self, data: Dict[str, Any], rule_type: str) -> Dict[str, Any]:
        """Apply minimum requirements scenario"""
        if rule_type == "structural":
            data["structural"]["loads"]["live_load"] = 50
            data["structural"]["materials"]["concrete"]["strength"] = 3000
        elif rule_type == "fire_safety":
            data["fire_safety"]["egress"]["exit_width"] = 36
            data["fire_safety"]["fire_ratings"]["walls"] = 2
        elif rule_type == "accessibility":
            data["accessibility"]["clear_width"] = 42
            data["accessibility"]["doors"]["entrance"]["width"] = 36
        elif rule_type == "energy":
            data["energy"]["insulation"]["walls"] = 25
            data["energy"]["windows"]["u_factor"] = 0.30
        
        return data
    
    def _apply_optimal_design(self, data: Dict[str, Any], rule_type: str) -> Dict[str, Any]:
        """Apply optimal design scenario"""
        if rule_type == "structural":
            data["structural"]["loads"]["live_load"] = 80
            data["structural"]["materials"]["concrete"]["strength"] = 5000
        elif rule_type == "fire_safety":
            data["fire_safety"]["egress"]["exit_width"] = 48
            data["fire_safety"]["fire_ratings"]["walls"] = 3
        elif rule_type == "accessibility":
            data["accessibility"]["clear_width"] = 48
            data["accessibility"]["doors"]["entrance"]["width"] = 42
        elif rule_type == "energy":
            data["energy"]["insulation"]["walls"] = 35
            data["energy"]["windows"]["u_factor"] = 0.25
        
        return data
    
    def _apply_insufficient_loads(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply insufficient loads scenario"""
        data["structural"]["loads"]["live_load"] = 30
        data["structural"]["loads"]["dead_load"] = 50
        return data
    
    def _apply_weak_materials(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply weak materials scenario"""
        data["structural"]["materials"]["concrete"]["strength"] = 2000
        data["structural"]["materials"]["steel"]["yield_strength"] = 30000
        return data
    
    def _apply_missing_components(self, data: Dict[str, Any], rule_type: str) -> Dict[str, Any]:
        """Apply missing components scenario"""
        if rule_type == "structural":
            data["structural"]["elements"]["columns"]["count"] = 10
        elif rule_type == "fire_safety":
            data["fire_safety"]["systems"]["sprinklers"] = False
        elif rule_type == "accessibility":
            data["accessibility"]["ramp"]["handrails"] = False
        
        return data
    
    def _apply_overdesigned(self, data: Dict[str, Any], rule_type: str) -> Dict[str, Any]:
        """Apply overdesigned scenario"""
        if rule_type == "structural":
            data["structural"]["loads"]["live_load"] = 120
            data["structural"]["materials"]["concrete"]["strength"] = 8000
        elif rule_type == "fire_safety":
            data["fire_safety"]["egress"]["exit_width"] = 60
            data["fire_safety"]["fire_ratings"]["walls"] = 4
        elif rule_type == "accessibility":
            data["accessibility"]["clear_width"] = 60
            data["accessibility"]["doors"]["entrance"]["width"] = 48
        
        return data
    
    def _apply_edge_case_minimum(self, data: Dict[str, Any], rule_type: str) -> Dict[str, Any]:
        """Apply edge case minimum scenario"""
        if rule_type == "structural":
            data["structural"]["loads"]["live_load"] = 50.1
            data["structural"]["materials"]["concrete"]["strength"] = 3000.1
        elif rule_type == "fire_safety":
            data["fire_safety"]["egress"]["exit_width"] = 36.1
            data["fire_safety"]["fire_ratings"]["walls"] = 2.1
        
        return data
    
    def _apply_edge_case_failing(self, data: Dict[str, Any], rule_type: str) -> Dict[str, Any]:
        """Apply edge case failing scenario"""
        if rule_type == "structural":
            data["structural"]["loads"]["live_load"] = 49.9
            data["structural"]["materials"]["concrete"]["strength"] = 2999.9
        elif rule_type == "fire_safety":
            data["fire_safety"]["egress"]["exit_width"] = 35.9
            data["fire_safety"]["fire_ratings"]["walls"] = 1.9
        
        return data
    
    def save_test_suite(self, test_suite: Dict[str, Any], output_file: str):
        """Save test suite to file"""
        output_path = Path(output_file)
        
        with open(output_path, 'w') as f:
            json.dump(test_suite, f, indent=2)
        
        print(f"Test suite saved to: {output_path}")


def main():
    """Command line interface for test data generator"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate test data for building code validation")
    parser.add_argument('--rule-types', nargs='+', 
                       choices=['structural', 'fire_safety', 'accessibility', 'energy', 
                               'mechanical', 'electrical', 'plumbing', 'environmental', 'general'],
                       default=['structural', 'fire_safety', 'accessibility', 'energy'],
                       help='Rule types to generate test data for')
    parser.add_argument('--output', default='test_suite.json',
                       help='Output file for test suite')
    
    args = parser.parse_args()
    
    generator = TestDataGenerator()
    test_suite = generator.generate_comprehensive_test_suite(args.rule_types)
    generator.save_test_suite(test_suite, args.output)
    
    print(f"Generated {test_suite['metadata']['total_scenarios']} test scenarios")
    print(f"Rule types: {', '.join(args.rule_types)}")


if __name__ == '__main__':
    main() 