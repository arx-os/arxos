"""
Building Aggregate - Domain Aggregate for Building Operations
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field
import uuid

from svgx_engine.domain.entities.building import Building
from svgx_engine.domain.value_objects.address import Address
from svgx_engine.domain.value_objects.coordinates import Coordinates
from svgx_engine.domain.value_objects.dimensions import Dimensions
from svgx_engine.domain.value_objects.money import Money
from svgx_engine.domain.value_objects.status import Status, StatusType
from svgx_engine.domain.value_objects.identifier import Identifier
from svgx_engine.domain.events.building_events import (
    BuildingCreatedEvent,
    BuildingUpdatedEvent,
    BuildingDeletedEvent,
    BuildingStatusChangedEvent,
    BuildingLocationChangedEvent,
    BuildingCostUpdatedEvent,
    building_event_publisher
)

@dataclass
class BuildingAggregate:
    """
    Building aggregate that encapsulates the building entity and related business logic.

    This aggregate serves as the main entry point for building operations,
    ensuring business rules are enforced and domain events are raised.
    """

    id: Identifier
    building: Building
    status: Status
    cost: Money
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate aggregate after initialization."""
        if not self.building:
            raise ValueError("Building entity is required")

        if not self.status:
            raise ValueError("Building status is required")

        if not self.cost:
            raise ValueError("Building cost is required")

    @property
def name(self) -> str:
        """Get building name."""
        return self.building.name

    @property
def address(self) -> Address:
        """Get building address."""
        return self.building.address

    @property
def dimensions(self) -> Dimensions:
        """Get building dimensions."""
        return self.building.dimensions

    @property
def area(self) -> float:
        """Get building area in square meters."""
        return self.building.area

    @property
def volume(self) -> float:
        """Get building volume in cubic meters."""
        return self.building.volume

    def update_name(self, new_name: str, updated_by: str) -> None:
        """
        Update building name.

        Args:
            new_name: New building name
            updated_by: User who made the update
        """
        old_name = self.building.name
        self.building.update_name(new_name)
        self.updated_at = datetime.utcnow()

        # Raise domain event
        event = BuildingUpdatedEvent(
            building_id=str(self.id),
            updated_fields={"name": new_name},
            updated_by=updated_by,
            previous_values={"name": old_name}
        )
        building_event_publisher.publish_building_updated(event)

    def update_address(self, new_address: Address, updated_by: str) -> None:
        """
        Update building address.

        Args:
            new_address: New building address
            updated_by: User who made the update
        """
        old_address = self.building.address
        self.building.update_address(new_address)
        self.updated_at = datetime.utcnow()

        # Raise domain event
        event = BuildingLocationChangedEvent(
            building_id=str(self.id),
            old_coordinates=old_address.coordinates if old_address.coordinates else Coordinates(0, 0),
            new_coordinates=new_address.coordinates if new_address.coordinates else Coordinates(0, 0),
            changed_by=updated_by
        )
        building_event_publisher.publish_building_location_changed(event)

    def update_dimensions(self, new_dimensions: Dimensions, updated_by: str) -> None:
        """
        Update building dimensions.

        Args:
            new_dimensions: New building dimensions
            updated_by: User who made the update
        """
        old_dimensions = self.building.dimensions
        self.building.update_dimensions(new_dimensions)
        self.updated_at = datetime.utcnow()

        # Raise domain event
        event = BuildingUpdatedEvent(
            building_id=str(self.id),
            updated_fields={"dimensions": new_dimensions},
            updated_by=updated_by,
            previous_values={"dimensions": old_dimensions}
        )
        building_event_publisher.publish_building_updated(event)

    def update_status(self, new_status: Status, updated_by: str, reason: Optional[str] = None) -> None:
        """
        Update building status.

        Args:
            new_status: New building status
            updated_by: User who made the update
            reason: Optional reason for status change
        """
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.utcnow()

        # Raise domain event
        event = BuildingStatusChangedEvent(
            building_id=str(self.id),
            old_status=old_status,
            new_status=new_status,
            changed_by=updated_by,
            reason=reason
        )
        building_event_publisher.publish_building_status_changed(event)

    def update_cost(self, new_cost: Money, updated_by: str, reason: Optional[str] = None) -> None:
        """
        Update building cost.

        Args:
            new_cost: New building cost
            updated_by: User who made the update
            reason: Optional reason for cost change
        """
        old_cost = self.cost
        self.cost = new_cost
        self.updated_at = datetime.utcnow()

        # Raise domain event
        event = BuildingCostUpdatedEvent(
            building_id=str(self.id),
            old_cost=old_cost.amount,
            new_cost=new_cost.amount,
            currency=new_cost.currency,
            updated_by=updated_by,
            reason=reason
        )
        building_event_publisher.publish_building_cost_updated(event)

    def add_metadata(self, key: str, value: Any, updated_by: str) -> None:
        """
        Add metadata to the building.

        Args:
            key: Metadata key
            value: Metadata value
            updated_by: User who made the update
        """
        self.building.add_metadata(key, value)
        self.updated_at = datetime.utcnow()

        # Raise domain event
        event = BuildingUpdatedEvent(
            building_id=str(self.id),
            updated_fields={"metadata": {key: value}},
            updated_by=updated_by
        )
        building_event_publisher.publish_building_updated(event)

    def remove_metadata(self, key: str, updated_by: str) -> None:
        """
        Remove metadata from the building.

        Args:
            key: Metadata key to remove
            updated_by: User who made the update
        """
        self.building.remove_metadata(key)
        self.updated_at = datetime.utcnow()

        # Raise domain event
        event = BuildingUpdatedEvent(
            building_id=str(self.id),
            updated_fields={"metadata": {key: None}},
            updated_by=updated_by
        )
        building_event_publisher.publish_building_updated(event)

    def delete(self, deleted_by: str, reason: Optional[str] = None) -> None:
        """
        Mark building as deleted.

        Args:
            deleted_by: User who deleted the building
            reason: Optional reason for deletion
        """
        # Change status to deleted
        deleted_status = Status(StatusType.DELETED)
        self.update_status(deleted_status, deleted_by, reason)

        # Raise deletion event
        event = BuildingDeletedEvent(
            building_id=str(self.id),
            deleted_by=deleted_by,
            deletion_reason=reason
        )
        building_event_publisher.publish_building_deleted(event)

    def is_active(self) -> bool:
        """Check if building is active."""
        return self.status.value == StatusType.ACTIVE.value

    def is_deleted(self) -> bool:
        """Check if building is deleted."""
        return self.status.value == StatusType.DELETED.value

    def is_under_construction(self) -> bool:
        """Check if building is under construction."""
        return self.status.value == StatusType.UNDER_CONSTRUCTION.value

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert aggregate to dictionary.

        Returns:
            Dictionary representation of the building aggregate
        """
        return {
            "id": str(self.id),
            "building": self.building.to_dict(),
            "status": self.status.value,
            "cost": {
                "amount": self.cost.amount,
                "currency": self.cost.currency
            },
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "area": self.area,
            "volume": self.volume
        }

    @classmethod
def create(
        cls,
        name: str,
        address: Address,
        coordinates: Coordinates,
        dimensions: Dimensions,
        status: Status,
        cost: Money,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "BuildingAggregate":
        """
        Create a new building aggregate.

        Args:
            name: Building name
            address: Building address
            coordinates: Building coordinates
            dimensions: Building dimensions
            status: Building status
            cost: Building cost
            metadata: Optional metadata

        Returns:
            New building aggregate
        """
        # Create building entity
        building = Building.create(
            name=name,
            address=address,
            dimensions=dimensions,
            metadata=metadata or {}
        )

        # Create aggregate
        aggregate_id = Identifier(str(uuid.uuid4()))
        aggregate = cls(
            id=aggregate_id,
            building=building,
            status=status,
            cost=cost,
            metadata=metadata or {}
        )

        # Raise creation event
        event = BuildingCreatedEvent(
            building_id=str(aggregate_id),
            name=name,
            address=address,
            coordinates=coordinates,
            status=status,
            created_by="system"
        )
        building_event_publisher.publish_building_created(event)

        return aggregate
