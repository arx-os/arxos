"""
Geometry utility functions for BIM processing with precision support.
"""

import math
from typing import List, Tuple, Dict, Any, Optional
from models.bim import Geometry, GeometryType

# Import precision system modules
from svgx_engine.core.precision_coordinate import PrecisionCoordinate, CoordinateValidator
from svgx_engine.core.precision_math import PrecisionMath
from svgx_engine.core.precision_validator import PrecisionValidator, ValidationLevel, ValidationType
from svgx_engine.core.precision_config import PrecisionConfig, config_manager


def normalize_coordinates(coordinates: List[List[float]], 
                        scale: float = 1.0,
                        config: Optional[PrecisionConfig] = None) -> List[List[float]]:
    """
    Normalize geometry coordinates with precision.
    
    Args:
        coordinates: List of coordinate pairs
        scale: Scale factor to apply
        config: Precision configuration (optional)
        
    Returns:
        Normalized coordinates
    """
    if config is None:
        config = config_manager.get_default_config()
    
    precision_math = PrecisionMath()
    coordinate_validator = CoordinateValidator()
    
    # Implementation for coordinate normalization logic with precision
    normalized = []
    for coord in coordinates:
        if isinstance(coord, list) and len(coord) >= 2:
            # Create precision coordinate
            precision_coord = PrecisionCoordinate(coord[0], coord[1], coord[2] if len(coord) > 2 else 0.0)
            
            # Apply scale with precision
            scaled_coord = PrecisionCoordinate(
                precision_math.multiply(precision_coord.x, scale),
                precision_math.multiply(precision_coord.y, scale),
                precision_math.multiply(precision_coord.z, scale)
            )
            
            # Validate coordinate
            if config.enable_coordinate_validation:
                validation_result = coordinate_validator.validate_coordinate(scaled_coord)
                if not validation_result.is_valid:
                    if config.should_fail_on_violation():
                        raise ValueError(f"Invalid coordinate after normalization: {validation_result.errors}")
                    elif config.auto_correct_precision_errors:
                        scaled_coord = _correct_coordinate(scaled_coord, config)
            
            normalized.append([scaled_coord.x, scaled_coord.y, scaled_coord.z])
        else:
            normalized.append(coord)
    return normalized


def calculate_distance(coord1: List[float], coord2: List[float],
                      config: Optional[PrecisionConfig] = None) -> float:
    """
    Calculate distance between two coordinates with precision.
    
    Args:
        coord1: First coordinate [x, y, z]
        coord2: Second coordinate [x, y, z]
        config: Precision configuration (optional)
        
    Returns:
        Distance between coordinates
    """
    from svgx_engine.core.precision_hooks import hook_manager, HookType, HookContext
    from svgx_engine.core.precision_errors import handle_precision_error, PrecisionErrorType, PrecisionErrorSeverity
    
    if config is None:
        config = config_manager.get_default_config()
    
    precision_math = PrecisionMath()
    
    # Convert to precision coordinates
    if len(coord1) >= 2:
        precision_coord1 = PrecisionCoordinate(coord1[0], coord1[1], coord1[2] if len(coord1) > 2 else 0.0)
    else:
        raise ValueError("First coordinate must have at least 2 components")
    
    if len(coord2) >= 2:
        precision_coord2 = PrecisionCoordinate(coord2[0], coord2[1], coord2[2] if len(coord2) > 2 else 0.0)
    else:
        raise ValueError("Second coordinate must have at least 2 components")
    
    # Create hook context for distance calculation
    distance_data = {
        'calculation_type': 'distance',
        'coord1': coord1,
        'coord2': coord2
    }
    
    context = HookContext(
        operation_name="distance_calculation",
        coordinates=[precision_coord1, precision_coord2],
        constraint_data=distance_data
    )
    
    # Execute geometric constraint hooks
    context = hook_manager.execute_hooks(HookType.GEOMETRIC_CONSTRAINT, context)
    
    try:
        # Calculate distance with precision
        distance = precision_math.distance(precision_coord1, precision_coord2)
        
        # Execute precision validation hooks
        context.coordinates = [precision_coord1, precision_coord2]
        hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)
        
        # Validate distance result
        if config.enable_geometric_validation:
            min_distance = config.validation_rules.get('min_distance', 0.000001)
            max_distance = config.validation_rules.get('max_distance', 1000000.0)
            
            if distance < min_distance:
                handle_precision_error(
                    error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                    message=f"Calculated distance {distance} is below minimum threshold {min_distance}",
                    operation="distance_calculation",
                    coordinates=[precision_coord1, precision_coord2],
                    context=distance_data,
                    severity=PrecisionErrorSeverity.WARNING
                )
            
            if distance > max_distance:
                handle_precision_error(
                    error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                    message=f"Calculated distance {distance} is above maximum threshold {max_distance}",
                    operation="distance_calculation",
                    coordinates=[precision_coord1, precision_coord2],
                    context=distance_data,
                    severity=PrecisionErrorSeverity.WARNING
                )
        
        return distance
        
    except Exception as e:
        # Handle distance calculation error
        handle_precision_error(
            error_type=PrecisionErrorType.CALCULATION_ERROR,
            message=f"Distance calculation failed: {str(e)}",
            operation="distance_calculation",
            coordinates=[precision_coord1, precision_coord2],
            context=distance_data,
            severity=PrecisionErrorSeverity.ERROR
        )
        raise


def calculate_bounding_box(coordinates: List[List[float]],
                          config: Optional[PrecisionConfig] = None) -> Tuple[float, float, float, float]:
    """
    Calculate bounding box for coordinates with precision.
    
    Args:
        coordinates: List of coordinate pairs
        config: Precision configuration (optional)
        
    Returns:
        Tuple of (min_x, min_y, max_x, max_y)
    """
    from svgx_engine.core.precision_hooks import hook_manager, HookType, HookContext
    from svgx_engine.core.precision_errors import handle_precision_error, PrecisionErrorType, PrecisionErrorSeverity
    
    if config is None:
        config = config_manager.get_default_config()
    
    precision_math = PrecisionMath()
    
    if not coordinates:
        return (0, 0, 0, 0)
    
    # Convert to precision coordinates
    precision_coords = []
    for coord in coordinates:
        if len(coord) >= 2:
            precision_coords.append(PrecisionCoordinate(coord[0], coord[1], coord[2] if len(coord) > 2 else 0.0))
    
    if not precision_coords:
        return (0, 0, 0, 0)
    
    # Create hook context for bounding box calculation
    bbox_data = {
        'coordinate_count': len(precision_coords),
        'calculation_type': 'bounding_box'
    }
    
    context = HookContext(
        operation_name="bounding_box_calculation",
        coordinates=precision_coords,
        constraint_data=bbox_data
    )
    
    # Execute geometric constraint hooks
    context = hook_manager.execute_hooks(HookType.GEOMETRIC_CONSTRAINT, context)
    
    try:
        # Calculate bounds with precision
        x_coords = [coord.x for coord in precision_coords]
        y_coords = [coord.y for coord in precision_coords]
        
        min_x = min(x_coords)
        max_x = max(x_coords)
        min_y = min(y_coords)
        max_y = max(y_coords)
        
        # Execute precision validation hooks
        context.coordinates = precision_coords
        hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)
        
        # Validate bounding box result
        if config.enable_geometric_validation:
            bbox_width = max_x - min_x
            bbox_height = max_y - min_y
            
            min_bbox_size = config.validation_rules.get('min_bbox_size', 0.000001)
            max_bbox_size = config.validation_rules.get('max_bbox_size', 1000000.0)
            
            if bbox_width < min_bbox_size or bbox_height < min_bbox_size:
                handle_precision_error(
                    error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                    message=f"Bounding box size ({bbox_width}, {bbox_height}) is below minimum threshold {min_bbox_size}",
                    operation="bounding_box_calculation",
                    coordinates=precision_coords,
                    context=bbox_data,
                    severity=PrecisionErrorSeverity.WARNING
                )
            
            if bbox_width > max_bbox_size or bbox_height > max_bbox_size:
                handle_precision_error(
                    error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                    message=f"Bounding box size ({bbox_width}, {bbox_height}) is above maximum threshold {max_bbox_size}",
                    operation="bounding_box_calculation",
                    coordinates=precision_coords,
                    context=bbox_data,
                    severity=PrecisionErrorSeverity.WARNING
                )
        
        return (min_x, min_y, max_x, max_y)
        
    except Exception as e:
        # Handle bounding box calculation error
        handle_precision_error(
            error_type=PrecisionErrorType.CALCULATION_ERROR,
            message=f"Bounding box calculation failed: {str(e)}",
            operation="bounding_box_calculation",
            coordinates=precision_coords,
            context=bbox_data,
            severity=PrecisionErrorSeverity.ERROR
        )
        raise


def calculate_box_intersection(bbox1: Tuple[float, float, float, float],
                              bbox2: Tuple[float, float, float, float],
                              config: Optional[PrecisionConfig] = None) -> Tuple[bool, Optional[Tuple[float, float, float, float]]]:
    """
    Calculate intersection between two bounding boxes with precision.
    
    Args:
        bbox1: First bounding box (min_x, min_y, max_x, max_y)
        bbox2: Second bounding box (min_x, min_y, max_x, max_y)
        config: Precision configuration (optional)
        
    Returns:
        Tuple of (intersects, intersection_bbox)
    """
    from svgx_engine.core.precision_hooks import hook_manager, HookType, HookContext
    from svgx_engine.core.precision_errors import handle_precision_error, PrecisionErrorType, PrecisionErrorSeverity
    
    if config is None:
        config = config_manager.get_default_config()
    
    precision_math = PrecisionMath()
    
    # Convert bounding box coordinates to precision coordinates
    min_x1, min_y1, max_x1, max_y1 = bbox1
    min_x2, min_y2, max_x2, max_y2 = bbox2
    
    precision_coords = [
        PrecisionCoordinate(min_x1, min_y1, 0.0),
        PrecisionCoordinate(max_x1, max_y1, 0.0),
        PrecisionCoordinate(min_x2, min_y2, 0.0),
        PrecisionCoordinate(max_x2, max_y2, 0.0)
    ]
    
    # Create hook context for box intersection calculation
    intersection_data = {
        'calculation_type': 'box_intersection',
        'bbox1': bbox1,
        'bbox2': bbox2
    }
    
    context = HookContext(
        operation_name="box_intersection_calculation",
        coordinates=precision_coords,
        constraint_data=intersection_data
    )
    
    # Execute geometric constraint hooks
    context = hook_manager.execute_hooks(HookType.GEOMETRIC_CONSTRAINT, context)
    
    try:
        # Calculate intersection with precision
        intersection_min_x = max(min_x1, min_x2)
        intersection_min_y = max(min_y1, min_y2)
        intersection_max_x = min(max_x1, max_x2)
        intersection_max_y = min(max_y1, max_y2)
        
        # Check if intersection exists
        intersects = (intersection_min_x <= intersection_max_x and 
                     intersection_min_y <= intersection_max_y)
        
        intersection_bbox = None
        if intersects:
            intersection_bbox = (intersection_min_x, intersection_min_y, 
                               intersection_max_x, intersection_max_y)
        
        # Execute precision validation hooks
        context.coordinates = precision_coords
        hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)
        
        # Validate intersection result
        if config.enable_geometric_validation and intersects:
            intersection_width = intersection_max_x - intersection_min_x
            intersection_height = intersection_max_y - intersection_min_y
            
            min_intersection_size = config.validation_rules.get('min_intersection_size', 0.000001)
            
            if intersection_width < min_intersection_size or intersection_height < min_intersection_size:
                handle_precision_error(
                    error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                    message=f"Intersection size ({intersection_width}, {intersection_height}) is below minimum threshold {min_intersection_size}",
                    operation="box_intersection_calculation",
                    coordinates=precision_coords,
                    context=intersection_data,
                    severity=PrecisionErrorSeverity.WARNING
                )
        
        return intersects, intersection_bbox
        
    except Exception as e:
        # Handle box intersection calculation error
        handle_precision_error(
            error_type=PrecisionErrorType.CALCULATION_ERROR,
            message=f"Box intersection calculation failed: {str(e)}",
            operation="box_intersection_calculation",
            coordinates=precision_coords,
            context=intersection_data,
            severity=PrecisionErrorSeverity.ERROR
        )
        raise


def calculate_centroid(coordinates: List[List[float]],
                      config: Optional[PrecisionConfig] = None) -> List[float]:
    """
    Calculate centroid of coordinates with precision.
    
    Args:
        coordinates: List of coordinate pairs
        config: Precision configuration (optional)
        
    Returns:
        Centroid coordinates [x, y]
    """
    if config is None:
        config = config_manager.get_default_config()
    
    precision_math = PrecisionMath()
    
    if not coordinates:
        return [0, 0]
    
    # Convert to precision coordinates
    precision_coords = []
    for coord in coordinates:
        if len(coord) >= 2:
            precision_coords.append(PrecisionCoordinate(coord[0], coord[1], coord[2] if len(coord) > 2 else 0.0))
    
    if not precision_coords:
        return [0, 0]
    
    # Calculate centroid with precision
    x_sum = 0.0
    y_sum = 0.0
    z_sum = 0.0
    count = len(precision_coords)
    
    for coord in precision_coords:
        x_sum = precision_math.add(x_sum, coord.x)
        y_sum = precision_math.add(y_sum, coord.y)
        z_sum = precision_math.add(z_sum, coord.z)
    
    if count == 0:
        return [0, 0]
    
    avg_x = precision_math.divide(x_sum, count)
    avg_y = precision_math.divide(y_sum, count)
    avg_z = precision_math.divide(z_sum, count)
    
    return [avg_x, avg_y, avg_z]


def calculate_area(coordinates: List[List[float]],
                  config: Optional[PrecisionConfig] = None) -> float:
    """
    Calculate area of polygon coordinates with precision.
    
    Args:
        coordinates: List of coordinate pairs forming a polygon
        config: Precision configuration (optional)
        
    Returns:
        Area of the polygon
    """
    from svgx_engine.core.precision_hooks import hook_manager, HookType, HookContext
    from svgx_engine.core.precision_errors import handle_precision_error, PrecisionErrorType, PrecisionErrorSeverity
    
    if config is None:
        config = config_manager.get_default_config()
    
    precision_math = PrecisionMath()
    
    if len(coordinates) < 3:
        return 0.0
    
    # Convert to precision coordinates
    precision_coords = []
    for coord in coordinates:
        if len(coord) >= 2:
            precision_coords.append(PrecisionCoordinate(coord[0], coord[1], coord[2] if len(coord) > 2 else 0.0))
    
    if len(precision_coords) < 3:
        return 0.0
    
    # Create hook context for area calculation
    area_data = {
        'coordinate_count': len(precision_coords),
        'geometry_type': 'polygon',
        'calculation_type': 'area'
    }
    
    context = HookContext(
        operation_name="area_calculation",
        coordinates=precision_coords,
        constraint_data=area_data
    )
    
    # Execute geometric constraint hooks
    context = hook_manager.execute_hooks(HookType.GEOMETRIC_CONSTRAINT, context)
    
    try:
        # Shoelace formula for polygon area with precision
        area = 0.0
        n = len(precision_coords)
        
        for i in range(n):
            j = (i + 1) % n
            area = precision_math.add(
                area,
                precision_math.multiply(precision_coords[i].x, precision_coords[j].y)
            )
            area = precision_math.subtract(
                area,
                precision_math.multiply(precision_coords[j].x, precision_coords[i].y)
            )
        
        area = abs(area) / 2.0
        
        # Execute precision validation hooks
        context.coordinates = precision_coords
        hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)
        
        # Validate area result
        if config.enable_geometric_validation:
            if area < config.validation_rules.get('min_area', 0.000001):
                handle_precision_error(
                    error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                    message=f"Calculated area {area} is below minimum threshold",
                    operation="area_calculation",
                    coordinates=precision_coords,
                    context=area_data,
                    severity=PrecisionErrorSeverity.WARNING
                )
        
        return area
        
    except Exception as e:
        # Handle area calculation error
        handle_precision_error(
            error_type=PrecisionErrorType.CALCULATION_ERROR,
            message=f"Area calculation failed: {str(e)}",
            operation="area_calculation",
            coordinates=precision_coords,
            context=area_data,
            severity=PrecisionErrorSeverity.ERROR
        )
        raise


def calculate_perimeter(coordinates: List[List[float]],
                       config: Optional[PrecisionConfig] = None) -> float:
    """
    Calculate perimeter of coordinates with precision.
    
    Args:
        coordinates: List of coordinate pairs
        config: Precision configuration (optional)
        
    Returns:
        Perimeter length
    """
    from svgx_engine.core.precision_hooks import hook_manager, HookType, HookContext
    from svgx_engine.core.precision_errors import handle_precision_error, PrecisionErrorType, PrecisionErrorSeverity
    
    if config is None:
        config = config_manager.get_default_config()
    
    precision_math = PrecisionMath()
    
    if len(coordinates) < 2:
        return 0.0
    
    # Convert to precision coordinates
    precision_coords = []
    for coord in coordinates:
        if len(coord) >= 2:
            precision_coords.append(PrecisionCoordinate(coord[0], coord[1], coord[2] if len(coord) > 2 else 0.0))
    
    if len(precision_coords) < 2:
        return 0.0
    
    # Create hook context for perimeter calculation
    perimeter_data = {
        'coordinate_count': len(precision_coords),
        'geometry_type': 'polygon',
        'calculation_type': 'perimeter'
    }
    
    context = HookContext(
        operation_name="perimeter_calculation",
        coordinates=precision_coords,
        constraint_data=perimeter_data
    )
    
    # Execute geometric constraint hooks
    context = hook_manager.execute_hooks(HookType.GEOMETRIC_CONSTRAINT, context)
    
    try:
        # Calculate perimeter with precision
        perimeter = 0.0
        for i in range(len(precision_coords) - 1):
            distance = precision_math.distance(precision_coords[i], precision_coords[i + 1])
            perimeter = precision_math.add(perimeter, distance)
        
        # Close the polygon if needed
        if len(precision_coords) > 2:
            distance = precision_math.distance(precision_coords[-1], precision_coords[0])
            perimeter = precision_math.add(perimeter, distance)
        
        # Execute precision validation hooks
        context.coordinates = precision_coords
        hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)
        
        # Validate perimeter result
        if config.enable_geometric_validation:
            if perimeter < config.validation_rules.get('min_perimeter', 0.001):
                handle_precision_error(
                    error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                    message=f"Calculated perimeter {perimeter} is below minimum threshold",
                    operation="perimeter_calculation",
                    coordinates=precision_coords,
                    context=perimeter_data,
                    severity=PrecisionErrorSeverity.WARNING
                )
        
        return perimeter
        
    except Exception as e:
        # Handle perimeter calculation error
        handle_precision_error(
            error_type=PrecisionErrorType.CALCULATION_ERROR,
            message=f"Perimeter calculation failed: {str(e)}",
            operation="perimeter_calculation",
            coordinates=precision_coords,
            context=perimeter_data,
            severity=PrecisionErrorSeverity.ERROR
        )
        raise


def transform_geometry(geometry: Geometry, 
                      translation: List[float] = None,
                      scale: float = 1.0,
                      rotation: float = 0.0,
                      config: Optional[PrecisionConfig] = None) -> Geometry:
    """
    Transform geometry with translation, scale, and rotation with precision.
    
    Args:
        geometry: Geometry to transform
        translation: Translation vector [dx, dy]
        scale: Scale factor
        rotation: Rotation angle in radians
        config: Precision configuration (optional)
        
    Returns:
        Transformed geometry
    """
    from svgx_engine.core.precision_hooks import hook_manager, HookType, HookContext
    from svgx_engine.core.precision_errors import handle_precision_error, PrecisionErrorType, PrecisionErrorSeverity
    
    if config is None:
        config = config_manager.get_default_config()
    
    precision_math = PrecisionMath()
    coordinate_validator = CoordinateValidator()
    
    if translation is None:
        translation = [0, 0]
    
    # Create hook context for geometry transformation
    transformation_data = {
        'translation': translation,
        'scale': scale,
        'rotation': rotation,
        'geometry_type': type(geometry).__name__
    }
    
    # Convert translation to precision coordinate
    translation_coord = PrecisionCoordinate(translation[0], translation[1], translation[2] if len(translation) > 2 else 0.0)
    
    # Create initial coordinates list for hook context
    initial_coords = []
    for coord in geometry.coordinates:
        if isinstance(coord, list) and len(coord) >= 2:
            precision_coord = PrecisionCoordinate(coord[0], coord[1], coord[2] if len(coord) > 2 else 0.0)
            initial_coords.append(precision_coord)
    
    context = HookContext(
        operation_name="geometry_transformation",
        coordinates=initial_coords,
        transformation_data=transformation_data
    )
    
    # Execute coordinate transformation hooks
    context = hook_manager.execute_hooks(HookType.COORDINATE_TRANSFORMATION, context)
    
    try:
        transformed_coords = []
        for coord in geometry.coordinates:
            if isinstance(coord, list) and len(coord) >= 2:
                # Create precision coordinate
                precision_coord = PrecisionCoordinate(coord[0], coord[1], coord[2] if len(coord) > 2 else 0.0)
                
                # Apply translation with precision
                x = precision_math.add(precision_coord.x, translation_coord.x)
                y = precision_math.add(precision_coord.y, translation_coord.y)
                z = precision_math.add(precision_coord.z, translation_coord.z)
                
                # Apply scale with precision
                x = precision_math.multiply(x, scale)
                y = precision_math.multiply(y, scale)
                z = precision_math.multiply(z, scale)
                
                # Apply rotation with precision
                if rotation != 0:
                    cos_r = precision_math.cos(rotation)
                    sin_r = precision_math.sin(rotation)
                    x_new = precision_math.subtract(
                        precision_math.multiply(x, cos_r),
                        precision_math.multiply(y, sin_r)
                    )
                    y_new = precision_math.add(
                        precision_math.multiply(x, sin_r),
                        precision_math.multiply(y, cos_r)
                    )
                    x, y = x_new, y_new
                
                # Create transformed coordinate
                transformed_coord = PrecisionCoordinate(x, y, z)
                
                # Validate transformed coordinate
                if config.enable_coordinate_validation:
                    validation_result = coordinate_validator.validate_coordinate(transformed_coord)
                    if not validation_result.is_valid:
                        if config.should_fail_on_violation():
                            raise ValueError(f"Invalid coordinate after transformation: {validation_result.errors}")
                        elif config.auto_correct_precision_errors:
                            transformed_coord = _correct_coordinate(transformed_coord, config)
                
                transformed_coords.append([transformed_coord.x, transformed_coord.y, transformed_coord.z])
            else:
                transformed_coords.append(coord)
        
        # Execute precision validation hooks on transformed coordinates
        context.coordinates = [PrecisionCoordinate(coord[0], coord[1], coord[2] if len(coord) > 2 else 0.0) 
                             for coord in transformed_coords if isinstance(coord, list)]
        hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)
        
    except Exception as e:
        # Handle transformation error
        handle_precision_error(
            error_type=PrecisionErrorType.TRANSFORMATION_ERROR,
            message=f"Geometry transformation failed: {str(e)}",
            operation="geometry_transformation",
            coordinates=initial_coords,
            context=transformation_data,
            severity=PrecisionErrorSeverity.ERROR
        )
        raise
    
    return Geometry(
        type=geometry.type,
        coordinates=transformed_coords,
        properties=geometry.properties
    )


def validate_geometry_coordinates(coordinates: List[List[float]],
                                config: Optional[PrecisionConfig] = None) -> Dict[str, Any]:
    """
    Validate geometry coordinates with precision requirements.
    
    Args:
        coordinates: List of coordinate pairs
        config: Precision configuration (optional)
        
    Returns:
        Validation result dictionary
    """
    if config is None:
        config = config_manager.get_default_config()
    
    coordinate_validator = CoordinateValidator()
    precision_validator = PrecisionValidator()
    
    validation_result = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'precision_violations': []
    }
    
    try:
        # Validate each coordinate
        for i, coord in enumerate(coordinates):
            if isinstance(coord, list) and len(coord) >= 2:
                precision_coord = PrecisionCoordinate(coord[0], coord[1], coord[2] if len(coord) > 2 else 0.0)
                
                # Validate coordinate
                coord_validation = coordinate_validator.validate_coordinate(precision_coord)
                if not coord_validation.is_valid:
                    validation_result['is_valid'] = False
                    validation_result['errors'].append(f"Coordinate {i}: {coord_validation.errors}")
                
                # Check precision violations
                precision_violations = _check_precision_violations(precision_coord, config)
                if precision_violations:
                    validation_result['precision_violations'].extend(precision_violations)
        
        # Validate geometric properties if coordinates form a polygon
        if len(coordinates) >= 3:
            area = calculate_area(coordinates, config)
            if area < config.validation_rules.get('min_area', 0.000001):
                validation_result['warnings'].append(f"Area {area} is below minimum threshold")
            
            perimeter = calculate_perimeter(coordinates, config)
            if perimeter < config.validation_rules.get('min_perimeter', 0.001):
                validation_result['warnings'].append(f"Perimeter {perimeter} is below minimum threshold")
        
    except Exception as e:
        validation_result['is_valid'] = False
        validation_result['errors'].append(f"Validation error: {str(e)}")
    
    return validation_result


def _correct_coordinate(coord: PrecisionCoordinate, config: PrecisionConfig) -> PrecisionCoordinate:
    """Correct coordinate based on precision level"""
    precision_value = config.get_precision_value()
    corrected_x = round(coord.x / precision_value) * precision_value
    corrected_y = round(coord.y / precision_value) * precision_value
    corrected_z = round(coord.z / precision_value) * precision_value
    
    return PrecisionCoordinate(corrected_x, corrected_y, corrected_z)


def _check_precision_violations(coord: PrecisionCoordinate, config: PrecisionConfig) -> List[str]:
    """Check for precision violations in a coordinate"""
    violations = []
    precision_value = config.get_precision_value()
    
    # Check if coordinates are properly rounded to precision level
    if abs(coord.x - round(coord.x / precision_value) * precision_value) > 1e-10:
        violations.append(f"X-coordinate {coord.x} not at precision level {precision_value}")
    if abs(coord.y - round(coord.y / precision_value) * precision_value) > 1e-10:
        violations.append(f"Y-coordinate {coord.y} not at precision level {precision_value}")
    if abs(coord.z - round(coord.z / precision_value) * precision_value) > 1e-10:
        violations.append(f"Z-coordinate {coord.z} not at precision level {precision_value}")
    
    return violations


def create_precision_geometry(geometry_type: str,
                            coordinates: List[List[float]],
                            config: Optional[PrecisionConfig] = None) -> Dict[str, Any]:
    """
    Create precision-aware geometry object.
    
    Args:
        geometry_type: Type of geometry
        coordinates: List of coordinate pairs
        config: Precision configuration (optional)
        
    Returns:
        Precision geometry object
    """
    if config is None:
        config = config_manager.get_default_config()
    
    # Validate coordinates
    validation_result = validate_geometry_coordinates(coordinates, config)
    
    # Calculate geometric properties with precision
    area = calculate_area(coordinates, config) if len(coordinates) >= 3 else 0.0
    perimeter = calculate_perimeter(coordinates, config) if len(coordinates) >= 2 else 0.0
    centroid = calculate_centroid(coordinates, config)
    bounding_box = calculate_bounding_box(coordinates, config)
    
    return {
        'type': geometry_type,
        'coordinates': coordinates,
        'precision_coordinates': [PrecisionCoordinate(coord[0], coord[1], coord[2] if len(coord) > 2 else 0.0) 
                                for coord in coordinates if len(coord) >= 2],
        'area': area,
        'perimeter': perimeter,
        'centroid': centroid,
        'bounding_box': bounding_box,
        'precision_level': config.precision_level.value,
        'validation_status': 'valid' if validation_result['is_valid'] else 'invalid',
        'validation_errors': validation_result['errors'],
        'precision_violations': validation_result['precision_violations']
    } 