"""
Building Entity - Core Domain Entity
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field
import uuid

from svgx_engine.domain.value_objects import Identifier, Address, Dimensions
from svgx_engine.domain.events import BuildingCreatedEvent, BuildingUpdatedEvent, DomainEvent

@dataclass
class Building:
    """
    Core building entity representing a physical building in the domain.
    
    This entity encapsulates the core business logic and invariants
    for building operations, following Domain-Driven Design principles.
    """
    
    id: Identifier
    name: str
    address: Address
    dimensions: Dimensions
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate building entity after initialization."""
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Building name cannot be empty")
        
        if not self.address:
            raise ValueError("Building address is required")
        
        if not self.dimensions:
            raise ValueError("Building dimensions are required")
    
    @property
    def full_name(self) -> str:
        """Get the full building name with address."""
        return f"{self.name} - {self.address.full_address}"
    
    @property
    def area(self) -> float:
        """Calculate building area in square meters."""
        return self.dimensions.area
    
    @property
    def volume(self) -> float:
        """Calculate building volume in cubic meters."""
        return self.dimensions.volume
    
    def update_name(self, new_name: str) -> None:
        """
        Update building name with validation.
        
        Args:
            new_name: New building name
        """
        if not new_name or len(new_name.strip()) == 0:
            raise ValueError("Building name cannot be empty")
        
        old_name = self.name
        self.name = new_name.strip()
        self.updated_at = datetime.utcnow()
        
        # Raise domain event
        self._raise_event(BuildingUpdatedEvent(
            building_id=str(self.id),
            updated_fields={"name": new_name},
            updated_by="system",
            previous_values={"name": old_name}
        ))
    
    def update_address(self, new_address: Address) -> None:
        """
        Update building address.
        
        Args:
            new_address: New building address
        """
        if not new_address:
            raise ValueError("Building address is required")
        
        old_address = self.address
        self.address = new_address
        self.updated_at = datetime.utcnow()
        
        # Raise domain event
        self._raise_event(BuildingUpdatedEvent(
            building_id=str(self.id),
            updated_fields={"address": new_address},
            updated_by="system",
            previous_values={"address": old_address}
        ))
    
    def update_dimensions(self, new_dimensions: Dimensions) -> None:
        """
        Update building dimensions.
        
        Args:
            new_dimensions: New building dimensions
        """
        if not new_dimensions:
            raise ValueError("Building dimensions are required")
        
        old_dimensions = self.dimensions
        self.dimensions = new_dimensions
        self.updated_at = datetime.utcnow()
        
        # Raise domain event
        self._raise_event(BuildingUpdatedEvent(
            building_id=str(self.id),
            updated_fields={"dimensions": new_dimensions},
            updated_by="system",
            previous_values={"dimensions": old_dimensions}
        ))
    
    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add metadata to the building.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()
        
        # Raise domain event
        self._raise_event(BuildingUpdatedEvent(
            building_id=str(self.id),
            updated_fields={"metadata": {key: value}},
            updated_by="system"
        ))
    
    def remove_metadata(self, key: str) -> None:
        """
        Remove metadata from the building.
        
        Args:
            key: Metadata key to remove
        """
        if key in self.metadata:
            old_value = self.metadata.pop(key)
            self.updated_at = datetime.utcnow()
            
            # Raise domain event
            self._raise_event(BuildingUpdatedEvent(
                building_id=str(self.id),
                updated_fields={"metadata": {key: None}},
                updated_by="system",
                previous_values={"metadata": {key: old_value}}
            ))
    
    def is_valid(self) -> bool:
        """
        Check if the building entity is valid.
        
        Returns:
            True if the building is valid, False otherwise
        """
        try:
            if not self.name or len(self.name.strip()) == 0:
                return False
            
            if not self.address:
                return False
            
            if not self.dimensions:
                return False
            
            return True
        except Exception:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert building entity to dictionary.
        
        Returns:
            Dictionary representation of the building
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "address": self.address.to_dict(),
            "dimensions": self.dimensions.to_dict(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "area": self.area,
            "volume": self.volume
        }
    
    def _raise_event(self, event: DomainEvent) -> None:
        """
        Raise a domain event.
        
        Args:
            event: Domain event to raise
        """
        # This would typically be handled by an event bus or publisher
        # For now, we'll just log the event
        print(f"Domain event raised: {event.event_type} for building {self.id}")
    
    @classmethod
    def create(
        cls,
        name: str,
        address: Address,
        dimensions: Dimensions,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "Building":
        """
        Create a new building entity.
        
        Args:
            name: Building name
            address: Building address
            dimensions: Building dimensions
            metadata: Optional metadata
            
        Returns:
            New building entity
        """
        building_id = Identifier(str(uuid.uuid4()))
        building = cls(
            id=building_id,
            name=name,
            address=address,
            dimensions=dimensions,
            metadata=metadata or {}
        )
        
        # Raise creation event
        building._raise_event(BuildingCreatedEvent(
            building_id=str(building_id),
            name=name,
            address=address,
            coordinates=address.coordinates if hasattr(address, 'coordinates') else None,
            status=None,  # Building entity doesn't have status
            created_by="system"
        ))
        
        return building 