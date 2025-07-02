"""
Stub for unit tests for classifier.
"""
import pytest
from fastapi.testclient import TestClient
from arx_svg_parser.services import classifier

def test_classify_elements():
    # TODO: Implement real test
    assert classifier.classify_elements([]) == [] 