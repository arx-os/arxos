"""
Geometry utility functions for BIM processing.
"""

import math
from typing import List, Tuple, Dict, Any
from models.bim import Geometry, GeometryType


def normalize_coordinates(coordinates: List[List[float]], 
                        scale: float = 1.0) -> List[List[float]]:
    """
    Normalize geometry coordinates.
    
    Args:
        coordinates: List of coordinate pairs
        scale: Scale factor to apply
        
    Returns:
        Normalized coordinates
    """
    # Implementation for coordinate normalization logic
    normalized = []
    for coord in coordinates:
        if isinstance(coord, list) and len(coord) >= 2:
            normalized.append([coord[0] * scale, coord[1] * scale])
        else:
            normalized.append(coord)
    return normalized


def calculate_bounding_box(coordinates: List[List[float]]) -> Tuple[float, float, float, float]:
    """
    Calculate bounding box for coordinates.
    
    Args:
        coordinates: List of coordinate pairs
        
    Returns:
        Tuple of (min_x, min_y, max_x, max_y)
    """
    if not coordinates:
        return (0, 0, 0, 0)
    
    x_coords = [coord[0] for coord in coordinates if len(coord) >= 2]
    y_coords = [coord[1] for coord in coordinates if len(coord) >= 2]
    
    if not x_coords or not y_coords:
        return (0, 0, 0, 0)
    
    return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))


def calculate_centroid(coordinates: List[List[float]]) -> List[float]:
    """
    Calculate centroid of coordinates.
    
    Args:
        coordinates: List of coordinate pairs
        
    Returns:
        Centroid coordinates [x, y]
    """
    if not coordinates:
        return [0, 0]
    
    x_sum = sum(coord[0] for coord in coordinates if len(coord) >= 2)
    y_sum = sum(coord[1] for coord in coordinates if len(coord) >= 2)
    count = len([coord for coord in coordinates if len(coord) >= 2])
    
    if count == 0:
        return [0, 0]
    
    return [x_sum / count, y_sum / count]


def calculate_area(coordinates: List[List[float]]) -> float:
    """
    Calculate area of polygon coordinates.
    
    Args:
        coordinates: List of coordinate pairs forming a polygon
        
    Returns:
        Area of the polygon
    """
    if len(coordinates) < 3:
        return 0.0
    
    # Shoelace formula for polygon area
    area = 0.0
    n = len(coordinates)
    
    for i in range(n):
        j = (i + 1) % n
        area += coordinates[i][0] * coordinates[j][1]
        area -= coordinates[j][0] * coordinates[i][1]
    
    return abs(area) / 2.0


def calculate_perimeter(coordinates: List[List[float]]) -> float:
    """
    Calculate perimeter of coordinates.
    
    Args:
        coordinates: List of coordinate pairs
        
    Returns:
        Perimeter length
    """
    if len(coordinates) < 2:
        return 0.0
    
    perimeter = 0.0
    for i in range(len(coordinates) - 1):
        dx = coordinates[i + 1][0] - coordinates[i][0]
        dy = coordinates[i + 1][1] - coordinates[i][1]
        perimeter += math.sqrt(dx * dx + dy * dy)
    
    return perimeter


def transform_geometry(geometry: Geometry, 
                      translation: List[float] = None,
                      scale: float = 1.0,
                      rotation: float = 0.0) -> Geometry:
    """
    Transform geometry with translation, scale, and rotation.
    
    Args:
        geometry: Geometry to transform
        translation: Translation vector [dx, dy]
        scale: Scale factor
        rotation: Rotation angle in radians
        
    Returns:
        Transformed geometry
    """
    if translation is None:
        translation = [0, 0]
    
    transformed_coords = []
    for coord in geometry.coordinates:
        if isinstance(coord, list) and len(coord) >= 2:
            # Apply translation
            x = coord[0] + translation[0]
            y = coord[1] + translation[1]
            
            # Apply scale
            x *= scale
            y *= scale
            
            # Apply rotation
            if rotation != 0:
                cos_r = math.cos(rotation)
                sin_r = math.sin(rotation)
                x_new = x * cos_r - y * sin_r
                y_new = x * sin_r + y * cos_r
                x, y = x_new, y_new
            
            transformed_coords.append([x, y])
        else:
            transformed_coords.append(coord)
    
    return Geometry(
        type=geometry.type,
        coordinates=transformed_coords,
        properties=geometry.properties
    ) 