"""
Error handling utilities for the Arxos SVGX Engine pipeline.
"""


class PipelineError(Exception):
    """Base exception for pipeline-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(Exception):
    """Exception for validation-related errors."""
    
    def __init__(self, message: str, field: str = None, value: any = None):
        super().__init__(message)
        self.message = message
        self.field = field
        self.value = value


class SymbolError(Exception):
    """Exception for symbol-related errors."""
    
    def __init__(self, message: str, symbol: str = None):
        super().__init__(message)
        self.message = message
        self.symbol = symbol


class BehaviorError(Exception):
    """Exception for behavior profile-related errors."""
    
    def __init__(self, message: str, behavior_profile: str = None):
        super().__init__(message)
        self.message = message
        self.behavior_profile = behavior_profile


class ComplianceError(Exception):
    """Exception for compliance-related errors."""
    
    def __init__(self, message: str, compliance_rule: str = None):
        super().__init__(message)
        self.message = message
        self.compliance_rule = compliance_rule


class SchemaError(Exception):
    """Exception for schema-related errors."""
    
    def __init__(self, message: str, schema_file: str = None):
        super().__init__(message)
        self.message = message
        self.schema_file = schema_file


def format_error_response(error: Exception, operation: str = None) -> dict:
    """Format an error into a standardized response."""
    response = {
        "success": False,
        "error": str(error),
        "error_type": type(error).__name__,
        "timestamp": __import__("time").time()
    }
    
    if operation:
        response["operation"] = operation
    
    # Add specific details based on error type
    if isinstance(error, ValidationError):
        response["field"] = error.field
        response["value"] = error.value
    elif isinstance(error, SymbolError):
        response["symbol"] = error.symbol
    elif isinstance(error, BehaviorError):
        response["behavior_profile"] = error.behavior_profile
    elif isinstance(error, ComplianceError):
        response["compliance_rule"] = error.compliance_rule
    elif isinstance(error, SchemaError):
        response["schema_file"] = error.schema_file
    elif isinstance(error, PipelineError):
        response["details"] = error.details
    
    return response