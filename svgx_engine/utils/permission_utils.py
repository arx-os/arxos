"""
Permission Enforcement Utilities for Arxos Platform

This module provides comprehensive permission enforcement with granular,
object-aware permission validation using user roles and object ownership metadata.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class PermissionLevel(str, Enum):
    """Permission levels for role hierarchy."""
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    VIEWER = "viewer"


class PermissionAction(str, Enum):
    """Permission actions for different operations."""
    # Repository actions
    REPOSITORY_READ = "repository:read"
    REPOSITORY_WRITE = "repository:write"
    REPOSITORY_DELETE = "repository:delete"
    REPOSITORY_ADMIN = "repository:admin"

    # Building actions
    BUILDING_READ = "building:read"
    BUILDING_WRITE = "building:write"
    BUILDING_DELETE = "building:delete"
    BUILDING_SHARE = "building:share"

    # Project actions
    PROJECT_READ = "project:read"
    PROJECT_WRITE = "project:write"
    PROJECT_DELETE = "project:delete"
    PROJECT_CREATE = "project:create"

    # User management
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    USER_INVITE = "user:invite"

    # Organization actions
    ORG_READ = "organization:read"
    ORG_WRITE = "organization:write"
    ORG_DELETE = "organization:delete"
    ORG_BILLING = "organization:billing"

    # Analytics actions
    ANALYTICS_READ = "analytics:read"
    ANALYTICS_EXPORT = "analytics:export"

    # API actions
    API_READ = "api:read"
    API_WRITE = "api:write"
    API_ADMIN = "api:admin"

    # Feature actions
    FEATURE_READ = "feature:read"
    FEATURE_WRITE = "feature:write"

    # Integration actions
    INTEGRATION_READ = "integration:read"
    INTEGRATION_WRITE = "integration:write"
    INTEGRATION_DELETE = "integration:delete"


class PermissionChecker:
    """Comprehensive permission checker for the Arxos Platform."""

    def __init__(self):
        pass
    """
    Perform __init__ operation

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        # Permission hierarchy with numeric levels
        self.permission_hierarchy = {
            PermissionLevel.OWNER: 100,
            PermissionLevel.ADMIN: 80,
            PermissionLevel.MANAGER: 60,
            PermissionLevel.USER: 40,
            PermissionLevel.VIEWER: 20
        }

        # Action permission mapping
        self.action_permissions = {
            # Repository permissions
            PermissionAction.REPOSITORY_READ: [PermissionLevel.VIEWER, PermissionLevel.USER, PermissionLevel.MANAGER, PermissionLevel.ADMIN, PermissionLevel.OWNER],
            PermissionAction.REPOSITORY_WRITE: [PermissionLevel.USER, PermissionLevel.MANAGER, PermissionLevel.ADMIN, PermissionLevel.OWNER],
            PermissionAction.REPOSITORY_DELETE: [PermissionLevel.ADMIN, PermissionLevel.OWNER],
            PermissionAction.REPOSITORY_ADMIN: [PermissionLevel.ADMIN, PermissionLevel.OWNER],

            # Building permissions
            PermissionAction.BUILDING_READ: [PermissionLevel.VIEWER, PermissionLevel.USER, PermissionLevel.MANAGER, PermissionLevel.ADMIN, PermissionLevel.OWNER],
            PermissionAction.BUILDING_WRITE: [PermissionLevel.USER, PermissionLevel.MANAGER, PermissionLevel.ADMIN, PermissionLevel.OWNER],
            PermissionAction.BUILDING_DELETE: [PermissionLevel.ADMIN, PermissionLevel.OWNER],
            PermissionAction.BUILDING_SHARE: [PermissionLevel.USER, PermissionLevel.MANAGER, PermissionLevel.ADMIN, PermissionLevel.OWNER],

            # Project permissions
            PermissionAction.PROJECT_READ: [PermissionLevel.VIEWER, PermissionLevel.USER, PermissionLevel.MANAGER, PermissionLevel.ADMIN, PermissionLevel.OWNER],
            PermissionAction.PROJECT_WRITE: [PermissionLevel.USER, PermissionLevel.MANAGER, PermissionLevel.ADMIN, PermissionLevel.OWNER],
            PermissionAction.PROJECT_DELETE: [PermissionLevel.ADMIN, PermissionLevel.OWNER],
            PermissionAction.PROJECT_CREATE: [PermissionLevel.USER, PermissionLevel.MANAGER, PermissionLevel.ADMIN, PermissionLevel.OWNER],

            # User management permissions
            PermissionAction.USER_READ: [PermissionLevel.MANAGER, PermissionLevel.ADMIN, PermissionLevel.OWNER],
            PermissionAction.USER_WRITE: [PermissionLevel.ADMIN, PermissionLevel.OWNER],
            PermissionAction.USER_DELETE: [PermissionLevel.ADMIN, PermissionLevel.OWNER],
            PermissionAction.USER_INVITE: [PermissionLevel.MANAGER, PermissionLevel.ADMIN, PermissionLevel.OWNER],

            # Organization permissions
            PermissionAction.ORG_READ: [PermissionLevel.USER, PermissionLevel.MANAGER, PermissionLevel.ADMIN, PermissionLevel.OWNER],
            PermissionAction.ORG_WRITE: [PermissionLevel.ADMIN, PermissionLevel.OWNER],
            PermissionAction.ORG_DELETE: [PermissionLevel.OWNER],
            PermissionAction.ORG_BILLING: [PermissionLevel.ADMIN, PermissionLevel.OWNER],

            # Analytics permissions
            PermissionAction.ANALYTICS_READ: [PermissionLevel.MANAGER, PermissionLevel.ADMIN, PermissionLevel.OWNER],
            PermissionAction.ANALYTICS_EXPORT: [PermissionLevel.ADMIN, PermissionLevel.OWNER],

            # API permissions
            PermissionAction.API_READ: [PermissionLevel.USER, PermissionLevel.MANAGER, PermissionLevel.ADMIN, PermissionLevel.OWNER],
            PermissionAction.API_WRITE: [PermissionLevel.ADMIN, PermissionLevel.OWNER],
            PermissionAction.API_ADMIN: [PermissionLevel.OWNER],

            # Feature permissions
            PermissionAction.FEATURE_READ: [PermissionLevel.USER, PermissionLevel.MANAGER, PermissionLevel.ADMIN, PermissionLevel.OWNER],
            PermissionAction.FEATURE_WRITE: [PermissionLevel.ADMIN, PermissionLevel.OWNER],

            # Integration permissions
            PermissionAction.INTEGRATION_READ: [PermissionLevel.USER, PermissionLevel.MANAGER, PermissionLevel.ADMIN, PermissionLevel.OWNER],
            PermissionAction.INTEGRATION_WRITE: [PermissionLevel.ADMIN, PermissionLevel.OWNER],
            PermissionAction.INTEGRATION_DELETE: [PermissionLevel.ADMIN, PermissionLevel.OWNER]
        }

    def check_permission(
        self,
        db,
        user_id: int,
        org_id: int,
        action: str,
        object_id: Optional[int] = None,
        object_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if a user has permission to perform an action.

        Args:
            db: Database session
            user_id: User ID
            org_id: Organization ID
            action: Permission action to check
            object_id: Object ID for object-specific permissions
            object_type: Type of object (repository, building, project, etc.)
            context: Additional context for audit logging

        Returns:
            bool: True if user has permission, False otherwise

        Raises:
            HTTPException: If permission is denied
        """
        try:
            # Get user information
            user = self._get_user(db, user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Check if user is active
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is inactive"
                )

            # Check if user belongs to organization
            if not self._user_belongs_to_org(db, user_id, org_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User does not belong to organization"
                )

            # Get user role in organization
            user_role = self._get_user_role(db, user_id, org_id)
            if not user_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User has no role in organization"
                )

            # Check if action is valid
            if action not in self.action_permissions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid action: {action}"
                )

            # Check if user role has permission for action
            if user_role not in self.action_permissions[action]:
                self._log_permission_denied(user_id, org_id, action, object_id, object_type, user_role, context)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {user_role} cannot perform {action}"
                )

            # Check object-specific permissions if object_id is provided
            if object_id and object_type:
                if not self._check_object_permission(db, user_id, org_id, action, object_id, object_type, user_role):
                    self._log_permission_denied(user_id, org_id, action, object_id, object_type, user_role, context)
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied: {user_role} cannot perform {action} on {object_type} {object_id}"
                    )

            # Log successful permission check
            self._log_permission_granted(user_id, org_id, action, object_id, object_type, user_role, context)

            return True

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error checking permission: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during permission check"
            )

    def _get_user(self, db, user_id: int):
        """Get user from database."""
        # This would typically query the User model
        # For now, return a mock user
        return {"id": user_id, "is_active": True}

    def _user_belongs_to_org(self, db, user_id: int, org_id: int) -> bool:
        """Check if user belongs to organization."""
        # This would typically query the UserOrganization model
        # For now, return True
        return True

    def _get_user_role(self, db, user_id: int, org_id: int) -> Optional[str]:
        """Get user role in organization."""
        # This would typically query the UserOrganization model
        # For now, return a default role
        return PermissionLevel.USER

    def _check_object_permission(
        self,
        db,
        user_id: int,
        org_id: int,
        action: str,
        object_id: int,
        object_type: str,
        user_role: str
    ) -> bool:
        """Check object-specific permissions."""

        # Owner has access to all objects
        if user_role == PermissionLevel.OWNER:
            return True

        # Check object ownership
        if self._is_object_owner(db, user_id, object_id, object_type):
            return True

        # Check shared access
        if self._has_shared_access(db, user_id, object_id, object_type):
            return True

        # Check organization-level access
        if self._has_org_access(db, user_id, org_id, object_id, object_type):
            return True

        return False

    def _is_object_owner(self, db, user_id: int, object_id: int, object_type: str) -> bool:
        """Check if user is the owner of the object."""
        # This would typically query the object's owner field'
        # For now, return False
        return False

    def _has_shared_access(self, db, user_id: int, object_id: int, object_type: str) -> bool:
        """Check if user has shared access to the object."""
        # This would typically query shared access tables
        # For now, return False
        return False

    def _has_org_access(self, db, user_id: int, org_id: int, object_id: int, object_type: str) -> bool:
        """Check if user has organization-level access to the object."""
        # This would typically query organization access tables
        # For now, return True for organization members
        return True

    def _log_permission_granted(
        self,
        user_id: int,
        org_id: int,
        action: str,
        object_id: Optional[int],
        object_type: Optional[str],
        user_role: str,
        context: Optional[Dict[str, Any]]
    ):
        """Log successful permission check."""
        logger.info(
            f"Permission granted: User {user_id} ({user_role}) performed {action}",
            extra={
                'user_id': user_id,
                'org_id': org_id,
                'action': action,
                'object_id': object_id,
                'object_type': object_type,
                'user_role': user_role,
                'context': context,
                'timestamp': datetime.utcnow().isoformat(),
                'result': 'granted'
            }
        )

    def _log_permission_denied(
        self,
        user_id: int,
        org_id: int,
        action: str,
        object_id: Optional[int],
        object_type: Optional[str],
        user_role: str,
        context: Optional[Dict[str, Any]]
    ):
        """Log denied permission check."""
        logger.warning(
            f"Permission denied: User {user_id} ({user_role}) attempted {action}",
            extra={
                'user_id': user_id,
                'org_id': org_id,
                'action': action,
                'object_id': object_id,
                'object_type': object_type,
                'user_role': user_role,
                'context': context,
                'timestamp': datetime.utcnow().isoformat(),
                'result': 'denied'
            }
        )


# Global permission checker instance
permission_checker = PermissionChecker()


def check_permission(
    db,
    user_id: int,
    org_id: int,
    action: str,
    object_id: Optional[int] = None,
    object_type: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Convenience function to check permissions.

    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        action: Permission action to check
        object_id: Object ID for object-specific permissions
        object_type: Type of object (repository, building, project, etc.)
        context: Additional context for audit logging

    Returns:
        bool: True if user has permission, False otherwise

    Raises:
        HTTPException: If permission is denied
    """
    return permission_checker.check_permission(
        db, user_id, org_id, action, object_id, object_type, context
    )


def require_permission(
    action: str,
    object_type: Optional[str] = None
):
    """
    Decorator to require permission for a function.

    Args:
        action: Permission action required
        object_type: Type of object for object-specific permissions
    """
def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract parameters from function signature
            # This is a simplified version - in practice, you'd need to'
            # inspect the function signature and extract the required parameters
            db = kwargs.get('db')
            user_id = kwargs.get('user_id')
            org_id = kwargs.get('org_id')
            object_id = kwargs.get('object_id')
            context = kwargs.get('context')

            if not all([db, user_id, org_id]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing required parameters for permission check"
                )

            # Check permission
            check_permission(db, user_id, org_id, action, object_id, object_type, context)

            # Call original function
            return func(*args, **kwargs)

        return wrapper
    return decorator
