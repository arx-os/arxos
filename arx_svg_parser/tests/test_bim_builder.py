"""
Stub for unit tests for bim_builder.
"""
import pytest
from fastapi.testclient import TestClient
from arx_svg_parser.services import bim_builder

def test_build_bim_model():
    # TODO: Implement real test
    assert bim_builder.build_bim_model([]) is not None 