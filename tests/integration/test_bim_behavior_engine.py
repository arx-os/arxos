"""
Comprehensive Test Suite for BIM Behavior Engine

This test suite validates the BIM behavior engine's ability to simulate'
realistic building system behaviors including:

🎯 **Test Coverage:**
- HVAC system behavior simulation
- Electrical system behavior simulation
- Plumbing system behavior simulation
- Fire protection system behavior simulation
- Security system behavior simulation
- Lighting system behavior simulation
- Structural system behavior simulation
- Environmental system behavior simulation
- Occupancy behavior simulation
- Maintenance behavior simulation

🏗️ **Test Categories:**
- Unit tests for individual behavior types
- Integration tests for system interactions
- Performance tests for simulation efficiency
- Validation tests for realistic behavior
- Error handling tests for edge cases
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any

from svgx_engine.services.bim_behavior_engine import (
    BIMBehaviorEngine, BIMBehaviorConfig, BIMBehaviorType, BIMBehaviorState
)
from svgx_engine.models.enhanced_bim import (
    EnhancedBIMModel, EnhancedBIMElement, BIMElementType, BIMSystemType
)


class TestBIMBehaviorEngine:
    """Comprehensive test suite for BIM behavior engine."""

    @pytest.fixture
def bim_behavior_engine(self):
        """Create BIM behavior engine for testing."""
        config = BIMBehaviorConfig(
            simulation_interval=0.1,  # Fast simulation for testing
            physics_enabled=True,
            environmental_factors=True,
            occupancy_modeling=True,
            maintenance_scheduling=True,
            energy_optimization=True,
            real_time_simulation=False  # Disable for testing
        )
        return BIMBehaviorEngine(config)

    @pytest.fixture
def sample_bim_model(self):
        """Create a sample BIM model for testing."""
        model = EnhancedBIMModel(
            id="test_bim_model",
            name="Test Building",
            description="Test BIM model for behavior engine testing"
        )

        # Add HVAC elements
        hvac_zone = EnhancedBIMElement(
            id="hvac_zone_1",
            name="Office Zone 1",
            element_type=BIMElementType.HVAC_ZONE,
            system_type=BIMSystemType.HVAC,
            properties={
                'area': 100.0,
                'volume': 300.0,
                'setpoint_temperature': 22.0
            }
        )
        model.add_element(hvac_zone)

        # Add electrical elements
        electrical_panel = EnhancedBIMElement(
            id="electrical_panel_1",
            name="Main Electrical Panel",
            element_type=BIMElementType.ELECTRICAL_PANEL,
            system_type=BIMSystemType.ELECTRICAL,
            properties={
                'voltage': 120.0,
                'capacity': 200.0
            }
        )
        model.add_element(electrical_panel)

        # Add plumbing elements
        plumbing_pipe = EnhancedBIMElement(
            id="plumbing_pipe_1",
            name="Main Water Pipe",
            element_type=BIMElementType.PLUMBING_PIPE,
            system_type=BIMSystemType.PLUMBING,
            properties={
                'diameter': 0.05,
                'length': 10.0
            }
        )
        model.add_element(plumbing_pipe)

        # Add fire protection elements
        smoke_detector = EnhancedBIMElement(
            id="smoke_detector_1",
            name="Smoke Detector 1",
            element_type=BIMElementType.SMOKE_DETECTOR,
            system_type=BIMSystemType.FIRE_PROTECTION,
            properties={
                'sensitivity': 'high',
                'location': 'ceiling'
            }
        )
        model.add_element(smoke_detector)

        # Add security elements
        security_camera = EnhancedBIMElement(
            id="security_camera_1",
            name="Security Camera 1",
            element_type=BIMElementType.SECURITY_CAMERA,
            system_type=BIMSystemType.SECURITY,
            properties={
                'resolution': '1080p',
                'field_of_view': 90.0
            }
        )
        model.add_element(security_camera)

        # Add lighting elements
        lighting_fixture = EnhancedBIMElement(
            id="lighting_fixture_1",
            name="LED Light Fixture 1",
            element_type=BIMElementType.LIGHTING_FIXTURE,
            system_type=BIMSystemType.LIGHTING,
            properties={
                'wattage': 50.0,
                'lumen_output': 5000.0
            }
        )
        model.add_element(lighting_fixture)

        return model

    def test_bim_behavior_engine_initialization(self, bim_behavior_engine):
        """Test BIM behavior engine initialization."""
        assert bim_behavior_engine is not None
        assert bim_behavior_engine.config is not None
        assert len(bim_behavior_engine.behavior_handlers) == 10  # All behavior types
        assert BIMBehaviorType.HVAC in bim_behavior_engine.behavior_handlers
        assert BIMBehaviorType.ELECTRICAL in bim_behavior_engine.behavior_handlers
        assert BIMBehaviorType.PLUMBING in bim_behavior_engine.behavior_handlers

    def test_environment_initialization(self, bim_behavior_engine):
        """Test environment initialization."""
        env = bim_behavior_engine._initialize_environment()

        assert 'ambient_temperature' in env
        assert 'ambient_humidity' in env
        assert 'ambient_pressure' in env
        assert 'outdoor_temperature' in env
        assert 'occupancy_level' in env
        assert 'time_of_day' in env

        assert isinstance(env['ambient_temperature'], float)
        assert isinstance(env['ambient_humidity'], float)
        assert isinstance(env['occupancy_level'], float)

    def test_behavior_type_detection(self, bim_behavior_engine, sample_bim_model):
        """Test behavior type detection for different element types."""
        for element in sample_bim_model.elements.values():
            behavior_type = bim_behavior_engine._get_behavior_type(element)
            assert behavior_type in BIMBehaviorType
            assert behavior_type in bim_behavior_engine.behavior_handlers

    def test_element_metrics_initialization(self, bim_behavior_engine, sample_bim_model):
        """Test element metrics initialization."""
        for element in sample_bim_model.elements.values():
            behavior_type = bim_behavior_engine._get_behavior_type(element)
            metrics = bim_behavior_engine._initialize_element_metrics(element, behavior_type)

            # Check common metrics
            assert 'temperature' in metrics
            assert 'humidity' in metrics
            assert 'energy_consumption' in metrics
            assert 'status' in metrics

            # Check behavior-specific metrics
            if behavior_type == BIMBehaviorType.HVAC:
                assert 'setpoint_temperature' in metrics
                assert 'air_flow_rate' in metrics
            elif behavior_type == BIMBehaviorType.ELECTRICAL:
                assert 'voltage' in metrics
                assert 'current' in metrics
                assert 'load_percentage' in metrics
            elif behavior_type == BIMBehaviorType.PLUMBING:
                assert 'water_flow_rate' in metrics
                assert 'water_pressure' in metrics

    @pytest.mark.asyncio
    async def test_hvac_behavior_simulation(self, bim_behavior_engine):
        """Test HVAC behavior simulation."""
        # Create test element data
        element_data = {
            'element': EnhancedBIMElement(
                id="test_hvac",
                name="Test HVAC Zone",
                element_type=BIMElementType.HVAC_ZONE,
                system_type=BIMSystemType.HVAC
            ),
            'behavior_type': BIMBehaviorType.HVAC,
            'state': BIMBehaviorState.NORMAL,
            'metrics': {
                'temperature': 22.0,
                'setpoint_temperature': 22.0,
                'cooling_capacity': 0.0,
                'heating_capacity': 0.0,
                'air_flow_rate': 0.0,
                'energy_consumption': 0.0
            },
            'last_update': datetime.now(),
            'alerts': [],
            'recommendations': []
        }

        # Simulate HVAC behavior
        result = await bim_behavior_engine._simulate_hvac_behavior(
            "test_session", "test_hvac", element_data
        )

        # Validate result
        assert result.element_id == "test_hvac"
        assert result.behavior_type == BIMBehaviorType.HVAC
        assert result.state in BIMBehaviorState
        assert isinstance(result.metrics, dict)
        assert 'temperature' in result.metrics
        assert 'energy_consumption' in result.metrics
        assert 'air_flow_rate' in result.metrics

    @pytest.mark.asyncio
    async def test_electrical_behavior_simulation(self, bim_behavior_engine):
        """Test electrical behavior simulation."""
        element_data = {
            'element': EnhancedBIMElement(
                id="test_electrical",
                name="Test Electrical Panel",
                element_type=BIMElementType.ELECTRICAL_PANEL,
                system_type=BIMSystemType.ELECTRICAL
            ),
            'behavior_type': BIMBehaviorType.ELECTRICAL,
            'state': BIMBehaviorState.NORMAL,
            'metrics': {
                'voltage': 120.0,
                'current': 0.0,
                'load_percentage': 0.0,
                'energy_consumption': 0.0,
                'circuit_breaker_status': 'closed'
            },
            'last_update': datetime.now(),
            'alerts': [],
            'recommendations': []
        }

        result = await bim_behavior_engine._simulate_electrical_behavior(
            "test_session", "test_electrical", element_data
        )

        assert result.element_id == "test_electrical"
        assert result.behavior_type == BIMBehaviorType.ELECTRICAL
        assert 'current' in result.metrics
        assert 'load_percentage' in result.metrics
        assert 'energy_consumption' in result.metrics

    @pytest.mark.asyncio
    async def test_plumbing_behavior_simulation(self, bim_behavior_engine):
        """Test plumbing behavior simulation."""
        element_data = {
            'element': EnhancedBIMElement(
                id="test_plumbing",
                name="Test Plumbing Pipe",
                element_type=BIMElementType.PLUMBING_PIPE,
                system_type=BIMSystemType.PLUMBING
            ),
            'behavior_type': BIMBehaviorType.PLUMBING,
            'state': BIMBehaviorState.NORMAL,
            'metrics': {
                'water_flow_rate': 0.0,
                'water_pressure': 200.0,
                'water_temperature': 20.0,
                'valve_position': 0.0
            },
            'last_update': datetime.now(),
            'alerts': [],
            'recommendations': []
        }

        result = await bim_behavior_engine._simulate_plumbing_behavior(
            "test_session", "test_plumbing", element_data
        )

        assert result.element_id == "test_plumbing"
        assert result.behavior_type == BIMBehaviorType.PLUMBING
        assert 'water_flow_rate' in result.metrics
        assert 'water_pressure' in result.metrics
        assert 'water_temperature' in result.metrics

    @pytest.mark.asyncio
    async def test_fire_protection_behavior_simulation(self, bim_behavior_engine):
        """Test fire protection behavior simulation."""
        element_data = {
            'element': EnhancedBIMElement(
                id="test_fire_protection",
                name="Test Smoke Detector",
                element_type=BIMElementType.SMOKE_DETECTOR,
                system_type=BIMSystemType.FIRE_PROTECTION
            ),
            'behavior_type': BIMBehaviorType.FIRE_PROTECTION,
            'state': BIMBehaviorState.NORMAL,
            'metrics': {
                'status': 'normal',
                'sensitivity': 'high'
            },
            'last_update': datetime.now(),
            'alerts': [],
            'recommendations': []
        }

        result = await bim_behavior_engine._simulate_fire_protection_behavior(
            "test_session", "test_fire_protection", element_data
        )

        assert result.element_id == "test_fire_protection"
        assert result.behavior_type == BIMBehaviorType.FIRE_PROTECTION
        assert 'status' in result.metrics

    @pytest.mark.asyncio
    async def test_security_behavior_simulation(self, bim_behavior_engine):
        """Test security behavior simulation."""
        element_data = {
            'element': EnhancedBIMElement(
                id="test_security",
                name="Test Security Camera",
                element_type=BIMElementType.SECURITY_CAMERA,
                system_type=BIMSystemType.SECURITY
            ),
            'behavior_type': BIMBehaviorType.SECURITY,
            'state': BIMBehaviorState.NORMAL,
            'metrics': {
                'recording_status': 'active',
                'motion_detected': False
            },
            'last_update': datetime.now(),
            'alerts': [],
            'recommendations': []
        }

        result = await bim_behavior_engine._simulate_security_behavior(
            "test_session", "test_security", element_data
        )

        assert result.element_id == "test_security"
        assert result.behavior_type == BIMBehaviorType.SECURITY
        assert 'recording_status' in result.metrics
        assert 'motion_detected' in result.metrics

    @pytest.mark.asyncio
    async def test_lighting_behavior_simulation(self, bim_behavior_engine):
        """Test lighting behavior simulation."""
        element_data = {
            'element': EnhancedBIMElement(
                id="test_lighting",
                name="Test Lighting Fixture",
                element_type=BIMElementType.LIGHTING_FIXTURE,
                system_type=BIMSystemType.LIGHTING
            ),
            'behavior_type': BIMBehaviorType.LIGHTING,
            'state': BIMBehaviorState.NORMAL,
            'metrics': {
                'light_level': 0.0,
                'energy_consumption': 0.0
            },
            'last_update': datetime.now(),
            'alerts': [],
            'recommendations': []
        }

        result = await bim_behavior_engine._simulate_lighting_behavior(
            "test_session", "test_lighting", element_data
        )

        assert result.element_id == "test_lighting"
        assert result.behavior_type == BIMBehaviorType.LIGHTING
        assert 'light_level' in result.metrics
        assert 'energy_consumption' in result.metrics

    def test_state_determination(self, bim_behavior_engine):
        """Test state determination logic."""
        # Test HVAC state determination
        normal_hvac_metrics = {
            'energy_consumption': 5000,
            'temperature': 22.0
        }
        state = bim_behavior_engine._determine_hvac_state(normal_hvac_metrics)
        assert state == BIMBehaviorState.NORMAL

        warning_hvac_metrics = {
            'energy_consumption': 12000,
            'temperature': 22.0
        }
        state = bim_behavior_engine._determine_hvac_state(warning_hvac_metrics)
        assert state == BIMBehaviorState.WARNING

        critical_hvac_metrics = {
            'energy_consumption': 5000,
            'temperature': 35.0
        }
        state = bim_behavior_engine._determine_hvac_state(critical_hvac_metrics)
        assert state == BIMBehaviorState.CRITICAL

        # Test plumbing state determination
        normal_plumbing_metrics = {
            'water_pressure': 150.0
        }
        state = bim_behavior_engine._determine_plumbing_state(normal_plumbing_metrics)
        assert state == BIMBehaviorState.NORMAL

        warning_plumbing_metrics = {
            'water_pressure': 40.0
        }
        state = bim_behavior_engine._determine_plumbing_state(warning_plumbing_metrics)
        assert state == BIMBehaviorState.WARNING

        critical_plumbing_metrics = {
            'water_pressure': 10.0
        }
        state = bim_behavior_engine._determine_plumbing_state(critical_plumbing_metrics)
        assert state == BIMBehaviorState.CRITICAL

    def test_alert_generation(self, bim_behavior_engine):
        """Test alert and recommendation generation."""
        # Test HVAC alerts
        high_energy_metrics = {
            'energy_consumption': 12000,
            'temperature': 25.0,
            'setpoint_temperature': 22.0
        }
        env = {'ambient_temperature': 25.0}
        alerts, recommendations = bim_behavior_engine._generate_hvac_alerts(
            high_energy_metrics, env
        )
        assert len(alerts) > 0
        assert len(recommendations) > 0

        # Test electrical alerts
        high_load_metrics = {
            'load_percentage': 85.0,
            'circuit_breaker_status': 'closed'
        }
        alerts, recommendations = bim_behavior_engine._generate_electrical_alerts(
            high_load_metrics
        )
        assert len(alerts) > 0
        assert len(recommendations) > 0

        # Test plumbing alerts
        low_pressure_metrics = {
            'water_pressure': 30.0
        }
        alerts, recommendations = bim_behavior_engine._generate_plumbing_alerts(
            low_pressure_metrics
        )
        assert len(alerts) > 0
        assert len(recommendations) > 0

    def test_simulation_session_management(self, bim_behavior_engine, sample_bim_model):
        """Test simulation session management."""
        # Start simulation
        session_id = bim_behavior_engine.start_bim_simulation(sample_bim_model)
        assert session_id in bim_behavior_engine.active_behaviors

        # Check session data
        session_data = bim_behavior_engine.active_behaviors[session_id]
        assert session_data['model'] == sample_bim_model
        assert 'elements' in session_data
        assert 'environment' in session_data

        # Check that all elements are initialized
        assert len(session_data['elements']) == len(sample_bim_model.elements)

        # Get simulation status
        status = bim_behavior_engine.get_simulation_status(session_id)
        assert status['session_id'] == session_id
        assert status['total_elements'] == len(sample_bim_model.elements)
        assert 'environment' in status

        # Stop simulation
        success = bim_behavior_engine.stop_simulation(session_id)
        assert success
        assert session_id not in bim_behavior_engine.active_behaviors

    def test_environment_update(self, bim_behavior_engine, sample_bim_model):
        """Test environment update functionality."""
        session_id = bim_behavior_engine.start_bim_simulation(sample_bim_model)

        # Get initial environment
        initial_env = bim_behavior_engine.active_behaviors[session_id]['environment']
        initial_temp = initial_env['outdoor_temperature']

        # Update environment
        bim_behavior_engine._update_environment(session_id)

        # Check that environment was updated
        updated_env = bim_behavior_engine.active_behaviors[session_id]['environment']
        assert updated_env['outdoor_temperature'] != initial_temp
        assert 'time_of_day' in updated_env
        assert 'occupancy_level' in updated_env

        bim_behavior_engine.stop_simulation(session_id)

    def test_performance_monitoring(self, bim_behavior_engine):
        """Test performance monitoring integration."""
        # The behavior engine should have performance monitoring
        assert hasattr(bim_behavior_engine, 'performance_monitor')
        assert bim_behavior_engine.performance_monitor is not None

    def test_error_handling(self, bim_behavior_engine):
        """Test error handling for invalid inputs."""
        # Test with invalid session ID
        status = bim_behavior_engine.get_simulation_status("invalid_session")
        assert "error" in status

        # Test stopping non-existent session
        success = bim_behavior_engine.stop_simulation("invalid_session")
        assert not success

    def test_behavior_history(self, bim_behavior_engine, sample_bim_model):
        """Test behavior history tracking."""
        session_id = bim_behavior_engine.start_bim_simulation(sample_bim_model)

        # Simulate some behavior updates
        for element in sample_bim_model.elements.values():
            element_data = bim_behavior_engine.active_behaviors[session_id]['elements'][element.id]
            bim_behavior_engine._store_simulation_results(session_id)

        # Check that history was stored
        assert session_id in bim_behavior_engine.behavior_history
        assert len(bim_behavior_engine.behavior_history[session_id]) > 0

        bim_behavior_engine.stop_simulation(session_id)


class TestBIMBehaviorIntegration:
    """Integration tests for BIM behavior with other SVGX Engine components."""

    @pytest.fixture
def integrated_bim_engine(self):
        """Create BIM behavior engine with full integration."""
        config = BIMBehaviorConfig(
            simulation_interval=0.1,
            physics_enabled=True,
            environmental_factors=True,
            occupancy_modeling=True,
            maintenance_scheduling=True,
            energy_optimization=True,
            real_time_simulation=False
        )
        return BIMBehaviorEngine(config)

    def test_physics_engine_integration(self, integrated_bim_engine):
        """Test integration with physics engine."""
        assert integrated_bim_engine.physics_engine is not None
        assert hasattr(integrated_bim_engine.physics_engine, 'simulate_element')

    def test_behavior_engine_integration(self, integrated_bim_engine):
        """Test integration with behavior engine."""
        assert integrated_bim_engine.behavior_engine is not None
        assert hasattr(integrated_bim_engine.behavior_engine, 'evaluate_behavior')

    def test_logic_engine_integration(self, integrated_bim_engine):
        """Test integration with logic engine."""
        assert integrated_bim_engine.logic_engine is not None
        assert hasattr(integrated_bim_engine.logic_engine, 'evaluate_rules')


class TestBIMBehaviorPerformance:
    """Performance tests for BIM behavior engine."""

    @pytest.fixture
def performance_bim_engine(self):
        """Create BIM behavior engine for performance testing."""
        config = BIMBehaviorConfig(
            simulation_interval=0.01,  # Very fast for performance testing
            physics_enabled=True,
            environmental_factors=True,
            occupancy_modeling=True,
            maintenance_scheduling=True,
            energy_optimization=True,
            real_time_simulation=False
        )
        return BIMBehaviorEngine(config)

    def test_simulation_performance(self, performance_bim_engine, sample_bim_model):
        """Test simulation performance with multiple elements."""
        session_id = performance_bim_engine.start_bim_simulation(sample_bim_model)

        # Measure simulation performance
        start_time = time.time()

        # Run multiple simulation steps
        for _ in range(10):
            for element in sample_bim_model.elements.values():
                element_data = performance_bim_engine.active_behaviors[session_id]['elements'][element.id]
                behavior_type = element_data['behavior_type']
                handler = performance_bim_engine.behavior_handlers[behavior_type]

                # Simulate behavior (synchronous for testing)
                asyncio.run(handler(session_id, element.id, element_data)
        end_time = time.time()
        simulation_time = end_time - start_time

        # Performance should be reasonable (less than 1 second for 10 steps)
        assert simulation_time < 1.0

        performance_bim_engine.stop_simulation(session_id)

    def test_memory_usage(self, performance_bim_engine, sample_bim_model):
        """Test memory usage during simulation."""
        import psutil
        import os

        process = psutil.Process(os.getpid()
        initial_memory = process.memory_info().rss

        # Start simulation
        session_id = performance_bim_engine.start_bim_simulation(sample_bim_model)

        # Run simulation for a while
        for _ in range(100):
            for element in sample_bim_model.elements.values():
                element_data = performance_bim_engine.active_behaviors[session_id]['elements'][element.id]
                behavior_type = element_data['behavior_type']
                handler = performance_bim_engine.behavior_handlers[behavior_type]
                asyncio.run(handler(session_id, element.id, element_data)
        # Check memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024  # 100MB

        performance_bim_engine.stop_simulation(session_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
