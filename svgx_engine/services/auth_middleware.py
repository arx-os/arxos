import jwt
import time
from typing import Optional, Dict, List, Callable
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = "your-secret-key-here"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Role definitions
ROLES = {
    "admin": {
        "permissions": ["read", "write", "delete", "admin"],
        "description": "Full system access"
    },
    "editor": {
        "permissions": ["read", "write"],
        "description": "Can read and edit content"
    },
    "viewer": {
        "permissions": ["read"],
        "description": "Read-only access"
    },
    "guest": {
        "permissions": ["read_limited"],
        "description": "Limited read access"
    }
}

# Permission mappings for endpoints
ENDPOINT_PERMISSIONS = {
    "GET /": ["read"],
    "GET /health/": ["read"],
    "GET /health/summary/": ["read"],
    "GET /health/history/": ["read"],
    "GET /metrics/": ["read"],
    "GET /metrics/prometheus": ["read"],
    "GET /errors/stats/": ["admin"],
    "POST /runtime/ui-event/": ["write"],
    "POST /runtime/undo/": ["write"],
    "POST /runtime/redo/": ["write"],
    "POST /runtime/annotation/update/": ["write"],
    "POST /runtime/annotation/delete/": ["write"],
    "POST /runtime/lock/": ["write"],
    "POST /runtime/unlock/": ["write"],
    "GET /runtime/lock-status/": ["read"],
    "POST /runtime/lock-timeout/": ["admin"],
    "GET /runtime/lock-timeout/": ["read"],
    "POST /runtime/release-session-locks/": ["write"],
    "GET /runtime/all-locks/": ["read"],
    "ws://runtime/events": ["read", "write"]
}

class User(BaseModel):
    """User model for authentication."""
    user_id: str
    username: str
    email: str
    role: str
    permissions: List[str]
    is_active: bool = True

class Token(BaseModel):
    """Token model for JWT."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    """Token data model."""
    user_id: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None

# Mock user database (in production, use real database)
USERS_DB = {
    "admin@example.com": {
        "user_id": "admin-001",
        "username": "admin",
        "email": "admin@example.com",
        "password_hash": "hashed_password_here",  # In production, use proper hashing
        "role": "admin",
        "is_active": True
    },
    "editor@example.com": {
        "user_id": "editor-001",
        "username": "editor",
        "email": "editor@example.com",
        "password_hash": "hashed_password_here",
        "role": "editor",
        "is_active": True
    },
    "viewer@example.com": {
        "user_id": "viewer-001",
        "username": "viewer",
        "email": "viewer@example.com",
        "password_hash": "hashed_password_here",
        "role": "viewer",
        "is_active": True
    },
    "guest@example.com": {
        "user_id": "guest-001",
        "username": "guest",
        "email": "guest@example.com",
        "password_hash": "hashed_password_here",
        "role": "guest",
        "is_active": True
    }
}

class AuthMiddleware:
    """Authentication and authorization middleware."""
    
    def __init__(self):
        self.security = HTTPBearer()
    
    def create_access_token(self, data: dict, expires_delta: Optional[int] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = time.time() + expires_delta
        else:
            expire = time.time() + (ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> TokenData:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            username: str = payload.get("username")
            role: str = payload.get("role")
            
            if user_id is None:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            return TokenData(user_id=user_id, username=username, role=role)
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    def get_user(self, email: str) -> Optional[User]:
        """Get user from database."""
        user_data = USERS_DB.get(email)
        if user_data:
            return User(
                user_id=user_data["user_id"],
                username=user_data["username"],
                email=user_data["email"],
                role=user_data["role"],
                permissions=ROLES[user_data["role"]]["permissions"],
                is_active=user_data["is_active"]
            )
        return None
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = self.get_user(email)
        if not user:
            return None
        if not user.is_active:
            return None
        # In production, verify password hash
        if password != "password":  # Mock password check
            return None
        return user
    
    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> User:
        """Get current authenticated user from token."""
        token_data = self.verify_token(credentials.credentials)
        user = self.get_user_by_id(token_data.user_id)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        for user_data in USERS_DB.values():
            if user_data["user_id"] == user_id:
                return User(
                    user_id=user_data["user_id"],
                    username=user_data["username"],
                    email=user_data["email"],
                    role=user_data["role"],
                    permissions=ROLES[user_data["role"]]["permissions"],
                    is_active=user_data["is_active"]
                )
        return None
    
    def check_permission(self, user: User, required_permission: str) -> bool:
        """Check if user has required permission."""
        return required_permission in user.permissions
    
    def require_permission(self, permission: str):
        """Decorator to require specific permission."""
        def permission_dependency(current_user: User = Depends(get_current_user)):
            if not self.check_permission(current_user, permission):
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied: {permission} required"
                )
            return current_user
        return permission_dependency
    
    def require_role(self, role: str):
        """Decorator to require specific role."""
        def role_dependency(current_user: User = Depends(get_current_user)):
            if current_user.role != role:
                raise HTTPException(
                    status_code=403,
                    detail=f"Role required: {role}"
                )
            return current_user
        return role_dependency
    
    def get_endpoint_permission(self, method: str, path: str) -> List[str]:
        """Get required permissions for an endpoint."""
        endpoint_key = f"{method} {path}"
        return ENDPOINT_PERMISSIONS.get(endpoint_key, ["read"])
    
    def check_endpoint_access(self, request: Request, user: User) -> bool:
        """Check if user has access to the endpoint."""
        method = request.method
        path = request.url.path
        required_permissions = self.get_endpoint_permission(method, path)
        
        for permission in required_permissions:
            if not self.check_permission(user, permission):
                return False
        return True
    
    def log_auth_event(self, event_type: str, user_id: str, success: bool, details: str = ""):
        """Log authentication events."""
        logger.info(f"AUTH_EVENT: {event_type} | User: {user_id} | Success: {success} | Details: {details}")

# Global auth middleware instance
auth_middleware = AuthMiddleware()

# Dependency functions for FastAPI
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> User:
    """Get current authenticated user."""
    return auth_middleware.get_current_user(credentials)

def require_read_permission():
    """Require read permission."""
    return auth_middleware.require_permission("read")

def require_write_permission():
    """Require write permission."""
    return auth_middleware.require_permission("write")

def require_admin_permission():
    """Require admin permission."""
    return auth_middleware.require_permission("admin")

def require_editor_role():
    """Require editor role."""
    return auth_middleware.require_role("editor")

def require_admin_role():
    """Require admin role."""
    return auth_middleware.require_role("admin")

# WebSocket authentication
async def authenticate_websocket(request: Request) -> Optional[User]:
    """Authenticate WebSocket connection."""
    try:
        # Extract token from query parameters or headers
        token = request.query_params.get("token") or request.headers.get("authorization")
        if not token:
            return None
        
        # Remove "Bearer " prefix if present
        if token.startswith("Bearer "):
            token = token[7:]
        
        token_data = auth_middleware.verify_token(token)
        user = auth_middleware.get_user_by_id(token_data.user_id)
        return user
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        return None 