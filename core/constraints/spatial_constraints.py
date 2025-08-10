"""
Spatial Relationship Constraint Validators.

Implements spatial constraints for distance, clearance, alignment, and
containment relationships between building components.
"""

import math
import time
import logging
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from dataclasses import dataclass

# Import Phase 1 foundation
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.spatial import ArxObject, ArxObjectType, BoundingBox3D, BoundingBox2D
from .constraint_core import (
    Constraint, ParametricConstraint, ConstraintType, ConstraintSeverity, 
    ConstraintScope, ConstraintResult, ConstraintViolation
)
from .constraint_engine import ConstraintEvaluationContext

logger = logging.getLogger(__name__)


class SpatialConstraintValidator:
    """
    Utility class for spatial constraint validation calculations.
    
    Provides geometric calculations and spatial relationship analysis
    for constraint evaluation.
    """
    
    @staticmethod
    def calculate_3d_distance(obj1: ArxObject, obj2: ArxObject) -> float:
        """Calculate 3D center-to-center distance between objects."""
        dx = obj1.geometry.x - obj2.geometry.x
        dy = obj1.geometry.y - obj2.geometry.y
        dz = obj1.geometry.z - obj2.geometry.z
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    @staticmethod
    def calculate_2d_distance(obj1: ArxObject, obj2: ArxObject) -> float:
        """Calculate 2D center-to-center distance (plan view)."""
        dx = obj1.geometry.x - obj2.geometry.x
        dy = obj1.geometry.y - obj2.geometry.y
        return math.sqrt(dx*dx + dy*dy)
    
    @staticmethod
    def calculate_surface_distance(obj1: ArxObject, obj2: ArxObject) -> float:
        """Calculate minimum surface-to-surface distance between objects."""
        bbox1 = obj1.get_bounding_box_3d()
        bbox2 = obj2.get_bounding_box_3d()
        
        # Calculate minimum distance between bounding boxes
        dx = max(0, max(bbox1.min_x - bbox2.max_x, bbox2.min_x - bbox1.max_x))
        dy = max(0, max(bbox1.min_y - bbox2.max_y, bbox2.min_y - bbox1.max_y))
        dz = max(0, max(bbox1.min_z - bbox2.max_z, bbox2.min_z - bbox1.max_z))
        
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    @staticmethod
    def calculate_clearance_violation(obj1: ArxObject, 
                                    obj2: ArxObject,
                                    required_clearance: float) -> Tuple[bool, float]:
        """
        Check clearance requirement between objects.
        
        Returns:
            Tuple of (is_violated, actual_clearance)
        """
        actual_clearance = SpatialConstraintValidator.calculate_surface_distance(obj1, obj2)
        is_violated = actual_clearance < required_clearance
        return is_violated, actual_clearance
    
    @staticmethod
    def check_alignment(objects: List[ArxObject], 
                       alignment_type: str = "horizontal",
                       tolerance: float = 1.0) -> Tuple[bool, List[ArxObject]]:
        """
        Check alignment of objects.
        
        Args:
            objects: Objects to check alignment
            alignment_type: 'horizontal', 'vertical', or 'plane'
            tolerance: Alignment tolerance in feet
            
        Returns:
            Tuple of (is_aligned, misaligned_objects)
        """
        if len(objects) < 2:
            return True, []
        
        misaligned = []
        
        if alignment_type == "horizontal":
            # Check Z-coordinate alignment
            reference_z = objects[0].geometry.z
            for obj in objects[1:]:
                if abs(obj.geometry.z - reference_z) > tolerance:
                    misaligned.append(obj)
        
        elif alignment_type == "vertical":
            # Check X and Y coordinate alignment (vertical column)
            reference_x = objects[0].geometry.x
            reference_y = objects[0].geometry.y
            for obj in objects[1:]:
                if (abs(obj.geometry.x - reference_x) > tolerance or 
                    abs(obj.geometry.y - reference_y) > tolerance):
                    misaligned.append(obj)
        
        elif alignment_type == "plane":
            # Check if objects lie on same plane (simplified to Z-plane)
            reference_z = objects[0].geometry.z
            for obj in objects[1:]:
                if abs(obj.geometry.z - reference_z) > tolerance:
                    misaligned.append(obj)
        
        return len(misaligned) == 0, misaligned
    
    @staticmethod
    def check_containment(container: ArxObject, 
                         contained_objects: List[ArxObject]) -> List[ArxObject]:
        """
        Check if objects are contained within container bounds.
        
        Returns:
            List of objects that violate containment
        """
        container_bbox = container.get_bounding_box_3d()
        violations = []
        
        for obj in contained_objects:
            obj_bbox = obj.get_bounding_box_3d()
            
            # Check if object is fully contained
            if (obj_bbox.min_x < container_bbox.min_x or
                obj_bbox.max_x > container_bbox.max_x or
                obj_bbox.min_y < container_bbox.min_y or
                obj_bbox.max_y > container_bbox.max_y or
                obj_bbox.min_z < container_bbox.min_z or
                obj_bbox.max_z > container_bbox.max_z):
                violations.append(obj)
        
        return violations
    
    @staticmethod
    def check_adjacency(obj1: ArxObject, 
                       obj2: ArxObject,
                       max_gap: float = 1.0,
                       adjacency_type: str = "any") -> Tuple[bool, float, str]:
        """
        Check adjacency between objects.
        
        Args:
            obj1: First object
            obj2: Second object
            max_gap: Maximum allowed gap
            adjacency_type: 'any', 'horizontal', 'vertical'
            
        Returns:
            Tuple of (is_adjacent, gap_distance, adjacency_direction)
        """
        bbox1 = obj1.get_bounding_box_3d()
        bbox2 = obj2.get_bounding_box_3d()
        
        # Calculate gaps in each direction
        gap_x = max(0, max(bbox1.min_x - bbox2.max_x, bbox2.min_x - bbox1.max_x))
        gap_y = max(0, max(bbox1.min_y - bbox2.max_y, bbox2.min_y - bbox1.max_y))
        gap_z = max(0, max(bbox1.min_z - bbox2.max_z, bbox2.min_z - bbox1.max_z))
        
        # Find minimum gap and direction
        min_gap = min(gap_x, gap_y, gap_z)
        
        if min_gap == gap_x:
            direction = "horizontal_x"
        elif min_gap == gap_y:
            direction = "horizontal_y"
        else:
            direction = "vertical_z"
        
        # Check adjacency based on type
        if adjacency_type == "horizontal" and direction.startswith("horizontal"):
            is_adjacent = min_gap <= max_gap
        elif adjacency_type == "vertical" and direction == "vertical_z":
            is_adjacent = min_gap <= max_gap
        else:  # any
            is_adjacent = min_gap <= max_gap
        
        return is_adjacent, min_gap, direction


class DistanceConstraint(ParametricConstraint):
    """
    Distance constraint between objects or object types.
    
    Validates minimum or maximum distance requirements between
    building components for safety, code compliance, or design standards.
    """
    
    def __init__(self, 
                 name: str = "Distance Constraint",
                 distance_type: str = "minimum",  # "minimum", "maximum", "exact"
                 required_distance: float = 3.0,  # feet
                 measurement_method: str = "center_to_center",  # "center_to_center", "surface_to_surface"
                 **kwargs):
        """
        Initialize distance constraint.
        
        Args:
            name: Constraint name
            distance_type: Type of distance requirement
            required_distance: Required distance in feet
            measurement_method: How to measure distance
        """
        super().__init__(
            name=name,
            constraint_type=ConstraintType.SPATIAL_DISTANCE,
            **kwargs
        )
        
        self.set_parameter('distance_type', distance_type)
        self.set_parameter('required_distance', required_distance)
        self.set_parameter('measurement_method', measurement_method)
        
        # Object type filters
        self.set_parameter('source_types', set())  # If empty, applies to all
        self.set_parameter('target_types', set())  # If empty, applies to all
    
    def is_applicable(self, arxobject: ArxObject) -> bool:
        """Check if constraint applies to object."""
        source_types = self.get_parameter('source_types', set())
        if source_types and arxobject.type not in source_types:
            return False
        return True
    
    def evaluate(self, 
                context: ConstraintEvaluationContext,
                target_objects: List[ArxObject]) -> ConstraintResult:
        """Evaluate distance constraint."""
        start_time = time.time()
        
        result = ConstraintResult(
            constraint_id=self.constraint_id,
            constraint_name=self.name,
            is_satisfied=True,
            evaluation_time_ms=0.0,
            evaluated_objects=[obj.id for obj in target_objects],
            evaluation_method="spatial_distance_check"
        )
        
        distance_type = self.get_parameter('distance_type')
        required_distance = self.get_parameter('required_distance')
        measurement_method = self.get_parameter('measurement_method')
        target_types = self.get_parameter('target_types', set())
        
        violations_found = 0
        objects_checked = 0
        
        # Check distances between all object pairs
        for i, obj1 in enumerate(target_objects):
            # Get related objects to check against
            related_objects = context.get_related_objects(
                obj1, "spatial", search_radius=required_distance * 3
            )
            
            # Filter by target types if specified
            if target_types:
                related_objects = [obj for obj in related_objects 
                                 if obj.type in target_types]
            
            for obj2 in related_objects:
                objects_checked += 1
                
                # Calculate distance based on measurement method
                if measurement_method == "surface_to_surface":
                    actual_distance = SpatialConstraintValidator.calculate_surface_distance(obj1, obj2)
                else:  # center_to_center
                    actual_distance = SpatialConstraintValidator.calculate_3d_distance(obj1, obj2)
                
                # Check distance requirement
                violation_detected = False
                
                if distance_type == "minimum":
                    if actual_distance < required_distance:
                        violation_detected = True
                elif distance_type == "maximum":
                    if actual_distance > required_distance:
                        violation_detected = True
                elif distance_type == "exact":
                    tolerance = self.get_parameter('tolerance', 0.5)
                    if abs(actual_distance - required_distance) > tolerance:
                        violation_detected = True
                
                if violation_detected:
                    violations_found += 1
                    
                    # Create violation
                    violation = self.create_violation(
                        description=f"{distance_type.title()} distance violation: {actual_distance:.2f}ft "
                                   f"({distance_type} required: {required_distance:.2f}ft)",
                        primary_object=obj1,
                        secondary_objects=[obj2],
                        technical_details={
                            'actual_distance': actual_distance,
                            'required_distance': required_distance,
                            'distance_type': distance_type,
                            'measurement_method': measurement_method,
                            'gap_amount': abs(actual_distance - required_distance)
                        },
                        suggested_fixes=[
                            f"Relocate {obj1.type.value} to maintain {required_distance:.1f}ft {distance_type} distance",
                            f"Consider alternative positioning for {obj2.type.value}",
                            "Review design layout for spatial optimization"
                        ]
                    )
                    
                    result.add_violation(violation)
        
        # Update result metrics
        result.objects_checked = objects_checked
        result.evaluation_time_ms = (time.time() - start_time) * 1000
        
        logger.debug(f"Distance constraint evaluation: {violations_found} violations in {objects_checked} checks")
        
        return result
    
    def get_affected_systems(self) -> List[ArxObjectType]:
        """Get systems affected by this constraint."""
        source_types = self.get_parameter('source_types', set())
        target_types = self.get_parameter('target_types', set())
        
        affected = list(source_types | target_types)
        return affected if affected else []


class ClearanceConstraint(ParametricConstraint):
    """
    Clearance constraint for maintenance access and safety.
    
    Ensures adequate clearance around equipment and systems for
    maintenance access, safety egress, and operational requirements.
    """
    
    def __init__(self,
                 name: str = "Clearance Constraint",
                 required_clearance: float = 3.0,  # feet
                 clearance_direction: str = "all",  # "all", "front", "sides", "top", "bottom"
                 **kwargs):
        """Initialize clearance constraint."""
        super().__init__(
            name=name,
            constraint_type=ConstraintType.SPATIAL_CLEARANCE,
            **kwargs
        )
        
        self.set_parameter('required_clearance', required_clearance)
        self.set_parameter('clearance_direction', clearance_direction)
        self.set_parameter('equipment_types', {
            ArxObjectType.ELECTRICAL_PANEL,
            ArxObjectType.HVAC_UNIT,
            ArxObjectType.FIRE_EXTINGUISHER
        })
    
    def is_applicable(self, arxobject: ArxObject) -> bool:
        """Check if object requires clearance."""
        equipment_types = self.get_parameter('equipment_types')
        return arxobject.type in equipment_types
    
    def evaluate(self, 
                context: ConstraintEvaluationContext,
                target_objects: List[ArxObject]) -> ConstraintResult:
        """Evaluate clearance requirements."""
        start_time = time.time()
        
        result = ConstraintResult(
            constraint_id=self.constraint_id,
            constraint_name=self.name,
            is_satisfied=True,
            evaluation_time_ms=0.0,
            evaluated_objects=[obj.id for obj in target_objects],
            evaluation_method="clearance_check"
        )
        
        required_clearance = self.get_parameter('required_clearance')
        clearance_direction = self.get_parameter('clearance_direction')
        
        for equipment in target_objects:
            if not self.is_applicable(equipment):
                continue
            
            # Get nearby objects that might obstruct clearance
            nearby_objects = context.get_related_objects(
                equipment, "spatial", search_radius=required_clearance * 2
            )
            
            for nearby_obj in nearby_objects:
                # Check clearance violation
                is_violated, actual_clearance = SpatialConstraintValidator.calculate_clearance_violation(
                    equipment, nearby_obj, required_clearance
                )
                
                if is_violated:
                    violation = self.create_violation(
                        description=f"Insufficient clearance: {actual_clearance:.2f}ft "
                                   f"(required: {required_clearance:.2f}ft)",
                        primary_object=equipment,
                        secondary_objects=[nearby_obj],
                        severity=ConstraintSeverity.ERROR,
                        technical_details={
                            'actual_clearance': actual_clearance,
                            'required_clearance': required_clearance,
                            'clearance_deficit': required_clearance - actual_clearance,
                            'clearance_direction': clearance_direction
                        },
                        suggested_fixes=[
                            f"Relocate {nearby_obj.type.value} to provide {required_clearance:.1f}ft clearance",
                            f"Reposition {equipment.type.value} for better access",
                            "Consider alternative equipment placement"
                        ]
                    )
                    
                    result.add_violation(violation)
        
        result.evaluation_time_ms = (time.time() - start_time) * 1000
        return result


class AlignmentConstraint(ParametricConstraint):
    """
    Alignment constraint for consistent installation patterns.
    
    Ensures objects are properly aligned for aesthetic, functional,
    or installation requirements.
    """
    
    def __init__(self,
                 name: str = "Alignment Constraint", 
                 alignment_type: str = "horizontal",  # "horizontal", "vertical", "plane"
                 alignment_tolerance: float = 0.5,  # feet
                 **kwargs):
        """Initialize alignment constraint."""
        super().__init__(
            name=name,
            constraint_type=ConstraintType.SPATIAL_ALIGNMENT,
            **kwargs
        )
        
        self.set_parameter('alignment_type', alignment_type)
        self.set_parameter('alignment_tolerance', alignment_tolerance)
        self.set_parameter('object_groups', {})  # Groups of objects that should align
    
    def is_applicable(self, arxobject: ArxObject) -> bool:
        """Check if object should be included in alignment checks."""
        # Apply to objects that are typically aligned (outlets, lights, etc.)
        alignable_types = {
            ArxObjectType.ELECTRICAL_OUTLET,
            ArxObjectType.ELECTRICAL_FIXTURE,
            ArxObjectType.HVAC_DIFFUSER,
            ArxObjectType.FIRE_SPRINKLER
        }
        return arxobject.type in alignable_types
    
    def evaluate(self, 
                context: ConstraintEvaluationContext,
                target_objects: List[ArxObject]) -> ConstraintResult:
        """Evaluate alignment requirements."""
        start_time = time.time()
        
        result = ConstraintResult(
            constraint_id=self.constraint_id,
            constraint_name=self.name,
            is_satisfied=True,
            evaluation_time_ms=0.0,
            evaluated_objects=[obj.id for obj in target_objects],
            evaluation_method="alignment_check"
        )
        
        alignment_type = self.get_parameter('alignment_type')
        tolerance = self.get_parameter('alignment_tolerance')
        
        # Group objects by type for alignment checking
        objects_by_type = {}
        for obj in target_objects:
            if self.is_applicable(obj):
                obj_type = obj.type
                if obj_type not in objects_by_type:
                    objects_by_type[obj_type] = []
                objects_by_type[obj_type].append(obj)
        
        # Check alignment within each type group
        for obj_type, objects in objects_by_type.items():
            if len(objects) < 2:
                continue
            
            is_aligned, misaligned_objects = SpatialConstraintValidator.check_alignment(
                objects, alignment_type, tolerance
            )
            
            if not is_aligned:
                # Create violation for misaligned objects
                for misaligned_obj in misaligned_objects:
                    violation = self.create_violation(
                        description=f"{alignment_type.title()} alignment violation for {obj_type.value}",
                        primary_object=misaligned_obj,
                        secondary_objects=objects[:3],  # Reference objects
                        severity=ConstraintSeverity.WARNING,
                        technical_details={
                            'alignment_type': alignment_type,
                            'tolerance': tolerance,
                            'object_type': obj_type.value,
                            'misaligned_count': len(misaligned_objects),
                            'total_objects': len(objects)
                        },
                        suggested_fixes=[
                            f"Align {misaligned_obj.type.value} with other {obj_type.value} objects",
                            "Use consistent installation grid pattern",
                            "Review architectural drawings for alignment guidelines"
                        ]
                    )
                    
                    result.add_violation(violation)
        
        result.evaluation_time_ms = (time.time() - start_time) * 1000
        return result


class ContainmentConstraint(ParametricConstraint):
    """
    Containment constraint for spatial boundaries.
    
    Ensures objects are properly contained within designated areas,
    rooms, or zones as required by design or code.
    """
    
    def __init__(self,
                 name: str = "Containment Constraint",
                 container_types: Optional[Set[ArxObjectType]] = None,
                 contained_types: Optional[Set[ArxObjectType]] = None,
                 **kwargs):
        """Initialize containment constraint."""
        super().__init__(
            name=name,
            constraint_type=ConstraintType.SPATIAL_CONTAINMENT,
            **kwargs
        )
        
        self.set_parameter('container_types', container_types or {
            ArxObjectType.STRUCTURAL_WALL,
            ArxObjectType.STRUCTURAL_SLAB
        })
        
        self.set_parameter('contained_types', contained_types or {
            ArxObjectType.ELECTRICAL_OUTLET,
            ArxObjectType.HVAC_DIFFUSER,
            ArxObjectType.FIRE_SPRINKLER
        })
    
    def is_applicable(self, arxobject: ArxObject) -> bool:
        """Check if object should be contained."""
        contained_types = self.get_parameter('contained_types')
        return arxobject.type in contained_types
    
    def evaluate(self, 
                context: ConstraintEvaluationContext,
                target_objects: List[ArxObject]) -> ConstraintResult:
        """Evaluate containment requirements."""
        start_time = time.time()
        
        result = ConstraintResult(
            constraint_id=self.constraint_id,
            constraint_name=self.name,
            is_satisfied=True,
            evaluation_time_ms=0.0,
            evaluated_objects=[obj.id for obj in target_objects],
            evaluation_method="containment_check"
        )
        
        container_types = self.get_parameter('container_types')
        
        # Find potential container objects
        all_objects = list(context.spatial_engine.objects.values())
        containers = [obj for obj in all_objects if obj.type in container_types]
        
        for obj in target_objects:
            if not self.is_applicable(obj):
                continue
            
            # Check if object is contained by any container
            is_contained = False
            containing_objects = []
            
            for container in containers:
                violations = SpatialConstraintValidator.check_containment(container, [obj])
                if not violations:  # Object is contained
                    is_contained = True
                    containing_objects.append(container)
                    break
            
            if not is_contained:
                violation = self.create_violation(
                    description=f"{obj.type.value} is not properly contained within required boundaries",
                    primary_object=obj,
                    severity=ConstraintSeverity.ERROR,
                    technical_details={
                        'object_type': obj.type.value,
                        'containers_checked': len(containers),
                        'required_container_types': [ct.value for ct in container_types]
                    },
                    suggested_fixes=[
                        f"Move {obj.type.value} within appropriate boundary/room",
                        "Verify object placement against architectural drawings",
                        "Check if additional containment structures are needed"
                    ]
                )
                
                result.add_violation(violation)
        
        result.evaluation_time_ms = (time.time() - start_time) * 1000
        return result


logger.info("Spatial constraint validators initialized")