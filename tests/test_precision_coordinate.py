"""
Unit tests for the PrecisionCoordinate class and related utilities.

Tests all functionality including coordinate validation, transformations,
comparisons, and serialization for the high-precision coordinate system.
"""

import unittest
import math
import json
import struct
import numpy as np
from decimal import Decimal

# Import the module to test
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgx_engine.core.precision_coordinate import (
    PrecisionCoordinate, 
    CoordinateValidator, 
    CoordinateTransformation
)


class TestPrecisionCoordinate(unittest.TestCase):
    """Test cases for the PrecisionCoordinate class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.coord1 = PrecisionCoordinate(1.0, 2.0, 3.0)
        self.coord2 = PrecisionCoordinate(4.0, 5.0, 6.0)
        self.coord3 = PrecisionCoordinate(1.000001, 2.000001, 3.000001)
    
    def test_coordinate_creation(self):
        """Test coordinate creation and basic properties."""
        coord = PrecisionCoordinate(1.0, 2.0, 3.0)
        
        self.assertEqual(coord.x, 1.0)
        self.assertEqual(coord.y, 2.0)
        self.assertEqual(coord.z, 3.0)
        
        # Test with default z value
        coord2d = PrecisionCoordinate(1.0, 2.0)
        self.assertEqual(coord2d.z, 0.0)
    
    def test_coordinate_validation(self):
        """Test coordinate validation for invalid values."""
        # Test NaN values
        with self.assertRaises(ValueError):
            PrecisionCoordinate(float('nan'), 2.0, 3.0)
        
        with self.assertRaises(ValueError):
            PrecisionCoordinate(1.0, float('nan'), 3.0)
        
        with self.assertRaises(ValueError):
            PrecisionCoordinate(1.0, 2.0, float('nan'))
        
        # Test infinite values
        with self.assertRaises(ValueError):
            PrecisionCoordinate(float('inf'), 2.0, 3.0)
        
        with self.assertRaises(ValueError):
            PrecisionCoordinate(1.0, float('-inf'), 3.0)
        
        # Test out of range values
        with self.assertRaises(ValueError):
            PrecisionCoordinate(1e7, 2.0, 3.0)  # Exceeds max range
    
    def test_coordinate_properties(self):
        """Test coordinate properties and conversions."""
        coord = PrecisionCoordinate(3.0, 4.0, 0.0)
        
        # Test as_tuple property
        self.assertEqual(coord.as_tuple, (3.0, 4.0, 0.0))
        
        # Test as_list property
        self.assertEqual(coord.as_list, [3.0, 4.0, 0.0])
        
        # Test magnitude property
        self.assertEqual(coord.magnitude, 5.0)  # sqrt(3^2 + 4^2)
    
    def test_distance_calculation(self):
        """Test distance calculation between coordinates."""
        coord1 = PrecisionCoordinate(0.0, 0.0, 0.0)
        coord2 = PrecisionCoordinate(3.0, 4.0, 0.0)
        
        distance = coord1.distance_to(coord2)
        self.assertEqual(distance, 5.0)  # sqrt(3^2 + 4^2)
        
        # Test 3D distance
        coord3 = PrecisionCoordinate(1.0, 1.0, 1.0)
        distance_3d = coord1.distance_to(coord3)
        expected = math.sqrt(1**2 + 1**2 + 1**2)
        self.assertAlmostEqual(distance_3d, expected, places=6)
    
    def test_coordinate_transformations(self):
        """Test coordinate transformation methods."""
        coord = PrecisionCoordinate(1.0, 0.0, 0.0)
        
        # Test scaling
        scaled = coord.scale(2.0)
        self.assertEqual(scaled.x, 2.0)
        self.assertEqual(scaled.y, 0.0)
        self.assertEqual(scaled.z, 0.0)
        
        # Test translation
        translated = coord.translate(1.0, 2.0, 3.0)
        self.assertEqual(translated.x, 2.0)
        self.assertEqual(translated.y, 2.0)
        self.assertEqual(translated.z, 3.0)
        
        # Test rotation (90 degrees around origin)
        rotated = coord.rotate(math.pi/2)
        self.assertAlmostEqual(rotated.x, 0.0, places=6)
        self.assertAlmostEqual(rotated.y, 1.0, places=6)
        
        # Test rotation around a center point
        center = PrecisionCoordinate(1.0, 1.0, 0.0)
        rotated_around_center = coord.rotate(math.pi/2, center)
        self.assertAlmostEqual(rotated_around_center.x, 2.0, places=6)
        self.assertAlmostEqual(rotated_around_center.y, 1.0, places=6)
    
    def test_complex_transformation(self):
        """Test complex transformation with scale, rotation, and translation."""
        coord = PrecisionCoordinate(1.0, 0.0, 0.0)
        
        # Apply scale=2, rotation=90°, translation=(1,1,0)
        transformed = coord.transform(
            scale=2.0,
            rotation=math.pi/2,
            translation=(1.0, 1.0, 0.0)
        )
        
        # Expected: scale by 2 -> (2,0,0), rotate 90° -> (0,2,0), translate -> (1,3,0)
        self.assertAlmostEqual(transformed.x, 1.0, places=6)
        self.assertAlmostEqual(transformed.y, 3.0, places=6)
        self.assertAlmostEqual(transformed.z, 0.0, places=6)
    
    def test_coordinate_comparisons(self):
        """Test coordinate comparison operations."""
        coord1 = PrecisionCoordinate(1.0, 2.0, 3.0)
        coord2 = PrecisionCoordinate(1.0, 2.0, 3.0)
        coord3 = PrecisionCoordinate(1.000001, 2.000001, 3.000001)
        
        # Test equality with tolerance
        self.assertEqual(coord1, coord2)
        self.assertEqual(coord1, coord3)  # Within tolerance
        
        # Test ordering
        coord_small = PrecisionCoordinate(0.0, 0.0, 0.0)
        coord_large = PrecisionCoordinate(2.0, 2.0, 2.0)
        
        self.assertLess(coord_small, coord1)
        self.assertLess(coord1, coord_large)
        
        # Test is_close_to method
        self.assertTrue(coord1.is_close_to(coord3))
        self.assertFalse(coord1.is_close_to(coord_large))
        
        # Test custom tolerance
        self.assertTrue(coord1.is_close_to(coord3, tolerance=1e-5))
    
    def test_coordinate_serialization(self):
        """Test coordinate serialization and deserialization."""
        coord = PrecisionCoordinate(1.234567, 2.345678, 3.456789)
        
        # Test dictionary serialization
        coord_dict = coord.to_dict()
        self.assertEqual(coord_dict['x'], 1.234567)
        self.assertEqual(coord_dict['y'], 2.345678)
        self.assertEqual(coord_dict['z'], 3.456789)
        self.assertEqual(coord_dict['type'], 'PrecisionCoordinate')
        
        # Test dictionary deserialization
        coord_from_dict = PrecisionCoordinate.from_dict(coord_dict)
        self.assertEqual(coord, coord_from_dict)
        
        # Test JSON serialization
        json_str = coord.to_json()
        coord_from_json = PrecisionCoordinate.from_json(json_str)
        self.assertEqual(coord, coord_from_json)
        
        # Test binary serialization
        serialized = coord.serialize()
        coord_from_binary = PrecisionCoordinate.deserialize(serialized)
        self.assertEqual(coord, coord_from_binary)
        
        # Test invalid binary data
        with self.assertRaises(ValueError):
            PrecisionCoordinate.deserialize(b'invalid')
    
    def test_coordinate_hashing(self):
        """Test coordinate hashing for use in sets and dictionaries."""
        coord1 = PrecisionCoordinate(1.0, 2.0, 3.0)
        coord2 = PrecisionCoordinate(1.0, 2.0, 3.0)
        coord3 = PrecisionCoordinate(4.0, 5.0, 6.0)
        
        # Test that equal coordinates have same hash
        self.assertEqual(hash(coord1), hash(coord2))
        
        # Test that different coordinates have different hashes
        self.assertNotEqual(hash(coord1), hash(coord3))
        
        # Test use in set
        coord_set = {coord1, coord2, coord3}
        self.assertEqual(len(coord_set), 2)  # coord1 and coord2 are equal
    
    def test_string_representations(self):
        """Test string representation methods."""
        coord = PrecisionCoordinate(1.234567, 2.345678, 3.456789)
        
        # Test __repr__
        repr_str = repr(coord)
        self.assertIn('PrecisionCoordinate', repr_str)
        self.assertIn('1.234567', repr_str)
        
        # Test __str__
        str_coord = str(coord)
        self.assertIn('1.234567', str_coord)
        self.assertIn('2.345678', str_coord)
        self.assertIn('3.456789', str_coord)


class TestCoordinateValidator(unittest.TestCase):
    """Test cases for the CoordinateValidator class."""
    
    def test_range_validation(self):
        """Test coordinate range validation."""
        validator = CoordinateValidator()
        
        # Test valid coordinates
        coord_valid = PrecisionCoordinate(100.0, 200.0, 300.0)
        self.assertTrue(validator.validate_coordinate_range(coord_valid))
        
        # Test coordinates at range limits
        coord_limit = PrecisionCoordinate(1e6, 1e6, 1e6)
        self.assertTrue(validator.validate_coordinate_range(coord_limit))
        
        # Test coordinates outside range
        coord_invalid = PrecisionCoordinate(2e6, 2e6, 2e6)
        self.assertFalse(validator.validate_coordinate_range(coord_invalid))
        
        # Test custom range
        coord_custom = PrecisionCoordinate(500.0, 500.0, 500.0)
        self.assertTrue(validator.validate_coordinate_range(coord_custom, 0, 1000))
        self.assertFalse(validator.validate_coordinate_range(coord_custom, 0, 100))
    
    def test_precision_validation(self):
        """Test coordinate precision validation."""
        validator = CoordinateValidator()
        
        # Test coordinates with good precision
        coord_good = PrecisionCoordinate(1.0, 2.0, 3.0)
        self.assertTrue(validator.validate_coordinate_precision(coord_good))
        
        # Test coordinates with poor precision
        coord_poor = PrecisionCoordinate(1.0000001, 2.0000001, 3.0000001)
        self.assertFalse(validator.validate_coordinate_precision(coord_poor, 1e-6))
        
        # Test with custom precision
        coord_custom = PrecisionCoordinate(1.001, 2.001, 3.001)
        self.assertTrue(validator.validate_coordinate_precision(coord_custom, 1e-3))


class TestCoordinateTransformation(unittest.TestCase):
    """Test cases for the CoordinateTransformation class."""
    
    def test_transformation_matrix_creation(self):
        """Test transformation matrix creation."""
        transformer = CoordinateTransformation()
        
        # Test identity matrix
        identity = transformer.create_transformation_matrix()
        expected_identity = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ])
        np.testing.assert_array_almost_equal(identity, expected_identity)
        
        # Test scaling matrix
        scale_matrix = transformer.create_transformation_matrix(scale=2.0)
        expected_scale = np.array([
            [2.0, 0.0, 0.0, 0.0],
            [0.0, 2.0, 0.0, 0.0],
            [0.0, 0.0, 2.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ])
        np.testing.assert_array_almost_equal(scale_matrix, expected_scale)
        
        # Test translation matrix
        trans_matrix = transformer.create_transformation_matrix(translation=(1.0, 2.0, 3.0))
        expected_trans = np.array([
            [1.0, 0.0, 0.0, 1.0],
            [0.0, 1.0, 0.0, 2.0],
            [0.0, 0.0, 1.0, 3.0],
            [0.0, 0.0, 0.0, 1.0]
        ])
        np.testing.assert_array_almost_equal(trans_matrix, expected_trans)
    
    def test_transformation_application(self):
        """Test applying transformation matrices to coordinates."""
        transformer = CoordinateTransformation()
        coord = PrecisionCoordinate(1.0, 0.0, 0.0)
        
        # Test identity transformation
        identity_matrix = transformer.create_transformation_matrix()
        transformed = transformer.apply_transformation(coord, identity_matrix)
        self.assertEqual(transformed, coord)
        
        # Test scaling transformation
        scale_matrix = transformer.create_transformation_matrix(scale=2.0)
        transformed = transformer.apply_transformation(coord, scale_matrix)
        self.assertEqual(transformed.x, 2.0)
        self.assertEqual(transformed.y, 0.0)
        self.assertEqual(transformed.z, 0.0)
        
        # Test translation transformation
        trans_matrix = transformer.create_transformation_matrix(translation=(1.0, 2.0, 3.0))
        transformed = transformer.apply_transformation(coord, trans_matrix)
        self.assertEqual(transformed.x, 2.0)
        self.assertEqual(transformed.y, 2.0)
        self.assertEqual(transformed.z, 3.0)
        
        # Test complex transformation
        complex_matrix = transformer.create_transformation_matrix(
            scale=2.0,
            rotation=math.pi/2,
            translation=(1.0, 1.0, 0.0)
        )
        transformed = transformer.apply_transformation(coord, complex_matrix)
        self.assertAlmostEqual(transformed.x, 1.0, places=6)
        self.assertAlmostEqual(transformed.y, 3.0, places=6)
        self.assertAlmostEqual(transformed.z, 0.0, places=6)


class TestPrecisionCoordinateIntegration(unittest.TestCase):
    """Integration tests for the precision coordinate system."""
    
    def test_precision_accuracy(self):
        """Test that the coordinate system maintains sub-millimeter precision."""
        # Test coordinates with sub-millimeter precision
        coord1 = PrecisionCoordinate(1.000001, 2.000001, 3.000001)
        coord2 = PrecisionCoordinate(1.000002, 2.000002, 3.000002)
        
        # The coordinates should be different but close
        self.assertNotEqual(coord1, coord2)
        self.assertTrue(coord1.is_close_to(coord2, tolerance=1e-5))
        
        # Test that precision is maintained through transformations
        transformed = coord1.transform(scale=1000.0)
        self.assertAlmostEqual(transformed.x, 1000.000001, places=6)
    
    def test_performance_with_large_numbers(self):
        """Test performance with large coordinate values."""
        # Test that the system handles large numbers correctly
        large_coord = PrecisionCoordinate(1e5, 2e5, 3e5)
        
        # Test transformations on large numbers
        scaled = large_coord.scale(0.001)
        self.assertAlmostEqual(scaled.x, 100.0, places=6)
        
        # Test distance calculations with large numbers
        coord2 = PrecisionCoordinate(1e5 + 1, 2e5 + 1, 3e5 + 1)
        distance = large_coord.distance_to(coord2)
        expected_distance = math.sqrt(1**2 + 1**2 + 1**2)
        self.assertAlmostEqual(distance, expected_distance, places=6)
    
    def test_serialization_performance(self):
        """Test serialization performance and correctness."""
        coord = PrecisionCoordinate(1.23456789, 2.34567890, 3.45678901)
        
        # Test multiple serialization cycles
        for _ in range(100):
            # JSON serialization
            json_str = coord.to_json()
            coord_from_json = PrecisionCoordinate.from_json(json_str)
            self.assertEqual(coord, coord_from_json)
            
            # Binary serialization
            binary_data = coord.serialize()
            coord_from_binary = PrecisionCoordinate.deserialize(binary_data)
            self.assertEqual(coord, coord_from_binary)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2) 