"""
Thermal Analysis Integration Service

This module provides integration between the advanced thermal analysis service
and the existing physics services, offering a unified interface for thermal analysis
with both basic and advanced capabilities.

Author: Arxos Development Team
Date: December 2024
"""

import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import numpy as np

from .advanced_thermal_analysis import (
    AdvancedThermalAnalysisService,
    AdvancedBoundaryCondition,
    BoundaryConditionType,
    PhaseChangeMaterial,
    MaterialPhase,
)
from .thermal_analysis import ThermalAnalysisService, ThermalAnalysisRequest
from .fluid_dynamics import FluidDynamicsService
from .structural_analysis import StructuralAnalysisService

logger = logging.getLogger(__name__)


@dataclass
class ThermalAnalysisMode:
    """Thermal analysis modes."""

    BASIC = "basic"
    ADVANCED = "advanced"
    COUPLED = "coupled"  # Multi-physics coupling


@dataclass
class ThermalAnalysisConfig:
    """Configuration for thermal analysis."""

    mode: str = ThermalAnalysisMode.ADVANCED
    enable_temperature_dependent_properties: bool = True
    enable_phase_change: bool = True
    enable_adaptive_mesh: bool = True
    enable_non_linear_solver: bool = True
    enable_optimization: bool = False
    enable_visualization: bool = True
    max_iterations: int = 100
    convergence_tolerance: float = 1e-6
    time_steps: Optional[List[float]] = None


class ThermalIntegrationService:
    """
    Integrated thermal analysis service that combines basic and advanced capabilities.

    Features:
    - Unified interface for thermal analysis
    - Automatic mode selection based on requirements
    - Multi-physics coupling capabilities
    - Performance optimization
    - Comprehensive result analysis
    """

    def __init__(self):
        """Initialize the thermal integration service."""
        self.advanced_service = AdvancedThermalAnalysisService()
        self.basic_service = ThermalAnalysisService()
        self.fluid_service = FluidDynamicsService()
        self.structural_service = StructuralAnalysisService()
        self.config = ThermalAnalysisConfig()
        logger.info("Thermal integration service initialized")

    def analyze_thermal_behavior(
        self,
        request: Union[Dict[str, Any], ThermalAnalysisRequest],
        config: Optional[ThermalAnalysisConfig] = None,
    ) -> Dict[str, Any]:
        """
        Analyze thermal behavior using appropriate analysis mode.

        Args:
            request: Thermal analysis request (dict or ThermalAnalysisRequest)
            config: Analysis configuration

        Returns:
            Analysis results
        """
        if config is None:
            config = self.config

        # Determine analysis mode based on request complexity
        mode = self._determine_analysis_mode(request, config)

        logger.info(f"Performing thermal analysis in {mode} mode")

        if mode == ThermalAnalysisMode.BASIC:
            return self._perform_basic_analysis(request, config)
        elif mode == ThermalAnalysisMode.ADVANCED:
            return self._perform_advanced_analysis(request, config)
        elif mode == ThermalAnalysisMode.COUPLED:
            return self._perform_coupled_analysis(request, config)
        else:
            raise ValueError(f"Unknown analysis mode: {mode}")

    def _determine_analysis_mode(
        self,
        request: Union[Dict[str, Any], ThermalAnalysisRequest],
        config: ThermalAnalysisConfig,
    ) -> str:
        """Determine the appropriate analysis mode based on request complexity."""

        # Check if advanced features are requested
        has_temperature_dependent = config.enable_temperature_dependent_properties
        has_phase_change = config.enable_phase_change
        has_complex_boundary_conditions = self._has_complex_boundary_conditions(request)
        has_multi_physics = self._has_multi_physics_requirements(request)

        # Use advanced mode if any advanced features are requested
        if (
            has_temperature_dependent
            or has_phase_change
            or has_complex_boundary_conditions
            or has_multi_physics
        ):
            return ThermalAnalysisMode.ADVANCED

        # Use coupled mode for multi-physics analysis
        if has_multi_physics:
            return ThermalAnalysisMode.COUPLED

        # Default to basic mode
        return ThermalAnalysisMode.BASIC

    def _has_complex_boundary_conditions(
        self, request: Union[Dict[str, Any], ThermalAnalysisRequest]
    ) -> bool:
        """Check if request has complex boundary conditions."""
        if isinstance(request, dict):
            boundary_conditions = request.get("boundary_conditions", [])
        else:
            boundary_conditions = request.boundary_conditions

        for bc in boundary_conditions:
            if hasattr(bc, "time_function") and bc.time_function is not None:
                return True
            if (
                hasattr(bc, "non_linear_function")
                and bc.non_linear_function is not None
            ):
                return True

        return False

    def _has_multi_physics_requirements(
        self, request: Union[Dict[str, Any], ThermalAnalysisRequest]
    ) -> bool:
        """Check if request requires multi-physics analysis."""
        if isinstance(request, dict):
            analysis_types = request.get("analysis_types", [])
            coupling = request.get("coupling", {})
        else:
            analysis_types = getattr(request, "analysis_types", [])
            coupling = getattr(request, "coupling", {})

        return len(analysis_types) > 1 or bool(coupling)

    def _perform_basic_analysis(
        self,
        request: Union[Dict[str, Any], ThermalAnalysisRequest],
        config: ThermalAnalysisConfig,
    ) -> Dict[str, Any]:
        """Perform basic thermal analysis."""
        try:
            if isinstance(request, dict):
                # Convert dict to ThermalAnalysisRequest
                thermal_request = self._dict_to_thermal_request(request)
            else:
                thermal_request = request

            # Perform basic analysis
            result = self.basic_service.analyze_thermal_behavior(thermal_request)

            # Convert result to standard format
            return self._convert_basic_result(result)

        except Exception as e:
            logger.error(f"Error in basic thermal analysis: {str(e)}")
            raise

    def _perform_advanced_analysis(
        self,
        request: Union[Dict[str, Any], ThermalAnalysisRequest],
        config: ThermalAnalysisConfig,
    ) -> Dict[str, Any]:
        """Perform advanced thermal analysis."""
        try:
            # Convert request to advanced format
            advanced_request = self._convert_to_advanced_request(request, config)

            # Perform advanced analysis
            result = self.advanced_service.solve_advanced_thermal_analysis(
                advanced_request["mesh"],
                advanced_request["materials"],
                advanced_request["boundary_conditions"],
                advanced_request.get("initial_temperature", 293.15),
                config.time_steps,
            )

            # Add analysis metadata
            result["analysis_mode"] = "advanced"
            result["config"] = {
                "temperature_dependent_properties": config.enable_temperature_dependent_properties,
                "phase_change": config.enable_phase_change,
                "adaptive_mesh": config.enable_adaptive_mesh,
                "non_linear_solver": config.enable_non_linear_solver,
            }

            return result

        except Exception as e:
            logger.error(f"Error in advanced thermal analysis: {str(e)}")
            raise

    def _perform_coupled_analysis(
        self,
        request: Union[Dict[str, Any], ThermalAnalysisRequest],
        config: ThermalAnalysisConfig,
    ) -> Dict[str, Any]:
        """Perform coupled multi-physics analysis."""
        try:
            # Perform thermal analysis
            thermal_result = self._perform_advanced_analysis(request, config)

            # Perform fluid analysis if required
            fluid_result = None
            if self._requires_fluid_analysis(request):
                fluid_result = self._perform_fluid_analysis(request)

            # Perform structural analysis if required
            structural_result = None
            if self._requires_structural_analysis(request):
                structural_result = self._perform_structural_analysis(request)

            # Couple results
            coupled_result = self._couple_analysis_results(
                thermal_result, fluid_result, structural_result
            )

            coupled_result["analysis_mode"] = "coupled"
            return coupled_result

        except Exception as e:
            logger.error(f"Error in coupled analysis: {str(e)}")
            raise

    def _convert_to_advanced_request(
        self,
        request: Union[Dict[str, Any], ThermalAnalysisRequest],
        config: ThermalAnalysisConfig,
    ) -> Dict[str, Any]:
        """Convert request to advanced thermal analysis format."""
        if isinstance(request, dict):
            # Extract components from dict
            mesh = request.get("mesh", [])
            materials = request.get("materials", {})
            boundary_conditions = request.get("boundary_conditions", [])
            initial_temperature = request.get("initial_temperature", 293.15)
        else:
            # Extract from ThermalAnalysisRequest
            mesh = request.mesh
            materials = self._extract_materials_from_request(request)
            boundary_conditions = self._convert_boundary_conditions(
                request.boundary_conditions
            )
            initial_temperature = 293.15

        return {
            "mesh": mesh,
            "materials": materials,
            "boundary_conditions": boundary_conditions,
            "initial_temperature": initial_temperature,
        }

    def _extract_materials_from_request(
        self, request: ThermalAnalysisRequest
    ) -> Dict[str, str]:
        """Extract material assignments from thermal analysis request."""
        materials = {}
        if hasattr(request, "materials") and request.materials:
            for element_id, material in request.materials.items():
                materials[str(element_id)] = material.name.lower().replace(" ", "_")
        return materials

    def _convert_boundary_conditions(
        self, boundary_conditions: List
    ) -> List[AdvancedBoundaryCondition]:
        """Convert boundary conditions to advanced format."""
        advanced_bcs = []

        for bc in boundary_conditions:
            if hasattr(bc, "type"):
                bc_type = BoundaryConditionType(bc.type.value)
            else:
                bc_type = BoundaryConditionType.TEMPERATURE

            advanced_bc = AdvancedBoundaryCondition(
                type=bc_type,
                location=bc.location if hasattr(bc, "location") else [0],
                value=bc.value if hasattr(bc, "value") else {"value": 293.15},
            )
            advanced_bcs.append(advanced_bc)

        return advanced_bcs

    def _dict_to_thermal_request(
        self, request_dict: Dict[str, Any]
    ) -> ThermalAnalysisRequest:
        """Convert dictionary to ThermalAnalysisRequest."""
        # This is a simplified conversion - in practice, you'd need more robust conversion
        return ThermalAnalysisRequest(
            analysis_type="thermal",
            mesh=request_dict.get("mesh", []),
            materials=request_dict.get("materials", {}),
            boundary_conditions=request_dict.get("boundary_conditions", []),
            heat_sources=request_dict.get("heat_sources", []),
            solver_settings=request_dict.get("solver_settings", {}),
        )

    def _convert_basic_result(self, result) -> Dict[str, Any]:
        """Convert basic analysis result to standard format."""
        return {
            "analysis_mode": "basic",
            "temperature_field": (
                result.temperature_field if hasattr(result, "temperature_field") else []
            ),
            "heat_flux": result.heat_flux if hasattr(result, "heat_flux") else [],
            "convergence_info": {"converged": True, "iterations": 1, "residual": 0.0},
            "material_phases": {},
            "final_temperature": (
                result.temperature_field if hasattr(result, "temperature_field") else []
            ),
            "final_heat_flux": result.heat_flux if hasattr(result, "heat_flux") else [],
        }

    def _requires_fluid_analysis(
        self, request: Union[Dict[str, Any], ThermalAnalysisRequest]
    ) -> bool:
        """Check if fluid analysis is required."""
        if isinstance(request, dict):
            analysis_types = request.get("analysis_types", [])
        else:
            analysis_types = getattr(request, "analysis_types", [])

        return "fluid" in analysis_types or "convection" in analysis_types

    def _requires_structural_analysis(
        self, request: Union[Dict[str, Any], ThermalAnalysisRequest]
    ) -> bool:
        """Check if structural analysis is required."""
        if isinstance(request, dict):
            analysis_types = request.get("analysis_types", [])
        else:
            analysis_types = getattr(request, "analysis_types", [])

        return "structural" in analysis_types or "stress" in analysis_types

    def _perform_fluid_analysis(
        self, request: Union[Dict[str, Any], ThermalAnalysisRequest]
    ) -> Dict[str, Any]:
        """Perform fluid dynamics analysis."""
        # Simplified fluid analysis
        return {
            "velocity_field": [],
            "pressure_field": [],
            "turbulence_field": [],
            "convergence_info": {"converged": True, "iterations": 1, "residual": 0.0},
        }

    def _perform_structural_analysis(
        self, request: Union[Dict[str, Any], ThermalAnalysisRequest]
    ) -> Dict[str, Any]:
        """Perform structural analysis."""
        # Simplified structural analysis
        return {
            "stress_field": [],
            "strain_field": [],
            "displacement_field": [],
            "convergence_info": {"converged": True, "iterations": 1, "residual": 0.0},
        }

    def _couple_analysis_results(
        self,
        thermal_result: Dict[str, Any],
        fluid_result: Optional[Dict[str, Any]],
        structural_result: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Couple results from different physics analyses."""
        coupled_result = thermal_result.copy()

        if fluid_result:
            coupled_result["fluid_analysis"] = fluid_result
            # Add fluid-thermal coupling effects
            coupled_result["convection_enhancement"] = (
                self._calculate_convection_enhancement(thermal_result, fluid_result)
            )

        if structural_result:
            coupled_result["structural_analysis"] = structural_result
            # Add thermal-structural coupling effects
            coupled_result["thermal_stress"] = self._calculate_thermal_stress(
                thermal_result, structural_result
            )

        return coupled_result

    def _calculate_convection_enhancement(
        self, thermal_result: Dict[str, Any], fluid_result: Dict[str, Any]
    ) -> float:
        """Calculate convection enhancement due to fluid flow."""
        # Simplified calculation
        return 1.2  # 20% enhancement

    def _calculate_thermal_stress(
        self, thermal_result: Dict[str, Any], structural_result: Dict[str, Any]
    ) -> List[float]:
        """Calculate thermal stress."""
        # Simplified thermal stress calculation
        temperature_field = thermal_result.get("final_temperature", [])
        thermal_stress = []

        for temp in temperature_field:
            # Simplified thermal stress = E * α * ΔT
            thermal_stress.append(200e9 * 12e-6 * (temp - 293.15))

        return thermal_stress

    def optimize_thermal_system(
        self,
        request: Union[Dict[str, Any], ThermalAnalysisRequest],
        objective_function: callable,
        optimization_variables: List[str],
        constraints: Optional[List[callable]] = None,
        config: Optional[ThermalAnalysisConfig] = None,
    ) -> Dict[str, Any]:
        """
        Optimize thermal system using advanced algorithms.

        Args:
            request: Thermal analysis request
            objective_function: Function to minimize
            optimization_variables: Variables to optimize
            constraints: Optimization constraints
            config: Analysis configuration

        Returns:
            Optimization results
        """
        if config is None:
            config = self.config

        # Use advanced service for optimization
        advanced_request = self._convert_to_advanced_request(request, config)

        return self.advanced_service.optimize_thermal_design(
            advanced_request["mesh"],
            advanced_request["materials"],
            advanced_request["boundary_conditions"],
            objective_function,
            optimization_variables,
            constraints,
        )

    def get_material_properties(
        self, material_name: str, temperature: float = 293.15
    ) -> Dict[str, float]:
        """
        Get material properties at specified temperature.

        Args:
            material_name: Name of the material
            temperature: Temperature in Kelvin

        Returns:
            Material properties
        """
        if material_name in self.advanced_service.materials:
            material = self.advanced_service.materials[material_name]
            return {
                "thermal_conductivity": material.get_property(
                    "thermal_conductivity", temperature
                ),
                "specific_heat": material.get_property("specific_heat", temperature),
                "density": material.get_property("density", temperature),
                "phase": material.get_phase(temperature).value,
            }
        else:
            # Fall back to basic service
            return self.basic_service.materials.get(material_name, {})

    def visualize_results(
        self,
        results: Dict[str, Any],
        mesh: List[Dict[str, Any]],
        config: Optional[ThermalAnalysisConfig] = None,
    ) -> None:
        """
        Visualize thermal analysis results.

        Args:
            results: Analysis results
            mesh: Finite element mesh
            config: Analysis configuration
        """
        if config is None:
            config = self.config

        if config.enable_visualization and results.get("analysis_mode") == "advanced":
            # Use advanced visualization
            temperature_field = np.array(results.get("final_temperature", []))
            heat_flux = results.get("final_heat_flux", [])
            material_phases = results.get("material_phases", {}).get(
                -1, {}
            )  # Last time step

            self.advanced_service.visualize_thermal_results(
                mesh, temperature_field, heat_flux, material_phases
            )
        else:
            # Use basic visualization
            logger.info("Basic visualization not implemented")

    def generate_report(
        self,
        results: Dict[str, Any],
        request: Union[Dict[str, Any], ThermalAnalysisRequest],
    ) -> Dict[str, Any]:
        """
        Generate comprehensive thermal analysis report.

        Args:
            results: Analysis results
            request: Original analysis request

        Returns:
            Analysis report
        """
        report = {
            "analysis_summary": {
                "mode": results.get("analysis_mode", "unknown"),
                "convergence": results.get("convergence_info", {}).get(
                    "converged", False
                ),
                "iterations": results.get("convergence_info", {}).get("iterations", 0),
                "residual": results.get("convergence_info", {}).get("residual", 0.0),
            },
            "thermal_results": {
                "temperature_range": {
                    "min": min(results.get("final_temperature", [0])),
                    "max": max(results.get("final_temperature", [0])),
                    "average": np.mean(results.get("final_temperature", [0])),
                },
                "heat_flux_summary": {
                    "total_heat_flux": sum(
                        np.linalg.norm(flux)
                        for flux in results.get("final_heat_flux", [])
                    ),
                    "max_heat_flux": max(
                        np.linalg.norm(flux)
                        for flux in results.get("final_heat_flux", [])
                    ),
                },
            },
            "material_analysis": {
                "phases_present": list(
                    set(
                        phase.value
                        for phase in results.get("material_phases", {}).values()
                    )
                ),
                "phase_change_locations": self._identify_phase_change_locations(
                    results
                ),
            },
            "performance_metrics": {
                "analysis_time": results.get("analysis_time", 0.0),
                "memory_usage": results.get("memory_usage", 0.0),
                "mesh_refinements": len(results.get("mesh_refinement_history", [])),
            },
        }

        return report

    def _identify_phase_change_locations(
        self, results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify locations where phase changes occur."""
        phase_changes = []
        material_phases = results.get("material_phases", {})

        if material_phases:
            # Analyze phase changes across time steps
            for time_step, phases in material_phases.items():
                for element_id, phase in phases.items():
                    if (
                        phase != MaterialPhase.SOLID
                    ):  # Non-solid phases indicate phase change
                        phase_changes.append(
                            {
                                "element_id": element_id,
                                "time_step": time_step,
                                "phase": phase.value,
                            }
                        )

        return phase_changes


# Example usage
if __name__ == "__main__":
    # Initialize integration service
    integration_service = ThermalIntegrationService()

    # Create analysis request
    request = {
        "mesh": [
            {"id": "0", "position": [0.0, 0.0, 0.0], "size": 0.1},
            {"id": "1", "position": [0.1, 0.0, 0.0], "size": 0.1},
            {"id": "2", "position": [0.2, 0.0, 0.0], "size": 0.1},
            {"id": "3", "position": [0.3, 0.0, 0.0], "size": 0.1},
            {"id": "4", "position": [0.4, 0.0, 0.0], "size": 0.1},
        ],
        "materials": {
            "0": "aluminum_6061",
            "1": "aluminum_6061",
            "2": "water",
            "3": "aluminum_6061",
            "4": "aluminum_6061",
        },
        "boundary_conditions": [
            {"type": "temperature", "location": [0], "value": {"value": 373.15}},
            {"type": "temperature", "location": [4], "value": {"value": 293.15}},
        ],
    }

    # Configure analysis
    config = ThermalAnalysisConfig(
        mode=ThermalAnalysisMode.ADVANCED,
        enable_temperature_dependent_properties=True,
        enable_phase_change=True,
        enable_adaptive_mesh=True,
        enable_non_linear_solver=True,
    )

    # Perform analysis
    results = integration_service.analyze_thermal_behavior(request, config)

    # Generate report
    report = integration_service.generate_report(results, request)

    print("Thermal analysis completed!")
    print(f"Analysis mode: {report['analysis_summary']['mode']}")
    print(f"Convergence: {report['analysis_summary']['convergence']}")
    print(
        f"Temperature range: {report['thermal_results']['temperature_range']['min']:.2f} - {report['thermal_results']['temperature_range']['max']:.2f} K"
    )
    print(f"Phases present: {report['material_analysis']['phases_present']}")
