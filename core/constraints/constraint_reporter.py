"""
Constraint Reporting and Visualization System.

Generates comprehensive constraint violation reports, analytics, and
visualizations for Building-Infrastructure-as-Code validation results.
"""

import time
import json
import logging
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from datetime import datetime, timezone
import csv
import io

# Import Phase 1 foundation
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.spatial import ArxObject, ArxObjectType, BoundingBox3D
from .constraint_core import (
    Constraint, ConstraintType, ConstraintSeverity, ConstraintScope,
    ConstraintResult, ConstraintViolation
)
from .constraint_engine import ConstraintEngine

logger = logging.getLogger(__name__)


@dataclass
class ConstraintReport:
    """
    Comprehensive constraint evaluation report.
    
    Contains aggregated results, analytics, and formatted output
    for constraint validation across building systems.
    """
    
    # Report metadata
    report_id: str = field(default_factory=lambda: f"report_{int(time.time())}")
    generated_at: float = field(default_factory=time.time)
    report_type: str = "comprehensive"
    project_name: str = ""
    
    # Evaluation results
    constraint_results: List[ConstraintResult] = field(default_factory=list)
    total_constraints_evaluated: int = 0
    total_objects_analyzed: int = 0
    
    # Violation summary
    total_violations: int = 0
    violations_by_severity: Dict[ConstraintSeverity, int] = field(default_factory=dict)
    violations_by_type: Dict[ConstraintType, int] = field(default_factory=dict)
    violations_by_system: Dict[ArxObjectType, int] = field(default_factory=dict)
    
    # Performance metrics
    total_evaluation_time_ms: float = 0.0
    average_constraint_time_ms: float = 0.0
    
    # Analytics
    compliance_score: float = 0.0  # 0.0 - 1.0
    system_health_scores: Dict[ArxObjectType, float] = field(default_factory=dict)
    critical_areas: List[Dict[str, Any]] = field(default_factory=list)
    
    # Recommendations
    priority_actions: List[str] = field(default_factory=list)
    system_recommendations: Dict[str, List[str]] = field(default_factory=dict)
    
    def add_constraint_result(self, result: ConstraintResult) -> None:
        """Add constraint result to report."""
        self.constraint_results.append(result)
        self.total_constraints_evaluated += 1
        self.total_objects_analyzed += len(result.evaluated_objects)
        self.total_evaluation_time_ms += result.evaluation_time_ms
        
        # Update violation counts
        for violation in result.violations:
            self.total_violations += 1
            
            # By severity
            if violation.severity not in self.violations_by_severity:
                self.violations_by_severity[violation.severity] = 0
            self.violations_by_severity[violation.severity] += 1
            
            # By constraint type
            constraint_type = ConstraintType(result.constraint_id.split('_')[0]) if '_' in result.constraint_id else None
            if constraint_type:
                if constraint_type not in self.violations_by_type:
                    self.violations_by_type[constraint_type] = 0
                self.violations_by_type[constraint_type] += 1
            
            # By affected systems
            for system_name in violation.affected_systems:
                try:
                    system_type = ArxObjectType(system_name)
                    if system_type not in self.violations_by_system:
                        self.violations_by_system[system_type] = 0
                    self.violations_by_system[system_type] += 1
                except ValueError:
                    pass  # Skip unknown system types
    
    def calculate_analytics(self) -> None:
        """Calculate report analytics and scores."""
        if self.total_constraints_evaluated == 0:
            return
        
        # Calculate compliance score
        satisfied_constraints = sum(1 for result in self.constraint_results if result.is_satisfied)
        self.compliance_score = satisfied_constraints / self.total_constraints_evaluated
        
        # Calculate average evaluation time
        self.average_constraint_time_ms = self.total_evaluation_time_ms / self.total_constraints_evaluated
        
        # Calculate system health scores
        self._calculate_system_health_scores()
        
        # Identify critical areas
        self._identify_critical_areas()
        
        # Generate recommendations
        self._generate_recommendations()
    
    def _calculate_system_health_scores(self) -> None:
        """Calculate health scores for each building system."""
        system_constraint_counts = defaultdict(int)
        system_violation_counts = defaultdict(int)
        
        for result in self.constraint_results:
            for violation in result.violations:
                for system_name in violation.affected_systems:
                    try:
                        system_type = ArxObjectType(system_name)
                        system_violation_counts[system_type] += 1
                    except ValueError:
                        pass
        
        # Count total constraints per system
        for result in self.constraint_results:
            # Estimate system involvement based on constraint type
            if result.constraint_id.startswith('electrical'):
                system_constraint_counts[ArxObjectType.ELECTRICAL_OUTLET] += 1
            elif result.constraint_id.startswith('hvac'):
                system_constraint_counts[ArxObjectType.HVAC_UNIT] += 1
            elif result.constraint_id.startswith('fire'):
                system_constraint_counts[ArxObjectType.FIRE_SPRINKLER] += 1
        
        # Calculate health scores (1.0 = perfect, 0.0 = critical)
        for system_type in system_constraint_counts:
            total_constraints = system_constraint_counts[system_type]
            violations = system_violation_counts.get(system_type, 0)
            
            if total_constraints > 0:
                health_score = max(0.0, 1.0 - (violations / total_constraints))
                self.system_health_scores[system_type] = health_score
    
    def _identify_critical_areas(self) -> None:
        """Identify critical areas requiring immediate attention."""
        critical_violations = []
        error_violations = []
        
        for result in self.constraint_results:
            for violation in result.violations:
                if violation.severity == ConstraintSeverity.CRITICAL:
                    critical_violations.append(violation)
                elif violation.severity == ConstraintSeverity.ERROR:
                    error_violations.append(violation)
        
        # Group violations by location/system
        location_violations = defaultdict(list)
        
        for violation in critical_violations + error_violations:
            if violation.location:
                # Round location to create zones
                zone_x = round(violation.location[0] / 10) * 10  # 10ft zones
                zone_y = round(violation.location[1] / 10) * 10
                zone_key = f"zone_{zone_x}_{zone_y}"
                location_violations[zone_key].append(violation)
        
        # Identify zones with multiple violations
        for zone, violations in location_violations.items():
            if len(violations) >= 3:  # 3 or more violations in same zone
                critical_area = {
                    'zone_id': zone,
                    'violation_count': len(violations),
                    'severity_breakdown': {
                        'critical': sum(1 for v in violations if v.severity == ConstraintSeverity.CRITICAL),
                        'error': sum(1 for v in violations if v.severity == ConstraintSeverity.ERROR)
                    },
                    'affected_systems': list(set(
                        system for violation in violations 
                        for system in violation.affected_systems
                    )),
                    'representative_violations': [v.description for v in violations[:3]]
                }
                
                self.critical_areas.append(critical_area)
        
        # Sort by violation count (descending)
        self.critical_areas.sort(key=lambda x: x['violation_count'], reverse=True)
    
    def _generate_recommendations(self) -> None:
        """Generate priority actions and system recommendations."""
        # Priority actions based on critical violations
        critical_count = self.violations_by_severity.get(ConstraintSeverity.CRITICAL, 0)
        error_count = self.violations_by_severity.get(ConstraintSeverity.ERROR, 0)
        
        if critical_count > 0:
            self.priority_actions.append(
                f"IMMEDIATE: Address {critical_count} critical safety violations"
            )
        
        if error_count > 0:
            self.priority_actions.append(
                f"HIGH: Resolve {error_count} code compliance violations"
            )
        
        if self.compliance_score < 0.7:
            self.priority_actions.append(
                f"MEDIUM: Improve overall compliance score ({self.compliance_score:.1%})"
            )
        
        # System-specific recommendations
        for system_type, health_score in self.system_health_scores.items():
            system_name = system_type.value.replace('_', ' ').title()
            recommendations = []
            
            if health_score < 0.5:
                recommendations.append(f"Critical: {system_name} system requires immediate review")
            elif health_score < 0.7:
                recommendations.append(f"High: {system_name} system needs attention")
            elif health_score < 0.9:
                recommendations.append(f"Medium: {system_name} system has minor issues")
            else:
                recommendations.append(f"Good: {system_name} system is compliant")
            
            violation_count = self.violations_by_system.get(system_type, 0)
            if violation_count > 0:
                recommendations.append(f"Address {violation_count} violations in {system_name}")
            
            self.system_recommendations[system_name] = recommendations
    
    def get_summary_dict(self) -> Dict[str, Any]:
        """Get report summary as dictionary."""
        return {
            'report_metadata': {
                'report_id': self.report_id,
                'generated_at': datetime.fromtimestamp(self.generated_at, timezone.utc).isoformat(),
                'project_name': self.project_name,
                'report_type': self.report_type
            },
            'evaluation_summary': {
                'constraints_evaluated': self.total_constraints_evaluated,
                'objects_analyzed': self.total_objects_analyzed,
                'total_violations': self.total_violations,
                'compliance_score': round(self.compliance_score, 3),
                'evaluation_time_ms': round(self.total_evaluation_time_ms, 1)
            },
            'violations_by_severity': {
                severity.value: count 
                for severity, count in self.violations_by_severity.items()
            },
            'violations_by_type': {
                constraint_type.value: count 
                for constraint_type, count in self.violations_by_type.items()
            },
            'system_health_scores': {
                system.value: round(score, 3)
                for system, score in self.system_health_scores.items()
            },
            'critical_areas': self.critical_areas,
            'priority_actions': self.priority_actions,
            'system_recommendations': self.system_recommendations
        }


class ConstraintReporter:
    """
    Constraint reporting and visualization system.
    
    Generates comprehensive reports, exports data, and provides
    analytics for constraint validation results.
    """
    
    def __init__(self, project_name: str = "Arxos BIM Project"):
        """Initialize constraint reporter."""
        self.project_name = project_name
        self.reports_generated = 0
        self.last_report: Optional[ConstraintReport] = None
        
        logger.info(f"Initialized ConstraintReporter for project: {project_name}")
    
    def generate_comprehensive_report(self, 
                                    constraint_results: List[ConstraintResult],
                                    report_type: str = "comprehensive") -> ConstraintReport:
        """
        Generate comprehensive constraint evaluation report.
        
        Args:
            constraint_results: List of constraint evaluation results
            report_type: Type of report to generate
            
        Returns:
            ConstraintReport with analysis and recommendations
        """
        start_time = time.time()
        
        report = ConstraintReport(
            project_name=self.project_name,
            report_type=report_type
        )
        
        # Add all constraint results
        for result in constraint_results:
            report.add_constraint_result(result)
        
        # Calculate analytics
        report.calculate_analytics()
        
        # Store as last report
        self.last_report = report
        self.reports_generated += 1
        
        generation_time = (time.time() - start_time) * 1000
        
        logger.info(f"Generated constraint report: {report.total_violations} violations, "
                   f"{report.compliance_score:.1%} compliance, {generation_time:.1f}ms")
        
        return report
    
    def generate_system_report(self, 
                              constraint_results: List[ConstraintResult],
                              target_system: ArxObjectType) -> ConstraintReport:
        """Generate system-specific constraint report."""
        
        # Filter results for target system
        system_results = []
        for result in constraint_results:
            # Check if result affects target system
            system_violations = [
                violation for violation in result.violations
                if target_system.value in violation.affected_systems
            ]
            
            if system_violations:
                # Create filtered result
                filtered_result = ConstraintResult(
                    constraint_id=result.constraint_id,
                    constraint_name=result.constraint_name,
                    is_satisfied=len(system_violations) == 0,
                    evaluation_time_ms=result.evaluation_time_ms,
                    violations=system_violations,
                    evaluated_objects=result.evaluated_objects,
                    evaluation_method=result.evaluation_method
                )
                system_results.append(filtered_result)
        
        return self.generate_comprehensive_report(
            system_results, 
            report_type=f"system_{target_system.value}"
        )
    
    def export_violations_csv(self, report: ConstraintReport) -> str:
        """Export violations to CSV format."""
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Violation ID', 'Constraint Name', 'Severity', 'Description',
            'Primary Object ID', 'Primary Object Type', 'Location X', 'Location Y', 'Location Z',
            'Secondary Objects', 'Affected Systems', 'Suggested Fixes'
        ])
        
        # Write violations
        for result in report.constraint_results:
            for violation in result.violations:
                location = violation.location or (0, 0, 0)
                secondary_objects = ', '.join(violation.secondary_object_ids)
                affected_systems = ', '.join(violation.affected_systems)
                suggested_fixes = '; '.join(violation.suggested_fixes)
                
                writer.writerow([
                    violation.id,
                    violation.constraint_name,
                    violation.severity.value,
                    violation.description,
                    violation.primary_object_id or '',
                    violation.affected_systems[0] if violation.affected_systems else '',
                    location[0], location[1], location[2],
                    secondary_objects,
                    affected_systems,
                    suggested_fixes
                ])
        
        return output.getvalue()
    
    def export_summary_json(self, report: ConstraintReport, pretty: bool = True) -> str:
        """Export report summary to JSON."""
        
        summary = report.get_summary_dict()
        
        if pretty:
            return json.dumps(summary, indent=2, default=str)
        else:
            return json.dumps(summary, default=str)
    
    def generate_text_summary(self, report: ConstraintReport) -> str:
        """Generate human-readable text summary."""
        
        lines = []
        lines.append("=" * 60)
        lines.append("ARXOS CONSTRAINT VALIDATION REPORT")
        lines.append("=" * 60)
        
        # Project info
        lines.append(f"Project: {report.project_name}")
        lines.append(f"Generated: {datetime.fromtimestamp(report.generated_at).strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Report ID: {report.report_id}")
        lines.append("")
        
        # Executive summary
        lines.append("EXECUTIVE SUMMARY")
        lines.append("-" * 20)
        lines.append(f"Compliance Score: {report.compliance_score:.1%}")
        lines.append(f"Total Violations: {report.total_violations}")
        lines.append(f"Constraints Evaluated: {report.total_constraints_evaluated}")
        lines.append(f"Objects Analyzed: {report.total_objects_analyzed}")
        lines.append("")
        
        # Violations by severity
        if report.violations_by_severity:
            lines.append("VIOLATIONS BY SEVERITY")
            lines.append("-" * 25)
            for severity in ConstraintSeverity:
                count = report.violations_by_severity.get(severity, 0)
                if count > 0:
                    icon = {"critical": "🔴", "error": "❌", "warning": "⚠️", "info": "ℹ️", "suggestion": "💡"}.get(severity.value, "•")
                    lines.append(f"{icon} {severity.value.upper()}: {count}")
            lines.append("")
        
        # System health scores
        if report.system_health_scores:
            lines.append("SYSTEM HEALTH SCORES")
            lines.append("-" * 20)
            for system_type, score in sorted(report.system_health_scores.items(), key=lambda x: x[1]):
                status_icon = "🟢" if score >= 0.9 else "🟡" if score >= 0.7 else "🔴"
                system_name = system_type.value.replace('_', ' ').title()
                lines.append(f"{status_icon} {system_name}: {score:.1%}")
            lines.append("")
        
        # Priority actions
        if report.priority_actions:
            lines.append("PRIORITY ACTIONS")
            lines.append("-" * 15)
            for i, action in enumerate(report.priority_actions, 1):
                lines.append(f"{i}. {action}")
            lines.append("")
        
        # Critical areas
        if report.critical_areas:
            lines.append("CRITICAL AREAS")
            lines.append("-" * 14)
            for area in report.critical_areas[:5]:  # Top 5 critical areas
                lines.append(f"Zone {area['zone_id']}: {area['violation_count']} violations")
                lines.append(f"   Systems: {', '.join(area['affected_systems'])}")
                if area['representative_violations']:
                    lines.append(f"   Examples: {area['representative_violations'][0]}")
                lines.append("")
        
        # Performance metrics
        lines.append("PERFORMANCE METRICS")
        lines.append("-" * 19)
        lines.append(f"Total Evaluation Time: {report.total_evaluation_time_ms:.1f}ms")
        lines.append(f"Average Per Constraint: {report.average_constraint_time_ms:.1f}ms")
        lines.append("")
        
        # Footer
        lines.append("=" * 60)
        lines.append("Report generated by Arxos Constraint System")
        lines.append("For detailed analysis, review individual violations")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def print_summary(self, report: ConstraintReport) -> None:
        """Print formatted report summary to console."""
        print(self.generate_text_summary(report))
    
    def get_violation_statistics(self, report: ConstraintReport) -> Dict[str, Any]:
        """Get detailed violation statistics."""
        
        violations = []
        for result in report.constraint_results:
            violations.extend(result.violations)
        
        # Most common violation types
        violation_types = Counter()
        for violation in violations:
            # Extract violation type from description
            violation_type = violation.description.split(':')[0].strip()
            violation_types[violation_type] += 1
        
        # Most affected objects
        object_violations = Counter()
        for violation in violations:
            if violation.primary_object_id:
                object_violations[violation.primary_object_id] += 1
        
        return {
            'total_violations': len(violations),
            'unique_objects_affected': len(object_violations),
            'most_common_types': dict(violation_types.most_common(10)),
            'most_affected_objects': dict(object_violations.most_common(10)),
            'average_fixes_per_violation': sum(len(v.suggested_fixes) for v in violations) / len(violations) if violations else 0,
            'violations_with_location': sum(1 for v in violations if v.location),
            'violations_with_fixes': sum(1 for v in violations if v.suggested_fixes)
        }


logger.info("Constraint reporting system initialized")