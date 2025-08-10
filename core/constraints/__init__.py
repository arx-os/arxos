"""
Arxos Constraint System.

Advanced constraint system for Building-Infrastructure-as-Code that enables
intelligent design validation, code compliance checking, and automated
conflict resolution through declarative constraint rules.
"""

__version__ = "2.0.0"
__author__ = "Arxos BIM Team"

from .constraint_core import (
    Constraint, ConstraintType, ConstraintSeverity, ConstraintScope,
    ConstraintResult, ConstraintViolation
)
from .constraint_engine import ConstraintEngine, ConstraintEvaluationContext
from .spatial_constraints import (
    SpatialConstraintValidator, DistanceConstraint, ClearanceConstraint,
    AlignmentConstraint, ContainmentConstraint
)
from .code_constraints import (
    BuildingCodeConstraint, FireSafetyConstraint, AccessibilityConstraint,
    ElectricalCodeConstraint, MechanicalCodeConstraint
)
from .system_constraints import (
    SystemConstraint, InterdependencyConstraint, CapacityConstraint,
    SequenceConstraint, CompatibilityConstraint
)
from .constraint_reporter import ConstraintReporter, ConstraintReport
from .integrated_validator import IntegratedValidator, UnifiedValidationResult

__all__ = [
    # Core constraint system
    'Constraint',
    'ConstraintType', 
    'ConstraintSeverity',
    'ConstraintScope',
    'ConstraintResult',
    'ConstraintViolation',
    
    # Constraint engine
    'ConstraintEngine',
    'ConstraintEvaluationContext',
    
    # Spatial constraints
    'SpatialConstraintValidator',
    'DistanceConstraint',
    'ClearanceConstraint', 
    'AlignmentConstraint',
    'ContainmentConstraint',
    
    # Code constraints
    'BuildingCodeConstraint',
    'FireSafetyConstraint',
    'AccessibilityConstraint',
    'ElectricalCodeConstraint',
    'MechanicalCodeConstraint',
    
    # System constraints
    'SystemConstraint',
    'InterdependencyConstraint',
    'CapacityConstraint',
    'SequenceConstraint',
    'CompatibilityConstraint',
    
    # Reporting
    'ConstraintReporter',
    'ConstraintReport',
    
    # Integrated validation
    'IntegratedValidator',
    'UnifiedValidationResult'
]