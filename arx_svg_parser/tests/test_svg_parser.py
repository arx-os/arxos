"""
Stub for unit tests for svg_parser.
"""
import pytest
from fastapi.testclient import TestClient
from arx_svg_parser.services import svg_parser

def test_parse_svg():
    # TODO: Implement real test
    assert svg_parser.extract_svg_elements("") is not None

def test_extract_svg_elements():
    # TODO: Implement real test
    assert svg_parser.extract_svg_elements('<svg></svg>') == [] 