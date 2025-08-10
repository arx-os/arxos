"""
Multi-Objective Optimization Framework.

Advanced multi-objective optimization with Pareto frontier generation,
trade-off analysis, and preference handling for Building-Infrastructure-as-Code.
"""

import time
import logging
import numpy as np
import math
from typing import Dict, Any, List, Optional, Tuple, Set, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import random
from copy import deepcopy

# Import optimization core
from .optimization_core import (
    OptimizationResult, OptimizationConfiguration, OptimizationStatus,
    OptimizationType, OptimizationObjective, OptimizationVariable
)
from .optimization_engine import OptimizationContext

logger = logging.getLogger(__name__)


class ParetoRelation(Enum):
    """Pareto dominance relations between solutions."""
    
    DOMINATES = "dominates"
    DOMINATED_BY = "dominated_by"
    NON_DOMINATED = "non_dominated"
    INCOMPARABLE = "incomparable"


class ScalarizationMethod(Enum):
    """Methods for scalarizing multi-objective problems."""
    
    WEIGHTED_SUM = "weighted_sum"
    WEIGHTED_TCHEBYCHEFF = "weighted_tchebycheff"
    ACHIEVEMENT_SCALARIZING = "achievement_scalarizing"
    EPSILON_CONSTRAINT = "epsilon_constraint"
    REFERENCE_POINT = "reference_point"


@dataclass
class ParetoSolution:
    """Single solution in Pareto frontier."""
    
    solution: Dict[str, Any]
    objective_values: Dict[str, float]
    constraint_violations: List[str] = field(default_factory=list)
    is_feasible: bool = True
    
    # Solution metadata
    solution_id: str = ""
    generation_method: str = ""
    evaluation_time: float = 0.0
    
    # Multi-objective metrics
    crowding_distance: float = 0.0
    dominance_count: int = 0
    dominated_solutions: Set[str] = field(default_factory=set)
    pareto_rank: int = 0
    
    def dominates(self, other: 'ParetoSolution') -> bool:
        """Check if this solution dominates another (minimization assumed)."""
        if not self.is_feasible and other.is_feasible:
            return False
        if self.is_feasible and not other.is_feasible:
            return True
        
        # Both feasible - check objective dominance
        better_in_one = False
        for obj_name in self.objective_values:
            if obj_name not in other.objective_values:
                continue
            
            self_val = self.objective_values[obj_name]
            other_val = other.objective_values[obj_name]
            
            if self_val > other_val:  # Worse in this objective
                return False
            elif self_val < other_val:  # Better in this objective
                better_in_one = True
        
        return better_in_one


@dataclass
class ParetoFrontier:
    """Collection of non-dominated solutions forming Pareto frontier."""
    
    solutions: List[ParetoSolution] = field(default_factory=list)
    objective_names: List[str] = field(default_factory=list)
    
    # Frontier metadata
    generation_time: float = 0.0
    hypervolume: float = 0.0
    spread_metric: float = 0.0
    convergence_metric: float = 0.0
    
    def add_solution(self, solution: ParetoSolution) -> bool:
        """Add solution to frontier, maintaining non-dominance."""
        
        # Check if solution is dominated by existing solutions
        for existing in self.solutions:
            if existing.dominates(solution):
                return False  # Solution is dominated
        
        # Remove solutions dominated by new solution
        self.solutions = [s for s in self.solutions if not solution.dominates(s)]
        
        # Add new solution
        self.solutions.append(solution)
        
        # Update crowding distances
        self._calculate_crowding_distances()
        
        return True
    
    def _calculate_crowding_distances(self) -> None:
        """Calculate crowding distance for each solution."""
        if len(self.solutions) <= 2:
            for solution in self.solutions:
                solution.crowding_distance = float('inf')
            return
        
        # Initialize distances
        for solution in self.solutions:
            solution.crowding_distance = 0.0
        
        # Calculate for each objective
        for obj_name in self.objective_names:
            # Sort by objective value
            sorted_solutions = sorted(self.solutions, 
                                    key=lambda s: s.objective_values.get(obj_name, 0))
            
            # Boundary solutions get infinite distance
            sorted_solutions[0].crowding_distance = float('inf')
            sorted_solutions[-1].crowding_distance = float('inf')
            
            # Calculate range
            obj_min = sorted_solutions[0].objective_values.get(obj_name, 0)
            obj_max = sorted_solutions[-1].objective_values.get(obj_name, 0)
            obj_range = obj_max - obj_min
            
            if obj_range == 0:
                continue
            
            # Calculate distances for intermediate solutions
            for i in range(1, len(sorted_solutions) - 1):
                prev_val = sorted_solutions[i-1].objective_values.get(obj_name, 0)
                next_val = sorted_solutions[i+1].objective_values.get(obj_name, 0)
                
                distance = (next_val - prev_val) / obj_range
                sorted_solutions[i].crowding_distance += distance
    
    def get_best_compromise_solution(self, weights: Optional[Dict[str, float]] = None) -> Optional[ParetoSolution]:
        """Get best compromise solution using weighted sum."""
        if not self.solutions:
            return None
        
        if weights is None:
            # Equal weights
            weights = {obj: 1.0 / len(self.objective_names) for obj in self.objective_names}
        
        best_solution = None
        best_score = float('inf')
        
        for solution in self.solutions:
            score = sum(weights.get(obj, 0) * val 
                       for obj, val in solution.objective_values.items())
            
            if score < best_score:
                best_score = score
                best_solution = solution
        
        return best_solution
    
    def calculate_hypervolume(self, reference_point: Dict[str, float]) -> float:
        """Calculate hypervolume indicator."""
        if not self.solutions or len(self.objective_names) > 3:
            return 0.0  # Simplified for high dimensions
        
        # Simplified hypervolume calculation for 2D case
        if len(self.objective_names) == 2:
            return self._calculate_hypervolume_2d(reference_point)
        
        return 0.0
    
    def _calculate_hypervolume_2d(self, reference_point: Dict[str, float]) -> float:
        """Calculate 2D hypervolume."""
        if len(self.objective_names) != 2:
            return 0.0
        
        obj1, obj2 = self.objective_names[:2]
        
        # Sort solutions by first objective
        sorted_solutions = sorted(self.solutions, 
                                key=lambda s: s.objective_values.get(obj1, 0))
        
        volume = 0.0
        prev_obj2 = reference_point[obj2]
        
        for solution in sorted_solutions:
            obj1_val = solution.objective_values.get(obj1, 0)
            obj2_val = solution.objective_values.get(obj2, 0)
            
            if obj1_val < reference_point[obj1] and obj2_val < reference_point[obj2]:
                width = reference_point[obj1] - obj1_val
                height = prev_obj2 - obj2_val
                volume += width * height
                prev_obj2 = obj2_val
        
        return volume


@dataclass
class ObjectiveWeighting:
    """Objective weighting configuration for multi-objective optimization."""
    
    weights: Dict[str, float] = field(default_factory=dict)
    priorities: Dict[str, int] = field(default_factory=dict)
    
    # Adaptive weighting
    adaptive_weights: bool = False
    weight_update_frequency: int = 50  # Update every N generations
    
    # Preference information
    aspiration_levels: Dict[str, float] = field(default_factory=dict)
    reservation_levels: Dict[str, float] = field(default_factory=dict)
    
    def normalize_weights(self) -> None:
        """Normalize weights to sum to 1.0."""
        total_weight = sum(self.weights.values())
        if total_weight > 0:
            self.weights = {obj: w / total_weight for obj, w in self.weights.items()}
    
    def update_adaptive_weights(self, 
                              current_solutions: List[ParetoSolution],
                              generation: int) -> None:
        """Update weights based on solution diversity."""
        if not self.adaptive_weights or generation % self.weight_update_frequency != 0:
            return
        
        # Calculate objective ranges
        obj_ranges = {}
        for obj_name in self.weights.keys():
            values = [s.objective_values.get(obj_name, 0) for s in current_solutions]
            if values:
                obj_ranges[obj_name] = max(values) - min(values)
        
        # Adjust weights inversely to ranges (focus on objectives with small ranges)
        total_inv_range = sum(1.0 / max(r, 1e-6) for r in obj_ranges.values())
        
        for obj_name, range_val in obj_ranges.items():
            self.weights[obj_name] = (1.0 / max(range_val, 1e-6)) / total_inv_range


class MultiObjectiveOptimizer:
    """
    Multi-objective optimization framework.
    
    Implements various multi-objective algorithms including NSGA-II,
    MOEA/D, and preference-based methods.
    """
    
    def __init__(self, configuration: OptimizationConfiguration):
        self.configuration = configuration
        self.algorithm = "nsga2"  # "nsga2", "moead", "spea2"
        
        # Multi-objective parameters
        self.population_size = configuration.population_size
        self.archive_size = configuration.population_size * 2
        self.reference_point_method = "nadir_ideal"
        
    def optimize_multi_objective(self, 
                                context: OptimizationContext,
                                problem_id: str,
                                weighting: Optional[ObjectiveWeighting] = None) -> Tuple[OptimizationResult, ParetoFrontier]:
        """Run multi-objective optimization."""
        
        if self.algorithm == "nsga2":
            return self._nsga2(context, problem_id, weighting)
        elif self.algorithm == "moead":
            return self._moead(context, problem_id, weighting)
        else:
            return self._nsga2(context, problem_id, weighting)  # Default
    
    def _nsga2(self, 
              context: OptimizationContext,
              problem_id: str,
              weighting: Optional[ObjectiveWeighting]) -> Tuple[OptimizationResult, ParetoFrontier]:
        """NSGA-II multi-objective genetic algorithm."""
        start_time = time.time()
        
        result = OptimizationResult(
            optimization_id=problem_id,
            algorithm_used="nsga2",
            optimization_status=OptimizationStatus.RUNNING
        )
        
        frontier = ParetoFrontier(
            objective_names=list(context.objectives.keys())
        )
        
        # Initialize population
        population = []
        for _ in range(self.population_size):
            individual = context.generate_random_solution()
            population.append(individual)
        
        # Evolution loop
        for generation in range(self.configuration.max_iterations):
            # Evaluate population
            pareto_solutions = []
            for individual in population:
                objectives, violations, feasible = context.evaluate_solution(individual)
                
                pareto_sol = ParetoSolution(
                    solution=individual.copy(),
                    objective_values=objectives,
                    constraint_violations=[v.description for v in violations],
                    is_feasible=feasible,
                    solution_id=f"gen{generation}_sol{len(pareto_solutions)}"
                )
                pareto_solutions.append(pareto_sol)
            
            # Non-dominated sorting
            fronts = self._fast_non_dominated_sort(pareto_solutions)
            
            # Create new population
            new_population = []
            front_index = 0
            
            while len(new_population) + len(fronts[front_index]) <= self.population_size:
                # Add entire front
                for solution in fronts[front_index]:
                    new_population.append(solution.solution)
                front_index += 1
                
                if front_index >= len(fronts):
                    break
            
            # Fill remaining spots using crowding distance
            if front_index < len(fronts) and len(new_population) < self.population_size:
                remaining_front = fronts[front_index]
                self._calculate_crowding_distances_for_front(remaining_front)
                
                # Sort by crowding distance (descending)
                remaining_front.sort(key=lambda s: s.crowding_distance, reverse=True)
                
                remaining_spots = self.population_size - len(new_population)
                for i in range(remaining_spots):
                    new_population.append(remaining_front[i].solution)
            
            population = new_population
            
            # Update frontier with first front
            if fronts:
                for solution in fronts[0]:
                    frontier.add_solution(solution)
            
            # Update result
            if frontier.solutions:
                best_compromise = frontier.get_best_compromise_solution(
                    weighting.weights if weighting else None
                )
                if best_compromise:
                    result.best_solution = best_compromise.solution
                    result.best_objective_values = best_compromise.objective_values
                    result.is_feasible = best_compromise.is_feasible
            
            result.iteration_count = generation + 1
            
            # Update adaptive weights
            if weighting and weighting.adaptive_weights:
                weighting.update_adaptive_weights(pareto_solutions, generation)
            
            # Check stopping criteria
            if time.time() - start_time > self.configuration.max_time_seconds:
                result.optimization_status = OptimizationStatus.MAX_TIME
                break
            
            # Generate offspring for next generation
            if generation < self.configuration.max_iterations - 1:
                offspring = self._generate_offspring_nsga2(population, context)
                population.extend(offspring)
        
        # Finalize results
        result.optimization_time = time.time() - start_time
        result.evaluation_count = context.evaluation_count
        
        if result.optimization_status == OptimizationStatus.RUNNING:
            result.optimization_status = OptimizationStatus.MAX_ITERATIONS
        
        # Store Pareto solutions
        result.pareto_solutions = [s.solution for s in frontier.solutions]
        result.pareto_front = [s.objective_values for s in frontier.solutions]
        
        logger.info(f"NSGA-II completed: {len(frontier.solutions)} Pareto solutions found")
        
        return result, frontier
    
    def _fast_non_dominated_sort(self, solutions: List[ParetoSolution]) -> List[List[ParetoSolution]]:
        """Fast non-dominated sorting algorithm."""
        
        # Initialize dominance information
        for solution in solutions:
            solution.dominance_count = 0
            solution.dominated_solutions = set()
        
        # Calculate dominance relationships
        for i, sol1 in enumerate(solutions):
            for j, sol2 in enumerate(solutions[i+1:], i+1):
                if sol1.dominates(sol2):
                    sol1.dominated_solutions.add(sol2.solution_id)
                    sol2.dominance_count += 1
                elif sol2.dominates(sol1):
                    sol2.dominated_solutions.add(sol1.solution_id)
                    sol1.dominance_count += 1
        
        # Create fronts
        fronts = []
        current_front = []
        
        # First front (non-dominated solutions)
        for solution in solutions:
            if solution.dominance_count == 0:
                solution.pareto_rank = 0
                current_front.append(solution)
        
        fronts.append(current_front)
        
        # Subsequent fronts
        front_index = 0
        while fronts[front_index]:
            next_front = []
            
            for solution in fronts[front_index]:
                for dominated_id in solution.dominated_solutions:
                    # Find dominated solution
                    dominated_sol = next((s for s in solutions if s.solution_id == dominated_id), None)
                    if dominated_sol:
                        dominated_sol.dominance_count -= 1
                        if dominated_sol.dominance_count == 0:
                            dominated_sol.pareto_rank = front_index + 1
                            next_front.append(dominated_sol)
            
            fronts.append(next_front)
            front_index += 1
        
        # Remove empty last front
        if not fronts[-1]:
            fronts.pop()
        
        return fronts
    
    def _calculate_crowding_distances_for_front(self, front: List[ParetoSolution]) -> None:
        """Calculate crowding distances for solutions in a front."""
        if len(front) <= 2:
            for solution in front:
                solution.crowding_distance = float('inf')
            return
        
        # Initialize distances
        for solution in front:
            solution.crowding_distance = 0.0
        
        # Get objective names
        if not front[0].objective_values:
            return
        
        objective_names = list(front[0].objective_values.keys())
        
        # Calculate for each objective
        for obj_name in objective_names:
            # Sort by objective value
            front.sort(key=lambda s: s.objective_values.get(obj_name, 0))
            
            # Boundary solutions get infinite distance
            front[0].crowding_distance = float('inf')
            front[-1].crowding_distance = float('inf')
            
            # Calculate range
            obj_min = front[0].objective_values.get(obj_name, 0)
            obj_max = front[-1].objective_values.get(obj_name, 0)
            obj_range = obj_max - obj_min
            
            if obj_range == 0:
                continue
            
            # Calculate distances for intermediate solutions
            for i in range(1, len(front) - 1):
                prev_val = front[i-1].objective_values.get(obj_name, 0)
                next_val = front[i+1].objective_values.get(obj_name, 0)
                
                distance = (next_val - prev_val) / obj_range
                front[i].crowding_distance += distance
    
    def _generate_offspring_nsga2(self, 
                                 population: List[Dict[str, Any]], 
                                 context: OptimizationContext) -> List[Dict[str, Any]]:
        """Generate offspring using tournament selection, crossover, and mutation."""
        offspring = []
        
        # Generate pairs for crossover
        for _ in range(len(population) // 2):
            # Tournament selection
            parent1 = self._tournament_selection(population, context)
            parent2 = self._tournament_selection(population, context)
            
            # Crossover
            if random.random() < self.configuration.crossover_rate:
                child1, child2 = self._crossover_multi_objective(parent1, parent2, context)
            else:
                child1, child2 = parent1.copy(), parent2.copy()
            
            # Mutation
            if random.random() < self.configuration.mutation_rate:
                child1 = self._mutate_multi_objective(child1, context)
            if random.random() < self.configuration.mutation_rate:
                child2 = self._mutate_multi_objective(child2, context)
            
            offspring.extend([child1, child2])
        
        return offspring
    
    def _tournament_selection(self, 
                             population: List[Dict[str, Any]], 
                             context: OptimizationContext,
                             tournament_size: int = 2) -> Dict[str, Any]:
        """Tournament selection for multi-objective problems."""
        
        # Select random individuals for tournament
        tournament = random.sample(population, min(tournament_size, len(population)))
        
        # Evaluate tournament individuals
        tournament_solutions = []
        for individual in tournament:
            objectives, violations, feasible = context.evaluate_solution(individual)
            sol = ParetoSolution(
                solution=individual,
                objective_values=objectives,
                is_feasible=feasible
            )
            tournament_solutions.append(sol)
        
        # Select best (non-dominated with highest crowding distance)
        best_solution = tournament_solutions[0]
        
        for solution in tournament_solutions[1:]:
            if solution.pareto_rank < best_solution.pareto_rank:
                best_solution = solution
            elif (solution.pareto_rank == best_solution.pareto_rank and 
                  solution.crowding_distance > best_solution.crowding_distance):
                best_solution = solution
        
        return best_solution.solution
    
    def _crossover_multi_objective(self, 
                                  parent1: Dict[str, Any], 
                                  parent2: Dict[str, Any],
                                  context: OptimizationContext) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Simulated binary crossover for multi-objective problems."""
        
        child1 = parent1.copy()
        child2 = parent2.copy()
        
        eta_c = 20  # Distribution index for crossover
        
        for var_name, variable in context.variables.items():
            if variable.variable_type not in [VariableType.CONTINUOUS, VariableType.INTEGER]:
                # Use simple crossover for discrete variables
                if random.random() < 0.5:
                    child1[var_name], child2[var_name] = parent2[var_name], parent1[var_name]
                continue
            
            if random.random() < 0.5:
                continue  # Skip this variable
            
            val1 = parent1[var_name]
            val2 = parent2[var_name]
            
            if abs(val1 - val2) < 1e-6:
                continue  # Parents have same value
            
            # Simulated binary crossover
            y1 = min(val1, val2)
            y2 = max(val1, val2)
            
            lb = variable.lower_bound
            ub = variable.upper_bound
            
            if random.random() <= 0.5:
                # Calculate beta
                if (y1 - lb) > (ub - y2):
                    beta = 1 + (2 * (ub - y2) / (y2 - y1))
                else:
                    beta = 1 + (2 * (y1 - lb) / (y2 - y1))
                
                beta = 1.0 / beta
                alpha = 2 - beta**(eta_c + 1)
                
                u = random.random()
                if u <= (1 / alpha):
                    betaq = (u * alpha)**(1 / (eta_c + 1))
                else:
                    betaq = (1 / (2 - u * alpha))**(1 / (eta_c + 1))
                
                c1 = 0.5 * ((y1 + y2) - betaq * (y2 - y1))
                c2 = 0.5 * ((y1 + y2) + betaq * (y2 - y1))
                
                # Apply bounds
                c1 = variable.clip_value(c1)
                c2 = variable.clip_value(c2)
                
                child1[var_name] = c1
                child2[var_name] = c2
        
        return child1, child2
    
    def _mutate_multi_objective(self, 
                               individual: Dict[str, Any],
                               context: OptimizationContext) -> Dict[str, Any]:
        """Polynomial mutation for multi-objective problems."""
        
        mutated = individual.copy()
        eta_m = 20  # Distribution index for mutation
        
        for var_name, variable in context.variables.items():
            if random.random() > (1.0 / len(context.variables)):
                continue  # Skip this variable
            
            if variable.variable_type == VariableType.CONTINUOUS:
                val = mutated[var_name]
                lb = variable.lower_bound
                ub = variable.upper_bound
                
                delta1 = (val - lb) / (ub - lb)
                delta2 = (ub - val) / (ub - lb)
                
                mut_pow = 1.0 / (eta_m + 1.0)
                
                u = random.random()
                if u <= 0.5:
                    xy = 1.0 - delta1
                    val = xy**(mut_pow) - 1.0
                    deltaq = val * (2 * u)**mut_pow
                else:
                    xy = 1.0 - delta2
                    val = xy**(mut_pow) - 1.0
                    deltaq = val * (2 * (1 - u))**mut_pow
                
                new_val = val + deltaq * (ub - lb)
                mutated[var_name] = variable.clip_value(new_val)
            
            elif variable.variable_type == VariableType.INTEGER:
                # Integer mutation
                mutated[var_name] = random.randint(variable.lower_bound, variable.upper_bound)
            
            elif variable.variable_type == VariableType.BINARY:
                mutated[var_name] = 1 - mutated[var_name]
            
            elif variable.variable_type == VariableType.CATEGORICAL:
                mutated[var_name] = random.choice(variable.categories)
        
        return mutated
    
    def _moead(self, 
              context: OptimizationContext,
              problem_id: str,
              weighting: Optional[ObjectiveWeighting]) -> Tuple[OptimizationResult, ParetoFrontier]:
        """MOEA/D (Multi-Objective Evolutionary Algorithm based on Decomposition)."""
        # Placeholder for MOEA/D implementation
        # For now, delegate to NSGA-II
        return self._nsga2(context, problem_id, weighting)


class TradeoffAnalysis:
    """
    Trade-off analysis for multi-objective solutions.
    
    Provides tools for analyzing trade-offs between objectives,
    sensitivity analysis, and decision support.
    """
    
    def __init__(self):
        self.analysis_methods = [
            "pareto_frontier_analysis",
            "sensitivity_analysis", 
            "preference_analysis",
            "robustness_analysis"
        ]
    
    def analyze_tradeoffs(self, 
                         frontier: ParetoFrontier,
                         context: OptimizationContext) -> Dict[str, Any]:
        """Comprehensive trade-off analysis."""
        
        analysis = {
            'frontier_statistics': self._analyze_frontier_statistics(frontier),
            'objective_correlations': self._analyze_objective_correlations(frontier),
            'sensitivity_analysis': self._perform_sensitivity_analysis(frontier, context),
            'knee_points': self._find_knee_points(frontier),
            'decision_recommendations': self._generate_decision_recommendations(frontier)
        }
        
        return analysis
    
    def _analyze_frontier_statistics(self, frontier: ParetoFrontier) -> Dict[str, Any]:
        """Analyze Pareto frontier statistics."""
        
        if not frontier.solutions:
            return {}
        
        stats = {}
        
        # Objective statistics
        for obj_name in frontier.objective_names:
            values = [s.objective_values.get(obj_name, 0) for s in frontier.solutions]
            
            stats[obj_name] = {
                'min': min(values),
                'max': max(values),
                'mean': sum(values) / len(values),
                'range': max(values) - min(values),
                'std': np.std(values) if len(values) > 1 else 0
            }
        
        # Frontier metrics
        stats['frontier_size'] = len(frontier.solutions)
        stats['feasible_solutions'] = sum(1 for s in frontier.solutions if s.is_feasible)
        stats['average_crowding_distance'] = np.mean([s.crowding_distance for s in frontier.solutions])
        
        return stats
    
    def _analyze_objective_correlations(self, frontier: ParetoFrontier) -> Dict[str, Dict[str, float]]:
        """Analyze correlations between objectives."""
        
        if len(frontier.objective_names) < 2 or len(frontier.solutions) < 2:
            return {}
        
        correlations = {}
        
        for i, obj1 in enumerate(frontier.objective_names):
            correlations[obj1] = {}
            values1 = [s.objective_values.get(obj1, 0) for s in frontier.solutions]
            
            for obj2 in frontier.objective_names[i+1:]:
                values2 = [s.objective_values.get(obj2, 0) for s in frontier.solutions]
                
                # Calculate Pearson correlation
                correlation = np.corrcoef(values1, values2)[0, 1]
                correlations[obj1][obj2] = correlation
                
                if obj2 not in correlations:
                    correlations[obj2] = {}
                correlations[obj2][obj1] = correlation
        
        return correlations
    
    def _perform_sensitivity_analysis(self, 
                                    frontier: ParetoFrontier,
                                    context: OptimizationContext) -> Dict[str, Any]:
        """Perform sensitivity analysis on Pareto solutions."""
        
        sensitivity = {}
        
        if not frontier.solutions:
            return sensitivity
        
        # Sample a few representative solutions
        sample_size = min(5, len(frontier.solutions))
        sample_solutions = random.sample(frontier.solutions, sample_size)
        
        for sol in sample_solutions:
            sol_sensitivity = {}
            
            # Test sensitivity to variable changes
            for var_name, variable in context.variables.items():
                if variable.variable_type not in [VariableType.CONTINUOUS, VariableType.INTEGER]:
                    continue
                
                original_value = sol.solution[var_name]
                
                # Small perturbation
                if variable.variable_type == VariableType.CONTINUOUS:
                    perturbation = (variable.upper_bound - variable.lower_bound) * 0.01
                else:
                    perturbation = 1
                
                # Test positive and negative perturbations
                perturbed_objectives = []
                
                for delta in [-perturbation, perturbation]:
                    test_solution = sol.solution.copy()
                    test_value = variable.clip_value(original_value + delta)
                    test_solution[var_name] = test_value
                    
                    # Evaluate perturbed solution
                    objectives, _, _ = context.evaluate_solution(test_solution)
                    perturbed_objectives.append(objectives)
                
                # Calculate sensitivity
                var_sensitivity = {}
                for obj_name in frontier.objective_names:
                    original_obj = sol.objective_values.get(obj_name, 0)
                    
                    if perturbed_objectives[0] and perturbed_objectives[1]:
                        obj_change = (perturbed_objectives[1].get(obj_name, 0) - 
                                     perturbed_objectives[0].get(obj_name, 0))
                        var_change = 2 * perturbation
                        
                        sensitivity_coef = obj_change / var_change if var_change != 0 else 0
                        var_sensitivity[obj_name] = abs(sensitivity_coef)
                
                sol_sensitivity[var_name] = var_sensitivity
            
            sensitivity[sol.solution_id] = sol_sensitivity
        
        return sensitivity
    
    def _find_knee_points(self, frontier: ParetoFrontier) -> List[ParetoSolution]:
        """Find knee points (maximum trade-off regions) in Pareto frontier."""
        
        if len(frontier.solutions) < 3 or len(frontier.objective_names) != 2:
            return []  # Only implemented for 2D problems
        
        knee_points = []
        
        # Sort solutions by first objective
        obj1, obj2 = frontier.objective_names[:2]
        sorted_solutions = sorted(frontier.solutions, 
                                key=lambda s: s.objective_values.get(obj1, 0))
        
        # Calculate angles between consecutive solutions
        for i in range(1, len(sorted_solutions) - 1):
            prev_sol = sorted_solutions[i-1]
            curr_sol = sorted_solutions[i]
            next_sol = sorted_solutions[i+1]
            
            # Calculate vectors
            v1 = (curr_sol.objective_values.get(obj1, 0) - prev_sol.objective_values.get(obj1, 0),
                  curr_sol.objective_values.get(obj2, 0) - prev_sol.objective_values.get(obj2, 0))
            
            v2 = (next_sol.objective_values.get(obj1, 0) - curr_sol.objective_values.get(obj1, 0),
                  next_sol.objective_values.get(obj2, 0) - curr_sol.objective_values.get(obj2, 0))
            
            # Calculate angle
            dot_product = v1[0] * v2[0] + v1[1] * v2[1]
            norm1 = math.sqrt(v1[0]**2 + v1[1]**2)
            norm2 = math.sqrt(v2[0]**2 + v2[1]**2)
            
            if norm1 > 0 and norm2 > 0:
                cos_angle = dot_product / (norm1 * norm2)
                angle = math.acos(max(-1, min(1, cos_angle)))  # Clamp to valid range
                
                # Knee points have large angles (sharp turns)
                if angle > math.pi / 3:  # 60 degrees
                    knee_points.append(curr_sol)
        
        return knee_points
    
    def _generate_decision_recommendations(self, frontier: ParetoFrontier) -> List[str]:
        """Generate decision recommendations based on frontier analysis."""
        
        recommendations = []
        
        if not frontier.solutions:
            recommendations.append("No feasible solutions found. Consider relaxing constraints.")
            return recommendations
        
        # Analyze frontier diversity
        if len(frontier.solutions) < 3:
            recommendations.append("Limited solution diversity. Consider expanding search or adjusting parameters.")
        
        # Check for dominant objectives
        if len(frontier.objective_names) >= 2:
            obj_ranges = {}
            for obj_name in frontier.objective_names:
                values = [s.objective_values.get(obj_name, 0) for s in frontier.solutions]
                obj_ranges[obj_name] = max(values) - min(values)
            
            max_range = max(obj_ranges.values())
            for obj_name, range_val in obj_ranges.items():
                if range_val < max_range * 0.1:  # Very small range
                    recommendations.append(f"Objective '{obj_name}' shows little variation - consider adjusting bounds or weights.")
        
        # Solution quality recommendations
        feasible_count = sum(1 for s in frontier.solutions if s.is_feasible)
        if feasible_count < len(frontier.solutions) * 0.8:
            recommendations.append("Many solutions violate constraints. Consider constraint relaxation or penalty adjustments.")
        
        # Best compromise recommendation
        if len(frontier.solutions) > 5:
            recommendations.append("Multiple good solutions available. Use preference information to select final solution.")
        
        return recommendations


logger.info("Multi-objective optimization framework initialized")