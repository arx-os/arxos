"""
Integration tests for building routes using real database.

These tests use a SQLite in-memory database with auto-created tables
to test the actual database operations.
"""

import pytest
from typing import Dict, Any
from fastapi.testclient import TestClient


def _sample_building_payload() -> Dict[str, Any]:
    """Create a sample building payload for testing."""
    return {
        "name": "Test Tower",
        "description": "A test high-rise",
        "building_type": "commercial",
        "status": "active",
        "address": {
            "street": "123 Test St",
            "city": "Testville",
            "state": "TS",
            "postal_code": "12345",
            "country": "United States",
        },
        "coordinates": {"latitude": 40.0, "longitude": -74.0},
        "dimensions": {"length": 100.0, "width": 50.0, "height": 30.0},
        "year_built": 2020,
        "total_floors": 10,
        "tags": ["sample", "test"],
        "metadata": {"key": "value"},
    }


def test_create_and_get_building(client: TestClient):
    """Test creating a building and then retrieving it by ID."""
    # Create building
    payload = _sample_building_payload()
    response = client.post("/api/v1/buildings/", json=payload)
    assert response.status_code == 201, f"Failed to create building: {response.text}"

    created = response.json()
    assert created["id"]
    assert created["name"] == payload["name"]

    # Get building by ID
    building_id = created["id"]
    get_response = client.get(f"/api/v1/buildings/{building_id}")
    assert get_response.status_code == 200, f"Failed to get building: {get_response.text}"

    retrieved = get_response.json()
    assert retrieved["id"] == building_id
    assert retrieved["name"] == payload["name"]


def test_list_buildings_with_pagination(client: TestClient):
    """Test listing buildings with pagination."""
    # Initially empty list
    initial_response = client.get("/api/v1/buildings/")
    assert initial_response.status_code == 200
    initial_data = initial_response.json()
    assert initial_data["total_count"] == 0

    # Create a building
    payload = _sample_building_payload()
    client.post("/api/v1/buildings/", json=payload)

    # List buildings again
    list_response = client.get("/api/v1/buildings/?page=1&page_size=10")
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert list_data["total_count"] == 1
    assert len(list_data["buildings"]) == 1


def test_get_nonexistent_building_returns_404(client: TestClient):
    """Test that getting a non-existent building returns 404."""
    response = client.get("/api/v1/buildings/nonexistent-id")
    assert response.status_code == 404


def test_delete_nonexistent_building_returns_404(client: TestClient):
    """Test that deleting a non-existent building returns 404."""
    response = client.delete("/api/v1/buildings/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.xfail(reason="Domain entity integration required for update flow")
def test_update_building_name_and_status(client: TestClient):
    """Test updating building name and status."""
    # Create building
    payload = _sample_building_payload()
    create_response = client.post("/api/v1/buildings/", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    building_id = created["id"]

    # Update name and status
    update_payload = {"name": "Updated Tower", "status": "maintenance"}
    update_response = client.put(f"/api/v1/buildings/{building_id}", json=update_payload)
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["name"] == "Updated Tower"
    assert updated["status"] == "maintenance"


@pytest.mark.xfail(reason="Domain entity integration required for delete flow")
def test_delete_building_success(client: TestClient):
    """Test successfully deleting a building."""
    # Create building
    payload = _sample_building_payload()
    create_response = client.post("/api/v1/buildings/", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    building_id = created["id"]

    # Delete building
    delete_response = client.delete(f"/api/v1/buildings/{building_id}")
    assert delete_response.status_code == 204

    # Verify building is deleted
    get_response = client.get(f"/api/v1/buildings/{building_id}")
    assert get_response.status_code == 404
