"""
Authentication utilities for Arxos SVG-BIM Integration System.

- JWT access and refresh token creation/validation
- Password hashing and verification
- User identity and role extraction
- Secure secret management
"""

import os
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from jose import JWTError
from enum import Enum
import secrets
import hashlib

# Load secrets and settings from environment
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key-change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
JWT_REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_MINUTES", "10080"))  # 7 days

# Password hashing context with stronger settings
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Increased from default 10
)

# OAuth2 scheme for FastAPI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# User Pydantic model (for token payload)
class TokenUser(BaseModel):
    id: str
    username: str
    roles: list[str] = []
    is_active: bool = True
    jti: Optional[str] = None  # JWT ID for token revocation

# Token response model
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int

# Password hashing utilities with enhanced security
def hash_password(password: str) -> str:
    """Hash password with bcrypt and additional salt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)

def generate_password_hash(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Generate password hash with custom salt."""
    if not salt:
        salt = secrets.token_hex(16)
    
    # Combine password with salt
    salted_password = password + salt
    hashed = pwd_context.hash(salted_password)
    
    return hashed, salt

def verify_password_with_salt(plain_password: str, hashed_password: str, salt: str) -> bool:
    """Verify password with salt."""
    salted_password = plain_password + salt
    return pwd_context.verify(salted_password, hashed_password)

# JWT token creation with enhanced security
def create_access_token(user: TokenUser, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token with enhanced security."""
    to_encode = user.dict()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
    
    # Add security claims
    to_encode.update({
        "exp": expire,
        "type": "access",
        "jti": secrets.token_hex(16),  # JWT ID for revocation
        "iat": datetime.now(timezone.utc),
        "iss": "arxos-svg-bim",  # Issuer
        "aud": "arxos-users"  # Audience
    })
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(user: TokenUser, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT refresh token with enhanced security."""
    to_encode = user.dict()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=JWT_REFRESH_TOKEN_EXPIRE_MINUTES))
    
    # Add security claims
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "jti": secrets.token_hex(16),  # JWT ID for revocation
        "iat": datetime.now(timezone.utc),
        "iss": "arxos-svg-bim",  # Issuer
        "aud": "arxos-users"  # Audience
    })
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

# JWT token decoding and validation with enhanced security
def decode_token(token: str) -> dict:
    """Decode and validate JWT token with enhanced security checks."""
    try:
        payload = jwt.decode(
            token, 
            JWT_SECRET_KEY, 
            algorithms=[JWT_ALGORITHM],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "require": ["exp", "iat", "type", "jti"]
            }
        )
        
        # Additional security checks
        if payload.get("iss") != "arxos-svg-bim":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token issuer")
        
        if payload.get("aud") != "arxos-users":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token audience")
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token validation failed")

# FastAPI dependency to get current user from JWT
def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenUser:
    """Get current user from JWT token with enhanced validation."""
    payload = decode_token(token)
    
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")
    
    # Check if token is revoked (in a real system, you'd check against a blacklist)
    # For now, we'll implement a simple in-memory blacklist
    if is_token_revoked(payload.get("jti")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
    
    return TokenUser(**payload)

# Token revocation tracking (in-memory for now, should be Redis in production)
_revoked_tokens: set = set()

def revoke_token(jti: str):
    """Revoke a token by its JTI."""
    _revoked_tokens.add(jti)

def is_token_revoked(jti: str) -> bool:
    """Check if a token is revoked."""
    return jti in _revoked_tokens

# FastAPI dependency to enforce roles
def require_roles(*roles):
    """FastAPI dependency to require specific roles."""
    def role_checker(user: TokenUser = Depends(get_current_user)):
        if not any(role in user.roles for role in roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return role_checker

def require_role(role: str):
    """FastAPI dependency to require a specific role."""
    def role_checker(user: TokenUser = Depends(get_current_user)):
        if role not in user.roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Role '{role}' required")
        return user
    return role_checker

# Utility for refresh token validation
def get_user_from_refresh_token(token: str) -> TokenUser:
    """Get user from refresh token with validation."""
    payload = decode_token(token)
    
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    
    # Check if refresh token is revoked
    if is_token_revoked(payload.get("jti")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has been revoked")
    
    return TokenUser(**payload)

# Permission checking utilities
def check_permission(required_permission: str):
    """Decorator to check permissions for FastAPI endpoints."""
    def decorator(func):
        from functools import wraps
        @wraps(func)
        async def wrapper(*args, user: TokenUser = Depends(get_current_user), **kwargs):
            if not has_permission(user, required_permission):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
            return await func(*args, user=user, **kwargs)
        return wrapper
    return decorator

def has_permission(user: TokenUser, required_permission: str) -> bool:
    """Check if user has the required permission."""
    # Enhanced permission system
    if "superuser" in user.roles:
        return True
    elif "admin" in user.roles:
        return True
    elif required_permission in user.roles:
        return True
    return False

def get_current_user_optional(request: Request) -> Optional[TokenUser]:
    """Get current user if authenticated, otherwise return None."""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        token = auth_header.split(" ")[1]
        return get_current_user(token)
    except:
        return None

# User management utilities
def create_user(username: str, email: str, password: str, roles: list = None) -> TokenUser:
    """Create a new user (for testing purposes)."""
    return TokenUser(
        id=str(hash(username)),
        username=username,
        roles=roles or ["viewer"],
        is_active=True
    )

def login_user(username: str, password: str) -> TokenUser:
    """Login a user (for testing purposes)."""
    # This is a simplified version for testing
    return TokenUser(
        id=str(hash(username)),
        username=username,
        roles=["viewer"],
        is_active=True
    )

def list_users():
    """Stub for list_users, to be implemented or replaced by actual service."""
    return []

def update_user_role(user_id: str, new_roles: list):
    """Stub for update_user_role, to be implemented or replaced by actual service."""
    return True

def deactivate_user(user_id: str):
    """Stub for deactivate_user, to be implemented or replaced by actual service."""
    return True

# Enhanced security utilities
def generate_secure_token() -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(32)

def hash_sensitive_data(data: str) -> str:
    """Hash sensitive data for storage."""
    return hashlib.sha256(data.encode()).hexdigest()

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

# Enums and constants
class UserRole(str, Enum):
    """User role constants."""
    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"
    SUPERUSER = "superuser"

class Permission:
    """Permission constants."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    MANAGE_USERS = "manage_users"
    CREATE_SYMBOL = "create_symbol"
    UPDATE_SYMBOL = "update_symbol"
    DELETE_SYMBOL = "delete_symbol"
    VIEW_SYMBOL = "view_symbol"
    READ_SYMBOL = "read_symbol"
    MANAGE_SYMBOLS = "manage_symbols"
    EXPORT_SYMBOL = "export_symbol"
    IMPORT_SYMBOL = "import_symbol"
    VALIDATE_SYMBOL = "validate_symbol"
    BULK_OPERATIONS = "bulk_operations"
    LIST_SYMBOLS = "list_symbols"
    LIST_USERS = "list_users"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    CREATE_USER = "create_user"
    BULK_CREATE_SYMBOLS = "bulk_create_symbols"
    BULK_UPDATE_SYMBOLS = "bulk_update_symbols"
    BULK_DELETE_SYMBOLS = "bulk_delete_symbols"
    BULK_EXPORT_SYMBOLS = "bulk_export_symbols"
    BULK_IMPORT_SYMBOLS = "bulk_import_symbols"
    BULK_VALIDATE_SYMBOLS = "bulk_validate_symbols"
    VIEW_STATISTICS = "view_statistics"
    VIEW_REPORTS = "view_reports"
    DOWNLOAD_REPORTS = "download_reports"

# Pydantic models
class User(BaseModel):
    """User model for authentication."""
    id: str
    username: str
    email: str
    roles: list[str] = []
    is_active: bool = True
    full_name: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    roles: list[str] = []

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    roles: Optional[list[str]] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str]
    roles: list[str]
    is_active: bool
    is_superuser: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

class Token(BaseModel):
    access_token: str
    token_type: str 