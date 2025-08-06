"""
SVGX Engine - Custom Behavior Plugin System Tests

Comprehensive test suite for the Custom Behavior Plugin System covering plugin discovery, loading, registration, validation, unloading, and error handling.
Follows Arxos engineering standards: absolute imports, global instances, comprehensive test coverage.
"""

import pytest
import os
import shutil
from datetime import datetime
from svgx_engine.runtime.custom_behavior_plugin_system import (
    custom_behavior_plugin_system,
    CustomBehaviorPluginSystem,
    PluginStatus,
    PluginMetadata,
    BehaviorPlugin,
)
from svgx_engine.runtime.behavior_management_system import (
    behavior_management_system,
    Behavior,
)

PLUGIN_DIR = os.path.join(os.path.dirname(__file__), "../runtime/plugins")


@pytest.fixture(scope="module", autouse=True)
def setup_plugin_dir():
    # Ensure plugin directory exists and is empty
    if os.path.exists(PLUGIN_DIR):
        shutil.rmtree(PLUGIN_DIR)
    os.makedirs(PLUGIN_DIR)
    yield
    shutil.rmtree(PLUGIN_DIR)


class TestCustomBehaviorPluginSystem:
    def test_discover_plugins_empty(self):
        """Test plugin discovery when directory is empty."""
        plugins = custom_behavior_plugin_system.discover_plugins()
        assert plugins == []

    def test_load_invalid_plugin(self):
        """Test loading a plugin with missing register function."""
        # Create invalid plugin file
        plugin_code = """
PLUGIN_METADATA = {
    'name': 'InvalidPlugin',
    'version': '0.1.0',
    'author': 'Test',
    'description': 'Invalid plugin.'
}
"""
        plugin_path = os.path.join(PLUGIN_DIR, "invalid_plugin.py")
        with open(plugin_path, "w") as f:
            f.write(plugin_code)

        plugin = custom_behavior_plugin_system.load_plugin("invalid_plugin")
        assert plugin is None or plugin.metadata.status == PluginStatus.ERROR

    def test_load_valid_plugin(self):
        """Test loading a valid plugin and registering a behavior."""
        # Create valid plugin file
        plugin_code = """
PLUGIN_METADATA = {
    'name': 'ValidPlugin',
    'version': '1.0.0',
    'author': 'Test',
    'description': 'Valid plugin.'
}

def register(behavior_management_system):
    from svgx_engine.runtime.behavior_management_system import Behavior, BehaviorType, BehaviorStatus, BehaviorMetadata
    from datetime import datetime
    behavior = Behavior(
        id='plugin_behavior',
        name='Plugin Behavior',
        behavior_type=BehaviorType.CUSTOM,
        status=BehaviorStatus.ACTIVE,
        metadata=BehaviorMetadata(
            author='Plugin',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version='1.0.0',
            description='Behavior from plugin',
            tags=['plugin'],
            dependencies=[],
            performance_metrics={},
            usage_examples=[]
        ),
        implementation={'method_name': 'plugin_method'}
    )
    behavior_management_system.register_behavior(behavior)
    return ['plugin_behavior']
"""
        plugin_path = os.path.join(PLUGIN_DIR, "valid_plugin.py")
        with open(plugin_path, "w") as f:
            f.write(plugin_code)

        plugin = custom_behavior_plugin_system.load_plugin("valid_plugin")
        assert plugin is not None
        assert plugin.metadata.status == PluginStatus.LOADED
        assert "plugin_behavior" in plugin.registered_behaviors
        # Check that the behavior is registered
        behavior = behavior_management_system.get_behavior("plugin_behavior")
        assert behavior is not None
        # Clean up
        custom_behavior_plugin_system.unload_plugin("valid_plugin")
        behavior_management_system.delete_behavior("plugin_behavior")

    def test_validate_plugin(self):
        """Test plugin validation logic."""
        # Create valid plugin file
        plugin_code = """
PLUGIN_METADATA = {
    'name': 'ValidatePlugin',
    'version': '1.0.0',
    'author': 'Test',
    'description': 'Plugin for validation.'
}

def register(behavior_management_system):
    return []
"""
        plugin_path = os.path.join(PLUGIN_DIR, "validate_plugin.py")
        with open(plugin_path, "w") as f:
            f.write(plugin_code)

        plugin = custom_behavior_plugin_system.load_plugin("validate_plugin")
        assert plugin is not None
        assert custom_behavior_plugin_system.validate_plugin("validate_plugin") is True
        # Clean up
        custom_behavior_plugin_system.unload_plugin("validate_plugin")

    def test_plugin_performance_monitoring(self):
        """Test plugin performance monitoring."""
        # Create plugin file
        plugin_code = """
PLUGIN_METADATA = {
    'name': 'PerfPlugin',
    'version': '1.0.0',
    'author': 'Test',
    'description': 'Plugin for performance.'
}

def register(behavior_management_system):
    return []
"""
        plugin_path = os.path.join(PLUGIN_DIR, "perf_plugin.py")
        with open(plugin_path, "w") as f:
            f.write(plugin_code)

        plugin = custom_behavior_plugin_system.load_plugin("perf_plugin")
        assert plugin is not None
        # Simulate performance metrics
        plugin.metadata.performance_metrics["load_time_ms"] = 10
        metrics = custom_behavior_plugin_system.monitor_plugin_performance(
            "perf_plugin"
        )
        assert metrics["load_time_ms"] == 10
        # Clean up
        custom_behavior_plugin_system.unload_plugin("perf_plugin")

    def test_unload_plugin(self):
        """Test unloading a plugin and removing its behaviors."""
        # Create plugin file
        plugin_code = """
PLUGIN_METADATA = {
    'name': 'UnloadPlugin',
    'version': '1.0.0',
    'author': 'Test',
    'description': 'Plugin for unloading.'
}

def register(behavior_management_system):
    from svgx_engine.runtime.behavior_management_system import Behavior, BehaviorType, BehaviorStatus, BehaviorMetadata
    from datetime import datetime
    behavior = Behavior(
        id='unload_behavior',
        name='Unload Behavior',
        behavior_type=BehaviorType.CUSTOM,
        status=BehaviorStatus.ACTIVE,
        metadata=BehaviorMetadata(
            author='Plugin',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version='1.0.0',
            description='Behavior for unload test',
            tags=['plugin'],
            dependencies=[],
            performance_metrics={},
            usage_examples=[]
        ),
        implementation={'method_name': 'unload_method'}
    )
    behavior_management_system.register_behavior(behavior)
    return ['unload_behavior']
"""
        plugin_path = os.path.join(PLUGIN_DIR, "unload_plugin.py")
        with open(plugin_path, "w") as f:
            f.write(plugin_code)

        plugin = custom_behavior_plugin_system.load_plugin("unload_plugin")
        assert plugin is not None
        assert "unload_behavior" in plugin.registered_behaviors
        # Unload plugin
        result = custom_behavior_plugin_system.unload_plugin("unload_plugin")
        assert result is True
        # Behavior should be removed
        behavior = behavior_management_system.get_behavior("unload_behavior")
        assert behavior is None
