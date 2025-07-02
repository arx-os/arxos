"""
Stub for unit tests for geometry_utils.
"""
import pytest
from fastapi.testclient import TestClient
from arx_svg_parser.utils import geometry_utils

def test_normalize_geometry():
    # TODO: Implement real test
    element = {'x': 0, 'y': 0}
    assert geometry_utils.normalize_geometry(element) == element 