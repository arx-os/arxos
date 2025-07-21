#!/usr/bin/env python3
"""
Geometry Resolver CLI Tool

This tool provides command-line interface for:
- Constraint validation
- Conflict detection
- Layout optimization
- 3D collision detection
- Geometric analysis
"""

import argparse
import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List
import time

# Use relative imports for package context
from core.services.geometry_resolver
    GeometryResolver, GeometricObject, Constraint, Point3D, BoundingBox,
    ConstraintType, ConflictType
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeometryResolverCLI:
    """CLI interface for geometry resolution"""
    
    def __init__(self):
        self.resolver = GeometryResolver()
    
    def load_scene(self, scene_file: str) -> bool:
        """Load scene from JSON file"""
        try:
            with open(scene_file, 'r') as f:
                scene_data = json.load(f)
            
            # Load objects
            for obj_data in scene_data.get('objects', []):
                obj = GeometricObject(
                    object_id=obj_data['id'],
                    object_type=obj_data['type'],
                    position=Point3D(**obj_data['position']),
                    rotation=Point3D(**obj_data.get('rotation', {'x': 0, 'y': 0, 'z': 0})),
                    scale=Point3D(**obj_data.get('scale', {'x': 1, 'y': 1, 'z': 1})),
                    properties=obj_data.get('properties', {})
                )
                self.resolver.add_object(obj)
            
            # Load constraints
            for constraint_data in scene_data.get('constraints', []):
                constraint = Constraint(
                    constraint_id=constraint_data['id'],
                    constraint_type=ConstraintType(constraint_data['type']),
                    objects=constraint_data['objects'],
                    parameters=constraint_data.get('parameters', {}),
                    priority=constraint_data.get('priority', 1),
                    enabled=constraint_data.get('enabled', True)
                )
                self.resolver.add_constraint(constraint)
            
            logger.info(f"Loaded {len(self.resolver.objects)} objects and {len(self.resolver.constraints)} constraints")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load scene: {e}")
            return False
    
    def save_scene(self, scene_file: str) -> bool:
        """Save scene to JSON file"""
        try:
            scene_data = {
                'objects': [],
                'constraints': []
            }
            
            # Save objects
            for obj in self.resolver.objects.values():
                obj_data = {
                    'id': obj.object_id,
                    'type': obj.object_type,
                    'position': {'x': obj.position.x, 'y': obj.position.y, 'z': obj.position.z},
                    'rotation': {'x': obj.rotation.x, 'y': obj.rotation.y, 'z': obj.rotation.z},
                    'scale': {'x': obj.scale.x, 'y': obj.scale.y, 'z': obj.scale.z},
                    'properties': obj.properties
                }
                scene_data['objects'].append(obj_data)
            
            # Save constraints
            for constraint in self.resolver.constraints.values():
                constraint_data = {
                    'id': constraint.constraint_id,
                    'type': constraint.constraint_type.value,
                    'objects': constraint.objects,
                    'parameters': constraint.parameters,
                    'priority': constraint.priority,
                    'enabled': constraint.enabled
                }
                scene_data['constraints'].append(constraint_data)
            
            with open(scene_file, 'w') as f:
                json.dump(scene_data, f, indent=2)
            
            logger.info(f"Saved scene to {scene_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save scene: {e}")
            return False
    
    def validate_constraints(self) -> None:
        """Validate all constraints"""
        logger.info("Validating constraints...")
        violations = self.resolver.validate_constraints()
        
        if not violations:
            logger.info("✓ All constraints satisfied")
        else:
            logger.warning(f"✗ Found {len(violations)} constraint violations:")
            for constraint_id, violation in violations:
                logger.warning(f"  - {constraint_id}: violation = {violation:.4f}")
    
    def detect_conflicts(self) -> None:
        """Detect geometric conflicts"""
        logger.info("Detecting conflicts...")
        conflicts = self.resolver.detect_conflicts()
        
        if not conflicts:
            logger.info("✓ No conflicts detected")
        else:
            logger.warning(f"✗ Found {len(conflicts)} conflicts:")
            for conflict in conflicts:
                logger.warning(f"  - {conflict.conflict_id}: {conflict.description}")
                logger.warning(f"    Severity: {conflict.severity:.4f}")
                logger.warning(f"    Objects: {', '.join(conflict.objects)}")
                for suggestion in conflict.resolution_suggestions:
                    logger.warning(f"    Suggestion: {suggestion}")
    
    def resolve_constraints(self, max_iterations: int = 100, tolerance: float = 0.01) -> None:
        """Resolve constraints"""
        logger.info(f"Resolving constraints (max_iterations={max_iterations}, tolerance={tolerance})...")
        
        start_time = time.time()
        result = self.resolver.resolve_constraints(max_iterations, tolerance)
        end_time = time.time()
        
        logger.info(f"Resolution completed in {end_time - start_time:.4f} seconds")
        logger.info(f"Iterations: {result.iterations}")
        logger.info(f"Success: {result.success}")
        logger.info(f"Conflicts resolved: {result.conflicts_resolved}")
        logger.info(f"Conflicts remaining: {result.conflicts_remaining}")
        logger.info(f"Optimization score: {result.optimization_score:.4f}")
        
        if result.final_violations:
            logger.warning("Remaining violations:")
            for constraint_id, violation in result.final_violations:
                logger.warning(f"  - {constraint_id}: {violation:.4f}")
    
    def optimize_layout(self, goals: Dict[str, float]) -> None:
        """Optimize layout"""
        logger.info("Optimizing layout...")
        logger.info(f"Optimization goals: {goals}")
        
        start_time = time.time()
        result = self.resolver.optimize_layout(goals)
        end_time = time.time()
        
        logger.info(f"Optimization completed in {end_time - start_time:.4f} seconds")
        logger.info(f"Success: {result.success}")
        logger.info(f"Conflicts resolved: {result.conflicts_resolved}")
        logger.info(f"Conflicts remaining: {result.conflicts_remaining}")
        logger.info(f"Optimization score: {result.optimization_score:.4f}")
    
    def detect_3d_collisions(self) -> None:
        """Detect 3D collisions"""
        logger.info("Detecting 3D collisions...")
        collisions = self.resolver.detect_3d_collisions()
        
        if not collisions:
            logger.info("✓ No 3D collisions detected")
        else:
            logger.warning(f"✗ Found {len(collisions)} 3D collisions:")
            for collision in collisions:
                logger.warning(f"  - {collision.conflict_id}: {collision.description}")
                logger.warning(f"    Severity: {collision.severity:.4f}")
                logger.warning(f"    Objects: {', '.join(collision.objects)}")
                for suggestion in collision.resolution_suggestions:
                    logger.warning(f"    Suggestion: {suggestion}")
    
    def analyze_geometry(self) -> None:
        """Perform comprehensive geometric analysis"""
        logger.info("Performing geometric analysis...")
        
        # Object statistics
        logger.info(f"Object count: {len(self.resolver.objects)}")
        logger.info(f"Constraint count: {len(self.resolver.constraints)}")
        
        # Bounding box analysis
        if self.resolver.objects:
            bboxes = [obj.get_bounding_box() for obj in self.resolver.objects.values()]
            min_x = min(bbox.min_point.x for bbox in bboxes)
            max_x = max(bbox.max_point.x for bbox in bboxes)
            min_y = min(bbox.min_point.y for bbox in bboxes)
            max_y = max(bbox.max_point.y for bbox in bboxes)
            min_z = min(bbox.min_point.z for bbox in bboxes)
            max_z = max(bbox.max_point.z for bbox in bboxes)
            
            logger.info(f"Scene bounds: X[{min_x:.2f}, {max_x:.2f}], Y[{min_y:.2f}, {max_y:.2f}], Z[{min_z:.2f}, {max_z:.2f}]")
            logger.info(f"Scene dimensions: {max_x-min_x:.2f} x {max_y-min_y:.2f} x {max_z-min_z:.2f}")
        
        # Constraint analysis
        constraint_types = {}
        for constraint in self.resolver.constraints.values():
            constraint_type = constraint.constraint_type.value
            constraint_types[constraint_type] = constraint_types.get(constraint_type, 0) + 1
        
        logger.info("Constraint types:")
        for constraint_type, count in constraint_types.items():
            logger.info(f"  - {constraint_type}: {count}")
        
        # Validation results
        violations = self.resolver.validate_constraints()
        logger.info(f"Constraint violations: {len(violations)}")
        
        # Conflict analysis
        conflicts = self.resolver.detect_conflicts()
        conflict_types = {}
        for conflict in conflicts:
            conflict_type = conflict.conflict_type.value
            conflict_types[conflict_type] = conflict_types.get(conflict_type, 0) + 1
        
        logger.info("Conflict types:")
        for conflict_type, count in conflict_types.items():
            logger.info(f"  - {conflict_type}: {count}")
    
    def export_results(self, output_file: str) -> None:
        """Export analysis results"""
        logger.info(f"Exporting results to {output_file}...")
        
        results = self.resolver.export_results()
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info("Results exported successfully")
    
    def create_sample_scene(self) -> None:
        """Create a sample scene for testing"""
        logger.info("Creating sample scene...")
        
        # Create sample objects
        objects = [
            GeometricObject(
                object_id="obj1",
                object_type="wall",
                position=Point3D(0, 0, 0),
                bounding_box=BoundingBox(
                    Point3D(-1, -0.1, 0),
                    Point3D(1, 0.1, 3)
                )
            ),
            GeometricObject(
                object_id="obj2",
                object_type="door",
                position=Point3D(2, 0, 0),
                bounding_box=BoundingBox(
                    Point3D(1.5, -0.05, 0),
                    Point3D(2.5, 0.05, 2.5)
                )
            ),
            GeometricObject(
                object_id="obj3",
                object_type="window",
                position=Point3D(-2, 0, 1.5),
                bounding_box=BoundingBox(
                    Point3D(-2.5, -0.05, 1),
                    Point3D(-1.5, 0.05, 2)
                )
            )
        ]
        
        for obj in objects:
            self.resolver.add_object(obj)
        
        # Create sample constraints
        constraints = [
            Constraint(
                constraint_id="clearance_1",
                constraint_type=ConstraintType.CLEARANCE,
                objects=["obj1", "obj2"],
                parameters={"min_clearance": 0.5}
            ),
            Constraint(
                constraint_id="alignment_1",
                constraint_type=ConstraintType.ALIGNMENT,
                objects=["obj2", "obj3"],
                parameters={"axis": "y", "tolerance": 0.1}
            )
        ]
        
        for constraint in constraints:
            self.resolver.add_constraint(constraint)
        
        logger.info("Sample scene created with 3 objects and 2 constraints")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Geometry Resolver CLI Tool")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Load scene command
    load_parser = subparsers.add_parser('load', help='Load scene from file')
    load_parser.add_argument('scene_file', help='Scene file path')
    
    # Save scene command
    save_parser = subparsers.add_parser('save', help='Save scene to file')
    save_parser.add_argument('scene_file', help='Scene file path')
    
    # Validate constraints command
    subparsers.add_parser('validate', help='Validate all constraints')
    
    # Detect conflicts command
    subparsers.add_parser('detect-conflicts', help='Detect geometric conflicts')
    
    # Resolve constraints command
    resolve_parser = subparsers.add_parser('resolve', help='Resolve constraints')
    resolve_parser.add_argument('--max-iterations', type=int, default=100, help='Maximum iterations')
    resolve_parser.add_argument('--tolerance', type=float, default=0.01, help='Tolerance for convergence')
    
    # Optimize layout command
    optimize_parser = subparsers.add_parser('optimize', help='Optimize layout')
    optimize_parser.add_argument('--minimize-overlaps', type=float, default=1.0, help='Weight for minimizing overlaps')
    optimize_parser.add_argument('--minimize-violations', type=float, default=1.0, help='Weight for minimizing violations')
    optimize_parser.add_argument('--minimize-area', type=float, default=0.5, help='Weight for minimizing area')
    optimize_parser.add_argument('--maximize-alignment', type=float, default=0.3, help='Weight for maximizing alignment')
    
    # Detect 3D collisions command
    subparsers.add_parser('detect-collisions', help='Detect 3D collisions')
    
    # Analyze geometry command
    subparsers.add_parser('analyze', help='Perform geometric analysis')
    
    # Export results command
    export_parser = subparsers.add_parser('export', help='Export analysis results')
    export_parser.add_argument('output_file', help='Output file path')
    
    # Create sample scene command
    subparsers.add_parser('create-sample', help='Create sample scene for testing')
    
    # Comprehensive analysis command
    subparsers.add_parser('comprehensive', help='Run comprehensive analysis')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = GeometryResolverCLI()
    
    try:
        if args.command == 'load':
            if not cli.load_scene(args.scene_file):
                sys.exit(1)
        
        elif args.command == 'save':
            if not cli.save_scene(args.scene_file):
                sys.exit(1)
        
        elif args.command == 'validate':
            cli.validate_constraints()
        
        elif args.command == 'detect-conflicts':
            cli.detect_conflicts()
        
        elif args.command == 'resolve':
            cli.resolve_constraints(args.max_iterations, args.tolerance)
        
        elif args.command == 'optimize':
            goals = {
                'minimize_overlaps': args.minimize_overlaps,
                'minimize_constraint_violations': args.minimize_violations,
                'minimize_total_area': args.minimize_area,
                'maximize_alignment': args.maximize_alignment
            }
            cli.optimize_layout(goals)
        
        elif args.command == 'detect-collisions':
            cli.detect_3d_collisions()
        
        elif args.command == 'analyze':
            cli.analyze_geometry()
        
        elif args.command == 'export':
            cli.export_results(args.output_file)
        
        elif args.command == 'create-sample':
            cli.create_sample_scene()
        
        elif args.command == 'comprehensive':
            logger.info("Running comprehensive analysis...")
            cli.analyze_geometry()
            cli.validate_constraints()
            cli.detect_conflicts()
            cli.detect_3d_collisions()
            cli.resolve_constraints()
            logger.info("Comprehensive analysis completed")
    
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 