"""
Comprehensive tests for Structural Logic Engine

Tests all aspects of structural analysis including:
- IBC load calculations
- Structural analysis with engineering calculations
- Material property analysis
- Code compliance validation
- Implementation guidance

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any

# Import the structural logic engine
import sys
import os

sys.path.append(".")

from svgx_engine.services.structural_logic_engine import (
    StructuralLogicEngine,
    StructuralElementType,
    LoadCategory,
    LoadCombination,
    MaterialType,
    MaterialProperties,
    LoadData,
    StructuralElement,
    AnalysisResult,
)


class TestStructuralLogicEngine:
    """Comprehensive test suite for Structural Logic Engine."""

    @pytest.fixture
    def structural_engine(self):
        """Create a structural logic engine instance."""
        return StructuralLogicEngine()

    @pytest.fixture
    def sample_beam_data(self):
        """Sample beam data for testing."""
        return {
            "id": "test_beam_001",
            "type": "beam",
            "material": "A36_Steel",
            "geometry": {"length": 6.0, "width": 0.2, "height": 0.3},  # m  # m  # m
            "nodes": [(0, 0, 0), (6, 0, 0)],
            "supports": [
                {"type": "pinned", "location": (0, 0, 0)},
                {"type": "pinned", "location": (6, 0, 0)},
            ],
            "loads": [
                {
                    "category": "live_load",
                    "magnitude": 2.4,  # kN/m²
                    "location": [3, 0, 0],
                    "direction": [0, 0, -1],
                    "duration": 0.0,
                    "area_factor": 1.0,
                }
            ],
        }

    @pytest.fixture
    def sample_column_data(self):
        """Sample column data for testing."""
        return {
            "id": "test_column_001",
            "type": "column",
            "material": "A992_Steel",
            "geometry": {"length": 3.0, "width": 0.3, "height": 0.3},  # m  # m  # m
            "nodes": [(0, 0, 0), (0, 0, 3)],
            "supports": [
                {"type": "fixed", "location": (0, 0, 0)},
                {"type": "pinned", "location": (0, 0, 3)},
            ],
            "loads": [
                {
                    "category": "dead_load",
                    "magnitude": 50.0,  # kN
                    "location": [0, 0, 1.5],
                    "direction": [0, 0, -1],
                    "duration": 0.0,
                    "area_factor": 1.0,
                }
            ],
        }

    @pytest.fixture
    def sample_concrete_slab_data(self):
        """Sample concrete slab data for testing."""
        return {
            "id": "test_slab_001",
            "type": "slab",
            "material": "Concrete_4000",
            "geometry": {"length": 5.0, "width": 4.0, "height": 0.2},  # m  # m  # m
            "nodes": [(0, 0, 0), (5, 0, 0), (5, 4, 0), (0, 4, 0)],
            "supports": [
                {"type": "fixed", "location": (0, 0, 0)},
                {"type": "fixed", "location": (5, 0, 0)},
                {"type": "fixed", "location": (5, 4, 0)},
                {"type": "fixed", "location": (0, 4, 0)},
            ],
            "loads": [
                {
                    "category": "live_load",
                    "magnitude": 2.4,  # kN/m²
                    "location": [2.5, 2, 0],
                    "direction": [0, 0, -1],
                    "duration": 0.0,
                    "area_factor": 1.0,
                }
            ],
        }

    def test_initialization(self, structural_engine):
        """Test structural logic engine initialization."""
        assert structural_engine is not None
        assert hasattr(structural_engine, "materials")
        assert hasattr(structural_engine, "load_factors")
        assert hasattr(structural_engine, "analysis_cache")
        assert hasattr(structural_engine, "performance_metrics")

        # Check that materials are initialized
        assert "A36_Steel" in structural_engine.materials
        assert "A992_Steel" in structural_engine.materials
        assert "Concrete_4000" in structural_engine.materials
        assert "Douglas_Fir" in structural_engine.materials
        assert "Concrete_Block" in structural_engine.materials

        # Check that load factors are initialized
        assert LoadCombination.ULTIMATE_1 in structural_engine.load_factors
        assert LoadCombination.ULTIMATE_2 in structural_engine.load_factors
        assert LoadCombination.SERVICE_1 in structural_engine.load_factors

    def test_material_properties(self, structural_engine):
        """Test material properties database."""
        # Test A36 Steel properties
        a36_steel = structural_engine.materials["A36_Steel"]
        assert a36_steel.name == "A36 Steel"
        assert a36_steel.type == MaterialType.STEEL
        assert a36_steel.elastic_modulus == 200000  # MPa
        assert a36_steel.yield_strength == 250  # MPa
        assert a36_steel.density == 7850  # kg/m³

        # Test Concrete properties
        concrete = structural_engine.materials["Concrete_4000"]
        assert concrete.name == "Concrete 4000 psi"
        assert concrete.type == MaterialType.CONCRETE
        assert concrete.compressive_strength == 27.6  # MPa
        assert concrete.tensile_strength == 3.3  # MPa

    def test_load_factors(self, structural_engine):
        """Test IBC load factors."""
        # Test Ultimate Load Combination 2
        factors = structural_engine.load_factors[LoadCombination.ULTIMATE_2]
        assert factors["D"] == 1.2
        assert factors["L"] == 1.6
        assert factors["Lr"] == 0.5
        assert factors["S"] == 0.5
        assert factors["W"] == 0.0
        assert factors["E"] == 0.0

        # Test Service Load Combination 1
        factors = structural_engine.load_factors[LoadCombination.SERVICE_1]
        assert factors["D"] == 1.0
        assert factors["L"] == 1.0
        assert factors["W"] == 0.0
        assert factors["E"] == 0.0

    def test_create_structural_element(self, structural_engine, sample_beam_data):
        """Test creating structural element from data."""
        element = structural_engine._create_structural_element(sample_beam_data)

        assert element.id == "test_beam_001"
        assert element.type == StructuralElementType.BEAM
        assert element.material.name == "A36 Steel"
        assert element.length == 6.0
        assert element.width == 0.2
        assert element.height == 0.3
        assert element.area == 0.06  # 0.2 * 0.3
        assert element.volume == 0.36  # 0.06 * 6.0
        assert len(element.loads) == 1
        assert element.loads[0].category == LoadCategory.LIVE_LOAD
        assert element.loads[0].magnitude == 2.4

    def test_calculate_dead_load(self, structural_engine, sample_beam_data):
        """Test dead load calculation."""
        element = structural_engine._create_structural_element(sample_beam_data)
        dead_load = structural_engine._calculate_dead_load(element)

        # Expected dead load calculation:
        # Volume = 0.36 m³
        # Density = 7850 kg/m³
        # Weight = 0.36 * 7850 * 9.81 = 27,777 N = 27.78 kN
        expected_dead_load = 0.36 * 7850 * 9.81 / 1000

        assert abs(dead_load - expected_dead_load) < 0.1

    def test_calculate_live_load(self, structural_engine, sample_beam_data):
        """Test live load calculation."""
        element = structural_engine._create_structural_element(sample_beam_data)
        live_load = structural_engine._calculate_live_load(element)

        # Expected live load calculation:
        # Tributary area = 0.06 * 6.0 = 0.36 m²
        # Base live load = 2.4 kN/m²
        # Area factor = 1.0 (since tributary area < 37.2 m²)
        # Live load = 2.4 * 0.36 * 1.0 = 0.864 kN
        # Plus additional live load from loads list = 2.4 kN/m² * 0.06 m² = 0.144 kN
        # Total = 0.864 + 0.144 = 1.008 kN

        assert live_load > 0
        assert live_load < 2.0  # Should be reasonable

    def test_calculate_wind_load(self, structural_engine, sample_beam_data):
        """Test wind load calculation."""
        element = structural_engine._create_structural_element(sample_beam_data)
        wind_load = structural_engine._calculate_wind_load(element)

        # Expected wind load calculation:
        # Wind speed = 50 m/s
        # Wind pressure = 0.613 * 50² = 1,532.5 Pa = 1.53 kN/m²
        # Wind load = 1.53 * 0.06 = 0.092 kN

        assert wind_load > 0
        assert wind_load < 1.0  # Should be reasonable

    def test_calculate_combined_loads(self, structural_engine, sample_beam_data):
        """Test combined load calculations."""
        element = structural_engine._create_structural_element(sample_beam_data)
        loads_analysis = structural_engine._calculate_loads(element)

        # Check that all load combinations are calculated
        assert "combined_loads" in loads_analysis
        assert LoadCombination.ULTIMATE_1.value in loads_analysis["combined_loads"]
        assert LoadCombination.ULTIMATE_2.value in loads_analysis["combined_loads"]
        assert LoadCombination.SERVICE_1.value in loads_analysis["combined_loads"]

        # Check that combined loads are positive
        for combination, load_value in loads_analysis["combined_loads"].items():
            assert load_value > 0

    def test_calculate_structural_properties(self, structural_engine, sample_beam_data):
        """Test structural properties calculation."""
        element = structural_engine._create_structural_element(sample_beam_data)
        properties = structural_engine._calculate_structural_properties(element)

        # Check cross-sectional properties
        assert properties["area"] == 0.06  # 0.2 * 0.3
        assert properties["moment_of_inertia_x"] == (0.2 * 0.3**3) / 12
        assert properties["moment_of_inertia_y"] == (0.3 * 0.2**3) / 12

        # Check material properties
        assert properties["elastic_modulus"] == 200000  # MPa
        assert properties["poisson_ratio"] == 0.3

        # Check stiffness properties
        assert properties["axial_stiffness"] > 0
        assert properties["flexural_stiffness_x"] > 0
        assert properties["flexural_stiffness_y"] > 0

    def test_calculate_stress_analysis(self, structural_engine, sample_beam_data):
        """Test stress analysis calculation."""
        element = structural_engine._create_structural_element(sample_beam_data)
        loads_analysis = structural_engine._calculate_loads(element)
        stress_analysis = structural_engine._calculate_stress_analysis(
            element, loads_analysis
        )

        # Check that all stress components are calculated
        assert "axial_stress" in stress_analysis
        assert "bending_stress" in stress_analysis
        assert "shear_stress" in stress_analysis
        assert "von_mises_stress" in stress_analysis
        assert "principal_stress_1" in stress_analysis
        assert "principal_stress_2" in stress_analysis

        # Check that stresses are reasonable (should be positive for this case)
        assert stress_analysis["axial_stress"] >= 0
        assert stress_analysis["bending_stress"] >= 0
        assert stress_analysis["shear_stress"] >= 0
        assert stress_analysis["von_mises_stress"] >= 0

    def test_calculate_deflection_analysis(self, structural_engine, sample_beam_data):
        """Test deflection analysis calculation."""
        element = structural_engine._create_structural_element(sample_beam_data)
        loads_analysis = structural_engine._calculate_loads(element)
        deflection_analysis = structural_engine._calculate_deflection_analysis(
            element, loads_analysis
        )

        # Check that deflection analysis is complete
        assert "max_deflection" in deflection_analysis
        assert "deflection_limit" in deflection_analysis
        assert "deflection_ratio" in deflection_analysis
        assert "is_deflection_ok" in deflection_analysis

        # Check that deflection limit is reasonable (L/360)
        expected_limit = 6.0 / 360  # 6m / 360
        assert abs(deflection_analysis["deflection_limit"] - expected_limit) < 0.001

        # Check that deflection ratio is reasonable
        assert deflection_analysis["deflection_ratio"] >= 0

    def test_calculate_buckling_analysis(self, structural_engine, sample_column_data):
        """Test buckling analysis calculation."""
        element = structural_engine._create_structural_element(sample_column_data)
        loads_analysis = structural_engine._calculate_loads(element)
        buckling_analysis = structural_engine._calculate_buckling_analysis(
            element, loads_analysis
        )

        # Check that buckling analysis is complete
        assert "euler_buckling_load" in buckling_analysis
        assert "critical_load" in buckling_analysis
        assert "buckling_safety_factor" in buckling_analysis
        assert "effective_length" in buckling_analysis
        assert "is_buckling_ok" in buckling_analysis

        # For a column, buckling analysis should be performed
        assert buckling_analysis["euler_buckling_load"] > 0
        assert buckling_analysis["critical_load"] > 0
        assert buckling_analysis["buckling_safety_factor"] > 0

    def test_calculate_safety_factors(self, structural_engine, sample_beam_data):
        """Test safety factor calculation."""
        element = structural_engine._create_structural_element(sample_beam_data)
        loads_analysis = structural_engine._calculate_loads(element)
        stress_analysis = structural_engine._calculate_stress_analysis(
            element, loads_analysis
        )
        safety_analysis = structural_engine._calculate_safety_factors(
            element, stress_analysis
        )

        # Check that safety analysis is complete
        assert "yield_safety_factor" in safety_analysis
        assert "ultimate_safety_factor" in safety_analysis
        assert "code_safety_factor" in safety_analysis
        assert "code_compliance" in safety_analysis
        assert "max_stress" in safety_analysis

        # Check that safety factors are reasonable
        assert safety_analysis["yield_safety_factor"] > 0
        assert safety_analysis["ultimate_safety_factor"] > 0
        assert safety_analysis["code_safety_factor"] == 1.67  # AISC safety factor
        assert safety_analysis["max_stress"] > 0

    @pytest.mark.asyncio
    async def test_analyze_structural_element_beam(
        self, structural_engine, sample_beam_data
    ):
        """Test comprehensive structural analysis for beam."""
        result = await structural_engine.analyze_structural_element(sample_beam_data)

        # Check result structure
        assert isinstance(result, AnalysisResult)
        assert result.element_id == "test_beam_001"
        assert result.element_type == StructuralElementType.BEAM
        assert result.status == "completed"
        assert result.timestamp is not None

        # Check engineering analysis
        assert "loads" in result.engineering_analysis
        assert "structural_properties" in result.engineering_analysis
        assert "stress_analysis" in result.engineering_analysis
        assert "deflection_analysis" in result.engineering_analysis
        assert "buckling_analysis" in result.engineering_analysis
        assert "safety_analysis" in result.engineering_analysis

        # Check code compliance
        assert "load_combinations" in result.code_compliance
        assert "stress_limits" in result.code_compliance
        assert "deflection_limits" in result.code_compliance
        assert "buckling_limits" in result.code_compliance
        assert "overall_compliance" in result.code_compliance

        # Check implementation guidance
        assert "design_recommendations" in result.implementation_guidance
        assert "construction_notes" in result.implementation_guidance
        assert "inspection_requirements" in result.implementation_guidance
        assert "maintenance_guidelines" in result.implementation_guidance
        assert "code_references" in result.implementation_guidance

        # Check performance metrics
        assert "analysis_time" in result.performance_metrics
        assert result.performance_metrics["analysis_time"] > 0

    @pytest.mark.asyncio
    async def test_analyze_structural_element_column(
        self, structural_engine, sample_column_data
    ):
        """Test comprehensive structural analysis for column."""
        result = await structural_engine.analyze_structural_element(sample_column_data)

        # Check result structure
        assert isinstance(result, AnalysisResult)
        assert result.element_id == "test_column_001"
        assert result.element_type == StructuralElementType.COLUMN
        assert result.status == "completed"

        # Check that buckling analysis is performed for column
        buckling_analysis = result.engineering_analysis["buckling_analysis"]
        assert buckling_analysis["euler_buckling_load"] > 0
        assert buckling_analysis["critical_load"] > 0
        assert buckling_analysis["buckling_safety_factor"] > 0

    @pytest.mark.asyncio
    async def test_analyze_structural_element_concrete_slab(
        self, structural_engine, sample_concrete_slab_data
    ):
        """Test comprehensive structural analysis for concrete slab."""
        result = await structural_engine.analyze_structural_element(
            sample_concrete_slab_data
        )

        # Check result structure
        assert isinstance(result, AnalysisResult)
        assert result.element_id == "test_slab_001"
        assert result.element_type == StructuralElementType.SLAB
        assert result.status == "completed"

        # Check that concrete material properties are used
        stress_analysis = result.engineering_analysis["stress_analysis"]
        safety_analysis = result.engineering_analysis["safety_analysis"]

        # Concrete has different strength properties than steel
        assert (
            safety_analysis["yield_strength"] == 0.0
        )  # Concrete doesn't have yield strength
        assert (
            safety_analysis["ultimate_strength"] == 0.0
        )  # Concrete doesn't have ultimate strength

    def test_validate_element(self, structural_engine):
        """Test element validation."""
        # Valid element data
        valid_data = {
            "id": "test_element",
            "type": "beam",
            "material": "A36_Steel",
            "geometry": {"length": 5.0, "width": 0.2, "height": 0.3},
        }
        assert structural_engine.validate_element(valid_data) == True

        # Invalid element data - missing required field
        invalid_data = {
            "id": "test_element",
            "type": "beam",
            "material": "A36_Steel",
            # Missing geometry
        }
        assert structural_engine.validate_element(invalid_data) == False

        # Invalid element data - unknown material
        invalid_material_data = {
            "id": "test_element",
            "type": "beam",
            "material": "Unknown_Material",
            "geometry": {"length": 5.0, "width": 0.2, "height": 0.3},
        }
        assert structural_engine.validate_element(invalid_material_data) == False

        # Invalid element data - invalid type
        invalid_type_data = {
            "id": "test_element",
            "type": "invalid_type",
            "material": "A36_Steel",
            "geometry": {"length": 5.0, "width": 0.2, "height": 0.3},
        }
        assert structural_engine.validate_element(invalid_type_data) == False

    def test_get_material_properties(self, structural_engine):
        """Test getting material properties."""
        # Test existing material
        a36_steel = structural_engine.get_material_properties("A36_Steel")
        assert a36_steel is not None
        assert a36_steel.name == "A36 Steel"
        assert a36_steel.type == MaterialType.STEEL

        # Test non-existing material
        unknown_material = structural_engine.get_material_properties("Unknown_Material")
        assert unknown_material is None

    def test_add_material(self, structural_engine):
        """Test adding new material."""
        new_material = MaterialProperties(
            name="Test_Steel",
            type=MaterialType.STEEL,
            elastic_modulus=210000,  # MPa
            poisson_ratio=0.3,
            yield_strength=300,  # MPa
            ultimate_strength=450,  # MPa
            density=7850,  # kg/m³
            thermal_expansion=12e-6,  # 1/°C
            compressive_strength=0.0,
            tensile_strength=450.0,
            shear_strength=180.0,
        )

        structural_engine.add_material(new_material)

        # Check that material was added
        added_material = structural_engine.get_material_properties("Test_Steel")
        assert added_material is not None
        assert added_material.name == "Test_Steel"
        assert added_material.yield_strength == 300

    def test_performance_metrics(self, structural_engine):
        """Test performance metrics tracking."""
        # Initial metrics
        initial_metrics = structural_engine.get_performance_metrics()
        assert initial_metrics["total_analyses"] == 0
        assert initial_metrics["successful_analyses"] == 0
        assert initial_metrics["failed_analyses"] == 0
        assert initial_metrics["average_analysis_time"] == 0.0

        # Update metrics
        structural_engine._update_performance_metrics(1.5, True)
        structural_engine._update_performance_metrics(2.0, True)
        structural_engine._update_performance_metrics(0.5, False)

        # Check updated metrics
        updated_metrics = structural_engine.get_performance_metrics()
        assert updated_metrics["total_analyses"] == 3
        assert updated_metrics["successful_analyses"] == 2
        assert updated_metrics["failed_analyses"] == 1
        assert updated_metrics["total_analysis_time"] == 4.0
        assert updated_metrics["average_analysis_time"] == 4.0 / 3.0

    @pytest.mark.asyncio
    async def test_error_handling(self, structural_engine):
        """Test error handling for invalid data."""
        # Invalid element data
        invalid_data = {
            "id": "invalid_element",
            "type": "invalid_type",
            "material": "Unknown_Material",
            "geometry": {},
        }

        result = await structural_engine.analyze_structural_element(invalid_data)

        # Check that error is handled gracefully
        assert result.status == "failed"
        assert len(result.errors) > 0
        assert result.timestamp is not None

    def test_load_combinations_comprehensive(self, structural_engine, sample_beam_data):
        """Test comprehensive load combination calculations."""
        element = structural_engine._create_structural_element(sample_beam_data)
        loads_analysis = structural_engine._calculate_loads(element)

        # Test all load combinations
        for combination in LoadCombination:
            load_value = loads_analysis["combined_loads"][combination.value]
            assert (
                load_value > 0
            ), f"Load combination {combination.value} should be positive"

            # Check that load factors are applied correctly
            factors = structural_engine.load_factors[combination]
            if combination == LoadCombination.ULTIMATE_1:
                # Only dead load should be considered
                assert load_value > loads_analysis["dead_load"]
            elif combination == LoadCombination.SERVICE_1:
                # Dead + live load
                assert (
                    load_value
                    > loads_analysis["dead_load"] + loads_analysis["live_load"] * 0.9
                )

    def test_stress_analysis_comprehensive(self, structural_engine, sample_beam_data):
        """Test comprehensive stress analysis."""
        element = structural_engine._create_structural_element(sample_beam_data)
        loads_analysis = structural_engine._calculate_loads(element)
        stress_analysis = structural_engine._calculate_stress_analysis(
            element, loads_analysis
        )

        # Check stress relationships
        von_mises = stress_analysis["von_mises_stress"]
        axial = stress_analysis["axial_stress"]
        shear = stress_analysis["shear_stress"]

        # Von Mises stress should be greater than or equal to axial stress
        assert von_mises >= axial

        # Principal stresses should be real numbers
        principal_1 = stress_analysis["principal_stress_1"]
        principal_2 = stress_analysis["principal_stress_2"]
        assert isinstance(principal_1, (int, float))
        assert isinstance(principal_2, (int, float))

        # Principal stresses should be different (unless pure shear)
        assert principal_1 != principal_2 or shear == 0

    def test_deflection_analysis_comprehensive(
        self, structural_engine, sample_beam_data
    ):
        """Test comprehensive deflection analysis."""
        element = structural_engine._create_structural_element(sample_beam_data)
        loads_analysis = structural_engine._calculate_loads(element)
        deflection_analysis = structural_engine._calculate_deflection_analysis(
            element, loads_analysis
        )

        # Check deflection relationships
        max_deflection = deflection_analysis["max_deflection"]
        deflection_limit = deflection_analysis["deflection_limit"]
        deflection_ratio = deflection_analysis["deflection_ratio"]

        # Deflection should be positive
        assert max_deflection > 0

        # Deflection limit should be L/360
        expected_limit = element.length / 360
        assert abs(deflection_limit - expected_limit) < 0.001

        # Deflection ratio should be max_deflection / deflection_limit
        assert abs(deflection_ratio - max_deflection / deflection_limit) < 0.001

        # Service load should be reasonable
        service_load = deflection_analysis["service_load"]
        assert service_load > 0
        assert service_load < 100  # Should be reasonable for this beam


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
