"""
SVGX Behavior Engine for handling programmable behavior and triggers.

This module manages behavior profiles, event triggers, and interactive
responses in SVGX elements.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import html

logger = logging.getLogger(__name__)


class TriggerType(Enum):
    """Types of behavior triggers."""
    CLICK = "click"
    HOVER = "hover"
    DRAG = "drag"
    TIME = "time"
    CONDITION = "condition"
    EXTERNAL = "external"


class ActionType(Enum):
    """Types of behavior actions."""
    ANIMATE = "animate"
    CALCULATE = "calculate"
    UPDATE = "update"
    TRIGGER = "trigger"
    LOG = "log"


@dataclass
class BehaviorTrigger:
    """Represents a behavior trigger."""
    event: str
    action: str
    condition: Optional[str] = None
    parameters: Dict[str, Any] = None


@dataclass
class BehaviorAction:
    """Represents a behavior action."""
    action_type: ActionType
    target: str
    parameters: Dict[str, Any]
    callback: Optional[Callable] = None


class SVGXBehaviorEngine:
    """Engine for managing SVGX behavior and interactions."""

    def __init__(self):
        self.triggers: Dict[str, List[BehaviorTrigger]] = {}
        self.actions: Dict[str, BehaviorAction] = {}
        self.event_handlers: Dict[str, Callable] = {}
        self.running = False
        self._setup_default_handlers()

    def _setup_default_handlers(self):
        """Setup default event handlers."""
        self.event_handlers = {
            'click': self._handle_click,
            'hover': self._handle_hover,
            'drag': self._handle_drag,
            'time': self._handle_time,
            'condition': self._handle_condition,
            'external': self._handle_external
        }

    def register_behavior(self, element_id: str, behavior_data: Dict[str, Any]):
        """
        Register behavior for an element.

        Args:
            element_id: ID of the SVGX element
            behavior_data: Behavior configuration
        """
        try:
            triggers = []

            # Parse triggers from behavior data
            if 'triggers' in behavior_data:
                for trigger_data in behavior_data['triggers']:
                    trigger = BehaviorTrigger(
                        event=trigger_data.get('event', ''),
                        action=trigger_data.get('action', ''),
                        condition=trigger_data.get('condition'),
                        parameters=trigger_data.get('parameters', {})
                    triggers.append(trigger)

            self.triggers[element_id] = triggers
            logger.info(f"Registered behavior for element {element_id}")

        except Exception as e:
            logger.error(f"Failed to register behavior for {element_id}: {e}")

    def register_action(self, action_id: str, action_data: Dict[str, Any]):
        """
        Register an action that can be triggered.

        Args:
            action_id: Unique identifier for the action
            action_data: Action configuration
        """
        try:
            action_type = ActionType(action_data.get('type', 'update')
            target = action_data.get('target', '')
            parameters = action_data.get('parameters', {})

            action = BehaviorAction(
                action_type=action_type,
                target=target,
                parameters=parameters
            )

            self.actions[action_id] = action
            logger.info(f"Registered action {action_id}")

        except Exception as e:
            logger.error(f"Failed to register action {action_id}: {e}")

    async def handle_event(self, element_id: str, event_type: str, event_data: Dict[str, Any] = None):
        """
        Handle an event for an element.

        Args:
            element_id: ID of the element
            event_type: Type of event
            event_data: Additional event data
        """
        try:
            if element_id not in self.triggers:
                return

            triggers = self.triggers[element_id]
            event_data = event_data or {}

            for trigger in triggers:
                if trigger.event == event_type:
                    await self._execute_trigger(trigger, element_id, event_data)

        except Exception as e:
            logger.error(f"Failed to handle event {event_type} for {element_id}: {e}")

    async def _execute_trigger(self, trigger: BehaviorTrigger, element_id: str, event_data: Dict[str, Any]):
        """
        Execute a trigger action.

        Args:
            trigger: The trigger to execute
            element_id: ID of the element
            event_data: Event data
        """
        try:
            # Check condition if specified
            if trigger.condition:
                if not self._evaluate_condition(trigger.condition, event_data):
                    return

            # Execute the action
            if trigger.action in self.actions:
                action = self.actions[trigger.action]
                await self._execute_action(action, element_id, event_data)
            else:
                # Default action handling
                await self._execute_default_action(trigger, element_id, event_data)

        except Exception as e:
            logger.error(f"Failed to execute trigger: {e}")

    def _evaluate_condition(self, condition: str, event_data: Dict[str, Any]) -> bool:
        """
        Evaluate a condition expression.

        Args:
            condition: Condition expression
            event_data: Event data for evaluation

        Returns:
            True if condition is met
        """
        try:
            # Simple condition evaluation
            # In a real implementation, this would use a proper expression parser
            if condition.startswith('if '):
                condition = condition[3:]  # Remove 'if '

            # Basic condition checks
            if '==' in condition:
                left, right = condition.split('==')
                return event_data.get(left.strip()) == right.strip()
            elif '!=' in condition:
                left, right = condition.split('!=')
                return event_data.get(left.strip()) != right.strip()
            elif '>' in condition:
                left, right = condition.split('>')
                return float(event_data.get(left.strip(), 0)) > float(right.strip()
            elif '<' in condition:
                left, right = condition.split('<')
                return float(event_data.get(left.strip(), 0)) < float(right.strip()
            return True

        except Exception as e:
            logger.warning(f"Failed to evaluate condition '{condition}': {e}")
            return False

    async def _execute_action(self, action: BehaviorAction, element_id: str, event_data: Dict[str, Any]):
        """
        Execute an action.

        Args:
            action: The action to execute
            element_id: ID of the element
            event_data: Event data
        """
        try:
            if action.action_type == ActionType.ANIMATE:
                await self._execute_animate_action(action, element_id, event_data)
            elif action.action_type == ActionType.CALCULATE:
                await self._execute_calculate_action(action, element_id, event_data)
            elif action.action_type == ActionType.UPDATE:
                await self._execute_update_action(action, element_id, event_data)
            elif action.action_type == ActionType.TRIGGER:
                await self._execute_trigger_action(action, element_id, event_data)
            elif action.action_type == ActionType.LOG:
                await self._execute_log_action(action, element_id, event_data)

        except Exception as e:
            logger.error(f"Failed to execute action: {e}")

    async def _execute_animate_action(self, action: BehaviorAction, element_id: str, event_data: Dict[str, Any]):
        """Execute an animation action."""
        target = action.target
        parameters = action.parameters

        animation_type = parameters.get('type', 'fade')
        duration = parameters.get('duration', 1000)

        logger.info(f"Animating {element_id} with {animation_type} for {duration}ms")
        # In a real implementation, this would trigger actual animations

    async def _execute_calculate_action(self, action: BehaviorAction, element_id: str, event_data: Dict[str, Any]):
        """Execute a calculation action."""
        formula = action.parameters.get('formula', '')
        target_var = action.parameters.get('target', 'result')

        try:
            # Simple formula evaluation
            result = # SECURITY: eval() removed - use safe alternatives
        # eval(formula, {"__builtins__": {}}, event_data)
            logger.info(f"Calculated {target_var} = {result} for {element_id}")
        except Exception as e:
            logger.error(f"Failed to calculate formula: {e}")

    async def _execute_update_action(self, action: BehaviorAction, element_id: str, event_data: Dict[str, Any]):
        """Execute an update action."""
        target = action.target
        value = action.parameters.get('value', '')

        logger.info(f"Updating {target} to {value} for {element_id}")
        # In a real implementation, this would update the actual element

    async def _execute_trigger_action(self, action: BehaviorAction, element_id: str, event_data: Dict[str, Any]):
        """Execute a trigger action."""
        target_element = action.parameters.get('target_element', '')
        event_type = action.parameters.get('event_type', 'click')

        logger.info(f"Triggering {event_type} on {target_element} from {element_id}")
        # In a real implementation, this would trigger events on other elements

    async def _execute_log_action(self, action: BehaviorAction, element_id: str, event_data: Dict[str, Any]):
        """Execute a logging action."""
        message = action.parameters.get('message', f'Event on {element_id}')
        level = action.parameters.get('level', 'info')

        if level == 'debug':
            logger.debug(message)
        elif level == 'info':
            logger.info(message)
        elif level == 'warning':
            logger.warning(message)
        elif level == 'error':
            logger.error(message)

    async def _execute_default_action(self, trigger: BehaviorTrigger, element_id: str, event_data: Dict[str, Any]):
        """Execute default action for unknown action types."""
        logger.info(f"Executing default action '{trigger.action}' for {element_id}")

    def _handle_click(self, element_id: str, event_data: Dict[str, Any]):
        """Handle click events."""
        logger.info(f"Click event on {element_id}")
        return asyncio.create_task(self.handle_event(element_id, 'click', event_data)
    def _handle_hover(self, element_id: str, event_data: Dict[str, Any]):
        """Handle hover events."""
        logger.info(f"Hover event on {element_id}")
        return asyncio.create_task(self.handle_event(element_id, 'hover', event_data)
    def _handle_drag(self, element_id: str, event_data: Dict[str, Any]):
        """Handle drag events."""
        logger.info(f"Drag event on {element_id}")
        return asyncio.create_task(self.handle_event(element_id, 'drag', event_data)
    def _handle_time(self, element_id: str, event_data: Dict[str, Any]):
        """Handle time-based events."""
        logger.info(f"Time event on {element_id}")
        return asyncio.create_task(self.handle_event(element_id, 'time', event_data)
    def _handle_condition(self, element_id: str, event_data: Dict[str, Any]):
        """Handle condition-based events."""
        logger.info(f"Condition event on {element_id}")
        return asyncio.create_task(self.handle_event(element_id, 'condition', event_data)
    def _handle_external(self, element_id: str, event_data: Dict[str, Any]):
        """Handle external events."""
        logger.info(f"External event on {element_id}")
        return asyncio.create_task(self.handle_event(element_id, 'external', event_data)
    def start(self):
        """Start the behavior engine."""
        self.running = True
        logger.info("SVGX Behavior Engine started")

    def stop(self):
        """Stop the behavior engine."""
        self.running = False
        logger.info("SVGX Behavior Engine stopped")

    def get_element_triggers(self, element_id: str) -> List[BehaviorTrigger]:
        """Get triggers for a specific element."""
        return self.triggers.get(element_id, [])

    def get_registered_actions(self) -> List[str]:
        """Get list of registered action IDs."""
        return list(self.actions.keys()
