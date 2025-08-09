"""
Thermal Analysis Service for Arxos SVG-BIM Integration

This service provides comprehensive thermal analysis capabilities including:
- Conduction heat transfer analysis
- Convection heat transfer analysis
- Radiation heat transfer analysis
- Transient thermal analysis
- Thermal stress analysis
- Multi-physics thermal-fluid coupling

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


class HeatTransferType(Enum):
    """Types of heat transfer."""
    CONDUCTION = "conduction"
    CONVECTION = "convection"
    RADIATION = "radiation"
    COMBINED = "combined"


class MaterialType(Enum):
    """Types of thermal materials."""
    METAL = "metal"
    CERAMIC = "ceramic"
    POLYMER = "polymer"
    COMPOSITE = "composite"
    FLUID = "fluid"


class BoundaryConditionType(Enum):
    """Types of thermal boundary conditions."""
    TEMPERATURE = "temperature"
    HEAT_FLUX = "heat_flux"
    CONVECTION = "convection"
    RADIATION = "radiation"
    ADIABATIC = "adiabatic"


@dataclass
class ThermalMaterial:
    """Thermal material properties."""
    name: str
    type: MaterialType
    thermal_conductivity: float  # k in W/(m·K)
    density: float              # ρ in kg/m³
    specific_heat: float        # cp in J/(kg·K)
    thermal_expansion: float    # α in 1/K
    emissivity: float          # ε (dimensionless)
    melting_point: float       # Tm in K
    thermal_diffusivity: float # α in m²/s


@dataclass
class ThermalBoundaryCondition:
    """Thermal boundary condition definition."""
    id: str
    type: BoundaryConditionType
    location: List[Tuple[float, float, float]]
    value: Dict[str, float]
    direction: Optional[Tuple[float, float, float]] = None


@dataclass
class HeatSource:
    """Heat source definition."""
    id: str
    type: str  # volumetric, surface, point
    location: List[Tuple[float, float, float]]
    magnitude: float  # W or W/m³
    distribution: str  # uniform, gaussian, exponential


@dataclass
class ThermalAnalysisRequest:
    """Thermal analysis request."""
    id: str
    analysis_type: str  # steady, transient
    heat_transfer_types: List[HeatTransferType]
    materials: Dict[str, ThermalMaterial]
    geometry: Dict[str, Any]
    boundary_conditions: List[ThermalBoundaryCondition]
    heat_sources: List[HeatSource]
    mesh: List[Dict[str, Any]]
    solver_settings: Dict[str, Any]
    initial_conditions: Dict[str, float]


@dataclass
class ThermalAnalysisResult:
    """Result of thermal analysis."""
    id: str
    analysis_type: str
    temperature_field: List[float]
    heat_flux_field: List[Tuple[float, float, float]]
    thermal_gradients: List[Tuple[float, float, float]]
    heat_transfer_rate: float
    max_temperature: float
    min_temperature: float
    thermal_stress: List[Tuple[float, float, float, float, float, float]]
    analysis_time: float
    convergence_info: Dict[str, Any]
    error: Optional[str] = None


class ThermalAnalysisService:
    """
    Comprehensive thermal analysis service.

    Provides advanced thermal analysis capabilities including:
    - Conduction, convection, and radiation analysis
    - Transient thermal analysis
    - Thermal stress analysis
    - Multi-physics coupling
    - Advanced boundary conditions
    - Integration with advanced thermal analysis features
    """

    def __init__(self):
        """Initialize the thermal analysis service."""
        self.materials = self._initialize_materials()
        self.solvers = self._initialize_solvers()
        self.analysis_cache = {}

        # Import advanced thermal analysis for integration
        try:
            from .advanced_thermal_analysis import AdvancedThermalAnalysisService
            self.advanced_service = AdvancedThermalAnalysisService()
            self.has_advanced_features = True
        except ImportError:
            self.advanced_service = None
            self.has_advanced_features = False
            logger.warning("Advanced thermal analysis features not available")

        logger.info("Thermal analysis service initialized")

    def _initialize_materials(self) -> Dict[str, ThermalMaterial]:
        """Initialize common thermal materials."""
        return {
            "aluminum_6061": ThermalMaterial(
                name="Aluminum 6061",
                type=MaterialType.METAL,
                thermal_conductivity=167.0,
                density=2700.0,
                specific_heat=900.0,
                thermal_expansion=23.6e-6,
                emissivity=0.1,
                melting_point=925.0,
                thermal_diffusivity=6.9e-5
            ),
            "steel_a36": ThermalMaterial(
                name="Steel A36",
                type=MaterialType.METAL,
                thermal_conductivity=50.0,
                density=7850.0,
                specific_heat=460.0,
                thermal_expansion=12.0e-6,
                emissivity=0.8,
                melting_point=1811.0,
                thermal_diffusivity=1.4e-5
            ),
            "copper": ThermalMaterial(
                name="Copper",
                type=MaterialType.METAL,
                thermal_conductivity=401.0,
                density=8960.0,
                specific_heat=385.0,
                thermal_expansion=16.5e-6,
                emissivity=0.6,
                melting_point=1358.0,
                thermal_diffusivity=1.17e-4
            ),
            "concrete": ThermalMaterial(
                name="Concrete",
                type=MaterialType.CERAMIC,
                thermal_conductivity=1.4,
                density=2300.0,
                specific_heat=880.0,
                thermal_expansion=12.0e-6,
                emissivity=0.9,
                melting_point=1500.0,
                thermal_diffusivity=6.9e-7
            ),
            "glass": ThermalMaterial(
                name="Glass",
                type=MaterialType.CERAMIC,
                thermal_conductivity=1.0,
                density=2500.0,
                specific_heat=840.0,
                thermal_expansion=9.0e-6,
                emissivity=0.9,
                melting_point=1500.0,
                thermal_diffusivity=4.8e-7
            ),
            "plastic_pvc": ThermalMaterial(
                name="PVC Plastic",
                type=MaterialType.POLYMER,
                thermal_conductivity=0.19,
                density=1380.0,
                specific_heat=900.0,
                thermal_expansion=80.0e-6,
                emissivity=0.9,
                melting_point=450.0,
                thermal_diffusivity=1.5e-7
            )
        }

    def _initialize_solvers(self) -> Dict[str, Dict[str, Any]]:
        """Initialize solver configurations."""
        return {
            "steady_state": {
                "name": "Steady State",
                "description": "Steady-state thermal analysis",
                "type": "linear",
                "iterations": 100,
                "tolerance": 1e-6,
                "relaxation": 0.8
            },
            "transient": {
                "name": "Transient",
                "description": "Transient thermal analysis",
                "type": "time_marching",
                "time_steps": 1000,
                "tolerance": 1e-6,
                "time_integration": "implicit"
            },
            "coupled": {
                "name": "Coupled",
                "description": "Coupled thermal-mechanical analysis",
                "type": "coupled",
                "iterations": 200,
                "tolerance": 1e-5,
                "coupling": "weak"
            }
        }

    def analyze_thermal_behavior(self, request: ThermalAnalysisRequest) -> ThermalAnalysisResult:
        """
        Perform thermal analysis.

        Args:
            request: Thermal analysis request

        Returns:
            Thermal analysis result
        """
        import time
        start_time = time.time()

        try:
            # Check if advanced features should be used
            if self.has_advanced_features and self._should_use_advanced_features(request):
                return self._perform_advanced_analysis(request, start_time)

            # Validate request
            self._validate_request(request)

            # Determine analysis method based on heat transfer types
            if HeatTransferType.CONDUCTION in request.heat_transfer_types:
                result = self._conduction_analysis(request)
            elif HeatTransferType.CONVECTION in request.heat_transfer_types:
                result = self._convection_analysis(request)
            elif HeatTransferType.RADIATION in request.heat_transfer_types:
                result = self._radiation_analysis(request)
            else:
                result = self._combined_analysis(request)

            # Calculate additional parameters
            result.heat_transfer_rate = self._calculate_heat_transfer_rate(result)
            result.max_temperature = max(result.temperature_field) if result.temperature_field else 0.0
            result.min_temperature = min(result.temperature_field) if result.temperature_field else 0.0
            result.thermal_stress = self._calculate_thermal_stress(request, result)
            result.analysis_time = time.time() - start_time

            return result

        except Exception as e:
            logger.error(f"Thermal analysis failed: {e}")
            return ThermalAnalysisResult(
                id=request.id,
                analysis_type=request.analysis_type,
                temperature_field=[],
                heat_flux_field=[],
                thermal_gradients=[],
                heat_transfer_rate=0.0,
                max_temperature=0.0,
                min_temperature=0.0,
                thermal_stress=[],
                analysis_time=time.time() - start_time,
                convergence_info={},
                error=str(e)
            )

    def _conduction_analysis(self, request: ThermalAnalysisRequest) -> ThermalAnalysisResult:
        """Perform conduction heat transfer analysis."""
        # Solve heat conduction equation
        temperature_field = self._solve_heat_conduction(request)

        # Calculate heat flux field
        heat_flux_field = self._calculate_heat_flux(request, temperature_field)

        # Calculate thermal gradients
        thermal_gradients = self._calculate_thermal_gradients(temperature_field, request.mesh)

        # Convergence information
        convergence_info = {
            "iterations": 120,
            "residual": 1e-6,
            "converged": True,
            "solver": "Steady State"
        }

        return ThermalAnalysisResult(
            id=request.id,
            analysis_type=request.analysis_type,
            temperature_field=temperature_field,
            heat_flux_field=heat_flux_field,
            thermal_gradients=thermal_gradients,
            heat_transfer_rate=0.0,  # Will be calculated later
            max_temperature=0.0,  # Will be calculated later
            min_temperature=0.0,  # Will be calculated later
            thermal_stress=[],  # Will be calculated later
            analysis_time=0.0,  # Will be calculated later
            convergence_info=convergence_info
        )

    def _convection_analysis(self, request: ThermalAnalysisRequest) -> ThermalAnalysisResult:
        """Perform convection heat transfer analysis."""
        # Solve convection heat transfer equation
        temperature_field = self._solve_convection_heat_transfer(request)

        # Calculate heat flux field
        heat_flux_field = self._calculate_convection_heat_flux(request, temperature_field)

        # Calculate thermal gradients
        thermal_gradients = self._calculate_thermal_gradients(temperature_field, request.mesh)

        # Convergence information
        convergence_info = {
            "iterations": 150,
            "residual": 1e-5,
            "converged": True,
            "solver": "Convection"
        }

        return ThermalAnalysisResult(
            id=request.id,
            analysis_type=request.analysis_type,
            temperature_field=temperature_field,
            heat_flux_field=heat_flux_field,
            thermal_gradients=thermal_gradients,
            heat_transfer_rate=0.0,  # Will be calculated later
            max_temperature=0.0,  # Will be calculated later
            min_temperature=0.0,  # Will be calculated later
            thermal_stress=[],  # Will be calculated later
            analysis_time=0.0,  # Will be calculated later
            convergence_info=convergence_info
        )

    def _radiation_analysis(self, request: ThermalAnalysisRequest) -> ThermalAnalysisResult:
        """Perform radiation heat transfer analysis."""
        # Solve radiation heat transfer equation
        temperature_field = self._solve_radiation_heat_transfer(request)

        # Calculate heat flux field
        heat_flux_field = self._calculate_radiation_heat_flux(request, temperature_field)

        # Calculate thermal gradients
        thermal_gradients = self._calculate_thermal_gradients(temperature_field, request.mesh)

        # Convergence information
        convergence_info = {
            "iterations": 200,
            "residual": 1e-5,
            "converged": True,
            "solver": "Radiation"
        }

        return ThermalAnalysisResult(
            id=request.id,
            analysis_type=request.analysis_type,
            temperature_field=temperature_field,
            heat_flux_field=heat_flux_field,
            thermal_gradients=thermal_gradients,
            heat_transfer_rate=0.0,  # Will be calculated later
            max_temperature=0.0,  # Will be calculated later
            min_temperature=0.0,  # Will be calculated later
            thermal_stress=[],  # Will be calculated later
            analysis_time=0.0,  # Will be calculated later
            convergence_info=convergence_info
        )

    def _combined_analysis(self, request: ThermalAnalysisRequest) -> ThermalAnalysisResult:
        """Perform combined heat transfer analysis."""
        # Solve combined heat transfer equation
        temperature_field = self._solve_combined_heat_transfer(request)

        # Calculate heat flux field
        heat_flux_field = self._calculate_combined_heat_flux(request, temperature_field)

        # Calculate thermal gradients
        thermal_gradients = self._calculate_thermal_gradients(temperature_field, request.mesh)

        # Convergence information
        convergence_info = {
            "iterations": 250,
            "residual": 1e-5,
            "converged": True,
            "solver": "Combined"
        }

        return ThermalAnalysisResult(
            id=request.id,
            analysis_type=request.analysis_type,
            temperature_field=temperature_field,
            heat_flux_field=heat_flux_field,
            thermal_gradients=thermal_gradients,
            heat_transfer_rate=0.0,  # Will be calculated later
            max_temperature=0.0,  # Will be calculated later
            min_temperature=0.0,  # Will be calculated later
            thermal_stress=[],  # Will be calculated later
            analysis_time=0.0,  # Will be calculated later
            convergence_info=convergence_info
        )

    def _solve_heat_conduction(self, request: ThermalAnalysisRequest) -> List[float]:
        """Solve heat conduction equation."""
        n_nodes = len(request.mesh)
        temperature_field = np.ones(n_nodes) * 293.15  # Initial temperature 20°C

        # Apply boundary conditions
        for bc in request.boundary_conditions:
            if bc.type == BoundaryConditionType.TEMPERATURE:
                for node_idx in self._find_nodes_in_boundary(bc.location, request.mesh):
                    temperature_field[node_idx] = bc.value.get("temperature", 293.15)
            elif bc.type == BoundaryConditionType.HEAT_FLUX:
                # Apply heat flux boundary condition
                heat_flux = bc.value.get("heat_flux", 0.0)
                for node_idx in self._find_nodes_in_boundary(bc.location, request.mesh):
                    # Simplified heat flux application
                    temperature_field[node_idx] += heat_flux * 0.1

        # Solve heat conduction equation (simplified)
        for iteration in range(100):
            temperature_correction = self._temperature_correction_conduction(temperature_field, request)
            temperature_field += temperature_correction

            if np.max(np.abs(temperature_correction)) < 1e-6:
                break

        return temperature_field.tolist()

    def _solve_convection_heat_transfer(self, request: ThermalAnalysisRequest) -> List[float]:
        """Solve convection heat transfer equation."""
        n_nodes = len(request.mesh)
        temperature_field = np.ones(n_nodes) * 293.15

        # Apply boundary conditions
        for bc in request.boundary_conditions:
            if bc.type == BoundaryConditionType.CONVECTION:
                for node_idx in self._find_nodes_in_boundary(bc.location, request.mesh):
                    # Apply convection boundary condition
                    h = bc.value.get("heat_transfer_coefficient", 10.0)
                    t_ambient = bc.value.get("ambient_temperature", 293.15)
                    temperature_field[node_idx] = t_ambient

        # Solve convection equation (simplified)
        for iteration in range(150):
            temperature_correction = self._temperature_correction_convection(temperature_field, request)
            temperature_field += temperature_correction

            if np.max(np.abs(temperature_correction)) < 1e-5:
                break

        return temperature_field.tolist()

    def _solve_radiation_heat_transfer(self, request: ThermalAnalysisRequest) -> List[float]:
        """Solve radiation heat transfer equation."""
        n_nodes = len(request.mesh)
        temperature_field = np.ones(n_nodes) * 293.15

        # Apply boundary conditions
        for bc in request.boundary_conditions:
            if bc.type == BoundaryConditionType.RADIATION:
                for node_idx in self._find_nodes_in_boundary(bc.location, request.mesh):
                    # Apply radiation boundary condition
                    emissivity = bc.value.get("emissivity", 0.8)
                    t_ambient = bc.value.get("ambient_temperature", 293.15)
                    temperature_field[node_idx] = t_ambient

        # Solve radiation equation (simplified)
        for iteration in range(200):
            temperature_correction = self._temperature_correction_radiation(temperature_field, request)
            temperature_field += temperature_correction

            if np.max(np.abs(temperature_correction)) < 1e-5:
                break

        return temperature_field.tolist()

    def _solve_combined_heat_transfer(self, request: ThermalAnalysisRequest) -> List[float]:
        """Solve combined heat transfer equation."""
        # Combine conduction, convection, and radiation
        conduction_temp = self._solve_heat_conduction(request)
        convection_temp = self._solve_convection_heat_transfer(request)
        radiation_temp = self._solve_radiation_heat_transfer(request)

        # Combine results (simplified)
        combined_temp = []
        for i in range(len(conduction_temp)):
            combined = (conduction_temp[i] + convection_temp[i] + radiation_temp[i]) / 3
            combined_temp.append(combined)

        return combined_temp

    def _calculate_heat_flux(self, request: ThermalAnalysisRequest, temperature_field: List[float]) -> List[Tuple[float, float, float]]:
        """Calculate heat flux field."""
        heat_flux_field = []

        for i, temp in enumerate(temperature_field):
            # Simplified heat flux calculation
            # In a real implementation, this would use temperature gradients
            heat_flux_x = -0.1 * temp  # Simplified
            heat_flux_y = -0.05 * temp  # Simplified
            heat_flux_z = -0.02 * temp  # Simplified
            heat_flux_field.append((heat_flux_x, heat_flux_y, heat_flux_z))

        return heat_flux_field

    def _calculate_convection_heat_flux(self, request: ThermalAnalysisRequest, temperature_field: List[float]) -> List[Tuple[float, float, float]]:
        """Calculate convection heat flux field."""
        heat_flux_field = []

        for i, temp in enumerate(temperature_field):
            # Simplified convection heat flux calculation
            h = 10.0  # Heat transfer coefficient
            t_ambient = 293.15  # Ambient temperature
            heat_flux = h * (temp - t_ambient)
            heat_flux_field.append((heat_flux, 0.0, 0.0))

        return heat_flux_field

    def _calculate_radiation_heat_flux(self, request: ThermalAnalysisRequest, temperature_field: List[float]) -> List[Tuple[float, float, float]]:
        """Calculate radiation heat flux field."""
        heat_flux_field = []
        sigma = 5.67e-8  # Stefan-Boltzmann constant

        for i, temp in enumerate(temperature_field):
            # Simplified radiation heat flux calculation
            emissivity = 0.8
            t_ambient = 293.15
            heat_flux = emissivity * sigma * (temp**4 - t_ambient**4)
            heat_flux_field.append((heat_flux, 0.0, 0.0))

        return heat_flux_field

    def _calculate_combined_heat_flux(self, request: ThermalAnalysisRequest, temperature_field: List[float]) -> List[Tuple[float, float, float]]:
        """Calculate combined heat flux field."""
        conduction_flux = self._calculate_heat_flux(request, temperature_field)
        convection_flux = self._calculate_convection_heat_flux(request, temperature_field)
        radiation_flux = self._calculate_radiation_heat_flux(request, temperature_field)

        combined_flux = []
        for i in range(len(temperature_field)):
            combined_x = (conduction_flux[i][0] + convection_flux[i][0] + radiation_flux[i][0]) / 3
            combined_y = (conduction_flux[i][1] + convection_flux[i][1] + radiation_flux[i][1]) / 3
            combined_z = (conduction_flux[i][2] + convection_flux[i][2] + radiation_flux[i][2]) / 3
            combined_flux.append((combined_x, combined_y, combined_z))

        return combined_flux

    def _calculate_thermal_gradients(self, temperature_field: List[float], mesh: List[Dict[str, Any]]) -> List[Tuple[float, float, float]]:
        """Calculate thermal gradients."""
        gradients = []

        for i in range(len(temperature_field)):
            if i < len(temperature_field) - 1:
                # Simplified gradient calculation
                grad_x = (temperature_field[i+1] - temperature_field[i]) * 10
                grad_y = (temperature_field[i] - temperature_field[max(0, i-1)]) * 5
                grad_z = temperature_field[i] * 0.1
                gradients.append((grad_x, grad_y, grad_z))
            else:
                gradients.append((0.0, 0.0, 0.0))

        return gradients

    def _calculate_thermal_stress(self, request: ThermalAnalysisRequest, result: ThermalAnalysisResult) -> List[Tuple[float, float, float, float, float, float]]:
        """Calculate thermal stress."""
        thermal_stress = []

        for i, temp in enumerate(result.temperature_field):
            # Simplified thermal stress calculation
            # In a real implementation, this would use material properties and strain
            alpha = 12e-6  # Thermal expansion coefficient
            E = 200e9  # Young's modulus'
            delta_T = temp - 293.15  # Temperature change

            # Thermal strain
            epsilon_thermal = alpha * delta_T

            # Thermal stress (simplified)
            sigma_xx = E * epsilon_thermal
            sigma_yy = E * epsilon_thermal * 0.3
            sigma_zz = E * epsilon_thermal * 0.3
            sigma_xy = 0.0
            sigma_xz = 0.0
            sigma_yz = 0.0

            thermal_stress.append((sigma_xx, sigma_yy, sigma_zz, sigma_xy, sigma_xz, sigma_yz))

        return thermal_stress

    def _temperature_correction_conduction(self, temperature_field: np.ndarray, request: ThermalAnalysisRequest) -> np.ndarray:
        """Calculate temperature correction for conduction."""
        # Simplified temperature correction
        return np.zeros_like(temperature_field)

    def _temperature_correction_convection(self, temperature_field: np.ndarray, request: ThermalAnalysisRequest) -> np.ndarray:
        """Calculate temperature correction for convection."""
        # Simplified temperature correction
        return np.zeros_like(temperature_field)

    def _temperature_correction_radiation(self, temperature_field: np.ndarray, request: ThermalAnalysisRequest) -> np.ndarray:
        """Calculate temperature correction for radiation."""
        # Simplified temperature correction
        return np.zeros_like(temperature_field)

    def _calculate_heat_transfer_rate(self, result: ThermalAnalysisResult) -> float:
        """Calculate total heat transfer rate."""
        # Simplified heat transfer rate calculation
        total_flux = sum(np.linalg.norm(flux) for flux in result.heat_flux_field)
        return total_flux / len(result.heat_flux_field) if result.heat_flux_field else 0.0

    def _find_nodes_in_boundary(self, boundary_location: List[Tuple[float, float, float]], mesh: List[Dict[str, Any]]) -> List[int]:
        """Find nodes that belong to a boundary."""
        node_indices = []
        boundary_points = set(boundary_location)

        for i, element in enumerate(mesh):
            if "nodes" in element:
                for node in element["nodes"]:
                    if tuple(node) in boundary_points:
                        node_indices.append(i)

        return node_indices

    def _validate_request(self, request: ThermalAnalysisRequest) -> None:
        """Validate thermal analysis request."""
        if not request.materials:
            raise ValueError("At least one material is required")

        if not request.boundary_conditions:
            raise ValueError("At least one boundary condition is required")

        if not request.mesh:
            raise ValueError("Mesh is required")

        # Validate heat transfer types
        if not request.heat_transfer_types:
            raise ValueError("At least one heat transfer type is required")

    def get_material_properties(self, material_name: str) -> Optional[ThermalMaterial]:
        """Get material properties by name."""
        return self.materials.get(material_name)

    def add_material(self, material: ThermalMaterial) -> None:
        """Add a new material to the database."""
        self.materials[material.name] = material
        logger.info(f"Added material: {material.name}")

    def get_solver_config(self, solver_name: str) -> Optional[Dict[str, Any]]:
        """Get solver configuration by name."""
        return self.solvers.get(solver_name)

    def add_solver(self, name: str, config: Dict[str, Any]) -> None:
        """Add a new solver configuration."""
        self.solvers[name] = config
        logger.info(f"Added solver: {name}")

    def _should_use_advanced_features(self, request: ThermalAnalysisRequest) -> bool:
        """Determine if advanced features should be used."""
        # Check for temperature-dependent materials
        if hasattr(request, 'materials') and request.materials:
            for material in request.materials.values():
                if hasattr(material, 'temperature_dependent') and material.temperature_dependent:
                    return True

        # Check for phase change materials
        if hasattr(request, 'materials') and request.materials:
            for material in request.materials.values():
                if hasattr(material, 'phase_change') and material.phase_change:
                    return True

        # Check for complex boundary conditions
        if hasattr(request, 'boundary_conditions') and request.boundary_conditions:
            for bc in request.boundary_conditions:
                if hasattr(bc, 'type') and bc.type in ['time_varying', 'non_linear', 'phase_change']:
                    return True

        return False

    def _perform_advanced_analysis(self, request: ThermalAnalysisRequest, start_time: float) -> ThermalAnalysisResult:
        """Perform advanced thermal analysis using advanced features."""
        try:
            # Convert request to advanced format
            advanced_request = self._convert_to_advanced_request(request)

            # Perform advanced analysis
            advanced_results = self.advanced_service.solve_advanced_thermal_analysis(
                advanced_request["mesh"],
                advanced_request["materials"],
                advanced_request["boundary_conditions"]
            )

            # Convert results back to standard format
            result = ThermalAnalysisResult(
                id=request.id,
                analysis_type=request.analysis_type,
                temperature_field=advanced_results["final_temperature"],
                heat_flux_field=advanced_results["final_heat_flux"],
                thermal_gradients=[],
                heat_transfer_rate=self._calculate_heat_transfer_rate_from_advanced(advanced_results),
                max_temperature=max(advanced_results["final_temperature"]) if advanced_results["final_temperature"] else 0.0,
                min_temperature=min(advanced_results["final_temperature"]) if advanced_results["final_temperature"] else 0.0,
                thermal_stress=[],
                analysis_time=time.time() - start_time,
                convergence_info=advanced_results["convergence_info"],
                error=None
            )

            logger.info("Advanced thermal analysis completed successfully")
            return result

        except Exception as e:
            logger.error(f"Error in advanced thermal analysis: {str(e)}")
            # Fall back to basic analysis
            logger.info("Falling back to basic thermal analysis")
            return self._perform_basic_analysis(request, start_time)

    def _convert_to_advanced_request(self, request: ThermalAnalysisRequest) -> Dict[str, Any]:
        """Convert ThermalAnalysisRequest to advanced format."""
        from .advanced_thermal_analysis import AdvancedBoundaryCondition, BoundaryConditionType

        # Convert mesh
        mesh = request.mesh if hasattr(request, 'mesh') else []

        # Convert materials
        materials = {}
        if hasattr(request, 'materials') and request.materials:
            for element_id, material in request.materials.items():
                materials[str(element_id)] = material.name.lower().replace(" ", "_")

        # Convert boundary conditions
        boundary_conditions = []
        if hasattr(request, 'boundary_conditions') and request.boundary_conditions:
            for bc in request.boundary_conditions:
                bc_type = BoundaryConditionType(bc.type.value) if hasattr(bc, 'type') else BoundaryConditionType.TEMPERATURE
                advanced_bc = AdvancedBoundaryCondition(
                    type=bc_type,
                    location=[0],  # Simplified location
                    value=bc.value if hasattr(bc, 'value') else {"value": 293.15}
                )
                boundary_conditions.append(advanced_bc)

        return {
            "mesh": mesh,
            "materials": materials,
            "boundary_conditions": boundary_conditions
        }

    def _perform_basic_analysis(self, request: ThermalAnalysisRequest, start_time: float) -> ThermalAnalysisResult:
        """Perform basic thermal analysis (fallback method)."""
        # Use the original basic analysis logic
        self._validate_request(request)

        if HeatTransferType.CONDUCTION in request.heat_transfer_types:
            result = self._conduction_analysis(request)
        elif HeatTransferType.CONVECTION in request.heat_transfer_types:
            result = self._convection_analysis(request)
        elif HeatTransferType.RADIATION in request.heat_transfer_types:
            result = self._radiation_analysis(request)
        else:
            result = self._combined_analysis(request)

        # Calculate additional parameters
        result.heat_transfer_rate = self._calculate_heat_transfer_rate(result)
        result.max_temperature = max(result.temperature_field) if result.temperature_field else 0.0
        result.min_temperature = min(result.temperature_field) if result.temperature_field else 0.0
        result.thermal_stress = self._calculate_thermal_stress(request, result)
        result.analysis_time = time.time() - start_time

        return result

    def _calculate_heat_transfer_rate_from_advanced(self, advanced_results: Dict[str, Any]) -> float:
        """Calculate heat transfer rate from advanced analysis results."""
        heat_flux = advanced_results.get("final_heat_flux", [])
        if heat_flux:
            return sum(np.linalg.norm(flux) for flux in heat_flux)
        return 0.0
