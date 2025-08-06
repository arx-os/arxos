"""
Authorization System for MCP Engineering

This module provides role-based access control (RBAC) for the MCP Engineering API,
including permission management and access control.
"""

from typing import Dict, List, Set, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class Permission(Enum):
    """Available permissions in the system."""

    # Building validation permissions
    VALIDATE_BUILDING = "validate_building"
    VIEW_VALIDATION_RESULTS = "view_validation_results"
    EXPORT_REPORTS = "export_reports"

    # AI/ML permissions
    GET_RECOMMENDATIONS = "get_recommendations"
    GET_PREDICTIONS = "get_predictions"
    VIEW_AI_ANALYSIS = "view_ai_analysis"

    # User management permissions
    CREATE_USER = "create_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    VIEW_USERS = "view_users"

    # System administration permissions
    VIEW_SYSTEM_METRICS = "view_system_metrics"
    MANAGE_SYSTEM_CONFIG = "manage_system_config"
    VIEW_LOGS = "view_logs"

    # API permissions
    API_READ = "api_read"
    API_WRITE = "api_write"
    API_ADMIN = "api_admin"


class Role(Enum):
    """Available roles in the system."""

    VIEWER = "viewer"
    USER = "user"
    ANALYST = "analyst"
    ADMIN = "admin"
    SYSTEM_ADMIN = "system_admin"


@dataclass
class User:
    """User entity with roles and permissions."""

    id: str
    username: str
    email: str
    roles: Set[Role]
    permissions: Set[Permission]
    is_active: bool = True
    created_at: datetime = None
    updated_at: datetime = None


class RoleBasedAccessControl:
    """Role-based access control system."""

    def __init__(self):
        """Initialize RBAC system with default role-permission mappings."""
        self.role_permissions = {
            Role.VIEWER: {
                Permission.VIEW_VALIDATION_RESULTS,
                Permission.VIEW_AI_ANALYSIS,
                Permission.API_READ,
            },
            Role.USER: {
                Permission.VALIDATE_BUILDING,
                Permission.VIEW_VALIDATION_RESULTS,
                Permission.EXPORT_REPORTS,
                Permission.GET_RECOMMENDATIONS,
                Permission.GET_PREDICTIONS,
                Permission.VIEW_AI_ANALYSIS,
                Permission.API_READ,
                Permission.API_WRITE,
            },
            Role.ANALYST: {
                Permission.VALIDATE_BUILDING,
                Permission.VIEW_VALIDATION_RESULTS,
                Permission.EXPORT_REPORTS,
                Permission.GET_RECOMMENDATIONS,
                Permission.GET_PREDICTIONS,
                Permission.VIEW_AI_ANALYSIS,
                Permission.VIEW_SYSTEM_METRICS,
                Permission.VIEW_LOGS,
                Permission.API_READ,
                Permission.API_WRITE,
            },
            Role.ADMIN: {
                Permission.VALIDATE_BUILDING,
                Permission.VIEW_VALIDATION_RESULTS,
                Permission.EXPORT_REPORTS,
                Permission.GET_RECOMMENDATIONS,
                Permission.GET_PREDICTIONS,
                Permission.VIEW_AI_ANALYSIS,
                Permission.CREATE_USER,
                Permission.UPDATE_USER,
                Permission.DELETE_USER,
                Permission.VIEW_USERS,
                Permission.VIEW_SYSTEM_METRICS,
                Permission.MANAGE_SYSTEM_CONFIG,
                Permission.VIEW_LOGS,
                Permission.API_READ,
                Permission.API_WRITE,
                Permission.API_ADMIN,
            },
            Role.SYSTEM_ADMIN: {
                Permission.VALIDATE_BUILDING,
                Permission.VIEW_VALIDATION_RESULTS,
                Permission.EXPORT_REPORTS,
                Permission.GET_RECOMMENDATIONS,
                Permission.GET_PREDICTIONS,
                Permission.VIEW_AI_ANALYSIS,
                Permission.CREATE_USER,
                Permission.UPDATE_USER,
                Permission.DELETE_USER,
                Permission.VIEW_USERS,
                Permission.VIEW_SYSTEM_METRICS,
                Permission.MANAGE_SYSTEM_CONFIG,
                Permission.VIEW_LOGS,
                Permission.API_READ,
                Permission.API_WRITE,
                Permission.API_ADMIN,
            },
        }

        self.users: Dict[str, User] = {}

    def get_permissions_for_role(self, role: Role) -> Set[Permission]:
        """
        Get permissions for a specific role.

        Args:
            role: Role to get permissions for

        Returns:
            Set of permissions for the role
        """
        return self.role_permissions.get(role, set())

    def get_permissions_for_user(self, user_id: str) -> Set[Permission]:
        """
        Get all permissions for a user based on their roles.

        Args:
            user_id: User identifier

        Returns:
            Set of all permissions for the user
        """
        if user_id not in self.users:
            return set()

        user = self.users[user_id]
        permissions = set()

        for role in user.roles:
            permissions.update(self.get_permissions_for_role(role))

        # Add user-specific permissions
        permissions.update(user.permissions)

        return permissions

    def has_permission(self, user_id: str, permission: Permission) -> bool:
        """
        Check if a user has a specific permission.

        Args:
            user_id: User identifier
            permission: Permission to check

        Returns:
            True if user has permission, False otherwise
        """
        user_permissions = self.get_permissions_for_user(user_id)
        return permission in user_permissions

    def has_any_permission(self, user_id: str, permissions: List[Permission]) -> bool:
        """
        Check if a user has any of the specified permissions.

        Args:
            user_id: User identifier
            permissions: List of permissions to check

        Returns:
            True if user has any of the permissions, False otherwise
        """
        user_permissions = self.get_permissions_for_user(user_id)
        return any(permission in user_permissions for permission in permissions)

    def has_all_permissions(self, user_id: str, permissions: List[Permission]) -> bool:
        """
        Check if a user has all of the specified permissions.

        Args:
            user_id: User identifier
            permissions: List of permissions to check

        Returns:
            True if user has all permissions, False otherwise
        """
        user_permissions = self.get_permissions_for_user(user_id)
        return all(permission in user_permissions for permission in permissions)

    def add_user(self, user: User) -> bool:
        """
        Add a user to the system.

        Args:
            user: User to add

        Returns:
            True if successful, False otherwise
        """
        try:
            self.users[user.id] = user
            return True
        except Exception:
            return False

    def update_user_roles(self, user_id: str, roles: Set[Role]) -> bool:
        """
        Update user roles.

        Args:
            user_id: User identifier
            roles: New roles for the user

        Returns:
            True if successful, False otherwise
        """
        if user_id not in self.users:
            return False

        try:
            self.users[user_id].roles = roles
            return True
        except Exception:
            return False

    def add_user_permission(self, user_id: str, permission: Permission) -> bool:
        """
        Add a specific permission to a user.

        Args:
            user_id: User identifier
            permission: Permission to add

        Returns:
            True if successful, False otherwise
        """
        if user_id not in self.users:
            return False

        try:
            self.users[user_id].permissions.add(permission)
            return True
        except Exception:
            return False

    def remove_user_permission(self, user_id: str, permission: Permission) -> bool:
        """
        Remove a specific permission from a user.

        Args:
            user_id: User identifier
            permission: Permission to remove

        Returns:
            True if successful, False otherwise
        """
        if user_id not in self.users:
            return False

        try:
            self.users[user_id].permissions.discard(permission)
            return True
        except Exception:
            return False


class AuthorizationMiddleware:
    """FastAPI middleware for authorization."""

    def __init__(self, rbac: RoleBasedAccessControl):
        """
        Initialize authorization middleware.

        Args:
            rbac: RBAC system instance
        """
        self.rbac = rbac

    async def check_permission(self, user_id: str, permission: Permission) -> bool:
        """
        Check if a user has a specific permission.

        Args:
            user_id: User identifier
            permission: Permission to check

        Returns:
            True if user has permission, False otherwise
        """
        return self.rbac.has_permission(user_id, permission)

    async def check_permissions(
        self, user_id: str, permissions: List[Permission], require_all: bool = True
    ) -> bool:
        """
        Check if a user has required permissions.

        Args:
            user_id: User identifier
            permissions: List of permissions to check
            require_all: If True, user must have all permissions; if False, any permission

        Returns:
            True if user has required permissions, False otherwise
        """
        if require_all:
            return self.rbac.has_all_permissions(user_id, permissions)
        else:
            return self.rbac.has_any_permission(user_id, permissions)


# Global RBAC instance
rbac_system = RoleBasedAccessControl()
