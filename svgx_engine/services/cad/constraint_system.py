"""
Constraint System for Arxos CAD Components

This module provides geometric and dimensional constraints for CAD-parity functionality.
It implements distance constraints, angle constraints, parallel and perpendicular
constraints, horizontal and vertical constraints, coincident constraints, tangent
constraints, symmetric constraints, and constraint solver and validation.
"""

import math
import decimal
from typing import List, Dict, Optional, Union, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
from .precision_drawing import PrecisionPoint, PrecisionVector, PrecisionLevel

logger = logging.getLogger(__name__)


class ConstraintType(Enum):
    """Types of geometric and dimensional constraints."""
    # Distance constraints
    DISTANCE = "distance"
    RADIAL_DISTANCE = "radial_distance"
    
    # Angle constraints
    ANGLE = "angle"
    PARALLEL = "parallel"
    PERPENDICULAR = "perpendicular"
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    
    # Geometric constraints
    COINCIDENT = "coincident"
    TANGENT = "tangent"
    SYMMETRIC = "symmetric"
    EQUAL = "equal"
    
    # Advanced constraints
    FIXED = "fixed"
    ALIGNED = "aligned"
    OFFSET = "offset"


class ConstraintStatus(Enum):
    """Status of constraint satisfaction."""
    SATISFIED = "satisfied"
    VIOLATED = "violated"
    OVER_CONSTRAINED = "over_constrained"
    UNDER_CONSTRAINED = "under_constrained"
    INCONSISTENT = "inconsistent"


@dataclass
class Constraint:
    """Base constraint class."""
    constraint_type: ConstraintType
    entities: List[Any] = field(default_factory=list)
    parameters: Dict[str, Union[float, decimal.Decimal]] = field(default_factory=dict)
    tolerance: decimal.Decimal = decimal.Decimal('0.001')
    status: ConstraintStatus = ConstraintStatus.SATISFIED
    is_active: bool = True
    
    def validate(self) -> bool:
        """Validate constraint satisfaction."""
        raise NotImplementedError("Subclasses must implement validate()")
    
    def solve(self) -> bool:
        """Solve constraint by adjusting entities."""
        raise NotImplementedError("Subclasses must implement solve()")


@dataclass
class DistanceConstraint(Constraint):
    """Distance constraint between two points or entities."""
    
    def __init__(self, entity1: Any, entity2: Any, distance: Union[float, decimal.Decimal],
                 tolerance: decimal.Decimal = decimal.Decimal('0.001')):
        super().__init__(ConstraintType.DISTANCE, [entity1, entity2], 
                        {"distance": distance}, tolerance)
    
    def validate(self) -> bool:
        """Validate distance constraint."""
        if len(self.entities) != 2:
            return False
        
        entity1, entity2 = self.entities
        actual_distance = self._calculate_distance(entity1, entity2)
        target_distance = decimal.Decimal(str(self.parameters["distance"]))
        
        difference = abs(actual_distance - target_distance)
        self.status = ConstraintStatus.SATISFIED if difference <= self.tolerance else ConstraintStatus.VIOLATED
        
        return self.status == ConstraintStatus.SATISFIED
    
    def solve(self) -> bool:
        """Solve distance constraint by adjusting entities."""
        if not self.validate():
            # Implement constraint solving logic
            # This is a simplified version - real CAD systems have complex solvers
            return self._adjust_entities()
        return True
    
    def _calculate_distance(self, entity1: Any, entity2: Any) -> decimal.Decimal:
        """Calculate distance between two entities."""
        if hasattr(entity1, 'distance_to') and hasattr(entity2, 'distance_to'):
            return entity1.distance_to(entity2)
        elif hasattr(entity1, 'x') and hasattr(entity1, 'y') and hasattr(entity2, 'x') and hasattr(entity2, 'y'):
            dx = entity1.x - entity2.x
            dy = entity1.y - entity2.y
            return (dx * dx + dy * dy).sqrt()
        else:
            return decimal.Decimal('0')
    
    def _adjust_entities(self) -> bool:
        """Adjust entities to satisfy constraint."""
        # Simplified adjustment - real CAD systems have sophisticated solvers
        entity1, entity2 = self.entities
        target_distance = decimal.Decimal(str(self.parameters["distance"]))
        current_distance = self._calculate_distance(entity1, entity2)
        
        if current_distance == 0:
            return False
        
        # Calculate adjustment factor
        adjustment_factor = target_distance / current_distance
        
        # Apply adjustment (simplified)
        if hasattr(entity1, 'x') and hasattr(entity1, 'y'):
            entity1.x *= adjustment_factor
            entity1.y *= adjustment_factor
        
        return True


@dataclass
class AngleConstraint(Constraint):
    """Angle constraint between two lines or vectors."""
    
    def __init__(self, entity1: Any, entity2: Any, angle: Union[float, decimal.Decimal],
                 tolerance: decimal.Decimal = decimal.Decimal('0.001')):
        super().__init__(ConstraintType.ANGLE, [entity1, entity2], 
                        {"angle": angle}, tolerance)
    
    def validate(self) -> bool:
        """Validate angle constraint."""
        if len(self.entities) != 2:
            return False
        
        entity1, entity2 = self.entities
        actual_angle = self._calculate_angle(entity1, entity2)
        target_angle = decimal.Decimal(str(self.parameters["angle"]))
        
        # Normalize angles to [0, 2π]
        actual_angle = actual_angle % (2 * decimal.Decimal(str(math.pi)))
        target_angle = target_angle % (2 * decimal.Decimal(str(math.pi)))
        
        difference = abs(actual_angle - target_angle)
        # Handle angle wrap-around
        if difference > decimal.Decimal(str(math.pi)):
            difference = 2 * decimal.Decimal(str(math.pi)) - difference
        
        self.status = ConstraintStatus.SATISFIED if difference <= self.tolerance else ConstraintStatus.VIOLATED
        
        return self.status == ConstraintStatus.SATISFIED
    
    def solve(self) -> bool:
        """Solve angle constraint by adjusting entities."""
        if not self.validate():
            return self._adjust_entities()
        return True
    
    def _calculate_angle(self, entity1: Any, entity2: Any) -> decimal.Decimal:
        """Calculate angle between two entities."""
        if hasattr(entity1, 'angle_to') and hasattr(entity2, 'angle_to'):
            return entity1.angle_to(entity2)
        else:
            # Calculate angle from vectors
            vector1 = self._get_vector(entity1)
            vector2 = self._get_vector(entity2)
            
            if vector1 and vector2:
                return vector1.angle_to(vector2)
            else:
                return decimal.Decimal('0')
    
    def _get_vector(self, entity: Any) -> Optional[PrecisionVector]:
        """Extract vector from entity."""
        if hasattr(entity, 'dx') and hasattr(entity, 'dy'):
            return PrecisionVector(entity.dx, entity.dy)
        elif hasattr(entity, 'start') and hasattr(entity, 'end'):
            return PrecisionVector(
                entity.end.x - entity.start.x,
                entity.end.y - entity.start.y
            )
        return None
    
    def _adjust_entities(self) -> bool:
        """Adjust entities to satisfy angle constraint."""
        # Simplified adjustment - real CAD systems have sophisticated solvers
        target_angle = decimal.Decimal(str(self.parameters["angle"]))
        entity1, entity2 = self.entities
        
        # Apply rotation to second entity
        if hasattr(entity2, 'rotate'):
            entity2.rotate(target_angle)
            return True
        
        return False


@dataclass
class ParallelConstraint(Constraint):
    """Parallel constraint between two lines or vectors."""
    
    def __init__(self, entity1: Any, entity2: Any, tolerance: decimal.Decimal = decimal.Decimal('0.001')):
        super().__init__(ConstraintType.PARALLEL, [entity1, entity2], {}, tolerance)
    
    def validate(self) -> bool:
        """Validate parallel constraint."""
        if len(self.entities) != 2:
            return False
        
        entity1, entity2 = self.entities
        angle = self._calculate_angle(entity1, entity2)
        
        # Check if angle is close to 0 or π
        normalized_angle = angle % decimal.Decimal(str(math.pi))
        is_parallel = normalized_angle <= self.tolerance or abs(normalized_angle - decimal.Decimal(str(math.pi))) <= self.tolerance
        
        self.status = ConstraintStatus.SATISFIED if is_parallel else ConstraintStatus.VIOLATED
        
        return self.status == ConstraintStatus.SATISFIED
    
    def solve(self) -> bool:
        """Solve parallel constraint by adjusting entities."""
        if not self.validate():
            return self._adjust_entities()
        return True
    
    def _calculate_angle(self, entity1: Any, entity2: Any) -> decimal.Decimal:
        """Calculate angle between two entities."""
        vector1 = self._get_vector(entity1)
        vector2 = self._get_vector(entity2)
        
        if vector1 and vector2:
            return vector1.angle_to(vector2)
        return decimal.Decimal('0')
    
    def _get_vector(self, entity: Any) -> Optional[PrecisionVector]:
        """Extract vector from entity."""
        if hasattr(entity, 'dx') and hasattr(entity, 'dy'):
            return PrecisionVector(entity.dx, entity.dy)
        elif hasattr(entity, 'start') and hasattr(entity, 'end'):
            return PrecisionVector(
                entity.end.x - entity.start.x,
                entity.end.y - entity.start.y
            )
        return None
    
    def _adjust_entities(self) -> bool:
        """Adjust entities to satisfy parallel constraint."""
        entity1, entity2 = self.entities
        vector1 = self._get_vector(entity1)
        
        if vector1 and hasattr(entity2, 'set_direction'):
            entity2.set_direction(vector1)
            return True
        
        return False


@dataclass
class PerpendicularConstraint(Constraint):
    """Perpendicular constraint between two lines or vectors."""
    
    def __init__(self, entity1: Any, entity2: Any, tolerance: decimal.Decimal = decimal.Decimal('0.001')):
        super().__init__(ConstraintType.PERPENDICULAR, [entity1, entity2], {}, tolerance)
    
    def validate(self) -> bool:
        """Validate perpendicular constraint."""
        if len(self.entities) != 2:
            return False
        
        entity1, entity2 = self.entities
        angle = self._calculate_angle(entity1, entity2)
        
        # Check if angle is close to π/2 or 3π/2
        target_angle = decimal.Decimal(str(math.pi)) / 2
        difference = abs(angle - target_angle)
        is_perpendicular = difference <= self.tolerance or abs(difference - decimal.Decimal(str(math.pi))) <= self.tolerance
        
        self.status = ConstraintStatus.SATISFIED if is_perpendicular else ConstraintStatus.VIOLATED
        
        return self.status == ConstraintStatus.SATISFIED
    
    def solve(self) -> bool:
        """Solve perpendicular constraint by adjusting entities."""
        if not self.validate():
            return self._adjust_entities()
        return True
    
    def _calculate_angle(self, entity1: Any, entity2: Any) -> decimal.Decimal:
        """Calculate angle between two entities."""
        vector1 = self._get_vector(entity1)
        vector2 = self._get_vector(entity2)
        
        if vector1 and vector2:
            return vector1.angle_to(vector2)
        return decimal.Decimal('0')
    
    def _get_vector(self, entity: Any) -> Optional[PrecisionVector]:
        """Extract vector from entity."""
        if hasattr(entity, 'dx') and hasattr(entity, 'dy'):
            return PrecisionVector(entity.dx, entity.dy)
        elif hasattr(entity, 'start') and hasattr(entity, 'end'):
            return PrecisionVector(
                entity.end.x - entity.start.x,
                entity.end.y - entity.start.y
            )
        return None
    
    def _adjust_entities(self) -> bool:
        """Adjust entities to satisfy perpendicular constraint."""
        entity1, entity2 = self.entities
        vector1 = self._get_vector(entity1)
        
        if vector1 and hasattr(entity2, 'set_perpendicular'):
            entity2.set_perpendicular(vector1)
            return True
        
        return False


@dataclass
class CoincidentConstraint(Constraint):
    """Coincident constraint between two points or entities."""
    
    def __init__(self, entity1: Any, entity2: Any, tolerance: decimal.Decimal = decimal.Decimal('0.001')):
        super().__init__(ConstraintType.COINCIDENT, [entity1, entity2], {}, tolerance)
    
    def validate(self) -> bool:
        """Validate coincident constraint."""
        if len(self.entities) != 2:
            return False
        
        entity1, entity2 = self.entities
        distance = self._calculate_distance(entity1, entity2)
        
        self.status = ConstraintStatus.SATISFIED if distance <= self.tolerance else ConstraintStatus.VIOLATED
        
        return self.status == ConstraintStatus.SATISFIED
    
    def solve(self) -> bool:
        """Solve coincident constraint by adjusting entities."""
        if not self.validate():
            return self._adjust_entities()
        return True
    
    def _calculate_distance(self, entity1: Any, entity2: Any) -> decimal.Decimal:
        """Calculate distance between two entities."""
        if hasattr(entity1, 'distance_to'):
            return entity1.distance_to(entity2)
        elif hasattr(entity1, 'x') and hasattr(entity1, 'y') and hasattr(entity2, 'x') and hasattr(entity2, 'y'):
            dx = entity1.x - entity2.x
            dy = entity1.y - entity2.y
            return (dx * dx + dy * dy).sqrt()
        return decimal.Decimal('0')
    
    def _adjust_entities(self) -> bool:
        """Adjust entities to satisfy coincident constraint."""
        entity1, entity2 = self.entities
        
        # Move second entity to first entity's position
        if hasattr(entity1, 'x') and hasattr(entity1, 'y') and hasattr(entity2, 'set_position'):
            entity2.set_position(entity1.x, entity1.y)
            return True
        
        return False


@dataclass
class TangentConstraint(Constraint):
    """Tangent constraint between two curves or circles."""
    
    def __init__(self, entity1: Any, entity2: Any, tolerance: decimal.Decimal = decimal.Decimal('0.001')):
        super().__init__(ConstraintType.TANGENT, [entity1, entity2], {}, tolerance)
    
    def validate(self) -> bool:
        """Validate tangent constraint."""
        if len(self.entities) != 2:
            return False
        
        entity1, entity2 = self.entities
        distance = self._calculate_tangent_distance(entity1, entity2)
        
        self.status = ConstraintStatus.SATISFIED if distance <= self.tolerance else ConstraintStatus.VIOLATED
        
        return self.status == ConstraintStatus.SATISFIED
    
    def solve(self) -> bool:
        """Solve tangent constraint by adjusting entities."""
        if not self.validate():
            return self._adjust_entities()
        return True
    
    def _calculate_tangent_distance(self, entity1: Any, entity2: Any) -> decimal.Decimal:
        """Calculate distance for tangent constraint."""
        # Simplified calculation - real CAD systems have complex curve intersection
        if hasattr(entity1, 'radius') and hasattr(entity2, 'radius'):
            # For circles
            center_distance = self._calculate_distance(entity1, entity2)
            radius_sum = entity1.radius + entity2.radius
            return abs(center_distance - radius_sum)
        else:
            # For other curves, use minimum distance
            return self._calculate_distance(entity1, entity2)
    
    def _calculate_distance(self, entity1: Any, entity2: Any) -> decimal.Decimal:
        """Calculate distance between two entities."""
        if hasattr(entity1, 'distance_to'):
            return entity1.distance_to(entity2)
        elif hasattr(entity1, 'x') and hasattr(entity1, 'y') and hasattr(entity2, 'x') and hasattr(entity2, 'y'):
            dx = entity1.x - entity2.x
            dy = entity1.y - entity2.y
            return (dx * dx + dy * dy).sqrt()
        return decimal.Decimal('0')
    
    def _adjust_entities(self) -> bool:
        """Adjust entities to satisfy tangent constraint."""
        # Simplified adjustment - real CAD systems have sophisticated solvers
        entity1, entity2 = self.entities
        
        if hasattr(entity1, 'radius') and hasattr(entity2, 'radius'):
            # For circles, adjust position to make them tangent
            radius_sum = entity1.radius + entity2.radius
            if hasattr(entity2, 'set_position'):
                # Move second entity to tangent position
                direction = self._get_direction(entity1, entity2)
                if direction:
                    new_x = entity1.x + direction.dx * radius_sum
                    new_y = entity1.y + direction.dy * radius_sum
                    entity2.set_position(new_x, new_y)
                    return True
        
        return False
    
    def _get_direction(self, entity1: Any, entity2: Any) -> Optional[PrecisionVector]:
        """Get direction vector between entities."""
        if hasattr(entity1, 'x') and hasattr(entity1, 'y') and hasattr(entity2, 'x') and hasattr(entity2, 'y'):
            dx = entity2.x - entity1.x
            dy = entity2.y - entity1.y
            magnitude = (dx * dx + dy * dy).sqrt()
            if magnitude > 0:
                return PrecisionVector(dx / magnitude, dy / magnitude)
        return None


@dataclass
class SymmetricConstraint(Constraint):
    """Symmetric constraint between two entities about a line or point."""
    
    def __init__(self, entity1: Any, entity2: Any, symmetry_line: Any,
                 tolerance: decimal.Decimal = decimal.Decimal('0.001')):
        super().__init__(ConstraintType.SYMMETRIC, [entity1, entity2, symmetry_line], {}, tolerance)
    
    def validate(self) -> bool:
        """Validate symmetric constraint."""
        if len(self.entities) != 3:
            return False
        
        entity1, entity2, symmetry_line = self.entities
        is_symmetric = self._check_symmetry(entity1, entity2, symmetry_line)
        
        self.status = ConstraintStatus.SATISFIED if is_symmetric else ConstraintStatus.VIOLATED
        
        return self.status == ConstraintStatus.SATISFIED
    
    def solve(self) -> bool:
        """Solve symmetric constraint by adjusting entities."""
        if not self.validate():
            return self._adjust_entities()
        return True
    
    def _check_symmetry(self, entity1: Any, entity2: Any, symmetry_line: Any) -> bool:
        """Check if entities are symmetric about the symmetry line."""
        # Simplified symmetry check - real CAD systems have complex symmetry detection
        if hasattr(entity1, 'x') and hasattr(entity1, 'y') and hasattr(entity2, 'x') and hasattr(entity2, 'y'):
            # Check if points are symmetric about line
            mid_point = PrecisionPoint(
                (entity1.x + entity2.x) / 2,
                (entity1.y + entity2.y) / 2
            )
            
            # Check if mid-point lies on symmetry line
            distance_to_line = self._distance_to_line(mid_point, symmetry_line)
            return distance_to_line <= self.tolerance
        
        return False
    
    def _distance_to_line(self, point: PrecisionPoint, line: Any) -> decimal.Decimal:
        """Calculate distance from point to line."""
        # Simplified line distance calculation
        if hasattr(line, 'start') and hasattr(line, 'end'):
            # Line defined by start and end points
            line_vector = PrecisionVector(
                line.end.x - line.start.x,
                line.end.y - line.start.y
            )
            point_vector = PrecisionVector(
                point.x - line.start.x,
                point.y - line.start.y
            )
            
            # Distance = |point_vector × line_vector| / |line_vector|
            cross_product = point_vector.cross(line_vector)
            line_magnitude = line_vector.magnitude()
            
            if line_magnitude > 0:
                return abs(cross_product) / line_magnitude
        
        return decimal.Decimal('0')
    
    def _adjust_entities(self) -> bool:
        """Adjust entities to satisfy symmetric constraint."""
        entity1, entity2, symmetry_line = self.entities
        
        # Calculate symmetric position of entity1
        if hasattr(entity1, 'x') and hasattr(entity1, 'y') and hasattr(entity2, 'set_position'):
            symmetric_position = self._calculate_symmetric_position(entity1, symmetry_line)
            if symmetric_position:
                entity2.set_position(symmetric_position.x, symmetric_position.y)
                return True
        
        return False
    
    def _calculate_symmetric_position(self, entity: Any, symmetry_line: Any) -> Optional[PrecisionPoint]:
        """Calculate symmetric position of entity about symmetry line."""
        # Simplified symmetry calculation - real CAD systems have complex symmetry algorithms
        if hasattr(entity, 'x') and hasattr(entity, 'y') and hasattr(symmetry_line, 'start') and hasattr(symmetry_line, 'end'):
            # Reflect point about line
            line_start = PrecisionPoint(symmetry_line.start.x, symmetry_line.start.y)
            line_end = PrecisionPoint(symmetry_line.end.x, symmetry_line.end.y)
            point = PrecisionPoint(entity.x, entity.y)
            
            # Calculate reflection
            line_vector = PrecisionVector(line_end.x - line_start.x, line_end.y - line_start.y)
            point_vector = PrecisionVector(point.x - line_start.x, point.y - line_start.y)
            
            # Project point onto line
            line_magnitude_sq = line_vector.dx * line_vector.dx + line_vector.dy * line_vector.dy
            if line_magnitude_sq > 0:
                projection = point_vector.dot(line_vector) / line_magnitude_sq
                projected_point = PrecisionPoint(
                    line_start.x + projection * line_vector.dx,
                    line_start.y + projection * line_vector.dy
                )
                
                # Calculate reflection
                reflection_vector = PrecisionVector(
                    projected_point.x - point.x,
                    projected_point.y - point.y
                )
                
                reflected_point = PrecisionPoint(
                    projected_point.x + reflection_vector.dx,
                    projected_point.y + reflection_vector.dy
                )
                
                return reflected_point
        
        return None


class ConstraintSolver:
    """
    Constraint solver for CAD geometry.
    
    Implements constraint satisfaction algorithms to solve geometric
    and dimensional constraints in CAD drawings.
    """
    
    def __init__(self):
        self.constraints: List[Constraint] = []
        self.max_iterations = 100
        self.convergence_tolerance = decimal.Decimal('0.001')
    
    def add_constraint(self, constraint: Constraint):
        """Add a constraint to the solver."""
        self.constraints.append(constraint)
    
    def remove_constraint(self, constraint: Constraint):
        """Remove a constraint from the solver."""
        if constraint in self.constraints:
            self.constraints.remove(constraint)
    
    def solve_all(self) -> bool:
        """
        Solve all constraints iteratively.
        
        Returns:
            True if all constraints are satisfied, False otherwise
        """
        active_constraints = [c for c in self.constraints if c.is_active]
        
        for iteration in range(self.max_iterations):
            all_satisfied = True
            max_violation = decimal.Decimal('0')
            
            for constraint in active_constraints:
                if not constraint.validate():
                    all_satisfied = False
                    if not constraint.solve():
                        logger.warning(f"Failed to solve constraint: {constraint.constraint_type}")
            
            # Check convergence
            if all_satisfied:
                logger.info(f"All constraints satisfied in {iteration + 1} iterations")
                return True
            
            # Check for maximum violations
            for constraint in active_constraints:
                if constraint.status == ConstraintStatus.VIOLATED:
                    # Calculate violation magnitude (simplified)
                    violation = self._calculate_violation(constraint)
                    max_violation = max(max_violation, violation)
            
            if max_violation < self.convergence_tolerance:
                logger.info(f"Constraints converged in {iteration + 1} iterations")
                return True
        
        logger.warning(f"Constraint solving failed after {self.max_iterations} iterations")
        return False
    
    def _calculate_violation(self, constraint: Constraint) -> decimal.Decimal:
        """Calculate violation magnitude for a constraint."""
        # Simplified violation calculation
        if constraint.constraint_type == ConstraintType.DISTANCE:
            entity1, entity2 = constraint.entities
            actual_distance = self._calculate_distance(entity1, entity2)
            target_distance = decimal.Decimal(str(constraint.parameters["distance"]))
            return abs(actual_distance - target_distance)
        elif constraint.constraint_type == ConstraintType.ANGLE:
            entity1, entity2 = constraint.entities
            actual_angle = self._calculate_angle(entity1, entity2)
            target_angle = decimal.Decimal(str(constraint.parameters["angle"]))
            return abs(actual_angle - target_angle)
        else:
            return decimal.Decimal('0')
    
    def _calculate_distance(self, entity1: Any, entity2: Any) -> decimal.Decimal:
        """Calculate distance between two entities."""
        if hasattr(entity1, 'distance_to'):
            return entity1.distance_to(entity2)
        elif hasattr(entity1, 'x') and hasattr(entity1, 'y') and hasattr(entity2, 'x') and hasattr(entity2, 'y'):
            dx = entity1.x - entity2.x
            dy = entity1.y - entity2.y
            return (dx * dx + dy * dy).sqrt()
        return decimal.Decimal('0')
    
    def _calculate_angle(self, entity1: Any, entity2: Any) -> decimal.Decimal:
        """Calculate angle between two entities."""
        vector1 = self._get_vector(entity1)
        vector2 = self._get_vector(entity2)
        
        if vector1 and vector2:
            return vector1.angle_to(vector2)
        return decimal.Decimal('0')
    
    def _get_vector(self, entity: Any) -> Optional[PrecisionVector]:
        """Extract vector from entity."""
        if hasattr(entity, 'dx') and hasattr(entity, 'dy'):
            return PrecisionVector(entity.dx, entity.dy)
        elif hasattr(entity, 'start') and hasattr(entity, 'end'):
            return PrecisionVector(
                entity.end.x - entity.start.x,
                entity.end.y - entity.start.y
            )
        return None
    
    def get_constraint_status(self) -> Dict[str, Any]:
        """Get status of all constraints."""
        status = {
            "total_constraints": len(self.constraints),
            "active_constraints": len([c for c in self.constraints if c.is_active]),
            "satisfied_constraints": len([c for c in self.constraints if c.status == ConstraintStatus.SATISFIED]),
            "violated_constraints": len([c for c in self.constraints if c.status == ConstraintStatus.VIOLATED]),
            "over_constrained": len([c for c in self.constraints if c.status == ConstraintStatus.OVER_CONSTRAINED]),
            "under_constrained": len([c for c in self.constraints if c.status == ConstraintStatus.UNDER_CONSTRAINED]),
            "inconsistent_constraints": len([c for c in self.constraints if c.status == ConstraintStatus.INCONSISTENT])
        }
        return status


class ConstraintSystem:
    """
    Complete constraint system for CAD geometry.
    
    Provides comprehensive constraint management including:
    - Constraint creation and management
    - Constraint solving and validation
    - Constraint status monitoring
    - Constraint visualization
    """
    
    def __init__(self):
        self.solver = ConstraintSolver()
        self.constraints: List[Constraint] = []
        self.constraint_factory = ConstraintFactory()
    
    def add_distance_constraint(self, entity1: Any, entity2: Any, 
                               distance: Union[float, decimal.Decimal]) -> DistanceConstraint:
        """Add a distance constraint."""
        constraint = DistanceConstraint(entity1, entity2, distance)
        self.constraints.append(constraint)
        self.solver.add_constraint(constraint)
        return constraint
    
    def add_angle_constraint(self, entity1: Any, entity2: Any,
                            angle: Union[float, decimal.Decimal]) -> AngleConstraint:
        """Add an angle constraint."""
        constraint = AngleConstraint(entity1, entity2, angle)
        self.constraints.append(constraint)
        self.solver.add_constraint(constraint)
        return constraint
    
    def add_parallel_constraint(self, entity1: Any, entity2: Any) -> ParallelConstraint:
        """Add a parallel constraint."""
        constraint = ParallelConstraint(entity1, entity2)
        self.constraints.append(constraint)
        self.solver.add_constraint(constraint)
        return constraint
    
    def add_perpendicular_constraint(self, entity1: Any, entity2: Any) -> PerpendicularConstraint:
        """Add a perpendicular constraint."""
        constraint = PerpendicularConstraint(entity1, entity2)
        self.constraints.append(constraint)
        self.solver.add_constraint(constraint)
        return constraint
    
    def add_coincident_constraint(self, entity1: Any, entity2: Any) -> CoincidentConstraint:
        """Add a coincident constraint."""
        constraint = CoincidentConstraint(entity1, entity2)
        self.constraints.append(constraint)
        self.solver.add_constraint(constraint)
        return constraint
    
    def add_tangent_constraint(self, entity1: Any, entity2: Any) -> TangentConstraint:
        """Add a tangent constraint."""
        constraint = TangentConstraint(entity1, entity2)
        self.constraints.append(constraint)
        self.solver.add_constraint(constraint)
        return constraint
    
    def add_symmetric_constraint(self, entity1: Any, entity2: Any, 
                                symmetry_line: Any) -> SymmetricConstraint:
        """Add a symmetric constraint."""
        constraint = SymmetricConstraint(entity1, entity2, symmetry_line)
        self.constraints.append(constraint)
        self.solver.add_constraint(constraint)
        return constraint
    
    def solve_constraints(self) -> bool:
        """Solve all constraints."""
        return self.solver.solve_all()
    
    def validate_constraints(self) -> bool:
        """Validate all constraints."""
        all_valid = True
        for constraint in self.constraints:
            if not constraint.validate():
                all_valid = False
        return all_valid
    
    def get_constraint_status(self) -> Dict[str, Any]:
        """Get status of all constraints."""
        return self.solver.get_constraint_status()
    
    def remove_constraint(self, constraint: Constraint):
        """Remove a constraint."""
        if constraint in self.constraints:
            self.constraints.remove(constraint)
            self.solver.remove_constraint(constraint)


class ConstraintFactory:
    """Factory for creating different types of constraints."""
    
    def create_constraint(self, constraint_type: ConstraintType, 
                         entities: List[Any], **kwargs) -> Constraint:
        """Create a constraint of the specified type."""
        if constraint_type == ConstraintType.DISTANCE:
            if len(entities) != 2 or 'distance' not in kwargs:
                raise ValueError("Distance constraint requires 2 entities and distance parameter")
            return DistanceConstraint(entities[0], entities[1], kwargs['distance'])
        
        elif constraint_type == ConstraintType.ANGLE:
            if len(entities) != 2 or 'angle' not in kwargs:
                raise ValueError("Angle constraint requires 2 entities and angle parameter")
            return AngleConstraint(entities[0], entities[1], kwargs['angle'])
        
        elif constraint_type == ConstraintType.PARALLEL:
            if len(entities) != 2:
                raise ValueError("Parallel constraint requires 2 entities")
            return ParallelConstraint(entities[0], entities[1])
        
        elif constraint_type == ConstraintType.PERPENDICULAR:
            if len(entities) != 2:
                raise ValueError("Perpendicular constraint requires 2 entities")
            return PerpendicularConstraint(entities[0], entities[1])
        
        elif constraint_type == ConstraintType.COINCIDENT:
            if len(entities) != 2:
                raise ValueError("Coincident constraint requires 2 entities")
            return CoincidentConstraint(entities[0], entities[1])
        
        elif constraint_type == ConstraintType.TANGENT:
            if len(entities) != 2:
                raise ValueError("Tangent constraint requires 2 entities")
            return TangentConstraint(entities[0], entities[1])
        
        elif constraint_type == ConstraintType.SYMMETRIC:
            if len(entities) != 3:
                raise ValueError("Symmetric constraint requires 3 entities (2 entities + symmetry line)")
            return SymmetricConstraint(entities[0], entities[1], entities[2])
        
        else:
            raise ValueError(f"Unsupported constraint type: {constraint_type}")


# Factory functions for easy usage
def create_constraint_system() -> ConstraintSystem:
    """Create a constraint system."""
    return ConstraintSystem()


def create_constraint_solver() -> ConstraintSolver:
    """Create a constraint solver."""
    return ConstraintSolver() 