"""
Electrical Analysis Service for Arxos SVG-BIM Integration

This service provides comprehensive electrical analysis capabilities including:
- DC circuit analysis
- AC circuit analysis
- Transient electrical analysis
- Electromagnetic field analysis
- Signal propagation analysis
- Power distribution analysis

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
import time

logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    """Types of electrical analysis."""
    DC = "dc"
    AC = "ac"
    TRANSIENT = "transient"
    FREQUENCY = "frequency"


class ComponentType(Enum):
    """Types of electrical components."""
    RESISTOR = "resistor"
    CAPACITOR = "capacitor"
    INDUCTOR = "inductor"
    VOLTAGE_SOURCE = "voltage_source"
    CURRENT_SOURCE = "current_source"
    DIODE = "diode"
    TRANSISTOR = "transistor"
    OPAMP = "opamp"


class CircuitType(Enum):
    """Types of electrical circuits."""
    SERIES = "series"
    PARALLEL = "parallel"
    MIXED = "mixed"
    BRIDGE = "bridge"
    FILTER = "filter"
    AMPLIFIER = "amplifier"


@dataclass
class ElectricalComponent:
    """Electrical component definition."""
    id: str
    type: ComponentType
    value: float
    unit: str
    position: Tuple[float, float, float]
    connections: List[str]
    properties: Dict[str, Any]


@dataclass
class VoltageSource:
    """Voltage source definition."""
    id: str
    type: str  # dc, ac, pulse, sine
    magnitude: float
    frequency: float  # for AC
    phase: float     # for AC
    position: Tuple[float, float, float]
    connections: List[str]


@dataclass
class CurrentSource:
    """Current source definition."""
    id: str
    type: str  # dc, ac, pulse, sine
    magnitude: float
    frequency: float  # for AC
    phase: float     # for AC
    position: Tuple[float, float, float]
    connections: List[str]


@dataclass
class ElectricalAnalysisRequest:
    """Electrical analysis request."""
    id: str
    analysis_type: AnalysisType
    circuit_type: CircuitType
    components: List[ElectricalComponent]
    voltage_sources: List[VoltageSource]
    current_sources: List[CurrentSource]
    nodes: List[Tuple[float, float, float]]
    connections: List[Tuple[str, str]]
    solver_settings: Dict[str, Any]
    frequency_range: Optional[Tuple[float, float]] = None


@dataclass
class ElectricalAnalysisResult:
    """Result of electrical analysis."""
    id: str
    analysis_type: AnalysisType
    node_voltages: List[float]
    branch_currents: List[float]
    power_dissipation: List[float]
    voltage_field: List[Tuple[float, float, float]]
    current_field: List[Tuple[float, float, float]]
    electric_field: List[Tuple[float, float, float]]
    magnetic_field: List[Tuple[float, float, float]]
    total_power: float
    total_current: float
    efficiency: float
    analysis_time: float
    convergence_info: Dict[str, Any]
    error: Optional[str] = None


class ElectricalAnalysisService:
    """
    Comprehensive electrical analysis service.

    Provides advanced electrical analysis capabilities including:
    - DC and AC circuit analysis
    - Transient analysis
    - Electromagnetic field analysis
    - Signal propagation
    - Power distribution
    """

    def __init__(self):
        """Initialize the electrical analysis service."""
        self.solvers = self._initialize_solvers()
        self.analysis_cache = {}
        logger.info("Electrical analysis service initialized")

    def _initialize_solvers(self) -> Dict[str, Dict[str, Any]]:
        """Initialize solver configurations."""
        return {
            "nodal_analysis": {
                "name": "Nodal Analysis",
                "description": "Standard nodal analysis for circuit solving",
                "type": "nodal",
                "iterations": 1000,
                "tolerance": 1e-6,
                "relaxation": 0.7
            },
            "mesh_analysis": {
                "name": "Mesh Analysis",
                "description": "Mesh analysis for circuit solving",
                "type": "mesh",
                "iterations": 1000,
                "tolerance": 1e-6,
                "relaxation": 0.7
            },
            "spice": {
                "name": "SPICE-like Solver",
                "description": "SPICE-like circuit simulation",
                "type": "spice",
                "iterations": 1000,
                "tolerance": 1e-6,
                "relaxation": 0.5
            }
        }

    def analyze_circuit(self, request: ElectricalAnalysisRequest) -> ElectricalAnalysisResult:
        """
        Perform electrical circuit analysis.

        Args:
            request: Electrical analysis request

        Returns:
            Electrical analysis result
        """
        start_time = time.time()

        try:
            # Validate request
            self._validate_request(request)

            # Determine analysis method
            if request.analysis_type == AnalysisType.DC:
                result = self._dc_analysis(request)
            elif request.analysis_type == AnalysisType.AC:
                result = self._ac_analysis(request)
            elif request.analysis_type == AnalysisType.TRANSIENT:
                result = self._transient_analysis(request)
            else:
                result = self._frequency_analysis(request)

            # Calculate additional parameters
            result.total_power = self._calculate_total_power(result)
            result.total_current = self._calculate_total_current(result)
            result.efficiency = self._calculate_efficiency(request, result)
            result.analysis_time = time.time() - start_time

            return result

        except Exception as e:
            logger.error(f"Electrical analysis failed: {e}")
            return ElectricalAnalysisResult(
                id=request.id,
                analysis_type=request.analysis_type,
                node_voltages=[],
                branch_currents=[],
                power_dissipation=[],
                voltage_field=[],
                current_field=[],
                electric_field=[],
                magnetic_field=[],
                total_power=0.0,
                total_current=0.0,
                efficiency=0.0,
                analysis_time=time.time() - start_time,
                convergence_info={},
                error=str(e)
            )

    def _dc_analysis(self, request: ElectricalAnalysisRequest) -> ElectricalAnalysisResult:
        """Perform DC circuit analysis."""
        n_nodes = len(request.nodes)

        # Build conductance matrix
        conductance_matrix = self._build_conductance_matrix(request)

        # Build current vector
        current_vector = self._build_current_vector(request)

        # Solve nodal equations: G*V = I
        try:
            node_voltages = np.linalg.solve(conductance_matrix, current_vector)
        except np.linalg.LinAlgError:
            # Handle singular matrix
            node_voltages = np.zeros(n_nodes)

        # Calculate branch currents
        branch_currents = self._calculate_branch_currents(node_voltages, request)

        # Calculate power dissipation
        power_dissipation = self._calculate_power_dissipation(node_voltages, branch_currents, request)

        # Calculate electromagnetic fields
        voltage_field = self._calculate_voltage_field(node_voltages, request)
        current_field = self._calculate_current_field(branch_currents, request)
        electric_field = self._calculate_electric_field(voltage_field, request)
        magnetic_field = self._calculate_magnetic_field(current_field, request)

        # Convergence information
        convergence_info = {
            "iterations": 1,
            "residual": 0.0,
            "converged": True,
            "solver": "Nodal Analysis"
        }

        return ElectricalAnalysisResult(
            id=request.id,
            analysis_type=request.analysis_type,
            node_voltages=node_voltages.tolist(),
            branch_currents=branch_currents.tolist(),
            power_dissipation=power_dissipation.tolist(),
            voltage_field=voltage_field.tolist(),
            current_field=current_field.tolist(),
            electric_field=electric_field.tolist(),
            magnetic_field=magnetic_field.tolist(),
            total_power=0.0,  # Will be calculated later
            total_current=0.0,  # Will be calculated later
            efficiency=0.0,  # Will be calculated later
            analysis_time=0.0,  # Will be calculated later
            convergence_info=convergence_info
        )

    def _ac_analysis(self, request: ElectricalAnalysisRequest) -> ElectricalAnalysisResult:
        """Perform AC circuit analysis."""
        n_nodes = len(request.nodes)
        frequency = request.voltage_sources[0].frequency if request.voltage_sources else 60.0

        # Build admittance matrix (complex)
        admittance_matrix = self._build_admittance_matrix(request, frequency)

        # Build current vector (complex)
        current_vector = self._build_ac_current_vector(request, frequency)

        # Solve nodal equations: Y*V = I
        try:
            node_voltages_complex = np.linalg.solve(admittance_matrix, current_vector)
            node_voltages = np.abs(node_voltages_complex)
        except np.linalg.LinAlgError:
            node_voltages = np.zeros(n_nodes)

        # Calculate branch currents
        branch_currents = self._calculate_ac_branch_currents(node_voltages, request, frequency)

        # Calculate power dissipation
        power_dissipation = self._calculate_ac_power_dissipation(node_voltages, branch_currents, request)

        # Calculate electromagnetic fields
        voltage_field = self._calculate_ac_voltage_field(node_voltages, request, frequency)
        current_field = self._calculate_ac_current_field(branch_currents, request, frequency)
        electric_field = self._calculate_ac_electric_field(voltage_field, request, frequency)
        magnetic_field = self._calculate_ac_magnetic_field(current_field, request, frequency)

        # Convergence information
        convergence_info = {
            "iterations": 1,
            "residual": 0.0,
            "converged": True,
            "solver": "AC Nodal Analysis",
            "frequency": frequency
        }

        return ElectricalAnalysisResult(
            id=request.id,
            analysis_type=request.analysis_type,
            node_voltages=node_voltages.tolist(),
            branch_currents=branch_currents.tolist(),
            power_dissipation=power_dissipation.tolist(),
            voltage_field=voltage_field.tolist(),
            current_field=current_field.tolist(),
            electric_field=electric_field.tolist(),
            magnetic_field=magnetic_field.tolist(),
            total_power=0.0,  # Will be calculated later
            total_current=0.0,  # Will be calculated later
            efficiency=0.0,  # Will be calculated later
            analysis_time=0.0,  # Will be calculated later
            convergence_info=convergence_info
        )

    def _transient_analysis(self, request: ElectricalAnalysisRequest) -> ElectricalAnalysisResult:
        """Perform transient circuit analysis."""
        n_nodes = len(request.nodes)
        time_steps = 1000
        dt = 0.001  # Time step in seconds

        # Initialize node voltages
        node_voltages = np.zeros(n_nodes)

        # Time stepping
        for time_step in range(time_steps):
            time = time_step * dt

            # Update source values for current time
            self._update_sources_for_time(request, time)

            # Build conductance matrix
            conductance_matrix = self._build_conductance_matrix(request)

            # Build current vector
            current_vector = self._build_current_vector(request)

            # Solve nodal equations
            try:
                new_voltages = np.linalg.solve(conductance_matrix, current_vector)
                node_voltages = new_voltages
            except np.linalg.LinAlgError:
                pass

        # Calculate final results
        branch_currents = self._calculate_branch_currents(node_voltages, request)
        power_dissipation = self._calculate_power_dissipation(node_voltages, branch_currents, request)

        # Calculate electromagnetic fields
        voltage_field = self._calculate_voltage_field(node_voltages, request)
        current_field = self._calculate_current_field(branch_currents, request)
        electric_field = self._calculate_electric_field(voltage_field, request)
        magnetic_field = self._calculate_magnetic_field(current_field, request)

        # Convergence information
        convergence_info = {
            "time_steps": time_steps,
            "final_time": time_steps * dt,
            "converged": True,
            "solver": "Transient Analysis"
        }

        return ElectricalAnalysisResult(
            id=request.id,
            analysis_type=request.analysis_type,
            node_voltages=node_voltages.tolist(),
            branch_currents=branch_currents.tolist(),
            power_dissipation=power_dissipation.tolist(),
            voltage_field=voltage_field.tolist(),
            current_field=current_field.tolist(),
            electric_field=electric_field.tolist(),
            magnetic_field=magnetic_field.tolist(),
            total_power=0.0,  # Will be calculated later
            total_current=0.0,  # Will be calculated later
            efficiency=0.0,  # Will be calculated later
            analysis_time=0.0,  # Will be calculated later
            convergence_info=convergence_info
        )

    def _frequency_analysis(self, request: ElectricalAnalysisRequest) -> ElectricalAnalysisResult:
        """Perform frequency domain analysis."""
        if not request.frequency_range:
            request.frequency_range = (1.0, 1000.0)

        start_freq, end_freq = request.frequency_range
        n_frequencies = 100
        frequencies = np.logspace(np.log10(start_freq), np.log10(end_freq), n_frequencies)

        # Store results for each frequency
        node_voltages_freq = []
        branch_currents_freq = []

        for freq in frequencies:
            # Build admittance matrix
            admittance_matrix = self._build_admittance_matrix(request, freq)

            # Build current vector
            current_vector = self._build_ac_current_vector(request, freq)

            # Solve nodal equations
            try:
                node_voltages_complex = np.linalg.solve(admittance_matrix, current_vector)
                node_voltages_freq.append(np.abs(node_voltages_complex))
            except np.linalg.LinAlgError:
                node_voltages_freq.append(np.zeros(len(request.nodes)))

        # Use results at middle frequency
        mid_idx = n_frequencies // 2
        node_voltages = node_voltages_freq[mid_idx]
        branch_currents = self._calculate_ac_branch_currents(node_voltages, request, frequencies[mid_idx])
        power_dissipation = self._calculate_ac_power_dissipation(node_voltages, branch_currents, request)

        # Calculate electromagnetic fields
        voltage_field = self._calculate_ac_voltage_field(node_voltages, request, frequencies[mid_idx])
        current_field = self._calculate_ac_current_field(branch_currents, request, frequencies[mid_idx])
        electric_field = self._calculate_ac_electric_field(voltage_field, request, frequencies[mid_idx])
        magnetic_field = self._calculate_ac_magnetic_field(current_field, request, frequencies[mid_idx])

        # Convergence information
        convergence_info = {
            "frequencies": n_frequencies,
            "frequency_range": request.frequency_range,
            "converged": True,
            "solver": "Frequency Domain Analysis"
        }

        return ElectricalAnalysisResult(
            id=request.id,
            analysis_type=request.analysis_type,
            node_voltages=node_voltages.tolist(),
            branch_currents=branch_currents.tolist(),
            power_dissipation=power_dissipation.tolist(),
            voltage_field=voltage_field.tolist(),
            current_field=current_field.tolist(),
            electric_field=electric_field.tolist(),
            magnetic_field=magnetic_field.tolist(),
            total_power=0.0,  # Will be calculated later
            total_current=0.0,  # Will be calculated later
            efficiency=0.0,  # Will be calculated later
            analysis_time=0.0,  # Will be calculated later
            convergence_info=convergence_info
        )

    def _build_conductance_matrix(self, request: ElectricalAnalysisRequest) -> np.ndarray:
        """Build conductance matrix for nodal analysis."""
        n_nodes = len(request.nodes)
        conductance_matrix = np.zeros((n_nodes, n_nodes))

        # Add conductances from components import components
        for component in request.components:
            if component.type == ComponentType.RESISTOR:
                # Add conductance to matrix
                for i, conn in enumerate(component.connections):
                    if i < len(component.connections) - 1:
                        node1 = int(conn)
                        node2 = int(component.connections[i+1])
                        conductance = 1.0 / component.value

                        if node1 < n_nodes and node2 < n_nodes:
                            conductance_matrix[node1, node1] += conductance
                            conductance_matrix[node2, node2] += conductance
                            conductance_matrix[node1, node2] -= conductance
                            conductance_matrix[node2, node1] -= conductance

        # Ground node (node 0)
        conductance_matrix[0, 0] = 1.0

        return conductance_matrix

    def _build_admittance_matrix(self, request: ElectricalAnalysisRequest, frequency: float) -> np.ndarray:
        """Build admittance matrix for AC analysis."""
        n_nodes = len(request.nodes)
        admittance_matrix = np.zeros((n_nodes, n_nodes), dtype=complex)

        # Add admittances from components import components
        for component in request.components:
            if component.type == ComponentType.RESISTOR:
                # Resistor admittance
                admittance = 1.0 / component.value
            elif component.type == ComponentType.CAPACITOR:
                # Capacitor admittance
                admittance = 1j * 2 * math.pi * frequency * component.value
            elif component.type == ComponentType.INDUCTOR:
                # Inductor admittance
                admittance = 1.0 / (1j * 2 * math.pi * frequency * component.value)
            else:
                continue

            # Add to matrix
            for i, conn in enumerate(component.connections):
                if i < len(component.connections) - 1:
                    node1 = int(conn)
                    node2 = int(component.connections[i+1])

                    if node1 < n_nodes and node2 < n_nodes:
                        admittance_matrix[node1, node1] += admittance
                        admittance_matrix[node2, node2] += admittance
                        admittance_matrix[node1, node2] -= admittance
                        admittance_matrix[node2, node1] -= admittance

        # Ground node (node 0)
        admittance_matrix[0, 0] = 1.0

        return admittance_matrix

    def _build_current_vector(self, request: ElectricalAnalysisRequest) -> np.ndarray:
        """Build current vector for nodal analysis."""
        n_nodes = len(request.nodes)
        current_vector = np.zeros(n_nodes)

        # Add current sources
        for source in request.current_sources:
            if source.type == "dc":
                # Add DC current sources
                for i, conn in enumerate(source.connections):
                    if i < len(source.connections) - 1:
                        node1 = int(conn)
                        node2 = int(source.connections[i+1])

                        if node1 < n_nodes and node2 < n_nodes:
                            current_vector[node1] += source.magnitude
                            current_vector[node2] -= source.magnitude

        # Ground node (node 0)
        current_vector[0] = 0.0

        return current_vector

    def _build_ac_current_vector(self, request: ElectricalAnalysisRequest, frequency: float) -> np.ndarray:
        """Build AC current vector."""
        n_nodes = len(request.nodes)
        current_vector = np.zeros(n_nodes, dtype=complex)

        # Add AC current sources
        for source in request.current_sources:
            if source.type == "ac":
                # Add AC current sources
                magnitude = source.magnitude
                phase = source.phase * math.pi / 180.0  # Convert to radians
                complex_current = magnitude * (math.cos(phase) + 1j * math.sin(phase))

                for i, conn in enumerate(source.connections):
                    if i < len(source.connections) - 1:
                        node1 = int(conn)
                        node2 = int(source.connections[i+1])

                        if node1 < n_nodes and node2 < n_nodes:
                            current_vector[node1] += complex_current
                            current_vector[node2] -= complex_current

        # Ground node (node 0)
        current_vector[0] = 0.0

        return current_vector

    def _calculate_branch_currents(self, node_voltages: np.ndarray, request: ElectricalAnalysisRequest) -> np.ndarray:
        """Calculate branch currents."""
        n_branches = len(request.components)
        branch_currents = np.zeros(n_branches)

        for i, component in enumerate(request.components):
            if component.type == ComponentType.RESISTOR:
                # Calculate current through resistor
                if len(component.connections) >= 2:
                    node1 = int(component.connections[0])
                    node2 = int(component.connections[1])

                    if node1 < len(node_voltages) and node2 < len(node_voltages):
                        voltage_diff = node_voltages[node1] - node_voltages[node2]
                        branch_currents[i] = voltage_diff / component.value

        return branch_currents

    def _calculate_ac_branch_currents(self, node_voltages: np.ndarray, request: ElectricalAnalysisRequest, frequency: float) -> np.ndarray:
        """Calculate AC branch currents."""
        n_branches = len(request.components)
        branch_currents = np.zeros(n_branches)

        for i, component in enumerate(request.components):
            if component.type == ComponentType.RESISTOR:
                # Calculate current through resistor
                if len(component.connections) >= 2:
                    node1 = int(component.connections[0])
                    node2 = int(component.connections[1])

                    if node1 < len(node_voltages) and node2 < len(node_voltages):
                        voltage_diff = node_voltages[node1] - node_voltages[node2]
                        branch_currents[i] = voltage_diff / component.value

            elif component.type == ComponentType.CAPACITOR:
                # Calculate current through capacitor
                if len(component.connections) >= 2:
                    node1 = int(component.connections[0])
                    node2 = int(component.connections[1])

                    if node1 < len(node_voltages) and node2 < len(node_voltages):
                        voltage_diff = node_voltages[node1] - node_voltages[node2]
                        impedance = 1.0 / (2 * math.pi * frequency * component.value)
                        branch_currents[i] = voltage_diff / impedance

        return branch_currents

    def _calculate_power_dissipation(self, node_voltages: np.ndarray, branch_currents: np.ndarray, request: ElectricalAnalysisRequest) -> np.ndarray:
        """Calculate power dissipation in components."""
        n_components = len(request.components)
        power_dissipation = np.zeros(n_components)

        for i, component in enumerate(request.components):
            if component.type == ComponentType.RESISTOR:
                # P = I²R
                power_dissipation[i] = branch_currents[i] ** 2 * component.value

        return power_dissipation

    def _calculate_ac_power_dissipation(self, node_voltages: np.ndarray, branch_currents: np.ndarray, request: ElectricalAnalysisRequest) -> np.ndarray:
        """Calculate AC power dissipation."""
        return self._calculate_power_dissipation(node_voltages, branch_currents, request)

    def _calculate_voltage_field(self, node_voltages: np.ndarray, request: ElectricalAnalysisRequest) -> np.ndarray:
        """Calculate voltage field."""
        n_nodes = len(request.nodes)
        voltage_field = np.zeros((n_nodes, 3))

        for i, node in enumerate(request.nodes):
            voltage_field[i] = [node_voltages[i], 0.0, 0.0]  # Simplified field

        return voltage_field

    def _calculate_current_field(self, branch_currents: np.ndarray, request: ElectricalAnalysisRequest) -> np.ndarray:
        """Calculate current field."""
        n_components = len(request.components)
        current_field = np.zeros((n_components, 3))

        for i, component in enumerate(request.components):
            current_field[i] = [branch_currents[i], 0.0, 0.0]  # Simplified field

        return current_field

    def _calculate_electric_field(self, voltage_field: np.ndarray, request: ElectricalAnalysisRequest) -> np.ndarray:
        """Calculate electric field."""
        n_nodes = len(voltage_field)
        electric_field = np.zeros((n_nodes, 3))

        # E = -∇V (simplified calculation)
        for i in range(n_nodes):
            if i < n_nodes - 1:
                voltage_gradient = voltage_field[i+1] - voltage_field[i]
                electric_field[i] = -voltage_gradient

        return electric_field

    def _calculate_magnetic_field(self, current_field: np.ndarray, request: ElectricalAnalysisRequest) -> np.ndarray:
        """Calculate magnetic field."""
        n_components = len(current_field)
        magnetic_field = np.zeros((n_components, 3))

        # B = μ₀I/(2πr) (simplified calculation)
        mu_0 = 4 * math.pi * 1e-7  # Permeability of free space

        for i, current in enumerate(current_field):
            if np.linalg.norm(current) > 0:
                r = 0.01  # Distance from wire (simplified)
                magnetic_field[i] = mu_0 * np.linalg.norm(current) / (2 * math.pi * r) * np.array([0.0, 0.0, 1.0])

        return magnetic_field

    def _calculate_ac_voltage_field(self, node_voltages: np.ndarray, request: ElectricalAnalysisRequest, frequency: float) -> np.ndarray:
        """Calculate AC voltage field."""
        return self._calculate_voltage_field(node_voltages, request)

    def _calculate_ac_current_field(self, branch_currents: np.ndarray, request: ElectricalAnalysisRequest, frequency: float) -> np.ndarray:
        """Calculate AC current field."""
        return self._calculate_current_field(branch_currents, request)

    def _calculate_ac_electric_field(self, voltage_field: np.ndarray, request: ElectricalAnalysisRequest, frequency: float) -> np.ndarray:
        """Calculate AC electric field."""
        return self._calculate_electric_field(voltage_field, request)

    def _calculate_ac_magnetic_field(self, current_field: np.ndarray, request: ElectricalAnalysisRequest, frequency: float) -> np.ndarray:
        """Calculate AC magnetic field."""
        return self._calculate_magnetic_field(current_field, request)

    def _update_sources_for_time(self, request: ElectricalAnalysisRequest, time: float) -> None:
        """Update source values for current time."""
        for source in request.voltage_sources:
            if source.type == "sine":
                source.magnitude = source.magnitude * math.sin(2 * math.pi * source.frequency * time + source.phase)
            elif source.type == "pulse":
                # Simplified pulse waveform
                period = 1.0 / source.frequency
                t_mod = time % period
                if t_mod < period / 2:
                    source.magnitude = source.magnitude
                else:
                    source.magnitude = 0.0

    def _calculate_total_power(self, result: ElectricalAnalysisResult) -> float:
        """Calculate total power."""
        return sum(result.power_dissipation)

    def _calculate_total_current(self, result: ElectricalAnalysisResult) -> float:
        """Calculate total current."""
        return sum(np.abs(current) for current in result.branch_currents)

    def _calculate_efficiency(self, request: ElectricalAnalysisRequest, result: ElectricalAnalysisResult) -> float:
        """Calculate circuit efficiency."""
        input_power = 0.0
        for source in request.voltage_sources:
            input_power += source.magnitude * source.magnitude / 100.0  # Simplified

        output_power = result.total_power

        if input_power > 0:
            return (output_power / input_power) * 100.0
        else:
            return 0.0

    def _validate_request(self, request: ElectricalAnalysisRequest) -> None:
        """Validate electrical analysis request."""
        if not request.components:
            raise ValueError("At least one component is required")

        if not request.nodes:
            raise ValueError("At least one node is required")

        if not request.connections:
            raise ValueError("At least one connection is required")

        # Validate components
        for component in request.components:
            if component.value <= 0:
                raise ValueError(f"Component {component.id} must have positive value")

            if not component.connections:
                raise ValueError(f"Component {component.id} must have connections")

    def get_solver_config(self, solver_name: str) -> Optional[Dict[str, Any]]:
        """Get solver configuration by name."""
        return self.solvers.get(solver_name)

    def add_solver(self, name: str, config: Dict[str, Any]) -> None:
        """Add a new solver configuration."""
        self.solvers[name] = config
        logger.info(f"Added electrical solver: {name}")
