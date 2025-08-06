"""
SVGX Engine - Phase 1 Implementation Test

Comprehensive test suite for Phase 1 implementation including:
- Engineering Logic Engine
- MCP Integration Service
- Object classification
- Performance monitoring
- Error handling

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import asyncio
import time
import logging
import sys
import os
from typing import Dict, Any, List
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Phase1ImplementationTest:
    """Comprehensive test suite for Phase 1 implementation."""

    def __init__(self):
        """Initialize the test suite."""
        self.test_results = []
        self.start_time = time.time()

        # Import the services we're testing
        try:
            from services.engineering_logic_engine import engineering_logic_engine
            from services.mcp_integration_service import mcp_integration_service

            self.engineering_engine = engineering_logic_engine
            self.mcp_service = mcp_integration_service

            logger.info(
                "✅ Successfully imported engineering logic engine and MCP integration service"
            )

        except ImportError as e:
            logger.error(f"❌ Failed to import services: {e}")
            raise

    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """
        Run comprehensive tests for Phase 1 implementation.

        Returns:
            Dictionary containing test results
        """
        logger.info("🚀 Starting Phase 1 implementation tests...")

        test_categories = [
            ("Object Classification", self.test_object_classification),
            ("Engineering Logic Engine", self.test_engineering_logic_engine),
            ("MCP Integration Service", self.test_mcp_integration_service),
            ("Performance Monitoring", self.test_performance_monitoring),
            ("Error Handling", self.test_error_handling),
            ("Integration Tests", self.test_integration_scenarios),
            ("Real-World Scenarios", self.test_real_world_scenarios),
        ]

        for category_name, test_func in test_categories:
            logger.info(f"\n📋 Testing: {category_name}")
            try:
                result = await test_func()
                self.test_results.append(
                    {
                        "category": category_name,
                        "status": "PASSED" if result.get("passed", False) else "FAILED",
                        "details": result,
                    }
                )
                logger.info(
                    f"✅ {category_name}: {'PASSED' if result.get('passed', False) else 'FAILED'}"
                )
            except Exception as e:
                logger.error(f"❌ {category_name} failed: {e}")
                self.test_results.append(
                    {"category": category_name, "status": "FAILED", "error": str(e)}
                )

        return self.generate_test_report()

    async def test_object_classification(self) -> Dict[str, Any]:
        """Test object classification functionality."""
        logger.info("Testing object classification...")

        test_objects = [
            # Electrical objects
            {"id": "outlet_1", "type": "outlet"},
            {"id": "switch_1", "type": "switch"},
            {"id": "panel_1", "type": "panel"},
            {"id": "transformer_1", "type": "transformer"},
            {"id": "breaker_1", "type": "breaker"},
            {"id": "fuse_1", "type": "fuse"},
            {"id": "receptacle_1", "type": "receptacle"},
            {"id": "junction_1", "type": "junction"},
            {"id": "conduit_1", "type": "conduit"},
            {"id": "cable_1", "type": "cable"},
            {"id": "wire_1", "type": "wire"},
            {"id": "light_1", "type": "light"},
            {"id": "fixture_1", "type": "fixture"},
            {"id": "sensor_1", "type": "sensor"},
            {"id": "controller_1", "type": "controller"},
            {"id": "meter_1", "type": "meter"},
            {"id": "generator_1", "type": "generator"},
            {"id": "ups_1", "type": "ups"},
            {"id": "capacitor_1", "type": "capacitor"},
            {"id": "inductor_1", "type": "inductor"},
            # HVAC objects
            {"id": "duct_1", "type": "duct"},
            {"id": "damper_1", "type": "damper"},
            {"id": "diffuser_1", "type": "diffuser"},
            {"id": "grille_1", "type": "grille"},
            {"id": "coil_1", "type": "coil"},
            {"id": "fan_1", "type": "fan"},
            {"id": "pump_1", "type": "pump"},
            {"id": "valve_1", "type": "valve"},
            {"id": "filter_1", "type": "filter"},
            {"id": "heater_1", "type": "heater"},
            {"id": "cooler_1", "type": "cooler"},
            {"id": "thermostat_1", "type": "thermostat"},
            {"id": "actuator_1", "type": "actuator"},
            {"id": "compressor_1", "type": "compressor"},
            {"id": "condenser_1", "type": "condenser"},
            {"id": "evaporator_1", "type": "evaporator"},
            {"id": "chiller_1", "type": "chiller"},
            {"id": "boiler_1", "type": "boiler"},
            {"id": "heat_exchanger_1", "type": "heat_exchanger"},
            # Plumbing objects
            {"id": "pipe_1", "type": "pipe"},
            {"id": "valve_1", "type": "valve"},
            {"id": "fitting_1", "type": "fitting"},
            {"id": "fixture_1", "type": "fixture"},
            {"id": "pump_1", "type": "pump"},
            {"id": "tank_1", "type": "tank"},
            {"id": "meter_1", "type": "meter"},
            {"id": "drain_1", "type": "drain"},
            {"id": "vent_1", "type": "vent"},
            {"id": "trap_1", "type": "trap"},
            {"id": "backflow_1", "type": "backflow"},
            {"id": "pressure_reducer_1", "type": "pressure_reducer"},
            {"id": "expansion_joint_1", "type": "expansion_joint"},
            {"id": "strainer_1", "type": "strainer"},
            {"id": "check_valve_1", "type": "check_valve"},
            {"id": "relief_valve_1", "type": "relief_valve"},
            {"id": "ball_valve_1", "type": "ball_valve"},
            {"id": "gate_valve_1", "type": "gate_valve"},
            {"id": "butterfly_valve_1", "type": "butterfly_valve"},
            # Structural objects
            {"id": "beam_1", "type": "beam"},
            {"id": "column_1", "type": "column"},
            {"id": "wall_1", "type": "wall"},
            {"id": "slab_1", "type": "slab"},
            {"id": "foundation_1", "type": "foundation"},
            {"id": "truss_1", "type": "truss"},
            {"id": "joist_1", "type": "joist"},
            {"id": "girder_1", "type": "girder"},
            {"id": "lintel_1", "type": "lintel"},
            {"id": "pier_1", "type": "pier"},
            {"id": "footing_1", "type": "footing"},
            {"id": "pile_1", "type": "pile"},
            {"id": "brace_1", "type": "brace"},
            {"id": "strut_1", "type": "strut"},
            {"id": "tie_1", "type": "tie"},
            # Security objects
            {"id": "camera_1", "type": "camera"},
            {"id": "sensor_1", "type": "sensor"},
            {"id": "detector_1", "type": "detector"},
            {"id": "reader_1", "type": "reader"},
            {"id": "lock_1", "type": "lock"},
            {"id": "keypad_1", "type": "keypad"},
            {"id": "panel_1", "type": "panel"},
            {"id": "siren_1", "type": "siren"},
            {"id": "strobe_1", "type": "strobe"},
            {"id": "intercom_1", "type": "intercom"},
            {"id": "card_reader_1", "type": "card_reader"},
            {"id": "biometric_1", "type": "biometric"},
            {"id": "motion_detector_1", "type": "motion_detector"},
            {"id": "glass_break_1", "type": "glass_break"},
            {"id": "smoke_detector_1", "type": "smoke_detector"},
            {"id": "heat_detector_1", "type": "heat_detector"},
            {"id": "access_control_1", "type": "access_control"},
            {"id": "alarm_1", "type": "alarm"},
            {"id": "monitor_1", "type": "monitor"},
            # Fire protection objects
            {"id": "sprinkler_1", "type": "sprinkler"},
            {"id": "detector_1", "type": "detector"},
            {"id": "alarm_1", "type": "alarm"},
            {"id": "panel_1", "type": "panel"},
            {"id": "pump_1", "type": "pump"},
            {"id": "tank_1", "type": "tank"},
            {"id": "valve_1", "type": "valve"},
            {"id": "hose_1", "type": "hose"},
            {"id": "extinguisher_1", "type": "extinguisher"},
            {"id": "riser_1", "type": "riser"},
            {"id": "header_1", "type": "header"},
            {"id": "branch_1", "type": "branch"},
            {"id": "nozzle_1", "type": "nozzle"},
            {"id": "flow_switch_1", "type": "flow_switch"},
            {"id": "tamper_switch_1", "type": "tamper_switch"},
            {"id": "supervisory_1", "type": "supervisory"},
            {"id": "horn_1", "type": "horn"},
            {"id": "strobe_1", "type": "strobe"},
            {"id": "annunciator_1", "type": "annunciator"},
            # Lighting objects
            {"id": "fixture_1", "type": "fixture"},
            {"id": "lamp_1", "type": "lamp"},
            {"id": "ballast_1", "type": "ballast"},
            {"id": "switch_1", "type": "switch"},
            {"id": "dimmer_1", "type": "dimmer"},
            {"id": "sensor_1", "type": "sensor"},
            {"id": "controller_1", "type": "controller"},
            {"id": "emergency_1", "type": "emergency"},
            {"id": "exit_1", "type": "exit"},
            {"id": "emergency_exit_1", "type": "emergency_exit"},
            {"id": "sconce_1", "type": "sconce"},
            {"id": "chandelier_1", "type": "chandelier"},
            {"id": "track_1", "type": "track"},
            {"id": "recessed_1", "type": "recessed"},
            {"id": "surface_1", "type": "surface"},
            {"id": "pendant_1", "type": "pendant"},
            {"id": "wall_washer_1", "type": "wall_washer"},
            {"id": "uplight_1", "type": "uplight"},
            {"id": "downlight_1", "type": "downlight"},
            # Communications objects
            {"id": "jack_1", "type": "jack"},
            {"id": "outlet_1", "type": "outlet"},
            {"id": "panel_1", "type": "panel"},
            {"id": "switch_1", "type": "switch"},
            {"id": "router_1", "type": "router"},
            {"id": "hub_1", "type": "hub"},
            {"id": "antenna_1", "type": "antenna"},
            {"id": "satellite_1", "type": "satellite"},
            {"id": "fiber_1", "type": "fiber"},
            {"id": "coax_1", "type": "coax"},
            {"id": "ethernet_1", "type": "ethernet"},
            {"id": "wifi_1", "type": "wifi"},
            {"id": "bluetooth_1", "type": "bluetooth"},
            {"id": "repeater_1", "type": "repeater"},
            {"id": "amplifier_1", "type": "amplifier"},
            {"id": "splitter_1", "type": "splitter"},
            {"id": "coupler_1", "type": "coupler"},
            {"id": "terminator_1", "type": "terminator"},
            {"id": "patch_panel_1", "type": "patch_panel"},
        ]

        classification_results = []
        expected_system_types = {
            "outlet": "electrical",
            "switch": "electrical",
            "panel": "electrical",
            "transformer": "electrical",
            "breaker": "electrical",
            "fuse": "electrical",
            "receptacle": "electrical",
            "junction": "electrical",
            "conduit": "electrical",
            "cable": "electrical",
            "wire": "electrical",
            "light": "electrical",
            "fixture": "electrical",
            "sensor": "electrical",
            "controller": "electrical",
            "meter": "electrical",
            "generator": "electrical",
            "ups": "electrical",
            "capacitor": "electrical",
            "inductor": "electrical",
            "duct": "hvac",
            "damper": "hvac",
            "diffuser": "hvac",
            "grille": "hvac",
            "coil": "hvac",
            "fan": "hvac",
            "pump": "hvac",
            "valve": "hvac",
            "filter": "hvac",
            "heater": "hvac",
            "cooler": "hvac",
            "thermostat": "hvac",
            "actuator": "hvac",
            "compressor": "hvac",
            "condenser": "hvac",
            "evaporator": "hvac",
            "chiller": "hvac",
            "boiler": "hvac",
            "heat_exchanger": "hvac",
            "pipe": "plumbing",
            "fitting": "plumbing",
            "fixture": "plumbing",
            "tank": "plumbing",
            "drain": "plumbing",
            "vent": "plumbing",
            "trap": "plumbing",
            "backflow": "plumbing",
            "pressure_reducer": "plumbing",
            "expansion_joint": "plumbing",
            "strainer": "plumbing",
            "check_valve": "plumbing",
            "relief_valve": "plumbing",
            "ball_valve": "plumbing",
            "gate_valve": "plumbing",
            "butterfly_valve": "plumbing",
            "beam": "structural",
            "column": "structural",
            "wall": "structural",
            "slab": "structural",
            "foundation": "structural",
            "truss": "structural",
            "joist": "structural",
            "girder": "structural",
            "lintel": "structural",
            "pier": "structural",
            "footing": "structural",
            "pile": "structural",
            "brace": "structural",
            "strut": "structural",
            "tie": "structural",
            "camera": "security",
            "detector": "security",
            "reader": "security",
            "lock": "security",
            "keypad": "security",
            "siren": "security",
            "strobe": "security",
            "intercom": "security",
            "card_reader": "security",
            "biometric": "security",
            "motion_detector": "security",
            "glass_break": "security",
            "smoke_detector": "security",
            "heat_detector": "security",
            "access_control": "security",
            "alarm": "security",
            "monitor": "security",
            "sprinkler": "fire_protection",
            "hose": "fire_protection",
            "extinguisher": "fire_protection",
            "riser": "fire_protection",
            "header": "fire_protection",
            "branch": "fire_protection",
            "nozzle": "fire_protection",
            "flow_switch": "fire_protection",
            "tamper_switch": "fire_protection",
            "supervisory": "fire_protection",
            "horn": "fire_protection",
            "annunciator": "fire_protection",
            "lamp": "lighting",
            "ballast": "lighting",
            "dimmer": "lighting",
            "emergency": "lighting",
            "exit": "lighting",
            "emergency_exit": "lighting",
            "sconce": "lighting",
            "chandelier": "lighting",
            "track": "lighting",
            "recessed": "lighting",
            "surface": "lighting",
            "pendant": "lighting",
            "wall_washer": "lighting",
            "uplight": "lighting",
            "downlight": "lighting",
            "router": "communications",
            "hub": "communications",
            "antenna": "communications",
            "satellite": "communications",
            "fiber": "communications",
            "coax": "communications",
            "ethernet": "communications",
            "wifi": "communications",
            "bluetooth": "communications",
            "repeater": "communications",
            "amplifier": "communications",
            "splitter": "communications",
            "coupler": "communications",
            "terminator": "communications",
            "patch_panel": "communications",
        }

        for obj in test_objects:
            object_type = obj["type"]
            expected_system = expected_system_types.get(object_type, "electrical")

            # Test engineering engine classification
            eng_system = self.engineering_engine._classify_object(obj)
            eng_correct = eng_system.value == expected_system

            # Test MCP service classification
            mcp_system = self.mcp_service._determine_system_type(object_type)
            mcp_correct = mcp_system == expected_system

            classification_results.append(
                {
                    "object_type": object_type,
                    "expected_system": expected_system,
                    "engineering_system": eng_system.value,
                    "mcp_system": mcp_system,
                    "engineering_correct": eng_correct,
                    "mcp_correct": mcp_correct,
                }
            )

        # Calculate accuracy
        total_objects = len(classification_results)
        eng_correct_count = sum(
            1 for r in classification_results if r["engineering_correct"]
        )
        mcp_correct_count = sum(1 for r in classification_results if r["mcp_correct"])

        eng_accuracy = eng_correct_count / total_objects
        mcp_accuracy = mcp_correct_count / total_objects

        return {
            "passed": eng_accuracy >= 0.95 and mcp_accuracy >= 0.95,
            "total_objects": total_objects,
            "engineering_accuracy": eng_accuracy,
            "mcp_accuracy": mcp_accuracy,
            "engineering_correct": eng_correct_count,
            "mcp_correct": mcp_correct_count,
            "results": classification_results,
        }

    async def test_engineering_logic_engine(self) -> Dict[str, Any]:
        """Test engineering logic engine functionality."""
        logger.info("Testing engineering logic engine...")

        test_objects = [
            {"id": "outlet_1", "type": "outlet", "voltage": 120, "current": 15},
            {"id": "switch_1", "type": "switch", "voltage": 120, "current": 10},
            {"id": "panel_1", "type": "panel", "voltage": 480, "current": 100},
            {"id": "duct_1", "type": "duct", "diameter": 0.3, "length": 10},
            {"id": "pipe_1", "type": "pipe", "diameter": 0.05, "length": 5},
            {"id": "beam_1", "type": "beam", "length": 6, "width": 0.2, "height": 0.3},
        ]

        analysis_results = []

        for obj in test_objects:
            try:
                result = await self.engineering_engine.analyze_object_addition(obj)
                analysis_results.append(
                    {
                        "object_id": obj["id"],
                        "object_type": obj["type"],
                        "status": result.status.value,
                        "system_type": result.system_type.value,
                        "has_engineering_analysis": bool(result.engineering_analysis),
                        "has_network_integration": bool(result.network_integration),
                        "has_code_compliance": bool(result.code_compliance),
                        "has_implementation_guidance": bool(
                            result.implementation_guidance
                        ),
                        "analysis_time": result.performance_metrics.get(
                            "analysis_time", 0
                        ),
                    }
                )
            except Exception as e:
                logger.error(f"Analysis failed for {obj['id']}: {e}")
                analysis_results.append(
                    {
                        "object_id": obj["id"],
                        "object_type": obj["type"],
                        "status": "FAILED",
                        "error": str(e),
                    }
                )

        # Check results
        successful_analyses = sum(
            1 for r in analysis_results if r["status"] == "completed"
        )
        total_analyses = len(analysis_results)
        success_rate = successful_analyses / total_analyses if total_analyses > 0 else 0

        return {
            "passed": success_rate >= 0.8,  # Allow some failures during development
            "total_analyses": total_analyses,
            "successful_analyses": successful_analyses,
            "success_rate": success_rate,
            "results": analysis_results,
        }

    async def test_mcp_integration_service(self) -> Dict[str, Any]:
        """Test MCP integration service functionality."""
        logger.info("Testing MCP integration service...")

        test_objects = [
            {"id": "outlet_1", "type": "outlet", "voltage": 120, "current": 15},
            {"id": "switch_1", "type": "switch", "voltage": 120, "current": 10},
            {"id": "panel_1", "type": "panel", "voltage": 480, "current": 100},
            {"id": "duct_1", "type": "duct", "diameter": 0.3, "length": 10},
            {"id": "pipe_1", "type": "pipe", "diameter": 0.05, "length": 5},
            {"id": "beam_1", "type": "beam", "length": 6, "width": 0.2, "height": 0.3},
        ]

        validation_results = []

        for obj in test_objects:
            try:
                result = await self.mcp_service.validate_compliance(obj)
                validation_results.append(
                    {
                        "object_id": obj["id"],
                        "object_type": obj["type"],
                        "status": result.status.value,
                        "system_type": result.system_type,
                        "overall_compliance": result.overall_compliance,
                        "has_local_validation": bool(result.local_validation),
                        "has_mcp_validation": bool(result.mcp_validation),
                        "violations_count": len(result.violations),
                        "warnings_count": len(result.warnings),
                        "recommendations_count": len(result.recommendations),
                        "validation_time": result.performance_metrics.get(
                            "total_validation_time", 0
                        ),
                    }
                )
            except Exception as e:
                logger.error(f"Validation failed for {obj['id']}: {e}")
                validation_results.append(
                    {
                        "object_id": obj["id"],
                        "object_type": obj["type"],
                        "status": "ERROR",
                        "error": str(e),
                    }
                )

        # Check results
        successful_validations = sum(
            1
            for r in validation_results
            if r["status"] == "compliant" or r["status"] == "non_compliant"
        )
        total_validations = len(validation_results)
        success_rate = (
            successful_validations / total_validations if total_validations > 0 else 0
        )

        return {
            "passed": success_rate >= 0.8,  # Allow some failures during development
            "total_validations": total_validations,
            "successful_validations": successful_validations,
            "success_rate": success_rate,
            "results": validation_results,
        }

    async def test_performance_monitoring(self) -> Dict[str, Any]:
        """Test performance monitoring functionality."""
        logger.info("Testing performance monitoring...")

        # Get performance metrics
        eng_metrics = self.engineering_engine.get_performance_metrics()
        mcp_metrics = self.mcp_service.get_performance_metrics()

        # Check if metrics are being tracked
        eng_has_metrics = all(
            key in eng_metrics
            for key in [
                "total_analyses",
                "successful_analyses",
                "failed_analyses",
                "average_response_time",
                "system_uptime",
            ]
        )

        mcp_has_metrics = all(
            key in mcp_metrics
            for key in [
                "total_validations",
                "successful_validations",
                "failed_validations",
                "average_validation_time",
                "system_uptime",
            ]
        )

        return {
            "passed": eng_has_metrics and mcp_has_metrics,
            "engineering_metrics": eng_metrics,
            "mcp_metrics": mcp_metrics,
            "engineering_has_metrics": eng_has_metrics,
            "mcp_has_metrics": mcp_has_metrics,
        }

    async def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling functionality."""
        logger.info("Testing error handling...")

        # Test with invalid object
        invalid_object = {"id": "invalid_1", "type": "invalid_type"}

        try:
            eng_result = await self.engineering_engine.analyze_object_addition(
                invalid_object
            )
            mcp_result = await self.mcp_service.validate_compliance(invalid_object)

            # Check if errors are properly handled
            eng_handled = eng_result.status.value in ["failed", "completed"]
            mcp_handled = mcp_result.status.value in [
                "error",
                "compliant",
                "non_compliant",
            ]

            return {
                "passed": eng_handled and mcp_handled,
                "engineering_error_handled": eng_handled,
                "mcp_error_handled": mcp_handled,
                "engineering_result": eng_result.status.value,
                "mcp_result": mcp_result.status.value,
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    async def test_integration_scenarios(self) -> Dict[str, Any]:
        """Test integration scenarios."""
        logger.info("Testing integration scenarios...")

        # Test electrical outlet scenario
        outlet_scenario = {
            "id": "outlet_kitchen_1",
            "type": "outlet",
            "voltage": 120,
            "current": 15,
            "location": "kitchen",
            "circuit_id": "circuit_1",
        }

        try:
            # Test engineering analysis
            eng_result = await self.engineering_engine.analyze_object_addition(
                outlet_scenario
            )

            # Test MCP validation
            mcp_result = await self.mcp_service.validate_compliance(outlet_scenario)

            # Check integration
            eng_success = eng_result.status.value == "completed"
            mcp_success = mcp_result.status.value in ["compliant", "non_compliant"]

            return {
                "passed": eng_success and mcp_success,
                "engineering_success": eng_success,
                "mcp_success": mcp_success,
                "engineering_result": eng_result.status.value,
                "mcp_result": mcp_result.status.value,
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    async def test_real_world_scenarios(self) -> Dict[str, Any]:
        """Test real-world scenarios."""
        logger.info("Testing real-world scenarios...")

        scenarios = [
            # Electrical panel scenario
            {
                "id": "panel_main_1",
                "type": "panel",
                "voltage": 480,
                "current": 200,
                "location": "electrical_room",
                "circuits": ["circuit_1", "circuit_2", "circuit_3"],
            },
            # HVAC duct scenario
            {
                "id": "duct_supply_1",
                "type": "duct",
                "diameter": 0.4,
                "length": 15,
                "location": "ceiling",
                "system": "supply_air",
            },
            # Plumbing pipe scenario
            {
                "id": "pipe_cold_water_1",
                "type": "pipe",
                "diameter": 0.025,
                "length": 8,
                "location": "wall",
                "system": "cold_water",
            },
        ]

        scenario_results = []

        for scenario in scenarios:
            try:
                eng_result = await self.engineering_engine.analyze_object_addition(
                    scenario
                )
                mcp_result = await self.mcp_service.validate_compliance(scenario)

                scenario_results.append(
                    {
                        "scenario_id": scenario["id"],
                        "object_type": scenario["type"],
                        "engineering_status": eng_result.status.value,
                        "mcp_status": mcp_result.status.value,
                        "engineering_system": eng_result.system_type.value,
                        "mcp_system": mcp_result.system_type,
                    }
                )

            except Exception as e:
                scenario_results.append(
                    {
                        "scenario_id": scenario["id"],
                        "object_type": scenario["type"],
                        "error": str(e),
                    }
                )

        successful_scenarios = sum(1 for r in scenario_results if "error" not in r)
        total_scenarios = len(scenario_results)
        success_rate = (
            successful_scenarios / total_scenarios if total_scenarios > 0 else 0
        )

        return {
            "passed": success_rate >= 0.7,  # Allow some failures during development
            "total_scenarios": total_scenarios,
            "successful_scenarios": successful_scenarios,
            "success_rate": success_rate,
            "results": scenario_results,
        }

    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["status"] == "PASSED")
        failed_tests = total_tests - passed_tests

        overall_success_rate = passed_tests / total_tests if total_tests > 0 else 0

        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": overall_success_rate,
                "overall_status": "PASSED" if overall_success_rate >= 0.8 else "FAILED",
            },
            "test_duration": time.time() - self.start_time,
            "timestamp": datetime.utcnow().isoformat(),
            "detailed_results": self.test_results,
        }

        # Log summary
        logger.info(f"\n📊 Test Summary:")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {overall_success_rate:.2%}")
        logger.info(f"Overall Status: {report['test_summary']['overall_status']}")

        return report


async def main():
    """Main test execution function."""
    logger.info("🚀 Starting Phase 1 Implementation Test Suite")

    try:
        # Create test instance
        test_suite = Phase1ImplementationTest()

        # Run comprehensive tests
        results = await test_suite.run_comprehensive_tests()

        # Print detailed results
        print("\n" + "=" * 80)
        print("PHASE 1 IMPLEMENTATION TEST RESULTS")
        print("=" * 80)

        for result in results["detailed_results"]:
            status_icon = "✅" if result["status"] == "PASSED" else "❌"
            print(f"{status_icon} {result['category']}: {result['status']}")

            if "details" in result:
                details = result["details"]
                if "success_rate" in details:
                    print(f"   Success Rate: {details['success_rate']:.2%}")
                if "total_objects" in details:
                    print(f"   Total Objects: {details['total_objects']}")
                if "total_analyses" in details:
                    print(f"   Total Analyses: {details['total_analyses']}")

        print("\n" + "=" * 80)
        print(f"OVERALL STATUS: {results['test_summary']['overall_status']}")
        print(f"SUCCESS RATE: {results['test_summary']['success_rate']:.2%}")
        print(f"TEST DURATION: {results['test_duration']:.2f} seconds")
        print("=" * 80)

        return results

    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        return {"error": str(e), "status": "FAILED"}


if __name__ == "__main__":
    # Run the test suite
    asyncio.run(main())
