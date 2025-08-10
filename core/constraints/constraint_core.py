"""
Core Constraint System Architecture.

Defines the fundamental constraint types, evaluation framework, and
violation detection system for Building-Infrastructure-as-Code.
"""

import uuid
import time
import logging
from typing import Dict, Any, List, Optional, Set, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import json
from datetime import datetime, timezone

# Import Phase 1 foundation
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.spatial import ArxObject, ArxObjectType, BoundingBox3D

logger = logging.getLogger(__name__)


class ConstraintType(Enum):
    """Types of constraints in the system."""
    
    # Spatial constraints
    SPATIAL_DISTANCE = "spatial_distance"
    SPATIAL_CLEARANCE = "spatial_clearance" 
    SPATIAL_ALIGNMENT = "spatial_alignment"
    SPATIAL_CONTAINMENT = "spatial_containment"
    SPATIAL_ADJACENCY = "spatial_adjacency"
    
    # Building code constraints
    CODE_FIRE_SAFETY = "code_fire_safety"
    CODE_ACCESSIBILITY = "code_accessibility"
    CODE_STRUCTURAL = "code_structural"
    CODE_ELECTRICAL = "code_electrical"
    CODE_MECHANICAL = "code_mechanical"
    CODE_PLUMBING = "code_plumbing"
    
    # System constraints
    SYSTEM_CAPACITY = "system_capacity"
    SYSTEM_INTERDEPENDENCY = "system_interdependency"
    SYSTEM_SEQUENCE = "system_sequence"
    SYSTEM_COMPATIBILITY = "system_compatibility"
    
    # Performance constraints
    PERFORMANCE_ENERGY = "performance_energy"
    PERFORMANCE_STRUCTURAL = "performance_structural"
    PERFORMANCE_THERMAL = "performance_thermal"
    
    # Custom constraints
    CUSTOM_BUSINESS_RULE = "custom_business_rule"
    CUSTOM_DESIGN_PATTERN = "custom_design_pattern"


class ConstraintSeverity(Enum):
    """Severity levels for constraint violations."""
    
    CRITICAL = "critical"      # System unsafe, must fix immediately
    ERROR = "error"           # Code violation, must fix before approval
    WARNING = "warning"       # Best practice violation, should fix
    INFO = "info"            # Informational, optimization opportunity
    SUGGESTION = "suggestion" # Design improvement suggestion


class ConstraintScope(Enum):
    """Scope of constraint application."""
    
    GLOBAL = "global"         # Applies to entire building/project
    SYSTEM = "system"         # Applies to specific building system
    ZONE = "zone"            # Applies to spatial zone/area
    OBJECT = "object"        # Applies to individual ArxObject
    RELATIONSHIP = "relationship"  # Applies to object relationships


@dataclass
class ConstraintViolation:
    """Represents a constraint violation with details."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    constraint_id: str = ""
    constraint_name: str = ""
    severity: ConstraintSeverity = ConstraintSeverity.ERROR
    
    # Violation details
    description: str = ""
    message: str = ""
    technical_details: Dict[str, Any] = field(default_factory=dict)
    
    # Affected objects
    primary_object_id: Optional[str] = None
    secondary_object_ids: List[str] = field(default_factory=list)
    affected_systems: List[str] = field(default_factory=list)
    
    # Spatial information
    location: Optional[Tuple[float, float, float]] = None
    bounding_box: Optional[BoundingBox3D] = None
    
    # Resolution information
    suggested_fixes: List[str] = field(default_factory=list)
    estimated_fix_cost: Optional[float] = None
    estimated_fix_time: Optional[int] = None  # hours
    
    # Metadata
    detected_at: float = field(default_factory=time.time)
    detected_by: str = "constraint_engine"
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert violation to dictionary."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, ConstraintSeverity):
                result[key] = value.value
            elif isinstance(value, BoundingBox3D):
                result[key] = {
                    'min_x': value.min_x, 'max_x': value.max_x,
                    'min_y': value.min_y, 'max_y': value.max_y,
                    'min_z': value.min_z, 'max_z': value.max_z
                }
            else:
                result[key] = value
        return result
    
    def get_display_message(self) -> str:
        """Get human-readable violation message."""
        if self.message:
            return self.message
        
        severity_icon = {
            ConstraintSeverity.CRITICAL: "🔴",
            ConstraintSeverity.ERROR: "❌", 
            ConstraintSeverity.WARNING: "⚠️",
            ConstraintSeverity.INFO: "ℹ️",
            ConstraintSeverity.SUGGESTION: "💡"
        }
        
        icon = severity_icon.get(self.severity, "")
        return f"{icon} {self.severity.value.upper()}: {self.description}"


@dataclass
class ConstraintResult:
    """Result of constraint evaluation."""
    
    constraint_id: str
    constraint_name: str
    is_satisfied: bool
    evaluation_time_ms: float
    
    # Violations (empty if satisfied)
    violations: List[ConstraintViolation] = field(default_factory=list)
    
    # Evaluation context
    evaluated_objects: List[str] = field(default_factory=list)
    evaluation_method: str = ""
    
    # Performance metrics
    objects_checked: int = 0
    rules_evaluated: int = 0
    
    # Additional details
    details: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    
    def add_violation(self, violation: ConstraintViolation) -> None:
        """Add violation to result."""
        self.violations.append(violation)
        self.is_satisfied = False
    
    def get_severity_counts(self) -> Dict[ConstraintSeverity, int]:
        """Get count of violations by severity."""
        counts = {severity: 0 for severity in ConstraintSeverity}
        for violation in self.violations:
            counts[violation.severity] += 1
        return counts


class Constraint(ABC):
    """
    Abstract base class for all constraints.
    
    Defines the interface that all constraints must implement for
    evaluation, violation detection, and integration with the constraint engine.
    """
    
    def __init__(self,
                 constraint_id: Optional[str] = None,
                 name: str = "",
                 description: str = "",
                 constraint_type: ConstraintType = ConstraintType.CUSTOM_BUSINESS_RULE,
                 severity: ConstraintSeverity = ConstraintSeverity.ERROR,
                 scope: ConstraintScope = ConstraintScope.OBJECT,
                 enabled: bool = True):
        """
        Initialize constraint.
        
        Args:
            constraint_id: Unique identifier
            name: Human-readable constraint name
            description: Detailed description
            constraint_type: Type of constraint
            severity: Default severity for violations
            scope: Scope of constraint application
            enabled: Whether constraint is active
        """
        self.constraint_id = constraint_id or str(uuid.uuid4())
        self.name = name or self.__class__.__name__
        self.description = description
        self.constraint_type = constraint_type
        self.severity = severity
        self.scope = scope
        self.enabled = enabled
        
        # Constraint configuration
        self.parameters: Dict[str, Any] = {}
        self.conditions: Dict[str, Any] = {}
        
        # Performance tracking
        self.evaluation_count = 0
        self.total_evaluation_time_ms = 0.0
        self.violation_count = 0
        
        # Metadata
        self.created_at = time.time()
        self.created_by = "system"
        self.tags: List[str] = []
        self.version = "1.0.0"
        
        logger.debug(f"Created constraint: {self.name} ({self.constraint_type.value})")
    
    @abstractmethod
    def evaluate(self, 
                context: 'ConstraintEvaluationContext',
                target_objects: List[ArxObject]) -> ConstraintResult:
        """
        Evaluate constraint against target objects.
        
        Args:
            context: Evaluation context with spatial engine, etc.
            target_objects: Objects to evaluate constraint against
            
        Returns:
            ConstraintResult with violations if any
        """
        pass
    
    @abstractmethod
    def is_applicable(self, arxobject: ArxObject) -> bool:
        """
        Check if constraint applies to given object.
        
        Args:
            arxobject: Object to check applicability
            
        Returns:
            True if constraint should be evaluated for this object
        """
        pass
    
    def get_affected_systems(self) -> List[ArxObjectType]:
        """Get building systems affected by this constraint."""
        return []
    
    def get_spatial_requirements(self) -> Dict[str, Any]:
        """Get spatial requirements for constraint evaluation."""
        return {}
    
    def set_parameter(self, key: str, value: Any) -> None:
        """Set constraint parameter."""
        self.parameters[key] = value
    
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """Get constraint parameter."""
        return self.parameters.get(key, default)
    
    def add_condition(self, key: str, condition: Any) -> None:
        """Add evaluation condition."""
        self.conditions[key] = condition
    
    def update_performance_metrics(self, evaluation_time_ms: float, violation_count: int) -> None:
        """Update performance tracking metrics."""
        self.evaluation_count += 1
        self.total_evaluation_time_ms += evaluation_time_ms
        self.violation_count += violation_count
    
    def get_average_evaluation_time(self) -> float:
        """Get average evaluation time in milliseconds."""
        if self.evaluation_count == 0:
            return 0.0
        return self.total_evaluation_time_ms / self.evaluation_count
    
    def create_violation(self,
                        description: str,
                        primary_object: Optional[ArxObject] = None,
                        secondary_objects: Optional[List[ArxObject]] = None,
                        severity: Optional[ConstraintSeverity] = None,
                        suggested_fixes: Optional[List[str]] = None,
                        technical_details: Optional[Dict[str, Any]] = None) -> ConstraintViolation:
        """
        Create constraint violation with standard fields populated.
        
        Args:
            description: Violation description
            primary_object: Primary object involved in violation
            secondary_objects: Additional objects involved
            severity: Override default severity
            suggested_fixes: List of suggested fixes
            technical_details: Technical details about violation
            
        Returns:
            ConstraintViolation instance
        """
        violation = ConstraintViolation(
            constraint_id=self.constraint_id,
            constraint_name=self.name,
            severity=severity or self.severity,
            description=description,
            technical_details=technical_details or {},
            suggested_fixes=suggested_fixes or []
        )
        
        if primary_object:
            violation.primary_object_id = primary_object.id
            violation.location = (primary_object.geometry.x, primary_object.geometry.y, primary_object.geometry.z)
            violation.bounding_box = primary_object.get_bounding_box()
            violation.affected_systems = [primary_object.type.value]
        
        if secondary_objects:
            violation.secondary_object_ids = [obj.id for obj in secondary_objects]
            violation.affected_systems.extend([obj.type.value for obj in secondary_objects])
        
        return violation
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert constraint to dictionary representation."""
        return {
            'constraint_id': self.constraint_id,
            'name': self.name,
            'description': self.description,
            'constraint_type': self.constraint_type.value,
            'severity': self.severity.value,
            'scope': self.scope.value,
            'enabled': self.enabled,
            'parameters': self.parameters,
            'conditions': self.conditions,
            'performance_metrics': {
                'evaluation_count': self.evaluation_count,
                'average_evaluation_time_ms': self.get_average_evaluation_time(),
                'violation_count': self.violation_count
            },
            'metadata': {
                'created_at': self.created_at,
                'created_by': self.created_by,
                'tags': self.tags,
                'version': self.version
            }
        }
    
    def __str__(self) -> str:
        """String representation of constraint."""
        return f"Constraint({self.name}, {self.constraint_type.value}, {self.severity.value})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"Constraint(id='{self.constraint_id}', name='{self.name}', "
                f"type={self.constraint_type.value}, severity={self.severity.value}, "
                f"enabled={self.enabled})")


class ParametricConstraint(Constraint):
    """
    Base class for parametric constraints with configurable thresholds.
    
    Provides common functionality for constraints that use numeric parameters
    and threshold-based evaluation.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Default parametric constraint parameters
        self.set_parameter('tolerance', 0.01)  # Default tolerance
        self.set_parameter('check_enabled', True)
        
    def check_numeric_threshold(self, 
                               actual_value: float,
                               expected_value: float,
                               threshold_type: str = 'min',
                               tolerance: Optional[float] = None) -> Tuple[bool, float]:
        """
        Check numeric value against threshold.
        
        Args:
            actual_value: Actual measured value
            expected_value: Expected/required value
            threshold_type: 'min', 'max', 'exact', or 'range'
            tolerance: Tolerance for comparison
            
        Returns:
            Tuple of (is_satisfied, difference)
        """
        tolerance = tolerance or self.get_parameter('tolerance', 0.01)
        
        if threshold_type == 'min':
            is_satisfied = actual_value >= (expected_value - tolerance)
            difference = expected_value - actual_value
        elif threshold_type == 'max':
            is_satisfied = actual_value <= (expected_value + tolerance)
            difference = actual_value - expected_value
        elif threshold_type == 'exact':
            difference = abs(actual_value - expected_value)
            is_satisfied = difference <= tolerance
        else:  # range - expected_value should be tuple (min, max)
            if isinstance(expected_value, (list, tuple)) and len(expected_value) == 2:
                min_val, max_val = expected_value
                is_satisfied = (min_val - tolerance) <= actual_value <= (max_val + tolerance)
                difference = min(abs(actual_value - min_val), abs(actual_value - max_val))
            else:
                raise ValueError("Range threshold requires expected_value as (min, max) tuple")
        
        return is_satisfied, difference
    
    def format_measurement_message(self,
                                  measurement_name: str,
                                  actual_value: float,
                                  expected_value: Union[float, Tuple[float, float]],
                                  units: str = "",
                                  threshold_type: str = 'min') -> str:
        """Format measurement violation message."""
        units_str = f" {units}" if units else ""
        
        if threshold_type == 'min':
            return f"{measurement_name}: {actual_value:.2f}{units_str} (required: ≥{expected_value:.2f}{units_str})"
        elif threshold_type == 'max':
            return f"{measurement_name}: {actual_value:.2f}{units_str} (required: ≤{expected_value:.2f}{units_str})"
        elif threshold_type == 'exact':
            return f"{measurement_name}: {actual_value:.2f}{units_str} (required: {expected_value:.2f}{units_str})"
        else:  # range
            if isinstance(expected_value, (list, tuple)) and len(expected_value) == 2:
                min_val, max_val = expected_value
                return f"{measurement_name}: {actual_value:.2f}{units_str} (required: {min_val:.2f}-{max_val:.2f}{units_str})"
        
        return f"{measurement_name}: {actual_value:.2f}{units_str}"


# Standard constraint implementations will be in separate modules
logger.info("Core constraint system initialized")