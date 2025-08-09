"""
Stress Analyzer for Structural Analysis

This module provides comprehensive stress analysis capabilities for structural analysis:
- Stress and strain calculations
- Failure criteria analysis (von Mises, Tresca, Mohr-Coulomb)
- Safety factor calculations
- Stress concentration analysis
- Fatigue analysis
- Multi-axial stress analysis

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


class FailureCriterion(Enum):
    """Types of failure criteria."""
    VON_MISES = "von_mises"
    TRESCA = "tresca"
    MOHR_COULOMB = "mohr_coulomb"
    MAXIMUM_NORMAL = "maximum_normal"
    MAXIMUM_SHEAR = "maximum_shear"


class StressState(Enum):
    """Types of stress states."""
    UNIAXIAL = "uniaxial"
    BIAXIAL = "biaxial"
    TRIAXIAL = "triaxial"
    PLANE_STRESS = "plane_stress"
    PLANE_STRAIN = "plane_strain"


@dataclass
class StressTensor:
    """3D stress tensor representation."""
    sigma_xx: float  # Normal stress in x direction
    sigma_yy: float  # Normal stress in y direction
    sigma_zz: float  # Normal stress in z direction
    tau_xy: float    # Shear stress xy
    tau_yz: float    # Shear stress yz
    tau_xz: float    # Shear stress xz

    def to_matrix(self) -> np.ndarray:
        """Convert to 3x3 stress matrix."""
        return np.array([
            [self.sigma_xx, self.tau_xy, self.tau_xz],
            [self.tau_xy, self.sigma_yy, self.tau_yz],
            [self.tau_xz, self.tau_yz, self.sigma_zz]
        ])

    @classmethod
def from_matrix(cls, matrix: np.ndarray) -> 'StressTensor':
        """Create from 3x3 stress matrix."""
        return cls(
            sigma_xx=matrix[0, 0],
            sigma_yy=matrix[1, 1],
            sigma_zz=matrix[2, 2],
            tau_xy=matrix[0, 1],
            tau_yz=matrix[1, 2],
            tau_xz=matrix[0, 2]
        )


@dataclass
class StrainTensor:
    """3D strain tensor representation."""
    epsilon_xx: float  # Normal strain in x direction
    epsilon_yy: float  # Normal strain in y direction
    epsilon_zz: float  # Normal strain in z direction
    gamma_xy: float    # Shear strain xy
    gamma_yz: float    # Shear strain yz
    gamma_xz: float    # Shear strain xz

    def to_matrix(self) -> np.ndarray:
        """Convert to 3x3 strain matrix."""
        return np.array([
            [self.epsilon_xx, self.gamma_xy/2, self.gamma_xz/2],
            [self.gamma_xy/2, self.epsilon_yy, self.gamma_yz/2],
            [self.gamma_xz/2, self.gamma_yz/2, self.epsilon_zz]
        ])

    @classmethod
def from_matrix(cls, matrix: np.ndarray) -> 'StrainTensor':
        """Create from 3x3 strain matrix."""
        return cls(
            epsilon_xx=matrix[0, 0],
            epsilon_yy=matrix[1, 1],
            epsilon_zz=matrix[2, 2],
            gamma_xy=2*matrix[0, 1],
            gamma_yz=2*matrix[1, 2],
            gamma_xz=2*matrix[0, 2]
        )


@dataclass
class MaterialStrength:
    """Material strength properties."""
    yield_strength: float      # σy in MPa
    ultimate_strength: float   # σu in MPa
    shear_strength: float      # τy in MPa
    compressive_strength: float # σc in MPa
    tensile_strength: float    # σt in MPa
    fatigue_strength: float    # σf in MPa
    fracture_toughness: float  # KIC in MPa·√m


class StressAnalyzer:
    """Comprehensive stress analyzer for structural analysis."""

    def __init__(self):
        """Initialize the stress analyzer."""
        self.material_strengths = self._initialize_material_strengths()

    def _initialize_material_strengths(self) -> Dict[str, MaterialStrength]:
        """Initialize standard material strength properties."""
        return {
            "steel_a36": MaterialStrength(
                yield_strength=250.0,
                ultimate_strength=400.0,
                shear_strength=145.0,
                compressive_strength=250.0,
                tensile_strength=400.0,
                fatigue_strength=200.0,
                fracture_toughness=100.0
            ),
            "steel_a992": MaterialStrength(
                yield_strength=345.0,
                ultimate_strength=450.0,
                shear_strength=200.0,
                compressive_strength=345.0,
                tensile_strength=450.0,
                fatigue_strength=275.0,
                fracture_toughness=120.0
            ),
            "concrete_c30": MaterialStrength(
                yield_strength=30.0,
                ultimate_strength=30.0,
                shear_strength=3.0,
                compressive_strength=30.0,
                tensile_strength=3.0,
                fatigue_strength=15.0,
                fracture_toughness=1.0
            ),
            "aluminum_6061": MaterialStrength(
                yield_strength=240.0,
                ultimate_strength=290.0,
                shear_strength=140.0,
                compressive_strength=240.0,
                tensile_strength=290.0,
                fatigue_strength=160.0,
                fracture_toughness=30.0
            ),
            "wood_douglas_fir": MaterialStrength(
                yield_strength=40.0,
                ultimate_strength=50.0,
                shear_strength=6.0,
                compressive_strength=40.0,
                tensile_strength=50.0,
                fatigue_strength=25.0,
                fracture_toughness=2.0
            )
        }

    def calculate_principal_stresses(self, stress_tensor: StressTensor) -> Tuple[float, float, float]:
        """
        Calculate principal stresses from stress tensor.

        Args:
            stress_tensor: 3D stress tensor

        Returns:
            Tuple of principal stresses (σ1, σ2, σ3) in MPa
        """
        stress_matrix = stress_tensor.to_matrix()
        eigenvalues = np.linalg.eigvals(stress_matrix)
        principal_stresses = sorted(eigenvalues.real, reverse=True)

        logger.info(f"Principal stresses: σ1={principal_stresses[0]:.2f}, "
                   f"σ2={principal_stresses[1]:.2f}, σ3={principal_stresses[2]:.2f} MPa")
        return tuple(principal_stresses)

    def calculate_maximum_shear_stress(self, stress_tensor: StressTensor) -> float:
        """
        Calculate maximum shear stress (Tresca criterion).

        Args:
            stress_tensor: 3D stress tensor

        Returns:
            Maximum shear stress in MPa
        """
        sigma_1, sigma_2, sigma_3 = self.calculate_principal_stresses(stress_tensor)
        max_shear_stress = (sigma_1 - sigma_3) / 2.0

        logger.info(f"Maximum shear stress: {max_shear_stress:.2f} MPa")
        return max_shear_stress

    def calculate_von_mises_stress(self, stress_tensor: StressTensor) -> float:
        """
        Calculate von Mises equivalent stress.

        Args:
            stress_tensor: 3D stress tensor

        Returns:
            von Mises equivalent stress in MPa
        """
        sigma_1, sigma_2, sigma_3 = self.calculate_principal_stresses(stress_tensor)

        von_mises = math.sqrt(0.5 * ((sigma_1 - sigma_2)**2 +
                                     (sigma_2 - sigma_3)**2 +
                                     (sigma_3 - sigma_1)**2))

        logger.info(f"von Mises stress: {von_mises:.2f} MPa")
        return von_mises

    def calculate_octahedral_shear_stress(self, stress_tensor: StressTensor) -> float:
        """
        Calculate octahedral shear stress.

        Args:
            stress_tensor: 3D stress tensor

        Returns:
            Octahedral shear stress in MPa
        """
        von_mises = self.calculate_von_mises_stress(stress_tensor)
        octahedral_shear = von_mises / math.sqrt(3.0)

        logger.info(f"Octahedral shear stress: {octahedral_shear:.2f} MPa")
        return octahedral_shear

    def calculate_strain_energy_density(self, stress_tensor: StressTensor,
                                      strain_tensor: StrainTensor) -> float:
        """
        Calculate strain energy density.

        Args:
            stress_tensor: 3D stress tensor
            strain_tensor: 3D strain tensor

        Returns:
            Strain energy density in J/m³
        """
        stress_matrix = stress_tensor.to_matrix()
        strain_matrix = strain_tensor.to_matrix()

        energy_density = 0.5 * np.trace(np.dot(stress_matrix, strain_matrix)
        logger.info(f"Strain energy density: {energy_density:.2f} J/m³")
        return energy_density

    def calculate_distortion_energy_density(self, stress_tensor: StressTensor) -> float:
        """
        Calculate distortion energy density (von Mises energy).

        Args:
            stress_tensor: 3D stress tensor

        Returns:
            Distortion energy density in J/m³
        """
        von_mises = self.calculate_von_mises_stress(stress_tensor)
        distortion_energy = von_mises**2 / (2 * 200e9)  # Assuming steel modulus

        logger.info(f"Distortion energy density: {distortion_energy:.2f} J/m³")
        return distortion_energy

    def check_failure_criterion(self, stress_tensor: StressTensor,
                               material: str, criterion: FailureCriterion) -> Tuple[bool, float]:
        """
        Check if failure occurs according to specified criterion.

        Args:
            stress_tensor: 3D stress tensor
            material: Material name
            criterion: Failure criterion

        Returns:
            Tuple of (failure_occurred, safety_factor)
        """
        if material not in self.material_strengths:
            raise ValueError(f"Unknown material: {material}")

        strength = self.material_strengths[material]
        sigma_1, sigma_2, sigma_3 = self.calculate_principal_stresses(stress_tensor)

        if criterion == FailureCriterion.VON_MISES:
            equivalent_stress = self.calculate_von_mises_stress(stress_tensor)
            safety_factor = strength.yield_strength / equivalent_stress
            failure = equivalent_stress > strength.yield_strength

        elif criterion == FailureCriterion.TRESCA:
            max_shear = self.calculate_maximum_shear_stress(stress_tensor)
            safety_factor = strength.shear_strength / max_shear
            failure = max_shear > strength.shear_strength

        elif criterion == FailureCriterion.MAXIMUM_NORMAL:
            max_normal = max(abs(sigma_1), abs(sigma_2), abs(sigma_3)
            safety_factor = strength.tensile_strength / max_normal
            failure = max_normal > strength.tensile_strength

        elif criterion == FailureCriterion.MAXIMUM_SHEAR:
            max_shear = self.calculate_maximum_shear_stress(stress_tensor)
            safety_factor = strength.shear_strength / max_shear
            failure = max_shear > strength.shear_strength

        elif criterion == FailureCriterion.MOHR_COULOMB:
            # Simplified Mohr-Coulomb for cohesive soils
            cohesion = 50.0  # kPa
            friction_angle = 30.0  # degrees
            max_shear = self.calculate_maximum_shear_stress(stress_tensor)
            normal_stress = (sigma_1 + sigma_3) / 2.0
            shear_strength = cohesion + normal_stress * math.tan(math.radians(friction_angle)
            safety_factor = shear_strength / max_shear
            failure = max_shear > shear_strength

        else:
            raise ValueError(f"Unknown failure criterion: {criterion}")

        logger.info(f"Failure check ({criterion.value}): failure={failure}, "
                   f"safety_factor={safety_factor:.2f}")
        return failure, safety_factor

    def calculate_stress_concentration_factor(self, geometry_type: str,
                                           dimensions: Dict[str, float]) -> float:
        """
        Calculate stress concentration factor for common geometries.

        Args:
            geometry_type: Type of stress concentration
            dimensions: Geometric dimensions

        Returns:
            Stress concentration factor Kt
        """
        if geometry_type == "hole_in_plate":
            d = dimensions.get("hole_diameter", 0.0)
            w = dimensions.get("plate_width", 0.0)
            if d > 0 and w > 0:
                ratio = d / w
                kt = 3.0 - 3.14 * ratio + 3.667 * ratio**2 - 1.527 * ratio**3
                return max(kt, 1.0)

        elif geometry_type == "fillet":
            r = dimensions.get("radius", 0.0)
            d = dimensions.get("depth", 0.0)
            if r > 0 and d > 0:
                ratio = r / d
                kt = 1.0 + 2.0 * (1.0 - ratio)**0.5
                return kt

        elif geometry_type == "shoulder":
            r = dimensions.get("radius", 0.0)
            d = dimensions.get("smaller_diameter", 0.0)
            D = dimensions.get("larger_diameter", 0.0)
            if r > 0 and d > 0 and D > 0:
                ratio = r / d
                d_ratio = d / D
                kt = 1.0 + 0.5 * (1.0 - d_ratio) * (1.0 + 2.0 * ratio**0.5)
                return kt

        # Default value
        return 1.0

    def calculate_fatigue_stress_range(self, stress_history: List[StressTensor]) -> float:
        """
        Calculate fatigue stress range from stress history.

        Args:
            stress_history: List of stress tensors over time

        Returns:
            Stress range in MPa
        """
        if len(stress_history) < 2:
            return 0.0

        von_mises_stresses = [self.calculate_von_mises_stress(stress)
                             for stress in stress_history]

        stress_range = max(von_mises_stresses) - min(von_mises_stresses)

        logger.info(f"Fatigue stress range: {stress_range:.2f} MPa")
        return stress_range

    def calculate_fatigue_life(self, stress_range: float, material: str,
                             stress_ratio: float = 0.0) -> float:
        """
        Calculate fatigue life using S-N curve.

        Args:
            stress_range: Stress range in MPa
            material: Material name
            stress_ratio: R = σmin/σmax

        Returns:
            Fatigue life in cycles
        """
        if material not in self.material_strengths:
            raise ValueError(f"Unknown material: {material}")

        strength = self.material_strengths[material]

        # Simplified S-N curve parameters
        if material.startswith("steel"):
            # Steel S-N curve
            if stress_range <= strength.fatigue_strength:
                # High cycle fatigue
                fatigue_life = 1e6 * (strength.fatigue_strength / stress_range)**3
            else:
                # Low cycle fatigue
                fatigue_life = 1e3 * (strength.yield_strength / stress_range)**2
        else:
            # Generic S-N curve
            fatigue_life = 1e6 * (strength.fatigue_strength / stress_range)**3

        # Adjust for stress ratio
        if stress_ratio != 0.0:
            fatigue_life *= (1.0 - 0.5 * abs(stress_ratio)
        logger.info(f"Fatigue life: {fatigue_life:.0f} cycles")
        return fatigue_life

    def calculate_equivalent_stress(self, stress_tensor: StressTensor,
                                  method: str = "von_mises") -> float:
        """
        Calculate equivalent stress using various methods.

        Args:
            stress_tensor: 3D stress tensor
            method: Method for equivalent stress calculation

        Returns:
            Equivalent stress in MPa
        """
        if method == "von_mises":
            return self.calculate_von_mises_stress(stress_tensor)
        elif method == "tresca":
            return self.calculate_maximum_shear_stress(stress_tensor) * 2.0
        elif method == "maximum_principal":
            sigma_1, _, _ = self.calculate_principal_stresses(stress_tensor)
            return abs(sigma_1)
        else:
            raise ValueError(f"Unknown equivalent stress method: {method}")

    def calculate_strain_from_stress(self, stress_tensor: StressTensor,
                                   elastic_modulus: float, poisson_ratio: float) -> StrainTensor:
        """
        Calculate strain from stress using Hooke's law.'

        Args:
            stress_tensor: 3D stress tensor
            elastic_modulus: Young's modulus in MPa'
            poisson_ratio: Poisson's ratio'

        Returns:
            3D strain tensor
        """
        E = elastic_modulus
        nu = poisson_ratio

        # Hooke's law for 3D'
        epsilon_xx = (stress_tensor.sigma_xx - nu * (stress_tensor.sigma_yy + stress_tensor.sigma_zz)) / E
        epsilon_yy = (stress_tensor.sigma_yy - nu * (stress_tensor.sigma_xx + stress_tensor.sigma_zz)) / E
        epsilon_zz = (stress_tensor.sigma_zz - nu * (stress_tensor.sigma_xx + stress_tensor.sigma_yy)) / E

        gamma_xy = stress_tensor.tau_xy / (E / (2 * (1 + nu)))
        gamma_yz = stress_tensor.tau_yz / (E / (2 * (1 + nu)))
        gamma_xz = stress_tensor.tau_xz / (E / (2 * (1 + nu)))

        strain_tensor = StrainTensor(epsilon_xx, epsilon_yy, epsilon_zz, gamma_xy, gamma_yz, gamma_xz)

        logger.info(f"Calculated strain from stress using E={E:.0f} MPa, ν={nu:.2f}")
        return strain_tensor

    def get_material_strength(self, material: str) -> Optional[MaterialStrength]:
        """Get material strength properties."""
        return self.material_strengths.get(material)

    def add_material_strength(self, material: str, strength: MaterialStrength) -> None:
        """Add custom material strength properties."""
        self.material_strengths[material] = strength
        logger.info(f"Added material strength for {material}")
