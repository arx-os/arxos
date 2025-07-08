import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_annotate_stub():
    response = client.post("/annotate", json={
        "svg_id": "bldg1-floor2",
        "annotations": [
            {"type": "note", "coordinates": [1200, 900], "text": "Test note"}
        ]
    })
    assert response.status_code == 200
    assert "Annotate endpoint stub" in response.json()["message"]

def test_annotate_svg():
    # Minimal SVG string
    svg_xml = '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"></svg>'
    response = client.post("/annotate", json={
        "svg_xml": svg_xml,
        "annotations": [
            {"type": "note", "coordinates": [50, 50], "text": "Test note"},
            {"type": "device", "coordinates": [80, 80], "id": "Device1"}
        ]
    })
    assert response.status_code == 200
    assert "modified_svg" in response.json()
    assert "<text" in response.json()["modified_svg"]
    assert "<circle" in response.json()["modified_svg"]

def test_annotate_invalid_type():
    svg_xml = '<svg xmlns="http://www.w3.org/2000/svg"></svg>'
    response = client.post("/annotate", json={
        "svg_xml": svg_xml,
        "annotations": [
            {"type": "invalid", "coordinates": [10, 10]}
        ]
    })
    assert response.status_code == 422

def test_annotate_bad_coordinates():
    svg_xml = '<svg xmlns="http://www.w3.org/2000/svg"></svg>'
    response = client.post("/annotate", json={
        "svg_xml": svg_xml,
        "annotations": [
            {"type": "note", "coordinates": [10]}
        ]
    })
    assert response.status_code == 422

def test_annotate_missing_svg_xml():
    response = client.post("/annotate", json={
        "annotations": [
            {"type": "note", "coordinates": [10, 10]}
        ]
    })
    assert response.status_code == 422

def test_annotate_empty_annotations():
    svg_xml = '<svg xmlns="http://www.w3.org/2000/svg"></svg>'
    response = client.post("/annotate", json={
        "svg_xml": svg_xml,
        "annotations": []
    })
    assert response.status_code == 200
    assert "modified_svg" in response.json() 