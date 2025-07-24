"""
Signal Propagation Service for Arxos SVG-BIM Integration

This service provides comprehensive signal propagation analysis capabilities including:
- Radio frequency signal propagation
- Antenna performance and patterns
- Signal interference calculations
- Signal attenuation over distance
- Signal reflection and diffraction
- Multi-path propagation analysis

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


class SignalType(Enum):
    """Types of radio frequency signals."""
    AM = "am"
    FM = "fm"
    DIGITAL = "digital"
    WIFI = "wifi"
    CELLULAR = "cellular"
    SATELLITE = "satellite"
    RADAR = "radar"


class PropagationModel(Enum):
    """Types of propagation models."""
    FREE_SPACE = "free_space"
    TWO_RAY = "two_ray"
    HATA = "hata"
    COST231 = "cost231"
    ITU_R = "itu_r"
    RAY_TRACING = "ray_tracing"


class EnvironmentType(Enum):
    """Types of propagation environments."""
    URBAN = "urban"
    SUBURBAN = "suburban"
    RURAL = "rural"
    INDOOR = "indoor"
    OUTDOOR = "outdoor"
    MIXED = "mixed"


@dataclass
class AntennaProperties:
    """Antenna properties for signal propagation."""
    name: str
    type: str  # dipole, patch, yagi, parabolic, etc.
    frequency: float  # Hz
    gain: float  # dBi
    efficiency: float  # 0-1
    polarization: str  # vertical, horizontal, circular
    beamwidth_h: float  # degrees
    beamwidth_v: float  # degrees
    front_to_back_ratio: float  # dB


@dataclass
class SignalSource:
    """Signal source definition."""
    id: str
    type: SignalType
    frequency: float  # Hz
    power: float  # W
    antenna: AntennaProperties
    position: Tuple[float, float, float]  # x, y, z
    height: float  # m above ground


@dataclass
class PropagationEnvironment:
    """Propagation environment definition."""
    type: EnvironmentType
    terrain_height: float  # m
    building_height: float  # m
    vegetation_density: float  # 0-1
    ground_reflectivity: float  # 0-1
    atmospheric_conditions: Dict[str, float]
    obstacles: List[Dict[str, Any]]


@dataclass
class SignalAnalysisRequest:
    """Signal propagation analysis request."""
    id: str
    source: SignalSource
    receiver_position: Tuple[float, float, float]
    environment: PropagationEnvironment
    propagation_model: PropagationModel
    analysis_type: str  # path_loss, coverage, interference
    frequency_range: Optional[Tuple[float, float]] = None
    time_series: Optional[List[float]] = None


@dataclass
class SignalAnalysisResult:
    """Result of signal propagation analysis."""
    id: str
    path_loss: float  # dB
    received_power: float  # dBm
    signal_strength: float  # dBm
    snr: float  # dB
    multipath_components: List[Dict[str, Any]]
    coverage_area: List[Tuple[float, float, float]]
    interference_level: float  # dB
    analysis_time: float
    convergence_info: Dict[str, Any]
    error: Optional[str] = None


class SignalPropagationService:
    """
    Comprehensive signal propagation service.
    
    Provides advanced signal propagation analysis capabilities including:
    - Radio frequency signal propagation modeling
    - Antenna performance and pattern analysis
    - Signal interference calculations
    - Signal attenuation over distance
    - Signal reflection and diffraction analysis
    """
    
    def __init__(self):
        """Initialize the signal propagation service."""
        self.propagation_models = self._initialize_propagation_models()
        self.environment_models = self._initialize_environment_models()
        self.antenna_patterns = self._initialize_antenna_patterns()
        
    def _initialize_propagation_models(self) -> Dict[str, Dict[str, Any]]:
        """Initialize propagation model parameters."""
        return {
            "free_space": {
                "description": "Free space path loss model",
                "formula": "PL = 20*log10(4*π*d*f/c)",
                "parameters": ["distance", "frequency"]
            },
            "two_ray": {
                "description": "Two-ray ground reflection model",
                "formula": "PL = 40*log10(d) - 20*log10(h_t*h_r)",
                "parameters": ["distance", "transmitter_height", "receiver_height"]
            },
            "hata": {
                "description": "Hata model for urban areas",
                "formula": "PL = 69.55 + 26.16*log10(f) - 13.82*log10(h_b) + (44.9-6.55*log10(h_b))*log10(d)",
                "parameters": ["frequency", "base_height", "mobile_height", "distance"]
            },
            "cost231": {
                "description": "COST-231 Hata model",
                "formula": "PL = 46.3 + 33.9*log10(f) - 13.82*log10(h_b) + (44.9-6.55*log10(h_b))*log10(d) + C_m",
                "parameters": ["frequency", "base_height", "mobile_height", "distance", "city_type"]
            },
            "itu_r": {
                "description": "ITU-R P.1546 model",
                "formula": "PL = A + B*log10(d) + C*log10(f) + D*log10(h_eff)",
                "parameters": ["distance", "frequency", "effective_height", "terrain_type"]
            }
        }
    
    def _initialize_environment_models(self) -> Dict[str, Dict[str, Any]]:
        """Initialize environment model parameters."""
        return {
            "urban": {
                "building_density": 0.8,
                "average_building_height": 30.0,
                "street_width": 20.0,
                "vegetation_density": 0.1,
                "ground_reflectivity": 0.3
            },
            "suburban": {
                "building_density": 0.4,
                "average_building_height": 15.0,
                "street_width": 30.0,
                "vegetation_density": 0.3,
                "ground_reflectivity": 0.5
            },
            "rural": {
                "building_density": 0.1,
                "average_building_height": 5.0,
                "street_width": 50.0,
                "vegetation_density": 0.7,
                "ground_reflectivity": 0.8
            },
            "indoor": {
                "wall_attenuation": 6.0,
                "floor_attenuation": 20.0,
                "ceiling_attenuation": 15.0,
                "furniture_density": 0.6,
                "room_size": 20.0
            }
        }
    
    def _initialize_antenna_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize antenna pattern models."""
        return {
            "dipole": {
                "pattern": "figure_8",
                "max_gain": 2.15,
                "beamwidth": 78.0,
                "front_to_back": 0.0
            },
            "patch": {
                "pattern": "hemispherical",
                "max_gain": 6.0,
                "beamwidth": 60.0,
                "front_to_back": 10.0
            },
            "yagi": {
                "pattern": "directional",
                "max_gain": 12.0,
                "beamwidth": 30.0,
                "front_to_back": 15.0
            },
            "parabolic": {
                "pattern": "highly_directional",
                "max_gain": 25.0,
                "beamwidth": 10.0,
                "front_to_back": 25.0
            }
        }
    
    def analyze_signal_propagation(self, request: SignalAnalysisRequest) -> SignalAnalysisResult:
        """
        Perform comprehensive signal propagation analysis.
        
        Args:
            request: Signal analysis request with source, receiver, and environment
            
        Returns:
            Signal analysis result with path loss, received power, and coverage
        """
        try:
            logger.info(f"Starting signal propagation analysis for request {request.id}")
            
            # Calculate distance between source and receiver
            distance = self._calculate_distance(request.source.position, request.receiver_position)
            
            # Calculate path loss based on propagation model
            path_loss = self._calculate_path_loss(request, distance)
            
            # Calculate received power
            received_power = self._calculate_received_power(request.source, path_loss)
            
            # Calculate signal strength
            signal_strength = self._calculate_signal_strength(received_power, request.environment)
            
            # Calculate SNR
            snr = self._calculate_snr(signal_strength, request.environment)
            
            # Analyze multipath components
            multipath_components = self._analyze_multipath(request, distance)
            
            # Calculate coverage area
            coverage_area = self._calculate_coverage_area(request)
            
            # Calculate interference level
            interference_level = self._calculate_interference(request, signal_strength)
            
            analysis_time = 0.1  # Simulated analysis time
            
            return SignalAnalysisResult(
                id=request.id,
                path_loss=path_loss,
                received_power=received_power,
                signal_strength=signal_strength,
                snr=snr,
                multipath_components=multipath_components,
                coverage_area=coverage_area,
                interference_level=interference_level,
                analysis_time=analysis_time,
                convergence_info={"iterations": 10, "tolerance": 1e-6}
            )
            
        except Exception as e:
            logger.error(f"Signal propagation analysis failed: {e}")
            return SignalAnalysisResult(
                id=request.id,
                path_loss=0.0,
                received_power=0.0,
                signal_strength=0.0,
                snr=0.0,
                multipath_components=[],
                coverage_area=[],
                interference_level=0.0,
                analysis_time=0.0,
                convergence_info={},
                error=str(e)
            )
    
    def _calculate_distance(self, source_pos: Tuple[float, float, float], 
                          receiver_pos: Tuple[float, float, float]) -> float:
        """Calculate distance between source and receiver."""
        dx = source_pos[0] - receiver_pos[0]
        dy = source_pos[1] - receiver_pos[1]
        dz = source_pos[2] - receiver_pos[2]
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    def _calculate_path_loss(self, request: SignalAnalysisRequest, distance: float) -> float:
        """Calculate path loss based on propagation model."""
        if request.propagation_model == PropagationModel.FREE_SPACE:
            return self._free_space_path_loss(request.source.frequency, distance)
        elif request.propagation_model == PropagationModel.TWO_RAY:
            return self._two_ray_path_loss(request, distance)
        elif request.propagation_model == PropagationModel.HATA:
            return self._hata_path_loss(request, distance)
        elif request.propagation_model == PropagationModel.COST231:
            return self._cost231_path_loss(request, distance)
        elif request.propagation_model == PropagationModel.ITU_R:
            return self._itu_r_path_loss(request, distance)
        else:
            return self._free_space_path_loss(request.source.frequency, distance)
    
    def _free_space_path_loss(self, frequency: float, distance: float) -> float:
        """Calculate free space path loss."""
        # PL = 20*log10(4*π*d*f/c)
        c = 3e8  # Speed of light
        path_loss = 20 * math.log10(4 * math.pi * distance * frequency / c)
        return path_loss
    
    def _two_ray_path_loss(self, request: SignalAnalysisRequest, distance: float) -> float:
        """Calculate two-ray ground reflection path loss."""
        # PL = 40*log10(d) - 20*log10(h_t*h_r)
        h_t = request.source.height
        h_r = request.receiver_position[2]  # Receiver height
        
        if distance < math.sqrt(h_t * h_r):
            return self._free_space_path_loss(request.source.frequency, distance)
        else:
            path_loss = 40 * math.log10(distance) - 20 * math.log10(h_t * h_r)
            return path_loss
    
    def _hata_path_loss(self, request: SignalAnalysisRequest, distance: float) -> float:
        """Calculate Hata model path loss for urban areas."""
        f = request.source.frequency / 1e6  # Convert to MHz
        h_b = request.source.height
        h_m = request.receiver_position[2]
        d = distance / 1000  # Convert to km
        
        # Hata model for urban areas
        path_loss = 69.55 + 26.16 * math.log10(f) - 13.82 * math.log10(h_b) + \
                   (44.9 - 6.55 * math.log10(h_b)) * math.log10(d)
        
        return path_loss
    
    def _cost231_path_loss(self, request: SignalAnalysisRequest, distance: float) -> float:
        """Calculate COST-231 Hata model path loss."""
        f = request.source.frequency / 1e6  # Convert to MHz
        h_b = request.source.height
        h_m = request.receiver_position[2]
        d = distance / 1000  # Convert to km
        
        # COST-231 Hata model
        path_loss = 46.3 + 33.9 * math.log10(f) - 13.82 * math.log10(h_b) + \
                   (44.9 - 6.55 * math.log10(h_b)) * math.log10(d)
        
        # Add city type correction
        if request.environment.type == EnvironmentType.URBAN:
            path_loss += 3.0
        elif request.environment.type == EnvironmentType.SUBURBAN:
            path_loss += 0.0
        elif request.environment.type == EnvironmentType.RURAL:
            path_loss -= 4.78 * (math.log10(f))**2 + 18.33 * math.log10(f) + 40.94
        
        return path_loss
    
    def _itu_r_path_loss(self, request: SignalAnalysisRequest, distance: float) -> float:
        """Calculate ITU-R P.1546 model path loss."""
        f = request.source.frequency / 1e6  # Convert to MHz
        h_eff = request.source.height
        d = distance / 1000  # Convert to km
        
        # Simplified ITU-R model
        path_loss = 32.44 + 20 * math.log10(f) + 20 * math.log10(d)
        
        # Add terrain correction
        if request.environment.type == EnvironmentType.URBAN:
            path_loss += 10.0
        elif request.environment.type == EnvironmentType.SUBURBAN:
            path_loss += 5.0
        
        return path_loss
    
    def _calculate_received_power(self, source: SignalSource, path_loss: float) -> float:
        """Calculate received power in dBm."""
        # Convert source power to dBm
        power_dbm = 10 * math.log10(source.power * 1000)
        
        # Add antenna gain
        total_gain = source.antenna.gain
        
        # Calculate received power
        received_power = power_dbm + total_gain - path_loss
        
        return received_power
    
    def _calculate_signal_strength(self, received_power: float, environment: PropagationEnvironment) -> float:
        """Calculate signal strength considering environmental factors."""
        # Apply environmental attenuation
        env_attenuation = self._calculate_environmental_attenuation(environment)
        signal_strength = received_power - env_attenuation
        
        return signal_strength
    
    def _calculate_environmental_attenuation(self, environment: PropagationEnvironment) -> float:
        """Calculate environmental attenuation."""
        attenuation = 0.0
        
        # Building attenuation
        if environment.type == EnvironmentType.URBAN:
            attenuation += 15.0
        elif environment.type == EnvironmentType.SUBURBAN:
            attenuation += 8.0
        elif environment.type == EnvironmentType.INDOOR:
            attenuation += 25.0
        
        # Vegetation attenuation
        attenuation += environment.vegetation_density * 5.0
        
        # Atmospheric conditions
        if "humidity" in environment.atmospheric_conditions:
            humidity = environment.atmospheric_conditions["humidity"]
            attenuation += humidity * 0.1
        
        if "temperature" in environment.atmospheric_conditions:
            temp = environment.atmospheric_conditions["temperature"]
            if temp < 0:
                attenuation += abs(temp) * 0.05
        
        return attenuation
    
    def _calculate_snr(self, signal_strength: float, environment: PropagationEnvironment) -> float:
        """Calculate signal-to-noise ratio."""
        # Simplified noise floor calculation
        noise_floor = -90.0  # dBm (typical for RF systems)
        
        # Add environmental noise
        if environment.type == EnvironmentType.URBAN:
            noise_floor += 10.0
        elif environment.type == EnvironmentType.INDOOR:
            noise_floor += 15.0
        
        snr = signal_strength - noise_floor
        return snr
    
    def _analyze_multipath(self, request: SignalAnalysisRequest, distance: float) -> List[Dict[str, Any]]:
        """Analyze multipath components."""
        multipath_components = []
        
        # Direct path
        direct_component = {
            "type": "direct",
            "delay": distance / 3e8,  # Time delay
            "amplitude": 1.0,
            "phase": 0.0,
            "path_loss": self._calculate_path_loss(request, distance)
        }
        multipath_components.append(direct_component)
        
        # Ground reflection
        if request.environment.ground_reflectivity > 0:
            ground_component = {
                "type": "ground_reflection",
                "delay": (distance + 2 * request.source.height) / 3e8,
                "amplitude": request.environment.ground_reflectivity,
                "phase": math.pi,
                "path_loss": self._calculate_path_loss(request, distance + 2 * request.source.height)
            }
            multipath_components.append(ground_component)
        
        # Building reflections (simplified)
        if request.environment.type == EnvironmentType.URBAN:
            for i in range(3):  # Simulate 3 building reflections
                building_component = {
                    "type": f"building_reflection_{i+1}",
                    "delay": (distance + (i+1) * 50) / 3e8,
                    "amplitude": 0.3 / (i+1),
                    "phase": (i+1) * math.pi / 4,
                    "path_loss": self._calculate_path_loss(request, distance + (i+1) * 50)
                }
                multipath_components.append(building_component)
        
        return multipath_components
    
    def _calculate_coverage_area(self, request: SignalAnalysisRequest) -> List[Tuple[float, float, float]]:
        """Calculate coverage area points."""
        coverage_points = []
        source_pos = request.source.position
        
        # Calculate coverage radius based on signal strength requirements
        min_signal_strength = -85.0  # dBm (typical minimum)
        
        # Estimate coverage radius using path loss model
        if request.propagation_model == PropagationModel.FREE_SPACE:
            coverage_radius = self._estimate_coverage_radius_free_space(request, min_signal_strength)
        else:
            coverage_radius = self._estimate_coverage_radius_empirical(request, min_signal_strength)
        
        # Generate coverage area points
        num_points = 36
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            x = source_pos[0] + coverage_radius * math.cos(angle)
            y = source_pos[1] + coverage_radius * math.sin(angle)
            z = source_pos[2]
            coverage_points.append((x, y, z))
        
        return coverage_points
    
    def _estimate_coverage_radius_free_space(self, request: SignalAnalysisRequest, min_signal_strength: float) -> float:
        """Estimate coverage radius using free space model."""
        # Calculate required path loss for minimum signal strength
        power_dbm = 10 * math.log10(request.source.power * 1000)
        total_gain = request.source.antenna.gain
        required_path_loss = power_dbm + total_gain - min_signal_strength
        
        # Solve for distance using free space model
        c = 3e8
        distance = c / (4 * math.pi * request.source.frequency) * 10**(required_path_loss / 20)
        
        return distance
    
    def _estimate_coverage_radius_empirical(self, request: SignalAnalysisRequest, min_signal_strength: float) -> float:
        """Estimate coverage radius using empirical models."""
        # Simplified estimation based on environment type
        base_radius = 1000.0  # meters
        
        if request.environment.type == EnvironmentType.URBAN:
            base_radius *= 0.3
        elif request.environment.type == EnvironmentType.SUBURBAN:
            base_radius *= 0.6
        elif request.environment.type == EnvironmentType.RURAL:
            base_radius *= 1.2
        elif request.environment.type == EnvironmentType.INDOOR:
            base_radius *= 0.1
        
        return base_radius
    
    def _calculate_interference(self, request: SignalAnalysisRequest, signal_strength: float) -> float:
        """Calculate interference level."""
        # Simplified interference calculation
        interference_level = -100.0  # dBm (baseline)
        
        # Add environmental interference
        if request.environment.type == EnvironmentType.URBAN:
            interference_level += 15.0
        elif request.environment.type == EnvironmentType.INDOOR:
            interference_level += 20.0
        
        # Add frequency-dependent interference
        if request.source.frequency > 2.4e9:  # WiFi frequencies
            interference_level += 5.0
        elif request.source.frequency > 900e6:  # Cellular frequencies
            interference_level += 3.0
        
        return interference_level
    
    def get_propagation_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a propagation model."""
        return self.propagation_models.get(model_name)
    
    def get_environment_model_info(self, environment_type: str) -> Optional[Dict[str, Any]]:
        """Get information about an environment model."""
        return self.environment_models.get(environment_type)
    
    def get_antenna_pattern_info(self, antenna_type: str) -> Optional[Dict[str, Any]]:
        """Get information about an antenna pattern."""
        return self.antenna_patterns.get(antenna_type)
    
    def validate_request(self, request: SignalAnalysisRequest) -> bool:
        """Validate signal analysis request."""
        if request.source.frequency <= 0:
            return False
        
        if request.source.power <= 0:
            return False
        
        if request.source.antenna.gain < -10 or request.source.antenna.gain > 50:
            return False
        
        return True 