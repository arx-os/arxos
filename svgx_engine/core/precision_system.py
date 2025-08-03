"""
Precision Drawing System for SVGX Engine

Provides sub-millimeter precision (0.001mm accuracy) for professional CAD functionality.
Implements high-precision coordinate system, validation, and display capabilities.

CTO Directives:
- Enterprise-grade precision system
- Sub-millimeter accuracy (0.001mm)
- Professional CAD coordinate system
- Comprehensive validation and display
"""

import math
import decimal
from dataclasses import dataclass
from enum import Enum
from typing import Tuple, List, Optional, Dict, Any
from decimal import Decimal, getcontext
import logging

# Configure decimal precision for sub-millimeter accuracy
getcontext().prec = 6  # 0.001mm precision

logger = logging.getLogger(__name__)

class PrecisionLevel(Enum):
    """Precision Levels"""
    MILLIMETER = 1.0
    SUB_MILLIMETER = 0.001
    MICRON = 0.0001
    NANOMETER = 0.000001

class CoordinateSystem(Enum):
    """Coordinate System Types"""
    CARTESIAN_2D = "cartesian_2d"
    CARTESIAN_3D = "cartesian_3d"
    POLAR_2D = "polar_2d"
    CYLINDRICAL_3D = "cylindrical_3d"

@dataclass
class PrecisionPoint:
    """High-precision point with sub-millimeter accuracy"""
    x: Decimal
    y: Decimal
    z: Optional[Decimal] = None
    precision_level: PrecisionLevel = PrecisionLevel.SUB_MILLIMETER
    
    def __post_init__(self):
        """Validate and normalize precision"""
        self.x = self._normalize_precision(self.x)
        self.y = self._normalize_precision(self.y)
        if self.z is not None:
            self.z = self._normalize_precision(self.z)
    
    def _normalize_precision(self, value: Decimal) -> Decimal:
        """Normalize value to specified precision level"""
        return Decimal(str(value)).quantize(
            Decimal(str(self.precision_level.value))
        )
    
    def distance_to(self, other: 'PrecisionPoint') -> Decimal:
        """Calculate distance to another point"""
        dx = self.x - other.x
        dy = self.y - other.y
        if self.z is not None and other.z is not None:
            dz = self.z - other.z
            return Decimal(str(math.sqrt(dx**2 + dy**2 + dz**2)))
        return Decimal(str(math.sqrt(dx**2 + dy**2)))
    
    def to_tuple(self) -> Tuple[Decimal, Decimal, Optional[Decimal]]:
        """Convert to tuple representation"""
        return (self.x, self.y, self.z)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        result = {
            'x': float(self.x),
            'y': float(self.y),
            'precision_level': self.precision_level.value
        }
        if self.z is not None:
            result['z'] = float(self.z)
        return result

@dataclass
class PrecisionVector:
    """High-precision vector with sub-millimeter accuracy"""
    dx: Decimal
    dy: Decimal
    dz: Optional[Decimal] = None
    precision_level: PrecisionLevel = PrecisionLevel.SUB_MILLIMETER
    
    def __post_init__(self):
        """Validate and normalize precision"""
        self.dx = self._normalize_precision(self.dx)
        self.dy = self._normalize_precision(self.dy)
        if self.dz is not None:
            self.dz = self._normalize_precision(self.dz)
    
    def _normalize_precision(self, value: Decimal) -> Decimal:
        """Normalize value to specified precision level"""
        return Decimal(str(value)).quantize(
            Decimal(str(self.precision_level.value))
        )
    
    def magnitude(self) -> Decimal:
        """Calculate vector magnitude"""
        if self.dz is not None:
            return Decimal(str(math.sqrt(self.dx**2 + self.dy**2 + self.dz**2)))
        return Decimal(str(math.sqrt(self.dx**2 + self.dy**2)))
    
    def normalize(self) -> 'PrecisionVector':
        """Normalize vector to unit length"""
        mag = self.magnitude()
        if mag == 0:
            return PrecisionVector(0, 0, self.dz)
        return PrecisionVector(
            self.dx / mag,
            self.dy / mag,
            self.dz / mag if self.dz is not None else None
        )

class PrecisionCoordinateSystem:
    """High-precision coordinate system for CAD operations"""
    
    def __init__(self, 
                 system_type: CoordinateSystem = CoordinateSystem.CARTESIAN_2D,
                 origin: Optional[PrecisionPoint] = None,
                 precision_level: PrecisionLevel = PrecisionLevel.SUB_MILLIMETER):
        self.system_type = system_type
        self.origin = origin or PrecisionPoint(0, 0, 0)
        self.precision_level = precision_level
        self.transform_matrix = self._create_identity_matrix()
        self.inverse_matrix = self._create_identity_matrix()
    
    def _create_identity_matrix(self) -> List[List[Decimal]]:
        """Create identity transformation matrix"""
        return [
            [Decimal('1'), Decimal('0'), Decimal('0'), Decimal('0')],
            [Decimal('0'), Decimal('1'), Decimal('0'), Decimal('0')],
            [Decimal('0'), Decimal('0'), Decimal('1'), Decimal('0')],
            [Decimal('0'), Decimal('0'), Decimal('0'), Decimal('1')]
        ]
    
    def transform_point(self, point: PrecisionPoint) -> PrecisionPoint:
        """Transform point using current transformation matrix"""
        # Convert to homogeneous coordinates
        coords = [point.x, point.y, point.z or Decimal('0'), Decimal('1')]
        
        # Apply transformation
        result = [Decimal('0')] * 4
        for i in range(4):
            for j in range(4):
                result[i] += self.transform_matrix[i][j] * coords[j]
        
        # Convert back to precision point
        return PrecisionPoint(
            result[0],
            result[1],
            result[2] if self.system_type == CoordinateSystem.CARTESIAN_3D else None,
            self.precision_level
        )
    
    def set_origin(self, origin: PrecisionPoint):
        """Set coordinate system origin"""
        self.origin = origin
        self._update_transformation_matrix()
    
    def _update_transformation_matrix(self):
        """Update transformation matrix based on origin"""
        # Translation matrix
        self.transform_matrix = [
            [Decimal('1'), Decimal('0'), Decimal('0'), -self.origin.x],
            [Decimal('0'), Decimal('1'), Decimal('0'), -self.origin.y],
            [Decimal('0'), Decimal('0'), Decimal('1'), -self.origin.z or Decimal('0')],
            [Decimal('0'), Decimal('0'), Decimal('0'), Decimal('1')]
        ]
        
        # Calculate inverse matrix
        self._calculate_inverse_matrix()
    
    def _calculate_inverse_matrix(self):
        """Calculate inverse transformation matrix"""
        # For translation, inverse is negative translation
        self.inverse_matrix = [
            [Decimal('1'), Decimal('0'), Decimal('0'), self.origin.x],
            [Decimal('0'), Decimal('1'), Decimal('0'), self.origin.y],
            [Decimal('0'), Decimal('0'), Decimal('1'), self.origin.z or Decimal('0')],
            [Decimal('0'), Decimal('0'), Decimal('0'), Decimal('1')]
        ]

class PrecisionValidator:
    """Validator for precision operations"""
    
    def __init__(self, precision_level: PrecisionLevel = PrecisionLevel.SUB_MILLIMETER):
    """
    Perform __init__ operation

Args:
        precision_level: Description of precision_level

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        self.precision_level = precision_level
        self.tolerance = Decimal(str(precision_level.value))
    
    def validate_point(self, point: PrecisionPoint) -> bool:
        """Validate point precision"""
        try:
            # Check if coordinates are within precision limits
            x_valid = abs(point.x - point.x.quantize(self.tolerance)) < self.tolerance
            y_valid = abs(point.y - point.y.quantize(self.tolerance)) < self.tolerance
            z_valid = True
            if point.z is not None:
                z_valid = abs(point.z - point.z.quantize(self.tolerance)) < self.tolerance
            
            return x_valid and y_valid and z_valid
        except Exception as e:
            logger.error(f"Point validation error: {e}")
            return False
    
    def validate_distance(self, distance: Decimal) -> bool:
        """Validate distance precision"""
        try:
            return distance >= 0 and abs(distance - distance.quantize(self.tolerance)) < self.tolerance
        except Exception as e:
            logger.error(f"Distance validation error: {e}")
            return False
    
    def validate_angle(self, angle: Decimal) -> bool:
        """Validate angle precision (in radians)"""
        try:
            # Normalize angle to 0-2π range
            normalized_angle = angle % (2 * Decimal(str(math.pi)))
            return abs(normalized_angle - normalized_angle.quantize(self.tolerance)) < self.tolerance
        except Exception as e:
            logger.error(f"Angle validation error: {e}")
            return False

class PrecisionDisplay:
    """
    Perform __init__ operation

Args:
        precision_level: Description of precision_level

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
    """Display utilities for precision values"""
    
    def __init__(self, precision_level: PrecisionLevel = PrecisionLevel.SUB_MILLIMETER):
        self.precision_level = precision_level
    
    def format_point(self, point: PrecisionPoint, units: str = "mm") -> str:
        """Format point for display"""
        if point.z is not None:
            return f"({float(point.x):.3f}, {float(point.y):.3f}, {float(point.z):.3f}) {units}"
        return f"({float(point.x):.3f}, {float(point.y):.3f}) {units}"
    
    def format_distance(self, distance: Decimal, units: str = "mm") -> str:
        """Format distance for display"""
        return f"{float(distance):.3f} {units}"
    
    def format_angle(self, angle: Decimal, units: str = "rad") -> str:
        """Format angle for display"""
        return f"{float(angle):.6f} {units}"
    
    def format_precision_level(self) -> str:
        """Format precision level for display"""
        if self.precision_level == PrecisionLevel.SUB_MILLIMETER:
            return "0.001mm"
        elif self.precision_level == PrecisionLevel.MICRON:
            return "0.0001mm"
        elif self.precision_level == PrecisionLevel.NANOMETER:
            return "0.000001mm"
        else:
    """
    Perform __init__ operation

Args:
        precision_level: Description of precision_level

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
            return "1.0mm"

class PrecisionDrawingSystem:
    """Main precision drawing system"""
    
    def __init__(self, precision_level: PrecisionLevel = PrecisionLevel.SUB_MILLIMETER):
        self.precision_level = precision_level
        self.coordinate_system = PrecisionCoordinateSystem(
            precision_level=precision_level
        )
        self.validator = PrecisionValidator(precision_level)
        self.display = PrecisionDisplay(precision_level)
        self.points = []
        self.vectors = []
        
        logger.info(f"Precision Drawing System initialized with {self.display.format_precision_level()} accuracy")
    
    def add_point(self, x: float, y: float, z: Optional[float] = None) -> PrecisionPoint:
        """Add a new precision point"""
        point = PrecisionPoint(
            Decimal(str(x)),
            Decimal(str(y)),
            Decimal(str(z)) if z is not None else None,
            self.precision_level
        )
        
        if self.validator.validate_point(point):
            self.points.append(point)
            logger.info(f"Added precision point: {self.display.format_point(point)}")
            return point
        else:
            raise ValueError(f"Invalid precision point: {self.display.format_point(point)}")
    
    def add_vector(self, dx: float, dy: float, dz: Optional[float] = None) -> PrecisionVector:
        """Add a new precision vector"""
        vector = PrecisionVector(
            Decimal(str(dx)),
            Decimal(str(dy)),
            Decimal(str(dz)) if dz is not None else None,
            self.precision_level
        )
        
        self.vectors.append(vector)
        logger.info(f"Added precision vector: {self.display.format_distance(vector.magnitude())}")
        return vector
    
    def calculate_distance(self, point1: PrecisionPoint, point2: PrecisionPoint) -> Decimal:
        """Calculate distance between two points"""
        distance = point1.distance_to(point2)
        
        if self.validator.validate_distance(distance):
            return distance
        else:
            raise ValueError(f"Invalid distance calculation: {self.display.format_distance(distance)}")
    
    def transform_point(self, point: PrecisionPoint) -> PrecisionPoint:
        """Transform point using coordinate system"""
        return self.coordinate_system.transform_point(point)
    
    def set_origin(self, x: float, y: float, z: Optional[float] = None):
        """Set coordinate system origin"""
        origin = PrecisionPoint(
            Decimal(str(x)),
            Decimal(str(y)),
            Decimal(str(z)) if z is not None else None,
            self.precision_level
        )
        self.coordinate_system.set_origin(origin)
        logger.info(f"Set coordinate system origin: {self.display.format_point(origin)}")
    
    def get_precision_info(self) -> Dict[str, Any]:
        """Get precision system information"""
        return {
            'precision_level': self.precision_level.value,
            'precision_display': self.display.format_precision_level(),
            'coordinate_system': self.coordinate_system.system_type.value,
            'origin': self.coordinate_system.origin.to_dict(),
            'point_count': len(self.points),
            'vector_count': len(self.vectors)
        }
    
    def validate_system(self) -> bool:
        """Validate entire precision system"""
        try:
            # Validate coordinate system
            if not self.validator.validate_point(self.coordinate_system.origin):
                logger.error("Invalid coordinate system origin")
                return False
            
            # Validate all points
            for i, point in enumerate(self.points):
                if not self.validator.validate_point(point):
                    logger.error(f"Invalid point at index {i}")
                    return False
            
            # Validate all vectors
            for i, vector in enumerate(self.vectors):
                if vector.magnitude() < 0:
                    logger.error(f"Invalid vector at index {i}")
                    return False
            
            logger.info("Precision system validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Precision system validation failed: {e}")
            return False

# Global instance for easy access
precision_drawing_system = PrecisionDrawingSystem() 