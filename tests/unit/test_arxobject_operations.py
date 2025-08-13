"""
Unit tests for ArxObject operations.

Tests the core ArxObject functionality including creation, validation,
hierarchy management, and spatial operations.
"""

import unittest
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Mock ArxObject structure based on the Go implementation
class ArxObject:
    """Mock ArxObject class for testing."""
    
    def __init__(self, id: str = None, **kwargs):
        self.id = id or f"arx:{uuid.uuid4()}"
        self.name = kwargs.get("name", "")
        self.type = kwargs.get("type", "generic")
        self.system = kwargs.get("system", "unknown")
        self.parent_id = kwargs.get("parent_id", "")
        self.children_ids = kwargs.get("children_ids", [])
        
        # Spatial properties
        self.position = kwargs.get("position", {"x": 0.0, "y": 0.0, "z": 0.0})
        self.rotation = kwargs.get("rotation", {"x": 0.0, "y": 0.0, "z": 0.0})
        self.scale = kwargs.get("scale", {"x": 1.0, "y": 1.0, "z": 1.0})
        self.bounds = kwargs.get("bounds", {
            "min": {"x": 0.0, "y": 0.0, "z": 0.0},
            "max": {"x": 1.0, "y": 1.0, "z": 1.0}
        })
        
        # Metadata
        self.properties = kwargs.get("properties", {})
        self.tags = kwargs.get("tags", [])
        self.created_at = kwargs.get("created_at", datetime.now().isoformat())
        self.updated_at = kwargs.get("updated_at", datetime.now().isoformat())
        self.version = kwargs.get("version", 1)
        
        # Building hierarchy
        self.building_id = kwargs.get("building_id", "")
        self.floor_id = kwargs.get("floor_id", "")
        self.room_id = kwargs.get("room_id", "")
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert ArxObject to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "system": self.system,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "position": self.position,
            "rotation": self.rotation,
            "scale": self.scale,
            "bounds": self.bounds,
            "properties": self.properties,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
            "building_id": self.building_id,
            "floor_id": self.floor_id,
            "room_id": self.room_id
        }
        
    def validate(self) -> List[str]:
        """Validate ArxObject and return list of errors."""
        errors = []
        
        # ID validation
        if not self.id or not self.id.startswith("arx:"):
            errors.append("ID must start with 'arx:' prefix")
            
        # Name validation
        if not self.name or len(self.name.strip()) == 0:
            errors.append("Name cannot be empty")
            
        # Type validation
        valid_types = ["building", "floor", "room", "device", "equipment", "generic"]
        if self.type not in valid_types:
            errors.append(f"Type must be one of: {valid_types}")
            
        # System validation
        valid_systems = [
            "electrical", "mechanical", "plumbing", "fire_protection",
            "structural", "architectural", "hvac", "data", "controls", "unknown"
        ]
        if self.system not in valid_systems:
            errors.append(f"System must be one of: {valid_systems}")
            
        # Position validation
        if not self._validate_coordinates(self.position):
            errors.append("Position must have valid x, y, z coordinates")
            
        # Bounds validation
        if not self._validate_bounds(self.bounds):
            errors.append("Bounds must have valid min and max coordinates")
            
        # Hierarchy validation
        if self.parent_id and self.parent_id == self.id:
            errors.append("Object cannot be its own parent")
            
        if self.id in self.children_ids:
            errors.append("Object cannot be its own child")
            
        return errors
        
    def _validate_coordinates(self, coords: Dict[str, float]) -> bool:
        """Validate coordinate structure."""
        if not isinstance(coords, dict):
            return False
        required_keys = ["x", "y", "z"]
        for key in required_keys:
            if key not in coords or not isinstance(coords[key], (int, float)):
                return False
        return True
        
    def _validate_bounds(self, bounds: Dict[str, Dict[str, float]]) -> bool:
        """Validate bounds structure."""
        if not isinstance(bounds, dict):
            return False
        if "min" not in bounds or "max" not in bounds:
            return False
        if not self._validate_coordinates(bounds["min"]):
            return False
        if not self._validate_coordinates(bounds["max"]):
            return False
        return True


class ArxObjectRepository:
    """Mock ArxObject repository for testing."""
    
    def __init__(self):
        self.objects = {}
        
    def create(self, obj: ArxObject) -> ArxObject:
        """Create a new ArxObject."""
        errors = obj.validate()
        if errors:
            raise ValueError(f"Validation errors: {errors}")
            
        # Check for ID conflicts
        if obj.id in self.objects:
            raise ValueError(f"Object with ID {obj.id} already exists")
            
        # Set creation timestamp
        obj.created_at = datetime.now().isoformat()
        obj.updated_at = obj.created_at
        obj.version = 1
        
        self.objects[obj.id] = obj
        return obj
        
    def find_by_id(self, id: str) -> Optional[ArxObject]:
        """Find ArxObject by ID."""
        return self.objects.get(id)
        
    def update(self, obj: ArxObject) -> ArxObject:
        """Update an existing ArxObject."""
        if obj.id not in self.objects:
            raise ValueError(f"Object with ID {obj.id} not found")
            
        errors = obj.validate()
        if errors:
            raise ValueError(f"Validation errors: {errors}")
            
        # Update timestamp and version
        obj.updated_at = datetime.now().isoformat()
        obj.version += 1
        
        self.objects[obj.id] = obj
        return obj
        
    def delete(self, id: str) -> bool:
        """Delete an ArxObject."""
        if id not in self.objects:
            return False
        del self.objects[id]
        return True
        
    def find_all(self) -> List[ArxObject]:
        """Find all ArxObjects."""
        return list(self.objects.values())
        
    def find_children(self, parent_id: str) -> List[ArxObject]:
        """Find all children of a parent object."""
        return [obj for obj in self.objects.values() if obj.parent_id == parent_id]
        
    def find_by_system(self, system: str) -> List[ArxObject]:
        """Find objects by system."""
        return [obj for obj in self.objects.values() if obj.system == system]
        
    def find_in_bounds(self, min_coords: Dict[str, float], max_coords: Dict[str, float]) -> List[ArxObject]:
        """Find objects within spatial bounds."""
        results = []
        for obj in self.objects.values():
            if self._object_in_bounds(obj, min_coords, max_coords):
                results.append(obj)
        return results
        
    def _object_in_bounds(self, obj: ArxObject, min_coords: Dict[str, float], max_coords: Dict[str, float]) -> bool:
        """Check if object is within bounds."""
        pos = obj.position
        return (min_coords["x"] <= pos["x"] <= max_coords["x"] and
                min_coords["y"] <= pos["y"] <= max_coords["y"] and
                min_coords["z"] <= pos["z"] <= max_coords["z"])


class TestArxObjectValidation(unittest.TestCase):
    """Test ArxObject validation functionality."""
    
    def test_valid_arxobject(self):
        """Test creating a valid ArxObject."""
        obj = ArxObject(
            name="Test Object",
            type="device",
            system="electrical",
            position={"x": 1.0, "y": 2.0, "z": 3.0}
        )
        
        errors = obj.validate()
        self.assertEqual(len(errors), 0, f"Valid object should have no errors: {errors}")
        
    def test_id_validation(self):
        """Test ID validation rules."""
        # Missing arx: prefix
        obj = ArxObject(id="invalid_id", name="Test")
        errors = obj.validate()
        self.assertTrue(any("arx:" in error for error in errors))
        
        # Valid ID
        obj = ArxObject(id="arx:test_123", name="Test")
        errors = obj.validate()
        id_errors = [e for e in errors if "arx:" in e]
        self.assertEqual(len(id_errors), 0)
        
    def test_name_validation(self):
        """Test name validation rules."""
        # Empty name
        obj = ArxObject(name="")
        errors = obj.validate()
        self.assertTrue(any("Name cannot be empty" in error for error in errors))
        
        # Whitespace only name
        obj = ArxObject(name="   ")
        errors = obj.validate()
        self.assertTrue(any("Name cannot be empty" in error for error in errors))
        
        # Valid name
        obj = ArxObject(name="Valid Name")
        errors = obj.validate()
        name_errors = [e for e in errors if "Name" in e]
        self.assertEqual(len(name_errors), 0)
        
    def test_type_validation(self):
        """Test type validation rules."""
        # Invalid type
        obj = ArxObject(name="Test", type="invalid_type")
        errors = obj.validate()
        self.assertTrue(any("Type must be one of" in error for error in errors))
        
        # Valid types
        valid_types = ["building", "floor", "room", "device", "equipment", "generic"]
        for obj_type in valid_types:
            with self.subTest(type=obj_type):
                obj = ArxObject(name="Test", type=obj_type)
                errors = obj.validate()
                type_errors = [e for e in errors if "Type must be one of" in e]
                self.assertEqual(len(type_errors), 0)
                
    def test_system_validation(self):
        """Test system validation rules."""
        # Invalid system
        obj = ArxObject(name="Test", system="invalid_system")
        errors = obj.validate()
        self.assertTrue(any("System must be one of" in error for error in errors))
        
        # Valid systems
        valid_systems = [
            "electrical", "mechanical", "plumbing", "fire_protection",
            "structural", "architectural", "hvac", "data", "controls", "unknown"
        ]
        for system in valid_systems:
            with self.subTest(system=system):
                obj = ArxObject(name="Test", system=system)
                errors = obj.validate()
                system_errors = [e for e in errors if "System must be one of" in e]
                self.assertEqual(len(system_errors), 0)
                
    def test_position_validation(self):
        """Test position validation rules."""
        # Missing coordinates
        obj = ArxObject(name="Test", position={"x": 1.0, "y": 2.0})
        errors = obj.validate()
        self.assertTrue(any("Position must have valid" in error for error in errors))
        
        # Invalid coordinate types
        obj = ArxObject(name="Test", position={"x": "invalid", "y": 2.0, "z": 3.0})
        errors = obj.validate()
        self.assertTrue(any("Position must have valid" in error for error in errors))
        
        # Valid position
        obj = ArxObject(name="Test", position={"x": 1.0, "y": 2.0, "z": 3.0})
        errors = obj.validate()
        position_errors = [e for e in errors if "Position must have valid" in e]
        self.assertEqual(len(position_errors), 0)
        
    def test_hierarchy_validation(self):
        """Test hierarchy validation rules."""
        # Self-parent
        obj = ArxObject(name="Test", id="arx:test", parent_id="arx:test")
        errors = obj.validate()
        self.assertTrue(any("cannot be its own parent" in error for error in errors))
        
        # Self-child
        obj = ArxObject(name="Test", id="arx:test", children_ids=["arx:test", "arx:other"])
        errors = obj.validate()
        self.assertTrue(any("cannot be its own child" in error for error in errors))
        
        # Valid hierarchy
        obj = ArxObject(name="Test", id="arx:test", parent_id="arx:parent", children_ids=["arx:child1", "arx:child2"])
        errors = obj.validate()
        hierarchy_errors = [e for e in errors if "own parent" in e or "own child" in e]
        self.assertEqual(len(hierarchy_errors), 0)


class TestArxObjectRepository(unittest.TestCase):
    """Test ArxObject repository operations."""
    
    def setUp(self):
        """Set up test environment."""
        self.repo = ArxObjectRepository()
        
    def test_create_object(self):
        """Test creating an object."""
        obj = ArxObject(
            name="Test Device",
            type="device",
            system="electrical"
        )
        
        created_obj = self.repo.create(obj)
        
        self.assertEqual(created_obj.name, "Test Device")
        self.assertEqual(created_obj.type, "device")
        self.assertEqual(created_obj.system, "electrical")
        self.assertEqual(created_obj.version, 1)
        self.assertIsNotNone(created_obj.created_at)
        self.assertIsNotNone(created_obj.updated_at)
        
    def test_create_invalid_object(self):
        """Test creating an invalid object."""
        obj = ArxObject(name="", type="invalid_type")
        
        with self.assertRaises(ValueError):
            self.repo.create(obj)
            
    def test_create_duplicate_id(self):
        """Test creating object with duplicate ID."""
        obj1 = ArxObject(id="arx:test", name="First")
        obj2 = ArxObject(id="arx:test", name="Second")
        
        self.repo.create(obj1)
        
        with self.assertRaises(ValueError) as context:
            self.repo.create(obj2)
        self.assertIn("already exists", str(context.exception))
        
    def test_find_by_id(self):
        """Test finding object by ID."""
        obj = ArxObject(id="arx:findme", name="Find Me")
        self.repo.create(obj)
        
        found_obj = self.repo.find_by_id("arx:findme")
        self.assertIsNotNone(found_obj)
        self.assertEqual(found_obj.name, "Find Me")
        
        not_found = self.repo.find_by_id("arx:notfound")
        self.assertIsNone(not_found)
        
    def test_update_object(self):
        """Test updating an object."""
        obj = ArxObject(name="Original Name", type="device")
        created_obj = self.repo.create(obj)
        original_version = created_obj.version
        
        # Update the object
        created_obj.name = "Updated Name"
        updated_obj = self.repo.update(created_obj)
        
        self.assertEqual(updated_obj.name, "Updated Name")
        self.assertEqual(updated_obj.version, original_version + 1)
        self.assertNotEqual(updated_obj.updated_at, updated_obj.created_at)
        
    def test_update_nonexistent_object(self):
        """Test updating non-existent object."""
        obj = ArxObject(id="arx:nonexistent", name="Test")
        
        with self.assertRaises(ValueError) as context:
            self.repo.update(obj)
        self.assertIn("not found", str(context.exception))
        
    def test_delete_object(self):
        """Test deleting an object."""
        obj = ArxObject(name="Delete Me")
        created_obj = self.repo.create(obj)
        
        # Verify object exists
        self.assertIsNotNone(self.repo.find_by_id(created_obj.id))
        
        # Delete object
        result = self.repo.delete(created_obj.id)
        self.assertTrue(result)
        
        # Verify object is gone
        self.assertIsNone(self.repo.find_by_id(created_obj.id))
        
    def test_delete_nonexistent_object(self):
        """Test deleting non-existent object."""
        result = self.repo.delete("arx:nonexistent")
        self.assertFalse(result)
        
    def test_find_all(self):
        """Test finding all objects."""
        # Start with empty repository
        self.assertEqual(len(self.repo.find_all()), 0)
        
        # Add some objects
        for i in range(3):
            obj = ArxObject(name=f"Object {i}", type="device")
            self.repo.create(obj)
            
        all_objects = self.repo.find_all()
        self.assertEqual(len(all_objects), 3)
        
    def test_find_children(self):
        """Test finding child objects."""
        # Create parent
        parent = ArxObject(id="arx:parent", name="Parent")
        self.repo.create(parent)
        
        # Create children
        for i in range(3):
            child = ArxObject(name=f"Child {i}", parent_id="arx:parent")
            self.repo.create(child)
            
        # Create unrelated object
        unrelated = ArxObject(name="Unrelated")
        self.repo.create(unrelated)
        
        children = self.repo.find_children("arx:parent")
        self.assertEqual(len(children), 3)
        
        for child in children:
            self.assertEqual(child.parent_id, "arx:parent")
            
    def test_find_by_system(self):
        """Test finding objects by system."""
        # Create objects in different systems
        systems = ["electrical", "mechanical", "plumbing"]
        for i, system in enumerate(systems):
            for j in range(2):
                obj = ArxObject(name=f"{system} {j}", system=system)
                self.repo.create(obj)
                
        # Find electrical objects
        electrical_objects = self.repo.find_by_system("electrical")
        self.assertEqual(len(electrical_objects), 2)
        
        for obj in electrical_objects:
            self.assertEqual(obj.system, "electrical")
            
    def test_find_in_bounds(self):
        """Test spatial bounds queries."""
        # Create objects at different positions
        positions = [
            {"x": 0.0, "y": 0.0, "z": 0.0},
            {"x": 5.0, "y": 5.0, "z": 5.0},
            {"x": 10.0, "y": 10.0, "z": 10.0},
            {"x": 15.0, "y": 15.0, "z": 15.0}
        ]
        
        for i, pos in enumerate(positions):
            obj = ArxObject(name=f"Object {i}", position=pos)
            self.repo.create(obj)
            
        # Query for objects in bounds (0-6 range)
        min_coords = {"x": 0.0, "y": 0.0, "z": 0.0}
        max_coords = {"x": 6.0, "y": 6.0, "z": 6.0}
        
        objects_in_bounds = self.repo.find_in_bounds(min_coords, max_coords)
        self.assertEqual(len(objects_in_bounds), 2)  # Objects at (0,0,0) and (5,5,5)
        
        for obj in objects_in_bounds:
            pos = obj.position
            self.assertLessEqual(pos["x"], 6.0)
            self.assertLessEqual(pos["y"], 6.0)
            self.assertLessEqual(pos["z"], 6.0)


class TestArxObjectHierarchy(unittest.TestCase):
    """Test ArxObject hierarchy management."""
    
    def setUp(self):
        """Set up test environment."""
        self.repo = ArxObjectRepository()
        
    def test_building_hierarchy(self):
        """Test building -> floor -> room hierarchy."""
        # Create building
        building = ArxObject(
            id="arx:building_1",
            name="Test Building",
            type="building",
            system="architectural"
        )
        self.repo.create(building)
        
        # Create floor
        floor = ArxObject(
            id="arx:floor_1",
            name="Ground Floor",
            type="floor",
            system="architectural",
            parent_id="arx:building_1",
            building_id="arx:building_1"
        )
        self.repo.create(floor)
        
        # Create room
        room = ArxObject(
            id="arx:room_1",
            name="Conference Room",
            type="room",
            system="architectural",
            parent_id="arx:floor_1",
            building_id="arx:building_1",
            floor_id="arx:floor_1"
        )
        self.repo.create(room)
        
        # Verify hierarchy
        floors = self.repo.find_children("arx:building_1")
        self.assertEqual(len(floors), 1)
        self.assertEqual(floors[0].id, "arx:floor_1")
        
        rooms = self.repo.find_children("arx:floor_1")
        self.assertEqual(len(rooms), 1)
        self.assertEqual(rooms[0].id, "arx:room_1")
        
    def test_device_placement(self):
        """Test placing devices in rooms."""
        # Create room
        room = ArxObject(
            id="arx:room_1",
            name="Office",
            type="room"
        )
        self.repo.create(room)
        
        # Create devices in room
        devices = [
            {"name": "Outlet 1", "system": "electrical", "position": {"x": 1.0, "y": 0.0, "z": 1.5}},
            {"name": "Light 1", "system": "electrical", "position": {"x": 2.0, "y": 2.0, "z": 3.0}},
            {"name": "HVAC Vent", "system": "mechanical", "position": {"x": 3.0, "y": 3.0, "z": 3.0}}
        ]
        
        for device_data in devices:
            device = ArxObject(
                name=device_data["name"],
                type="device",
                system=device_data["system"],
                position=device_data["position"],
                parent_id="arx:room_1",
                room_id="arx:room_1"
            )
            self.repo.create(device)
            
        # Verify devices in room
        room_devices = self.repo.find_children("arx:room_1")
        self.assertEqual(len(room_devices), 3)
        
        # Find electrical devices
        electrical_devices = [d for d in room_devices if d.system == "electrical"]
        self.assertEqual(len(electrical_devices), 2)


class TestArxObjectSpatialOperations(unittest.TestCase):
    """Test ArxObject spatial operations."""
    
    def setUp(self):
        """Set up test environment."""
        self.repo = ArxObjectRepository()
        
    def test_position_updates(self):
        """Test updating object positions."""
        obj = ArxObject(
            name="Mobile Device",
            type="device",
            position={"x": 0.0, "y": 0.0, "z": 0.0}
        )
        created_obj = self.repo.create(obj)
        
        # Update position
        created_obj.position = {"x": 10.0, "y": 5.0, "z": 2.0}
        updated_obj = self.repo.update(created_obj)
        
        self.assertEqual(updated_obj.position["x"], 10.0)
        self.assertEqual(updated_obj.position["y"], 5.0)
        self.assertEqual(updated_obj.position["z"], 2.0)
        
    def test_bounds_calculation(self):
        """Test object bounds calculations."""
        obj = ArxObject(
            name="Device with Bounds",
            position={"x": 5.0, "y": 5.0, "z": 5.0},
            bounds={
                "min": {"x": 4.0, "y": 4.0, "z": 4.0},
                "max": {"x": 6.0, "y": 6.0, "z": 6.0}
            }
        )
        
        errors = obj.validate()
        bounds_errors = [e for e in errors if "Bounds" in e]
        self.assertEqual(len(bounds_errors), 0)
        
    def test_spatial_queries(self):
        """Test spatial query functionality."""
        # Create grid of objects
        for x in range(0, 10, 2):
            for y in range(0, 10, 2):
                obj = ArxObject(
                    name=f"Object_{x}_{y}",
                    position={"x": float(x), "y": float(y), "z": 0.0}
                )
                self.repo.create(obj)
                
        # Query center area
        center_objects = self.repo.find_in_bounds(
            {"x": 2.0, "y": 2.0, "z": -1.0},
            {"x": 6.0, "y": 6.0, "z": 1.0}
        )
        
        # Should find objects at (2,2), (2,4), (4,2), (4,4), (6,6) - but (6,6) is outside Y bound
        expected_count = 4  # (2,2), (2,4), (4,2), (4,4)
        self.assertEqual(len(center_objects), expected_count)


if __name__ == "__main__":
    # Run specific test groups
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "validation":
            suite = unittest.TestLoader().loadTestsFromTestCase(TestArxObjectValidation)
        elif sys.argv[1] == "repository":
            suite = unittest.TestLoader().loadTestsFromTestCase(TestArxObjectRepository)
        elif sys.argv[1] == "hierarchy":
            suite = unittest.TestLoader().loadTestsFromTestCase(TestArxObjectHierarchy)
        elif sys.argv[1] == "spatial":
            suite = unittest.TestLoader().loadTestsFromTestCase(TestArxObjectSpatialOperations)
        else:
            suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    else:
        suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with error code if tests failed
    sys.exit(0 if result.wasSuccessful() else 1)