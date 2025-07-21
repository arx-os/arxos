"""
Security Middleware for Arxos.

This module provides security middleware components including:
- Request validation and sanitization
- Rate limiting and DDoS protection
- Security headers injection
- Request/response logging
"""

import time
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from collections import defaultdict, deque
import threading
from .validation import InputValidator, SecurityValidator, ValidationError, SecurityError
from .authentication import AuthService, RBACService, User, Permission


@dataclass
class RequestContext:
    """Request context for security processing."""
    request_id: str
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    method: str
    path: str
    timestamp: datetime
    headers: Dict[str, str]
    body: Optional[str] = None


@dataclass
class SecurityEvent:
    """Security event for monitoring."""
    event_type: str
    severity: str
    timestamp: datetime
    request_id: str
    user_id: Optional[str]
    ip_address: str
    details: Dict[str, Any]
    threat_indicators: List[str] = None


class RateLimitMiddleware:
    """Rate limiting middleware for DDoS protection."""
    
    def __init__(self, requests_per_minute: int = 60, burst_limit: int = 100):
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.rate_limits = defaultdict(lambda: deque())
        self.lock = threading.Lock()
    
    def check_rate_limit(self, ip_address: str) -> bool:
        """Check if request is within rate limits."""
        current_time = time.time()
        
        with self.lock:
            # Clean old entries
            while (self.rate_limits[ip_address] and 
                   current_time - self.rate_limits[ip_address][0] > 60):
                self.rate_limits[ip_address].popleft()
            
            # Check rate limit
            if len(self.rate_limits[ip_address]) >= self.requests_per_minute:
                return False
            
            # Add current request
            self.rate_limits[ip_address].append(current_time)
            return True
    
    def get_rate_limit_info(self, ip_address: str) -> Dict[str, Any]:
        """Get rate limit information for IP address."""
        with self.lock:
            current_time = time.time()
            recent_requests = [
                req_time for req_time in self.rate_limits[ip_address]
                if current_time - req_time <= 60
            ]
            
            return {
                'requests_in_last_minute': len(recent_requests),
                'limit': self.requests_per_minute,
                'remaining': max(0, self.requests_per_minute - len(recent_requests)),
                'reset_time': current_time + 60
            }


class SecurityMiddleware:
    """Main security middleware for request processing."""
    
    def __init__(self, auth_service: AuthService, rbac_service: RBACService):
        self.auth_service = auth_service
        self.rbac_service = rbac_service
        self.input_validator = InputValidator()
        self.security_validator = SecurityValidator()
        self.rate_limiter = RateLimitMiddleware()
        self.security_events = []
        self.lock = threading.Lock()
    
    def process_request(self, request_context: RequestContext) -> Dict[str, Any]:
        """Process incoming request with security checks."""
        try:
            # Rate limiting
            if not self.rate_limiter.check_rate_limit(request_context.ip_address):
                self._log_security_event(
                    'rate_limit_exceeded',
                    'medium',
                    request_context,
                    {'rate_limit_info': self.rate_limiter.get_rate_limit_info(request_context.ip_address)}
                )
                raise SecurityError("Rate limit exceeded")
            
            # Input validation
            validated_data = self._validate_request_data(request_context)
            
            # Threat detection
            threats = self._detect_threats(request_context)
            if threats:
                self._log_security_event(
                    'threat_detected',
                    'high',
                    request_context,
                    {'threats': threats}
                )
                raise SecurityError(f"Security threats detected: {threats}")
            
            # Authentication and authorization
            user = self._authenticate_user(request_context)
            if user:
                self._authorize_request(user, request_context)
            
            return {
                'validated_data': validated_data,
                'user': user,
                'security_headers': self._generate_security_headers()
            }
            
        except Exception as e:
            self._log_security_event(
                'security_error',
                'high',
                request_context,
                {'error': str(e)}
            )
            raise
    
    def _validate_request_data(self, request_context: RequestContext) -> Dict[str, Any]:
        """Validate request data for security."""
        validated_data = {}
        
        # Validate headers
        for header_name, header_value in request_context.headers.items():
            if header_value:
                # Basic header validation
                if len(header_value) > 8192:  # 8KB limit
                    raise ValidationError(f"Header '{header_name}' too long")
                
                # Check for suspicious header patterns
                if self.security_validator.detect_threats(header_value):
                    raise SecurityError(f"Suspicious content in header '{header_name}'")
        
        # Validate body if present
        if request_context.body:
            if len(request_context.body) > 1048576:  # 1MB limit
                raise ValidationError("Request body too large")
            
            # Check for threats in body
            body_threats = self.security_validator.detect_threats(request_context.body)
            if body_threats:
                raise SecurityError("Suspicious content in request body")
            
            # Try to parse as JSON
            try:
                body_data = json.loads(request_context.body)
                validated_data['body'] = body_data
            except json.JSONDecodeError:
                validated_data['body'] = request_context.body
        
        return validated_data
    
    def _detect_threats(self, request_context: RequestContext) -> List[Dict[str, Any]]:
        """Detect security threats in request."""
        threats = []
        
        # Check URL path
        path_threats = self.security_validator.detect_threats(request_context.path)
        threats.extend(path_threats)
        
        # Check user agent
        if request_context.user_agent:
            ua_threats = self.security_validator.detect_threats(request_context.user_agent)
            threats.extend(ua_threats)
        
        # Check headers
        for header_value in request_context.headers.values():
            if header_value:
                header_threats = self.security_validator.detect_threats(header_value)
                threats.extend(header_threats)
        
        # Check body
        if request_context.body:
            body_threats = self.security_validator.detect_threats(request_context.body)
            threats.extend(body_threats)
        
        return threats
    
    def _authenticate_user(self, request_context: RequestContext) -> Optional[User]:
        """Authenticate user from request."""
        # Extract token from headers
        auth_header = request_context.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        try:
            payload = self.auth_service.verify_token(token)
            if payload:
                # Create user object from token payload
                user = User(
                    id=payload['user_id'],
                    username=payload['username'],
                    email="",  # Not stored in token
                    roles=[],  # Will be loaded from database
                    attributes={}
                )
                return user
        except Exception as e:
            self._log_security_event(
                'authentication_failed',
                'medium',
                request_context,
                {'error': str(e)}
            )
        
        return None
    
    def _authorize_request(self, user: User, request_context: RequestContext):
        """Authorize request based on user permissions."""
        # Check if user has permission for the requested resource
        resource_type = self._get_resource_type(request_context.path)
        action = self._get_action(request_context.method)
        
        # Basic authorization check
        if not self.rbac_service.check_permission(user, action):
            self._log_security_event(
                'authorization_failed',
                'high',
                request_context,
                {
                    'user_id': user.id,
                    'resource_type': resource_type,
                    'action': action
                }
            )
            raise SecurityError("Access denied")
    
    def _get_resource_type(self, path: str) -> str:
        """Extract resource type from path."""
        path_parts = path.split('/')
        if len(path_parts) > 1:
            return path_parts[1]
        return 'default'
    
    def _get_action(self, method: str) -> Permission:
        """Map HTTP method to permission."""
        method_permissions = {
            'GET': Permission.READ,
            'POST': Permission.WRITE,
            'PUT': Permission.WRITE,
            'PATCH': Permission.WRITE,
            'DELETE': Permission.DELETE
        }
        return method_permissions.get(method, Permission.READ)
    
    def _generate_security_headers(self) -> Dict[str, str]:
        """Generate comprehensive security headers."""
        return {
            # OWASP Top 10 2021 - A05:2021 Security Misconfiguration
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; frame-src 'none'; object-src 'none'; base-uri 'self'; form-action 'self'; upgrade-insecure-requests",
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()',
            
            # Additional security headers
            'X-Permitted-Cross-Domain-Policies': 'none',
            'X-Download-Options': 'noopen',
            'X-DNS-Prefetch-Control': 'off',
            'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
            
            # Custom security headers
            'X-Security-Scanner': 'Arxos-Security-Engine',
            'X-Content-Security': 'enabled',
            'X-Request-ID': self._generate_request_id(),
        }
    
    def _log_security_event(self, event_type: str, severity: str, 
                           request_context: RequestContext, details: Dict[str, Any]):
        """Log security event for monitoring."""
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            timestamp=datetime.utcnow(),
            request_id=request_context.request_id,
            user_id=request_context.user_id,
            ip_address=request_context.ip_address,
            details=details,
            threat_indicators=self._extract_threat_indicators(details)
        )
        
        with self.lock:
            self.security_events.append(event)
    
    def _extract_threat_indicators(self, details: Dict[str, Any]) -> List[str]:
        """Extract threat indicators from event details."""
        indicators = []
        
        if 'threats' in details:
            for threat in details['threats']:
                indicators.append(threat['type'])
        
        if 'error' in details:
            error = details['error'].lower()
            if 'sql' in error or 'injection' in error:
                indicators.append('sql_injection')
            if 'xss' in error or 'script' in error:
                indicators.append('xss')
            if 'traversal' in error or 'path' in error:
                indicators.append('path_traversal')
        
        return indicators


class RequestLogger:
    """Request logging for security monitoring."""
    
    def __init__(self, log_file: str = "security_requests.log"):
        self.log_file = log_file
        self.log_format = "{timestamp} | {request_id} | {ip_address} | {method} | {path} | {status_code} | {response_time} | {user_id}"
    
    def log_request(self, request_context: RequestContext, response_status: int, 
                   response_time: float, user_id: Optional[str] = None):
        """Log request details."""
        log_entry = self.log_format.format(
            timestamp=request_context.timestamp.isoformat(),
            request_id=request_context.request_id,
            ip_address=request_context.ip_address,
            method=request_context.method,
            path=request_context.path,
            status_code=response_status,
            response_time=f"{response_time:.3f}",
            user_id=user_id or "anonymous"
        )
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry + '\n')
    
    def get_request_stats(self, time_window: timedelta = timedelta(hours=1)) -> Dict[str, Any]:
        """Get request statistics for monitoring."""
        stats = {
            'total_requests': 0,
            'unique_ips': set(),
            'status_codes': defaultdict(int),
            'response_times': [],
            'errors': 0
        }
        
        cutoff_time = datetime.utcnow() - time_window
        
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    parts = line.strip().split(' | ')
                    if len(parts) >= 7:
                        timestamp_str = parts[0]
                        try:
                            timestamp = datetime.fromisoformat(timestamp_str)
                            if timestamp >= cutoff_time:
                                stats['total_requests'] += 1
                                stats['unique_ips'].add(parts[2])
                                stats['status_codes'][parts[5]] += 1
                                
                                try:
                                    response_time = float(parts[6])
                                    stats['response_times'].append(response_time)
                                except ValueError:
                                    pass
                                
                                if parts[5].startswith('4') or parts[5].startswith('5'):
                                    stats['errors'] += 1
                        except ValueError:
                            continue
        except FileNotFoundError:
            pass
        
        # Calculate averages
        if stats['response_times']:
            stats['avg_response_time'] = sum(stats['response_times']) / len(stats['response_times'])
        else:
            stats['avg_response_time'] = 0
        
        stats['unique_ips'] = len(stats['unique_ips'])
        stats['status_codes'] = dict(stats['status_codes'])
        
        return stats 

    def _generate_request_id(self) -> str:
        """Generate unique request ID for tracking."""
        import uuid
        return str(uuid.uuid4())


class AdvancedRateLimitMiddleware:
    """Advanced rate limiting middleware with multi-tier protection."""
    
    def __init__(self):
        # Multi-tier rate limits
        self.rate_limits = {
            'api': {'requests': 1000, 'window': 3600},  # 1000 requests per hour
            'auth': {'requests': 5, 'window': 300},      # 5 login attempts per 5 minutes
            'upload': {'requests': 10, 'window': 3600},   # 10 uploads per hour
            'admin': {'requests': 100, 'window': 3600},   # 100 admin actions per hour
            'default': {'requests': 60, 'window': 60}     # 60 requests per minute
        }
        
        self.rate_limit_data = defaultdict(lambda: defaultdict(lambda: deque()))
        self.lock = threading.Lock()
    
    def check_rate_limit(self, ip_address: str, endpoint_type: str = 'default') -> bool:
        """Check if request is within rate limits for specific endpoint type."""
        current_time = time.time()
        limit_config = self.rate_limits.get(endpoint_type, self.rate_limits['default'])
        
        with self.lock:
            # Clean old entries
            while (self.rate_limit_data[ip_address][endpoint_type] and 
                   current_time - self.rate_limit_data[ip_address][endpoint_type][0] > limit_config['window']):
                self.rate_limit_data[ip_address][endpoint_type].popleft()
            
            # Check rate limit
            if len(self.rate_limit_data[ip_address][endpoint_type]) >= limit_config['requests']:
                return False
            
            # Add current request
            self.rate_limit_data[ip_address][endpoint_type].append(current_time)
            return True
    
    def get_rate_limit_info(self, ip_address: str, endpoint_type: str = 'default') -> Dict[str, Any]:
        """Get rate limit information for IP address and endpoint type."""
        with self.lock:
            current_time = time.time()
            limit_config = self.rate_limits.get(endpoint_type, self.rate_limits['default'])
            
            recent_requests = [
                req_time for req_time in self.rate_limit_data[ip_address][endpoint_type]
                if current_time - req_time <= limit_config['window']
            ]
            
            return {
                'endpoint_type': endpoint_type,
                'requests_in_window': len(recent_requests),
                'limit': limit_config['requests'],
                'window_seconds': limit_config['window'],
                'remaining': max(0, limit_config['requests'] - len(recent_requests)),
                'reset_time': current_time + limit_config['window'],
                'is_blocked': len(recent_requests) >= limit_config['requests']
            }
    
    def get_all_rate_limits(self, ip_address: str) -> Dict[str, Dict[str, Any]]:
        """Get rate limit information for all endpoint types."""
        return {
            endpoint_type: self.get_rate_limit_info(ip_address, endpoint_type)
            for endpoint_type in self.rate_limits.keys()
        }
    
    def reset_rate_limit(self, ip_address: str, endpoint_type: str = None):
        """Reset rate limit for IP address and optionally specific endpoint type."""
        with self.lock:
            if endpoint_type:
                self.rate_limit_data[ip_address][endpoint_type].clear()
            else:
                self.rate_limit_data[ip_address].clear() 