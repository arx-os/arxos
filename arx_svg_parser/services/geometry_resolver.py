"""
Enhanced Geometry Resolution System

This module provides:
- 3D geometry generation from 2D SVG
- Coordinate system transformations
- Geometric validation and error correction
- Geometry optimization algorithms
- Spatial constraint validation
- Geometric conflict detection
- Automatic layout optimization
- 3D collision detection
- Constraint satisfaction algorithms
"""

import math
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from datetime import datetime
import logging
from ..utils.errors import GeometryError, ValidationError
from ..utils.response_helpers import ResponseHelper

logger = logging.getLogger(__name__)

class CoordinateSystem(Enum):
    """Supported coordinate systems"""
    SVG_2D = "svg_2d"
    BIM_3D = "bim_3d"
    REAL_WORLD_METERS = "real_world_meters"
    REAL_WORLD_FEET = "real_world_feet"

class GeometryType(Enum):
    """Types of geometry"""
    POINT_2D = "point_2d"
    POINT_3D = "point_3d"
    LINE_2D = "line_2d"
    LINE_3D = "line_3d"
    POLYGON_2D = "polygon_2d"
    POLYGON_3D = "polygon_3d"
    POLYHEDRON = "polyhedron"
    EXTRUSION = "extrusion"
    REVOLUTION = "revolution"

class ValidationError(Enum):
    """Types of geometric validation errors"""
    INVALID_COORDINATES = "invalid_coordinates"
    SELF_INTERSECTING = "self_intersecting"
    NON_CLOSED_POLYGON = "non_closed_polygon"
    ZERO_AREA = "zero_area"
    ZERO_VOLUME = "zero_volume"
    INVALID_TRANSFORMATION = "invalid_transformation"
    SCALE_TOO_SMALL = "scale_too_small"
    SCALE_TOO_LARGE = "scale_too_large"


class ConstraintType(Enum):
    """Types of geometric constraints"""
    DISTANCE = "distance"
    ALIGNMENT = "alignment"
    PARALLEL = "parallel"
    PERPENDICULAR = "perpendicular"
    ANGLE = "angle"
    CLEARANCE = "clearance"
    CONTAINMENT = "containment"
    INTERSECTION = "intersection"
    MIN_SIZE = "min_size"
    MAX_SIZE = "max_size"


class ConflictType(Enum):
    """Types of geometric conflicts"""
    OVERLAP = "overlap"
    INTERSECTION = "intersection"
    CLEARANCE_VIOLATION = "clearance_violation"
    SIZE_VIOLATION = "size_violation"
    ALIGNMENT_VIOLATION = "alignment_violation"
    ANGLE_VIOLATION = "angle_violation"


@dataclass
class Point3D:
    """3D point representation"""
    x: float
    y: float
    z: float
    
    def distance_to(self, other: 'Point3D') -> float:
        """Calculate distance to another point"""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2 + (self.z - other.z)**2)
    
    def __add__(self, other: 'Point3D') -> 'Point3D':
        return Point3D(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other: 'Point3D') -> 'Point3D':
        return Point3D(self.x - other.x, self.y - other.y, self.z - other.z)


@dataclass
class BoundingBox:
    """3D bounding box"""
    min_point: Point3D
    max_point: Point3D
    
    @property
    def center(self) -> Point3D:
        """Get center point of bounding box"""
        return Point3D(
            (self.min_point.x + self.max_point.x) / 2,
            (self.min_point.y + self.max_point.y) / 2,
            (self.min_point.z + self.max_point.z) / 2
        )
    
    @property
    def size(self) -> Point3D:
        """Get size of bounding box"""
        return Point3D(
            self.max_point.x - self.min_point.x,
            self.max_point.y - self.min_point.y,
            self.max_point.z - self.min_point.z
        )
    
    def intersects(self, other: 'BoundingBox') -> bool:
        """Check if this bounding box intersects with another"""
        return not (
            self.max_point.x < other.min_point.x or
            self.min_point.x > other.max_point.x or
            self.max_point.y < other.min_point.y or
            self.min_point.y > other.max_point.y or
            self.max_point.z < other.min_point.z or
            self.min_point.z > other.max_point.z
        )
    
    def contains(self, point: Point3D) -> bool:
        """Check if point is inside bounding box"""
        return (
            self.min_point.x <= point.x <= self.max_point.x and
            self.min_point.y <= point.y <= self.max_point.y and
            self.min_point.z <= point.z <= self.max_point.z
        )


@dataclass
class GeometricObject:
    """Base geometric object"""
    object_id: str
    object_type: str
    position: Point3D
    rotation: Point3D = field(default_factory=lambda: Point3D(0, 0, 0))
    scale: Point3D = field(default_factory=lambda: Point3D(1, 1, 1))
    bounding_box: Optional[BoundingBox] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def get_bounding_box(self) -> BoundingBox:
        """Get bounding box of the object"""
        if self.bounding_box:
            return self.bounding_box
        # Default bounding box
        size = Point3D(1, 1, 1)  # Default size
        return BoundingBox(
            Point3D(self.position.x - size.x/2, self.position.y - size.y/2, self.position.z - size.z/2),
            Point3D(self.position.x + size.x/2, self.position.y + size.y/2, self.position.z + size.z/2)
        )


@dataclass
class Constraint:
    """Geometric constraint definition"""
    constraint_id: str
    constraint_type: ConstraintType
    objects: List[str]  # Object IDs involved in constraint
    parameters: Dict[str, Any]  # Constraint parameters (distance, angle, etc.)
    priority: int = 1  # Constraint priority (higher = more important)
    enabled: bool = True
    
    def evaluate(self, objects: Dict[str, GeometricObject]) -> Tuple[bool, float]:
        """Evaluate constraint satisfaction"""
        if not self.enabled:
            return True, 0.0
        
        obj_list = [objects[obj_id] for obj_id in self.objects if obj_id in objects]
        if len(obj_list) < 2:
            return True, 0.0
        
        if self.constraint_type == ConstraintType.DISTANCE:
            return self._evaluate_distance(obj_list)
        elif self.constraint_type == ConstraintType.ALIGNMENT:
            return self._evaluate_alignment(obj_list)
        elif self.constraint_type == ConstraintType.PARALLEL:
            return self._evaluate_parallel(obj_list)
        elif self.constraint_type == ConstraintType.PERPENDICULAR:
            return self._evaluate_perpendicular(obj_list)
        elif self.constraint_type == ConstraintType.ANGLE:
            return self._evaluate_angle(obj_list)
        elif self.constraint_type == ConstraintType.CLEARANCE:
            return self._evaluate_clearance(obj_list)
        elif self.constraint_type == ConstraintType.CONTAINMENT:
            return self._evaluate_containment(obj_list)
        elif self.constraint_type == ConstraintType.INTERSECTION:
            return self._evaluate_intersection(obj_list)
        elif self.constraint_type == ConstraintType.MIN_SIZE:
            return self._evaluate_min_size(obj_list)
        elif self.constraint_type == ConstraintType.MAX_SIZE:
            return self._evaluate_max_size(obj_list)
        
        return True, 0.0
    
    def _evaluate_distance(self, objects: List[GeometricObject]) -> Tuple[bool, float]:
        """Evaluate distance constraint"""
        target_distance = self.parameters.get('distance', 0.0)
        tolerance = self.parameters.get('tolerance', 0.1)
        
        actual_distance = objects[0].position.distance_to(objects[1].position)
        deviation = abs(actual_distance - target_distance)
        
        return deviation <= tolerance, deviation
    
    def _evaluate_alignment(self, objects: List[GeometricObject]) -> Tuple[bool, float]:
        """Evaluate alignment constraint"""
        axis = self.parameters.get('axis', 'x')  # x, y, z
        tolerance = self.parameters.get('tolerance', 0.1)
        
        if axis == 'x':
            deviation = abs(objects[0].position.x - objects[1].position.x)
        elif axis == 'y':
            deviation = abs(objects[0].position.y - objects[1].position.y)
        else:  # z
            deviation = abs(objects[0].position.z - objects[1].position.z)
        
        return deviation <= tolerance, deviation
    
    def _evaluate_parallel(self, objects: List[GeometricObject]) -> Tuple[bool, float]:
        """Evaluate parallel constraint"""
        tolerance = self.parameters.get('tolerance', 0.1)
        
        # Simplified: check if rotation angles are similar
        angle_diff = abs(objects[0].rotation.z - objects[1].rotation.z)
        return angle_diff <= tolerance, angle_diff
    
    def _evaluate_perpendicular(self, objects: List[GeometricObject]) -> Tuple[bool, float]:
        """Evaluate perpendicular constraint"""
        tolerance = self.parameters.get('tolerance', 0.1)
        
        # Simplified: check if rotation angles differ by 90 degrees
        angle_diff = abs(abs(objects[0].rotation.z - objects[1].rotation.z) - math.pi/2)
        return angle_diff <= tolerance, angle_diff
    
    def _evaluate_angle(self, objects: List[GeometricObject]) -> Tuple[bool, float]:
        """Evaluate angle constraint"""
        target_angle = self.parameters.get('angle', 0.0)
        tolerance = self.parameters.get('tolerance', 0.1)
        
        actual_angle = abs(objects[0].rotation.z - objects[1].rotation.z)
        deviation = abs(actual_angle - target_angle)
        
        return deviation <= tolerance, deviation
    
    def _evaluate_clearance(self, objects: List[GeometricObject]) -> Tuple[bool, float]:
        """Evaluate clearance constraint"""
        min_clearance = self.parameters.get('min_clearance', 0.0)
        
        bbox1 = objects[0].get_bounding_box()
        bbox2 = objects[1].get_bounding_box()
        
        # Calculate minimum distance between bounding boxes
        min_distance = self._calculate_bbox_distance(bbox1, bbox2)
        violation = max(0, min_clearance - min_distance)
        
        return violation == 0, violation
    
    def _evaluate_containment(self, objects: List[GeometricObject]) -> Tuple[bool, float]:
        """Evaluate containment constraint"""
        bbox1 = objects[0].get_bounding_box()
        bbox2 = objects[1].get_bounding_box()
        
        # Check if bbox2 is contained within bbox1
        contained = (
            bbox1.min_point.x <= bbox2.min_point.x and
            bbox1.max_point.x >= bbox2.max_point.x and
            bbox1.min_point.y <= bbox2.min_point.y and
            bbox1.max_point.y >= bbox2.max_point.y and
            bbox1.min_point.z <= bbox2.min_point.z and
            bbox1.max_point.z >= bbox2.max_point.z
        )
        
        return contained, 0.0 if contained else 1.0
    
    def _evaluate_intersection(self, objects: List[GeometricObject]) -> Tuple[bool, float]:
        """Evaluate intersection constraint"""
        bbox1 = objects[0].get_bounding_box()
        bbox2 = objects[1].get_bounding_box()
        
        intersecting = bbox1.intersects(bbox2)
        return intersecting, 0.0 if intersecting else 1.0
    
    def _evaluate_min_size(self, objects: List[GeometricObject]) -> Tuple[bool, float]:
        """Evaluate minimum size constraint"""
        min_size = self.parameters.get('min_size', Point3D(0, 0, 0))
        
        bbox = objects[0].get_bounding_box()
        size = bbox.size
        
        violations = [
            max(0, min_size.x - size.x),
            max(0, min_size.y - size.y),
            max(0, min_size.z - size.z)
        ]
        
        total_violation = sum(violations)
        return total_violation == 0, total_violation
    
    def _evaluate_max_size(self, objects: List[GeometricObject]) -> Tuple[bool, float]:
        """Evaluate maximum size constraint"""
        max_size = self.parameters.get('max_size', Point3D(float('inf'), float('inf'), float('inf')))
        
        bbox = objects[0].get_bounding_box()
        size = bbox.size
        
        violations = [
            max(0, size.x - max_size.x),
            max(0, size.y - max_size.y),
            max(0, size.z - max_size.z)
        ]
        
        total_violation = sum(violations)
        return total_violation == 0, total_violation
    
    def _calculate_bbox_distance(self, bbox1: BoundingBox, bbox2: BoundingBox) -> float:
        """Calculate minimum distance between two bounding boxes"""
        if bbox1.intersects(bbox2):
            return 0.0
        
        # Calculate minimum distance along each axis
        dx = max(0, bbox1.min_point.x - bbox2.max_point.x, bbox2.min_point.x - bbox1.max_point.x)
        dy = max(0, bbox1.min_point.y - bbox2.max_point.y, bbox2.min_point.y - bbox1.max_point.y)
        dz = max(0, bbox1.min_point.z - bbox2.max_point.z, bbox2.min_point.z - bbox1.max_point.z)
        
        return math.sqrt(dx*dx + dy*dy + dz*dz)


@dataclass
class GeometricConflict:
    """Geometric conflict between objects"""
    conflict_id: str
    conflict_type: ConflictType
    objects: List[str]  # Object IDs involved in conflict
    severity: float  # Conflict severity (0.0 to 1.0)
    description: str
    resolution_suggestions: List[str] = field(default_factory=list)


@dataclass
class ResolutionResult:
    """Result of constraint resolution"""
    success: bool
    iterations: int
    final_violations: List[Tuple[str, float]]  # Constraint ID and violation amount
    conflicts_resolved: int
    conflicts_remaining: int
    optimization_score: float
    execution_time: float


class GeometryResolver:
    """Main geometry resolution system"""
    
    def __init__(self):
        self.objects: Dict[str, GeometricObject] = {}
        self.constraints: Dict[str, Constraint] = {}
        self.conflicts: List[GeometricConflict] = []
        self.resolution_history: List[ResolutionResult] = []
    
    def add_object(self, obj: GeometricObject):
        """Add a geometric object to the system"""
        self.objects[obj.object_id] = obj
    
    def add_constraint(self, constraint: Constraint):
        """Add a constraint to the system"""
        self.constraints[constraint.constraint_id] = constraint
    
    def validate_constraints(self) -> List[Tuple[str, float]]:
        """Validate all constraints and return violations"""
        violations = []
        
        for constraint_id, constraint in self.constraints.items():
            satisfied, violation = constraint.evaluate(self.objects)
            if not satisfied:
                violations.append((constraint_id, violation))
        
        return violations
    
    def detect_conflicts(self) -> List[GeometricConflict]:
        """Detect geometric conflicts between objects"""
        self.conflicts.clear()
        conflict_id = 0
        
        # Check for overlaps
        object_ids = list(self.objects.keys())
        for i in range(len(object_ids)):
            for j in range(i + 1, len(object_ids)):
                obj1_id = object_ids[i]
                obj2_id = object_ids[j]
                
                obj1 = self.objects[obj1_id]
                obj2 = self.objects[obj2_id]
                
                bbox1 = obj1.get_bounding_box()
                bbox2 = obj2.get_bounding_box()
                
                # Check for overlap
                if bbox1.intersects(bbox2):
                    overlap_volume = self._calculate_overlap_volume(bbox1, bbox2)
                    severity = min(1.0, overlap_volume / min(bbox1.size.x * bbox1.size.y * bbox1.size.z,
                                                           bbox2.size.x * bbox2.size.y * bbox2.size.z))
                    
                    conflict = GeometricConflict(
                        conflict_id=f"conflict_{conflict_id}",
                        conflict_type=ConflictType.OVERLAP,
                        objects=[obj1_id, obj2_id],
                        severity=severity,
                        description=f"Objects {obj1_id} and {obj2_id} overlap",
                        resolution_suggestions=[
                            f"Move {obj1_id} away from {obj2_id}",
                            f"Move {obj2_id} away from {obj1_id}",
                            f"Resize {obj1_id} or {obj2_id}",
                            f"Rotate {obj1_id} or {obj2_id}"
                        ]
                    )
                    self.conflicts.append(conflict)
                    conflict_id += 1
        
        # Check constraint violations
        violations = self.validate_constraints()
        for constraint_id, violation in violations:
            constraint = self.constraints[constraint_id]
            
            conflict = GeometricConflict(
                conflict_id=f"conflict_{conflict_id}",
                conflict_type=ConflictType.CLEARANCE_VIOLATION,
                objects=constraint.objects,
                severity=min(1.0, violation),
                description=f"Constraint {constraint_id} violated: {constraint.constraint_type.value}",
                resolution_suggestions=[
                    f"Adjust position of objects {constraint.objects}",
                    f"Modify constraint parameters for {constraint_id}",
                    f"Disable constraint {constraint_id} if not critical"
                ]
            )
            self.conflicts.append(conflict)
            conflict_id += 1
        
        return self.conflicts
    
    def resolve_constraints(self, max_iterations: int = 100, tolerance: float = 0.01) -> ResolutionResult:
        """Resolve constraints using optimization"""
        import time
        start_time = time.time()
        
        # Initial state
        initial_violations = self.validate_constraints()
        initial_score = sum(violation for _, violation in initial_violations)
        
        # Detect conflicts
        conflicts = self.detect_conflicts()
        initial_conflicts = len(conflicts)
        
        # Constraint resolution using gradient descent
        for iteration in range(max_iterations):
            violations = self.validate_constraints()
            current_score = sum(violation for _, violation in violations)
            
            if current_score < tolerance:
                break
            
            # Apply constraint forces
            self._apply_constraint_forces(violations)
        
        # Final state
        final_violations = self.validate_constraints()
        final_conflicts = len(self.detect_conflicts())
        
        execution_time = time.time() - start_time
        
        result = ResolutionResult(
            success=len(final_violations) == 0,
            iterations=iteration + 1,
            final_violations=final_violations,
            conflicts_resolved=initial_conflicts - final_conflicts,
            conflicts_remaining=final_conflicts,
            optimization_score=initial_score - sum(violation for _, violation in final_violations),
            execution_time=execution_time
        )
        
        self.resolution_history.append(result)
        return result
    
    def optimize_layout(self, optimization_goals: Dict[str, float]) -> ResolutionResult:
        """Optimize layout based on multiple goals"""
        import time
        start_time = time.time()
        
        # Define optimization objectives
        objectives = {
            'minimize_overlaps': optimization_goals.get('minimize_overlaps', 1.0),
            'minimize_constraint_violations': optimization_goals.get('minimize_constraint_violations', 1.0),
            'minimize_total_area': optimization_goals.get('minimize_total_area', 0.5),
            'maximize_alignment': optimization_goals.get('maximize_alignment', 0.3)
        }
        
        # Multi-objective optimization
        best_score = float('inf')
        best_positions = {}
        
        for iteration in range(50):  # Optimization iterations
            # Generate candidate positions
            candidate_positions = self._generate_candidate_positions()
            
            # Evaluate candidate
            score = self._evaluate_layout(candidate_positions, objectives)
            
            if score < best_score:
                best_score = score
                best_positions = candidate_positions.copy()
        
        # Apply best solution
        for obj_id, position in best_positions.items():
            if obj_id in self.objects:
                self.objects[obj_id].position = position
        
        # Final resolution
        result = self.resolve_constraints()
        result.execution_time = time.time() - start_time
        
        return result
    
    def detect_3d_collisions(self) -> List[GeometricConflict]:
        """Detect 3D collisions between objects"""
        collisions = []
        collision_id = 0
        
        object_ids = list(self.objects.keys())
        for i in range(len(object_ids)):
            for j in range(i + 1, len(object_ids)):
                obj1_id = object_ids[i]
                obj2_id = object_ids[j]
                
                obj1 = self.objects[obj1_id]
                obj2 = self.objects[obj2_id]
                
                # Check for 3D collision using bounding boxes
                bbox1 = obj1.get_bounding_box()
                bbox2 = obj2.get_bounding_box()
                
                if bbox1.intersects(bbox2):
                    # Calculate collision volume
                    collision_volume = self._calculate_collision_volume(bbox1, bbox2)
                    
                    # Calculate severity based on collision volume
                    obj1_volume = bbox1.size.x * bbox1.size.y * bbox1.size.z
                    obj2_volume = bbox2.size.x * bbox2.size.y * bbox2.size.z
                    severity = collision_volume / min(obj1_volume, obj2_volume)
                    
                    collision = GeometricConflict(
                        conflict_id=f"collision_{collision_id}",
                        conflict_type=ConflictType.INTERSECTION,
                        objects=[obj1_id, obj2_id],
                        severity=severity,
                        description=f"3D collision between {obj1_id} and {obj2_id}",
                        resolution_suggestions=[
                            f"Move {obj1_id} in Z direction",
                            f"Move {obj2_id} in Z direction",
                            f"Reduce height of {obj1_id} or {obj2_id}",
                            f"Add vertical separation between objects"
                        ]
                    )
                    collisions.append(collision)
                    collision_id += 1
        
        return collisions
    
    def _apply_constraint_forces(self, violations: List[Tuple[str, float]]):
        """Apply constraint forces to resolve violations"""
        for constraint_id, violation in violations:
            constraint = self.constraints[constraint_id]
            
            if not constraint.enabled:
                continue
            
            # Get objects involved in constraint
            obj_list = [self.objects[obj_id] for obj_id in constraint.objects if obj_id in self.objects]
            if len(obj_list) < 2:
                continue
            
            # Apply corrective forces based on constraint type
            if constraint.constraint_type == ConstraintType.DISTANCE:
                self._apply_distance_force(obj_list[0], obj_list[1], constraint.parameters)
            elif constraint.constraint_type == ConstraintType.ALIGNMENT:
                self._apply_alignment_force(obj_list[0], obj_list[1], constraint.parameters)
            elif constraint.constraint_type == ConstraintType.CLEARANCE:
                self._apply_clearance_force(obj_list[0], obj_list[1], constraint.parameters)
    
    def _apply_distance_force(self, obj1: GeometricObject, obj2: GeometricObject, parameters: Dict[str, Any]):
        """Apply distance constraint force"""
        target_distance = parameters.get('distance', 0.0)
        current_distance = obj1.position.distance_to(obj2.position)
        
        if current_distance == 0:
            # Avoid division by zero
            direction = Point3D(1, 0, 0)
        else:
            direction = Point3D(
                (obj2.position.x - obj1.position.x) / current_distance,
                (obj2.position.y - obj1.position.y) / current_distance,
                (obj2.position.z - obj1.position.z) / current_distance
            )
        
        # Calculate correction
        correction = (target_distance - current_distance) * 0.1  # Damping factor
        
        # Apply correction
        obj1.position = Point3D(
            obj1.position.x - direction.x * correction / 2,
            obj1.position.y - direction.y * correction / 2,
            obj1.position.z - direction.z * correction / 2
        )
        obj2.position = Point3D(
            obj2.position.x + direction.x * correction / 2,
            obj2.position.y + direction.y * correction / 2,
            obj2.position.z + direction.z * correction / 2
        )
    
    def _apply_alignment_force(self, obj1: GeometricObject, obj2: GeometricObject, parameters: Dict[str, Any]):
        """Apply alignment constraint force"""
        axis = parameters.get('axis', 'x')
        correction_factor = 0.1
        
        if axis == 'x':
            avg_x = (obj1.position.x + obj2.position.x) / 2
            obj1.position.x += (avg_x - obj1.position.x) * correction_factor
            obj2.position.x += (avg_x - obj2.position.x) * correction_factor
        elif axis == 'y':
            avg_y = (obj1.position.y + obj2.position.y) / 2
            obj1.position.y += (avg_y - obj1.position.y) * correction_factor
            obj2.position.y += (avg_y - obj2.position.y) * correction_factor
        else:  # z
            avg_z = (obj1.position.z + obj2.position.z) / 2
            obj1.position.z += (avg_z - obj1.position.z) * correction_factor
            obj2.position.z += (avg_z - obj2.position.z) * correction_factor
    
    def _apply_clearance_force(self, obj1: GeometricObject, obj2: GeometricObject, parameters: Dict[str, Any]):
        """Apply clearance constraint force"""
        min_clearance = parameters.get('min_clearance', 0.0)
        
        bbox1 = obj1.get_bounding_box()
        bbox2 = obj2.get_bounding_box()
        
        # Calculate current distance
        current_distance = self._calculate_bbox_distance(bbox1, bbox2)
        
        if current_distance < min_clearance:
            # Calculate separation direction
            center1 = bbox1.center
            center2 = bbox2.center
            
            direction = Point3D(
                center2.x - center1.x,
                center2.y - center1.y,
                center2.z - center1.z
            )
            
            # Normalize direction
            length = math.sqrt(direction.x**2 + direction.y**2 + direction.z**2)
            if length > 0:
                direction = Point3D(direction.x/length, direction.y/length, direction.z/length)
            else:
                direction = Point3D(1, 0, 0)
            
            # Apply separation
            separation = (min_clearance - current_distance) * 0.1
            obj1.position = Point3D(
                obj1.position.x - direction.x * separation / 2,
                obj1.position.y - direction.y * separation / 2,
                obj1.position.z - direction.z * separation / 2
            )
            obj2.position = Point3D(
                obj2.position.x + direction.x * separation / 2,
                obj2.position.y + direction.y * separation / 2,
                obj2.position.z + direction.z * separation / 2
            )
    
    def _generate_candidate_positions(self) -> Dict[str, Point3D]:
        """Generate candidate positions for optimization"""
        import random
        
        candidate_positions = {}
        for obj_id, obj in self.objects.items():
            # Add small random perturbation
            perturbation = Point3D(
                random.uniform(-0.5, 0.5),
                random.uniform(-0.5, 0.5),
                random.uniform(-0.5, 0.5)
            )
            candidate_positions[obj_id] = Point3D(
                obj.position.x + perturbation.x,
                obj.position.y + perturbation.y,
                obj.position.z + perturbation.z
            )
        
        return candidate_positions
    
    def _evaluate_layout(self, positions: Dict[str, Point3D], objectives: Dict[str, float]) -> float:
        """Evaluate layout quality based on objectives"""
        score = 0.0
        
        # Temporarily apply positions
        original_positions = {obj_id: obj.position for obj_id, obj in self.objects.items()}
        for obj_id, position in positions.items():
            if obj_id in self.objects:
                self.objects[obj_id].position = position
        
        # Evaluate overlaps
        if objectives['minimize_overlaps'] > 0:
            overlaps = len(self.detect_conflicts())
            score += overlaps * objectives['minimize_overlaps']
        
        # Evaluate constraint violations
        if objectives['minimize_constraint_violations'] > 0:
            violations = self.validate_constraints()
            score += sum(violation for _, violation in violations) * objectives['minimize_constraint_violations']
        
        # Evaluate total area
        if objectives['minimize_total_area'] > 0:
            total_area = self._calculate_total_area()
            score += total_area * objectives['minimize_total_area']
        
        # Restore original positions
        for obj_id, position in original_positions.items():
            if obj_id in self.objects:
                self.objects[obj_id].position = position
        
        return score
    
    def _calculate_total_area(self) -> float:
        """Calculate total area occupied by all objects"""
        if not self.objects:
            return 0.0
        
        min_x = min(obj.get_bounding_box().min_point.x for obj in self.objects.values())
        max_x = max(obj.get_bounding_box().max_point.x for obj in self.objects.values())
        min_y = min(obj.get_bounding_box().min_point.y for obj in self.objects.values())
        max_y = max(obj.get_bounding_box().max_point.y for obj in self.objects.values())
        
        return (max_x - min_x) * (max_y - min_y)
    
    def _calculate_overlap_volume(self, bbox1: BoundingBox, bbox2: BoundingBox) -> float:
        """Calculate overlap volume between two bounding boxes"""
        if not bbox1.intersects(bbox2):
            return 0.0
        
        # Calculate intersection
        min_x = max(bbox1.min_point.x, bbox2.min_point.x)
        max_x = min(bbox1.max_point.x, bbox2.max_point.x)
        min_y = max(bbox1.min_point.y, bbox2.min_point.y)
        max_y = min(bbox1.max_point.y, bbox2.max_point.y)
        min_z = max(bbox1.min_point.z, bbox2.min_point.z)
        max_z = min(bbox1.max_point.z, bbox2.max_point.z)
        
        return (max_x - min_x) * (max_y - min_y) * (max_z - min_z)
    
    def _calculate_collision_volume(self, bbox1: BoundingBox, bbox2: BoundingBox) -> float:
        """Calculate collision volume between two bounding boxes"""
        return self._calculate_overlap_volume(bbox1, bbox2)
    
    def export_results(self) -> Dict[str, Any]:
        """Export resolution results and statistics"""
        return {
            'timestamp': datetime.now().isoformat(),
            'object_count': len(self.objects),
            'constraint_count': len(self.constraints),
            'conflict_count': len(self.conflicts),
            'resolution_history': [
                {
                    'success': result.success,
                    'iterations': result.iterations,
                    'conflicts_resolved': result.conflicts_resolved,
                    'conflicts_remaining': result.conflicts_remaining,
                    'optimization_score': result.optimization_score,
                    'execution_time': result.execution_time
                }
                for result in self.resolution_history
            ],
            'current_violations': self.validate_constraints(),
            'current_conflicts': [conflict.__dict__ for conflict in self.conflicts]
        } 

class GeometryOptimizer:
    """Geometry optimization algorithms for performance and quality."""
    
    def __init__(self):
        self.optimization_levels = {
            'low': {'tolerance': 0.1, 'max_vertices': 1000},
            'medium': {'tolerance': 0.05, 'max_vertices': 500},
            'high': {'tolerance': 0.01, 'max_vertices': 100}
        }
    
    def optimize_mesh(self, geometry: Dict[str, Any], level: str = 'medium') -> Dict[str, Any]:
        """
        Optimize mesh geometry for performance.
        
        Args:
            geometry: Geometry data to optimize
            level: Optimization level ('low', 'medium', 'high')
            
        Returns:
            Optimized geometry data
        """
        if level not in self.optimization_levels:
            level = 'medium'
        
        config = self.optimization_levels[level]
        geometry_type = geometry.get('type', '')
        
        if geometry_type in ['polyhedron', 'polygon_3d', 'polygon']:
            return self._optimize_polyhedron(geometry, config)
        elif geometry_type in ['extrusion', 'line_3d']:
            return self._optimize_extrusion(geometry, config)
        elif geometry_type in ['cylinder', 'box']:
            return self._optimize_primitive(geometry, config)
        else:
            # For other types, add optimization metadata
            return {
                **geometry,
                'optimization_level': config
            }
    
    def _optimize_polyhedron(self, geometry: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize polyhedron or polygon geometry."""
        faces = geometry.get('faces', None)
        # If 'polygon' with only 'coordinates', treat as a single face
        if faces is None and geometry.get('type', '') == 'polygon' and 'coordinates' in geometry:
            faces = [geometry['coordinates']]
        if not faces:
            return {**geometry, 'optimization_level': config}
        
        optimized_faces = []
        for face in faces:
            if len(face) > config['max_vertices']:
                # Simplify face by removing vertices
                simplified_face = self._simplify_polygon(face, config['tolerance'])
                optimized_faces.append(simplified_face)
            else:
                optimized_faces.append(face)
        
        result = {
            **geometry,
            'faces': optimized_faces,
            'optimization_level': config
        }
        # If original was a 'polygon' with only 'coordinates', keep 'coordinates' key for compatibility
        if geometry.get('type', '') == 'polygon' and 'coordinates' in geometry:
            result['coordinates'] = optimized_faces[0]
        return result
    
    def _optimize_extrusion(self, geometry: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize extrusion geometry."""
        segments = geometry.get('segments', [])
        if not segments:
            return geometry
        
        optimized_segments = []
        for segment in segments:
            if len(segment) > config['max_vertices']:
                # Simplify segment
                simplified_segment = self._simplify_line_segment(segment, config['tolerance'])
                optimized_segments.append(simplified_segment)
            else:
                optimized_segments.append(segment)
        
        return {
            **geometry,
            'segments': optimized_segments,
            'optimization_level': config
        }
    
    def _optimize_primitive(self, geometry: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize primitive geometry (cylinder, box)."""
        # Primitives are already optimized, just add metadata
        return {
            **geometry,
            'optimization_level': config
        }
    
    def _simplify_polygon(self, vertices: List[List[float]], tolerance: float) -> List[List[float]]:
        """Simplify polygon using Douglas-Peucker algorithm."""
        if len(vertices) <= 3:
            return vertices
        
        # Simplified Douglas-Peucker implementation
        def perpendicular_distance(point, line_start, line_end):
            """Calculate perpendicular distance from point to line."""
            if line_start == line_end:
                return 0.0
            
            # Vector from line_start to line_end
            line_vec = [line_end[0] - line_start[0], line_end[1] - line_start[1]]
            line_length = math.sqrt(line_vec[0]**2 + line_vec[1]**2)
            
            if line_length == 0:
                return 0.0
            
            # Vector from line_start to point
            point_vec = [point[0] - line_start[0], point[1] - line_start[1]]
            
            # Project point onto line
            projection = (point_vec[0] * line_vec[0] + point_vec[1] * line_vec[1]) / line_length
            
            # Clamp projection to line segment
            projection = max(0, min(1, projection))
            
            # Calculate projected point
            projected = [
                line_start[0] + projection * line_vec[0],
                line_start[1] + projection * line_vec[1]
            ]
            
            # Calculate distance
            return math.sqrt((point[0] - projected[0])**2 + (point[1] - projected[1])**2)
        
        def douglas_peucker(points, tolerance):
            """Douglas-Peucker algorithm for line simplification."""
            if len(points) <= 2:
                return points
            
            # Find point with maximum distance
            max_distance = 0
            max_index = 0
            
            for i in range(1, len(points) - 1):
                distance = perpendicular_distance(points[i], points[0], points[-1])
                if distance > max_distance:
                    max_distance = distance
                    max_index = i
            
            # If max distance is greater than tolerance, recursively simplify
            if max_distance > tolerance:
                left = douglas_peucker(points[:max_index + 1], tolerance)
                right = douglas_peucker(points[max_index:], tolerance)
                return left[:-1] + right
            else:
                return [points[0], points[-1]]
        
        return douglas_peucker(vertices, tolerance)
    
    def _simplify_line_segment(self, segment: List[List[float]], tolerance: float) -> List[List[float]]:
        """Simplify line segment."""
        if len(segment) <= 2:
            return segment
        
        # Convert 3D points to 2D for simplification
        points_2d = [[p[0], p[1]] for p in segment]
        simplified_2d = self._simplify_polygon(points_2d, tolerance)
        
        # Convert back to 3D
        simplified_3d = []
        for i, point_2d in enumerate(simplified_2d):
            # Interpolate Z coordinate
            if i < len(segment):
                z = segment[i][2]
            else:
                z = segment[-1][2]
            simplified_3d.append([point_2d[0], point_2d[1], z])
        
        return simplified_3d
    
    def generate_lod(self, geometry: Dict[str, Any], levels: List[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Generate multiple levels of detail (LOD) for geometry.
        
        Args:
            geometry: Original geometry data
            levels: List of LOD levels to generate
            
        Returns:
            Dictionary of LOD levels with optimized geometry
        """
        if levels is None:
            levels = ['low', 'medium', 'high']
        
        lod_geometries = {}
        for level in levels:
            if level in self.optimization_levels:
                optimized = self.optimize_mesh(geometry, level)
                lod_geometries[level] = optimized
        
        return lod_geometries
    
    def calculate_optimization_metrics(self, original: Dict[str, Any], optimized: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate optimization metrics.
        
        Args:
            original: Original geometry
            optimized: Optimized geometry
            
        Returns:
            Optimization metrics
        """
        original_vertices = self._count_vertices(original)
        optimized_vertices = self._count_vertices(optimized)
        
        reduction_ratio = 1.0 - (optimized_vertices / original_vertices) if original_vertices > 0 else 0.0
        
        return {
            'original_vertices': original_vertices,
            'optimized_vertices': optimized_vertices,
            'reduction_ratio': reduction_ratio,
            'compression_efficiency': reduction_ratio * 100  # Percentage
        }
    
    def _count_vertices(self, geometry: Dict[str, Any]) -> int:
        """Count vertices in geometry."""
        geometry_type = geometry.get('type', '')
        
        if geometry_type in ['polyhedron', 'polygon_3d']:
            faces = geometry.get('faces', [])
            return sum(len(face) for face in faces)
        elif geometry_type in ['extrusion', 'line_3d']:
            segments = geometry.get('segments', [])
            return sum(len(segment) for segment in segments)
        elif geometry_type in ['point_2d', 'point_3d']:
            return 1
        else:
            return 0

class GeometryProcessor:
    """Enhanced geometry processing with 3D generation and transformations."""
    
    def __init__(self):
        self.coordinate_systems = {}
        self.transformation_matrices = {}
        self.validation_rules = self._build_validation_rules()
        self.optimizer = GeometryOptimizer()
        
    def generate_3d_from_2d_svg(self, svg_geometry: Dict[str, Any], height: float = 3.0) -> Dict[str, Any]:
        """
        Generate 3D geometry from 2D SVG geometry.
        
        Args:
            svg_geometry: 2D SVG geometry data
            height: Extrusion height for 3D generation
            
        Returns:
            3D geometry data
        """
        geometry_type = svg_geometry.get('type', '')
        
        if geometry_type == 'polygon':
            return self._extrude_polygon_to_3d(svg_geometry, height)
        elif geometry_type == 'line':
            return self._extrude_line_to_3d(svg_geometry, height)
        elif geometry_type == 'circle':
            return self._extrude_circle_to_3d(svg_geometry, height)
        elif geometry_type == 'rect':
            return self._extrude_rect_to_3d(svg_geometry, height)
        else:
            # Default: create a 3D point
            return self._create_3d_point(svg_geometry)
    
    def _extrude_polygon_to_3d(self, svg_geometry: Dict[str, Any], height: float) -> Dict[str, Any]:
        """Extrude 2D polygon to 3D polyhedron."""
        coordinates_2d = svg_geometry.get('coordinates', [])
        if not coordinates_2d:
            return self._create_default_3d_geometry()
        
        # Create bottom and top faces
        bottom_face = coordinates_2d
        top_face = [[x, y, height] for x, y in coordinates_2d]
        
        # Create side faces (triangles)
        side_faces = []
        for i in range(len(coordinates_2d)):
            p1 = coordinates_2d[i]
            p2 = coordinates_2d[(i + 1) % len(coordinates_2d)]
            p3 = [p2[0], p2[1], height]
            p4 = [p1[0], p1[1], height]
            
            # Create two triangles for each side face
            side_faces.extend([
                [p1, p2, p3],  # Triangle 1
                [p1, p3, p4]   # Triangle 2
            ])
        
        return {
            'type': 'polyhedron',
            'faces': [bottom_face, top_face] + side_faces,
            'volume': self._calculate_polyhedron_volume([bottom_face, top_face] + side_faces),
            'surface_area': self._calculate_polyhedron_surface_area([bottom_face, top_face] + side_faces)
        }
    
    def _extrude_line_to_3d(self, svg_geometry: Dict[str, Any], height: float) -> Dict[str, Any]:
        """Extrude 2D line to 3D geometry."""
        coordinates_2d = svg_geometry.get('coordinates', [])
        if len(coordinates_2d) < 2:
            return self._create_default_3d_geometry()
        
        # Create 3D line segments
        line_3d = []
        for i in range(len(coordinates_2d) - 1):
            p1_2d = coordinates_2d[i]
            p2_2d = coordinates_2d[i + 1]
            
            # Create 3D line segment
            line_3d.append([
                [p1_2d[0], p1_2d[1], 0],
                [p2_2d[0], p2_2d[1], 0],
                [p2_2d[0], p2_2d[1], height],
                [p1_2d[0], p1_2d[1], height]
            ])
        
        return {
            'type': 'extrusion',
            'segments': line_3d,
            'length': self._calculate_3d_line_length(line_3d),
            'volume': self._calculate_extrusion_volume(line_3d, height)
        }
    
    def _extrude_circle_to_3d(self, svg_geometry: Dict[str, Any], height: float) -> Dict[str, Any]:
        """Extrude 2D circle to 3D cylinder."""
        center = svg_geometry.get('coordinates', [0, 0])
        radius = svg_geometry.get('radius', 1.0)
        
        # Create cylinder geometry
        cylinder = {
            'type': 'cylinder',
            'center': [center[0], center[1], height/2],
            'radius': radius,
            'height': height,
            'volume': math.pi * radius * radius * height,
            'surface_area': 2 * math.pi * radius * (radius + height)
        }
        
        return cylinder
    
    def _extrude_rect_to_3d(self, svg_geometry: Dict[str, Any], height: float) -> Dict[str, Any]:
        """Extrude 2D rectangle to 3D box."""
        x = svg_geometry.get('x', 0)
        y = svg_geometry.get('y', 0)
        width = svg_geometry.get('width', 1)
        height_2d = svg_geometry.get('height', 1)
        
        # Create box geometry
        box = {
            'type': 'box',
            'min_point': [x, y, 0],
            'max_point': [x + width, y + height_2d, height],
            'volume': width * height_2d * height,
            'surface_area': 2 * (width * height_2d + width * height + height_2d * height)
        }
        
        return box
    
    def _create_3d_point(self, svg_geometry: Dict[str, Any]) -> Dict[str, Any]:
        """Create 3D point from 2D coordinates."""
        coordinates = svg_geometry.get('coordinates', [0, 0])
        return {
            'type': 'point_3d',
            'coordinates': [coordinates[0], coordinates[1], 0],
            'volume': 0,
            'surface_area': 0
        }
    
    def _create_default_3d_geometry(self) -> Dict[str, Any]:
        """Create default 3D geometry when conversion fails."""
        return {
            'type': 'point_3d',
            'coordinates': [0, 0, 0],
            'volume': 0,
            'surface_area': 0
        }
    
    def transform_coordinate_system(self, geometry: Dict[str, Any], 
                                  from_system: CoordinateSystem, 
                                  to_system: CoordinateSystem,
                                  scale_factors: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Transform geometry between coordinate systems.
        
        Args:
            geometry: Geometry data to transform
            from_system: Source coordinate system
            to_system: Target coordinate system
            scale_factors: Optional scale factors for transformation
            
        Returns:
            Transformed geometry data
        """
        try:
            # Get transformation matrix
            transform_matrix = self._get_transformation_matrix(from_system, to_system, scale_factors)
            
            # Apply transformation to geometry
            transformed_geometry = self._apply_transformation(geometry, transform_matrix)
            
            # Validate transformed geometry
            validation_result = self._validate_geometry(transformed_geometry)
            if not validation_result['valid']:
                logger.warning(f"Geometry validation failed after transformation: {validation_result['errors']}")
            
            return transformed_geometry
            
        except Exception as e:
            logger.error(f"Coordinate transformation failed: {e}")
            raise GeometryError(f"Error transforming coordinate system: {e}") from e
    
    def _get_transformation_matrix(self, from_system: CoordinateSystem, 
                                 to_system: CoordinateSystem,
                                 scale_factors: Optional[Dict[str, float]] = None) -> np.ndarray:
        """Get transformation matrix between coordinate systems."""
        
        # Default scale factors
        if scale_factors is None:
            scale_factors = {'x': 1.0, 'y': 1.0, 'z': 1.0}
        
        # Create transformation matrix
        if from_system == CoordinateSystem.SVG_2D and to_system == CoordinateSystem.BIM_3D:
            # SVG to BIM transformation (2D to 3D)
            matrix = np.array([
                [scale_factors['x'], 0, 0, 0],
                [0, scale_factors['y'], 0, 0],
                [0, 0, scale_factors['z'], 0],
                [0, 0, 0, 1]
            ])
        elif from_system == CoordinateSystem.BIM_3D and to_system == CoordinateSystem.REAL_WORLD_METERS:
            # BIM to real-world meters
            matrix = np.array([
                [1.0, 0, 0, 0],
                [0, 1.0, 0, 0],
                [0, 0, 1.0, 0],
                [0, 0, 0, 1]
            ])
        elif from_system == CoordinateSystem.REAL_WORLD_METERS and to_system == CoordinateSystem.REAL_WORLD_FEET:
            # Meters to feet
            matrix = np.array([
                [3.28084, 0, 0, 0],
                [0, 3.28084, 0, 0],
                [0, 0, 3.28084, 0],
                [0, 0, 0, 1]
            ])
        else:
            # Identity matrix for unknown transformations
            matrix = np.eye(4)
        
        return matrix
    
    def _apply_transformation(self, geometry: Dict[str, Any], transform_matrix: np.ndarray) -> Dict[str, Any]:
        """Apply transformation matrix to geometry."""
        geometry_type = geometry.get('type', '')
        
        if geometry_type in ['point_2d', 'point_3d']:
            coords = geometry.get('coordinates', [0, 0, 0])
            if len(coords) == 2:
                coords = [coords[0], coords[1], 0]
            
            # Apply transformation
            point = np.array([coords[0], coords[1], coords[2], 1])
            transformed_point = transform_matrix @ point
            
            return {
                **geometry,
                'coordinates': transformed_point[:3].tolist()
            }
        
        elif geometry_type in ['polygon_2d', 'polygon_3d']:
            coordinates = geometry.get('coordinates', [])
            transformed_coordinates = []
            
            for coord in coordinates:
                if len(coord) == 2:
                    coord = [coord[0], coord[1], 0]
                
                point = np.array([coord[0], coord[1], coord[2], 1])
                transformed_point = transform_matrix @ point
                transformed_coordinates.append(transformed_point[:3].tolist())
            
            return {
                **geometry,
                'coordinates': transformed_coordinates
            }
        
        else:
            # For other geometry types, return as-is
            return geometry
    
    def _validate_geometry(self, geometry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate geometry for errors and correct them.
        
        Args:
            geometry: Geometry data to validate
            
        Returns:
            Validation result with errors and corrections
        """
        try:
            validation_result = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'corrections': []
            }
            
            geometry_type = geometry.get('type', '')
            
            # Check for invalid coordinates
            if geometry_type in ['point_2d', 'point_3d']:
                coords = geometry.get('coordinates', [])
                if not self._are_valid_coordinates(coords):
                    validation_result['valid'] = False
                    validation_result['errors'].append(ValidationError.INVALID_COORDINATES.value)
                    # Correct coordinates
                    corrected_coords = self._correct_coordinates(coords)
                    validation_result['corrections'].append({
                        'type': 'coordinates',
                        'original': coords,
                        'corrected': corrected_coords
                    })
            
            # Check for self-intersecting polygons (only if more than 4 points)
            if geometry_type in ['polygon_2d', 'polygon_3d', 'polygon']:
                coordinates = geometry.get('coordinates', [])
                # Only check for self-intersection if polygon is closed and has more than 4 points
                if len(coordinates) > 4 and coordinates[0] == coordinates[-1]:
                    if self._is_self_intersecting(coordinates):
                        validation_result['valid'] = False
                        validation_result['errors'].append(ValidationError.SELF_INTERSECTING.value)
                        # Correct polygon
                        corrected_coords = self._correct_self_intersecting_polygon(coordinates)
                        validation_result['corrections'].append({
                            'type': 'polygon',
                            'original': coordinates,
                            'corrected': corrected_coords
                        })
            
            # Check for non-closed polygons
            if geometry_type in ['polygon_2d', 'polygon_3d', 'polygon']:
                coordinates = geometry.get('coordinates', [])
                if len(coordinates) > 2 and coordinates[0] != coordinates[-1]:
                    validation_result['valid'] = False
                    validation_result['errors'].append(ValidationError.NON_CLOSED_POLYGON.value)
                    # Close polygon
                    corrected_coords = coordinates + [coordinates[0]]
                    validation_result['corrections'].append({
                        'type': 'close_polygon',
                        'original': coordinates,
                        'corrected': corrected_coords
                    })
            
            # Check for zero area/volume
            if geometry_type in ['polygon_2d', 'polygon_3d', 'polygon']:
                area = self._calculate_polygon_area(geometry.get('coordinates', []))
                if area < 1e-6:
                    validation_result['warnings'].append(ValidationError.ZERO_AREA.value)
            
            return validation_result
        except Exception as e:
            logger.error(f"Error validating geometry: {e}")
            raise ValidationError(f"Error validating geometry: {e}") from e
    
    def _are_valid_coordinates(self, coords: List[float]) -> bool:
        """Check if coordinates are valid (finite numbers)."""
        return all(math.isfinite(coord) for coord in coords)
    
    def _correct_coordinates(self, coords: List[float]) -> List[float]:
        """Correct invalid coordinates."""
        corrected = []
        for coord in coords:
            if math.isfinite(coord):
                corrected.append(coord)
            else:
                corrected.append(0.0)  # Default to 0 for invalid coordinates
        return corrected
    
    def _is_self_intersecting(self, coordinates: List[List[float]]) -> bool:
        """Check if polygon is self-intersecting (robust check)."""
        n = len(coordinates)
        if n < 4:
            return False
        # For a closed polygon, last point == first point
        # Only check pairs of non-adjacent segments, skip closing segment
        for i in range(n - 1):
            for j in range(i + 1, n - 1):
                # Segments are (i, i+1) and (j, j+1)
                # Skip adjacent segments and segments sharing a vertex
                if abs(i - j) <= 1 or (i == 0 and j == n - 2):
                    continue
                if self._lines_intersect(coordinates[i], coordinates[i+1], coordinates[j], coordinates[j+1]):
                    return True
        return False
    
    def _lines_intersect(self, p1: List[float], p2: List[float], 
                        p3: List[float], p4: List[float]) -> bool:
        """Check if two line segments intersect."""
        # Simplified line intersection check
        def ccw(A, B, C):
            return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])
        
        return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)
    
    def _correct_self_intersecting_polygon(self, coordinates: List[List[float]]) -> List[List[float]]:
        """Correct self-intersecting polygon (simplified)."""
        # Simplified correction: remove problematic segments
        if len(coordinates) < 4:
            return coordinates
        
        corrected = [coordinates[0]]
        for i in range(1, len(coordinates)):
            # Skip segments that would cause self-intersection
            if i < len(coordinates) - 1:
                corrected.append(coordinates[i])
        
        return corrected
    
    def _calculate_polygon_area(self, coordinates: List[List[float]]) -> float:
        """Calculate area of polygon using shoelace formula."""
        if len(coordinates) < 3:
            return 0.0
        
        area = 0.0
        for i in range(len(coordinates)):
            j = (i + 1) % len(coordinates)
            area += coordinates[i][0] * coordinates[j][1]
            area -= coordinates[j][0] * coordinates[i][1]
        
        return abs(area) / 2.0
    
    def _calculate_polyhedron_volume(self, faces: List[List[List[float]]]) -> float:
        """Calculate volume of polyhedron."""
        # Simplified volume calculation
        return 1.0  # Placeholder
    
    def _calculate_polyhedron_surface_area(self, faces: List[List[List[float]]]) -> float:
        """Calculate surface area of polyhedron."""
        # Simplified surface area calculation
        return 1.0  # Placeholder
    
    def _calculate_3d_line_length(self, segments: List[List[List[float]]]) -> float:
        """Calculate length of 3D line."""
        total_length = 0.0
        for segment in segments:
            if len(segment) >= 2:
                p1 = segment[0]
                p2 = segment[1]
                length = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2 + (p2[2] - p1[2])**2)
                total_length += length
        return total_length
    
    def _calculate_extrusion_volume(self, segments: List[List[List[float]]], height: float) -> float:
        """Calculate volume of extrusion."""
        # Simplified volume calculation
        return 1.0  # Placeholder
    
    def _build_validation_rules(self) -> Dict[str, Any]:
        """Build validation rules for geometry."""
        return {
            'min_coordinate_value': -1e6,
            'max_coordinate_value': 1e6,
            'min_polygon_vertices': 3,
            'max_polygon_vertices': 1000,
            'min_line_length': 0.001,
            'max_line_length': 1e6
        } 

    def optimize_geometry(self, geometry: Dict[str, Any], level: str = 'medium') -> Dict[str, Any]:
        """
        Optimize geometry for performance and quality.
        
        Args:
            geometry: Geometry data to optimize
            level: Optimization level ('low', 'medium', 'high')
            
        Returns:
            Optimized geometry data
        """
        return self.optimizer.optimize_mesh(geometry, level)
    
    def generate_lod_levels(self, geometry: Dict[str, Any], levels: List[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Generate multiple levels of detail for geometry.
        
        Args:
            geometry: Original geometry data
            levels: List of LOD levels to generate
            
        Returns:
            Dictionary of LOD levels with optimized geometry
        """
        return self.optimizer.generate_lod(geometry, levels)
    
    def get_optimization_metrics(self, original: Dict[str, Any], optimized: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get optimization metrics for geometry.
        
        Args:
            original: Original geometry
            optimized: Optimized geometry
            
        Returns:
            Optimization metrics
        """
        return self.optimizer.calculate_optimization_metrics(original, optimized)
    
    def batch_process_geometry(self, geometries: List[Dict[str, Any]], 
                             operations: List[str] = None) -> List[Dict[str, Any]]:
        """
        Batch process multiple geometries with specified operations.
        
        Args:
            geometries: List of geometry data
            operations: List of operations to apply ('validate', 'optimize', 'transform')
            
        Returns:
            List of processed geometries
        """
        if operations is None:
            operations = ['validate', 'optimize']
        
        processed_geometries = []
        
        for geometry in geometries:
            processed = geometry.copy()
            
            if 'validate' in operations:
                validation_result = self._validate_geometry(processed)
                if validation_result['corrections']:
                    # Apply corrections
                    for correction in validation_result['corrections']:
                        if correction['type'] == 'coordinates':
                            processed['coordinates'] = correction['corrected']
                        elif correction['type'] == 'polygon':
                            processed['coordinates'] = correction['corrected']
                        elif correction['type'] == 'close_polygon':
                            processed['coordinates'] = correction['corrected']
            
            if 'optimize' in operations:
                processed = self.optimize_geometry(processed, 'medium')
            
            processed_geometries.append(processed)
        
        return processed_geometries 