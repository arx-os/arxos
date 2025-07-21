"""
Tests for enhanced geometry processing functionality.

This module tests:
- 3D geometry generation from 2D SVG
- Coordinate system transformations
- Geometric validation and error correction
- Geometry optimization algorithms
"""

import unittest
import math
import numpy as np
from typing import Dict, Any

from core.services.geometry_resolver
    GeometryProcessor, GeometryOptimizer,
    CoordinateSystem, ValidationError, GeometryType
)


class TestGeometryProcessing(unittest.TestCase):
    """Test cases for geometry processing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = GeometryProcessor()
        self.optimizer = GeometryOptimizer()
        
        # Test SVG geometries
        self.svg_polygon = {
            'type': 'polygon',
            'coordinates': [[0, 0], [10, 0], [10, 10], [0, 10]]
        }
        
        self.svg_line = {
            'type': 'line',
            'coordinates': [[0, 0], [10, 0], [10, 10], [0, 10]]
        }
        
        self.svg_circle = {
            'type': 'circle',
            'coordinates': [5, 5],
            'radius': 3.0
        }
        
        self.svg_rect = {
            'type': 'rect',
            'x': 0, 'y': 0,
            'width': 10, 'height': 8
        }
        
        self.svg_point = {
            'type': 'point',
            'coordinates': [5, 5]
        }
    
    def test_3d_generation_from_2d_svg(self):
        """Test 3D geometry generation from 2D SVG."""
        # Test polygon extrusion
        result = self.processor.generate_3d_from_2d_svg(self.svg_polygon, height=3.0)
        self.assertEqual(result['type'], 'polyhedron')
        self.assertIn('faces', result)
        self.assertIn('volume', result)
        self.assertIn('surface_area', result)
        
        # Test line extrusion
        result = self.processor.generate_3d_from_2d_svg(self.svg_line, height=2.0)
        self.assertEqual(result['type'], 'extrusion')
        self.assertIn('segments', result)
        self.assertIn('length', result)
        self.assertIn('volume', result)
        
        # Test circle extrusion
        result = self.processor.generate_3d_from_2d_svg(self.svg_circle, height=4.0)
        self.assertEqual(result['type'], 'cylinder')
        self.assertIn('center', result)
        self.assertIn('radius', result)
        self.assertIn('height', result)
        self.assertIn('volume', result)
        self.assertIn('surface_area', result)
        
        # Test rectangle extrusion
        result = self.processor.generate_3d_from_2d_svg(self.svg_rect, height=5.0)
        self.assertEqual(result['type'], 'box')
        self.assertIn('min_point', result)
        self.assertIn('max_point', result)
        self.assertIn('volume', result)
        self.assertIn('surface_area', result)
        
        # Test point conversion
        result = self.processor.generate_3d_from_2d_svg(self.svg_point, height=1.0)
        self.assertEqual(result['type'], 'point_3d')
        self.assertIn('coordinates', result)
        self.assertEqual(len(result['coordinates']), 3)
    
    def test_coordinate_system_transformations(self):
        """Test coordinate system transformations."""
        # Test SVG to BIM transformation
        geometry = {
            'type': 'point_3d',
            'coordinates': [100, 200, 0]
        }
        
        result = self.processor.transform_coordinate_system(
            geometry,
            CoordinateSystem.SVG_2D,
            CoordinateSystem.BIM_3D,
            {'x': 0.01, 'y': 0.01, 'z': 1.0}
        )
        
        self.assertEqual(result['type'], 'point_3d')
        self.assertEqual(len(result['coordinates']), 3)
        
        # Test meters to feet transformation
        geometry = {
            'type': 'polygon_3d',
            'coordinates': [[1, 2, 0], [3, 2, 0], [3, 4, 0], [1, 4, 0]]
        }
        
        result = self.processor.transform_coordinate_system(
            geometry,
            CoordinateSystem.REAL_WORLD_METERS,
            CoordinateSystem.REAL_WORLD_FEET
        )
        
        self.assertEqual(result['type'], 'polygon_3d')
        self.assertIn('coordinates', result)
        
        # Test with invalid transformation (should return original)
        result = self.processor.transform_coordinate_system(
            geometry,
            CoordinateSystem.SVG_2D,
            CoordinateSystem.REAL_WORLD_FEET
        )
        
        self.assertEqual(result['type'], 'polygon_3d')
    
    def test_geometric_validation(self):
        """Test geometric validation and error correction."""
        # Test valid geometry
        valid_geometry = {
            'type': 'polygon_2d',
            'coordinates': [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]
        }

        validation_result = self.processor._validate_geometry(valid_geometry)
        print('VALIDATION RESULT:', validation_result)
        self.assertTrue(validation_result['valid'])
        self.assertEqual(len(validation_result['errors']), 0)
        
        # Test invalid coordinates
        invalid_geometry = {
            'type': 'point_3d',
            'coordinates': [float('inf'), 5, 0]
        }
        
        validation_result = self.processor._validate_geometry(invalid_geometry)
        self.assertFalse(validation_result['valid'])
        self.assertIn(ValidationError.INVALID_COORDINATES.value, validation_result['errors'])
        self.assertGreater(len(validation_result['corrections']), 0)
        
        # Test non-closed polygon
        non_closed_geometry = {
            'type': 'polygon_2d',
            'coordinates': [[0, 0], [10, 0], [10, 10], [0, 10]]
        }
        
        validation_result = self.processor._validate_geometry(non_closed_geometry)
        self.assertFalse(validation_result['valid'])
        self.assertIn(ValidationError.NON_CLOSED_POLYGON.value, validation_result['errors'])
        self.assertGreater(len(validation_result['corrections']), 0)
        
        # Test zero area polygon
        zero_area_geometry = {
            'type': 'polygon_2d',
            'coordinates': [[0, 0], [0, 0], [0, 0], [0, 0]]
        }
        
        validation_result = self.processor._validate_geometry(zero_area_geometry)
        self.assertTrue(validation_result['valid'])  # Valid but with warning
        self.assertIn(ValidationError.ZERO_AREA.value, validation_result['warnings'])
    
    def test_geometry_optimization(self):
        """Test geometry optimization algorithms."""
        # Test polyhedron optimization
        polyhedron_geometry = {
            'type': 'polyhedron',
            'faces': [
                [[0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0]],
                [[0, 0, 5], [10, 0, 5], [10, 10, 5], [0, 10, 5]]
            ]
        }
        
        optimized = self.optimizer.optimize_mesh(polyhedron_geometry, 'medium')
        self.assertEqual(optimized['type'], 'polyhedron')
        self.assertIn('optimization_level', optimized)
        
        # Test extrusion optimization
        extrusion_geometry = {
            'type': 'extrusion',
            'segments': [
                [[0, 0, 0], [10, 0, 0], [10, 0, 5], [0, 0, 5]],
                [[10, 0, 0], [10, 10, 0], [10, 10, 5], [10, 0, 5]]
            ]
        }
        
        optimized = self.optimizer.optimize_mesh(extrusion_geometry, 'high')
        self.assertEqual(optimized['type'], 'extrusion')
        self.assertIn('optimization_level', optimized)
        
        # Test primitive optimization
        primitive_geometry = {
            'type': 'cylinder',
            'center': [5, 5, 2.5],
            'radius': 3.0,
            'height': 5.0
        }
        
        optimized = self.optimizer.optimize_mesh(primitive_geometry, 'low')
        self.assertEqual(optimized['type'], 'cylinder')
        self.assertIn('optimization_level', optimized)
    
    def test_lod_generation(self):
        """Test level of detail (LOD) generation."""
        geometry = {
            'type': 'polyhedron',
            'faces': [
                [[0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0]],
                [[0, 0, 5], [10, 0, 5], [10, 10, 5], [0, 10, 5]]
            ]
        }
        
        lod_levels = self.optimizer.generate_lod(geometry, ['low', 'medium', 'high'])
        
        self.assertIn('low', lod_levels)
        self.assertIn('medium', lod_levels)
        self.assertIn('high', lod_levels)
        
        for level, optimized_geometry in lod_levels.items():
            self.assertEqual(optimized_geometry['type'], 'polyhedron')
            self.assertIn('optimization_level', optimized_geometry)
    
    def test_optimization_metrics(self):
        """Test optimization metrics calculation."""
        original_geometry = {
            'type': 'polyhedron',
            'faces': [
                [[0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0]],
                [[0, 0, 5], [10, 0, 5], [10, 10, 5], [0, 10, 5]]
            ]
        }
        
        optimized_geometry = {
            'type': 'polyhedron',
            'faces': [
                [[0, 0, 0], [10, 0, 0], [0, 10, 0]],
                [[0, 0, 5], [10, 0, 5], [0, 10, 5]]
            ]
        }
        
        metrics = self.optimizer.calculate_optimization_metrics(original_geometry, optimized_geometry)
        
        self.assertIn('original_vertices', metrics)
        self.assertIn('optimized_vertices', metrics)
        self.assertIn('reduction_ratio', metrics)
        self.assertIn('compression_efficiency', metrics)
        
        self.assertGreater(metrics['reduction_ratio'], 0)
        self.assertLessEqual(metrics['reduction_ratio'], 1.0)
    
    def test_batch_processing(self):
        """Test batch processing of geometries."""
        geometries = [
            self.svg_polygon,
            self.svg_line,
            self.svg_circle,
            self.svg_rect
        ]
        
        # Test batch processing with validation and optimization
        processed = self.processor.batch_process_geometry(
            geometries,
            operations=['validate', 'optimize']
        )
        
        self.assertEqual(len(processed), len(geometries))
        
        for processed_geometry in processed:
            self.assertIsInstance(processed_geometry, dict)
            self.assertIn('type', processed_geometry)
    
    def test_polygon_simplification(self):
        """Test polygon simplification using Douglas-Peucker algorithm."""
        # Create a complex polygon
        complex_polygon = [
            [0, 0], [1, 0.1], [2, 0], [3, 0.1], [4, 0],
            [4, 1], [3, 0.9], [2, 1], [1, 0.9], [0, 1]
        ]
        
        simplified = self.optimizer._simplify_polygon(complex_polygon, tolerance=0.2)
        
        self.assertLessEqual(len(simplified), len(complex_polygon))
        self.assertGreaterEqual(len(simplified), 3)  # Minimum 3 vertices for polygon
        
        # Test with simple polygon (should remain unchanged)
        simple_polygon = [[0, 0], [10, 0], [10, 10], [0, 10]]
        simplified = self.optimizer._simplify_polygon(simple_polygon, tolerance=0.1)
        self.assertEqual(len(simplified), len(simple_polygon))
    
    def test_line_segment_simplification(self):
        """Test line segment simplification."""
        # Create a complex 3D line segment
        complex_segment = [
            [0, 0, 0], [1, 0.1, 0], [2, 0, 0], [3, 0.1, 0], [4, 0, 0]
        ]
        
        simplified = self.optimizer._simplify_line_segment(complex_segment, tolerance=0.2)
        
        self.assertLessEqual(len(simplified), len(complex_segment))
        self.assertGreaterEqual(len(simplified), 2)  # Minimum 2 points for line
        
        # Verify Z coordinates are preserved
        for point in simplified:
            self.assertEqual(len(point), 3)
    
    def test_vertex_counting(self):
        """Test vertex counting functionality."""
        # Test polyhedron
        polyhedron = {
            'type': 'polyhedron',
            'faces': [
                [[0, 0, 0], [10, 0, 0], [10, 10, 0]],
                [[0, 0, 5], [10, 0, 5], [10, 10, 5]]
            ]
        }
        
        vertex_count = self.optimizer._count_vertices(polyhedron)
        self.assertEqual(vertex_count, 6)  # 3 vertices per face * 2 faces
        
        # Test extrusion
        extrusion = {
            'type': 'extrusion',
            'segments': [
                [[0, 0, 0], [10, 0, 0], [10, 0, 5]],
                [[10, 0, 0], [10, 10, 0], [10, 10, 5]]
            ]
        }
        
        vertex_count = self.optimizer._count_vertices(extrusion)
        self.assertEqual(vertex_count, 6)  # 3 vertices per segment * 2 segments
        
        # Test point
        point = {
            'type': 'point_3d',
            'coordinates': [5, 5, 0]
        }
        
        vertex_count = self.optimizer._count_vertices(point)
        self.assertEqual(vertex_count, 1)
    
    def test_error_handling(self):
        """Test error handling in geometry processing."""
        # Test with empty geometry
        empty_geometry = {}
        result = self.processor.generate_3d_from_2d_svg(empty_geometry)
        self.assertEqual(result['type'], 'point_3d')
        
        # Test with invalid geometry type
        invalid_geometry = {'type': 'invalid_type'}
        result = self.processor.generate_3d_from_2d_svg(invalid_geometry)
        self.assertEqual(result['type'], 'point_3d')
        
        # Test transformation with invalid coordinates
        invalid_coords_geometry = {
            'type': 'point_3d',
            'coordinates': [float('nan'), 5, 0]
        }
        
        result = self.processor.transform_coordinate_system(
            invalid_coords_geometry,
            CoordinateSystem.SVG_2D,
            CoordinateSystem.BIM_3D
        )
        
        # Should handle gracefully
        self.assertIn('coordinates', result)
    
    def test_performance_optimization(self):
        """Test performance optimization features."""
        # Create a large geometry for testing
        large_polygon = {
            'type': 'polygon',
            'coordinates': [[i, i] for i in range(100)]  # 100 vertices
        }
        
        # Test optimization at different levels
        for level in ['low', 'medium', 'high']:
            optimized = self.optimizer.optimize_mesh(large_polygon, level)
            self.assertIn('optimization_level', optimized)
            
            # Verify optimization reduces complexity
            if level == 'high':
                # High optimization should significantly reduce vertices
                original_vertices = len(large_polygon['coordinates'])
                optimized_vertices = self.optimizer._count_vertices(optimized)
                self.assertLess(optimized_vertices, original_vertices)


if __name__ == '__main__':
    unittest.main() 