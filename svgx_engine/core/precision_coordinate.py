"""
High-Precision Coordinate System for CAD Applications

This module provides a precision coordinate system with 64-bit floating point precision
for sub-millimeter accuracy (0.001mm) required for professional CAD functionality.
"""

import math
import json
import struct
from typing import Tuple, Optional, Union, List
from decimal import Decimal, getcontext
from dataclasses import dataclass
import numpy as np

# Configure decimal precision for sub-millimeter accuracy
getcontext().prec = 10  # 10 decimal places for 0.001mm precision


@dataclass
class PrecisionCoordinate:
    """
    High-precision coordinate class with 64-bit floating point precision.
    
    Provides sub-millimeter accuracy (0.001mm) for professional CAD applications.
    Uses both numpy.float64 for performance and Decimal for maximum precision.
    """
    
    x: float
    y: float
    z: float = 0.0
    
    def __post_init__(self):
        """Validate and normalize coordinates after initialization."""
        from .precision_hooks import hook_manager, HookType, HookContext
        
        # Create hook context for coordinate creation
        context = HookContext(
            operation_name="coordinate_creation",
            coordinates=[self]
        )
        
        # Execute coordinate creation hooks
        context = hook_manager.execute_hooks(HookType.COORDINATE_CREATION, context)
        
        # Validate and normalize coordinates
        self._validate_coordinates()
        self._normalize_coordinates()
        
        # Execute precision validation hooks
        context.coordinates = [self]
        hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)
    
    def _validate_coordinates(self) -> None:
        """
        Validate coordinate values for range and NaN detection.
        
        Raises:
            ValueError: If coordinates are NaN, infinite, or out of valid range
        """
        # Check for NaN values
        if (math.isnan(self.x) or math.isnan(self.y) or math.isnan(self.z)):
            raise ValueError("Coordinate values cannot be NaN")
        
        # Check for infinite values
        if (math.isinf(self.x) or math.isinf(self.y) or math.isinf(self.z)):
            raise ValueError("Coordinate values cannot be infinite")
        
        # Check for reasonable range (adjust based on application needs)
        max_coordinate = 1e6  # 1 million units
        if (abs(self.x) > max_coordinate or 
            abs(self.y) > max_coordinate or 
            abs(self.z) > max_coordinate):
            raise ValueError(f"Coordinate values exceed maximum range of {max_coordinate}")
    
    def _normalize_coordinates(self) -> None:
        """
        Normalize coordinates to ensure consistent precision.
        Converts to numpy.float64 for performance while maintaining precision.
        """
        self.x = np.float64(self.x)
        self.y = np.float64(self.y)
        self.z = np.float64(self.z)
    
    @property
    def as_tuple(self) -> Tuple[float, float, float]:
        """Return coordinates as a tuple."""
        return (self.x, self.y, self.z)
    
    @property
    def as_list(self) -> List[float]:
        """Return coordinates as a list."""
        return [self.x, self.y, self.z]
    
    @property
    def magnitude(self) -> float:
        """Calculate the magnitude (distance from origin) of the coordinate."""
        return np.sqrt(self.x**2 + self.y**2 + self.z**2)
    
    def distance_to(self, other: 'PrecisionCoordinate') -> float:
        """
        Calculate the distance to another coordinate.
        
        Args:
            other: Another PrecisionCoordinate instance
            
        Returns:
            float: Distance between the two coordinates
        """
        if not isinstance(other, PrecisionCoordinate):
            raise TypeError("other must be a PrecisionCoordinate instance")
        
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return np.sqrt(dx**2 + dy**2 + dz**2)
    
    def transform(self, scale: float = 1.0, 
                 rotation: float = 0.0, 
                 translation: Optional[Tuple[float, float, float]] = None) -> 'PrecisionCoordinate':
        """
        Apply transformation to the coordinate.
        
        Args:
            scale: Scale factor (default: 1.0)
            rotation: Rotation angle in radians (default: 0.0)
            translation: Translation vector (dx, dy, dz) (default: None)
            
        Returns:
            PrecisionCoordinate: Transformed coordinate
        """
        from .precision_hooks import hook_manager, HookType, HookContext
        from .precision_errors import handle_precision_error, PrecisionErrorType, PrecisionErrorSeverity
        
        # Create hook context for coordinate transformation
        transformation_data = {
            'scale': scale,
            'rotation': rotation,
            'translation': translation
        }
        
        context = HookContext(
            operation_name="coordinate_transformation",
            coordinates=[self],
            transformation_data=transformation_data
        )
        
        # Execute coordinate transformation hooks
        context = hook_manager.execute_hooks(HookType.COORDINATE_TRANSFORMATION, context)
        
        try:
            # Apply scaling
            new_x = self.x * scale
            new_y = self.y * scale
            new_z = self.z * scale
            
            # Apply rotation (2D rotation around Z-axis)
            if rotation != 0.0:
                cos_r = np.cos(rotation)
                sin_r = np.sin(rotation)
                old_x, old_y = new_x, new_y
                new_x = old_x * cos_r - old_y * sin_r
                new_y = old_x * sin_r + old_y * cos_r
            
            # Apply translation
            if translation is not None:
                dx, dy, dz = translation
                new_x += dx
                new_y += dy
                new_z += dz
            
            transformed_coord = PrecisionCoordinate(new_x, new_y, new_z)
            
            # Execute precision validation hooks on transformed coordinate
            context.coordinates = [transformed_coord]
            hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)
            
            return transformed_coord
            
        except Exception as e:
            # Handle transformation error
            handle_precision_error(
                error_type=PrecisionErrorType.TRANSFORMATION_ERROR,
                message=f"Coordinate transformation failed: {str(e)}",
                operation="coordinate_transformation",
                coordinates=[self],
                context=transformation_data,
                severity=PrecisionErrorSeverity.ERROR
            )
            raise
    
    def scale(self, factor: float) -> 'PrecisionCoordinate':
        """
        Scale the coordinate by a factor.
        
        Args:
            factor: Scale factor
            
        Returns:
            PrecisionCoordinate: Scaled coordinate
        """
        return PrecisionCoordinate(
            self.x * factor,
            self.y * factor,
            self.z * factor
        )
    
    def rotate(self, angle: float, center: Optional['PrecisionCoordinate'] = None) -> 'PrecisionCoordinate':
        """
        Rotate the coordinate around a center point.
        
        Args:
            angle: Rotation angle in radians
            center: Center point for rotation (default: origin)
            
        Returns:
            PrecisionCoordinate: Rotated coordinate
        """
        if center is None:
            center = PrecisionCoordinate(0.0, 0.0, 0.0)
        
        # Translate to origin
        dx = self.x - center.x
        dy = self.y - center.y
        
        # Apply rotation
        cos_a = np.cos(angle)
        sin_a = np.sin(angle)
        new_x = dx * cos_a - dy * sin_a
        new_y = dx * sin_a + dy * cos_a
        
        # Translate back
        return PrecisionCoordinate(
            new_x + center.x,
            new_y + center.y,
            self.z
        )
    
    def translate(self, dx: float, dy: float, dz: float = 0.0) -> 'PrecisionCoordinate':
        """
        Translate the coordinate by the given offsets.
        
        Args:
            dx: X translation offset
            dy: Y translation offset
            dz: Z translation offset (default: 0.0)
            
        Returns:
            PrecisionCoordinate: Translated coordinate
        """
        return PrecisionCoordinate(
            self.x + dx,
            self.y + dy,
            self.z + dz
        )
    
    def __eq__(self, other: object) -> bool:
        """Compare coordinates for equality with tolerance."""
        if not isinstance(other, PrecisionCoordinate):
            return False
        return self.distance_to(other) < self._get_tolerance()
    
    def __lt__(self, other: 'PrecisionCoordinate') -> bool:
        """Compare coordinates for ordering (lexicographic)."""
        if not isinstance(other, PrecisionCoordinate):
            raise TypeError("Can only compare with other PrecisionCoordinate instances")
        
        if self.x != other.x:
            return self.x < other.x
        if self.y != other.y:
            return self.y < other.y
        return self.z < other.z
    
    def __hash__(self) -> int:
        """Hash the coordinate for use in sets and dictionaries."""
        return hash((self.x, self.y, self.z))
    
    def __repr__(self) -> str:
        """String representation of the coordinate."""
        return f"PrecisionCoordinate(x={self.x:.6f}, y={self.y:.6f}, z={self.z:.6f})"
    
    def __str__(self) -> str:
        """User-friendly string representation."""
        return f"({self.x:.6f}, {self.y:.6f}, {self.z:.6f})"
    
    def _get_tolerance(self) -> float:
        """Get the tolerance for coordinate comparisons."""
        return 1e-6  # 0.001mm tolerance
    
    def is_close_to(self, other: 'PrecisionCoordinate', tolerance: Optional[float] = None) -> bool:
        """
        Check if this coordinate is close to another within tolerance.
        
        Args:
            other: Another PrecisionCoordinate instance
            tolerance: Custom tolerance (default: system tolerance)
            
        Returns:
            bool: True if coordinates are within tolerance
        """
        if tolerance is None:
            tolerance = self._get_tolerance()
        
        return self.distance_to(other) <= tolerance
    
    def to_dict(self) -> dict:
        """Convert coordinate to dictionary for serialization."""
        return {
            'x': float(self.x),
            'y': float(self.y),
            'z': float(self.z),
            'type': 'PrecisionCoordinate'
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PrecisionCoordinate':
        """Create coordinate from dictionary."""
        if data.get('type') != 'PrecisionCoordinate':
            raise ValueError("Invalid coordinate data")
        
        return cls(
            x=data['x'],
            y=data['y'],
            z=data.get('z', 0.0)
        )
    
    def serialize(self) -> bytes:
        """Serialize coordinate to bytes for storage/transmission."""
        return struct.pack('ddd', self.x, self.y, self.z)
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'PrecisionCoordinate':
        """Deserialize coordinate from bytes."""
        if len(data) != 24:  # 3 * 8 bytes for double precision
            raise ValueError("Invalid serialized coordinate data")
        
        x, y, z = struct.unpack('ddd', data)
        return cls(x, y, z)
    
    def to_json(self) -> str:
        """Convert coordinate to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'PrecisionCoordinate':
        """Create coordinate from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


class CoordinateValidator:
    """Utility class for coordinate validation operations."""
    
    @staticmethod
    def validate_coordinate_range(coordinate: PrecisionCoordinate, 
                                min_range: float = -1e6, 
                                max_range: float = 1e6) -> bool:
        """
        Validate that coordinate is within specified range.
        
        Args:
            coordinate: Coordinate to validate
            min_range: Minimum allowed value
            max_range: Maximum allowed value
            
        Returns:
            bool: True if coordinate is within range
        """
        return (min_range <= coordinate.x <= max_range and
                min_range <= coordinate.y <= max_range and
                min_range <= coordinate.z <= max_range)
    
    @staticmethod
    def validate_coordinate_precision(coordinate: PrecisionCoordinate, 
                                   max_precision: float = 1e-6) -> bool:
        """
        Validate coordinate precision.
        
        Args:
            coordinate: Coordinate to validate
            max_precision: Maximum allowed precision error
            
        Returns:
            bool: True if coordinate meets precision requirements
        """
        # Check if coordinate values can be represented with required precision
        x_prec = abs(coordinate.x - round(coordinate.x / max_precision) * max_precision)
        y_prec = abs(coordinate.y - round(coordinate.y / max_precision) * max_precision)
        z_prec = abs(coordinate.z - round(coordinate.z / max_precision) * max_precision)
        
        return x_prec <= max_precision and y_prec <= max_precision and z_prec <= max_precision


class CoordinateTransformation:
    """Utility class for coordinate transformation operations with precision validation."""
    
    def __init__(self, config: Optional['PrecisionConfig'] = None):
        """
        Initialize coordinate transformation with precision configuration.
        
        Args:
            config: Precision configuration (optional)
        """
        from .precision_config import config_manager
        from .precision_math import PrecisionMath
        
        self.config = config or config_manager.get_default_config()
        self.precision_math = PrecisionMath()
    
    def create_transformation_matrix(self, scale: float = 1.0,
                                  rotation: float = 0.0,
                                  translation: Tuple[float, float, float] = (0.0, 0.0, 0.0)) -> np.ndarray:
        """
        Create a 4x4 transformation matrix with precision validation.
        
        Args:
            scale: Scale factor
            rotation: Rotation angle in radians
            translation: Translation vector (dx, dy, dz)
            
        Returns:
            np.ndarray: 4x4 transformation matrix
        """
        from .precision_hooks import hook_manager, HookType, HookContext
        from .precision_errors import handle_precision_error, PrecisionErrorType, PrecisionErrorSeverity
        
        # Create hook context for matrix creation
        matrix_data = {
            'scale': scale,
            'rotation': rotation,
            'translation': translation,
            'operation_type': 'matrix_creation'
        }
        
        context = HookContext(
            operation_name="transformation_matrix_creation",
            coordinates=[],
            constraint_data=matrix_data
        )
        
        # Execute geometric constraint hooks
        context = hook_manager.execute_hooks(HookType.GEOMETRIC_CONSTRAINT, context)
        
        try:
            # Validate transformation parameters
            if self.config.enable_geometric_validation:
                if scale <= 0:
                    handle_precision_error(
                        error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                        message=f"Invalid scale factor: {scale} (must be positive)",
                        operation="transformation_matrix_creation",
                        coordinates=[],
                        context=matrix_data,
                        severity=PrecisionErrorSeverity.ERROR
                    )
                    raise ValueError(f"Scale factor must be positive, got {scale}")
                
                if abs(rotation) > 2 * np.pi:
                    handle_precision_error(
                        error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                        message=f"Rotation angle {rotation} is outside valid range [-2π, 2π]",
                        operation="transformation_matrix_creation",
                        coordinates=[],
                        context=matrix_data,
                        severity=PrecisionErrorSeverity.WARNING
                    )
            
            # Use precision math for trigonometric calculations
            cos_r = self.precision_math.cos(rotation)
            sin_r = self.precision_math.sin(rotation)
            dx, dy, dz = translation
            
            # Create transformation matrix with precision
            matrix = np.array([
                [scale * cos_r, -scale * sin_r, 0, dx],
                [scale * sin_r, scale * cos_r, 0, dy],
                [0, 0, scale, dz],
                [0, 0, 0, 1]
            ], dtype=np.float64)
            
            # Execute precision validation hooks
            hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)
            
            return matrix
            
        except Exception as e:
            # Handle matrix creation error
            handle_precision_error(
                error_type=PrecisionErrorType.CALCULATION_ERROR,
                message=f"Transformation matrix creation failed: {str(e)}",
                operation="transformation_matrix_creation",
                coordinates=[],
                context=matrix_data,
                severity=PrecisionErrorSeverity.ERROR
            )
            raise
    
    def apply_transformation(self, coordinate: PrecisionCoordinate, 
                           matrix: np.ndarray) -> PrecisionCoordinate:
        """
        Apply transformation matrix to coordinate with precision validation.
        
        Args:
            coordinate: Coordinate to transform
            matrix: 4x4 transformation matrix
            
        Returns:
            PrecisionCoordinate: Transformed coordinate
        """
        from .precision_hooks import hook_manager, HookType, HookContext
        from .precision_errors import handle_precision_error, PrecisionErrorType, PrecisionErrorSeverity
        
        # Create hook context for transformation application
        transformation_data = {
            'matrix_shape': matrix.shape,
            'original_coordinate': coordinate.as_tuple,
            'operation_type': 'coordinate_transformation'
        }
        
        context = HookContext(
            operation_name="coordinate_transformation_application",
            coordinates=[coordinate],
            constraint_data=transformation_data
        )
        
        # Execute geometric constraint hooks
        context = hook_manager.execute_hooks(HookType.GEOMETRIC_CONSTRAINT, context)
        
        try:
            # Validate matrix
            if matrix.shape != (4, 4):
                handle_precision_error(
                    error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                    message=f"Invalid transformation matrix shape: {matrix.shape} (expected (4, 4))",
                    operation="coordinate_transformation_application",
                    coordinates=[coordinate],
                    context=transformation_data,
                    severity=PrecisionErrorSeverity.ERROR
                )
                raise ValueError(f"Transformation matrix must be 4x4, got {matrix.shape}")
            
            # Convert coordinate to homogeneous coordinates with precision
            point = np.array([
                self.precision_math.to_float(coordinate.x),
                self.precision_math.to_float(coordinate.y),
                self.precision_math.to_float(coordinate.z),
                1.0
            ], dtype=np.float64)
            
            # Apply transformation with precision
            transformed = matrix @ point
            
            # Create new coordinate with precision validation
            transformed_coord = PrecisionCoordinate(
                transformed[0], 
                transformed[1], 
                transformed[2]
            )
            
            # Execute precision validation hooks
            context.coordinates = [transformed_coord]
            hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)
            
            # Validate transformed coordinate
            if self.config.enable_geometric_validation:
                max_coordinate = self.config.validation_rules.get('max_coordinate', 1e6)
                if (abs(transformed_coord.x) > max_coordinate or 
                    abs(transformed_coord.y) > max_coordinate or 
                    abs(transformed_coord.z) > max_coordinate):
                    handle_precision_error(
                        error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                        message=f"Transformed coordinate {transformed_coord} exceeds maximum range {max_coordinate}",
                        operation="coordinate_transformation_application",
                        coordinates=[transformed_coord],
                        context=transformation_data,
                        severity=PrecisionErrorSeverity.WARNING
                    )
            
            return transformed_coord
            
        except Exception as e:
            # Handle transformation error
            handle_precision_error(
                error_type=PrecisionErrorType.TRANSFORMATION_ERROR,
                message=f"Coordinate transformation failed: {str(e)}",
                operation="coordinate_transformation_application",
                coordinates=[coordinate],
                context=transformation_data,
                severity=PrecisionErrorSeverity.ERROR
            )
            raise
    
    def scale_coordinate(self, coordinate: PrecisionCoordinate, 
                        scale_factor: float) -> PrecisionCoordinate:
        """
        Scale a coordinate with precision validation.
        
        Args:
            coordinate: Coordinate to scale
            scale_factor: Scale factor
            
        Returns:
            PrecisionCoordinate: Scaled coordinate
        """
        from .precision_hooks import hook_manager, HookType, HookContext
        from .precision_errors import handle_precision_error, PrecisionErrorType, PrecisionErrorSeverity
        
        # Create hook context for scaling
        scaling_data = {
            'scale_factor': scale_factor,
            'operation_type': 'coordinate_scaling'
        }
        
        context = HookContext(
            operation_name="coordinate_scaling",
            coordinates=[coordinate],
            constraint_data=scaling_data
        )
        
        # Execute geometric constraint hooks
        context = hook_manager.execute_hooks(HookType.GEOMETRIC_CONSTRAINT, context)
        
        try:
            # Validate scale factor
            if self.config.enable_geometric_validation and scale_factor <= 0:
                handle_precision_error(
                    error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                    message=f"Invalid scale factor: {scale_factor} (must be positive)",
                    operation="coordinate_scaling",
                    coordinates=[coordinate],
                    context=scaling_data,
                    severity=PrecisionErrorSeverity.ERROR
                )
                raise ValueError(f"Scale factor must be positive, got {scale_factor}")
            
            # Apply scaling with precision math
            new_x = self.precision_math.multiply(coordinate.x, scale_factor)
            new_y = self.precision_math.multiply(coordinate.y, scale_factor)
            new_z = self.precision_math.multiply(coordinate.z, scale_factor)
            
            scaled_coord = PrecisionCoordinate(new_x, new_y, new_z)
            
            # Execute precision validation hooks
            context.coordinates = [scaled_coord]
            hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)
            
            return scaled_coord
            
        except Exception as e:
            # Handle scaling error
            handle_precision_error(
                error_type=PrecisionErrorType.TRANSFORMATION_ERROR,
                message=f"Coordinate scaling failed: {str(e)}",
                operation="coordinate_scaling",
                coordinates=[coordinate],
                context=scaling_data,
                severity=PrecisionErrorSeverity.ERROR
            )
            raise
    
    def rotate_coordinate(self, coordinate: PrecisionCoordinate, 
                         angle: float, 
                         center: Optional[PrecisionCoordinate] = None) -> PrecisionCoordinate:
        """
        Rotate a coordinate around a center point with precision validation.
        
        Args:
            coordinate: Coordinate to rotate
            angle: Rotation angle in radians
            center: Center point for rotation (default: origin)
            
        Returns:
            PrecisionCoordinate: Rotated coordinate
        """
        from .precision_hooks import hook_manager, HookType, HookContext
        from .precision_errors import handle_precision_error, PrecisionErrorType, PrecisionErrorSeverity
        
        if center is None:
            center = PrecisionCoordinate(0.0, 0.0, 0.0)
        
        # Create hook context for rotation
        rotation_data = {
            'angle': angle,
            'center': center.as_tuple,
            'operation_type': 'coordinate_rotation'
        }
        
        context = HookContext(
            operation_name="coordinate_rotation",
            coordinates=[coordinate, center],
            constraint_data=rotation_data
        )
        
        # Execute geometric constraint hooks
        context = hook_manager.execute_hooks(HookType.GEOMETRIC_CONSTRAINT, context)
        
        try:
            # Validate rotation angle
            if self.config.enable_geometric_validation and abs(angle) > 2 * np.pi:
                handle_precision_error(
                    error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                    message=f"Rotation angle {angle} is outside valid range [-2π, 2π]",
                    operation="coordinate_rotation",
                    coordinates=[coordinate, center],
                    context=rotation_data,
                    severity=PrecisionErrorSeverity.WARNING
                )
            
            # Translate to origin
            dx = self.precision_math.subtract(coordinate.x, center.x)
            dy = self.precision_math.subtract(coordinate.y, center.y)
            
            # Apply rotation with precision math
            cos_a = self.precision_math.cos(angle)
            sin_a = self.precision_math.sin(angle)
            
            new_x = self.precision_math.subtract(
                self.precision_math.multiply(dx, cos_a),
                self.precision_math.multiply(dy, sin_a)
            )
            new_y = self.precision_math.add(
                self.precision_math.multiply(dx, sin_a),
                self.precision_math.multiply(dy, cos_a)
            )
            
            # Translate back
            final_x = self.precision_math.add(new_x, center.x)
            final_y = self.precision_math.add(new_y, center.y)
            
            rotated_coord = PrecisionCoordinate(final_x, final_y, coordinate.z)
            
            # Execute precision validation hooks
            context.coordinates = [rotated_coord]
            hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)
            
            return rotated_coord
            
        except Exception as e:
            # Handle rotation error
            handle_precision_error(
                error_type=PrecisionErrorType.TRANSFORMATION_ERROR,
                message=f"Coordinate rotation failed: {str(e)}",
                operation="coordinate_rotation",
                coordinates=[coordinate, center],
                context=rotation_data,
                severity=PrecisionErrorSeverity.ERROR
            )
            raise
    
    def translate_coordinate(self, coordinate: PrecisionCoordinate, 
                           dx: float, dy: float, dz: float = 0.0) -> PrecisionCoordinate:
        """
        Translate a coordinate with precision validation.
        
        Args:
            coordinate: Coordinate to translate
            dx: X translation offset
            dy: Y translation offset
            dz: Z translation offset (default: 0.0)
            
        Returns:
            PrecisionCoordinate: Translated coordinate
        """
        from .precision_hooks import hook_manager, HookType, HookContext
        from .precision_errors import handle_precision_error, PrecisionErrorType, PrecisionErrorSeverity
        
        # Create hook context for translation
        translation_data = {
            'translation': (dx, dy, dz),
            'operation_type': 'coordinate_translation'
        }
        
        context = HookContext(
            operation_name="coordinate_translation",
            coordinates=[coordinate],
            constraint_data=translation_data
        )
        
        # Execute geometric constraint hooks
        context = hook_manager.execute_hooks(HookType.GEOMETRIC_CONSTRAINT, context)
        
        try:
            # Apply translation with precision math
            new_x = self.precision_math.add(coordinate.x, dx)
            new_y = self.precision_math.add(coordinate.y, dy)
            new_z = self.precision_math.add(coordinate.z, dz)
            
            translated_coord = PrecisionCoordinate(new_x, new_y, new_z)
            
            # Execute precision validation hooks
            context.coordinates = [translated_coord]
            hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)
            
            return translated_coord
            
        except Exception as e:
            # Handle translation error
            handle_precision_error(
                error_type=PrecisionErrorType.TRANSFORMATION_ERROR,
                message=f"Coordinate translation failed: {str(e)}",
                operation="coordinate_translation",
                coordinates=[coordinate],
                context=translation_data,
                severity=PrecisionErrorSeverity.ERROR
            )
            raise


# Example usage and testing
if __name__ == "__main__":
    # Test coordinate creation and validation
    coord1 = PrecisionCoordinate(1.0, 2.0, 3.0)
    coord2 = PrecisionCoordinate(1.000001, 2.000001, 3.000001)
    
    print(f"Coordinate 1: {coord1}")
    print(f"Coordinate 2: {coord2}")
    print(f"Distance between coordinates: {coord1.distance_to(coord2):.6f}")
    print(f"Coordinates are close: {coord1.is_close_to(coord2)}")
    
    # Test transformations
    transformed = coord1.transform(scale=2.0, rotation=math.pi/4, translation=(1.0, 1.0, 0.0))
    print(f"Transformed coordinate: {transformed}")
    
    # Test serialization
    serialized = coord1.serialize()
    deserialized = PrecisionCoordinate.deserialize(serialized)
    print(f"Serialization test: {coord1 == deserialized}")
    
    # Test JSON serialization
    json_str = coord1.to_json()
    from_json = PrecisionCoordinate.from_json(json_str)
    print(f"JSON serialization test: {coord1 == from_json}") 