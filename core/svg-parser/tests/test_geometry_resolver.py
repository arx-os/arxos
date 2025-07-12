"""
Unit tests for Geometry Resolver System

Tests cover:
- Constraint validation
- Conflict detection
- Layout optimization
- 3D collision detection
- Geometric operations
"""

import unittest
import tempfile
import json
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from ..services.geometry_resolver import (
    GeometryResolver, GeometricObject, Constraint, Point3D, BoundingBox,
    ConstraintType, ConflictType, GeometricConflict, ResolutionResult
)


class TestPoint3D(unittest.TestCase):
    """Test Point3D class"""
    
    def test_point_creation(self):
        """Test point creation"""
        point = Point3D(1.0, 2.0, 3.0)
        self.assertEqual(point.x, 1.0)
        self.assertEqual(point.y, 2.0)
        self.assertEqual(point.z, 3.0)
    
    def test_point_distance(self):
        """Test distance calculation"""
        point1 = Point3D(0, 0, 0)
        point2 = Point3D(3, 4, 0)
        distance = point1.distance_to(point2)
        self.assertEqual(distance, 5.0)
    
    def test_point_arithmetic(self):
        """Test point arithmetic operations"""
        point1 = Point3D(1, 2, 3)
        point2 = Point3D(4, 5, 6)
        
        result = point1 + point2
        self.assertEqual(result.x, 5)
        self.assertEqual(result.y, 7)
        self.assertEqual(result.z, 9)
        
        result = point2 - point1
        self.assertEqual(result.x, 3)
        self.assertEqual(result.y, 3)
        self.assertEqual(result.z, 3)


class TestBoundingBox(unittest.TestCase):
    """Test BoundingBox class"""
    
    def test_bbox_creation(self):
        """Test bounding box creation"""
        min_point = Point3D(0, 0, 0)
        max_point = Point3D(10, 10, 10)
        bbox = BoundingBox(min_point, max_point)
        
        self.assertEqual(bbox.min_point, min_point)
        self.assertEqual(bbox.max_point, max_point)
    
    def test_bbox_center(self):
        """Test center calculation"""
        bbox = BoundingBox(Point3D(0, 0, 0), Point3D(10, 10, 10))
        center = bbox.center
        
        self.assertEqual(center.x, 5)
        self.assertEqual(center.y, 5)
        self.assertEqual(center.z, 5)
    
    def test_bbox_size(self):
        """Test size calculation"""
        bbox = BoundingBox(Point3D(0, 0, 0), Point3D(10, 5, 3))
        size = bbox.size
        
        self.assertEqual(size.x, 10)
        self.assertEqual(size.y, 5)
        self.assertEqual(size.z, 3)
    
    def test_bbox_intersection(self):
        """Test intersection detection"""
        bbox1 = BoundingBox(Point3D(0, 0, 0), Point3D(10, 10, 10))
        bbox2 = BoundingBox(Point3D(5, 5, 5), Point3D(15, 15, 15))
        bbox3 = BoundingBox(Point3D(20, 20, 20), Point3D(30, 30, 30))
        
        self.assertTrue(bbox1.intersects(bbox2))
        self.assertFalse(bbox1.intersects(bbox3))
    
    def test_bbox_contains(self):
        """Test point containment"""
        bbox = BoundingBox(Point3D(0, 0, 0), Point3D(10, 10, 10))
        
        inside_point = Point3D(5, 5, 5)
        outside_point = Point3D(15, 15, 15)
        
        self.assertTrue(bbox.contains(inside_point))
        self.assertFalse(bbox.contains(outside_point))


class TestGeometricObject(unittest.TestCase):
    """Test GeometricObject class"""
    
    def test_object_creation(self):
        """Test object creation"""
        obj = GeometricObject(
            object_id="test_obj",
            object_type="wall",
            position=Point3D(0, 0, 0)
        )
        
        self.assertEqual(obj.object_id, "test_obj")
        self.assertEqual(obj.object_type, "wall")
        self.assertEqual(obj.position, Point3D(0, 0, 0))
    
    def test_object_bounding_box(self):
        """Test bounding box generation"""
        obj = GeometricObject(
            object_id="test_obj",
            object_type="wall",
            position=Point3D(5, 5, 5)
        )
        
        bbox = obj.get_bounding_box()
        self.assertEqual(bbox.center, Point3D(5, 5, 5))


class TestConstraint(unittest.TestCase):
    """Test Constraint class"""
    
    def setUp(self):
        """Set up test objects"""
        self.obj1 = GeometricObject(
            object_id="obj1",
            object_type="wall",
            position=Point3D(0, 0, 0)
        )
        self.obj2 = GeometricObject(
            object_id="obj2",
            object_type="door",
            position=Point3D(5, 0, 0)
        )
        self.objects = {"obj1": self.obj1, "obj2": self.obj2}
    
    def test_distance_constraint(self):
        """Test distance constraint evaluation"""
        constraint = Constraint(
            constraint_id="dist_1",
            constraint_type=ConstraintType.DISTANCE,
            objects=["obj1", "obj2"],
            parameters={"distance": 5.0, "tolerance": 0.1}
        )
        
        satisfied, violation = constraint.evaluate(self.objects)
        self.assertTrue(satisfied)
        self.assertLess(violation, 0.1)
    
    def test_alignment_constraint(self):
        """Test alignment constraint evaluation"""
        constraint = Constraint(
            constraint_id="align_1",
            constraint_type=ConstraintType.ALIGNMENT,
            objects=["obj1", "obj2"],
            parameters={"axis": "y", "tolerance": 0.1}
        )
        
        satisfied, violation = constraint.evaluate(self.objects)
        self.assertTrue(satisfied)
        self.assertEqual(violation, 0.0)
    
    def test_clearance_constraint(self):
        """Test clearance constraint evaluation"""
        # Create objects with bounding boxes
        obj1 = GeometricObject(
            object_id="obj1",
            object_type="wall",
            position=Point3D(0, 0, 0),
            bounding_box=BoundingBox(Point3D(-1, -1, 0), Point3D(1, 1, 3))
        )
        obj2 = GeometricObject(
            object_id="obj2",
            object_type="door",
            position=Point3D(3, 0, 0),
            bounding_box=BoundingBox(Point3D(2, -0.5, 0), Point3D(4, 0.5, 2.5))
        )
        objects = {"obj1": obj1, "obj2": obj2}
        
        constraint = Constraint(
            constraint_id="clearance_1",
            constraint_type=ConstraintType.CLEARANCE,
            objects=["obj1", "obj2"],
            parameters={"min_clearance": 0.5}
        )
        
        satisfied, violation = constraint.evaluate(objects)
        self.assertTrue(satisfied)
        self.assertEqual(violation, 0.0)
    
    def test_disabled_constraint(self):
        """Test disabled constraint"""
        constraint = Constraint(
            constraint_id="test",
            constraint_type=ConstraintType.DISTANCE,
            objects=["obj1", "obj2"],
            parameters={"distance": 0.0},
            enabled=False
        )
        
        satisfied, violation = constraint.evaluate(self.objects)
        self.assertTrue(satisfied)
        self.assertEqual(violation, 0.0)


class TestGeometryResolver(unittest.TestCase):
    """Test GeometryResolver class"""
    
    def setUp(self):
        """Set up test resolver"""
        self.resolver = GeometryResolver()
        
        # Create test objects
        self.obj1 = GeometricObject(
            object_id="obj1",
            object_type="wall",
            position=Point3D(0, 0, 0),
            bounding_box=BoundingBox(Point3D(-1, -0.1, 0), Point3D(1, 0.1, 3))
        )
        self.obj2 = GeometricObject(
            object_id="obj2",
            object_type="door",
            position=Point3D(2, 0, 0),
            bounding_box=BoundingBox(Point3D(1.5, -0.05, 0), Point3D(2.5, 0.05, 2.5))
        )
        
        self.resolver.add_object(self.obj1)
        self.resolver.add_object(self.obj2)
    
    def test_add_objects(self):
        """Test adding objects"""
        self.assertEqual(len(self.resolver.objects), 2)
        self.assertIn("obj1", self.resolver.objects)
        self.assertIn("obj2", self.resolver.objects)
    
    def test_add_constraints(self):
        """Test adding constraints"""
        constraint = Constraint(
            constraint_id="test_constraint",
            constraint_type=ConstraintType.DISTANCE,
            objects=["obj1", "obj2"],
            parameters={"distance": 2.0}
        )
        
        self.resolver.add_constraint(constraint)
        self.assertEqual(len(self.resolver.constraints), 1)
        self.assertIn("test_constraint", self.resolver.constraints)
    
    def test_validate_constraints(self):
        """Test constraint validation"""
        constraint = Constraint(
            constraint_id="test_constraint",
            constraint_type=ConstraintType.DISTANCE,
            objects=["obj1", "obj2"],
            parameters={"distance": 2.0, "tolerance": 0.1}
        )
        
        self.resolver.add_constraint(constraint)
        violations = self.resolver.validate_constraints()
        
        # Should have no violations since distance is exactly 2.0
        self.assertEqual(len(violations), 0)
    
    def test_detect_conflicts(self):
        """Test conflict detection"""
        # Create overlapping objects
        obj3 = GeometricObject(
            object_id="obj3",
            object_type="window",
            position=Point3D(0, 0, 0),
            bounding_box=BoundingBox(Point3D(-0.5, -0.5, 0), Point3D(0.5, 0.5, 2))
        )
        self.resolver.add_object(obj3)
        
        conflicts = self.resolver.detect_conflicts()
        self.assertGreater(len(conflicts), 0)
        
        # Check for overlap conflict
        overlap_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.OVERLAP]
        self.assertGreater(len(overlap_conflicts), 0)
    
    def test_resolve_constraints(self):
        """Test constraint resolution"""
        # Create a constraint that needs resolution
        constraint = Constraint(
            constraint_id="test_constraint",
            constraint_type=ConstraintType.DISTANCE,
            objects=["obj1", "obj2"],
            parameters={"distance": 1.0, "tolerance": 0.1}
        )
        
        self.resolver.add_constraint(constraint)
        
        # Initial validation should show violation
        initial_violations = self.resolver.validate_constraints()
        self.assertGreater(len(initial_violations), 0)
        
        # Resolve constraints
        result = self.resolver.resolve_constraints(max_iterations=50, tolerance=0.1)
        
        # Should have attempted resolution
        self.assertGreater(result.iterations, 0)
        self.assertGreater(result.optimization_score, 0)
    
    def test_detect_3d_collisions(self):
        """Test 3D collision detection"""
        # Create objects that collide in 3D
        obj3 = GeometricObject(
            object_id="obj3",
            object_type="beam",
            position=Point3D(0, 0, 1.5),
            bounding_box=BoundingBox(Point3D(-0.5, -0.5, 1), Point3D(0.5, 0.5, 2))
        )
        self.resolver.add_object(obj3)
        
        collisions = self.resolver.detect_3d_collisions()
        self.assertGreater(len(collisions), 0)
        
        # Check for intersection conflicts
        intersection_conflicts = [c for c in collisions if c.conflict_type == ConflictType.INTERSECTION]
        self.assertGreater(len(intersection_conflicts), 0)
    
    def test_optimize_layout(self):
        """Test layout optimization"""
        # Create optimization goals
        goals = {
            'minimize_overlaps': 1.0,
            'minimize_constraint_violations': 1.0,
            'minimize_total_area': 0.5,
            'maximize_alignment': 0.3
        }
        
        result = self.resolver.optimize_layout(goals)
        
        # Should complete optimization
        self.assertIsInstance(result, ResolutionResult)
        # Optimization score can be 0 if no improvements needed
        self.assertGreaterEqual(result.optimization_score, 0)
    
    def test_export_results(self):
        """Test results export"""
        # Add some constraints and resolve
        constraint = Constraint(
            constraint_id="test_constraint",
            constraint_type=ConstraintType.DISTANCE,
            objects=["obj1", "obj2"],
            parameters={"distance": 2.0}
        )
        self.resolver.add_constraint(constraint)
        
        self.resolver.resolve_constraints()
        results = self.resolver.export_results()
        
        # Check export structure
        self.assertIn('timestamp', results)
        self.assertIn('object_count', results)
        self.assertIn('constraint_count', results)
        self.assertIn('conflict_count', results)
        self.assertIn('resolution_history', results)
        self.assertIn('current_violations', results)
        self.assertIn('current_conflicts', results)
        
        self.assertEqual(results['object_count'], 2)
        self.assertEqual(results['constraint_count'], 1)


class TestGeometryResolverCLI(unittest.TestCase):
    """Test GeometryResolverCLI class"""
    
    def setUp(self):
        """Set up test CLI"""
        import sys
        from pathlib import Path
        root_path = str(Path(__file__).parent.parent)
        if root_path not in sys.path:
            sys.path.insert(0, root_path)
        try:
            from ..cmd.geometry_resolver_cli import GeometryResolverCLI
        except ImportError:
            from ..cmd.geometry_resolver_cli import GeometryResolverCLI
        self.cli = GeometryResolverCLI()
    
    def test_create_sample_scene(self):
        """Test sample scene creation"""
        self.cli.create_sample_scene()
        
        self.assertEqual(len(self.cli.resolver.objects), 3)
        self.assertEqual(len(self.cli.resolver.constraints), 2)
        
        # Check object types
        object_types = [obj.object_type for obj in self.cli.resolver.objects.values()]
        self.assertIn("wall", object_types)
        self.assertIn("door", object_types)
        self.assertIn("window", object_types)
    
    def test_save_and_load_scene(self):
        """Test scene save and load"""
        # Create sample scene
        self.cli.create_sample_scene()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            # Save scene
            success = self.cli.save_scene(temp_file)
            self.assertTrue(success)
            
            # Import GeometryResolverCLI for new instance
            try:
                from ..cmd.geometry_resolver_cli import GeometryResolverCLI
            except ImportError:
                from ..cmd.geometry_resolver_cli import GeometryResolverCLI
            # Create new CLI and load scene
            new_cli = GeometryResolverCLI()
            success = new_cli.load_scene(temp_file)
            self.assertTrue(success)
            
            # Check loaded data
            self.assertEqual(len(new_cli.resolver.objects), 3)
            self.assertEqual(len(new_cli.resolver.constraints), 2)
            
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_analyze_geometry(self):
        """Test geometric analysis"""
        self.cli.create_sample_scene()
        
        # Should not raise any exceptions
        self.cli.analyze_geometry()
    
    def test_validate_constraints(self):
        """Test constraint validation"""
        self.cli.create_sample_scene()
        
        # Should not raise any exceptions
        self.cli.validate_constraints()
    
    def test_detect_conflicts(self):
        """Test conflict detection"""
        self.cli.create_sample_scene()
        
        # Should not raise any exceptions
        self.cli.detect_conflicts()
    
    def test_export_results(self):
        """Test results export"""
        self.cli.create_sample_scene()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            self.cli.export_results(temp_file)
            # Check file was created and contains valid JSON
            with open(temp_file, 'r') as f:
                data = json.load(f)
            self.assertIn('timestamp', data)
            self.assertIn('object_count', data)
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestPerformance(unittest.TestCase):
    """Test performance characteristics"""
    
    def test_large_scene_performance(self):
        """Test performance with large number of objects"""
        resolver = GeometryResolver()
        
        # Create 100 objects
        for i in range(100):
            obj = GeometricObject(
                object_id=f"obj_{i}",
                object_type="wall",
                position=Point3D(i, i, 0),
                bounding_box=BoundingBox(
                    Point3D(i-0.5, i-0.5, 0),
                    Point3D(i+0.5, i+0.5, 3)
                )
            )
            resolver.add_object(obj)
        
        # Add some constraints
        for i in range(50):
            constraint = Constraint(
                constraint_id=f"constraint_{i}",
                constraint_type=ConstraintType.DISTANCE,
                objects=[f"obj_{i}", f"obj_{i+1}"],
                parameters={"distance": 1.0}
            )
            resolver.add_constraint(constraint)
        
        # Test performance
        import time
        start_time = time.time()
        
        violations = resolver.validate_constraints()
        conflicts = resolver.detect_conflicts()
        result = resolver.resolve_constraints(max_iterations=10)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time (less than 5 seconds)
        self.assertLess(execution_time, 5.0)
        
        # Should have results
        self.assertIsInstance(result, ResolutionResult)


if __name__ == '__main__':
    unittest.main() 