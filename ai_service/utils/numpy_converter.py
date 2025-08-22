"""
Utility to convert numpy types to Python native types for JSON serialization
"""

import numpy as np
from typing import Any, Dict, List, Union


def convert_numpy_to_native(obj: Any) -> Any:
    """
    Recursively convert numpy types to native Python types
    
    Args:
        obj: Object that may contain numpy types
        
    Returns:
        Object with all numpy types converted to native Python types
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_to_native(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_to_native(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_to_native(item) for item in obj)
    elif hasattr(obj, '__dict__'):
        # Handle Pydantic models and other objects with __dict__
        result = {}
        for key, value in obj.__dict__.items():
            if not key.startswith('_'):  # Skip private attributes
                result[key] = convert_numpy_to_native(value)
        return result
    else:
        return obj


def clean_arxobject_dict(obj_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean an ArxObject dictionary for JSON serialization
    
    Args:
        obj_dict: ArxObject dictionary that may contain numpy types
        
    Returns:
        Cleaned dictionary safe for JSON serialization
    """
    cleaned = {}
    
    for key, value in obj_dict.items():
        if key == 'confidence' and isinstance(value, dict):
            # Ensure all confidence scores are floats
            cleaned[key] = {
                'classification': float(value.get('classification', 0)),
                'position': float(value.get('position', 0)),
                'properties': float(value.get('properties', 0)),
                'relationships': float(value.get('relationships', 0)),
                'overall': float(value.get('overall', 0))
            }
        elif key == 'position' and isinstance(value, dict):
            # Ensure position coordinates are integers
            cleaned[key] = {
                'x': int(value.get('x', 0)),
                'y': int(value.get('y', 0)),
                'z': int(value.get('z', 0))
            }
        elif key == 'dimensions' and isinstance(value, dict):
            # Ensure dimensions are integers
            cleaned[key] = {
                'width': int(value.get('width', 0)),
                'height': int(value.get('height', 0)),
                'depth': int(value.get('depth', 0))
            }
        elif key == 'transform' and isinstance(value, dict):
            # Ensure transform matrix is all floats
            if 'matrix' in value:
                cleaned[key] = {
                    'matrix': [[float(cell) for cell in row] for row in value['matrix']]
                }
            else:
                cleaned[key] = value
        else:
            # Recursively clean other values
            cleaned[key] = convert_numpy_to_native(value)
    
    return cleaned