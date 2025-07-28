from lxml import etree as ET
from lxml.etree import QName
import math
from typing import List, Dict, Any, Tuple, Optional
from services.coordinate_validator import validate_coordinates, validate_scale_factors, validate_anchor_points, CoordinateValidationError
from services.coordinate_validator import validate_transformation_matrix as validate_matrix

SVG_NS = "http://www.w3.org/2000/svg"

def apply_affine_transform(svg_str, anchor_points):
    # For MVP: Only handle uniform scaling and translation using first two anchor pairs
    try:
        root = ET.fromstring(svg_str.encode('utf-8'))
    except Exception as e:
        return {"error": f"Failed to parse SVG: {str(e)}"}

    if len(anchor_points) < 2:
        return {"error": "At least two anchor points required for scaling."}

    # Calculate scale and translation from first two anchor points
    svg1, real1 = anchor_points[0]['svg'], anchor_points[0]['real']
    svg2, real2 = anchor_points[1]['svg'], anchor_points[1]['real']
    dx_svg, dy_svg = svg2[0] - svg1[0], svg2[1] - svg1[1]
    dx_real, dy_real = real2[0] - real1[0], real2[1] - real1[1]
    if dx_svg == 0 or dy_svg == 0:
        return {"error": "Invalid anchor points for scaling."}
    scale_x = dx_real / dx_svg
    scale_y = dy_real / dy_svg
    trans_x = real1[0] - svg1[0] * scale_x
    trans_y = real1[1] - svg1[1] * scale_y

    def transform_point(x, y):
        return x * scale_x + trans_x, y * scale_y + trans_y

    # Update coordinates for supported SVG elements
    for elem in root.iter():
        tag = ET.QName(elem).localname
        if tag in ['rect', 'circle', 'ellipse']:
            for attr in ['x', 'cx']:
                if attr in elem.attrib:
                    x = float(elem.attrib[attr])
                    new_x, _ = transform_point(x, 0)
                    elem.attrib[attr] = str(new_x)
            for attr in ['y', 'cy']:
                if attr in elem.attrib:
                    y = float(elem.attrib[attr])
                    _, new_y = transform_point(0, y)
                    elem.attrib[attr] = str(new_y)
        elif tag == 'line':
            for attr in ['x1', 'x2']:
                if attr in elem.attrib:
                    x = float(elem.attrib[attr])
                    new_x, _ = transform_point(x, 0)
                    elem.attrib[attr] = str(new_x)
            for attr in ['y1', 'y2']:
                if attr in elem.attrib:
                    y = float(elem.attrib[attr])
                    _, new_y = transform_point(0, y)
                    elem.attrib[attr] = str(new_y)
        elif tag in ['polyline', 'polygon']:
            if 'points' in elem.attrib:
                points = elem.attrib['points'].strip().split()
                new_points = []
                for pt in points:
                    if ',' in pt:
                        x, y = map(float, pt.split(','))
                        new_x, new_y = transform_point(x, y)
                        new_points.append(f"{new_x},{new_y}")
                elem.attrib['points'] = ' '.join(new_points)
        # For MVP, skip path transformation (complex)

    return ET.tostring(root, encoding='unicode', pretty_print=True)

def convert_to_real_world_coordinates(
    svg_coordinates: List[List[float]],
    scale_x: float,
    scale_y: float,
    origin_x: float = 0.0,
    origin_y: float = 0.0,
    units: str = "meters"
) -> List[List[float]]:
    """
    Convert SVG coordinates to real-world coordinates using scale factors
    
    Args:
        svg_coordinates: List of [x, y] coordinates in SVG space
        scale_x: Scale factor for X axis
        scale_y: Scale factor for Y axis
        origin_x: Origin X coordinate in real-world space
        origin_y: Origin Y coordinate in real-world space
        units: Units for real-world coordinates
        
    Returns:
        List of [x, y] coordinates in real-world space
    """
    # Validate inputs
    validation = validate_coordinates(svg_coordinates, "svg")
    if not validation["valid"]:
        raise CoordinateValidationError("Invalid SVG coordinates", "svg_coordinates", svg_coordinates)
    
    scale_validation = validate_scale_factors(scale_x, scale_y)
    if not scale_validation["valid"]:
        raise CoordinateValidationError("Invalid scale factors", "scale_factors", {"x": scale_x, "y": scale_y})
    
    # Convert coordinates
    real_world_coords = []
    for coord in svg_coordinates:
        x, y = coord
        real_x = x * scale_x + origin_x
        real_y = y * scale_y + origin_y
        real_world_coords.append([real_x, real_y])
    
    return real_world_coords

def validate_coordinate_system(anchor_points: List[Dict[str, List[float]]]) -> Dict[str, Any]:
    """
    Validate coordinate system and anchor points
    
    Args:
        anchor_points: List of anchor point dictionaries with 'svg' and 'real' coordinates
        
    Returns:
        Dictionary with validation results
    """
    return validate_anchor_points(anchor_points)

def calculate_scale_factors(anchor_points: List[Dict[str, List[float]]]) -> Dict[str, float]:
    """
    Calculate scale factors from anchor points
    
    Args:
        anchor_points: List of anchor point dictionaries
        
    Returns:
        Dictionary with scale factors and confidence
    """
    if len(anchor_points) < 2:
        return {"x": 1.0, "y": 1.0, "uniform": True, "confidence": 0.0}
    
    # Calculate scale factors from first two points
    svg1, real1 = anchor_points[0]["svg"], anchor_points[0]["real"]
    svg2, real2 = anchor_points[1]["svg"], anchor_points[1]["real"]
    
    dx_svg = svg2[0] - svg1[0]
    dy_svg = svg2[1] - svg1[1]
    dx_real = real2[0] - real1[0]
    dy_real = real2[1] - real1[1]
    
    if dx_svg == 0 or dy_svg == 0:
        return {"x": 1.0, "y": 1.0, "uniform": True, "confidence": 0.0}
    
    scale_x = dx_real / dx_svg
    scale_y = dy_real / dy_svg
    
    # Check if scaling is uniform
    scale_ratio = abs(scale_x - scale_y) / max(abs(scale_x), abs(scale_y))
    uniform = scale_ratio < 0.01  # Within 1%
    
    # Calculate confidence based on number of anchor points and scale consistency
    confidence = min(1.0, len(anchor_points) / 4.0)  # More points = higher confidence
    
    if len(anchor_points) > 2:
        # Check consistency across multiple anchor points
        scale_consistencies = []
        for i in range(1, len(anchor_points)):
            for j in range(i + 1, len(anchor_points)):
                svg_i, real_i = anchor_points[i]["svg"], anchor_points[i]["real"]
                svg_j, real_j = anchor_points[j]["svg"], anchor_points[j]["real"]
                
                dx_svg_ij = svg_j[0] - svg_i[0]
                dy_svg_ij = svg_j[1] - svg_i[1]
                dx_real_ij = real_j[0] - real_i[0]
                dy_real_ij = real_j[1] - real_i[1]
                
                if dx_svg_ij != 0 and dy_svg_ij != 0:
                    scale_x_ij = dx_real_ij / dx_svg_ij
                    scale_y_ij = dy_real_ij / dy_svg_ij
                    
                    # Check consistency with main scale factors
                    x_consistency = 1.0 - abs(scale_x_ij - scale_x) / abs(scale_x)
                    y_consistency = 1.0 - abs(scale_y_ij - scale_y) / abs(scale_y)
                    scale_consistencies.append(min(x_consistency, y_consistency))
        
        if scale_consistencies:
            avg_consistency = sum(scale_consistencies) / len(scale_consistencies)
            confidence = min(1.0, confidence * avg_consistency)
    
    return {
        "x": scale_x,
        "y": scale_y,
        "uniform": uniform,
        "confidence": confidence
    }

def transform_coordinates_batch(
    coordinates: List[List[float]],
    source_system: str,
    target_system: str,
    transformation_matrix: Optional[List[List[float]]] = None
) -> List[List[float]]:
    """
    Transform coordinates between different coordinate systems with precision validation.
    
    Args:
        coordinates: List of [x, y] coordinates to transform
        source_system: Source coordinate system
        target_system: Target coordinate system
        transformation_matrix: Optional 4x4 transformation matrix
        
    Returns:
        List of transformed coordinates
    """
    from svgx_engine.core.precision_hooks import hook_manager, HookType, HookContext
    from svgx_engine.core.precision_errors import handle_precision_error, PrecisionErrorType, PrecisionErrorSeverity
    from svgx_engine.core.precision_coordinate import PrecisionCoordinate
    from svgx_engine.core.precision_math import PrecisionMath
    from svgx_engine.core.precision_config import config_manager
    
    # Initialize precision components
    config = config_manager.get_default_config()
    precision_math = PrecisionMath()
    
    # Create hook context for batch transformation
    transformation_data = {
        'source_system': source_system,
        'target_system': target_system,
        'coordinate_count': len(coordinates),
        'has_matrix': transformation_matrix is not None,
        'operation_type': 'batch_coordinate_transformation'
    }
    
    context = HookContext(
        operation_name="batch_coordinate_transformation",
        coordinates=[],
        constraint_data=transformation_data
    )
    
    # Execute geometric constraint hooks
    context = hook_manager.execute_hooks(HookType.GEOMETRIC_CONSTRAINT, context)
    
    try:
        # Validate inputs with precision validation
        validation = validate_coordinates(coordinates, source_system)
        if not validation["valid"]:
            handle_precision_error(
                error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                message=f"Invalid source coordinates: {validation.get('errors', 'Unknown error')}",
                operation="batch_coordinate_transformation",
                coordinates=[],
                context=transformation_data,
                severity=PrecisionErrorSeverity.ERROR
            )
            raise CoordinateValidationError("Invalid source coordinates", "coordinates", coordinates)
        
        if transformation_matrix:
            matrix_validation = validate_transformation_matrix(transformation_matrix)
            if not matrix_validation["valid"]:
                handle_precision_error(
                    error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                    message=f"Invalid transformation matrix: {matrix_validation.get('errors', 'Unknown error')}",
                    operation="batch_coordinate_transformation",
                    coordinates=[],
                    context=transformation_data,
                    severity=PrecisionErrorSeverity.ERROR
                )
                raise CoordinateValidationError("Invalid transformation matrix", "transformation_matrix", transformation_matrix)
        
        # Convert coordinates to precision coordinates
        precision_coords = []
        for coord in coordinates:
            if len(coord) >= 2:
                precision_coord = PrecisionCoordinate(coord[0], coord[1], coord[2] if len(coord) > 2 else 0.0)
                precision_coords.append(precision_coord)
        
        # Apply transformation based on coordinate systems
        if source_system == "svg" and target_system in ["real_world_meters", "real_world_feet"]:
            # Simple scale transformation with precision
            scale_factor = 1.0  # This would come from calibration
            transformed_coords = []
            for coord in precision_coords:
                scaled_x = precision_math.multiply(coord.x, scale_factor)
                scaled_y = precision_math.multiply(coord.y, scale_factor)
                transformed_coords.append([scaled_x, scaled_y])
            
        elif source_system in ["real_world_meters", "real_world_feet"] and target_system == "svg":
            # Inverse transformation with precision
            scale_factor = 1.0  # This would come from calibration
            transformed_coords = []
            for coord in precision_coords:
                scaled_x = precision_math.divide(coord.x, scale_factor)
                scaled_y = precision_math.divide(coord.y, scale_factor)
                transformed_coords.append([scaled_x, scaled_y])
            
        elif transformation_matrix:
            # Apply matrix transformation with precision
            transformed_coords = apply_matrix_transformation_precision(precision_coords, transformation_matrix, config)
            
        else:
            # Identity transformation
            transformed_coords = [[coord.x, coord.y] for coord in precision_coords]
        
        # Validate transformed coordinates
        if config.enable_geometric_validation:
            max_coordinate = config.validation_rules.get('max_coordinate', 1e6)
            for i, coord in enumerate(transformed_coords):
                if len(coord) >= 2:
                    if abs(coord[0]) > max_coordinate or abs(coord[1]) > max_coordinate:
                        handle_precision_error(
                            error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                            message=f"Transformed coordinate {coord} at index {i} exceeds maximum range {max_coordinate}",
                            operation="batch_coordinate_transformation",
                            coordinates=precision_coords,
                            context=transformation_data,
                            severity=PrecisionErrorSeverity.WARNING
                        )
        
        # Execute precision validation hooks
        context.coordinates = precision_coords
        hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)
        
        return transformed_coords
        
    except Exception as e:
        # Handle batch transformation error
        handle_precision_error(
            error_type=PrecisionErrorType.TRANSFORMATION_ERROR,
            message=f"Batch coordinate transformation failed: {str(e)}",
            operation="batch_coordinate_transformation",
            coordinates=precision_coords if 'precision_coords' in locals() else [],
            context=transformation_data,
            severity=PrecisionErrorSeverity.ERROR
        )
        raise

def apply_matrix_transformation_precision(
    coordinates: List[PrecisionCoordinate], 
    matrix: List[List[float]],
    config: Optional['PrecisionConfig'] = None
) -> List[List[float]]:
    """
    Apply 4x4 transformation matrix to precision coordinates with validation.
    
    Args:
        coordinates: List of PrecisionCoordinate instances
        matrix: 4x4 transformation matrix
        config: Precision configuration (optional)
        
    Returns:
        List of transformed coordinates as [x, y] lists
    """
    from svgx_engine.core.precision_hooks import hook_manager, HookType, HookContext
    from svgx_engine.core.precision_errors import handle_precision_error, PrecisionErrorType, PrecisionErrorSeverity
    from svgx_engine.core.precision_math import PrecisionMath
    from svgx_engine.core.precision_config import config_manager
    
    if config is None:
        config = config_manager.get_default_config()
    
    precision_math = PrecisionMath()
    
    # Create hook context for matrix transformation
    matrix_data = {
        'matrix_shape': (len(matrix), len(matrix[0]) if matrix else 0),
        'coordinate_count': len(coordinates),
        'operation_type': 'matrix_transformation'
    }
    
    context = HookContext(
        operation_name="matrix_transformation",
        coordinates=coordinates,
        constraint_data=matrix_data
    )
    
    # Execute geometric constraint hooks
    context = hook_manager.execute_hooks(HookType.GEOMETRIC_CONSTRAINT, context)
    
    try:
        # Validate matrix
        if not matrix or len(matrix) != 4 or any(len(row) != 4 for row in matrix):
            handle_precision_error(
                error_type=PrecisionErrorType.GEOMETRIC_ERROR,
                message=f"Invalid transformation matrix shape: {matrix_data['matrix_shape']} (expected 4x4)",
                operation="matrix_transformation",
                coordinates=coordinates,
                context=matrix_data,
                severity=PrecisionErrorSeverity.ERROR
            )
            raise ValueError(f"Transformation matrix must be 4x4, got {matrix_data['matrix_shape']}")
        
        transformed_coords = []
        
        for coord in coordinates:
            # Treat as homogeneous coordinates [x, y, 0, 1] with precision
            x = precision_math.to_float(coord.x)
            y = precision_math.to_float(coord.y)
            z = precision_math.to_float(coord.z)
            
            # Apply matrix multiplication with precision
            result = [0.0, 0.0, 0.0, 0.0]
            
            for i in range(4):
                result[i] = precision_math.add(
                    precision_math.add(
                        precision_math.multiply(matrix[i][0], x),
                        precision_math.multiply(matrix[i][1], y)
                    ),
                    precision_math.add(
                        precision_math.multiply(matrix[i][2], z),
                        precision_math.multiply(matrix[i][3], 1.0)
                    )
                )
            
            # Convert back from homogeneous coordinates
            if abs(result[3]) > 1e-12:  # Avoid division by very small numbers
                transformed_x = precision_math.divide(result[0], result[3])
                transformed_y = precision_math.divide(result[1], result[3])
            else:
                transformed_x = result[0]
                transformed_y = result[1]
            
            transformed_coords.append([transformed_x, transformed_y])
        
        # Execute precision validation hooks
        context.coordinates = coordinates
        hook_manager.execute_hooks(HookType.PRECISION_VALIDATION, context)
        
        return transformed_coords
        
    except Exception as e:
        # Handle matrix transformation error
        handle_precision_error(
            error_type=PrecisionErrorType.TRANSFORMATION_ERROR,
            message=f"Matrix transformation failed: {str(e)}",
            operation="matrix_transformation",
            coordinates=coordinates,
            context=matrix_data,
            severity=PrecisionErrorSeverity.ERROR
        )
        raise

def apply_matrix_transformation(
    coordinates: List[List[float]], 
    matrix: List[List[float]]
) -> List[List[float]]:
    """
    Apply 4x4 transformation matrix to coordinates (legacy function for backward compatibility).
    
    Args:
        coordinates: List of [x, y] coordinates
        matrix: 4x4 transformation matrix
        
    Returns:
        List of transformed coordinates
    """
    # Convert to precision coordinates and use the precision-aware version
    from svgx_engine.core.precision_coordinate import PrecisionCoordinate
    
    precision_coords = []
    for coord in coordinates:
        if len(coord) >= 2:
            precision_coord = PrecisionCoordinate(coord[0], coord[1], coord[2] if len(coord) > 2 else 0.0)
            precision_coords.append(precision_coord)
    
    # Use the precision-aware transformation
    transformed_coords = apply_matrix_transformation_precision(precision_coords, matrix)
    
    return transformed_coords

def create_transformation_matrix(
    scale_x: float = 1.0,
    scale_y: float = 1.0,
    rotation: float = 0.0,
    translation_x: float = 0.0,
    translation_y: float = 0.0
) -> List[List[float]]:
    """
    Create a 4x4 transformation matrix from scale, rotation, and translation
    
    Args:
        scale_x: Scale factor for X axis
        scale_y: Scale factor for Y axis
        rotation: Rotation angle in radians
        translation_x: Translation in X direction
        translation_y: Translation in Y direction
        
    Returns:
        4x4 transformation matrix
    """
    cos_r = math.cos(rotation)
    sin_r = math.sin(rotation)
    
    matrix = [
        [scale_x * cos_r, -scale_y * sin_r, 0, translation_x],
        [scale_x * sin_r, scale_y * cos_r, 0, translation_y],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ]
    
    return matrix

def convert_svg_to_bim_coordinates(
    svg_coordinates: List[List[float]],
    project_id: str,
    floor_id: Optional[str] = None,
    scale_factors: Optional[Dict[str, float]] = None
) -> List[List[float]]:
    """
    Convert SVG coordinates to BIM coordinates
    
    Args:
        svg_coordinates: List of [x, y] coordinates in SVG space
        project_id: BIM project identifier
        floor_id: Optional floor identifier
        scale_factors: Optional scale factors (will be retrieved from project if not provided)
        
    Returns:
        List of [x, y] coordinates in BIM space
    """
    # In a real implementation, this would:
    # 1. Retrieve project-specific coordinate system information
    # 2. Get scale factors from project calibration
    # 3. Apply project-specific transformations
    
    # For now, use default scale factors
    if not scale_factors:
        scale_factors = {"x": 1.0, "y": 1.0}
    
    return convert_to_real_world_coordinates(
        svg_coordinates,
        scale_factors["x"],
        scale_factors["y"],
        0.0, 0.0,
        "meters"
    )

def validate_transformation_matrix(matrix: List[List[float]]) -> Dict[str, Any]:
    """
    Validate transformation matrix
    
    Args:
        matrix: 4x4 transformation matrix
        
    Returns:
        Dictionary with validation results
    """
    return validate_matrix(matrix) 