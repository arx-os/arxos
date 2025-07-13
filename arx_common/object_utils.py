"""
Object Utilities for Arxos Platform

Provides standardized object manipulation functions used across
the platform. Centralizes common object operations to ensure
consistency and reduce code duplication.
"""

from typing import Any, Dict, List, Optional, Union, Set
import json
import structlog
from datetime import datetime
from dataclasses import asdict, is_dataclass

logger = structlog.get_logger(__name__)

def flatten_dict(data: Dict[str, Any], separator: str = ".", prefix: str = "") -> Dict[str, Any]:
    """
    Flatten a nested dictionary.
    
    Args:
        data: Dictionary to flatten
        separator: Separator for nested keys
        prefix: Prefix for current level
        
    Returns:
        Flattened dictionary
    """
    flattened = {}
    
    for key, value in data.items():
        new_key = f"{prefix}{separator}{key}" if prefix else key
        
        if isinstance(value, dict):
            flattened.update(flatten_dict(value, separator, new_key))
        elif isinstance(value, list):
            # Handle lists by creating indexed keys
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    flattened.update(flatten_dict(item, separator, f"{new_key}[{i}]"))
                else:
                    flattened[f"{new_key}[{i}]"] = item
        else:
            flattened[new_key] = value
    
    return flattened

def unflatten_dict(data: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
    """
    Unflatten a flattened dictionary.
    
    Args:
        data: Flattened dictionary
        separator: Separator used for flattening
        
    Returns:
        Nested dictionary
    """
    result = {}
    
    for key, value in data.items():
        keys = key.split(separator)
        current = result
        
        for i, k in enumerate(keys):
            if i == len(keys) - 1:
                current[k] = value
            else:
                if k not in current:
                    current[k] = {}
                current = current[k]
    
    return result

def deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary (takes precedence)
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result

def remove_none_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove None values from dictionary recursively.
    
    Args:
        data: Dictionary to clean
        
    Returns:
        Dictionary with None values removed
    """
    if not isinstance(data, dict):
        return data
    
    cleaned = {}
    for key, value in data.items():
        if value is not None:
            if isinstance(value, dict):
                cleaned_value = remove_none_values(value)
                if cleaned_value:  # Only add if not empty
                    cleaned[key] = cleaned_value
            elif isinstance(value, list):
                cleaned_list = [remove_none_values(item) for item in value if item is not None]
                if cleaned_list:  # Only add if not empty
                    cleaned[key] = cleaned_list
            else:
                cleaned[key] = value
    
    return cleaned

def get_nested_value(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    """
    Get nested value from dictionary using dot notation.
    
    Args:
        data: Dictionary to search
        path: Dot-separated path (e.g., "user.profile.name")
        default: Default value if path not found
        
    Returns:
        Value at path or default
    """
    keys = path.split(".")
    current = data
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current

def set_nested_value(data: Dict[str, Any], path: str, value: Any) -> Dict[str, Any]:
    """
    Set nested value in dictionary using dot notation.
    
    Args:
        data: Dictionary to modify
        path: Dot-separated path (e.g., "user.profile.name")
        value: Value to set
        
    Returns:
        Modified dictionary
    """
    keys = path.split(".")
    result = data.copy()
    current = result
    
    for i, key in enumerate(keys[:-1]):
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value
    return result

def object_to_dict(obj: Any) -> Dict[str, Any]:
    """
    Convert object to dictionary.
    
    Args:
        obj: Object to convert
        
    Returns:
        Dictionary representation
    """
    if isinstance(obj, dict):
        return obj
    elif is_dataclass(obj):
        return asdict(obj)
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    elif hasattr(obj, 'to_dict'):
        return obj.to_dict()
    else:
        logger.warning("object_to_dict_failed",
                      object_type=type(obj).__name__)
        return {}

def dict_to_object(data: Dict[str, Any], obj_class: type) -> Any:
    """
    Convert dictionary to object.
    
    Args:
        data: Dictionary to convert
        obj_class: Class to instantiate
        
    Returns:
        Object instance
    """
    try:
        if is_dataclass(obj_class):
            return obj_class(**data)
        else:
            return obj_class(**data)
    except Exception as e:
        logger.warning("dict_to_object_failed",
                      object_class=obj_class.__name__,
                      error=str(e))
        return None

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """
    Validate that required fields are present in data.
    
    Args:
        data: Data to validate
        required_fields: List of required field names
        
    Returns:
        List of missing field names
    """
    missing_fields = []
    
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)
    
    return missing_fields

def filter_dict(data: Dict[str, Any], allowed_keys: Set[str]) -> Dict[str, Any]:
    """
    Filter dictionary to only include specified keys.
    
    Args:
        data: Dictionary to filter
        allowed_keys: Set of allowed keys
        
    Returns:
        Filtered dictionary
    """
    return {key: value for key, value in data.items() if key in allowed_keys}

def exclude_dict(data: Dict[str, Any], excluded_keys: Set[str]) -> Dict[str, Any]:
    """
    Filter dictionary to exclude specified keys.
    
    Args:
        data: Dictionary to filter
        excluded_keys: Set of keys to exclude
        
    Returns:
        Filtered dictionary
    """
    return {key: value for key, value in data.items() if key not in excluded_keys}

def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Safely get value from dictionary.
    
    Args:
        data: Dictionary to search
        key: Key to get
        default: Default value if key not found
        
    Returns:
        Value or default
    """
    return data.get(key, default)

def safe_set(data: Dict[str, Any], key: str, value: Any) -> Dict[str, Any]:
    """
    Safely set value in dictionary.
    
    Args:
        data: Dictionary to modify
        key: Key to set
        value: Value to set
        
    Returns:
        Modified dictionary
    """
    result = data.copy()
    result[key] = value
    return result

def compare_objects(obj1: Any, obj2: Any, ignore_keys: Optional[Set[str]] = None) -> Dict[str, Any]:
    """
    Compare two objects and return differences.
    
    Args:
        obj1: First object
        obj2: Second object
        ignore_keys: Keys to ignore in comparison
        
    Returns:
        Dictionary with differences
    """
    if ignore_keys is None:
        ignore_keys = set()
    
    dict1 = object_to_dict(obj1)
    dict2 = object_to_dict(obj2)
    
    all_keys = set(dict1.keys()) | set(dict2.keys())
    differences = {}
    
    for key in all_keys:
        if key in ignore_keys:
            continue
            
        value1 = dict1.get(key)
        value2 = dict2.get(key)
        
        if value1 != value2:
            differences[key] = {
                "old": value1,
                "new": value2
            }
    
    return differences

def serialize_object(obj: Any) -> str:
    """
    Serialize object to JSON string.
    
    Args:
        obj: Object to serialize
        
    Returns:
        JSON string
    """
    try:
        # Handle datetime objects
        if isinstance(obj, datetime):
            return obj.isoformat()
        
        # Convert to dict first
        data = object_to_dict(obj)
        
        # Remove None values
        data = remove_none_values(data)
        
        return json.dumps(data, default=str)
    except Exception as e:
        logger.error("serialize_object_failed",
                    object_type=type(obj).__name__,
                    error=str(e))
        return "{}"

def deserialize_object(json_str: str, obj_class: Optional[type] = None) -> Any:
    """
    Deserialize JSON string to object.
    
    Args:
        json_str: JSON string to deserialize
        obj_class: Class to instantiate (optional)
        
    Returns:
        Deserialized object
    """
    try:
        data = json.loads(json_str)
        
        if obj_class:
            return dict_to_object(data, obj_class)
        else:
            return data
    except Exception as e:
        logger.error("deserialize_object_failed",
                    error=str(e))
        return None

def create_object_id() -> str:
    """
    Create a unique object ID.
    
    Returns:
        Unique object ID string
    """
    import uuid
    return str(uuid.uuid4())

def validate_object_structure(data: Dict[str, Any], schema: Dict[str, type]) -> List[str]:
    """
    Validate object structure against schema.
    
    Args:
        data: Data to validate
        schema: Schema defining expected types
        
    Returns:
        List of validation errors
    """
    errors = []
    
    for field, expected_type in schema.items():
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(data[field], expected_type):
            errors.append(f"Field {field} must be {expected_type.__name__}, got {type(data[field]).__name__}")
    
    return errors 