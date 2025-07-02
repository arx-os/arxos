"""
Stub for unit tests for parse.
"""
import pytest
from fastapi.testclient import TestClient
from arx_svg_parser.app import app

client = TestClient(app)

def test_parse_stub():
    response = client.post("/parse", json={"svg_base64": "PHN2ZyB4bWxucz0i..."})
    assert response.status_code == 200
    assert "Parse endpoint stub" in response.json()["message"]

def test_parse_valid():
    # Valid base64-encoded SVG
    import base64
    svg = '<svg xmlns="http://www.w3.org/2000/svg"></svg>'
    svg_b64 = base64.b64encode(svg.encode()).decode()
    response = client.post("/parse", json={"svg_base64": svg_b64})
    assert response.status_code == 200
    assert "summary" in response.json()

def test_parse_invalid_base64():
    response = client.post("/parse", json={"svg_base64": "not_base64!@#"})
    assert response.status_code == 400 or response.status_code == 422

def test_parse_empty_string():
    response = client.post("/parse", json={"svg_base64": ""})
    assert response.status_code == 422

def test_parse_non_svg_content():
    import base64
    not_svg = base64.b64encode(b"not an svg").decode()
    response = client.post("/parse", json={"svg_base64": not_svg})
    assert response.status_code == 400

def test_parse():
    # TODO: Implement real test
    assert app is not None 