"""
Domain Layer - Core Domain Models and Business Logic

This module contains the core domain models, entities, value objects,
aggregates, repositories, services, and events that implement the
business logic and rules of the SVGX Engine.
"""

# Domain Entities
from svgx_engine.domain.entities import (
    Building,
)

# Domain Value Objects
from svgx_engine.domain.value_objects import (
    Address, Coordinates, Dimensions, Identifier, Money, Status,
)

# Domain Aggregates
from svgx_engine.domain.aggregates import (
    BuildingAggregate,
)

# Domain Repositories
from svgx_engine.domain.repositories import (
    BuildingRepository,
)

# Domain Services
from svgx_engine.domain.services import (
    BuildingService,
)

# Domain Events
from svgx_engine.domain.events import (
    BuildingCreatedEvent, BuildingUpdatedEvent, BuildingDeletedEvent,
    BuildingStatusChangedEvent, BuildingLocationChangedEvent, BuildingCostUpdatedEvent,
    building_event_publisher
)

# Version and metadata
__version__ = "1.0.0"
__description__ = "Domain layer for SVGX Engine"

# Export all domain components
__all__ = [
    # Entities
    "Building",

    # Value Objects
    "Address", "Coordinates", "Dimensions", "Identifier", "Money", "Status",

    # Aggregates
    "BuildingAggregate",

    # Repositories
    "BuildingRepository",

    # Services
    "BuildingService",

    # Events
    "BuildingCreatedEvent", "BuildingUpdatedEvent", "BuildingDeletedEvent",
    "BuildingStatusChangedEvent", "BuildingLocationChangedEvent", "BuildingCostUpdatedEvent",
    "building_event_publisher"
]
