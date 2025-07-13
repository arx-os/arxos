import time
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional

logger = structlog.get_logger(__name__)

class LoggingContextMiddleware(BaseHTTPMiddleware):
    """Middleware to bind request context to structlog contextvars."""
    
    async def dispatch(self, request, call_next):
        start_time = time.time()
        
        # Clear previous context
        structlog.contextvars.clear_contextvars()
        
        # Generate request ID if not present
        request_id = request.headers.get("X-Request-ID", f"req_{int(time.time() * 1000)}")
        
        # Bind comprehensive request context
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            path=request.url.path,
            method=request.method,
            client_ip=self._get_client_ip(request),
            user_agent=request.headers.get("User-Agent", "unknown"),
            content_length=request.headers.get("Content-Length", "0"),
            content_type=request.headers.get("Content-Type", "unknown"),
            referer=request.headers.get("Referer", "unknown"),
            host=request.headers.get("Host", "unknown")
        )
        
        # Add user context if available
        if hasattr(request.state, 'user') and request.state.user:
            structlog.contextvars.bind_contextvars(
                user_id=request.state.user.id,
                user_roles=request.state.user.roles
            )
        
        logger.info("request_started",
                   request_id=request_id,
                   path=request.url.path,
                   method=request.method)
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Add response context
            structlog.contextvars.bind_contextvars(
                status_code=response.status_code,
                response_time=duration,
                response_size=response.headers.get("Content-Length", "0")
            )
            
            logger.info("request_completed",
                       request_id=request_id,
                       status_code=response.status_code,
                       response_time=duration)
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            logger.error("request_failed",
                        request_id=request_id,
                        error=str(e),
                        error_type=type(e).__name__,
                        response_time=duration)
            raise
    
    def _get_client_ip(self, request) -> str:
        """Get client IP address from various headers."""
        # Check for forwarded headers
        if forwarded_for := request.headers.get("X-Forwarded-For"):
            return forwarded_for.split(",")[0].strip()
        if real_ip := request.headers.get("X-Real-IP"):
            return real_ip
        if client_ip := request.headers.get("X-Client-IP"):
            return client_ip
        
        # Fallback to client host
        return request.client.host if request.client else "unknown" 