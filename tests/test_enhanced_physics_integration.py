"""
Comprehensive Test Suite for Enhanced Physics Engine Integration

This test suite validates the enhanced physics engine integration with BIM behavior
including fluid dynamics, electrical analysis, structural analysis, thermal modeling,
and acoustic modeling for realistic building system simulation.

🎯 **Test Coverage:**
- Enhanced physics engine calculations
- Physics-BIM integration service
- Real-time simulation performance
- Data validation and error handling
- Enterprise-grade reliability testing

🏗️ **Test Categories:**
- Unit tests for individual physics engines
- Integration tests for physics-BIM combination
- Performance tests for simulation efficiency
- Validation tests for realistic calculations
- Error handling tests for edge cases
"""

import pytest
import time
import math
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add the parent directory to the path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from svgx_engine.services.enhanced_physics_engine import (
    EnhancedPhysicsEngine,
    PhysicsConfig,
    PhysicsType,
    PhysicsResult,
    FluidDynamicsEngine,
    ElectricalEngine,
    StructuralEngine,
    ThermalEngine,
    AcousticEngine,
)
from svgx_engine.services.physics_bim_integration import (
    PhysicsBIMIntegration,
    PhysicsBIMConfig,
    PhysicsBIMResult,
)
from svgx_engine.models.enhanced_bim import (
    EnhancedBIMModel,
    EnhancedBIMElement,
    BIMElementType,
    BIMSystemType,
)


class TestEnhancedPhysicsEngine:
    """Comprehensive test suite for enhanced physics engine."""

    @pytest.fixture
    def physics_engine(self):
        """Create enhanced physics engine for testing."""
        config = PhysicsConfig(
            calculation_interval=0.1, max_iterations=50, convergence_tolerance=1e-6
        )
        return EnhancedPhysicsEngine(config)

    @pytest.fixture
    def fluid_engine(self):
        """Create fluid dynamics engine for testing."""
        config = PhysicsConfig()
        return FluidDynamicsEngine(config)

    @pytest.fixture
    def electrical_engine(self):
        """Create electrical engine for testing."""
        config = PhysicsConfig()
        return ElectricalEngine(config)

    @pytest.fixture
    def structural_engine(self):
        """Create structural engine for testing."""
        config = PhysicsConfig()
        return StructuralEngine(config)

    @pytest.fixture
    def thermal_engine(self):
        """Create thermal engine for testing."""
        config = PhysicsConfig()
        return ThermalEngine(config)

    @pytest.fixture
    def acoustic_engine(self):
        """Create acoustic engine for testing."""
        config = PhysicsConfig()
        return AcousticEngine(config)

    def test_physics_engine_initialization(self, physics_engine):
        """Test enhanced physics engine initialization."""
        assert physics_engine is not None
        assert physics_engine.config is not None
        assert physics_engine.fluid_engine is not None
        assert physics_engine.electrical_engine is not None
        assert physics_engine.structural_engine is not None
        assert physics_engine.thermal_engine is not None
        assert physics_engine.acoustic_engine is not None

    def test_fluid_dynamics_air_flow(self, fluid_engine):
        """Test air flow calculations in fluid dynamics."""
        duct_data = {
            "diameter": 0.3,  # m
            "length": 10.0,  # m
            "flow_rate": 0.5,  # m³/s
            "roughness": 0.0001,  # m
        }

        result = fluid_engine.calculate_air_flow(duct_data)

        assert result.physics_type == PhysicsType.FLUID_DYNAMICS
        assert result.state in [
            PhysicsState.NORMAL,
            PhysicsState.WARNING,
            PhysicsState.CRITICAL,
        ]
        assert "velocity" in result.metrics
        assert "pressure_drop" in result.metrics
        assert "reynolds_number" in result.metrics
        assert result.flows["air_flow_rate"] == 0.5
        assert result.flows["velocity"] > 0

    def test_fluid_dynamics_water_flow(self, fluid_engine):
        """Test water flow calculations in fluid dynamics."""
        pipe_data = {
            "diameter": 0.05,  # m
            "length": 10.0,  # m
            "flow_rate": 0.01,  # m³/s
            "roughness": 0.000045,  # m
        }

        result = fluid_engine.calculate_water_flow(pipe_data)

        assert result.physics_type == PhysicsType.FLUID_DYNAMICS
        assert result.state in [
            PhysicsState.NORMAL,
            PhysicsState.WARNING,
            PhysicsState.CRITICAL,
        ]
        assert "velocity" in result.metrics
        assert "pressure_drop" in result.metrics
        assert "reynolds_number" in result.metrics
        assert result.flows["water_flow_rate"] == 0.01
        assert result.flows["velocity"] > 0

    def test_electrical_circuit_analysis(self, electrical_engine):
        """Test electrical circuit analysis."""
        circuit_data = {
            "voltage": 120.0,  # V
            "resistance": 10.0,  # ohms
            "inductance": 0.1,  # H
            "capacitance": 0.001,  # F
            "frequency": 60.0,  # Hz
        }

        result = electrical_engine.analyze_circuit(circuit_data)

        assert result.physics_type == PhysicsType.ELECTRICAL
        assert result.state in [
            PhysicsState.NORMAL,
            PhysicsState.WARNING,
            PhysicsState.CRITICAL,
        ]
        assert "current" in result.metrics
        assert "impedance" in result.metrics
        assert "power_factor" in result.metrics
        assert result.currents["circuit_current"] > 0
        assert result.voltages["circuit_voltage"] == 120.0

    def test_electrical_load_balancing(self, electrical_engine):
        """Test electrical load balancing."""
        loads = [
            {"id": "load1", "power": 1000, "current": 8.33},
            {"id": "load2", "power": 1500, "current": 12.5},
            {"id": "load3", "power": 800, "current": 6.67},
        ]

        result = electrical_engine.calculate_load_balancing(loads)

        assert result.physics_type == PhysicsType.ELECTRICAL
        assert result.state in [
            PhysicsState.NORMAL,
            PhysicsState.WARNING,
            PhysicsState.CRITICAL,
        ]
        assert "total_power" in result.metrics
        assert "total_current" in result.metrics
        assert "load_factor" in result.metrics
        assert result.currents["total_current"] > 0

    def test_structural_beam_analysis(self, structural_engine):
        """Test structural beam analysis."""
        beam_data = {
            "length": 5.0,  # m
            "width": 0.2,  # m
            "height": 0.3,  # m
            "load": 1000.0,  # N
            "material": "steel",
        }

        result = structural_engine.analyze_beam(beam_data)

        assert result.physics_type == PhysicsType.STRUCTURAL
        assert result.state in [
            PhysicsState.NORMAL,
            PhysicsState.WARNING,
            PhysicsState.CRITICAL,
        ]
        assert "max_stress" in result.metrics
        assert "max_deflection" in result.metrics
        assert "safety_factor" in result.metrics
        assert result.forces["load"] == 1000.0
        assert result.stresses["max_stress"] > 0

    def test_structural_column_analysis(self, structural_engine):
        """Test structural column analysis."""
        column_data = {
            "height": 3.0,  # m
            "diameter": 0.3,  # m
            "load": 50000.0,  # N
            "material": "steel",
        }

        result = structural_engine.analyze_column(column_data)

        assert result.physics_type == PhysicsType.STRUCTURAL
        assert result.state in [
            PhysicsState.NORMAL,
            PhysicsState.WARNING,
            PhysicsState.CRITICAL,
        ]
        assert "axial_stress" in result.metrics
        assert "buckling_load" in result.metrics
        assert "safety_factor" in result.metrics
        assert result.forces["load"] == 50000.0
        assert result.stresses["axial_stress"] > 0

    def test_thermal_heat_transfer(self, thermal_engine):
        """Test thermal heat transfer calculations."""
        thermal_data = {
            "surface_area": 10.0,  # m²
            "thickness": 0.1,  # m
            "temp_difference": 20.0,  # K
            "thermal_conductivity": 0.5,  # W/(m·K)
        }

        result = thermal_engine.calculate_heat_transfer(thermal_data)

        assert result.physics_type == PhysicsType.THERMAL
        assert result.state in [
            PhysicsState.NORMAL,
            PhysicsState.WARNING,
            PhysicsState.CRITICAL,
        ]
        assert "heat_transfer_rate" in result.metrics
        assert "thermal_resistance" in result.metrics
        assert "u_value" in result.metrics
        assert result.temperatures["temp_difference"] == 20.0

    def test_thermal_hvac_performance(self, thermal_engine):
        """Test HVAC thermal performance calculations."""
        hvac_data = {
            "air_flow_rate": 0.5,  # m³/s
            "temp_difference": 10.0,  # K
            "efficiency": 0.8,
        }

        result = thermal_engine.calculate_hvac_performance(hvac_data)

        assert result.physics_type == PhysicsType.THERMAL
        assert result.state in [
            PhysicsState.NORMAL,
            PhysicsState.WARNING,
            PhysicsState.CRITICAL,
        ]
        assert "capacity" in result.metrics
        assert "power_consumption" in result.metrics
        assert "efficiency" in result.metrics
        assert "cop" in result.metrics
        assert result.temperatures["temp_difference"] == 10.0

    def test_acoustic_sound_propagation(self, acoustic_engine):
        """Test acoustic sound propagation calculations."""
        acoustic_data = {
            "sound_power": 0.001,  # W
            "distance": 5.0,  # m
            "absorption_coefficient": 0.1,
            "room_volume": 100.0,  # m³
        }

        result = acoustic_engine.calculate_sound_propagation(acoustic_data)

        assert result.physics_type == PhysicsType.ACOUSTIC
        assert result.state in [
            PhysicsState.NORMAL,
            PhysicsState.WARNING,
            PhysicsState.CRITICAL,
        ]
        assert "spl_source" in result.metrics
        assert "spl_receiver" in result.metrics
        assert "reverberation_time" in result.metrics
        assert result.metrics["sound_power"] == 0.001

    def test_physics_engine_calculation(self, physics_engine):
        """Test physics engine calculation for different types."""
        # Test fluid dynamics
        fluid_data = {
            "fluid_type": "air",
            "diameter": 0.3,
            "length": 10.0,
            "flow_rate": 0.5,
        }

        result = physics_engine.calculate_physics(
            PhysicsType.FLUID_DYNAMICS, fluid_data
        )
        assert result.physics_type == PhysicsType.FLUID_DYNAMICS
        assert result.state in [
            PhysicsState.NORMAL,
            PhysicsState.WARNING,
            PhysicsState.CRITICAL,
        ]

        # Test electrical
        electrical_data = {"voltage": 120.0, "resistance": 10.0}

        result = physics_engine.calculate_physics(
            PhysicsType.ELECTRICAL, electrical_data
        )
        assert result.physics_type == PhysicsType.ELECTRICAL
        assert result.state in [
            PhysicsState.NORMAL,
            PhysicsState.WARNING,
            PhysicsState.CRITICAL,
        ]

        # Test structural
        structural_data = {
            "length": 5.0,
            "width": 0.2,
            "height": 0.3,
            "load": 1000.0,
            "material": "steel",
        }

        result = physics_engine.calculate_physics(
            PhysicsType.STRUCTURAL, structural_data
        )
        assert result.physics_type == PhysicsType.STRUCTURAL
        assert result.state in [
            PhysicsState.NORMAL,
            PhysicsState.WARNING,
            PhysicsState.CRITICAL,
        ]

    def test_physics_data_validation(self, physics_engine):
        """Test physics data validation."""
        # Valid fluid dynamics data
        valid_fluid_data = {"diameter": 0.3, "length": 10.0, "flow_rate": 0.5}
        assert physics_engine.validate_physics_data(
            PhysicsType.FLUID_DYNAMICS, valid_fluid_data
        )

        # Invalid fluid dynamics data (missing required fields)
        invalid_fluid_data = {"diameter": 0.3}
        assert not physics_engine.validate_physics_data(
            PhysicsType.FLUID_DYNAMICS, invalid_fluid_data
        )

        # Valid electrical data
        valid_electrical_data = {"voltage": 120.0}
        assert physics_engine.validate_physics_data(
            PhysicsType.ELECTRICAL, valid_electrical_data
        )

    def test_physics_engine_performance(self, physics_engine):
        """Test physics engine performance."""
        start_time = time.time()

        # Run multiple calculations
        for i in range(10):
            fluid_data = {
                "fluid_type": "air",
                "diameter": 0.3,
                "length": 10.0,
                "flow_rate": 0.5 + i * 0.1,
            }
            result = physics_engine.calculate_physics(
                PhysicsType.FLUID_DYNAMICS, fluid_data
            )
            assert result is not None

        end_time = time.time()
        total_time = end_time - start_time

        # Performance should be reasonable (less than 1 second for 10 calculations)
        assert total_time < 1.0

    def test_physics_engine_summary(self, physics_engine):
        """Test physics engine summary generation."""
        # Run some calculations first
        for i in range(5):
            fluid_data = {
                "fluid_type": "air",
                "diameter": 0.3,
                "length": 10.0,
                "flow_rate": 0.5 + i * 0.1,
            }
            physics_engine.calculate_physics(PhysicsType.FLUID_DYNAMICS, fluid_data)

        summary = physics_engine.get_physics_summary()

        assert "total_calculations" in summary
        assert "calculations_by_type" in summary
        assert "latest_results" in summary
        assert summary["total_calculations"] >= 5


class TestPhysicsBIMIntegration:
    """Comprehensive test suite for physics-BIM integration."""

    @pytest.fixture
    def physics_bim_integration(self):
        """Create physics-BIM integration service for testing."""
        config = PhysicsBIMConfig(
            physics_enabled=True,
            behavior_enabled=True,
            integration_enabled=True,
            real_time_simulation=False,  # Disable for testing
        )
        return PhysicsBIMIntegration(config)

    @pytest.fixture
    def sample_bim_model(self):
        """Create a sample BIM model for testing."""
        model = EnhancedBIMModel(
            id="test_physics_bim_model",
            name="Test Physics BIM Model",
            description="Test BIM model for physics integration testing",
        )

        # Add HVAC elements
        hvac_zone = EnhancedBIMElement(
            id="hvac_zone_physics_1",
            name="HVAC Zone Physics 1",
            element_type=BIMElementType.HVAC_ZONE,
            system_type=BIMSystemType.HVAC,
            properties={
                "diameter": 0.3,
                "length": 10.0,
                "flow_rate": 0.5,
                "setpoint_temperature": 22.0,
            },
        )
        model.add_element(hvac_zone)

        # Add electrical elements
        electrical_panel = EnhancedBIMElement(
            id="electrical_panel_physics_1",
            name="Electrical Panel Physics 1",
            element_type=BIMElementType.ELECTRICAL_PANEL,
            system_type=BIMSystemType.ELECTRICAL,
            properties={"voltage": 120.0, "resistance": 10.0, "capacity": 200.0},
        )
        model.add_element(electrical_panel)

        # Add structural elements
        structural_beam = EnhancedBIMElement(
            id="structural_beam_physics_1",
            name="Structural Beam Physics 1",
            element_type=BIMElementType.BEAM,
            system_type=BIMSystemType.STRUCTURAL,
            properties={
                "length": 5.0,
                "width": 0.2,
                "height": 0.3,
                "load": 1000.0,
                "material": "steel",
            },
        )
        model.add_element(structural_beam)

        # Add plumbing elements
        plumbing_pipe = EnhancedBIMElement(
            id="plumbing_pipe_physics_1",
            name="Plumbing Pipe Physics 1",
            element_type=BIMElementType.PLUMBING_PIPE,
            system_type=BIMSystemType.PLUMBING,
            properties={"diameter": 0.05, "length": 10.0, "flow_rate": 0.01},
        )
        model.add_element(plumbing_pipe)

        return model

    def test_physics_bim_integration_initialization(self, physics_bim_integration):
        """Test physics-BIM integration initialization."""
        assert physics_bim_integration is not None
        assert physics_bim_integration.config is not None
        assert physics_bim_integration.physics_engine is not None
        assert physics_bim_integration.bim_behavior_engine is not None

    def test_integrated_simulation_start(
        self, physics_bim_integration, sample_bim_model
    ):
        """Test starting integrated simulation."""
        session_id = physics_bim_integration.start_integrated_simulation(
            sample_bim_model
        )

        assert session_id in physics_bim_integration.active_simulations
        session_data = physics_bim_integration.active_simulations[session_id]
        assert session_data["model"] == sample_bim_model
        assert "elements" in session_data
        assert "physics_results" in session_data
        assert "behavior_results" in session_data

    def test_element_simulation_initialization(
        self, physics_bim_integration, sample_bim_model
    ):
        """Test element simulation initialization."""
        session_id = physics_bim_integration.start_integrated_simulation(
            sample_bim_model
        )
        session_data = physics_bim_integration.active_simulations[session_id]

        for element_id, element_data in session_data["elements"].items():
            assert "physics_type" in element_data
            assert "behavior_type" in element_data
            assert "physics_data" in element_data
            assert "behavior_data" in element_data
            assert element_data["physics_data"]["element_id"] == element_id

    def test_physics_type_detection(self, physics_bim_integration, sample_bim_model):
        """Test physics type detection for different elements."""
        session_id = physics_bim_integration.start_integrated_simulation(
            sample_bim_model
        )
        session_data = physics_bim_integration.active_simulations[session_id]

        for element_id, element_data in session_data["elements"].items():
            physics_type = element_data["physics_type"]
            assert physics_type in PhysicsType
            assert (
                physics_type in physics_bim_integration.physics_engine.behavior_handlers
            )

    def test_behavior_type_detection(self, physics_bim_integration, sample_bim_model):
        """Test behavior type detection for different elements."""
        session_id = physics_bim_integration.start_integrated_simulation(
            sample_bim_model
        )
        session_data = physics_bim_integration.active_simulations[session_id]

        for element_id, element_data in session_data["elements"].items():
            behavior_type = element_data["behavior_type"]
            assert behavior_type in BIMBehaviorType
            assert (
                behavior_type
                in physics_bim_integration.bim_behavior_engine.behavior_handlers
            )

    def test_integrated_simulation_step(
        self, physics_bim_integration, sample_bim_model
    ):
        """Test integrated simulation step execution."""
        session_id = physics_bim_integration.start_integrated_simulation(
            sample_bim_model
        )

        results = physics_bim_integration.run_integrated_simulation_step(session_id)

        assert len(results) == len(sample_bim_model.elements)

        for element_id, result in results.items():
            assert isinstance(result, PhysicsBIMResult)
            assert result.element_id == element_id
            assert result.timestamp is not None
            assert "integration_metrics" in result.__dict__

    def test_simulation_status(self, physics_bim_integration, sample_bim_model):
        """Test simulation status retrieval."""
        session_id = physics_bim_integration.start_integrated_simulation(
            sample_bim_model
        )

        # Run a simulation step
        physics_bim_integration.run_integrated_simulation_step(session_id)

        status = physics_bim_integration.get_simulation_status(session_id)

        assert status["session_id"] == session_id
        assert status["status"] == "running"
        assert status["total_elements"] == len(sample_bim_model.elements)
        assert status["physics_enabled"] == True
        assert status["behavior_enabled"] == True
        assert "performance_metrics" in status
        assert "physics_states" in status
        assert "behavior_states" in status

    def test_integration_summary(self, physics_bim_integration, sample_bim_model):
        """Test integration summary generation."""
        session_id = physics_bim_integration.start_integrated_simulation(
            sample_bim_model
        )

        # Run simulation steps
        for _ in range(3):
            physics_bim_integration.run_integrated_simulation_step(session_id)

        summary = physics_bim_integration.get_integration_summary()

        assert "total_sessions" in summary
        assert "total_calculations" in summary
        assert "performance_metrics" in summary
        assert "active_sessions" in summary
        assert summary["total_sessions"] >= 1
        assert summary["total_calculations"] >= 3

    def test_simulation_stop(self, physics_bim_integration, sample_bim_model):
        """Test simulation stop functionality."""
        session_id = physics_bim_integration.start_integrated_simulation(
            sample_bim_model
        )

        assert session_id in physics_bim_integration.active_simulations

        success = physics_bim_integration.stop_simulation(session_id)
        assert success
        assert session_id not in physics_bim_integration.active_simulations

    def test_integration_data_validation(
        self, physics_bim_integration, sample_bim_model
    ):
        """Test integration data validation."""
        # Valid BIM model
        assert physics_bim_integration.validate_integration_data(sample_bim_model)

        # Invalid BIM model (empty)
        empty_model = EnhancedBIMModel(
            id="empty_model", name="Empty Model", description="Empty BIM model"
        )
        assert not physics_bim_integration.validate_integration_data(empty_model)

    def test_integration_performance(self, physics_bim_integration, sample_bim_model):
        """Test integration performance."""
        session_id = physics_bim_integration.start_integrated_simulation(
            sample_bim_model
        )

        start_time = time.time()

        # Run multiple simulation steps
        for _ in range(5):
            results = physics_bim_integration.run_integrated_simulation_step(session_id)
            assert len(results) == len(sample_bim_model.elements)

        end_time = time.time()
        total_time = end_time - start_time

        # Performance should be reasonable (less than 2 seconds for 5 steps)
        assert total_time < 2.0

        physics_bim_integration.stop_simulation(session_id)

    def test_error_handling(self, physics_bim_integration):
        """Test error handling for invalid inputs."""
        # Test with invalid session ID
        status = physics_bim_integration.get_simulation_status("invalid_session")
        assert "error" in status

        # Test stopping non-existent session
        success = physics_bim_integration.stop_simulation("invalid_session")
        assert not success


class TestPhysicsBIMPerformance:
    """Performance tests for physics-BIM integration."""

    @pytest.fixture
    def performance_integration(self):
        """Create physics-BIM integration for performance testing."""
        config = PhysicsBIMConfig(
            physics_enabled=True,
            behavior_enabled=True,
            integration_enabled=True,
            real_time_simulation=False,
        )
        return PhysicsBIMIntegration(config)

    def test_large_model_performance(self, performance_integration):
        """Test performance with large BIM model."""
        # Create large BIM model
        large_model = EnhancedBIMModel(
            id="large_physics_bim_model",
            name="Large Physics BIM Model",
            description="Large BIM model for performance testing",
        )

        # Add many elements
        for i in range(50):
            element = EnhancedBIMElement(
                id=f"element_{i}",
                name=f"Element {i}",
                element_type=(
                    BIMElementType.HVAC_ZONE
                    if i % 4 == 0
                    else BIMElementType.ELECTRICAL_PANEL
                ),
                system_type=(
                    BIMSystemType.HVAC if i % 4 == 0 else BIMSystemType.ELECTRICAL
                ),
                properties={
                    "diameter": 0.3,
                    "length": 10.0,
                    "flow_rate": 0.5 + i * 0.01,
                    "voltage": 120.0,
                    "resistance": 10.0 + i * 0.1,
                },
            )
            large_model.add_element(element)

        session_id = performance_integration.start_integrated_simulation(large_model)

        start_time = time.time()

        # Run simulation step
        results = performance_integration.run_integrated_simulation_step(session_id)

        end_time = time.time()
        simulation_time = end_time - start_time

        # Performance should be reasonable (less than 5 seconds for 50 elements)
        assert simulation_time < 5.0
        assert len(results) == 50

        performance_integration.stop_simulation(session_id)

    def test_memory_usage(self, performance_integration):
        """Test memory usage during simulation."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Create and run simulation
        large_model = EnhancedBIMModel(
            id="memory_test_model",
            name="Memory Test Model",
            description="Model for memory usage testing",
        )

        # Add elements
        for i in range(20):
            element = EnhancedBIMElement(
                id=f"memory_element_{i}",
                name=f"Memory Element {i}",
                element_type=BIMElementType.HVAC_ZONE,
                system_type=BIMSystemType.HVAC,
                properties={"diameter": 0.3, "length": 10.0, "flow_rate": 0.5},
            )
            large_model.add_element(element)

        session_id = performance_integration.start_integrated_simulation(large_model)

        # Run multiple simulation steps
        for _ in range(10):
            performance_integration.run_integrated_simulation_step(session_id)

        # Check memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 200MB)
        assert memory_increase < 200 * 1024 * 1024  # 200MB

        performance_integration.stop_simulation(session_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
