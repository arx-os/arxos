"""
Custom Authentication Dependencies for Arxos

Custom authentication implementation built specifically for Arxos
without external dependencies. Handles user validation and authorization.
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import Request, HTTPException, Depends
from datetime import datetime
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import base64
import hmac
import hashlib
import json

from application.config import get_config
# Avoid circular/invalid imports for core security here; use local types (Dict) instead


# Security scheme (kept for future explicit token deps; not used in centralized checks yet)
security = HTTPBearer(auto_error=False)


class AuthManager:
    """
    Custom Authentication Manager for Arxos

    Handles user authentication and authorization without external dependencies.
    Built specifically for Arxos using custom authentication logic.
    """

    def __init__(self):
        """Initialize authentication manager"""
        self.logger = logging.getLogger(__name__)
        self.config = get_config()

        # User session storage (in production, use database)
        self.user_sessions: Dict[str, Dict[str, Any]] = {}

        # API key storage (in production, use secure storage)
        self.api_keys: Dict[str, Dict[str, Any]] = {
            'default-key': {
                'user_id': 'anonymous',
                'permissions': ['pdf_analysis', 'schedule_generation'],
                'active': True
            }
        }

        self.logger.info("Custom Authentication Manager initialized")

    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate API key"""
        if api_key in self.api_keys:
            key_data = self.api_keys[api_key]
            if key_data.get('active', False):
                return key_data
        return None

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token using HS256 with configured secret and expiry checks.

        No external libs to honor project constraints.
        """
        try:
            if token.startswith('Bearer '):
                token = token[7:]

            # Parse JWT (header.payload.signature)
            parts = token.split('.')
            if len(parts) != 3:
                return None

            def _b64url_decode(data: str) -> bytes:
                padding = '=' * (-len(data) % 4)
                return base64.urlsafe_b64decode(data + padding)

            header_bytes = _b64url_decode(parts[0])
            payload_bytes = _b64url_decode(parts[1])
            signature = parts[2]

            header = json.loads(header_bytes.decode('utf-8'))
            payload = json.loads(payload_bytes.decode('utf-8'))

            # Algorithm enforcement
            alg = header.get('alg')
            expected_alg = self.config.get('security', {}).get('algorithm', 'HS256')
            if alg != expected_alg:
                return None

            # Verify signature
            signing_input = f"{parts[0]}.{parts[1]}".encode('utf-8')
            secret = self.config.get('security', {}).get('secret_key', '')
            if not secret:
                self.logger.error("Missing JWT secret_key in configuration")
                return None
            digest = hmac.new(secret.encode('utf-8'), signing_input, hashlib.sha256).digest()
            expected_sig = base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')
            if not hmac.compare_digest(signature, expected_sig):
                return None

            # Expiration check (exp is seconds since epoch)
            exp = payload.get('exp')
            if exp is not None:
                from time import time
                if time() > float(exp):
                    return None

            # Normalize user info
            user_id = payload.get('sub') or payload.get('user_id') or 'authenticated_user'
            permissions = payload.get('permissions') or self.get_user_permissions(user_id)

            return {
                'user_id': user_id,
                'permissions': permissions,
                'token_type': 'jwt',
                'claims': payload,
            }

        except Exception as e:
            self.logger.error(f"Token validation error: {e}")
            return None

    def get_user_permissions(self, user_id: str) -> list[str]:
        """Get user permissions"""
        # Simplified permission system
        # In production, use database-based permissions
        default_permissions = ['pdf_analysis', 'schedule_generation']

        if user_id == 'anonymous':
            return ['pdf_analysis']
        elif user_id == 'authenticated_user':
            return default_permissions + ['cost_estimation', 'timeline_generation']
        else:
            return default_permissions

    def check_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has specific permission"""
        permissions = self.get_user_permissions(user_id)
        return permission in permissions

    def create_session(self, user_id: str, session_data: Dict[str, Any]) -> str:
        """Create user session"""
        import uuid
        session_id = str(uuid.uuid4())
        self.user_sessions[session_id] = {
            'user_id': user_id,
            'created_at': session_data.get('created_at'),
            'permissions': self.get_user_permissions(user_id),
            **session_data
        }

        self.logger.info(f"Created session for user: {user_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get user session"""
        return self.user_sessions.get(session_id)

    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate user session"""
        if session_id in self.user_sessions:
            del self.user_sessions[session_id]
            self.logger.info(f"Invalidated session: {session_id}")
            return True
        return False


# Global authentication manager
_auth_manager = AuthManager()

# Public type alias for route dependencies
User = Dict[str, Any]


async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Get current user from request import request
    This is a simplified authentication implementation.
    In production, use proper JWT validation and database lookups.
    """
    try:
        # Check for API key in headers
        api_key = request.headers.get('X-API-Key')
        if api_key:
            key_data = _auth_manager.validate_api_key(api_key)
            if key_data:
                return {
                    'id': key_data['user_id'],
                    'permissions': key_data['permissions'],
                    'auth_type': 'api_key'
                }

        # Check for Bearer token
        auth_header = request.headers.get('Authorization')
        if auth_header:
            token_data = _auth_manager.validate_token(auth_header)
            if token_data:
                return {
                    'id': token_data['user_id'],
                    'permissions': token_data['permissions'],
                    'auth_type': 'jwt',
                    'claims': token_data.get('claims')
                }

        # Check for session cookie
        session_id = request.cookies.get('session_id')
        if session_id:
            session_data = _auth_manager.get_session(session_id)
            if session_data:
                return {
                    'id': session_data['user_id'],
                    'permissions': session_data['permissions'],
                    'auth_type': 'session'
                }

        # Return anonymous user if no authentication found
        return {
            'id': 'anonymous',
            'permissions': ['pdf_analysis'],
            'auth_type': 'anonymous'
        }

    except Exception as e:
        logging.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Authentication failed"
        )


async def get_current_user_required(request: Request) -> Dict[str, Any]:
    """
    Get current user with authentication required

    Raises HTTPException if no valid authentication is found.
    """
    user = await get_current_user(request)

    if user['id'] == 'anonymous':
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    return user


async def require_permission(permission: str):
    """
    Dependency to require specific permission

    Usage:
        @app.get("/protected")
        async def protected_route(user = Depends(require_permission("pdf_analysis"))):
            return {"message": "Access granted"}
    """
    async def _require_permission(request: Request) -> Dict[str, Any]:
        user = await get_current_user(request)

        # Centralized resolution: prefer permissions on request.state or user['permissions']
        try:
            state_perms = getattr(request.state, 'permissions', None)
            perms = state_perms if state_perms is not None else user.get('permissions', [])
            if isinstance(perms, str):
                perms = [perms]
            if permission in set(perms):
                return user
        except Exception:
            pass

        # Fallback to manager-based permission model
        if not _auth_manager.check_permission(user['id'], permission):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {permission}"
            )

        return user

    return _require_permission


async def get_optional_user(request: Request) -> Optional[Dict[str, Any]]:
    """
    Get current user if available, otherwise return None

    This allows for optional authentication.
    """
    try:
        return await get_current_user(request)
    except HTTPException:
        return None


def create_api_key(user_id: str, permissions: list[str]) -> str:
    """Create new API key"""
    import uuid

    api_key = f"arxos_{uuid.uuid4().hex}"
    _auth_manager.api_keys[api_key] = {
        'user_id': user_id,
        'permissions': permissions,
        'active': True
    }

    return api_key


def revoke_api_key(api_key: str) -> bool:
    """Revoke API key"""
    if api_key in _auth_manager.api_keys:
        _auth_manager.api_keys[api_key]['active'] = False
        return True
    return False


def get_user_sessions() -> Dict[str, Dict[str, Any]]:
    """Get all user sessions (for admin purposes)"""
    return _auth_manager.user_sessions.copy()


def get_api_keys() -> Dict[str, Dict[str, Any]]:
    """Get all API keys (for admin purposes)"""
    return _auth_manager.api_keys.copy()


# Response formatting helpers for legacy route consistency
def format_success_response(*, data: Dict[str, Any], message: str = "OK", request: Optional[Request] = None) -> Dict[str, Any]:
    """Format consistent success response for legacy routes."""
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": getattr(request.state, 'request_id', None) if request else None,
    }


def format_error_response(*, error_code: str, message: str, details: Optional[Dict[str, Any]] = None, request: Optional[Request] = None) -> Dict[str, Any]:
    """Format consistent error response for legacy routes."""
    return {
        "success": False,
        "error": True,
        "error_code": error_code,
        "message": message,
        "details": details or {},
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": getattr(request.state, 'request_id', None) if request else None,
    }


def format_paginated_response(*, items: List[Dict[str, Any]], total_count: int, page: int, per_page: int, request: Optional[Request] = None) -> Dict[str, Any]:
    """Format consistent paginated response for legacy routes."""
    total_pages = (total_count + per_page - 1) // per_page

    return {
        "success": True,
        "message": "OK",
        "data": {
            "items": items,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        },
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": getattr(request.state, 'request_id', None) if request else None,
    }


def format_validation_error_response(*, field_errors: List[Dict[str, str]], request: Optional[Request] = None) -> Dict[str, Any]:
    """Format consistent validation error response for legacy routes."""
    return format_error_response(
        error_code="VALIDATION_ERROR",
        message="Input validation failed",
        details={"field_errors": field_errors},
        request=request
    )


def format_not_found_response(*, resource_type: str, resource_id: str, request: Optional[Request] = None) -> Dict[str, Any]:
    """Format consistent not found response for legacy routes."""
    return format_error_response(
        error_code="NOT_FOUND",
        message=f"{resource_type} not found",
        details={"resource_type": resource_type, "resource_id": resource_id},
        request=request
    )


def format_permission_denied_response(*, permission: str, request: Optional[Request] = None) -> Dict[str, Any]:
    """Format consistent permission denied response for legacy routes."""
    return format_error_response(
        error_code="PERMISSION_DENIED",
        message="Insufficient permissions",
        details={"required_permission": permission},
        request=request
    )


def format_internal_error_response(*, error_id: Optional[str] = None, request: Optional[Request] = None) -> Dict[str, Any]:
    """Format consistent internal error response for legacy routes."""
    return format_error_response(
        error_code="INTERNAL_ERROR",
        message="An internal error occurred",
        details={"error_id": error_id} if error_id else {},
        request=request
    )


# Convenience permission dependencies for legacy routes
def _has_permission(perms: Any, required: str) -> bool:
    if perms is None:
        return False
    if isinstance(perms, str):
        perms = [perms]
    perm_set = set(perms)
    if required in perm_set:
        return True
    # Accept namespaced permissions like buildings:read, devices:write, etc.
    suffix = f":{required}"
    if any(p.endswith(suffix) for p in perm_set):
        return True
    if required == "write":
        # write is implied by admin or any create/update/delete scoped permission
        if "admin" in perm_set or any(p.endswith(":create") or p.endswith(":update") or p.endswith(":delete") for p in perm_set):
            return True
    if required == "read":
        # read implied by write/admin
        if "admin" in perm_set or "write" in perm_set or any(p.endswith(":write") for p in perm_set):
            return True
    if required == "admin" and ("admin" in perm_set or any(p.endswith(":admin") for p in perm_set)):
        return True
    return False


async def require_read_permission(request: Request) -> User:
    user = await get_current_user(request)
    perms = getattr(request.state, 'permissions', None) or user.get('permissions', [])
    if not _has_permission(perms, "read"):
        raise HTTPException(status_code=403, detail="Permission denied: read")
    return user


async def require_write_permission(request: Request) -> User:
    user = await get_current_user(request)
    perms = getattr(request.state, 'permissions', None) or user.get('permissions', [])
    if not _has_permission(perms, "write"):
        raise HTTPException(status_code=403, detail="Permission denied: write")
    return user


async def require_admin_permission(request: Request) -> User:
    user = await get_current_user(request)
    perms = getattr(request.state, 'permissions', None) or user.get('permissions', [])
    if not _has_permission(perms, "admin"):
        raise HTTPException(status_code=403, detail="Permission denied: admin")
    return user


# Permission enforcement for building operations
async def require_building_permission(permission: str):
    """
    Dependency to require specific building permission.

    Permissions:
    - buildings:read - for GET/list operations
    - buildings:create - for POST operations
    - buildings:update - for PUT/PATCH operations
    - buildings:delete - for DELETE operations
    """
    async def _require_permission(request: Request) -> Dict[str, Any]:
        user = await get_current_user(request)

        # Check if user has the required permission
        user_permissions = getattr(request.state, 'permissions', [])
        if not user_permissions:
            user_permissions = user.get('permissions', [])

        if isinstance(user_permissions, str):
            user_permissions = [user_permissions]

        if permission not in user_permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {permission} required for this operation"
            )

        return user

    return _require_permission


# Specific permission dependencies for building operations
async def require_building_read_permission(request: Request) -> Dict[str, Any]:
    """Require buildings:read permission for GET operations."""
    return await require_building_permission("buildings:read")(request)


async def require_building_create_permission(request: Request) -> Dict[str, Any]:
    """Require buildings:create permission for POST operations."""
    return await require_building_permission("buildings:create")(request)


async def require_building_update_permission(request: Request) -> Dict[str, Any]:
    """Require buildings:update permission for PUT/PATCH operations."""
    return await require_building_permission("buildings:update")(request)


async def require_building_delete_permission(request: Request) -> Dict[str, Any]:
    """Require buildings:delete permission for DELETE operations."""
    return await require_building_permission("buildings:delete")(request)


# Centralized permission checking for legacy routes
async def get_user_permissions(request: Request) -> List[str]:
    """Get user permissions from request state or user object."""
    try:
        # Try to get permissions from request state first
        state_perms = getattr(request.state, 'permissions', None)
        if state_perms is not None:
            return state_perms if isinstance(state_perms, list) else [state_perms]

        # Fallback to user object permissions
        user = await get_current_user(request)
        user_perms = user.get('permissions', [])
        return user_perms if isinstance(user_perms, list) else [user_perms]

    except Exception:
        return []


async def check_building_permission(request: Request, permission: str) -> bool:
    """Check if user has specific building permission."""
    try:
        user_permissions = await get_user_permissions(request)
        return permission in user_permissions
    except Exception:
        return False


# Legacy route permission enforcement
def enforce_building_permissions(permission: str):
    """Decorator to enforce building permissions on legacy routes."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract request from args or kwargs
            request = None
            for arg in args:
                if hasattr(arg, 'state'):
                    request = arg
                    break

            if not request:
                for value in kwargs.values():
                    if hasattr(value, 'state'):
                        request = value
                        break

            if request and await check_building_permission(request, permission):
                return await func(*args, **kwargs)
            else:
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied: {permission} required"
                )
        return wrapper
    return decorator
