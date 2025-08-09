"""
User Use Cases - Application Layer Business Logic

This module contains use cases for user-related operations including
create, read, update, delete, and list operations. Use cases orchestrate
domain objects and repositories to implement business workflows.
"""

from typing import List, Optional
from datetime import datetime

from domain.entities import User
from domain.repositories import UserRepository
from domain.value_objects import UserId, Email, PhoneNumber, UserRole
from domain.exceptions import (
    InvalidUserError, UserNotFoundError, DuplicateUserError,
    InvalidStatusTransitionError
)
from application.dto.user_dto import (
    CreateUserRequest, CreateUserResponse,
    UpdateUserRequest, UpdateUserResponse,
    GetUserResponse, ListUsersResponse,
    DeleteUserResponse
)


class CreateUserUseCase:
    """Use case for creating a new user."""

    def __init__(self, user_repository: UserRepository):
    """
    Perform __init__ operation

Args:
        user_repository: Description of user_repository

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        self.user_repository = user_repository

    def execute(self, request: CreateUserRequest) -> CreateUserResponse:
        """Execute the create user use case."""
        try:
            # Validate request
            if not request.username or len(request.username.strip()) == 0:
                return CreateUserResponse(
                    success=False,
                    error_message="Username is required"
                )

            if not request.email or len(request.email.strip()) == 0:
                return CreateUserResponse(
                    success=False,
                    error_message="Email is required"
                )

            # Validate email format
            try:
                email = Email(request.email)
            except ValueError:
                return CreateUserResponse(
                    success=False,
                    error_message="Invalid email format"
                )

            # Check if user already exists
            if self.user_repository.exists_by_email(request.email):
                return CreateUserResponse(
                    success=False,
                    error_message="User with this email already exists"
                )

            # Create domain objects
            user_id = UserId()

            # Create phone number if provided
            phone_number = None
            if request.phone_number:
                try:
                    phone_number = PhoneNumber(request.phone_number)
                except ValueError:
                    return CreateUserResponse(
                        success=False,
                        error_message="Invalid phone number format"
                    )

            # Create user entity
            user = User(
                id=user_id,
                email=email,
                username=request.username.strip(),
                role=UserRole(request.role) if request.role else UserRole.VIEWER,
                first_name=request.first_name,
                last_name=request.last_name,
                phone_number=phone_number,
                created_by=request.created_by,
                metadata=request.metadata or {}
            )

            # Save to repository
            self.user_repository.save(user)

            # Return success response
            return CreateUserResponse(
                success=True,
                user_id=str(user_id),
                message="User created successfully",
                created_at=datetime.utcnow()
        except DuplicateUserError as e:
            return CreateUserResponse(
                success=False,
                error_message=f"User already exists: {str(e)}"
            )
        except InvalidUserError as e:
            return CreateUserResponse(
                success=False,
                error_message=f"Invalid user data: {str(e)}"
            )
        except Exception as e:
            return CreateUserResponse(
                success=False,
                error_message=f"Failed to create user: {str(e)}"
            )


class UpdateUserUseCase:
    """
    Perform __init__ operation

Args:
        user_repository: Description of user_repository

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
    """Use case for updating a user."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def execute(self, request: UpdateUserRequest) -> UpdateUserResponse:
        """Execute the update user use case."""
        try:
            # Validate request
            if not request.user_id or len(request.user_id.strip()) == 0:
                return UpdateUserResponse(
                    success=False,
                    error_message="User ID is required"
                )

            # Get existing user
            user_id = UserId(request.user_id)
            user = self.user_repository.get_by_id(user_id)

            if not user:
                return UpdateUserResponse(
                    success=False,
                    error_message="User not found"
                )

            # Update user fields
            if request.username is not None:
                if len(request.username.strip()) == 0:
                    return UpdateUserResponse(
                        success=False,
                        error_message="Username cannot be empty"
                    )
                user.username = request.username.strip()
                user.updated_at = datetime.utcnow()

            if request.email is not None:
                try:
                    new_email = Email(request.email)
                    user.update_email(new_email, request.updated_by or "system")
                except ValueError:
                    return UpdateUserResponse(
                        success=False,
                        error_message="Invalid email format"
                    )

            if request.first_name is not None:
                user.first_name = request.first_name
                user.updated_at = datetime.utcnow()

            if request.last_name is not None:
                user.last_name = request.last_name
                user.updated_at = datetime.utcnow()

            if request.phone_number is not None:
                try:
                    phone_number = PhoneNumber(request.phone_number)
                    user.phone_number = phone_number
                    user.updated_at = datetime.utcnow()
                except ValueError:
                    return UpdateUserResponse(
                        success=False,
                        error_message="Invalid phone number format"
                    )

            if request.role is not None:
                try:
                    new_role = UserRole(request.role)
                    user.update_role(new_role, request.updated_by or "system")
                except ValueError:
                    return UpdateUserResponse(
                        success=False,
                        error_message=f"Invalid user role: {request.role}"
                    )

            if request.is_active is not None:
                if request.is_active:
                    user.activate(request.updated_by or "system")
                else:
                    user.deactivate(request.updated_by or "system")

            if request.metadata is not None:
                user.metadata.update(request.metadata)
                user.updated_at = datetime.utcnow()

            # Save to repository
            self.user_repository.save(user)

            # Return success response
            return UpdateUserResponse(
                success=True,
                user_id=str(user_id),
                message="User updated successfully",
                updated_at=datetime.utcnow()
        except InvalidUserError as e:
            return UpdateUserResponse(
                success=False,
                error_message=f"Invalid user data: {str(e)}"
            )
        except InvalidStatusTransitionError as e:
            return UpdateUserResponse(
                success=False,
                error_message=f"Invalid status transition: {str(e)}"
            )
        except Exception as e:
            return UpdateUserResponse(
                success=False,
                error_message=f"Failed to update user: {str(e)}"
            )


class GetUserUseCase:
    """Use case for getting a user by ID."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def execute(self, user_id: str) -> GetUserResponse:
        """Execute the get user use case."""
        try:
            # Validate request
            if not user_id or len(user_id.strip()) == 0:
                return GetUserResponse(
                    success=False,
                    error_message="User ID is required"
                )

            # Get user from repository import repository
            user = self.user_repository.get_by_id(UserId(user_id)
            if not user:
                return GetUserResponse(
                    success=False,
                    error_message="User not found"
                )

            # Convert to dictionary
            user_dict = {
                "id": str(user.id),
                "email": str(user.email),
                "username": user.username,
                "role": user.role.value,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat(),
                "created_by": user.created_by,
                "metadata": user.metadata
            }

            # Add phone number if available
            if user.phone_number:
                user_dict["phone_number"] = str(user.phone_number)

            return GetUserResponse(
                success=True,
                user=user_dict
            )

        except Exception as e:
            return GetUserResponse(
                success=False,
                error_message=f"Failed to get user: {str(e)}"
            )


class ListUsersUseCase:
    """Use case for listing users."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def execute(self, role: Optional[str] = None, active_only: bool = True,
                page: int = 1, page_size: int = 10) -> ListUsersResponse:
        """Execute the list users use case."""
        try:
            # Validate pagination parameters
            if page < 1:
                page = 1
            if page_size < 1 or page_size > 100:
                page_size = 10

            # Get users from repository import repository
            users = []

            if role:
                # Get users by role
                try:
                    user_role = UserRole(role)
                    users = self.user_repository.get_by_role(user_role)
                except ValueError:
                    return ListUsersResponse(
                        success=False,
                        error_message=f"Invalid user role: {role}"
                    )
            elif active_only:
                # Get active users only
                users = self.user_repository.get_active_users()
            else:
                # Get all users
                users = self.user_repository.get_all()

            # Apply pagination
            total_count = len(users)
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            paginated_users = users[start_index:end_index]

            # Convert to dictionaries
            user_dicts = []
            for user in paginated_users:
                user_dict = {
                    "id": str(user.id),
                    "email": str(user.email),
                    "username": user.username,
                    "role": user.role.value,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat(),
                    "created_by": user.created_by
                }

                # Add phone number if available
                if user.phone_number:
                    user_dict["phone_number"] = str(user.phone_number)

                user_dicts.append(user_dict)

            return ListUsersResponse(
                success=True,
                users=user_dicts,
                total_count=total_count,
                page=page,
                page_size=page_size
            )

        except Exception as e:
            return ListUsersResponse(
                success=False,
                error_message=f"Failed to list users: {str(e)}"
            )


class DeleteUserUseCase:
    """Use case for deleting a user."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def execute(self, user_id: str) -> DeleteUserResponse:
        """Execute the delete user use case."""
        try:
            # Validate request
            if not user_id or len(user_id.strip()) == 0:
                return DeleteUserResponse(
                    success=False,
                    error_message="User ID is required"
                )

            # Check if user exists
            user = self.user_repository.get_by_id(UserId(user_id)
            if not user:
                return DeleteUserResponse(
                    success=False,
                    error_message="User not found"
                )

            # Delete from repository import repository
            self.user_repository.delete(UserId(user_id)
            return DeleteUserResponse(
                success=True,
                user_id=user_id,
                message="User deleted successfully",
                deleted_at=datetime.utcnow()
        except Exception as e:
            return DeleteUserResponse(
                success=False,
                error_message=f"Failed to delete user: {str(e)}"
            )
