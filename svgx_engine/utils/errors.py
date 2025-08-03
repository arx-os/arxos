"""
Error classes for the SVGX Engine.

This module provides custom exception classes for the SVGX Engine.
"""


class SVGXError(Exception):
    """Base exception for SVGX Engine errors."""
    
    def __init__(self, message: str, context: str = None):
    """
    Perform __init__ operation

Args:
        message: Description of message
        context: Description of context

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        self.message = message
        self.context = context
        super().__init__(self.message)


class SymbolError(SVGXError):
    """
    Perform __init__ operation

Args:
        message: Description of message
        symbol_name: Description of symbol_name

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
    """Exception raised for symbol-related errors."""
    
    def __init__(self, message: str, symbol_name: str = None):
        self.symbol_name = symbol_name
        super().__init__(message, symbol_name)


class ValidationError(SVGXError):
    """Exception raised for validation errors."""
    
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message, field)


class PipelineError(SVGXError):
    """Exception raised for pipeline-related errors."""
    
    def __init__(self, message: str, operation: str = None):
        self.operation = operation
        super().__init__(message, operation)


class ConfigurationError(SVGXError):
    """Exception raised for configuration errors."""
    
    def __init__(self, message: str, config_key: str = None):
        self.config_key = config_key
        super().__init__(message, config_key)


class SecurityError(SVGXError):
    """Exception raised for security-related errors."""
    
    def __init__(self, message: str, security_context: str = None):
        self.security_context = security_context
        super().__init__(message, security_context)


class ExportError(SVGXError):
    """Exception raised for export-related errors."""
    
    def __init__(self, message: str, export_format: str = None):
        self.export_format = export_format
        super().__init__(message, export_format)


class ImportError(SVGXError):
    """Exception raised for import-related errors."""
    
    def __init__(self, message: str, import_format: str = None):
        self.import_format = import_format
        super().__init__(message, import_format)


class PerformanceError(SVGXError):
    """Exception raised for performance-related errors."""
    
    def __init__(self, message: str, performance_metric: str = None):
        self.performance_metric = performance_metric
        super().__init__(message, performance_metric)


class PersistenceError(SVGXError):
    """Exception raised for persistence-related errors."""
    
    def __init__(self, message: str, persistence_operation: str = None):
        self.persistence_operation = persistence_operation
        super().__init__(message, persistence_operation)


class NetworkError(SVGXError):
    """Exception raised for network-related errors."""
    
    def __init__(self, message: str, network_endpoint: str = None):
        self.network_endpoint = network_endpoint
        super().__init__(message, network_endpoint)


class AuthenticationError(SVGXError):
    """Exception raised for authentication-related errors."""
    
    def __init__(self, message: str, auth_context: str = None):
        self.auth_context = auth_context
        super().__init__(message, auth_context)


class AuthorizationError(SVGXError):
    """Exception raised for authorization-related errors."""
    
    def __init__(self, message: str, auth_context: str = None):
        self.auth_context = auth_context
        super().__init__(message, auth_context)


class ResourceNotFoundError(SVGXError):
    """Exception raised when a resource is not found."""
    
    def __init__(self, message: str, resource_type: str = None, resource_id: str = None):
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(message, resource_type)


class MetadataError(SVGXError):
    """Exception raised for metadata-related errors."""
    
    def __init__(self, message: str, metadata_key: str = None):
        self.metadata_key = metadata_key
        super().__init__(message, metadata_key)


class CacheError(SVGXError):
    """Exception raised for cache-related errors."""
    
    def __init__(self, message: str, cache_operation: str = None):
        self.cache_operation = cache_operation
        super().__init__(message, cache_operation)


class DatabaseError(SVGXError):
    """Exception raised for database-related errors."""
    
    def __init__(self, message: str, database_operation: str = None):
        self.database_operation = database_operation
        super().__init__(message, database_operation)


class RecognitionError(SVGXError):
    """Exception raised for recognition-related errors."""
    
    def __init__(self, message: str, recognition_type: str = None):
        self.recognition_type = recognition_type
        super().__init__(message, recognition_type)


class BIMError(SVGXError):
    """Exception raised for BIM-related errors."""
    
    def __init__(self, message: str, bim_operation: str = None):
        self.bim_operation = bim_operation
        super().__init__(message, bim_operation)


class PhysicsError(SVGXError):
    """Exception raised for physics-related errors."""
    
    def __init__(self, message: str, physics_type: str = None):
        self.physics_type = physics_type
        super().__init__(message, physics_type)


class IntegrationError(SVGXError):
    """Exception raised for integration-related errors."""
    
    def __init__(self, message: str, integration_type: str = None):
        self.integration_type = integration_type
        super().__init__(message, integration_type)


class BehaviorError(SVGXError):
    """Exception raised for behavior-related errors."""
    
    def __init__(self, message: str, behavior_type: str = None):
        self.behavior_type = behavior_type
        super().__init__(message, behavior_type)


class StateMachineError(SVGXError):
    """Exception raised for state machine-related errors."""
    
    def __init__(self, message: str, state_machine_operation: str = None):
        self.state_machine_operation = state_machine_operation
        super().__init__(message, state_machine_operation)


class TransitionError(SVGXError):
    """Exception raised for state transition-related errors."""
    
    def __init__(self, message: str, transition_operation: str = None):
        self.transition_operation = transition_operation
        super().__init__(message, transition_operation)


class LogicError(SVGXError):
    """Exception raised for logic-related errors."""
    
    def __init__(self, message: str, logic_operation: str = None):
        self.logic_operation = logic_operation
        super().__init__(message, logic_operation)


class EventError(SVGXError):
    """Exception raised for event-related errors."""
    
    def __init__(self, message: str, event_type: str = None):
        self.event_type = event_type
        super().__init__(message, event_type)


class ConditionError(SVGXError):
    """Exception raised for condition-related errors."""
    
    def __init__(self, message: str, condition_type: str = None):
        self.condition_type = condition_type
        super().__init__(message, condition_type)


# Additional error classes for core behavior systems
class StateError(SVGXError):
    """Exception raised for state-related errors."""
    
    def __init__(self, message: str, state_operation: str = None):
        self.state_operation = state_operation
        super().__init__(message, state_operation)


class OptimizationError(SVGXError):
    """Exception raised for optimization-related errors."""
    
    def __init__(self, message: str, optimization_operation: str = None):
        self.optimization_operation = optimization_operation
        super().__init__(message, optimization_operation)


class MemoryError(SVGXError):
    """Exception raised for memory-related errors."""
    
    def __init__(self, message: str, memory_operation: str = None):
        self.memory_operation = memory_operation
        super().__init__(message, memory_operation)