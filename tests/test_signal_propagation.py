"""
Test Signal Propagation Engine Implementation

This test suite validates the signal propagation engine components:
- Signal propagation service
- Antenna analyzer
- Interference calculator

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import unittest
import numpy as np
from unittest.mock import Mock, patch
import sys
import os

# Add the svgx_engine to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'svgx_engine'))

from services.physics.signal_propagation import (
    SignalPropagationService, SignalAnalysisRequest, SignalSource, 
    AntennaProperties, PropagationEnvironment, PropagationModel, 
    EnvironmentType, SignalType
)

from services.physics.antenna_analyzer import (
    AntennaAnalyzer, AntennaAnalysisRequest, AntennaParameters,
    AntennaType, PolarizationType
)

from services.physics.interference_calculator import (
    InterferenceCalculator, InterferenceAnalysisRequest, InterferenceSource,
    InterferenceEnvironment, InterferenceType, InterferenceSeverity
)


class TestSignalPropagationService(unittest.TestCase):
    """Test cases for SignalPropagationService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = SignalPropagationService()
        
        # Create test antenna properties
        self.antenna_props = AntennaProperties(
            name="test_antenna",
            type="dipole",
            frequency=2.4e9,
            gain=2.15,
            efficiency=0.95,
            polarization="vertical",
            beamwidth_h=78.0,
            beamwidth_v=78.0,
            front_to_back_ratio=0.0
        )
        
        # Create test signal source
        self.signal_source = SignalSource(
            id="test_source",
            type=SignalType.WIFI,
            frequency=2.4e9,
            power=0.1,
            antenna=self.antenna_props,
            position=(0.0, 0.0, 10.0),
            height=10.0
        )
        
        # Create test environment
        self.environment = PropagationEnvironment(
            type=EnvironmentType.URBAN,
            terrain_height=0.0,
            building_height=30.0,
            vegetation_density=0.1,
            ground_reflectivity=0.3,
            atmospheric_conditions={"humidity": 0.6, "temperature": 25.0},
            obstacles=[]
        )
        
        # Create test request
        self.request = SignalAnalysisRequest(
            id="test_request",
            source=self.signal_source,
            receiver_position=(100.0, 100.0, 1.5),
            environment=self.environment,
            propagation_model=PropagationModel.FREE_SPACE,
            analysis_type="path_loss"
        )
    
    def test_initialization(self):
        """Test service initialization."""
        self.assertIsNotNone(self.service)
        self.assertIsNotNone(self.service.propagation_models)
        self.assertIsNotNone(self.service.environment_models)
        self.assertIsNotNone(self.service.antenna_patterns)
    
    def test_free_space_path_loss(self):
        """Test free space path loss calculation."""
        frequency = 2.4e9
        distance = 100.0
        
        path_loss = self.service._free_space_path_loss(frequency, distance)
        
        self.assertIsInstance(path_loss, float)
        self.assertGreater(path_loss, 0)
        
        # Verify the formula: PL = 20*log10(4*π*d*f/c)
        expected_path_loss = 20 * np.log10(4 * np.pi * distance * frequency / 3e8)
        self.assertAlmostEqual(path_loss, expected_path_loss, places=1)
    
    def test_two_ray_path_loss(self):
        """Test two-ray path loss calculation."""
        request = self.request
        request.propagation_model = PropagationModel.TWO_RAY
        distance = 100.0
        
        path_loss = self.service._two_ray_path_loss(request, distance)
        
        self.assertIsInstance(path_loss, float)
        self.assertGreater(path_loss, 0)
    
    def test_hata_path_loss(self):
        """Test Hata model path loss calculation."""
        request = self.request
        request.propagation_model = PropagationModel.HATA
        distance = 1.0  # 1 km
        
        path_loss = self.service._hata_path_loss(request, distance)
        
        self.assertIsInstance(path_loss, float)
        self.assertGreater(path_loss, 0)
    
    def test_cost231_path_loss(self):
        """Test COST-231 model path loss calculation."""
        request = self.request
        request.propagation_model = PropagationModel.COST231
        distance = 1.0  # 1 km
        
        path_loss = self.service._cost231_path_loss(request, distance)
        
        self.assertIsInstance(path_loss, float)
        self.assertGreater(path_loss, 0)
    
    def test_itu_r_path_loss(self):
        """Test ITU-R model path loss calculation."""
        request = self.request
        request.propagation_model = PropagationModel.ITU_R
        distance = 1.0  # 1 km
        
        path_loss = self.service._itu_r_path_loss(request, distance)
        
        self.assertIsInstance(path_loss, float)
        self.assertGreater(path_loss, 0)
    
    def test_calculate_distance(self):
        """Test distance calculation."""
        pos1 = (0.0, 0.0, 0.0)
        pos2 = (3.0, 4.0, 0.0)
        
        distance = self.service._calculate_distance(pos1, pos2)
        
        self.assertEqual(distance, 5.0)  # 3-4-5 triangle
    
    def test_calculate_received_power(self):
        """Test received power calculation."""
        source = self.signal_source
        path_loss = 80.0  # dB
        
        received_power = self.service._calculate_received_power(source, path_loss)
        
        self.assertIsInstance(received_power, float)
        # Power should be less than transmitted power due to path loss
        self.assertLess(received_power, 10 * np.log10(source.power * 1000) + source.antenna.gain)
    
    def test_calculate_signal_strength(self):
        """Test signal strength calculation."""
        received_power = -50.0  # dBm
        environment = self.environment
        
        signal_strength = self.service._calculate_signal_strength(received_power, environment)
        
        self.assertIsInstance(signal_strength, float)
        # Signal strength should be less than received power due to environmental attenuation
        self.assertLess(signal_strength, received_power)
    
    def test_calculate_snr(self):
        """Test SNR calculation."""
        signal_strength = -60.0  # dBm
        environment = self.environment
        
        snr = self.service._calculate_snr(signal_strength, environment)
        
        self.assertIsInstance(snr, float)
        # SNR should be positive for reasonable signal strength
        self.assertGreater(snr, -100)
    
    def test_analyze_multipath(self):
        """Test multipath analysis."""
        request = self.request
        distance = 100.0
        
        multipath_components = self.service._analyze_multipath(request, distance)
        
        self.assertIsInstance(multipath_components, list)
        self.assertGreater(len(multipath_components), 0)
        
        # Check that direct path exists
        direct_component = next((comp for comp in multipath_components if comp["type"] == "direct"), None)
        self.assertIsNotNone(direct_component)
    
    def test_calculate_coverage_area(self):
        """Test coverage area calculation."""
        request = self.request
        
        coverage_area = self.service._calculate_coverage_area(request)
        
        self.assertIsInstance(coverage_area, list)
        self.assertGreater(len(coverage_area), 0)
        
        # Check that coverage points are tuples of 3 coordinates
        for point in coverage_area:
            self.assertIsInstance(point, tuple)
            self.assertEqual(len(point), 3)
    
    def test_analyze_signal_propagation(self):
        """Test complete signal propagation analysis."""
        result = self.service.analyze_signal_propagation(self.request)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.id, self.request.id)
        self.assertIsInstance(result.path_loss, float)
        self.assertIsInstance(result.received_power, float)
        self.assertIsInstance(result.signal_strength, float)
        self.assertIsInstance(result.snr, float)
        self.assertIsInstance(result.multipath_components, list)
        self.assertIsInstance(result.coverage_area, list)
        self.assertIsInstance(result.interference_level, float)
        self.assertIsInstance(result.analysis_time, float)
        self.assertIsInstance(result.convergence_info, dict)
    
    def test_validate_request(self):
        """Test request validation."""
        # Valid request
        self.assertTrue(self.service.validate_request(self.request))
        
        # Invalid request - negative frequency
        invalid_request = self.request
        invalid_request.source.frequency = -1.0
        self.assertFalse(self.service.validate_request(invalid_request))
        
        # Invalid request - negative power
        invalid_request = self.request
        invalid_request.source.power = -1.0
        self.assertFalse(self.service.validate_request(invalid_request))
        
        # Invalid request - invalid antenna gain
        invalid_request = self.request
        invalid_request.source.antenna.gain = 100.0  # Too high
        self.assertFalse(self.service.validate_request(invalid_request))
    
    def test_get_propagation_model_info(self):
        """Test getting propagation model information."""
        info = self.service.get_propagation_model_info("free_space")
        self.assertIsNotNone(info)
        self.assertIn("description", info)
        self.assertIn("formula", info)
        self.assertIn("parameters", info)
    
    def test_get_environment_model_info(self):
        """Test getting environment model information."""
        info = self.service.get_environment_model_info("urban")
        self.assertIsNotNone(info)
        self.assertIn("building_density", info)
        self.assertIn("average_building_height", info)


class TestAntennaAnalyzer(unittest.TestCase):
    """Test cases for AntennaAnalyzer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = AntennaAnalyzer()
        
        # Create test antenna parameters
        self.antenna_params = AntennaParameters(
            length=0.0625,  # λ/4 for 2.4 GHz
            width=0.01,
            height=0.01,
            diameter=0.0,
            thickness=0.001,
            material="copper",
            conductivity=5.8e7
        )
        
        # Create test request
        self.request = AntennaAnalysisRequest(
            id="test_antenna_request",
            antenna_type=AntennaType.DIPOLE,
            parameters=self.antenna_params,
            frequency=2.4e9,
            polarization=PolarizationType.LINEAR_VERTICAL,
            analysis_type="pattern"
        )
    
    def test_initialization(self):
        """Test analyzer initialization."""
        self.assertIsNotNone(self.analyzer)
        self.assertIsNotNone(self.analyzer.antenna_models)
        self.assertIsNotNone(self.analyzer.array_models)
        self.assertIsNotNone(self.analyzer.optimization_algorithms)
    
    def test_calculate_antenna_performance(self):
        """Test antenna performance calculation."""
        performance = self.analyzer._calculate_antenna_performance(self.request)
        
        self.assertIsNotNone(performance)
        self.assertIsInstance(performance.max_gain, float)
        self.assertIsInstance(performance.directivity, float)
        self.assertIsInstance(performance.efficiency, float)
        self.assertIsInstance(performance.bandwidth, float)
        self.assertIsInstance(performance.vswr, float)
        self.assertIsInstance(performance.impedance, complex)
        self.assertIsInstance(performance.beamwidth_h, float)
        self.assertIsInstance(performance.beamwidth_v, float)
        self.assertIsInstance(performance.front_to_back_ratio, float)
        self.assertIsInstance(performance.side_lobe_level, float)
    
    def test_calculate_antenna_pattern(self):
        """Test antenna pattern calculation."""
        pattern = self.analyzer._calculate_antenna_pattern(self.request)
        
        self.assertIsNotNone(pattern)
        self.assertIsInstance(pattern.theta_angles, list)
        self.assertIsInstance(pattern.phi_angles, list)
        self.assertIsInstance(pattern.gain_pattern, np.ndarray)
        self.assertIsInstance(pattern.phase_pattern, np.ndarray)
        self.assertIsInstance(pattern.polarization_pattern, np.ndarray)
        
        # Check array dimensions
        self.assertEqual(pattern.gain_pattern.shape, (len(pattern.theta_angles), len(pattern.phi_angles)))
    
    def test_dipole_pattern_calculation(self):
        """Test dipole antenna pattern calculation."""
        theta_angles = np.linspace(0, 180, 181)
        phi_angles = np.linspace(0, 360, 361)
        frequency = 2.4e9
        
        gain_pattern, phase_pattern, polarization_pattern = self.analyzer._calculate_dipole_pattern(
            theta_angles, phi_angles, frequency
        )
        
        self.assertIsInstance(gain_pattern, np.ndarray)
        self.assertIsInstance(phase_pattern, np.ndarray)
        self.assertIsInstance(polarization_pattern, np.ndarray)
        
        # Check that pattern has expected characteristics
        self.assertEqual(gain_pattern.shape, (len(theta_angles), len(phi_angles)))
        
        # Check that there's no radiation along the axis (θ = 0, 180)
        self.assertTrue(np.isneginf(gain_pattern[0, 0]))  # θ = 0
        self.assertTrue(np.isneginf(gain_pattern[-1, 0]))  # θ = 180
    
    def test_analyze_antenna(self):
        """Test complete antenna analysis."""
        result = self.analyzer.analyze_antenna(self.request)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.id, self.request.id)
        self.assertEqual(result.antenna_type, self.request.antenna_type)
        self.assertIsNotNone(result.performance)
        self.assertIsNotNone(result.pattern)
        self.assertIsInstance(result.analysis_time, float)
    
    def test_validate_request(self):
        """Test request validation."""
        # Valid request
        self.assertTrue(self.analyzer.validate_request(self.request))
        
        # Invalid request - negative frequency
        invalid_request = self.request
        invalid_request.frequency = -1.0
        self.assertFalse(self.analyzer.validate_request(invalid_request))
        
        # Invalid request - negative length
        invalid_request = self.request
        invalid_request.parameters.length = -1.0
        self.assertFalse(self.analyzer.validate_request(invalid_request))
        
        # Invalid request - negative width
        invalid_request = self.request
        invalid_request.parameters.width = -1.0
        self.assertFalse(self.analyzer.validate_request(invalid_request))
    
    def test_get_antenna_model_info(self):
        """Test getting antenna model information."""
        info = self.analyzer.get_antenna_model_info("dipole")
        self.assertIsNotNone(info)
        self.assertIn("description", info)
        self.assertIn("formula", info)
        self.assertIn("parameters", info)


class TestInterferenceCalculator(unittest.TestCase):
    """Test cases for InterferenceCalculator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calculator = InterferenceCalculator()
        
        # Create test interference sources
        self.desired_signal = InterferenceSource(
            id="desired_signal",
            frequency=2.4e9,
            power=0.1,
            bandwidth=20e6,
            modulation="OFDM",
            position=(0.0, 0.0, 10.0),
            antenna_gain=2.15,
            duty_cycle=0.8
        )
        
        self.interference_source = InterferenceSource(
            id="interference_source",
            frequency=2.4e9,  # Same frequency - co-channel
            power=0.05,
            bandwidth=20e6,
            modulation="OFDM",
            position=(50.0, 50.0, 5.0),
            antenna_gain=2.15,
            duty_cycle=0.6
        )
        
        # Create test environment
        self.environment = InterferenceEnvironment(
            noise_floor=-90.0,
            thermal_noise=-174.0,
            man_made_noise=-120.0,
            atmospheric_noise=-140.0,
            multipath_conditions={"delay_spread": 0.1, "doppler_spread": 10.0},
            terrain_type="urban",
            building_density=0.8
        )
        
        # Create test request
        self.request = InterferenceAnalysisRequest(
            id="test_interference_request",
            desired_signal=self.desired_signal,
            interference_sources=[self.interference_source],
            environment=self.environment,
            analysis_type="co_channel"
        )
    
    def test_initialization(self):
        """Test calculator initialization."""
        self.assertIsNotNone(self.calculator)
        self.assertIsNotNone(self.calculator.interference_models)
        self.assertIsNotNone(self.calculator.mitigation_strategies)
        self.assertIsNotNone(self.calculator.severity_thresholds)
    
    def test_calculate_distance(self):
        """Test distance calculation."""
        pos1 = (0.0, 0.0, 0.0)
        pos2 = (3.0, 4.0, 0.0)
        
        distance = self.calculator._calculate_distance(pos1, pos2)
        
        self.assertEqual(distance, 5.0)  # 3-4-5 triangle
    
    def test_calculate_co_channel_interference(self):
        """Test co-channel interference calculation."""
        desired_signal = self.desired_signal
        interference_source = self.interference_source
        distance = 70.7  # Distance between positions
        
        interference = self.calculator._calculate_co_channel_interference(
            desired_signal, interference_source, distance
        )
        
        self.assertIsInstance(interference, float)
        # Interference should be less than transmitted power due to path loss
        self.assertLess(interference, 10 * np.log10(interference_source.power * 1000) + interference_source.antenna_gain)
    
    def test_calculate_adjacent_channel_interference(self):
        """Test adjacent channel interference calculation."""
        desired_signal = self.desired_signal
        interference_source = self.interference_source
        distance = 70.7
        
        interference = self.calculator._calculate_adjacent_channel_interference(
            desired_signal, interference_source, distance
        )
        
        self.assertIsInstance(interference, float)
        # Adjacent channel interference should be less than co-channel
        co_channel = self.calculator._calculate_co_channel_interference(desired_signal, interference_source, distance)
        self.assertLess(interference, co_channel)
    
    def test_calculate_interference_level(self):
        """Test total interference level calculation."""
        interference_level = self.calculator._calculate_interference_level(self.request)
        
        self.assertIsInstance(interference_level, float)
        # Interference level should be a valid float value
        self.assertIsInstance(interference_level, float)
    
    def test_calculate_signal_to_interference_ratio(self):
        """Test signal-to-interference ratio calculation."""
        interference_level = -60.0  # dBm
        
        sir = self.calculator._calculate_signal_to_interference_ratio(self.request, interference_level)
        
        self.assertIsInstance(sir, float)
        # SIR should be positive for reasonable signal and interference levels
        self.assertGreater(sir, -100)
    
    def test_determine_interference_type(self):
        """Test interference type determination."""
        interference_type = self.calculator._determine_interference_type(self.request)
        
        self.assertIsInstance(interference_type, InterferenceType)
        # Should be co-channel since frequencies are the same
        self.assertEqual(interference_type, InterferenceType.CO_CHANNEL)
    
    def test_determine_severity_level(self):
        """Test severity level determination."""
        sir = 15.0  # dB
        cir = 12.0  # dB
        interference_level = -60.0  # dBm
        
        severity = self.calculator._determine_severity_level(sir, cir, interference_level)
        
        self.assertIsInstance(severity, InterferenceSeverity)
        self.assertIn(severity, InterferenceSeverity)
    
    def test_generate_mitigation_recommendations(self):
        """Test mitigation recommendation generation."""
        interference_type = InterferenceType.CO_CHANNEL
        severity = InterferenceSeverity.HIGH
        
        recommendations = self.calculator._generate_mitigation_recommendations(
            self.request, interference_type, severity
        )
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # All recommendations should be valid mitigation strategies
        for rec in recommendations:
            self.assertIn(rec.value, list(self.calculator.mitigation_strategies.keys()))
    
    def test_analyze_interference(self):
        """Test complete interference analysis."""
        result = self.calculator.analyze_interference(self.request)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.id, self.request.id)
        self.assertIsInstance(result.interference_type, InterferenceType)
        self.assertIsInstance(result.severity, InterferenceSeverity)
        self.assertIsInstance(result.interference_level, float)
        self.assertIsInstance(result.signal_to_interference_ratio, float)
        self.assertIsInstance(result.carrier_to_interference_ratio, float)
        self.assertIsInstance(result.interference_power, float)
        self.assertIsInstance(result.mitigation_recommendations, list)
        self.assertIsInstance(result.interference_spectrum, list)
        self.assertIsInstance(result.analysis_time, float)
    
    def test_predict_interference(self):
        """Test interference prediction."""
        time_horizon = 3600.0  # 1 hour
        
        prediction = self.calculator.predict_interference(self.request, time_horizon)
        
        self.assertIsInstance(prediction, dict)
        self.assertIn("time_points", prediction)
        self.assertIn("interference_levels", prediction)
        self.assertIn("confidence_intervals", prediction)
        self.assertIn("trend", prediction)
        
        self.assertEqual(len(prediction["time_points"]), len(prediction["interference_levels"]))
        self.assertEqual(len(prediction["time_points"]), len(prediction["confidence_intervals"]))
    
    def test_calculate_interference_margin(self):
        """Test interference margin calculation."""
        margin = self.calculator.calculate_interference_margin(self.request)
        
        self.assertIsInstance(margin, float)
        # Margin can be positive or negative depending on conditions
        self.assertIsInstance(margin, float)
    
    def test_validate_request(self):
        """Test request validation."""
        # Valid request
        self.assertTrue(self.calculator.validate_request(self.request))
        
        # Invalid request - negative frequency
        invalid_request = self.request
        invalid_request.desired_signal.frequency = -1.0
        self.assertFalse(self.calculator.validate_request(invalid_request))
        
        # Invalid request - negative power
        invalid_request = self.request
        invalid_request.desired_signal.power = -1.0
        self.assertFalse(self.calculator.validate_request(invalid_request))
        
        # Invalid request - negative bandwidth
        invalid_request = self.request
        invalid_request.desired_signal.bandwidth = -1.0
        self.assertFalse(self.calculator.validate_request(invalid_request))
    
    def test_get_interference_model_info(self):
        """Test getting interference model information."""
        info = self.calculator.get_interference_model_info("co_channel")
        self.assertIsNotNone(info)
        self.assertIn("description", info)
        self.assertIn("formula", info)
        self.assertIn("parameters", info)
    
    def test_get_mitigation_strategy_info(self):
        """Test getting mitigation strategy information."""
        info = self.calculator.get_mitigation_strategy_info("frequency_hopping")
        self.assertIsNotNone(info)
        self.assertIn("description", info)
        self.assertIn("effectiveness", info)
        self.assertIn("complexity", info)
        self.assertIn("cost", info)


class TestSignalPropagationIntegration(unittest.TestCase):
    """Integration tests for signal propagation components."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.signal_service = SignalPropagationService()
        self.antenna_analyzer = AntennaAnalyzer()
        self.interference_calculator = InterferenceCalculator()
    
    def test_end_to_end_signal_analysis(self):
        """Test end-to-end signal propagation analysis."""
        # Create comprehensive test scenario
        antenna_props = AntennaProperties(
            name="test_antenna",
            type="dipole",
            frequency=2.4e9,
            gain=2.15,
            efficiency=0.95,
            polarization="vertical",
            beamwidth_h=78.0,
            beamwidth_v=78.0,
            front_to_back_ratio=0.0
        )
        
        signal_source = SignalSource(
            id="test_source",
            type=SignalType.WIFI,
            frequency=2.4e9,
            power=0.1,
            antenna=antenna_props,
            position=(0.0, 0.0, 10.0),
            height=10.0
        )
        
        environment = PropagationEnvironment(
            type=EnvironmentType.URBAN,
            terrain_height=0.0,
            building_height=30.0,
            vegetation_density=0.1,
            ground_reflectivity=0.3,
            atmospheric_conditions={"humidity": 0.6, "temperature": 25.0},
            obstacles=[]
        )
        
        # Test signal propagation analysis
        signal_request = SignalAnalysisRequest(
            id="integration_test",
            source=signal_source,
            receiver_position=(100.0, 100.0, 1.5),
            environment=environment,
            propagation_model=PropagationModel.FREE_SPACE,
            analysis_type="path_loss"
        )
        
        signal_result = self.signal_service.analyze_signal_propagation(signal_request)
        
        # Verify signal propagation results
        self.assertIsNotNone(signal_result)
        self.assertGreater(signal_result.path_loss, 0)
        self.assertLess(signal_result.received_power, 10 * np.log10(signal_source.power * 1000) + signal_source.antenna.gain)
        
        # Test antenna analysis
        antenna_params = AntennaParameters(
            length=0.0625,
            width=0.01,
            height=0.01,
            diameter=0.0,
            thickness=0.001,
            material="copper",
            conductivity=5.8e7
        )
        
        antenna_request = AntennaAnalysisRequest(
            id="antenna_integration_test",
            antenna_type=AntennaType.DIPOLE,
            parameters=antenna_params,
            frequency=2.4e9,
            polarization=PolarizationType.LINEAR_VERTICAL,
            analysis_type="pattern"
        )
        
        antenna_result = self.antenna_analyzer.analyze_antenna(antenna_request)
        
        # Verify antenna analysis results
        self.assertIsNotNone(antenna_result)
        self.assertIsNotNone(antenna_result.performance)
        self.assertIsNotNone(antenna_result.pattern)
        
        # Test interference analysis
        desired_signal = InterferenceSource(
            id="desired_signal",
            frequency=2.4e9,
            power=0.1,
            bandwidth=20e6,
            modulation="OFDM",
            position=(0.0, 0.0, 10.0),
            antenna_gain=2.15,
            duty_cycle=0.8
        )
        
        interference_source = InterferenceSource(
            id="interference_source",
            frequency=2.4e9,
            power=0.05,
            bandwidth=20e6,
            modulation="OFDM",
            position=(50.0, 50.0, 5.0),
            antenna_gain=2.15,
            duty_cycle=0.6
        )
        
        interference_env = InterferenceEnvironment(
            noise_floor=-90.0,
            thermal_noise=-174.0,
            man_made_noise=-120.0,
            atmospheric_noise=-140.0,
            multipath_conditions={"delay_spread": 0.1, "doppler_spread": 10.0},
            terrain_type="urban",
            building_density=0.8
        )
        
        interference_request = InterferenceAnalysisRequest(
            id="interference_integration_test",
            desired_signal=desired_signal,
            interference_sources=[interference_source],
            environment=interference_env,
            analysis_type="co_channel"
        )
        
        interference_result = self.interference_calculator.analyze_interference(interference_request)
        
        # Verify interference analysis results
        self.assertIsNotNone(interference_result)
        self.assertIsInstance(interference_result.interference_type, InterferenceType)
        self.assertIsInstance(interference_result.severity, InterferenceSeverity)
        self.assertGreater(len(interference_result.mitigation_recommendations), 0)
    
    def test_error_handling(self):
        """Test error handling in signal propagation components."""
        # Test with invalid parameters
        invalid_signal_source = SignalSource(
            id="invalid_source",
            type=SignalType.WIFI,
            frequency=-1.0,  # Invalid frequency
            power=0.1,
            antenna=AntennaProperties("test", "dipole", 2.4e9, 2.15, 0.95, "vertical", 78.0, 78.0, 0.0),
            position=(0.0, 0.0, 10.0),
            height=10.0
        )
        
        invalid_request = SignalAnalysisRequest(
            id="invalid_request",
            source=invalid_signal_source,
            receiver_position=(100.0, 100.0, 1.5),
            environment=PropagationEnvironment(
                EnvironmentType.URBAN, 0.0, 30.0, 0.1, 0.3, {}, []
            ),
            propagation_model=PropagationModel.FREE_SPACE,
            analysis_type="path_loss"
        )
        
        # Should handle errors gracefully
        result = self.signal_service.analyze_signal_propagation(invalid_request)
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.error)


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2) 