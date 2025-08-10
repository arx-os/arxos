"""
Unified Building Entity - Core Domain Entity

This entity combines the best features from both the main domain
and SVGX domain building entities, eliminating duplication and
providing a single source of truth for building operations.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from ..value_objects import (
    BuildingId, Address, Coordinates, Dimensions, BuildingStatus
)
from ..events import (
    BuildingCreated, BuildingUpdated, BuildingStatusChanged
)
from domain.exceptions import InvalidBuildingError, InvalidStatusTransitionError

@dataclass
class Building:
    """
    Unified building entity representing a physical building in the domain.

    This entity combines the best features from both domain models:
    - Main domain: Rich business logic, status management, relationships
    - SVGX domain: Precision dimensions, metadata handling, validation

    Attributes:
        id: Unique building identifier
        name: Building name
        address: Building address with coordinates
        status: Current building status
        dimensions: Building dimensions (optional for planning phase)
        description: Building description
        created_at: Creation timestamp
        updated_at: Last update timestamp
        created_by: User who created the building
        metadata: Additional building metadata
        floors: List of floors in the building
        projects: List of projects associated with the building
    """

    id: BuildingId
    name: str
    address: Address
    status: BuildingStatus = BuildingStatus.PLANNED
    dimensions: Optional[Dimensions] = None
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Relationships
    floors: List['Floor'] = field(default_factory=list)
    projects: List['Project'] = field(default_factory=list)

    # Domain events
    _domain_events: List = field(default_factory=list, init=False)

    def __post_init__(self):
        """Validate building data after initialization."""
        self._validate_building_data()
        self._add_domain_event(BuildingCreated(
            building_id=str(self.id),
            building_name=self.name,
            address=str(self.address),
            created_by=self.created_by or "system"
        ))

    def _validate_building_data(self):
        """Validate building data according to business rules."""
        if not self.name or len(self.name.strip()) == 0:
            raise InvalidBuildingError("Building name cannot be empty")

        if not self.address:
            raise InvalidBuildingError("Building address is required")

        if not self.address.is_valid():
            raise InvalidBuildingError("Building must have a valid address")

    @property
    def full_name(self) -> str:
        """Get the full building name with address."""
        return f"{self.name} - {self.address.full_address}"

    @property
    def area(self) -> Optional[float]:
        """Calculate building area in square meters."""
        if self.dimensions:
            return self.dimensions.area
        return None

    @property
    def volume(self) -> Optional[float]:
        """Calculate building volume in cubic meters."""
        if self.dimensions:
            return self.dimensions.volume
        return None

    @property
    def floor_count(self) -> int:
        """Get the number of floors in the building."""
        return len(self.floors)

    @property
    def room_count(self) -> int:
        """Get the total number of rooms in the building."""
        return sum(len(floor.rooms) for floor in self.floors)

    @property
    def device_count(self) -> int:
        """Get the total number of devices in the building."""
        return sum(len(room.devices) for floor in self.floors for room in floor.rooms)

    def update_name(self, new_name: str, updated_by: str) -> None:
        """Update building name."""
        if not new_name or len(new_name.strip()) == 0:
            raise InvalidBuildingError("Building name cannot be empty")

        old_name = self.name
        self.name = new_name.strip()
        self.updated_at = datetime.utcnow()

        self._add_domain_event(BuildingUpdated(
            building_id=str(self.id),
            updated_fields=["name"],
            updated_by=updated_by
        ))

    def update_status(self, new_status: BuildingStatus, updated_by: str) -> None:
        """Update building status."""
        if new_status == self.status:
            return

        # Validate status transition
        self._validate_status_transition(self.status, new_status)

        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.utcnow()

        self._add_domain_event(BuildingStatusChanged(
            building_id=str(self.id),
            old_status=old_status.value,
            new_status=new_status.value,
            changed_by=updated_by
        ))

    def update_dimensions(self, new_dimensions: Dimensions, updated_by: str) -> None:
        """Update building dimensions."""
        if not new_dimensions:
            raise InvalidBuildingError("Building dimensions are required")

        old_dimensions = self.dimensions
        self.dimensions = new_dimensions
        self.updated_at = datetime.utcnow()

        self._add_domain_event(BuildingUpdated(
            building_id=str(self.id),
            updated_fields=["dimensions"],
            updated_by=updated_by
        ))

    def add_metadata(self, key: str, value: Any, updated_by: str) -> None:
        """Add metadata to the building."""
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()

        self._add_domain_event(BuildingUpdated(
            building_id=str(self.id),
            updated_fields=["metadata"],
            updated_by=updated_by
        ))

    def remove_metadata(self, key: str, updated_by: str) -> None:
        """Remove metadata from the building."""
        if key in self.metadata:
            self.metadata.pop(key)
            self.updated_at = datetime.utcnow()

            self._add_domain_event(BuildingUpdated(
                building_id=str(self.id),
                updated_fields=["metadata"],
                updated_by=updated_by
            ))

    def _validate_status_transition(self, current_status: BuildingStatus, new_status: BuildingStatus) -> None:
        """Validate status transition according to business rules."""
        valid_transitions = {
            BuildingStatus.PLANNED: [BuildingStatus.UNDER_CONSTRUCTION],
            BuildingStatus.UNDER_CONSTRUCTION: [BuildingStatus.COMPLETED, BuildingStatus.MAINTENANCE],
            BuildingStatus.COMPLETED: [BuildingStatus.OPERATIONAL, BuildingStatus.MAINTENANCE],
            BuildingStatus.OPERATIONAL: [BuildingStatus.MAINTENANCE, BuildingStatus.DECOMMISSIONED],
            BuildingStatus.MAINTENANCE: [BuildingStatus.OPERATIONAL, BuildingStatus.DECOMMISSIONED],
            BuildingStatus.DECOMMISSIONED: []  # Terminal state
        }

        if new_status not in valid_transitions.get(current_status, []):
            raise InvalidStatusTransitionError(
                f"Invalid status transition from {current_status.value} to {new_status.value}"
            )

    def is_valid(self) -> bool:
        """Check if the building entity is valid."""
        try:
            if not self.name or len(self.name.strip()) == 0:
                return False

            if not self.address:
                return False

            if not self.address.is_valid():
                return False

            return True
        except Exception:
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert building entity to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "address": self.address.to_dict(),
            "status": self.status.value,
            "dimensions": self.dimensions.to_dict() if self.dimensions else None,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "metadata": self.metadata,
            "area": self.area,
            "volume": self.volume,
            "floor_count": self.floor_count,
            "room_count": self.room_count,
            "device_count": self.device_count
        }

    def _add_domain_event(self, event) -> None:
        """Add domain event to the collection."""
        self._domain_events.append(event)

    def get_domain_events(self) -> List:
        """Get all domain events."""
        return self._domain_events.copy()

    def clear_domain_events(self) -> None:
        """Clear domain events after processing."""
        self._domain_events.clear()

    @classmethod
    def create(
        cls,
        name: str,
        address: Address,
        status: BuildingStatus = BuildingStatus.PLANNED,
        dimensions: Optional[Dimensions] = None,
        description: Optional[str] = None,
        created_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "Building":
        """Create a new building entity."""
        building_id = BuildingId.from_string(str(uuid.uuid4()))
        return cls(
            id=building_id,
            name=name,
            address=address,
            status=status,
            dimensions=dimensions,
            description=description,
            created_by=created_by,
            metadata=metadata or {}
        )
