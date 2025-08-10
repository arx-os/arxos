"""
Optimization-Aware Conflict Resolution System.

Advanced conflict resolution that uses optimization algorithms to automatically
resolve spatial conflicts and constraint violations in Building-Infrastructure-as-Code.
"""

import time
import logging
import math
from typing import Dict, Any, List, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import random
import copy

# Import Phase 1 and 2 components
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.spatial import (
    SpatialConflictEngine, ArxObject, ArxObjectType, BoundingBox3D,
    ConflictType
)
from core.constraints import (
    ConstraintViolation, ConstraintSeverity, IntegratedValidator
)

# Import optimization components
from .optimization_core import (
    OptimizationObjective, OptimizationVariable, OptimizationConstraint,
    OptimizationResult, OptimizationConfiguration, VariableType,
    OptimizationType
)
from .optimization_engine import OptimizationEngine, OptimizationContext
from .optimization_algorithms import GeneticAlgorithm, SimulatedAnnealing

logger = logging.getLogger(__name__)


class ResolutionStrategy(Enum):
    """Conflict resolution strategies."""
    
    MINIMAL_DISPLACEMENT = "minimal_displacement"
    COST_MINIMIZATION = "cost_minimization"  
    PRIORITY_BASED = "priority_based"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    MULTI_OBJECTIVE = "multi_objective"
    CONSTRAINT_RELAXATION = "constraint_relaxation"


class ResolutionScope(Enum):
    """Scope of conflict resolution."""
    
    LOCAL = "local"  # Resolve individual conflicts
    REGIONAL = "regional"  # Resolve conflicts in area
    GLOBAL = "global"  # Optimize entire system
    INCREMENTAL = "incremental"  # Step-by-step resolution


@dataclass
class ConflictGroup:
    """Group of related conflicts that should be resolved together."""
    
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    constraint_violations: List[ConstraintViolation] = field(default_factory=list)
    affected_objects: Set[str] = field(default_factory=set)
    
    # Group metadata
    group_id: str = ""
    priority: int = 1  # 1 = highest priority
    resolution_complexity: str = "medium"  # "simple", "medium", "complex"
    
    # Spatial bounds
    bounding_region: Optional[BoundingBox3D] = None
    
    def calculate_severity_score(self) -> float:
        """Calculate overall severity score for conflict group."""
        
        severity_weights = {
            'critical': 100,
            'high': 10,
            'medium': 3,
            'low': 1
        }
        
        # Conflict severity
        conflict_score = sum(severity_weights.get(conflict.get('severity', 'medium'), 3) 
                           for conflict in self.conflicts)
        
        # Constraint violation severity
        constraint_weights = {
            ConstraintSeverity.CRITICAL: 100,
            ConstraintSeverity.ERROR: 10,
            ConstraintSeverity.WARNING: 3,
            ConstraintSeverity.INFO: 1,
            ConstraintSeverity.SUGGESTION: 0.5
        }
        
        constraint_score = sum(constraint_weights.get(violation.severity, 3) 
                             for violation in self.constraint_violations)
        
        return conflict_score + constraint_score


@dataclass 
class ResolutionSolution:
    """Proposed resolution solution."""
    
    # Object modifications
    object_positions: Dict[str, Tuple[float, float, float]] = field(default_factory=dict)
    object_orientations: Dict[str, Tuple[float, float, float]] = field(default_factory=dict)
    object_sizes: Dict[str, Tuple[float, float, float]] = field(default_factory=dict)
    object_properties: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Solution quality metrics
    conflicts_resolved: int = 0
    violations_resolved: int = 0
    displacement_cost: float = 0.0
    modification_cost: float = 0.0
    performance_impact: float = 0.0
    
    # Solution metadata
    solution_id: str = ""
    generation_method: str = ""
    confidence_score: float = 0.0
    
    def apply_to_spatial_engine(self, spatial_engine: SpatialConflictEngine) -> bool:
        """Apply resolution solution to spatial engine."""
        
        try:
            # Apply position changes
            for obj_id, (x, y, z) in self.object_positions.items():
                if obj_id in spatial_engine.objects:
                    obj = spatial_engine.objects[obj_id]
                    obj.geometry.x = x
                    obj.geometry.y = y
                    obj.geometry.z = z
            
            # Apply orientation changes
            for obj_id, (rx, ry, rz) in self.object_orientations.items():
                if obj_id in spatial_engine.objects:
                    obj = spatial_engine.objects[obj_id]
                    obj.geometry.rotation_x = rx
                    obj.geometry.rotation_y = ry
                    obj.geometry.rotation_z = rz
            
            # Apply size changes
            for obj_id, (length, width, height) in self.object_sizes.items():
                if obj_id in spatial_engine.objects:
                    obj = spatial_engine.objects[obj_id]
                    obj.geometry.length = length
                    obj.geometry.width = width
                    obj.geometry.height = height
            
            # Apply property changes
            for obj_id, properties in self.object_properties.items():
                if obj_id in spatial_engine.objects:
                    obj = spatial_engine.objects[obj_id]
                    if obj.metadata:
                        for prop_name, prop_value in properties.items():
                            setattr(obj.metadata, prop_name, prop_value)
            
            # Update spatial indices
            for obj_id in (set(self.object_positions.keys()) | 
                          set(self.object_orientations.keys()) | 
                          set(self.object_sizes.keys())):
                if obj_id in spatial_engine.objects:
                    obj = spatial_engine.objects[obj_id]
                    try:
                        spatial_engine.octree.remove(obj)
                        spatial_engine.rtree.remove(obj)
                    except:
                        pass
                    spatial_engine.octree.insert(obj)
                    spatial_engine.rtree.insert(obj)
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying resolution solution: {e}")
            return False
    
    def calculate_total_cost(self) -> float:
        """Calculate total cost of resolution solution."""
        return self.displacement_cost + self.modification_cost + abs(self.performance_impact)


class OptimizationBasedResolver:
    """
    Optimization-based conflict resolution system.
    
    Uses optimization algorithms to automatically resolve conflicts and 
    constraint violations by finding optimal object repositioning and modifications.
    """
    
    def __init__(self, 
                 spatial_engine: SpatialConflictEngine,
                 integrated_validator: IntegratedValidator,
                 configuration: Optional[OptimizationConfiguration] = None):
        """
        Initialize optimization-based resolver.
        
        Args:
            spatial_engine: Phase 1 spatial conflict engine
            integrated_validator: Phase 2 integrated validator  
            configuration: Optimization configuration
        """
        
        self.spatial_engine = spatial_engine
        self.integrated_validator = integrated_validator
        self.configuration = configuration or OptimizationConfiguration()
        
        # Resolution settings
        self.default_strategy = ResolutionStrategy.MINIMAL_DISPLACEMENT
        self.default_scope = ResolutionScope.LOCAL
        self.max_displacement_distance = 20.0  # feet
        self.displacement_cost_per_foot = 1.0
        self.modification_cost_base = 100.0
        
        # Performance tracking
        self.resolutions_attempted = 0
        self.resolutions_successful = 0
        self.total_resolution_time = 0.0
        
        logger.info("Initialized OptimizationBasedResolver")
    
    def resolve_all_conflicts(self, 
                            strategy: ResolutionStrategy = None,
                            scope: ResolutionScope = None) -> List[ResolutionSolution]:
        """Resolve all conflicts and constraint violations in the system."""
        
        start_time = time.time()
        strategy = strategy or self.default_strategy
        scope = scope or self.default_scope
        
        logger.info(f"Starting conflict resolution with strategy: {strategy.value}, scope: {scope.value}")
        
        # Identify conflicts and violations
        conflict_groups = self._identify_conflict_groups(scope)
        
        if not conflict_groups:
            logger.info("No conflicts found to resolve")
            return []
        
        logger.info(f"Identified {len(conflict_groups)} conflict groups")
        
        # Resolve conflict groups
        solutions = []
        
        for group in conflict_groups:
            group_start_time = time.time()
            self.resolutions_attempted += 1
            
            solution = self._resolve_conflict_group(group, strategy)
            
            if solution:
                solutions.append(solution)
                self.resolutions_successful += 1
                logger.info(f"Resolved conflict group {group.group_id}: "
                           f"{solution.conflicts_resolved} conflicts, "
                           f"{solution.violations_resolved} violations")
            
            group_resolution_time = time.time() - group_start_time
            logger.debug(f"Group resolution time: {group_resolution_time:.2f}s")
        
        # Apply solutions in order of priority
        applied_solutions = []
        
        for solution in sorted(solutions, key=lambda s: s.confidence_score, reverse=True):
            # Test if solution is still valid (conflicts may have been resolved by previous solutions)
            if self._validate_solution(solution):
                success = solution.apply_to_spatial_engine(self.spatial_engine)
                if success:
                    applied_solutions.append(solution)
                    logger.info(f"Applied solution {solution.solution_id}")
                else:
                    logger.warning(f"Failed to apply solution {solution.solution_id}")
        
        total_resolution_time = time.time() - start_time
        self.total_resolution_time += total_resolution_time
        
        logger.info(f"Conflict resolution completed: {len(applied_solutions)} solutions applied in {total_resolution_time:.2f}s")
        
        return applied_solutions
    
    def _identify_conflict_groups(self, scope: ResolutionScope) -> List[ConflictGroup]:
        """Identify groups of related conflicts."""
        
        # Get spatial conflicts
        spatial_conflicts = self.spatial_engine.detect_all_conflicts()
        
        # Get constraint violations 
        import asyncio
        validation_result = asyncio.run(
            self.integrated_validator.validate_comprehensive()
        )
        
        constraint_violations = []
        if hasattr(validation_result, 'constraint_results'):
            for result in validation_result.constraint_results:
                constraint_violations.extend(result.violations)
        
        if not spatial_conflicts and not constraint_violations:
            return []
        
        # Group conflicts by proximity and object involvement
        groups = []
        
        if scope == ResolutionScope.LOCAL:
            # Each conflict gets its own group
            for i, conflict in enumerate(spatial_conflicts):
                group = ConflictGroup(
                    conflicts=[conflict],
                    constraint_violations=[],
                    affected_objects={conflict.get('object1_id', ''), conflict.get('object2_id', '')},
                    group_id=f"spatial_group_{i}",
                    priority=self._calculate_conflict_priority(conflict)
                )
                groups.append(group)
            
            # Group constraint violations
            for i, violation in enumerate(constraint_violations):
                affected_objects = {violation.primary_object_id} if violation.primary_object_id else set()
                affected_objects.update(violation.secondary_object_ids)
                
                group = ConflictGroup(
                    conflicts=[],
                    constraint_violations=[violation],
                    affected_objects=affected_objects,
                    group_id=f"constraint_group_{i}",
                    priority=self._calculate_violation_priority(violation)
                )
                groups.append(group)
        
        elif scope == ResolutionScope.REGIONAL:
            # Group conflicts by spatial regions
            groups = self._group_conflicts_by_region(spatial_conflicts, constraint_violations)
        
        elif scope == ResolutionScope.GLOBAL:
            # Single group with all conflicts
            all_affected_objects = set()
            for conflict in spatial_conflicts:
                all_affected_objects.update({conflict.get('object1_id', ''), conflict.get('object2_id', '')})
            for violation in constraint_violations:
                if violation.primary_object_id:
                    all_affected_objects.add(violation.primary_object_id)
                all_affected_objects.update(violation.secondary_object_ids)
            
            group = ConflictGroup(
                conflicts=spatial_conflicts,
                constraint_violations=constraint_violations,
                affected_objects=all_affected_objects,
                group_id="global_group",
                priority=1
            )
            groups = [group]
        
        # Sort by priority and severity
        groups.sort(key=lambda g: (g.priority, g.calculate_severity_score()), reverse=True)
        
        return groups
    
    def _group_conflicts_by_region(self, 
                                 spatial_conflicts: List[Dict[str, Any]],
                                 constraint_violations: List[ConstraintViolation]) -> List[ConflictGroup]:
        """Group conflicts by spatial regions."""
        
        # Use a simple grid-based grouping
        grid_size = 50.0  # 50ft grid cells
        region_groups = {}
        
        # Group spatial conflicts
        for conflict in spatial_conflicts:
            obj1_id = conflict.get('object1_id')
            obj2_id = conflict.get('object2_id')
            
            # Get object positions
            positions = []
            for obj_id in [obj1_id, obj2_id]:
                if obj_id and obj_id in self.spatial_engine.objects:
                    obj = self.spatial_engine.objects[obj_id]
                    positions.append((obj.geometry.x, obj.geometry.y))
            
            if positions:
                # Calculate average position
                avg_x = sum(pos[0] for pos in positions) / len(positions)
                avg_y = sum(pos[1] for pos in positions) / len(positions)
                
                # Determine grid cell
                grid_x = int(avg_x // grid_size)
                grid_y = int(avg_y // grid_size)
                region_key = (grid_x, grid_y)
                
                if region_key not in region_groups:
                    region_groups[region_key] = ConflictGroup(
                        group_id=f"region_{grid_x}_{grid_y}",
                        priority=1
                    )
                
                region_groups[region_key].conflicts.append(conflict)
                region_groups[region_key].affected_objects.update({obj1_id, obj2_id})
        
        # Group constraint violations similarly
        for violation in constraint_violations:
            if violation.location:
                x, y, _ = violation.location
                grid_x = int(x // grid_size)
                grid_y = int(y // grid_size)
                region_key = (grid_x, grid_y)
                
                if region_key not in region_groups:
                    region_groups[region_key] = ConflictGroup(
                        group_id=f"region_{grid_x}_{grid_y}",
                        priority=1
                    )
                
                region_groups[region_key].constraint_violations.append(violation)
                if violation.primary_object_id:
                    region_groups[region_key].affected_objects.add(violation.primary_object_id)
                region_groups[region_key].affected_objects.update(violation.secondary_object_ids)
        
        return list(region_groups.values())
    
    def _resolve_conflict_group(self, 
                              group: ConflictGroup,
                              strategy: ResolutionStrategy) -> Optional[ResolutionSolution]:
        """Resolve a single conflict group using optimization."""
        
        if not group.affected_objects:
            return None
        
        # Set up optimization problem
        variables = self._create_resolution_variables(group)
        objectives = self._create_resolution_objectives(group, strategy)
        constraints = self._create_resolution_constraints(group)
        
        if not variables or not objectives:
            logger.warning(f"Could not create optimization problem for group {group.group_id}")
            return None
        
        # Create optimization context
        context = OptimizationContext(
            spatial_engine=self.spatial_engine,
            constraint_engine=self.integrated_validator.constraint_engine,
            integrated_validator=self.integrated_validator
        )
        
        # Add problem definition
        for variable in variables:
            context.variables[variable.name] = variable
        for objective in objectives:
            context.objectives[objective.name] = objective
        for constraint in constraints:
            context.constraints[constraint.name] = constraint
        
        # Select and run optimization algorithm
        if len(group.affected_objects) <= 3:
            # Small problem - use simulated annealing
            algorithm = SimulatedAnnealing(self.configuration)
        else:
            # Larger problem - use genetic algorithm
            algorithm = GeneticAlgorithm(self.configuration)
        
        # Run optimization
        try:
            result = algorithm.optimize(context, f"resolve_{group.group_id}")
            
            if result.best_solution and result.is_feasible:
                # Convert optimization result to resolution solution
                resolution_solution = self._convert_to_resolution_solution(
                    result, group, strategy
                )
                return resolution_solution
            else:
                logger.warning(f"No feasible solution found for group {group.group_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error in optimization for group {group.group_id}: {e}")
            return None
    
    def _create_resolution_variables(self, group: ConflictGroup) -> List[OptimizationVariable]:
        """Create optimization variables for conflict resolution."""
        
        variables = []
        
        for obj_id in group.affected_objects:
            if not obj_id or obj_id not in self.spatial_engine.objects:
                continue
            
            obj = self.spatial_engine.objects[obj_id]
            
            # Position variables
            variables.append(OptimizationVariable(
                name=f"{obj_id}_x",
                variable_type=VariableType.CONTINUOUS,
                lower_bound=obj.geometry.x - self.max_displacement_distance,
                upper_bound=obj.geometry.x + self.max_displacement_distance,
                initial_value=obj.geometry.x,
                affects_objects={obj_id},
                affects_property="x",
                description=f"X position for {obj_id}"
            ))
            
            variables.append(OptimizationVariable(
                name=f"{obj_id}_y", 
                variable_type=VariableType.CONTINUOUS,
                lower_bound=obj.geometry.y - self.max_displacement_distance,
                upper_bound=obj.geometry.y + self.max_displacement_distance,
                initial_value=obj.geometry.y,
                affects_objects={obj_id},
                affects_property="y",
                description=f"Y position for {obj_id}"
            ))
            
            # Z position with smaller range (typically constrained by floor/ceiling)
            z_range = min(self.max_displacement_distance, 5.0)
            variables.append(OptimizationVariable(
                name=f"{obj_id}_z",
                variable_type=VariableType.CONTINUOUS,
                lower_bound=obj.geometry.z - z_range,
                upper_bound=obj.geometry.z + z_range,
                initial_value=obj.geometry.z,
                affects_objects={obj_id},
                affects_property="z",
                description=f"Z position for {obj_id}"
            ))
        
        return variables
    
    def _create_resolution_objectives(self, 
                                    group: ConflictGroup,
                                    strategy: ResolutionStrategy) -> List[OptimizationObjective]:
        """Create optimization objectives for conflict resolution."""
        
        objectives = []
        
        if strategy == ResolutionStrategy.MINIMAL_DISPLACEMENT:
            # Minimize total displacement
            def displacement_objective(solution: Dict[str, Any], context: OptimizationContext) -> float:
                total_displacement = 0.0
                
                for obj_id in group.affected_objects:
                    if not obj_id or obj_id not in self.spatial_engine.objects:
                        continue
                    
                    obj = self.spatial_engine.objects[obj_id]
                    original_x = obj.geometry.x
                    original_y = obj.geometry.y
                    original_z = obj.geometry.z
                    
                    new_x = solution.get(f"{obj_id}_x", original_x)
                    new_y = solution.get(f"{obj_id}_y", original_y) 
                    new_z = solution.get(f"{obj_id}_z", original_z)
                    
                    displacement = math.sqrt(
                        (new_x - original_x)**2 + 
                        (new_y - original_y)**2 + 
                        (new_z - original_z)**2
                    )
                    
                    total_displacement += displacement
                
                return total_displacement
            
            objectives.append(OptimizationObjective(
                name="minimize_displacement",
                optimization_type=OptimizationType.MINIMIZE,
                evaluation_function=displacement_objective,
                weight=1.0,
                priority=1,
                description="Minimize total object displacement"
            ))
        
        elif strategy == ResolutionStrategy.COST_MINIMIZATION:
            # Minimize modification cost
            def cost_objective(solution: Dict[str, Any], context: OptimizationContext) -> float:
                total_cost = 0.0
                
                for obj_id in group.affected_objects:
                    if not obj_id or obj_id not in self.spatial_engine.objects:
                        continue
                    
                    obj = self.spatial_engine.objects[obj_id]
                    
                    # Calculate displacement cost
                    original_x = obj.geometry.x
                    original_y = obj.geometry.y
                    original_z = obj.geometry.z
                    
                    new_x = solution.get(f"{obj_id}_x", original_x)
                    new_y = solution.get(f"{obj_id}_y", original_y)
                    new_z = solution.get(f"{obj_id}_z", original_z)
                    
                    displacement = math.sqrt(
                        (new_x - original_x)**2 + 
                        (new_y - original_y)**2 + 
                        (new_z - original_z)**2
                    )
                    
                    # Base cost per object + displacement cost
                    base_cost = self.modification_cost_base
                    displacement_cost = displacement * self.displacement_cost_per_foot
                    
                    # System priority affects cost
                    system_priority = obj.get_system_priority()
                    priority_multiplier = system_priority  # Higher priority = higher cost to move
                    
                    total_cost += (base_cost + displacement_cost) * priority_multiplier
                
                return total_cost
            
            objectives.append(OptimizationObjective(
                name="minimize_cost",
                optimization_type=OptimizationType.MINIMIZE,
                evaluation_function=cost_objective,
                weight=1.0,
                priority=1,
                description="Minimize modification cost"
            ))
        
        # Always include conflict resolution objective
        def conflict_resolution_objective(solution: Dict[str, Any], context: OptimizationContext) -> float:
            # Apply solution temporarily
            original_state = self._save_object_states(group.affected_objects)
            self._apply_solution_temporarily(solution, group.affected_objects)
            
            # Count remaining conflicts
            remaining_conflicts = 0
            
            # Check spatial conflicts
            for conflict in group.conflicts:
                obj1_id = conflict.get('object1_id')
                obj2_id = conflict.get('object2_id')
                
                if obj1_id and obj2_id and obj1_id in self.spatial_engine.objects and obj2_id in self.spatial_engine.objects:
                    obj1 = self.spatial_engine.objects[obj1_id]
                    obj2 = self.spatial_engine.objects[obj2_id]
                    
                    # Check if conflict still exists
                    if self.spatial_engine.check_collision(obj1, obj2):
                        remaining_conflicts += 1
            
            # Check constraint violations
            violations = context.get_constraint_violations()
            remaining_conflicts += len([v for v in violations 
                                      if v.primary_object_id in group.affected_objects])
            
            # Restore original state
            self._restore_object_states(original_state)
            
            return remaining_conflicts
        
        objectives.append(OptimizationObjective(
            name="resolve_conflicts", 
            optimization_type=OptimizationType.MINIMIZE,
            evaluation_function=conflict_resolution_objective,
            weight=10.0,  # High weight for conflict resolution
            priority=1,
            description="Minimize remaining conflicts"
        ))
        
        return objectives
    
    def _create_resolution_constraints(self, group: ConflictGroup) -> List[OptimizationConstraint]:
        """Create optimization constraints for resolution."""
        
        constraints = []
        
        # Spatial bounds constraint
        def spatial_bounds_constraint(solution: Dict[str, Any], context: OptimizationContext) -> float:
            violations = 0
            
            world_bounds = self.spatial_engine.world_bounds
            
            for obj_id in group.affected_objects:
                if not obj_id:
                    continue
                
                x = solution.get(f"{obj_id}_x", 0)
                y = solution.get(f"{obj_id}_y", 0) 
                z = solution.get(f"{obj_id}_z", 0)
                
                # Check if within world bounds
                if not world_bounds.contains_point(x, y, z):
                    violations += 1
            
            return violations
        
        constraints.append(OptimizationConstraint(
            name="spatial_bounds",
            constraint_function=spatial_bounds_constraint,
            constraint_type="inequality",
            upper_bound=0,  # No violations allowed
            description="Objects must remain within spatial bounds"
        ))
        
        return constraints
    
    def _save_object_states(self, object_ids: Set[str]) -> Dict[str, Dict[str, Any]]:
        """Save current state of objects."""
        
        states = {}
        
        for obj_id in object_ids:
            if obj_id and obj_id in self.spatial_engine.objects:
                obj = self.spatial_engine.objects[obj_id]
                states[obj_id] = {
                    'geometry': copy.deepcopy(obj.geometry),
                    'metadata': copy.deepcopy(obj.metadata) if obj.metadata else None
                }
        
        return states
    
    def _restore_object_states(self, states: Dict[str, Dict[str, Any]]) -> None:
        """Restore object states."""
        
        for obj_id, state in states.items():
            if obj_id in self.spatial_engine.objects:
                obj = self.spatial_engine.objects[obj_id]
                obj.geometry = copy.deepcopy(state['geometry'])
                if state['metadata']:
                    obj.metadata = copy.deepcopy(state['metadata'])
    
    def _apply_solution_temporarily(self, solution: Dict[str, Any], object_ids: Set[str]) -> None:
        """Apply solution temporarily for evaluation."""
        
        for obj_id in object_ids:
            if not obj_id or obj_id not in self.spatial_engine.objects:
                continue
            
            obj = self.spatial_engine.objects[obj_id]
            
            # Update positions
            if f"{obj_id}_x" in solution:
                obj.geometry.x = solution[f"{obj_id}_x"]
            if f"{obj_id}_y" in solution:
                obj.geometry.y = solution[f"{obj_id}_y"]
            if f"{obj_id}_z" in solution:
                obj.geometry.z = solution[f"{obj_id}_z"]
    
    def _convert_to_resolution_solution(self, 
                                      optimization_result: OptimizationResult,
                                      group: ConflictGroup,
                                      strategy: ResolutionStrategy) -> ResolutionSolution:
        """Convert optimization result to resolution solution."""
        
        solution = ResolutionSolution(
            solution_id=f"resolution_{group.group_id}_{int(time.time())}",
            generation_method=f"optimization_{strategy.value}",
            confidence_score=1.0 - optimization_result.best_objective_values.get('resolve_conflicts', 0) / max(1, len(group.conflicts) + len(group.constraint_violations))
        )
        
        # Extract object position changes
        for obj_id in group.affected_objects:
            if not obj_id or obj_id not in self.spatial_engine.objects:
                continue
            
            original_obj = self.spatial_engine.objects[obj_id]
            
            new_x = optimization_result.best_solution.get(f"{obj_id}_x", original_obj.geometry.x)
            new_y = optimization_result.best_solution.get(f"{obj_id}_y", original_obj.geometry.y) 
            new_z = optimization_result.best_solution.get(f"{obj_id}_z", original_obj.geometry.z)
            
            # Only record if position actually changed
            if (abs(new_x - original_obj.geometry.x) > 0.01 or
                abs(new_y - original_obj.geometry.y) > 0.01 or
                abs(new_z - original_obj.geometry.z) > 0.01):
                
                solution.object_positions[obj_id] = (new_x, new_y, new_z)
                
                # Calculate displacement cost
                displacement = math.sqrt(
                    (new_x - original_obj.geometry.x)**2 +
                    (new_y - original_obj.geometry.y)**2 + 
                    (new_z - original_obj.geometry.z)**2
                )
                solution.displacement_cost += displacement * self.displacement_cost_per_foot
        
        # Set resolution metrics
        solution.conflicts_resolved = len(group.conflicts)
        solution.violations_resolved = len(group.constraint_violations)
        solution.modification_cost = len(solution.object_positions) * self.modification_cost_base
        
        return solution
    
    def _validate_solution(self, solution: ResolutionSolution) -> bool:
        """Validate that solution is still applicable."""
        
        # Check if objects still exist
        for obj_id in solution.object_positions.keys():
            if obj_id not in self.spatial_engine.objects:
                return False
        
        # Check if solution still resolves conflicts
        # (Simplified validation - could be more comprehensive)
        return True
    
    def _calculate_conflict_priority(self, conflict: Dict[str, Any]) -> int:
        """Calculate priority for conflict resolution."""
        
        conflict_type = conflict.get('type', 'collision')
        severity = conflict.get('severity', 'medium')
        
        # Base priority by type
        type_priorities = {
            'collision': 1,
            'clearance': 2,
            'code_violation': 1,
            'access': 3
        }
        
        # Severity multiplier
        severity_multipliers = {
            'critical': 1,
            'high': 2,
            'medium': 3,
            'low': 4
        }
        
        base_priority = type_priorities.get(conflict_type, 3)
        severity_multiplier = severity_multipliers.get(severity, 3)
        
        return base_priority * severity_multiplier
    
    def _calculate_violation_priority(self, violation: ConstraintViolation) -> int:
        """Calculate priority for constraint violation resolution."""
        
        severity_priorities = {
            ConstraintSeverity.CRITICAL: 1,
            ConstraintSeverity.ERROR: 2,
            ConstraintSeverity.WARNING: 3,
            ConstraintSeverity.INFO: 4,
            ConstraintSeverity.SUGGESTION: 5
        }
        
        return severity_priorities.get(violation.severity, 3)
    
    def get_resolution_statistics(self) -> Dict[str, Any]:
        """Get conflict resolution statistics."""
        
        success_rate = (self.resolutions_successful / max(1, self.resolutions_attempted)) * 100
        
        return {
            'resolutions_attempted': self.resolutions_attempted,
            'resolutions_successful': self.resolutions_successful,
            'success_rate_percent': success_rate,
            'total_resolution_time': self.total_resolution_time,
            'average_resolution_time': self.total_resolution_time / max(1, self.resolutions_attempted)
        }


logger.info("Optimization-aware conflict resolution system initialized")