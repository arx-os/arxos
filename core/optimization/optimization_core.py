"""
Core Optimization Architecture.

Foundational classes and types for the Arxos optimization engine including
objectives, variables, constraints, and result structures.
"""

import time
import logging
import numpy as np
from typing import Dict, Any, List, Optional, Set, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import uuid

# Import Phase 1 and 2 foundation
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.spatial import ArxObject, ArxObjectType, BoundingBox3D
from core.constraints import ConstraintResult, ConstraintViolation, ConstraintSeverity

logger = logging.getLogger(__name__)


class OptimizationType(Enum):
    """Types of optimization problems."""
    
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"
    MULTI_OBJECTIVE = "multi_objective"
    CONSTRAINT_SATISFACTION = "constraint_satisfaction"
    PARETO_OPTIMIZATION = "pareto_optimization"


class OptimizationStatus(Enum):
    """Optimization execution status."""
    
    PENDING = "pending"
    RUNNING = "running"
    CONVERGED = "converged"
    MAX_ITERATIONS = "max_iterations"
    MAX_TIME = "max_time"
    USER_STOPPED = "user_stopped"
    ERROR = "error"
    INFEASIBLE = "infeasible"


class VariableType(Enum):
    """Types of optimization variables."""
    
    CONTINUOUS = "continuous"
    INTEGER = "integer"
    BINARY = "binary"
    CATEGORICAL = "categorical"
    POSITION = "position"
    ORIENTATION = "orientation"
    SIZE = "size"


@dataclass
class OptimizationVariable:
    """
    Optimization variable definition.
    
    Represents a parameter that can be optimized including bounds,
    constraints, and type information.
    """
    
    name: str
    variable_type: VariableType
    lower_bound: Optional[Union[float, int]] = None
    upper_bound: Optional[Union[float, int]] = None
    initial_value: Optional[Union[float, int, str]] = None
    
    # For categorical variables
    categories: Optional[List[str]] = None
    
    # Variable metadata
    description: str = ""
    units: str = ""
    precision: float = 1e-6
    
    # Relationship to ArxObjects
    affects_objects: Set[str] = field(default_factory=set)  # Object IDs
    affects_property: str = ""  # Property name (e.g., "x", "y", "length")
    
    def __post_init__(self):
        """Validate variable definition."""
        if self.variable_type == VariableType.CATEGORICAL:
            if not self.categories:
                raise ValueError(f"Categorical variable {self.name} must have categories")
        elif self.variable_type in [VariableType.CONTINUOUS, VariableType.INTEGER]:
            if self.lower_bound is None or self.upper_bound is None:
                raise ValueError(f"Variable {self.name} must have lower and upper bounds")
            if self.lower_bound >= self.upper_bound:
                raise ValueError(f"Variable {self.name} lower bound must be less than upper bound")
    
    def is_valid_value(self, value: Union[float, int, str]) -> bool:
        """Check if value is valid for this variable."""
        if self.variable_type == VariableType.CATEGORICAL:
            return value in self.categories
        elif self.variable_type == VariableType.BINARY:
            return value in [0, 1, True, False]
        elif self.variable_type == VariableType.INTEGER:
            return (isinstance(value, int) and 
                   self.lower_bound <= value <= self.upper_bound)
        elif self.variable_type == VariableType.CONTINUOUS:
            return (isinstance(value, (int, float)) and 
                   self.lower_bound <= value <= self.upper_bound)
        return True
    
    def clip_value(self, value: Union[float, int, str]) -> Union[float, int, str]:
        """Clip value to variable bounds."""
        if self.variable_type == VariableType.CATEGORICAL:
            return value if value in self.categories else self.categories[0]
        elif self.variable_type == VariableType.BINARY:
            return 1 if value else 0
        elif self.variable_type in [VariableType.INTEGER, VariableType.CONTINUOUS]:
            return max(self.lower_bound, min(self.upper_bound, value))
        return value


@dataclass
class OptimizationObjective:
    """
    Optimization objective function definition.
    
    Defines what to optimize (minimize/maximize) including the evaluation
    function and weighting for multi-objective problems.
    """
    
    name: str
    optimization_type: OptimizationType
    weight: float = 1.0
    priority: int = 1  # 1 = highest priority
    
    # Objective function
    evaluation_function: Optional[Callable] = None
    
    # Objective metadata
    description: str = ""
    units: str = ""
    target_value: Optional[float] = None
    acceptable_range: Optional[Tuple[float, float]] = None
    
    # Performance tracking
    best_value: Optional[float] = None
    worst_value: Optional[float] = None
    evaluation_count: int = 0
    total_evaluation_time: float = 0.0
    
    def evaluate(self, 
                solution: Dict[str, Any],
                context: 'OptimizationContext') -> float:
        """
        Evaluate objective function for given solution.
        
        Args:
            solution: Variable values for solution
            context: Optimization context with spatial engine and constraints
            
        Returns:
            Objective function value
        """
        start_time = time.time()
        
        try:
            if self.evaluation_function:
                value = self.evaluation_function(solution, context)
            else:
                # Default evaluation based on objective type
                value = self._default_evaluation(solution, context)
            
            # Update performance tracking
            self.evaluation_count += 1
            self.total_evaluation_time += (time.time() - start_time)
            
            if self.best_value is None:
                self.best_value = value
                self.worst_value = value
            else:
                if self.optimization_type == OptimizationType.MINIMIZE:
                    self.best_value = min(self.best_value, value)
                    self.worst_value = max(self.worst_value, value)
                else:
                    self.best_value = max(self.best_value, value)
                    self.worst_value = min(self.worst_value, value)
            
            return value
            
        except Exception as e:
            logger.error(f"Error evaluating objective {self.name}: {e}")
            return float('inf') if self.optimization_type == OptimizationType.MINIMIZE else float('-inf')
    
    def _default_evaluation(self, 
                          solution: Dict[str, Any],
                          context: 'OptimizationContext') -> float:
        """Default objective evaluation for common cases."""
        
        # Conflict minimization objective
        if "conflict" in self.name.lower():
            return self._evaluate_conflicts(solution, context)
        
        # Constraint violation minimization
        elif "constraint" in self.name.lower() or "violation" in self.name.lower():
            return self._evaluate_constraint_violations(solution, context)
        
        # Cost optimization
        elif "cost" in self.name.lower():
            return self._evaluate_cost(solution, context)
        
        # Performance optimization
        elif "performance" in self.name.lower() or "efficiency" in self.name.lower():
            return self._evaluate_performance(solution, context)
        
        else:
            logger.warning(f"No evaluation function provided for objective {self.name}")
            return 0.0
    
    def _evaluate_conflicts(self, 
                          solution: Dict[str, Any],
                          context: 'OptimizationContext') -> float:
        """Evaluate spatial conflicts for solution."""
        # Apply solution to spatial engine
        context.apply_solution(solution)
        
        # Get conflicts
        conflicts = context.spatial_engine.detect_all_conflicts()
        
        # Return conflict count or severity-weighted sum
        if conflicts:
            severity_weights = {'low': 1, 'medium': 3, 'high': 5, 'critical': 10}
            return sum(severity_weights.get(conflict.get('severity', 'medium'), 3) 
                      for conflict in conflicts)
        return 0.0
    
    def _evaluate_constraint_violations(self, 
                                      solution: Dict[str, Any],
                                      context: 'OptimizationContext') -> float:
        """Evaluate constraint violations for solution."""
        # Apply solution
        context.apply_solution(solution)
        
        # Get constraint violations
        violations = context.get_constraint_violations()
        
        # Weight by severity
        severity_weights = {
            ConstraintSeverity.CRITICAL: 100,
            ConstraintSeverity.ERROR: 10,
            ConstraintSeverity.WARNING: 3,
            ConstraintSeverity.INFO: 1,
            ConstraintSeverity.SUGGESTION: 0.5
        }
        
        return sum(severity_weights.get(violation.severity, 3) for violation in violations)
    
    def _evaluate_cost(self, 
                      solution: Dict[str, Any],
                      context: 'OptimizationContext') -> float:
        """Evaluate cost for solution."""
        total_cost = 0.0
        
        # Material costs
        for obj in context.spatial_engine.objects.values():
            if hasattr(obj, 'metadata') and obj.metadata:
                material_cost = getattr(obj.metadata, 'material_cost', 0.0)
                installation_cost = getattr(obj.metadata, 'installation_cost', 0.0)
                total_cost += material_cost + installation_cost
        
        # Penalty for constraint violations (hidden costs)
        violations = context.get_constraint_violations()
        violation_penalty = len(violations) * 1000.0  # $1000 per violation
        
        return total_cost + violation_penalty
    
    def _evaluate_performance(self, 
                            solution: Dict[str, Any],
                            context: 'OptimizationContext') -> float:
        """Evaluate system performance for solution."""
        # Apply solution
        context.apply_solution(solution)
        
        performance_score = 100.0  # Start with perfect score
        
        # Penalize for inefficiencies
        violations = context.get_constraint_violations()
        performance_score -= len(violations) * 5.0
        
        conflicts = context.spatial_engine.detect_all_conflicts()
        performance_score -= len(conflicts) * 3.0
        
        return max(0.0, performance_score)


@dataclass
class OptimizationConstraint:
    """
    Optimization constraint definition.
    
    Defines constraints that solutions must satisfy during optimization,
    distinct from design constraints (Phase 2).
    """
    
    name: str
    constraint_function: Optional[Callable] = None
    constraint_type: str = "inequality"  # "equality", "inequality"
    tolerance: float = 1e-6
    
    # Constraint bounds
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    target_value: Optional[float] = None
    
    # Constraint metadata
    description: str = ""
    priority: int = 1  # 1 = highest priority
    
    def evaluate(self, 
                solution: Dict[str, Any],
                context: 'OptimizationContext') -> Tuple[bool, float]:
        """
        Evaluate constraint for solution.
        
        Returns:
            Tuple of (is_satisfied, constraint_value)
        """
        if not self.constraint_function:
            return True, 0.0
        
        try:
            value = self.constraint_function(solution, context)
            
            if self.constraint_type == "equality":
                is_satisfied = abs(value - (self.target_value or 0.0)) <= self.tolerance
            else:  # inequality
                if self.lower_bound is not None and value < self.lower_bound:
                    is_satisfied = False
                elif self.upper_bound is not None and value > self.upper_bound:
                    is_satisfied = False
                else:
                    is_satisfied = True
            
            return is_satisfied, value
            
        except Exception as e:
            logger.error(f"Error evaluating constraint {self.name}: {e}")
            return False, float('inf')


@dataclass
class OptimizationResult:
    """
    Complete optimization result.
    
    Contains the optimal solution, objective values, constraint satisfaction,
    and performance metrics.
    """
    
    # Result identification
    optimization_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    algorithm_used: str = ""
    
    # Solution
    best_solution: Dict[str, Any] = field(default_factory=dict)
    best_objective_values: Dict[str, float] = field(default_factory=dict)
    is_feasible: bool = True
    
    # Optimization progress
    iteration_count: int = 0
    evaluation_count: int = 0
    optimization_status: OptimizationStatus = OptimizationStatus.PENDING
    
    # Performance metrics
    optimization_time: float = 0.0
    convergence_history: List[Dict[str, float]] = field(default_factory=list)
    
    # Constraint satisfaction
    constraint_violations: List[str] = field(default_factory=list)
    constraint_satisfaction_score: float = 1.0
    
    # Multi-objective results
    pareto_solutions: List[Dict[str, Any]] = field(default_factory=list)
    pareto_front: List[Dict[str, float]] = field(default_factory=list)
    
    # Solution quality metrics
    objective_improvement: Dict[str, float] = field(default_factory=dict)
    solution_robustness: float = 0.0
    sensitivity_analysis: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    def add_iteration_result(self, 
                           iteration: int,
                           objective_values: Dict[str, float],
                           constraint_violations: List[str] = None) -> None:
        """Add result from optimization iteration."""
        
        self.iteration_count = iteration
        
        # Update best solution if better
        if self._is_better_solution(objective_values):
            self.best_objective_values = objective_values.copy()
            self.constraint_violations = constraint_violations or []
            
        # Add to convergence history
        history_entry = {
            'iteration': iteration,
            **objective_values,
            'constraint_violations': len(constraint_violations or [])
        }
        self.convergence_history.append(history_entry)
        
        # Update constraint satisfaction
        if constraint_violations:
            self.constraint_satisfaction_score = max(0.0, 
                1.0 - len(constraint_violations) / 100.0)  # Rough scoring
        else:
            self.constraint_satisfaction_score = 1.0
    
    def _is_better_solution(self, objective_values: Dict[str, float]) -> bool:
        """Check if new solution is better than current best."""
        if not self.best_objective_values:
            return True
        
        # For single objective, simple comparison
        if len(objective_values) == 1:
            objective_name = list(objective_values.keys())[0]
            return objective_values[objective_name] < self.best_objective_values.get(objective_name, float('inf'))
        
        # For multi-objective, check Pareto dominance
        return self._dominates(objective_values, self.best_objective_values)
    
    def _dominates(self, solution1: Dict[str, float], solution2: Dict[str, float]) -> bool:
        """Check if solution1 Pareto dominates solution2."""
        better_in_one = False
        
        for objective, value1 in solution1.items():
            value2 = solution2.get(objective, float('inf'))
            
            if value1 > value2:  # Worse in this objective
                return False
            elif value1 < value2:  # Better in this objective
                better_in_one = True
        
        return better_in_one


@dataclass 
class OptimizationConfiguration:
    """
    Optimization algorithm configuration.
    
    Contains algorithm settings, stopping criteria, and performance options.
    """
    
    # Algorithm selection
    algorithm: str = "genetic_algorithm"
    
    # Population-based algorithm settings
    population_size: int = 50
    elite_size: int = 5
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8
    
    # Stopping criteria
    max_iterations: int = 1000
    max_evaluations: int = 10000
    max_time_seconds: float = 300.0  # 5 minutes
    convergence_tolerance: float = 1e-6
    stagnation_limit: int = 50  # Iterations without improvement
    
    # Performance settings
    parallel_processing: bool = True
    max_workers: int = 4
    use_gpu_acceleration: bool = False
    
    # Solution diversity
    maintain_diversity: bool = True
    diversity_threshold: float = 0.01
    
    # Logging and monitoring
    log_frequency: int = 10  # Log every N iterations
    save_intermediate_results: bool = True
    
    # Advanced settings
    adaptive_parameters: bool = True
    restart_strategy: bool = False
    local_search: bool = True


@dataclass
class OptimizationMetrics:
    """
    Real-time optimization performance metrics.
    
    Tracks optimization progress, performance, and quality indicators.
    """
    
    # Progress metrics
    current_iteration: int = 0
    total_evaluations: int = 0
    elapsed_time: float = 0.0
    estimated_time_remaining: float = 0.0
    
    # Solution quality
    best_objective_value: float = float('inf')
    current_objective_value: float = float('inf')
    improvement_rate: float = 0.0
    
    # Algorithm performance
    evaluations_per_second: float = 0.0
    convergence_rate: float = 0.0
    stagnation_counter: int = 0
    
    # Population diversity (for population-based algorithms)
    population_diversity: float = 1.0
    solution_spread: float = 0.0
    
    # Resource utilization
    memory_usage_mb: float = 0.0
    cpu_utilization: float = 0.0
    gpu_utilization: float = 0.0
    
    # Constraint satisfaction
    feasible_solutions_ratio: float = 0.0
    constraint_violation_severity: float = 0.0
    
    def update_from_result(self, result: OptimizationResult) -> None:
        """Update metrics from optimization result."""
        self.current_iteration = result.iteration_count
        self.total_evaluations = result.evaluation_count
        self.elapsed_time = result.optimization_time
        
        if result.best_objective_values:
            # For single objective
            if len(result.best_objective_values) == 1:
                self.best_objective_value = list(result.best_objective_values.values())[0]
        
        # Update constraint satisfaction
        self.feasible_solutions_ratio = result.constraint_satisfaction_score
        
        # Calculate improvement rate
        if len(result.convergence_history) > 1:
            recent_values = [entry.get('objective_value', 0) 
                           for entry in result.convergence_history[-10:]]
            if len(recent_values) > 1:
                self.improvement_rate = (recent_values[-1] - recent_values[0]) / len(recent_values)


logger.info("Optimization core architecture initialized")