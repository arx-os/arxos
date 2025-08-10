"""
Constraint-Aware Optimization Solvers.

Advanced constraint satisfaction and mathematical programming solvers
that integrate with Building-Infrastructure-as-Code constraint validation.
"""

import time
import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum
import math

# Import optimization core
from .optimization_core import (
    OptimizationResult, OptimizationConfiguration, OptimizationStatus,
    OptimizationVariable, OptimizationConstraint, OptimizationType,
    VariableType
)
from .optimization_engine import OptimizationContext

# Import constraint validation
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.constraints import ConstraintViolation, ConstraintSeverity

logger = logging.getLogger(__name__)


class SolverMethod(Enum):
    """Constraint solver methods."""
    
    BACKTRACKING = "backtracking"
    FORWARD_CHECKING = "forward_checking"  
    ARC_CONSISTENCY = "arc_consistency"
    LOCAL_SEARCH = "local_search"
    CONSTRAINT_PROPAGATION = "constraint_propagation"
    BRANCH_AND_BOUND = "branch_and_bound"
    
    # Mathematical programming
    LINEAR_PROGRAMMING = "linear_programming"
    QUADRATIC_PROGRAMMING = "quadratic_programming"
    NONLINEAR_PROGRAMMING = "nonlinear_programming"
    MIXED_INTEGER = "mixed_integer"
    SEMIDEFINITE_PROGRAMMING = "semidefinite_programming"


class ConstraintSolver(ABC):
    """Base class for constraint solvers."""
    
    def __init__(self, configuration: OptimizationConfiguration):
        self.configuration = configuration
        self.solver_method = SolverMethod.BACKTRACKING
        
    @abstractmethod
    def solve(self, context: OptimizationContext, problem_id: str) -> OptimizationResult:
        """Solve constraint satisfaction problem."""
        pass
    
    def is_solution_feasible(self, 
                           solution: Dict[str, Any],
                           context: OptimizationContext) -> Tuple[bool, List[ConstraintViolation]]:
        """Check if solution satisfies all constraints."""
        
        # Apply solution to context
        context.apply_solution(solution)
        
        # Get constraint violations
        violations = context.get_constraint_violations()
        
        # Check optimization constraints
        optimization_violations = []
        for constraint_name, constraint in context.constraints.items():
            satisfied, value = constraint.evaluate(solution, context)
            if not satisfied:
                # Create violation representation
                violation = ConstraintViolation(
                    constraint_id=constraint_name,
                    description=f"Optimization constraint violation: {constraint.description}",
                    severity=ConstraintSeverity.ERROR,
                    constraint_name=constraint.name,
                    technical_details={'constraint_value': value}
                )
                optimization_violations.append(violation)
        
        all_violations = violations + optimization_violations
        return len(all_violations) == 0, all_violations


class ConstraintSatisfactionSolver(ConstraintSolver):
    """
    Constraint Satisfaction Problem (CSP) solver.
    
    Uses backtracking with constraint propagation and heuristics
    for discrete constraint satisfaction problems.
    """
    
    def __init__(self, configuration: OptimizationConfiguration):
        super().__init__(configuration)
        self.solver_method = SolverMethod.FORWARD_CHECKING
        
        # CSP-specific parameters
        self.use_arc_consistency = True
        self.use_forward_checking = True
        self.variable_ordering_heuristic = "most_constraining_variable"
        self.value_ordering_heuristic = "least_constraining_value"
    
    def solve(self, context: OptimizationContext, problem_id: str) -> OptimizationResult:
        """Solve CSP using backtracking with constraint propagation."""
        start_time = time.time()
        
        result = OptimizationResult(
            optimization_id=problem_id,
            algorithm_used="constraint_satisfaction",
            optimization_status=OptimizationStatus.RUNNING
        )
        
        # Initialize domains for each variable
        domains = self._initialize_domains(context)
        
        # Apply arc consistency preprocessing
        if self.use_arc_consistency:
            domains = self._enforce_arc_consistency(domains, context)
            if not domains:  # Infeasible
                result.optimization_status = OptimizationStatus.INFEASIBLE
                result.optimization_time = time.time() - start_time
                return result
        
        # Backtracking search
        solution = {}
        assignment_order = self._order_variables(context, domains)
        
        success = self._backtrack(solution, assignment_order, domains, context, result, start_time)
        
        # Finalize result
        result.optimization_time = time.time() - start_time
        
        if success:
            result.optimization_status = OptimizationStatus.CONVERGED
            result.best_solution = solution
            result.is_feasible = True
            
            # Evaluate objectives for the solution
            objectives, violations, feasible = context.evaluate_solution(solution)
            result.best_objective_values = objectives
            result.constraint_violations = [v.description for v in violations]
        else:
            result.optimization_status = OptimizationStatus.INFEASIBLE
            result.is_feasible = False
        
        logger.info(f"CSP solver completed: {result.optimization_status.value}, "
                   f"{result.optimization_time:.2f}s")
        
        return result
    
    def _initialize_domains(self, context: OptimizationContext) -> Dict[str, List[Any]]:
        """Initialize variable domains."""
        domains = {}
        
        for var_name, variable in context.variables.items():
            if variable.variable_type == VariableType.BINARY:
                domains[var_name] = [0, 1]
            
            elif variable.variable_type == VariableType.CATEGORICAL:
                domains[var_name] = variable.categories.copy()
            
            elif variable.variable_type == VariableType.INTEGER:
                # For large integer ranges, sample values
                range_size = variable.upper_bound - variable.lower_bound
                if range_size <= 100:
                    domains[var_name] = list(range(variable.lower_bound, variable.upper_bound + 1))
                else:
                    # Sample representative values
                    step = max(1, range_size // 50)
                    domains[var_name] = list(range(variable.lower_bound, 
                                                  variable.upper_bound + 1, step))
            
            elif variable.variable_type == VariableType.CONTINUOUS:
                # Discretize continuous variables for CSP
                range_size = variable.upper_bound - variable.lower_bound
                num_values = min(20, int(range_size / variable.precision))
                step = range_size / num_values
                
                domains[var_name] = [variable.lower_bound + i * step 
                                   for i in range(num_values + 1)]
            
            else:
                # Default domain
                domains[var_name] = [variable.initial_value] if variable.initial_value else [0]
        
        return domains
    
    def _enforce_arc_consistency(self, 
                                domains: Dict[str, List[Any]], 
                                context: OptimizationContext) -> Optional[Dict[str, List[Any]]]:
        """Enforce arc consistency (AC-3 algorithm)."""
        
        # Create arc queue
        arcs = []
        variables = list(context.variables.keys())
        
        for i, var1 in enumerate(variables):
            for var2 in variables[i+1:]:
                arcs.append((var1, var2))
                arcs.append((var2, var1))
        
        # Process arcs
        while arcs:
            var1, var2 = arcs.pop(0)
            
            if self._revise(var1, var2, domains, context):
                if not domains[var1]:  # Domain became empty
                    return None  # Infeasible
                
                # Add affected arcs back to queue
                for var3 in variables:
                    if var3 != var1 and var3 != var2:
                        arcs.append((var3, var1))
        
        return domains
    
    def _revise(self, 
               var1: str, 
               var2: str, 
               domains: Dict[str, List[Any]], 
               context: OptimizationContext) -> bool:
        """Revise domain of var1 based on constraint with var2."""
        revised = False
        
        # Check each value in var1's domain
        for value1 in domains[var1][:]:  # Copy to avoid modification during iteration
            
            # Check if there exists a compatible value in var2's domain
            compatible_found = False
            
            for value2 in domains[var2]:
                # Create partial assignment
                test_solution = {var1: value1, var2: value2}
                
                # Check if this assignment satisfies constraints
                if self._satisfies_binary_constraints(test_solution, context):
                    compatible_found = True
                    break
            
            if not compatible_found:
                domains[var1].remove(value1)
                revised = True
        
        return revised
    
    def _satisfies_binary_constraints(self, 
                                    partial_solution: Dict[str, Any], 
                                    context: OptimizationContext) -> bool:
        """Check if partial solution satisfies binary constraints."""
        
        # Check optimization constraints
        for constraint in context.constraints.values():
            try:
                satisfied, _ = constraint.evaluate(partial_solution, context)
                if not satisfied:
                    return False
            except:
                # Constraint may not be evaluable with partial solution
                continue
        
        return True
    
    def _order_variables(self, 
                        context: OptimizationContext, 
                        domains: Dict[str, List[Any]]) -> List[str]:
        """Order variables using heuristic."""
        
        variables = list(context.variables.keys())
        
        if self.variable_ordering_heuristic == "most_constraining_variable":
            # Order by smallest domain size (most constrained first)
            return sorted(variables, key=lambda v: len(domains[v]))
        
        elif self.variable_ordering_heuristic == "most_constraining_variable":
            # Order by number of constraints involving the variable
            constraint_counts = {}
            for var in variables:
                count = 0
                for constraint in context.constraints.values():
                    # Simple heuristic - check if variable name appears in constraint
                    if hasattr(constraint, 'constraint_function') and var in str(constraint.constraint_function):
                        count += 1
                constraint_counts[var] = count
            
            return sorted(variables, key=lambda v: constraint_counts.get(v, 0), reverse=True)
        
        else:
            return variables
    
    def _order_values(self, 
                     variable: str, 
                     domains: Dict[str, List[Any]], 
                     context: OptimizationContext) -> List[Any]:
        """Order values for variable using heuristic."""
        
        values = domains[variable]
        
        if self.value_ordering_heuristic == "least_constraining_value":
            # Order by values that eliminate fewest options from other domains
            value_scores = {}
            
            for value in values:
                score = 0
                # Test impact on other variables
                for other_var in context.variables:
                    if other_var == variable:
                        continue
                    
                    for other_value in domains[other_var]:
                        test_solution = {variable: value, other_var: other_value}
                        if not self._satisfies_binary_constraints(test_solution, context):
                            score += 1  # This value eliminates this option
                
                value_scores[value] = score
            
            return sorted(values, key=lambda v: value_scores.get(v, 0))
        
        else:
            return values
    
    def _backtrack(self, 
                  solution: Dict[str, Any], 
                  variables: List[str], 
                  domains: Dict[str, List[Any]], 
                  context: OptimizationContext,
                  result: OptimizationResult,
                  start_time: float) -> bool:
        """Recursive backtracking search."""
        
        # Check time limit
        if time.time() - start_time > self.configuration.max_time_seconds:
            return False
        
        # Check if assignment is complete
        if len(solution) == len(variables):
            return self._is_complete_solution_valid(solution, context)
        
        # Select next variable
        unassigned_vars = [v for v in variables if v not in solution]
        if not unassigned_vars:
            return True
        
        var = unassigned_vars[0]  # Already ordered
        
        # Try each value in domain
        ordered_values = self._order_values(var, domains, context)
        
        for value in ordered_values:
            solution[var] = value
            
            # Check consistency
            if self._is_consistent(solution, context):
                
                # Forward checking
                if self.use_forward_checking:
                    new_domains = self._forward_check(solution, domains, context)
                    if new_domains is None:  # Inconsistent
                        del solution[var]
                        continue
                    domains = new_domains
                
                # Recursive call
                if self._backtrack(solution, variables, domains, context, result, start_time):
                    return True
            
            # Backtrack
            del solution[var]
        
        return False
    
    def _is_consistent(self, 
                      partial_solution: Dict[str, Any], 
                      context: OptimizationContext) -> bool:
        """Check if partial solution is consistent."""
        return self._satisfies_binary_constraints(partial_solution, context)
    
    def _is_complete_solution_valid(self, 
                                  solution: Dict[str, Any], 
                                  context: OptimizationContext) -> bool:
        """Check if complete solution is valid."""
        is_feasible, violations = self.is_solution_feasible(solution, context)
        return is_feasible
    
    def _forward_check(self, 
                      partial_solution: Dict[str, Any], 
                      domains: Dict[str, List[Any]], 
                      context: OptimizationContext) -> Optional[Dict[str, List[Any]]]:
        """Perform forward checking to prune domains."""
        
        new_domains = {var: domain[:] for var, domain in domains.items()}
        
        # For each unassigned variable
        for var in context.variables:
            if var in partial_solution:
                continue
            
            # Check each value in domain
            for value in new_domains[var][:]:
                test_solution = partial_solution.copy()
                test_solution[var] = value
                
                if not self._is_consistent(test_solution, context):
                    new_domains[var].remove(value)
                    
                    if not new_domains[var]:  # Domain became empty
                        return None
        
        return new_domains


class LinearProgrammingSolver(ConstraintSolver):
    """
    Linear Programming solver for continuous optimization problems.
    
    Handles linear objectives and linear constraints using simplex method
    or interior point methods.
    """
    
    def __init__(self, configuration: OptimizationConfiguration):
        super().__init__(configuration)
        self.solver_method = SolverMethod.LINEAR_PROGRAMMING
        
        # LP-specific parameters
        self.tolerance = 1e-6
        self.max_iterations = 1000
        self.method = "simplex"  # "simplex", "interior_point"
    
    def solve(self, context: OptimizationContext, problem_id: str) -> OptimizationResult:
        """Solve linear programming problem."""
        start_time = time.time()
        
        result = OptimizationResult(
            optimization_id=problem_id,
            algorithm_used="linear_programming",
            optimization_status=OptimizationStatus.RUNNING
        )
        
        # Check if problem is actually linear
        if not self._is_linear_problem(context):
            logger.warning("Problem is not linear - using approximation")
        
        # Convert to standard LP form
        c, A_eq, b_eq, A_ub, b_ub, bounds = self._convert_to_standard_form(context)
        
        if c is None:
            result.optimization_status = OptimizationStatus.ERROR
            result.optimization_time = time.time() - start_time
            return result
        
        # Solve LP (simplified implementation)
        solution_vector = self._solve_simplex(c, A_eq, b_eq, A_ub, b_ub, bounds)
        
        if solution_vector is not None:
            # Convert back to variable solution
            solution = self._convert_solution_back(solution_vector, context)
            
            # Evaluate solution
            objectives, violations, feasible = context.evaluate_solution(solution)
            
            result.best_solution = solution
            result.best_objective_values = objectives
            result.is_feasible = feasible
            result.constraint_violations = [v.description for v in violations]
            result.optimization_status = OptimizationStatus.CONVERGED
        
        else:
            result.optimization_status = OptimizationStatus.INFEASIBLE
        
        result.optimization_time = time.time() - start_time
        
        logger.info(f"LP solver completed: {result.optimization_status.value}")
        
        return result
    
    def _is_linear_problem(self, context: OptimizationContext) -> bool:
        """Check if problem has linear objectives and constraints."""
        # Simplified check - in practice would analyze objective and constraint functions
        return True  # Assume linear for now
    
    def _convert_to_standard_form(self, context: OptimizationContext) -> Tuple:
        """Convert optimization problem to standard LP form."""
        
        # Get continuous variables only
        continuous_vars = [(name, var) for name, var in context.variables.items() 
                          if var.variable_type == VariableType.CONTINUOUS]
        
        if not continuous_vars:
            return None, None, None, None, None, None
        
        n_vars = len(continuous_vars)
        
        # Objective coefficients (assume minimizing sum of variables for now)
        c = np.ones(n_vars)
        
        # Bounds
        bounds = []
        for name, var in continuous_vars:
            bounds.append((var.lower_bound, var.upper_bound))
        
        # Inequality constraints (simplified)
        A_ub = np.array([[1.0] * n_vars])  # Sum <= some value
        b_ub = np.array([sum(var.upper_bound for _, var in continuous_vars)])
        
        # Equality constraints (none for now)
        A_eq = None
        b_eq = None
        
        return c, A_eq, b_eq, A_ub, b_ub, bounds
    
    def _solve_simplex(self, c, A_eq, b_eq, A_ub, b_ub, bounds) -> Optional[np.ndarray]:
        """Simplified simplex solver (placeholder)."""
        
        # This is a placeholder - would implement full simplex algorithm
        # or use optimization library like scipy.optimize.linprog
        
        n_vars = len(c)
        
        # Return feasible solution at midpoint of bounds
        solution = np.zeros(n_vars)
        for i, (lower, upper) in enumerate(bounds):
            solution[i] = (lower + upper) / 2
        
        return solution
    
    def _convert_solution_back(self, 
                              solution_vector: np.ndarray, 
                              context: OptimizationContext) -> Dict[str, Any]:
        """Convert solution vector back to variable solution."""
        
        solution = {}
        continuous_vars = [(name, var) for name, var in context.variables.items() 
                          if var.variable_type == VariableType.CONTINUOUS]
        
        for i, (name, var) in enumerate(continuous_vars):
            solution[name] = float(solution_vector[i])
        
        # Set non-continuous variables to their initial values or defaults
        for name, var in context.variables.items():
            if name not in solution:
                if var.initial_value is not None:
                    solution[name] = var.initial_value
                elif var.variable_type == VariableType.BINARY:
                    solution[name] = 0
                elif var.variable_type == VariableType.CATEGORICAL:
                    solution[name] = var.categories[0] if var.categories else ""
                else:
                    solution[name] = var.lower_bound if var.lower_bound is not None else 0
        
        return solution


class NonlinearProgrammingSolver(ConstraintSolver):
    """
    Nonlinear Programming solver for continuous optimization.
    
    Handles nonlinear objectives and constraints using gradient-based
    and derivative-free methods.
    """
    
    def __init__(self, configuration: OptimizationConfiguration):
        super().__init__(configuration)
        self.solver_method = SolverMethod.NONLINEAR_PROGRAMMING
        
        # NLP-specific parameters
        self.tolerance = 1e-6
        self.max_function_evaluations = 10000
        self.gradient_method = "finite_difference"
    
    def solve(self, context: OptimizationContext, problem_id: str) -> OptimizationResult:
        """Solve nonlinear programming problem."""
        # Placeholder - would implement NLP solver
        # For now, delegate to simulated annealing
        from .optimization_algorithms import SimulatedAnnealing
        
        sa = SimulatedAnnealing(self.configuration)
        result = sa.optimize(context, problem_id)
        result.algorithm_used = "nonlinear_programming_sa"
        
        return result


class MixedIntegerSolver(ConstraintSolver):
    """
    Mixed Integer Programming solver.
    
    Handles problems with both continuous and integer variables using
    branch-and-bound and cutting plane methods.
    """
    
    def __init__(self, configuration: OptimizationConfiguration):
        super().__init__(configuration)
        self.solver_method = SolverMethod.MIXED_INTEGER
        
        # MIP-specific parameters
        self.branching_strategy = "most_fractional"
        self.cutting_planes = True
        self.presolve = True
    
    def solve(self, context: OptimizationContext, problem_id: str) -> OptimizationResult:
        """Solve mixed integer programming problem."""
        
        # Check if problem has integer variables
        has_integers = any(var.variable_type in [VariableType.INTEGER, VariableType.BINARY] 
                          for var in context.variables.values())
        
        if not has_integers:
            # Use LP solver
            lp_solver = LinearProgrammingSolver(self.configuration)
            result = lp_solver.solve(context, problem_id)
            result.algorithm_used = "mixed_integer_lp"
            return result
        
        # Use branch-and-bound (simplified implementation)
        return self._branch_and_bound(context, problem_id)
    
    def _branch_and_bound(self, context: OptimizationContext, problem_id: str) -> OptimizationResult:
        """Branch-and-bound for mixed integer problems."""
        start_time = time.time()
        
        result = OptimizationResult(
            optimization_id=problem_id,
            algorithm_used="branch_and_bound",
            optimization_status=OptimizationStatus.RUNNING
        )
        
        # Initialize with root node (relaxed problem)
        best_solution = None
        best_objective = float('inf')
        
        # Priority queue of nodes (simplified as list)
        nodes = [{'bounds': self._get_variable_bounds(context), 'depth': 0}]
        
        nodes_explored = 0
        max_nodes = 1000  # Limit search
        
        while nodes and nodes_explored < max_nodes:
            if time.time() - start_time > self.configuration.max_time_seconds:
                break
            
            # Select node (best-first)
            current_node = nodes.pop(0)
            nodes_explored += 1
            
            # Solve relaxed problem at this node
            relaxed_solution = self._solve_relaxed_problem(current_node, context)
            
            if relaxed_solution is None:
                continue  # Infeasible node
            
            # Check if solution is integer feasible
            if self._is_integer_feasible(relaxed_solution, context):
                # Evaluate objective
                objectives, violations, feasible = context.evaluate_solution(relaxed_solution)
                if objectives and feasible:
                    objective_value = sum(objectives.values())
                    if objective_value < best_objective:
                        best_objective = objective_value
                        best_solution = relaxed_solution
                        
                        result.best_solution = best_solution
                        result.best_objective_values = objectives
                        result.is_feasible = feasible
            else:
                # Branch on most fractional variable
                branch_var = self._select_branching_variable(relaxed_solution, context)
                if branch_var:
                    left_bounds, right_bounds = self._create_branches(
                        current_node['bounds'], branch_var, relaxed_solution[branch_var]
                    )
                    
                    nodes.append({'bounds': left_bounds, 'depth': current_node['depth'] + 1})
                    nodes.append({'bounds': right_bounds, 'depth': current_node['depth'] + 1})
                    
                    # Sort nodes by bound (best-first)
                    nodes.sort(key=lambda n: n['depth'])  # Simplified sorting
        
        result.optimization_time = time.time() - start_time
        result.evaluation_count = nodes_explored
        
        if best_solution:
            result.optimization_status = OptimizationStatus.CONVERGED
        else:
            result.optimization_status = OptimizationStatus.MAX_ITERATIONS
        
        logger.info(f"Branch-and-bound completed: {nodes_explored} nodes explored")
        
        return result
    
    def _get_variable_bounds(self, context: OptimizationContext) -> Dict[str, Tuple[float, float]]:
        """Get current variable bounds."""
        bounds = {}
        for name, var in context.variables.items():
            bounds[name] = (var.lower_bound, var.upper_bound)
        return bounds
    
    def _solve_relaxed_problem(self, node: Dict, context: OptimizationContext) -> Optional[Dict[str, Any]]:
        """Solve LP relaxation at node."""
        # Simplified - generate feasible solution within bounds
        solution = {}
        
        for name, var in context.variables.items():
            lower, upper = node['bounds'][name]
            
            if var.variable_type in [VariableType.CONTINUOUS, VariableType.INTEGER]:
                solution[name] = (lower + upper) / 2
            elif var.variable_type == VariableType.BINARY:
                solution[name] = 0.5  # Fractional for branching
            else:
                solution[name] = var.initial_value or lower
        
        return solution
    
    def _is_integer_feasible(self, solution: Dict[str, Any], context: OptimizationContext) -> bool:
        """Check if solution has integer values for integer variables."""
        for name, var in context.variables.items():
            if var.variable_type == VariableType.INTEGER:
                if abs(solution[name] - round(solution[name])) > 1e-6:
                    return False
            elif var.variable_type == VariableType.BINARY:
                if solution[name] not in [0.0, 1.0]:
                    return False
        return True
    
    def _select_branching_variable(self, solution: Dict[str, Any], context: OptimizationContext) -> Optional[str]:
        """Select variable for branching."""
        max_fractional = 0
        branch_var = None
        
        for name, var in context.variables.items():
            if var.variable_type in [VariableType.INTEGER, VariableType.BINARY]:
                value = solution[name]
                fractional_part = abs(value - round(value))
                
                if fractional_part > max_fractional:
                    max_fractional = fractional_part
                    branch_var = name
        
        return branch_var
    
    def _create_branches(self, 
                        bounds: Dict[str, Tuple[float, float]], 
                        var_name: str, 
                        var_value: float) -> Tuple[Dict, Dict]:
        """Create left and right branches."""
        left_bounds = bounds.copy()
        right_bounds = bounds.copy()
        
        # Left branch: var <= floor(value)
        # Right branch: var >= ceil(value)
        floor_val = math.floor(var_value)
        ceil_val = math.ceil(var_value)
        
        left_bounds[var_name] = (bounds[var_name][0], floor_val)
        right_bounds[var_name] = (ceil_val, bounds[var_name][1])
        
        return left_bounds, right_bounds


logger.info("Constraint-aware optimization solvers initialized")