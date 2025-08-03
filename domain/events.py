"""
Domain Events - Event-Driven Architecture Implementation

This module contains domain events that represent significant occurrences
within the domain. Domain events are used to decouple components and
enable event-driven architecture patterns.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
import uuid


class EventType(Enum):
    """Domain event types enumeration."""
    BUILDING_CREATED = "building_created"
    BUILDING_UPDATED = "building_updated"
    BUILDING_DELETED = "building_deleted"
    BUILDING_STATUS_CHANGED = "building_status_changed"
    
    FLOOR_ADDED = "floor_added"
    FLOOR_UPDATED = "floor_updated"
    FLOOR_DELETED = "floor_deleted"
    FLOOR_STATUS_CHANGED = "floor_status_changed"
    
    ROOM_ADDED = "room_added"
    ROOM_UPDATED = "room_updated"
    ROOM_DELETED = "room_deleted"
    ROOM_STATUS_CHANGED = "room_status_changed"
    
    DEVICE_ADDED = "device_added"
    DEVICE_UPDATED = "device_updated"
    DEVICE_DELETED = "device_deleted"
    DEVICE_STATUS_CHANGED = "device_status_changed"
    
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_ROLE_CHANGED = "user_role_changed"
    
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_DELETED = "project_deleted"
    PROJECT_STATUS_CHANGED = "project_status_changed"


class DomainEvent(ABC):
    """Base class for all domain events."""
    
    def __init__(self, event_id: str = None, occurred_on: datetime = None, version: int = 1, metadata: Dict[str, Any] = None):
    """
    Perform __init__ operation

Args:
        event_id: Description of event_id
        occurred_on: Description of occurred_on
        version: Description of version
        metadata: Description of metadata

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        self.event_id = event_id or str(uuid.uuid4())
        self.occurred_on = occurred_on or datetime.utcnow()
        self.version = version
        self.metadata = metadata or {}
        self.event_type = None  # Will be set by subclasses
        
        # Validate event after initialization
        if not self.event_id:
            raise ValueError("Event ID is required")
        if not self.occurred_on:
            raise ValueError("Event occurrence time is required")
    
    @abstractmethod
    def get_aggregate_id(self) -> str:
        """Get the aggregate root ID for this event."""
        pass


class BuildingCreated(DomainEvent):
    """Event raised when a building is created."""
    
    event_type = EventType.BUILDING_CREATED
    
    def __init__(self, building_id: str, building_name: str, address: str, created_by: str, **kwargs):
        super().__init__(**kwargs)
        self.building_id = building_id
        self.building_name = building_name
        self.address = address
        self.created_by = created_by
        self.event_type = EventType.BUILDING_CREATED
    
    def get_aggregate_id(self) -> str:
        return self.building_id


class BuildingUpdated(DomainEvent):
    """Event raised when a building is updated."""
    
    event_type = EventType.BUILDING_UPDATED
    
    def __init__(self, building_id: str, updated_fields: List[str], updated_by: str, **kwargs):
        super().__init__(**kwargs)
        self.building_id = building_id
        self.updated_fields = updated_fields
        self.updated_by = updated_by
        self.event_type = EventType.BUILDING_UPDATED
    
    def get_aggregate_id(self) -> str:
        return self.building_id


class BuildingStatusChanged(DomainEvent):
    """Event raised when building status changes."""
    
    event_type = EventType.BUILDING_STATUS_CHANGED
    
    def __init__(self, building_id: str, old_status: str, new_status: str, changed_by: str, **kwargs):
        super().__init__(**kwargs)
        self.building_id = building_id
        self.old_status = old_status
        self.new_status = new_status
        self.changed_by = changed_by
        self.event_type = EventType.BUILDING_STATUS_CHANGED
    
    def get_aggregate_id(self) -> str:
        return self.building_id


class BuildingDeleted(DomainEvent):
    """Event raised when a building is deleted."""
    
    event_type = EventType.BUILDING_DELETED
    
    def __init__(self, building_id: str, building_name: str, deleted_by: str, **kwargs):
        super().__init__(**kwargs)
        self.building_id = building_id
        self.building_name = building_name
        self.deleted_by = deleted_by
        self.event_type = EventType.BUILDING_DELETED
    
    def get_aggregate_id(self) -> str:
        return self.building_id


class FloorCreated(DomainEvent):
    """Event raised when a floor is created."""
    
    event_type = EventType.FLOOR_ADDED  # Using same event type as FloorAdded
    
    def __init__(self, floor_id: str, building_id: str, floor_number: int, created_by: str, **kwargs):
        super().__init__(**kwargs)
        self.floor_id = floor_id
        self.building_id = building_id
        self.floor_number = floor_number
        self.created_by = created_by
        self.event_type = EventType.FLOOR_ADDED
    
    def get_aggregate_id(self) -> str:
        return self.floor_id


class FloorUpdated(DomainEvent):
    """Event raised when a floor is updated."""
    
    event_type = EventType.FLOOR_UPDATED
    
    def __init__(self, floor_id: str, updated_fields: List[str], updated_by: str, **kwargs):
        super().__init__(**kwargs)
        self.floor_id = floor_id
        self.updated_fields = updated_fields
        self.updated_by = updated_by
        self.event_type = EventType.FLOOR_UPDATED
    
    def get_aggregate_id(self) -> str:
        return self.floor_id


class FloorDeleted(DomainEvent):
    """Event raised when a floor is deleted."""
    
    event_type = EventType.FLOOR_DELETED
    
    def __init__(self, floor_id: str, floor_number: int, deleted_by: str, **kwargs):
        super().__init__(**kwargs)
        self.floor_id = floor_id
        self.floor_number = floor_number
        self.deleted_by = deleted_by
        self.event_type = EventType.FLOOR_DELETED
    
    def get_aggregate_id(self) -> str:
        return self.floor_id


class FloorAdded(DomainEvent):
    """Event raised when a floor is added to a building."""
    
    event_type = EventType.FLOOR_ADDED
    
    def __init__(self, building_id: str, floor_id: str, floor_number: int, added_by: str, **kwargs):
        super().__init__(**kwargs)
        self.building_id = building_id
        self.floor_id = floor_id
        self.floor_number = floor_number
        self.added_by = added_by
        self.event_type = EventType.FLOOR_ADDED
    
    def get_aggregate_id(self) -> str:
        return self.building_id


class FloorStatusChanged(DomainEvent):
    """Event raised when floor status changes."""
    
    event_type = EventType.FLOOR_STATUS_CHANGED
    
    def __init__(self, building_id: str, floor_id: str, old_status: str, new_status: str, changed_by: str, **kwargs):
        super().__init__(**kwargs)
        self.building_id = building_id
        self.floor_id = floor_id
        self.old_status = old_status
        self.new_status = new_status
        self.changed_by = changed_by
        self.event_type = EventType.FLOOR_STATUS_CHANGED
    
    def get_aggregate_id(self) -> str:
        return self.building_id


class RoomAdded(DomainEvent):
    """Event raised when a room is added to a floor."""
    
    event_type = EventType.ROOM_ADDED
    
    def __init__(self, building_id: str, floor_id: str, room_id: str, room_number: str, added_by: str, **kwargs):
        super().__init__(**kwargs)
        self.building_id = building_id
        self.floor_id = floor_id
        self.room_id = room_id
        self.room_number = room_number
        self.added_by = added_by
        self.event_type = EventType.ROOM_ADDED
    
    def get_aggregate_id(self) -> str:
        return self.building_id


class RoomCreated(DomainEvent):
    """Event raised when a room is created."""
    
    event_type = EventType.ROOM_ADDED  # Using same event type as RoomAdded
    
    def __init__(self, room_id: str, floor_id: str, room_number: str, room_type: str, created_by: str, **kwargs):
        super().__init__(**kwargs)
        self.room_id = room_id
        self.floor_id = floor_id
        self.room_number = room_number
        self.room_type = room_type
        self.created_by = created_by
        self.event_type = EventType.ROOM_ADDED
    
    def get_aggregate_id(self) -> str:
        return self.room_id


class RoomUpdated(DomainEvent):
    """Event raised when a room is updated."""
    
    event_type = EventType.ROOM_UPDATED
    
    def __init__(self, room_id: str, updated_fields: List[str], updated_by: str, **kwargs):
        super().__init__(**kwargs)
        self.room_id = room_id
        self.updated_fields = updated_fields
        self.updated_by = updated_by
        self.event_type = EventType.ROOM_UPDATED
    
    def get_aggregate_id(self) -> str:
        return self.room_id


class RoomDeleted(DomainEvent):
    """Event raised when a room is deleted."""
    
    event_type = EventType.ROOM_DELETED
    
    def __init__(self, room_id: str, room_number: str, deleted_by: str, **kwargs):
        super().__init__(**kwargs)
        self.room_id = room_id
        self.room_number = room_number
        self.deleted_by = deleted_by
        self.event_type = EventType.ROOM_DELETED
    
    def get_aggregate_id(self) -> str:
        return self.room_id


class RoomStatusChanged(DomainEvent):
    """Event raised when room status changes."""
    
    event_type = EventType.ROOM_STATUS_CHANGED
    
    def __init__(self, building_id: str, floor_id: str, room_id: str, old_status: str, new_status: str, changed_by: str, **kwargs):
        super().__init__(**kwargs)
        self.building_id = building_id
        self.floor_id = floor_id
        self.room_id = room_id
        self.old_status = old_status
        self.new_status = new_status
        self.changed_by = changed_by
        self.event_type = EventType.ROOM_STATUS_CHANGED
    
    def get_aggregate_id(self) -> str:
        return self.building_id


class DeviceAdded(DomainEvent):
    """Event raised when a device is added to a room."""
    
    event_type = EventType.DEVICE_ADDED
    
    def __init__(self, building_id: str, floor_id: str, room_id: str, device_id: str, device_type: str, added_by: str, **kwargs):
        super().__init__(**kwargs)
        self.building_id = building_id
        self.floor_id = floor_id
        self.room_id = room_id
        self.device_id = device_id
        self.device_type = device_type
        self.added_by = added_by
        self.event_type = EventType.DEVICE_ADDED
    
    def get_aggregate_id(self) -> str:
        return self.building_id


class DeviceCreated(DomainEvent):
    """Event raised when a device is created."""
    
    event_type = EventType.DEVICE_ADDED  # Using same event type as DeviceAdded
    
    def __init__(self, device_id: str, room_id: str, device_type: str, name: str, created_by: str, **kwargs):
        super().__init__(**kwargs)
        self.device_id = device_id
        self.room_id = room_id
        self.device_type = device_type
        self.name = name
        self.created_by = created_by
        self.event_type = EventType.DEVICE_ADDED
    
    def get_aggregate_id(self) -> str:
        return self.device_id


class DeviceUpdated(DomainEvent):
    """Event raised when a device is updated."""
    
    event_type = EventType.DEVICE_UPDATED
    
    def __init__(self, device_id: str, updated_fields: List[str], updated_by: str, **kwargs):
        super().__init__(**kwargs)
        self.device_id = device_id
        self.updated_fields = updated_fields
        self.updated_by = updated_by
        self.event_type = EventType.DEVICE_UPDATED
    
    def get_aggregate_id(self) -> str:
        return self.device_id


class DeviceDeleted(DomainEvent):
    """Event raised when a device is deleted."""
    
    event_type = EventType.DEVICE_DELETED
    
    def __init__(self, device_id: str, device_name: str, deleted_by: str, **kwargs):
        super().__init__(**kwargs)
        self.device_id = device_id
        self.device_name = device_name
        self.deleted_by = deleted_by
        self.event_type = EventType.DEVICE_DELETED
    
    def get_aggregate_id(self) -> str:
        return self.device_id


class DeviceStatusChanged(DomainEvent):
    """Event raised when device status changes."""
    
    event_type = EventType.DEVICE_STATUS_CHANGED
    
    def __init__(self, building_id: str, floor_id: str, room_id: str, device_id: str, old_status: str, new_status: str, changed_by: str, **kwargs):
        super().__init__(**kwargs)
        self.building_id = building_id
        self.floor_id = floor_id
        self.room_id = room_id
        self.device_id = device_id
        self.old_status = old_status
        self.new_status = new_status
        self.changed_by = changed_by
        self.event_type = EventType.DEVICE_STATUS_CHANGED
    
    def get_aggregate_id(self) -> str:
        return self.building_id


class UserCreated(DomainEvent):
    """Event raised when a user is created."""
    
    event_type = EventType.USER_CREATED
    
    def __init__(self, user_id: str, email: str, role: str, created_by: str, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.email = email
        self.role = role
        self.created_by = created_by
        self.event_type = EventType.USER_CREATED
    
    def get_aggregate_id(self) -> str:
        return self.user_id


class UserUpdated(DomainEvent):
    """Event raised when a user is updated."""
    
    event_type = EventType.USER_UPDATED
    
    def __init__(self, user_id: str, updated_fields: List[str], updated_by: str, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.updated_fields = updated_fields
        self.updated_by = updated_by
        self.event_type = EventType.USER_UPDATED
    
    def get_aggregate_id(self) -> str:
        return self.user_id


class UserDeleted(DomainEvent):
    """Event raised when a user is deleted."""
    
    event_type = EventType.USER_DELETED
    
    def __init__(self, user_id: str, email: str, deleted_by: str, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.email = email
        self.deleted_by = deleted_by
        self.event_type = EventType.USER_DELETED
    
    def get_aggregate_id(self) -> str:
        return self.user_id


class UserRoleChanged(DomainEvent):
    """Event raised when user role changes."""
    
    event_type = EventType.USER_ROLE_CHANGED
    
    def __init__(self, user_id: str, old_role: str, new_role: str, changed_by: str, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.old_role = old_role
        self.new_role = new_role
        self.changed_by = changed_by
        self.event_type = EventType.USER_ROLE_CHANGED
    
    def get_aggregate_id(self) -> str:
        return self.user_id


class ProjectCreated(DomainEvent):
    """Event raised when a project is created."""
    
    event_type = EventType.PROJECT_CREATED
    
    def __init__(self, project_id: str, project_name: str, building_id: str, created_by: str, **kwargs):
        super().__init__(**kwargs)
        self.project_id = project_id
        self.project_name = project_name
        self.building_id = building_id
        self.created_by = created_by
        self.event_type = EventType.PROJECT_CREATED
    
    def get_aggregate_id(self) -> str:
        return self.project_id


class ProjectUpdated(DomainEvent):
    """Event raised when a project is updated."""
    
    event_type = EventType.PROJECT_UPDATED
    
    def __init__(self, project_id: str, updated_fields: List[str], updated_by: str, **kwargs):
        super().__init__(**kwargs)
        self.project_id = project_id
        self.updated_fields = updated_fields
        self.updated_by = updated_by
        self.event_type = EventType.PROJECT_UPDATED
    
    def get_aggregate_id(self) -> str:
        return self.project_id


class ProjectDeleted(DomainEvent):
    """Event raised when a project is deleted."""
    
    event_type = EventType.PROJECT_DELETED
    
    def __init__(self, project_id: str, project_name: str, deleted_by: str, **kwargs):
        super().__init__(**kwargs)
        self.project_id = project_id
        self.project_name = project_name
        self.deleted_by = deleted_by
        self.event_type = EventType.PROJECT_DELETED
    
    def get_aggregate_id(self) -> str:
        return self.project_id


class ProjectStatusChanged(DomainEvent):
    """Event raised when project status changes."""
    
    event_type = EventType.PROJECT_STATUS_CHANGED
    
    def __init__(self, project_id: str, old_status: str, new_status: str, changed_by: str, **kwargs):
        super().__init__(**kwargs)
        self.project_id = project_id
        self.old_status = old_status
        self.new_status = new_status
        self.changed_by = changed_by
        self.event_type = EventType.PROJECT_STATUS_CHANGED
    
    def get_aggregate_id(self) -> str:
        return self.project_id


class EventHandler(ABC):
    """Abstract base class for event handlers."""
    
    @abstractmethod
    def handle(self, event: DomainEvent) -> None:
        """Handle a domain event."""
        pass


class EventBus:
    """
    Perform __init__ operation

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
    """Event bus for publishing and subscribing to domain events."""
    
    def __init__(self):
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._event_store: List[DomainEvent] = []
    
    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Subscribe a handler to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Unsubscribe a handler from an event type."""
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h != handler
            ]
    
    def publish(self, event: DomainEvent) -> None:
        """Publish a domain event to all subscribed handlers."""
        self._event_store.append(event)
        
        if event.event_type in self._handlers:
            for handler in self._handlers[event.event_type]:
                try:
                    handler.handle(event)
                except Exception as e:
                    # Log error but don't stop other handlers
                    print(f"Error handling event {event.event_type}: {e}")
    
    def get_events_by_aggregate_id(self, aggregate_id: str) -> List[DomainEvent]:
        """Get all events for a specific aggregate."""
        return [event for event in self._event_store if event.get_aggregate_id() == aggregate_id]
    
    def get_events_by_type(self, event_type: EventType) -> List[DomainEvent]:
        """Get all events of a specific type."""
        return [event for event in self._event_store if event.event_type == event_type]
    
    def clear_events(self) -> None:
        """Clear all stored events."""
        self._event_store.clear()


# Global event bus instance
event_bus = EventBus()


def publish_event(event: DomainEvent) -> None:
    """Publish a domain event to the global event bus."""
    event_bus.publish(event)


def subscribe_to_event(event_type: EventType, handler: EventHandler) -> None:
    """Subscribe to events on the global event bus."""
    event_bus.subscribe(event_type, handler)


def unsubscribe_from_event(event_type: EventType, handler: EventHandler) -> None:
    """Unsubscribe from events on the global event bus."""
    event_bus.unsubscribe(event_type, handler) 