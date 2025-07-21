"""
SVGX Engine - Custom Behavior Plugin System

Handles extensible plugin architecture for custom behaviors, including dynamic loading, registration, validation, security, performance monitoring, and dependency management.
Integrates with the core behavior management system and event-driven engine.
Follows Arxos engineering standards: absolute imports, global instances, modular/testable code, and comprehensive documentation.
"""

from typing import Dict, Any, List, Optional, Set, Callable, Type
from svgx_engine.runtime.event_driven_behavior_engine import Event, EventType, EventPriority
from svgx_engine.runtime.behavior_management_system import behavior_management_system, Behavior, BehaviorType, BehaviorStatus, BehaviorMetadata
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import importlib
import sys
import os
import traceback
import threading
import time
import types
import inspect

logger = logging.getLogger(__name__)

class PluginStatus(Enum):
    LOADED = "loaded"
    UNLOADED = "unloaded"
    ERROR = "error"
    INVALID = "invalid"
    DISABLED = "disabled"

@dataclass
class PluginMetadata:
    name: str
    version: str
    author: str
    description: str
    entry_point: str
    dependencies: List[str] = field(default_factory=list)
    loaded_at: Optional[datetime] = None
    status: PluginStatus = PluginStatus.UNLOADED
    error: Optional[str] = None
    performance_metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BehaviorPlugin:
    id: str
    metadata: PluginMetadata
    module: Optional[types.ModuleType] = None
    registered_behaviors: List[str] = field(default_factory=list)
    last_loaded: Optional[datetime] = None
    last_error: Optional[str] = None

class CustomBehaviorPluginSystem:
    """
    Extensible plugin system for custom behaviors, supporting dynamic loading, registration, validation, security, and monitoring.
    """
    def __init__(self):
        # {plugin_id: BehaviorPlugin}
        self.plugins: Dict[str, BehaviorPlugin] = {}
        # {behavior_id: plugin_id}
        self.behavior_to_plugin: Dict[str, str] = {}
        # Thread safety
        self._lock = threading.RLock()
        # Plugin directory
        self.plugin_dir = os.path.join(os.path.dirname(__file__), "plugins")
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir)

    def discover_plugins(self) -> List[str]:
        """Discover available plugin modules in the plugin directory."""
        plugins = []
        for fname in os.listdir(self.plugin_dir):
            if fname.endswith(".py") and not fname.startswith("__"):
                plugins.append(fname[:-3])
        logger.info(f"Discovered plugins: {plugins}")
        return plugins

    def load_plugin(self, plugin_name: str) -> Optional[BehaviorPlugin]:
        """Dynamically load a plugin module by name."""
        try:
            with self._lock:
                module_path = f"svgx_engine.runtime.plugins.{plugin_name}"
                if module_path in sys.modules:
                    importlib.reload(sys.modules[module_path])
                    module = sys.modules[module_path]
                else:
                    module = importlib.import_module(module_path)
                
                # Validate plugin structure
                if not hasattr(module, "register"):
                    raise ImportError(f"Plugin {plugin_name} missing required 'register' function.")
                
                # Extract metadata
                meta = getattr(module, "PLUGIN_METADATA", None)
                if not meta or not isinstance(meta, dict):
                    raise ImportError(f"Plugin {plugin_name} missing or invalid PLUGIN_METADATA.")
                
                plugin_metadata = PluginMetadata(
                    name=meta.get("name", plugin_name),
                    version=meta.get("version", "0.1.0"),
                    author=meta.get("author", "Unknown"),
                    description=meta.get("description", ""),
                    entry_point=module_path,
                    dependencies=meta.get("dependencies", []),
                    loaded_at=datetime.utcnow(),
                    status=PluginStatus.LOADED
                )
                
                plugin = BehaviorPlugin(
                    id=plugin_name,
                    metadata=plugin_metadata,
                    module=module,
                    last_loaded=datetime.utcnow()
                )
                
                # Register plugin behaviors
                registered_behaviors = module.register(behavior_management_system)
                if not isinstance(registered_behaviors, list):
                    registered_behaviors = []
                plugin.registered_behaviors = registered_behaviors
                for behavior_id in registered_behaviors:
                    self.behavior_to_plugin[behavior_id] = plugin_name
                
                self.plugins[plugin_name] = plugin
                logger.info(f"Loaded plugin: {plugin_name}")
                return plugin
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {e}\n{traceback.format_exc()}")
            plugin_metadata = PluginMetadata(
                name=plugin_name,
                version="0.0.0",
                author="Unknown",
                description="",
                entry_point=plugin_name,
                loaded_at=datetime.utcnow(),
                status=PluginStatus.ERROR,
                error=str(e)
            )
            plugin = BehaviorPlugin(
                id=plugin_name,
                metadata=plugin_metadata,
                last_error=str(e)
            )
            self.plugins[plugin_name] = plugin
            return None

    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin and remove its behaviors."""
        try:
            with self._lock:
                if plugin_name not in self.plugins:
                    logger.warning(f"Plugin {plugin_name} not loaded")
                    return False
                plugin = self.plugins[plugin_name]
                # Remove registered behaviors
                for behavior_id in plugin.registered_behaviors:
                    behavior_management_system.delete_behavior(behavior_id)
                    self.behavior_to_plugin.pop(behavior_id, None)
                plugin.metadata.status = PluginStatus.UNLOADED
                plugin.last_loaded = None
                logger.info(f"Unloaded plugin: {plugin_name}")
                return True
        except Exception as e:
            logger.error(f"Error unloading plugin {plugin_name}: {e}")
            return False

    def validate_plugin(self, plugin_name: str) -> bool:
        """Validate plugin structure and security."""
        try:
            with self._lock:
                if plugin_name not in self.plugins:
                    logger.warning(f"Plugin {plugin_name} not loaded")
                    return False
                plugin = self.plugins[plugin_name]
                module = plugin.module
                # Check for required functions
                if not hasattr(module, "register"):
                    logger.error(f"Plugin {plugin_name} missing 'register' function")
                    return False
                # Check for forbidden imports (basic security)
                source = inspect.getsource(module)
                forbidden = ["os.system", "subprocess", "eval", "exec", "open(", "importlib.import_module"]
                for bad in forbidden:
                    if bad in source:
                        logger.error(f"Plugin {plugin_name} uses forbidden code: {bad}")
                        return False
                logger.info(f"Plugin {plugin_name} validated successfully")
                return True
        except Exception as e:
            logger.error(f"Error validating plugin {plugin_name}: {e}")
            return False

    def monitor_plugin_performance(self, plugin_name: str) -> Dict[str, Any]:
        """Return performance metrics for a plugin."""
        try:
            with self._lock:
                if plugin_name not in self.plugins:
                    return {}
                plugin = self.plugins[plugin_name]
                return plugin.metadata.performance_metrics
        except Exception as e:
            logger.error(f"Error monitoring plugin {plugin_name}: {e}")
            return {}

    def get_plugin(self, plugin_name: str) -> Optional[BehaviorPlugin]:
        return self.plugins.get(plugin_name)

    def get_plugins(self, status: Optional[PluginStatus] = None) -> List[BehaviorPlugin]:
        if status:
            return [p for p in self.plugins.values() if p.metadata.status == status]
        return list(self.plugins.values())

    def get_plugin_behaviors(self, plugin_name: str) -> List[str]:
        plugin = self.plugins.get(plugin_name)
        return plugin.registered_behaviors if plugin else []

    def reload_plugin(self, plugin_name: str) -> Optional[BehaviorPlugin]:
        self.unload_plugin(plugin_name)
        return self.load_plugin(plugin_name)

# Global instance
custom_behavior_plugin_system = CustomBehaviorPluginSystem()

# Register with the event-driven engine
def _register_custom_behavior_plugin_system():
    def handler(event: Event):
        if event.type == EventType.SYSTEM and event.data.get('plugin'):
            # Plugin events are handled internally
            return None
        return None
    
    # Import here to avoid circular imports
    from svgx_engine.runtime.event_driven_behavior_engine import event_driven_behavior_engine
    event_driven_behavior_engine.register_handler(
        event_type=EventType.SYSTEM,
        handler_id='custom_behavior_plugin_system',
        handler=handler,
        priority=4
    )

_register_custom_behavior_plugin_system() 