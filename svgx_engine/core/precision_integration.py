"""
Precision System Integration Utilities

This module provides integration utilities for connecting the precision system
with the geometry engine, including adapters and factory functions.
"""

import logging
from typing import Dict, Any, List, Tuple, Optional, Union
from dataclasses import dataclass

from .precision_coordinate import PrecisionCoordinate, CoordinateValidator
from .precision_math import PrecisionMath
from .precision_validator import PrecisionValidator, ValidationLevel, ValidationType
from .precision_input import PrecisionInputHandler, InputType, InputMode
from .precision_config import PrecisionConfig, config_manager

logger = logging.getLogger(__name__)


@dataclass
class PrecisionGeometryAdapter:
    """Adapter for converting between precision types and legacy geometry types"""

    config: PrecisionConfig

    def __post_init__(self):
        """Initialize precision components"""
        self.coordinate_validator = CoordinateValidator()
        self.precision_math = PrecisionMath()
        self.precision_validator = PrecisionValidator()
        self.input_handler = PrecisionInputHandler()

    def to_precision_coordinate(self, x: float, y: float, z: float = 0.0) -> PrecisionCoordinate:
        """Convert legacy coordinates to PrecisionCoordinate"""
        try:
            coord = PrecisionCoordinate(x, y, z)

            # Validate coordinate
            if self.config.enable_coordinate_validation:
                validation_result = self.coordinate_validator.validate_coordinate(coord)
                if not validation_result.is_valid:
                    if self.config.should_fail_on_violation():
                        raise ValueError(f"Invalid coordinate: {validation_result.errors}")
                    elif self.config.auto_correct_precision_errors:
                        coord = self._correct_coordinate(coord, validation_result)

            return coord
        except Exception as e:
            logger.error(f"Failed to convert to precision coordinate: {e}")
            raise

    def from_precision_coordinate(self, coord: PrecisionCoordinate) -> Tuple[float, float, float]:
        """Convert PrecisionCoordinate to legacy tuple format"""
        return (coord.x, coord.y, coord.z)

    def to_precision_coordinates(self, coords: List[List[float]]) -> List[PrecisionCoordinate]:
        """Convert list of legacy coordinates to PrecisionCoordinate list"""
        precision_coords = []
        for coord in coords:
            if len(coord) >= 2:
                z = coord[2] if len(coord) > 2 else 0.0
                precision_coords.append(self.to_precision_coordinate(coord[0], coord[1], z))
        return precision_coords

    def from_precision_coordinates(self, coords: List[PrecisionCoordinate]) -> List[List[float]]:
        """Convert list of PrecisionCoordinate to legacy format"""
        return [self.from_precision_coordinate(coord) for coord in coords]

    def _correct_coordinate(self, coord: PrecisionCoordinate, validation_result) -> PrecisionCoordinate:
        """Correct coordinate based on validation result"""
        # Simple correction: round to precision level
        precision_value = self.config.get_precision_value()
        corrected_x = round(coord.x / precision_value) * precision_value
        corrected_y = round(coord.y / precision_value) * precision_value
        corrected_z = round(coord.z / precision_value) * precision_value

        return PrecisionCoordinate(corrected_x, corrected_y, corrected_z)


@dataclass
class PrecisionGeometryFactory:
    """Factory for creating precision-aware geometric objects"""

    config: PrecisionConfig
    adapter: PrecisionGeometryAdapter

    def __post_init__(self):
        """Initialize factory components"""
        self.precision_math = PrecisionMath()
        self.precision_validator = PrecisionValidator()

    def create_point_2d(self, x: float, y: float) -> Dict[str, Any]:
        """Create a 2D point with precision"""
        coord = self.adapter.to_precision_coordinate(x, y, 0.0)

        return {
            'type': 'point_2d',
            'coordinates': self.adapter.from_precision_coordinate(coord),
            'precision_coordinate': coord,
            'precision_level': self.config.precision_level.value,
            'validation_status': 'valid'
        }

    def create_point_3d(self, x: float, y: float, z: float) -> Dict[str, Any]:
        """Create a 3D point with precision"""
        coord = self.adapter.to_precision_coordinate(x, y, z)

        return {
            'type': 'point_3d',
            'coordinates': self.adapter.from_precision_coordinate(coord),
            'precision_coordinate': coord,
            'precision_level': self.config.precision_level.value,
            'validation_status': 'valid'
        }

    def create_line_2d(self, start_x: float, start_y: float,
                       end_x: float, end_y: float) -> Dict[str, Any]:
        """Create a 2D line with precision"""
        start_coord = self.adapter.to_precision_coordinate(start_x, start_y, 0.0)
        end_coord = self.adapter.to_precision_coordinate(end_x, end_y, 0.0)

        # Calculate length with precision
        length = self.precision_math.distance(start_coord, end_coord)

        return {
            'type': 'line_2d',
            'coordinates': [
                self.adapter.from_precision_coordinate(start_coord),
                self.adapter.from_precision_coordinate(end_coord)
            ],
            'precision_coordinates': [start_coord, end_coord],
            'length': length,
            'precision_level': self.config.precision_level.value,
            'validation_status': 'valid'
        }

    def create_polygon_2d(self, coordinates: List[List[float]]) -> Dict[str, Any]:
        """Create a 2D polygon with precision"""
        precision_coords = self.adapter.to_precision_coordinates(coordinates)

        # Calculate area and perimeter with precision
        area = self._calculate_polygon_area(precision_coords)
        perimeter = self._calculate_polygon_perimeter(precision_coords)

        return {
            'type': 'polygon_2d',
            'coordinates': self.adapter.from_precision_coordinates(precision_coords),
            'precision_coordinates': precision_coords,
            'area': area,
            'perimeter': perimeter,
            'precision_level': self.config.precision_level.value,
            'validation_status': 'valid'
        }

    def create_circle_2d(self, center_x: float, center_y: float, radius: float) -> Dict[str, Any]:
        """Create a 2D circle with precision"""
        center_coord = self.adapter.to_precision_coordinate(center_x, center_y, 0.0)

        # Calculate area and perimeter with precision
        area = self.precision_math.multiply(
            self.precision_math.multiply(radius, radius),
            self.precision_math.pi()
        )
        perimeter = self.precision_math.multiply(
            self.precision_math.multiply(radius, 2),
            self.precision_math.pi()
        )

        return {
            'type': 'circle_2d',
            'center': self.adapter.from_precision_coordinate(center_coord),
            'radius': radius,
            'precision_center': center_coord,
            'area': area,
            'perimeter': perimeter,
            'precision_level': self.config.precision_level.value,
            'validation_status': 'valid'
        }

    def create_rectangle_2d(self, x: float, y: float, width: float, height: float) -> Dict[str, Any]:
        """Create a 2D rectangle with precision"""
        # Create corner points
        corners = [
            self.adapter.to_precision_coordinate(x, y, 0.0),
            self.adapter.to_precision_coordinate(x + width, y, 0.0),
            self.adapter.to_precision_coordinate(x + width, y + height, 0.0),
            self.adapter.to_precision_coordinate(x, y + height, 0.0)
        ]

        # Calculate area and perimeter
        area = self.precision_math.multiply(width, height)
        perimeter = self.precision_math.multiply(
            self.precision_math.add(width, height),
            2
        )

        return {
            'type': 'rectangle_2d',
            'position': [x, y],
            'size': [width, height],
            'precision_corners': corners,
            'area': area,
            'perimeter': perimeter,
            'precision_level': self.config.precision_level.value,
            'validation_status': 'valid'
        }

    def _calculate_polygon_area(self, coordinates: List[PrecisionCoordinate]) -> float:
        """Calculate polygon area using precision math"""
        if len(coordinates) < 3:
            return 0.0

        area = 0.0
        for i in range(len(coordinates)):
            j = (i + 1) % len(coordinates)
            area = self.precision_math.add(
                area,
                self.precision_math.multiply(coordinates[i].x, coordinates[j].y)
            )
            area = self.precision_math.subtract(
                area,
                self.precision_math.multiply(coordinates[j].x, coordinates[i].y)
            )

        return abs(area) / 2.0

    def _calculate_polygon_perimeter(self, coordinates: List[PrecisionCoordinate]) -> float:
        """Calculate polygon perimeter using precision math"""
        if len(coordinates) < 2:
            return 0.0

        perimeter = 0.0
        for i in range(len(coordinates) - 1):
            perimeter = self.precision_math.add(
                perimeter,
                self.precision_math.distance(coordinates[i], coordinates[i + 1])
            )

        # Close the polygon if needed
        if len(coordinates) > 2:
            perimeter = self.precision_math.add(
                perimeter,
                self.precision_math.distance(coordinates[-1], coordinates[0])
            )

        return perimeter


@dataclass
class PrecisionGeometryTransformer:
    """Transformer for precision-aware geometric transformations"""

    config: PrecisionConfig
    adapter: PrecisionGeometryAdapter

    def __post_init__(self):
        """Initialize transformer components"""
        self.precision_math = PrecisionMath()
        self.precision_validator = PrecisionValidator()

    def translate(self, geometry: Dict[str, Any], dx: float, dy: float, dz: float = 0.0) -> Dict[str, Any]:
        """Translate geometry with precision"""
        translation_coord = self.adapter.to_precision_coordinate(dx, dy, dz)

        if 'precision_coordinates' in geometry:
            # Transform precision coordinates
            transformed_coords = []
            for coord in geometry['precision_coordinates']:
                transformed_coord = coord.transform(translation_coord)
                transformed_coords.append(transformed_coord)

            # Update geometry
            geometry['precision_coordinates'] = transformed_coords
            geometry['coordinates'] = self.adapter.from_precision_coordinates(transformed_coords)

        elif 'precision_coordinate' in geometry:
            # Transform single coordinate
            transformed_coord = geometry['precision_coordinate'].transform(translation_coord)
            geometry['precision_coordinate'] = transformed_coord
            geometry['coordinates'] = self.adapter.from_precision_coordinate(transformed_coord)

        return geometry

    def scale(self, geometry: Dict[str, Any], scale_x: float, scale_y: float, scale_z: float = 1.0) -> Dict[str, Any]:
        """Scale geometry with precision"""
        scale_coord = self.adapter.to_precision_coordinate(scale_x, scale_y, scale_z)

        if 'precision_coordinates' in geometry:
            # Scale precision coordinates
            scaled_coords = []
            for coord in geometry['precision_coordinates']:
                scaled_coord = PrecisionCoordinate(
                    self.precision_math.multiply(coord.x, scale_coord.x),
                    self.precision_math.multiply(coord.y, scale_coord.y),
                    self.precision_math.multiply(coord.z, scale_coord.z)
                )
                scaled_coords.append(scaled_coord)

            # Update geometry
            geometry['precision_coordinates'] = scaled_coords
            geometry['coordinates'] = self.adapter.from_precision_coordinates(scaled_coords)

        elif 'precision_coordinate' in geometry:
            # Scale single coordinate
            coord = geometry['precision_coordinate']
            scaled_coord = PrecisionCoordinate(
                self.precision_math.multiply(coord.x, scale_coord.x),
                self.precision_math.multiply(coord.y, scale_coord.y),
                self.precision_math.multiply(coord.z, scale_coord.z)
            )
            geometry['precision_coordinate'] = scaled_coord
            geometry['coordinates'] = self.adapter.from_precision_coordinate(scaled_coord)

        return geometry

    def rotate(self, geometry: Dict[str, Any], angle_degrees: float, center_x: float = 0.0, center_y: float = 0.0) -> Dict[str, Any]:
        """Rotate geometry with precision"""
        center_coord = self.adapter.to_precision_coordinate(center_x, center_y, 0.0)
        angle_radians = self.precision_math.multiply(angle_degrees, self.precision_math.pi() / 180.0)

        if 'precision_coordinates' in geometry:
            # Rotate precision coordinates
            rotated_coords = []
            for coord in geometry['precision_coordinates']:
                rotated_coord = self._rotate_coordinate(coord, center_coord, angle_radians)
                rotated_coords.append(rotated_coord)

            # Update geometry
            geometry['precision_coordinates'] = rotated_coords
            geometry['coordinates'] = self.adapter.from_precision_coordinates(rotated_coords)

        elif 'precision_coordinate' in geometry:
            # Rotate single coordinate
            rotated_coord = self._rotate_coordinate(geometry['precision_coordinate'], center_coord, angle_radians)
            geometry['precision_coordinate'] = rotated_coord
            geometry['coordinates'] = self.adapter.from_precision_coordinate(rotated_coord)

        return geometry

    def _rotate_coordinate(self, coord: PrecisionCoordinate, center: PrecisionCoordinate, angle: float) -> PrecisionCoordinate:
        """Rotate a coordinate around a center point"""
        # Translate to origin
        dx = self.precision_math.subtract(coord.x, center.x)
        dy = self.precision_math.subtract(coord.y, center.y)

        # Rotate
        cos_angle = self.precision_math.cos(angle)
        sin_angle = self.precision_math.sin(angle)

        new_x = self.precision_math.subtract(
            self.precision_math.multiply(dx, cos_angle),
            self.precision_math.multiply(dy, sin_angle)
        )
        new_y = self.precision_math.add(
            self.precision_math.multiply(dx, sin_angle),
            self.precision_math.multiply(dy, cos_angle)
        )

        # Translate back
        final_x = self.precision_math.add(new_x, center.x)
        final_y = self.precision_math.add(new_y, center.y)

        return PrecisionCoordinate(final_x, final_y, coord.z)


@dataclass
class PrecisionGeometryValidator:
    """Validator for precision-aware geometric objects"""

    config: PrecisionConfig
    adapter: PrecisionGeometryAdapter

    def __post_init__(self):
        """Initialize validator components"""
        self.precision_validator = PrecisionValidator()
        self.coordinate_validator = CoordinateValidator()

    def validate_geometry(self, geometry: Dict[str, Any]) -> Dict[str, Any]:
        """Validate geometry with precision requirements"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'precision_violations': []
        }

        try:
            # Validate coordinates
            if 'precision_coordinates' in geometry:
                for i, coord in enumerate(geometry['precision_coordinates']):
                    coord_validation = self.coordinate_validator.validate_coordinate(coord)
                    if not coord_validation.is_valid:
                        validation_result['is_valid'] = False
                        validation_result['errors'].append(f"Coordinate {i}: {coord_validation.errors}")

            elif 'precision_coordinate' in geometry:
                coord_validation = self.coordinate_validator.validate_coordinate(geometry['precision_coordinate'])
                if not coord_validation.is_valid:
                    validation_result['is_valid'] = False
                    validation_result['errors'].append(f"Coordinate: {coord_validation.errors}")

            # Validate geometric properties
            if 'area' in geometry:
                area_validation = self._validate_area(geometry['area'])
                if not area_validation['is_valid']:
                    validation_result['warnings'].append(area_validation['message'])

            if 'perimeter' in geometry:
                perimeter_validation = self._validate_perimeter(geometry['perimeter'])
                if not perimeter_validation['is_valid']:
                    validation_result['warnings'].append(perimeter_validation['message'])

            # Check precision violations
            precision_violations = self._check_precision_violations(geometry)
            if precision_violations:
                validation_result['precision_violations'] = precision_violations
                if self.config.should_fail_on_violation():
                    validation_result['is_valid'] = False

        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Validation error: {str(e)}")

        return validation_result

    def _validate_area(self, area: float) -> Dict[str, Any]:
        """Validate area value"""
        rules = self.config.validation_rules
        min_area = rules.get('min_area', 0.000001)
        max_area = rules.get('max_area', 1e12)

        if area < min_area:
            return {
                'is_valid': False,
                'message': f"Area {area} is below minimum {min_area}"
            }
        elif area > max_area:
            return {
                'is_valid': False,
                'message': f"Area {area} is above maximum {max_area}"
            }

        return {'is_valid': True, 'message': ''}

    def _validate_perimeter(self, perimeter: float) -> Dict[str, Any]:
        """Validate perimeter value"""
        rules = self.config.validation_rules
        min_perimeter = rules.get('min_perimeter', 0.001)
        max_perimeter = rules.get('max_perimeter', 1e6)

        if perimeter < min_perimeter:
            return {
                'is_valid': False,
                'message': f"Perimeter {perimeter} is below minimum {min_perimeter}"
            }
        elif perimeter > max_perimeter:
            return {
                'is_valid': False,
                'message': f"Perimeter {perimeter} is above maximum {max_perimeter}"
            }

        return {'is_valid': True, 'message': ''}

    def _check_precision_violations(self, geometry: Dict[str, Any]) -> List[str]:
        """Check for precision violations"""
        violations = []
        precision_value = self.config.get_precision_value()

        if 'precision_coordinates' in geometry:
            for i, coord in enumerate(geometry['precision_coordinates']):
                # Check if coordinates are properly rounded to precision level
                if abs(coord.x - round(coord.x / precision_value) * precision_value) > 1e-10:
                    violations.append(f"Coordinate {i} x-value not at precision level")
                if abs(coord.y - round(coord.y / precision_value) * precision_value) > 1e-10:
                    violations.append(f"Coordinate {i} y-value not at precision level")

        return violations


class PrecisionIntegrationManager:
    """Manager for precision system integration"""

    def __init__(self, config: Optional[PrecisionConfig] = None):
        """Initialize integration manager"""
        self.config = config or config_manager.get_default_config()
        self.adapter = PrecisionGeometryAdapter(self.config)
        self.factory = PrecisionGeometryFactory(self.config, self.adapter)
        self.transformer = PrecisionGeometryTransformer(self.config, self.adapter)
        self.validator = PrecisionGeometryValidator(self.config, self.adapter)

    def create_geometry(self, geometry_type: str, **kwargs) -> Dict[str, Any]:
        """Create geometry with precision"""
        try:
            if geometry_type == 'point_2d':
                return self.factory.create_point_2d(kwargs['x'], kwargs['y'])
            elif geometry_type == 'point_3d':
                return self.factory.create_point_3d(kwargs['x'], kwargs['y'], kwargs.get('z', 0.0))
            elif geometry_type == 'line_2d':
                return self.factory.create_line_2d(
                    kwargs['start_x'], kwargs['start_y'],
                    kwargs['end_x'], kwargs['end_y']
                )
            elif geometry_type == 'polygon_2d':
                return self.factory.create_polygon_2d(kwargs['coordinates'])
            elif geometry_type == 'circle_2d':
                return self.factory.create_circle_2d(
                    kwargs['center_x'], kwargs['center_y'], kwargs['radius']
                )
            elif geometry_type == 'rectangle_2d':
                return self.factory.create_rectangle_2d(
                    kwargs['x'], kwargs['y'], kwargs['width'], kwargs['height']
                )
            else:
                raise ValueError(f"Unsupported geometry type: {geometry_type}")
        except Exception as e:
            logger.error(f"Failed to create geometry {geometry_type}: {e}")
            raise

    def transform_geometry(self, geometry: Dict[str, Any], transform_type: str, **kwargs) -> Dict[str, Any]:
        """Transform geometry with precision"""
        try:
            if transform_type == 'translate':
                return self.transformer.translate(
                    geometry, kwargs['dx'], kwargs['dy'], kwargs.get('dz', 0.0)
                )
            elif transform_type == 'scale':
                return self.transformer.scale(
                    geometry, kwargs['scale_x'], kwargs['scale_y'], kwargs.get('scale_z', 1.0)
                )
            elif transform_type == 'rotate':
                return self.transformer.rotate(
                    geometry, kwargs['angle'], kwargs.get('center_x', 0.0), kwargs.get('center_y', 0.0)
                )
            else:
                raise ValueError(f"Unsupported transform type: {transform_type}")
        except Exception as e:
            logger.error(f"Failed to transform geometry: {e}")
            raise

    def validate_geometry(self, geometry: Dict[str, Any]) -> Dict[str, Any]:
        """Validate geometry with precision requirements"""
        return self.validator.validate_geometry(geometry)

    def convert_legacy_geometry(self, geometry: Dict[str, Any]) -> Dict[str, Any]:
        """Convert legacy geometry to precision-aware format"""
        try:
            geometry_type = geometry.get('type', '')

            if geometry_type in ['point_2d', 'point_3d']:
                coords = geometry.get('coordinates', [0, 0, 0])
                if len(coords) >= 2:
                    return self.create_geometry(geometry_type, x=coords[0], y=coords[1], z=coords[2] if len(coords) > 2 else 0.0)

            elif geometry_type == 'line_2d':
                coords = geometry.get('coordinates', [])
                if len(coords) >= 2:
                    start = coords[0]
                    end = coords[1]
                    return self.create_geometry(geometry_type,
                                             start_x=start[0], start_y=start[1],
                                             end_x=end[0], end_y=end[1])

            elif geometry_type in ['polygon_2d', 'polygon_3d']:
                coords = geometry.get('coordinates', [])
                return self.create_geometry('polygon_2d', coordinates=coords)

            elif geometry_type == 'circle_2d':
                center = geometry.get('center', [0, 0])
                radius = geometry.get('radius', 1.0)
                return self.create_geometry(geometry_type,
                                         center_x=center[0], center_y=center[1],
                                         radius=radius)

            elif geometry_type == 'rectangle_2d':
                x = geometry.get('x', 0)
                y = geometry.get('y', 0)
                width = geometry.get('width', 1)
                height = geometry.get('height', 1)
                return self.create_geometry(geometry_type,
                                         x=x, y=y, width=width, height=height)

            else:
                # Return as-is for unsupported types
                return geometry

        except Exception as e:
            logger.error(f"Failed to convert legacy geometry: {e}")
            return geometry


# Global integration manager instance
integration_manager = PrecisionIntegrationManager()
