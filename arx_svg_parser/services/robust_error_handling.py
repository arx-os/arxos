"""
Robust Error Handling & Reporting System for SVG-BIM

This module provides comprehensive error handling including:
- Assembly warnings collection and reporting
- Recovery strategies for partial/incomplete data
- Structured error/warning output for UI/API consumption
- Fallback mechanisms for unknown types and missing data
- User-friendly error messages and recommendations
"""

import time
import json
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import traceback
import uuid

from utils.errors import (
    SVGParseError, BIMAssemblyError, GeometryError, RelationshipError,
    EnrichmentError, ValidationError, ExportError, APIError, UnknownBIMTypeError
)

logger = logging.getLogger(__name__)


class WarningLevel(Enum):
    """Warning severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RecoveryStrategy(Enum):
    """Recovery strategy types."""
    SKIP = "skip"
    FALLBACK = "fallback"
    RETRY = "retry"
    DEFAULT = "default"
    GENERIC = "generic"


@dataclass
class AssemblyWarning:
    """Assembly warning with detailed information."""
    id: str
    level: WarningLevel
    category: str
    message: str
    element_id: Optional[str] = None
    element_type: Optional[str] = None
    property_name: Optional[str] = None
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None
    recommendation: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryAction:
    """Recovery action taken for an error."""
    id: str
    strategy: RecoveryStrategy
    original_error: str
    recovery_method: str
    fallback_value: Optional[Any] = None
    success: bool = True
    timestamp: float = field(default_factory=time.time)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorReport:
    """Comprehensive error report for UI/API consumption."""
    report_id: str
    timestamp: float
    success: bool
    warnings: List[AssemblyWarning]
    recovery_actions: List[RecoveryAction]
    errors: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class WarningCollector:
    """Collects and manages assembly warnings."""
    
    def __init__(self):
        self.warnings: List[AssemblyWarning] = []
        self.warning_counts: Dict[str, int] = defaultdict(int)
        self.categories: Dict[str, List[AssemblyWarning]] = defaultdict(list)
    
    def add_warning(self, level: WarningLevel, category: str, message: str,
                   element_id: Optional[str] = None, element_type: Optional[str] = None,
                   property_name: Optional[str] = None, expected_value: Optional[Any] = None,
                   actual_value: Optional[Any] = None, recommendation: Optional[str] = None,
                   context: Optional[Dict[str, Any]] = None) -> str:
        """Add a warning to the collection."""
        warning_id = str(uuid.uuid4())
        
        warning = AssemblyWarning(
            id=warning_id,
            level=level,
            category=category,
            message=message,
            element_id=element_id,
            element_type=element_type,
            property_name=property_name,
            expected_value=expected_value,
            actual_value=actual_value,
            recommendation=recommendation,
            context=context or {}
        )
        
        self.warnings.append(warning)
        self.warning_counts[category] += 1
        self.categories[category].append(warning)
        
        # Log warning
        log_message = f"[{category}] {message}"
        if element_id:
            log_message += f" (Element: {element_id})"
        
        if level == WarningLevel.ERROR:
            logger.error(log_message)
        elif level == WarningLevel.WARNING:
            logger.warning(log_message)
        elif level == WarningLevel.CRITICAL:
            logger.critical(log_message)
        else:
            logger.info(log_message)
        
        return warning_id
    
    def add_missing_geometry_warning(self, element_id: str, element_type: str) -> str:
        """Add warning for missing geometry."""
        return self.add_warning(
            level=WarningLevel.WARNING,
            category="missing_geometry",
            message=f"Missing geometry for {element_type} element",
            element_id=element_id,
            element_type=element_type,
            recommendation="Consider adding geometry data or using a placeholder"
        )
    
    def add_ambiguous_type_warning(self, element_id: str, detected_types: List[str]) -> str:
        """Add warning for ambiguous element type."""
        return self.add_warning(
            level=WarningLevel.WARNING,
            category="ambiguous_type",
            message=f"Ambiguous element type detected",
            element_id=element_id,
            element_type="unknown",
            actual_value=detected_types,
            recommendation=f"Specify explicit type from: {', '.join(detected_types)}"
        )
    
    def add_property_conflict_warning(self, element_id: str, property_name: str,
                                    expected_value: Any, actual_value: Any) -> str:
        """Add warning for property conflicts."""
        return self.add_warning(
            level=WarningLevel.WARNING,
            category="property_conflict",
            message=f"Property conflict detected for {property_name}",
            element_id=element_id,
            property_name=property_name,
            expected_value=expected_value,
            actual_value=actual_value,
            recommendation="Verify property values and resolve conflicts"
        )
    
    def add_unknown_type_warning(self, element_id: str, unknown_type: str) -> str:
        """Add warning for unknown BIM type."""
        return self.add_warning(
            level=WarningLevel.WARNING,
            category="unknown_type",
            message=f"Unknown BIM type: {unknown_type}",
            element_id=element_id,
            element_type=unknown_type,
            recommendation="Consider adding type mapping or using generic BIMElement"
        )
    
    def add_validation_warning(self, element_id: str, validation_errors: List[str]) -> str:
        """Add warning for validation errors."""
        return self.add_warning(
            level=WarningLevel.ERROR,
            category="validation_error",
            message=f"Validation failed: {', '.join(validation_errors)}",
            element_id=element_id,
            actual_value=validation_errors,
            recommendation="Fix validation errors or use fallback values"
        )
    
    def get_warnings_by_category(self, category: str) -> List[AssemblyWarning]:
        """Get warnings by category."""
        return self.categories.get(category, [])
    
    def get_warnings_by_level(self, level: WarningLevel) -> List[AssemblyWarning]:
        """Get warnings by severity level."""
        return [w for w in self.warnings if w.level == level]
    
    def get_warning_summary(self) -> Dict[str, Any]:
        """Get summary of all warnings."""
        summary = {
            "total_warnings": len(self.warnings),
            "by_level": {},
            "by_category": dict(self.warning_counts),
            "critical_count": len(self.get_warnings_by_level(WarningLevel.CRITICAL)),
            "error_count": len(self.get_warnings_by_level(WarningLevel.ERROR)),
            "warning_count": len(self.get_warnings_by_level(WarningLevel.WARNING)),
            "info_count": len(self.get_warnings_by_level(WarningLevel.INFO))
        }
        
        for level in WarningLevel:
            summary["by_level"][level.value] = len(self.get_warnings_by_level(level))
        
        return summary


class RecoveryManager:
    """Manages recovery strategies for errors and incomplete data."""
    
    def __init__(self):
        self.recovery_actions: List[RecoveryAction] = []
        self.fallback_values: Dict[str, Any] = {
            "geometry": {"type": "unknown", "coordinates": []},
            "properties": {},
            "type": "generic",
            "system": "unknown",
            "space": "unknown"
        }
        self.recovery_strategies: Dict[str, RecoveryStrategy] = {
            "missing_geometry": RecoveryStrategy.FALLBACK,
            "unknown_type": RecoveryStrategy.GENERIC,
            "validation_error": RecoveryStrategy.DEFAULT,
            "property_conflict": RecoveryStrategy.DEFAULT,
            "ambiguous_type": RecoveryStrategy.FALLBACK
        }
    
    def add_recovery_action(self, strategy: RecoveryStrategy, original_error: str,
                           recovery_method: str, fallback_value: Optional[Any] = None,
                           success: bool = True, context: Optional[Dict[str, Any]] = None) -> str:
        """Add a recovery action."""
        action_id = str(uuid.uuid4())
        
        action = RecoveryAction(
            id=action_id,
            strategy=strategy,
            original_error=original_error,
            recovery_method=recovery_method,
            fallback_value=fallback_value,
            success=success,
            context=context or {}
        )
        
        self.recovery_actions.append(action)
        return action_id
    
    def recover_missing_geometry(self, element_id: str, element_type: str) -> Dict[str, Any]:
        """Recover from missing geometry."""
        fallback_geometry = self.fallback_values["geometry"].copy()
        fallback_geometry["element_id"] = element_id
        fallback_geometry["element_type"] = element_type
        
        self.add_recovery_action(
            strategy=RecoveryStrategy.FALLBACK,
            original_error="Missing geometry",
            recovery_method="Using placeholder geometry",
            fallback_value=fallback_geometry,
            context={"element_id": element_id, "element_type": element_type}
        )
        
        return fallback_geometry
    
    def recover_unknown_type(self, element_id: str, unknown_type: str) -> str:
        """Recover from unknown BIM type."""
        fallback_type = "generic"
        
        self.add_recovery_action(
            strategy=RecoveryStrategy.GENERIC,
            original_error=f"Unknown BIM type: {unknown_type}",
            recovery_method="Using generic BIMElement",
            fallback_value=fallback_type,
            context={"element_id": element_id, "unknown_type": unknown_type}
        )
        
        return fallback_type
    
    def recover_ambiguous_type(self, element_id: str, detected_types: List[str]) -> str:
        """Recover from ambiguous type detection."""
        # Use the first detected type as fallback
        fallback_type = detected_types[0] if detected_types else "generic"
        
        self.add_recovery_action(
            strategy=RecoveryStrategy.FALLBACK,
            original_error="Ambiguous type detection",
            recovery_method=f"Using first detected type: {fallback_type}",
            fallback_value=fallback_type,
            context={"element_id": element_id, "detected_types": detected_types}
        )
        
        return fallback_type
    
    def recover_property_conflict(self, element_id: str, property_name: str,
                                expected_value: Any, actual_value: Any) -> Any:
        """Recover from property conflicts."""
        # Use expected value as fallback
        fallback_value = expected_value
        
        self.add_recovery_action(
            strategy=RecoveryStrategy.DEFAULT,
            original_error=f"Property conflict: {property_name}",
            recovery_method=f"Using expected value: {expected_value}",
            fallback_value=fallback_value,
            context={
                "element_id": element_id,
                "property_name": property_name,
                "expected_value": expected_value,
                "actual_value": actual_value
            }
        )
        
        return fallback_value
    
    def recover_validation_error(self, element_id: str, validation_errors: List[str]) -> Dict[str, Any]:
        """Recover from validation errors."""
        # Create minimal valid properties
        fallback_properties = {
            "valid": False,
            "validation_errors": validation_errors,
            "recovered": True
        }
        
        self.add_recovery_action(
            strategy=RecoveryStrategy.DEFAULT,
            original_error=f"Validation errors: {', '.join(validation_errors)}",
            recovery_method="Using minimal valid properties",
            fallback_value=fallback_properties,
            context={"element_id": element_id, "validation_errors": validation_errors}
        )
        
        return fallback_properties
    
    def get_recovery_summary(self) -> Dict[str, Any]:
        """Get summary of recovery actions."""
        summary = {
            "total_actions": len(self.recovery_actions),
            "successful_recoveries": len([a for a in self.recovery_actions if a.success]),
            "failed_recoveries": len([a for a in self.recovery_actions if not a.success]),
            "by_strategy": defaultdict(int)
        }
        
        for action in self.recovery_actions:
            summary["by_strategy"][action.strategy.value] += 1
        
        return summary


class ErrorReporter:
    """Generates structured error reports for UI/API consumption."""
    
    def __init__(self, warning_collector: WarningCollector, recovery_manager: RecoveryManager):
        self.warning_collector = warning_collector
        self.recovery_manager = recovery_manager
    
    def generate_error_report(self, success: bool, errors: List[str] = None,
                            metadata: Optional[Dict[str, Any]] = None) -> ErrorReport:
        """Generate comprehensive error report."""
        report_id = str(uuid.uuid4())
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        # Create report
        report = ErrorReport(
            report_id=report_id,
            timestamp=time.time(),
            success=success,
            warnings=self.warning_collector.warnings,
            recovery_actions=self.recovery_manager.recovery_actions,
            errors=errors or [],
            recommendations=recommendations,
            metadata=metadata or {}
        )
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on warnings and recovery actions."""
        recommendations = []
        
        # Analyze warnings
        warning_summary = self.warning_collector.get_warning_summary()
        
        if warning_summary["critical_count"] > 0:
            recommendations.append("Critical issues detected. Review and fix before proceeding.")
        
        if warning_summary["error_count"] > 0:
            recommendations.append("Validation errors found. Consider fixing data quality issues.")
        
        if warning_summary["by_category"].get("missing_geometry", 0) > 0:
            recommendations.append("Missing geometry detected. Add geometry data for better visualization.")
        
        if warning_summary["by_category"].get("unknown_type", 0) > 0:
            recommendations.append("Unknown types detected. Consider adding type mappings.")
        
        if warning_summary["by_category"].get("ambiguous_type", 0) > 0:
            recommendations.append("Ambiguous types detected. Specify explicit type information.")
        
        # Analyze recovery actions
        recovery_summary = self.recovery_manager.get_recovery_summary()
        
        if recovery_summary["failed_recoveries"] > 0:
            recommendations.append("Some recovery actions failed. Review error logs for details.")
        
        if recovery_summary["successful_recoveries"] > 0:
            recommendations.append("Recovery actions applied successfully. Review results for accuracy.")
        
        return recommendations
    
    def to_json(self, report: ErrorReport) -> str:
        """Convert error report to JSON string."""
        return json.dumps(self._report_to_dict(report), indent=2, default=str)
    
    def to_dict(self, report: ErrorReport) -> Dict[str, Any]:
        """Convert error report to dictionary."""
        return self._report_to_dict(report)
    
    def _report_to_dict(self, report: ErrorReport) -> Dict[str, Any]:
        """Convert error report to dictionary format."""
        return {
            "report_id": report.report_id,
            "timestamp": report.timestamp,
            "success": report.success,
            "warnings": [
                {
                    "id": w.id,
                    "level": w.level.value,
                    "category": w.category,
                    "message": w.message,
                    "element_id": w.element_id,
                    "element_type": w.element_type,
                    "property_name": w.property_name,
                    "expected_value": w.expected_value,
                    "actual_value": w.actual_value,
                    "recommendation": w.recommendation,
                    "timestamp": w.timestamp,
                    "context": w.context
                }
                for w in report.warnings
            ],
            "recovery_actions": [
                {
                    "id": a.id,
                    "strategy": a.strategy.value,
                    "original_error": a.original_error,
                    "recovery_method": a.recovery_method,
                    "fallback_value": a.fallback_value,
                    "success": a.success,
                    "timestamp": a.timestamp,
                    "context": a.context
                }
                for a in report.recovery_actions
            ],
            "errors": report.errors,
            "recommendations": report.recommendations,
            "symbol_metadata": report.symbol_metadata,
            "summary": {
                "total_warnings": len(report.warnings),
                "total_recovery_actions": len(report.recovery_actions),
                "total_errors": len(report.errors),
                "total_recommendations": len(report.recommendations)
            }
        }


class RobustErrorHandler:
    """Main error handling system that coordinates warnings, recovery, and reporting."""
    
    def __init__(self):
        self.warning_collector = WarningCollector()
        self.recovery_manager = RecoveryManager()
        self.error_reporter = ErrorReporter(self.warning_collector, self.recovery_manager)
        self.errors: List[str] = []
    
    def handle_missing_geometry(self, element_id: str, element_type: str) -> Dict[str, Any]:
        """Handle missing geometry with recovery."""
        # Add warning
        self.warning_collector.add_missing_geometry_warning(element_id, element_type)
        
        # Attempt recovery
        try:
            recovered_geometry = self.recovery_manager.recover_missing_geometry(element_id, element_type)
            return recovered_geometry
        except Exception as e:
            self.errors.append(f"Failed to recover geometry for {element_id}: {e}")
            return self.recovery_manager.fallback_values["geometry"]
    
    def handle_unknown_type(self, element_id: str, unknown_type: str) -> str:
        """Handle unknown BIM type with recovery."""
        # Add warning
        self.warning_collector.add_unknown_type_warning(element_id, unknown_type)
        
        # Attempt recovery
        try:
            recovered_type = self.recovery_manager.recover_unknown_type(element_id, unknown_type)
            return recovered_type
        except Exception as e:
            self.errors.append(f"Failed to recover type for {element_id}: {e}")
            return "generic"
    
    def handle_ambiguous_type(self, element_id: str, detected_types: List[str]) -> str:
        """Handle ambiguous type detection with recovery."""
        # Add warning
        self.warning_collector.add_ambiguous_type_warning(element_id, detected_types)
        
        # Attempt recovery
        try:
            recovered_type = self.recovery_manager.recover_ambiguous_type(element_id, detected_types)
            return recovered_type
        except Exception as e:
            self.errors.append(f"Failed to recover ambiguous type for {element_id}: {e}")
            return "generic"
    
    def handle_property_conflict(self, element_id: str, property_name: str,
                               expected_value: Any, actual_value: Any) -> Any:
        """Handle property conflicts with recovery."""
        # Add warning
        self.warning_collector.add_property_conflict_warning(
            element_id, property_name, expected_value, actual_value
        )
        
        # Attempt recovery
        try:
            recovered_value = self.recovery_manager.recover_property_conflict(
                element_id, property_name, expected_value, actual_value
            )
            return recovered_value
        except Exception as e:
            self.errors.append(f"Failed to recover property conflict for {element_id}: {e}")
            return expected_value
    
    def handle_validation_error(self, element_id: str, validation_errors: List[str]) -> Dict[str, Any]:
        """Handle validation errors with recovery."""
        # Add warning
        self.warning_collector.add_validation_warning(element_id, validation_errors)
        
        # Attempt recovery
        try:
            recovered_properties = self.recovery_manager.recover_validation_error(
                element_id, validation_errors
            )
            return recovered_properties
        except Exception as e:
            self.errors.append(f"Failed to recover validation error for {element_id}: {e}")
            return {"valid": False, "validation_errors": validation_errors}
    
    def handle_exception(self, exception: Exception, context: str = "") -> None:
        """Handle exceptions and add to error list."""
        error_message = f"{context}: {str(exception)}" if context else str(exception)
        self.errors.append(error_message)
        logger.error(error_message, exc_info=True)
    
    def generate_report(self, success: bool = True, metadata: Optional[Dict[str, Any]] = None) -> ErrorReport:
        """Generate comprehensive error report."""
        return self.error_reporter.generate_error_report(
            success=success,
            errors=self.errors,
            metadata=metadata
        )
    
    def get_report_json(self, success: bool = True, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Generate error report as JSON string."""
        report = self.generate_report(success, metadata)
        return self.error_reporter.to_json(report)
    
    def get_report_dict(self, success: bool = True, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate error report as dictionary."""
        report = self.generate_report(success, metadata)
        return self.error_reporter.to_dict(report)
    
    def clear(self) -> None:
        """Clear all warnings, recovery actions, and errors."""
        self.warning_collector.warnings.clear()
        self.warning_collector.warning_counts.clear()
        self.warning_collector.categories.clear()
        self.recovery_manager.recovery_actions.clear()
        self.errors.clear()


# Convenience functions for easy integration
def create_error_handler() -> RobustErrorHandler:
    """Create a new error handler instance."""
    return RobustErrorHandler()


def handle_assembly_warning(handler: RobustErrorHandler, level: WarningLevel, category: str,
                          message: str, **kwargs) -> str:
    """Add assembly warning using error handler."""
    return handler.warning_collector.add_warning(level, category, message, **kwargs)


def handle_recovery_action(handler: RobustErrorHandler, strategy: RecoveryStrategy,
                          original_error: str, recovery_method: str, **kwargs) -> str:
    """Add recovery action using error handler."""
    return handler.recovery_manager.add_recovery_action(
        strategy, original_error, recovery_method, **kwargs
    )


def generate_error_report(handler: RobustErrorHandler, success: bool = True,
                        metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generate error report using error handler."""
    return handler.get_report_dict(success, metadata) 