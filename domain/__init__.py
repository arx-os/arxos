"""
Domain Layer - Core Business Logic

This package contains the domain layer of the Clean Architecture implementation.
It includes entities, value objects, domain events, and repository interfaces.

The domain layer is the innermost layer and contains:
- Entities: Core business objects with identity and lifecycle
- Value Objects: Immutable objects that describe domain characteristics
- Domain Events: Events that occur within the domain
- Repository Interfaces: Abstract interfaces for data access
- Domain Services: Business logic that doesn't belong to entities
"""

from .entities import *
from .value_objects import *
from .events import *
from .repositories import *
from .services import *
from .exceptions import *

__all__ = [
    # Entities
    "Building",
    "Floor",
    "Room",
    "Device",
    "User",
    "Project",
    # Value Objects
    "BuildingId",
    "FloorId",
    "RoomId",
    "DeviceId",
    "UserId",
    "ProjectId",
    "Address",
    "Coordinates",
    "Dimensions",
    "Email",
    "PhoneNumber",
    "BuildingStatus",
    "FloorStatus",
    "RoomStatus",
    "DeviceStatus",
    "UserRole",
    "ProjectStatus",
    # Events
    "DomainEvent",
    "EventType",
    "EventHandler",
    "EventBus",
    "BuildingCreated",
    "BuildingUpdated",
    "BuildingStatusChanged",
    "FloorAdded",
    "FloorUpdated",
    "FloorStatusChanged",
    "RoomAdded",
    "RoomUpdated",
    "RoomStatusChanged",
    "DeviceAdded",
    "DeviceUpdated",
    "DeviceStatusChanged",
    "UserCreated",
    "UserUpdated",
    "UserRoleChanged",
    "ProjectCreated",
    "ProjectUpdated",
    "ProjectStatusChanged",
    "publish_event",
    "subscribe_to_event",
    "unsubscribe_from_event",
    # Repository Interfaces
    "BuildingRepository",
    "FloorRepository",
    "RoomRepository",
    "DeviceRepository",
    "UserRepository",
    "ProjectRepository",
    "UnitOfWork",
    "RepositoryFactory",
    # Domain Services
    "BuildingDomainService",
    "FloorDomainService",
    "RoomDomainService",
    "DeviceDomainService",
    "UserDomainService",
    "ProjectDomainService",
    # Exceptions
    "DomainException",
    "InvalidBuildingError",
    "InvalidFloorError",
    "InvalidRoomError",
    "InvalidDeviceError",
    "InvalidUserError",
    "InvalidProjectError",
    "InvalidAddressError",
    "InvalidCoordinatesError",
    "InvalidDimensionsError",
    "InvalidEmailError",
    "InvalidPhoneNumberError",
    "DuplicateFloorError",
    "DuplicateRoomError",
    "DuplicateDeviceError",
    "BuildingNotFoundError",
    "FloorNotFoundError",
    "RoomNotFoundError",
    "DeviceNotFoundError",
    "UserNotFoundError",
    "ProjectNotFoundError",
    "InvalidStatusTransitionError",
    "InsufficientPermissionsError",
    "BusinessRuleViolationError",
    "ValidationError",
    "ConcurrencyError",
    "DomainEventError",
    "RepositoryError",
    "RepositoryConnectionError",
    "RepositoryQueryError",
    "RepositoryTransactionError",
    "DomainServiceError",
    "DomainServiceConfigurationError",
    "DomainServiceExecutionError",
    "format_error_message",
    "raise_domain_exception",
]
