"""
SVGX Engine - Core Functionality Tests

Comprehensive test suite for core SVGX functionality:
- Main application endpoints
- Precision management
- WASM integration
- Interactive behaviors
- Performance validation

CTO Targets:
- <16ms UI response time
- <32ms redraw time
- <100ms physics simulation
"""

import pytest
import asyncio
import time
import json
from typing import Dict, Any
from unittest.mock import Mock, patch

# SVGX Engine imports
from svgx_engine.app import app
from svgx_engine.utils.precision_manager import (
    SVGXPrecisionManager, PrecisionLevel, PrecisionConfig, FixedPointNumber
)
from svgx_engine.utils.wasm_integration import WASMIntegration, WASMOperationType
from svgx_engine.parser.parser import SVGXParser
from svgx_engine.runtime.evaluator import SVGXEvaluator


class TestMainApplication:
    """Test main FastAPI application endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"
        assert "performance" in data
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
    
    def test_parse_svgx(self, client):
        """Test SVGX parsing endpoint."""
        svgx_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
  <arx:object id="rm201" type="architecture.room" system="architecture">
    <arx:geometry x="0" y="0" width="3000mm" height="4000mm"/>
  </arx:object>
  <path d="M0,0 L3000,0 L3000,4000 L0,4000 Z"
        style="stroke:black;fill:none;stroke-width:2"
        arx:layer="walls"
        arx:precision="1mm"/>
</svg>'''
        
        response = client.post("/parse", json={"content": svgx_content})
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "elements" in data
        assert data["count"] > 0
        assert "duration_ms" in data
    
    def test_evaluate_behavior(self, client):
        """Test behavior evaluation endpoint."""
        svgx_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
  <arx:object id="lf01" type="electrical.light_fixture" system="electrical">
    <arx:behavior>
      <variables>
        <voltage unit="V">120</voltage>
        <power unit="W">20</power>
      </variables>
      <calculations>
        <current formula="power / voltage"/>
      </calculations>
    </arx:behavior>
  </arx:object>
</svg>'''
        
        response = client.post("/evaluate", json={"content": svgx_content})
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "results" in data
        assert "duration_ms" in data
    
    def test_simulate_physics(self, client):
        """Test physics simulation endpoint."""
        svgx_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
  <arx:object id="obj01" type="mechanical.component" system="mechanical">
    <arx:physics>
      <mass unit="kg">2.5</mass>
      <anchor>ceiling</anchor>
      <forces>
        <force type="gravity" direction="down" value="9.81"/>
      </forces>
    </arx:physics>
  </arx:object>
</svg>'''
        
        response = client.post("/simulate", json={"content": svgx_content})
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "simulation" in data
        assert "duration_ms" in data
    
    def test_interactive_operations(self, client):
        """Test interactive operation endpoints."""
        # Test click operation
        click_data = {
            "operation": "click",
            "element_id": "test_element",
            "coordinates": {"x": 100, "y": 200},
            "modifiers": {"ctrl": False}
        }
        
        response = client.post("/interactive", json=click_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["operation"] == "click"
        assert "result" in data
        assert "duration_ms" in data
        
        # Test drag operations
        drag_start_data = {
            "operation": "drag_start",
            "element_id": "test_element",
            "coordinates": {"x": 100, "y": 200},
            "modifiers": {}
        }
        
        response = client.post("/interactive", json=drag_start_data)
        assert response.status_code == 200
        
        # Test hover operation
        hover_data = {
            "operation": "hover",
            "element_id": "test_element",
            "coordinates": {"x": 150, "y": 250},
            "modifiers": {}
        }
        
        response = client.post("/interactive", json=hover_data)
        assert response.status_code == 200
    
    def test_precision_operations(self, client):
        """Test precision operations."""
        precision_data = {
            "level": "edit",
            "coordinates": {"x": 123.456, "y": 789.012, "z": 0}
        }
        
        response = client.post("/precision", json=precision_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["precision_level"] == "edit"
        assert data["precision_value_mm"] == 0.01
    
    def test_compilation_endpoints(self, client):
        """Test compilation endpoints."""
        svgx_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
  <rect x="0" y="0" width="100" height="100" style="fill:red"/>
</svg>'''
        
        # Test SVG compilation
        response = client.post("/compile/svg", json={"content": svgx_content})
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["format"] == "svg"
        assert "content" in data
        
        # Test JSON compilation
        response = client.post("/compile/json", json={"content": svgx_content})
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["format"] == "json"
        assert "content" in data
    
    def test_get_state(self, client):
        """Test getting interactive state."""
        response = client.get("/state")
        assert response.status_code == 200
        
        data = response.json()
        assert "selected_elements" in data
        assert "hovered_element" in data
        assert "drag_state" in data
        assert "constraints" in data
        assert "precision_level" in data


class TestPrecisionManager:
    """Test precision management functionality."""
    
    @pytest.fixture
    def precision_manager(self):
        """Create precision manager instance."""
        return SVGXPrecisionManager()
    
    def test_precision_levels(self, precision_manager):
        """Test precision level management."""
        # Test UI precision
        precision_manager.set_precision_level(PrecisionLevel.UI)
        assert precision_manager.get_precision_value() == 0.1
        
        # Test Edit precision
        precision_manager.set_precision_level(PrecisionLevel.EDIT)
        assert precision_manager.get_precision_value() == 0.01
        
        # Test Compute precision
        precision_manager.set_precision_level(PrecisionLevel.COMPUTE)
        assert precision_manager.get_precision_value() == 0.001
    
    def test_coordinate_rounding(self, precision_manager):
        """Test coordinate rounding functionality."""
        coordinates = {"x": 123.456789, "y": 789.012345, "z": 0.123456}
        
        # Test UI precision rounding
        precision_manager.set_precision_level(PrecisionLevel.UI)
        rounded_ui = precision_manager.round_coordinates(coordinates)
        
        assert abs(rounded_ui["x"] - 123.5) < 0.01
        assert abs(rounded_ui["y"] - 789.0) < 0.01
        assert abs(rounded_ui["z"] - 0.1) < 0.01
        
        # Test Edit precision rounding
        precision_manager.set_precision_level(PrecisionLevel.EDIT)
        rounded_edit = precision_manager.round_coordinates(coordinates)
        
        assert abs(rounded_edit["x"] - 123.46) < 0.001
        assert abs(rounded_edit["y"] - 789.01) < 0.001
        assert abs(rounded_edit["z"] - 0.12) < 0.001
    
    def test_snap_to_grid(self, precision_manager):
        """Test snap to grid functionality."""
        coordinates = {"x": 123.456, "y": 789.012, "z": 0.123}
        
        # Test with default grid (current precision)
        precision_manager.set_precision_level(PrecisionLevel.UI)
        snapped = precision_manager.snap_to_grid(coordinates)
        
        assert snapped["x"] % 0.1 < 0.001
        assert snapped["y"] % 0.1 < 0.001
        assert snapped["z"] % 0.1 < 0.001
        
        # Test with custom grid
        custom_snapped = precision_manager.snap_to_grid(coordinates, grid_size=1.0)
        assert custom_snapped["x"] % 1.0 < 0.001
        assert custom_snapped["y"] % 1.0 < 0.001
        assert custom_snapped["z"] % 1.0 < 0.001
    
    def test_distance_calculation(self, precision_manager):
        """Test distance calculation with precision."""
        point1 = {"x": 0, "y": 0, "z": 0}
        point2 = {"x": 3, "y": 4, "z": 0}
        
        distance = precision_manager.calculate_distance(point1, point2)
        assert abs(distance - 5.0) < 0.001
    
    def test_precision_validation(self, precision_manager):
        """Test precision validation."""
        precision_manager.set_precision_level(PrecisionLevel.UI)
        
        # Valid precision values
        assert precision_manager.validate_precision(0.1)
        assert precision_manager.validate_precision(0.2)
        assert precision_manager.validate_precision(0.0)
        
        # Invalid precision values
        assert not precision_manager.validate_precision(0.15)
        assert not precision_manager.validate_precision(0.05)
    
    def test_precision_conversion(self, precision_manager):
        """Test precision level conversion."""
        value = 123.456789
        
        # Convert from UI to Edit precision
        converted = precision_manager.convert_precision(
            value, PrecisionLevel.UI, PrecisionLevel.EDIT
        )
        
        # Should be rounded to Edit precision
        assert abs(converted - 123.46) < 0.001
    
    def test_fixed_point_arithmetic(self):
        """Test fixed-point number arithmetic."""
        # Test basic operations
        fp1 = FixedPointNumber(1.5)
        fp2 = FixedPointNumber(2.5)
        
        # Addition
        result = fp1 + fp2
        assert abs(result.to_float() - 4.0) < 0.001
        
        # Multiplication
        result = fp1 * fp2
        assert abs(result.to_float() - 3.75) < 0.001
        
        # Division
        result = fp1 / fp2
        assert abs(result.to_float() - 0.6) < 0.001
    
    def test_precision_info(self, precision_manager):
        """Test precision information retrieval."""
        info = precision_manager.get_precision_info()
        
        assert "current_level" in info
        assert "precision_values" in info
        assert "use_fixed_point" in info
        assert "fixed_point_scale" in info


class TestWASMIntegration:
    """Test WASM integration functionality."""
    
    @pytest.fixture
    def wasm_integration(self):
        """Create WASM integration instance."""
        return WASMIntegration()
    
    def test_geometric_calculations(self, wasm_integration):
        """Test geometric calculations via WASM."""
        # Test distance calculation
        data = {
            "operation": "distance",
            "point1": {"x": 0, "y": 0, "z": 0},
            "point2": {"x": 3, "y": 4, "z": 0}
        }
        
        result = wasm_integration.execute_wasm_operation(
            WASMOperationType.GEOMETRIC_CALCULATION, data
        )
        
        assert result["status"] == "success"
        assert "result" in result
        assert abs(result["result"]["distance"] - 5.0) < 0.001
        assert "duration_ms" in result
    
    def test_physics_simulation(self, wasm_integration):
        """Test physics simulation via WASM."""
        # Test force calculation
        data = {
            "operation": "force_calculation",
            "mass": 2.0,
            "acceleration": {"x": 0, "y": -9.81, "z": 0}
        }
        
        result = wasm_integration.execute_wasm_operation(
            WASMOperationType.PHYSICS_SIMULATION, data
        )
        
        assert result["status"] == "success"
        assert "result" in result
        assert abs(result["result"]["force"]["y"] - (-19.62)) < 0.001
    
    def test_precision_calculations(self, wasm_integration):
        """Test precision calculations via WASM."""
        # Test rounding
        data = {
            "operation": "round",
            "value": 123.456789,
            "precision": 0.01
        }
        
        result = wasm_integration.execute_wasm_operation(
            WASMOperationType.PRECISION_CALCULATION, data
        )
        
        assert result["status"] == "success"
        assert "result" in result
        assert abs(result["result"]["rounded_value"] - 123.46) < 0.001
    
    def test_rendering_optimization(self, wasm_integration):
        """Test rendering optimization via WASM."""
        # Test bounds calculation
        data = {
            "operation": "calculate_bounds",
            "elements": [
                {"x": 0, "y": 0, "width": 100, "height": 100},
                {"x": 50, "y": 50, "width": 50, "height": 50}
            ]
        }
        
        result = wasm_integration.execute_wasm_operation(
            WASMOperationType.RENDERING_OPTIMIZATION, data
        )
        
        assert result["status"] == "success"
        assert "result" in result
        assert "bounds" in result["result"]
    
    def test_performance_stats(self, wasm_integration):
        """Test performance statistics."""
        # Execute some operations to generate stats
        for _ in range(5):
            wasm_integration.execute_wasm_operation(
                WASMOperationType.GEOMETRIC_CALCULATION,
                {"operation": "distance", "point1": {"x": 0, "y": 0}, "point2": {"x": 1, "y": 1}}
            )
        
        stats = wasm_integration.get_performance_stats()
        assert "geometric" in stats
        assert stats["geometric"]["count"] == 5
        assert "avg_duration_ms" in stats["geometric"]
    
    def test_wasm_availability(self, wasm_integration):
        """Test WASM availability checking."""
        available = wasm_integration.is_wasm_available()
        assert isinstance(available, bool)
        
        operations = wasm_integration.get_available_operations()
        assert isinstance(operations, list)
        assert len(operations) > 0


class TestPerformanceTargets:
    """Test CTO performance targets."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        return TestClient(app)
    
    def test_ui_response_time_target(self, client):
        """Test UI response time target (<16ms)."""
        start_time = time.time()
        
        response = client.get("/health")
        
        duration = (time.time() - start_time) * 1000
        assert duration < 16.0, f"UI response time {duration:.2f}ms exceeds 16ms target"
    
    def test_parse_response_time_target(self, client):
        """Test parsing response time target."""
        svgx_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
  <rect x="0" y="0" width="100" height="100"/>
</svg>'''
        
        start_time = time.time()
        
        response = client.post("/parse", json={"content": svgx_content})
        
        duration = (time.time() - start_time) * 1000
        assert duration < 32.0, f"Parse response time {duration:.2f}ms exceeds 32ms target"
    
    def test_interactive_response_time_target(self, client):
        """Test interactive response time target (<16ms)."""
        start_time = time.time()
        
        response = client.post("/interactive", json={
            "operation": "click",
            "element_id": "test",
            "coordinates": {"x": 100, "y": 200},
            "modifiers": {}
        })
        
        duration = (time.time() - start_time) * 1000
        assert duration < 16.0, f"Interactive response time {duration:.2f}ms exceeds 16ms target"
    
    def test_physics_simulation_time_target(self, client):
        """Test physics simulation time target (<100ms)."""
        svgx_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
  <arx:object id="obj01" type="mechanical.component">
    <arx:physics>
      <mass unit="kg">2.5</mass>
      <forces>
        <force type="gravity" direction="down" value="9.81"/>
      </forces>
    </arx:physics>
  </arx:object>
</svg>'''
        
        start_time = time.time()
        
        response = client.post("/simulate", json={"content": svgx_content})
        
        duration = (time.time() - start_time) * 1000
        assert duration < 100.0, f"Physics simulation time {duration:.2f}ms exceeds 100ms target"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 