"""
Precision Error Types and Handling

This module provides precision-specific error types and comprehensive error handling
mechanisms for the precision validation system. It ensures proper error reporting,
logging, and recovery for precision violations.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import logging
import traceback
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from decimal import Decimal

from .precision_validator import ValidationResult, ValidationLevel, ValidationType
from .precision_coordinate import PrecisionCoordinate

logger = logging.getLogger(__name__)


class PrecisionErrorType(Enum):
    """Types of precision errors."""
    COORDINATE_RANGE_VIOLATION = "coordinate_range_violation"
    COORDINATE_PRECISION_VIOLATION = "coordinate_precision_violation"
    COORDINATE_NAN_VIOLATION = "coordinate_nan_violation"
    TRANSFORMATION_ERROR = "transformation_error"
    CONSTRAINT_VIOLATION = "constraint_violation"
    GEOMETRIC_ERROR = "geometric_error"
    CALCULATION_ERROR = "calculation_error"
    VALIDATION_ERROR = "validation_error"
    RECOVERY_ERROR = "recovery_error"
    SYSTEM_ERROR = "system_error"


class PrecisionErrorSeverity(Enum):
    """Severity levels for precision errors."""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


@dataclass
class PrecisionError:
    """Precision error with detailed information."""
    error_id: str
    error_type: PrecisionErrorType
    severity: PrecisionErrorSeverity
    message: str
    operation: str
    coordinates: List[PrecisionCoordinate] = field(default_factory=list)
    validation_results: List[ValidationResult] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    stack_trace: Optional[str] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False
    corrected_coordinates: List[PrecisionCoordinate] = field(default_factory=list)

    def __post_init__(self):
        """Initialize error with stack trace if not provided."""
        if self.stack_trace is None:
            self.stack_trace = traceback.format_exc()

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for serialization."""
        return {
            "error_id": self.error_id,
            "error_type": self.error_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "operation": self.operation,
            "coordinates": [str(coord) for coord in self.coordinates],
            "validation_results": [result.to_dict() for result in self.validation_results],
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "stack_trace": self.stack_trace,
            "recovery_attempted": self.recovery_attempted,
            "recovery_successful": self.recovery_successful,
            "corrected_coordinates": [str(coord) for coord in self.corrected_coordinates]
        }


@dataclass
class PrecisionErrorReport:
    """Comprehensive precision error report."""
    report_id: str
    errors: List[PrecisionError] = field(default_factory=list)
    warnings: List[PrecisionError] = field(default_factory=list)
    info_messages: List[PrecisionError] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def add_error(self, error: PrecisionError) -> None:
        """Add error to report."""
        self.errors.append(error)

    def add_warning(self, warning: PrecisionError) -> None:
        """Add warning to report."""
        self.warnings.append(warning)

    def add_info(self, info: PrecisionError) -> None:
        """Add info message to report."""
        self.info_messages.append(info)

    def generate_summary(self) -> Dict[str, Any]:
        """Generate error summary."""
        total_errors = len(self.errors)
        total_warnings = len(self.warnings)
        total_info = len(self.info_messages)

        # Count errors by type
        error_types = {}
        for error in self.errors:
            error_type = error.error_type.value
            error_types[error_type] = error_types.get(error_type, 0) + 1

        # Count errors by severity
        severity_counts = {}
        for error in self.errors:
            severity = error.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        self.summary = {
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "total_info": total_info,
            "error_types": error_types,
            "severity_counts": severity_counts,
            "timestamp": self.timestamp.isoformat()
        }

        return self.summary

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "report_id": self.report_id,
            "errors": [error.to_dict() for error in self.errors],
            "warnings": [warning.to_dict() for warning in self.warnings],
            "info_messages": [info.to_dict() for info in self.info_messages],
            "summary": self.generate_summary()
        }


class PrecisionErrorHandler:
    """Comprehensive precision error handler."""

    def __init__(self):
        """Initialize precision error handler."""
        self.error_reports: List[PrecisionErrorReport] = []
        self.current_report: Optional[PrecisionErrorReport] = None
        self.logger = logging.getLogger(__name__)
        self.error_callbacks: List[callable] = []
        self.recovery_strategies: Dict[PrecisionErrorType, callable] = {}

        # Register default recovery strategies
        self._register_default_recovery_strategies()

    def start_error_report(self, report_id: str) -> PrecisionErrorReport:
        """Start a new error report."""
        self.current_report = PrecisionErrorReport(report_id=report_id)
        self.error_reports.append(self.current_report)
        return self.current_report

    def end_error_report(self) -> Optional[PrecisionErrorReport]:
        """End the current error report."""
        if self.current_report:
            self.current_report.generate_summary()
            report = self.current_report
            self.current_report = None
            return report
        return None

    def handle_error(self, error_type: PrecisionErrorType,
                    message: str,
                    operation: str,
                    coordinates: Optional[List[PrecisionCoordinate]] = None,
                    validation_results: Optional[List[ValidationResult]] = None,
                    context: Optional[Dict[str, Any]] = None,
                    severity: PrecisionErrorSeverity = PrecisionErrorSeverity.ERROR,
                    attempt_recovery: bool = True) -> PrecisionError:
        """Handle a precision error."""
        # Create error
        error = PrecisionError(
            error_id=self._generate_error_id(),
            error_type=error_type,
            severity=severity,
            message=message,
            operation=operation,
            coordinates=coordinates or [],
            validation_results=validation_results or [],
            context=context or {}
        )

        # Log error
        self._log_error(error)

        # Add to current report if available
        if self.current_report:
            if severity == PrecisionErrorSeverity.CRITICAL or severity == PrecisionErrorSeverity.ERROR:
                self.current_report.add_error(error)
            elif severity == PrecisionErrorSeverity.WARNING:
                self.current_report.add_warning(error)
            else:
                self.current_report.add_info(error)

        # Attempt recovery if enabled
        if attempt_recovery and error_type in self.recovery_strategies:
            try:
                error.recovery_attempted = True
                recovery_result = self.recovery_strategies[error_type](error)
                error.recovery_successful = recovery_result

                if recovery_result:
                    self.logger.info(f"Recovery successful for error {error.error_id}")
                else:
                    self.logger.warning(f"Recovery failed for error {error.error_id}")

            except Exception as recovery_error:
                self.logger.error(f"Recovery strategy failed for error {error.error_id}: {recovery_error}")
                error.recovery_successful = False

        # Notify error callbacks
        self._notify_error_callbacks(error)

        return error

    def register_error_callback(self, callback: callable) -> None:
        """Register error callback."""
        self.error_callbacks.append(callback)

    def register_recovery_strategy(self, error_type: PrecisionErrorType, strategy: callable) -> None:
        """Register recovery strategy for error type."""
        self.recovery_strategies[error_type] = strategy

    def _generate_error_id(self) -> str:
        """Generate unique error ID."""
        import uuid
        return f"precision_error_{uuid.uuid4().hex[:8]}"

    def _log_error(self, error: PrecisionError) -> None:
        """Log precision error."""
        log_message = f"Precision Error [{error.error_type.value}]: {error.message}"
        log_context = {
            "error_id": error.error_id,
            "operation": error.operation,
            "coordinates_count": len(error.coordinates),
            "validation_results_count": len(error.validation_results)
        }

        if error.severity == PrecisionErrorSeverity.CRITICAL:
            self.logger.critical(log_message, extra=log_context, exc_info=True)
        elif error.severity == PrecisionErrorSeverity.ERROR:
            self.logger.error(log_message, extra=log_context)
        elif error.severity == PrecisionErrorSeverity.WARNING:
            self.logger.warning(log_message, extra=log_context)
        elif error.severity == PrecisionErrorSeverity.INFO:
            self.logger.info(log_message, extra=log_context)
        else:
            self.logger.debug(log_message, extra=log_context)

    def _notify_error_callbacks(self, error: PrecisionError) -> None:
        """Notify registered error callbacks."""
        for callback in self.error_callbacks:
            try:
                callback(error)
            except Exception as e:
                self.logger.error(f"Error callback failed: {e}")

    def _register_default_recovery_strategies(self) -> None:
        """Register default recovery strategies."""

        # Coordinate range violation recovery
        self.register_recovery_strategy(
            PrecisionErrorType.COORDINATE_RANGE_VIOLATION,
            self._recover_coordinate_range_violation
        )

        # Coordinate precision violation recovery
        self.register_recovery_strategy(
            PrecisionErrorType.COORDINATE_PRECISION_VIOLATION,
            self._recover_coordinate_precision_violation
        )

        # Coordinate NaN violation recovery
        self.register_recovery_strategy(
            PrecisionErrorType.COORDINATE_NAN_VIOLATION,
            self._recover_coordinate_nan_violation
        )

        # Transformation error recovery
        self.register_recovery_strategy(
            PrecisionErrorType.TRANSFORMATION_ERROR,
            self._recover_transformation_error
        )

        # Constraint violation recovery
        self.register_recovery_strategy(
            PrecisionErrorType.CONSTRAINT_VIOLATION,
            self._recover_constraint_violation
        )

    def _recover_coordinate_range_violation(self, error: PrecisionError) -> bool:
        """Recover from coordinate range violation."""
        try:
            corrected_coordinates = []
            for coord in error.coordinates:
                # Clamp coordinates to valid range
                max_range = 1e6
                corrected_x = max(-max_range, min(max_range, coord.x))
                corrected_y = max(-max_range, min(max_range, coord.y))
                corrected_z = max(-max_range, min(max_range, coord.z))

                corrected_coord = PrecisionCoordinate(corrected_x, corrected_y, corrected_z)
                corrected_coordinates.append(corrected_coord)

            error.corrected_coordinates = corrected_coordinates
            return True

        except Exception as e:
            self.logger.error(f"Coordinate range recovery failed: {e}")
            return False

    def _recover_coordinate_precision_violation(self, error: PrecisionError) -> bool:
        """Recover from coordinate precision violation."""
        try:
            corrected_coordinates = []
            precision_value = 0.001  # Default precision

            for coord in error.coordinates:
                # Round to precision
                corrected_x = round(coord.x / precision_value) * precision_value
                corrected_y = round(coord.y / precision_value) * precision_value
                corrected_z = round(coord.z / precision_value) * precision_value

                corrected_coord = PrecisionCoordinate(corrected_x, corrected_y, corrected_z)
                corrected_coordinates.append(corrected_coord)

            error.corrected_coordinates = corrected_coordinates
            return True

        except Exception as e:
            self.logger.error(f"Coordinate precision recovery failed: {e}")
            return False

    def _recover_coordinate_nan_violation(self, error: PrecisionError) -> bool:
        """Recover from coordinate NaN violation."""
        try:
            corrected_coordinates = []

            for coord in error.coordinates:
                # Replace NaN values with 0
                corrected_x = 0.0 if coord.x != coord.x else coord.x
                corrected_y = 0.0 if coord.y != coord.y else coord.y
                corrected_z = 0.0 if coord.z != coord.z else coord.z

                corrected_coord = PrecisionCoordinate(corrected_x, corrected_y, corrected_z)
                corrected_coordinates.append(corrected_coord)

            error.corrected_coordinates = corrected_coordinates
            return True

        except Exception as e:
            self.logger.error(f"Coordinate NaN recovery failed: {e}")
            return False

    def _recover_transformation_error(self, error: PrecisionError) -> bool:
        """Recover from transformation error."""
        try:
            # For transformation errors, we might need to revert to original coordinates
            # This is a simplified recovery - in practice, this would be more complex
            if error.coordinates:
                error.corrected_coordinates = error.coordinates.copy()
                return True
            return False

        except Exception as e:
            self.logger.error(f"Transformation recovery failed: {e}")
            return False

    def _recover_constraint_violation(self, error: PrecisionError) -> bool:
        """Recover from constraint violation."""
        try:
            # For constraint violations, we might need to adjust coordinates
            # This is a simplified recovery - in practice, this would be more complex
            if error.coordinates:
                error.corrected_coordinates = error.coordinates.copy()
                return True
            return False

        except Exception as e:
            self.logger.error(f"Constraint recovery failed: {e}")
            return False


class PrecisionErrorLogger:
    """Specialized logger for precision errors."""

    def __init__(self, log_file: Optional[str] = None):
        """Initialize precision error logger."""
        self.logger = logging.getLogger("precision_errors")
        self.log_file = log_file

        # Configure logger
        self._configure_logger()

    def _configure_logger(self) -> None:
        """Configure precision error logger."""
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Create file handler if log file specified
        if self.log_file:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # Set log level
        self.logger.setLevel(logging.INFO)

    def log_error(self, error: PrecisionError) -> None:
        """Log precision error."""
        log_message = f"[{error.error_type.value}] {error.message}"

        if error.severity == PrecisionErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error.severity == PrecisionErrorSeverity.ERROR:
            self.logger.error(log_message)
        elif error.severity == PrecisionErrorSeverity.WARNING:
            self.logger.warning(log_message)
        elif error.severity == PrecisionErrorSeverity.INFO:
            self.logger.info(log_message)
        else:
            self.logger.debug(log_message)

    def log_error_report(self, report: PrecisionErrorReport) -> None:
        """Log precision error report."""
        summary = report.generate_summary()

        self.logger.info(f"Precision Error Report: {report.report_id}")
        self.logger.info(f"Total Errors: {summary['total_errors']}")
        self.logger.info(f"Total Warnings: {summary['total_warnings']}")
        self.logger.info(f"Error Types: {summary['error_types']}")
        self.logger.info(f"Severity Counts: {summary['severity_counts']}")


# Global error handler instance
error_handler = PrecisionErrorHandler()

# Global error logger instance
error_logger = PrecisionErrorLogger()


def handle_precision_error(error_type: PrecisionErrorType,
                         message: str,
                         operation: str,
                         coordinates: Optional[List[PrecisionCoordinate]] = None,
                         validation_results: Optional[List[ValidationResult]] = None,
                         context: Optional[Dict[str, Any]] = None,
                         severity: PrecisionErrorSeverity = PrecisionErrorSeverity.ERROR,
                         attempt_recovery: bool = True) -> PrecisionError:
    """Convenience function to handle precision errors."""
    return error_handler.handle_error(
        error_type=error_type,
        message=message,
        operation=operation,
        coordinates=coordinates,
        validation_results=validation_results,
        context=context,
        severity=severity,
        attempt_recovery=attempt_recovery
    )


def log_precision_error(error: PrecisionError) -> None:
    """Convenience function to log precision errors."""
    error_logger.log_error(error)


def log_precision_error_report(report: PrecisionErrorReport) -> None:
    """Convenience function to log precision error reports."""
    error_logger.log_error_report(report)
