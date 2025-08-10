"""
Design Space Exploration and Sensitivity Analysis.

Advanced tools for exploring the design space, conducting sensitivity analysis,
and generating optimization insights for Building-Infrastructure-as-Code.
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
from itertools import product
import json

# Import optimization core
from .optimization_core import (
    OptimizationResult, OptimizationConfiguration, OptimizationVariable,
    OptimizationObjective, VariableType
)
from .optimization_engine import OptimizationContext
from .multi_objective import ParetoFrontier, ParetoSolution

logger = logging.getLogger(__name__)


class ExplorationMethod(Enum):
    """Design space exploration methods."""
    
    GRID_SEARCH = "grid_search"
    RANDOM_SAMPLING = "random_sampling"
    LATIN_HYPERCUBE = "latin_hypercube"
    SOBOL_SEQUENCE = "sobol_sequence"
    MORRIS_SCREENING = "morris_screening"
    ADAPTIVE_SAMPLING = "adaptive_sampling"


class SensitivityMethod(Enum):
    """Sensitivity analysis methods."""
    
    LOCAL_SENSITIVITY = "local_sensitivity"
    GLOBAL_SENSITIVITY = "global_sensitivity"
    MORRIS_METHOD = "morris_method"
    SOBOL_INDICES = "sobol_indices"
    VARIANCE_BASED = "variance_based"
    CORRELATION_ANALYSIS = "correlation_analysis"


@dataclass
class DesignPoint:
    """Single point in design space."""
    
    variables: Dict[str, Any] = field(default_factory=dict)
    objectives: Dict[str, float] = field(default_factory=dict)
    constraints_satisfied: bool = True
    constraint_violations: List[str] = field(default_factory=list)
    
    # Point metadata
    point_id: str = ""
    evaluation_time: float = 0.0
    generation_method: str = ""
    
    # Analysis results
    sensitivity_coefficients: Dict[str, Dict[str, float]] = field(default_factory=dict)
    local_gradients: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    def get_objective_vector(self, objective_names: List[str]) -> List[float]:
        """Get objective values as vector."""
        return [self.objectives.get(name, 0.0) for name in objective_names]
    
    def get_variable_vector(self, variable_names: List[str]) -> List[Any]:
        """Get variable values as vector."""
        return [self.variables.get(name, 0) for name in variable_names]


@dataclass
class SensitivityResult:
    """Results of sensitivity analysis."""
    
    # Local sensitivity
    local_sensitivities: Dict[str, Dict[str, float]] = field(default_factory=dict)  # obj -> var -> sensitivity
    
    # Global sensitivity
    sobol_indices: Dict[str, Dict[str, float]] = field(default_factory=dict)  # obj -> var -> index
    total_sobol_indices: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Morris method
    morris_mu: Dict[str, Dict[str, float]] = field(default_factory=dict)  # Mean effects
    morris_mu_star: Dict[str, Dict[str, float]] = field(default_factory=dict)  # Mean absolute effects  
    morris_sigma: Dict[str, Dict[str, float]] = field(default_factory=dict)  # Standard deviation
    
    # Correlation analysis
    variable_correlations: Dict[str, Dict[str, float]] = field(default_factory=dict)
    objective_correlations: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Analysis metadata
    method_used: str = ""
    sample_size: int = 0
    analysis_time: float = 0.0
    
    def get_most_sensitive_variables(self, 
                                   objective: str,
                                   method: str = "sobol",
                                   top_k: int = 5) -> List[Tuple[str, float]]:
        """Get most sensitive variables for an objective."""
        
        if method == "sobol" and objective in self.sobol_indices:
            sensitivities = self.sobol_indices[objective]
        elif method == "morris" and objective in self.morris_mu_star:
            sensitivities = self.morris_mu_star[objective]
        elif method == "local" and objective in self.local_sensitivities:
            sensitivities = self.local_sensitivities[objective]
        else:
            return []
        
        # Sort by sensitivity value (descending)
        sorted_vars = sorted(sensitivities.items(), key=lambda x: abs(x[1]), reverse=True)
        
        return sorted_vars[:top_k]


@dataclass
class ParametricDesign:
    """Parametric design configuration for exploration."""
    
    base_design: Dict[str, Any] = field(default_factory=dict)
    parameter_ranges: Dict[str, Tuple[Any, Any]] = field(default_factory=dict)
    parameter_steps: Dict[str, int] = field(default_factory=dict)
    
    # Design constraints
    design_rules: List[Callable] = field(default_factory=list)
    performance_targets: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    
    # Exploration settings
    exploration_method: ExplorationMethod = ExplorationMethod.LATIN_HYPERCUBE
    sample_size: int = 100
    
    def generate_design_variants(self, context: OptimizationContext) -> List[Dict[str, Any]]:
        """Generate parametric design variants."""
        
        variants = []
        
        if self.exploration_method == ExplorationMethod.GRID_SEARCH:
            variants = self._generate_grid_search(context)
        elif self.exploration_method == ExplorationMethod.RANDOM_SAMPLING:
            variants = self._generate_random_sampling(context)
        elif self.exploration_method == ExplorationMethod.LATIN_HYPERCUBE:
            variants = self._generate_latin_hypercube(context)
        else:
            variants = self._generate_random_sampling(context)  # Default
        
        # Apply design rules
        filtered_variants = []
        for variant in variants:
            if self._satisfies_design_rules(variant):
                filtered_variants.append(variant)
        
        return filtered_variants
    
    def _generate_grid_search(self, context: OptimizationContext) -> List[Dict[str, Any]]:
        """Generate grid search design variants."""
        
        # Get parameter combinations
        param_values = {}
        for var_name, variable in context.variables.items():
            if var_name in self.parameter_ranges:
                min_val, max_val = self.parameter_ranges[var_name]
                steps = self.parameter_steps.get(var_name, 5)
                
                if variable.variable_type == VariableType.CONTINUOUS:
                    param_values[var_name] = np.linspace(min_val, max_val, steps)
                elif variable.variable_type == VariableType.INTEGER:
                    param_values[var_name] = list(range(int(min_val), int(max_val) + 1))
                elif variable.variable_type == VariableType.CATEGORICAL:
                    param_values[var_name] = variable.categories
                else:
                    param_values[var_name] = [min_val, max_val]
            else:
                # Use base design value
                param_values[var_name] = [self.base_design.get(var_name, variable.initial_value)]
        
        # Generate all combinations
        param_names = list(param_values.keys())
        param_combinations = list(product(*param_values.values()))
        
        variants = []
        for combination in param_combinations:
            variant = dict(zip(param_names, combination))
            variants.append(variant)
        
        return variants
    
    def _generate_random_sampling(self, context: OptimizationContext) -> List[Dict[str, Any]]:
        """Generate random sampling design variants."""
        
        variants = []
        
        for _ in range(self.sample_size):
            variant = self.base_design.copy()
            
            for var_name, variable in context.variables.items():
                if var_name in self.parameter_ranges:
                    min_val, max_val = self.parameter_ranges[var_name]
                    
                    if variable.variable_type == VariableType.CONTINUOUS:
                        variant[var_name] = random.uniform(min_val, max_val)
                    elif variable.variable_type == VariableType.INTEGER:
                        variant[var_name] = random.randint(int(min_val), int(max_val))
                    elif variable.variable_type == VariableType.CATEGORICAL:
                        variant[var_name] = random.choice(variable.categories)
                    elif variable.variable_type == VariableType.BINARY:
                        variant[var_name] = random.choice([0, 1])
            
            variants.append(variant)
        
        return variants
    
    def _generate_latin_hypercube(self, context: OptimizationContext) -> List[Dict[str, Any]]:
        """Generate Latin Hypercube Sampling design variants."""
        
        # Get continuous variables for LHS
        continuous_vars = [(name, var) for name, var in context.variables.items()
                          if (var.variable_type == VariableType.CONTINUOUS and 
                              name in self.parameter_ranges)]
        
        if not continuous_vars:
            return self._generate_random_sampling(context)
        
        n_vars = len(continuous_vars)
        n_samples = self.sample_size
        
        # Generate LHS matrix
        lhs_matrix = np.zeros((n_samples, n_vars))
        
        for i in range(n_vars):
            # Generate random permutation
            perm = np.random.permutation(n_samples)
            # Generate uniform random values within intervals
            uniform_vals = np.random.uniform(0, 1, n_samples)
            # Create LHS samples
            lhs_matrix[:, i] = (perm + uniform_vals) / n_samples
        
        # Convert LHS matrix to design variants
        variants = []
        
        for sample_idx in range(n_samples):
            variant = self.base_design.copy()
            
            # Map LHS values to variable ranges
            for var_idx, (var_name, variable) in enumerate(continuous_vars):
                min_val, max_val = self.parameter_ranges[var_name]
                lhs_val = lhs_matrix[sample_idx, var_idx]
                variant[var_name] = min_val + lhs_val * (max_val - min_val)
            
            # Handle discrete variables with random sampling
            for var_name, variable in context.variables.items():
                if var_name not in dict(continuous_vars) and var_name in self.parameter_ranges:
                    min_val, max_val = self.parameter_ranges[var_name]
                    
                    if variable.variable_type == VariableType.INTEGER:
                        variant[var_name] = random.randint(int(min_val), int(max_val))
                    elif variable.variable_type == VariableType.CATEGORICAL:
                        variant[var_name] = random.choice(variable.categories)
                    elif variable.variable_type == VariableType.BINARY:
                        variant[var_name] = random.choice([0, 1])
            
            variants.append(variant)
        
        return variants
    
    def _satisfies_design_rules(self, variant: Dict[str, Any]) -> bool:
        """Check if variant satisfies design rules."""
        
        for rule in self.design_rules:
            try:
                if not rule(variant):
                    return False
            except:
                continue  # Skip rule if evaluation fails
        
        return True


class DesignSpaceExplorer:
    """
    Design space explorer for comprehensive design space analysis.
    
    Provides tools for systematic exploration of the design space,
    identification of design regions, and optimization opportunities.
    """
    
    def __init__(self, configuration: OptimizationConfiguration):
        self.configuration = configuration
        
        # Exploration parameters
        self.default_sample_size = 500
        self.exploration_method = ExplorationMethod.LATIN_HYPERCUBE
        self.parallel_evaluation = True
        
    def explore_design_space(self, 
                           context: OptimizationContext,
                           parametric_design: Optional[ParametricDesign] = None,
                           sample_size: Optional[int] = None) -> List[DesignPoint]:
        """Explore design space systematically."""
        
        start_time = time.time()
        sample_size = sample_size or self.default_sample_size
        
        logger.info(f"Starting design space exploration with {sample_size} samples")
        
        # Generate design points
        if parametric_design:
            parametric_design.sample_size = sample_size
            design_variants = parametric_design.generate_design_variants(context)
        else:
            design_variants = self._generate_exploration_samples(context, sample_size)
        
        # Evaluate design points
        design_points = []
        
        for i, variant in enumerate(design_variants):
            point_start_time = time.time()
            
            # Evaluate objectives and constraints
            objectives, violations, feasible = context.evaluate_solution(variant)
            
            design_point = DesignPoint(
                variables=variant.copy(),
                objectives=objectives,
                constraints_satisfied=feasible,
                constraint_violations=[v.description for v in violations],
                point_id=f"design_point_{i}",
                evaluation_time=time.time() - point_start_time,
                generation_method=self.exploration_method.value
            )
            
            design_points.append(design_point)
        
        exploration_time = time.time() - start_time
        
        logger.info(f"Design space exploration completed: {len(design_points)} points evaluated in {exploration_time:.2f}s")
        
        return design_points
    
    def _generate_exploration_samples(self, 
                                    context: OptimizationContext, 
                                    sample_size: int) -> List[Dict[str, Any]]:
        """Generate exploration samples using specified method."""
        
        if self.exploration_method == ExplorationMethod.GRID_SEARCH:
            return self._generate_grid_samples(context, sample_size)
        elif self.exploration_method == ExplorationMethod.RANDOM_SAMPLING:
            return self._generate_random_samples(context, sample_size)
        elif self.exploration_method == ExplorationMethod.LATIN_HYPERCUBE:
            return self._generate_lhs_samples(context, sample_size)
        elif self.exploration_method == ExplorationMethod.SOBOL_SEQUENCE:
            return self._generate_sobol_samples(context, sample_size)
        else:
            return self._generate_lhs_samples(context, sample_size)  # Default
    
    def _generate_grid_samples(self, context: OptimizationContext, sample_size: int) -> List[Dict[str, Any]]:
        """Generate grid-based samples."""
        
        # Calculate grid dimensions
        n_vars = len(context.variables)
        grid_size = int(sample_size ** (1/n_vars)) + 1
        
        # Generate grid points
        samples = []
        
        # Get variable bounds
        var_ranges = {}
        for var_name, variable in context.variables.items():
            if variable.variable_type in [VariableType.CONTINUOUS, VariableType.INTEGER]:
                var_ranges[var_name] = np.linspace(variable.lower_bound, variable.upper_bound, grid_size)
            elif variable.variable_type == VariableType.BINARY:
                var_ranges[var_name] = [0, 1]
            elif variable.variable_type == VariableType.CATEGORICAL:
                var_ranges[var_name] = variable.categories
            else:
                var_ranges[var_name] = [variable.initial_value or 0]
        
        # Generate combinations
        var_names = list(var_ranges.keys())
        combinations = list(product(*var_ranges.values()))
        
        # Limit to sample size
        if len(combinations) > sample_size:
            combinations = random.sample(combinations, sample_size)
        
        for combination in combinations:
            sample = dict(zip(var_names, combination))
            samples.append(sample)
        
        return samples
    
    def _generate_random_samples(self, context: OptimizationContext, sample_size: int) -> List[Dict[str, Any]]:
        """Generate random samples."""
        
        samples = []
        
        for _ in range(sample_size):
            sample = context.generate_random_solution()
            samples.append(sample)
        
        return samples
    
    def _generate_lhs_samples(self, context: OptimizationContext, sample_size: int) -> List[Dict[str, Any]]:
        """Generate Latin Hypercube samples."""
        
        # Get continuous variables
        continuous_vars = [(name, var) for name, var in context.variables.items()
                          if var.variable_type == VariableType.CONTINUOUS]
        
        samples = []
        
        if continuous_vars:
            n_vars = len(continuous_vars)
            
            # Generate LHS matrix
            lhs_matrix = np.zeros((sample_size, n_vars))
            
            for i in range(n_vars):
                perm = np.random.permutation(sample_size)
                uniform_vals = np.random.uniform(0, 1, sample_size)
                lhs_matrix[:, i] = (perm + uniform_vals) / sample_size
            
            # Convert to samples
            for sample_idx in range(sample_size):
                sample = {}
                
                # Map LHS values to continuous variables
                for var_idx, (var_name, variable) in enumerate(continuous_vars):
                    lhs_val = lhs_matrix[sample_idx, var_idx]
                    sample[var_name] = variable.lower_bound + lhs_val * (variable.upper_bound - variable.lower_bound)
                
                # Random values for discrete variables
                for var_name, variable in context.variables.items():
                    if var_name not in dict(continuous_vars):
                        if variable.variable_type == VariableType.INTEGER:
                            sample[var_name] = random.randint(variable.lower_bound, variable.upper_bound)
                        elif variable.variable_type == VariableType.BINARY:
                            sample[var_name] = random.choice([0, 1])
                        elif variable.variable_type == VariableType.CATEGORICAL:
                            sample[var_name] = random.choice(variable.categories)
                        else:
                            sample[var_name] = variable.initial_value or 0
                
                samples.append(sample)
        
        else:
            # No continuous variables - use random sampling
            samples = self._generate_random_samples(context, sample_size)
        
        return samples
    
    def _generate_sobol_samples(self, context: OptimizationContext, sample_size: int) -> List[Dict[str, Any]]:
        """Generate Sobol sequence samples (simplified implementation)."""
        # For now, use LHS as placeholder for Sobol sequence
        return self._generate_lhs_samples(context, sample_size)
    
    def identify_design_regions(self, 
                              design_points: List[DesignPoint],
                              context: OptimizationContext) -> Dict[str, Any]:
        """Identify interesting design regions."""
        
        regions = {
            'feasible_region': self._identify_feasible_region(design_points),
            'pareto_region': self._identify_pareto_region(design_points, context),
            'high_performance_regions': self._identify_high_performance_regions(design_points, context),
            'constraint_boundaries': self._identify_constraint_boundaries(design_points)
        }
        
        return regions
    
    def _identify_feasible_region(self, design_points: List[DesignPoint]) -> Dict[str, Any]:
        """Identify feasible design region."""
        
        feasible_points = [p for p in design_points if p.constraints_satisfied]
        
        if not feasible_points:
            return {'feasible_fraction': 0.0, 'bounds': {}}
        
        # Calculate feasible region bounds
        variable_bounds = {}
        
        if feasible_points:
            var_names = list(feasible_points[0].variables.keys())
            
            for var_name in var_names:
                values = [p.variables.get(var_name, 0) for p in feasible_points]
                variable_bounds[var_name] = {
                    'min': min(values),
                    'max': max(values),
                    'mean': sum(values) / len(values)
                }
        
        return {
            'feasible_fraction': len(feasible_points) / len(design_points),
            'feasible_count': len(feasible_points),
            'bounds': variable_bounds
        }
    
    def _identify_pareto_region(self, design_points: List[DesignPoint], context: OptimizationContext) -> Dict[str, Any]:
        """Identify Pareto-optimal region."""
        
        if len(context.objectives) < 2:
            return {}
        
        # Convert to Pareto solutions
        pareto_solutions = []
        for point in design_points:
            if point.constraints_satisfied:
                pareto_sol = ParetoSolution(
                    solution=point.variables,
                    objective_values=point.objectives,
                    is_feasible=True,
                    solution_id=point.point_id
                )
                pareto_solutions.append(pareto_sol)
        
        # Find Pareto frontier
        frontier = ParetoFrontier(objective_names=list(context.objectives.keys()))
        for solution in pareto_solutions:
            frontier.add_solution(solution)
        
        return {
            'pareto_solutions_count': len(frontier.solutions),
            'pareto_fraction': len(frontier.solutions) / len(design_points) if design_points else 0,
            'objective_ranges': self._calculate_objective_ranges(frontier.solutions)
        }
    
    def _identify_high_performance_regions(self, design_points: List[DesignPoint], context: OptimizationContext) -> Dict[str, Any]:
        """Identify high-performance design regions."""
        
        if not design_points:
            return {}
        
        # Define performance thresholds (top 10% for each objective)
        high_performers = {}
        
        for obj_name in context.objectives.keys():
            obj_values = [p.objectives.get(obj_name, float('inf')) 
                         for p in design_points if p.constraints_satisfied]
            
            if obj_values:
                threshold = np.percentile(obj_values, 90)  # Top 10%
                high_perf_points = [p for p in design_points 
                                  if (p.constraints_satisfied and 
                                      p.objectives.get(obj_name, float('inf')) <= threshold)]
                
                high_performers[obj_name] = {
                    'count': len(high_perf_points),
                    'threshold': threshold,
                    'fraction': len(high_perf_points) / len(design_points)
                }
        
        return high_performers
    
    def _identify_constraint_boundaries(self, design_points: List[DesignPoint]) -> Dict[str, Any]:
        """Identify constraint boundaries."""
        
        # Find points near constraint boundaries
        boundary_points = []
        constraint_violations = {}
        
        for point in design_points:
            if not point.constraints_satisfied:
                for violation in point.constraint_violations:
                    if violation not in constraint_violations:
                        constraint_violations[violation] = 0
                    constraint_violations[violation] += 1
        
        return {
            'constraint_violation_frequency': constraint_violations,
            'infeasible_fraction': sum(1 for p in design_points if not p.constraints_satisfied) / len(design_points)
        }
    
    def _calculate_objective_ranges(self, solutions: List[ParetoSolution]) -> Dict[str, Dict[str, float]]:
        """Calculate objective value ranges."""
        
        if not solutions:
            return {}
        
        ranges = {}
        
        # Get all objective names
        obj_names = set()
        for sol in solutions:
            obj_names.update(sol.objective_values.keys())
        
        for obj_name in obj_names:
            values = [sol.objective_values.get(obj_name, 0) for sol in solutions]
            
            ranges[obj_name] = {
                'min': min(values),
                'max': max(values),
                'range': max(values) - min(values),
                'mean': sum(values) / len(values)
            }
        
        return ranges


class SensitivityAnalyzer:
    """
    Advanced sensitivity analysis for optimization problems.
    
    Implements various sensitivity analysis methods including local gradients,
    global sensitivity indices, and Morris screening.
    """
    
    def __init__(self, configuration: OptimizationConfiguration):
        self.configuration = configuration
        
        # Sensitivity analysis parameters
        self.perturbation_size = 0.01  # 1% perturbation for local sensitivity
        self.morris_trajectories = 10  # Number of trajectories for Morris method
        self.sobol_sample_size = 1000  # Sample size for Sobol indices
        
    def perform_sensitivity_analysis(self, 
                                   context: OptimizationContext,
                                   design_points: Optional[List[DesignPoint]] = None,
                                   method: SensitivityMethod = SensitivityMethod.LOCAL_SENSITIVITY) -> SensitivityResult:
        """Perform comprehensive sensitivity analysis."""
        
        start_time = time.time()
        
        logger.info(f"Starting sensitivity analysis using {method.value}")
        
        result = SensitivityResult(
            method_used=method.value,
            analysis_time=0.0
        )
        
        if method == SensitivityMethod.LOCAL_SENSITIVITY:
            self._local_sensitivity_analysis(context, result)
        elif method == SensitivityMethod.MORRIS_METHOD:
            self._morris_sensitivity_analysis(context, result)
        elif method == SensitivityMethod.SOBOL_INDICES:
            self._sobol_sensitivity_analysis(context, result)
        elif method == SensitivityMethod.CORRELATION_ANALYSIS:
            if design_points:
                self._correlation_analysis(design_points, result)
        else:
            # Default to local sensitivity
            self._local_sensitivity_analysis(context, result)
        
        result.analysis_time = time.time() - start_time
        
        logger.info(f"Sensitivity analysis completed in {result.analysis_time:.2f}s")
        
        return result
    
    def _local_sensitivity_analysis(self, context: OptimizationContext, result: SensitivityResult) -> None:
        """Perform local sensitivity analysis using finite differences."""
        
        # Use current solution or generate baseline
        baseline_solution = context.current_solution.copy() if context.current_solution else context.generate_random_solution()
        
        # Evaluate baseline
        baseline_objectives, _, _ = context.evaluate_solution(baseline_solution)
        
        if not baseline_objectives:
            return
        
        # Calculate sensitivities for each variable
        for var_name, variable in context.variables.items():
            if variable.variable_type not in [VariableType.CONTINUOUS, VariableType.INTEGER]:
                continue
            
            # Calculate perturbation
            baseline_value = baseline_solution[var_name]
            
            if variable.variable_type == VariableType.CONTINUOUS:
                range_size = variable.upper_bound - variable.lower_bound
                perturbation = range_size * self.perturbation_size
            else:  # Integer
                perturbation = max(1, int(abs(baseline_value) * self.perturbation_size))
            
            # Forward difference
            perturbed_solution = baseline_solution.copy()
            perturbed_value = variable.clip_value(baseline_value + perturbation)
            perturbed_solution[var_name] = perturbed_value
            
            perturbed_objectives, _, _ = context.evaluate_solution(perturbed_solution)
            
            if not perturbed_objectives:
                continue
            
            # Calculate sensitivities for each objective
            for obj_name in baseline_objectives.keys():
                if obj_name in perturbed_objectives:
                    baseline_obj = baseline_objectives[obj_name]
                    perturbed_obj = perturbed_objectives[obj_name]
                    
                    # Sensitivity = (df/dx) = (f(x+h) - f(x)) / h
                    actual_perturbation = perturbed_value - baseline_value
                    if actual_perturbation != 0:
                        sensitivity = (perturbed_obj - baseline_obj) / actual_perturbation
                    else:
                        sensitivity = 0.0
                    
                    # Store sensitivity
                    if obj_name not in result.local_sensitivities:
                        result.local_sensitivities[obj_name] = {}
                    result.local_sensitivities[obj_name][var_name] = sensitivity
    
    def _morris_sensitivity_analysis(self, context: OptimizationContext, result: SensitivityResult) -> None:
        """Perform Morris sensitivity analysis (method of elementary effects)."""
        
        # Morris method parameters
        p = 4  # Number of levels
        delta = p / (2 * (p - 1))  # Grid jump
        
        # Get continuous variables only
        continuous_vars = [(name, var) for name, var in context.variables.items()
                          if var.variable_type == VariableType.CONTINUOUS]
        
        if not continuous_vars:
            return
        
        k = len(continuous_vars)  # Number of variables
        
        # Generate Morris trajectories
        for trajectory in range(self.morris_trajectories):
            # Generate base point
            base_point = {}
            for var_name, variable in continuous_vars:
                # Random point on Morris grid
                grid_value = random.choice(range(p)) / (p - 1)
                base_point[var_name] = variable.lower_bound + grid_value * (variable.upper_bound - variable.lower_bound)
            
            # Add non-continuous variables
            for var_name, variable in context.variables.items():
                if var_name not in dict(continuous_vars):
                    if variable.variable_type == VariableType.INTEGER:
                        base_point[var_name] = random.randint(variable.lower_bound, variable.upper_bound)
                    elif variable.variable_type == VariableType.BINARY:
                        base_point[var_name] = random.choice([0, 1])
                    elif variable.variable_type == VariableType.CATEGORICAL:
                        base_point[var_name] = random.choice(variable.categories)
            
            # Evaluate base point
            base_objectives, _, _ = context.evaluate_solution(base_point)
            if not base_objectives:
                continue
            
            # Generate trajectory by changing one variable at a time
            current_point = base_point.copy()
            
            for var_name, variable in continuous_vars:
                # Calculate elementary effect
                delta_val = delta * (variable.upper_bound - variable.lower_bound)
                
                # Random direction
                direction = random.choice([-1, 1])
                
                # Perturb variable
                new_value = variable.clip_value(current_point[var_name] + direction * delta_val)
                current_point[var_name] = new_value
                
                # Evaluate perturbed point
                perturbed_objectives, _, _ = context.evaluate_solution(current_point)
                
                if perturbed_objectives:
                    # Calculate elementary effects
                    for obj_name in base_objectives.keys():
                        if obj_name in perturbed_objectives:
                            effect = perturbed_objectives[obj_name] - base_objectives[obj_name]
                            
                            # Store effect
                            if obj_name not in result.morris_mu:
                                result.morris_mu[obj_name] = {}
                                result.morris_mu_star[obj_name] = {}
                                result.morris_sigma[obj_name] = {}
                            
                            if var_name not in result.morris_mu[obj_name]:
                                result.morris_mu[obj_name][var_name] = []
                            
                            result.morris_mu[obj_name][var_name].append(effect)
                
                # Update base for next variable
                base_objectives = perturbed_objectives if perturbed_objectives else base_objectives
        
        # Calculate Morris statistics
        for obj_name in result.morris_mu.keys():
            result.morris_mu_star[obj_name] = {}
            result.morris_sigma[obj_name] = {}
            
            for var_name in result.morris_mu[obj_name].keys():
                effects = result.morris_mu[obj_name][var_name]
                
                if effects:
                    # Mean effect
                    result.morris_mu[obj_name][var_name] = np.mean(effects)
                    
                    # Mean absolute effect
                    result.morris_mu_star[obj_name][var_name] = np.mean(np.abs(effects))
                    
                    # Standard deviation
                    result.morris_sigma[obj_name][var_name] = np.std(effects)
    
    def _sobol_sensitivity_analysis(self, context: OptimizationContext, result: SensitivityResult) -> None:
        """Perform Sobol global sensitivity analysis (simplified implementation)."""
        
        # Simplified Sobol analysis - full implementation would require specialized sampling
        # For now, use variance-based approach with random sampling
        
        samples = []
        objectives_list = []
        
        # Generate samples
        for _ in range(self.sobol_sample_size):
            sample = context.generate_random_solution()
            samples.append(sample)
            
            objectives, _, _ = context.evaluate_solution(sample)
            objectives_list.append(objectives)
        
        if not objectives_list or not objectives_list[0]:
            return
        
        # Calculate variance-based sensitivity indices (simplified)
        objective_names = list(objectives_list[0].keys())
        
        for obj_name in objective_names:
            obj_values = [obj.get(obj_name, 0) for obj in objectives_list if obj]
            
            if len(obj_values) < 2:
                continue
            
            total_variance = np.var(obj_values)
            
            if total_variance == 0:
                continue
            
            result.sobol_indices[obj_name] = {}
            result.total_sobol_indices[obj_name] = {}
            
            # Calculate first-order indices for each variable
            for var_name, variable in context.variables.items():
                if variable.variable_type not in [VariableType.CONTINUOUS, VariableType.INTEGER]:
                    continue
                
                # Group samples by variable value (binning for continuous)
                var_values = [sample[var_name] for sample in samples]
                
                if variable.variable_type == VariableType.CONTINUOUS:
                    # Bin continuous values
                    n_bins = 10
                    bins = np.linspace(min(var_values), max(var_values), n_bins + 1)
                    bin_indices = np.digitize(var_values, bins)
                    
                    # Calculate conditional variances
                    conditional_means = []
                    for bin_idx in range(1, n_bins + 1):
                        bin_obj_values = [obj_values[i] for i in range(len(obj_values)) 
                                        if bin_indices[i] == bin_idx]
                        if bin_obj_values:
                            conditional_means.append(np.mean(bin_obj_values))
                    
                    if conditional_means and len(conditional_means) > 1:
                        variance_of_means = np.var(conditional_means)
                        sobol_index = variance_of_means / total_variance
                    else:
                        sobol_index = 0.0
                
                else:  # Integer
                    # Group by actual integer values
                    unique_values = list(set(var_values))
                    conditional_means = []
                    
                    for val in unique_values:
                        val_obj_values = [obj_values[i] for i in range(len(obj_values)) 
                                        if var_values[i] == val]
                        if val_obj_values:
                            conditional_means.append(np.mean(val_obj_values))
                    
                    if conditional_means and len(conditional_means) > 1:
                        variance_of_means = np.var(conditional_means)
                        sobol_index = variance_of_means / total_variance
                    else:
                        sobol_index = 0.0
                
                result.sobol_indices[obj_name][var_name] = max(0.0, min(1.0, sobol_index))
                result.total_sobol_indices[obj_name][var_name] = sobol_index  # Simplified
    
    def _correlation_analysis(self, design_points: List[DesignPoint], result: SensitivityResult) -> None:
        """Perform correlation analysis on design points."""
        
        if len(design_points) < 2:
            return
        
        # Extract variable and objective data
        var_names = list(design_points[0].variables.keys())
        obj_names = list(design_points[0].objectives.keys()) if design_points[0].objectives else []
        
        if not obj_names:
            return
        
        # Create data matrices
        var_data = {}
        obj_data = {}
        
        for var_name in var_names:
            var_values = []
            for point in design_points:
                value = point.variables.get(var_name, 0)
                # Convert to numeric for correlation
                if isinstance(value, (int, float)):
                    var_values.append(float(value))
                else:
                    var_values.append(0.0)  # Default for non-numeric
            var_data[var_name] = var_values
        
        for obj_name in obj_names:
            obj_values = [point.objectives.get(obj_name, 0) for point in design_points]
            obj_data[obj_name] = obj_values
        
        # Calculate variable correlations
        result.variable_correlations = {}
        for i, var1 in enumerate(var_names):
            result.variable_correlations[var1] = {}
            for var2 in var_names[i+1:]:
                if len(set(var_data[var1])) > 1 and len(set(var_data[var2])) > 1:
                    correlation = np.corrcoef(var_data[var1], var_data[var2])[0, 1]
                    if not np.isnan(correlation):
                        result.variable_correlations[var1][var2] = correlation
        
        # Calculate objective correlations
        result.objective_correlations = {}
        for i, obj1 in enumerate(obj_names):
            result.objective_correlations[obj1] = {}
            for obj2 in obj_names[i+1:]:
                if len(set(obj_data[obj1])) > 1 and len(set(obj_data[obj2])) > 1:
                    correlation = np.corrcoef(obj_data[obj1], obj_data[obj2])[0, 1]
                    if not np.isnan(correlation):
                        result.objective_correlations[obj1][obj2] = correlation


@dataclass
class OptimizationInsights:
    """
    Optimization insights and recommendations.
    
    Contains analysis results, recommendations, and actionable insights
    from design space exploration and sensitivity analysis.
    """
    
    # Design space insights
    design_space_coverage: float = 0.0
    feasible_design_fraction: float = 0.0
    promising_regions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Sensitivity insights
    critical_variables: Dict[str, List[Tuple[str, float]]] = field(default_factory=dict)  # obj -> [(var, sensitivity)]
    robust_variables: List[str] = field(default_factory=list)
    
    # Optimization recommendations
    algorithm_recommendations: List[str] = field(default_factory=list)
    parameter_recommendations: Dict[str, Any] = field(default_factory=dict)
    constraint_recommendations: List[str] = field(default_factory=list)
    
    # Performance insights
    convergence_predictions: Dict[str, float] = field(default_factory=dict)
    optimization_difficulty: str = "medium"  # "easy", "medium", "hard"
    expected_runtime: float = 0.0
    
    def generate_summary_report(self) -> str:
        """Generate human-readable insights summary."""
        
        lines = []
        lines.append("OPTIMIZATION INSIGHTS SUMMARY")
        lines.append("=" * 40)
        lines.append("")
        
        # Design space
        lines.append("Design Space Analysis:")
        lines.append(f"  • Feasible design fraction: {self.feasible_design_fraction:.1%}")
        lines.append(f"  • Design space coverage: {self.design_space_coverage:.1%}")
        lines.append(f"  • Promising regions found: {len(self.promising_regions)}")
        lines.append("")
        
        # Critical variables
        if self.critical_variables:
            lines.append("Most Critical Variables:")
            for obj_name, variables in self.critical_variables.items():
                lines.append(f"  {obj_name}:")
                for var_name, sensitivity in variables[:3]:  # Top 3
                    lines.append(f"    - {var_name}: {sensitivity:.3f}")
            lines.append("")
        
        # Recommendations
        if self.algorithm_recommendations:
            lines.append("Algorithm Recommendations:")
            for rec in self.algorithm_recommendations:
                lines.append(f"  • {rec}")
            lines.append("")
        
        # Performance
        lines.append("Optimization Difficulty:")
        lines.append(f"  • Problem complexity: {self.optimization_difficulty}")
        if self.expected_runtime > 0:
            lines.append(f"  • Expected runtime: {self.expected_runtime:.1f}s")
        
        return "\n".join(lines)


logger.info("Design space exploration and sensitivity analysis initialized")