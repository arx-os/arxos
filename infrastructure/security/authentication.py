"""
JWT Authentication System for MCP Engineering

This module provides JWT-based authentication for the MCP Engineering API,
including token creation, validation, and user management.
"""

import jwt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum


class TokenType(Enum):
    """Token types for different authentication scenarios."""

    ACCESS = "access"
    REFRESH = "refresh"
    API = "api"


@dataclass
class TokenPayload:
    """Token payload structure."""

    user_id: str
    token_type: TokenType
    permissions: list[str]
    expires_at: datetime


class JWTAuthentication:
    """JWT-based authentication system."""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        """
        Initialize JWT authentication.

        Args:
            secret_key: Secret key for JWT signing
            algorithm: JWT algorithm to use
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_blacklist = set()  # In production, use Redis

    def create_token(
        self,
        user_id: str,
        token_type: TokenType = TokenType.ACCESS,
        permissions: Optional[list[str]] = None,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a JWT token.

        Args:
            user_id: User identifier
            token_type: Type of token to create
            permissions: List of user permissions
            expires_delta: Token expiration time

        Returns:
            JWT token string
        """
        if permissions is None:
            permissions = []

        if expires_delta is None:
            if token_type == TokenType.ACCESS:
                expires_delta = timedelta(minutes=15)
            elif token_type == TokenType.REFRESH:
                expires_delta = timedelta(days=7)
            elif token_type == TokenType.API:
                expires_delta = timedelta(days=365)

        expire = datetime.utcnow() + expires_delta

        to_encode = {
            "sub": user_id,
            "type": token_type.value,
            "permissions": permissions,
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(32),  # JWT ID for blacklisting
        }

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token to verify

        Returns:
            Decoded token payload or None if invalid
        """
        try:
            # Check if token is blacklisted
            if token in self.token_blacklist:
                return None

            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Check if token has expired
            if datetime.fromtimestamp(payload["exp"]) < datetime.utcnow():
                return None

            return payload
        except jwt.PyJWTError:
            return None

    def blacklist_token(self, token: str) -> bool:
        """
        Add a token to the blacklist.

        Args:
            token: Token to blacklist

        Returns:
            True if successful, False otherwise
        """
        try:
            # Verify token is valid before blacklisting
            payload = self.verify_token(token)
            if payload:
                self.token_blacklist.add(token)
                return True
            return False
        except Exception:
            return False

    def has_permission(self, token: str, required_permission: str) -> bool:
        """
        Check if a token has a specific permission.

        Args:
            token: JWT token
            required_permission: Permission to check

        Returns:
            True if token has permission, False otherwise
        """
        payload = self.verify_token(token)
        if not payload:
            return False

        permissions = payload.get("permissions", [])
        return required_permission in permissions

    def get_user_id(self, token: str) -> Optional[str]:
        """
        Extract user ID from token.

        Args:
            token: JWT token

        Returns:
            User ID or None if invalid
        """
        payload = self.verify_token(token)
        if payload:
            return payload.get("sub")
        return None


class AuthenticationMiddleware:
    """FastAPI middleware for JWT authentication."""

    def __init__(self, jwt_auth: JWTAuthentication):
        """
        Initialize authentication middleware.

        Args:
            jwt_auth: JWT authentication instance
        """
        self.jwt_auth = jwt_auth

    async def authenticate_request(self, request) -> Optional[Dict[str, Any]]:
        """
        Authenticate an incoming request.

        Args:
            request: FastAPI request object

        Returns:
            Token payload if authenticated, None otherwise
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None

        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header[7:]  # Remove "Bearer " prefix
        return self.jwt_auth.verify_token(token)


class RateLimiter:
    """Rate limiting for API endpoints."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # In production, use Redis

    def is_allowed(self, client_id: str) -> tuple[bool, int]:
        """
        Check if a client is allowed to make a request.

        Args:
            client_id: Client identifier

        Returns:
            Tuple of (allowed, remaining_requests)
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)

        # Clean old requests
        if client_id in self.requests:
            self.requests[client_id] = [
                req_time
                for req_time in self.requests[client_id]
                if req_time > window_start
            ]
        else:
            self.requests[client_id] = []

        # Check if under limit
        if len(self.requests[client_id]) < self.max_requests:
            self.requests[client_id].append(now)
            return True, self.max_requests - len(self.requests[client_id])

        return False, 0


# Global instances
jwt_auth = JWTAuthentication(
    secret_key="your-secret-key-here"
)  # Use environment variable
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)
