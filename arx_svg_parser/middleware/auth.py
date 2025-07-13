"""
Authentication middleware for Arxos SVG-BIM Integration System.

Provides JWT-based authentication with:
- Token validation and refresh
- Role-based access control
- Security headers
- Audit logging
"""

import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import Request, Response, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
import jwt
import structlog

from utils.auth import decode_token, get_current_user, TokenUser, revoke_token
from services.access_control import access_control_service

logger = structlog.get_logger(__name__)

# Security scheme
security = HTTPBearer()

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """JWT-based authentication middleware."""
    
    def __init__(self, app, require_auth: bool = True, 
                 excluded_paths: List[str] = None):
        super().__init__(app)
        self.require_auth = require_auth
        self.excluded_paths = set(excluded_paths or [
            "/auth/login",
            "/auth/register",
            "/auth/refresh",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health"
        ])
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process request through authentication checks."""
        start_time = time.time()
        
        # Check if path requires authentication
        if self._is_excluded_path(request.url.path):
            response = await call_next(request)
            return response
        
        # Extract and validate token
        token = self._extract_token(request)
        if not token:
            if self.require_auth:
                logger.warning("authentication_required",
                             path=request.url.path,
                             method=request.method,
                             client_ip=self._get_client_ip(request))
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            response = await call_next(request)
            return response
        
        # Validate token
        try:
            user = self._validate_token(token)
            if not user:
                logger.warning("invalid_token",
                             path=request.url.path,
                             method=request.method,
                             client_ip=self._get_client_ip(request))
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            
            # Add user to request state
            request.state.user = user
            
            # Log successful authentication
            logger.info("authentication_successful",
                       user_id=user.id,
                       username=user.username,
                       roles=user.roles,
                       path=request.url.path,
                       method=request.method,
                       client_ip=self._get_client_ip(request))
            
            # Process request
            response = await call_next(request)
            
            # Add user info to response headers (for debugging)
            response.headers["X-User-ID"] = user.id
            response.headers["X-User-Roles"] = ",".join(user.roles)
            
            return response
            
        except jwt.ExpiredSignatureError:
            logger.warning("token_expired",
                          path=request.url.path,
                          method=request.method,
                          client_ip=self._get_client_ip(request))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.InvalidTokenError as e:
            logger.warning("invalid_token_error",
                          path=request.url.path,
                          method=request.method,
                          error=str(e),
                          client_ip=self._get_client_ip(request))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            logger.error("authentication_error",
                        path=request.url.path,
                        method=request.method,
                        error=str(e),
                        error_type=type(e).__name__,
                        client_ip=self._get_client_ip(request))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication failed"
            )
    
    def _is_excluded_path(self, path: str) -> bool:
        """Check if path is excluded from authentication."""
        return path in self.excluded_paths or any(
            path.startswith(excluded) for excluded in self.excluded_paths
        )
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from request."""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None
        
        if not auth_header.startswith("Bearer "):
            return None
        
        return auth_header[7:]  # Remove "Bearer " prefix
    
    def _validate_token(self, token: str) -> Optional[TokenUser]:
        """Validate JWT token and return user."""
        try:
            payload = decode_token(token)
            
            # Check token type
            if payload.get("type") != "access":
                return None
            
            # Create TokenUser object
            user = TokenUser(
                id=payload.get("id"),
                username=payload.get("username"),
                roles=payload.get("roles", []),
                is_active=payload.get("is_active", True)
            )
            
            return user
            
        except Exception as e:
            logger.error("token_validation_failed",
                        error=str(e),
                        error_type=type(e).__name__)
            return None
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        if ip := request.headers.get("X-Forwarded-For"):
            return ip.split(",")[0].strip()
        if ip := request.headers.get("X-Real-IP"):
            return ip
        if ip := request.headers.get("X-Client-IP"):
            return ip
        
        return request.client.host if request.client else "unknown"

class RoleBasedAccessMiddleware(BaseHTTPMiddleware):
    """Role-based access control middleware."""
    
    def __init__(self, app, required_roles: List[str] = None, 
                 excluded_paths: List[str] = None):
        super().__init__(app)
        self.required_roles = required_roles or []
        self.excluded_paths = set(excluded_paths or [])
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Check role-based access."""
        # Check if path is excluded
        if request.url.path in self.excluded_paths:
            response = await call_next(request)
            return response
        
        # Get user from request state
        user = getattr(request.state, 'user', None)
        if not user:
            logger.warning("access_denied_no_user",
                          path=request.url.path,
                          method=request.method,
                          client_ip=self._get_client_ip(request))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Check if user has required roles
        if self.required_roles and not self._has_required_roles(user, self.required_roles):
            self._log_access_denied(request, user)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Log successful access
        self._log_access_granted(request, user)
        
        response = await call_next(request)
        return response
    
    def _has_required_roles(self, user: TokenUser, required_roles: List[str]) -> bool:
        """Check if user has any of the required roles."""
        return any(role in user.roles for role in required_roles)
    
    def _log_access_denied(self, request: Request, user: TokenUser):
        """Log access denied events."""
        logger.warning("access_denied",
                      user_id=user.id,
                      user_roles=user.roles,
                      required_roles=self.required_roles,
                      path=request.url.path,
                      method=request.method,
                      client_ip=self._get_client_ip(request))
        
        # Log to audit system
        access_control_service.log_audit_event(
            user_id=user.id,
            action="access_denied",
            resource_type="api",
            resource_id=request.url.path,
            details={"required_roles": self.required_roles, "user_roles": user.roles},
            ip_address=self._get_client_ip(request),
            user_agent=request.headers.get("User-Agent", ""),
            success=False
        )
    
    def _log_access_granted(self, request: Request, user: TokenUser):
        """Log access granted events."""
        logger.info("access_granted",
                   user_id=user.id,
                   user_roles=user.roles,
                   path=request.url.path,
                   method=request.method,
                   client_ip=self._get_client_ip(request))
        
        # Log to audit system
        access_control_service.log_audit_event(
            user_id=user.id,
            action="access_granted",
            resource_type="api",
            resource_id=request.url.path,
            details={"user_roles": user.roles},
            ip_address=self._get_client_ip(request),
            user_agent=request.headers.get("User-Agent", ""),
            success=True
        )
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        if ip := request.headers.get("X-Forwarded-For"):
            return ip.split(",")[0].strip()
        if ip := request.headers.get("X-Real-IP"):
            return ip
        if ip := request.headers.get("X-Client-IP"):
            return ip
        
        return request.client.host if request.client else "unknown"

class TokenRefreshMiddleware(BaseHTTPMiddleware):
    """Token refresh middleware."""
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Handle token refresh logic."""
        response = await call_next(request)
        
        # Check if response indicates token refresh is needed
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            # Check if we can refresh the token
            refresh_token = self._extract_refresh_token(request)
            if refresh_token:
                try:
                    new_tokens = await self._refresh_tokens(refresh_token)
                    if new_tokens:
                        # Add new tokens to response headers
                        response.headers["X-New-Access-Token"] = new_tokens["access_token"]
                        response.headers["X-New-Refresh-Token"] = new_tokens["refresh_token"]
                        response.headers["X-Token-Refreshed"] = "true"
                        
                        logger.info("token_refreshed",
                                  path=request.url.path,
                                  method=request.method)
                except Exception as e:
                    logger.error("token_refresh_failed",
                               error=str(e),
                               error_type=type(e).__name__,
                               path=request.url.path,
                               method=request.method)
        
        return response
    
    def _extract_refresh_token(self, request: Request) -> Optional[str]:
        """Extract refresh token from request."""
        # Check for refresh token in headers or body
        refresh_token = request.headers.get("X-Refresh-Token")
        if refresh_token:
            return refresh_token
        
        return None
    
    async def _refresh_tokens(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """Refresh access token using refresh token."""
        try:
            # This would typically call your token refresh service
            # For now, return None to indicate no refresh
            return None
        except Exception as e:
            logger.error("token_refresh_error",
                        error=str(e),
                        error_type=type(e).__name__)
            return None

# FastAPI dependencies for role-based access
def require_roles(*roles: str):
    """Dependency to require specific roles."""
    def role_checker(request: Request):
        user = getattr(request.state, 'user', None)
        if not user:
            logger.warning("role_check_failed_no_user",
                          path=request.url.path,
                          method=request.method,
                          required_roles=list(roles))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        if not any(role in user.roles for role in roles):
            logger.warning("role_check_failed_insufficient_roles",
                          user_id=user.id,
                          user_roles=user.roles,
                          required_roles=list(roles),
                          path=request.url.path,
                          method=request.method)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return user
    
    return role_checker

def require_role(role: str):
    """Dependency to require a specific role."""
    def role_checker(request: Request):
        user = getattr(request.state, 'user', None)
        if not user:
            logger.warning("role_check_failed_no_user",
                          path=request.url.path,
                          method=request.method,
                          required_role=role)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        if role not in user.roles:
            logger.warning("role_check_failed_insufficient_roles",
                          user_id=user.id,
                          user_roles=user.roles,
                          required_role=role,
                          path=request.url.path,
                          method=request.method)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required"
            )
        
        return user
    
    return role_checker

def get_current_user_dependency(request: Request) -> TokenUser:
    """Dependency to get current user from request state."""
    user = getattr(request.state, 'user', None)
    if not user:
        logger.warning("get_current_user_failed",
                      path=request.url.path,
                      method=request.method)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user

# Utility functions
def get_user_from_request(request: Request) -> Optional[TokenUser]:
    """Get user from request state."""
    return getattr(request.state, 'user', None)

def is_authenticated(request: Request) -> bool:
    """Check if request is authenticated."""
    return hasattr(request.state, 'user') and request.state.user is not None

def has_role(request: Request, role: str) -> bool:
    """Check if user has specific role."""
    user = get_user_from_request(request)
    return user is not None and role in user.roles

def has_any_role(request: Request, roles: List[str]) -> bool:
    """Check if user has any of the specified roles."""
    user = get_user_from_request(request)
    return user is not None and any(role in user.roles for role in roles)

# Global middleware instances
auth_middleware = AuthenticationMiddleware(None)
role_middleware = RoleBasedAccessMiddleware(None)
token_refresh_middleware = TokenRefreshMiddleware(None) 