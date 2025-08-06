#!/usr/bin/env python3
"""
Authentication System for MCP

This module provides JWT-based authentication and authorization
with role-based access control for the MCP service.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from enum import Enum

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class UserRole(str, Enum):
    """User role enumeration"""

    ADMIN = "admin"
    ENGINEER = "engineer"
    ARCHITECT = "architect"
    INSPECTOR = "inspector"
    VIEWER = "viewer"
    API_USER = "api_user"


class Permission(str, Enum):
    """Permission enumeration"""

    READ_VALIDATION = "read_validation"
    WRITE_VALIDATION = "write_validation"
    READ_BUILDING_MODELS = "read_building_models"
    WRITE_BUILDING_MODELS = "write_building_models"
    READ_MCP_FILES = "read_mcp_files"
    WRITE_MCP_FILES = "write_mcp_files"
    READ_REPORTS = "read_reports"
    WRITE_REPORTS = "write_reports"
    MANAGE_USERS = "manage_users"
    MANAGE_CODES = "manage_codes"
    MANAGE_JURISDICTIONS = "manage_jurisdictions"
    MANAGE_KNOWLEDGE = "manage_knowledge"
    MANAGE_VERSIONS = "manage_versions"
    MANAGE_REFERENCES = "manage_references"
    SYSTEM_ADMIN = "system_admin"


@dataclass
class User:
    """User data structure"""

    user_id: str
    username: str
    email: str
    roles: List[UserRole]
    permissions: List[Permission]
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


class TokenData(BaseModel):
    """Token data structure"""

    user_id: str
    username: str
    roles: List[str]
    permissions: List[str]
    exp: Optional[datetime] = None


class AuthenticationManager:
    """Manages authentication and authorization"""

    def __init__(self):
        # JWT Configuration
        self.secret_key = os.getenv(
            "JWT_SECRET_KEY", "your-secret-key-change-in-production"
        )
        self.algorithm = "HS256"
        self.access_token_expire_minutes = int(
            os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        )
        self.refresh_token_expire_days = int(
            os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")
        )

        # Password hashing
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        # Security
        self.security = HTTPBearer()

        # Role-based permissions mapping
        self.role_permissions = {
            UserRole.ADMIN: [
                Permission.READ_VALIDATION,
                Permission.WRITE_VALIDATION,
                Permission.READ_BUILDING_MODELS,
                Permission.WRITE_BUILDING_MODELS,
                Permission.READ_MCP_FILES,
                Permission.WRITE_MCP_FILES,
                Permission.READ_REPORTS,
                Permission.WRITE_REPORTS,
                Permission.MANAGE_USERS,
                Permission.SYSTEM_ADMIN,
            ],
            UserRole.ENGINEER: [
                Permission.READ_VALIDATION,
                Permission.WRITE_VALIDATION,
                Permission.READ_BUILDING_MODELS,
                Permission.WRITE_BUILDING_MODELS,
                Permission.READ_MCP_FILES,
                Permission.READ_REPORTS,
                Permission.WRITE_REPORTS,
            ],
            UserRole.ARCHITECT: [
                Permission.READ_VALIDATION,
                Permission.WRITE_VALIDATION,
                Permission.READ_BUILDING_MODELS,
                Permission.WRITE_BUILDING_MODELS,
                Permission.READ_MCP_FILES,
                Permission.READ_REPORTS,
            ],
            UserRole.INSPECTOR: [
                Permission.READ_VALIDATION,
                Permission.READ_BUILDING_MODELS,
                Permission.READ_MCP_FILES,
                Permission.READ_REPORTS,
                Permission.WRITE_REPORTS,
            ],
            UserRole.VIEWER: [
                Permission.READ_VALIDATION,
                Permission.READ_BUILDING_MODELS,
                Permission.READ_MCP_FILES,
                Permission.READ_REPORTS,
            ],
            UserRole.API_USER: [
                Permission.READ_VALIDATION,
                Permission.WRITE_VALIDATION,
                Permission.READ_BUILDING_MODELS,
                Permission.WRITE_BUILDING_MODELS,
                Permission.READ_MCP_FILES,
                Permission.READ_REPORTS,
            ],
        }

        # Mock user database (in production, this would be a real database)
        self.users = self._initialize_mock_users()

    def _initialize_mock_users(self) -> Dict[str, User]:
        """Initialize mock users for development"""
        return {
            "admin": User(
                user_id="admin_001",
                username="admin",
                email="admin@arxos.com",
                roles=[UserRole.ADMIN],
                permissions=self.role_permissions[UserRole.ADMIN],
                created_at=datetime.now(),
                last_login=datetime.now(),
            ),
            "engineer": User(
                user_id="engineer_001",
                username="engineer",
                email="engineer@arxos.com",
                roles=[UserRole.ENGINEER],
                permissions=self.role_permissions[UserRole.ENGINEER],
                created_at=datetime.now(),
                last_login=datetime.now(),
            ),
            "architect": User(
                user_id="architect_001",
                username="architect",
                email="architect@arxos.com",
                roles=[UserRole.ARCHITECT],
                permissions=self.role_permissions[UserRole.ARCHITECT],
                created_at=datetime.now(),
                last_login=datetime.now(),
            ),
            "inspector": User(
                user_id="inspector_001",
                username="inspector",
                email="inspector@arxos.com",
                roles=[UserRole.INSPECTOR],
                permissions=self.role_permissions[UserRole.INSPECTOR],
                created_at=datetime.now(),
                last_login=datetime.now(),
            ),
            "viewer": User(
                user_id="viewer_001",
                username="viewer",
                email="viewer@arxos.com",
                roles=[UserRole.VIEWER],
                permissions=self.role_permissions[UserRole.VIEWER],
                created_at=datetime.now(),
                last_login=datetime.now(),
            ),
            "api_user": User(
                user_id="api_001",
                username="api_user",
                email="api@arxos.com",
                roles=[UserRole.API_USER],
                permissions=self.role_permissions[UserRole.API_USER],
                created_at=datetime.now(),
                last_login=datetime.now(),
            ),
        }

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash password"""
        return self.pwd_context.hash(password)

    def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.access_token_expire_minutes
            )

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(
        self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
    ) -> TokenData:
        """Verify JWT token and return token data"""
        try:
            payload = jwt.decode(
                credentials.credentials, self.secret_key, algorithms=[self.algorithm]
            )

            # Check if token is expired
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
                )

            # Extract user data
            user_id = payload.get("sub")
            username = payload.get("username")
            roles = payload.get("roles", [])
            permissions = payload.get("permissions", [])

            if user_id is None or username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                )

            return TokenData(
                user_id=user_id,
                username=username,
                roles=roles,
                permissions=permissions,
                exp=datetime.fromtimestamp(exp) if exp else None,
            )

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

    def get_current_user(self, token: TokenData = Depends(verify_token)) -> User:
        """Get current authenticated user"""
        user = self.users.get(token.username)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled",
            )

        # Update last login
        user.last_login = datetime.now()

        return user

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        user = self.users.get(username)

        if not user:
            return None

        # For mock users, use simple password check
        # In production, this would verify against hashed passwords
        if username == "admin" and password == "admin123":
            return user
        elif username == "engineer" and password == "engineer123":
            return user
        elif username == "architect" and password == "architect123":
            return user
        elif username == "inspector" and password == "inspector123":
            return user
        elif username == "viewer" and password == "viewer123":
            return user
        elif username == "api_user" and password == "api123":
            return user

        return None

    def has_permission(self, user: User, permission: Permission) -> bool:
        """Check if user has specific permission"""
        return permission in user.permissions

    def has_role(self, user: User, role: UserRole) -> bool:
        """Check if user has specific role"""
        return role in user.roles

    def require_permission(self, permission: Permission):
        """Dependency to require specific permission"""

        def permission_dependency(current_user: User = Depends(get_current_user)):
            if not self.has_permission(current_user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission}",
                )
            return current_user

        return permission_dependency

    def require_role(self, role: UserRole):
        """Dependency to require specific role"""

        def role_dependency(current_user: User = Depends(get_current_user)):
            if not self.has_role(current_user, role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role required: {role}",
                )
            return current_user

        return role_dependency

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.users.get(username)

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        for user in self.users.values():
            if user.user_id == user_id:
                return user
        return None

    def create_user(
        self, username: str, email: str, password: str, roles: List[UserRole]
    ) -> User:
        """Create new user (admin only)"""
        if username in self.users:
            raise ValueError("Username already exists")

        # Hash password
        hashed_password = self.get_password_hash(password)

        # Get permissions for roles
        permissions = []
        for role in roles:
            if role in self.role_permissions:
                permissions.extend(self.role_permissions[role])

        # Remove duplicates
        permissions = list(set(permissions))

        # Create user
        user = User(
            user_id=f"user_{len(self.users) + 1:03d}",
            username=username,
            email=email,
            roles=roles,
            permissions=permissions,
            created_at=datetime.now(),
        )

        self.users[username] = user
        logger.info(f"Created new user: {username}")

        return user

    def update_user_roles(self, username: str, roles: List[UserRole]) -> User:
        """Update user roles (admin only)"""
        user = self.users.get(username)
        if not user:
            raise ValueError("User not found")

        # Update roles
        user.roles = roles

        # Update permissions based on new roles
        permissions = []
        for role in roles:
            if role in self.role_permissions:
                permissions.extend(self.role_permissions[role])

        user.permissions = list(set(permissions))

        logger.info(f"Updated roles for user {username}: {roles}")
        return user

    def deactivate_user(self, username: str) -> bool:
        """Deactivate user account (admin only)"""
        user = self.users.get(username)
        if not user:
            return False

        user.is_active = False
        logger.info(f"Deactivated user: {username}")
        return True

    def activate_user(self, username: str) -> bool:
        """Activate user account (admin only)"""
        user = self.users.get(username)
        if not user:
            return False

        user.is_active = True
        logger.info(f"Activated user: {username}")
        return True

    def get_all_users(self) -> List[User]:
        """Get all users (admin only)"""
        return list(self.users.values())

    def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics"""
        total_users = len(self.users)
        active_users = len([u for u in self.users.values() if u.is_active])

        role_counts = {}
        for user in self.users.values():
            for role in user.roles:
                role_counts[role.value] = role_counts.get(role.value, 0) + 1

        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "role_distribution": role_counts,
        }


# Global authentication manager instance
auth_manager = AuthenticationManager()


# Convenience functions for dependency injection
def get_current_user(
    current_user: User = Depends(auth_manager.get_current_user),
) -> User:
    """Get current authenticated user"""
    return current_user


def require_permission(permission: Permission):
    """Require specific permission"""
    return auth_manager.require_permission(permission)


def require_role(role: UserRole):
    """Require specific role"""
    return auth_manager.require_role(role)


def require_admin():
    """Require admin role"""
    return require_role(UserRole.ADMIN)


def require_engineer():
    """Require engineer role"""
    return require_role(UserRole.ENGINEER)


def require_architect():
    """Require architect role"""
    return require_role(UserRole.ARCHITECT)


def require_inspector():
    """Require inspector role"""
    return require_role(UserRole.INSPECTOR)
