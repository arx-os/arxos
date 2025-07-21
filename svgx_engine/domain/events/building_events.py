"""
Building Domain Events

Domain events related to building operations.
These events represent something that happened in the building domain
and are used for communication between aggregates and external systems.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from ..value_objects.identifier import Identifier
from ..value_objects.address import Address
from ..value_objects.coordinates import Coordinates
from ..value_objects.status import Status
from . import DomainEvent


@dataclass
class BuildingCreatedEvent(DomainEvent):
    """
    Domain event raised when a building is created.
    
    Attributes:
        building_id: ID of the created building
        name: Building name
        address: Building address
        coordinates: Building coordinates
        created_at: Event timestamp
    """
    
    building_id: Identifier
    name: str
    address: Address
    coordinates: Coordinates
    created_at: datetime
    
    @property
    def event_type(self) -> str:
        """Get event type."""
        return "building.created"
    
    @property
    def event_version(self) -> str:
        """Get event version."""
        return "1.0"
    
    def to_dict(self) -> dict:
        """Convert event to dictionary."""
        return {
            "event_type": self.event_type,
            "event_version": self.event_version,
            "building_id": str(self.building_id),
            "name": self.name,
            "address": self.address.full_address,
            "coordinates": {
                "latitude": self.coordinates.latitude,
                "longitude": self.coordinates.longitude
            },
            "created_at": self.created_at.isoformat()
        }


@dataclass
class BuildingUpdatedEvent(DomainEvent):
    """
    Domain event raised when a building is updated.
    
    Attributes:
        building_id: ID of the updated building
        update_type: Type of update event
        data: Event data
        updated_at: Event timestamp
    """
    
    building_id: Identifier
    update_type: str
    data: dict
    updated_at: datetime
    
    @property
    def event_type(self) -> str:
        """Get event type."""
        return "building.updated"
    
    @property
    def event_version(self) -> str:
        """Get event version."""
        return "1.0"
    
    def to_dict(self) -> dict:
        """Convert event to dictionary."""
        return {
            "event_type": self.event_type,
            "event_version": self.event_version,
            "building_id": str(self.building_id),
            "update_type": self.update_type,
            "data": self.data,
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class BuildingStatusChangedEvent(DomainEvent):
    """
    Domain event raised when a building status changes.
    
    Attributes:
        building_id: ID of the building
        old_status: Previous status
        new_status: New status
        changed_at: Event timestamp
    """
    
    building_id: Identifier
    old_status: Status
    new_status: Status
    changed_at: datetime
    
    @property
    def event_type(self) -> str:
        """Get event type."""
        return "building.status_changed"
    
    @property
    def event_version(self) -> str:
        """Get event version."""
        return "1.0"
    
    def to_dict(self) -> dict:
        """Convert event to dictionary."""
        return {
            "event_type": self.event_type,
            "event_version": self.event_version,
            "building_id": str(self.building_id),
            "old_status": self.old_status.value,
            "new_status": self.new_status.value,
            "changed_at": self.changed_at.isoformat()
        }


@dataclass
class BuildingAddressChangedEvent(DomainEvent):
    """
    Domain event raised when a building address changes.
    
    Attributes:
        building_id: ID of the building
        old_address: Previous address
        new_address: New address
        changed_at: Event timestamp
    """
    
    building_id: Identifier
    old_address: Address
    new_address: Address
    changed_at: datetime
    
    @property
    def event_type(self) -> str:
        """Get event type."""
        return "building.address_changed"
    
    @property
    def event_version(self) -> str:
        """Get event version."""
        return "1.0"
    
    def to_dict(self) -> dict:
        """Convert event to dictionary."""
        return {
            "event_type": self.event_type,
            "event_version": self.event_version,
            "building_id": str(self.building_id),
            "old_address": self.old_address.full_address,
            "new_address": self.new_address.full_address,
            "changed_at": self.changed_at.isoformat()
        }


@dataclass
class BuildingDeletedEvent(DomainEvent):
    """
    Domain event raised when a building is deleted.
    
    Attributes:
        building_id: ID of the deleted building
        deleted_at: Event timestamp
    """
    
    building_id: Identifier
    deleted_at: datetime
    
    @property
    def event_type(self) -> str:
        """Get event type."""
        return "building.deleted"
    
    @property
    def event_version(self) -> str:
        """Get event version."""
        return "1.0"
    
    def to_dict(self) -> dict:
        """Convert event to dictionary."""
        return {
            "event_type": self.event_type,
            "event_version": self.event_version,
            "building_id": str(self.building_id),
            "deleted_at": self.deleted_at.isoformat()
        }


@dataclass
class BuildingArchivedEvent(DomainEvent):
    """
    Domain event raised when a building is archived.
    
    Attributes:
        building_id: ID of the archived building
        archived_at: Event timestamp
        reason: Optional reason for archiving
    """
    
    building_id: Identifier
    archived_at: datetime
    reason: Optional[str] = None
    
    @property
    def event_type(self) -> str:
        """Get event type."""
        return "building.archived"
    
    @property
    def event_version(self) -> str:
        """Get event version."""
        return "1.0"
    
    def to_dict(self) -> dict:
        """Convert event to dictionary."""
        return {
            "event_type": self.event_type,
            "event_version": self.event_version,
            "building_id": str(self.building_id),
            "archived_at": self.archived_at.isoformat(),
            "reason": self.reason
        } 