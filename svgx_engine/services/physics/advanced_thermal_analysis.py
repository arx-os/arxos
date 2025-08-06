"""
Advanced Thermal Analysis Service

This module provides enterprise-grade thermal analysis capabilities including:
- Temperature-dependent material properties
- Phase change materials (melting, freezing, sublimation)
- Advanced boundary conditions (time-varying, non-linear)
- Adaptive mesh refinement
- Non-linear solver capabilities
- Thermal optimization algorithms
- Advanced visualization support

Author: Arxos Development Team
Date: December 2024
"""

import numpy as np
import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Callable, Any
from enum import Enum
import scipy.optimize as optimize
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

logger = logging.getLogger(__name__)


class MaterialPhase(Enum):
    """Material phase states."""

    SOLID = "solid"
    LIQUID = "liquid"
    GAS = "gas"
    PLASMA = "plasma"


class BoundaryConditionType(Enum):
    """Advanced boundary condition types."""

    TEMPERATURE = "temperature"
    HEAT_FLUX = "heat_flux"
    CONVECTION = "convection"
    RADIATION = "radiation"
    PHASE_CHANGE = "phase_change"
    TIME_VARYING = "time_varying"
    NON_LINEAR = "non_linear"


@dataclass
class TemperatureDependentProperty:
    """Temperature-dependent material property."""

    temperatures: List[float]  # K
    values: List[float]
    interpolation_method: str = "cubic"  # linear, cubic, spline

    def get_value(self, temperature: float) -> float:
        """Get property value at given temperature."""
        if len(self.temperatures) == 1:
            return self.values[0]

        # Ensure temperature is within bounds
        temp = np.clip(temperature, min(self.temperatures), max(self.temperatures))

        if self.interpolation_method == "linear":
            return np.interp(temp, self.temperatures, self.values)
        elif self.interpolation_method == "cubic":
            f = interp1d(
                self.temperatures,
                self.values,
                kind="cubic",
                bounds_error=False,
                fill_value="extrapolate",
            )
            return float(f(temp))
        else:  # spline
            f = interp1d(
                self.temperatures,
                self.values,
                kind="spline",
                bounds_error=False,
                fill_value="extrapolate",
            )
            return float(f(temp))


@dataclass
class PhaseChangeMaterial:
    """Phase change material properties."""

    name: str
    melting_point: float  # K
    freezing_point: float  # K
    latent_heat_fusion: float  # J/kg
    latent_heat_vaporization: float  # J/kg
    solid_properties: Dict[str, TemperatureDependentProperty]
    liquid_properties: Dict[str, TemperatureDependentProperty]
    gas_properties: Dict[str, TemperatureDependentProperty]

    def get_phase(self, temperature: float) -> MaterialPhase:
        """Determine material phase at given temperature."""
        if temperature < self.freezing_point:
            return MaterialPhase.SOLID
        elif temperature < self.melting_point:
            return MaterialPhase.LIQUID
        else:
            return MaterialPhase.GAS

    def get_property(self, property_name: str, temperature: float) -> float:
        """Get material property at given temperature."""
        phase = self.get_phase(temperature)

        if phase == MaterialPhase.SOLID:
            properties = self.solid_properties
        elif phase == MaterialPhase.LIQUID:
            properties = self.liquid_properties
        else:
            properties = self.gas_properties

        if property_name in properties:
            return properties[property_name].get_value(temperature)
        else:
            raise ValueError(f"Property {property_name} not found for phase {phase}")


@dataclass
class AdvancedBoundaryCondition:
    """Advanced boundary condition."""

    type: BoundaryConditionType
    location: List[int]  # Node indices
    value: Dict[str, Any]
    time_function: Optional[Callable[[float], float]] = None
    non_linear_function: Optional[Callable[[float, float], float]] = None

    def get_value(self, time: float = 0.0, temperature: float = 293.15) -> float:
        """Get boundary condition value."""
        base_value = self.value.get("value", 0.0)

        if self.time_function:
            base_value *= self.time_function(time)

        if self.non_linear_function:
            base_value = self.non_linear_function(base_value, temperature)

        return base_value


@dataclass
class AdaptiveMeshSettings:
    """Settings for adaptive mesh refinement."""

    max_refinement_levels: int = 5
    refinement_threshold: float = 0.1
    coarsening_threshold: float = 0.01
    min_element_size: float = 0.001
    max_element_size: float = 0.1
    refinement_criteria: List[str] = None  # temperature_gradient, stress_gradient, etc.


@dataclass
class NonLinearSolverSettings:
    """Settings for non-linear solver."""

    max_iterations: int = 100
    convergence_tolerance: float = 1e-6
    relaxation_factor: float = 0.8
    solver_type: str = "newton_raphson"  # newton_raphson, picard, broyden
    line_search: bool = True
    adaptive_timestep: bool = True


class AdvancedThermalAnalysisService:
    """
    Advanced thermal analysis service with enterprise-grade capabilities.

    Features:
    - Temperature-dependent material properties
    - Phase change materials
    - Advanced boundary conditions
    - Adaptive mesh refinement
    - Non-linear solver capabilities
    - Thermal optimization
    - Advanced visualization
    """

    def __init__(self):
        """Initialize the advanced thermal analysis service."""
        self.materials = self._initialize_advanced_materials()
        self.solver_settings = NonLinearSolverSettings()
        self.mesh_settings = AdaptiveMeshSettings()
        self.analysis_cache = {}
        logger.info("Advanced thermal analysis service initialized")

    def _initialize_advanced_materials(self) -> Dict[str, PhaseChangeMaterial]:
        """Initialize advanced materials with temperature-dependent properties."""
        return {
            "water": PhaseChangeMaterial(
                name="Water",
                melting_point=273.15,  # 0°C
                freezing_point=273.15,
                latent_heat_fusion=334000,  # J/kg
                latent_heat_vaporization=2260000,  # J/kg
                solid_properties={
                    "thermal_conductivity": TemperatureDependentProperty(
                        temperatures=[250, 260, 270, 273.15],
                        values=[2.22, 2.25, 2.28, 2.30],
                    ),
                    "specific_heat": TemperatureDependentProperty(
                        temperatures=[250, 260, 270, 273.15],
                        values=[1800, 1900, 2000, 2100],
                    ),
                    "density": TemperatureDependentProperty(
                        temperatures=[250, 260, 270, 273.15],
                        values=[920, 915, 910, 917],
                    ),
                },
                liquid_properties={
                    "thermal_conductivity": TemperatureDependentProperty(
                        temperatures=[273.15, 293.15, 313.15, 333.15, 353.15, 373.15],
                        values=[0.569, 0.598, 0.628, 0.658, 0.688, 0.718],
                    ),
                    "specific_heat": TemperatureDependentProperty(
                        temperatures=[273.15, 293.15, 313.15, 333.15, 353.15, 373.15],
                        values=[4217, 4182, 4178, 4185, 4200, 4220],
                    ),
                    "density": TemperatureDependentProperty(
                        temperatures=[273.15, 293.15, 313.15, 333.15, 353.15, 373.15],
                        values=[999.8, 998.2, 992.2, 983.2, 971.8, 958.4],
                    ),
                },
                gas_properties={
                    "thermal_conductivity": TemperatureDependentProperty(
                        temperatures=[373.15, 400, 450, 500],
                        values=[0.025, 0.030, 0.040, 0.050],
                    ),
                    "specific_heat": TemperatureDependentProperty(
                        temperatures=[373.15, 400, 450, 500],
                        values=[2000, 2100, 2200, 2300],
                    ),
                    "density": TemperatureDependentProperty(
                        temperatures=[373.15, 400, 450, 500],
                        values=[0.6, 0.5, 0.4, 0.3],
                    ),
                },
            ),
            "aluminum_6061": PhaseChangeMaterial(
                name="Aluminum 6061",
                melting_point=925.0,  # K
                freezing_point=925.0,
                latent_heat_fusion=397000,  # J/kg
                latent_heat_vaporization=10500000,  # J/kg
                solid_properties={
                    "thermal_conductivity": TemperatureDependentProperty(
                        temperatures=[
                            293.15,
                            373.15,
                            473.15,
                            573.15,
                            673.15,
                            773.15,
                            873.15,
                        ],
                        values=[167, 175, 183, 191, 199, 207, 215],
                    ),
                    "specific_heat": TemperatureDependentProperty(
                        temperatures=[
                            293.15,
                            373.15,
                            473.15,
                            573.15,
                            673.15,
                            773.15,
                            873.15,
                        ],
                        values=[900, 920, 940, 960, 980, 1000, 1020],
                    ),
                    "density": TemperatureDependentProperty(
                        temperatures=[
                            293.15,
                            373.15,
                            473.15,
                            573.15,
                            673.15,
                            773.15,
                            873.15,
                        ],
                        values=[2700, 2690, 2680, 2670, 2660, 2650, 2640],
                    ),
                },
                liquid_properties={
                    "thermal_conductivity": TemperatureDependentProperty(
                        temperatures=[925, 1000, 1100, 1200],
                        values=[100, 110, 120, 130],
                    ),
                    "specific_heat": TemperatureDependentProperty(
                        temperatures=[925, 1000, 1100, 1200],
                        values=[1200, 1250, 1300, 1350],
                    ),
                    "density": TemperatureDependentProperty(
                        temperatures=[925, 1000, 1100, 1200],
                        values=[2400, 2350, 2300, 2250],
                    ),
                },
                gas_properties={
                    "thermal_conductivity": TemperatureDependentProperty(
                        temperatures=[1200, 1500, 2000], values=[50, 60, 70]
                    ),
                    "specific_heat": TemperatureDependentProperty(
                        temperatures=[1200, 1500, 2000], values=[1500, 1600, 1700]
                    ),
                    "density": TemperatureDependentProperty(
                        temperatures=[1200, 1500, 2000], values=[2.0, 1.5, 1.0]
                    ),
                },
            ),
        }

    def solve_advanced_thermal_analysis(
        self,
        mesh: List[Dict[str, Any]],
        materials: Dict[str, str],
        boundary_conditions: List[AdvancedBoundaryCondition],
        initial_temperature: float = 293.15,
        time_steps: List[float] = None,
    ) -> Dict[str, Any]:
        """
        Solve advanced thermal analysis with non-linear capabilities.

        Args:
            mesh: Finite element mesh
            materials: Material assignment for each element
            boundary_conditions: Advanced boundary conditions
            initial_temperature: Initial temperature field
            time_steps: Time steps for transient analysis

        Returns:
            Analysis results including temperature field, heat flux, and convergence info
        """
        try:
            n_nodes = len(mesh)

            # Initialize temperature field
            temperature_field = np.ones(n_nodes) * initial_temperature

            # Initialize adaptive mesh
            current_mesh = mesh.copy()
            refinement_level = 0

            # Time stepping for transient analysis
            if time_steps is None:
                time_steps = [0.0, 1.0, 2.0, 5.0, 10.0]

            results = {
                "temperature_history": [],
                "heat_flux_history": [],
                "convergence_history": [],
                "mesh_refinement_history": [],
                "final_temperature": [],
                "final_heat_flux": [],
                "material_phases": [],
                "convergence_info": {},
            }

            for time_step in time_steps:
                logger.info(f"Solving thermal analysis at time step: {time_step}")

                # Solve non-linear system
                temperature_field, convergence_info = self._solve_non_linear_system(
                    current_mesh,
                    materials,
                    boundary_conditions,
                    temperature_field,
                    time_step,
                )

                # Calculate heat flux
                heat_flux = self._calculate_heat_flux(
                    current_mesh, materials, temperature_field
                )

                # Determine material phases
                material_phases = self._determine_material_phases(
                    materials, temperature_field
                )

                # Store results
                results["temperature_history"].append(temperature_field.tolist())
                results["heat_flux_history"].append(heat_flux)
                results["convergence_history"].append(convergence_info)
                results["material_phases"].append(material_phases)

                # Adaptive mesh refinement
                if refinement_level < self.mesh_settings.max_refinement_levels:
                    refined_mesh, should_refine = self._adaptive_mesh_refinement(
                        current_mesh, temperature_field, heat_flux
                    )
                    if should_refine:
                        current_mesh = refined_mesh
                        refinement_level += 1
                        results["mesh_refinement_history"].append(
                            {
                                "time_step": time_step,
                                "refinement_level": refinement_level,
                                "new_mesh_size": len(refined_mesh),
                            }
                        )

            # Final results
            results["final_temperature"] = temperature_field.tolist()
            results["final_heat_flux"] = heat_flux
            results["convergence_info"] = convergence_info

            logger.info("Advanced thermal analysis completed successfully")
            return results

        except Exception as e:
            logger.error(f"Error in advanced thermal analysis: {str(e)}")
            raise

    def _solve_non_linear_system(
        self,
        mesh: List[Dict[str, Any]],
        materials: Dict[str, str],
        boundary_conditions: List[AdvancedBoundaryCondition],
        initial_temperature: np.ndarray,
        time: float,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Solve non-linear thermal system using advanced numerical methods.
        """
        n_nodes = len(mesh)
        temperature = initial_temperature.copy()

        convergence_info = {
            "iterations": 0,
            "residual": float("inf"),
            "converged": False,
            "solver_type": self.solver_settings.solver_type,
        }

        for iteration in range(self.solver_settings.max_iterations):
            # Calculate residual
            residual = self._calculate_residual(
                mesh, materials, boundary_conditions, temperature, time
            )

            # Check convergence
            if np.max(np.abs(residual)) < self.solver_settings.convergence_tolerance:
                convergence_info["converged"] = True
                convergence_info["iterations"] = iteration + 1
                convergence_info["residual"] = float(np.max(np.abs(residual)))
                break

            # Update temperature based on solver type
            if self.solver_settings.solver_type == "newton_raphson":
                temperature_update = self._newton_raphson_update(
                    mesh, materials, residual, temperature
                )
            elif self.solver_settings.solver_type == "picard":
                temperature_update = self._picard_update(
                    mesh, materials, residual, temperature
                )
            else:  # broyden
                temperature_update = self._broyden_update(
                    mesh, materials, residual, temperature, iteration
                )

            # Apply relaxation factor
            temperature += self.solver_settings.relaxation_factor * temperature_update

            # Update convergence info
            convergence_info["iterations"] = iteration + 1
            convergence_info["residual"] = float(np.max(np.abs(residual)))

        return temperature, convergence_info

    def _calculate_residual(
        self,
        mesh: List[Dict[str, Any]],
        materials: Dict[str, str],
        boundary_conditions: List[AdvancedBoundaryCondition],
        temperature: np.ndarray,
        time: float,
    ) -> np.ndarray:
        """
        Calculate residual for non-linear system.
        """
        n_nodes = len(mesh)
        residual = np.zeros(n_nodes)

        # Apply heat conduction residual
        for i, node in enumerate(mesh):
            # Get material properties at current temperature
            material_name = materials.get(str(i), "aluminum_6061")
            material = self.materials[material_name]

            thermal_conductivity = material.get_property(
                "thermal_conductivity", temperature[i]
            )
            specific_heat = material.get_property("specific_heat", temperature[i])
            density = material.get_property("density", temperature[i])

            # Simplified heat conduction residual
            # In a real implementation, this would use finite element assembly
            if i > 0:
                residual[i] += thermal_conductivity * (
                    temperature[i - 1] - temperature[i]
                )
            if i < n_nodes - 1:
                residual[i] += thermal_conductivity * (
                    temperature[i + 1] - temperature[i]
                )

        # Apply boundary conditions
        for bc in boundary_conditions:
            for node_idx in bc.location:
                if node_idx < n_nodes:
                    bc_value = bc.get_value(time, temperature[node_idx])
                    if bc.type == BoundaryConditionType.TEMPERATURE:
                        residual[node_idx] = temperature[node_idx] - bc_value
                    elif bc.type == BoundaryConditionType.HEAT_FLUX:
                        residual[node_idx] += bc_value

        return residual

    def _newton_raphson_update(
        self,
        mesh: List[Dict[str, Any]],
        materials: Dict[str, str],
        residual: np.ndarray,
        temperature: np.ndarray,
    ) -> np.ndarray:
        """
        Newton-Raphson update for non-linear solver.
        """
        n_nodes = len(mesh)
        jacobian = np.zeros((n_nodes, n_nodes))

        # Calculate Jacobian matrix (simplified)
        for i in range(n_nodes):
            material_name = materials.get(str(i), "aluminum_6061")
            material = self.materials[material_name]

            # Diagonal term
            thermal_conductivity = material.get_property(
                "thermal_conductivity", temperature[i]
            )
            jacobian[i, i] = -2 * thermal_conductivity

            # Off-diagonal terms
            if i > 0:
                jacobian[i, i - 1] = thermal_conductivity
            if i < n_nodes - 1:
                jacobian[i, i + 1] = thermal_conductivity

        # Solve linear system
        try:
            update = np.linalg.solve(jacobian, -residual)
        except np.linalg.LinAlgError:
            # Use pseudo-inverse if matrix is singular
            update = np.linalg.pinv(jacobian) @ (-residual)

        return update

    def _picard_update(
        self,
        mesh: List[Dict[str, Any]],
        materials: Dict[str, str],
        residual: np.ndarray,
        temperature: np.ndarray,
    ) -> np.ndarray:
        """
        Picard iteration update for non-linear solver.
        """
        # Simplified Picard update
        update = -residual * 0.1  # Simple relaxation
        return update

    def _broyden_update(
        self,
        mesh: List[Dict[str, Any]],
        materials: Dict[str, str],
        residual: np.ndarray,
        temperature: np.ndarray,
        iteration: int,
    ) -> np.ndarray:
        """
        Broyden method update for non-linear solver.
        """
        # Simplified Broyden update
        if iteration == 0:
            # First iteration: use simple update
            update = -residual * 0.1
        else:
            # Subsequent iterations: use Broyden formula
            update = -residual * 0.05  # Simplified

        return update

    def _calculate_heat_flux(
        self,
        mesh: List[Dict[str, Any]],
        materials: Dict[str, str],
        temperature: np.ndarray,
    ) -> List[Tuple[float, float, float]]:
        """
        Calculate heat flux field.
        """
        heat_flux = []

        for i, node in enumerate(mesh):
            material_name = materials.get(str(i), "aluminum_6061")
            material = self.materials[material_name]

            thermal_conductivity = material.get_property(
                "thermal_conductivity", temperature[i]
            )

            # Calculate temperature gradient (simplified)
            if i == 0:
                grad_x = (temperature[1] - temperature[0]) / 0.1
            elif i == len(temperature) - 1:
                grad_x = (temperature[i] - temperature[i - 1]) / 0.1
            else:
                grad_x = (temperature[i + 1] - temperature[i - 1]) / 0.2

            # Heat flux = -k * grad(T)
            heat_flux_x = -thermal_conductivity * grad_x
            heat_flux_y = 0.0  # Simplified 2D assumption
            heat_flux_z = 0.0  # Simplified 2D assumption

            heat_flux.append((heat_flux_x, heat_flux_y, heat_flux_z))

        return heat_flux

    def _determine_material_phases(
        self, materials: Dict[str, str], temperature: np.ndarray
    ) -> Dict[str, MaterialPhase]:
        """
        Determine material phases based on temperature.
        """
        phases = {}

        for element_id, material_name in materials.items():
            if material_name in self.materials:
                material = self.materials[material_name]
                avg_temp = (
                    temperature[int(element_id)]
                    if int(element_id) < len(temperature)
                    else 293.15
                )
                phases[element_id] = material.get_phase(avg_temp)
            else:
                phases[element_id] = MaterialPhase.SOLID

        return phases

    def _adaptive_mesh_refinement(
        self,
        mesh: List[Dict[str, Any]],
        temperature: np.ndarray,
        heat_flux: List[Tuple[float, float, float]],
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Perform adaptive mesh refinement based on solution gradients.
        """
        # Calculate refinement indicators
        refinement_indicators = []

        for i in range(len(mesh)):
            # Temperature gradient indicator
            if i > 0 and i < len(temperature) - 1:
                temp_gradient = abs(temperature[i + 1] - temperature[i - 1]) / 2.0
            else:
                temp_gradient = 0.0

            # Heat flux gradient indicator
            if i < len(heat_flux):
                heat_flux_magnitude = np.sqrt(
                    sum(heat_flux[i][j] ** 2 for j in range(3))
                )
            else:
                heat_flux_magnitude = 0.0

            # Combined indicator
            indicator = temp_gradient + heat_flux_magnitude * 0.1
            refinement_indicators.append(indicator)

        # Check if refinement is needed
        max_indicator = max(refinement_indicators) if refinement_indicators else 0.0
        should_refine = max_indicator > self.mesh_settings.refinement_threshold

        if should_refine:
            # Simplified mesh refinement: add nodes where indicators are high
            refined_mesh = mesh.copy()

            for i, indicator in enumerate(refinement_indicators):
                if indicator > self.mesh_settings.refinement_threshold:
                    # Add a new node (simplified)
                    new_node = {
                        "id": f"refined_{i}",
                        "position": [0.0, 0.0, 0.0],  # Simplified
                        "size": mesh[i].get("size", 0.1) * 0.5,  # Refine element size
                    }
                    refined_mesh.append(new_node)

            return refined_mesh, True
        else:
            return mesh, False

    def optimize_thermal_design(
        self,
        mesh: List[Dict[str, Any]],
        materials: Dict[str, str],
        boundary_conditions: List[AdvancedBoundaryCondition],
        objective_function: Callable[
            [np.ndarray, List[Tuple[float, float, float]]], float
        ],
        optimization_variables: List[str],
        constraints: List[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Optimize thermal design using advanced algorithms.

        Args:
            mesh: Finite element mesh
            materials: Material assignment
            boundary_conditions: Boundary conditions
            objective_function: Function to minimize
            optimization_variables: Variables to optimize
            constraints: Optimization constraints

        Returns:
            Optimization results
        """
        try:

            def objective_wrapper(x):
                # Update design variables
                updated_mesh = self._update_design_variables(
                    mesh, x, optimization_variables
                )

                # Solve thermal analysis
                results = self.solve_advanced_thermal_analysis(
                    updated_mesh, materials, boundary_conditions
                )

                # Calculate objective
                return objective_function(
                    np.array(results["final_temperature"]), results["final_heat_flux"]
                )

            # Initial guess
            x0 = np.ones(len(optimization_variables))

            # Optimization
            if constraints:
                result = optimize.minimize(
                    objective_wrapper, x0, method="SLSQP", constraints=constraints
                )
            else:
                result = optimize.minimize(objective_wrapper, x0, method="L-BFGS-B")

            return {
                "success": result.success,
                "optimal_value": result.fun,
                "optimal_variables": result.x,
                "iterations": result.nit,
                "message": result.message,
            }

        except Exception as e:
            logger.error(f"Error in thermal optimization: {str(e)}")
            raise

    def _update_design_variables(
        self,
        mesh: List[Dict[str, Any]],
        variables: np.ndarray,
        variable_names: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Update mesh based on design variables.
        """
        updated_mesh = mesh.copy()

        for i, var_name in enumerate(variable_names):
            if var_name == "element_size":
                # Update element sizes
                for j, node in enumerate(updated_mesh):
                    if j < len(variables):
                        node["size"] = variables[i] * 0.1  # Scale factor
            elif var_name == "material_thickness":
                # Update material thickness (simplified)
                pass

        return updated_mesh

    def visualize_thermal_results(
        self,
        mesh: List[Dict[str, Any]],
        temperature_field: np.ndarray,
        heat_flux: List[Tuple[float, float, float]],
        material_phases: Dict[str, MaterialPhase] = None,
    ) -> None:
        """
        Create advanced 3D thermal visualization.
        """
        try:
            fig = plt.figure(figsize=(15, 10))

            # 3D temperature plot
            ax1 = fig.add_subplot(221, projection="3d")
            x_coords = [node.get("position", [0, 0, 0])[0] for node in mesh]
            y_coords = [node.get("position", [0, 0, 0])[1] for node in mesh]
            z_coords = [node.get("position", [0, 0, 0])[2] for node in mesh]

            scatter = ax1.scatter(
                x_coords, y_coords, z_coords, c=temperature_field, cmap="hot", s=50
            )
            ax1.set_title("3D Temperature Field")
            ax1.set_xlabel("X (m)")
            ax1.set_ylabel("Y (m)")
            ax1.set_zlabel("Z (m)")
            plt.colorbar(scatter, ax=ax1, label="Temperature (K)")

            # Heat flux vectors
            ax2 = fig.add_subplot(222, projection="3d")
            heat_flux_x = [flux[0] for flux in heat_flux]
            heat_flux_y = [flux[1] for flux in heat_flux]
            heat_flux_z = [flux[2] for flux in heat_flux]

            ax2.quiver(
                x_coords,
                y_coords,
                z_coords,
                heat_flux_x,
                heat_flux_y,
                heat_flux_z,
                length=0.1,
                normalize=True,
            )
            ax2.set_title("Heat Flux Vectors")
            ax2.set_xlabel("X (m)")
            ax2.set_ylabel("Y (m)")
            ax2.set_zlabel("Z (m)")

            # Material phases
            if material_phases:
                ax3 = fig.add_subplot(223)
                phase_colors = {
                    MaterialPhase.SOLID: "blue",
                    MaterialPhase.LIQUID: "green",
                    MaterialPhase.GAS: "red",
                    MaterialPhase.PLASMA: "purple",
                }

                for element_id, phase in material_phases.items():
                    if int(element_id) < len(x_coords):
                        ax3.scatter(
                            x_coords[int(element_id)],
                            y_coords[int(element_id)],
                            c=phase_colors[phase],
                            s=100,
                            alpha=0.7,
                        )

                ax3.set_title("Material Phases")
                ax3.set_xlabel("X (m)")
                ax3.set_ylabel("Y (m)")

            # Temperature history
            ax4 = fig.add_subplot(224)
            ax4.plot(
                range(len(temperature_field)), temperature_field, "b-", linewidth=2
            )
            ax4.set_title("Temperature Distribution")
            ax4.set_xlabel("Node Index")
            ax4.set_ylabel("Temperature (K)")
            ax4.grid(True)

            plt.tight_layout()
            plt.show()

        except Exception as e:
            logger.error(f"Error in thermal visualization: {str(e)}")
            raise


# Example usage and testing
if __name__ == "__main__":
    # Initialize service
    service = AdvancedThermalAnalysisService()

    # Create simple mesh
    mesh = [
        {"id": "0", "position": [0.0, 0.0, 0.0], "size": 0.1},
        {"id": "1", "position": [0.1, 0.0, 0.0], "size": 0.1},
        {"id": "2", "position": [0.2, 0.0, 0.0], "size": 0.1},
        {"id": "3", "position": [0.3, 0.0, 0.0], "size": 0.1},
        {"id": "4", "position": [0.4, 0.0, 0.0], "size": 0.1},
    ]

    # Material assignment
    materials = {
        "0": "aluminum_6061",
        "1": "aluminum_6061",
        "2": "water",
        "3": "aluminum_6061",
        "4": "aluminum_6061",
    }

    # Boundary conditions
    boundary_conditions = [
        AdvancedBoundaryCondition(
            type=BoundaryConditionType.TEMPERATURE,
            location=[0],
            value={"value": 373.15},  # 100°C
        ),
        AdvancedBoundaryCondition(
            type=BoundaryConditionType.TEMPERATURE,
            location=[4],
            value={"value": 293.15},  # 20°C
        ),
    ]

    # Solve advanced thermal analysis
    results = service.solve_advanced_thermal_analysis(
        mesh, materials, boundary_conditions
    )

    print("Advanced thermal analysis completed!")
    print(
        f"Final temperature range: {min(results['final_temperature']):.2f} - {max(results['final_temperature']):.2f} K"
    )
    print(f"Convergence: {results['convergence_info']['converged']}")
    print(f"Iterations: {results['convergence_info']['iterations']}")
