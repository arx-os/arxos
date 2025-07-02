"""
Stub for unit tests for ingest.
"""
import pytest
from fastapi.testclient import TestClient
from arx_svg_parser.app import app

client = TestClient(app)

def test_ingest_stub():
    response = client.post("/ingest", json={
        "file_type": "image",
        "file_data": "<base64-encoded file>",
        "building_id": "bldg-123",
        "floor_label": "1st Floor"
    })
    assert response.status_code == 200
    assert "Ingest endpoint stub" in response.json()["message"]

def test_ingest_svg():
    response = client.post("/ingest", json={
        "file_type": "image",
        "file_data": "<base64-encoded file>",
        "building_id": "bldg-123",
        "floor_label": "1st Floor"
    })
    assert response.status_code == 200
    data = response.json()
    assert "svg" in data
    assert "summary" in data
    assert "Dummy Floorplan" in data["svg"]

def test_ingest_invalid_file_type():
    response = client.post("/ingest", json={
        "file_type": "doc",
        "file_data": "<base64-encoded file>",
        "building_id": "bldg-123",
        "floor_label": "1st Floor"
    })
    assert response.status_code == 422

def test_ingest_empty_file_data():
    response = client.post("/ingest", json={
        "file_type": "image",
        "file_data": "",
        "building_id": "bldg-123",
        "floor_label": "1st Floor"
    })
    assert response.status_code == 422

def test_ingest_missing_building_id():
    response = client.post("/ingest", json={
        "file_type": "image",
        "file_data": "<base64-encoded file>",
        "floor_label": "1st Floor"
    })
    assert response.status_code == 422

def test_ingest_missing_floor_label():
    response = client.post("/ingest", json={
        "file_type": "image",
        "file_data": "<base64-encoded file>",
        "building_id": "bldg-123"
    })
    assert response.status_code == 422

def test_ingest():
    # TODO: Implement real test
    assert app is not None 