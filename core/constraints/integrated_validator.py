"""
Integrated Constraint and Conflict Validation System.

Combines Phase 1 conflict detection with Phase 2 constraint validation
for unified Building-Infrastructure-as-Code validation and reporting.
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Set, Union, Tuple
from dataclasses import dataclass

# Import Phase 1 foundation
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.spatial import SpatialConflictEngine, ArxObject, ArxObjectType, BoundingBox3D
from core.spatial.spatial_conflict_engine import ConflictReport
from .constraint_engine import ConstraintEngine, ConstraintEvaluationContext
from .constraint_core import ConstraintResult, ConstraintViolation, ConstraintSeverity
from .constraint_reporter import ConstraintReporter, ConstraintReport

logger = logging.getLogger(__name__)


@dataclass
class UnifiedValidationResult:
    """
    Unified result combining conflicts and constraint violations.
    
    Provides comprehensive validation status for Building-Infrastructure-as-Code
    with integrated conflict detection and constraint compliance.
    """
    
    # Validation metadata
    validation_id: str
    project_name: str
    validated_at: float
    validation_scope: str = "comprehensive"
    
    # Objects validated
    total_objects: int = 0
    objects_with_issues: int = 0
    
    # Conflict detection results
    spatial_conflicts: List[ConflictReport] = None
    conflict_count: int = 0
    
    # Constraint validation results
    constraint_results: List[ConstraintResult] = None
    constraint_violations: int = 0
    
    # Unified metrics
    overall_compliance_score: float = 0.0
    critical_issues_count: int = 0
    validation_time_ms: float = 0.0
    
    # Integrated recommendations
    immediate_actions: List[str] = None
    optimization_opportunities: List[str] = None


class IntegratedValidator:
    """
    Integrated constraint and conflict validation system.
    
    Combines Phase 1 spatial conflict detection with Phase 2 constraint
    validation for comprehensive Building-Infrastructure-as-Code validation.
    """
    
    def __init__(self, 
                 spatial_engine: SpatialConflictEngine,
                 project_name: str = "Arxos BIM Project"):
        """
        Initialize integrated validator.
        
        Args:
            spatial_engine: Phase 1 spatial conflict engine
            project_name: Project name for reporting
        """
        self.spatial_engine = spatial_engine
        self.project_name = project_name
        
        # Initialize constraint system
        self.constraint_engine = ConstraintEngine(spatial_engine)
        self.constraint_reporter = ConstraintReporter(project_name)
        
        # Load standard constraints
        self._initialize_standard_constraints()
        
        # Validation metrics
        self.validations_performed = 0
        self.total_validation_time_ms = 0.0
        
        logger.info(f"Initialized IntegratedValidator for project: {project_name}")
    
    def _initialize_standard_constraints(self) -> None:
        """Initialize standard building constraints."""
        
        # Import constraint types
        from .spatial_constraints import (
            DistanceConstraint, ClearanceConstraint, AlignmentConstraint
        )
        from .code_constraints import (
            FireSafetyConstraint, AccessibilityConstraint, ElectricalCodeConstraint
        )
        from .system_constraints import (
            InterdependencyConstraint, CapacityConstraint
        )
        
        # Standard spatial constraints
        self.constraint_engine.register_constraint(
            DistanceConstraint(
                name="Fire Sprinkler Spacing",
                distance_type="maximum",
                required_distance=15.0,
                measurement_method="center_to_center"
            )
        )
        
        self.constraint_engine.register_constraint(
            ClearanceConstraint(
                name="Electrical Panel Clearance",
                required_clearance=3.0,
                clearance_direction="front"
            )
        )
        
        self.constraint_engine.register_constraint(
            AlignmentConstraint(
                name="Outlet Alignment",
                alignment_type="horizontal",
                alignment_tolerance=0.5
            )
        )
        
        # Standard code constraints
        self.constraint_engine.register_constraint(
            FireSafetyConstraint(
                name="Fire Sprinkler Coverage",
                safety_requirement="sprinkler_spacing"
            )
        )
        
        self.constraint_engine.register_constraint(
            AccessibilityConstraint(
                name="ADA Door Clearance",
                accessibility_requirement="door_clearance"
            )
        )
        
        self.constraint_engine.register_constraint(
            ElectricalCodeConstraint(
                name="Electrical Panel Working Space",
                electrical_requirement="panel_clearance"
            )
        )
        
        # Standard system constraints
        self.constraint_engine.register_constraint(
            InterdependencyConstraint(
                name="Electrical Circuit Dependencies",
                dependency_type="electrical_circuit"
            )
        )
        
        self.constraint_engine.register_constraint(
            CapacityConstraint(
                name="Electrical Panel Capacity",
                capacity_type="electrical_load"
            )
        )
        
        logger.info(f"Initialized {len(self.constraint_engine.constraints)} standard constraints")
    
    async def validate_comprehensive(self, 
                                   spatial_bounds: Optional[BoundingBox3D] = None,
                                   include_conflicts: bool = True,
                                   include_constraints: bool = True) -> UnifiedValidationResult:
        """
        Perform comprehensive validation including conflicts and constraints.
        
        Args:
            spatial_bounds: Optional bounds to limit validation scope
            include_conflicts: Include spatial conflict detection
            include_constraints: Include constraint validation
            
        Returns:
            UnifiedValidationResult with comprehensive analysis
        """
        start_time = time.time()
        
        validation_id = f"validation_{int(time.time())}"
        
        # Get objects to validate
        if spatial_bounds:
            target_objects = self.spatial_engine.octree.query_range(spatial_bounds)
            validation_scope = f"spatial_bounds_{spatial_bounds.min_x}_{spatial_bounds.max_x}"
        else:
            target_objects = list(self.spatial_engine.objects.values())
            validation_scope = "comprehensive"
        
        logger.info(f"Starting comprehensive validation of {len(target_objects)} objects")
        
        # Initialize result
        result = UnifiedValidationResult(
            validation_id=validation_id,
            project_name=self.project_name,
            validated_at=time.time(),
            validation_scope=validation_scope,
            total_objects=len(target_objects),
            spatial_conflicts=[],
            constraint_results=[],
            immediate_actions=[],
            optimization_opportunities=[]
        )
        
        # Run conflict detection
        if include_conflicts and target_objects:
            logger.debug("Running spatial conflict detection...")
            conflict_start = time.time()
            
            conflicts = []
            for obj in target_objects:
                obj_conflicts = self.spatial_engine.detect_conflicts(obj)
                conflicts.extend(obj_conflicts)
            
            result.spatial_conflicts = conflicts
            result.conflict_count = len(conflicts)
            
            logger.debug(f"Detected {len(conflicts)} spatial conflicts in {(time.time() - conflict_start) * 1000:.1f}ms")
        
        # Run constraint validation
        if include_constraints and target_objects:
            logger.debug("Running constraint validation...")
            constraint_start = time.time()
            
            # Create evaluation context
            context = ConstraintEvaluationContext(
                spatial_engine=self.spatial_engine,
                spatial_bounds=spatial_bounds
            )
            
            # Run constraint evaluation in parallel
            constraint_results = await self.constraint_engine.evaluate_constraints_async(
                target_objects, context=context
            )
            
            result.constraint_results = constraint_results
            result.constraint_violations = sum(len(r.violations) for r in constraint_results)
            
            logger.debug(f"Found {result.constraint_violations} constraint violations in {(time.time() - constraint_start) * 1000:.1f}ms")
        
        # Calculate unified metrics
        self._calculate_unified_metrics(result)
        
        # Generate integrated recommendations
        self._generate_integrated_recommendations(result)
        
        # Update performance metrics
        result.validation_time_ms = (time.time() - start_time) * 1000
        self.validations_performed += 1
        self.total_validation_time_ms += result.validation_time_ms
        
        logger.info(f"Comprehensive validation completed: {result.overall_compliance_score:.1%} compliance, "
                   f"{result.critical_issues_count} critical issues, {result.validation_time_ms:.1f}ms")
        
        return result
    
    def validate_object(self, arxobject: ArxObject) -> UnifiedValidationResult:
        """
        Validate single object for conflicts and constraint violations.
        
        Args:
            arxobject: Object to validate
            
        Returns:
            UnifiedValidationResult for single object
        """
        start_time = time.time()
        
        validation_id = f"object_{arxobject.id}_{int(time.time())}"
        
        result = UnifiedValidationResult(
            validation_id=validation_id,
            project_name=self.project_name,
            validated_at=time.time(),
            validation_scope=f"object_{arxobject.id}",
            total_objects=1,
            spatial_conflicts=[],
            constraint_results=[],
            immediate_actions=[],
            optimization_opportunities=[]
        )
        
        # Check conflicts for this object
        conflicts = self.spatial_engine.detect_conflicts(arxobject)
        result.spatial_conflicts = conflicts
        result.conflict_count = len(conflicts)
        
        # Check constraints for this object
        constraint_results = self.constraint_engine.evaluate_object_constraints(arxobject)
        result.constraint_results = constraint_results
        result.constraint_violations = sum(len(r.violations) for r in constraint_results)
        
        # Calculate metrics
        self._calculate_unified_metrics(result)
        
        # Generate recommendations
        self._generate_integrated_recommendations(result)
        
        result.validation_time_ms = (time.time() - start_time) * 1000
        
        return result
    
    def validate_system(self, system_type: ArxObjectType) -> UnifiedValidationResult:
        """
        Validate entire building system.
        
        Args:
            system_type: Building system to validate
            
        Returns:
            UnifiedValidationResult for system
        """
        start_time = time.time()
        
        # Get all objects of system type
        system_objects = [
            obj for obj in self.spatial_engine.objects.values()
            if obj.type == system_type
        ]
        
        if not system_objects:
            logger.warning(f"No objects found for system type: {system_type.value}")
            return UnifiedValidationResult(
                validation_id=f"system_{system_type.value}_{int(time.time())}",
                project_name=self.project_name,
                validated_at=time.time(),
                validation_scope=f"system_{system_type.value}",
                total_objects=0
            )
        
        validation_id = f"system_{system_type.value}_{int(time.time())}"
        
        result = UnifiedValidationResult(
            validation_id=validation_id,
            project_name=self.project_name,
            validated_at=time.time(),
            validation_scope=f"system_{system_type.value}",
            total_objects=len(system_objects),
            spatial_conflicts=[],
            constraint_results=[],
            immediate_actions=[],
            optimization_opportunities=[]
        )
        
        # Check conflicts for system objects
        conflicts = []
        for obj in system_objects:
            obj_conflicts = self.spatial_engine.detect_conflicts(obj)
            conflicts.extend(obj_conflicts)
        
        result.spatial_conflicts = conflicts
        result.conflict_count = len(conflicts)
        
        # Check system-specific constraints
        constraint_results = self.constraint_engine.evaluate_system_constraints(system_type)
        
        # Also check object-level constraints
        for obj in system_objects:
            obj_constraints = self.constraint_engine.evaluate_object_constraints(obj)
            constraint_results.extend(obj_constraints)
        
        result.constraint_results = constraint_results
        result.constraint_violations = sum(len(r.violations) for r in constraint_results)
        
        # Calculate metrics
        self._calculate_unified_metrics(result)
        
        # Generate recommendations  
        self._generate_integrated_recommendations(result)
        
        result.validation_time_ms = (time.time() - start_time) * 1000
        
        logger.info(f"System validation ({system_type.value}): {len(system_objects)} objects, "
                   f"{result.conflict_count} conflicts, {result.constraint_violations} violations")
        
        return result
    
    def _calculate_unified_metrics(self, result: UnifiedValidationResult) -> None:
        """Calculate unified validation metrics."""
        
        if result.total_objects == 0:
            result.overall_compliance_score = 1.0
            return
        
        # Count critical issues
        critical_conflicts = sum(1 for conflict in result.spatial_conflicts 
                               if conflict.severity == "high")
        
        critical_violations = 0
        error_violations = 0
        
        for constraint_result in result.constraint_results:
            for violation in constraint_result.violations:
                if violation.severity == ConstraintSeverity.CRITICAL:
                    critical_violations += 1
                elif violation.severity == ConstraintSeverity.ERROR:
                    error_violations += 1
        
        result.critical_issues_count = critical_conflicts + critical_violations
        
        # Calculate overall compliance score
        total_issues = result.conflict_count + result.constraint_violations
        
        if total_issues == 0:
            result.overall_compliance_score = 1.0
        else:
            # Weight critical issues more heavily
            weighted_issues = (critical_conflicts * 3 + 
                             critical_violations * 3 + 
                             error_violations * 2 + 
                             (total_issues - critical_conflicts - critical_violations - error_violations))
            
            # Scale against total objects (simplified scoring)
            max_possible_issues = result.total_objects * 5  # Assume max 5 issues per object
            compliance = max(0.0, 1.0 - (weighted_issues / max_possible_issues))
            result.overall_compliance_score = compliance
        
        # Count objects with issues
        objects_with_issues = set()
        
        for conflict in result.spatial_conflicts:
            objects_with_issues.add(conflict.object1_id)
            objects_with_issues.add(conflict.object2_id)
        
        for constraint_result in result.constraint_results:
            for violation in constraint_result.violations:
                if violation.primary_object_id:
                    objects_with_issues.add(violation.primary_object_id)
                objects_with_issues.update(violation.secondary_object_ids)
        
        result.objects_with_issues = len(objects_with_issues)
    
    def _generate_integrated_recommendations(self, result: UnifiedValidationResult) -> None:
        """Generate integrated recommendations combining conflicts and constraints."""
        
        # Immediate actions for critical issues
        if result.critical_issues_count > 0:
            result.immediate_actions.append(
                f"CRITICAL: Address {result.critical_issues_count} critical safety/structural issues immediately"
            )
        
        # Spatial conflicts
        if result.conflict_count > 0:
            high_severity_conflicts = sum(1 for c in result.spatial_conflicts if c.severity == "high")
            if high_severity_conflicts > 0:
                result.immediate_actions.append(
                    f"HIGH: Resolve {high_severity_conflicts} high-severity spatial conflicts"
                )
            
            result.optimization_opportunities.append(
                f"Optimize spatial layout to reduce {result.conflict_count} total conflicts"
            )
        
        # Constraint violations
        if result.constraint_violations > 0:
            error_violations = 0
            warning_violations = 0
            
            for constraint_result in result.constraint_results:
                for violation in constraint_result.violations:
                    if violation.severity == ConstraintSeverity.ERROR:
                        error_violations += 1
                    elif violation.severity == ConstraintSeverity.WARNING:
                        warning_violations += 1
            
            if error_violations > 0:
                result.immediate_actions.append(
                    f"HIGH: Fix {error_violations} code compliance violations"
                )
            
            if warning_violations > 0:
                result.optimization_opportunities.append(
                    f"Address {warning_violations} design optimization opportunities"
                )
        
        # System-specific recommendations
        if result.overall_compliance_score < 0.8:
            result.optimization_opportunities.append(
                f"Improve overall compliance score from {result.overall_compliance_score:.1%} to >80%"
            )
        
        if result.objects_with_issues > 0:
            affected_percentage = (result.objects_with_issues / result.total_objects) * 100
            if affected_percentage > 20:
                result.immediate_actions.append(
                    f"MEDIUM: {affected_percentage:.0f}% of objects have issues - review design systematically"
                )
    
    def generate_unified_report(self, validation_result: UnifiedValidationResult) -> ConstraintReport:
        """
        Generate unified report combining conflicts and constraints.
        
        Args:
            validation_result: Unified validation result
            
        Returns:
            ConstraintReport with integrated analysis
        """
        # Convert conflicts to constraint violations for unified reporting
        conflict_results = []
        
        for conflict in validation_result.spatial_conflicts:
            # Create constraint result for conflict
            conflict_violation = ConstraintViolation(
                constraint_id="spatial_conflict",
                constraint_name="Spatial Conflict Detection",
                severity=ConstraintSeverity.ERROR if conflict.severity == "high" else ConstraintSeverity.WARNING,
                description=f"Spatial conflict: {conflict.conflict_type.value} - {conflict.description}",
                primary_object_id=conflict.object1_id,
                secondary_object_ids=[conflict.object2_id],
                technical_details={
                    'conflict_type': conflict.conflict_type.value,
                    'distance': conflict.distance,
                    'severity': conflict.severity
                },
                suggested_fixes=[conflict.resolution_strategy] if conflict.resolution_strategy else []
            )
            
            conflict_result = ConstraintResult(
                constraint_id="spatial_conflict",
                constraint_name="Spatial Conflict Detection",
                is_satisfied=False,
                evaluation_time_ms=0.0,
                violations=[conflict_violation]
            )
            
            conflict_results.append(conflict_result)
        
        # Combine constraint results
        all_results = validation_result.constraint_results + conflict_results
        
        # Generate comprehensive report
        report = self.constraint_reporter.generate_comprehensive_report(
            all_results, 
            report_type="unified_validation"
        )
        
        # Add validation-specific metrics
        report.project_name = validation_result.project_name
        report.total_objects_analyzed = validation_result.total_objects
        
        return report
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of validation system status."""
        
        constraint_summary = self.constraint_engine.get_constraint_summary()
        
        return {
            'project_name': self.project_name,
            'validations_performed': self.validations_performed,
            'average_validation_time_ms': (
                self.total_validation_time_ms / self.validations_performed
                if self.validations_performed > 0 else 0
            ),
            'spatial_engine': {
                'total_objects': len(self.spatial_engine.objects),
                'octree_bounds': {
                    'min_x': self.spatial_engine.world_bounds.min_x,
                    'max_x': self.spatial_engine.world_bounds.max_x,
                    'min_y': self.spatial_engine.world_bounds.min_y,
                    'max_y': self.spatial_engine.world_bounds.max_y,
                    'min_z': self.spatial_engine.world_bounds.min_z,
                    'max_z': self.spatial_engine.world_bounds.max_z
                }
            },
            'constraint_engine': constraint_summary,
            'reports_generated': self.constraint_reporter.reports_generated
        }


logger.info("Integrated constraint and conflict validation system initialized")