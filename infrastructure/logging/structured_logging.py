"""
Comprehensive Structured Logging Strategy

Provides enterprise-grade structured logging with correlation IDs, 
performance metrics, and integration with monitoring systems.
"""

import json
import logging
import logging.config
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from contextlib import contextmanager
from functools import wraps
import threading
from dataclasses import dataclass, asdict

# Thread-local storage for request context
_context = threading.local()


@dataclass
class LogContext:
    """Structured log context with correlation tracking."""
    request_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    operation: Optional[str] = None
    component: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    extra_fields: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        result = asdict(self)
        if self.extra_fields:
            result.update(self.extra_fields)
        return {k: v for k, v in result.items() if v is not None}


class ContextualFormatter(logging.Formatter):
    """Custom formatter that includes structured context."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Add context to the record
        context = get_log_context()
        if context:
            for key, value in context.to_dict().items():
                if not hasattr(record, key):
                    setattr(record, key, value)
        
        # Add timestamp if not present
        if not hasattr(record, 'timestamp'):
            record.timestamp = datetime.utcnow().isoformat()
        
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add context
        context = get_log_context()
        if context:
            log_data.update(context.to_dict())
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields from the record
        for key, value in record.__dict__.items():
            if key not in log_data and not key.startswith('_'):
                if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                    log_data[key] = value
        
        return json.dumps(log_data, default=str, ensure_ascii=False)


class PerformanceLogger:
    """Logger for performance metrics and timing."""
    
    def __init__(self, logger_name: str = "performance"):
        self.logger = logging.getLogger(logger_name)
    
    def log_operation_time(self, operation: str, duration: float, 
                          success: bool = True, details: Dict[str, Any] = None):
        """Log operation timing with structured data."""
        log_data = {
            'operation': operation,
            'duration_ms': round(duration * 1000, 2),
            'success': success,
            'performance_metric': True
        }
        
        if details:
            log_data.update(details)
        
        level = logging.INFO if success else logging.WARNING
        self.logger.log(level, f"Operation {operation} completed", extra=log_data)
    
    def log_database_query(self, query_type: str, table: str, duration: float, 
                          rows_affected: int = None, success: bool = True):
        """Log database query performance."""
        self.log_operation_time(
            f"db_{query_type}",
            duration,
            success,
            {
                'table': table,
                'rows_affected': rows_affected,
                'query_type': query_type,
                'database_metric': True
            }
        )
    
    def log_api_request(self, method: str, endpoint: str, status_code: int, 
                       duration: float, user_id: str = None):
        """Log API request performance."""
        self.log_operation_time(
            "api_request",
            duration,
            200 <= status_code < 400,
            {
                'http_method': method,
                'endpoint': endpoint,
                'status_code': status_code,
                'user_id': user_id,
                'api_metric': True
            }
        )


class SecurityLogger:
    """Logger for security-related events."""
    
    def __init__(self, logger_name: str = "security"):
        self.logger = logging.getLogger(logger_name)
    
    def log_authentication_attempt(self, username: str, success: bool, 
                                 ip_address: str = None, user_agent: str = None):
        """Log authentication attempts."""
        self.logger.info(
            f"Authentication {'successful' if success else 'failed'} for user: {username}",
            extra={
                'event_type': 'authentication',
                'username': username,
                'success': success,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'security_event': True
            }
        )
    
    def log_authorization_failure(self, user_id: str, resource: str, 
                                action: str, ip_address: str = None):
        """Log authorization failures."""
        self.logger.warning(
            f"Authorization denied for user {user_id} accessing {resource}",
            extra={
                'event_type': 'authorization_failure',
                'user_id': user_id,
                'resource': resource,
                'action': action,
                'ip_address': ip_address,
                'security_event': True
            }
        )
    
    def log_suspicious_activity(self, event_type: str, description: str, 
                              user_id: str = None, ip_address: str = None,
                              severity: str = "medium"):
        """Log suspicious activities."""
        level = logging.WARNING if severity == "medium" else logging.ERROR
        self.logger.log(
            level,
            f"Suspicious activity detected: {description}",
            extra={
                'event_type': 'suspicious_activity',
                'activity_type': event_type,
                'description': description,
                'user_id': user_id,
                'ip_address': ip_address,
                'severity': severity,
                'security_event': True
            }
        )


class BusinessLogger:
    """Logger for business events and domain activities."""
    
    def __init__(self, logger_name: str = "business"):
        self.logger = logging.getLogger(logger_name)
    
    def log_entity_created(self, entity_type: str, entity_id: str, 
                          created_by: str = None, details: Dict[str, Any] = None):
        """Log entity creation events."""
        log_data = {
            'event_type': 'entity_created',
            'entity_type': entity_type,
            'entity_id': entity_id,
            'created_by': created_by,
            'business_event': True
        }
        
        if details:
            log_data.update(details)
        
        self.logger.info(f"{entity_type} created with ID: {entity_id}", extra=log_data)
    
    def log_entity_updated(self, entity_type: str, entity_id: str, 
                          updated_fields: List[str], updated_by: str = None):
        """Log entity update events."""
        self.logger.info(
            f"{entity_type} {entity_id} updated",
            extra={
                'event_type': 'entity_updated',
                'entity_type': entity_type,
                'entity_id': entity_id,
                'updated_fields': updated_fields,
                'updated_by': updated_by,
                'business_event': True
            }
        )
    
    def log_business_rule_violation(self, rule_name: str, entity_type: str, 
                                  entity_id: str, details: Dict[str, Any] = None):
        """Log business rule violations."""
        log_data = {
            'event_type': 'business_rule_violation',
            'rule_name': rule_name,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'business_event': True
        }
        
        if details:
            log_data.update(details)
        
        self.logger.warning(f"Business rule violation: {rule_name}", extra=log_data)


class AuditLogger:
    """Logger for audit trail and compliance."""
    
    def __init__(self, logger_name: str = "audit"):
        self.logger = logging.getLogger(logger_name)
    
    def log_data_access(self, user_id: str, resource_type: str, resource_id: str, 
                       action: str, ip_address: str = None):
        """Log data access for compliance."""
        self.logger.info(
            f"Data access: {action} on {resource_type} {resource_id}",
            extra={
                'event_type': 'data_access',
                'user_id': user_id,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'action': action,
                'ip_address': ip_address,
                'audit_event': True
            }
        )
    
    def log_configuration_change(self, user_id: str, component: str, 
                                old_value: Any, new_value: Any):
        """Log configuration changes."""
        self.logger.info(
            f"Configuration changed in {component}",
            extra={
                'event_type': 'configuration_change',
                'user_id': user_id,
                'component': component,
                'old_value': str(old_value),
                'new_value': str(new_value),
                'audit_event': True
            }
        )


# Context management functions
def set_log_context(context: LogContext) -> None:
    """Set the log context for the current thread."""
    _context.current = context


def get_log_context() -> Optional[LogContext]:
    """Get the current log context."""
    return getattr(_context, 'current', None)


def clear_log_context() -> None:
    """Clear the log context for the current thread."""
    if hasattr(_context, 'current'):
        del _context.current


@contextmanager
def log_context(request_id: str = None, user_id: str = None, operation: str = None, 
                component: str = None, **extra_fields):
    """Context manager for setting log context."""
    if request_id is None:
        request_id = str(uuid.uuid4())
    
    context = LogContext(
        request_id=request_id,
        user_id=user_id,
        operation=operation,
        component=component,
        extra_fields=extra_fields
    )
    
    old_context = get_log_context()
    try:
        set_log_context(context)
        yield context
    finally:
        if old_context:
            set_log_context(old_context)
        else:
            clear_log_context()


def timed_operation(operation_name: str = None, log_level: int = logging.INFO):
    """Decorator to log operation timing."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            logger = logging.getLogger(func.__module__)
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.log(
                    log_level,
                    f"Operation {op_name} completed successfully",
                    extra={
                        'operation': op_name,
                        'duration_ms': round(duration * 1000, 2),
                        'success': True,
                        'performance_metric': True
                    }
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                logger.error(
                    f"Operation {op_name} failed: {str(e)}",
                    extra={
                        'operation': op_name,
                        'duration_ms': round(duration * 1000, 2),
                        'success': False,
                        'error_type': type(e).__name__,
                        'performance_metric': True
                    }
                )
                raise
                
        return wrapper
    return decorator


# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': JSONFormatter
        },
        'contextual': {
            '()': ContextualFormatter,
            'format': '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'contextual',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'json',
            'filename': 'logs/application.log',
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 10,
            'encoding': 'utf8'
        },
        'performance': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'json',
            'filename': 'logs/performance.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'encoding': 'utf8'
        },
        'security': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'json',
            'filename': 'logs/security.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 10,
            'encoding': 'utf8'
        },
        'audit': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'json',
            'filename': 'logs/audit.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 20,
            'encoding': 'utf8'
        }
    },
    'loggers': {
        'performance': {
            'handlers': ['performance'],
            'level': 'INFO',
            'propagate': False
        },
        'security': {
            'handlers': ['security', 'console'],
            'level': 'INFO',
            'propagate': False
        },
        'business': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False
        },
        'audit': {
            'handlers': ['audit'],
            'level': 'INFO',
            'propagate': False
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'file']
    }
}


def setup_logging(config: Dict[str, Any] = None, log_dir: str = "logs") -> None:
    """Setup comprehensive logging configuration."""
    import os
    
    # Create log directory
    os.makedirs(log_dir, exist_ok=True)
    
    # Use provided config or default
    config = config or LOGGING_CONFIG
    
    # Update file paths if log_dir is different
    if log_dir != "logs":
        for handler_config in config['handlers'].values():
            if 'filename' in handler_config:
                filename = os.path.basename(handler_config['filename'])
                handler_config['filename'] = os.path.join(log_dir, filename)
    
    logging.config.dictConfig(config)


# Global logger instances
performance_logger = PerformanceLogger()
security_logger = SecurityLogger()
business_logger = BusinessLogger()
audit_logger = AuditLogger()


def get_logger(name: str) -> logging.Logger:
    """Get a logger with structured context support."""
    return logging.getLogger(name)