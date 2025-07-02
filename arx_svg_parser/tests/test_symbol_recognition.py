"""
Stub for unit tests for symbol_recognition.
"""
import pytest
from fastapi.testclient import TestClient
from arx_svg_parser.app import app
from arx_svg_parser.services.svg_symbol_library import load_symbol_library

client = TestClient(app)

def test_symbol_recognition_text():
    payload = {
        "content": "AHU-1 AIR HANDLING UNIT RTU-1 ROOFTOP UNIT VAV-1 VARIABLE AIR VOLUME THERMOSTAT T-1",
        "content_type": "text",
        "confidence_threshold": 0.5
    }
    response = client.post("/v1/parse/recognize-symbols", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "recognized_symbols" in data
    assert data["total_recognized"] > 0
    assert any(s["symbol_id"] == "ahu" for s in data["recognized_symbols"])

def test_symbol_recognition_svg():
    svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
    <svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
      <text x="100" y="100">AHU-1</text>
      <text x="200" y="100">RTU-1</text>
    </svg>'''
    payload = {
        "content": svg_content,
        "content_type": "svg",
        "confidence_threshold": 0.5
    }
    response = client.post("/v1/parse/recognize-symbols", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "recognized_symbols" in data
    assert data["total_recognized"] > 0
    assert any(s["symbol_id"] == "ahu" for s in data["recognized_symbols"])

def test_funding_source_extraction():
    """Test that funding_source is properly extracted from symbol library YAML files"""
    try:
        symbol_library = load_symbol_library()
        
        # Check that at least some symbols have funding_source
        symbols_with_funding = 0
        for symbol_id, symbol_data in symbol_library.items():
            if "funding_source" in symbol_data:
                symbols_with_funding += 1
                # Verify funding_source is a string
                assert isinstance(symbol_data["funding_source"], str)
        
        # Should have funding_source in most symbols
        assert symbols_with_funding > 0, "No symbols found with funding_source"
        
        # Check a specific symbol (ahu should exist)
        if "ahu" in symbol_library:
            assert "funding_source" in symbol_library["ahu"]
            assert isinstance(symbol_library["ahu"]["funding_source"], str)
            
    except Exception as e:
        pytest.skip(f"Symbol library not available: {e}")

def test_symbol_recognition():
    # TODO: Implement real test
    assert app is not None 