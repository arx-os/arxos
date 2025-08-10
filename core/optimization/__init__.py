"""
Arxos Optimization Engine - Phase 3.

Advanced optimization algorithms for Building-Infrastructure-as-Code that leverage
Phase 1 spatial indexing and Phase 2 constraint validation to automatically optimize
building layouts, minimize conflicts, and maximize performance objectives.

Core Components:
- OptimizationEngine: High-performance parallel optimization coordinator
- OptimizationAlgorithms: Advanced algorithms (genetic, simulated annealing, etc.)
- ConstraintSolvers: Constraint-aware optimization solvers
- MultiObjectiveOptimizer: Pareto-optimal solution generation
- DesignSpaceExplorer: Design space exploration and sensitivity analysis
- ConflictResolver: Optimization-aware conflict resolution
- OptimizationDashboard: Performance analytics and visualization

Key Features:
- GPU-accelerated parallel processing
- Multi-objective optimization with Pareto frontiers
- Real-time constraint-aware optimization
- Design space exploration and sensitivity analysis
- Automated conflict resolution with optimization
- Performance analytics and optimization insights
"""

# Core optimization engine and algorithms
from .optimization_core import (
    OptimizationObjective, OptimizationVariable, OptimizationConstraint,
    OptimizationResult, OptimizationConfiguration, OptimizationMetrics
)

from .optimization_engine import OptimizationEngine, OptimizationContext

from .optimization_algorithms import (
    GeneticAlgorithm, SimulatedAnnealing, ParticleSwarmOptimization,
    GradientBasedOptimizer, HybridOptimizer
)

# Constraint-aware solvers
from .constraint_solvers import (
    ConstraintSatisfactionSolver, LinearProgrammingSolver,
    NonlinearProgrammingSolver, MixedIntegerSolver
)

# Multi-objective optimization
from .multi_objective import (
    MultiObjectiveOptimizer, ParetoFrontier, ObjectiveWeighting,
    TradeoffAnalysis
)

# Design space exploration
from .design_explorer import (
    DesignSpaceExplorer, SensitivityAnalyzer, ParametricDesign,
    OptimizationInsights
)

# Optimization-aware conflict resolution
from .optimization_resolver import OptimizationBasedResolver

# Performance analytics
from .optimization_dashboard import OptimizationDashboard, OptimizationVisualizer

__all__ = [
    # Core
    'OptimizationObjective', 'OptimizationVariable', 'OptimizationConstraint',
    'OptimizationResult', 'OptimizationConfiguration', 'OptimizationMetrics',
    'OptimizationEngine', 'OptimizationContext',
    
    # Algorithms
    'GeneticAlgorithm', 'SimulatedAnnealing', 'ParticleSwarmOptimization',
    'GradientBasedOptimizer', 'HybridOptimizer',
    
    # Constraint solvers
    'ConstraintSatisfactionSolver', 'LinearProgrammingSolver',
    'NonlinearProgrammingSolver', 'MixedIntegerSolver',
    
    # Multi-objective
    'MultiObjectiveOptimizer', 'ParetoFrontier', 'ObjectiveWeighting',
    'TradeoffAnalysis',
    
    # Design exploration
    'DesignSpaceExplorer', 'SensitivityAnalyzer', 'ParametricDesign',
    'OptimizationInsights',
    
    # Conflict resolution
    'OptimizationBasedResolver',
    
    # Analytics
    'OptimizationDashboard', 'OptimizationVisualizer'
]

__version__ = "3.0.0"