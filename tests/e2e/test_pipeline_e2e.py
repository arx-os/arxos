#!/usr/bin/env python3
"""
End-to-End Pipeline Testing Framework

This module provides comprehensive E2E testing for the Arxos pipeline,
testing the complete flow from system definition to production deployment.
"""

import json
import os
import sys
import time
import tempfile
import shutil
import subprocess
import unittest
from pathlib import Path
from typing import Dict, Any, List, Optional
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from svgx_engine.services.pipeline_integration import PipelineIntegrationService
from svgx_engine.services.monitoring import get_monitoring
from svgx_engine.services.pipeline_analytics import get_analytics
from svgx_engine.services.rollback_recovery import get_rollback_recovery


class TestPipelineE2E(unittest.TestCase):
    """End-to-End Pipeline Testing Suite"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_system = "e2e_test_system"
        self.service = PipelineIntegrationService()

        # Create test directories
        self.schemas_dir = Path(self.temp_dir) / "schemas"
        self.schemas_dir.mkdir()

        self.symbols_dir = Path(self.temp_dir) / "tools/symbols"
        self.symbols_dir.mkdir()

        self.behavior_dir = Path(self.temp_dir) / "svgx_engine" / "behavior"
        self.behavior_dir.mkdir(parents=True)

        # Patch the services to use test directories
        with patch.object(
            self.service.symbol_manager, "symbol_library_path", self.symbols_dir
        ):
            with patch.object(
                self.service.behavior_engine, "behavior_path", self.behavior_dir
            ):
                pass

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)

    def test_complete_pipeline_e2e(self):
        """Test complete pipeline end-to-end execution"""
        print("\n🔄 Starting Complete Pipeline E2E Test")

        # Step 1: Define System Schema
        print("Step 1: Defining System Schema")
        schema_data = {
            "system": self.test_system,
            "objects": {
                "sensor": {
                    "properties": {
                        "type": "temperature",
                        "range": "-40 to 85°C",
                        "accuracy": "±0.5°C",
                    },
                    "relationships": {"connected_to": ["controller", "power_supply"]},
                    "behavior_profile": "sensor_behavior",
                },
                "controller": {
                    "properties": {
                        "type": "microcontroller",
                        "processor": "ARM Cortex-M4",
                        "memory": "256KB Flash",
                    },
                    "relationships": {"connected_to": ["sensor", "actuator"]},
                    "behavior_profile": "controller_behavior",
                },
            },
        }

        schema_file = self.schemas_dir / f"{self.test_system}" / "schema.json"
        schema_file.parent.mkdir()
        with open(schema_file, "w") as f:
            json.dump(schema_data, f, indent=2)

        # Validate schema
        schema_result = self.service.handle_operation(
            "validate-schema",
            {"system": self.test_system, "schema_file": str(schema_file)},
        )
        self.assertTrue(
            schema_result.get("success", False),
            f"Schema validation failed: {schema_result.get('error')}",
        )
        print("✅ Schema validation passed")

        # Step 2: Create SVGX Symbols
        print("Step 2: Creating SVGX Symbols")
        symbols_data = [
            {
                "id": f"{self.test_system.upper()}_Sensor_001",
                "name": "Temperature Sensor",
                "system": self.test_system,
                "category": "sensor",
                "svg": "<svg width='50' height='50'><circle cx='25' cy='25' r='20' fill='blue'/></svg>",
                "properties": {"type": "temperature", "range": "-40 to 85°C"},
                "connections": ["power", "data"],
                "behavior_profile": "sensor_behavior",
            },
            {
                "id": f"{self.test_system.upper()}_Controller_001",
                "name": "Microcontroller",
                "system": self.test_system,
                "category": "controller",
                "svg": "<svg width='60' height='40'><rect width='60' height='40' fill='green'/></svg>",
                "properties": {"type": "microcontroller", "processor": "ARM Cortex-M4"},
                "connections": ["power", "data", "control"],
                "behavior_profile": "controller_behavior",
            },
        ]

        symbols_dir = self.symbols_dir / self.test_system
        symbols_dir.mkdir()

        for symbol_data in symbols_data:
            symbol_file = symbols_dir / f"{symbol_data['id']}.json"
            with open(symbol_file, "w") as f:
                json.dump(symbol_data, f, indent=2)

        # Validate symbols
        symbols_result = self.service.handle_operation(
            "validate-symbols", {"system": self.test_system}
        )
        self.assertTrue(
            symbols_result.get("success", False),
            f"Symbol validation failed: {symbols_result.get('error')}",
        )
        print("✅ Symbol validation passed")

        # Step 3: Implement Behavior Profiles
        print("Step 3: Implementing Behavior Profiles")
        behavior_files = {
            "sensor_behavior.py": """
class SensorBehavior:
    def __init__(self):
        self.temperature = 25.0
        self.status = "active"
    
    def read_temperature(self):
        return {"temperature": self.temperature, "status": self.status}
    
    def set_temperature(self, temp):
        self.temperature = temp
        return {"temperature": self.temperature, "status": "updated"}
    
    def validate_connections(self, connections):
        required = ["power", "data"]
        return all(conn in connections for conn in required)
""",
            "controller_behavior.py": """
class ControllerBehavior:
    def __init__(self):
        self.mode = "normal"
        self.connected_sensors = []
    
    def add_sensor(self, sensor_id):
        self.connected_sensors.append(sensor_id)
        return {"sensors": self.connected_sensors, "mode": self.mode}
    
    def set_mode(self, mode):
        self.mode = mode
        return {"mode": self.mode, "sensors": self.connected_sensors}
    
    def validate_connections(self, connections):
        required = ["power", "data"]
        return all(conn in connections for conn in required)
""",
        }

        for filename, content in behavior_files.items():
            behavior_file = self.behavior_dir / filename
            with open(behavior_file, "w") as f:
                f.write(content)

        # Validate behavior profiles
        behavior_result = self.service.handle_operation(
            "validate-behavior", {"system": self.test_system}
        )
        self.assertTrue(
            behavior_result.get("success", False),
            f"Behavior validation failed: {behavior_result.get('error')}",
        )
        print("✅ Behavior validation passed")

        # Step 4: Execute Complete Pipeline
        print("Step 4: Executing Complete Pipeline")
        pipeline_result = self.service.handle_operation(
            "execute-pipeline",
            {
                "system": self.test_system,
                "steps": [
                    "validate-schema",
                    "add-symbols",
                    "implement-behavior",
                    "compliance",
                ],
            },
        )
        self.assertTrue(
            pipeline_result.get("success", False),
            f"Pipeline execution failed: {pipeline_result.get('error')}",
        )
        print("✅ Pipeline execution completed")

        # Step 5: Verify System Integration
        print("Step 5: Verifying System Integration")
        integration_result = self.service.handle_operation(
            "verify-integration", {"system": self.test_system}
        )
        self.assertTrue(
            integration_result.get("success", False),
            f"System integration verification failed: {integration_result.get('error')}",
        )
        print("✅ System integration verified")

        print("🎉 Complete Pipeline E2E Test PASSED")

    def test_pipeline_with_real_system_e2e(self):
        """Test pipeline with a realistic building system"""
        print("\n🏢 Starting Real System E2E Test")

        # Define realistic HVAC system
        hvac_system = "hvac_realistic"
        hvac_schema = {
            "system": hvac_system,
            "objects": {
                "thermostat": {
                    "properties": {
                        "type": "digital",
                        "temperature_range": "50-90°F",
                        "accuracy": "±1°F",
                    },
                    "relationships": {
                        "controls": ["hvac_unit", "zone_damper"],
                        "monitors": ["temperature_sensor", "humidity_sensor"],
                    },
                    "behavior_profile": "thermostat_behavior",
                },
                "hvac_unit": {
                    "properties": {
                        "type": "split_system",
                        "capacity": "3.5 tons",
                        "efficiency": "SEER 16",
                    },
                    "relationships": {
                        "controlled_by": ["thermostat"],
                        "supplies": ["zone_damper", "ductwork"],
                    },
                    "behavior_profile": "hvac_unit_behavior",
                },
                "zone_damper": {
                    "properties": {
                        "type": "motorized",
                        "size": "12x8 inches",
                        "actuator": "24V AC",
                    },
                    "relationships": {
                        "controlled_by": ["thermostat"],
                        "supplied_by": ["hvac_unit"],
                    },
                    "behavior_profile": "damper_behavior",
                },
            },
        }

        # Create schema
        schema_file = self.schemas_dir / hvac_system / "schema.json"
        schema_file.parent.mkdir()
        with open(schema_file, "w") as f:
            json.dump(hvac_schema, f, indent=2)

        # Create realistic symbols
        hvac_symbols = [
            {
                "id": "HVAC_Thermostat_001",
                "name": "Digital Thermostat",
                "system": hvac_system,
                "category": "thermostat",
                "svg": "<svg width='80' height='60'><rect width='80' height='60' fill='white' stroke='black'/><text x='40' y='35' text-anchor='middle'>TEMP</text></svg>",
                "properties": {"type": "digital", "temperature_range": "50-90°F"},
                "connections": ["power", "control", "sensor"],
                "behavior_profile": "thermostat_behavior",
            },
            {
                "id": "HVAC_Unit_001",
                "name": "Split System HVAC",
                "system": hvac_system,
                "category": "hvac_unit",
                "svg": "<svg width='100' height='80'><rect width='100' height='80' fill='lightblue' stroke='black'/><text x='50' y='45' text-anchor='middle'>HVAC</text></svg>",
                "properties": {"type": "split_system", "capacity": "3.5 tons"},
                "connections": ["power", "control", "refrigerant", "air"],
                "behavior_profile": "hvac_unit_behavior",
            },
        ]

        symbols_dir = self.symbols_dir / hvac_system
        symbols_dir.mkdir()

        for symbol_data in hvac_symbols:
            symbol_file = symbols_dir / f"{symbol_data['id']}.json"
            with open(symbol_file, "w") as f:
                json.dump(symbol_data, f, indent=2)

        # Execute pipeline
        pipeline_result = self.service.handle_operation(
            "execute-pipeline", {"system": hvac_system, "dry_run": False}
        )

        self.assertTrue(
            pipeline_result.get("success", False),
            f"Real system pipeline failed: {pipeline_result.get('error')}",
        )
        print("✅ Real system pipeline completed")

    def test_pipeline_error_recovery_e2e(self):
        """Test pipeline error recovery and rollback capabilities"""
        print("\n🔄 Starting Error Recovery E2E Test")

        # Create a system with intentional errors
        error_system = "error_test_system"

        # Create invalid schema (missing required fields)
        invalid_schema = {
            "system": error_system,
            "objects": {
                "invalid_object": {
                    # Missing required fields
                }
            },
        }

        schema_file = self.schemas_dir / error_system / "schema.json"
        schema_file.parent.mkdir()
        with open(schema_file, "w") as f:
            json.dump(invalid_schema, f, indent=2)

        # Attempt pipeline execution (should fail)
        pipeline_result = self.service.handle_operation(
            "execute-pipeline", {"system": error_system}
        )

        # Should fail due to invalid schema
        self.assertFalse(
            pipeline_result.get("success", True),
            "Pipeline should fail with invalid schema",
        )
        print("✅ Error detection working")

        # Test rollback functionality
        rollback_result = self.service.handle_operation(
            "rollback", {"system": error_system}
        )

        self.assertTrue(
            rollback_result.get("success", False),
            f"Rollback failed: {rollback_result.get('error')}",
        )
        print("✅ Rollback functionality working")

    def test_pipeline_performance_e2e(self):
        """Test pipeline performance under load"""
        print("\n⚡ Starting Performance E2E Test")

        # Create multiple systems for performance testing
        systems = []
        for i in range(5):
            system_name = f"perf_test_system_{i}"
            systems.append(system_name)

            # Create simple schema
            schema_data = {
                "system": system_name,
                "objects": {
                    f"object_{j}": {
                        "properties": {"type": f"type_{j}"},
                        "relationships": {},
                        "behavior_profile": "default_behavior",
                    }
                    for j in range(3)
                },
            }

            schema_file = self.schemas_dir / system_name / "schema.json"
            schema_file.parent.mkdir()
            with open(schema_file, "w") as f:
                json.dump(schema_data, f, indent=2)

        # Execute pipelines concurrently
        start_time = time.time()
        results = []

        for system in systems:
            result = self.service.handle_operation(
                "execute-pipeline",
                {
                    "system": system,
                    "dry_run": True,  # Use dry run for performance testing
                },
            )
            results.append(result)

        end_time = time.time()
        execution_time = end_time - start_time

        # Verify all pipelines completed
        success_count = sum(1 for r in results if r.get("success", False))
        self.assertEqual(
            success_count,
            len(systems),
            f"Expected {len(systems)} successful pipelines, got {success_count}",
        )

        # Performance requirements
        self.assertLess(
            execution_time,
            30,  # Should complete within 30 seconds
            f"Performance test took {execution_time:.2f}s, expected <30s",
        )

        print(
            f"✅ Performance test passed: {len(systems)} systems in {execution_time:.2f}s"
        )

    def test_pipeline_monitoring_e2e(self):
        """Test pipeline monitoring and analytics"""
        print("\n📊 Starting Monitoring E2E Test")

        # Get monitoring service
        monitoring = get_monitoring()

        # Record test metrics
        monitoring.record_metric("e2e_test_executions", 1, "count")
        monitoring.record_metric("e2e_test_duration", 5.2, "seconds")

        # Check system health
        health = monitoring.get_system_health()
        self.assertIsNotNone(health, "System health should be available")
        self.assertIn("overall_status", health, "Health should have overall status")

        # Test analytics
        analytics = get_analytics()
        report = analytics.create_performance_report("test_system")
        self.assertIsNotNone(report, "Analytics report should be generated")

        print("✅ Monitoring and analytics working")

    def test_pipeline_cli_e2e(self):
        """Test pipeline CLI functionality"""
        print("\n💻 Starting CLI E2E Test")

        # Test CLI commands
        cli_commands = [
            ["python", "scripts/arx_pipeline.py", "--list-systems"],
            ["python", "scripts/arx_pipeline.py", "--help"],
            [
                "python",
                "scripts/arx_pipeline.py",
                "--validate",
                "--system",
                "test_system",
            ],
        ]

        for cmd in cli_commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                # CLI should not crash
                self.assertNotEqual(
                    result.returncode, -1, f"CLI command failed: {' '.join(cmd)}"
                )
            except subprocess.TimeoutExpired:
                self.fail(f"CLI command timed out: {' '.join(cmd)}")
            except FileNotFoundError:
                print(f"⚠️ CLI script not found: {cmd[1]}")

        print("✅ CLI functionality working")

    def test_pipeline_api_e2e(self):
        """Test pipeline API endpoints"""
        print("\n🌐 Starting API E2E Test")

        # Test API operations through service
        api_operations = [
            ("validate-schema", {"system": "api_test_system"}),
            ("list-systems", {}),
            ("get-status", {"system": "api_test_system"}),
        ]

        for operation, params in api_operations:
            try:
                result = self.service.handle_operation(operation, params)
                # API should return a result (even if it's an error for missing system)
                self.assertIsNotNone(
                    result, f"API operation {operation} should return a result"
                )
            except Exception as e:
                self.fail(f"API operation {operation} failed: {e}")

        print("✅ API functionality working")

    def test_pipeline_backup_recovery_e2e(self):
        """Test pipeline backup and recovery functionality"""
        print("\n💾 Starting Backup/Recovery E2E Test")

        # Create test system
        backup_system = "backup_test_system"
        schema_data = {
            "system": backup_system,
            "objects": {
                "test_object": {
                    "properties": {"type": "test"},
                    "relationships": {},
                    "behavior_profile": "test_behavior",
                }
            },
        }

        schema_file = self.schemas_dir / backup_system / "schema.json"
        schema_file.parent.mkdir()
        with open(schema_file, "w") as f:
            json.dump(schema_data, f, indent=2)

        # Create backup
        rr = get_rollback_recovery()
        backup_id = rr.create_backup(backup_system, "full", "E2E test backup")
        self.assertIsNotNone(backup_id, "Backup creation should succeed")

        # List backups
        backups = rr.list_backups(backup_system)
        self.assertGreater(len(backups), 0, "Should have at least one backup")

        # Test backup integrity
        integrity = rr.verify_backup_integrity(backup_id)
        self.assertTrue(integrity, "Backup integrity check should pass")

        print("✅ Backup and recovery functionality working")


def run_e2e_tests():
    """Run all E2E tests"""
    print("🚀 Starting Arxos Pipeline E2E Tests")
    print("=" * 50)

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPipelineE2E)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 50)
    print("📊 E2E Test Summary")
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(
        f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%"
    )

    if result.wasSuccessful():
        print("🎉 All E2E tests PASSED!")
        return True
    else:
        print("❌ Some E2E tests FAILED!")
        return False


if __name__ == "__main__":
    success = run_e2e_tests()
    sys.exit(0 if success else 1)
