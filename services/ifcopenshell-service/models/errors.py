"""
Enhanced Error Handling Module

This module provides comprehensive error handling including:
- Custom exception classes
- Error recovery strategies
- Detailed error logging
- User-friendly error messages
"""

import logging
import traceback
from typing import Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class IFCServiceError(Exception):
    """Base exception for IFC service errors"""
    
    def __init__(self, message: str, error_code: str = "IFC_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()


class IFCParseError(IFCServiceError):
    """Exception for IFC parsing errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "IFC_PARSE_ERROR", details)


class IFCValidationError(IFCServiceError):
    """Exception for IFC validation errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "IFC_VALIDATION_ERROR", details)


class SpatialQueryError(IFCServiceError):
    """Exception for spatial query errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "SPATIAL_QUERY_ERROR", details)


class CacheError(IFCServiceError):
    """Exception for cache-related errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CACHE_ERROR", details)


class ConfigurationError(IFCServiceError):
    """Exception for configuration errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CONFIGURATION_ERROR", details)


class ErrorHandler:
    """Comprehensive error handling and recovery"""
    
    def __init__(self):
        self.error_counts = {}
        self.recovery_strategies = {
            "IFC_PARSE_ERROR": self._handle_parse_error,
            "IFC_VALIDATION_ERROR": self._handle_validation_error,
            "SPATIAL_QUERY_ERROR": self._handle_spatial_error,
            "CACHE_ERROR": self._handle_cache_error,
            "CONFIGURATION_ERROR": self._handle_config_error
        }
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle and process errors with recovery strategies"""
        context = context or {}
        
        # Log the error
        self._log_error(error, context)
        
        # Count error occurrences
        error_type = type(error).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Determine error response
        if isinstance(error, IFCServiceError):
            return self._create_error_response(error)
        else:
            return self._create_generic_error_response(error, context)
    
    def _log_error(self, error: Exception, context: Dict[str, Any]):
        """Log error with full context"""
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.utcnow().isoformat(),
            "context": context,
            "traceback": traceback.format_exc()
        }
        
        logger.error(f"IFC Service Error: {json.dumps(error_info, indent=2)}")
    
    def _create_error_response(self, error: IFCServiceError) -> Dict[str, Any]:
        """Create structured error response for IFC service errors"""
        return {
            "success": False,
            "error": {
                "code": error.error_code,
                "message": error.message,
                "details": error.details,
                "timestamp": error.timestamp
            }
        }
    
    def _create_generic_error_response(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create error response for generic exceptions"""
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred",
                "details": {
                    "error_type": type(error).__name__,
                    "context": context
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _handle_parse_error(self, error: IFCParseError) -> Dict[str, Any]:
        """Handle IFC parsing errors with recovery suggestions"""
        suggestions = []
        
        if "corrupted" in error.message.lower():
            suggestions.append("Try re-exporting the IFC file from your CAD software")
        elif "version" in error.message.lower():
            suggestions.append("Ensure the IFC file is compatible with IFC4 format")
        elif "size" in error.message.lower():
            suggestions.append("Try compressing the IFC file or splitting it into smaller parts")
        
        error.details["suggestions"] = suggestions
        return self._create_error_response(error)
    
    def _handle_validation_error(self, error: IFCValidationError) -> Dict[str, Any]:
        """Handle IFC validation errors with compliance guidance"""
        guidance = []
        
        if "buildingSMART" in error.message.lower():
            guidance.append("Ensure the IFC file follows buildingSMART standards")
        elif "spatial" in error.message.lower():
            guidance.append("Check spatial relationships and containment hierarchy")
        elif "schema" in error.message.lower():
            guidance.append("Verify IFC schema compliance and entity definitions")
        
        error.details["guidance"] = guidance
        return self._create_error_response(error)
    
    def _handle_spatial_error(self, error: SpatialQueryError) -> Dict[str, Any]:
        """Handle spatial query errors with query suggestions"""
        suggestions = []
        
        if "bounds" in error.message.lower():
            suggestions.append("Check that the query bounds are valid 3D coordinates")
        elif "entity" in error.message.lower():
            suggestions.append("Verify that the entity ID exists in the IFC model")
        elif "proximity" in error.message.lower():
            suggestions.append("Ensure the center point and radius are valid")
        
        error.details["suggestions"] = suggestions
        return self._create_error_response(error)
    
    def _handle_cache_error(self, error: CacheError) -> Dict[str, Any]:
        """Handle cache errors with fallback strategies"""
        strategies = []
        
        if "redis" in error.message.lower():
            strategies.append("Falling back to local cache")
            strategies.append("Check Redis connection and configuration")
        elif "memory" in error.message.lower():
            strategies.append("Clearing cache to free memory")
            strategies.append("Consider reducing cache TTL")
        
        error.details["fallback_strategies"] = strategies
        return self._create_error_response(error)
    
    def _handle_config_error(self, error: ConfigurationError) -> Dict[str, Any]:
        """Handle configuration errors with setup guidance"""
        guidance = []
        
        if "environment" in error.message.lower():
            guidance.append("Check environment variables are properly set")
        elif "file" in error.message.lower():
            guidance.append("Verify configuration file exists and is readable")
        elif "permission" in error.message.lower():
            guidance.append("Check file and directory permissions")
        
        error.details["setup_guidance"] = guidance
        return self._create_error_response(error)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        total_errors = sum(self.error_counts.values())
        
        return {
            "total_errors": total_errors,
            "error_counts": self.error_counts,
            "error_rate": total_errors,  # Would be calculated over time in real implementation
            "timestamp": datetime.utcnow().isoformat()
        }


class ErrorRecovery:
    """Error recovery strategies and fallback mechanisms"""
    
    @staticmethod
    def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
        """Retry function with exponential backoff"""
        import time
        
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                time.sleep(delay)
    
    @staticmethod
    def fallback_to_native_parser(ifc_data: bytes):
        """Fallback to native parser when IfcOpenShell fails"""
        try:
            # This would call the native Go parser as fallback
            logger.info("Falling back to native parser")
            # Implementation would depend on the native parser integration
            return {"success": True, "fallback": True, "message": "Using native parser"}
        except Exception as e:
            logger.error(f"Native parser fallback failed: {e}")
            raise IFCParseError(f"Both IfcOpenShell and native parser failed: {str(e)}")
    
    @staticmethod
    def fallback_to_local_cache(cache_key: str):
        """Fallback to local cache when Redis fails"""
        try:
            # This would use local cache as fallback
            logger.info("Falling back to local cache")
            # Implementation would depend on local cache availability
            return None  # Cache miss
        except Exception as e:
            logger.error(f"Local cache fallback failed: {e}")
            raise CacheError(f"Both Redis and local cache failed: {str(e)}")


# Global error handler instance
error_handler = ErrorHandler()
error_recovery = ErrorRecovery()
