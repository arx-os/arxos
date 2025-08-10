"""
Authentication Middleware - Unified Authentication Layer

This module provides unified authentication middleware that handles
JWT token validation, user authentication, and role-based access control
across all API endpoints.
"""

from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from datetime import datetime, timedelta

from application.unified.services.auth_service import AuthService
from application.unified.dto.user_dto import UserDTO
class AuthenticationError(Exception):
    pass

class AuthorizationError(Exception):
    pass

logger = logging.getLogger(__name__)

security = HTTPBearer()


class AuthMiddleware:
    """
    Unified authentication middleware providing JWT validation and RBAC.

    This middleware implements:
    - JWT token validation
    - User authentication
    - Role-based access control
    - Session management
    - Rate limiting integration
    """

    def __init__(self, auth_service: AuthService):
        """Initialize authentication middleware with auth service."""
        self.auth_service = auth_service
        self.logger = logging.getLogger(self.__class__.__name__)

    async def authenticate(self, request: Request) -> Optional[UserDTO]:
        """
        Authenticate the request using JWT token.

        Args:
            request: FastAPI request object

        Returns:
            User DTO if authentication successful, None otherwise

        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            # Extract token from request import request
            token = await self._extract_token(request)
            if not token:
                return None

            # Validate token
            payload = await self._validate_token(token)
            if not payload:
                return None

            # Get user from token import token
            user = await self._get_user_from_token(payload)
            if not user:
                return None

            # Merge permissions/roles from token claims into user profile
            try:
                token_perms = payload.get("permissions") or []
                token_roles = payload.get("roles") or []
                # Normalize to lists
                if isinstance(token_perms, str):
                    token_perms = [token_perms]
                if isinstance(token_roles, str):
                    token_roles = [token_roles]
                # Merge unique
                user.permissions = sorted(list({*(user.permissions or []), *token_perms}))
                user.roles = sorted(list({*(user.roles or []), *token_roles}))
            except Exception:
                # Non-fatal; proceed with existing user perms/roles
                pass

            # Store user in request state
            request.state.user = user
            request.state.token = token

            self.logger.info(f"User authenticated: {user.id}")
            return user

        except AuthenticationError as e:
            self.logger.warning(f"Authentication failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except Exception as e:
            self.logger.error(f"Unexpected authentication error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    async def authorize(self, request: Request, required_roles: Optional[list] = None,
                       required_permissions: Optional[list] = None) -> bool:
        """
        Authorize the request based on user roles and permissions.

        Args:
            request: FastAPI request object
            required_roles: List of required roles
            required_permissions: List of required permissions

        Returns:
            True if authorization successful

        Raises:
            AuthorizationError: If authorization fails
        """
        try:
            # Get user from request state
            user = getattr(request.state, 'user', None)
            if not user:
                raise AuthorizationError("User not authenticated")

            # Check roles if required
            if required_roles:
                if not await self._check_roles(user, required_roles):
                    raise AuthorizationError(f"User does not have required roles: {required_roles}")

            # Check permissions if required
            if required_permissions:
                if not await self._check_permissions(user, required_permissions):
                    raise AuthorizationError(f"User does not have required permissions: {required_permissions}")

            self.logger.info(f"User authorized: {user.id}")
            return True

        except AuthorizationError as e:
            self.logger.warning(f"Authorization failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        except Exception as e:
            self.logger.error(f"Unexpected authorization error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    async def _extract_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from request headers."""
        try:
            # Try to get token from Authorization header
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                return auth_header[7:]  # Remove "Bearer " prefix

            # Try to get token from query parameters
            token = request.query_params.get("token")
            if token:
                return token

            # Try to get token from cookies import cookies
            token = request.cookies.get("access_token")
            if token:
                return token

            return None

        except Exception as e:
            self.logger.error(f"Error extracting token: {e}")
            return None

    async def _validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token and return payload."""
        try:
            # Validate token with auth service
            payload = await self.auth_service.validate_token(token)
            return payload

        except Exception as e:
            self.logger.error(f"Token validation failed: {e}")
            return None

    async def _get_user_from_token(self, payload: Dict[str, Any]) -> Optional[UserDTO]:
        """Get user from token payload."""
        try:
            user_id = payload.get("sub")
            if not user_id:
                return None

            # Get user from auth service
            user = await self.auth_service.get_user_by_id(user_id)
            return user

        except Exception as e:
            self.logger.error(f"Error getting user from token: {e}")
            return None

    async def _check_roles(self, user: UserDTO, required_roles: list) -> bool:
        """Check if user has required roles."""
        try:
            user_roles = user.roles or []
            return any(role in user_roles for role in required_roles)

        except Exception as e:
            self.logger.error(f"Error checking roles: {e}")
            return False

    async def _check_permissions(self, user: UserDTO, required_permissions: list) -> bool:
        """Check if user has required permissions."""
        try:
            user_permissions = user.permissions or []
            return any(permission in user_permissions for permission in required_permissions)

        except Exception as e:
            self.logger.error(f"Error checking permissions: {e}")
            return False

    async def refresh_token(self, request: Request) -> Optional[str]:
        """
        Refresh the user's access token.'

        Args:
            request: FastAPI request object

        Returns:
            New access token if refresh successful
        """
        try:
            # Get refresh token from request import request
            refresh_token = request.cookies.get("refresh_token")
            if not refresh_token:
                return None

            # Refresh token with auth service
            new_token = await self.auth_service.refresh_token(refresh_token)
            return new_token

        except Exception as e:
            self.logger.error(f"Token refresh failed: {e}")
            return None

    async def logout(self, request: Request) -> bool:
        """
        Logout the user and invalidate tokens.

        Args:
            request: FastAPI request object

        Returns:
            True if logout successful
        """
        try:
            # Get user from request state
            user = getattr(request.state, 'user', None)
            if not user:
                return False

            # Invalidate tokens with auth service
            await self.auth_service.logout(user.id)

            self.logger.info(f"User logged out: {user.id}")
            return True

        except Exception as e:
            self.logger.error(f"Logout failed: {e}")
            return False
