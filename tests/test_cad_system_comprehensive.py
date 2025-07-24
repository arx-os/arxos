"""
Comprehensive CAD System Tests for SVGX Engine

Tests all CAD components including precision, constraints, grid/snap,
dimensioning, parametric, assembly, and views systems.

CTO Directives:
- Comprehensive CAD system testing
- Enterprise-grade test coverage
- Professional CAD functionality validation
- Complete CAD system integration testing
"""

import unittest
import sys
import os
from decimal import Decimal
from typing import Dict, Any

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from svgx_engine.core.precision_system import (
    PrecisionPoint, PrecisionLevel, PrecisionDrawingSystem
)
from svgx_engine.core.constraint_system import (
    ConstraintType, DistanceConstraint, AngleConstraint, ParallelConstraint,
    PerpendicularConstraint, CoincidentConstraint, TangentConstraint,
    SymmetricConstraint, ConstraintManager
)
from svgx_engine.core.grid_snap_system import (
    GridConfig, SnapConfig, GridSnapManager
)
from svgx_engine.core.dimensioning_system import (
    DimensionType, LinearDimension, RadialDimension, AngularDimension,
    OrdinateDimension, DimensionManager
)
from svgx_engine.core.parametric_system import (
    ParameterType, Parameter, ParameterExpression, ParametricGeometry,
    ParametricAssembly, ParametricModelingSystem
)
from svgx_engine.core.assembly_system import (
    Component, AssemblyConstraint, Assembly, AssemblyManager
)
from svgx_engine.core.drawing_views_system import (
    ViewType, ViewConfig, DrawingView, ViewGenerator, ViewManager
)
from svgx_engine.core.cad_system_integration import CADSystem

class TestPrecisionSystem(unittest.TestCase):
    """Test precision drawing system"""
    
    def setUp(self):
        self.precision_system = PrecisionDrawingSystem()
    
    def test_precision_point_creation(self):
        """Test precision point creation"""
        point = self.precision_system.add_point(10.5, 20.3)
        self.assertIsNotNone(point)
        self.assertEqual(float(point.x), 10.5)
        self.assertEqual(float(point.y), 20.3)
        self.assertEqual(point.precision_level, PrecisionLevel.SUB_MILLIMETER)
    
    def test_precision_point_3d(self):
        """Test 3D precision point creation"""
        point = self.precision_system.add_point(10.5, 20.3, 30.7)
        self.assertIsNotNone(point)
        self.assertEqual(float(point.x), 10.5)
        self.assertEqual(float(point.y), 20.3)
        self.assertEqual(float(point.z), 30.7)
    
    def test_distance_calculation(self):
        """Test distance calculation between points"""
        point1 = self.precision_system.add_point(0, 0)
        point2 = self.precision_system.add_point(3, 4)
        distance = self.precision_system.calculate_distance(point1, point2)
        self.assertEqual(float(distance), 5.0)
    
    def test_coordinate_system_transformation(self):
        """Test coordinate system transformation"""
        point = self.precision_system.add_point(10, 20)
        self.precision_system.set_origin(5, 5)
        transformed = self.precision_system.transform_point(point)
        self.assertEqual(float(transformed.x), 5.0)
        self.assertEqual(float(transformed.y), 15.0)
    
    def test_precision_validation(self):
        """Test precision system validation"""
        self.assertTrue(self.precision_system.validate_system())
    
    def test_precision_info(self):
        """Test precision system information"""
        info = self.precision_system.get_precision_info()
        self.assertIn('precision_level', info)
        self.assertIn('precision_display', info)
        self.assertIn('coordinate_system', info)

class TestConstraintSystem(unittest.TestCase):
    """Test constraint system"""
    
    def setUp(self):
        self.constraint_manager = ConstraintManager()
    
    def test_distance_constraint(self):
        """Test distance constraint creation"""
        constraint = self.constraint_manager.create_distance_constraint(
            "entity1", "entity2", 10.0
        )
        self.assertIsNotNone(constraint)
        self.assertEqual(constraint.constraint_type, ConstraintType.DISTANCE)
        self.assertEqual(constraint.parameters['distance'], 10.0)
    
    def test_angle_constraint(self):
        """Test angle constraint creation"""
        constraint = self.constraint_manager.create_angle_constraint(
            "entity1", "entity2", 90.0
        )
        self.assertIsNotNone(constraint)
        self.assertEqual(constraint.constraint_type, ConstraintType.ANGLE)
        self.assertEqual(constraint.parameters['angle'], 90.0)
    
    def test_parallel_constraint(self):
        """Test parallel constraint creation"""
        constraint = self.constraint_manager.create_parallel_constraint(
            "entity1", "entity2"
        )
        self.assertIsNotNone(constraint)
        self.assertEqual(constraint.constraint_type, ConstraintType.PARALLEL)
    
    def test_perpendicular_constraint(self):
        """Test perpendicular constraint creation"""
        constraint = self.constraint_manager.create_perpendicular_constraint(
            "entity1", "entity2"
        )
        self.assertIsNotNone(constraint)
        self.assertEqual(constraint.constraint_type, ConstraintType.PERPENDICULAR)
    
    def test_coincident_constraint(self):
        """Test coincident constraint creation"""
        constraint = self.constraint_manager.create_coincident_constraint(
            ["entity1", "entity2", "entity3"]
        )
        self.assertIsNotNone(constraint)
        self.assertEqual(constraint.constraint_type, ConstraintType.COINCIDENT)
        self.assertEqual(len(constraint.entities), 3)
    
    def test_constraint_solving(self):
        """Test constraint solving"""
        # Add some constraints
        self.constraint_manager.create_distance_constraint("entity1", "entity2", 10.0)
        self.constraint_manager.create_parallel_constraint("entity1", "entity3")
        
        # Solve constraints
        success = self.constraint_manager.solve_all_constraints()
        self.assertTrue(success)
    
    def test_constraint_info(self):
        """Test constraint system information"""
        info = self.constraint_manager.get_constraint_info()
        self.assertIn('total_constraints', info)
        self.assertIn('status_counts', info)

class TestGridSnapSystem(unittest.TestCase):
    """Test grid and snap system"""
    
    def setUp(self):
        grid_config = GridConfig()
        snap_config = SnapConfig()
        self.grid_snap_manager = GridSnapManager(grid_config, snap_config)
    
    def test_grid_configuration(self):
        """Test grid configuration"""
        grid_config = GridConfig(
            spacing_x=Decimal('5.0'),
            spacing_y=Decimal('5.0'),
            origin_x=Decimal('0.0'),
            origin_y=Decimal('0.0'),
            visible=True,
            snap_enabled=True
        )
        self.grid_snap_manager.set_grid_config(grid_config)
        
        info = self.grid_snap_manager.get_system_info()
        self.assertIn('grid', info)
        self.assertIn('snap', info)
    
    def test_snap_configuration(self):
        """Test snap configuration"""
        snap_config = SnapConfig(
            tolerance=Decimal('0.5'),
            angle_snap=Decimal('15.0'),
            visual_feedback=True,
            magnetic_snap=True
        )
        self.grid_snap_manager.set_snap_config(snap_config)
        
        info = self.grid_snap_manager.get_system_info()
        self.assertIn('snap', info)
    
    def test_point_snapping(self):
        """Test point snapping"""
        point = PrecisionPoint(Decimal('12.3'), Decimal('18.7'))
        snapped = self.grid_snap_manager.snap_point(point)
        self.assertIsNotNone(snapped)
    
    def test_angle_snapping(self):
        """Test angle snapping"""
        angle = Decimal('23.5')
        snapped = self.grid_snap_manager.snap_angle(angle)
        self.assertIsNotNone(snapped)
    
    def test_system_validation(self):
        """Test grid and snap system validation"""
        self.assertTrue(self.grid_snap_manager.validate_system())

class TestDimensioningSystem(unittest.TestCase):
    """Test dimensioning system"""
    
    def setUp(self):
        self.dimension_manager = DimensionManager()
    
    def test_linear_dimension(self):
        """Test linear dimension creation"""
        start_point = PrecisionPoint(Decimal('0'), Decimal('0'))
        end_point = PrecisionPoint(Decimal('10'), Decimal('0'))
        
        dimension = self.dimension_manager.create_linear_dimension(
            start_point, end_point, DimensionType.LINEAR_HORIZONTAL
        )
        self.assertIsNotNone(dimension)
        self.assertEqual(dimension.dimension_type, DimensionType.LINEAR_HORIZONTAL)
    
    def test_radial_dimension(self):
        """Test radial dimension creation"""
        center_point = PrecisionPoint(Decimal('0'), Decimal('0'))
        circumference_point = PrecisionPoint(Decimal('5'), Decimal('0'))
        
        dimension = self.dimension_manager.create_radial_dimension(
            center_point, circumference_point, Decimal('5.0')
        )
        self.assertIsNotNone(dimension)
        self.assertEqual(dimension.dimension_type, DimensionType.RADIAL)
    
    def test_angular_dimension(self):
        """Test angular dimension creation"""
        vertex_point = PrecisionPoint(Decimal('0'), Decimal('0'))
        first_line_end = PrecisionPoint(Decimal('10'), Decimal('0'))
        second_line_end = PrecisionPoint(Decimal('0'), Decimal('10'))
        
        dimension = self.dimension_manager.create_angular_dimension(
            vertex_point, first_line_end, second_line_end, Decimal('90')
        )
        self.assertIsNotNone(dimension)
        self.assertEqual(dimension.dimension_type, DimensionType.ANGULAR)
    
    def test_dimension_formatting(self):
        """Test dimension text formatting"""
        start_point = PrecisionPoint(Decimal('0'), Decimal('0'))
        end_point = PrecisionPoint(Decimal('10'), Decimal('0'))
        
        dimension = self.dimension_manager.create_linear_dimension(
            start_point, end_point, DimensionType.LINEAR_HORIZONTAL
        )
        
        formatted_text = dimension.format_text()
        self.assertIsInstance(formatted_text, str)
        self.assertIn('10.000', formatted_text)
    
    def test_dimension_style(self):
        """Test dimension style management"""
        style = self.dimension_manager.get_style("default")
        self.assertIsNotNone(style)
        self.assertEqual(style.style_name, "default")
    
    def test_system_validation(self):
        """Test dimensioning system validation"""
        self.assertTrue(self.dimension_manager.validate_system())

class TestParametricSystem(unittest.TestCase):
    """Test parametric modeling system"""
    
    def setUp(self):
        self.parametric_system = ParametricModelingSystem()
    
    def test_parameter_creation(self):
        """Test parameter creation"""
        parameter = self.parametric_system.add_parameter(
            "length", ParameterType.LENGTH, 10.0, "mm", "Test length"
        )
        self.assertIsNotNone(parameter)
        self.assertEqual(parameter.name, "length")
        self.assertEqual(parameter.parameter_type, ParameterType.LENGTH)
        self.assertEqual(parameter.value, 10.0)
    
    def test_parameter_validation(self):
        """Test parameter validation"""
        # Valid parameter
        parameter = self.parametric_system.add_parameter(
            "radius", ParameterType.RADIUS, 5.0, "mm", "Test radius"
        )
        self.assertTrue(parameter.validate())
        
        # Invalid parameter (negative radius)
        invalid_parameter = Parameter(
            "invalid", "radius", ParameterType.RADIUS, -5.0, "mm", ""
        )
        self.assertFalse(invalid_parameter.validate())
    
    def test_expression_evaluation(self):
        """Test parameter expression evaluation"""
        # Add parameters
        self.parametric_system.add_parameter("width", ParameterType.LENGTH, 10.0)
        self.parametric_system.add_parameter("height", ParameterType.LENGTH, 5.0)
        
        # Add expression
        expression = self.parametric_system.add_expression(
            "width * height", "area", ["width", "height"]
        )
        self.assertIsNotNone(expression)
    
    def test_parametric_geometry(self):
        """Test parametric geometry creation"""
        # Create parameters
        self.parametric_system.add_parameter("width", ParameterType.LENGTH, 10.0)
        self.parametric_system.add_parameter("height", ParameterType.LENGTH, 5.0)
        
        # Create geometry
        geometry = self.parametric_system.create_parametric_geometry(
            "rectangle", {}, []
        )
        self.assertIsNotNone(geometry)
        self.assertEqual(geometry.geometry_type, "rectangle")
    
    def test_parametric_assembly(self):
        """Test parametric assembly creation"""
        # Create components
        component1 = self.parametric_system.create_parametric_geometry(
            "rectangle", {}, []
        )
        component2 = self.parametric_system.create_parametric_geometry(
            "circle", {}, []
        )
        
        # Create assembly
        assembly = self.parametric_system.create_parametric_assembly(
            "test_assembly", [component1, component2]
        )
        self.assertIsNotNone(assembly)
        self.assertEqual(assembly.name, "test_assembly")
        self.assertEqual(len(assembly.components), 2)
    
    def test_system_validation(self):
        """Test parametric system validation"""
        self.assertTrue(self.parametric_system.validate_system())

class TestAssemblySystem(unittest.TestCase):
    """Test assembly management system"""
    
    def setUp(self):
        self.assembly_manager = AssemblyManager()
    
    def test_assembly_creation(self):
        """Test assembly creation"""
        assembly = self.assembly_manager.create_assembly("test_assembly")
        self.assertIsNotNone(assembly)
        self.assertEqual(assembly.name, "test_assembly")
    
    def test_component_creation(self):
        """Test component creation"""
        geometry = {"type": "rectangle", "width": 10, "height": 5}
        position = PrecisionPoint(Decimal('0'), Decimal('0'))
        
        component = Component(
            component_id="comp1",
            name="test_component",
            geometry=geometry,
            position=position
        )
        self.assertIsNotNone(component)
        self.assertEqual(component.name, "test_component")
    
    def test_component_transformation(self):
        """Test component transformation"""
        geometry = {"type": "rectangle", "width": 10, "height": 5}
        position = PrecisionPoint(Decimal('0'), Decimal('0'))
        
        component = Component(
            component_id="comp1",
            name="test_component",
            geometry=geometry,
            position=position,
            rotation=Decimal('0.785'),  # 45 degrees
            scale=Decimal('2.0')
        )
        
        transformed_geometry = component.get_transformed_geometry()
        self.assertIsNotNone(transformed_geometry)
    
    def test_assembly_constraint(self):
        """Test assembly constraint creation"""
        constraint = AssemblyConstraint(
            constraint_id="constraint1",
            constraint_type=ConstraintType.DISTANCE,
            component1="comp1",
            component2="comp2",
            parameters={"distance": 10.0}
        )
        self.assertIsNotNone(constraint)
        self.assertTrue(constraint.validate())
    
    def test_assembly_validation(self):
        """Test assembly validation"""
        assembly = self.assembly_manager.create_assembly("test_assembly")
        success = self.assembly_manager.validate_assembly(assembly.assembly_id)
        self.assertTrue(success)
    
    def test_interference_checking(self):
        """Test interference checking"""
        assembly = self.assembly_manager.create_assembly("test_assembly")
        interference_pairs = self.assembly_manager.check_assembly_interference(assembly.assembly_id)
        self.assertIsInstance(interference_pairs, list)

class TestDrawingViewsSystem(unittest.TestCase):
    """Test drawing views system"""
    
    def setUp(self):
        self.view_manager = ViewManager()
    
    def test_view_creation(self):
        """Test view creation"""
        config = ViewConfig(
            view_type=ViewType.FRONT,
            scale=Decimal('1.0'),
            show_hidden_lines=True,
            show_center_lines=True
        )
        
        view = self.view_manager.view_generator.create_view(
            "Front View", ViewType.FRONT, config
        )
        self.assertIsNotNone(view)
        self.assertEqual(view.name, "Front View")
        self.assertEqual(view.view_type, ViewType.FRONT)
    
    def test_standard_views_generation(self):
        """Test standard views generation"""
        model_geometry = {
            "type": "rectangle",
            "width": 10,
            "height": 5,
            "center": {"x": 0, "y": 0}
        }
        
        standard_views = self.view_manager.view_generator.generate_standard_views(model_geometry)
        self.assertIsNotNone(standard_views)
        self.assertIn('front', standard_views)
        self.assertIn('top', standard_views)
        self.assertIn('right', standard_views)
        self.assertIn('isometric', standard_views)
    
    def test_view_transformation(self):
        """Test view transformation"""
        config = ViewConfig(
            view_type=ViewType.TOP,
            scale=Decimal('1.0')
        )
        
        view = self.view_manager.view_generator.create_view(
            "Top View", ViewType.TOP, config
        )
        
        model_geometry = {
            "type": "circle",
            "center": {"x": 0, "y": 0, "z": 0},
            "radius": 5
        }
        
        view_data = view.generate_view(model_geometry)
        self.assertIsNotNone(view_data)
        self.assertIn('geometry', view_data)
        self.assertIn('viewport', view_data)
    
    def test_layout_creation(self):
        """Test layout creation"""
        model_geometry = {
            "type": "rectangle",
            "width": 10,
            "height": 5
        }
        
        layout_id = self.view_manager.create_standard_layout(model_geometry)
        self.assertIsNotNone(layout_id)
        
        views = self.view_manager.get_layout_views(layout_id)
        self.assertIsNotNone(views)
        self.assertGreater(len(views), 0)
    
    def test_layout_validation(self):
        """Test layout validation"""
        model_geometry = {
            "type": "rectangle",
            "width": 10,
            "height": 5
        }
        
        layout_id = self.view_manager.create_standard_layout(model_geometry)
        self.assertTrue(self.view_manager.validate_layout(layout_id))

class TestCADSystemIntegration(unittest.TestCase):
    """Test CAD system integration"""
    
    def setUp(self):
        self.cad_system = CADSystem()
    
    def test_cad_system_initialization(self):
        """Test CAD system initialization"""
        self.assertIsNotNone(self.cad_system.precision_system)
        self.assertIsNotNone(self.cad_system.constraint_system)
        self.assertIsNotNone(self.cad_system.grid_snap_system)
        self.assertIsNotNone(self.cad_system.dimensioning_system)
        self.assertIsNotNone(self.cad_system.parametric_system)
        self.assertIsNotNone(self.cad_system.assembly_system)
        self.assertIsNotNone(self.cad_system.view_system)
    
    def test_drawing_creation(self):
        """Test drawing creation"""
        drawing_id = self.cad_system.create_new_drawing("Test Drawing")
        self.assertIsNotNone(drawing_id)
        self.assertIsNotNone(self.cad_system.current_drawing)
        self.assertEqual(self.cad_system.current_drawing['name'], "Test Drawing")
    
    def test_precision_point_addition(self):
        """Test precision point addition"""
        self.cad_system.create_new_drawing("Test Drawing")
        point = self.cad_system.add_precision_point(10.5, 20.3)
        self.assertIsNotNone(point)
        self.assertEqual(float(point.x), 10.5)
        self.assertEqual(float(point.y), 20.3)
    
    def test_constraint_addition(self):
        """Test constraint addition"""
        self.cad_system.create_new_drawing("Test Drawing")
        success = self.cad_system.add_constraint(
            ConstraintType.DISTANCE,
            ["entity1", "entity2"],
            {"distance": 10.0}
        )
        self.assertTrue(success)
    
    def test_dimension_addition(self):
        """Test dimension addition"""
        self.cad_system.create_new_drawing("Test Drawing")
        start_point = PrecisionPoint(Decimal('0'), Decimal('0'))
        end_point = PrecisionPoint(Decimal('10'), Decimal('0'))
        
        success = self.cad_system.add_dimension(
            DimensionType.LINEAR_HORIZONTAL,
            start_point,
            end_point
        )
        self.assertTrue(success)
    
    def test_parameter_addition(self):
        """Test parameter addition"""
        self.cad_system.create_new_drawing("Test Drawing")
        success = self.cad_system.add_parameter(
            "length", ParameterType.LENGTH, 10.0, "mm", "Test length"
        )
        self.assertTrue(success)
    
    def test_assembly_creation(self):
        """Test assembly creation"""
        self.cad_system.create_new_drawing("Test Drawing")
        assembly_id = self.cad_system.create_assembly("Test Assembly")
        self.assertIsNotNone(assembly_id)
    
    def test_views_generation(self):
        """Test views generation"""
        self.cad_system.create_new_drawing("Test Drawing")
        model_geometry = {
            "type": "rectangle",
            "width": 10,
            "height": 5
        }
        
        views = self.cad_system.generate_views(model_geometry)
        self.assertIsNotNone(views)
        self.assertGreater(len(views), 0)
    
    def test_constraint_solving(self):
        """Test constraint solving"""
        self.cad_system.create_new_drawing("Test Drawing")
        success = self.cad_system.solve_constraints()
        self.assertTrue(success)
    
    def test_drawing_validation(self):
        """Test drawing validation"""
        self.cad_system.create_new_drawing("Test Drawing")
        success = self.cad_system.validate_drawing()
        self.assertTrue(success)
    
    def test_drawing_info(self):
        """Test drawing information retrieval"""
        self.cad_system.create_new_drawing("Test Drawing")
        info = self.cad_system.get_drawing_info()
        self.assertIsNotNone(info)
        self.assertIn('drawing_id', info)
        self.assertIn('name', info)
    
    def test_drawing_export(self):
        """Test drawing export"""
        self.cad_system.create_new_drawing("Test Drawing")
        export_data = self.cad_system.export_drawing("json")
        self.assertIsNotNone(export_data)
        self.assertIn('drawing_info', export_data)

def run_comprehensive_tests():
    """Run all comprehensive CAD system tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestPrecisionSystem,
        TestConstraintSystem,
        TestGridSnapSystem,
        TestDimensioningSystem,
        TestParametricSystem,
        TestAssemblySystem,
        TestDrawingViewsSystem,
        TestCADSystemIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"CAD SYSTEM COMPREHENSIVE TEST RESULTS")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1) 