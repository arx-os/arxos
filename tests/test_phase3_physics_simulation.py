"""
Test Phase 3: Advanced Physics Simulation

This test file verifies the implementation of Phase 3 physics simulation components:
- Structural analysis engine
- Load calculator
- Stress analyzer
- Flow calculator
- Pressure analyzer

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import unittest
import sys
import os
import numpy as np
from typing import Dict, List, Any

# Add the svgx_engine to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'svgx_engine'))

from services.physics.structural_analysis import (
    StructuralAnalysisService, MaterialProperties, Load, StructuralElement, 
    AnalysisType, LoadType, MaterialType
)
from services.physics.load_calculator import (
    LoadCalculator, LoadCategory, LoadCombination, MaterialDensity,
    WindParameters, SeismicParameters
)
from services.physics.stress_analyzer import (
    StressAnalyzer, StressTensor, StrainTensor, MaterialStrength,
    FailureCriterion, StressState
)
from services.physics.flow_calculator import (
    FlowCalculator, FlowRegime, ValveType, PumpType, PipeProperties,
    ValveProperties, PumpProperties
)
from services.physics.pressure_analyzer import (
    PressureAnalyzer, PressureType, PressureUnit, PressurePoint,
    PressureVessel, PressureWave
)


class TestPhase3PhysicsSimulation(unittest.TestCase):
    """Test suite for Phase 3 physics simulation components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.structural_service = StructuralAnalysisService()
        self.load_calculator = LoadCalculator()
        self.stress_analyzer = StressAnalyzer()
        self.flow_calculator = FlowCalculator()
        self.pressure_analyzer = PressureAnalyzer()
        
    def test_structural_analysis_service(self):
        """Test structural analysis service functionality."""
        print("\n=== Testing Structural Analysis Service ===")
        
        # Test material initialization
        materials = self.structural_service.materials
        self.assertIsNotNone(materials)
        self.assertIn("A36_Steel", materials)
        self.assertIn("Concrete_C30", materials)
        
        # Test material properties
        steel = materials["A36_Steel"]
        self.assertEqual(steel.name, "A36 Steel")
        self.assertEqual(steel.type, MaterialType.STEEL)
        self.assertGreater(steel.elastic_modulus, 0)
        self.assertGreater(steel.yield_strength, 0)
        
        print("✓ Structural analysis service initialized successfully")
        
    def test_load_calculator(self):
        """Test load calculator functionality."""
        print("\n=== Testing Load Calculator ===")
        
        # Test dead load calculation
        volume = 10.0  # m³
        material = "concrete"
        dead_load = self.load_calculator.calculate_dead_load(volume, material)
        self.assertGreater(dead_load, 0)
        print(f"✓ Dead load calculation: {dead_load:.2f} kN")
        
        # Test live load calculation
        area = 100.0  # m²
        occupancy = "office"
        live_load = self.load_calculator.calculate_live_load(area, occupancy)
        self.assertGreater(live_load, 0)
        print(f"✓ Live load calculation: {live_load:.2f} kN")
        
        # Test wind load calculation
        area = 50.0  # m²
        height = 20.0  # m
        wind_load = self.load_calculator.calculate_wind_load(area, height)
        self.assertGreater(wind_load, 0)
        print(f"✓ Wind load calculation: {wind_load:.2f} kN")
        
        # Test load combination
        loads = {
            "dead": 100.0,
            "live": 50.0,
            "wind": 20.0
        }
        combined_load = self.load_calculator.combine_loads(loads, LoadCombination.ULTIMATE_1)
        self.assertGreater(combined_load, 0)
        print(f"✓ Load combination: {combined_load:.2f} kN")
        
    def test_stress_analyzer(self):
        """Test stress analyzer functionality."""
        print("\n=== Testing Stress Analyzer ===")
        
        # Create a stress tensor
        stress_tensor = StressTensor(
            sigma_xx=100.0,  # MPa
            sigma_yy=50.0,
            sigma_zz=25.0,
            tau_xy=20.0,
            tau_yz=10.0,
            tau_xz=15.0
        )
        
        # Test principal stresses
        sigma_1, sigma_2, sigma_3 = self.stress_analyzer.calculate_principal_stresses(stress_tensor)
        self.assertGreater(sigma_1, sigma_2)
        self.assertGreater(sigma_2, sigma_3)
        print(f"✓ Principal stresses: σ1={sigma_1:.2f}, σ2={sigma_2:.2f}, σ3={sigma_3:.2f} MPa")
        
        # Test von Mises stress
        von_mises = self.stress_analyzer.calculate_von_mises_stress(stress_tensor)
        self.assertGreater(von_mises, 0)
        print(f"✓ von Mises stress: {von_mises:.2f} MPa")
        
        # Test failure criterion
        material = "steel_a36"
        failure, safety_factor = self.stress_analyzer.check_failure_criterion(
            stress_tensor, material, FailureCriterion.VON_MISES
        )
        self.assertIsInstance(failure, bool)
        self.assertGreater(safety_factor, 0)
        print(f"✓ Failure check: failure={failure}, safety_factor={safety_factor:.2f}")
        
    def test_flow_calculator(self):
        """Test flow calculator functionality."""
        print("\n=== Testing Flow Calculator ===")
        
        # Test Reynolds number calculation
        velocity = 2.0  # m/s
        diameter = 0.1  # m
        fluid = "water"
        reynolds = self.flow_calculator.calculate_reynolds_number(velocity, diameter, fluid)
        self.assertGreater(reynolds, 0)
        print(f"✓ Reynolds number: {reynolds:.0f}")
        
        # Test flow regime determination
        regime = self.flow_calculator.determine_flow_regime(reynolds)
        self.assertIn(regime, [FlowRegime.LAMINAR, FlowRegime.TURBULENT, FlowRegime.TRANSITIONAL])
        print(f"✓ Flow regime: {regime.value}")
        
        # Test friction factor calculation
        roughness = 0.000045  # m (steel)
        friction_factor = self.flow_calculator.calculate_friction_factor(reynolds, roughness, diameter)
        self.assertGreater(friction_factor, 0)
        print(f"✓ Friction factor: {friction_factor:.4f}")
        
        # Test pipe pressure drop
        flow_rate = 0.01  # m³/s
        pipe = PipeProperties(
            diameter=0.1,
            length=100.0,
            roughness=0.000045,
            material="steel",
            wall_thickness=0.005
        )
        pressure_drop = self.flow_calculator.calculate_pressure_drop_pipe(flow_rate, pipe, fluid)
        self.assertGreater(pressure_drop, 0)
        print(f"✓ Pipe pressure drop: {pressure_drop:.2f} Pa")
        
    def test_pressure_analyzer(self):
        """Test pressure analyzer functionality."""
        print("\n=== Testing Pressure Analyzer ===")
        
        # Test hydrostatic pressure
        depth = 10.0  # m
        fluid_density = 998.0  # kg/m³
        hydrostatic_pressure = self.pressure_analyzer.calculate_hydrostatic_pressure(depth, fluid_density)
        self.assertGreater(hydrostatic_pressure, 0)
        print(f"✓ Hydrostatic pressure: {hydrostatic_pressure:.2f} Pa")
        
        # Test dynamic pressure
        velocity = 5.0  # m/s
        dynamic_pressure = self.pressure_analyzer.calculate_dynamic_pressure(velocity, fluid_density)
        self.assertGreater(dynamic_pressure, 0)
        print(f"✓ Dynamic pressure: {dynamic_pressure:.2f} Pa")
        
        # Test pressure unit conversion
        pressure_pa = 101325.0  # Pa (1 atm)
        pressure_psi = self.pressure_analyzer.convert_pressure_units(
            pressure_pa, PressureUnit.PA, PressureUnit.PSI
        )
        self.assertGreater(pressure_psi, 0)
        print(f"✓ Pressure conversion: {pressure_pa:.2f} Pa = {pressure_psi:.2f} psi")
        
        # Test pressure vessel analysis
        vessel = PressureVessel(
            diameter=1.0,
            length=3.0,
            wall_thickness=0.01,
            material="steel",
            design_pressure=1e6,
            operating_pressure=5e5,
            temperature=293.15
        )
        stresses = self.pressure_analyzer.calculate_pressure_vessel_stress(vessel)
        self.assertIn("hoop_stress", stresses)
        self.assertIn("longitudinal_stress", stresses)
        print(f"✓ Vessel stresses calculated: hoop={stresses['hoop_stress']:.2f} Pa")
        
    def test_integrated_structural_analysis(self):
        """Test integrated structural analysis workflow."""
        print("\n=== Testing Integrated Structural Analysis ===")
        
        # Create a simple beam element
        material = MaterialProperties(
            name="steel_a36",
            type=MaterialType.STEEL,
            elastic_modulus=200e9,  # Pa
            poisson_ratio=0.3,
            yield_strength=250e6,  # Pa
            ultimate_strength=400e6,  # Pa
            density=7850.0,  # kg/m³
            thermal_expansion=12e-6,  # 1/°C
            fatigue_strength=200e6  # Pa
        )
        
        # Create loads
        dead_load = Load(
            id="dead_1",
            type=LoadType.DEAD,
            magnitude=1000.0,  # N
            direction=(0.0, -1.0, 0.0),
            location=(0.0, 0.0, 0.0),
            duration=0.0
        )
        
        live_load = Load(
            id="live_1",
            type=LoadType.LIVE,
            magnitude=500.0,  # N
            direction=(0.0, -1.0, 0.0),
            location=(0.0, 0.0, 0.0),
            duration=0.0
        )
        
        # Create structural element
        element = StructuralElement(
            id="beam_1",
            type="beam",
            material=material,
            geometry={
                "length": 5.0,
                "width": 0.2,
                "height": 0.3
            },
            nodes=[(0.0, 0.0, 0.0), (5.0, 0.0, 0.0)],
            supports=[{"node": 0, "type": "fixed"}],
            loads=[dead_load, live_load]
        )
        
        # Perform structural analysis
        results = self.structural_service.analyze_structure([element], AnalysisType.STATIC)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
        result = results[0]
        self.assertEqual(result.element_id, "beam_1")
        self.assertEqual(result.analysis_type, AnalysisType.STATIC)
        self.assertGreater(result.safety_factor, 0)
        
        print(f"✓ Integrated analysis completed: safety_factor={result.safety_factor:.2f}")
        
    def test_integrated_fluid_analysis(self):
        """Test integrated fluid dynamics analysis workflow."""
        print("\n=== Testing Integrated Fluid Dynamics Analysis ===")
        
        # Create pipe properties
        pipe = PipeProperties(
            diameter=0.1,  # m
            length=100.0,  # m
            roughness=0.000045,  # m
            material="steel",
            wall_thickness=0.005  # m
        )
        
        # Calculate flow parameters
        flow_rate = 0.01  # m³/s
        fluid = "water"
        
        # Calculate pressure drop
        pressure_drop = self.flow_calculator.calculate_pressure_drop_pipe(flow_rate, pipe, fluid)
        self.assertGreater(pressure_drop, 0)
        
        # Calculate velocity
        area = np.pi * pipe.diameter**2 / 4.0
        velocity = flow_rate / area
        
        # Calculate Reynolds number
        reynolds = self.flow_calculator.calculate_reynolds_number(velocity, pipe.diameter, fluid)
        
        # Determine flow regime
        regime = self.flow_calculator.determine_flow_regime(reynolds)
        
        print(f"✓ Fluid analysis: flow_rate={flow_rate:.3f} m³/s, "
              f"pressure_drop={pressure_drop:.2f} Pa, regime={regime.value}")
        
    def test_material_properties(self):
        """Test material properties and databases."""
        print("\n=== Testing Material Properties ===")
        
        # Test structural materials
        steel_props = self.structural_service.get_material_properties("A36_Steel")
        self.assertIsNotNone(steel_props)
        print(f"✓ Steel properties: E={steel_props.elastic_modulus:.0f} Pa")
        
        # Test stress analyzer materials
        steel_strength = self.stress_analyzer.get_material_strength("steel_a36")
        self.assertIsNotNone(steel_strength)
        print(f"✓ Steel strength: σy={steel_strength.yield_strength:.0f} MPa")
        
        # Test flow calculator fluids
        water_props = self.flow_calculator.get_fluid_properties("water")
        self.assertIsNotNone(water_props)
        print(f"✓ Water properties: ρ={water_props['density']:.0f} kg/m³")
        
        # Test pressure analyzer materials
        steel_pressure_props = self.pressure_analyzer.get_material_properties("steel")
        self.assertIsNotNone(steel_pressure_props)
        print(f"✓ Steel pressure properties: σy={steel_pressure_props['yield_strength']:.0f} Pa")
        
    def test_error_handling(self):
        """Test error handling and validation."""
        print("\n=== Testing Error Handling ===")
        
        # Test invalid material
        with self.assertRaises(ValueError):
            self.load_calculator.calculate_dead_load(10.0, "invalid_material")
        
        # Test invalid fluid
        with self.assertRaises(ValueError):
            self.flow_calculator.calculate_reynolds_number(1.0, 0.1, "invalid_fluid")
        
        # Test invalid material in stress analyzer
        with self.assertRaises(ValueError):
            stress_tensor = StressTensor(100.0, 50.0, 25.0, 20.0, 10.0, 15.0)
            self.stress_analyzer.check_failure_criterion(stress_tensor, "invalid_material", FailureCriterion.VON_MISES)
        
        print("✓ Error handling tests passed")
        
    def test_performance_benchmarks(self):
        """Test performance benchmarks for physics calculations."""
        print("\n=== Testing Performance Benchmarks ===")
        
        import time
        
        # Benchmark structural analysis
        start_time = time.time()
        for _ in range(100):
            stress_tensor = StressTensor(100.0, 50.0, 25.0, 20.0, 10.0, 15.0)
            self.stress_analyzer.calculate_von_mises_stress(stress_tensor)
        structural_time = time.time() - start_time
        print(f"✓ Structural analysis: {structural_time:.3f}s for 100 calculations")
        
        # Benchmark flow calculations
        start_time = time.time()
        for _ in range(100):
            self.flow_calculator.calculate_reynolds_number(2.0, 0.1, "water")
        flow_time = time.time() - start_time
        print(f"✓ Flow calculations: {flow_time:.3f}s for 100 calculations")
        
        # Benchmark pressure calculations
        start_time = time.time()
        for _ in range(100):
            self.pressure_analyzer.calculate_hydrostatic_pressure(10.0, 998.0)
        pressure_time = time.time() - start_time
        print(f"✓ Pressure calculations: {pressure_time:.3f}s for 100 calculations")
        
        # Verify performance is reasonable (less than 1 second for 100 calculations)
        self.assertLess(structural_time, 1.0)
        self.assertLess(flow_time, 1.0)
        self.assertLess(pressure_time, 1.0)
        
    def test_advanced_features(self):
        """Test advanced physics simulation features."""
        print("\n=== Testing Advanced Features ===")
        
        # Test fatigue analysis
        stress_history = [
            StressTensor(100.0, 50.0, 25.0, 20.0, 10.0, 15.0),
            StressTensor(150.0, 75.0, 37.5, 30.0, 15.0, 22.5),
            StressTensor(200.0, 100.0, 50.0, 40.0, 20.0, 30.0)
        ]
        stress_range = self.stress_analyzer.calculate_fatigue_stress_range(stress_history)
        self.assertGreater(stress_range, 0)
        print(f"✓ Fatigue stress range: {stress_range:.2f} MPa")
        
        # Test buckling analysis
        element = StructuralElement(
            id="column_1",
            type="column",
            material=self.structural_service.materials["A36_Steel"],
            geometry={"length": 3.0, "width": 0.2, "height": 0.2},
            nodes=[(0.0, 0.0, 0.0), (0.0, 3.0, 0.0)],
            supports=[{"node": 0, "type": "fixed"}],
            loads=[]
        )
        buckling_result = self.structural_service._buckling_analysis(element)
        self.assertIsNotNone(buckling_result.buckling_load)
        print(f"✓ Buckling load: {buckling_result.buckling_load:.2f} N")
        
        # Test pressure wave propagation
        wave = PressureWave(
            amplitude=1000.0,
            frequency=10.0,
            wavelength=10.0,
            speed=1500.0,
            direction=(1.0, 0.0, 0.0)
        )
        pressure = self.pressure_analyzer.calculate_pressure_wave_propagation(wave, 5.0, 0.1)
        self.assertIsInstance(pressure, float)
        print(f"✓ Wave pressure: {pressure:.2f} Pa")
        
    def test_data_validation(self):
        """Test data validation and integrity checks."""
        print("\n=== Testing Data Validation ===")
        
        # Test pressure validation
        pressure = 101325.0  # Pa
        expected_range = (0.0, 1e6)  # Pa
        is_valid = self.pressure_analyzer.validate_pressure_measurement(pressure, expected_range)
        self.assertTrue(is_valid)
        
        # Test invalid pressure
        invalid_pressure = 2e6  # Pa (outside range)
        is_valid = self.pressure_analyzer.validate_pressure_measurement(invalid_pressure, expected_range)
        self.assertFalse(is_valid)
        
        print("✓ Data validation tests passed")
        
    def test_integration_with_existing_services(self):
        """Test integration with existing physics services."""
        print("\n=== Testing Integration with Existing Services ===")
        
        # Test that new components can work with existing structural analysis
        from services.physics.structural_analysis import StructuralAnalysisService
        
        # Create a simple analysis
        material = self.structural_service.materials["A36_Steel"]
        element = StructuralElement(
            id="test_beam",
            type="beam",
            material=material,
            geometry={"length": 2.0, "width": 0.1, "height": 0.1},
            nodes=[(0.0, 0.0, 0.0), (2.0, 0.0, 0.0)],
            supports=[{"node": 0, "type": "fixed"}],
            loads=[]
        )
        
        # Use load calculator to add loads
        dead_load_value = self.load_calculator.calculate_dead_load(0.02, "steel")  # 0.02 m³
        dead_load = Load(
            id="dead_load",
            type=LoadType.DEAD,
            magnitude=dead_load_value * 1000,  # Convert to N
            direction=(0.0, -1.0, 0.0),
            location=(1.0, 0.0, 0.0),
            duration=0.0
        )
        element.loads.append(dead_load)
        
        # Perform analysis
        results = self.structural_service.analyze_structure([element], AnalysisType.STATIC)
        self.assertGreater(len(results), 0)
        
        # Use stress analyzer to check results
        if results[0].stresses:
            stress_data = results[0].stresses[0]  # First stress point
            stress_tensor = StressTensor(
                sigma_xx=stress_data[0],
                sigma_yy=stress_data[1],
                sigma_zz=stress_data[2],
                tau_xy=stress_data[3],
                tau_yz=stress_data[4],
                tau_xz=stress_data[5]
            )
            
            von_mises = self.stress_analyzer.calculate_von_mises_stress(stress_tensor)
            self.assertGreater(von_mises, 0)
            
        print("✓ Integration with existing services successful")


def run_phase3_tests():
    """Run all Phase 3 physics simulation tests."""
    print("=" * 60)
    print("PHASE 3: ADVANCED PHYSICS SIMULATION TEST SUITE")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_cases = [
        TestPhase3PhysicsSimulation('test_structural_analysis_service'),
        TestPhase3PhysicsSimulation('test_load_calculator'),
        TestPhase3PhysicsSimulation('test_stress_analyzer'),
        TestPhase3PhysicsSimulation('test_flow_calculator'),
        TestPhase3PhysicsSimulation('test_pressure_analyzer'),
        TestPhase3PhysicsSimulation('test_integrated_structural_analysis'),
        TestPhase3PhysicsSimulation('test_integrated_fluid_analysis'),
        TestPhase3PhysicsSimulation('test_material_properties'),
        TestPhase3PhysicsSimulation('test_error_handling'),
        TestPhase3PhysicsSimulation('test_performance_benchmarks'),
        TestPhase3PhysicsSimulation('test_advanced_features'),
        TestPhase3PhysicsSimulation('test_data_validation'),
        TestPhase3PhysicsSimulation('test_integration_with_existing_services'),
    ]
    
    for test_case in test_cases:
        test_suite.addTest(test_case)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("PHASE 3 TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n✓ ALL PHASE 3 TESTS PASSED!")
        print("✓ Advanced Physics Simulation implementation is complete and functional.")
    else:
        print("\n✗ SOME TESTS FAILED!")
        print("Please review the failures and fix the implementation.")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_phase3_tests()
    sys.exit(0 if success else 1) 