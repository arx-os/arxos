"""
SVGX Engine - Error Handler Service

This module provides centralized error handling for SVGX Engine services.
"""

import logging
import traceback
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import json

from structlog import get_logger

try:
    from svgx_engine.utils.errors import SVGXError, ExportError, ImportError, ValidationError
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.errors import SVGXError, ExportError, ImportError, ValidationError

logger = get_logger()


class ErrorSeverity(Enum):
    """Error severity levels for categorization and alerting."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories for classification and handling."""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RESOURCE_NOT_FOUND = "resource_not_found"
    CONFLICT = "conflict"
    RATE_LIMIT = "rate_limit"
    NETWORK = "network"
    DATABASE = "database"
    INTERNAL = "internal"
    EXTERNAL_SERVICE = "external_service"
    TIMEOUT = "timeout"
    CONFIGURATION = "configuration"

class ErrorHandler:
    """
    Comprehensive error handling service with categorization, structured logging,
    and automated recovery procedures.
    """
    
    def __init__(self):
        self.error_counts = {}  # error_type -> count
        self.recovery_procedures = {}  # error_type -> recovery function
        self.alert_thresholds = {}  # error_type -> threshold for alerting
        self._init_default_recovery_procedures()
        self._init_alert_thresholds()
    
    def _init_default_recovery_procedures(self):
        """Initialize default recovery procedures for common error types."""
        self.recovery_procedures = {
            ErrorCategory.VALIDATION: self._recover_validation_error,
            ErrorCategory.CONFLICT: self._recover_conflict_error,
            ErrorCategory.RATE_LIMIT: self._recover_rate_limit_error,
            ErrorCategory.TIMEOUT: self._recover_timeout_error,
            ErrorCategory.NETWORK: self._recover_network_error,
        }
    
    def _init_alert_thresholds(self):
        """Initialize alert thresholds for different error types."""
        self.alert_thresholds = {
            ErrorSeverity.CRITICAL: 1,  # Alert immediately
            ErrorSeverity.HIGH: 5,      # Alert after 5 occurrences
            ErrorSeverity.MEDIUM: 10,   # Alert after 10 occurrences
            ErrorSeverity.LOW: 50,      # Alert after 50 occurrences
        }
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    category: ErrorCategory = ErrorCategory.INTERNAL) -> Dict[str, Any]:
        """
        Handle an error with comprehensive logging and recovery procedures.
        
        Args:
            error: The exception that occurred
            context: Additional context information
            severity: Error severity level
            category: Error category for classification
            
        Returns:
            Dict containing error information and recovery status
        """
        error_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Extract error information
        error_info = {
            "error_id": error_id,
            "timestamp": timestamp,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "severity": severity.value,
            "category": category.value,
            "context": context or {},
            "traceback": traceback.format_exc()
        }
        
        # Log the error
        self._log_error(error_info)
        
        # Update error counts
        self._update_error_counts(category)
        
        # Check if alert should be triggered
        if self._should_trigger_alert(category, severity):
            self._trigger_alert(error_info)
        
        # Attempt recovery
        recovery_result = self._attempt_recovery(error_info, category)
        
        # Return structured error response
        return {
            "status": "error",
            "error_id": error_id,
            "message": self._get_user_friendly_message(error_info),
            "error_code": self._get_error_code(error_info),
            "severity": severity.value,
            "category": category.value,
            "recovery_attempted": recovery_result["attempted"],
            "recovery_successful": recovery_result["successful"],
            "suggestions": self._get_recovery_suggestions(error_info)
        }
    
    def _log_error(self, error_info: Dict[str, Any]):
        """Log error with structured information."""
        log_level = self._get_log_level(error_info["severity"])
        logger.log(log_level, f"Error {error_info['error_id']}: {error_info['error_type']} - {error_info['error_message']}")
        logger.debug(f"Error details: {json.dumps(error_info, indent=2)}")
    
    def _get_log_level(self, severity: str) -> int:
        """Get appropriate log level for error severity."""
        severity_levels = {
            "low": logging.INFO,
            "medium": logging.WARNING,
            "high": logging.ERROR,
            "critical": logging.CRITICAL
        }
        return severity_levels.get(severity, logging.ERROR)
    
    def _update_error_counts(self, category: ErrorCategory):
        """Update error count for the category."""
        category_key = category.value
        self.error_counts[category_key] = self.error_counts.get(category_key, 0) + 1
    
    def _should_trigger_alert(self, category: ErrorCategory, severity: ErrorSeverity) -> bool:
        """Check if an alert should be triggered based on thresholds."""
        if severity == ErrorSeverity.CRITICAL:
            return True
        
        threshold = self.alert_thresholds.get(severity, 10)
        count = self.error_counts.get(category.value, 0)
        return count >= threshold
    
    def _trigger_alert(self, error_info: Dict[str, Any]):
        """Trigger an alert for the error."""
        alert_message = f"ALERT: {error_info['severity'].upper()} error detected - {error_info['error_type']}: {error_info['error_message']}"
        logger.critical(alert_message)
        # TODO: Integrate with external alerting systems (Slack, email, etc.)
    
    def _attempt_recovery(self, error_info: Dict[str, Any], category: ErrorCategory) -> Dict[str, bool]:
        """Attempt to recover from the error using registered procedures."""
        recovery_func = self.recovery_procedures.get(category)
        if not recovery_func:
            return {"attempted": False, "successful": False}
        
        try:
            success = recovery_func(error_info)
            return {"attempted": True, "successful": success}
        except Exception as recovery_error:
            logger.error(f"Recovery procedure failed: {recovery_error}")
            return {"attempted": True, "successful": False}
    
    def _get_user_friendly_message(self, error_info: Dict[str, Any]) -> str:
        """Get a user-friendly error message."""
        error_type = error_info["error_type"]
        category = error_info["category"]
        
        messages = {
            "ValidationError": "The provided data is invalid. Please check your input and try again.",
            "AuthenticationError": "Authentication failed. Please log in again.",
            "AuthorizationError": "You don't have permission to perform this action.",
            "ResourceNotFoundError": "The requested resource was not found.",
            "ConflictError": "The operation conflicts with the current state. Please try again.",
            "RateLimitError": "Too many requests. Please wait a moment and try again.",
            "NetworkError": "Network connection failed. Please check your connection and try again.",
            "TimeoutError": "The operation timed out. Please try again.",
            "DatabaseError": "Database operation failed. Please try again later.",
            "ConfigurationError": "System configuration error. Please contact support."
        }
        
        return messages.get(error_type, "An unexpected error occurred. Please try again.")
    
    def _get_error_code(self, error_info: Dict[str, Any]) -> str:
        """Get a standardized error code."""
        category = error_info["category"]
        error_type = error_info["error_type"]
        
        codes = {
            "validation": "VALIDATION_ERROR",
            "authentication": "AUTH_ERROR",
            "authorization": "PERMISSION_ERROR",
            "resource_not_found": "NOT_FOUND",
            "conflict": "CONFLICT_ERROR",
            "rate_limit": "RATE_LIMIT",
            "network": "NETWORK_ERROR",
            "timeout": "TIMEOUT_ERROR",
            "database": "DB_ERROR",
            "internal": "INTERNAL_ERROR",
            "external_service": "EXTERNAL_ERROR",
            "configuration": "CONFIG_ERROR"
        }
        
        return codes.get(category, "UNKNOWN_ERROR")
    
    def _get_recovery_suggestions(self, error_info: Dict[str, Any]) -> List[str]:
        """Get suggestions for error recovery."""
        category = error_info["category"]
        
        suggestions = {
            "validation": [
                "Check that all required fields are provided",
                "Verify data format and constraints",
                "Ensure all values are within acceptable ranges"
            ],
            "authentication": [
                "Verify your credentials",
                "Check if your session has expired",
                "Try logging in again"
            ],
            "authorization": [
                "Contact your administrator for access",
                "Check if you have the required permissions",
                "Verify your role and access level"
            ],
            "conflict": [
                "Refresh the page to get the latest state",
                "Try the operation again in a moment",
                "Check if another user is editing the same resource"
            ],
            "rate_limit": [
                "Wait a few moments before trying again",
                "Reduce the frequency of your requests",
                "Contact support if you need higher limits"
            ],
            "network": [
                "Check your internet connection",
                "Try again in a few moments",
                "Contact support if the problem persists"
            ],
            "timeout": [
                "Try the operation again",
                "Check your network connection",
                "Contact support if timeouts continue"
            ]
        }
        
        return suggestions.get(category, ["Please try again", "Contact support if the problem persists"])
    
    # Recovery procedures
    def _recover_validation_error(self, error_info: Dict[str, Any]) -> bool:
        """Recovery procedure for validation errors."""
        # Validation errors are typically not recoverable automatically
        # but we can log them for analysis
        logger.info(f"Validation error recovery attempted for {error_info['error_id']}")
        return False
    
    def _recover_conflict_error(self, error_info: Dict[str, Any]) -> bool:
        """Recovery procedure for conflict errors."""
        # Conflicts might be resolved by retrying after a short delay
        logger.info(f"Conflict error recovery attempted for {error_info['error_id']}")
        return False
    
    def _recover_rate_limit_error(self, error_info: Dict[str, Any]) -> bool:
        """Recovery procedure for rate limit errors."""
        # Rate limits are typically resolved by waiting
        logger.info(f"Rate limit error recovery attempted for {error_info['error_id']}")
        return False
    
    def _recover_timeout_error(self, error_info: Dict[str, Any]) -> bool:
        """Recovery procedure for timeout errors."""
        # Timeouts might be resolved by retrying
        logger.info(f"Timeout error recovery attempted for {error_info['error_id']}")
        return False
    
    def _recover_network_error(self, error_info: Dict[str, Any]) -> bool:
        """Recovery procedure for network errors."""
        # Network errors might be resolved by retrying
        logger.info(f"Network error recovery attempted for {error_info['error_id']}")
        return False
    
    def register_recovery_procedure(self, category: ErrorCategory, recovery_func):
        """Register a custom recovery procedure for an error category."""
        self.recovery_procedures[category] = recovery_func
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        return {
            "error_counts": dict(self.error_counts),
            "total_errors": sum(self.error_counts.values()),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def reset_error_counts(self):
        """Reset error counts (useful for testing)."""
        self.error_counts.clear()

# Global error handler instance
error_handler = ErrorHandler() 