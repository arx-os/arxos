"""
SVGX Engine Core Module

Core functionality for CAD primitives, constraints, and precision management.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

from .precision import (
    precision_manager,
    PrecisionManager,
    PrecisionConfig,
    PrecisionLevel,
    PrecisionDisplayMode,
    PrecisionValidator,
)

from .primitives import Line, Arc, Circle, Rectangle, Polyline

from .constraints import (
    Constraint,
    ParallelConstraint,
    PerpendicularConstraint,
    EqualConstraint,
    FixedConstraint,
    ConstraintType,
)

__all__ = [
    # Precision management
    "precision_manager",
    "PrecisionManager",
    "PrecisionConfig",
    "PrecisionLevel",
    "PrecisionDisplayMode",
    "PrecisionValidator",
    # CAD primitives
    "Line",
    "Arc",
    "Circle",
    "Rectangle",
    "Polyline",
    # Constraints
    "Constraint",
    "ParallelConstraint",
    "PerpendicularConstraint",
    "EqualConstraint",
    "FixedConstraint",
    "ConstraintType",
]
