import time
import structlog
import asyncio
from functools import wraps
from typing import Optional, Any, Callable
from contextlib import contextmanager

logger = structlog.get_logger(__name__)

def log_performance(func: Callable) -> Callable:
    """Decorator to log function performance with structured logging."""
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        func_name = f"{func.__module__}.{func.__name__}"
        
        logger.debug("function_start", function=func_name)
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            logger.info("function_completed",
                       function=func_name,
                       duration=duration,
                       status="success")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            logger.error("function_failed",
                        function=func_name,
                        duration=duration,
                        error=str(e),
                        error_type=type(e).__name__,
                        status="error")
            raise
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        func_name = f"{func.__module__}.{func.__name__}"
        
        logger.debug("function_start", function=func_name)
        
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            
            logger.info("function_completed",
                       function=func_name,
                       duration=duration,
                       status="success")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            logger.error("function_failed",
                        function=func_name,
                        duration=duration,
                        error=str(e),
                        error_type=type(e).__name__,
                        status="error")
            raise
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

@contextmanager
def log_operation(operation_name: str, **context):
    """Context manager for logging operations with structured context."""
    start_time = time.time()
    
    logger.info("operation_start", operation=operation_name, **context)
    
    try:
        yield
        duration = time.time() - start_time
        
        logger.info("operation_completed",
                   operation=operation_name,
                   duration=duration,
                   status="success",
                   **context)
        
    except Exception as e:
        duration = time.time() - start_time
        
        logger.error("operation_failed",
                    operation=operation_name,
                    duration=duration,
                    error=str(e),
                    error_type=type(e).__name__,
                    status="error",
                    **context)
        raise

class PerformanceMonitor:
    """Class for monitoring performance metrics with structured logging."""
    
    def __init__(self, operation_name: str, **context):
        self.operation_name = operation_name
        self.context = context
        self.start_time = None
        self.logger = structlog.get_logger(__name__)
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.info("operation_start", operation=self.operation_name, **self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type is None:
            self.logger.info("operation_completed",
                           operation=self.operation_name,
                           duration=duration,
                           status="success",
                           **self.context)
        else:
            self.logger.error("operation_failed",
                            operation=self.operation_name,
                            duration=duration,
                            error=str(exc_val),
                            error_type=exc_type.__name__,
                            status="error",
                            **self.context)
    
    async def __aenter__(self):
        self.start_time = time.time()
        self.logger.info("operation_start", operation=self.operation_name, **self.context)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type is None:
            self.logger.info("operation_completed",
                           operation=self.operation_name,
                           duration=duration,
                           status="success",
                           **self.context)
        else:
            self.logger.error("operation_failed",
                            operation=self.operation_name,
                            duration=duration,
                            error=str(exc_val),
                            error_type=exc_type.__name__,
                            status="error",
                            **self.context) 