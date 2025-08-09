"""
Pressure Analyzer for Fluid Dynamics Analysis

This module provides comprehensive pressure analysis capabilities for fluid dynamics:
- Pressure drop calculations
- Pressure distribution analysis
- Pressure wave propagation
- Pressure vessel analysis
- Pressure safety analysis
- Pressure measurement and calibration

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


class PressureType(Enum):
    """Types of pressure measurements."""
    STATIC = "static"
    DYNAMIC = "dynamic"
    TOTAL = "total"
    ABSOLUTE = "absolute"
    GAUGE = "gauge"
    VACUUM = "vacuum"


class PressureUnit(Enum):
    """Pressure units."""
    PA = "Pa"
    KPA = "kPa"
    MPA = "MPa"
    BAR = "bar"
    PSI = "psi"
    ATM = "atm"
    MMHG = "mmHg"
    INHG = "inHg"


@dataclass
class PressurePoint:
    """Pressure measurement point."""
    x: float      # m
    y: float      # m
    z: float      # m
    pressure: float  # Pa
    pressure_type: PressureType
    timestamp: float  # s


@dataclass
class PressureVessel:
    """Pressure vessel properties."""
    diameter: float      # m
    length: float        # m
    wall_thickness: float # m
    material: str
    design_pressure: float # Pa
    operating_pressure: float # Pa
    temperature: float   # K


@dataclass
class PressureWave:
    """Pressure wave properties."""
    amplitude: float     # Pa
    frequency: float     # Hz
    wavelength: float    # m
    speed: float         # m/s
    direction: Tuple[float, float, float]  # unit vector


class PressureAnalyzer:
    """Comprehensive pressure analyzer for fluid dynamics analysis."""

    def __init__(self):
        """Initialize the pressure analyzer."""
        self.material_properties = self._initialize_material_properties()
        self.pressure_conversion_factors = self._initialize_conversion_factors()

    def _initialize_material_properties(self) -> Dict[str, Dict[str, float]]:
        """Initialize material properties for pressure analysis."""
        return {
            "steel": {
                "yield_strength": 250e6,      # Pa
                "ultimate_strength": 400e6,    # Pa
                "elastic_modulus": 200e9,      # Pa
                "poisson_ratio": 0.3,
                "density": 7850.0,             # kg/m³
            },
            "aluminum": {
                "yield_strength": 240e6,
                "ultimate_strength": 290e6,
                "elastic_modulus": 70e9,
                "poisson_ratio": 0.33,
                "density": 2700.0,
            },
            "copper": {
                "yield_strength": 70e6,
                "ultimate_strength": 220e6,
                "elastic_modulus": 110e9,
                "poisson_ratio": 0.34,
                "density": 8960.0,
            },
            "plastic": {
                "yield_strength": 30e6,
                "ultimate_strength": 50e6,
                "elastic_modulus": 3e9,
                "poisson_ratio": 0.4,
                "density": 1200.0,
            },
        }

    def _initialize_conversion_factors(self) -> Dict[str, float]:
        """Initialize pressure unit conversion factors."""
        return {
            "Pa_to_kPa": 1e-3,
            "Pa_to_MPa": 1e-6,
            "Pa_to_bar": 1e-5,
            "Pa_to_psi": 1.450377e-4,
            "Pa_to_atm": 9.869233e-6,
            "Pa_to_mmHg": 7.50062e-3,
            "Pa_to_inHg": 2.952998e-4,
        }

    def convert_pressure_units(self, pressure: float, from_unit: PressureUnit,
                             to_unit: PressureUnit) -> float:
        """
        Convert pressure between different units.

        Args:
            pressure: Pressure value
            from_unit: Source unit
            to_unit: Target unit

        Returns:
            Converted pressure value
        """
        # Convert to Pa first
        if from_unit == PressureUnit.PA:
            pressure_pa = pressure
        elif from_unit == PressureUnit.KPA:
            pressure_pa = pressure * 1000.0
        elif from_unit == PressureUnit.MPA:
            pressure_pa = pressure * 1e6
        elif from_unit == PressureUnit.BAR:
            pressure_pa = pressure * 1e5
        elif from_unit == PressureUnit.PSI:
            pressure_pa = pressure / 1.450377e-4
        elif from_unit == PressureUnit.ATM:
            pressure_pa = pressure / 9.869233e-6
        elif from_unit == PressureUnit.MMHG:
            pressure_pa = pressure / 7.50062e-3
        elif from_unit == PressureUnit.INHG:
            pressure_pa = pressure / 2.952998e-4
        else:
            raise ValueError(f"Unknown pressure unit: {from_unit}")

        # Convert from Pa to target unit
        if to_unit == PressureUnit.PA:
            return pressure_pa
        elif to_unit == PressureUnit.KPA:
            return pressure_pa * 1e-3
        elif to_unit == PressureUnit.MPA:
            return pressure_pa * 1e-6
        elif to_unit == PressureUnit.BAR:
            return pressure_pa * 1e-5
        elif to_unit == PressureUnit.PSI:
            return pressure_pa * 1.450377e-4
        elif to_unit == PressureUnit.ATM:
            return pressure_pa * 9.869233e-6
        elif to_unit == PressureUnit.MMHG:
            return pressure_pa * 7.50062e-3
        elif to_unit == PressureUnit.INHG:
            return pressure_pa * 2.952998e-4
        else:
            raise ValueError(f"Unknown pressure unit: {to_unit}")

    def calculate_hydrostatic_pressure(self, depth: float, fluid_density: float,
                                     gravity: float = 9.81) -> float:
        """
        Calculate hydrostatic pressure at given depth.

        Args:
            depth: Depth below surface in m
            fluid_density: Fluid density in kg/m³
            gravity: Gravitational acceleration in m/s²

        Returns:
            Hydrostatic pressure in Pa
        """
        pressure = fluid_density * gravity * depth
        logger.info(f"Hydrostatic pressure: {pressure:.2f} Pa at depth {depth:.2f} m")
        return pressure

    def calculate_dynamic_pressure(self, velocity: float, fluid_density: float) -> float:
        """
        Calculate dynamic pressure from flow velocity.

        Args:
            velocity: Flow velocity in m/s
            fluid_density: Fluid density in kg/m³

        Returns:
            Dynamic pressure in Pa
        """
        dynamic_pressure = 0.5 * fluid_density * velocity**2
        logger.info(f"Dynamic pressure: {dynamic_pressure:.2f} Pa at velocity {velocity:.2f} m/s")
        return dynamic_pressure

    def calculate_total_pressure(self, static_pressure: float, dynamic_pressure: float) -> float:
        """
        Calculate total pressure from static and dynamic components.

        Args:
            static_pressure: Static pressure in Pa
            dynamic_pressure: Dynamic pressure in Pa

        Returns:
            Total pressure in Pa
        """
        total_pressure = static_pressure + dynamic_pressure
        logger.info(f"Total pressure: {total_pressure:.2f} Pa")
        return total_pressure

    def calculate_pressure_vessel_stress(self, vessel: PressureVessel) -> Dict[str, float]:
        """
        Calculate stresses in pressure vessel using thin-wall theory.

        Args:
            vessel: Pressure vessel properties

        Returns:
            Dictionary of stresses (hoop, longitudinal, radial)
        """
        if vessel.material not in self.material_properties:
            raise ValueError(f"Unknown material: {vessel.material}")

        # Thin-wall theory (t << D)
        radius = vessel.diameter / 2.0
        hoop_stress = vessel.operating_pressure * radius / vessel.wall_thickness
        longitudinal_stress = vessel.operating_pressure * radius / (2.0 * vessel.wall_thickness)
        radial_stress = -vessel.operating_pressure / 2.0  # At inner surface

        stresses = {
            "hoop_stress": hoop_stress,
            "longitudinal_stress": longitudinal_stress,
            "radial_stress": radial_stress,
            "von_mises_stress": math.sqrt(hoop_stress**2 + longitudinal_stress**2 -
                                        hoop_stress * longitudinal_stress)
        }

        logger.info(f"Vessel stresses: hoop={hoop_stress:.2f}, "
                   f"longitudinal={longitudinal_stress:.2f}, "
                   f"radial={radial_stress:.2f} Pa")
        return stresses

    def check_pressure_vessel_safety(self, vessel: PressureVessel) -> Tuple[bool, float]:
        """
        Check pressure vessel safety against material strength.

        Args:
            vessel: Pressure vessel properties

        Returns:
            Tuple of (safe, safety_factor)
        """
        if vessel.material not in self.material_properties:
            raise ValueError(f"Unknown material: {vessel.material}")

        material = self.material_properties[vessel.material]
        stresses = self.calculate_pressure_vessel_stress(vessel)

        # Use von Mises stress for safety check
        von_mises_stress = stresses["von_mises_stress"]
        safety_factor = material["yield_strength"] / von_mises_stress
        safe = von_mises_stress < material["yield_strength"]

        logger.info(f"Vessel safety: safe={safe}, safety_factor={safety_factor:.2f}")
        return safe, safety_factor

    def calculate_pressure_wave_speed(self, fluid_density: float, bulk_modulus: float) -> float:
        """
        Calculate speed of pressure wave in fluid.

        Args:
            fluid_density: Fluid density in kg/m³
            bulk_modulus: Bulk modulus in Pa

        Returns:
            Wave speed in m/s
        """
        wave_speed = math.sqrt(bulk_modulus / fluid_density)
        logger.info(f"Pressure wave speed: {wave_speed:.2f} m/s")
        return wave_speed

    def calculate_pressure_wave_propagation(self, wave: PressureWave,
                                          distance: float, time: float) -> float:
        """
        Calculate pressure at given distance and time for wave propagation.

        Args:
            wave: Pressure wave properties
            distance: Distance from source in m
            time: Time from wave start in s

        Returns:
            Pressure at location in Pa
        """
        # Simplified wave equation
        phase = 2.0 * math.pi * (time - distance / wave.speed) / (1.0 / wave.frequency)
        pressure = wave.amplitude * math.sin(phase) * math.exp(-distance / wave.wavelength)

        logger.info(f"Wave pressure: {pressure:.2f} Pa at distance {distance:.2f} m")
        return pressure

    def calculate_pressure_drop_distributed(self, flow_rate: float, pipe_diameter: float,
                                          pipe_length: float, fluid_density: float,
                                          friction_factor: float) -> float:
        """
        Calculate distributed pressure drop in pipe.

        Args:
            flow_rate: Flow rate in m³/s
            pipe_diameter: Pipe diameter in m
            pipe_length: Pipe length in m
            fluid_density: Fluid density in kg/m³
            friction_factor: Darcy friction factor

        Returns:
            Pressure drop in Pa
        """
        # Calculate velocity
        area = math.pi * pipe_diameter**2 / 4.0
        velocity = flow_rate / area

        # Darcy-Weisbach equation
        pressure_drop = friction_factor * (pipe_length / pipe_diameter) * (fluid_density * velocity**2 / 2.0)

        logger.info(f"Distributed pressure drop: {pressure_drop:.2f} Pa")
        return pressure_drop

    def calculate_pressure_drop_local(self, velocity: float, fluid_density: float,
                                    loss_coefficient: float) -> float:
        """
        Calculate local pressure drop (fittings, valves, etc.).

        Args:
            velocity: Flow velocity in m/s
            fluid_density: Fluid density in kg/m³
            loss_coefficient: Loss coefficient K

        Returns:
            Pressure drop in Pa
        """
        pressure_drop = loss_coefficient * (fluid_density * velocity**2 / 2.0)
        logger.info(f"Local pressure drop: {pressure_drop:.2f} Pa")
        return pressure_drop

    def calculate_pressure_distribution_2d(self, boundary_conditions: List[PressurePoint],
                                         grid_size: Tuple[int, int],
                                         domain_size: Tuple[float, float]) -> np.ndarray:
        """
        Calculate 2D pressure distribution using finite difference method.

        Args:
            boundary_conditions: List of pressure boundary conditions
            grid_size: Grid size (nx, ny)
            domain_size: Domain size (width, height) in m

        Returns:
            2D pressure field as numpy array
        """
        nx, ny = grid_size
        width, height = domain_size

        # Initialize pressure field
        pressure_field = np.zeros((nx, ny))

        # Apply boundary conditions
        for condition in boundary_conditions:
            # Convert to grid coordinates
            i = int(condition.x / width * (nx - 1))
            j = int(condition.y / height * (ny - 1))
            if 0 <= i < nx and 0 <= j < ny:
                pressure_field[i, j] = condition.pressure

        # Solve using finite difference (simplified)
        for _ in range(100):  # Iterations
            pressure_old = pressure_field.copy()
            for i in range(1, nx-1):
                for j in range(1, ny-1):
                    # Laplace equation: ∇²p = 0
                    pressure_field[i, j] = 0.25 * (
                        pressure_old[i+1, j] + pressure_old[i-1, j] +
                        pressure_old[i, j+1] + pressure_old[i, j-1]
                    )

        logger.info(f"2D pressure distribution calculated for {nx}x{ny} grid")
        return pressure_field

    def calculate_pressure_gradient(self, pressure_field: np.ndarray,
                                  grid_spacing: Tuple[float, float]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate pressure gradient from pressure field.

        Args:
            pressure_field: 2D pressure field
            grid_spacing: Grid spacing (dx, dy) in m

        Returns:
            Tuple of (dp/dx, dp/dy) gradients
        """
        dx, dy = grid_spacing

        # Calculate gradients using finite differences
        dp_dx = np.gradient(pressure_field, dx, axis=0)
        dp_dy = np.gradient(pressure_field, dy, axis=1)

        logger.info(f"Pressure gradients calculated")
        return dp_dx, dp_dy

    def calculate_pressure_measurement_uncertainty(self, pressure: float,
                                                measurement_accuracy: float,
                                                calibration_uncertainty: float) -> float:
        """
        Calculate uncertainty in pressure measurement.

        Args:
            pressure: Measured pressure in Pa
            measurement_accuracy: Measurement accuracy as percentage
            calibration_uncertainty: Calibration uncertainty as percentage

        Returns:
            Measurement uncertainty in Pa
        """
        accuracy_uncertainty = pressure * measurement_accuracy / 100.0
        calibration_uncertainty_pa = pressure * calibration_uncertainty / 100.0

        total_uncertainty = math.sqrt(accuracy_uncertainty**2 + calibration_uncertainty_pa**2)

        logger.info(f"Pressure measurement uncertainty: {total_uncertainty:.2f} Pa")
        return total_uncertainty

    def calculate_critical_pressure_ratio(self, specific_heat_ratio: float) -> float:
        """
        Calculate critical pressure ratio for choked flow.

        Args:
            specific_heat_ratio: Specific heat ratio γ

        Returns:
            Critical pressure ratio
        """
        critical_ratio = (2.0 / (specific_heat_ratio + 1.0))**(specific_heat_ratio / (specific_heat_ratio - 1.0))
        logger.info(f"Critical pressure ratio: {critical_ratio:.3f}")
        return critical_ratio

    def calculate_pressure_recovery_factor(self, geometry_type: str,
                                         reynolds_number: float) -> float:
        """
        Calculate pressure recovery factor for different geometries.

        Args:
            geometry_type: Type of geometry (diffuser, nozzle, etc.)
            reynolds_number: Reynolds number

        Returns:
            Pressure recovery factor (0-1)
        """
        if geometry_type == "diffuser":
            # Simplified pressure recovery for diffuser
            if reynolds_number < 2300:
                recovery_factor = 0.8
            else:
                recovery_factor = 0.9
        elif geometry_type == "nozzle":
            recovery_factor = 0.95
        elif geometry_type == "sudden_expansion":
            recovery_factor = 0.6
        elif geometry_type == "sudden_contraction":
            recovery_factor = 0.7
        else:
            recovery_factor = 1.0

        logger.info(f"Pressure recovery factor: {recovery_factor:.3f}")
        return recovery_factor

    def get_material_properties(self, material: str) -> Optional[Dict[str, float]]:
        """Get material properties for pressure analysis."""
        return self.material_properties.get(material)

    def add_material_properties(self, material: str, properties: Dict[str, float]) -> None:
        """Add custom material properties."""
        self.material_properties[material] = properties
        logger.info(f"Added material properties for {material}")

    def validate_pressure_measurement(self, pressure: float, expected_range: Tuple[float, float]) -> bool:
        """
        Validate pressure measurement against expected range.

        Args:
            pressure: Measured pressure in Pa
            expected_range: Expected range (min, max) in Pa

        Returns:
            True if pressure is within expected range
        """
        min_pressure, max_pressure = expected_range
        valid = min_pressure <= pressure <= max_pressure

        logger.info(f"Pressure validation: {valid} ({pressure:.2f} Pa in range "
                   f"[{min_pressure:.2f}, {max_pressure:.2f}] Pa)")
        return valid
