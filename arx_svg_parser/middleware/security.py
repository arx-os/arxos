"""
Security middleware for Arxos SVG-BIM Integration System.

Provides security features including:
- Rate limiting
- CORS handling
- Security headers
- Request sanitization
- Audit logging
"""

import time
import hashlib
import structlog
from typing import Dict, List, Optional, Tuple
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from collections import defaultdict
import asyncio

logger = structlog.get_logger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with structured logging."""
    
    def __init__(self, app, requests_per_minute: int = 60, 
                 burst_limit: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.requests = defaultdict(list)
        self.lock = asyncio.Lock()
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Apply rate limiting with structured logging."""
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        async with self.lock:
            # Clean old requests
            self._clean_old_requests(client_ip, current_time)
            
            # Check rate limit
            if not self._is_allowed(client_ip, current_time):
                logger.warning("rate_limit_exceeded",
                             client_ip=client_ip,
                             path=request.url.path,
                             method=request.method,
                             limit=self.requests_per_minute,
                             current=len(self.requests[client_ip]))
                
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
            
            # Add current request
            self.requests[client_ip].append(current_time)
        
        logger.debug("rate_limit_check_passed",
                    client_ip=client_ip,
                    path=request.url.path,
                    method=request.method,
                    current_requests=len(self.requests[client_ip]))
        
        response = await call_next(request)
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        if ip := request.headers.get("X-Forwarded-For"):
            return ip.split(",")[0].strip()
        if ip := request.headers.get("X-Real-IP"):
            return ip
        if ip := request.headers.get("X-Client-IP"):
            return ip
        
        return request.client.host if request.client else "unknown"
    
    def _clean_old_requests(self, client_ip: str, current_time: float):
        """Remove requests older than 1 minute."""
        cutoff_time = current_time - 60
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > cutoff_time
        ]
    
    def _is_allowed(self, client_ip: str, current_time: float) -> bool:
        """Check if request is allowed under rate limit."""
        recent_requests = len(self.requests[client_ip])
        return recent_requests < self.requests_per_minute

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses."""
    
    def __init__(self, app):
        super().__init__(app)
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Add security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        logger.debug("security_headers_added",
                    path=request.url.path,
                    method=request.method,
                    headers_count=len(self.security_headers))
        
        return response

class RequestSanitizationMiddleware(BaseHTTPMiddleware):
    """Sanitize incoming requests for security."""
    
    def __init__(self, app):
        super().__init__(app)
        self.suspicious_patterns = [
            r"<script",
            r"javascript:",
            r"onload=",
            r"onerror=",
            r"onclick=",
            r"sqlmap",
            r"union select",
            r"drop table",
            r"delete from",
            r"insert into"
        ]
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Sanitize request for suspicious content."""
        client_ip = self._get_client_ip(request)
        
        # Check URL for suspicious patterns
        if self._contains_suspicious_patterns(str(request.url)):
            logger.warning("suspicious_request_detected",
                          client_ip=client_ip,
                          path=request.url.path,
                          method=request.method,
                          suspicious_url=str(request.url))
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Suspicious request detected"
            )
        
        # Check headers for suspicious content
        suspicious_headers = self._check_suspicious_headers(request.headers)
        if suspicious_headers:
            logger.warning("suspicious_headers_detected",
                          client_ip=client_ip,
                          path=request.url.path,
                          method=request.method,
                          suspicious_headers=suspicious_headers)
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Suspicious headers detected"
            )
        
        response = await call_next(request)
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        if ip := request.headers.get("X-Forwarded-For"):
            return ip.split(",")[0].strip()
        if ip := request.headers.get("X-Real-IP"):
            return ip
        if ip := request.headers.get("X-Client-IP"):
            return ip
        
        return request.client.host if request.client else "unknown"
    
    def _contains_suspicious_patterns(self, text: str) -> bool:
        """Check if text contains suspicious patterns."""
        import re
        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in self.suspicious_patterns)
    
    def _check_suspicious_headers(self, headers) -> List[str]:
        """Check headers for suspicious content."""
        suspicious = []
        for name, value in headers.items():
            if self._contains_suspicious_patterns(f"{name}: {value}"):
                suspicious.append(f"{name}: {value}")
        return suspicious

class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Audit logging middleware for security events."""
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Log security-relevant events."""
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "unknown")
        
        # Log request details for audit
        logger.info("audit_request",
                   client_ip=client_ip,
                   user_agent=user_agent,
                   path=request.url.path,
                   method=request.method,
                   content_length=request.headers.get("Content-Length", "0"),
                   referer=request.headers.get("Referer", "unknown"))
        
        try:
            response = await call_next(request)
            
            # Log response details
            logger.info("audit_response",
                       client_ip=client_ip,
                       path=request.url.path,
                       method=request.method,
                       status_code=response.status_code,
                       response_size=response.headers.get("Content-Length", "0"))
            
            return response
            
        except Exception as e:
            # Log security-relevant exceptions
            logger.error("audit_exception",
                        client_ip=client_ip,
                        path=request.url.path,
                        method=request.method,
                        error=str(e),
                        error_type=type(e).__name__)
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        if ip := request.headers.get("X-Forwarded-For"):
            return ip.split(",")[0].strip()
        if ip := request.headers.get("X-Real-IP"):
            return ip
        if ip := request.headers.get("X-Client-IP"):
            return ip
        
        return request.client.host if request.client else "unknown"

class CORSMiddleware(BaseHTTPMiddleware):
    """CORS handling middleware."""
    
    def __init__(self, app, allowed_origins: List[str] = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or ["*"]
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Handle CORS preflight and add CORS headers."""
        origin = request.headers.get("Origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
            self._add_cors_headers(response, origin)
            return response
        
        # Process normal request
        response = await call_next(request)
        self._add_cors_headers(response, origin)
        
        logger.debug("cors_headers_added",
                    origin=origin,
                    path=request.url.path,
                    method=request.method)
        
        return response
    
    def _add_cors_headers(self, response: Response, origin: Optional[str]):
        """Add CORS headers to response."""
        if "*" in self.allowed_origins or (origin and origin in self.allowed_origins):
            response.headers["Access-Control-Allow-Origin"] = origin or "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
            response.headers["Access-Control-Allow-Credentials"] = "true"

# Global middleware instances
rate_limit_middleware = RateLimitMiddleware(None)
security_headers_middleware = SecurityHeadersMiddleware(None)
request_sanitization_middleware = RequestSanitizationMiddleware(None)
audit_logging_middleware = AuditLoggingMiddleware(None)
cors_middleware = CORSMiddleware(None) 