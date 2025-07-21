"""
Domain Events Module

This module contains all domain events used in the domain layer.
Domain events represent something that happened in the domain and are used
for communication between aggregates and external systems.
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


from .building_events import (
    BuildingCreatedEvent,
    BuildingUpdatedEvent,
    BuildingStatusChangedEvent,
    BuildingAddressChangedEvent,
    BuildingDeletedEvent,
    BuildingArchivedEvent
)

__all__ = [
    'DomainEvent',
    'BuildingCreatedEvent',
    'BuildingUpdatedEvent',
    'BuildingStatusChangedEvent',
    'BuildingAddressChangedEvent',
    'BuildingDeletedEvent',
    'BuildingArchivedEvent'
] 