"""
API Middleware

This module contains middleware components for the Arxos API including
request logging, error handling, authentication, and rate limiting.
"""

import time
import uuid
import hashlib
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import structlog

from application.logging_config import get_logger
from application.exceptions import ApplicationError, ValidationError, BusinessRuleError


logger = get_logger("api.middleware")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging all API requests."""
    
    def __init__(self, app: ASGIApp):
    """
    Perform __init__ operation

Args:
        app: Description of app

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        super().__init__(app)
        self.logger = get_logger("api.request_logging")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request start
        start_time = time.time()
        
        # Extract request details
        method = request.method
        url = str(request.url)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log request
        self.logger.info(
            f"Request started: {method} {url}",
            request_id=request_id,
            method=method,
            url=url,
            client_ip=client_ip,
            user_agent=user_agent,
            timestamp=datetime.utcnow().isoformat()
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            self.logger.info(
                f"Request completed: {method} {url} - {response.status_code}",
                request_id=request_id,
                method=method,
                url=url,
                status_code=response.status_code,
                duration_ms=duration * 1000,
                timestamp=datetime.utcnow().isoformat()
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log error
            self.logger.error(
                f"Request failed: {method} {url} - {str(e)}",
                request_id=request_id,
                method=method,
                url=url,
                error=str(e),
                duration_ms=duration * 1000,
                timestamp=datetime.utcnow().isoformat()
            )
            
            # Re-raise the exception
            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Perform __init__ operation

Args:
        app: Description of app

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
    """Middleware for handling and formatting errors."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger("api.error_handling")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and handle errors."""
        try:
            response = await call_next(request)
            return response
            
        except ApplicationError as e:
            # Handle application-specific errors
            self.logger.error(
                f"Application error: {e.message}",
                request_id=getattr(request.state, 'request_id', None),
                error_code=e.error_code,
                details=e.details
            )
            
            return JSONResponse(
                status_code=400,
                content={
                    "error": True,
                    "error_code": e.error_code,
                    "message": e.message,
                    "details": e.details,
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": getattr(request.state, 'request_id', None)
                }
            )
            
        except ValidationError as e:
            # Handle validation errors
            self.logger.error(
                f"Validation error: {e.message}",
                request_id=getattr(request.state, 'request_id', None),
                field=e.field,
                value=e.value
            )
            
            return JSONResponse(
                status_code=422,
                content={
                    "error": True,
                    "error_code": "VALIDATION_ERROR",
                    "message": e.message,
                    "details": {"field": e.field, "value": e.value},
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": getattr(request.state, 'request_id', None)
                }
            )
            
        except BusinessRuleError as e:
            # Handle business rule errors
            self.logger.error(
                f"Business rule error: {e.message}",
                request_id=getattr(request.state, 'request_id', None),
                rule=e.rule,
                context=e.context
            )
            
            return JSONResponse(
                status_code=400,
                content={
                    "error": True,
                    "error_code": "BUSINESS_RULE_ERROR",
                    "message": e.message,
                    "details": {"rule": e.rule, "context": e.context},
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": getattr(request.state, 'request_id', None)
                }
            )
            
        except Exception as e:
            # Handle all other exceptions
            self.logger.error(
                f"Unhandled exception: {str(e)}",
                request_id=getattr(request.state, 'request_id', None),
                exception_type=type(e).__name__,
                exc_info=True
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": True,
                    "error_code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {"exception_type": type(e).__name__},
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": getattr(request.state, 'request_id', None)
                }
            )


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for API authentication."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger("api.authentication")
        self.api_keys = self._load_api_keys()
    
    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from environment or configuration."""
        # In production, this would load from secure storage
        return {
            "test-api-key": "test-user",
            "admin-api-key": "admin-user"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and authenticate."""
        # Skip authentication for certain endpoints
        if self._should_skip_auth(request):
            return await call_next(request)
        
        # Extract API key
        api_key = request.headers.get("X-API-Key")
        
        if not api_key:
            return JSONResponse(
                status_code=401,
                content={
                    "error": True,
                    "error_code": "MISSING_API_KEY",
                    "message": "API key is required",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Validate API key
        if api_key not in self.api_keys:
            return JSONResponse(
                status_code=401,
                content={
                    "error": True,
                    "error_code": "INVALID_API_KEY",
                    "message": "Invalid API key",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Set user information
        request.state.user_id = self.api_keys[api_key]
        request.state.api_key = api_key
        
        # Log authentication
        self.logger.info(
            f"API key authenticated: {api_key}",
            request_id=getattr(request.state, 'request_id', None),
            user_id=request.state.user_id,
            api_key=api_key
        )
        
        return await call_next(request)
    
    def _should_skip_auth(self, request: Request) -> bool:
        """Check if authentication should be skipped for this request."""
        skip_paths = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/"
        ]
        
        return any(request.url.path.startswith(path) for path in skip_paths)


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting API requests."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger("api.rate_limiting")
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
        self.max_requests = 100  # requests per window
        self.window_seconds = 60  # 1 minute window
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and apply rate limiting."""
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Check rate limit
        if not self._check_rate_limit(client_id):
            return JSONResponse(
                status_code=429,
                content={
                    "error": True,
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "message": "Rate limit exceeded. Please try again later.",
                    "details": {
                        "max_requests": self.max_requests,
                        "window_seconds": self.window_seconds
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(self._get_remaining_requests(client_id))
        response.headers["X-RateLimit-Reset"] = str(self._get_reset_time(client_id))
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Use API key if available, otherwise use IP address
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key}"
        
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    def _check_rate_limit(self, client_id: str) -> bool:
        """Check if client has exceeded rate limit."""
        now = datetime.utcnow()
        
        if client_id not in self.rate_limits:
            self.rate_limits[client_id] = {
                "requests": 1,
                "window_start": now
            }
            return True
        
        client_data = self.rate_limits[client_id]
        
        # Check if window has expired
        if (now - client_data["window_start"]).total_seconds() > self.window_seconds:
            # Reset window
            client_data["requests"] = 1
            client_data["window_start"] = now
            return True
        
        # Check if limit exceeded
        if client_data["requests"] >= self.max_requests:
            return False
        
        # Increment request count
        client_data["requests"] += 1
        return True
    
    def _get_remaining_requests(self, client_id: str) -> int:
        """Get remaining requests for client."""
        if client_id not in self.rate_limits:
            return self.max_requests
        
        client_data = self.rate_limits[client_id]
        return max(0, self.max_requests - client_data["requests"])
    
    def _get_reset_time(self, client_id: str) -> int:
        """Get reset time for rate limit window."""
        if client_id not in self.rate_limits:
            return int(datetime.utcnow().timestamp()) + self.window_seconds
        
        client_data = self.rate_limits[client_id]
        reset_time = client_data["window_start"] + timedelta(seconds=self.window_seconds)
        return int(reset_time.timestamp())


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for security headers and protection."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger("api.security")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add security headers."""
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting API metrics."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger("api.metrics")
        self.metrics: Dict[str, int] = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "requests_by_method": {},
            "requests_by_endpoint": {}
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics."""
        # Update total requests
        self.metrics["total_requests"] += 1
        
        # Update method metrics
        method = request.method
        self.metrics["requests_by_method"][method] = self.metrics["requests_by_method"].get(method, 0) + 1
        
        # Update endpoint metrics
        endpoint = request.url.path
        self.metrics["requests_by_endpoint"][endpoint] = self.metrics["requests_by_endpoint"].get(endpoint, 0) + 1
        
        try:
            response = await call_next(request)
            
            # Update successful requests
            if response.status_code < 400:
                self.metrics["successful_requests"] += 1
            else:
                self.metrics["failed_requests"] += 1
            
            return response
            
        except Exception as e:
            # Update failed requests
            self.metrics["failed_requests"] += 1
            raise


class CompressionMiddleware(BaseHTTPMiddleware):
    """Middleware for response compression."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger("api.compression")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and compress response if needed."""
        response = await call_next(request)
        
        # Check if response should be compressed
        if self._should_compress(response):
            # Add compression headers
            response.headers["Content-Encoding"] = "gzip"
            response.headers["Vary"] = "Accept-Encoding"
        
        return response
    
    def _should_compress(self, response: Response) -> bool:
        """Check if response should be compressed."""
        # Only compress JSON responses larger than 1KB
        content_type = response.headers.get("content-type", "")
        content_length = response.headers.get("content-length", "0")
        
        return (
            "application/json" in content_type and
            int(content_length) > 1024
        ) 