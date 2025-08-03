"""
Example Behavior Handler Plugin for SVGX Engine

This plugin demonstrates how to create a custom behavior handler
that can process UI events and modify canvas objects.
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


class ExampleBehaviorPlugin(BehaviorHandlerPlugin):
    """Example behavior handler plugin that adds custom behaviors."""
    
    def __init__(self):
        """
        Initialize the plugin.
        
        Args:
            None
            
        Returns:
            None
            
        Raises:
            None
        """
        self.initialized = False
        self.config = {}
        self.behavior_count = 0
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin with configuration."""
        try:
            self.config = config
            self.initialized = True
            logger.info("ExampleBehaviorPlugin initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize ExampleBehaviorPlugin: {e}")
            return False
    
    def cleanup(self) -> None:
        """Clean up plugin resources."""
        self.initialized = False
        logger.info("ExampleBehaviorPlugin cleaned up")
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name="ExampleBehaviorPlugin",
            version="1.0.0",
            description="Example behavior handler plugin that demonstrates custom behaviors",
            author="SVGX Team",
            plugin_type=PluginType.BEHAVIOR_HANDLER,
            security_level=PluginSecurityLevel.VERIFIED,
            tags=["example", "behavior", "demo"],
            dependencies=[],
            requirements=[],
            homepage="https://github.com/svgx-engine/plugins",
            license="MIT"
        )
    
    async def handle_behavior(self, behavior_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a behavior event with custom logic."""
        if not self.initialized:
            raise RuntimeError("Plugin not initialized")
        
        self.behavior_count += 1
        
        # Extract behavior information
        behavior_type = behavior_data.get('type', 'unknown')
        canvas_id = behavior_data.get('canvas_id')
        object_id = behavior_data.get('object_id')
        user_id = context.get('user_id', 'unknown')
        
        logger.info(f"Processing behavior: {behavior_type} for object {object_id} on canvas {canvas_id}")
        
        # Apply custom behavior logic based on type
        result = {
            'processed': True,
            'behavior_type': behavior_type,
            'plugin': 'ExampleBehaviorPlugin',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'behavior_count': self.behavior_count,
            'modifications': {}
        }
        
        if behavior_type == 'select':
            # Add selection highlighting
            result['modifications'] = {
                'highlight': True,
                'highlight_color': '#ffeb3b',
                'highlight_width': 2
            }
        
        elif behavior_type == 'hover':
            # Add hover effects
            result['modifications'] = {
                'cursor': 'pointer',
                'tooltip': f"Object {object_id} (hovered by {user_id})"
            }
        
        elif behavior_type == 'click':
            # Add click effects
            result['modifications'] = {
                'click_effect': True,
                'click_sound': 'click.mp3',
                'click_animation': 'pulse'
            }
        
        elif behavior_type == 'drag':
            # Add drag effects
            result['modifications'] = {
                'drag_effect': True,
                'drag_cursor': 'grabbing',
                'drag_preview': True
            }
        
        elif behavior_type == 'resize':
            # Add resize effects
            result['modifications'] = {
                'resize_handles': True,
                'resize_constraints': {
                    'min_width': 10,
                    'min_height': 10,
                    'aspect_ratio': 'free'
                }
            }
        
        # Log the behavior processing
        logger.info(f"Behavior processed successfully: {behavior_type} -> {result['modifications']}")
        
        return result


# Plugin factory function for dynamic loading
def create_plugin() -> ExampleBehaviorPlugin:
    """Factory function to create plugin instance."""
    return ExampleBehaviorPlugin() 