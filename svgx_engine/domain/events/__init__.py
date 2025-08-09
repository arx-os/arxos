"""
Domain Events - Event-Driven Architecture

This module contains domain events that represent something that happened
in the domain and are used for communication between aggregates and
external systems.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict


@dataclass
class DomainEvent(ABC):
    """Base class for all domain events."""

    @property
    @abstractmethod
def event_type(self) -> str:
        """Get the event type."""
        pass

    @property
    @abstractmethod
def event_version(self) -> str:
        """Get the event version."""
        pass

    @abstractmethod
def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        pass


from svgx_engine.domain.events.building_events import (
    BuildingCreatedEvent,
    BuildingUpdatedEvent,
    BuildingDeletedEvent,
    BuildingStatusChangedEvent,
    BuildingLocationChangedEvent,
    BuildingCostUpdatedEvent,
    building_event_publisher
)

# Version and metadata
__version__ = "1.0.0"
__description__ = "Domain events for SVGX Engine"

# Export all events
__all__ = [
    "BuildingCreatedEvent",
    "BuildingUpdatedEvent",
    "BuildingDeletedEvent",
    "BuildingStatusChangedEvent",
    "BuildingLocationChangedEvent",
    "BuildingCostUpdatedEvent",
    "building_event_publisher"
]
