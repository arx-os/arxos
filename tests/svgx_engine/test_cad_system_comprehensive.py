"""
Comprehensive Test Suite for SVGX Engine CAD System

This test suite provides comprehensive testing for the complete CAD system including:
- Integration of all CAD components
- End-to-end CAD workflows
- System validation and statistics
- Data export and import functionality
"""

import unittest
from decimal import Decimal
from typing import Dict, Any

from svgx_engine.services.cad.cad_system import create_cad_system
from svgx_engine.services.cad.precision_drawing_system import (
    PrecisionConfig, PrecisionLevel, PrecisionPoint, PrecisionVector
)
from svgx_engine.services.cad.grid_snap_system import GridConfig, SnapConfig
from svgx_engine.services.cad.constraint_system import ConstraintType
from svgx_engine.services.cad.dimensioning_system import DimensionStyle
from svgx_engine.services.cad.parametric_modeling import ParameterType
from svgx_engine.services.cad.assembly_management import ComponentType, AssemblyConstraintType


class TestCADSystemComprehensive(unittest.TestCase):
    """Comprehensive test suite for the complete CAD system."""

    def setUp(self):
        """Set up test environment."""
        # Create CAD system with custom configuration
        precision_config = PrecisionConfig(
            default_precision=PrecisionLevel.COMPUTE,
            ui_precision=Decimal("0.1"),
            edit_precision=Decimal("0.01"),
            compute_precision=Decimal("0.001")
        )

        grid_config = GridConfig(
            enabled=True,
            visible=True,
            spacing_x=Decimal("10.0"),
            spacing_y=Decimal("10.0"),
            snap_tolerance=Decimal("2.0")
        )

        snap_config = SnapConfig(
            enabled=True,
            tolerance=Decimal("2.0"),
            visual_feedback=True
        )

        self.cad_system = create_cad_system(precision_config, grid_config, snap_config)

    def test_system_initialization(self):
        """Test CAD system initialization."""
        self.assertIsNotNone(self.cad_system.precision_system)
        self.assertIsNotNone(self.cad_system.constraint_system)
        self.assertIsNotNone(self.cad_system.grid_snap_system)
        self.assertIsNotNone(self.cad_system.dimensioning_system)
        self.assertIsNotNone(self.cad_system.parametric_system)
        self.assertIsNotNone(self.cad_system.assembly_manager)
        self.assertIsNotNone(self.cad_system.drawing_view_manager)

    def test_precision_operations(self):
        """Test precision drawing operations."""
        # Test point creation
        point1 = self.cad_system.create_point(10.123, 20.456)
        point2 = self.cad_system.create_point(30.789, 40.012)

        self.assertIsInstance(point1, PrecisionPoint)
        self.assertIsInstance(point2, PrecisionPoint)
        self.assertEqual(point1.x, Decimal("10.123"))
        self.assertEqual(point1.y, Decimal("20.456"))

        # Test vector creation
        vector1 = self.cad_system.create_vector(5.0, 10.0)
        self.assertIsInstance(vector1, PrecisionVector)
        self.assertEqual(vector1.dx, Decimal("5.000"))
        self.assertEqual(vector1.dy, Decimal("10.000"))

        # Test distance calculation
        distance = point1.distance_to(point2)
        self.assertIsInstance(distance, Decimal)
        self.assertGreater(distance, 0)

    def test_grid_snap_operations(self):
        """Test grid and snap operations."""
        # Create a point
        target_point = PrecisionPoint(15.5, 25.5, precision_level=PrecisionLevel.COMPUTE)

        # Test snapping
        snapped_point = self.cad_system.snap_point(target_point, use_grid=True, use_snap=True)

        if snapped_point:
            self.assertIsInstance(snapped_point, PrecisionPoint)
            # Snapped point should be different from original import original
            self.assertNotEqual(target_point.x, snapped_point.x)
            self.assertNotEqual(target_point.y, snapped_point.y)

    def test_constraint_operations(self):
        """Test constraint operations."""
        # Create points for constraints
        point1 = self.cad_system.create_point(0, 0)
        point2 = self.cad_system.create_point(10, 0)
        point3 = self.cad_system.create_point(0, 10)

        # Add points to constraint system
        self.cad_system.constraint_system.add_point("p1", {"x": 0, "y": 0})
        self.cad_system.constraint_system.add_point("p2", {"x": 10, "y": 0})
        self.cad_system.constraint_system.add_point("p3", {"x": 0, "y": 10})

        # Test distance constraint
        constraint_id = self.cad_system.add_constraint(
            "distance", ["p1", "p2"], {"distance": 10.0}
        )
        self.assertIsInstance(constraint_id, str)
        self.assertGreater(len(constraint_id), 0)

        # Test horizontal constraint
        horizontal_constraint_id = self.cad_system.add_constraint(
            "horizontal", ["p1", "p2"]
        )
        self.assertIsInstance(horizontal_constraint_id, str)

        # Test solving constraints
        results = self.cad_system.solve_constraints()
        self.assertIsInstance(results, dict)

    def test_dimensioning_operations(self):
        """Test dimensioning operations."""
        # Create points for dimensions
        start_point = PrecisionPoint(0, 0, precision_level=PrecisionLevel.COMPUTE)
        end_point = PrecisionPoint(10, 0, precision_level=PrecisionLevel.COMPUTE)
        center_point = PrecisionPoint(5, 5, precision_level=PrecisionLevel.COMPUTE)
        radius_point = PrecisionPoint(8, 5, precision_level=PrecisionLevel.COMPUTE)

        # Test linear dimension
        linear_dim_id = self.cad_system.create_linear_dimension(
            start_point, end_point, "standard", 5.0
        )
        self.assertIsInstance(linear_dim_id, str)

        # Test radial dimension
        radial_dim_id = self.cad_system.create_radial_dimension(
            center_point, radius_point, "standard"
        )
        self.assertIsInstance(radial_dim_id, str)

        # Test angular dimension
        start_vector = PrecisionVector(1, 0, precision_level=PrecisionLevel.COMPUTE)
        end_vector = PrecisionVector(0, 1, precision_level=PrecisionLevel.COMPUTE)

        angular_dim_id = self.cad_system.create_angular_dimension(
            center_point, start_vector, end_vector, "standard"
        )
        self.assertIsInstance(angular_dim_id, str)

    def test_parametric_modeling_operations(self):
        """Test parametric modeling operations."""
        # Create parametric model
        model_name = self.cad_system.create_parametric_model("test_model")
        self.assertIsInstance(model_name, str)
        self.assertEqual(self.cad_system.active_model, model_name)

        # Add parameters to model
        success = self.cad_system.add_parameter_to_model(
            model_name, "length", 100.0, "length", "mm", "Length parameter"
        )
        self.assertTrue(success)

        success = self.cad_system.add_parameter_to_model(
            model_name, "width", 50.0, "length", "mm", "Width parameter"
        )
        self.assertTrue(success)

        success = self.cad_system.add_parameter_to_model(
            model_name, "height", 25.0, "length", "mm", "Height parameter"
        )
        self.assertTrue(success)

    def test_assembly_operations(self):
        """Test assembly operations."""
        # Create assembly
        assembly_id = self.cad_system.create_assembly("test_assembly")
        self.assertIsInstance(assembly_id, str)
        self.assertEqual(self.cad_system.active_assembly, assembly_id)

        # Create points for components
        pos1 = PrecisionPoint(0, 0, precision_level=PrecisionLevel.COMPUTE)
        pos2 = PrecisionPoint(10, 0, precision_level=PrecisionLevel.COMPUTE)
        pos3 = PrecisionPoint(0, 10, precision_level=PrecisionLevel.COMPUTE)

        # Add components to assembly
        success = self.cad_system.add_component_to_assembly(
            assembly_id, "comp1", "Component 1", "part", pos1
        )
        self.assertTrue(success)

        success = self.cad_system.add_component_to_assembly(
            assembly_id, "comp2", "Component 2", "part", pos2
        )
        self.assertTrue(success)

        success = self.cad_system.add_component_to_assembly(
            assembly_id, "comp3", "Component 3", "part", pos3
        )
        self.assertTrue(success)

    def test_drawing_view_operations(self):
        """Test drawing view operations."""
        # Create assembly data for views
        assembly_data = {
            "components": [
                {"id": "comp1", "position": {"x": 0, "y": 0}},
                {"id": "comp2", "position": {"x": 10, "y": 0}},
                {"id": "comp3", "position": {"x": 0, "y": 10}}
            ]
        }

        # Generate standard views
        view_ids = self.cad_system.generate_standard_views(assembly_data)
        self.assertIsInstance(view_ids, dict)
        self.assertIn("front", view_ids)
        self.assertIn("top", view_ids)
        self.assertIn("side", view_ids)

        # Generate isometric view
        isometric_view_id = self.cad_system.generate_isometric_view(assembly_data)
        self.assertIsInstance(isometric_view_id, str)

    def test_system_statistics(self):
        """Test system statistics retrieval."""
        stats = self.cad_system.get_system_statistics()
        self.assertIsInstance(stats, dict)

        # Check that all subsystems have statistics
        self.assertIn("precision_system", stats)
        self.assertIn("constraint_system", stats)
        self.assertIn("grid_snap_system", stats)
        self.assertIn("dimensioning_system", stats)
        self.assertIn("parametric_system", stats)
        self.assertIn("assembly_manager", stats)
        self.assertIn("drawing_view_manager", stats)

    def test_system_validation(self):
        """Test system validation."""
        validation_results = self.cad_system.validate_system()
        self.assertIsInstance(validation_results, dict)

        # All subsystems should be valid
        for subsystem, is_valid in validation_results.items():
            self.assertTrue(is_valid, f"Subsystem {subsystem} is not valid")

    def test_data_export_import(self):
        """Test data export and import functionality."""
        # Create some test data
        self.cad_system.create_point(10, 20)
        self.cad_system.create_vector(5, 10)
        self.cad_system.create_parametric_model("export_test_model")
        self.cad_system.create_assembly("export_test_assembly")

        # Export system data
        exported_data = self.cad_system.export_system_data()
        self.assertIsInstance(exported_data, dict)

        # Check that exported data contains all subsystems
        self.assertIn("precision_system", exported_data)
        self.assertIn("constraint_system", exported_data)
        self.assertIn("grid_snap_system", exported_data)
        self.assertIn("dimensioning_system", exported_data)
        self.assertIn("parametric_system", exported_data)
        self.assertIn("assembly_manager", exported_data)
        self.assertIn("drawing_view_manager", exported_data)

        # Create new CAD system and import data
        new_cad_system = create_cad_system()
        new_cad_system.import_system_data(exported_data)

        # Verify that data was imported correctly
        new_stats = new_cad_system.get_system_statistics()
        self.assertIsInstance(new_stats, dict)

    def test_end_to_end_workflow(self):
        """Test complete end-to-end CAD workflow."""
        # 1. Set precision level
        self.cad_system.set_precision_level("compute")

        # 2. Create precision points
        point1 = self.cad_system.create_point(0, 0)
        point2 = self.cad_system.create_point(10, 0)
        point3 = self.cad_system.create_point(0, 10)

        # 3. Snap points to grid
        snapped_point1 = self.cad_system.snap_point(point1)
        snapped_point2 = self.cad_system.snap_point(point2)
        snapped_point3 = self.cad_system.snap_point(point3)

        # 4. Add constraints
        self.cad_system.constraint_system.add_point("p1", {"x": 0, "y": 0})
        self.cad_system.constraint_system.add_point("p2", {"x": 10, "y": 0})
        self.cad_system.constraint_system.add_point("p3", {"x": 0, "y": 10})

        constraint1 = self.cad_system.add_constraint("horizontal", ["p1", "p2"])
        constraint2 = self.cad_system.add_constraint("vertical", ["p1", "p3"])

        # 5. Create dimensions
        dim1 = self.cad_system.create_linear_dimension(snapped_point1, snapped_point2)
        dim2 = self.cad_system.create_linear_dimension(snapped_point1, snapped_point3)

        # 6. Create parametric model
        model_name = self.cad_system.create_parametric_model("workflow_model")
        self.cad_system.add_parameter_to_model(model_name, "width", 10.0, "length")
        self.cad_system.add_parameter_to_model(model_name, "height", 10.0, "length")

        # 7. Create assembly
        assembly_id = self.cad_system.create_assembly("workflow_assembly")
        self.cad_system.add_component_to_assembly(assembly_id, "comp1", "Component 1", "part", snapped_point1)
        self.cad_system.add_component_to_assembly(assembly_id, "comp2", "Component 2", "part", snapped_point2)

        # 8. Generate views
        assembly_data = {"components": [{"id": "comp1"}, {"id": "comp2"}]}
        view_ids = self.cad_system.generate_standard_views(assembly_data)
        isometric_id = self.cad_system.generate_isometric_view(assembly_data)

        # 9. Validate system
        validation_results = self.cad_system.validate_system()
        self.assertTrue(all(validation_results.values()))

        # 10. Get statistics
        stats = self.cad_system.get_system_statistics()
        self.assertIsInstance(stats, dict)

        # Verify that all components have data
        self.assertGreater(stats["precision_system"]["total_points"], 0)
        self.assertGreater(stats["constraint_system"]["total_constraints"], 0)
        self.assertGreater(stats["dimensioning_system"]["total_dimensions"], 0)
        self.assertGreater(stats["parametric_system"]["total_models"], 0)
        self.assertGreater(stats["assembly_manager"]["total_assemblies"], 0)
        self.assertGreater(stats["drawing_view_manager"]["total_views"], 0)

    def test_error_handling(self):
        """Test error handling in the CAD system."""
        # Test invalid constraint type
        with self.assertRaises(ValueError):
            self.cad_system.add_constraint("invalid_type", ["p1", "p2"])

        # Test invalid precision level
        with self.assertRaises(ValueError):
            self.cad_system.set_precision_level("invalid_level")

        # Test adding component to non-existent assembly
        success = self.cad_system.add_component_to_assembly(
            "non_existent", "comp1", "Component 1", "part",
            PrecisionPoint(0, 0, precision_level=PrecisionLevel.COMPUTE)
        )
        self.assertFalse(success)

    def test_performance_operations(self):
        """Test performance with multiple operations."""
        # Create many points
        points = []
        for i in range(100):
            point = self.cad_system.create_point(i, i)
            points.append(point)

        # Create many constraints
        self.cad_system.constraint_system.add_point("origin", {"x": 0, "y": 0})
        for i in range(50):
            self.cad_system.constraint_system.add_point(f"p{i}", {"x": i, "y": i})
            self.cad_system.add_constraint("horizontal", [f"p{i}", "origin"])

        # Create many dimensions
        for i in range(25):
            start_point = PrecisionPoint(i, 0, precision_level=PrecisionLevel.COMPUTE)
            end_point = PrecisionPoint(i + 1, 0, precision_level=PrecisionLevel.COMPUTE)
            self.cad_system.create_linear_dimension(start_point, end_point)

        # Verify system still works
        stats = self.cad_system.get_system_statistics()
        self.assertGreater(stats["precision_system"]["total_points"], 100)
        self.assertGreater(stats["constraint_system"]["total_constraints"], 50)
        self.assertGreater(stats["dimensioning_system"]["total_dimensions"], 25)


if __name__ == "__main__":
    unittest.main()
