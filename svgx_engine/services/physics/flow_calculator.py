"""
Flow Calculator for Fluid Dynamics Analysis

This module provides comprehensive flow calculation capabilities for fluid dynamics:
- Flow rate calculations
- Pressure drop analysis
- Valve behavior and flow control
- Pump curves and efficiency
- Pipe and duct flow analysis
- Flow regime determination

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


class FlowRegime(Enum):
    """Types of fluid flow regimes."""
    LAMINAR = "laminar"
    TURBULENT = "turbulent"
    TRANSITIONAL = "transitional"


class ValveType(Enum):
    """Types of valves."""
    GATE = "gate"
    GLOBE = "globe"
    BALL = "ball"
    BUTTERFLY = "butterfly"
    CHECK = "check"
    RELIEF = "relief"


class PumpType(Enum):
    """Types of pumps."""
    CENTRIFUGAL = "centrifugal"
    POSITIVE_DISPLACEMENT = "positive_displacement"
    AXIAL = "axial"
    RECIPROCATING = "reciprocating"


@dataclass
class PipeProperties:
    """Pipe properties for flow calculations."""
    diameter: float      # m
    length: float        # m
    roughness: float     # m
    material: str
    wall_thickness: float # m


@dataclass
class ValveProperties:
    """Valve properties for flow calculations."""
    type: ValveType
    diameter: float      # m
    cv_factor: float     # Flow coefficient
    opening: float       # 0-1 (0=closed, 1=fully open)
    pressure_drop: float # Pa


@dataclass
class PumpProperties:
    """Pump properties for flow calculations."""
    type: PumpType
    design_flow_rate: float  # m³/s
    design_head: float       # m
    efficiency: float        # 0-1
    power: float            # W
    speed: float            # rpm


class FlowCalculator:
    """Comprehensive flow calculator for fluid dynamics analysis."""
    
    def __init__(self):
        """Initialize the flow calculator."""
        self.valve_cv_factors = self._initialize_valve_cv_factors()
        self.pipe_roughness = self._initialize_pipe_roughness()
        self.fluid_properties = self._initialize_fluid_properties()
        
    def _initialize_valve_cv_factors(self) -> Dict[str, float]:
        """Initialize standard valve CV factors."""
        return {
            "gate_valve": 0.15,
            "globe_valve": 6.0,
            "ball_valve": 0.05,
            "butterfly_valve": 0.3,
            "check_valve": 2.5,
            "relief_valve": 0.1,
        }
    
    def _initialize_pipe_roughness(self) -> Dict[str, float]:
        """Initialize pipe roughness values."""
        return {
            "steel": 0.000045,      # m
            "cast_iron": 0.00026,
            "concrete": 0.0003,
            "plastic": 0.0000015,
            "copper": 0.0000015,
            "aluminum": 0.0000015,
            "galvanized_steel": 0.00015,
        }
    
    def _initialize_fluid_properties(self) -> Dict[str, Dict[str, float]]:
        """Initialize fluid properties."""
        return {
            "water": {
                "density": 998.0,      # kg/m³
                "viscosity": 0.001,    # Pa·s
                "temperature": 293.15,  # K
            },
            "air": {
                "density": 1.225,
                "viscosity": 1.81e-5,
                "temperature": 293.15,
            },
            "oil": {
                "density": 850.0,
                "viscosity": 0.01,
                "temperature": 293.15,
            },
            "steam": {
                "density": 0.6,
                "viscosity": 1.2e-5,
                "temperature": 373.15,
            },
        }
    
    def calculate_reynolds_number(self, velocity: float, diameter: float, 
                                fluid: str) -> float:
        """
        Calculate Reynolds number for flow regime determination.
        
        Args:
            velocity: Flow velocity in m/s
            diameter: Pipe diameter in m
            fluid: Fluid name
            
        Returns:
            Reynolds number (dimensionless)
        """
        if fluid not in self.fluid_properties:
            raise ValueError(f"Unknown fluid: {fluid}")
        
        rho = self.fluid_properties[fluid]["density"]
        mu = self.fluid_properties[fluid]["viscosity"]
        
        reynolds = rho * velocity * diameter / mu
        
        logger.info(f"Reynolds number: {reynolds:.0f} for {fluid} at {velocity:.2f} m/s")
        return reynolds
    
    def determine_flow_regime(self, reynolds: float) -> FlowRegime:
        """
        Determine flow regime based on Reynolds number.
        
        Args:
            reynolds: Reynolds number
            
        Returns:
            Flow regime
        """
        if reynolds < 2300:
            regime = FlowRegime.LAMINAR
        elif reynolds > 4000:
            regime = FlowRegime.TURBULENT
        else:
            regime = FlowRegime.TRANSITIONAL
        
        logger.info(f"Flow regime: {regime.value} (Re={reynolds:.0f})")
        return regime
    
    def calculate_friction_factor(self, reynolds: float, roughness: float, 
                                diameter: float) -> float:
        """
        Calculate Darcy friction factor using Colebrook-White equation.
        
        Args:
            reynolds: Reynolds number
            roughness: Pipe roughness in m
            diameter: Pipe diameter in m
            
        Returns:
            Darcy friction factor
        """
        relative_roughness = roughness / diameter
        
        if reynolds < 2300:
            # Laminar flow
            friction_factor = 64.0 / reynolds
        else:
            # Turbulent flow - Colebrook-White equation
            # Initial guess using Swamee-Jain approximation
            friction_factor = 0.25 / (math.log10(relative_roughness / 3.7 + 5.74 / reynolds**0.9))**2
            
            # Iterative solution for more accuracy
            for _ in range(10):
                old_f = friction_factor
                friction_factor = 1.0 / (2.0 * math.log10(2.51 / (reynolds * math.sqrt(old_f)) + 
                                        relative_roughness / 3.7))**2
                if abs(friction_factor - old_f) < 1e-6:
                    break
        
        logger.info(f"Friction factor: {friction_factor:.4f}")
        return friction_factor
    
    def calculate_pressure_drop_pipe(self, flow_rate: float, pipe: PipeProperties, 
                                   fluid: str) -> float:
        """
        Calculate pressure drop in pipe using Darcy-Weisbach equation.
        
        Args:
            flow_rate: Flow rate in m³/s
            pipe: Pipe properties
            fluid: Fluid name
            
        Returns:
            Pressure drop in Pa
        """
        if fluid not in self.fluid_properties:
            raise ValueError(f"Unknown fluid: {fluid}")
        
        rho = self.fluid_properties[fluid]["density"]
        mu = self.fluid_properties[fluid]["viscosity"]
        
        # Calculate velocity
        area = math.pi * pipe.diameter**2 / 4.0
        velocity = flow_rate / area
        
        # Calculate Reynolds number
        reynolds = self.calculate_reynolds_number(velocity, pipe.diameter, fluid)
        
        # Calculate friction factor
        friction_factor = self.calculate_friction_factor(reynolds, pipe.roughness, pipe.diameter)
        
        # Darcy-Weisbach equation
        pressure_drop = friction_factor * (pipe.length / pipe.diameter) * (rho * velocity**2 / 2.0)
        
        logger.info(f"Pipe pressure drop: {pressure_drop:.2f} Pa")
        return pressure_drop
    
    def calculate_valve_pressure_drop(self, flow_rate: float, valve: ValveProperties, 
                                    fluid: str) -> float:
        """
        Calculate pressure drop across valve.
        
        Args:
            flow_rate: Flow rate in m³/s
            valve: Valve properties
            fluid: Fluid name
            
        Returns:
            Pressure drop in Pa
        """
        if fluid not in self.fluid_properties:
            raise ValueError(f"Unknown fluid: {fluid}")
        
        rho = self.fluid_properties[fluid]["density"]
        
        # Calculate velocity
        area = math.pi * valve.diameter**2 / 4.0
        velocity = flow_rate / area
        
        # Valve pressure drop coefficient (simplified)
        if valve.type == ValveType.GATE:
            k_factor = 0.15 * (1.0 - valve.opening**2) / valve.opening**2
        elif valve.type == ValveType.GLOBE:
            k_factor = 6.0 * (1.0 - valve.opening**2) / valve.opening**2
        elif valve.type == ValveType.BALL:
            k_factor = 0.05 * (1.0 - valve.opening**2) / valve.opening**2
        elif valve.type == ValveType.BUTTERFLY:
            k_factor = 0.3 * (1.0 - valve.opening**2) / valve.opening**2
        else:
            k_factor = 1.0
        
        pressure_drop = k_factor * (rho * velocity**2 / 2.0)
        
        logger.info(f"Valve pressure drop: {pressure_drop:.2f} Pa")
        return pressure_drop
    
    def calculate_pump_head(self, pump: PumpProperties, flow_rate: float) -> float:
        """
        Calculate pump head at given flow rate using pump curve.
        
        Args:
            pump: Pump properties
            flow_rate: Flow rate in m³/s
            
        Returns:
            Pump head in m
        """
        # Simplified pump curve (parabolic)
        design_flow = pump.design_flow_rate
        design_head = pump.design_head
        
        # Pump curve equation: H = H0 - k*Q²
        k = design_head / (design_flow**2)
        head = design_head - k * flow_rate**2
        
        # Ensure head doesn't go negative
        head = max(head, 0.0)
        
        logger.info(f"Pump head: {head:.2f} m at {flow_rate:.3f} m³/s")
        return head
    
    def calculate_pump_power(self, pump: PumpProperties, flow_rate: float, 
                           head: float, fluid: str) -> float:
        """
        Calculate pump power requirement.
        
        Args:
            pump: Pump properties
            flow_rate: Flow rate in m³/s
            head: Pump head in m
            fluid: Fluid name
            
        Returns:
            Pump power in W
        """
        if fluid not in self.fluid_properties:
            raise ValueError(f"Unknown fluid: {fluid}")
        
        rho = self.fluid_properties[fluid]["density"]
        g = 9.81  # m/s²
        
        # Hydraulic power
        hydraulic_power = rho * g * flow_rate * head
        
        # Actual power considering efficiency
        actual_power = hydraulic_power / pump.efficiency
        
        logger.info(f"Pump power: {actual_power:.2f} W")
        return actual_power
    
    def calculate_flow_rate_from_pressure_drop(self, pressure_drop: float, 
                                             pipe: PipeProperties, fluid: str) -> float:
        """
        Calculate flow rate from pressure drop (iterative solution).
        
        Args:
            pressure_drop: Pressure drop in Pa
            pipe: Pipe properties
            fluid: Fluid name
            
        Returns:
            Flow rate in m³/s
        """
        if fluid not in self.fluid_properties:
            raise ValueError(f"Unknown fluid: {fluid}")
        
        rho = self.fluid_properties[fluid]["density"]
        mu = self.fluid_properties[fluid]["viscosity"]
        
        # Initial guess using laminar flow
        area = math.pi * pipe.diameter**2 / 4.0
        initial_velocity = pressure_drop * pipe.diameter**2 / (32 * mu * pipe.length)
        initial_flow_rate = initial_velocity * area
        
        # Iterative solution
        flow_rate = initial_flow_rate
        for _ in range(20):
            velocity = flow_rate / area
            reynolds = self.calculate_reynolds_number(velocity, pipe.diameter, fluid)
            friction_factor = self.calculate_friction_factor(reynolds, pipe.roughness, pipe.diameter)
            
            # Calculate new flow rate
            new_flow_rate = math.sqrt(2 * pressure_drop * pipe.diameter**5 / 
                                    (friction_factor * rho * pipe.length)) * area / 4.0
            
            if abs(new_flow_rate - flow_rate) < 1e-6:
                break
            flow_rate = new_flow_rate
        
        logger.info(f"Flow rate from pressure drop: {flow_rate:.6f} m³/s")
        return flow_rate
    
    def calculate_orifice_flow_rate(self, pressure_drop: float, orifice_diameter: float, 
                                  pipe_diameter: float, fluid: str, 
                                  discharge_coefficient: float = 0.61) -> float:
        """
        Calculate flow rate through orifice.
        
        Args:
            pressure_drop: Pressure drop in Pa
            orifice_diameter: Orifice diameter in m
            pipe_diameter: Pipe diameter in m
            fluid: Fluid name
            discharge_coefficient: Discharge coefficient (default 0.61)
            
        Returns:
            Flow rate in m³/s
        """
        if fluid not in self.fluid_properties:
            raise ValueError(f"Unknown fluid: {fluid}")
        
        rho = self.fluid_properties[fluid]["density"]
        beta = orifice_diameter / pipe_diameter
        
        # Orifice area
        area = math.pi * orifice_diameter**2 / 4.0
        
        # Flow rate through orifice
        flow_rate = discharge_coefficient * area * math.sqrt(2 * pressure_drop / rho)
        
        logger.info(f"Orifice flow rate: {flow_rate:.6f} m³/s")
        return flow_rate
    
    def calculate_network_flow_distribution(self, network_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate flow distribution in pipe network using Hardy Cross method.
        
        Args:
            network_data: Network topology and properties
            
        Returns:
            Dictionary of flow rates for each pipe
        """
        # Simplified network analysis
        # This is a basic implementation - full Hardy Cross would be more complex
        
        flows = {}
        for pipe_id, pipe_data in network_data["pipes"].items():
            # Simplified flow calculation
            pressure_diff = pipe_data.get("pressure_difference", 1000.0)  # Pa
            resistance = pipe_data.get("resistance", 1.0)
            flows[pipe_id] = math.sqrt(pressure_diff / resistance)
        
        logger.info(f"Network flow distribution calculated for {len(flows)} pipes")
        return flows
    
    def calculate_cavitation_risk(self, pressure: float, vapor_pressure: float, 
                                velocity: float, fluid: str) -> float:
        """
        Calculate cavitation risk factor.
        
        Args:
            pressure: Static pressure in Pa
            vapor_pressure: Vapor pressure in Pa
            velocity: Flow velocity in m/s
            fluid: Fluid name
            
        Returns:
            Cavitation risk factor (0-1, 1=high risk)
        """
        if fluid not in self.fluid_properties:
            raise ValueError(f"Unknown fluid: {fluid}")
        
        rho = self.fluid_properties[fluid]["density"]
        
        # Dynamic pressure
        dynamic_pressure = 0.5 * rho * velocity**2
        
        # Total pressure
        total_pressure = pressure + dynamic_pressure
        
        # Cavitation risk
        if total_pressure <= vapor_pressure:
            risk = 1.0
        else:
            risk = max(0.0, (vapor_pressure - pressure) / dynamic_pressure)
        
        logger.info(f"Cavitation risk: {risk:.3f}")
        return risk
    
    def calculate_heat_transfer_coefficient(self, velocity: float, diameter: float, 
                                          fluid: str, temperature_diff: float) -> float:
        """
        Calculate convective heat transfer coefficient.
        
        Args:
            velocity: Flow velocity in m/s
            diameter: Pipe diameter in m
            fluid: Fluid name
            temperature_diff: Temperature difference in K
            
        Returns:
            Heat transfer coefficient in W/(m²·K)
        """
        if fluid not in self.fluid_properties:
            raise ValueError(f"Unknown fluid: {fluid}")
        
        rho = self.fluid_properties[fluid]["density"]
        mu = self.fluid_properties[fluid]["viscosity"]
        
        # Calculate Reynolds number
        reynolds = self.calculate_reynolds_number(velocity, diameter, fluid)
        
        # Calculate Prandtl number (simplified)
        if fluid == "water":
            prandtl = 7.0
        elif fluid == "air":
            prandtl = 0.7
        else:
            prandtl = 1.0
        
        # Nusselt number correlation (Dittus-Boelter for turbulent flow)
        if reynolds > 4000:
            nusselt = 0.023 * reynolds**0.8 * prandtl**0.4
        else:
            nusselt = 3.66  # Laminar flow
        
        # Thermal conductivity (simplified)
        if fluid == "water":
            thermal_conductivity = 0.6  # W/(m·K)
        elif fluid == "air":
            thermal_conductivity = 0.025
        else:
            thermal_conductivity = 0.1
        
        # Heat transfer coefficient
        htc = nusselt * thermal_conductivity / diameter
        
        logger.info(f"Heat transfer coefficient: {htc:.2f} W/(m²·K)")
        return htc
    
    def get_fluid_properties(self, fluid: str) -> Optional[Dict[str, float]]:
        """Get fluid properties."""
        return self.fluid_properties.get(fluid)
    
    def add_fluid_properties(self, fluid: str, properties: Dict[str, float]) -> None:
        """Add custom fluid properties."""
        self.fluid_properties[fluid] = properties
        logger.info(f"Added fluid properties for {fluid}")
    
    def get_valve_cv_factor(self, valve_type: str) -> Optional[float]:
        """Get valve CV factor."""
        return self.valve_cv_factors.get(valve_type)
    
    def get_pipe_roughness(self, material: str) -> Optional[float]:
        """Get pipe roughness for material."""
        return self.pipe_roughness.get(material) 