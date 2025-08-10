"""
High-Performance Optimization Engine.

Coordinates optimization algorithms with Phase 1 spatial indexing and Phase 2
constraint validation for Building-Infrastructure-as-Code optimization.
"""

import asyncio
import time
import logging
import threading
import copy
from typing import Dict, Any, List, Optional, Set, Union, Callable, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing

# Import Phase 1 and 2 foundation
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.spatial import SpatialConflictEngine, ArxObject, ArxObjectType, BoundingBox3D
from core.constraints import (
    ConstraintEngine, ConstraintResult, ConstraintViolation, 
    IntegratedValidator, ConstraintEvaluationContext
)

from .optimization_core import (
    OptimizationObjective, OptimizationVariable, OptimizationConstraint,
    OptimizationResult, OptimizationConfiguration, OptimizationMetrics,
    OptimizationType, OptimizationStatus, VariableType
)

logger = logging.getLogger(__name__)


@dataclass
class OptimizationContext:
    """
    Optimization execution context.
    
    Provides optimization algorithms with access to spatial engine,
    constraint validation, and solution manipulation capabilities.
    """
    
    # Core engines
    spatial_engine: SpatialConflictEngine
    constraint_engine: ConstraintEngine
    integrated_validator: Optional[IntegratedValidator] = None
    
    # Optimization problem definition
    variables: Dict[str, OptimizationVariable] = field(default_factory=dict)
    objectives: Dict[str, OptimizationObjective] = field(default_factory=dict)
    constraints: Dict[str, OptimizationConstraint] = field(default_factory=dict)
    
    # Current state
    current_solution: Dict[str, Any] = field(default_factory=dict)
    original_state: Dict[str, Any] = field(default_factory=dict)
    
    # Performance tracking
    solution_cache: Dict[str, Tuple[Dict[str, float], List[ConstraintViolation]]] = field(default_factory=dict)
    evaluation_count: int = 0
    
    def __post_init__(self):
        """Initialize optimization context."""
        if not self.integrated_validator:
            self.integrated_validator = IntegratedValidator(
                self.spatial_engine, "Optimization Context"
            )
        
        # Save original state
        self.save_original_state()
    
    def save_original_state(self) -> None:
        """Save original object positions and properties."""
        self.original_state = {}
        
        for obj_id, obj in self.spatial_engine.objects.items():
            self.original_state[obj_id] = {
                'geometry': copy.deepcopy(obj.geometry),
                'metadata': copy.deepcopy(obj.metadata) if obj.metadata else None
            }
    
    def restore_original_state(self) -> None:
        """Restore objects to original state."""
        for obj_id, original_data in self.original_state.items():
            if obj_id in self.spatial_engine.objects:
                obj = self.spatial_engine.objects[obj_id]
                obj.geometry = copy.deepcopy(original_data['geometry'])
                if original_data['metadata']:
                    obj.metadata = copy.deepcopy(original_data['metadata'])
    
    def apply_solution(self, solution: Dict[str, Any]) -> bool:
        """
        Apply optimization solution to spatial engine.
        
        Args:
            solution: Variable values to apply
            
        Returns:
            True if solution was applied successfully
        """
        try:
            for var_name, value in solution.items():
                if var_name not in self.variables:
                    continue
                
                variable = self.variables[var_name]
                
                # Apply variable to affected objects
                for obj_id in variable.affects_objects:
                    if obj_id not in self.spatial_engine.objects:
                        continue
                    
                    obj = self.spatial_engine.objects[obj_id]
                    property_name = variable.affects_property
                    
                    # Apply to geometry properties
                    if hasattr(obj.geometry, property_name):
                        setattr(obj.geometry, property_name, value)
                    
                    # Apply to metadata properties
                    elif obj.metadata and hasattr(obj.metadata, property_name):
                        setattr(obj.metadata, property_name, value)
            
            # Update current solution
            self.current_solution = solution.copy()
            
            # Update spatial indices (objects may have moved)
            self._update_spatial_indices()
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying solution: {e}")
            return False
    
    def _update_spatial_indices(self) -> None:
        """Update spatial indices after object modifications."""
        # Remove and re-add all objects to spatial indices
        # This is simplified - could be optimized to only update modified objects
        objects_to_update = list(self.spatial_engine.objects.values())
        
        for obj in objects_to_update:
            try:
                self.spatial_engine.octree.remove(obj)
                self.spatial_engine.rtree.remove(obj)
            except:
                pass  # Object may not be in index
            
            self.spatial_engine.octree.insert(obj)
            self.spatial_engine.rtree.insert(obj)
    
    def evaluate_solution(self, solution: Dict[str, Any]) -> Tuple[Dict[str, float], List[ConstraintViolation], bool]:
        """
        Evaluate complete solution.
        
        Returns:
            Tuple of (objective_values, constraint_violations, is_feasible)
        """
        # Check cache first
        solution_key = str(sorted(solution.items()))
        if solution_key in self.solution_cache:
            return self.solution_cache[solution_key]
        
        self.evaluation_count += 1
        
        # Apply solution
        success = self.apply_solution(solution)
        if not success:
            return {}, [], False
        
        # Evaluate objectives
        objective_values = {}
        for obj_name, objective in self.objectives.items():
            value = objective.evaluate(solution, self)
            objective_values[obj_name] = value
        
        # Get constraint violations
        constraint_violations = self.get_constraint_violations()
        
        # Check optimization constraints
        is_feasible = True
        for constraint_name, constraint in self.constraints.items():
            satisfied, _ = constraint.evaluate(solution, self)
            if not satisfied:
                is_feasible = False
        
        # Cache result
        result = (objective_values, constraint_violations, is_feasible)
        self.solution_cache[solution_key] = result
        
        return result
    
    def get_constraint_violations(self) -> List[ConstraintViolation]:
        """Get all constraint violations for current state."""
        try:
            # Run comprehensive validation
            validation_result = asyncio.run(
                self.integrated_validator.validate_comprehensive()
            )
            
            # Extract violations from constraint results
            violations = []
            if hasattr(validation_result, 'constraint_results'):
                for result in validation_result.constraint_results:
                    violations.extend(result.violations)
            
            return violations
            
        except Exception as e:
            logger.error(f"Error getting constraint violations: {e}")
            return []
    
    def generate_random_solution(self) -> Dict[str, Any]:
        """Generate random feasible solution."""
        import random
        
        solution = {}
        
        for var_name, variable in self.variables.items():
            if variable.variable_type == VariableType.CONTINUOUS:
                value = random.uniform(variable.lower_bound, variable.upper_bound)
            elif variable.variable_type == VariableType.INTEGER:
                value = random.randint(variable.lower_bound, variable.upper_bound)
            elif variable.variable_type == VariableType.BINARY:
                value = random.choice([0, 1])
            elif variable.variable_type == VariableType.CATEGORICAL:
                value = random.choice(variable.categories)
            else:
                # Position, orientation, size variables
                if variable.lower_bound is not None and variable.upper_bound is not None:
                    value = random.uniform(variable.lower_bound, variable.upper_bound)
                else:
                    value = variable.initial_value or 0.0
            
            solution[var_name] = value
        
        return solution
    
    def get_solution_bounds(self) -> Tuple[List[float], List[float]]:
        """Get lower and upper bounds for all variables."""
        lower_bounds = []
        upper_bounds = []
        
        for variable in self.variables.values():
            if variable.variable_type in [VariableType.CONTINUOUS, VariableType.INTEGER]:
                lower_bounds.append(variable.lower_bound)
                upper_bounds.append(variable.upper_bound)
            elif variable.variable_type == VariableType.BINARY:
                lower_bounds.append(0)
                upper_bounds.append(1)
            else:
                # Categorical variables - use indices
                lower_bounds.append(0)
                upper_bounds.append(len(variable.categories) - 1 if variable.categories else 1)
        
        return lower_bounds, upper_bounds


class OptimizationEngine:
    """
    High-performance optimization engine.
    
    Coordinates optimization algorithms with spatial indexing and constraint
    validation for automated Building-Infrastructure-as-Code optimization.
    """
    
    def __init__(self, 
                 spatial_engine: SpatialConflictEngine,
                 constraint_engine: ConstraintEngine,
                 configuration: Optional[OptimizationConfiguration] = None):
        """
        Initialize optimization engine.
        
        Args:
            spatial_engine: Phase 1 spatial conflict engine
            constraint_engine: Phase 2 constraint engine
            configuration: Optimization settings
        """
        self.spatial_engine = spatial_engine
        self.constraint_engine = constraint_engine
        self.configuration = configuration or OptimizationConfiguration()
        
        # Create integrated validator
        self.integrated_validator = IntegratedValidator(
            spatial_engine, "Optimization Engine"
        )
        
        # Optimization state
        self.contexts: Dict[str, OptimizationContext] = {}
        self.active_optimizations: Dict[str, threading.Thread] = {}
        self.optimization_results: Dict[str, OptimizationResult] = {}
        
        # Performance tracking
        self.metrics = OptimizationMetrics()
        self.total_optimizations_run: int = 0
        
        # Resource management
        self.thread_pool = ThreadPoolExecutor(max_workers=self.configuration.max_workers)
        self.process_pool = None
        if self.configuration.parallel_processing:
            cpu_count = multiprocessing.cpu_count()
            self.process_pool = ProcessPoolExecutor(max_workers=min(cpu_count, 4))
        
        logger.info(f"Initialized OptimizationEngine with {self.configuration.max_workers} workers")
    
    def create_optimization_problem(self,
                                  variables: List[OptimizationVariable],
                                  objectives: List[OptimizationObjective],
                                  constraints: Optional[List[OptimizationConstraint]] = None) -> str:
        """
        Create optimization problem.
        
        Args:
            variables: Optimization variables
            objectives: Optimization objectives
            constraints: Optimization constraints (optional)
            
        Returns:
            Optimization problem ID
        """
        problem_id = f"optimization_{int(time.time())}_{len(self.contexts)}"
        
        # Create optimization context
        context = OptimizationContext(
            spatial_engine=self.spatial_engine,
            constraint_engine=self.constraint_engine,
            integrated_validator=self.integrated_validator
        )
        
        # Add variables
        for variable in variables:
            context.variables[variable.name] = variable
        
        # Add objectives
        for objective in objectives:
            context.objectives[objective.name] = objective
        
        # Add constraints
        if constraints:
            for constraint in constraints:
                context.constraints[constraint.name] = constraint
        
        self.contexts[problem_id] = context
        
        logger.info(f"Created optimization problem {problem_id} with {len(variables)} variables, "
                   f"{len(objectives)} objectives, {len(constraints or [])} constraints")
        
        return problem_id
    
    def optimize(self, 
                problem_id: str,
                algorithm: str = None) -> OptimizationResult:
        """
        Run optimization for problem.
        
        Args:
            problem_id: Optimization problem ID
            algorithm: Algorithm to use (None for auto-select)
            
        Returns:
            OptimizationResult with solution
        """
        if problem_id not in self.contexts:
            raise ValueError(f"Unknown optimization problem: {problem_id}")
        
        context = self.contexts[problem_id]
        algorithm = algorithm or self.configuration.algorithm
        
        # Select and run optimization algorithm
        if algorithm == "genetic_algorithm":
            result = self._run_genetic_algorithm(context, problem_id)
        elif algorithm == "simulated_annealing":
            result = self._run_simulated_annealing(context, problem_id)
        elif algorithm == "particle_swarm":
            result = self._run_particle_swarm(context, problem_id)
        elif algorithm == "gradient_descent":
            result = self._run_gradient_descent(context, problem_id)
        else:
            # Default to genetic algorithm
            result = self._run_genetic_algorithm(context, problem_id)
        
        # Store result
        self.optimization_results[problem_id] = result
        self.total_optimizations_run += 1
        
        # Update metrics
        self.metrics.update_from_result(result)
        
        logger.info(f"Optimization {problem_id} completed: {result.optimization_status.value}, "
                   f"{result.iteration_count} iterations, {result.optimization_time:.2f}s")
        
        return result
    
    def _run_genetic_algorithm(self, 
                              context: OptimizationContext,
                              problem_id: str) -> OptimizationResult:
        """Run genetic algorithm optimization."""
        start_time = time.time()
        
        result = OptimizationResult(
            optimization_id=problem_id,
            algorithm_used="genetic_algorithm",
            optimization_status=OptimizationStatus.RUNNING
        )
        
        # Initialize population
        population_size = self.configuration.population_size
        population = []
        
        for _ in range(population_size):
            individual = context.generate_random_solution()
            population.append(individual)
        
        best_solution = None
        best_fitness = float('inf')
        stagnation_counter = 0
        
        # Evolution loop
        for iteration in range(self.configuration.max_iterations):
            # Evaluate population
            fitness_scores = []
            
            for individual in population:
                objectives, violations, is_feasible = context.evaluate_solution(individual)
                
                # Calculate fitness (minimize)
                if objectives:
                    fitness = sum(objectives.values())  # Simple sum for multi-objective
                    if not is_feasible:
                        fitness += 1000.0 * len(violations)  # Penalty for infeasibility
                else:
                    fitness = float('inf')
                
                fitness_scores.append(fitness)
                
                # Update best solution
                if fitness < best_fitness:
                    best_fitness = fitness
                    best_solution = individual.copy()
                    stagnation_counter = 0
                else:
                    stagnation_counter += 1
            
            # Update result
            if best_solution:
                objectives, violations, is_feasible = context.evaluate_solution(best_solution)
                result.add_iteration_result(
                    iteration,
                    objectives,
                    [v.description for v in violations]
                )
                result.best_solution = best_solution.copy()
                result.is_feasible = is_feasible
            
            # Check stopping criteria
            if stagnation_counter >= self.configuration.stagnation_limit:
                result.optimization_status = OptimizationStatus.CONVERGED
                break
            
            if time.time() - start_time > self.configuration.max_time_seconds:
                result.optimization_status = OptimizationStatus.MAX_TIME
                break
            
            # Generate new population
            population = self._evolve_population(population, fitness_scores, context)
        
        # Finalize result
        result.optimization_time = time.time() - start_time
        result.evaluation_count = context.evaluation_count
        
        if result.optimization_status == OptimizationStatus.RUNNING:
            result.optimization_status = OptimizationStatus.MAX_ITERATIONS
        
        return result
    
    def _evolve_population(self, 
                          population: List[Dict[str, Any]], 
                          fitness_scores: List[float],
                          context: OptimizationContext) -> List[Dict[str, Any]]:
        """Evolve population using genetic operators."""
        import random
        
        # Selection (tournament selection)
        new_population = []
        elite_size = self.configuration.elite_size
        
        # Keep elite solutions
        elite_indices = sorted(range(len(fitness_scores)), key=lambda i: fitness_scores[i])[:elite_size]
        for i in elite_indices:
            new_population.append(population[i].copy())
        
        # Generate offspring
        while len(new_population) < len(population):
            # Parent selection
            parent1 = self._tournament_selection(population, fitness_scores)
            parent2 = self._tournament_selection(population, fitness_scores)
            
            # Crossover
            if random.random() < self.configuration.crossover_rate:
                child1, child2 = self._crossover(parent1, parent2, context)
            else:
                child1, child2 = parent1.copy(), parent2.copy()
            
            # Mutation
            if random.random() < self.configuration.mutation_rate:
                child1 = self._mutate(child1, context)
            if random.random() < self.configuration.mutation_rate:
                child2 = self._mutate(child2, context)
            
            new_population.extend([child1, child2])
        
        return new_population[:len(population)]
    
    def _tournament_selection(self, 
                            population: List[Dict[str, Any]], 
                            fitness_scores: List[float],
                            tournament_size: int = 3) -> Dict[str, Any]:
        """Tournament selection for genetic algorithm."""
        import random
        
        tournament_indices = random.sample(range(len(population)), 
                                         min(tournament_size, len(population)))
        best_index = min(tournament_indices, key=lambda i: fitness_scores[i])
        return population[best_index].copy()
    
    def _crossover(self, 
                  parent1: Dict[str, Any], 
                  parent2: Dict[str, Any],
                  context: OptimizationContext) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Crossover operation for genetic algorithm."""
        import random
        
        child1 = parent1.copy()
        child2 = parent2.copy()
        
        # Uniform crossover
        for var_name in context.variables:
            if random.random() < 0.5:
                child1[var_name], child2[var_name] = parent2[var_name], parent1[var_name]
        
        return child1, child2
    
    def _mutate(self, 
               individual: Dict[str, Any],
               context: OptimizationContext) -> Dict[str, Any]:
        """Mutation operation for genetic algorithm."""
        import random
        
        mutated = individual.copy()
        
        for var_name, variable in context.variables.items():
            if random.random() < 0.1:  # 10% chance to mutate each variable
                
                if variable.variable_type == VariableType.CONTINUOUS:
                    # Gaussian mutation
                    current_value = mutated[var_name]
                    mutation_range = (variable.upper_bound - variable.lower_bound) * 0.1
                    mutated_value = current_value + random.gauss(0, mutation_range)
                    mutated[var_name] = variable.clip_value(mutated_value)
                
                elif variable.variable_type == VariableType.INTEGER:
                    mutated[var_name] = random.randint(variable.lower_bound, variable.upper_bound)
                
                elif variable.variable_type == VariableType.BINARY:
                    mutated[var_name] = 1 - mutated[var_name]  # Flip bit
                
                elif variable.variable_type == VariableType.CATEGORICAL:
                    mutated[var_name] = random.choice(variable.categories)
        
        return mutated
    
    def _run_simulated_annealing(self, 
                               context: OptimizationContext,
                               problem_id: str) -> OptimizationResult:
        """Run simulated annealing optimization."""
        import random
        import math
        
        start_time = time.time()
        
        result = OptimizationResult(
            optimization_id=problem_id,
            algorithm_used="simulated_annealing",
            optimization_status=OptimizationStatus.RUNNING
        )
        
        # Initialize with random solution
        current_solution = context.generate_random_solution()
        current_objectives, current_violations, current_feasible = context.evaluate_solution(current_solution)
        current_fitness = sum(current_objectives.values()) if current_objectives else float('inf')
        
        best_solution = current_solution.copy()
        best_fitness = current_fitness
        
        # Annealing schedule
        initial_temp = 1000.0
        final_temp = 0.01
        cooling_rate = 0.95
        
        temperature = initial_temp
        
        for iteration in range(self.configuration.max_iterations):
            # Generate neighbor solution
            neighbor = self._generate_neighbor(current_solution, context)
            neighbor_objectives, neighbor_violations, neighbor_feasible = context.evaluate_solution(neighbor)
            neighbor_fitness = sum(neighbor_objectives.values()) if neighbor_objectives else float('inf')
            
            # Accept or reject
            if neighbor_fitness < current_fitness:
                # Better solution - always accept
                current_solution = neighbor
                current_fitness = neighbor_fitness
                current_objectives = neighbor_objectives
                current_violations = neighbor_violations
                
                if neighbor_fitness < best_fitness:
                    best_solution = neighbor.copy()
                    best_fitness = neighbor_fitness
            
            else:
                # Worse solution - accept with probability based on temperature
                delta = neighbor_fitness - current_fitness
                probability = math.exp(-delta / temperature) if temperature > 0 else 0
                
                if random.random() < probability:
                    current_solution = neighbor
                    current_fitness = neighbor_fitness
                    current_objectives = neighbor_objectives
                    current_violations = neighbor_violations
            
            # Update result
            result.add_iteration_result(
                iteration,
                current_objectives,
                [v.description for v in current_violations]
            )
            
            # Cool down
            temperature *= cooling_rate
            
            # Check stopping criteria
            if temperature < final_temp:
                result.optimization_status = OptimizationStatus.CONVERGED
                break
            
            if time.time() - start_time > self.configuration.max_time_seconds:
                result.optimization_status = OptimizationStatus.MAX_TIME
                break
        
        # Finalize result
        result.best_solution = best_solution
        result.optimization_time = time.time() - start_time
        result.evaluation_count = context.evaluation_count
        
        if result.optimization_status == OptimizationStatus.RUNNING:
            result.optimization_status = OptimizationStatus.MAX_ITERATIONS
        
        return result
    
    def _generate_neighbor(self, 
                          solution: Dict[str, Any],
                          context: OptimizationContext) -> Dict[str, Any]:
        """Generate neighbor solution for simulated annealing."""
        import random
        
        neighbor = solution.copy()
        
        # Modify one random variable
        var_name = random.choice(list(context.variables.keys()))
        variable = context.variables[var_name]
        
        if variable.variable_type == VariableType.CONTINUOUS:
            current_value = neighbor[var_name]
            step_size = (variable.upper_bound - variable.lower_bound) * 0.05  # 5% of range
            neighbor[var_name] = variable.clip_value(
                current_value + random.uniform(-step_size, step_size)
            )
        
        elif variable.variable_type == VariableType.INTEGER:
            neighbor[var_name] = random.randint(variable.lower_bound, variable.upper_bound)
        
        elif variable.variable_type == VariableType.BINARY:
            neighbor[var_name] = 1 - neighbor[var_name]
        
        elif variable.variable_type == VariableType.CATEGORICAL:
            neighbor[var_name] = random.choice(variable.categories)
        
        return neighbor
    
    def _run_particle_swarm(self, context: OptimizationContext, problem_id: str) -> OptimizationResult:
        """Run particle swarm optimization (placeholder)."""
        # Simplified implementation - would implement full PSO algorithm
        return self._run_genetic_algorithm(context, problem_id)
    
    def _run_gradient_descent(self, context: OptimizationContext, problem_id: str) -> OptimizationResult:
        """Run gradient descent optimization (placeholder)."""
        # Simplified implementation - would implement gradient-based optimization
        return self._run_simulated_annealing(context, problem_id)
    
    def get_optimization_status(self, problem_id: str) -> OptimizationMetrics:
        """Get real-time optimization status."""
        if problem_id in self.optimization_results:
            result = self.optimization_results[problem_id]
            metrics = OptimizationMetrics()
            metrics.update_from_result(result)
            return metrics
        
        return self.metrics
    
    def stop_optimization(self, problem_id: str) -> bool:
        """Stop running optimization."""
        if problem_id in self.active_optimizations:
            # Implementation would signal thread to stop
            logger.info(f"Stopping optimization {problem_id}")
            return True
        return False
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        logger.info("Shutting down OptimizationEngine...")
        
        self.thread_pool.shutdown(wait=True)
        if self.process_pool:
            self.process_pool.shutdown(wait=True)
        
        logger.info("OptimizationEngine shutdown complete")


logger.info("Optimization engine initialized")