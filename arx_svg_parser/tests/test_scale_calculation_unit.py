#!/usr/bin/env python3
"""
Unit Tests for Scale Calculation
Tests scale factor calculations, real-world coordinate conversion, and transformation matrices
"""

import unittest
import json
import math
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the actual scale calculation functions
try:
    from services.transform import (
        calculate_scale_factors,
        convert_to_real_world_coordinates,
        validate_coordinate_system,
        transform_coordinates_batch,
        create_transformation_matrix
    )
    from services.coordinate_validator import validate_coordinates, validate_scale_factors
    SCALE_SERVICES_AVAILABLE = True
except ImportError:
    # Mock the functions if they're not available
    SCALE_SERVICES_AVAILABLE = False
    
    def calculate_scale_factors(anchor_points):
        """Mock scale factor calculation"""
        if len(anchor_points) < 2:
            return {"x": 1.0, "y": 1.0, "uniform": True, "confidence": 0.0}
        
        svg1, real1 = anchor_points[0]["svg"], anchor_points[0]["real"]
        svg2, real2 = anchor_points[1]["svg"], anchor_points[1]["real"]
        
        dx_svg = svg2[0] - svg1[0]
        dy_svg = svg2[1] - svg1[1]
        dx_real = real2[0] - real1[0]
        dy_real = real2[1] - real1[1]
        
        if dx_svg == 0 or dy_svg == 0:
            return {"x": 1.0, "y": 1.0, "uniform": True, "confidence": 0.0}
        
        scale_x = dx_real / dx_svg
        scale_y = dy_real / dy_svg
        
        scale_ratio = abs(scale_x - scale_y) / max(abs(scale_x), abs(scale_y))
        uniform = scale_ratio < 0.01
        
        confidence = min(1.0, len(anchor_points) / 4.0)
        
        return {
            "x": scale_x,
            "y": scale_y,
            "uniform": uniform,
            "confidence": confidence
        }
    
    def convert_to_real_world_coordinates(svg_coordinates, scale_x, scale_y, origin_x=0.0, origin_y=0.0, units="meters"):
        """Mock real-world coordinate conversion"""
        real_world_coords = []
        for coord in svg_coordinates:
            x, y = coord
            real_x = x * scale_x + origin_x
            real_y = y * scale_y + origin_y
            real_world_coords.append([real_x, real_y])
        return real_world_coords
    
    def validate_coordinate_system(anchor_points):
        """Mock coordinate system validation"""
        if len(anchor_points) < 2:
            return {"valid": False, "error": "At least two anchor points required"}
        
        # Check for valid coordinates
        for i, point in enumerate(anchor_points):
            if "svg" not in point or "real" not in point:
                return {"valid": False, "error": f"Invalid anchor point {i}"}
            
            if len(point["svg"]) != 2 or len(point["real"]) != 2:
                return {"valid": False, "error": f"Invalid coordinate format in anchor point {i}"}
        
        return {"valid": True, "errors": [], "warnings": []}
    
    def transform_coordinates_batch(coordinates, source_system, target_system, transformation_matrix=None):
        """Mock coordinate transformation"""
        if transformation_matrix is None:
            transformation_matrix = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        
        transformed_coords = []
        for coord in coordinates:
            x, y = coord
            # Simple matrix transformation
            new_x = transformation_matrix[0][0] * x + transformation_matrix[0][1] * y + transformation_matrix[0][2]
            new_y = transformation_matrix[1][0] * x + transformation_matrix[1][1] * y + transformation_matrix[1][2]
            transformed_coords.append([new_x, new_y])
        
        return transformed_coords
    
    def create_transformation_matrix(scale_x=1.0, scale_y=1.0, rotation=0.0, translation_x=0.0, translation_y=0.0):
        """Mock transformation matrix creation"""
        cos_r = math.cos(math.radians(rotation))
        sin_r = math.sin(math.radians(rotation))
        
        return [
            [scale_x * cos_r, -scale_y * sin_r, translation_x],
            [scale_x * sin_r, scale_y * cos_r, translation_y],
            [0, 0, 1]
        ]
    
    def validate_coordinates(coordinates, system_type):
        """Mock coordinate validation"""
        if not coordinates:
            return {"valid": False, "error": "No coordinates provided"}
        
        for i, coord in enumerate(coordinates):
            if len(coord) != 2:
                return {"valid": False, "error": f"Invalid coordinate format at index {i}"}
            
            if not isinstance(coord[0], (int, float)) or not isinstance(coord[1], (int, float)):
                return {"valid": False, "error": f"Non-numeric coordinates at index {i}"}
        
        return {"valid": True, "errors": []}
    
    def validate_scale_factors(scale_x, scale_y):
        """Mock scale factor validation"""
        if scale_x <= 0 or scale_y <= 0:
            return {"valid": False, "error": "Scale factors must be positive"}
        
        if scale_x > 1000 or scale_y > 1000:
            return {"valid": False, "error": "Scale factors too large"}
        
        return {"valid": True, "errors": []}


class TestScaleCalculationUnit(unittest.TestCase):
    """Unit tests for scale calculation functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Sample anchor points for testing
        self.valid_anchor_points = [
            {"svg": [0, 0], "real": [0, 0]},
            {"svg": [100, 100], "real": [50, 50]},  # 1:2 scale
            {"svg": [200, 200], "real": [100, 100]}  # Consistent scale
        ]
        
        self.uniform_anchor_points = [
            {"svg": [0, 0], "real": [0, 0]},
            {"svg": [100, 100], "real": [50, 50]},  # Uniform 1:2 scale
        ]
        
        self.non_uniform_anchor_points = [
            {"svg": [0, 0], "real": [0, 0]},
            {"svg": [100, 100], "real": [50, 100]},  # Different X and Y scales
        ]
        
        self.invalid_anchor_points = [
            {"svg": [0, 0]},  # Missing real coordinates
            {"svg": [100, 100], "real": [50, 50]}
        ]
        
        # Sample coordinates for testing
        self.test_coordinates = [
            [0, 0],
            [100, 100],
            [200, 200],
            [300, 300]
        ]
    
    def tearDown(self):
        """Clean up test fixtures"""
        pass
    
    def test_scale_factor_calculation_basic(self):
        """Test basic scale factor calculation"""
        scale_factors = calculate_scale_factors(self.uniform_anchor_points)
        
        self.assertIn("x", scale_factors)
        self.assertIn("y", scale_factors)
        self.assertIn("uniform", scale_factors)
        self.assertIn("confidence", scale_factors)
        
        # Should be 1:2 scale (50 real units / 100 SVG units)
        self.assertEqual(scale_factors["x"], 0.5)
        self.assertEqual(scale_factors["y"], 0.5)
        self.assertTrue(scale_factors["uniform"])
        self.assertGreater(scale_factors["confidence"], 0)
    
    def test_scale_factor_calculation_uniform(self):
        """Test uniform scale factor calculation"""
        scale_factors = calculate_scale_factors(self.uniform_anchor_points)
        
        self.assertTrue(scale_factors["uniform"])
        self.assertEqual(scale_factors["x"], scale_factors["y"])
    
    def test_scale_factor_calculation_non_uniform(self):
        """Test non-uniform scale factor calculation"""
        scale_factors = calculate_scale_factors(self.non_uniform_anchor_points)
        
        self.assertFalse(scale_factors["uniform"])
        self.assertNotEqual(scale_factors["x"], scale_factors["y"])
        
        # X scale should be 0.5 (50/100)
        # Y scale should be 1.0 (100/100)
        self.assertEqual(scale_factors["x"], 0.5)
        self.assertEqual(scale_factors["y"], 1.0)
    
    def test_scale_factor_calculation_insufficient_points(self):
        """Test scale factor calculation with insufficient anchor points"""
        insufficient_points = [{"svg": [0, 0], "real": [0, 0]}]
        scale_factors = calculate_scale_factors(insufficient_points)
        
        self.assertEqual(scale_factors["x"], 1.0)
        self.assertEqual(scale_factors["y"], 1.0)
        self.assertTrue(scale_factors["uniform"])
        self.assertEqual(scale_factors["confidence"], 0.0)
    
    def test_scale_factor_calculation_zero_distance(self):
        """Test scale factor calculation with zero distance"""
        zero_distance_points = [
            {"svg": [0, 0], "real": [0, 0]},
            {"svg": [0, 0], "real": [50, 50]}  # Same SVG coordinates
        ]
        scale_factors = calculate_scale_factors(zero_distance_points)
        
        self.assertEqual(scale_factors["x"], 1.0)
        self.assertEqual(scale_factors["y"], 1.0)
        self.assertTrue(scale_factors["uniform"])
        self.assertEqual(scale_factors["confidence"], 0.0)
    
    def test_scale_factor_confidence_calculation(self):
        """Test scale factor confidence calculation"""
        # Test with 2 points (minimum)
        scale_factors_2 = calculate_scale_factors(self.uniform_anchor_points)
        confidence_2 = scale_factors_2["confidence"]
        
        # Test with 3 points (more confidence)
        scale_factors_3 = calculate_scale_factors(self.valid_anchor_points)
        confidence_3 = scale_factors_3["confidence"]
        
        # More points should give higher confidence
        self.assertGreater(confidence_3, confidence_2)
        self.assertLessEqual(confidence_3, 1.0)
        self.assertGreaterEqual(confidence_3, 0.0)
    
    def test_real_world_coordinate_conversion_basic(self):
        """Test basic real-world coordinate conversion"""
        scale_x, scale_y = 0.5, 0.5  # 1:2 scale
        origin_x, origin_y = 10, 20
        
        real_world_coords = convert_to_real_world_coordinates(
            self.test_coordinates, scale_x, scale_y, origin_x, origin_y, "feet"
        )
        
        self.assertEqual(len(real_world_coords), len(self.test_coordinates))
        
        # Test first coordinate: [0, 0] -> [10, 20]
        self.assertEqual(real_world_coords[0], [10, 20])
        
        # Test second coordinate: [100, 100] -> [60, 70]
        self.assertEqual(real_world_coords[1], [60, 70])
        
        # Test third coordinate: [200, 200] -> [110, 120]
        self.assertEqual(real_world_coords[2], [110, 120])
    
    def test_real_world_coordinate_conversion_different_scales(self):
        """Test real-world coordinate conversion with different X and Y scales"""
        scale_x, scale_y = 0.5, 1.0  # Different scales
        origin_x, origin_y = 0, 0
        
        real_world_coords = convert_to_real_world_coordinates(
            self.test_coordinates, scale_x, scale_y, origin_x, origin_y, "meters"
        )
        
        # Test first coordinate: [0, 0] -> [0, 0]
        self.assertEqual(real_world_coords[0], [0, 0])
        
        # Test second coordinate: [100, 100] -> [50, 100]
        self.assertEqual(real_world_coords[1], [50, 100])
        
        # Test third coordinate: [200, 200] -> [100, 200]
        self.assertEqual(real_world_coords[2], [100, 200])
    
    def test_real_world_coordinate_conversion_with_origin(self):
        """Test real-world coordinate conversion with non-zero origin"""
        scale_x, scale_y = 1.0, 1.0  # No scaling
        origin_x, origin_y = 100, 200
        
        real_world_coords = convert_to_real_world_coordinates(
            self.test_coordinates, scale_x, scale_y, origin_x, origin_y, "feet"
        )
        
        # Test first coordinate: [0, 0] -> [100, 200]
        self.assertEqual(real_world_coords[0], [100, 200])
        
        # Test second coordinate: [100, 100] -> [200, 300]
        self.assertEqual(real_world_coords[1], [200, 300])
    
    def test_real_world_coordinate_conversion_empty_input(self):
        """Test real-world coordinate conversion with empty input"""
        with self.assertRaises(Exception):
            convert_to_real_world_coordinates([], 1.0, 1.0)
    
    def test_coordinate_system_validation_valid(self):
        """Test coordinate system validation with valid anchor points"""
        validation_result = validate_coordinate_system(self.valid_anchor_points)
        
        self.assertTrue(validation_result["valid"])
        self.assertIn("errors", validation_result)
        self.assertIn("warnings", validation_result)
    
    def test_coordinate_system_validation_insufficient_points(self):
        """Test coordinate system validation with insufficient anchor points"""
        insufficient_points = [{"svg": [0, 0], "real": [0, 0]}]
        validation_result = validate_coordinate_system(insufficient_points)
        self.assertFalse(validation_result["valid"])
        self.assertTrue(any("anchor" in e.lower() or "point" in e.lower() for e in validation_result["errors"]))
    
    def test_coordinate_system_validation_invalid_format(self):
        """Test coordinate system validation with invalid format"""
        with self.assertRaises(KeyError):
            validate_coordinate_system(self.invalid_anchor_points)
    
    def test_coordinate_transformation_batch_basic(self):
        """Test basic coordinate transformation batch"""
        transformation_matrix = [
            [2, 0, 0, 10],
            [0, 2, 0, 20],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ]  # 4x4 matrix
        transformed_coords = transform_coordinates_batch(
            self.test_coordinates, "svg", "real_world", transformation_matrix
        )
        self.assertEqual(len(transformed_coords), len(self.test_coordinates))
        self.assertEqual(transformed_coords[0], [10, 20])
        self.assertEqual(transformed_coords[1], [210, 220])
    
    def test_coordinate_transformation_batch_identity(self):
        """Test coordinate transformation with identity matrix"""
        identity_matrix = [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ]
        transformed_coords = transform_coordinates_batch(
            self.test_coordinates, "svg", "real_world", identity_matrix
        )
        self.assertEqual(transformed_coords, self.test_coordinates)
    
    def test_coordinate_transformation_batch_no_matrix(self):
        """Test coordinate transformation without transformation matrix"""
        transformed_coords = transform_coordinates_batch(
            self.test_coordinates, "svg", "real_world"
        )
        self.assertEqual(transformed_coords, self.test_coordinates)
    
    def test_transformation_matrix_creation_identity(self):
        """Test transformation matrix creation for identity transformation"""
        matrix = create_transformation_matrix()
        expected_matrix = [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ]
        self.assertEqual(matrix, expected_matrix)
    
    def test_transformation_matrix_creation_scale(self):
        """Test transformation matrix creation for scaling"""
        matrix = create_transformation_matrix(scale_x=2.0, scale_y=3.0)
        expected_matrix = [
            [2.0, -0.0, 0, 0.0],
            [0.0, 3.0, 0, 0.0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ]
        self.assertEqual(matrix, expected_matrix)
    
    def test_transformation_matrix_creation_translation(self):
        """Test transformation matrix creation for translation"""
        matrix = create_transformation_matrix(translation_x=10, translation_y=20)
        expected_matrix = [
            [1.0, -0.0, 0, 10],
            [0.0, 1.0, 0, 20],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ]
        self.assertEqual(matrix, expected_matrix)
    
    def test_transformation_matrix_creation_rotation(self):
        """Test transformation matrix creation for rotation"""
        matrix = create_transformation_matrix(rotation=math.radians(90))
        expected_matrix = [
            [0.0, -1.0, 0, 0.0],
            [1.0, 0.0, 0, 0.0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ]
        for i in range(4):
            for j in range(4):
                self.assertAlmostEqual(matrix[i][j], expected_matrix[i][j], places=6)
    
    def test_transformation_matrix_creation_combined(self):
        """Test transformation matrix creation with combined transformations"""
        matrix = create_transformation_matrix(
            scale_x=2.0, scale_y=3.0, rotation=math.radians(45), translation_x=10, translation_y=20
        )
        self.assertEqual(len(matrix), 4)
        self.assertEqual(len(matrix[0]), 4)
        self.assertEqual(len(matrix[1]), 4)
        self.assertEqual(len(matrix[2]), 4)
        self.assertEqual(len(matrix[3]), 4)
        self.assertNotEqual(matrix, [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
    
    def test_coordinate_validation_valid(self):
        """Test coordinate validation with valid coordinates"""
        validation_result = validate_coordinates(self.test_coordinates, "svg")
        
        self.assertTrue(validation_result["valid"])
        self.assertIn("errors", validation_result)
    
    def test_coordinate_validation_empty(self):
        """Test coordinate validation with empty coordinates"""
        validation_result = validate_coordinates([], "svg")
        self.assertFalse(validation_result["valid"])
        self.assertTrue(any("no coordinates" in e.lower() for e in validation_result["errors"]))
    
    def test_coordinate_validation_invalid_format(self):
        """Test coordinate validation with invalid format"""
        invalid_coordinates = [[0], [100, 100, 100], [200, 200]]
        validation_result = validate_coordinates(invalid_coordinates, "svg")
        self.assertFalse(validation_result["valid"])
        self.assertTrue(any("must be a list of two numbers" in e.lower() for e in validation_result["errors"]))
    
    def test_coordinate_validation_non_numeric(self):
        """Test coordinate validation with non-numeric values"""
        non_numeric_coordinates = [[0, 0], ["100", 100], [200, 200]]
        validation_result = validate_coordinates(non_numeric_coordinates, "svg")
        self.assertFalse(validation_result["valid"])
        self.assertTrue(any("must contain numeric values" in e.lower() for e in validation_result["errors"]))
    
    def test_scale_factor_validation_valid(self):
        """Test scale factor validation with valid factors"""
        validation_result = validate_scale_factors(1.0, 1.0)
        
        self.assertTrue(validation_result["valid"])
        self.assertIn("errors", validation_result)
    
    def test_scale_factor_validation_negative(self):
        """Test scale factor validation with negative factors"""
        validation_result = validate_scale_factors(-1.0, 1.0)
        self.assertFalse(validation_result["valid"])
        self.assertTrue(any("must be positive" in e.lower() for e in validation_result["errors"]))
    
    def test_scale_factor_validation_zero(self):
        """Test scale factor validation with zero factors"""
        validation_result = validate_scale_factors(0.0, 1.0)
        self.assertFalse(validation_result["valid"])
        self.assertTrue(any("must be positive" in e.lower() for e in validation_result["errors"]))
    
    def test_scale_factor_validation_too_large(self):
        """Test scale factor validation with too large factors"""
        # Use a value above the max (10000.0) to trigger the warning
        validation_result = validate_scale_factors(20001, 1.0)
        self.assertTrue(validation_result["valid"])
        self.assertTrue(any("outside recommended range" in w.lower() for w in validation_result["warnings"]))
    
    def test_precision_validation(self):
        """Test precision of scale calculations"""
        # Test with very precise coordinates
        precise_anchor_points = [
            {"svg": [0.000001, 0.000001], "real": [0.000002, 0.000002]},
            {"svg": [100.000001, 100.000001], "real": [200.000002, 200.000002]}
        ]
        
        scale_factors = calculate_scale_factors(precise_anchor_points)
        
        # Should be approximately 2.0
        self.assertAlmostEqual(scale_factors["x"], 2.0, places=6)
        self.assertAlmostEqual(scale_factors["y"], 2.0, places=6)
    
    def test_error_propagation(self):
        """Test error propagation in coordinate conversion"""
        # Test with coordinates that have small errors
        coordinates_with_error = [
            [0.001, 0.001],
            [100.001, 100.001],
            [200.001, 200.001]
        ]
        
        scale_x, scale_y = 0.5, 0.5
        real_world_coords = convert_to_real_world_coordinates(
            coordinates_with_error, scale_x, scale_y
        )
        
        # Errors should be scaled appropriately
        self.assertAlmostEqual(real_world_coords[0][0], 0.0005, places=6)
        self.assertAlmostEqual(real_world_coords[1][0], 50.0005, places=6)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2) 