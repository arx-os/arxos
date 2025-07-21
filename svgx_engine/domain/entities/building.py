"""
Building Entity - Core Domain Entity for Clean Architecture.

This module defines the Building entity which represents a physical structure
containing floors and systems in the Arxos domain model.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

from ..value_objects import Identifier, Address, Dimensions
from ..events import BuildingCreatedEvent, BuildingUpdatedEvent, DomainEvent


@dataclass
class Building:
    """
    Building Entity - Represents a physical structure in the domain.
    
    This entity encapsulates the core business logic for buildings,
    including validation rules, business invariants, and domain events.
    """
    
    # Identity
    id: Identifier
    
    # Core Properties
    name: str
    address: Address
    dimensions: Dimensions
    
    # Relationships
    floors: List['Floor'] = field(default_factory=list)
    systems: List['System'] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    # Status
    is_active: bool = True
    status: str = "active"  # active, inactive, demolished, under_construction
    
    # Additional Properties
    building_type: str = "commercial"  # commercial, residential, industrial, mixed
    year_built: Optional[int] = None
    total_area: Optional[float] = None
    energy_rating: Optional[str] = None
    
    # Domain Events
    _domain_events: List[DomainEvent] = field(default_factory=list, repr=False)
    
    def __post_init__(self):
        """Validate entity invariants after initialization."""
        self._validate_invariants()
    
    def _validate_invariants(self):
        """Validate business invariants for the Building entity."""
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Building name cannot be empty")
        
        if len(self.name) > 255:
            raise ValueError("Building name cannot exceed 255 characters")
        
        if self.year_built and (self.year_built < 1800 or self.year_built > datetime.now().year + 10):
            raise ValueError("Year built must be between 1800 and current year + 10")
        
        if self.total_area and self.total_area <= 0:
            raise ValueError("Total area must be positive")
    
    def add_floor(self, floor: 'Floor') -> None:
        """
        Add a floor to the building.
        
        Args:
            floor: Floor entity to add
            
        Raises:
            ValueError: If floor number already exists
        """
        if any(f.floor_number == floor.floor_number for f in self.floors):
            raise ValueError(f"Floor number {floor.floor_number} already exists")
        
        self.floors.append(floor)
        self._add_domain_event(BuildingUpdatedEvent(
            building_id=self.id,
            update_type="floor_added",
            data={"floor_number": floor.floor_number},
            updated_at=datetime.utcnow()
        ))
    
    def remove_floor(self, floor_number: int) -> None:
        """
        Remove a floor from the building.
        
        Args:
            floor_number: Number of the floor to remove
            
        Raises:
            ValueError: If floor number doesn't exist
        """
        floor_to_remove = next((f for f in self.floors if f.floor_number == floor_number), None)
        if not floor_to_remove:
            raise ValueError(f"Floor number {floor_number} does not exist")
        
        self.floors.remove(floor_to_remove)
        self._add_domain_event(BuildingUpdatedEvent(
            building_id=self.id,
            update_type="floor_removed",
            data={"floor_number": floor_number},
            updated_at=datetime.utcnow()
        ))
    
    def add_system(self, system: 'System') -> None:
        """
        Add a system to the building.
        
        Args:
            system: System entity to add
        """
        if any(s.id == system.id for s in self.systems):
            raise ValueError(f"System with ID {system.id} already exists")
        
        self.systems.append(system)
        self._add_domain_event(BuildingUpdatedEvent(
            building_id=self.id,
            update_type="system_added",
            data={"system_id": str(system.id)},
            updated_at=datetime.utcnow()
        ))
    
    def remove_system(self, system_id: str) -> None:
        """
        Remove a system from the building.
        
        Args:
            system_id: ID of the system to remove
            
        Raises:
            ValueError: If system doesn't exist
        """
        system_to_remove = next((s for s in self.systems if str(s.id) == system_id), None)
        if not system_to_remove:
            raise ValueError(f"System with ID {system_id} does not exist")
        
        self.systems.remove(system_to_remove)
        self._add_domain_event(BuildingUpdatedEvent(
            building_id=self.id,
            update_type="system_removed",
            data={"system_id": system_id},
            updated_at=datetime.utcnow()
        ))
    
    def update_info(self, name: Optional[str] = None, 
                   address: Optional[Address] = None,
                   building_type: Optional[str] = None,
                   year_built: Optional[int] = None,
                   total_area: Optional[float] = None,
                   energy_rating: Optional[str] = None,
                   updated_by: Optional[str] = None) -> None:
        """
        Update building information.
        
        Args:
            name: New building name
            address: New address
            building_type: New building type
            year_built: New year built
            total_area: New total area
            energy_rating: New energy rating
            updated_by: User who made the update
        """
        if name is not None:
            self.name = name
        
        if address is not None:
            self.address = address
        
        if building_type is not None:
            self.building_type = building_type
        
        if year_built is not None:
            self.year_built = year_built
        
        if total_area is not None:
            self.total_area = total_area
        
        if energy_rating is not None:
            self.energy_rating = energy_rating
        
        if updated_by is not None:
            self.updated_by = updated_by
        
        self.updated_at = datetime.utcnow()
        self._validate_invariants()
        
        self._add_domain_event(BuildingUpdatedEvent(
            building_id=self.id,
            update_type="info_updated",
            data={
                k: v for k, v in locals().items() 
                if k not in ['self', 'updated_by'] and v is not None
            },
            updated_at=self.updated_at
        ))
    
    def activate(self) -> None:
        """Activate the building."""
        if not self.is_active:
            self.is_active = True
            self.status = "active"
            self.updated_at = datetime.utcnow()
            
            self._add_domain_event(BuildingUpdatedEvent(
                building_id=self.id,
                update_type="building_activated",
                data={},
                updated_at=self.updated_at
            ))
    
    def deactivate(self) -> None:
        """Deactivate the building."""
        if self.is_active:
            self.is_active = False
            self.status = "inactive"
            self.updated_at = datetime.utcnow()
            
            self._add_domain_event(BuildingUpdatedEvent(
                building_id=self.id,
                update_type="building_deactivated",
                data={},
                updated_at=self.updated_at
            ))
    
    def get_total_floors(self) -> int:
        """Get the total number of floors."""
        return len(self.floors)
    
    def get_total_systems(self) -> int:
        """Get the total number of systems."""
        return len(self.systems)
    
    def get_systems_by_type(self, system_type: str) -> List['System']:
        """Get all systems of a specific type."""
        return [s for s in self.systems if s.system_type == system_type]
    
    def get_floor_by_number(self, floor_number: int) -> Optional['Floor']:
        """Get a floor by its number."""
        return next((f for f in self.floors if f.floor_number == floor_number), None)
    
    def _add_domain_event(self, event: DomainEvent) -> None:
        """Add a domain event to the entity."""
        self._domain_events.append(event)
    
    def get_domain_events(self) -> List[DomainEvent]:
        """Get all domain events and clear them."""
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events
    
    def clear_domain_events(self) -> None:
        """Clear all domain events."""
        self._domain_events.clear()
    
    @classmethod
    def create(cls, name: str, address: Address, dimensions: Dimensions,
               building_type: str = "commercial", created_by: Optional[str] = None) -> 'Building':
        """
        Factory method to create a new Building entity.
        
        Args:
            name: Building name
            address: Building address
            dimensions: Building dimensions
            building_type: Type of building
            created_by: User who created the building
            
        Returns:
            New Building entity
        """
        building = cls(
            id=Identifier.generate_uuid("BLD"),
            name=name,
            address=address,
            dimensions=dimensions,
            building_type=building_type,
            created_by=created_by
        )
        
        # Add creation event
        building._add_domain_event(BuildingCreatedEvent(
            building_id=building.id,
            name=building.name,
            address=str(building.address),
            building_type=building.building_type,
            created_by=building.created_by
        ))
        
        return building
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary representation."""
        return {
            'id': str(self.id),
            'name': self.name,
            'address': self.address.to_dict(),
            'dimensions': self.dimensions.to_dict(),
            'floors': [floor.to_dict() for floor in self.floors],
            'systems': [system.to_dict() for system in self.systems],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'is_active': self.is_active,
            'status': self.status,
            'building_type': self.building_type,
            'year_built': self.year_built,
            'total_area': self.total_area,
            'energy_rating': self.energy_rating
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Building':
        """Create entity from dictionary representation."""
        # This would need proper implementation with Floor and System entities
        # For now, return a basic building
        return cls(
            id=Identifier(data['id']),
            name=data['name'],
            address=Address.from_dict(data['address']),
            dimensions=Dimensions.from_dict(data['dimensions']),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            created_by=data.get('created_by'),
            updated_by=data.get('updated_by'),
            is_active=data.get('is_active', True),
            status=data.get('status', 'active'),
            building_type=data.get('building_type', 'commercial'),
            year_built=data.get('year_built'),
            total_area=data.get('total_area'),
            energy_rating=data.get('energy_rating')
        ) 