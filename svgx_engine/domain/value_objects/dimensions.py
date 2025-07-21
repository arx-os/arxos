"""
Dimensions Value Object

Represents physical dimensions (length, width, height) in the domain.
This is a value object that is immutable and defined by its attributes.
"""

from dataclasses import dataclass
from typing import Optional
import math


@dataclass(frozen=True)
class Dimensions:
    """
    Dimensions value object representing physical size.
    
    Attributes:
        length: Length in meters
        width: Width in meters
        height: Height in meters (optional for 2D objects)
    """
    
    length: float
    width: float
    height: Optional[float] = None
    
    def __post_init__(self):
        """Validate dimensions after initialization."""
        self._validate_length()
        self._validate_width()
        self._validate_height()
    
    def _validate_length(self):
        """Validate length value."""
        if not isinstance(self.length, (int, float)):
            raise ValueError("Length must be a number")
        if self.length <= 0:
            raise ValueError("Length must be positive")
    
    def _validate_width(self):
        """Validate width value."""
        if not isinstance(self.width, (int, float)):
            raise ValueError("Width must be a number")
        if self.width <= 0:
            raise ValueError("Width must be positive")
    
    def _validate_height(self):
        """Validate height value if provided."""
        if self.height is not None:
            if not isinstance(self.height, (int, float)):
                raise ValueError("Height must be a number")
            if self.height <= 0:
                raise ValueError("Height must be positive")
    
    @property
    def is_2d(self) -> bool:
        """Check if dimensions are 2D (no height)."""
        return self.height is None
    
    @property
    def is_3d(self) -> bool:
        """Check if dimensions are 3D (has height)."""
        return self.height is not None
    
    @property
    def area(self) -> float:
        """Calculate surface area (length * width)."""
        return self.length * self.width
    
    @property
    def volume(self) -> Optional[float]:
        """Calculate volume (length * width * height)."""
        if self.height is None:
            return None
        return self.length * self.width * self.height
    
    @property
    def perimeter(self) -> float:
        """Calculate perimeter (2 * (length + width))."""
        return 2 * (self.length + self.width)
    
    @property
    def surface_area(self) -> Optional[float]:
        """Calculate total surface area for 3D objects."""
        if self.height is None:
            return self.area
        
        return 2 * (self.length * self.width + 
                   self.length * self.height + 
                   self.width * self.height)
    
    def fits_inside(self, other: 'Dimensions') -> bool:
        """
        Check if these dimensions fit inside another set of dimensions.
        
        Args:
            other: Another Dimensions object
            
        Returns:
            True if these dimensions fit inside the other dimensions
        """
        if not isinstance(other, Dimensions):
            raise ValueError("Other must be a Dimensions object")
        
        # For 2D comparison
        if self.is_2d and other.is_2d:
            return (self.length <= other.length and self.width <= other.width) or \
                   (self.length <= other.width and self.width <= other.length)
        
        # For 3D comparison
        if self.is_3d and other.is_3d:
            # Check all possible orientations
            return any([
                self._fits_3d(other.length, other.width, other.height),
                self._fits_3d(other.length, other.height, other.width),
                self._fits_3d(other.width, other.length, other.height),
                self._fits_3d(other.width, other.height, other.length),
                self._fits_3d(other.height, other.length, other.width),
                self._fits_3d(other.height, other.width, other.length)
            ])
        
        return False
    
    def _fits_3d(self, l: float, w: float, h: float) -> bool:
        """Helper method to check if 3D dimensions fit in given space."""
        return (self.length <= l and 
                self.width <= w and 
                self.height is not None and 
                self.height <= h)
    
    def scale(self, factor: float) -> 'Dimensions':
        """
        Create a new Dimensions object scaled by the given factor.
        
        Args:
            factor: Scaling factor
            
        Returns:
            New Dimensions object with scaled dimensions
        """
        if factor <= 0:
            raise ValueError("Scaling factor must be positive")
        
        new_length = self.length * factor
        new_width = self.width * factor
        new_height = self.height * factor if self.height is not None else None
        
        return Dimensions(new_length, new_width, new_height)
    
    def __str__(self) -> str:
        """String representation of dimensions."""
        if self.height is None:
            return f"{self.length}m × {self.width}m"
        return f"{self.length}m × {self.width}m × {self.height}m"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Dimensions(length={self.length}, width={self.width}, height={self.height})"
    
    def to_dict(self) -> dict:
        """Convert dimensions to dictionary representation."""
        return {
            'length': self.length,
            'width': self.width,
            'height': self.height
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Dimensions':
        """Create dimensions from dictionary representation."""
        return cls(
            length=data['length'],
            width=data['width'],
            height=data.get('height')
        ) 