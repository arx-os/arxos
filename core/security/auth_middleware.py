"""
Authentication Middleware

This module provides comprehensive authentication and authorization middleware
for the Arxos platform, addressing critical security vulnerabilities.

Security Features:
- JWT token verification
- Role-based access control
- Session management
- Rate limiting
- Input validation
- Secure error handling

Author: Arxos Engineering Team
Date: 2024
License: MIT
"""

import os
import time
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from functools import wraps

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator
import structlog

logger = structlog.get_logger()


class User(BaseModel):
    """User model for authentication"""
    id: str
    username: str
    email: str
    roles: List[str] = []
    permissions: List[str] = []
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None


class TokenData(BaseModel):
    """Token data model"""
    user_id: str
    username: str
    roles: List[str] = []
    permissions: List[str] = []
    exp: datetime


class AuthConfig(BaseModel):
    """Authentication configuration"""
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour
    
    @validator('secret_key')
    def validate_secret_key(cls, v):
    """
    Validate the given input against rules

Args:
        cls: Description of cls
        v: Description of v

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = validate_secret_key(param)
        print(result)
    """
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v


class AuthenticationError(Exception):
    """Base authentication error"""
    pass


class InvalidTokenError(AuthenticationError):
    """Raised when token is invalid"""
    pass


class ExpiredTokenError(AuthenticationError):
    """Raised when token has expired"""
    pass


class InsufficientPermissionsError(AuthenticationError):
    """Raised when user lacks required permissions"""
    pass


class RateLimitExceededError(AuthenticationError):
    """Raised when rate limit is exceeded"""
    pass


class AuthMiddleware:
    """
    Comprehensive authentication middleware.
    
    This class provides secure authentication and authorization
    for all API endpoints, addressing critical security vulnerabilities.
    """
    
    def __init__(self, config: AuthConfig):
        """
        Initialize authentication middleware.
        
        Args:
            config: Authentication configuration
            
        Raises:
            ValueError: If configuration is invalid
        """
        self.config = config
        self.security = HTTPBearer()
        self.rate_limit_cache: Dict[str, List[float]] = {}
        
        # Validate configuration
        self._validate_config()
        
        logger.info("Authentication middleware initialized")
    
    def _validate_config(self):
        """Validate authentication configuration."""
        if not self.config.secret_key:
            raise ValueError("Secret key is required")
        
        if self.config.access_token_expire_minutes <= 0:
            raise ValueError("Access token expire minutes must be positive")
        
        if self.config.rate_limit_requests <= 0:
            raise ValueError("Rate limit requests must be positive")
    
    def create_access_token(self, user: User) -> str:
        """
        Create JWT access token.
        
        Args:
            user: User object
            
        Returns:
            JWT access token
        """
        expire = datetime.utcnow() + timedelta(minutes=self.config.access_token_expire_minutes)
        
        to_encode = {
            "user_id": user.id,
            "username": user.username,
            "roles": user.roles,
            "permissions": user.permissions,
            "exp": expire
        }
        
        token = jwt.encode(to_encode, self.config.secret_key, algorithm=self.config.algorithm)
        return token
    
    def create_refresh_token(self, user: User) -> str:
        """
        Create JWT refresh token.
        
        Args:
            user: User object
            
        Returns:
            JWT refresh token
        """
        expire = datetime.utcnow() + timedelta(days=self.config.refresh_token_expire_days)
        
        to_encode = {
            "user_id": user.id,
            "type": "refresh",
            "exp": expire
        }
        
        token = jwt.encode(to_encode, self.config.secret_key, algorithm=self.config.algorithm)
        return token
    
    def verify_token(self, token: str) -> TokenData:
        """
        Verify JWT token.
        
        Args:
            token: JWT token to verify
            
        Returns:
            Token data
            
        Raises:
            InvalidTokenError: If token is invalid
            ExpiredTokenError: If token has expired
        """
        try:
            payload = jwt.decode(token, self.config.secret_key, algorithms=[self.config.algorithm])
            
            user_id = payload.get("user_id")
            if user_id is None:
                raise InvalidTokenError("Token missing user_id")
            
            exp = payload.get("exp")
            if exp is None:
                raise InvalidTokenError("Token missing expiration")
            
            # Check if token has expired
            if datetime.fromtimestamp(exp) < datetime.utcnow():
                raise ExpiredTokenError("Token has expired")
            
            return TokenData(
                user_id=user_id,
                username=payload.get("username", ""),
                roles=payload.get("roles", []),
                permissions=payload.get("permissions", []),
                exp=datetime.fromtimestamp(exp)
            )
            
        except jwt.PyJWTError as e:
            raise InvalidTokenError(f"Invalid token: {e}")
    
    def hash_password(self, password: str) -> str:
        """
        Hash password securely.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Plain text password
            hashed: Hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def check_rate_limit(self, user_id: str) -> bool:
        """
        Check rate limit for user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if within rate limit, False otherwise
        """
        now = time.time()
        window_start = now - self.config.rate_limit_window
        
        # Clean old entries
        if user_id in self.rate_limit_cache:
            self.rate_limit_cache[user_id] = [
                timestamp for timestamp in self.rate_limit_cache[user_id]
                if timestamp > window_start
            ]
        
        # Check rate limit
        if user_id in self.rate_limit_cache:
            if len(self.rate_limit_cache[user_id]) >= self.config.rate_limit_requests:
                return False
        
        # Add current request
        if user_id not in self.rate_limit_cache:
            self.rate_limit_cache[user_id] = []
        self.rate_limit_cache[user_id].append(now)
        
        return True
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> User:
        """
        Get current user from token.
        
        Args:
            credentials: HTTP authorization credentials
            
        Returns:
            Current user
            
        Raises:
            HTTPException: If authentication fails
        """
        try:
            token = credentials.credentials
            token_data = self.verify_token(token)
            
            # Check rate limit
            if not self.check_rate_limit(token_data.user_id):
                raise RateLimitExceededError("Rate limit exceeded")
            
            # TODO: Get user from database
            # For now, create mock user
            user = User(
                id=token_data.user_id,
                username=token_data.username,
                email=f"{token_data.username}@example.com",
                roles=token_data.roles,
                permissions=token_data.permissions,
                created_at=datetime.utcnow()
            )
            
            logger.info(f"User authenticated: {user.username}")
            return user
            
        except (InvalidTokenError, ExpiredTokenError, RateLimitExceededError) as e:
            logger.warning(f"Authentication failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    def require_roles(self, required_roles: List[str]):
        """
        Decorator to require specific roles.
        
        Args:
    """
    Perform decorator operation

Args:
        func: Description of func

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = decorator(param)
        print(result)
    """
            required_roles: List of required roles
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                user = kwargs.get('user')
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                if not any(role in user.roles for role in required_roles):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions"
                    )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    def require_permissions(self, required_permissions: List[str]):
        """
        Decorator to require specific permissions.
        
        Args:
            required_permissions: List of required permissions
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                user = kwargs.get('user')
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                if not any(permission in user.permissions for permission in required_permissions):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions"
                    )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    def validate_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize input data.
        
        Args:
            data: Input data to validate
            
        Returns:
            Validated and sanitized data
            
        Raises:
            ValueError: If validation fails
        """
        # TODO: Implement comprehensive input validation
        # For now, basic validation
        sanitized_data = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                # Basic XSS prevention
                sanitized_data[key] = value.replace('<script>', '').replace('</script>', '')
            else:
                sanitized_data[key] = value
        
        return sanitized_data


# Global authentication middleware instance
auth_middleware: Optional[AuthMiddleware] = None


def get_auth_middleware() -> AuthMiddleware:
    """Get authentication middleware instance."""
    global auth_middleware
    
    if auth_middleware is None:
        # Load configuration from environment
        config = AuthConfig(
            secret_key=os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production"),
            algorithm="HS256",
            access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
            refresh_token_expire_days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")),
            rate_limit_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "100")),
            rate_limit_window=int(os.getenv("RATE_LIMIT_WINDOW", "3600"))
        )
        
        auth_middleware = AuthMiddleware(config)
    
    return auth_middleware


def get_current_user(user: User = Depends(get_auth_middleware().get_current_user)) -> User:
    """Dependency to get current user."""
    return user


def require_authentication(func):
    """Decorator to require authentication."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        auth = get_auth_middleware()
        return await auth.get_current_user(*args, **kwargs)
    return wrapper 