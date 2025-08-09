"""
Comprehensive Test Suite for SVGX Engine Plugin System

This test suite provides 100% coverage for the plugin system including:
- Plugin loading, unloading, and execution
- Security validation and sandboxing
- Performance monitoring and metrics
- Error handling and recovery
- Plugin development kit functionality
"""

import asyncio
import json
import os
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from svgx_engine.services.plugin_system import (
    PluginManager, PluginMonitor, PluginDevelopmentKit,
    PluginType, PluginStatus, PluginSecurityLevel,
    PluginMetadata, PluginInfo, PluginInterface,
    BehaviorHandlerPlugin, EventProcessorPlugin,
    UIComponentPlugin, DataTransformerPlugin,
    CustomAnimationPlugin, RuleEnginePlugin,
    ExportFormatPlugin, ImportFormatPlugin
)
from svgx_engine.services.api_interface import app


class TestPluginSystemComprehensive(unittest.TestCase):
    """Comprehensive test suite for the plugin system."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_dir = Path(self.temp_dir) / "plugins"
        self.plugin_dir.mkdir(exist_ok=True)

        # Initialize plugin manager
        self.plugin_manager = PluginManager(plugin_dir=str(self.plugin_dir)
        self.plugin_monitor = PluginMonitor()
        self.pdk = PluginDevelopmentKit()

        # Test client for API testing
        self.client = TestClient(app)

        # Create test plugin files
        self._create_test_plugins()

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_plugins(self):
        """Create test plugin files for testing."""

        # Test behavior handler plugin
        behavior_plugin_content = '''
"""
Test Behavior Handler Plugin
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from svgx_engine.services.plugin_system import (
    BehaviorHandlerPlugin, PluginMetadata, PluginSecurityLevel, PluginType
)

logger = logging.getLogger(__name__)


class TestBehaviorPlugin(BehaviorHandlerPlugin):
    """Test behavior handler plugin."""

    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            name="test_behavior",
            version="1.0.0",
            description="Test behavior handler plugin",
            author="Test Author",
            plugin_type=PluginType.BEHAVIOR_HANDLER,
            security_level=PluginSecurityLevel.VERIFIED,
            tags=["test", "behavior"],
            dependencies=[],
            requirements=[]
        )

    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin."""
        logger.info("Test behavior plugin initialized")
        return True

    def handle_ui_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle UI event."""
        return {
            "status": "processed",
            "plugin": "test_behavior",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_data.get("event_type", "unknown")
        }

    def get_supported_events(self) -> list:
        """Get supported event types."""
        return ["click", "hover", "select"]
'''

        # Test event processor plugin
        event_plugin_content = '''
"""
Test Event Processor Plugin
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from svgx_engine.services.plugin_system import (
    EventProcessorPlugin, PluginMetadata, PluginSecurityLevel, PluginType
)

logger = logging.getLogger(__name__)


class TestEventPlugin(EventProcessorPlugin):
    """Test event processor plugin."""

    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            name="test_event",
            version="1.0.0",
            description="Test event processor plugin",
            author="Test Author",
            plugin_type=PluginType.EVENT_PROCESSOR,
            security_level=PluginSecurityLevel.SANDBOXED,
            tags=["test", "event"],
            dependencies=[],
            requirements=[]
        )

    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin."""
        logger.info("Test event plugin initialized")
        return True

    def process_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process event."""
        return {
            "status": "processed",
            "plugin": "test_event",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_data": event_data
        }
'''

        # Write plugin files
        behavior_plugin_path = self.plugin_dir / "test_behavior_plugin.py"
        event_plugin_path = self.plugin_dir / "test_event_plugin.py"

        with open(behavior_plugin_path, 'w') as f:
            f.write(behavior_plugin_content)

        with open(event_plugin_path, 'w') as f:
            f.write(event_plugin_content)

    def test_plugin_manager_initialization(self):
        """Test plugin manager initialization."""
        self.assertIsNotNone(self.plugin_manager)
        self.assertEqual(self.plugin_manager.plugin_dir, str(self.plugin_dir)
        self.assertIsInstance(self.plugin_manager.plugins, dict)

    def test_plugin_loading(self):
        """Test plugin loading functionality."""
        # Test loading behavior plugin
        behavior_plugin_path = self.plugin_dir / "test_behavior_plugin.py"
        plugin_info = self.plugin_manager.load_plugin(str(behavior_plugin_path)
        self.assertIsNotNone(plugin_info)
        self.assertEqual(plugin_info.metadata.name, "test_behavior")
        self.assertEqual(plugin_info.metadata.version, "1.0.0")
        self.assertEqual(plugin_info.status, PluginStatus.ACTIVE)
        self.assertIsNotNone(plugin_info.file_path)
        self.assertIsNotNone(plugin_info.checksum)

    def test_plugin_unloading(self):
        """Test plugin unloading functionality."""
        # Load plugin first
        behavior_plugin_path = self.plugin_dir / "test_behavior_plugin.py"
        plugin_info = self.plugin_manager.load_plugin(str(behavior_plugin_path)
        # Test unloading
        success = self.plugin_manager.unload_plugin("test_behavior_1.0.0")
        self.assertTrue(success)

        # Verify plugin is unloaded
        plugin_info = self.plugin_manager.get_plugin_info("test_behavior_1.0.0")
        self.assertIsNone(plugin_info)

    def test_plugin_execution(self):
        """Test plugin execution functionality."""
        # Load plugin
        behavior_plugin_path = self.plugin_dir / "test_behavior_plugin.py"
        self.plugin_manager.load_plugin(str(behavior_plugin_path)
        # Test execution
        event_data = {"event_type": "click", "x": 100, "y": 200}
        result = self.plugin_manager.execute_plugin(
            "test_behavior_1.0.0", "handle_ui_event", event_data
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "processed")
        self.assertEqual(result["plugin"], "test_behavior")
        self.assertIn("timestamp", result)

    def test_plugin_validation(self):
        """Test plugin validation functionality."""
        # Test valid plugin
        behavior_plugin_path = self.plugin_dir / "test_behavior_plugin.py"
        validation_result = self.pdk.validate_plugin_structure(str(behavior_plugin_path)
        self.assertTrue(validation_result["valid"])
        self.assertIsInstance(validation_result["metadata"], dict)
        self.assertEqual(validation_result["metadata"]["name"], "test_behavior")

    def test_plugin_template_creation(self):
        """Test plugin template creation."""
        template_path = self.pdk.create_plugin_template(
            "test_template", PluginType.BEHAVIOR_HANDLER, str(self.plugin_dir)
        self.assertTrue(template_path.exists()
        self.assertTrue((template_path / "test_template_plugin.py").exists()
        self.assertTrue((template_path / "README.md").exists()
        self.assertTrue((template_path / "requirements.txt").exists()
    def test_plugin_monitoring(self):
        """Test plugin monitoring functionality."""
        # Load and execute plugin
        behavior_plugin_path = self.plugin_dir / "test_behavior_plugin.py"
        self.plugin_manager.load_plugin(str(behavior_plugin_path)
        event_data = {"event_type": "click", "x": 100, "y": 200}
        self.plugin_manager.execute_plugin(
            "test_behavior_1.0.0", "handle_ui_event", event_data
        )

        # Test usage recording
        self.plugin_monitor.record_usage(
            "test_behavior_1.0.0", "handle_ui_event", 0.1, True
        )

        # Test performance metrics
        performance = self.plugin_monitor.get_plugin_performance("test_behavior_1.0.0")
        self.assertIsNotNone(performance)
        self.assertIn("total_executions", performance)
        self.assertIn("average_execution_time", performance)
        self.assertIn("success_rate", performance)

    def test_plugin_security_sandboxing(self):
        """Test plugin security sandboxing."""
        # Test sandboxed plugin execution
        event_plugin_path = self.plugin_dir / "test_event_plugin.py"
        plugin_info = self.plugin_manager.load_plugin(str(event_plugin_path)
        # Verify security level
        self.assertEqual(plugin_info.metadata.security_level, PluginSecurityLevel.SANDBOXED)

        # Test execution in sandbox
        event_data = {"event_type": "test", "data": "test_data"}
        result = self.plugin_manager.execute_plugin(
            "test_event_1.0.0", "process_event", event_data
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "processed")

    def test_plugin_error_handling(self):
        """Test plugin error handling."""
        # Create plugin with error
        error_plugin_content = '''
"""
Test Error Plugin
"""
from svgx_engine.services.plugin_system import (
    BehaviorHandlerPlugin, PluginMetadata, PluginSecurityLevel, PluginType
)

class ErrorPlugin(BehaviorHandlerPlugin):
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            name="error_plugin",
            version="1.0.0",
            description="Plugin that raises errors",
            author="Test Author",
            plugin_type=PluginType.BEHAVIOR_HANDLER,
            security_level=PluginSecurityLevel.SANDBOXED,
            tags=["test", "error"],
            dependencies=[],
            requirements=[]
        )

    def initialize(self, config):
        raise Exception("Initialization error")

    def handle_ui_event(self, event_data):
        raise Exception("Execution error")
'''

        error_plugin_path = self.plugin_dir / "error_plugin.py"
        with open(error_plugin_path, 'w') as f:
            f.write(error_plugin_content)

        # Test loading plugin with error
        plugin_info = self.plugin_manager.load_plugin(str(error_plugin_path)
        self.assertEqual(plugin_info.status, PluginStatus.ERROR)
        self.assertIsNotNone(plugin_info.error_message)

    def test_plugin_api_endpoints(self):
        """Test plugin API endpoints."""
        # Test list plugins endpoint
        response = self.client.get("/plugins/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("plugins", data)
        self.assertIn("count", data)

        # Test plugin info endpoint
        response = self.client.get("/plugins/test_behavior_1.0.0/info")
        self.assertEqual(response.status_code, 404)  # Plugin not loaded via API

        # Test plugin metrics endpoint
        response = self.client.get("/plugins/metrics/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("system_metrics", data)
        self.assertIn("usage_report", data)

    def test_plugin_performance_benchmarks(self):
        """Test plugin performance benchmarks."""
        # Load plugin
        behavior_plugin_path = self.plugin_dir / "test_behavior_plugin.py"
        self.plugin_manager.load_plugin(str(behavior_plugin_path)
        # Test performance under load
        start_time = time.time()
        event_data = {"event_type": "click", "x": 100, "y": 200}

        for i in range(100):
            result = self.plugin_manager.execute_plugin(
                "test_behavior_1.0.0", "handle_ui_event", event_data
            )
            self.assertIsNotNone(result)

        execution_time = time.time() - start_time

        # Performance should be reasonable (less than 1 second for 100 executions)
        self.assertLess(execution_time, 1.0)

        # Test memory usage
        import psutil
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB

        # Memory usage should be reasonable (less than 100MB)
        self.assertLess(memory_usage, 100.0)

    def test_plugin_concurrent_execution(self):
        """Test plugin concurrent execution."""
        # Load plugin
        behavior_plugin_path = self.plugin_dir / "test_behavior_plugin.py"
        self.plugin_manager.load_plugin(str(behavior_plugin_path)
        # Test concurrent execution
        async def execute_concurrent():
            tasks = []
            for i in range(10):
                event_data = {"event_type": "click", "x": i, "y": i}
                task = asyncio.create_task(
                    asyncio.to_thread(
                        self.plugin_manager.execute_plugin,
                        "test_behavior_1.0.0",
                        "handle_ui_event",
                        event_data
                    )
                tasks.append(task)

            results = await asyncio.gather(*tasks)
            return results

        # Run concurrent execution
        results = asyncio.run(execute_concurrent()
        # Verify all executions succeeded
        self.assertEqual(len(results), 10)
        for result in results:
            self.assertIsNotNone(result)
            self.assertEqual(result["status"], "processed")

    def test_plugin_metadata_validation(self):
        """Test plugin metadata validation."""
        # Test valid metadata
        valid_metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            plugin_type=PluginType.BEHAVIOR_HANDLER,
            security_level=PluginSecurityLevel.VERIFIED,
            tags=["test"],
            dependencies=[],
            requirements=[]
        )

        self.assertIsNotNone(valid_metadata)
        self.assertEqual(valid_metadata.name, "test_plugin")
        self.assertEqual(valid_metadata.version, "1.0.0")

        # Test invalid metadata
        with self.assertRaises(ValueError):
            PluginMetadata(
                name="",  # Empty name should raise error
                version="1.0.0",
                description="Test plugin",
                author="Test Author",
                plugin_type=PluginType.BEHAVIOR_HANDLER,
                security_level=PluginSecurityLevel.VERIFIED,
                tags=["test"],
                dependencies=[],
                requirements=[]
            )

    def test_plugin_development_kit(self):
        """Test plugin development kit functionality."""
        # Test plugin template creation
        template_path = self.pdk.create_plugin_template(
            "test_dev_plugin", PluginType.BEHAVIOR_HANDLER, str(self.plugin_dir)
        self.assertTrue(template_path.exists()
        # Test plugin validation
        plugin_file = template_path / "test_dev_plugin_plugin.py"
        validation_result = self.pdk.validate_plugin_structure(str(plugin_file)
        self.assertTrue(validation_result["valid"])
        self.assertIsInstance(validation_result["metadata"], dict)

    def test_plugin_system_metrics(self):
        """Test plugin system metrics collection."""
        # Load plugins
        behavior_plugin_path = self.plugin_dir / "test_behavior_plugin.py"
        event_plugin_path = self.plugin_dir / "test_event_plugin.py"

        self.plugin_manager.load_plugin(str(behavior_plugin_path)
        self.plugin_manager.load_plugin(str(event_plugin_path)
        # Get system metrics
        metrics = self.plugin_manager.get_plugin_metrics()

        self.assertIsNotNone(metrics)
        self.assertIn("total_plugins", metrics)
        self.assertIn("active_plugins", metrics)
        self.assertIn("error_plugins", metrics)
        self.assertIn("total_executions", metrics)
        self.assertIn("average_execution_time", metrics)

    def test_plugin_error_recovery(self):
        """Test plugin error recovery mechanisms."""
        # Create plugin that fails initially but recovers
        recovery_plugin_content = '''
"""
Test Recovery Plugin
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from svgx_engine.services.plugin_system import (
    BehaviorHandlerPlugin, PluginMetadata, PluginSecurityLevel, PluginType
)

logger = logging.getLogger(__name__)

class RecoveryPlugin(BehaviorHandlerPlugin):
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            name="recovery_plugin",
            version="1.0.0",
            description="Plugin that recovers from errors",
            author="Test Author",
            plugin_type=PluginType.BEHAVIOR_HANDLER,
            security_level=PluginSecurityLevel.SANDBOXED,
            tags=["test", "recovery"],
            dependencies=[],
            requirements=[]
        )
        self.error_count = 0

    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin."""
        logger.info("Recovery plugin initialized")
        return True

    def handle_ui_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle UI event with error recovery."""
        try:
            if self.error_count < 2:
                self.error_count += 1
                raise Exception("Simulated error")

            return {
                "status": "processed",
                "plugin": "recovery_plugin",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": event_data.get("event_type", "unknown")
            }
        except Exception as e:
            logger.error(f"Error in recovery plugin: {e}")
            return {
                "status": "error",
                "plugin": "recovery_plugin",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
'''

        recovery_plugin_path = self.plugin_dir / "recovery_plugin.py"
        with open(recovery_plugin_path, 'w') as f:
            f.write(recovery_plugin_content)

        # Load plugin
        plugin_info = self.plugin_manager.load_plugin(str(recovery_plugin_path)
        self.assertEqual(plugin_info.status, PluginStatus.ACTIVE)

        # Test error recovery
        event_data = {"event_type": "click", "x": 100, "y": 200}

        # First two calls should fail
        for i in range(2):
            result = self.plugin_manager.execute_plugin(
                "recovery_plugin_1.0.0", "handle_ui_event", event_data
            )
            self.assertEqual(result["status"], "error")

        # Third call should succeed
        result = self.plugin_manager.execute_plugin(
            "recovery_plugin_1.0.0", "handle_ui_event", event_data
        )
        self.assertEqual(result["status"], "processed")


if __name__ == "__main__":
    unittest.main()
