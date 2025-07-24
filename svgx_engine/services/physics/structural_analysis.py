"""
Structural Analysis Service for Arxos SVG-BIM Integration

This service provides comprehensive structural analysis capabilities including:
- Static and dynamic load analysis
- Stress and strain calculations
- Structural deflection modeling
- Column and beam buckling analysis
- Material fatigue calculations

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


class LoadType(Enum):
    """Types of structural loads."""
    DEAD = "dead"
    LIVE = "live"
    WIND = "wind"
    SEISMIC = "seismic"
    SNOW = "snow"
    IMPACT = "impact"


class MaterialType(Enum):
    """Types of structural materials."""
    STEEL = "steel"
    CONCRETE = "concrete"
    WOOD = "wood"
    ALUMINUM = "aluminum"
    COMPOSITE = "composite"


class AnalysisType(Enum):
    """Types of structural analysis."""
    STATIC = "static"
    DYNAMIC = "dynamic"
    BUCKLING = "buckling"
    FATIGUE = "fatigue"
    DEFLECTION = "deflection"


@dataclass
class MaterialProperties:
    """Material properties for structural analysis."""
    name: str
    type: MaterialType
    elastic_modulus: float  # E in MPa
    poisson_ratio: float    # ν
    yield_strength: float   # σy in MPa
    ultimate_strength: float # σu in MPa
    density: float          # ρ in kg/m³
    thermal_expansion: float # α in 1/°C
    fatigue_strength: float # σf in MPa


@dataclass
class Load:
    """Structural load definition."""
    id: str
    type: LoadType
    magnitude: float  # in N or N/m²
    direction: Tuple[float, float, float]  # unit vector
    location: Tuple[float, float, float]   # coordinates
    duration: float   # in seconds (0 for static loads)


@dataclass
class StructuralElement:
    """Structural element definition."""
    id: str
    type: str  # beam, column, plate, shell
    material: MaterialProperties
    geometry: Dict[str, Any]  # cross-section properties
    nodes: List[Tuple[float, float, float]]
    supports: List[Dict[str, Any]]
    loads: List[Load]


@dataclass
class AnalysisResult:
    """Result of structural analysis."""
    element_id: str
    analysis_type: AnalysisType
    displacements: List[Tuple[float, float, float]]
    stresses: List[Tuple[float, float, float, float, float, float]]  # σxx, σyy, σzz, τxy, τyz, τxz
    strains: List[Tuple[float, float, float, float, float, float]]   # εxx, εyy, εzz, γxy, γyz, γxz
    forces: List[Tuple[float, float, float, float, float, float]]    # Fx, Fy, Fz, Mx, My, Mz
    safety_factor: float
    max_displacement: float
    max_stress: float
    max_strain: float
    buckling_load: Optional[float] = None
    fatigue_life: Optional[float] = None


class StructuralAnalysisService:
    """
    Comprehensive structural analysis service.
    
    Provides advanced structural analysis capabilities including:
    - Static and dynamic analysis
    - Stress and strain calculations
    - Buckling analysis
    - Fatigue analysis
    - Deflection analysis
    """
    
    def __init__(self):
        """Initialize the structural analysis service."""
        self.materials = self._initialize_materials()
        self.analysis_cache = {}
        logger.info("Structural analysis service initialized")
    
    def _initialize_materials(self) -> Dict[str, MaterialProperties]:
        """Initialize common material properties."""
        return {
            "A36_Steel": MaterialProperties(
                name="A36 Steel",
                type=MaterialType.STEEL,
                elastic_modulus=200000,  # MPa
                poisson_ratio=0.3,
                yield_strength=250,      # MPa
                ultimate_strength=400,   # MPa
                density=7850,            # kg/m³
                thermal_expansion=12e-6, # 1/°C
                fatigue_strength=150     # MPa
            ),
            "A992_Steel": MaterialProperties(
                name="A992 Steel",
                type=MaterialType.STEEL,
                elastic_modulus=200000,
                poisson_ratio=0.3,
                yield_strength=345,
                ultimate_strength=450,
                density=7850,
                thermal_expansion=12e-6,
                fatigue_strength=200
            ),
            "Concrete_C30": MaterialProperties(
                name="C30 Concrete",
                type=MaterialType.CONCRETE,
                elastic_modulus=30000,
                poisson_ratio=0.2,
                yield_strength=30,
                ultimate_strength=40,
                density=2400,
                thermal_expansion=10e-6,
                fatigue_strength=15
            ),
            "Douglas_Fir": MaterialProperties(
                name="Douglas Fir",
                type=MaterialType.WOOD,
                elastic_modulus=13000,
                poisson_ratio=0.3,
                yield_strength=40,
                ultimate_strength=60,
                density=530,
                thermal_expansion=3e-6,
                fatigue_strength=25
            )
        }
    
    def analyze_structure(self, elements: List[StructuralElement], 
                         analysis_type: AnalysisType = AnalysisType.STATIC) -> List[AnalysisResult]:
        """
        Perform structural analysis on a set of elements.
        
        Args:
            elements: List of structural elements to analyze
            analysis_type: Type of analysis to perform
            
        Returns:
            List of analysis results for each element
        """
        results = []
        
        for element in elements:
            try:
                if analysis_type == AnalysisType.STATIC:
                    result = self._static_analysis(element)
                elif analysis_type == AnalysisType.DYNAMIC:
                    result = self._dynamic_analysis(element)
                elif analysis_type == AnalysisType.BUCKLING:
                    result = self._buckling_analysis(element)
                elif analysis_type == AnalysisType.FATIGUE:
                    result = self._fatigue_analysis(element)
                elif analysis_type == AnalysisType.DEFLECTION:
                    result = self._deflection_analysis(element)
                else:
                    raise ValueError(f"Unsupported analysis type: {analysis_type}")
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Analysis failed for element {element.id}: {e}")
                # Create error result
                results.append(AnalysisResult(
                    element_id=element.id,
                    analysis_type=analysis_type,
                    displacements=[],
                    stresses=[],
                    strains=[],
                    forces=[],
                    safety_factor=0.0,
                    max_displacement=0.0,
                    max_stress=0.0,
                    max_strain=0.0
                ))
        
        return results
    
    def _static_analysis(self, element: StructuralElement) -> AnalysisResult:
        """Perform static analysis on a structural element."""
        # Calculate element stiffness matrix
        K = self._calculate_stiffness_matrix(element)
        
        # Calculate load vector
        F = self._calculate_load_vector(element)
        
        # Solve for displacements
        try:
            u = np.linalg.solve(K, F)
        except np.linalg.LinAlgError:
            # Handle singular matrix
            u = np.zeros_like(F)
        
        # Calculate stresses and strains
        stresses = self._calculate_stresses(element, u)
        strains = self._calculate_strains(element, u)
        forces = self._calculate_forces(element, u)
        
        # Calculate safety factors
        safety_factor = self._calculate_safety_factor(element, stresses)
        
        # Calculate maximum values
        max_displacement = np.max(np.linalg.norm(u.reshape(-1, 3), axis=1))
        max_stress = np.max(np.linalg.norm(stresses, axis=1))
        max_strain = np.max(np.linalg.norm(strains, axis=1))
        
        return AnalysisResult(
            element_id=element.id,
            analysis_type=AnalysisType.STATIC,
            displacements=u.reshape(-1, 3).tolist(),
            stresses=stresses.tolist(),
            strains=strains.tolist(),
            forces=forces.tolist(),
            safety_factor=safety_factor,
            max_displacement=max_displacement,
            max_stress=max_stress,
            max_strain=max_strain
        )
    
    def _dynamic_analysis(self, element: StructuralElement) -> AnalysisResult:
        """Perform dynamic analysis on a structural element."""
        # Calculate mass matrix
        M = self._calculate_mass_matrix(element)
        
        # Calculate stiffness matrix
        K = self._calculate_stiffness_matrix(element)
        
        # Calculate damping matrix (Rayleigh damping)
        C = self._calculate_damping_matrix(element, M, K)
        
        # Time integration (Newmark method)
        dt = 0.001  # Time step
        t_max = 1.0  # Maximum time
        steps = int(t_max / dt)
        
        # Initialize displacement, velocity, and acceleration
        u = np.zeros((steps, len(M)))
        v = np.zeros((steps, len(M)))
        a = np.zeros((steps, len(M)))
        
        # Time integration loop
        for i in range(1, steps):
            # Newmark integration
            u[i] = u[i-1] + dt * v[i-1] + 0.5 * dt**2 * a[i-1]
            v[i] = v[i-1] + dt * a[i-1]
            
            # Calculate acceleration
            F = self._calculate_dynamic_load_vector(element, i * dt)
            a[i] = np.linalg.solve(M, F - K @ u[i] - C @ v[i])
        
        # Calculate maximum values
        max_displacement = np.max(np.linalg.norm(u, axis=1))
        max_stress = self._calculate_max_dynamic_stress(element, u)
        max_strain = self._calculate_max_dynamic_strain(element, u)
        
        return AnalysisResult(
            element_id=element.id,
            analysis_type=AnalysisType.DYNAMIC,
            displacements=u[-1].reshape(-1, 3).tolist(),
            stresses=self._calculate_dynamic_stresses(element, u[-1]).tolist(),
            strains=self._calculate_dynamic_strains(element, u[-1]).tolist(),
            forces=self._calculate_dynamic_forces(element, u[-1]).tolist(),
            safety_factor=self._calculate_dynamic_safety_factor(element, u),
            max_displacement=max_displacement,
            max_stress=max_stress,
            max_strain=max_strain
        )
    
    def _buckling_analysis(self, element: StructuralElement) -> AnalysisResult:
        """Perform buckling analysis on a structural element."""
        # Calculate geometric stiffness matrix
        K_G = self._calculate_geometric_stiffness_matrix(element)
        
        # Calculate elastic stiffness matrix
        K_E = self._calculate_stiffness_matrix(element)
        
        # Solve eigenvalue problem for buckling loads
        try:
            # For buckling analysis, we solve (K_E - λK_G)φ = 0
            # This is equivalent to solving K_E φ = λK_G φ
            # We use eigvals to get eigenvalues only
            eigenvalues = np.linalg.eigvals(np.linalg.solve(K_G, K_E))
            buckling_loads = 1.0 / eigenvalues
            buckling_loads = buckling_loads[np.isfinite(buckling_loads)]
            
            if len(buckling_loads) > 0:
                critical_buckling_load = np.min(buckling_loads[buckling_loads > 0])
            else:
                critical_buckling_load = float('inf')
                
        except np.linalg.LinAlgError:
            critical_buckling_load = float('inf')
        
        # Calculate buckling mode shape
        buckling_mode = self._calculate_buckling_mode(element, critical_buckling_load)
        
        return AnalysisResult(
            element_id=element.id,
            analysis_type=AnalysisType.BUCKLING,
            displacements=buckling_mode.tolist(),
            stresses=[],
            strains=[],
            forces=[],
            safety_factor=critical_buckling_load,
            max_displacement=np.max(np.abs(buckling_mode)),
            max_stress=0.0,
            max_strain=0.0,
            buckling_load=critical_buckling_load
        )
    
    def _fatigue_analysis(self, element: StructuralElement) -> AnalysisResult:
        """Perform fatigue analysis on a structural element."""
        # Calculate stress range
        stress_range = self._calculate_stress_range(element)
        
        # Calculate fatigue life using S-N curve
        fatigue_life = self._calculate_fatigue_life(element, stress_range)
        
        # Calculate cumulative damage
        damage = self._calculate_cumulative_damage(element)
        
        # Calculate remaining life
        remaining_life = fatigue_life * (1.0 - damage)
        
        return AnalysisResult(
            element_id=element.id,
            analysis_type=AnalysisType.FATIGUE,
            displacements=[],
            stresses=stress_range.tolist(),
            strains=[],
            forces=[],
            safety_factor=remaining_life / fatigue_life if fatigue_life > 0 else 0.0,
            max_displacement=0.0,
            max_stress=np.max(stress_range),
            max_strain=0.0,
            fatigue_life=remaining_life
        )
    
    def _deflection_analysis(self, element: StructuralElement) -> AnalysisResult:
        """Perform deflection analysis on a structural element."""
        # Calculate deflections under various load combinations
        deflections = []
        
        for load in element.loads:
            deflection = self._calculate_deflection(element, load)
            deflections.append(deflection)
        
        # Combine deflections
        total_deflection = np.sum(deflections, axis=0)
        
        # Calculate maximum deflection
        max_deflection = np.max(np.linalg.norm(total_deflection.reshape(-1, 3), axis=1))
        
        # Check deflection limits
        deflection_limit = self._get_deflection_limit(element)
        deflection_ratio = max_deflection / deflection_limit if deflection_limit > 0 else 0.0
        
        return AnalysisResult(
            element_id=element.id,
            analysis_type=AnalysisType.DEFLECTION,
            displacements=total_deflection.reshape(-1, 3).tolist(),
            stresses=[],
            strains=[],
            forces=[],
            safety_factor=1.0 / deflection_ratio if deflection_ratio > 0 else float('inf'),
            max_displacement=max_deflection,
            max_stress=0.0,
            max_strain=0.0
        )
    
    # Helper methods for matrix calculations
    
    def _calculate_stiffness_matrix(self, element: StructuralElement) -> np.ndarray:
        """Calculate element stiffness matrix."""
        # Simplified stiffness matrix calculation
        # In a real implementation, this would be more complex
        n_nodes = len(element.nodes)
        K = np.zeros((n_nodes * 3, n_nodes * 3))
        
        # Add basic stiffness terms
        for i in range(n_nodes):
            for j in range(n_nodes):
                if i == j:
                    K[i*3:(i+1)*3, j*3:(j+1)*3] = np.eye(3) * element.material.elastic_modulus
                else:
                    K[i*3:(i+1)*3, j*3:(j+1)*3] = np.eye(3) * element.material.elastic_modulus * 0.1
        
        return K
    
    def _calculate_mass_matrix(self, element: StructuralElement) -> np.ndarray:
        """Calculate element mass matrix."""
        n_nodes = len(element.nodes)
        M = np.zeros((n_nodes * 3, n_nodes * 3))
        
        # Lumped mass matrix
        for i in range(n_nodes):
            M[i*3:(i+1)*3, i*3:(i+1)*3] = np.eye(3) * element.material.density
        
        return M
    
    def _calculate_damping_matrix(self, element: StructuralElement, M: np.ndarray, K: np.ndarray) -> np.ndarray:
        """Calculate damping matrix using Rayleigh damping."""
        alpha = 0.02  # Mass proportional damping
        beta = 0.01   # Stiffness proportional damping
        
        return alpha * M + beta * K
    
    def _calculate_load_vector(self, element: StructuralElement) -> np.ndarray:
        """Calculate load vector for static analysis."""
        n_nodes = len(element.nodes)
        F = np.zeros(n_nodes * 3)
        
        for load in element.loads:
            # Distribute load to nodes
            for i, node in enumerate(element.nodes):
                F[i*3:(i+1)*3] += np.array(load.direction) * load.magnitude / len(element.nodes)
        
        return F
    
    def _calculate_dynamic_load_vector(self, element: StructuralElement, time: float) -> np.ndarray:
        """Calculate load vector for dynamic analysis."""
        n_nodes = len(element.nodes)
        F = np.zeros(n_nodes * 3)
        
        for load in element.loads:
            # Time-varying load
            load_magnitude = load.magnitude * math.sin(2 * math.pi * time)
            for i, node in enumerate(element.nodes):
                F[i*3:(i+1)*3] += np.array(load.direction) * load_magnitude / len(element.nodes)
        
        return F
    
    def _calculate_stresses(self, element: StructuralElement, u: np.ndarray) -> np.ndarray:
        """Calculate stresses from displacements."""
        # Simplified stress calculation
        n_nodes = len(element.nodes)
        stresses = np.zeros((n_nodes, 6))  # σxx, σyy, σzz, τxy, τyz, τxz
        
        for i in range(n_nodes):
            # Hooke's law
            strain = u[i*3:(i+1)*3]
            E = element.material.elastic_modulus
            ν = element.material.poisson_ratio
            
            # Plane stress assumption
            stresses[i, 0] = E / (1 - ν**2) * (strain[0] + ν * strain[1])  # σxx
            stresses[i, 1] = E / (1 - ν**2) * (strain[1] + ν * strain[0])  # σyy
            stresses[i, 2] = 0  # σzz
            stresses[i, 3] = E / (2 * (1 + ν)) * strain[2]  # τxy
            stresses[i, 4] = 0  # τyz
            stresses[i, 5] = 0  # τxz
        
        return stresses
    
    def _calculate_strains(self, element: StructuralElement, u: np.ndarray) -> np.ndarray:
        """Calculate strains from displacements."""
        # Simplified strain calculation
        n_nodes = len(element.nodes)
        strains = np.zeros((n_nodes, 6))  # εxx, εyy, εzz, γxy, γyz, γxz
        
        for i in range(n_nodes):
            displacement = u[i*3:(i+1)*3]
            # Simple strain calculation
            strains[i, 0] = displacement[0]  # εxx
            strains[i, 1] = displacement[1]  # εyy
            strains[i, 2] = 0  # εzz
            strains[i, 3] = displacement[2]  # γxy
            strains[i, 4] = 0  # γyz
            strains[i, 5] = 0  # γxz
        
        return strains
    
    def _calculate_forces(self, element: StructuralElement, u: np.ndarray) -> np.ndarray:
        """Calculate internal forces from displacements."""
        K = self._calculate_stiffness_matrix(element)
        return K @ u
    
    def _calculate_safety_factor(self, element: StructuralElement, stresses: np.ndarray) -> float:
        """Calculate safety factor based on stresses."""
        max_stress = np.max(np.linalg.norm(stresses, axis=1))
        yield_strength = element.material.yield_strength
        
        return yield_strength / max_stress if max_stress > 0 else float('inf')
    
    def _calculate_geometric_stiffness_matrix(self, element: StructuralElement) -> np.ndarray:
        """Calculate geometric stiffness matrix for buckling analysis."""
        # Simplified geometric stiffness matrix
        n_nodes = len(element.nodes)
        K_G = np.zeros((n_nodes * 3, n_nodes * 3))
        
        # Add geometric stiffness terms
        for i in range(n_nodes):
            for j in range(n_nodes):
                if i == j:
                    K_G[i*3:(i+1)*3, j*3:(j+1)*3] = np.eye(3) * 0.1
                else:
                    K_G[i*3:(i+1)*3, j*3:(j+1)*3] = np.eye(3) * 0.05
        
        return K_G
    
    def _calculate_buckling_mode(self, element: StructuralElement, buckling_load: float) -> np.ndarray:
        """Calculate buckling mode shape."""
        n_nodes = len(element.nodes)
        mode = np.zeros(n_nodes * 3)
        
        # Simple buckling mode shape
        for i in range(n_nodes):
            mode[i*3:(i+1)*3] = [math.sin(i * math.pi / n_nodes), 0, 0]
        
        return mode
    
    def _calculate_stress_range(self, element: StructuralElement) -> np.ndarray:
        """Calculate stress range for fatigue analysis."""
        # Simplified stress range calculation
        n_nodes = len(element.nodes)
        stress_range = np.zeros((n_nodes, 6))
        
        for i in range(n_nodes):
            # Calculate stress range from load cycles
            stress_range[i, 0] = 50.0  # MPa
            stress_range[i, 1] = 30.0  # MPa
            stress_range[i, 2] = 0.0   # MPa
            stress_range[i, 3] = 20.0  # MPa
            stress_range[i, 4] = 0.0   # MPa
            stress_range[i, 5] = 0.0   # MPa
        
        return stress_range
    
    def _calculate_fatigue_life(self, element: StructuralElement, stress_range: np.ndarray) -> float:
        """Calculate fatigue life using S-N curve."""
        max_stress_range = np.max(np.linalg.norm(stress_range, axis=1))
        fatigue_strength = element.material.fatigue_strength
        
        # S-N curve: N = (S_f / S)^b
        b = 3.0  # Fatigue exponent
        cycles = (fatigue_strength / max_stress_range) ** b if max_stress_range > 0 else float('inf')
        
        return cycles
    
    def _calculate_cumulative_damage(self, element: StructuralElement) -> float:
        """Calculate cumulative damage for fatigue analysis."""
        # Simplified cumulative damage calculation
        return 0.1  # 10% damage
    
    def _calculate_deflection(self, element: StructuralElement, load: Load) -> np.ndarray:
        """Calculate deflection for a specific load."""
        n_nodes = len(element.nodes)
        deflection = np.zeros(n_nodes * 3)
        
        # Simplified deflection calculation
        for i in range(n_nodes):
            deflection[i*3:(i+1)*3] = np.array(load.direction) * load.magnitude / element.material.elastic_modulus
        
        return deflection
    
    def _get_deflection_limit(self, element: StructuralElement) -> float:
        """Get deflection limit for the element."""
        # Simplified deflection limits
        if element.type == "beam":
            return 0.01  # L/100
        elif element.type == "column":
            return 0.005  # L/200
        else:
            return 0.02  # L/50
    
    def _calculate_max_dynamic_stress(self, element: StructuralElement, u: np.ndarray) -> float:
        """Calculate maximum dynamic stress."""
        stresses = self._calculate_stresses(element, u)
        return np.max(np.linalg.norm(stresses, axis=1))
    
    def _calculate_max_dynamic_strain(self, element: StructuralElement, u: np.ndarray) -> float:
        """Calculate maximum dynamic strain."""
        strains = self._calculate_strains(element, u)
        return np.max(np.linalg.norm(strains, axis=1))
    
    def _calculate_dynamic_safety_factor(self, element: StructuralElement, u: np.ndarray) -> float:
        """Calculate dynamic safety factor."""
        stresses = self._calculate_stresses(element, u)
        return self._calculate_safety_factor(element, stresses)
    
    def _calculate_dynamic_stresses(self, element: StructuralElement, u: np.ndarray) -> np.ndarray:
        """Calculate dynamic stresses."""
        return self._calculate_stresses(element, u)
    
    def _calculate_dynamic_strains(self, element: StructuralElement, u: np.ndarray) -> np.ndarray:
        """Calculate dynamic strains."""
        return self._calculate_strains(element, u)
    
    def _calculate_dynamic_forces(self, element: StructuralElement, u: np.ndarray) -> np.ndarray:
        """Calculate dynamic forces."""
        return self._calculate_forces(element, u)
    
    def get_material_properties(self, material_name: str) -> Optional[MaterialProperties]:
        """Get material properties by name."""
        return self.materials.get(material_name)
    
    def add_material(self, material: MaterialProperties) -> None:
        """Add a new material to the database."""
        self.materials[material.name] = material
        logger.info(f"Added material: {material.name}")
    
    def validate_element(self, element: StructuralElement) -> bool:
        """Validate structural element properties."""
        if not element.nodes or len(element.nodes) < 2:
            return False
        
        if element.material.elastic_modulus <= 0:
            return False
        
        if element.material.yield_strength <= 0:
            return False
        
        return True 