"""
Load Calculator for Structural Analysis

This module provides comprehensive load calculation capabilities for structural analysis:
- Dead load calculations
- Live load calculations
- Wind load calculations
- Seismic load calculations
- Dynamic load calculations
- Load combinations and safety factors

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


class LoadCategory(Enum):
    """Categories of structural loads."""
    DEAD = "dead"
    LIVE = "live"
    WIND = "wind"
    SEISMIC = "seismic"
    SNOW = "snow"
    IMPACT = "impact"
    THERMAL = "thermal"
    PRESTRESS = "prestress"


class LoadCombination(Enum):
    """Standard load combinations."""
    ULTIMATE_1 = "ultimate_1"  # 1.4D + 1.6L
    ULTIMATE_2 = "ultimate_2"  # 1.2D + 1.6L + 0.5W
    ULTIMATE_3 = "ultimate_3"  # 1.2D + 1.0W + 1.0L
    ULTIMATE_4 = "ultimate_4"  # 1.2D + 1.0E + 1.0L
    SERVICE_1 = "service_1"    # 1.0D + 1.0L
    SERVICE_2 = "service_2"    # 1.0D + 0.5L + 1.0W


@dataclass
class MaterialDensity:
    """Material density for dead load calculations."""
    name: str
    density: float  # kg/m³
    unit_weight: float  # kN/m³


@dataclass
class WindParameters:
    """Wind load parameters."""
    basic_wind_speed: float  # m/s
    exposure_category: str   # A, B, C, D
    topographic_factor: float
    gust_factor: float
    directionality_factor: float
    importance_factor: float


@dataclass
class SeismicParameters:
    """Seismic load parameters."""
    spectral_acceleration: float  # g
    site_class: str  # A, B, C, D, E, F
    importance_factor: float
    response_modification_factor: float
    fundamental_period: float  # seconds


class LoadCalculator:
    """Comprehensive load calculator for structural analysis."""

    def __init__(self):
        """Initialize the load calculator with standard material densities."""
        self.material_densities = self._initialize_material_densities()
        self.load_factors = self._initialize_load_factors()
        self.wind_parameters = self._initialize_wind_parameters()
        self.seismic_parameters = self._initialize_seismic_parameters()

    def _initialize_material_densities(self) -> Dict[str, MaterialDensity]:
        """Initialize standard material densities."""
        return {
            "concrete": MaterialDensity("concrete", 2400.0, 23.5),
            "steel": MaterialDensity("steel", 7850.0, 77.0),
            "wood": MaterialDensity("wood", 500.0, 4.9),
            "aluminum": MaterialDensity("aluminum", 2700.0, 26.5),
            "glass": MaterialDensity("glass", 2500.0, 24.5),
            "brick": MaterialDensity("brick", 1800.0, 17.6),
            "stone": MaterialDensity("stone", 2600.0, 25.5),
            "soil": MaterialDensity("soil", 1800.0, 17.6),
            "water": MaterialDensity("water", 1000.0, 9.81),
        }

    def _initialize_load_factors(self) -> Dict[str, float]:
        """Initialize load factors for different combinations."""
        return {
            "dead_load": 1.2,
            "live_load": 1.6,
            "wind_load": 1.0,
            "seismic_load": 1.0,
            "snow_load": 1.6,
            "impact_load": 1.0,
        }

    def _initialize_wind_parameters(self) -> Dict[str, WindParameters]:
        """Initialize standard wind parameters."""
        return {
            "standard": WindParameters(
                basic_wind_speed=50.0,
                exposure_category="C",
                topographic_factor=1.0,
                gust_factor=0.85,
                directionality_factor=0.85,
                importance_factor=1.0
            ),
            "high_wind": WindParameters(
                basic_wind_speed=70.0,
                exposure_category="C",
                topographic_factor=1.0,
                gust_factor=0.85,
                directionality_factor=0.85,
                importance_factor=1.15
            ),
            "coastal": WindParameters(
                basic_wind_speed=60.0,
                exposure_category="D",
                topographic_factor=1.0,
                gust_factor=0.85,
                directionality_factor=0.85,
                importance_factor=1.0
            )
        }

    def _initialize_seismic_parameters(self) -> Dict[str, SeismicParameters]:
        """Initialize standard seismic parameters."""
        return {
            "low_seismic": SeismicParameters(
                spectral_acceleration=0.2,
                site_class="C",
                importance_factor=1.0,
                response_modification_factor=3.0,
                fundamental_period=0.5
            ),
            "moderate_seismic": SeismicParameters(
                spectral_acceleration=0.4,
                site_class="C",
                importance_factor=1.0,
                response_modification_factor=3.0,
                fundamental_period=0.5
            ),
            "high_seismic": SeismicParameters(
                spectral_acceleration=0.8,
                site_class="C",
                importance_factor=1.25,
                response_modification_factor=3.0,
                fundamental_period=0.5
            )
        }

    def calculate_dead_load(self, volume: float, material: str) -> float:
        """
        Calculate dead load for a given volume and material.

        Args:
            volume: Volume in m³
            material: Material name

        Returns:
            Dead load in kN
        """
        if material not in self.material_densities:
            raise ValueError(f"Unknown material: {material}")

        unit_weight = self.material_densities[material].unit_weight
        dead_load = volume * unit_weight
        logger.info(f"Calculated dead load: {dead_load:.2f} kN for {volume:.2f} m³ of {material}")
        return dead_load

    def calculate_live_load(self, area: float, occupancy_type: str) -> float:
        """
        Calculate live load based on occupancy type.

        Args:
            area: Floor area in m²
            occupancy_type: Type of occupancy

        Returns:
            Live load in kN
        """
        live_load_values = {
            "residential": 1.92,  # kN/m²
            "office": 2.40,
            "retail": 3.60,
            "warehouse": 6.00,
            "parking": 2.40,
            "roof": 0.96,
            "balcony": 3.00,
            "stairway": 3.60,
            "corridor": 3.60,
        }

        if occupancy_type not in live_load_values:
            raise ValueError(f"Unknown occupancy type: {occupancy_type}")

        live_load = area * live_load_values[occupancy_type]
        logger.info(f"Calculated live load: {live_load:.2f} kN for {area:.2f} m² {occupancy_type}")
        return live_load

    def calculate_wind_load(self, area: float, height: float, wind_params: Optional[WindParameters] = None) -> float:
        """
        Calculate wind load using ASCE 7 methodology.

        Args:
            area: Projected area in m²
            height: Height above ground in m
            wind_params: Wind parameters (uses standard if None)

        Returns:
            Wind load in kN
        """
        if wind_params is None:
            wind_params = self.wind_parameters["standard"]

        # Calculate velocity pressure
        velocity_pressure = 0.613 * wind_params.basic_wind_speed**2

        # Calculate exposure factor
        exposure_factors = {"A": 0.7, "B": 0.7, "C": 1.0, "D": 1.2}
        exposure_factor = exposure_factors.get(wind_params.exposure_category, 1.0)

        # Calculate height factor
        height_factor = (height / 10.0)**0.2 if height > 10.0 else 1.0

        # Calculate design wind pressure
        design_pressure = (velocity_pressure * exposure_factor * height_factor *
                         wind_params.topographic_factor * wind_params.gust_factor *
                         wind_params.directionality_factor * wind_params.importance_factor)

        wind_load = area * design_pressure / 1000.0  # Convert to kN
        logger.info(f"Calculated wind load: {wind_load:.2f} kN for {area:.2f} m² at height {height:.1f} m")
        return wind_load

    def calculate_seismic_load(self, weight: float, seismic_params: Optional[SeismicParameters] = None) -> float:
        """
        Calculate seismic load using simplified equivalent lateral force method.

        Args:
            weight: Total weight of structure in kN
            seismic_params: Seismic parameters (uses moderate if None)

        Returns:
            Seismic load in kN
        """
        if seismic_params is None:
            seismic_params = self.seismic_parameters["moderate_seismic"]

        # Calculate base shear
        base_shear = (weight * seismic_params.spectral_acceleration *
                     seismic_params.importance_factor / seismic_params.response_modification_factor)

        logger.info(f"Calculated seismic load: {base_shear:.2f} kN for weight {weight:.2f} kN")
        return base_shear

    def calculate_snow_load(self, area: float, roof_slope: float, ground_snow_load: float = 1.44) -> float:
        """
        Calculate snow load on roof.

        Args:
            area: Roof area in m²
            roof_slope: Roof slope in degrees
            ground_snow_load: Ground snow load in kN/m²

        Returns:
            Snow load in kN
        """
        # Calculate roof snow load factor
        if roof_slope <= 5.0:
            roof_factor = 1.0
        elif roof_slope <= 30.0:
            roof_factor = 1.0 - (roof_slope - 5.0) / 25.0 * 0.2
        else:
            roof_factor = 0.8

        snow_load = area * ground_snow_load * roof_factor
        logger.info(f"Calculated snow load: {snow_load:.2f} kN for {area:.2f} m² roof with {roof_slope:.1f}° slope")
        return snow_load

    def calculate_impact_load(self, static_load: float, impact_factor: float = 1.5) -> float:
        """
        Calculate impact load.

        Args:
            static_load: Static load in kN
            impact_factor: Impact factor (default 1.5)

        Returns:
            Impact load in kN
        """
        impact_load = static_load * impact_factor
        logger.info(f"Calculated impact load: {impact_load:.2f} kN with factor {impact_factor}")
        return impact_load

    def calculate_thermal_load(self, area: float, temperature_diff: float,
                             thermal_coefficient: float = 12e-6) -> float:
        """
        Calculate thermal load due to temperature changes.

        Args:
            area: Cross-sectional area in m²
            temperature_diff: Temperature difference in °C
            thermal_coefficient: Thermal expansion coefficient in 1/°C

        Returns:
            Thermal load in kN
        """
        # Simplified thermal load calculation
        thermal_strain = thermal_coefficient * temperature_diff
        thermal_load = area * thermal_strain * 200e9 / 1000.0  # Assuming steel modulus
        logger.info(f"Calculated thermal load: {thermal_load:.2f} kN for {temperature_diff:.1f}°C change")
        return thermal_load

    def combine_loads(self, loads: Dict[str, float], combination: LoadCombination) -> float:
        """
        Combine loads according to standard load combinations.

        Args:
            loads: Dictionary of loads by category
            combination: Load combination type

        Returns:
            Combined load in kN
        """
        D = loads.get("dead", 0.0)
        L = loads.get("live", 0.0)
        W = loads.get("wind", 0.0)
        E = loads.get("seismic", 0.0)
        S = loads.get("snow", 0.0)

        if combination == LoadCombination.ULTIMATE_1:
            combined = 1.4 * D + 1.6 * L
        elif combination == LoadCombination.ULTIMATE_2:
            combined = 1.2 * D + 1.6 * L + 0.5 * W
        elif combination == LoadCombination.ULTIMATE_3:
            combined = 1.2 * D + 1.0 * W + 1.0 * L
        elif combination == LoadCombination.ULTIMATE_4:
            combined = 1.2 * D + 1.0 * E + 1.0 * L
        elif combination == LoadCombination.SERVICE_1:
            combined = 1.0 * D + 1.0 * L
        elif combination == LoadCombination.SERVICE_2:
            combined = 1.0 * D + 0.5 * L + 1.0 * W
        else:
            raise ValueError(f"Unknown load combination: {combination}")

        logger.info(f"Combined load ({combination.value}): {combined:.2f} kN")
        return combined

    def calculate_dynamic_load(self, static_load: float, frequency: float,
                             damping_ratio: float = 0.05) -> float:
        """
        Calculate dynamic load amplification factor.

        Args:
            static_load: Static load in kN
            frequency: Loading frequency in Hz
            damping_ratio: Damping ratio (default 0.05)

        Returns:
            Dynamic load in kN
        """
        # Simplified dynamic amplification factor
        if frequency < 1.0:
            amplification_factor = 1.0
        else:
            amplification_factor = 1.0 + 0.5 * frequency / (2 * math.pi * damping_ratio)

        dynamic_load = static_load * amplification_factor
        logger.info(f"Calculated dynamic load: {dynamic_load:.2f} kN (amplification: {amplification_factor:.2f})")
        return dynamic_load

    def get_material_density(self, material: str) -> Optional[MaterialDensity]:
        """Get material density information."""
        return self.material_densities.get(material)

    def add_material_density(self, material: str, density: float, unit_weight: float) -> None:
        """Add custom material density."""
        self.material_densities[material] = MaterialDensity(material, density, unit_weight)
        logger.info(f"Added material density for {material}")

    def get_wind_parameters(self, category: str) -> Optional[WindParameters]:
        """Get wind parameters for a category."""
        return self.wind_parameters.get(category)

    def get_seismic_parameters(self, category: str) -> Optional[SeismicParameters]:
        """Get seismic parameters for a category."""
        return self.seismic_parameters.get(category)
