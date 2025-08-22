"""
Coordinate System for Arxos
Handles transformations between PDF space and world space with nanometer precision
"""

from typing import Tuple, Optional, Dict, Any
from pydantic import BaseModel, Field
import numpy as np
from enum import Enum


class Units(str, Enum):
    """Measurement units"""
    IMPERIAL = "imperial"
    METRIC = "metric"
    

class Point3D(BaseModel):
    """3D point with nanometer precision using int64"""
    x: int = Field(..., description="X coordinate in nanometers")
    y: int = Field(..., description="Y coordinate in nanometers")
    z: int = Field(..., description="Z coordinate in nanometers")
    
    @classmethod
    def from_mm(cls, x: float, y: float, z: float = 0) -> "Point3D":
        """Create from millimeters"""
        return cls(
            x=int(x * 1_000_000),
            y=int(y * 1_000_000),
            z=int(z * 1_000_000)
        )
    
    @classmethod
    def from_inches(cls, x: float, y: float, z: float = 0) -> "Point3D":
        """Create from inches"""
        return cls(
            x=int(x * 25_400_000),
            y=int(y * 25_400_000),
            z=int(z * 25_400_000)
        )
    
    @classmethod
    def from_feet(cls, x: float, y: float, z: float = 0) -> "Point3D":
        """Create from feet"""
        return cls(
            x=int(x * 304_800_000),
            y=int(y * 304_800_000),
            z=int(z * 304_800_000)
        )
    
    def to_mm(self) -> Tuple[float, float, float]:
        """Convert to millimeters"""
        return (
            self.x / 1_000_000,
            self.y / 1_000_000,
            self.z / 1_000_000
        )
    
    def to_feet(self) -> Tuple[float, float, float]:
        """Convert to feet"""
        return (
            self.x / 304_800_000,
            self.y / 304_800_000,
            self.z / 304_800_000
        )


class BoundingBox(BaseModel):
    """Axis-aligned bounding box in world space"""
    min_point: Point3D
    max_point: Point3D
    
    @property
    def width_nm(self) -> int:
        """Width in nanometers"""
        return self.max_point.x - self.min_point.x
    
    @property
    def height_nm(self) -> int:
        """Height in nanometers"""
        return self.max_point.y - self.min_point.y
    
    @property
    def depth_nm(self) -> int:
        """Depth in nanometers"""
        return self.max_point.z - self.min_point.z
    
    def contains(self, point: Point3D) -> bool:
        """Check if point is inside bounding box"""
        return (
            self.min_point.x <= point.x <= self.max_point.x and
            self.min_point.y <= point.y <= self.max_point.y and
            self.min_point.z <= point.z <= self.max_point.z
        )
    
    def intersects(self, other: "BoundingBox") -> bool:
        """Check if two bounding boxes intersect"""
        return not (
            self.max_point.x < other.min_point.x or
            self.min_point.x > other.max_point.x or
            self.max_point.y < other.min_point.y or
            self.min_point.y > other.max_point.y or
            self.max_point.z < other.min_point.z or
            self.min_point.z > other.max_point.z
        )


class Transform(BaseModel):
    """3D transformation matrix for rotation, scale, and translation"""
    matrix: list[list[float]] = Field(
        default_factory=lambda: [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ],
        description="4x4 transformation matrix"
    )
    
    @classmethod
    def identity(cls) -> "Transform":
        """Create identity transform"""
        return cls()
    
    @classmethod
    def translation(cls, x: int, y: int, z: int = 0) -> "Transform":
        """Create translation transform (values in nanometers)"""
        return cls(matrix=[
            [1, 0, 0, x],
            [0, 1, 0, y],
            [0, 0, 1, z],
            [0, 0, 0, 1]
        ])
    
    @classmethod
    def scale(cls, sx: float, sy: float, sz: float = 1.0) -> "Transform":
        """Create scale transform"""
        return cls(matrix=[
            [sx, 0, 0, 0],
            [0, sy, 0, 0],
            [0, 0, sz, 0],
            [0, 0, 0, 1]
        ])
    
    @classmethod
    def rotation_z(cls, angle_radians: float) -> "Transform":
        """Create rotation around Z axis"""
        cos_a = float(np.cos(angle_radians))
        sin_a = float(np.sin(angle_radians))
        return cls(matrix=[
            [cos_a, -sin_a, 0, 0],
            [sin_a, cos_a, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
    
    def apply(self, point: Point3D) -> Point3D:
        """Apply transform to a point"""
        p = np.array([point.x, point.y, point.z, 1])
        m = np.array(self.matrix)
        result = m @ p
        return Point3D(
            x=int(result[0]),
            y=int(result[1]),
            z=int(result[2])
        )
    
    def compose(self, other: "Transform") -> "Transform":
        """Compose two transforms (multiply matrices)"""
        m1 = np.array(self.matrix)
        m2 = np.array(other.matrix)
        result = m1 @ m2
        return Transform(matrix=result.tolist())


class CoordinateSystem(BaseModel):
    """
    Coordinate system for PDF to world space transformation
    Maintains nanometer precision throughout the pipeline
    """
    
    # PDF properties
    pdf_width_pixels: int = Field(..., description="PDF page width in pixels")
    pdf_height_pixels: int = Field(..., description="PDF page height in pixels")
    pdf_dpi: float = Field(72.0, description="PDF dots per inch")
    
    # Scale properties
    scale_numerator: float = Field(1.0, description="Scale numerator (e.g., 1/4)")
    scale_denominator: float = Field(48.0, description="Scale denominator (1/4\" = 1' => 48)")
    units: Units = Field(Units.IMPERIAL, description="Measurement units")
    
    # World space origin
    origin: Point3D = Field(
        default_factory=lambda: Point3D(x=0, y=0, z=0),
        description="Origin point in world coordinates"
    )
    
    # Cached transform
    _pdf_to_world: Optional[Transform] = None
    
    def get_scale_factor(self) -> float:
        """Get the scale factor for PDF to real world conversion"""
        if self.units == Units.IMPERIAL:
            # e.g., 1/4" = 1' means 1 inch on paper = 48 inches in real world
            return self.scale_denominator / self.scale_numerator
        else:
            # For metric, scale is typically 1:100, 1:50, etc.
            return self.scale_denominator
    
    def pdf_to_world_point(self, pdf_x: float, pdf_y: float) -> Point3D:
        """
        Convert PDF pixel coordinates to world nanometer coordinates
        
        Args:
            pdf_x: X coordinate in PDF pixels
            pdf_y: Y coordinate in PDF pixels
            
        Returns:
            Point3D in world space (nanometers)
        """
        # Convert pixels to inches (PDF space)
        inches_x = pdf_x / self.pdf_dpi
        inches_y = pdf_y / self.pdf_dpi
        
        # Apply scale factor to get real-world dimensions
        scale_factor = self.get_scale_factor()
        
        if self.units == Units.IMPERIAL:
            # Convert to real-world feet
            real_feet_x = inches_x * scale_factor / 12.0
            real_feet_y = inches_y * scale_factor / 12.0
            
            # Convert to nanometers and apply origin offset
            world_point = Point3D.from_feet(real_feet_x, real_feet_y)
        else:
            # Convert to real-world millimeters
            real_mm_x = inches_x * 25.4 * scale_factor
            real_mm_y = inches_y * 25.4 * scale_factor
            
            # Convert to nanometers and apply origin offset
            world_point = Point3D.from_mm(real_mm_x, real_mm_y)
        
        # Apply origin offset
        world_point.x += self.origin.x
        world_point.y += self.origin.y
        world_point.z += self.origin.z
        
        return world_point
    
    def world_to_pdf_point(self, world_point: Point3D) -> Tuple[float, float]:
        """
        Convert world nanometer coordinates back to PDF pixel coordinates
        
        Args:
            world_point: Point in world space (nanometers)
            
        Returns:
            Tuple of (x, y) in PDF pixels
        """
        # Remove origin offset
        x = world_point.x - self.origin.x
        y = world_point.y - self.origin.y
        
        scale_factor = self.get_scale_factor()
        
        if self.units == Units.IMPERIAL:
            # Convert nanometers to feet
            feet_x, feet_y, _ = Point3D(x=x, y=y, z=0).to_feet()
            
            # Apply inverse scale to get inches on paper
            inches_x = feet_x * 12.0 / scale_factor
            inches_y = feet_y * 12.0 / scale_factor
        else:
            # Convert nanometers to mm
            mm_x, mm_y, _ = Point3D(x=x, y=y, z=0).to_mm()
            
            # Apply inverse scale to get inches on paper
            inches_x = mm_x / (25.4 * scale_factor)
            inches_y = mm_y / (25.4 * scale_factor)
        
        # Convert inches to pixels
        pdf_x = inches_x * self.pdf_dpi
        pdf_y = inches_y * self.pdf_dpi
        
        return (pdf_x, pdf_y)
    
    def extract_scale_from_text(self, text: str) -> bool:
        """
        Extract scale from text like "1/4\" = 1'-0\"" or "1:100"
        
        Returns:
            True if scale was successfully extracted
        """
        import re
        
        # Imperial scale pattern: 1/4" = 1'-0"
        imperial_pattern = r'(\d+)/(\d+)"?\s*=\s*(\d+)\'?\s*-?\s*(\d+)"?'
        match = re.search(imperial_pattern, text)
        if match:
            num1, den1, feet, inches = match.groups()
            self.scale_numerator = float(num1) / float(den1)
            self.scale_denominator = float(feet) * 12 + float(inches)
            self.units = Units.IMPERIAL
            return True
        
        # Metric scale pattern: 1:100
        metric_pattern = r'1\s*:\s*(\d+)'
        match = re.search(metric_pattern, text)
        if match:
            self.scale_numerator = 1.0
            self.scale_denominator = float(match.group(1))
            self.units = Units.METRIC
            return True
        
        return False


class Dimensions(BaseModel):
    """Real-world dimensions of an object"""
    width: int = Field(..., description="Width in nanometers")
    height: int = Field(..., description="Height in nanometers")
    depth: int = Field(0, description="Depth in nanometers (for 3D objects)")
    
    @property
    def width_mm(self) -> float:
        return self.width / 1_000_000
    
    @property
    def height_mm(self) -> float:
        return self.height / 1_000_000
    
    @property
    def depth_mm(self) -> float:
        return self.depth / 1_000_000
    
    @property
    def width_feet(self) -> float:
        return self.width / 304_800_000
    
    @property
    def height_feet(self) -> float:
        return self.height / 304_800_000
    
    @property
    def depth_feet(self) -> float:
        return self.depth / 304_800_000