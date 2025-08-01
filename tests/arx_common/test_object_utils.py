"""
Tests for core.shared.object_utils module.

This module contains comprehensive tests for the object manipulation and data
structure utility functions provided by the core.shared.object_utils module.
"""

import pytest
import json
from datetime import datetime
from dataclasses import dataclass

from core.shared.object_utils import (
    flatten_dict,
    unflatten_dict,
    deep_merge,
    remove_none_values,
    get_nested_value,
    set_nested_value,
    object_to_dict,
    dict_to_object,
    validate_required_fields,
    filter_dict,
    exclude_dict,
    safe_get,
    safe_set,
    compare_objects,
    serialize_object,
    deserialize_object,
    create_object_id,
    validate_object_structure
)


@dataclass
class ObjectTestData:
    """Test dataclass for object utilities."""
    id: str
    name: str
    value: int
    optional_field: str = None


class TestObjectUtils:
    """Test object utility functions."""
    
    def test_flatten_dict(self):
        """Test flattening nested dictionary."""
        data = {
            "user": {
                "profile": {
                    "name": "John",
                    "age": 30
                },
                "settings": {
                    "theme": "dark"
                }
            },
            "items": [
                {"id": 1, "name": "item1"},
                {"id": 2, "name": "item2"}
            ]
        }
        
        flattened = flatten_dict(data)
        
        assert "user.profile.name" in flattened
        assert flattened["user.profile.name"] == "John"
        assert "user.settings.theme" in flattened
        assert flattened["user.settings.theme"] == "dark"
        assert "items[0].id" in flattened
        assert flattened["items[0].id"] == 1
    
    def test_flatten_dict_custom_separator(self):
        """Test flattening with custom separator."""
        data = {"a": {"b": {"c": "value"}}}
        flattened = flatten_dict(data, separator="_")
        
        assert "a_b_c" in flattened
        assert flattened["a_b_c"] == "value"
    
    def test_unflatten_dict(self):
        """Test unflattening dictionary."""
        flattened = {
            "user.profile.name": "John",
            "user.profile.age": 30,
            "user.settings.theme": "dark"
        }
        
        unflattened = unflatten_dict(flattened)
        
        assert "user" in unflattened
        assert unflattened["user"]["profile"]["name"] == "John"
        assert unflattened["user"]["profile"]["age"] == 30
        assert unflattened["user"]["settings"]["theme"] == "dark"
    
    def test_deep_merge(self):
        """Test deep merging dictionaries."""
        dict1 = {"a": 1, "b": {"c": 2, "d": 3}}
        dict2 = {"b": {"d": 4, "e": 5}, "f": 6}
        
        merged = deep_merge(dict1, dict2)
        
        assert merged["a"] == 1
        assert merged["b"]["c"] == 2
        assert merged["b"]["d"] == 4  # Overridden by dict2
        assert merged["b"]["e"] == 5
        assert merged["f"] == 6
    
    def test_remove_none_values(self):
        """Test removing None values from dictionary."""
        data = {
            "a": 1,
            "b": None,
            "c": {
                "d": 2,
                "e": None,
                "f": {
                    "g": None
                }
            },
            "h": [1, None, 3]
        }
        
        cleaned = remove_none_values(data)
        
        assert "a" in cleaned
        assert "b" not in cleaned
        assert "c" in cleaned
        assert "e" not in cleaned["c"]
        assert "f" not in cleaned["c"]  # Empty dict removed
        assert "h" in cleaned
        assert None not in cleaned["h"]
    
    def test_get_nested_value(self):
        """Test getting nested value."""
        data = {"user": {"profile": {"name": "John"}}}
        
        assert get_nested_value(data, "user.profile.name") == "John"
        assert get_nested_value(data, "user.profile.age", default=30) == 30
        assert get_nested_value(data, "nonexistent.path") is None
    
    def test_set_nested_value(self):
        """Test setting nested value."""
        data = {"user": {"profile": {"name": "John"}}}
        
        result = set_nested_value(data, "user.profile.age", 30)
        
        assert result["user"]["profile"]["name"] == "John"
        assert result["user"]["profile"]["age"] == 30
    
    def test_object_to_dict_dataclass(self):
        """Test converting dataclass to dictionary."""
        obj = ObjectTestData(id="1", name="test", value=42)
        result = object_to_dict(obj)
        
        assert result["id"] == "1"
        assert result["name"] == "test"
        assert result["value"] == 42
        assert result["optional_field"] is None
    
    def test_object_to_dict_dict(self):
        """Test converting dictionary to dictionary."""
        data = {"key": "value"}
        result = object_to_dict(data)
        assert result == data
    
    def test_object_to_dict_regular_object(self):
        """Test converting regular object to dictionary."""
        class RegularObject:
            def __init__(self):
                self.attr = "value"
        
        obj = RegularObject()
        result = object_to_dict(obj)
        
        assert result["attr"] == "value"
    
    def test_dict_to_object_dataclass(self):
        """Test converting dictionary to dataclass."""
        data = {"id": "1", "name": "test", "value": 42}
        result = dict_to_object(data, ObjectTestData)
        
        assert isinstance(result, ObjectTestData)
        assert result.id == "1"
        assert result.name == "test"
        assert result.value == 42
    
    def test_validate_required_fields(self):
        """Test validating required fields."""
        data = {"name": "John", "age": 30}
        required = ["name", "email"]
        
        missing = validate_required_fields(data, required)
        
        assert "email" in missing
        assert "name" not in missing
    
    def test_filter_dict(self):
        """Test filtering dictionary."""
        data = {"a": 1, "b": 2, "c": 3}
        allowed = {"a", "c"}
        
        filtered = filter_dict(data, allowed)
        
        assert "a" in filtered
        assert "b" not in filtered
        assert "c" in filtered
    
    def test_exclude_dict(self):
        """Test excluding keys from dictionary."""
        data = {"a": 1, "b": 2, "c": 3}
        excluded = {"b"}
        
        filtered = exclude_dict(data, excluded)
        
        assert "a" in filtered
        assert "b" not in filtered
        assert "c" in filtered
    
    def test_safe_get(self):
        """Test safely getting value from dictionary."""
        data = {"key": "value"}
        
        assert safe_get(data, "key") == "value"
        assert safe_get(data, "nonexistent", "default") == "default"
        assert safe_get(data, "nonexistent") is None
    
    def test_safe_set(self):
        """Test safely setting value in dictionary."""
        data = {"key": "old_value"}
        
        result = safe_set(data, "key", "new_value")
        
        assert result["key"] == "new_value"
        assert data["key"] == "old_value"  # Original unchanged
    
    def test_compare_objects(self):
        """Test comparing objects."""
        obj1 = ObjectTestData(id="1", name="John", value=30)
        obj2 = ObjectTestData(id="1", name="Jane", value=30)
        
        differences = compare_objects(obj1, obj2)
        
        assert "name" in differences
        assert differences["name"]["old"] == "John"
        assert differences["name"]["new"] == "Jane"
        assert "id" not in differences  # Same value
    
    def test_compare_objects_with_ignore(self):
        """Test comparing objects with ignored fields."""
        obj1 = ObjectTestData(id="1", name="John", value=30)
        obj2 = ObjectTestData(id="2", name="Jane", value=30)
        
        differences = compare_objects(obj1, obj2, ignore_keys={"id"})
        
        assert "id" not in differences
        assert "name" in differences
    
    def test_serialize_object_dataclass(self):
        """Test serializing dataclass object."""
        obj = ObjectTestData(id="1", name="test", value=42)
        result = serialize_object(obj)
        
        data = json.loads(result)
        assert data["id"] == "1"
        assert data["name"] == "test"
        assert data["value"] == 42
    
    def test_serialize_object_datetime(self):
        """Test serializing datetime object."""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        result = serialize_object(dt)
        
        assert result == dt.isoformat()
    
    def test_deserialize_object(self):
        """Test deserializing object."""
        data = {"id": "1", "name": "test", "value": 42}
        json_str = json.dumps(data)
        
        result = deserialize_object(json_str, ObjectTestData)
        
        assert isinstance(result, ObjectTestData)
        assert result.id == "1"
        assert result.name == "test"
        assert result.value == 42
    
    def test_deserialize_object_no_class(self):
        """Test deserializing without specifying class."""
        data = {"key": "value"}
        json_str = json.dumps(data)
        
        result = deserialize_object(json_str)
        
        assert result == data
    
    def test_create_object_id(self):
        """Test creating object ID."""
        id1 = create_object_id()
        id2 = create_object_id()
        
        assert isinstance(id1, str)
        assert len(id1) > 0
        assert id1 != id2
    
    def test_validate_object_structure(self):
        """Test validating object structure."""
        data = {"name": "John", "age": 30}
        schema = {"name": str, "age": int, "email": str}
        
        errors = validate_object_structure(data, schema)
        
        assert any("Missing required field: email" in error for error in errors)  # Missing required field
        assert not any("name" in error for error in errors)  # Correct type
        assert not any("age" in error for error in errors)  # Correct type
    
    def test_validate_object_structure_type_error(self):
        """Test validating object structure with type error."""
        data = {"name": "John", "age": "30"}  # age should be int
        schema = {"name": str, "age": int}
        
        errors = validate_object_structure(data, schema)
        
        assert any("Field age must be int, got str" in error for error in errors)  # Wrong type


if __name__ == "__main__":
    pytest.main([__file__]) 