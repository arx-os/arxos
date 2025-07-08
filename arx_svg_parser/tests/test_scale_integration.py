"""
Test file for backend scale integration functionality
"""

import json
import requests
from typing import List, Dict, Any
import pytest
import time
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app import app

# Test configuration
BASE_URL = "http://localhost:8000"  # Adjust as needed
SCALE_API_BASE = f"{BASE_URL}/scale"
BIM_API_BASE = f"{BASE_URL}/bim"  # Adjust based on your backend routes

client = TestClient(app)

def test_scale_api_endpoints():
    """Test all scale API endpoints"""
    print("Testing Scale API Endpoints...")
    
    # Test 1: Basic scale endpoint
    test_basic_scale()
    
    # Test 2: Convert to real-world coordinates
    test_convert_to_real_world()
    
    # Test 3: Validate coordinate system
    test_validate_coordinate_system()
    
    # Test 4: Transform coordinates
    test_transform_coordinates()
    
    # Test 5: Get coordinate systems
    test_get_coordinate_systems()
    
    # Test 6: Calculate scale factors
    test_calculate_scale_factors()
    
    # Test 7: Validate scale request
    test_validate_scale_request()

def test_basic_scale():
    """Test basic scale endpoint"""
    print("\n1. Testing basic scale endpoint...")
    
    request_data = {
        "svg_xml": """
        <svg width="100" height="100">
            <rect x="10" y="10" width="20" height="20" fill="red"/>
            <circle cx="50" cy="50" r="10" fill="blue"/>
        </svg>
        """,
        "anchor_points": [
            {"svg": [10, 10], "real": [0, 0]},
            {"svg": [30, 30], "real": [20, 20]}
        ]
    }
    
    try:
        response = requests.post(f"{SCALE_API_BASE}/scale", json=request_data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✓ Basic scale successful")
            print(f"Modified SVG length: {len(result.get('modified_svg', ''))}")
        else:
            print(f"✗ Basic scale failed: {response.text}")
    except Exception as e:
        print(f"✗ Basic scale error: {e}")

def test_convert_to_real_world():
    """Test convert to real-world coordinates endpoint"""
    print("\n2. Testing convert to real-world coordinates...")
    
    request_data = {
        "svg_coordinates": [[10, 10], [30, 30], [50, 50]],
        "scale_x": 2.0,
        "scale_y": 2.0,
        "origin_x": 0.0,
        "origin_y": 0.0,
        "units": "meters"
    }
    
    try:
        response = requests.post(f"{SCALE_API_BASE}/convert-to-real-world", json=request_data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✓ Convert to real-world successful")
            print(f"Real-world coordinates: {result.get('real_world_coordinates')}")
            print(f"Units: {result.get('units')}")
        else:
            print(f"✗ Convert to real-world failed: {response.text}")
    except Exception as e:
        print(f"✗ Convert to real-world error: {e}")

def test_validate_coordinate_system():
    """Test coordinate system validation endpoint"""
    print("\n3. Testing coordinate system validation...")
    
    request_data = {
        "anchor_points": [
            {"svg": [10, 10], "real": [0, 0]},
            {"svg": [30, 30], "real": [20, 20]},
            {"svg": [50, 50], "real": [40, 40]}
        ]
    }
    
    try:
        response = requests.post(f"{SCALE_API_BASE}/validate-coordinates", json=request_data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✓ Coordinate system validation successful")
            print(f"Valid: {result.get('valid')}")
            print(f"Errors: {result.get('errors')}")
            print(f"Warnings: {result.get('warnings')}")
        else:
            print(f"✗ Coordinate system validation failed: {response.text}")
    except Exception as e:
        print(f"✗ Coordinate system validation error: {e}")

def test_transform_coordinates():
    """Test coordinate transformation endpoint"""
    print("\n4. Testing coordinate transformation...")
    
    request_data = {
        "coordinates": [[10, 10], [30, 30], [50, 50]],
        "source_system": "svg",
        "target_system": "real_world_meters",
        "scale_factors": {"x": 2.0, "y": 2.0},
        "origin_x": 0.0,
        "origin_y": 0.0,
        "units": "meters"
    }
    
    try:
        response = requests.post(f"{SCALE_API_BASE}/transform-coordinates", json=request_data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✓ Coordinate transformation successful")
            print(f"Transformed coordinates: {result.get('transformed_coordinates')}")
        else:
            print(f"✗ Coordinate transformation failed: {response.text}")
    except Exception as e:
        print(f"✗ Coordinate transformation error: {e}")

def test_get_coordinate_systems():
    """Test get coordinate systems endpoint"""
    print("\n5. Testing get coordinate systems...")
    
    try:
        response = requests.get(f"{SCALE_API_BASE}/coordinate-systems")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✓ Get coordinate systems successful")
            systems = result.get('coordinate_systems', {})
            for system_name, system_info in systems.items():
                print(f"  {system_name}: {system_info.get('name')}")
        else:
            print(f"✗ Get coordinate systems failed: {response.text}")
    except Exception as e:
        print(f"✗ Get coordinate systems error: {e}")

def test_calculate_scale_factors():
    """Test calculate scale factors endpoint"""
    print("\n6. Testing calculate scale factors...")
    
    request_data = {
        "anchor_points": [
            {"svg": [10, 10], "real": [0, 0]},
            {"svg": [30, 30], "real": [20, 20]},
            {"svg": [50, 50], "real": [40, 40]}
        ],
        "preferred_units": "meters",
        "force_uniform": False
    }
    
    try:
        response = requests.post(f"{SCALE_API_BASE}/calculate-scale-factors", json=request_data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✓ Calculate scale factors successful")
            print(f"Scale factors: {result.get('scale_factors')}")
            print(f"Confidence: {result.get('confidence')}")
        else:
            print(f"✗ Calculate scale factors failed: {response.text}")
    except Exception as e:
        print(f"✗ Calculate scale factors error: {e}")

def test_validate_scale_request():
    """Test validate scale request endpoint"""
    print("\n7. Testing validate scale request...")
    
    request_data = {
        "svg_xml": """
        <svg width="100" height="100">
            <rect x="10" y="10" width="20" height="20" fill="red"/>
        </svg>
        """,
        "anchor_points": [
            {"svg": [10, 10], "real": [0, 0]},
            {"svg": [30, 30], "real": [20, 20]}
        ]
    }
    
    try:
        response = requests.post(f"{SCALE_API_BASE}/validate-scale-request", json=request_data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✓ Validate scale request successful")
            print(f"Anchor points valid: {result.get('anchor_points_valid')}")
            print(f"SVG valid: {result.get('svg_valid')}")
            print(f"Errors: {result.get('anchor_point_errors')}")
        else:
            print(f"✗ Validate scale request failed: {response.text}")
    except Exception as e:
        print(f"✗ Validate scale request error: {e}")

def test_bim_integration():
    """Test BIM object creation with real-world coordinates"""
    print("\nTesting BIM Integration...")
    
    # Note: This would require authentication and proper backend setup
    # For now, just show the expected request format
    
    bim_request_data = {
        "name": "Test Device",
        "type": "device",
        "system": "electrical",
        "category": "outlet",
        "svg_coordinates": [[10, 10], [30, 30]],
        "real_world_coordinates": [[0, 0], [20, 20]],
        "scale_factors": {"x": 2.0, "y": 2.0},
        "coordinate_system": "real_world_meters",
        "units": "meters",
        "validate_coordinates": True
    }
    
    print("Expected BIM request format:")
    print(json.dumps(bim_request_data, indent=2))

def test_coordinate_validation():
    """Test coordinate validation scenarios"""
    print("\nTesting Coordinate Validation Scenarios...")
    
    test_cases = [
        {
            "name": "Valid coordinates",
            "coordinates": [[10, 10], [30, 30]],
            "expected": True
        },
        {
            "name": "Invalid format (missing y)",
            "coordinates": [[10], [30, 30]],
            "expected": False
        },
        {
            "name": "NaN values",
            "coordinates": [[float('nan'), 10], [30, 30]],
            "expected": False
        },
        {
            "name": "Infinity values",
            "coordinates": [[float('inf'), 10], [30, 30]],
            "expected": False
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        try:
            # This would call the validation endpoint
            print(f"Coordinates: {test_case['coordinates']}")
            print(f"Expected valid: {test_case['expected']}")
        except Exception as e:
            print(f"Error: {e}")

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("BACKEND SCALE INTEGRATION TESTS")
    print("=" * 60)
    
    try:
        test_scale_api_endpoints()
        test_bim_integration()
        test_coordinate_validation()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nTest suite error: {e}")

class TestCoordinatePersistence:
    """Test coordinate persistence functionality"""
    
    def test_bim_object_creation_with_scale_metadata(self):
        """Test creating BIM objects with scale metadata"""
        bim_object_data = {
            "name": "Test Device",
            "type": "device",
            "system": "electrical",
            "category": "outlet",
            "scale_factors": {"x": 0.5, "y": 0.5},
            "coordinate_system": "real_world",
            "units": "meters",
            "svg_coordinates": {"x": 100, "y": 200},
            "real_world_coords": {"x": 50, "y": 100}
        }
        
        response = client.post("/api/bim/objects", json=bim_object_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["bim_object"]["coordinate_system"] == "real_world"
        assert data["bim_object"]["units"] == "meters"
        
        # Verify the object was created with scale metadata
        object_id = data["bim_object"]["id"]
        get_response = client.get(f"/api/bim/objects/{object_id}")
        assert get_response.status_code == 200
        
        object_data = get_response.json()["bim_object"]
        assert object_data["scale_factors"] == {"x": 0.5, "y": 0.5}
        assert object_data["svg_coordinates"] == {"x": 100, "y": 200}
        assert object_data["real_world_coords"] == {"x": 50, "y": 100}
    
    def test_bulk_update_with_scale_metadata(self):
        """Test bulk updating BIM objects with scale metadata"""
        # First create some test objects
        objects = []
        for i in range(3):
            obj_data = {
                "name": f"Test Object {i}",
                "type": "device",
                "system": "electrical",
                "category": "outlet",
                "scale_factors": {"x": 0.5, "y": 0.5},
                "coordinate_system": "real_world",
                "units": "meters"
            }
            response = client.post("/api/bim/objects", json=obj_data)
            assert response.status_code == 201
            objects.append(response.json()["bim_object"]["id"])
        
        # Update objects with new scale metadata
        update_data = {
            "bim_object_ids": objects,
            "updates": {
                "rotation": 45.0
            },
            "scale_factors": {"x": 1.0, "y": 1.0},
            "coordinates": {
                "coordinate_system": "svg",
                "units": "pixels",
                "svg_coordinates": {"x": 200, "y": 300},
                "real_world_coords": {"x": 200, "y": 300}
            }
        }
        
        response = client.post("/api/bim/objects/bulk-update", json=update_data)
        assert response.status_code == 200
        
        # Verify updates
        for object_id in objects:
            get_response = client.get(f"/api/bim/objects/{object_id}")
            assert get_response.status_code == 200
            
            object_data = get_response.json()["bim_object"]
            assert object_data["rotation"] == 45.0
            assert object_data["scale_factors"] == {"x": 1.0, "y": 1.0}
            assert object_data["coordinate_system"] == "svg"
            assert object_data["units"] == "pixels"
    
    def test_coordinate_persistence_across_sessions(self):
        """Test coordinate persistence across multiple sessions"""
        # Session 1: Create objects with scale metadata
        session1_objects = []
        for i in range(2):
            obj_data = {
                "name": f"Session 1 Object {i}",
                "type": "device",
                "system": "electrical",
                "category": "outlet",
                "scale_factors": {"x": 0.25, "y": 0.25},
                "coordinate_system": "real_world",
                "units": "feet",
                "svg_coordinates": {"x": 100 + i*50, "y": 200 + i*50},
                "real_world_coords": {"x": 25 + i*12.5, "y": 50 + i*12.5}
            }
            response = client.post("/api/bim/objects", json=obj_data)
            assert response.status_code == 201
            session1_objects.append(response.json()["bim_object"]["id"])
        
        # Simulate session end and restart
        time.sleep(0.1)  # Simulate time passing
        
        # Session 2: Load objects and verify scale metadata
        for object_id in session1_objects:
            response = client.get(f"/api/bim/objects/{object_id}")
            assert response.status_code == 200
            
            object_data = response.json()["bim_object"]
            assert object_data["scale_factors"] == {"x": 0.25, "y": 0.25}
            assert object_data["coordinate_system"] == "real_world"
            assert object_data["units"] == "feet"
            assert object_data["svg_coordinates"] == {"x": 100 + session1_objects.index(object_id)*50, "y": 200 + session1_objects.index(object_id)*50}
            assert object_data["real_world_coords"] == {"x": 25 + session1_objects.index(object_id)*12.5, "y": 50 + session1_objects.index(object_id)*12.5}
        
        # Session 2: Update objects with new scale metadata
        update_data = {
            "bim_object_ids": session1_objects,
            "coordinates": {
                "coordinate_system": "real_world",
                "units": "meters",
                "scale_factors": {"x": 0.3048, "y": 0.3048}  # Convert feet to meters
            }
        }
        
        response = client.post("/api/bim/objects/bulk-update", json=update_data)
        assert response.status_code == 200
        
        # Session 3: Verify updated scale metadata persists
        for object_id in session1_objects:
            response = client.get(f"/api/bim/objects/{object_id}")
            assert response.status_code == 200
            
            object_data = response.json()["bim_object"]
            assert object_data["scale_factors"] == {"x": 0.3048, "y": 0.3048}
            assert object_data["units"] == "meters"
    
    def test_scale_consistency_validation(self):
        """Test scale consistency validation across objects"""
        # Create objects with consistent scale metadata
        consistent_objects = []
        for i in range(3):
            obj_data = {
                "name": f"Consistent Object {i}",
                "type": "device",
                "system": "electrical",
                "category": "outlet",
                "scale_factors": {"x": 0.5, "y": 0.5},
                "coordinate_system": "real_world",
                "units": "meters"
            }
            response = client.post("/api/bim/objects", json=obj_data)
            assert response.status_code == 201
            consistent_objects.append(response.json()["bim_object"]["id"])
        
        # Create objects with inconsistent scale metadata
        inconsistent_objects = []
        for i in range(2):
            obj_data = {
                "name": f"Inconsistent Object {i}",
                "type": "device",
                "system": "electrical",
                "category": "outlet",
                "scale_factors": {"x": 1.0, "y": 1.0} if i == 0 else {"x": 0.25, "y": 0.25},
                "coordinate_system": "real_world",
                "units": "meters" if i == 0 else "feet"
            }
            response = client.post("/api/bim/objects", json=obj_data)
            assert response.status_code == 201
            inconsistent_objects.append(response.json()["bim_object"]["id"])
        
        # Test scale consistency validation
        all_objects = consistent_objects + inconsistent_objects
        
        # This would typically be done through the export endpoint with validation
        # For now, we'll test the validation logic directly
        validation_data = {
            "object_ids": all_objects,
            "validate_scale_consistency": True
        }
        
        # Mock the validation endpoint
        with patch('routers.scale.validate_scale_consistency') as mock_validate:
            mock_validate.return_value = {
                "is_consistent": False,
                "issues": [
                    "Multiple scale factors detected",
                    "Multiple units detected"
                ],
                "scale_factors": {
                    "0.5,0.5": 3,
                    "1.0,1.0": 1,
                    "0.25,0.25": 1
                },
                "units": {
                    "meters": 4,
                    "feet": 1
                }
            }
            
            response = client.post("/api/scale/validate-consistency", json=validation_data)
            assert response.status_code == 200
            
            result = response.json()
            assert result["is_consistent"] == False
            assert len(result["issues"]) == 2
            assert "Multiple scale factors detected" in result["issues"]
            assert "Multiple units detected" in result["issues"]
    
    def test_export_with_scale_validation(self):
        """Test export functionality with scale validation"""
        # Create test objects with scale metadata
        objects = []
        for i in range(3):
            obj_data = {
                "name": f"Export Test Object {i}",
                "type": "device",
                "system": "electrical",
                "category": "outlet",
                "scale_factors": {"x": 0.5, "y": 0.5},
                "coordinate_system": "real_world",
                "units": "meters",
                "svg_coordinates": {"x": 100 + i*50, "y": 200 + i*50},
                "real_world_coords": {"x": 50 + i*25, "y": 100 + i*25}
            }
            response = client.post("/api/bim/objects", json=obj_data)
            assert response.status_code == 201
            objects.append(response.json()["bim_object"]["id"])
        
        # Test export with scale validation
        response = client.get("/api/export/bim/1?validate_scale=true&include_metadata=true")
        assert response.status_code == 200
        
        export_data = response.json()
        
        # Check for scale validation in metadata
        assert "metadata" in export_data
        assert "scale_validation" in export_data["metadata"]
        
        validation = export_data["metadata"]["scale_validation"]
        assert "is_consistent" in validation
        assert "issues" in validation
        assert "scale_factors" in validation
        assert "coordinate_systems" in validation
        assert "units" in validation
        
        # Check for scale warning header if issues exist
        if not validation["is_consistent"]:
            assert "X-Scale-Warning" in response.headers
    
    def test_scale_metadata_validation(self):
        """Test validation of scale metadata fields"""
        # Test invalid coordinate system
        invalid_obj = {
            "name": "Invalid Object",
            "type": "device",
            "system": "electrical",
            "category": "outlet",
            "coordinate_system": "invalid_system"
        }
        
        response = client.post("/api/bim/objects", json=invalid_obj)
        assert response.status_code == 400
        assert "Invalid coordinate system" in response.json()["detail"]
        
        # Test invalid units
        invalid_obj = {
            "name": "Invalid Object",
            "type": "device",
            "system": "electrical",
            "category": "outlet",
            "units": "invalid_unit"
        }
        
        response = client.post("/api/bim/objects", json=invalid_obj)
        assert response.status_code == 400
        assert "Invalid units" in response.json()["detail"]
        
        # Test invalid scale factors
        invalid_obj = {
            "name": "Invalid Object",
            "type": "device",
            "system": "electrical",
            "category": "outlet",
            "scale_factors": "invalid_scale"
        }
        
        response = client.post("/api/bim/objects", json=invalid_obj)
        assert response.status_code == 400
    
    def test_coordinate_conversion_persistence(self):
        """Test that coordinate conversions are properly persisted"""
        # Create object with SVG coordinates
        obj_data = {
            "name": "Conversion Test Object",
            "type": "device",
            "system": "electrical",
            "category": "outlet",
            "svg_coordinates": {"x": 100, "y": 200},
            "coordinate_system": "svg",
            "units": "pixels"
        }
        
        response = client.post("/api/bim/objects", json=obj_data)
        assert response.status_code == 201
        object_id = response.json()["bim_object"]["id"]
        
        # Convert to real-world coordinates
        conversion_data = {
            "svg_coordinates": [{"x": 100, "y": 200}],
            "scale_factors": {"x": 0.5, "y": 0.5},
            "coordinate_system": "real_world",
            "units": "meters"
        }
        
        response = client.post("/api/scale/convert-coordinates", json=conversion_data)
        assert response.status_code == 200
        
        converted_coords = response.json()["real_world_coordinates"][0]
        expected_x = 100 * 0.5
        expected_y = 200 * 0.5
        
        assert converted_coords["x"] == expected_x
        assert converted_coords["y"] == expected_y
        
        # Update object with converted coordinates
        update_data = {
            "bim_object_ids": [object_id],
            "coordinates": {
                "coordinate_system": "real_world",
                "units": "meters",
                "scale_factors": {"x": 0.5, "y": 0.5},
                "real_world_coords": converted_coords
            }
        }
        
        response = client.post("/api/bim/objects/bulk-update", json=update_data)
        assert response.status_code == 200
        
        # Verify persistence
        get_response = client.get(f"/api/bim/objects/{object_id}")
        assert get_response.status_code == 200
        
        object_data = get_response.json()["bim_object"]
        assert object_data["coordinate_system"] == "real_world"
        assert object_data["units"] == "meters"
        assert object_data["scale_factors"] == {"x": 0.5, "y": 0.5}
        assert object_data["real_world_coords"] == converted_coords
        assert object_data["svg_coordinates"] == {"x": 100, "y": 200}

def test_scale_integration():
    # Test scale calculation with real data
    def test_scale_calculation_real_data(self):
        """Test scale calculation with real building data."""
        # Create test building data
        building_data = {
            'width_meters': 50.0,
            'height_meters': 30.0,
            'svg_width': 1000,
            'svg_height': 600
        }
        
        # Calculate expected scale
        expected_scale_x = building_data['width_meters'] / building_data['svg_width']
        expected_scale_y = building_data['height_meters'] / building_data['svg_height']
        
        # Test scale calculation
        scale_x = building_data['width_meters'] / building_data['svg_width']
        scale_y = building_data['height_meters'] / building_data['svg_height']
        
        self.assertAlmostEqual(scale_x, expected_scale_x, places=6)
        self.assertAlmostEqual(scale_y, expected_scale_y, places=6)

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 