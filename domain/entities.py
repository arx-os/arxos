"""
Domain Entities - Core Business Objects

This module contains domain entities that represent the core business
objects with identity, lifecycle, and business logic. Entities are
the primary objects in the domain model and contain the business
rules and invariants.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from .value_objects import (
    BuildingId, FloorId, RoomId, DeviceId, UserId, ProjectId,
    Address, Coordinates, Dimensions, Email, PhoneNumber,
    BuildingStatus, FloorStatus, RoomStatus, DeviceStatus, UserRole, ProjectStatus
)
from .events import (
    BuildingCreated, BuildingUpdated, BuildingStatusChanged,
    FloorAdded, FloorUpdated, FloorStatusChanged,
    RoomAdded, RoomUpdated, RoomStatusChanged,
    DeviceAdded, DeviceUpdated, DeviceStatusChanged,
    UserCreated, UserUpdated, UserRoleChanged,
    ProjectCreated, ProjectUpdated, ProjectStatusChanged,
    publish_event
)
from .exceptions import (
    InvalidBuildingError, InvalidFloorError, InvalidRoomError, InvalidDeviceError,
    InvalidUserError, InvalidProjectError, DuplicateFloorError, DuplicateRoomError,
    DuplicateDeviceError, InvalidStatusTransitionError, raise_domain_exception
)


@dataclass
class Building:
    """Building entity with business logic and validation."""

    id: BuildingId
    name: str
    address: Address
    status: BuildingStatus = BuildingStatus.PLANNED
    coordinates: Optional[Coordinates] = None
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

    def add_floor(self, floor: 'Floor') -> None:
        """Add a floor to the building."""
        if floor in self.floors:
            raise DuplicateFloorError(f"Floor {floor.floor_number} already exists in building")

        self.floors.append(floor)
        self.updated_at = datetime.utcnow()

        self._add_domain_event(FloorAdded(
            building_id=str(self.id),
            floor_id=str(floor.id),
            floor_number=floor.floor_number,
            added_by=floor.created_by or "system"
        ))

    def remove_floor(self, floor_id: FloorId) -> None:
        """Remove a floor from the building."""
        floor = next((f for f in self.floors if f.id == floor_id), None)
        if not floor:
            raise_domain_exception(
                FloorNotFoundError, 'floor_not_found',
                floor_id=str(floor_id), building_id=str(self.id)
            )
        self.floors.remove(floor)
        self.updated_at = datetime.utcnow()

    def get_floor_by_number(self, floor_number: int) -> Optional['Floor']:
        """Get a floor by its number."""
        return next((f for f in self.floors if f.floor_number == floor_number), None)

    def _add_domain_event(self, event) -> None:
        """Add domain event to the collection."""
        self._domain_events.append(event)

    def get_domain_events(self) -> List:
        """Get all domain events."""
        return self._domain_events.copy()

    def clear_domain_events(self) -> None:
        """Clear domain events after processing."""
        self._domain_events.clear()


@dataclass
class Floor:
    """Floor entity with business logic and validation."""

    id: FloorId
    building_id: BuildingId
    floor_number: int
    name: str
    status: FloorStatus = FloorStatus.PLANNED
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Relationships
    rooms: List['Room'] = field(default_factory=list)

    # Domain events
    _domain_events: List = field(default_factory=list, init=False)

    def __post_init__(self):
        """Validate floor data after initialization."""
        self._validate_floor_data()

    def _validate_floor_data(self):
        """Validate floor data according to business rules."""
        if not self.name or len(self.name.strip()) == 0:
            raise InvalidFloorError("Floor name cannot be empty")

        if self.floor_number < 0:
            raise InvalidFloorError("Floor number must be non-negative")

    @property
    def full_name(self) -> str:
        """Get the full floor name."""
        return f"{self.name} (Floor {self.floor_number})"
    @property
    def room_count(self) -> int:
        """Get the number of rooms on this floor."""
        return len(self.rooms)

    @property
    def device_count(self) -> int:
        """Get the total number of devices on this floor."""
        return sum(len(room.devices) for room in self.rooms)

    def update_name(self, new_name: str, updated_by: str) -> None:
        """Update floor name."""
        if not new_name or len(new_name.strip()) == 0:
            raise InvalidFloorError("Floor name cannot be empty")

        self.name = new_name.strip()
        self.updated_at = datetime.utcnow()

        self._add_domain_event(FloorUpdated(
            building_id=str(self.building_id),
            floor_id=str(self.id),
            updated_fields=["name"],
            updated_by=updated_by
        ))

    def update_status(self, new_status: FloorStatus, updated_by: str) -> None:
        """Update floor status."""
        if new_status == self.status:
            return

        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.utcnow()

        self._add_domain_event(FloorStatusChanged(
            building_id=str(self.building_id),
            floor_id=str(self.id),
            old_status=old_status.value,
            new_status=new_status.value,
            changed_by=updated_by
        ))

    def add_room(self, room: 'Room') -> None:
        """Add a room to the floor."""
        if room in self.rooms:
            raise DuplicateRoomError(f"Room {room.room_number} already exists on floor")

        self.rooms.append(room)
        self.updated_at = datetime.utcnow()

        self._add_domain_event(RoomAdded(
            building_id=str(self.building_id),
            floor_id=str(self.id),
            room_id=str(room.id),
            room_number=room.room_number,
            added_by=room.created_by or "system"
        ))

    def remove_room(self, room_id: RoomId) -> None:
        """Remove a room from the floor."""
        room = next((r for r in self.rooms if r.id == room_id), None)
        if not room:
            raise_domain_exception(
                RoomNotFoundError, 'room_not_found',
                room_id=str(room_id), floor_id=str(self.id)
            )
        self.rooms.remove(room)
        self.updated_at = datetime.utcnow()

    def get_room_by_number(self, room_number: str) -> Optional['Room']:
        """Get a room by its number."""
        return next((r for r in self.rooms if r.room_number == room_number), None)

    def _add_domain_event(self, event) -> None:
        """Add domain event to the collection."""
        self._domain_events.append(event)

    def get_domain_events(self) -> List:
        """Get all domain events."""
        return self._domain_events.copy()

    def clear_domain_events(self) -> None:
        """Clear domain events after processing."""
        self._domain_events.clear()


@dataclass
class Room:
    """Room entity with business logic and validation."""

    id: RoomId
    floor_id: FloorId
    room_number: str
    name: str
    status: RoomStatus = RoomStatus.PLANNED
    room_type: str = "general"
    dimensions: Optional[Dimensions] = None
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Relationships
    devices: List['Device'] = field(default_factory=list)

    # Domain events
    _domain_events: List = field(default_factory=list, init=False)

    def __post_init__(self):
        """Validate room data after initialization."""
        self._validate_room_data()

    def _validate_room_data(self):
        """Validate room data according to business rules."""
        if not self.name or len(self.name.strip()) == 0:
            raise InvalidRoomError("Room name cannot be empty")

        if not self.room_number or len(self.room_number.strip()) == 0:
            raise InvalidRoomError("Room number cannot be empty")

    @property
    def full_name(self) -> str:
        """Get the full room name."""
        return f"{self.name} ({self.room_number})"
    @property
    def area(self) -> Optional[float]:
        """Calculate room area in square meters."""
        if self.dimensions:
            return self.dimensions.area
        return None

    @property
    def volume(self) -> Optional[float]:
        """Calculate room volume in cubic meters."""
        if self.dimensions:
            return self.dimensions.volume
        return None

    @property
    def device_count(self) -> int:
        """Get the number of devices in this room."""
        return len(self.devices)

    def update_name(self, new_name: str, updated_by: str) -> None:
        """Update room name."""
        if not new_name or len(new_name.strip()) == 0:
            raise InvalidRoomError("Room name cannot be empty")

        self.name = new_name.strip()
        self.updated_at = datetime.utcnow()

        self._add_domain_event(RoomUpdated(
            building_id="",  # Would need building_id from context import context
            floor_id=str(self.floor_id),
            room_id=str(self.id),
            updated_fields=["name"],
            updated_by=updated_by
        ))

    def update_status(self, new_status: RoomStatus, updated_by: str) -> None:
        """Update room status."""
        if new_status == self.status:
            return

        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.utcnow()

        self._add_domain_event(RoomStatusChanged(
            building_id="",  # Would need building_id from context import context
            floor_id=str(self.floor_id),
            room_id=str(self.id),
            old_status=old_status.value,
            new_status=new_status.value,
            changed_by=updated_by
        ))

    def add_device(self, device: 'Device') -> None:
        """Add a device to the room."""
        if device in self.devices:
            raise DuplicateDeviceError(f"Device {device.device_id} already exists in room")

        self.devices.append(device)
        self.updated_at = datetime.utcnow()

        self._add_domain_event(DeviceAdded(
            building_id="",  # Would need building_id from context import context
            floor_id=str(self.floor_id),
            room_id=str(self.id),
            device_id=str(device.id),
            device_type=device.device_type,
            added_by=device.created_by or "system"
        ))

    def remove_device(self, device_id: DeviceId) -> None:
        """Remove a device from the room."""
        device = next((d for d in self.devices if d.id == device_id), None)
        if not device:
            raise_domain_exception(
                DeviceNotFoundError, 'device_not_found',
                device_id=str(device_id), room_id=str(self.id)
            )
        self.devices.remove(device)
        self.updated_at = datetime.utcnow()

    def get_device_by_id(self, device_id: DeviceId) -> Optional['Device']:
        """Get a device by its ID."""
        return next((d for d in self.devices if d.id == device_id), None)

    def get_devices_by_type(self, device_type: str) -> List['Device']:
        """Get devices by type."""
        return [d for d in self.devices if d.device_type == device_type]

    def _add_domain_event(self, event) -> None:
        """Add domain event to the collection."""
        self._domain_events.append(event)

    def get_domain_events(self) -> List:
        """Get all domain events."""
        return self._domain_events.copy()

    def clear_domain_events(self) -> None:
        """Clear domain events after processing."""
        self._domain_events.clear()


@dataclass
class Device:
    """Device entity with business logic and validation."""

    id: DeviceId
    room_id: RoomId
    device_id: str  # External device identifier
    device_type: str
    name: str
    status: DeviceStatus = DeviceStatus.INSTALLED
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Domain events
    _domain_events: List = field(default_factory=list, init=False)

    def __post_init__(self):
        """Validate device data after initialization."""
        self._validate_device_data()

    def _validate_device_data(self):
        """Validate device data according to business rules."""
        if not self.name or len(self.name.strip()) == 0:
            raise InvalidDeviceError("Device name cannot be empty")

        if not self.device_id or len(self.device_id.strip()) == 0:
            raise InvalidDeviceError("Device ID cannot be empty")

        if not self.device_type or len(self.device_type.strip()) == 0:
            raise InvalidDeviceError("Device type cannot be empty")

    @property
    def full_name(self) -> str:
        """Get the full device name."""
        return f"{self.name} ({self.device_type})"
    def update_name(self, new_name: str, updated_by: str) -> None:
        """Update device name."""
        if not new_name or len(new_name.strip()) == 0:
            raise InvalidDeviceError("Device name cannot be empty")

        self.name = new_name.strip()
        self.updated_at = datetime.utcnow()

        self._add_domain_event(DeviceUpdated(
            building_id="",  # Would need building_id from context import context
            floor_id="",     # Would need floor_id from context import context
            room_id=str(self.room_id),
            device_id=str(self.id),
            updated_fields=["name"],
            updated_by=updated_by
        ))

    def update_status(self, new_status: DeviceStatus, updated_by: str) -> None:
        """Update device status."""
        if new_status == self.status:
            return

        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.utcnow()

        self._add_domain_event(DeviceStatusChanged(
            building_id="",  # Would need building_id from context import context
            floor_id="",     # Would need floor_id from context import context
            room_id=str(self.room_id),
            device_id=str(self.id),
            old_status=old_status.value,
            new_status=new_status.value,
            changed_by=updated_by
        ))

    def _add_domain_event(self, event) -> None:
        """Add domain event to the collection."""
        self._domain_events.append(event)

    def get_domain_events(self) -> List:
        """Get all domain events."""
        return self._domain_events.copy()

    def clear_domain_events(self) -> None:
        """Clear domain events after processing."""
        self._domain_events.clear()


@dataclass
class User:
    """User entity with business logic and validation."""

    id: UserId
    email: Email
    username: str
    role: UserRole = UserRole.VIEWER
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[PhoneNumber] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Domain events
    _domain_events: List = field(default_factory=list, init=False)

    def __post_init__(self):
        """Validate user data after initialization."""
        self._validate_user_data()
        self._add_domain_event(UserCreated(
            user_id=str(self.id),
            email=str(self.email),
            role=self.role.value,
            created_by=self.created_by or "system"
        ))

    def _validate_user_data(self):
        """Validate user data according to business rules."""
        if not self.username or len(self.username.strip()) == 0:
            raise InvalidUserError("Username cannot be empty")

        if len(self.username) < 3:
            raise InvalidUserError("Username must be at least 3 characters long")

    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.username

    def update_email(self, new_email: Email, updated_by: str) -> None:
        """Update user email."""
        old_email = self.email
        self.email = new_email
        self.updated_at = datetime.utcnow()

        self._add_domain_event(UserUpdated(
            user_id=str(self.id),
            updated_fields=["email"],
            updated_by=updated_by
        ))

    def update_role(self, new_role: UserRole, updated_by: str) -> None:
        """Update user role."""
        if new_role == self.role:
            return

        old_role = self.role
        self.role = new_role
        self.updated_at = datetime.utcnow()

        self._add_domain_event(UserRoleChanged(
            user_id=str(self.id),
            old_role=old_role.value,
            new_role=new_role.value,
            changed_by=updated_by
        ))

    def deactivate(self, deactivated_by: str) -> None:
        """Deactivate the user."""
        if not self.is_active:
            return

        self.is_active = False
        self.updated_at = datetime.utcnow()

        self._add_domain_event(UserUpdated(
            user_id=str(self.id),
            updated_fields=["is_active"],
            updated_by=deactivated_by
        ))

    def activate(self, activated_by: str) -> None:
        """Activate the user."""
        if self.is_active:
            return

        self.is_active = True
        self.updated_at = datetime.utcnow()

        self._add_domain_event(UserUpdated(
            user_id=str(self.id),
            updated_fields=["is_active"],
            updated_by=activated_by
        ))

    def _add_domain_event(self, event) -> None:
        """Add domain event to the collection."""
        self._domain_events.append(event)

    def get_domain_events(self) -> List:
        """Get all domain events."""
        return self._domain_events.copy()

    def clear_domain_events(self) -> None:
        """Clear domain events after processing."""
        self._domain_events.clear()


@dataclass
class Project:
    """Project entity with business logic and validation."""

    id: ProjectId
    name: str
    building_id: BuildingId
    status: ProjectStatus = ProjectStatus.DRAFT
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Domain events
    _domain_events: List = field(default_factory=list, init=False)

    def __post_init__(self):
        """Validate project data after initialization."""
        self._validate_project_data()
        self._add_domain_event(ProjectCreated(
            project_id=str(self.id),
            project_name=self.name,
            building_id=str(self.building_id),
            created_by=self.created_by or "system"
        ))

    def _validate_project_data(self):
        """Validate project data according to business rules."""
        if not self.name or len(self.name.strip()) == 0:
            raise InvalidProjectError("Project name cannot be empty")

        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise InvalidProjectError("Start date cannot be after end date")

    @property
    def duration_days(self) -> Optional[int]:
        """Calculate project duration in days."""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return None

    def update_name(self, new_name: str, updated_by: str) -> None:
        """Update project name."""
        if not new_name or len(new_name.strip()) == 0:
            raise InvalidProjectError("Project name cannot be empty")

        self.name = new_name.strip()
        self.updated_at = datetime.utcnow()

        self._add_domain_event(ProjectUpdated(
            project_id=str(self.id),
            updated_fields=["name"],
            updated_by=updated_by
        ))

    def update_status(self, new_status: ProjectStatus, updated_by: str) -> None:
        """Update project status."""
        if new_status == self.status:
            return

        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.utcnow()

        self._add_domain_event(ProjectStatusChanged(
            project_id=str(self.id),
            old_status=old_status.value,
            new_status=new_status.value,
            changed_by=updated_by
        ))

    def _add_domain_event(self, event) -> None:
        """Add domain event to the collection."""
        self._domain_events.append(event)

    def get_domain_events(self) -> List:
        """Get all domain events."""
        return self._domain_events.copy()

    def clear_domain_events(self) -> None:
        """Clear domain events after processing."""
        self._domain_events.clear()
