"""
Building Aggregate

Represents a building aggregate with its related entities and business logic.
This aggregate encapsulates the building entity and its related value objects,
ensuring consistency and business rules.
"""

from typing import List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime

from ..entities.building import Building
from ..value_objects.address import Address
from ..value_objects.coordinates import Coordinates
from ..value_objects.dimensions import Dimensions
from ..value_objects.money import Money
from ..value_objects.status import Status, StatusType
from ..value_objects.identifier import Identifier
from ..events.building_events import (
    BuildingCreatedEvent,
    BuildingUpdatedEvent,
    BuildingStatusChangedEvent,
    BuildingAddressChangedEvent
)


@dataclass
class BuildingAggregate:
    """
    Building aggregate representing a building with its related entities.
    
    This aggregate encapsulates the building entity and ensures business rules
    are enforced when making changes to the building or its related entities.
    """
    
    building: Building
    _domain_events: List = field(default_factory=list, repr=False)
    
    def __post_init__(self):
        """Validate aggregate after initialization."""
        if not isinstance(self.building, Building):
            raise ValueError("Building must be a Building entity")
    
    @classmethod
    def create(cls, 
               name: str,
               address: Address,
               coordinates: Coordinates,
               dimensions: Dimensions,
               building_type: str,
               status: Status = None) -> 'BuildingAggregate':
        """
        Create a new building aggregate.
        
        Args:
            name: Building name
            address: Building address
            coordinates: Building coordinates
            dimensions: Building dimensions
            building_type: Type of building
            status: Initial status (defaults to active)
            
        Returns:
            New BuildingAggregate instance
        """
        if status is None:
            status = Status.active("Building created")
        
        building = Building.create(
            name=name,
            address=address,
            coordinates=coordinates,
            dimensions=dimensions,
            building_type=building_type,
            status=status
        )
        
        aggregate = cls(building=building)
        aggregate._add_domain_event(BuildingCreatedEvent(
            building_id=building.id,
            name=building.name,
            address=building.address,
            coordinates=building.coordinates,
            created_at=datetime.utcnow()
        ))
        
        return aggregate
    
    @property
    def id(self) -> Identifier:
        """Get building ID."""
        return self.building.id
    
    @property
    def name(self) -> str:
        """Get building name."""
        return self.building.name
    
    @property
    def address(self) -> Address:
        """Get building address."""
        return self.building.address
    
    @property
    def coordinates(self) -> Coordinates:
        """Get building coordinates."""
        return self.building.coordinates
    
    @property
    def dimensions(self) -> Dimensions:
        """Get building dimensions."""
        return self.building.dimensions
    
    @property
    def building_type(self) -> str:
        """Get building type."""
        return self.building.building_type
    
    @property
    def status(self) -> Status:
        """Get building status."""
        return self.building.status
    
    @property
    def domain_events(self) -> List:
        """Get all domain events."""
        return self._domain_events.copy()
    
    def clear_domain_events(self):
        """Clear all domain events."""
        self._domain_events.clear()
    
    def _add_domain_event(self, event):
        """Add a domain event to the aggregate."""
        self._domain_events.append(event)
    
    def update_name(self, new_name: str):
        """
        Update building name.
        
        Args:
            new_name: New building name
        """
        if not new_name or not new_name.strip():
            raise ValueError("Building name cannot be empty")
        
        old_name = self.building.name
        self.building.update_name(new_name)
        
        self._add_domain_event(BuildingUpdatedEvent(
            building_id=self.building.id,
            field_name="name",
            old_value=old_name,
            new_value=new_name,
            updated_at=datetime.utcnow()
        ))
    
    def update_address(self, new_address: Address):
        """
        Update building address.
        
        Args:
            new_address: New building address
        """
        if not isinstance(new_address, Address):
            raise ValueError("Address must be an Address value object")
        
        old_address = self.building.address
        self.building.update_address(new_address)
        
        self._add_domain_event(BuildingAddressChangedEvent(
            building_id=self.building.id,
            old_address=old_address,
            new_address=new_address,
            changed_at=datetime.utcnow()
        ))
    
    def update_coordinates(self, new_coordinates: Coordinates):
        """
        Update building coordinates.
        
        Args:
            new_coordinates: New building coordinates
        """
        if not isinstance(new_coordinates, Coordinates):
            raise ValueError("Coordinates must be a Coordinates value object")
        
        old_coordinates = self.building.coordinates
        self.building.update_coordinates(new_coordinates)
        
        self._add_domain_event(BuildingUpdatedEvent(
            building_id=self.building.id,
            field_name="coordinates",
            old_value=old_coordinates,
            new_value=new_coordinates,
            updated_at=datetime.utcnow()
        ))
    
    def update_dimensions(self, new_dimensions: Dimensions):
        """
        Update building dimensions.
        
        Args:
            new_dimensions: New building dimensions
        """
        if not isinstance(new_dimensions, Dimensions):
            raise ValueError("Dimensions must be a Dimensions value object")
        
        old_dimensions = self.building.dimensions
        self.building.update_dimensions(new_dimensions)
        
        self._add_domain_event(BuildingUpdatedEvent(
            building_id=self.building.id,
            field_name="dimensions",
            old_value=old_dimensions,
            new_value=new_dimensions,
            updated_at=datetime.utcnow()
        ))
    
    def change_status(self, new_status: Status):
        """
        Change building status.
        
        Args:
            new_status: New building status
        """
        if not isinstance(new_status, Status):
            raise ValueError("Status must be a Status value object")
        
        if not self.building.status.can_transition_to(new_status):
            raise ValueError(f"Cannot transition from {self.building.status.value} to {new_status.value}")
        
        old_status = self.building.status
        self.building.change_status(new_status)
        
        self._add_domain_event(BuildingStatusChangedEvent(
            building_id=self.building.id,
            old_status=old_status,
            new_status=new_status,
            changed_at=datetime.utcnow()
        ))
    
    def is_active(self) -> bool:
        """Check if building is active."""
        return self.building.is_active()
    
    def is_available(self) -> bool:
        """Check if building is available for use."""
        return self.building.is_available()
    
    def get_area(self) -> float:
        """Get building area in square meters."""
        return self.building.get_area()
    
    def get_volume(self) -> Optional[float]:
        """Get building volume in cubic meters."""
        return self.building.get_volume()
    
    def calculate_distance_to(self, other_coordinates: Coordinates) -> float:
        """
        Calculate distance to another location.
        
        Args:
            other_coordinates: Coordinates to calculate distance to
            
        Returns:
            Distance in kilometers
        """
        return self.building.calculate_distance_to(other_coordinates)
    
    def __str__(self) -> str:
        """String representation of building aggregate."""
        return f"BuildingAggregate(id={self.building.id}, name='{self.building.name}')"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"BuildingAggregate(building={self.building}, domain_events_count={len(self._domain_events)})" 