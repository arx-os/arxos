"""
SVGX Engine - Electrical Logic Engine Test Suite

Comprehensive test suite for the Electrical Logic Engine implementation.
Tests all electrical engineering calculations, code compliance, and performance.

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


class ElectricalLogicEngineTest:
    """Comprehensive test suite for Electrical Logic Engine."""

    def __init__(self):
        """Initialize the test suite."""
        self.test_results = []
        self.start_time = time.time()

        # Import the Electrical Logic Engine
        try:
            from services.electrical_logic_engine import ElectricalLogicEngine

            self.electrical_engine = ElectricalLogicEngine()
            logger.info("✅ Successfully imported Electrical Logic Engine")

        except ImportError as e:
            logger.error(f"❌ Failed to import Electrical Logic Engine: {e}")
            raise

    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """
        Run comprehensive tests for Electrical Logic Engine.

        Returns:
            Dictionary containing test results
        """
        logger.info("🚀 Starting Electrical Logic Engine tests...")

        test_categories = [
            ("Electrical Object Analysis", self.test_electrical_object_analysis),
            ("Circuit Analysis", self.test_circuit_analysis),
            ("Load Calculations", self.test_load_calculations),
            ("Voltage Drop Analysis", self.test_voltage_drop_analysis),
            ("Protection Coordination", self.test_protection_coordination),
            ("Harmonic Analysis", self.test_harmonic_analysis),
            ("Panel Analysis", self.test_panel_analysis),
            ("Safety Analysis", self.test_safety_analysis),
            ("Code Compliance", self.test_code_compliance),
            ("Performance Testing", self.test_performance),
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

    async def test_electrical_object_analysis(self) -> Dict[str, Any]:
        """Test electrical object analysis functionality."""
        logger.info("Testing electrical object analysis...")

        test_objects = [
            # Outlet test
            {
                "id": "outlet_1",
                "type": "outlet",
                "voltage": 120,
                "current": 15,
                "power": 1800,
                "power_factor": 0.9,
                "resistance": 0.1,
                "length": 50,
            },
            # Panel test
            {
                "id": "panel_1",
                "type": "panel",
                "voltage": 480,
                "current": 100,
                "power": 48000,
                "power_factor": 0.95,
                "panel_capacity": 200,
                "phase_a_load": 30,
                "phase_b_load": 35,
                "phase_c_load": 25,
            },
            # Transformer test
            {
                "id": "transformer_1",
                "type": "transformer",
                "voltage": 480,
                "current": 50,
                "power": 24000,
                "power_factor": 0.9,
                "reactance": 0.05,
            },
        ]

        passed_tests = 0
        total_tests = len(test_objects)

        for object_data in test_objects:
            try:
                result = await self.electrical_engine.analyze_object(object_data)

                # Validate result structure
                assert hasattr(result, "object_id")
                assert hasattr(result, "object_type")
                assert hasattr(result, "circuit_analysis")
                assert hasattr(result, "load_calculations")
                assert hasattr(result, "voltage_drop_analysis")
                assert hasattr(result, "protection_coordination")
                assert hasattr(result, "harmonic_analysis")
                assert hasattr(result, "panel_analysis")
                assert hasattr(result, "safety_analysis")
                assert hasattr(result, "code_compliance")

                # Validate analysis results
                assert result.object_id == object_data["id"]
                assert result.circuit_analysis is not None
                assert result.load_calculations is not None
                assert result.voltage_drop_analysis is not None

                passed_tests += 1
                logger.info(f"✅ Object {object_data['id']} analysis passed")

            except Exception as e:
                logger.error(f"❌ Object {object_data['id']} analysis failed: {e}")

        success_rate = (passed_tests / total_tests) * 100

        return {
            "passed": success_rate >= 90,
            "success_rate": success_rate,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "details": f"Electrical object analysis: {passed_tests}/{total_tests} tests passed",
        }

    async def test_circuit_analysis(self) -> Dict[str, Any]:
        """Test circuit analysis functionality."""
        logger.info("Testing circuit analysis...")

        test_cases = [
            {
                "name": "Branch Circuit",
                "data": {
                    "type": "outlet",
                    "voltage": 120,
                    "power": 1000,
                    "power_factor": 0.9,
                },
            },
            {
                "name": "Feeder Circuit",
                "data": {
                    "type": "breaker",
                    "voltage": 480,
                    "power": 50000,
                    "power_factor": 0.95,
                },
            },
            {
                "name": "Main Circuit",
                "data": {
                    "type": "panel",
                    "voltage": 480,
                    "power": 100000,
                    "power_factor": 0.9,
                },
            },
        ]

        passed_tests = 0
        total_tests = len(test_cases)

        for test_case in test_cases:
            try:
                from services.electrical_logic_engine import CircuitAnalyzer

                analyzer = CircuitAnalyzer()
                result = await analyzer.analyze_circuit(test_case["data"])

                # Validate circuit analysis results
                assert "circuit_type" in result
                assert "voltage_level" in result
                assert "current_rating" in result
                assert "impedance" in result
                assert "power_factor" in result

                # Validate calculations
                assert result["current_rating"] > 0
                assert result["impedance"] > 0
                assert 0 < result["power_factor"] <= 1

                passed_tests += 1
                logger.info(f"✅ Circuit analysis for {test_case['name']} passed")

            except Exception as e:
                logger.error(f"❌ Circuit analysis for {test_case['name']} failed: {e}")

        success_rate = (passed_tests / total_tests) * 100

        return {
            "passed": success_rate >= 90,
            "success_rate": success_rate,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "details": f"Circuit analysis: {passed_tests}/{total_tests} tests passed",
        }

    async def test_load_calculations(self) -> Dict[str, Any]:
        """Test load calculation functionality."""
        logger.info("Testing load calculations...")

        test_cases = [
            {
                "name": "Residential Load",
                "data": {
                    "power": 2000,
                    "demand_factor": 0.8,
                    "diversity_factor": 0.9,
                    "capacity": 3000,
                },
            },
            {
                "name": "Commercial Load",
                "data": {
                    "power": 10000,
                    "demand_factor": 0.7,
                    "diversity_factor": 0.85,
                    "capacity": 15000,
                },
            },
            {
                "name": "Industrial Load",
                "data": {
                    "power": 50000,
                    "demand_factor": 0.9,
                    "diversity_factor": 0.95,
                    "capacity": 60000,
                },
            },
        ]

        passed_tests = 0
        total_tests = len(test_cases)

        for test_case in test_cases:
            try:
                from services.electrical_logic_engine import LoadCalculator

                calculator = LoadCalculator()
                result = await calculator.calculate_load(test_case["data"])

                # Validate load calculation results
                assert "connected_load" in result
                assert "demand_load" in result
                assert "diversity_factor" in result
                assert "load_percentage" in result
                assert "peak_load" in result

                # Validate calculations
                assert result["connected_load"] > 0
                assert result["demand_load"] > 0
                assert 0 < result["diversity_factor"] <= 1
                assert result["load_percentage"] >= 0
                assert result["peak_load"] > 0

                passed_tests += 1
                logger.info(f"✅ Load calculation for {test_case['name']} passed")

            except Exception as e:
                logger.error(f"❌ Load calculation for {test_case['name']} failed: {e}")

        success_rate = (passed_tests / total_tests) * 100

        return {
            "passed": success_rate >= 90,
            "success_rate": success_rate,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "details": f"Load calculations: {passed_tests}/{total_tests} tests passed",
        }

    async def test_voltage_drop_analysis(self) -> Dict[str, Any]:
        """Test voltage drop analysis functionality."""
        logger.info("Testing voltage drop analysis...")

        test_cases = [
            {
                "name": "Short Circuit",
                "data": {
                    "current": 10,
                    "resistance": 0.1,
                    "length": 50,
                    "voltage": 120,
                },
            },
            {
                "name": "Long Circuit",
                "data": {
                    "current": 20,
                    "resistance": 0.2,
                    "length": 200,
                    "voltage": 240,
                },
            },
            {
                "name": "High Current Circuit",
                "data": {
                    "current": 50,
                    "resistance": 0.05,
                    "length": 100,
                    "voltage": 480,
                },
            },
        ]

        passed_tests = 0
        total_tests = len(test_cases)

        for test_case in test_cases:
            try:
                from services.electrical_logic_engine import VoltageDropCalculator

                calculator = VoltageDropCalculator()
                result = await calculator.calculate_voltage_drop(test_case["data"])

                # Validate voltage drop analysis results
                assert "voltage_drop_volts" in result
                assert "voltage_drop_percent" in result
                assert "voltage_regulation" in result
                assert "acceptable_drop" in result

                # Validate calculations
                assert result["voltage_drop_volts"] >= 0
                assert result["voltage_drop_percent"] >= 0
                assert isinstance(result["acceptable_drop"], bool)

                passed_tests += 1
                logger.info(f"✅ Voltage drop analysis for {test_case['name']} passed")

            except Exception as e:
                logger.error(
                    f"❌ Voltage drop analysis for {test_case['name']} failed: {e}"
                )

        success_rate = (passed_tests / total_tests) * 100

        return {
            "passed": success_rate >= 90,
            "success_rate": success_rate,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "details": f"Voltage drop analysis: {passed_tests}/{total_tests} tests passed",
        }

    async def test_protection_coordination(self) -> Dict[str, Any]:
        """Test protection coordination functionality."""
        logger.info("Testing protection coordination...")

        test_cases = [
            {
                "name": "Coordinated Protection",
                "data": {
                    "coordination_factor": 0.8,
                    "trip_time": 0.1,
                    "selectivity_factor": 0.9,
                    "backup_protection": True,
                },
            },
            {
                "name": "Non-Coordinated Protection",
                "data": {
                    "coordination_factor": 0.5,
                    "trip_time": 0.2,
                    "selectivity_factor": 0.6,
                    "backup_protection": False,
                },
            },
        ]

        passed_tests = 0
        total_tests = len(test_cases)

        for test_case in test_cases:
            try:
                from services.electrical_logic_engine import ProtectionCoordinator

                coordinator = ProtectionCoordinator()
                result = await coordinator.coordinate_protection(test_case["data"])

                # Validate protection coordination results
                assert "coordination_status" in result
                assert "trip_time" in result
                assert "selectivity" in result
                assert "backup_protection" in result
                assert "coordination_curve" in result

                passed_tests += 1
                logger.info(
                    f"✅ Protection coordination for {test_case['name']} passed"
                )

            except Exception as e:
                logger.error(
                    f"❌ Protection coordination for {test_case['name']} failed: {e}"
                )

        success_rate = (passed_tests / total_tests) * 100

        return {
            "passed": success_rate >= 90,
            "success_rate": success_rate,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "details": f"Protection coordination: {passed_tests}/{total_tests} tests passed",
        }

    async def test_harmonic_analysis(self) -> Dict[str, Any]:
        """Test harmonic analysis functionality."""
        logger.info("Testing harmonic analysis...")

        test_cases = [
            {
                "name": "Low Harmonic Load",
                "data": {
                    "thd": 2.5,
                    "3rd_harmonic": 1.5,
                    "5th_harmonic": 1.2,
                    "7th_harmonic": 0.8,
                    "9th_harmonic": 0.5,
                    "displacement_pf": 0.95,
                },
            },
            {
                "name": "High Harmonic Load",
                "data": {
                    "thd": 8.0,
                    "3rd_harmonic": 5.0,
                    "5th_harmonic": 4.0,
                    "7th_harmonic": 2.5,
                    "9th_harmonic": 1.5,
                    "displacement_pf": 0.85,
                },
            },
        ]

        passed_tests = 0
        total_tests = len(test_cases)

        for test_case in test_cases:
            try:
                from services.electrical_logic_engine import HarmonicAnalyzer

                analyzer = HarmonicAnalyzer()
                result = await analyzer.analyze_harmonics(test_case["data"])

                # Validate harmonic analysis results
                assert "total_harmonic_distortion" in result
                assert "harmonic_spectrum" in result
                assert "power_factor" in result
                assert "harmonic_limits" in result

                # Validate calculations
                assert result["total_harmonic_distortion"] >= 0
                assert isinstance(result["harmonic_spectrum"], dict)
                assert 0 < result["power_factor"] <= 1
                assert isinstance(result["harmonic_limits"], bool)

                passed_tests += 1
                logger.info(f"✅ Harmonic analysis for {test_case['name']} passed")

            except Exception as e:
                logger.error(
                    f"❌ Harmonic analysis for {test_case['name']} failed: {e}"
                )

        success_rate = (passed_tests / total_tests) * 100

        return {
            "passed": success_rate >= 90,
            "success_rate": success_rate,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "details": f"Harmonic analysis: {passed_tests}/{total_tests} tests passed",
        }

    async def test_panel_analysis(self) -> Dict[str, Any]:
        """Test panel analysis functionality."""
        logger.info("Testing panel analysis...")

        test_cases = [
            {
                "name": "Balanced Panel",
                "data": {
                    "panel_capacity": 200,
                    "phase_a_load": 30,
                    "phase_b_load": 32,
                    "phase_c_load": 28,
                },
            },
            {
                "name": "Unbalanced Panel",
                "data": {
                    "panel_capacity": 200,
                    "phase_a_load": 50,
                    "phase_b_load": 30,
                    "phase_c_load": 20,
                },
            },
        ]

        passed_tests = 0
        total_tests = len(test_cases)

        for test_case in test_cases:
            try:
                from services.electrical_logic_engine import PanelAnalyzer

                analyzer = PanelAnalyzer()
                result = await analyzer.analyze_panel(test_case["data"])

                # Validate panel analysis results
                assert "panel_capacity" in result
                assert "load_distribution" in result
                assert "phase_balance" in result
                assert "spare_capacity" in result
                assert "upgrade_recommendations" in result

                # Validate calculations
                assert result["panel_capacity"] > 0
                assert isinstance(result["load_distribution"], dict)
                assert isinstance(result["phase_balance"], bool)
                assert isinstance(result["upgrade_recommendations"], list)

                passed_tests += 1
                logger.info(f"✅ Panel analysis for {test_case['name']} passed")

            except Exception as e:
                logger.error(f"❌ Panel analysis for {test_case['name']} failed: {e}")

        success_rate = (passed_tests / total_tests) * 100

        return {
            "passed": success_rate >= 90,
            "success_rate": success_rate,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "details": f"Panel analysis: {passed_tests}/{total_tests} tests passed",
        }

    async def test_safety_analysis(self) -> Dict[str, Any]:
        """Test safety analysis functionality."""
        logger.info("Testing safety analysis...")

        test_cases = [
            {
                "name": "Low Voltage",
                "data": {"voltage": 120, "current": 10, "grounded": True},
            },
            {
                "name": "High Voltage",
                "data": {"voltage": 480, "current": 100, "grounded": True},
            },
            {
                "name": "Ungrounded",
                "data": {"voltage": 240, "current": 20, "grounded": False},
            },
        ]

        passed_tests = 0
        total_tests = len(test_cases)

        for test_case in test_cases:
            try:
                from services.electrical_logic_engine import SafetyAnalyzer

                analyzer = SafetyAnalyzer()
                result = await analyzer.analyze_safety(test_case["data"])

                # Validate safety analysis results
                assert "shock_hazard" in result
                assert "fire_hazard" in result
                assert "arc_flash" in result
                assert "grounding" in result
                assert "safety_recommendations" in result

                # Validate assessments
                assert result["shock_hazard"] in ["low", "medium", "high"]
                assert result["fire_hazard"] in ["low", "medium", "high"]
                assert result["arc_flash"] in ["low", "medium", "high"]
                assert isinstance(result["grounding"], bool)
                assert isinstance(result["safety_recommendations"], list)

                passed_tests += 1
                logger.info(f"✅ Safety analysis for {test_case['name']} passed")

            except Exception as e:
                logger.error(f"❌ Safety analysis for {test_case['name']} failed: {e}")

        success_rate = (passed_tests / total_tests) * 100

        return {
            "passed": success_rate >= 90,
            "success_rate": success_rate,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "details": f"Safety analysis: {passed_tests}/{total_tests} tests passed",
        }

    async def test_code_compliance(self) -> Dict[str, Any]:
        """Test code compliance functionality."""
        logger.info("Testing code compliance...")

        test_cases = [
            {
                "name": "Compliant Equipment",
                "data": {
                    "voltage": 120,
                    "current": 15,
                    "local_code_compliant": True,
                    "safety_compliant": True,
                    "installation_compliant": True,
                },
            },
            {
                "name": "Non-Compliant Equipment",
                "data": {
                    "voltage": 1000,
                    "current": 200,
                    "local_code_compliant": False,
                    "safety_compliant": False,
                    "installation_compliant": False,
                },
            },
        ]

        passed_tests = 0
        total_tests = len(test_cases)

        for test_case in test_cases:
            try:
                from services.electrical_logic_engine import ElectricalCodeValidator

                validator = ElectricalCodeValidator()
                result = await validator.validate_compliance(test_case["data"])

                # Validate code compliance results
                assert "nec_compliance" in result
                assert "local_code_compliance" in result
                assert "safety_compliance" in result
                assert "installation_compliance" in result
                assert "overall_compliance" in result

                # Validate compliance checks
                assert isinstance(result["nec_compliance"], bool)
                assert isinstance(result["local_code_compliance"], bool)
                assert isinstance(result["safety_compliance"], bool)
                assert isinstance(result["installation_compliance"], bool)
                assert isinstance(result["overall_compliance"], bool)

                passed_tests += 1
                logger.info(f"✅ Code compliance for {test_case['name']} passed")

            except Exception as e:
                logger.error(f"❌ Code compliance for {test_case['name']} failed: {e}")

        success_rate = (passed_tests / total_tests) * 100

        return {
            "passed": success_rate >= 90,
            "success_rate": success_rate,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "details": f"Code compliance: {passed_tests}/{total_tests} tests passed",
        }

    async def test_performance(self) -> Dict[str, Any]:
        """Test performance of Electrical Logic Engine."""
        logger.info("Testing performance...")

        # Test object with comprehensive data
        test_object = {
            "id": "performance_test_1",
            "type": "panel",
            "voltage": 480,
            "current": 100,
            "power": 48000,
            "power_factor": 0.95,
            "panel_capacity": 200,
            "phase_a_load": 30,
            "phase_b_load": 35,
            "phase_c_load": 25,
            "resistance": 0.1,
            "length": 100,
            "thd": 3.5,
            "coordination_factor": 0.8,
            "trip_time": 0.1,
            "selectivity_factor": 0.9,
            "backup_protection": True,
            "grounded": True,
        }

        # Performance test
        start_time = time.time()

        try:
            result = await self.electrical_engine.analyze_object(test_object)
            analysis_time = time.time() - start_time

            # Check performance metrics
            metrics = self.electrical_engine.get_performance_metrics()

            # Performance requirements
            performance_ok = analysis_time < 1.0  # Should complete in under 1 second
            metrics_ok = metrics["total_analyses"] > 0

            passed = performance_ok and metrics_ok

            logger.info(f"✅ Performance test completed in {analysis_time:.3f}s")

            return {
                "passed": passed,
                "analysis_time": analysis_time,
                "performance_ok": performance_ok,
                "metrics_ok": metrics_ok,
                "details": f"Performance test: {analysis_time:.3f}s analysis time",
            }

        except Exception as e:
            logger.error(f"❌ Performance test failed: {e}")
            return {
                "passed": False,
                "error": str(e),
                "details": "Performance test failed",
            }

    async def test_real_world_scenarios(self) -> Dict[str, Any]:
        """Test real-world electrical scenarios."""
        logger.info("Testing real-world scenarios...")

        scenarios = [
            {
                "name": "Residential Outlet",
                "data": {
                    "id": "res_outlet_1",
                    "type": "outlet",
                    "voltage": 120,
                    "current": 15,
                    "power": 1800,
                    "power_factor": 0.9,
                    "resistance": 0.1,
                    "length": 50,
                    "demand_factor": 0.8,
                    "diversity_factor": 0.9,
                    "capacity": 2000,
                    "thd": 2.5,
                    "coordination_factor": 0.8,
                    "grounded": True,
                    "local_code_compliant": True,
                    "safety_compliant": True,
                    "installation_compliant": True,
                },
            },
            {
                "name": "Commercial Panel",
                "data": {
                    "id": "com_panel_1",
                    "type": "panel",
                    "voltage": 480,
                    "current": 100,
                    "power": 48000,
                    "power_factor": 0.95,
                    "panel_capacity": 200,
                    "phase_a_load": 30,
                    "phase_b_load": 35,
                    "phase_c_load": 25,
                    "resistance": 0.05,
                    "length": 100,
                    "thd": 4.0,
                    "coordination_factor": 0.9,
                    "grounded": True,
                    "local_code_compliant": True,
                    "safety_compliant": True,
                    "installation_compliant": True,
                },
            },
            {
                "name": "Industrial Transformer",
                "data": {
                    "id": "ind_transformer_1",
                    "type": "transformer",
                    "voltage": 480,
                    "current": 50,
                    "power": 24000,
                    "power_factor": 0.9,
                    "reactance": 0.05,
                    "resistance": 0.02,
                    "length": 200,
                    "thd": 6.0,
                    "coordination_factor": 0.7,
                    "grounded": True,
                    "local_code_compliant": True,
                    "safety_compliant": True,
                    "installation_compliant": True,
                },
            },
        ]

        passed_scenarios = 0
        total_scenarios = len(scenarios)

        for scenario in scenarios:
            try:
                result = await self.electrical_engine.analyze_object(scenario["data"])

                # Validate comprehensive analysis
                assert result.circuit_analysis is not None
                assert result.load_calculations is not None
                assert result.voltage_drop_analysis is not None
                assert result.protection_coordination is not None
                assert result.harmonic_analysis is not None
                assert result.panel_analysis is not None
                assert result.safety_analysis is not None
                assert result.code_compliance is not None

                # Check for warnings and recommendations
                assert isinstance(result.warnings, list)
                assert isinstance(result.recommendations, list)

                passed_scenarios += 1
                logger.info(f"✅ Real-world scenario {scenario['name']} passed")

            except Exception as e:
                logger.error(f"❌ Real-world scenario {scenario['name']} failed: {e}")

        success_rate = (passed_scenarios / total_scenarios) * 100

        return {
            "passed": success_rate >= 90,
            "success_rate": success_rate,
            "passed_scenarios": passed_scenarios,
            "total_scenarios": total_scenarios,
            "details": f"Real-world scenarios: {passed_scenarios}/{total_scenarios} scenarios passed",
        }

    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        total_tests = len(self.test_results)
        passed_tests = sum(
            1 for result in self.test_results if result["status"] == "PASSED"
        )
        failed_tests = total_tests - passed_tests
        overall_success_rate = (
            (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        )

        # Calculate total test time
        total_time = time.time() - self.start_time

        # Generate detailed report
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": overall_success_rate,
                "total_time": total_time,
                "status": "PASSED" if overall_success_rate >= 90 else "FAILED",
            },
            "test_results": self.test_results,
            "performance_metrics": (
                self.electrical_engine.get_performance_metrics()
                if hasattr(self, "electrical_engine")
                else {}
            ),
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Log summary
        logger.info(f"\n📊 ELECTRICAL LOGIC ENGINE TEST SUMMARY")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {overall_success_rate:.1f}%")
        logger.info(f"Total Time: {total_time:.2f}s")
        logger.info(f"Status: {report['summary']['status']}")

        return report


async def main():
    """Main test execution function."""
    logger.info("🚀 Starting Electrical Logic Engine Test Suite")

    try:
        # Create test instance
        test_suite = ElectricalLogicEngineTest()

        # Run comprehensive tests
        report = await test_suite.run_comprehensive_tests()

        # Print final status
        if report["summary"]["status"] == "PASSED":
            logger.info("🎉 All Electrical Logic Engine tests PASSED!")
        else:
            logger.error("❌ Some Electrical Logic Engine tests FAILED!")

        return report

    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
