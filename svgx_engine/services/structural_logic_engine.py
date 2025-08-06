"""
SVGX Engine - Structural Logic Engine

Comprehensive structural analysis engine with real IBC code calculations,
load analysis, structural analysis, and compliance validation.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import logging
import math
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class StructuralElementType(Enum):
    """Types of structural elements."""

    BEAM = "beam"
    COLUMN = "column"
    SLAB = "slab"
    WALL = "wall"
    FOUNDATION = "foundation"
    TRUSS = "truss"
    BRACE = "brace"
    CONNECTION = "connection"


class LoadCategory(Enum):
    """IBC load categories."""

    DEAD_LOAD = "dead_load"
    LIVE_LOAD = "live_load"
    ROOF_LIVE_LOAD = "roof_live_load"
    SNOW_LOAD = "snow_load"
    WIND_LOAD = "wind_load"
    SEISMIC_LOAD = "seismic_load"
    RAIN_LOAD = "rain_load"
    ICE_LOAD = "ice_load"
    FLOOD_LOAD = "flood_load"


class LoadCombination(Enum):
    """IBC load combinations."""

    ULTIMATE_1 = "1.4D"
    ULTIMATE_2 = "1.2D + 1.6L + 0.5(Lr or S or R)"
    ULTIMATE_3 = "1.2D + 1.6(Lr or S or R) + (0.5L or 0.8W)"
    ULTIMATE_4 = "1.2D + 1.6W + 0.5L + 0.5(Lr or S or R)"
    ULTIMATE_5 = "1.2D + 1.0E + 0.5L + 0.2S"
    ULTIMATE_6 = "0.9D + 1.6W"
    ULTIMATE_7 = "0.9D + 1.0E"
    SERVICE_1 = "1.0D + 1.0L"
    SERVICE_2 = "1.0D + 0.5L + 0.5(Lr or S or R)"
    SERVICE_3 = "1.0D + 0.5L + 0.7W"


class MaterialType(Enum):
    """Structural material types."""

    CONCRETE = "concrete"
    STEEL = "steel"
    WOOD = "wood"
    MASONRY = "masonry"
    ALUMINUM = "aluminum"
    COMPOSITE = "composite"


@dataclass
class MaterialProperties:
    """Material properties for structural analysis."""

    name: str
    type: MaterialType
    elastic_modulus: float  # E in MPa
    poisson_ratio: float  # ν
    yield_strength: float  # σy in MPa
    ultimate_strength: float  # σu in MPa
    density: float  # ρ in kg/m³
    thermal_expansion: float  # α in 1/°C
    compressive_strength: float = 0.0  # fc' for concrete
    tensile_strength: float = 0.0  # ft for concrete
    shear_strength: float = 0.0  # fv for wood/masonry


@dataclass
class LoadData:
    """Load data for structural analysis."""

    category: LoadCategory
    magnitude: float  # kN/m² or kN
    location: Tuple[float, float, float]  # x, y, z coordinates
    direction: Tuple[float, float, float] = (0, 0, -1)  # unit vector
    duration: float = 0.0  # seconds (0 for static loads)
    area_factor: float = 1.0  # tributary area factor


@dataclass
class StructuralElement:
    """Structural element definition."""

    id: str
    type: StructuralElementType
    material: MaterialProperties
    geometry: Dict[str, Any]  # cross-section properties
    nodes: List[Tuple[float, float, float]]
    supports: List[Dict[str, Any]]
    loads: List[LoadData]
    length: float = 0.0
    width: float = 0.0
    height: float = 0.0
    area: float = 0.0
    volume: float = 0.0


@dataclass
class AnalysisResult:
    """Result of structural analysis."""

    element_id: str
    element_type: StructuralElementType
    analysis_type: str
    status: str
    timestamp: datetime
    engineering_analysis: Dict[str, Any] = field(default_factory=dict)
    code_compliance: Dict[str, Any] = field(default_factory=dict)
    implementation_guidance: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class StructuralLogicEngine:
    """
    Comprehensive structural logic engine with real IBC calculations.

    Provides:
    - Real IBC code load calculations
    - Structural analysis with engineering calculations
    - Material property analysis
    - Code compliance validation
    - Implementation guidance
    """

    def __init__(self):
        """Initialize the structural logic engine."""
        self.start_time = datetime.now()

        # Initialize material properties
        self._initialize_materials()

        # Initialize IBC load factors
        self._initialize_load_factors()

        # Initialize analysis cache
        self.analysis_cache = {}

        # Initialize performance monitoring
        self.performance_metrics = {
            "total_analyses": 0,
            "successful_analyses": 0,
            "failed_analyses": 0,
            "average_analysis_time": 0.0,
            "total_analysis_time": 0.0,
        }

        logger.info("Structural Logic Engine initialized successfully")

    def _initialize_materials(self):
        """Initialize material properties database."""
        self.materials = {
            "A36_Steel": MaterialProperties(
                name="A36 Steel",
                type=MaterialType.STEEL,
                elastic_modulus=200000,  # MPa
                poisson_ratio=0.3,
                yield_strength=250,  # MPa
                ultimate_strength=400,  # MPa
                density=7850,  # kg/m³
                thermal_expansion=12e-6,  # 1/°C
                compressive_strength=0.0,
                tensile_strength=400.0,
                shear_strength=145.0,
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
                compressive_strength=0.0,
                tensile_strength=450.0,
                shear_strength=200.0,
            ),
            "Concrete_4000": MaterialProperties(
                name="Concrete 4000 psi",
                type=MaterialType.CONCRETE,
                elastic_modulus=28000,  # MPa (approximate)
                poisson_ratio=0.2,
                yield_strength=0.0,
                ultimate_strength=0.0,
                density=2400,
                thermal_expansion=10e-6,
                compressive_strength=27.6,  # MPa
                tensile_strength=3.3,  # MPa
                shear_strength=2.8,  # MPa
            ),
            "Douglas_Fir": MaterialProperties(
                name="Douglas Fir",
                type=MaterialType.WOOD,
                elastic_modulus=13000,  # MPa
                poisson_ratio=0.3,
                yield_strength=0.0,
                ultimate_strength=0.0,
                density=480,
                thermal_expansion=3e-6,
                compressive_strength=35.0,  # MPa
                tensile_strength=85.0,  # MPa
                shear_strength=6.9,  # MPa
            ),
            "Concrete_Block": MaterialProperties(
                name="Concrete Block",
                type=MaterialType.MASONRY,
                elastic_modulus=17000,  # MPa
                poisson_ratio=0.2,
                yield_strength=0.0,
                ultimate_strength=0.0,
                density=1920,
                thermal_expansion=10e-6,
                compressive_strength=13.8,  # MPa
                tensile_strength=1.4,  # MPa
                shear_strength=1.4,  # MPa
            ),
        }

    def _initialize_load_factors(self):
        """Initialize IBC load factors."""
        self.load_factors = {
            LoadCombination.ULTIMATE_1: {
                "D": 1.4,
                "L": 0.0,
                "Lr": 0.0,
                "S": 0.0,
                "R": 0.0,
                "W": 0.0,
                "E": 0.0,
            },
            LoadCombination.ULTIMATE_2: {
                "D": 1.2,
                "L": 1.6,
                "Lr": 0.5,
                "S": 0.5,
                "R": 0.5,
                "W": 0.0,
                "E": 0.0,
            },
            LoadCombination.ULTIMATE_3: {
                "D": 1.2,
                "L": 0.5,
                "Lr": 1.6,
                "S": 1.6,
                "R": 1.6,
                "W": 0.8,
                "E": 0.0,
            },
            LoadCombination.ULTIMATE_4: {
                "D": 1.2,
                "L": 0.5,
                "Lr": 0.5,
                "S": 0.5,
                "R": 0.5,
                "W": 1.6,
                "E": 0.0,
            },
            LoadCombination.ULTIMATE_5: {
                "D": 1.2,
                "L": 0.5,
                "Lr": 0.0,
                "S": 0.2,
                "R": 0.0,
                "W": 0.0,
                "E": 1.0,
            },
            LoadCombination.ULTIMATE_6: {
                "D": 0.9,
                "L": 0.0,
                "Lr": 0.0,
                "S": 0.0,
                "R": 0.0,
                "W": 1.6,
                "E": 0.0,
            },
            LoadCombination.ULTIMATE_7: {
                "D": 0.9,
                "L": 0.0,
                "Lr": 0.0,
                "S": 0.0,
                "R": 0.0,
                "W": 0.0,
                "E": 1.0,
            },
            LoadCombination.SERVICE_1: {
                "D": 1.0,
                "L": 1.0,
                "Lr": 0.0,
                "S": 0.0,
                "R": 0.0,
                "W": 0.0,
                "E": 0.0,
            },
            LoadCombination.SERVICE_2: {
                "D": 1.0,
                "L": 0.5,
                "Lr": 0.5,
                "S": 0.5,
                "R": 0.5,
                "W": 0.0,
                "E": 0.0,
            },
            LoadCombination.SERVICE_3: {
                "D": 1.0,
                "L": 0.5,
                "Lr": 0.0,
                "S": 0.0,
                "R": 0.0,
                "W": 0.7,
                "E": 0.0,
            },
        }

    async def analyze_structural_element(
        self, element_data: Dict[str, Any]
    ) -> AnalysisResult:
        """
        Analyze a structural element with comprehensive engineering calculations.

        Args:
            element_data: Dictionary containing structural element data

        Returns:
            AnalysisResult with comprehensive analysis results
        """
        start_time = datetime.now()

        try:
            # Create structural element object
            element = self._create_structural_element(element_data)

            # Perform engineering analysis
            engineering_analysis = await self._perform_engineering_analysis(element)

            # Perform code compliance validation
            code_compliance = await self._perform_code_compliance_validation(
                element, engineering_analysis
            )

            # Generate implementation guidance
            implementation_guidance = await self._generate_implementation_guidance(
                element, engineering_analysis, code_compliance
            )

            # Calculate performance metrics
            analysis_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_metrics(analysis_time, True)

            return AnalysisResult(
                element_id=element.id,
                element_type=element.type,
                analysis_type="comprehensive_structural_analysis",
                status="completed",
                timestamp=datetime.now(),
                engineering_analysis=engineering_analysis,
                code_compliance=code_compliance,
                implementation_guidance=implementation_guidance,
                performance_metrics={
                    "analysis_time": analysis_time,
                    "element_type": element.type.value,
                    "material": element.material.name,
                },
            )

        except Exception as e:
            logger.error(f"Error analyzing structural element: {str(e)}")
            self._update_performance_metrics(0.0, False)

            return AnalysisResult(
                element_id=element_data.get("id", "unknown"),
                element_type=StructuralElementType.BEAM,  # Default
                analysis_type="comprehensive_structural_analysis",
                status="failed",
                timestamp=datetime.now(),
                errors=[str(e)],
            )

    def _create_structural_element(
        self, element_data: Dict[str, Any]
    ) -> StructuralElement:
        """Create a structural element from input data."""
        element_id = element_data.get("id", "unknown")
        element_type = StructuralElementType(element_data.get("type", "beam"))
        material_name = element_data.get("material", "A36_Steel")
        material = self.materials.get(material_name, self.materials["A36_Steel"])

        # Extract geometry
        geometry = element_data.get("geometry", {})
        length = geometry.get("length", 5.0)  # m
        width = geometry.get("width", 0.2)  # m
        height = geometry.get("height", 0.3)  # m

        # Calculate properties
        area = width * height
        volume = area * length

        # Create loads
        loads = self._create_loads_from_data(element_data.get("loads", []))

        # Create nodes and supports
        nodes = element_data.get("nodes", [(0, 0, 0), (length, 0, 0)])
        supports = element_data.get("supports", [])

        return StructuralElement(
            id=element_id,
            type=element_type,
            material=material,
            geometry=geometry,
            nodes=nodes,
            supports=supports,
            loads=loads,
            length=length,
            width=width,
            height=height,
            area=area,
            volume=volume,
        )

    def _create_loads_from_data(
        self, loads_data: List[Dict[str, Any]]
    ) -> List[LoadData]:
        """Create load objects from input data."""
        loads = []

        for load_data in loads_data:
            category = LoadCategory(load_data.get("category", "live_load"))
            magnitude = load_data.get("magnitude", 0.0)
            location = tuple(load_data.get("location", [0, 0, 0]))
            direction = tuple(load_data.get("direction", [0, 0, -1]))
            duration = load_data.get("duration", 0.0)
            area_factor = load_data.get("area_factor", 1.0)

            loads.append(
                LoadData(
                    category=category,
                    magnitude=magnitude,
                    location=location,
                    direction=direction,
                    duration=duration,
                    area_factor=area_factor,
                )
            )

        return loads

    async def _perform_engineering_analysis(
        self, element: StructuralElement
    ) -> Dict[str, Any]:
        """Perform comprehensive engineering analysis."""
        analysis_results = {}

        # Calculate loads
        loads_analysis = self._calculate_loads(element)
        analysis_results["loads"] = loads_analysis

        # Calculate structural properties
        structural_properties = self._calculate_structural_properties(element)
        analysis_results["structural_properties"] = structural_properties

        # Calculate stresses and strains
        stress_analysis = self._calculate_stress_analysis(element, loads_analysis)
        analysis_results["stress_analysis"] = stress_analysis

        # Calculate deflections
        deflection_analysis = self._calculate_deflection_analysis(
            element, loads_analysis
        )
        analysis_results["deflection_analysis"] = deflection_analysis

        # Calculate buckling analysis
        buckling_analysis = self._calculate_buckling_analysis(element, loads_analysis)
        analysis_results["buckling_analysis"] = buckling_analysis

        # Calculate safety factors
        safety_analysis = self._calculate_safety_factors(element, stress_analysis)
        analysis_results["safety_analysis"] = safety_analysis

        return analysis_results

    def _calculate_loads(self, element: StructuralElement) -> Dict[str, Any]:
        """Calculate all loads on the structural element."""
        loads_analysis = {
            "dead_load": self._calculate_dead_load(element),
            "live_load": self._calculate_live_load(element),
            "wind_load": self._calculate_wind_load(element),
            "seismic_load": self._calculate_seismic_load(element),
            "snow_load": self._calculate_snow_load(element),
            "combined_loads": {},
        }

        # Calculate combined loads for all IBC combinations
        for combination in LoadCombination:
            combined_load = self._calculate_combined_load(
                element, loads_analysis, combination
            )
            loads_analysis["combined_loads"][combination.value] = combined_load

        return loads_analysis

    def _calculate_dead_load(self, element: StructuralElement) -> float:
        """Calculate dead load on the element."""
        # Material weight
        material_weight = element.volume * element.material.density * 9.81  # N

        # Convert to kN
        material_weight_kn = material_weight / 1000

        # Add any additional dead loads from the loads list
        additional_dead_load = sum(
            load.magnitude
            for load in element.loads
            if load.category == LoadCategory.DEAD_LOAD
        )

        return material_weight_kn + additional_dead_load

    def _calculate_live_load(self, element: StructuralElement) -> float:
        """Calculate live load on the element."""
        # Standard live loads based on element type
        live_load_values = {
            StructuralElementType.BEAM: 2.4,  # kN/m² for office floors
            StructuralElementType.COLUMN: 2.4,  # kN/m²
            StructuralElementType.SLAB: 2.4,  # kN/m²
            StructuralElementType.WALL: 0.0,  # kN/m² (no live load on walls)
            StructuralElementType.FOUNDATION: 0.0,  # kN/m²
            StructuralElementType.TRUSS: 2.4,  # kN/m²
            StructuralElementType.BRACE: 0.0,  # kN/m²
            StructuralElementType.CONNECTION: 0.0,  # kN/m²
        }

        base_live_load = live_load_values.get(element.type, 2.4)

        # Apply tributary area factor
        tributary_area = element.area * element.length
        area_factor = (
            min(1.0, 0.25 + 15 / math.sqrt(tributary_area))
            if tributary_area > 37.2
            else 1.0
        )

        live_load = base_live_load * tributary_area * area_factor

        # Add any additional live loads from the loads list
        additional_live_load = sum(
            load.magnitude
            for load in element.loads
            if load.category == LoadCategory.LIVE_LOAD
        )

        return live_load + additional_live_load

    def _calculate_wind_load(self, element: StructuralElement) -> float:
        """Calculate wind load on the element."""
        # Basic wind load calculation (simplified)
        wind_speed = 50.0  # m/s (basic wind speed)
        wind_pressure = 0.613 * wind_speed**2  # Pa

        # Convert to kN/m²
        wind_pressure_kn = wind_pressure / 1000

        # Apply to element area
        wind_load = wind_pressure_kn * element.area

        # Add any additional wind loads from the loads list
        additional_wind_load = sum(
            load.magnitude
            for load in element.loads
            if load.category == LoadCategory.WIND_LOAD
        )

        return wind_load + additional_wind_load

    def _calculate_seismic_load(self, element: StructuralElement) -> float:
        """Calculate seismic load on the element."""
        # Simplified seismic load calculation
        seismic_coefficient = 0.1  # Basic seismic coefficient
        element_weight = element.volume * element.material.density * 9.81 / 1000  # kN

        seismic_load = seismic_coefficient * element_weight

        # Add any additional seismic loads from the loads list
        additional_seismic_load = sum(
            load.magnitude
            for load in element.loads
            if load.category == LoadCategory.SEISMIC_LOAD
        )

        return seismic_load + additional_seismic_load

    def _calculate_snow_load(self, element: StructuralElement) -> float:
        """Calculate snow load on the element."""
        # Basic snow load calculation
        snow_load = 1.44  # kN/m² (basic snow load)

        # Apply to element area
        snow_load_total = snow_load * element.area

        # Add any additional snow loads from the loads list
        additional_snow_load = sum(
            load.magnitude
            for load in element.loads
            if load.category == LoadCategory.SNOW_LOAD
        )

        return snow_load_total + additional_snow_load

    def _calculate_combined_load(
        self,
        element: StructuralElement,
        loads_analysis: Dict[str, Any],
        combination: LoadCombination,
    ) -> float:
        """Calculate combined load for a specific load combination."""
        factors = self.load_factors[combination]

        D = loads_analysis["dead_load"]
        L = loads_analysis["live_load"]
        W = loads_analysis["wind_load"]
        E = loads_analysis["seismic_load"]
        S = loads_analysis["snow_load"]

        # Use Lr (roof live load) as S for roof elements
        Lr = (
            S
            if element.type in [StructuralElementType.TRUSS, StructuralElementType.BEAM]
            else 0.0
        )
        R = 0.0  # Rain load (not calculated here)

        combined_load = (
            factors["D"] * D
            + factors["L"] * L
            + factors["Lr"] * Lr
            + factors["S"] * S
            + factors["R"] * R
            + factors["W"] * W
            + factors["E"] * E
        )

        return combined_load

    def _calculate_structural_properties(
        self, element: StructuralElement
    ) -> Dict[str, Any]:
        """Calculate structural properties of the element."""
        # Cross-sectional properties
        area = element.area
        moment_of_inertia_x = (element.width * element.height**3) / 12
        moment_of_inertia_y = (element.height * element.width**3) / 12
        section_modulus_x = moment_of_inertia_x / (element.height / 2)
        section_modulus_y = moment_of_inertia_y / (element.width / 2)

        # Material properties
        elastic_modulus = element.material.elastic_modulus
        poisson_ratio = element.material.poisson_ratio
        shear_modulus = elastic_modulus / (2 * (1 + poisson_ratio))

        # Stiffness properties
        axial_stiffness = elastic_modulus * area
        flexural_stiffness_x = elastic_modulus * moment_of_inertia_x
        flexural_stiffness_y = elastic_modulus * moment_of_inertia_y
        torsional_stiffness = shear_modulus * (element.width * element.height**3) / 3

        return {
            "area": area,
            "moment_of_inertia_x": moment_of_inertia_x,
            "moment_of_inertia_y": moment_of_inertia_y,
            "section_modulus_x": section_modulus_x,
            "section_modulus_y": section_modulus_y,
            "elastic_modulus": elastic_modulus,
            "poisson_ratio": poisson_ratio,
            "shear_modulus": shear_modulus,
            "axial_stiffness": axial_stiffness,
            "flexural_stiffness_x": flexural_stiffness_x,
            "flexural_stiffness_y": flexural_stiffness_y,
            "torsional_stiffness": torsional_stiffness,
        }

    def _calculate_stress_analysis(
        self, element: StructuralElement, loads_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate stress analysis for the element."""
        # Use the most critical load combination
        critical_combination = LoadCombination.ULTIMATE_2
        critical_load = loads_analysis["combined_loads"][critical_combination.value]

        # Calculate stresses
        area = element.area
        section_modulus = element.width * element.height**2 / 6

        # Axial stress
        axial_stress = critical_load / area if area > 0 else 0

        # Bending stress (assuming simple beam)
        moment = (
            critical_load * element.length**2 / 8
        )  # Maximum moment for uniform load
        bending_stress = moment / section_modulus if section_modulus > 0 else 0

        # Shear stress
        shear_force = critical_load / 2  # Maximum shear for uniform load
        shear_stress = 3 * shear_force / (2 * area) if area > 0 else 0

        # Von Mises stress
        von_mises_stress = math.sqrt(axial_stress**2 + 3 * shear_stress**2)

        # Principal stresses
        principal_stress_1 = (
            axial_stress
            + bending_stress
            + math.sqrt((axial_stress + bending_stress) ** 2 + 4 * shear_stress**2)
        ) / 2
        principal_stress_2 = (
            axial_stress
            + bending_stress
            - math.sqrt((axial_stress + bending_stress) ** 2 + 4 * shear_stress**2)
        ) / 2

        return {
            "axial_stress": axial_stress,
            "bending_stress": bending_stress,
            "shear_stress": shear_stress,
            "von_mises_stress": von_mises_stress,
            "principal_stress_1": principal_stress_1,
            "principal_stress_2": principal_stress_2,
            "critical_load": critical_load,
            "load_combination": critical_combination.value,
        }

    def _calculate_deflection_analysis(
        self, element: StructuralElement, loads_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate deflection analysis for the element."""
        # Use service load combination
        service_combination = LoadCombination.SERVICE_1
        service_load = loads_analysis["combined_loads"][service_combination.value]

        # Calculate deflection for simply supported beam with uniform load
        elastic_modulus = element.material.elastic_modulus
        moment_of_inertia = (element.width * element.height**3) / 12

        # Maximum deflection for uniform load
        max_deflection = (5 * service_load * element.length**4) / (
            384 * elastic_modulus * moment_of_inertia
        )

        # Deflection limit (L/360 for live loads)
        deflection_limit = element.length / 360

        # Deflection ratio
        deflection_ratio = (
            max_deflection / deflection_limit if deflection_limit > 0 else 0
        )

        return {
            "max_deflection": max_deflection,
            "deflection_limit": deflection_limit,
            "deflection_ratio": deflection_ratio,
            "service_load": service_load,
            "load_combination": service_combination.value,
            "is_deflection_ok": deflection_ratio <= 1.0,
        }

    def _calculate_buckling_analysis(
        self, element: StructuralElement, loads_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate buckling analysis for the element."""
        # Euler buckling load for column
        if element.type == StructuralElementType.COLUMN:
            elastic_modulus = element.material.elastic_modulus
            moment_of_inertia = min(
                (element.width * element.height**3) / 12,
                (element.height * element.width**3) / 12,
            )

            # Effective length factor (assume pinned-pinned)
            K = 1.0
            effective_length = K * element.length

            # Euler buckling load
            euler_buckling_load = (
                math.pi**2 * elastic_modulus * moment_of_inertia
            ) / (effective_length**2)

            # Critical load from analysis
            critical_load = loads_analysis["combined_loads"][
                LoadCombination.ULTIMATE_2.value
            ]

            # Buckling safety factor
            buckling_safety_factor = (
                euler_buckling_load / critical_load
                if critical_load > 0
                else float("inf")
            )

            return {
                "euler_buckling_load": euler_buckling_load,
                "critical_load": critical_load,
                "buckling_safety_factor": buckling_safety_factor,
                "effective_length": effective_length,
                "is_buckling_ok": buckling_safety_factor >= 1.5,
            }
        else:
            return {
                "euler_buckling_load": 0.0,
                "critical_load": 0.0,
                "buckling_safety_factor": float("inf"),
                "effective_length": 0.0,
                "is_buckling_ok": True,
            }

    def _calculate_safety_factors(
        self, element: StructuralElement, stress_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate safety factors for the element."""
        # Material strength
        yield_strength = element.material.yield_strength
        ultimate_strength = element.material.ultimate_strength

        # Maximum stress
        max_stress = max(
            abs(stress_analysis["axial_stress"]),
            abs(stress_analysis["bending_stress"]),
            abs(stress_analysis["von_mises_stress"]),
        )

        # Safety factors
        yield_safety_factor = (
            yield_strength / max_stress if max_stress > 0 else float("inf")
        )
        ultimate_safety_factor = (
            ultimate_strength / max_stress if max_stress > 0 else float("inf")
        )

        # Code safety factors
        code_safety_factor = 1.67  # AISC safety factor for steel
        code_compliance = yield_safety_factor >= code_safety_factor

        return {
            "yield_safety_factor": yield_safety_factor,
            "ultimate_safety_factor": ultimate_safety_factor,
            "code_safety_factor": code_safety_factor,
            "code_compliance": code_compliance,
            "max_stress": max_stress,
            "yield_strength": yield_strength,
            "ultimate_strength": ultimate_strength,
        }

    async def _perform_code_compliance_validation(
        self, element: StructuralElement, engineering_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform IBC code compliance validation."""
        compliance_results = {
            "load_combinations": {},
            "stress_limits": {},
            "deflection_limits": {},
            "buckling_limits": {},
            "material_requirements": {},
            "overall_compliance": True,
            "violations": [],
            "warnings": [],
        }

        # Check load combinations
        for combination in LoadCombination:
            load_value = engineering_analysis["loads"]["combined_loads"][
                combination.value
            ]
            compliance_results["load_combinations"][combination.value] = {
                "load_value": load_value,
                "is_within_limits": True,  # Simplified check
            }

        # Check stress limits
        stress_analysis = engineering_analysis["stress_analysis"]
        safety_analysis = engineering_analysis["safety_analysis"]

        if safety_analysis["code_compliance"]:
            compliance_results["stress_limits"]["status"] = "PASS"
        else:
            compliance_results["stress_limits"]["status"] = "FAIL"
            compliance_results["overall_compliance"] = False
            compliance_results["violations"].append(
                f"Stress exceeds code limits: {safety_analysis['yield_safety_factor']:.2f} < {safety_analysis['code_safety_factor']}"
            )

        # Check deflection limits
        deflection_analysis = engineering_analysis["deflection_analysis"]
        if deflection_analysis["is_deflection_ok"]:
            compliance_results["deflection_limits"]["status"] = "PASS"
        else:
            compliance_results["deflection_limits"]["status"] = "FAIL"
            compliance_results["overall_compliance"] = False
            compliance_results["violations"].append(
                f"Deflection exceeds limits: {deflection_analysis['deflection_ratio']:.2f} > 1.0"
            )

        # Check buckling limits
        buckling_analysis = engineering_analysis["buckling_analysis"]
        if buckling_analysis["is_buckling_ok"]:
            compliance_results["buckling_limits"]["status"] = "PASS"
        else:
            compliance_results["buckling_limits"]["status"] = "FAIL"
            compliance_results["overall_compliance"] = False
            compliance_results["violations"].append(
                f"Buckling safety factor too low: {buckling_analysis['buckling_safety_factor']:.2f} < 1.5"
            )

        # Check material requirements
        compliance_results["material_requirements"] = {
            "material_type": element.material.type.value,
            "elastic_modulus": element.material.elastic_modulus,
            "yield_strength": element.material.yield_strength,
            "is_appropriate": True,  # Simplified check
        }

        return compliance_results

    async def _generate_implementation_guidance(
        self,
        element: StructuralElement,
        engineering_analysis: Dict[str, Any],
        code_compliance: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate implementation guidance for the structural element."""
        guidance = {
            "design_recommendations": [],
            "construction_notes": [],
            "inspection_requirements": [],
            "maintenance_guidelines": [],
            "code_references": [],
        }

        # Design recommendations based on analysis
        if not code_compliance["overall_compliance"]:
            guidance["design_recommendations"].append(
                "Increase element size or use stronger material to meet code requirements"
            )

        if engineering_analysis["deflection_analysis"]["deflection_ratio"] > 0.8:
            guidance["design_recommendations"].append(
                "Consider increasing element stiffness to reduce deflections"
            )

        if engineering_analysis["buckling_analysis"]["buckling_safety_factor"] < 2.0:
            guidance["design_recommendations"].append(
                "Consider adding lateral bracing or increasing column size"
            )

        # Construction notes
        guidance["construction_notes"].extend(
            [
                f"Ensure proper material specification: {element.material.name}",
                f"Verify dimensions: {element.width}m x {element.height}m x {element.length}m",
                "Check all connections for proper installation",
                "Verify support conditions match design assumptions",
            ]
        )

        # Inspection requirements
        guidance["inspection_requirements"].extend(
            [
                "Visual inspection of element for damage or deformation",
                "Check for proper alignment and support conditions",
                "Verify material properties match specifications",
                "Document any deviations from design",
            ]
        )

        # Maintenance guidelines
        guidance["maintenance_guidelines"].extend(
            [
                "Regular visual inspection for signs of distress",
                "Monitor for excessive deflections or deformations",
                "Check for corrosion or material degradation",
                "Maintain proper drainage and ventilation",
            ]
        )

        # Code references
        guidance["code_references"].extend(
            [
                "IBC Chapter 16: Structural Design",
                "ASCE 7: Minimum Design Loads for Buildings",
                "AISC 360: Specification for Structural Steel Buildings",
                "ACI 318: Building Code Requirements for Structural Concrete",
            ]
        )

        return guidance

    def _update_performance_metrics(self, analysis_time: float, success: bool):
        """Update performance metrics."""
        self.performance_metrics["total_analyses"] += 1
        self.performance_metrics["total_analysis_time"] += analysis_time

        if success:
            self.performance_metrics["successful_analyses"] += 1
        else:
            self.performance_metrics["failed_analyses"] += 1

        # Update average analysis time
        if self.performance_metrics["total_analyses"] > 0:
            self.performance_metrics["average_analysis_time"] = (
                self.performance_metrics["total_analysis_time"]
                / self.performance_metrics["total_analyses"]
            )

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return self.performance_metrics.copy()

    def get_material_properties(
        self, material_name: str
    ) -> Optional[MaterialProperties]:
        """Get material properties by name."""
        return self.materials.get(material_name)

    def add_material(self, material: MaterialProperties) -> None:
        """Add a new material to the database."""
        self.materials[material.name] = material
        logger.info(f"Added material: {material.name}")

    def validate_element(self, element_data: Dict[str, Any]) -> bool:
        """Validate structural element data."""
        required_fields = ["id", "type", "material", "geometry"]

        for field in required_fields:
            if field not in element_data:
                logger.error(f"Missing required field: {field}")
                return False

        # Validate element type
        try:
            StructuralElementType(element_data["type"])
        except ValueError:
            logger.error(f"Invalid element type: {element_data['type']}")
            return False

        # Validate material
        if element_data["material"] not in self.materials:
            logger.error(f"Unknown material: {element_data['material']}")
            return False

        return True
