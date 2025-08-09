"""
Building Events - Domain Events for Building Operations
"""

from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
import uuid

from svgx_engine.domain.value_objects.identifier import Identifier
from svgx_engine.domain.value_objects.address import Address
from svgx_engine.domain.value_objects.coordinates import Coordinates
from svgx_engine.domain.value_objects.status import Status

@dataclass
class DomainEvent:
    """Base class for all domain events."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_on: datetime = field(default_factory=datetime.utcnow)
    event_type: str = field(init=False)

    def __post_init__(self):
        pass
    """
    Perform __post_init__ operation

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __post_init__(param)
        print(result)
    """
        self.event_type = self.__class__.__name__

@dataclass
class BuildingCreatedEvent(DomainEvent):
    """Event raised when a building is created."""
    building_id: str
    name: str
    address: Address
    coordinates: Coordinates
    status: Status
    created_by: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BuildingUpdatedEvent(DomainEvent):
    """Event raised when a building is updated."""
    building_id: str
    updated_fields: Dict[str, Any]
    updated_by: str
    previous_values: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BuildingDeletedEvent(DomainEvent):
    """Event raised when a building is deleted."""
    building_id: str
    deleted_by: str
    deletion_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BuildingStatusChangedEvent(DomainEvent):
    """Event raised when a building status changes."""
    building_id: str
    old_status: Status
    new_status: Status
    changed_by: str
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BuildingLocationChangedEvent(DomainEvent):
    """Event raised when a building location changes."""
    building_id: str
    old_coordinates: Coordinates
    new_coordinates: Coordinates
    changed_by: str
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BuildingCostUpdatedEvent(DomainEvent):
    """Event raised when a building cost is updated."""
    building_id: str
    old_cost: float
    new_cost: float
    currency: str
    updated_by: str
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class BuildingEventPublisher:
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
    """Event publisher for building domain events."""

    def __init__(self):
        self.subscribers: Dict[str, list] = {}

    def subscribe(self, event_type: str, subscriber):
        """Subscribe to building events."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(subscriber)

    def publish(self, event: DomainEvent):
        """Publish a building domain event."""
        event_type = event.event_type
        if event_type in self.subscribers:
            for subscriber in self.subscribers[event_type]:
                try:
                    subscriber(event)
                except Exception as e:
                    # Log error but don't stop other subscribers'
                    print(f"Error in event subscriber: {e}")

    def publish_building_created(self, event: BuildingCreatedEvent):
        """Publish building created event."""
        self.publish(event)

    def publish_building_updated(self, event: BuildingUpdatedEvent):
        """Publish building updated event."""
        self.publish(event)

    def publish_building_deleted(self, event: BuildingDeletedEvent):
        """Publish building deleted event."""
        self.publish(event)

    def publish_building_status_changed(self, event: BuildingStatusChangedEvent):
        """Publish building status changed event."""
        self.publish(event)

    def publish_building_location_changed(self, event: BuildingLocationChangedEvent):
        """Publish building location changed event."""
        self.publish(event)

    def publish_building_cost_updated(self, event: BuildingCostUpdatedEvent):
        """Publish building cost updated event."""
        self.publish(event)

# Global event publisher instance
building_event_publisher = BuildingEventPublisher()
