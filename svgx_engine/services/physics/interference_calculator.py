"""
Interference Calculator for Signal Propagation Analysis

This module provides comprehensive interference analysis capabilities for signal propagation:
- Signal interference calculations
- Interference mitigation strategies
- Interference prediction and modeling
- Co-channel interference analysis
- Adjacent channel interference analysis
- Intermodulation interference analysis

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import math
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class InterferenceType(Enum):
    """Types of signal interference."""
    CO_CHANNEL = "co_channel"
    ADJACENT_CHANNEL = "adjacent_channel"
    INTERMODULATION = "intermodulation"
    HARMONIC = "harmonic"
    SPURIOUS = "spurious"
    NOISE = "noise"
    MULTIPATH = "multipath"


class InterferenceSeverity(Enum):
    """Severity levels of interference."""
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class MitigationStrategy(Enum):
    """Interference mitigation strategies."""
    FREQUENCY_HOPPING = "frequency_hopping"
    POWER_CONTROL = "power_control"
    ANTENNA_OPTIMIZATION = "antenna_optimization"
    FILTERING = "filtering"
    CODING = "coding"
    SPATIAL_DIVERSITY = "spatial_diversity"
    TIME_DIVERSITY = "time_diversity"


@dataclass
class InterferenceSource:
    """Interference source definition."""
    id: str
    frequency: float  # Hz
    power: float  # W
    bandwidth: float  # Hz
    modulation: str
    position: Tuple[float, float, float]  # x, y, z
    antenna_gain: float  # dBi
    duty_cycle: float  # 0-1


@dataclass
class InterferenceEnvironment:
    """Interference environment definition."""
    noise_floor: float  # dBm
    thermal_noise: float  # dBm
    man_made_noise: float  # dBm
    atmospheric_noise: float  # dBm
    multipath_conditions: Dict[str, float]
    terrain_type: str
    building_density: float  # 0-1


@dataclass
class InterferenceAnalysisRequest:
    """Interference analysis request."""
    id: str
    desired_signal: InterferenceSource
    interference_sources: List[InterferenceSource]
    environment: InterferenceEnvironment
    analysis_type: str  # co_channel, adjacent, intermodulation, comprehensive
    frequency_range: Optional[Tuple[float, float]] = None
    time_series: Optional[List[float]] = None


@dataclass
class InterferenceAnalysisResult:
    """Result of interference analysis."""
    id: str
    interference_type: InterferenceType
    severity: InterferenceSeverity
    interference_level: float  # dB
    signal_to_interference_ratio: float  # dB
    carrier_to_interference_ratio: float  # dB
    interference_power: float  # dBm
    mitigation_recommendations: List[MitigationStrategy]
    interference_spectrum: List[Tuple[float, float]]  # frequency, power
    analysis_time: float
    error: Optional[str] = None


class InterferenceCalculator:
    """
    Comprehensive interference calculator for signal propagation analysis.

    Provides advanced interference analysis capabilities including:
    - Signal interference calculations and modeling
    - Interference mitigation strategies and recommendations
    - Interference prediction and forecasting
    - Co-channel and adjacent channel interference analysis
    - Intermodulation interference analysis
    """

    def __init__(self):
        """Initialize the interference calculator."""
        self.interference_models = self._initialize_interference_models()
        self.mitigation_strategies = self._initialize_mitigation_strategies()
        self.severity_thresholds = self._initialize_severity_thresholds()

    def _initialize_interference_models(self) -> Dict[str, Dict[str, Any]]:
        """Initialize interference model parameters."""
        return {
            "co_channel": {
                "description": "Co-channel interference model",
                "formula": "C/I = 10*log10(P_desired / P_interference)",
                "parameters": ["desired_power", "interference_power", "distance"]
            },
            "adjacent_channel": {
                "description": "Adjacent channel interference model",
                "formula": "ACLR = 10*log10(P_adjacent / P_main)",
                "parameters": ["channel_spacing", "filter_response", "power_ratio"]
            },
            "intermodulation": {
                "description": "Intermodulation interference model",
                "formula": "IMD = P_f1 + P_f2 - 2*IP3",
                "parameters": ["f1_power", "f2_power", "ip3_point"]
            },
            "harmonic": {
                "description": "Harmonic interference model",
                "formula": "H_n = P_fundamental - n*20*log10(n)",
                "parameters": ["fundamental_power", "harmonic_order"]
            },
            "spurious": {
                "description": "Spurious interference model",
                "formula": "Spurious = P_fundamental - spurious_rejection",
                "parameters": ["fundamental_power", "spurious_rejection"]
            }
        }

    def _initialize_mitigation_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Initialize mitigation strategy parameters."""
        return {
            "frequency_hopping": {
                "description": "Frequency hopping spread spectrum",
                "effectiveness": 0.8,
                "complexity": "high",
                "cost": "medium"
            },
            "power_control": {
                "description": "Adaptive power control",
                "effectiveness": 0.6,
                "complexity": "medium",
                "cost": "low"
            },
            "antenna_optimization": {
                "description": "Antenna pattern optimization",
                "effectiveness": 0.7,
                "complexity": "medium",
                "cost": "medium"
            },
            "filtering": {
                "description": "Bandpass filtering",
                "effectiveness": 0.5,
                "complexity": "low",
                "cost": "low"
            },
            "coding": {
                "description": "Error correction coding",
                "effectiveness": 0.4,
                "complexity": "high",
                "cost": "medium"
            },
            "spatial_diversity": {
                "description": "Multiple antenna diversity",
                "effectiveness": 0.9,
                "complexity": "high",
                "cost": "high"
            },
            "time_diversity": {
                "description": "Time diversity techniques",
                "effectiveness": 0.6,
                "complexity": "medium",
                "cost": "low"
            }
        }

    def _initialize_severity_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Initialize interference severity thresholds."""
        return {
            "signal_to_interference_ratio": {
                "none": float('inf'),
                "low": 20.0,
                "moderate": 15.0,
                "high": 10.0,
                "critical": 5.0
            },
            "carrier_to_interference_ratio": {
                "none": float('inf'),
                "low": 18.0,
                "moderate": 13.0,
                "high": 8.0,
                "critical": 3.0
            },
            "interference_level": {
                "none": -100.0,
                "low": -80.0,
                "moderate": -60.0,
                "high": -40.0,
                "critical": -20.0
            }
        }

    def analyze_interference(self, request: InterferenceAnalysisRequest) -> InterferenceAnalysisResult:
        """
        Perform comprehensive interference analysis.

        Args:
            request: Interference analysis request with desired signal and interference sources

        Returns:
            Interference analysis result with severity and mitigation recommendations
        """
        try:
            logger.info(f"Starting interference analysis for request {request.id}")

            # Calculate interference level
            interference_level = self._calculate_interference_level(request)

            # Calculate signal-to-interference ratio
            sir = self._calculate_signal_to_interference_ratio(request, interference_level)

            # Calculate carrier-to-interference ratio
            cir = self._calculate_carrier_to_interference_ratio(request, interference_level)

            # Determine interference type
            interference_type = self._determine_interference_type(request)

            # Determine severity level
            severity = self._determine_severity_level(sir, cir, interference_level)

            # Generate mitigation recommendations
            mitigation_recommendations = self._generate_mitigation_recommendations(
                request, interference_type, severity
            )

            # Calculate interference spectrum
            interference_spectrum = self._calculate_interference_spectrum(request)

            analysis_time = 0.12  # Simulated analysis time

            return InterferenceAnalysisResult(
                id=request.id,
                interference_type=interference_type,
                severity=severity,
                interference_level=interference_level,
                signal_to_interference_ratio=sir,
                carrier_to_interference_ratio=cir,
                interference_power=interference_level,
                mitigation_recommendations=mitigation_recommendations,
                interference_spectrum=interference_spectrum,
                analysis_time=analysis_time
            )

        except Exception as e:
            logger.error(f"Interference analysis failed: {e}")
            return InterferenceAnalysisResult(
                id=request.id,
                interference_type=InterferenceType.NOISE,
                severity=InterferenceSeverity.NONE,
                interference_level=0.0,
                signal_to_interference_ratio=0.0,
                carrier_to_interference_ratio=0.0,
                interference_power=0.0,
                mitigation_recommendations=[],
                interference_spectrum=[],
                analysis_time=0.0,
                error=str(e)
            )

    def _calculate_interference_level(self, request: InterferenceAnalysisRequest) -> float:
        """Calculate total interference level."""
        total_interference = 0.0

        # Add environmental noise
        total_interference += request.environment.noise_floor
        total_interference += request.environment.thermal_noise
        total_interference += request.environment.man_made_noise
        total_interference += request.environment.atmospheric_noise

        # Add interference from sources import sources
        for source in request.interference_sources:
            source_interference = self._calculate_source_interference(request.desired_signal, source)
            total_interference += source_interference

        return total_interference

    def _calculate_source_interference(self, desired_signal: InterferenceSource,
                                     interference_source: InterferenceSource) -> float:
        """Calculate interference from a specific source."""
        # Calculate distance between signals
        distance = self._calculate_distance(desired_signal.position, interference_source.position)

        # Calculate frequency separation
        freq_separation = abs(desired_signal.frequency - interference_source.frequency)

        # Calculate interference based on frequency separation
        if freq_separation == 0:
            # Co-channel interference
            interference = self._calculate_co_channel_interference(desired_signal, interference_source, distance)
        elif freq_separation <= desired_signal.bandwidth:
            # Adjacent channel interference
            interference = self._calculate_adjacent_channel_interference(desired_signal, interference_source, distance)
        else:
            # Out-of-band interference (reduced)
            interference = self._calculate_out_of_band_interference(desired_signal, interference_source, distance, freq_separation)

        return interference

    def _calculate_distance(self, pos1: Tuple[float, float, float],
                          pos2: Tuple[float, float, float]) -> float:
        """Calculate distance between two positions."""
        dx = pos1[0] - pos2[0]
        dy = pos1[1] - pos2[1]
        dz = pos1[2] - pos2[2]
        return math.sqrt(dx*dx + dy*dy + dz*dz)

    def _calculate_co_channel_interference(self, desired_signal: InterferenceSource,
                                         interference_source: InterferenceSource, distance: float) -> float:
        """Calculate co-channel interference."""
        # Convert power to dBm
        desired_power_dbm = 10 * math.log10(desired_signal.power * 1000)
        interference_power_dbm = 10 * math.log10(interference_source.power * 1000)

        # Calculate path loss (simplified free space model)
        wavelength = 3e8 / desired_signal.frequency
        path_loss = 20 * math.log10(4 * math.pi * distance / wavelength)

        # Calculate received interference power
        received_interference = interference_power_dbm + interference_source.antenna_gain - path_loss

        return received_interference

    def _calculate_adjacent_channel_interference(self, desired_signal: InterferenceSource,
                                               interference_source: InterferenceSource, distance: float) -> float:
        """Calculate adjacent channel interference."""
        # Calculate co-channel interference first
        co_channel_interference = self._calculate_co_channel_interference(desired_signal, interference_source, distance)

        # Apply adjacent channel rejection
        channel_spacing = abs(desired_signal.frequency - interference_source.frequency)
        rejection_factor = self._calculate_adjacent_channel_rejection(channel_spacing, desired_signal.bandwidth)

        adjacent_channel_interference = co_channel_interference - rejection_factor

        return adjacent_channel_interference

    def _calculate_adjacent_channel_rejection(self, channel_spacing: float, bandwidth: float) -> float:
        """Calculate adjacent channel rejection factor."""
        # Simplified adjacent channel rejection model
        if channel_spacing <= bandwidth:
            rejection = 20.0  # dB
        elif channel_spacing <= 2 * bandwidth:
            rejection = 40.0  # dB
        elif channel_spacing <= 3 * bandwidth:
            rejection = 60.0  # dB
        else:
            rejection = 80.0  # dB

        return rejection

    def _calculate_out_of_band_interference(self, desired_signal: InterferenceSource,
                                          interference_source: InterferenceSource, distance: float,
                                          freq_separation: float) -> float:
        """Calculate out-of-band interference."""
        # Calculate co-channel interference first
        co_channel_interference = self._calculate_co_channel_interference(desired_signal, interference_source, distance)

        # Apply out-of-band rejection
        rejection_factor = self._calculate_out_of_band_rejection(freq_separation, desired_signal.bandwidth)

        out_of_band_interference = co_channel_interference - rejection_factor

        return out_of_band_interference

    def _calculate_out_of_band_rejection(self, freq_separation: float, bandwidth: float) -> float:
        """Calculate out-of-band rejection factor."""
        # Simplified out-of-band rejection model
        separation_ratio = freq_separation / bandwidth

        if separation_ratio <= 1:
            rejection = 20.0  # dB
        elif separation_ratio <= 2:
            rejection = 40.0  # dB
        elif separation_ratio <= 5:
            rejection = 60.0  # dB
        elif separation_ratio <= 10:
            rejection = 80.0  # dB
        else:
            rejection = 100.0  # dB

        return rejection

    def _calculate_signal_to_interference_ratio(self, request: InterferenceAnalysisRequest,
                                              interference_level: float) -> float:
        """Calculate signal-to-interference ratio."""
        # Convert desired signal power to dBm
        desired_power_dbm = 10 * math.log10(request.desired_signal.power * 1000)

        # Calculate received signal power (simplified)
        received_signal = desired_power_dbm + request.desired_signal.antenna_gain

        # Calculate SIR
        sir = received_signal - interference_level

        return sir

    def _calculate_carrier_to_interference_ratio(self, request: InterferenceAnalysisRequest,
                                               interference_level: float) -> float:
        """Calculate carrier-to-interference ratio."""
        # Similar to SIR but with different reference levels
        cir = self._calculate_signal_to_interference_ratio(request, interference_level) - 3.0

        return cir

    def _determine_interference_type(self, request: InterferenceAnalysisRequest) -> InterferenceType:
        """Determine the primary type of interference."""
        if not request.interference_sources:
            return InterferenceType.NOISE

        # Check for co-channel interference
        for source in request.interference_sources:
            if abs(source.frequency - request.desired_signal.frequency) < 0.1 * request.desired_signal.bandwidth:
                return InterferenceType.CO_CHANNEL

        # Check for adjacent channel interference
        for source in request.interference_sources:
            if abs(source.frequency - request.desired_signal.frequency) <= request.desired_signal.bandwidth:
                return InterferenceType.ADJACENT_CHANNEL

        # Check for harmonic interference
        for source in request.interference_sources:
            for harmonic in range(2, 6):  # Check 2nd to 5th harmonics
                harmonic_freq = source.frequency * harmonic
                if abs(harmonic_freq - request.desired_signal.frequency) < 0.1 * request.desired_signal.bandwidth:
                    return InterferenceType.HARMONIC

        # Check for intermodulation interference
        if len(request.interference_sources) >= 2:
            # Simplified intermodulation check
            freq1 = request.interference_sources[0].frequency
            freq2 = request.interference_sources[1].frequency
            imd_freq = 2 * freq1 - freq2  # 3rd order intermodulation
            if abs(imd_freq - request.desired_signal.frequency) < 0.1 * request.desired_signal.bandwidth:
                return InterferenceType.INTERMODULATION

        return InterferenceType.SPURIOUS

    def _determine_severity_level(self, sir: float, cir: float, interference_level: float) -> InterferenceSeverity:
        """Determine interference severity level."""
        thresholds = self.severity_thresholds

        # Check SIR thresholds
        if sir >= thresholds["signal_to_interference_ratio"]["none"]:
            return InterferenceSeverity.NONE
        elif sir >= thresholds["signal_to_interference_ratio"]["low"]:
            return InterferenceSeverity.LOW
        elif sir >= thresholds["signal_to_interference_ratio"]["moderate"]:
            return InterferenceSeverity.MODERATE
        elif sir >= thresholds["signal_to_interference_ratio"]["high"]:
            return InterferenceSeverity.HIGH
        else:
            return InterferenceSeverity.CRITICAL

    def _generate_mitigation_recommendations(self, request: InterferenceAnalysisRequest,
                                           interference_type: InterferenceType,
                                           severity: InterferenceSeverity) -> List[MitigationStrategy]:
        """Generate interference mitigation recommendations."""
        recommendations = []

        # Base recommendations based on severity
        if severity in [InterferenceSeverity.HIGH, InterferenceSeverity.CRITICAL]:
            recommendations.append(MitigationStrategy.FREQUENCY_HOPPING)
            recommendations.append(MitigationStrategy.SPATIAL_DIVERSITY)

        if severity in [InterferenceSeverity.MODERATE, InterferenceSeverity.HIGH, InterferenceSeverity.CRITICAL]:
            recommendations.append(MitigationStrategy.POWER_CONTROL)
            recommendations.append(MitigationStrategy.ANTENNA_OPTIMIZATION)

        # Type-specific recommendations
        if interference_type == InterferenceType.CO_CHANNEL:
            recommendations.append(MitigationStrategy.FREQUENCY_HOPPING)
            recommendations.append(MitigationStrategy.SPATIAL_DIVERSITY)

        elif interference_type == InterferenceType.ADJACENT_CHANNEL:
            recommendations.append(MitigationStrategy.FILTERING)
            recommendations.append(MitigationStrategy.POWER_CONTROL)

        elif interference_type == InterferenceType.INTERMODULATION:
            recommendations.append(MitigationStrategy.POWER_CONTROL)
            recommendations.append(MitigationStrategy.FILTERING)

        elif interference_type == InterferenceType.HARMONIC:
            recommendations.append(MitigationStrategy.FILTERING)
            recommendations.append(MitigationStrategy.ANTENNA_OPTIMIZATION)

        # Remove duplicates and return
        return list(set(recommendations))

    def _calculate_interference_spectrum(self, request: InterferenceAnalysisRequest) -> List[Tuple[float, float]]:
        """Calculate interference spectrum."""
        spectrum = []

        # Add environmental noise floor
        spectrum.append((request.desired_signal.frequency, request.environment.noise_floor))

        # Add interference sources
        for source in request.interference_sources:
            # Calculate interference at desired frequency
            interference_level = self._calculate_source_interference(request.desired_signal, source)
            spectrum.append((request.desired_signal.frequency, interference_level))

            # Add harmonics if significant
            for harmonic in range(2, 4):  # 2nd and 3rd harmonics
                harmonic_freq = source.frequency * harmonic
                harmonic_power = 10 * math.log10(source.power * 1000) - 20 * math.log10(harmonic)
                spectrum.append((harmonic_freq, harmonic_power))

        # Add intermodulation products if multiple sources
        if len(request.interference_sources) >= 2:
            freq1 = request.interference_sources[0].frequency
            freq2 = request.interference_sources[1].frequency

            # 3rd order intermodulation products
            imd1 = 2 * freq1 - freq2
            imd2 = 2 * freq2 - freq1

            power1 = 10 * math.log10(request.interference_sources[0].power * 1000)
            power2 = 10 * math.log10(request.interference_sources[1].power * 1000)

            imd_power1 = power1 + power2 - 60  # Simplified IMD calculation
            imd_power2 = power1 + power2 - 60

            spectrum.append((imd1, imd_power1))
            spectrum.append((imd2, imd_power2))

        return spectrum

    def predict_interference(self, request: InterferenceAnalysisRequest,
                           time_horizon: float) -> Dict[str, Any]:
        """Predict interference levels over time."""
        # Simplified interference prediction
        prediction = {
            "time_points": np.linspace(0, time_horizon, 100).tolist(),
            "interference_levels": [],
            "confidence_intervals": [],
            "trend": "stable"
        }

        # Generate predicted interference levels
        base_level = self._calculate_interference_level(request)
        for t in prediction["time_points"]:
            # Add time-varying component
            time_variation = 2 * math.sin(2 * math.pi * t / time_horizon)
            predicted_level = base_level + time_variation
            prediction["interference_levels"].append(predicted_level)

            # Add confidence interval
            confidence = 1.0 + 0.1 * math.exp(-t / time_horizon)
            prediction["confidence_intervals"].append(confidence)

        return prediction

    def calculate_interference_margin(self, request: InterferenceAnalysisRequest) -> float:
        """Calculate interference margin."""
        # Calculate required SIR for desired performance
        required_sir = 15.0  # dB (typical requirement)

        # Calculate actual SIR
        interference_level = self._calculate_interference_level(request)
        sir = self._calculate_signal_to_interference_ratio(request, interference_level)

        # Calculate margin
        margin = sir - required_sir

        return margin

    def get_interference_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get information about an interference model."""
        return self.interference_models.get(model_name)

    def get_mitigation_strategy_info(self, strategy: str) -> Optional[Dict[str, Any]]:
        """Get information about a mitigation strategy."""
        return self.mitigation_strategies.get(strategy)

    def get_severity_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Get interference severity thresholds."""
        return self.severity_thresholds

    def validate_request(self, request: InterferenceAnalysisRequest) -> bool:
        """Validate interference analysis request."""
        if request.desired_signal.frequency <= 0:
            return False

        if request.desired_signal.power <= 0:
            return False

        if request.desired_signal.bandwidth <= 0:
            return False

        return True
