# SVGX Engine Plugin Development Guide

## Overview

The SVGX Engine provides a comprehensive plugin system that allows developers to extend the engine's functionality with custom behaviors, event processors, UI components, and more. This guide covers all aspects of plugin development, from basic concepts to advanced features.

## Table of Contents

1. [Plugin System Overview](#plugin-system-overview)
2. [Plugin Types](#plugin-types)
3. [Creating Your First Plugin](#creating-your-first-plugin)
4. [Plugin Architecture](#plugin-architecture)
5. [Security and Validation](#security-and-validation)
6. [Testing Plugins](#testing-plugins)
7. [Deployment and Distribution](#deployment-and-distribution)
8. [Best Practices](#best-practices)
9. [API Reference](#api-reference)
10. [Examples](#examples)

## Plugin System Overview

### Key Features

- **Dynamic Loading**: Plugins can be loaded and unloaded at runtime
- **Security Levels**: Multiple security levels for different trust requirements
- **Sandboxing**: Untrusted plugins run in isolated environments
- **Validation**: Automatic validation of plugin structure and security
- **Monitoring**: Built-in performance monitoring and usage tracking
- **Type Safety**: Strong typing with comprehensive interfaces

### Plugin Lifecycle

1. **Discovery**: Plugin files are discovered in the plugins directory
2. **Validation**: Security and structure validation
3. **Loading**: Plugin module is loaded and instantiated
4. **Initialization**: Plugin is initialized with configuration
5. **Execution**: Plugin methods are called during runtime
6. **Monitoring**: Performance and usage are tracked
7. **Cleanup**: Plugin resources are cleaned up on unload

## Plugin Types

### Behavior Handler Plugins

Handle custom behaviors for UI interactions:

```python
from svgx_engine.services.plugin_system import BehaviorHandlerPlugin

class MyBehaviorPlugin(BehaviorHandlerPlugin):
    async def handle_behavior(self, behavior_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        # Custom behavior logic
        return {"processed": True, "result": "custom_behavior"}
```

### Event Processor Plugins

Process and transform events:

```python
from svgx_engine.services.plugin_system import EventProcessorPlugin

class MyEventPlugin(EventProcessorPlugin):
    async def process_event(self, event_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        # Event processing logic
        return {"processed": True, "transformed_event": event_data}
```

### UI Component Plugins

Create custom UI components:

```python
from svgx_engine.services.plugin_system import UIComponentPlugin

class MyUIComponentPlugin(UIComponentPlugin):
    def render_component(self, props: Dict[str, Any]) -> Dict[str, Any]:
        # Component rendering logic
        return {"type": "custom_component", "props": props}
```

### Data Transformer Plugins

Transform data between formats:

```python
from svgx_engine.services.plugin_system import DataTransformerPlugin

class MyDataTransformerPlugin(DataTransformerPlugin):
    def transform_data(self, data: Any, config: Dict[str, Any]) -> Any:
        # Data transformation logic
        return transformed_data
```

### Custom Animation Plugins

Create custom animations:

```python
from svgx_engine.services.plugin_system import CustomAnimationPlugin

class MyAnimationPlugin(CustomAnimationPlugin):
    async def create_animation(self, animation_config: Dict[str, Any]) -> Dict[str, Any]:
        # Animation creation logic
        return {"animation": "custom_animation", "config": animation_config}
```

### Rule Engine Plugins

Implement custom business rules:

```python
from svgx_engine.services.plugin_system import RuleEnginePlugin

class MyRulePlugin(RuleEnginePlugin):
    def evaluate_rule(self, rule_data: Dict[str, Any], context: Dict[str, Any]) -> bool:
        # Rule evaluation logic
        return rule_result
```

### Export/Import Format Plugins

Handle custom file formats:

```python
from svgx_engine.services.plugin_system import ExportFormatPlugin, ImportFormatPlugin

class MyExportPlugin(ExportFormatPlugin):
    def export_data(self, data: Any, format_config: Dict[str, Any]) -> bytes:
        # Export logic
        return exported_bytes

class MyImportPlugin(ImportFormatPlugin):
    def import_data(self, data: bytes, format_config: Dict[str, Any]) -> Any:
        # Import logic
        return imported_data
```

## Creating Your First Plugin

### Step 1: Create Plugin Structure

```python
"""
My First Plugin for SVGX Engine

This plugin demonstrates basic plugin development.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from svgx_engine.services.plugin_system import (
    BehaviorHandlerPlugin,
    PluginMetadata,
    PluginSecurityLevel,
    PluginType
)

logger = logging.getLogger(__name__)


class MyFirstPlugin(BehaviorHandlerPlugin):
    """My first plugin implementation."""

    def __init__(self):
        self.initialized = False
        self.config = {}

    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin with configuration."""
        try:
            self.config = config
            self.initialized = True
            logger.info("MyFirstPlugin initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize MyFirstPlugin: {e}")
            return False

    def cleanup(self) -> None:
        """Clean up plugin resources."""
        self.initialized = False
        logger.info("MyFirstPlugin cleaned up")

    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name="MyFirstPlugin",
            version="1.0.0",
            description="My first plugin for SVGX Engine",
            author="Your Name",
            plugin_type=PluginType.BEHAVIOR_HANDLER,
            security_level=PluginSecurityLevel.VERIFIED,
            tags=["example", "first", "demo"]
        )

    async def handle_behavior(self, behavior_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a behavior event."""
        if not self.initialized:
            raise RuntimeError("Plugin not initialized")

        # Your custom behavior logic here
        behavior_type = behavior_data.get('type', 'unknown')

        result = {
            'processed': True,
            'behavior_type': behavior_type,
            'plugin': 'MyFirstPlugin',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'message': f"Processed {behavior_type} behavior"
        }

        logger.info(f"MyFirstPlugin processed behavior: {behavior_type}")
        return result


# Plugin factory function
def create_plugin() -> MyFirstPlugin:
    """Factory function to create plugin instance."""
    return MyFirstPlugin()
```

### Step 2: Save the Plugin

Save your plugin in the `plugins/` directory:

```bash
# Create plugins directory if it doesn't exist
mkdir -p plugins

# Save your plugin
cp my_first_plugin.py plugins/
```

### Step 3: Load and Test the Plugin

```python
from svgx_engine.services.plugin_system import plugin_manager

# Load the plugin
plugin_info = plugin_manager.load_plugin("plugins/my_first_plugin.py")

# Test the plugin
result = plugin_manager.execute_plugin(
    "MyFirstPlugin_1.0.0",
    "handle_behavior",
    {"type": "click", "canvas_id": "canvas_123"},
    {"user_id": "user_456"}
)

print(f"Plugin result: {result}")
```

## Plugin Architecture

### Required Methods

Every plugin must implement these methods:

#### `initialize(config: Dict[str, Any]) -> bool`

Initialize the plugin with configuration. Return `True` on success, `False` on failure.

```python
def initialize(self, config: Dict[str, Any]) -> bool:
    try:
        self.config = config
        # Initialize your plugin resources
        return True
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        return False
```

#### `cleanup() -> None`

Clean up plugin resources when the plugin is unloaded.

```python
def cleanup(self) -> None:
    # Clean up resources
    self.initialized = False
    # Close connections, free memory, etc.
```

#### `get_metadata() -> PluginMetadata`

Return plugin metadata for registration and identification.

```python
def get_metadata(self) -> PluginMetadata:
    return PluginMetadata(
        name="MyPlugin",
        version="1.0.0",
        description="My plugin description",
        author="Your Name",
        plugin_type=PluginType.BEHAVIOR_HANDLER,
        security_level=PluginSecurityLevel.VERIFIED,
        tags=["custom", "example"]
    )
```

### Plugin-Specific Methods

Each plugin type has specific methods that must be implemented:

#### Behavior Handler
```python
async def handle_behavior(self, behavior_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    # Process behavior and return result
    return {"processed": True, "result": "custom_behavior"}
```

#### Event Processor
```python
async def process_event(self, event_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    # Process event and return result
    return {"processed": True, "transformed_event": event_data}
```

#### UI Component
```python
def render_component(self, props: Dict[str, Any]) -> Dict[str, Any]:
    # Render component and return result
    return {"type": "custom_component", "props": props}
```

## Security and Validation

### Security Levels

Plugins are classified by security level:

- **TRUSTED**: Signed by trusted authority, full access
- **VERIFIED**: Code verified and safe, standard access
- **SANDBOXED**: Run in restricted environment
- **UNTRUSTED**: Run with maximum restrictions

### Validation Process

Plugins are automatically validated for:

1. **File Size**: Maximum 10MB
2. **Forbidden Imports**: No dangerous modules
3. **Forbidden Functions**: No dangerous functions
4. **Suspicious Patterns**: No malicious code patterns
5. **Structure**: Proper plugin structure

### Security Best Practices

```python
# ✅ Good: Safe imports
import json
import logging
from datetime import datetime

# ❌ Bad: Dangerous imports
import os
import subprocess
import sys

# ✅ Good: Safe function usage
data = json.loads(json_string)

# ❌ Bad: Dangerous function usage
result = eval(user_input)
```

### Sandboxing

Untrusted plugins run in sandboxed environments:

```python
# Plugin runs in isolated environment
result = await plugin_manager.execute_plugin(
    plugin_name="untrusted_plugin",
    method="process_data",
    data=user_data
)
```

## Testing Plugins

### Unit Testing

```python
import pytest
from svgx_engine.services.plugin_system import plugin_manager

class TestMyPlugin:
    def setup_method(self):
        self.plugin_info = plugin_manager.load_plugin("plugins/my_plugin.py")
        self.plugin = plugin_manager.get_plugin("MyPlugin_1.0.0")

    def teardown_method(self):
        plugin_manager.unload_plugin("MyPlugin_1.0.0")

    def test_plugin_initialization(self):
        """Test plugin initialization."""
        assert self.plugin.initialize({}) == True
        assert self.plugin.initialized == True

    def test_plugin_metadata(self):
        """Test plugin metadata."""
        metadata = self.plugin.get_metadata()
        assert metadata.name == "MyPlugin"
        assert metadata.version == "1.0.0"

    @pytest.mark.asyncio
    async def test_behavior_handling(self):
        """Test behavior handling."""
        self.plugin.initialize({})

        result = await self.plugin.handle_behavior(
            {"type": "click", "canvas_id": "test"},
            {"user_id": "test_user"}
        )

        assert result["processed"] == True
        assert result["behavior_type"] == "click"
```

### Integration Testing

```python
import asyncio
from svgx_engine.services.plugin_system import plugin_manager

async def test_plugin_integration():
    """Test plugin integration with the engine."""

    # Load plugin
    plugin_info = plugin_manager.load_plugin("plugins/my_plugin.py")
    assert plugin_info is not None

    # Test plugin execution
    result = await plugin_manager.execute_plugin(
        "MyPlugin_1.0.0",
        "handle_behavior",
        {"type": "click", "canvas_id": "test_canvas"},
        {"user_id": "test_user"}
    )

    assert result["processed"] == True

    # Test plugin metrics
    metrics = plugin_manager.get_plugin_metrics()
    assert "MyPlugin_1.0.0" in metrics["active_plugins"]

    # Cleanup
    plugin_manager.unload_plugin("MyPlugin_1.0.0")

# Run integration test
asyncio.run(test_plugin_integration())
```

### Performance Testing

```python
import time
import asyncio
from svgx_engine.services.plugin_system import plugin_manager

async def test_plugin_performance():
    """Test plugin performance."""

    plugin_name = "MyPlugin_1.0.0"
    plugin_manager.load_plugin("plugins/my_plugin.py")

    # Test execution time
    start_time = time.time()

    for i in range(100):
        await plugin_manager.execute_plugin(
            plugin_name,
            "handle_behavior",
            {"type": "click", "canvas_id": f"canvas_{i}"},
            {"user_id": "test_user"}
        )

    end_time = time.time()
    total_time = end_time - start_time

    print(f"Processed 100 behaviors in {total_time:.2f} seconds")
    print(f"Average time per behavior: {total_time/100:.3f} seconds")

    # Check performance metrics
    performance = plugin_manager.get_plugin_performance(plugin_name)
    print(f"Plugin performance: {performance}")

asyncio.run(test_plugin_performance())
```

## Deployment and Distribution

### Plugin Packaging

Create a plugin package:

```python
# setup.py for your plugin
from setuptools import setup, find_packages

setup(
    name="my-svgx-plugin",
    version="1.0.0",
    description="My custom plugin for SVGX Engine",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "svgx-engine>=1.0.0"
    ],
    entry_points={
        "svgx_plugins": [
            "my_plugin = my_plugin:MyPlugin"
        ]
    }
)
```

### Plugin Distribution

```bash
# Build plugin package
python setup.py sdist bdist_wheel

# Install plugin
pip install dist/my-svgx-plugin-1.0.0.tar.gz

# Or install from source
pip install -e .
```

### Plugin Configuration

```yaml
# plugin_config.yaml
plugins:
  my_plugin:
    enabled: true
    config:
      custom_setting: "value"
      timeout: 30
    security_level: "verified"
    auto_load: true
```

## Best Practices

### Code Organization

```python
"""
Well-organized plugin structure
"""

import logging
from typing import Any, Dict, Optional
from datetime import datetime, timezone

from svgx_engine.services.plugin_system import (
    BehaviorHandlerPlugin,
    PluginMetadata,
    PluginSecurityLevel,
    PluginType
)

logger = logging.getLogger(__name__)


class WellOrganizedPlugin(BehaviorHandlerPlugin):
    """Well-organized plugin with proper structure."""

    def __init__(self):
        self.initialized = False
        self.config = {}
        self._setup_logging()

    def _setup_logging(self):
        """Setup plugin-specific logging."""
        self.logger = logging.getLogger(f"{__name__}.WellOrganizedPlugin")

    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin with proper error handling."""
        try:
            self.config = config
            self._validate_config()
            self._setup_resources()
            self.initialized = True
            self.logger.info("Plugin initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            return False

    def _validate_config(self):
        """Validate plugin configuration."""
        required_keys = ["api_key", "endpoint"]
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"Missing required config key: {key}")

    def _setup_resources(self):
        """Setup plugin resources."""
        # Initialize connections, caches, etc.
        pass

    def cleanup(self) -> None:
        """Clean up plugin resources properly."""
        try:
            self._cleanup_resources()
            self.initialized = False
            self.logger.info("Plugin cleaned up successfully")
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")

    def _cleanup_resources(self):
        """Clean up plugin resources."""
        # Close connections, free memory, etc.
        pass

    def get_metadata(self) -> PluginMetadata:
        """Get comprehensive plugin metadata."""
        return PluginMetadata(
            name="WellOrganizedPlugin",
            version="1.0.0",
            description="A well-organized plugin example",
            author="Your Name",
            plugin_type=PluginType.BEHAVIOR_HANDLER,
            security_level=PluginSecurityLevel.VERIFIED,
            tags=["well-organized", "example", "best-practices"],
            dependencies=["requests>=2.25.0"],
            requirements=["python>=3.8"],
            homepage="https://github.com/your-org/svgx-plugin",
            license="MIT"
        )

    async def handle_behavior(self, behavior_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle behavior with proper error handling and logging."""
        if not self.initialized:
            raise RuntimeError("Plugin not initialized")

        try:
            result = await self._process_behavior(behavior_data, context)
            self.logger.info(f"Behavior processed successfully: {behavior_data.get('type')}")
            return result
        except Exception as e:
            self.logger.error(f"Behavior processing failed: {e}")
            return {
                "processed": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def _process_behavior(self, behavior_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Process behavior with custom logic."""
        behavior_type = behavior_data.get('type', 'unknown')

        # Your custom behavior logic here
        result = {
            "processed": True,
            "behavior_type": behavior_type,
            "plugin": "WellOrganizedPlugin",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "custom_data": "your_custom_data"
        }

        return result
```

### Error Handling

```python
def handle_behavior(self, behavior_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle behavior with comprehensive error handling."""
    try:
        # Validate input
        if not behavior_data:
            raise ValueError("Behavior data is required")

        # Process behavior
        result = self._process_behavior(behavior_data, context)

        # Validate output
        if not isinstance(result, dict):
            raise ValueError("Result must be a dictionary")

        return result

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return {"processed": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"processed": False, "error": "Internal error"}
```

### Performance Optimization

```python
class OptimizedPlugin(BehaviorHandlerPlugin):
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes

    def _get_cached_result(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached result if available and not expired."""
        if key in self.cache:
            timestamp, result = self.cache[key]
            if time.time() - timestamp < self.cache_ttl:
                return result
            else:
                del self.cache[key]
        return None

    def _cache_result(self, key: str, result: Dict[str, Any]):
        """Cache result with timestamp."""
        self.cache[key] = (time.time(), result)

    async def handle_behavior(self, behavior_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle behavior with caching for performance."""
        cache_key = f"{behavior_data.get('type')}_{behavior_data.get('canvas_id')}"

        # Check cache first
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return cached_result

        # Process behavior
        result = await self._process_behavior(behavior_data, context)

        # Cache result
        self._cache_result(cache_key, result)

        return result
```

## API Reference

### PluginManager

Main class for managing plugins.

#### Methods

- `load_plugin(plugin_path: Union[str, Path]) -> Optional[PluginInfo]`
- `unload_plugin(plugin_name: str) -> bool`
- `get_plugin(plugin_name: str) -> Optional[PluginInterface]`
- `execute_plugin(plugin_name: str, method: str, *args, **kwargs) -> Any`
- `list_plugins(plugin_type: Optional[PluginType] = None) -> List[PluginInfo]`

### PluginMetadata

Metadata for plugin registration.

#### Fields

- `name: str` - Plugin name
- `version: str` - Plugin version
- `description: str` - Plugin description
- `author: str` - Plugin author
- `plugin_type: PluginType` - Type of plugin
- `security_level: PluginSecurityLevel` - Security level
- `tags: List[str]` - Plugin tags
- `dependencies: List[str]` - Required dependencies
- `requirements: List[str]` - System requirements

### PluginTypes

Available plugin types:

- `BEHAVIOR_HANDLER` - Handle UI behaviors
- `EVENT_PROCESSOR` - Process events
- `UI_COMPONENT` - Create UI components
- `DATA_TRANSFORMER` - Transform data
- `CUSTOM_ANIMATION` - Create animations
- `RULE_ENGINE` - Implement business rules
- `EXPORT_FORMAT` - Export data formats
- `IMPORT_FORMAT` - Import data formats

### SecurityLevels

Plugin security levels:

- `TRUSTED` - Signed by trusted authority
- `VERIFIED` - Code verified and safe
- `SANDBOXED` - Run in restricted environment
- `UNTRUSTED` - Run with maximum restrictions

## Examples

### Simple Behavior Plugin

```python
class SimpleBehaviorPlugin(BehaviorHandlerPlugin):
    def initialize(self, config: Dict[str, Any]) -> bool:
        self.initialized = True
        return True

    def cleanup(self) -> None:
        self.initialized = False

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="SimpleBehaviorPlugin",
            version="1.0.0",
            description="A simple behavior plugin",
            author="Your Name",
            plugin_type=PluginType.BEHAVIOR_HANDLER,
            security_level=PluginSecurityLevel.VERIFIED
        )

    async def handle_behavior(self, behavior_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "processed": True,
            "behavior_type": behavior_data.get("type"),
            "message": "Simple behavior processed"
        }
```

### Advanced Event Processor

```python
class AdvancedEventProcessorPlugin(EventProcessorPlugin):
    def __init__(self):
        self.event_count = 0
        self.event_types = set()

    def initialize(self, config: Dict[str, Any]) -> bool:
        self.config = config
        self.initialized = True
        return True

    def cleanup(self) -> None:
        self.initialized = False

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="AdvancedEventProcessorPlugin",
            version="1.0.0",
            description="Advanced event processing with analytics",
            author="Your Name",
            plugin_type=PluginType.EVENT_PROCESSOR,
            security_level=PluginSecurityLevel.VERIFIED,
            tags=["advanced", "analytics", "event-processing"]
        )

    async def process_event(self, event_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        self.event_count += 1
        event_type = event_data.get("type", "unknown")
        self.event_types.add(event_type)

        # Advanced event processing logic
        processed_event = {
            "original_event": event_data,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "analytics": {
                "total_events": self.event_count,
                "unique_event_types": len(self.event_types),
                "event_types": list(self.event_types)
            }
        }

        return {
            "processed": True,
            "processed_event": processed_event,
            "analytics": processed_event["analytics"]
        }
```

## Conclusion

This guide provides comprehensive coverage of plugin development for the SVGX Engine. By following these guidelines and best practices, you can create robust, secure, and performant plugins that extend the engine's functionality.

For additional support:

- **Plugin Examples**: [https://github.com/svgx-engine/plugins](https://github.com/svgx-engine/plugins)
- **API Documentation**: [https://docs.svgx-engine.com/plugins](https://docs.svgx-engine.com/plugins)
- **Community Forum**: [https://community.svgx-engine.com](https://community.svgx-engine.com)
- **Support Email**: plugins@svgx-engine.com
