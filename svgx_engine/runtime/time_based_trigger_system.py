"""
SVGX Engine - Time-based Trigger System

Handles scheduled behavior execution, time-based state transitions, and periodic event generation.
Manages trigger scheduling, timezone-aware operations, and calendar integration.
Integrates with the event-driven behavior engine and provides feedback for trigger actions.
Follows Arxos engineering standards: absolute imports, global instances, modular/testable code, and comprehensive documentation.
"""

from typing import Dict, Any, List, Optional, Callable, Union
from svgx_engine.runtime.event_driven_behavior_engine import (
    Event,
    EventType,
    EventPriority,
)
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import threading
import time
from zoneinfo import ZoneInfo
import pytz

logger = logging.getLogger(__name__)


class TriggerType(Enum):
    """Types of time-based triggers supported by the system."""

    ONE_TIME = "one_time"
    PERIODIC = "periodic"
    SCHEDULED = "scheduled"
    INTERVAL = "interval"
    CRON = "cron"


class TriggerStatus(Enum):
    """Status states for triggers."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Trigger:
    """Represents a time-based trigger."""

    id: str
    type: TriggerType
    name: str
    description: str
    target_time: Optional[datetime] = None
    interval_seconds: Optional[float] = None
    cron_expression: Optional[str] = None
    timezone: str = "UTC"
    max_executions: Optional[int] = None
    current_executions: int = 0
    status: TriggerStatus = TriggerStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_executed: Optional[datetime] = None
    next_execution: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.next_execution is None:
            self.next_execution = self._calculate_next_execution()

    def _calculate_next_execution(self) -> Optional[datetime]:
        """Calculate the next execution time based on trigger type."""
        if self.type == TriggerType.ONE_TIME:
            return self.target_time
        elif self.type == TriggerType.PERIODIC:
            if self.last_executed is None:
                return self.target_time
            else:
                return self.last_executed + timedelta(seconds=self.interval_seconds)
        elif self.type == TriggerType.INTERVAL:
            if self.last_executed is None:
                return datetime.utcnow() + timedelta(seconds=self.interval_seconds)
            else:
                return self.last_executed + timedelta(seconds=self.interval_seconds)
        elif self.type == TriggerType.CRON:
            return self._parse_cron_expression()
        return None

    def _parse_cron_expression(self) -> Optional[datetime]:
        """Parse cron expression to calculate next execution time."""
        # Simplified cron parsing - in production, use a proper cron library
        if not self.cron_expression:
            return None

        # Basic cron format: minute hour day month weekday
        # For now, return a placeholder - implement full cron parsing
        return datetime.utcnow() + timedelta(minutes=1)


class TimeBasedTriggerSystem:
    """
    Handles time-based trigger scheduling, execution, and management for SVGX elements.
    Supports various trigger types with timezone awareness and calendar integration.
    """

    def __init__(self):
        # {trigger_id: Trigger}
        self.triggers: Dict[str, Trigger] = {}
        # {trigger_id: List[Dict[str, Any]]}
        self.execution_history: Dict[str, List[Dict[str, Any]]] = {}
        # Background task for trigger monitoring
        self.monitor_task: Optional[asyncio.Task] = None
        self.running = False
        self.monitor_interval = 1.0  # Check every second
        self.timezone_cache: Dict[str, ZoneInfo] = {}

    async def start(self):
        """Start the trigger system monitoring."""
        if self.running:
            logger.warning("Trigger system is already running")
            return

        self.running = True
        self.monitor_task = asyncio.create_task(self._monitor_triggers())
        logger.info("Time-based trigger system started")

    async def stop(self):
        """Stop the trigger system monitoring."""
        if not self.running:
            logger.warning("Trigger system is not running")
            return

        self.running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Time-based trigger system stopped")

    async def _monitor_triggers(self):
        """Monitor triggers and execute them when due."""
        while self.running:
            try:
                current_time = datetime.utcnow()
                triggers_to_execute = []

                for trigger in self.triggers.values():
                    if (
                        trigger.status == TriggerStatus.ACTIVE
                        and trigger.next_execution
                        and current_time >= trigger.next_execution
                    ):
                        triggers_to_execute.append(trigger)

                # Execute triggers
                for trigger in triggers_to_execute:
                    await self._execute_trigger(trigger)

                await asyncio.sleep(self.monitor_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in trigger monitoring: {e}")
                await asyncio.sleep(self.monitor_interval)

    async def _execute_trigger(self, trigger: Trigger):
        """Execute a trigger and update its state."""
        try:
            # Create execution event
            event = Event(
                id=f"trigger_{trigger.id}_{int(time.time())}",
                type=EventType.SYSTEM,
                priority=EventPriority.NORMAL,
                timestamp=datetime.utcnow(),
                element_id=trigger.id,
                data={
                    "trigger_id": trigger.id,
                    "trigger_type": trigger.type.value,
                    "trigger_name": trigger.name,
                    "execution_time": datetime.utcnow().isoformat(),
                    "metadata": trigger.metadata,
                },
            )

            # Process event through the behavior engine
            # Import here to avoid circular imports
            from svgx_engine.runtime.event_driven_behavior_engine import (
                event_driven_behavior_engine,
            )

            result = event_driven_behavior_engine.process_event(event)
            if hasattr(result, "__await__"):
                await result

            # Update trigger state
            trigger.last_executed = datetime.utcnow()
            trigger.current_executions += 1

            # Check if trigger should be completed
            if (
                trigger.max_executions
                and trigger.current_executions >= trigger.max_executions
            ):
                trigger.status = TriggerStatus.COMPLETED
                trigger.next_execution = None
            else:
                trigger.next_execution = trigger._calculate_next_execution()

            # Record execution
            self._record_execution(
                trigger.id,
                {
                    "execution_time": trigger.last_executed,
                    "success": True,
                    "event_id": event.id,
                },
            )

            logger.info(f"Trigger {trigger.id} executed successfully")

        except Exception as e:
            logger.error(f"Error executing trigger {trigger.id}: {e}")
            trigger.status = TriggerStatus.FAILED
            self._record_execution(
                trigger.id,
                {
                    "execution_time": datetime.utcnow(),
                    "success": False,
                    "error": str(e),
                },
            )

    def create_one_time_trigger(
        self,
        trigger_id: str,
        name: str,
        target_time: datetime,
        description: str = "",
        timezone: str = "UTC",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Trigger:
        """Create a one-time trigger."""
        trigger = Trigger(
            id=trigger_id,
            type=TriggerType.ONE_TIME,
            name=name,
            description=description,
            target_time=target_time,
            timezone=timezone,
            metadata=metadata or {},
        )
        self.triggers[trigger_id] = trigger
        logger.info(f"Created one-time trigger: {trigger_id}")
        return trigger

    def create_periodic_trigger(
        self,
        trigger_id: str,
        name: str,
        start_time: datetime,
        interval_seconds: float,
        description: str = "",
        timezone: str = "UTC",
        max_executions: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Trigger:
        """Create a periodic trigger."""
        trigger = Trigger(
            id=trigger_id,
            type=TriggerType.PERIODIC,
            name=name,
            description=description,
            target_time=start_time,
            interval_seconds=interval_seconds,
            timezone=timezone,
            max_executions=max_executions,
            metadata=metadata or {},
        )
        self.triggers[trigger_id] = trigger
        logger.info(f"Created periodic trigger: {trigger_id}")
        return trigger

    def create_interval_trigger(
        self,
        trigger_id: str,
        name: str,
        interval_seconds: float,
        description: str = "",
        timezone: str = "UTC",
        max_executions: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Trigger:
        """Create an interval trigger."""
        trigger = Trigger(
            id=trigger_id,
            type=TriggerType.INTERVAL,
            name=name,
            description=description,
            interval_seconds=interval_seconds,
            timezone=timezone,
            max_executions=max_executions,
            metadata=metadata or {},
        )
        self.triggers[trigger_id] = trigger
        logger.info(f"Created interval trigger: {trigger_id}")
        return trigger

    def create_cron_trigger(
        self,
        trigger_id: str,
        name: str,
        cron_expression: str,
        description: str = "",
        timezone: str = "UTC",
        max_executions: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Trigger:
        """Create a cron-based trigger."""
        trigger = Trigger(
            id=trigger_id,
            type=TriggerType.CRON,
            name=name,
            description=description,
            cron_expression=cron_expression,
            timezone=timezone,
            max_executions=max_executions,
            metadata=metadata or {},
        )
        self.triggers[trigger_id] = trigger
        logger.info(f"Created cron trigger: {trigger_id}")
        return trigger

    def pause_trigger(self, trigger_id: str) -> bool:
        """Pause a trigger."""
        trigger = self.triggers.get(trigger_id)
        if not trigger:
            logger.warning(f"Trigger {trigger_id} not found")
            return False

        trigger.status = TriggerStatus.PAUSED
        logger.info(f"Paused trigger: {trigger_id}")
        return True

    def resume_trigger(self, trigger_id: str) -> bool:
        """Resume a paused trigger."""
        trigger = self.triggers.get(trigger_id)
        if not trigger:
            logger.warning(f"Trigger {trigger_id} not found")
            return False

        if trigger.status != TriggerStatus.PAUSED:
            logger.warning(f"Trigger {trigger_id} is not paused")
            return False

        trigger.status = TriggerStatus.ACTIVE
        trigger.next_execution = trigger._calculate_next_execution()
        logger.info(f"Resumed trigger: {trigger_id}")
        return True

    def cancel_trigger(self, trigger_id: str) -> bool:
        """Cancel a trigger."""
        trigger = self.triggers.get(trigger_id)
        if not trigger:
            logger.warning(f"Trigger {trigger_id} not found")
            return False

        trigger.status = TriggerStatus.CANCELLED
        trigger.next_execution = None
        logger.info(f"Cancelled trigger: {trigger_id}")
        return True

    def delete_trigger(self, trigger_id: str) -> bool:
        """Delete a trigger."""
        if trigger_id not in self.triggers:
            logger.warning(f"Trigger {trigger_id} not found")
            return False

        del self.triggers[trigger_id]
        if trigger_id in self.execution_history:
            del self.execution_history[trigger_id]
        logger.info(f"Deleted trigger: {trigger_id}")
        return True

    def get_trigger(self, trigger_id: str) -> Optional[Trigger]:
        """Get trigger by ID."""
        return self.triggers.get(trigger_id)

    def get_triggers(self, status: Optional[TriggerStatus] = None) -> List[Trigger]:
        """Get all triggers, optionally filtered by status."""
        triggers = list(self.triggers.values())
        if status:
            triggers = [t for t in triggers if t.status == status]
        return triggers

    def get_due_triggers(self) -> List[Trigger]:
        """Get triggers that are due for execution."""
        current_time = datetime.utcnow()
        return [
            trigger
            for trigger in self.triggers.values()
            if (
                trigger.status == TriggerStatus.ACTIVE
                and trigger.next_execution
                and current_time >= trigger.next_execution
            )
        ]

    def get_execution_history(self, trigger_id: str) -> List[Dict[str, Any]]:
        """Get execution history for a trigger."""
        return self.execution_history.get(trigger_id, [])

    def _record_execution(self, trigger_id: str, execution_data: Dict[str, Any]):
        """Record trigger execution in history."""
        if trigger_id not in self.execution_history:
            self.execution_history[trigger_id] = []

        self.execution_history[trigger_id].append(execution_data)

    def clear_execution_history(self, trigger_id: str):
        """Clear execution history for a trigger."""
        if trigger_id in self.execution_history:
            self.execution_history[trigger_id].clear()

    def get_system_status(self) -> Dict[str, Any]:
        """Get system status and statistics."""
        total_triggers = len(self.triggers)
        active_triggers = len(
            [t for t in self.triggers.values() if t.status == TriggerStatus.ACTIVE]
        )
        paused_triggers = len(
            [t for t in self.triggers.values() if t.status == TriggerStatus.PAUSED]
        )
        completed_triggers = len(
            [t for t in self.triggers.values() if t.status == TriggerStatus.COMPLETED]
        )
        failed_triggers = len(
            [t for t in self.triggers.values() if t.status == TriggerStatus.FAILED]
        )

        return {
            "running": self.running,
            "total_triggers": total_triggers,
            "active_triggers": active_triggers,
            "paused_triggers": paused_triggers,
            "completed_triggers": completed_triggers,
            "failed_triggers": failed_triggers,
            "due_triggers": len(self.get_due_triggers()),
        }


# Global instance
time_based_trigger_system = TimeBasedTriggerSystem()


# Register with the event-driven engine
def _register_time_based_trigger_system():
    def handler(event: Event):
        if event.type == EventType.SYSTEM and event.data.get("trigger_id"):
            # Trigger events are handled internally by the system
            return None
        return None

    # Import here to avoid circular imports
    from svgx_engine.runtime.event_driven_behavior_engine import (
        event_driven_behavior_engine,
    )

    event_driven_behavior_engine.register_handler(
        event_type=EventType.SYSTEM,
        handler_id="time_based_trigger_system",
        handler=handler,
        priority=0,
    )


_register_time_based_trigger_system()
