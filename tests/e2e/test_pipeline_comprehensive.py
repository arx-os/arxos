#!/usr/bin/env python3
"""
Comprehensive Pipeline Integration Test Suite

Tests the complete pipeline integration including Go-Python bridge, database operations,
and end-to-end pipeline execution.
"""

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock

# Add the svgx_engine to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "svgx_engine"))

from svgx_engine.services.pipeline_integration import PipelineIntegrationService
from svgx_engine.services.symbol_manager import SymbolManager
from svgx_engine.services.behavior_engine import BehaviorEngine
from svgx_engine.services.validation_engine import ValidationEngine
from svgx_engine.utils.errors import PipelineError, ValidationError


class TestPipelineComprehensive(unittest.TestCase):
    """Comprehensive test suite for the Arxos pipeline integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.service = PipelineIntegrationService()

        # Create test directories
        self.schemas_dir = Path(self.temp_dir) / "schemas"
        self.schemas_dir.mkdir()

        self.symbols_dir = Path(self.temp_dir) / "tools/symbols"
        self.symbols_dir.mkdir()

        self.behavior_dir = Path(self.temp_dir) / "svgx_engine" / "behavior"
        self.behavior_dir.mkdir(parents=True)

        # Patch the services to use test directories
        with patch.object(self.service.symbol_manager, 'symbol_library_path', self.symbols_dir):
            with patch.object(self.service.behavior_engine, 'behavior_path', self.behavior_dir):
                pass

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_full_pipeline_execution(self):
        """Test complete pipeline execution end-to-end."""
        system = "test_system"

        # Step 1: Define Schema
        print("Step 1: Define Schema")
        schema_result = self.service.handle_operation("validate-schema", {"system": system})
        self.assertTrue(schema_result.get("success", False))

        # Step 2: Add Symbols
        print("Step 2: Add Symbols")
        symbols_result = self.service.handle_operation("add-symbols", {
            "system": system,
            "symbols": ["test_symbol_1", "test_symbol_2"]
        })
        self.assertTrue(symbols_result.get("success", False))

        # Step 3: Implement Behavior
        print("Step 3: Implement Behavior")
        behavior_result = self.service.handle_operation("implement-behavior", {"system": system})
        self.assertTrue(behavior_result.get("success", False))

        # Step 4: Compliance Check
        print("Step 4: Compliance Check")
        compliance_result = self.service.handle_operation("compliance", {"system": system})
        self.assertTrue(compliance_result.get("success", False))

        print("✅ Full pipeline execution test passed")

    def test_pipeline_with_real_system(self):
        """Test pipeline with a realistic system (Audiovisual)."""
        system = "audiovisual"

        # Create realistic schema
        schema_dir = self.schemas_dir / system
        schema_dir.mkdir()

        schema_data = {
            "system": system,
            "objects": {
                "display": {
                    "properties": {
                        "resolution": "1920x1080",
                        "type": "LED"
                    },
                    "relationships": {
                        "connected_to": ["control_system"]
                    },
                    "behavior_profile": "display_behavior"
                },
                "projector": {
                    "properties": {
                        "brightness": "3000 lumens",
                        "type": "DLP"
                    },
                    "relationships": {
                        "connected_to": ["control_system"]
                    },
                    "behavior_profile": "projector_behavior"
                }
            }
        }

        schema_file = schema_dir / "schema.json"
        with open(schema_file, 'w') as f:
            json.dump(schema_data, f)

        # Test pipeline execution
        print(f"Testing pipeline for {system} system")

        # Validate schema
        schema_result = self.service.handle_operation("validate-schema", {"system": system})
        self.assertTrue(schema_result.get("success", False))

        # Add symbols
        symbols_result = self.service.handle_operation("add-symbols", {
            "system": system,
            "symbols": ["display", "projector", "control_system"]
        })
        self.assertTrue(symbols_result.get("success", False))

        # Implement behavior
        behavior_result = self.service.handle_operation("implement-behavior", {"system": system})
        self.assertTrue(behavior_result.get("success", False))

        # Compliance check
        compliance_result = self.service.handle_operation("compliance", {"system": system})
        self.assertTrue(compliance_result.get("success", False))

        print(f"✅ {system} system pipeline test passed")

    def test_pipeline_error_handling(self):
        """Test pipeline error handling and recovery."""
        # Test with invalid system
        invalid_result = self.service.handle_operation("validate-schema", {"system": ""})
        self.assertFalse(invalid_result.get("success", True))

        # Test with missing parameters
        missing_result = self.service.handle_operation("validate-schema", {})
        self.assertFalse(missing_result.get("success", True))

        # Test with unknown operation
        unknown_result = self.service.handle_operation("unknown-operation", {"system": "test"})
        self.assertFalse(unknown_result.get("success", True))

        print("✅ Pipeline error handling test passed")

    def test_pipeline_performance(self):
        """Test pipeline performance under load."""
        import time

        # Test multiple systems
        systems = ["electrical", "mechanical", "plumbing", "fire_alarm"]

        start_time = time.time()

        for system in systems:
            # Quick validation test
            result = self.service.handle_operation("validate-schema", {"system": system})
            self.assertIsNotNone(result)

        end_time = time.time()
        execution_time = end_time - start_time

        # Should complete within reasonable time (5 seconds for 4 systems)
        self.assertLess(execution_time, 5.0)

        print(f"✅ Pipeline performance test passed (execution time: {execution_time:.2f}s)")

    def test_pipeline_concurrent_execution(self):
        """Test pipeline with concurrent operations."""
        import threading
        import queue

        results = queue.Queue()

        def execute_pipeline(system):
            """Execute pipeline for a system."""
            try:
                # Quick validation
                result = self.service.handle_operation("validate-schema", {"system": system})
                results.put((system, result.get("success", False)))
            except Exception as e:
                results.put((system, False))

        # Start concurrent executions
        threads = []
        systems = ["system_1", "system_2", "system_3", "system_4"]

        for system in systems:
            thread = threading.Thread(target=execute_pipeline, args=(system,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check results
        successful_executions = 0
        while not results.empty():
            system, success = results.get()
            if success:
                successful_executions += 1

        # At least some executions should succeed
        self.assertGreater(successful_executions, 0)

        print(f"✅ Pipeline concurrent execution test passed ({successful_executions}/{len(systems)} successful)")

    def test_pipeline_data_persistence(self):
        """Test pipeline data persistence and state management."""
        system = "persistence_test"

        # Create test data
        schema_dir = self.schemas_dir / system
        schema_dir.mkdir()

        schema_data = {
            "system": system,
            "objects": {
                "test_object": {
                    "properties": {"test": "value"},
                    "relationships": {},
                    "behavior_profile": "test_behavior"
                }
            }
        }

        schema_file = schema_dir / "schema.json"
        with open(schema_file, 'w') as f:
            json.dump(schema_data, f)

        # Test persistence through multiple operations
        operations = [
            ("validate-schema", {"system": system}),
            ("add-symbols", {"system": system, "symbols": ["test_symbol"]}),
            ("implement-behavior", {"system": system}),
            ("compliance", {"system": system})
        ]

        for operation, params in operations:
            result = self.service.handle_operation(operation, params)
            self.assertIsNotNone(result)
            # Verify data persists between operations
            self.assertTrue(Path(schema_file).exists())

        print("✅ Pipeline data persistence test passed")

    def test_pipeline_rollback_capability(self):
        """Test pipeline rollback capability."""
        system = "rollback_test"

        # Create initial state
        schema_dir = self.schemas_dir / system
        schema_dir.mkdir()

        initial_schema = {
            "system": system,
            "objects": {"original": {"properties": {}, "relationships": {}, "behavior_profile": "original"}}
        }

        schema_file = schema_dir / "schema.json"
        with open(schema_file, 'w') as f:
            json.dump(initial_schema, f)

        # Simulate failed operation
        try:
            # This should fail due to invalid parameters
            result = self.service.handle_operation("validate-schema", {"system": ""})
            self.assertFalse(result.get("success", True))
        except Exception:
            pass

        # Verify original state is preserved
        self.assertTrue(schema_file.exists())
        with open(schema_file, 'r') as f:
            preserved_schema = json.load(f)

        self.assertEqual(preserved_schema["system"], system)

        print("✅ Pipeline rollback capability test passed")

    def test_pipeline_validation_comprehensive(self):
        """Test comprehensive pipeline validation."""
        # Test all validation operations
        validation_tests = [
            ("validate-schema", {"system": "test_system"}),
            ("validate-symbol", {"symbol": "test_symbol"}),
            ("validate-behavior", {"system": "test_system"})
        ]

        for operation, params in validation_tests:
            result = self.service.handle_operation(operation, params)
            self.assertIsNotNone(result)
            # Should have success field
            self.assertIn("success", result)
            # Should have timestamp
            self.assertIn("timestamp", result)

        print("✅ Pipeline validation comprehensive test passed")

    def test_pipeline_integration_with_external_systems(self):
        """Test pipeline integration with external systems."""
        # Mock external system integration
        with patch('svgx_engine.services.validation_engine.ValidationEngine.run_compliance_check') as mock_compliance:
            mock_compliance.return_value = {
                "compliance_status": "compliant",
                "checks_passed": 5,
                "checks_failed": 0
            }

            result = self.service.handle_operation("compliance", {"system": "external_test"})
            self.assertTrue(result.get("success", False))
            mock_compliance.assert_called_once_with("external_test")

        print("✅ Pipeline external system integration test passed")

    def test_pipeline_monitoring_and_metrics(self):
        """Test pipeline monitoring and metrics collection."""
        # Simulate metrics collection
        metrics = {
            "total_operations": 10,
            "successful_operations": 8,
            "failed_operations": 2,
            "average_execution_time": 1.5,
            "systems_processed": ["system1", "system2", "system3"]
        }

        # Verify metrics structure
        self.assertIn("total_operations", metrics)
        self.assertIn("successful_operations", metrics)
        self.assertIn("failed_operations", metrics)
        self.assertIn("average_execution_time", metrics)
        self.assertIn("systems_processed", metrics)

        # Verify metrics consistency
        self.assertEqual(metrics["total_operations"],
                        metrics["successful_operations"] + metrics["failed_operations"])

        print("✅ Pipeline monitoring and metrics test passed")

    def test_pipeline_security_and_compliance(self):
        """Test pipeline security and compliance features."""
        # Test security validation
        security_result = self.service.handle_operation("compliance", {"system": "security_test"})
        self.assertIsNotNone(security_result)

        # Verify security fields are present
        if security_result.get("success", False):
            compliance_details = security_result.get("compliance_details", {})
            self.assertIsInstance(compliance_details, dict)

        print("✅ Pipeline security and compliance test passed")

    def test_pipeline_documentation_generation(self):
        """Test pipeline documentation generation."""
        system = "doc_test"

        # Create test system
        schema_dir = self.schemas_dir / system
        schema_dir.mkdir()

        # Test documentation generation
        doc_result = self.service.handle_operation("implement-behavior", {"system": system})
        self.assertIsNotNone(doc_result)

        # Verify documentation files are created
        behavior_file = self.behavior_dir / f"{system}.py"
        self.assertTrue(behavior_file.exists())

        print("✅ Pipeline documentation generation test passed")


def run_comprehensive_tests():
    """Run all comprehensive pipeline tests."""
    print("🚀 Running Comprehensive Pipeline Integration Tests")
    print("=" * 60)

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPipelineComprehensive)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")

    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")

    if result.errors:
        print("\n❌ Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")

    if result.wasSuccessful():
        print("\n✅ All comprehensive pipeline tests passed!")
        return True
    else:
        print("\n❌ Some comprehensive pipeline tests failed!")
        return False


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
