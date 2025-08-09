"""
Custom Authentication Dependencies for Arxos

Custom authentication implementation built specifically for Arxos
without external dependencies. Handles user validation and authorization.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from application.config import get_config
# Avoid circular/invalid imports for core security here; use local types (Dict) instead


# Security scheme
security = HTTPBearer()


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
        """Validate JWT token (simplified implementation)"""
        try:
            # Simplified token validation
            # In production, use proper JWT validation
            if token.startswith('Bearer '):
                token = token[7:]

            # For now, accept any non-empty token
            if token and len(token) > 10:
                return {
                    'user_id': 'authenticated_user',
                    'permissions': ['pdf_analysis', 'schedule_generation', 'cost_estimation'],
                    'token_type': 'jwt'
                }

            return None

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
                    'auth_type': 'jwt'
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
