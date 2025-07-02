"""
Stub for unit tests for scale.
"""
import pytest
from fastapi.testclient import TestClient
from arx_svg_parser.app import app

client = TestClient(app)

def test_scale_stub():
    response = client.post("/scale", json={
        "svg_id": "bldg1-floor2",
        "anchor_points": [
            {"svg": [0, 0], "real": [0.0, 0.0]},
            {"svg": [5000, 0], "real": [10.0, 0.0]},
            {"svg": [0, 5000], "real": [0.0, 10.0]}
        ]
    })
    assert response.status_code == 200
    assert "Scale endpoint stub" in response.json()["message"]

def test_scale_svg():
    svg_xml = '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect x="0" y="0" width="10" height="10"/></svg>'
    response = client.post("/scale", json={
        "svg_xml": svg_xml,
        "anchor_points": [
            {"svg": [0, 0], "real": [0.0, 0.0]},
            {"svg": [10, 0], "real": [20.0, 0.0]}
        ]
    })
    assert response.status_code == 200
    assert "modified_svg" in response.json()
    # Check that the rect x attribute was scaled
    assert "x=\"0.0\"" in response.json()["modified_svg"]

def test_scale_less_than_two_anchors():
    svg_xml = '<svg xmlns="http://www.w3.org/2000/svg"></svg>'
    response = client.post("/scale", json={
        "svg_xml": svg_xml,
        "anchor_points": [
            {"svg": [0, 0], "real": [0.0, 0.0]}
        ]
    })
    assert response.status_code == 422

def test_scale_bad_anchor_format():
    svg_xml = '<svg xmlns="http://www.w3.org/2000/svg"></svg>'
    response = client.post("/scale", json={
        "svg_xml": svg_xml,
        "anchor_points": [
            {"svg": [0], "real": [0.0, 0.0]},
            {"svg": [10, 0], "real": [20.0, 0.0]}
        ]
    })
    assert response.status_code == 422

def test_scale_invalid_svg():
    response = client.post("/scale", json={
        "svg_xml": "not an svg",
        "anchor_points": [
            {"svg": [0, 0], "real": [0.0, 0.0]},
            {"svg": [10, 0], "real": [20.0, 0.0]}
        ]
    })
    assert response.status_code == 400

def test_scale():
    # TODO: Implement real test
    assert app is not None 