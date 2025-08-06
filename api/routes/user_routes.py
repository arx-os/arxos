"""
User management API routes.

This module provides REST endpoints for user management operations
using the application services layer.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from api.dependencies import (
    User,
    require_read_permission,
    require_write_permission,
    format_success_response,
    format_error_response,
)
from application.logging import get_logger
from infrastructure import get_repository_factory
from application.factory import get_user_service
from application.dto import CreateUserRequest, UpdateUserRequest, GetUserRequest

logger = get_logger("api.user_routes")
router = APIRouter(prefix="/users", tags=["users"])


# Request/Response Models
class UserCreateRequest(BaseModel):
    """Request model for creating a user."""

    username: str = Field(..., description="Username", min_length=3, max_length=50)
    email: str = Field(..., description="Email address", max_length=255)
    first_name: str = Field(..., description="First name", min_length=1, max_length=100)
    last_name: str = Field(..., description="Last name", min_length=1, max_length=100)
    role: str = Field(default="user", description="User role")
    phone: Optional[str] = Field(None, description="Phone number", max_length=20)
    department: Optional[str] = Field(None, description="Department", max_length=100)
    status: str = Field(default="active", description="User status")
    created_by: Optional[str] = Field(None, description="User who created the user")


class UserUpdateRequest(BaseModel):
    """Request model for updating a user."""

    username: Optional[str] = Field(
        None, description="Username", min_length=3, max_length=50
    )
    email: Optional[str] = Field(None, description="Email address", max_length=255)
    first_name: Optional[str] = Field(
        None, description="First name", min_length=1, max_length=100
    )
    last_name: Optional[str] = Field(
        None, description="Last name", min_length=1, max_length=100
    )
    role: Optional[str] = Field(None, description="User role")
    phone: Optional[str] = Field(None, description="Phone number", max_length=20)
    department: Optional[str] = Field(None, description="Department", max_length=100)
    status: Optional[str] = Field(None, description="User status")
    updated_by: Optional[str] = Field(None, description="User who updated the user")


def get_user_application_service():
    """Dependency to get user application service."""
    factory = get_repository_factory()
    uow = factory.create_unit_of_work()
    return get_user_service(uow)


# API Endpoints
@router.post(
    "/",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Create a new user with the specified properties.",
)
async def create_user(
    request: UserCreateRequest,
    user: User = Depends(require_write_permission),
    user_service=Depends(get_user_application_service),
) -> Dict[str, Any]:
    """Create a new user."""
    try:
        # Convert API request to application DTO
        create_request = CreateUserRequest(
            username=request.username,
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            role=request.role,
            phone=request.phone,
            department=request.department,
            status=request.status,
            created_by=user.user_id,
        )

        # Use application service to create user
        result = user_service.create_user(
            username=create_request.username,
            email=create_request.email,
            first_name=create_request.first_name,
            last_name=create_request.last_name,
            role=create_request.role,
            phone=create_request.phone,
            department=create_request.department,
            created_by=create_request.created_by,
        )

        if result.success:
            return format_success_response(
                data={
                    "user_id": str(result.user_id),
                    "username": result.username,
                    "email": result.email,
                    "first_name": result.first_name,
                    "last_name": result.last_name,
                    "role": result.role,
                    "phone": result.phone,
                    "department": result.department,
                    "status": result.status,
                    "created_by": result.created_by,
                    "created_at": (
                        result.created_at.isoformat()
                        if result.created_at
                        else datetime.utcnow().isoformat()
                    ),
                },
                message="User created successfully",
            )
        else:
            return format_error_response(
                error_code="USER_CREATION_ERROR",
                message=result.error_message or "Failed to create user",
                details={"error": result.error_message},
            )

    except Exception as e:
        logger.error(f"Failed to create user: {str(e)}")
        return format_error_response(
            error_code="USER_CREATION_ERROR",
            message="Failed to create user",
            details={"error": str(e)},
        )


@router.get(
    "/",
    response_model=Dict[str, Any],
    summary="List users",
    description="Retrieve a list of users with optional filtering and pagination.",
)
async def list_users(
    role: Optional[str] = Query(None, description="Filter by user role"),
    status: Optional[str] = Query(None, description="Filter by user status"),
    department: Optional[str] = Query(None, description="Filter by department"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    user: User = Depends(require_read_permission),
    user_service=Depends(get_user_application_service),
) -> Dict[str, Any]:
    """List users with filtering and pagination."""
    try:
        # Use application service to list users
        result = user_service.list_users(
            role=role,
            status=status,
            department=department,
            page=page,
            page_size=page_size,
        )

        if result.success:
            return format_success_response(
                data={
                    "users": [
                        {
                            "user_id": str(user.user_id),
                            "username": user.username,
                            "email": user.email,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                            "role": user.role,
                            "phone": user.phone,
                            "department": user.department,
                            "status": user.status,
                            "created_by": user.created_by,
                            "created_at": (
                                user.created_at.isoformat() if user.created_at else None
                            ),
                        }
                        for user in result.users
                    ],
                    "pagination": {
                        "page": result.page,
                        "page_size": result.page_size,
                        "total_count": result.total_count,
                        "total_pages": result.total_pages,
                    },
                },
                message="Users retrieved successfully",
            )
        else:
            return format_error_response(
                error_code="USER_LIST_ERROR",
                message=result.error_message or "Failed to retrieve users",
                details={"error": result.error_message},
            )

    except Exception as e:
        logger.error(f"Failed to list users: {str(e)}")
        return format_error_response(
            error_code="USER_LIST_ERROR",
            message="Failed to retrieve users",
            details={"error": str(e)},
        )


@router.get(
    "/{user_id}",
    response_model=Dict[str, Any],
    summary="Get user details",
    description="Retrieve detailed information about a specific user.",
)
async def get_user(
    user_id: str,
    user: User = Depends(require_read_permission),
    user_service=Depends(get_user_application_service),
) -> Dict[str, Any]:
    """Get user details by ID."""
    try:
        # Use application service to get user
        result = user_service.get_user(user_id=user_id)

        if result.success and result.user:
            user_data = result.user
            return format_success_response(
                data={
                    "user_id": str(user_data.user_id),
                    "username": user_data.username,
                    "email": user_data.email,
                    "first_name": user_data.first_name,
                    "last_name": user_data.last_name,
                    "role": user_data.role,
                    "phone": user_data.phone,
                    "department": user_data.department,
                    "status": user_data.status,
                    "created_by": user_data.created_by,
                    "created_at": (
                        user_data.created_at.isoformat()
                        if user_data.created_at
                        else None
                    ),
                    "updated_at": (
                        user_data.updated_at.isoformat()
                        if user_data.updated_at
                        else None
                    ),
                },
                message="User retrieved successfully",
            )
        else:
            return format_error_response(
                error_code="USER_NOT_FOUND",
                message=result.error_message or "User not found",
                details={"user_id": user_id},
            )

    except Exception as e:
        logger.error(f"Failed to get user {user_id}: {str(e)}")
        return format_error_response(
            error_code="USER_RETRIEVAL_ERROR",
            message="Failed to retrieve user",
            details={"error": str(e), "user_id": user_id},
        )


@router.put(
    "/{user_id}",
    response_model=Dict[str, Any],
    summary="Update user",
    description="Update an existing user with new information.",
)
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    user: User = Depends(require_write_permission),
    user_service=Depends(get_user_application_service),
) -> Dict[str, Any]:
    """Update user by ID."""
    try:
        # Convert API request to application DTO
        update_request = UpdateUserRequest(
            user_id=user_id,
            username=request.username,
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            role=request.role,
            phone=request.phone,
            department=request.department,
            status=request.status,
            updated_by=user.user_id,
        )

        # Use application service to update user
        result = user_service.update_user(
            user_id=user_id,
            username=update_request.username,
            email=update_request.email,
            first_name=update_request.first_name,
            last_name=update_request.last_name,
            role=update_request.role,
            phone=update_request.phone,
            department=update_request.department,
            status=update_request.status,
            updated_by=update_request.updated_by,
        )

        if result.success:
            return format_success_response(
                data={
                    "user_id": str(result.user_id),
                    "username": result.username,
                    "email": result.email,
                    "first_name": result.first_name,
                    "last_name": result.last_name,
                    "role": result.role,
                    "phone": result.phone,
                    "department": result.department,
                    "status": result.status,
                    "updated_by": result.updated_by,
                    "updated_at": (
                        result.updated_at.isoformat()
                        if result.updated_at
                        else datetime.utcnow().isoformat()
                    ),
                },
                message="User updated successfully",
            )
        else:
            return format_error_response(
                error_code="USER_UPDATE_ERROR",
                message=result.error_message or "Failed to update user",
                details={"error": result.error_message, "user_id": user_id},
            )

    except Exception as e:
        logger.error(f"Failed to update user {user_id}: {str(e)}")
        return format_error_response(
            error_code="USER_UPDATE_ERROR",
            message="Failed to update user",
            details={"error": str(e), "user_id": user_id},
        )


@router.delete(
    "/{user_id}",
    response_model=Dict[str, Any],
    summary="Delete user",
    description="Delete a user and all associated data.",
)
async def delete_user(
    user_id: str,
    user: User = Depends(require_write_permission),
    user_service=Depends(get_user_application_service),
) -> Dict[str, Any]:
    """Delete user by ID."""
    try:
        # Use application service to delete user
        result = user_service.delete_user(user_id=user_id, deleted_by=user.user_id)

        if result.success:
            return format_success_response(
                data={
                    "user_id": user_id,
                    "deleted_by": user.user_id,
                    "deleted_at": datetime.utcnow().isoformat(),
                },
                message="User deleted successfully",
            )
        else:
            return format_error_response(
                error_code="USER_DELETE_ERROR",
                message=result.error_message or "Failed to delete user",
                details={"error": result.error_message, "user_id": user_id},
            )

    except Exception as e:
        logger.error(f"Failed to delete user {user_id}: {str(e)}")
        return format_error_response(
            error_code="USER_DELETE_ERROR",
            message="Failed to delete user",
            details={"error": str(e), "user_id": user_id},
        )


@router.get(
    "/{user_id}/statistics",
    response_model=Dict[str, Any],
    summary="Get user statistics",
    description="Retrieve statistics and metrics for a specific user.",
)
async def get_user_statistics(
    user_id: str,
    user: User = Depends(require_read_permission),
    user_service=Depends(get_user_application_service),
) -> Dict[str, Any]:
    """Get user statistics."""
    try:
        # Use application service to get user statistics
        result = user_service.get_user_statistics(user_id=user_id)

        if result.success:
            return format_success_response(
                data={
                    "user_id": user_id,
                    "statistics": {
                        "total_users": result.total_users,
                        "active_users": result.active_users,
                        "inactive_users": result.inactive_users,
                        "role_distribution": result.role_distribution,
                        "department_distribution": result.department_distribution,
                        "status_distribution": result.status_distribution,
                        "recent_activity": result.recent_activity,
                    },
                    "last_updated": datetime.utcnow().isoformat(),
                },
                message="User statistics retrieved successfully",
            )
        else:
            return format_error_response(
                error_code="USER_STATISTICS_ERROR",
                message=result.error_message or "Failed to retrieve user statistics",
                details={"error": result.error_message, "user_id": user_id},
            )

    except Exception as e:
        logger.error(f"Failed to get statistics for user {user_id}: {str(e)}")
        return format_error_response(
            error_code="USER_STATISTICS_ERROR",
            message="Failed to retrieve user statistics",
            details={"error": str(e), "user_id": user_id},
        )
