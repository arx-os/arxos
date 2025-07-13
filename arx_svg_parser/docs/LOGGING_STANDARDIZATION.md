# Logging Standardization with Structlog

## Overview

The Arxos Platform has been standardized to use `structlog` for structured logging across all Python services. This implementation follows best engineering practices and clean code principles.

## Key Features

### 1. Structured Logging
- **No string interpolation** - All logs use structured arguments
- **Rich context** - Request ID, user ID, operation type, performance metrics
- **Consistent format** - JSON in production, readable in development

### 2. Environment-Specific Configuration
- **Development**: Human-readable console output
- **Production**: JSON format for log aggregation
- **Testing**: Configurable log levels and formats

### 3. Performance Monitoring
- **Decorators**: `@log_performance` for function timing
- **Context Managers**: `log_operation()` for operation tracking
- **Class-based**: `PerformanceMonitor` for complex operations

### 4. Request Context
- **Middleware**: Automatic request context binding
- **Context Variables**: Request ID, user info, client IP
- **Response Tracking**: Status codes, response times

## Implementation

### Core Utilities

#### `arx_svg_parser/utils/logging.py`
```python
import structlog
import os

def configure_logging(
    log_level: str = "INFO",
    enable_json: bool = True,
    enable_console: bool = True,
    enable_file: bool = False,
    log_file: Optional[str] = None
):
    """Configure structured logging with best practices."""
    # Implementation details...

def setup_logging_for_environment():
    """Configure logging based on environment."""
    env = os.getenv("ENVIRONMENT", "development")
    # Environment-specific configuration...
```

#### `arx_svg_parser/utils/performance.py`
```python
import structlog
import time

def log_performance(func: Callable) -> Callable:
    """Decorator to log function performance with structured logging."""
    # Implementation for sync and async functions...

@contextmanager
def log_operation(operation_name: str, **context):
    """Context manager for logging operations with structured context."""
    # Implementation...

class PerformanceMonitor:
    """Class for monitoring performance metrics with structured logging."""
    # Implementation...
```

### Middleware

#### `arx_svg_parser/middleware/context_middleware.py`
```python
class LoggingContextMiddleware(BaseHTTPMiddleware):
    """Middleware to bind request context to structlog contextvars."""
    
    async def dispatch(self, request, call_next):
        # Bind comprehensive request context
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            path=request.url.path,
            method=request.method,
            client_ip=self._get_client_ip(request),
            # ... additional context
        )
        # Process request and log results
```

## Usage Examples

### Basic Logging
```python
import structlog

logger = structlog.get_logger(__name__)

# ✅ CORRECT - Structured logging
logger.info("user_authenticated", 
           user_id=user.id, 
           method="jwt", 
           success=True)

# ❌ AVOID - String interpolation
logger.info(f"User {user.id} authenticated successfully")
```

### Performance Monitoring
```python
from arx_svg_parser.utils.performance import log_performance, log_operation

# Using decorator
@log_performance
async def process_data(data: dict) -> dict:
    # Processing logic...
    return result

# Using context manager
with log_operation("data_processing", user_id=user.id):
    # Processing logic...
    pass

# Using PerformanceMonitor class
async with PerformanceMonitor("complex_operation", user_id=user.id):
    # Complex operation...
    pass
```

### Error Handling
```python
try:
    # Operation that might fail
    result = await risky_operation()
except Exception as e:
    logger.error("operation_failed",
                operation="risky_operation",
                error=str(e),
                error_type=type(e).__name__,
                user_id=user.id,
                context={"data_size": len(data)})
    raise
```

### Security Events
```python
logger.warning("security_event",
              event_type="login_attempt",
              user_id=user.id,
              ip_address=client_ip,
              success=False,
              reason="invalid_credentials")
```

## Log Levels

### DEBUG
- Detailed diagnostic information
- Function entry/exit points
- Variable values for debugging

### INFO
- General operational events
- User actions (login, logout, data access)
- System state changes

### WARNING
- Unexpected but handled situations
- Rate limit exceeded
- Security events (failed login attempts)

### ERROR
- Error conditions that don't stop execution
- Database connection failures
- External API failures

### CRITICAL
- System-level failures
- Database connection lost
- Application startup failures

## Context Variables

### Request Context (Automatic)
- `request_id`: Unique request identifier
- `path`: Request URL path
- `method`: HTTP method
- `client_ip`: Client IP address
- `user_agent`: Browser/client information
- `user_id`: Authenticated user ID
- `user_roles`: User roles/permissions

### Performance Context
- `duration`: Operation duration in seconds
- `memory_usage`: Memory consumption
- `cpu_usage`: CPU utilization
- `operation`: Operation name/type

### Error Context
- `error`: Error message
- `error_type`: Exception class name
- `stack_trace`: Full stack trace (when needed)
- `context`: Additional error context

## Testing

### Test Configuration
```python
@pytest.fixture(autouse=True)
def setup_logging():
    """Configure logging for tests."""
    configure_logging(log_level="DEBUG", enable_json=False)
```

### Testing Structured Logs
```python
def test_structured_logging(caplog):
    """Test structured logging output."""
    logger = structlog.get_logger(__name__)
    
    with caplog.at_level("INFO"):
        logger.info("test_event", user_id="123", action="login")
    
    # Verify structured log contains expected fields
    log_record = caplog.records[-1]
    assert "test_event" in log_record.message
    assert "user_id" in log_record.message
```

## Migration Guide

### From Legacy Logging
```python
# OLD - Legacy logging
import logging
logger = logging.getLogger(__name__)
logger.info(f"User {user.id} logged in")

# NEW - Structured logging
import structlog
logger = structlog.get_logger(__name__)
logger.info("user_logged_in", user_id=user.id)
```

### From Print Statements
```python
# OLD - Print statements
print(f"Processing data for user {user.id}")

# NEW - Structured logging
logger.info("processing_data", user_id=user.id)
```

## Best Practices

### 1. Always Use Structured Arguments
```python
# ✅ Good
logger.info("user_action", 
           user_id=user.id, 
           action="data_export", 
           file_count=5)

# ❌ Avoid
logger.info(f"User {user.id} exported {file_count} files")
```

### 2. Include Relevant Context
```python
# ✅ Good - Rich context
logger.error("database_error",
            operation="user_query",
            user_id=user.id,
            query_type="select",
            error=str(e),
            retry_attempt=2)

# ❌ Avoid - Minimal context
logger.error(f"Database error: {e}")
```

### 3. Use Appropriate Log Levels
```python
# DEBUG - Detailed diagnostic info
logger.debug("processing_step", step="validation", data_size=len(data))

# INFO - General operational events
logger.info("user_login", user_id=user.id, method="password")

# WARNING - Unexpected but handled
logger.warning("rate_limit_exceeded", user_id=user.id, limit=100)

# ERROR - Error conditions
logger.error("external_api_failed", api="payment", error=str(e))

# CRITICAL - System failures
logger.critical("database_connection_lost", db_host=host)
```

### 4. Performance Monitoring
```python
# For simple functions
@log_performance
def calculate_metrics(data):
    return process_data(data)

# For complex operations
with log_operation("batch_processing", batch_size=len(items)):
    for item in items:
        process_item(item)

# For async operations
@log_performance
async def async_operation():
    await asyncio.sleep(0.1)
    return result
```

### 5. Error Context
```python
try:
    result = risky_operation()
except ValueError as e:
    logger.error("validation_error",
                error=str(e),
                error_type="ValueError",
                context={"input_data": data})
    raise
except Exception as e:
    logger.error("unexpected_error",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True)
    raise
```

## Configuration

### Environment Variables
```bash
# Development
ENVIRONMENT=development
LOG_LEVEL=DEBUG
LOG_JSON=false

# Production
ENVIRONMENT=production
LOG_LEVEL=INFO
LOG_JSON=true
LOG_FILE=/var/log/arx_svg_parser/app.log
```

### Application Startup
```python
# In main.py
from arx_svg_parser.utils.logging import setup_logging_for_environment

# Setup environment-specific logging
setup_logging_for_environment()
logger = structlog.get_logger(__name__)

logger.info("application_started", version="1.0.0")
```

## Monitoring and Observability

### Log Aggregation
- **Production**: JSON format for easy parsing
- **Development**: Human-readable format for debugging
- **Testing**: Configurable format for test verification

### Metrics Collection
- **Performance**: Duration, throughput, error rates
- **Security**: Authentication events, access attempts
- **Business**: User actions, feature usage

### Alerting
- **Error Rates**: Monitor error frequency
- **Performance**: Alert on slow operations
- **Security**: Alert on suspicious activities

## Conclusion

This logging standardization provides:
- **Observability**: Easy to search, filter, and analyze logs
- **Debugging**: Rich context for troubleshooting
- **Performance**: Minimal overhead with structured logging
- **Maintainability**: Consistent patterns across the codebase
- **Scalability**: Works well with log aggregation systems

The implementation follows industry best practices and ensures that all logging across the Arxos Platform is consistent, structured, and provides valuable insights for monitoring and debugging. 