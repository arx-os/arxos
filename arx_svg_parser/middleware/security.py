"""
Security middleware for Arxos SVG-BIM Integration System.

Provides comprehensive security features:
- Rate limiting
- Security headers
- Request validation
- IP filtering
- Audit logging
"""

import time
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import Request, Response, HTTPException, status
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
import logging

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware."""
    
    def __init__(self, app, rate_limit_per_minute: int = 60, 
                 blocked_ips: List[str] = None, allowed_ips: List[str] = None):
        super().__init__(app)
        self.rate_limit_per_minute = rate_limit_per_minute
        self.blocked_ips = set(blocked_ips or [])
        self.allowed_ips = set(allowed_ips or [])
        self.request_counts: Dict[str, List[float]] = {}
        self.suspicious_ips: Dict[str, int] = {}
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process request through security checks."""
        start_time = time.time()
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check IP filtering
        if not self._check_ip_access(client_ip):
            self._log_security_event(request, "IP_BLOCKED", client_ip)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Check rate limiting
        if not self._check_rate_limit(client_ip):
            self._log_security_event(request, "RATE_LIMIT_EXCEEDED", client_ip)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        # Validate request
        if not self._validate_request(request):
            self._log_security_event(request, "INVALID_REQUEST", client_ip)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid request"
            )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Add security headers
            self._add_security_headers(response)
            
            # Log successful request
            duration = time.time() - start_time
            self._log_request(request, response, client_ip, duration, success=True)
            
            return response
            
        except Exception as e:
            # Log failed request
            duration = time.time() - start_time
            self._log_request(request, None, client_ip, duration, success=False, error=str(e))
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract real client IP address."""
        # Check for forwarded headers
        if ip := request.headers.get("X-Forwarded-For"):
            return ip.split(",")[0].strip()
        if ip := request.headers.get("X-Real-IP"):
            return ip
        if ip := request.headers.get("X-Client-IP"):
            return ip
        
        return request.client.host if request.client else "unknown"
    
    def _check_ip_access(self, client_ip: str) -> bool:
        """Check if IP is allowed/blocked."""
        # Check blocked IPs
        if client_ip in self.blocked_ips:
            return False
        
        # Check allowed IPs (if specified, only allow listed IPs)
        if self.allowed_ips and client_ip not in self.allowed_ips:
            return False
        
        return True
    
    def _check_rate_limit(self, client_ip: str) -> bool:
        """Check rate limiting for client IP."""
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        if client_ip in self.request_counts:
            self.request_counts[client_ip] = [
                req_time for req_time in self.request_counts[client_ip]
                if req_time > minute_ago
            ]
        
        # Check current request count
        current_requests = len(self.request_counts.get(client_ip, []))
        if current_requests >= self.rate_limit_per_minute:
            return False
        
        # Add current request
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        self.request_counts[client_ip].append(now)
        
        return True
    
    def _validate_request(self, request: Request) -> bool:
        """Validate request for security issues."""
        # Check for suspicious patterns
        user_agent = request.headers.get("User-Agent", "")
        if self._is_suspicious_user_agent(user_agent):
            return False
        
        # Check request size
        content_length = request.headers.get("Content-Length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
            return False
        
        return True
    
    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check if user agent is suspicious."""
        suspicious_patterns = [
            "bot", "crawler", "spider", "scraper", "curl", "wget",
            "python-requests", "go-http-client", "java-http-client"
        ]
        
        user_agent_lower = user_agent.lower()
        return any(pattern in user_agent_lower for pattern in suspicious_patterns)
    
    def _add_security_headers(self, response: Response):
        """Add security headers to response."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    def _log_request(self, request: Request, response: Optional[Response], 
                    client_ip: str, duration: float, success: bool, error: str = None):
        """Log request details."""
        log_data = {
            "method": request.method,
            "url": str(request.url),
            "client_ip": client_ip,
            "user_agent": request.headers.get("User-Agent", ""),
            "duration": duration,
            "success": success,
            "status_code": response.status_code if response else None,
            "error": error
        }
        
        if success:
            logger.info(f"Request processed: {log_data}")
        else:
            logger.warning(f"Request failed: {log_data}")
    
    def _log_security_event(self, request: Request, event_type: str, client_ip: str):
        """Log security events."""
        log_data = {
            "event_type": event_type,
            "method": request.method,
            "url": str(request.url),
            "client_ip": client_ip,
            "user_agent": request.headers.get("User-Agent", ""),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.warning(f"Security event: {log_data}")

class PasswordSecurity:
    """Password security utilities."""
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Hash password with salt."""
        if not salt:
            salt = secrets.token_hex(16)
        
        # Combine password with salt
        salted_password = password + salt
        hashed = hashlib.sha256(salted_password.encode()).hexdigest()
        
        return hashed, salt
    
    @staticmethod
    def verify_password(password: str, hashed_password: str, salt: str) -> bool:
        """Verify password against hash."""
        salted_password = password + salt
        computed_hash = hashlib.sha256(salted_password.encode()).hexdigest()
        return computed_hash == hashed_password
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """Validate password strength."""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            return False, "Password must contain at least one special character"
        
        return True, "Password meets strength requirements"
    
    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """Generate a secure random password."""
        import string
        characters = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
        return ''.join(secrets.choice(characters) for _ in range(length))

class SessionSecurity:
    """Session security utilities."""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = timedelta(hours=24)
    
    def create_session(self, user_id: str, ip_address: str = None, 
                     user_agent: str = None) -> str:
        """Create a new secure session."""
        session_id = secrets.token_urlsafe(32)
        created_at = datetime.utcnow()
        expires_at = created_at + self.session_timeout
        
        session_data = {
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "created_at": created_at,
            "expires_at": expires_at,
            "is_active": True
        }
        
        self.active_sessions[session_id] = session_data
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Validate session and return session data if valid."""
        if session_id not in self.active_sessions:
            return None
        
        session_data = self.active_sessions[session_id]
        
        # Check if session is active and not expired
        if not session_data["is_active"] or datetime.utcnow() > session_data["expires_at"]:
            del self.active_sessions[session_id]
            return None
        
        return session_data
    
    def revoke_session(self, session_id: str) -> bool:
        """Revoke a session."""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["is_active"] = False
            return True
        return False
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions."""
        now = datetime.utcnow()
        expired_sessions = [
            session_id for session_id, session_data in self.active_sessions.items()
            if now > session_data["expires_at"]
        ]
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]

class RateLimiter:
    """Rate limiting utility."""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.request_times: Dict[str, List[float]] = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed for identifier."""
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        if identifier in self.request_times:
            self.request_times[identifier] = [
                req_time for req_time in self.request_times[identifier]
                if req_time > minute_ago
            ]
        
        # Check current request count
        current_requests = len(self.request_times.get(identifier, []))
        if current_requests >= self.requests_per_minute:
            return False
        
        # Add current request
        if identifier not in self.request_times:
            self.request_times[identifier] = []
        self.request_times[identifier].append(now)
        
        return True
    
    def get_remaining_requests(self, identifier: str) -> int:
        """Get remaining requests for identifier."""
        now = time.time()
        minute_ago = now - 60
        
        if identifier in self.request_times:
            recent_requests = [
                req_time for req_time in self.request_times[identifier]
                if req_time > minute_ago
            ]
            return max(0, self.requests_per_minute - len(recent_requests))
        
        return self.requests_per_minute

# Global instances
security_middleware = SecurityMiddleware(None)
password_security = PasswordSecurity()
session_security = SessionSecurity()
rate_limiter = RateLimiter() 