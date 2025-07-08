import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_bim_extraction():
    svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
    <svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
      <g id="arx-objects">
        <g id="ahu_12345678" class="arx-symbol arx-ahu" transform="translate(100,100)" 
           data-symbol-id="ahu" data-symbol-name="Air Handling Unit (AHU)" 
           data-system="mechanical" data-confidence="0.9">
          <rect x="0" y="0" width="40" height="20" fill="#ccc" stroke="#000"/>
          <text x="20" y="15" font-size="10" text-anchor="middle">AHU</text>
        </g>
        <g id="thermostat_87654321" class="arx-symbol arx-thermostat" transform="translate(200,150)" 
           data-symbol-id="thermostat" data-symbol-name="Thermostat" 
           data-system="mechanical" data-confidence="0.8">
          <circle cx="0" cy="0" r="15" fill="#fff" stroke="#000"/>
          <text x="0" y="5" font-size="8" text-anchor="middle">T</text>
        </g>
      </g>
      <text x="100" y="200">ROOM 101 - CONFERENCE ROOM</text>
      <text x="200" y="200">THERMOSTAT T-1</text>
    </svg>'''
    data = {
        "svg_content": svg_content,
        "building_id": "TEST_BUILDING",
        "floor_label": "FLOOR_1"
    }
    response = client.post("/v1/parse/extract-bim", data=data)
    assert response.status_code == 200
    result = response.json()
    assert "devices" in result
    assert "rooms" in result
    assert "systems" in result
    assert len(result["devices"]) > 0
    assert len(result["rooms"]) > 0 