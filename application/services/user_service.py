"""
User Application Service - High-Level User Operations

This module contains the user application service that coordinates
user use cases and provides high-level business operations for
user management with infrastructure integration.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import time

from domain.repositories import UnitOfWork
from domain.events import UserCreated, UserUpdated, UserDeleted
from application.dto.user_dto import (
    CreateUserRequest,
    CreateUserResponse,
    UpdateUserRequest,
    UpdateUserResponse,
    GetUserResponse,
    ListUsersResponse,
    DeleteUserResponse,
)
from infrastructure.services.cache_service import RedisCacheService
from infrastructure.services.event_store import EventStoreService
from infrastructure.services.message_queue import MessageQueueService
from infrastructure.monitoring.metrics import MetricsCollector
from infrastructure.monitoring.logging import StructuredLogger


class UserApplicationService:
    """Application service for user operations with infrastructure integration."""

    def __init__(
        self,
        unit_of_work: UnitOfWork,
        cache_service: Optional[RedisCacheService] = None,
        event_store: Optional[EventStoreService] = None,
        message_queue: Optional[MessageQueueService] = None,
        metrics: Optional[MetricsCollector] = None,
        logger: Optional[StructuredLogger] = None,
    ):
        """Initialize user application service with infrastructure dependencies."""
        self.unit_of_work = unit_of_work
        self.cache_service = cache_service
        self.event_store = event_store
        self.message_queue = message_queue
        self.metrics = metrics
        self.logger = logger

    def create_user(
        self,
        email: str,
        first_name: str,
        last_name: str,
        role: str = "user",
        phone_number: Optional[str] = None,
        department: Optional[str] = None,
        created_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CreateUserResponse:
        """Create a new user with infrastructure integration."""
        start_time = time.time()

        try:
            # Log the operation
            if self.logger:
                self.logger.info(
                    "Creating user",
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    role=role,
                    created_by=created_by,
                )

            # Execute use case directly with UnitOfWork
            from application.use_cases.user_use_cases import CreateUserUseCase

            create_user_uc = CreateUserUseCase(self.unit_of_work)

            request = CreateUserRequest(
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=role,
                phone_number=phone_number,
                department=department,
                created_by=created_by,
                metadata=metadata,
            )
            result = create_user_uc.execute(request)

            if result.success:
                # Publish domain event
                if self.event_store:
                    user_created_event = UserCreated(
                        user_id=str(result.user_id),
                        email=email,
                        role=role,
                        created_by=created_by,
                    )
                    self.event_store.store_event(user_created_event)

                # Publish message to queue
                if self.message_queue:
                    message = {
                        "event_type": "user.created",
                        "user_id": str(result.user_id),
                        "email": email,
                        "first_name": first_name,
                        "last_name": last_name,
                        "role": role,
                        "created_by": created_by,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                    self.message_queue.publish("user.events", message)

                # Clear cache
                if self.cache_service:
                    self.cache_service.delete("users:list")
                    self.cache_service.delete("users:statistics")

                # Record metrics
                if self.metrics:
                    self.metrics.record_timing("user.create", time.time() - start_time)
                    self.metrics.increment_counter("user.created")

                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter("user.create.error")

                return result

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error("Failed to create user", email=email, error=str(e))

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter("user.create.error")

            return CreateUserResponse(
                success=False, error_message=f"Failed to create user: {str(e)}"
            )

    def update_user(
        self,
        user_id: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        phone_number: Optional[str] = None,
        department: Optional[str] = None,
        role: Optional[str] = None,
        status: Optional[str] = None,
        updated_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UpdateUserResponse:
        """Update a user with infrastructure integration."""
        start_time = time.time()

        try:
            # Log the operation
            if self.logger:
                self.logger.info(
                    "Updating user", user_id=user_id, updated_by=updated_by
                )

            # Execute use case directly with UnitOfWork
            from application.use_cases.user_use_cases import UpdateUserUseCase

            update_user_uc = UpdateUserUseCase(self.unit_of_work)

            request = UpdateUserRequest(
                user_id=user_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone_number,
                department=department,
                role=role,
                status=status,
                updated_by=updated_by,
                metadata=metadata,
            )
            result = update_user_uc.execute(request)

            if result.success:
                # Publish domain event
                if self.event_store:
                    user_updated_event = UserUpdated(
                        user_id=user_id,
                        updated_fields=[
                            field
                            for field in [first_name, last_name, email, role, status]
                            if field is not None
                        ],
                        updated_by=updated_by,
                    )
                    self.event_store.store_event(user_updated_event)

                # Clear cache
                if self.cache_service:
                    self.cache_service.delete(f"user:{user_id}")
                    self.cache_service.delete("users:list")

                # Record metrics
                if self.metrics:
                    self.metrics.record_timing("user.update", time.time() - start_time)
                    self.metrics.increment_counter("user.updated")

                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter("user.update.error")

                return result

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to update user", user_id=user_id, error=str(e)
                )

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter("user.update.error")

            return UpdateUserResponse(
                success=False, error_message=f"Failed to update user: {str(e)}"
            )

    def get_user(self, user_id: str) -> GetUserResponse:
        """Get a user with infrastructure integration."""
        start_time = time.time()

        try:
            # Check cache first
            if self.cache_service:
                cached_user = self.cache_service.get(f"user:{user_id}")
                if cached_user:
                    if self.metrics:
                        self.metrics.increment_counter("user.get.cache_hit")
                    return GetUserResponse(success=True, user=cached_user)

            # Execute use case directly with UnitOfWork
            from application.use_cases.user_use_cases import GetUserUseCase

            get_user_uc = GetUserUseCase(self.unit_of_work)

            result = get_user_uc.execute(user_id)

            if result.success:
                # Cache the result
                if self.cache_service:
                    self.cache_service.set(f"user:{user_id}", result.user, ttl=300)

                # Record metrics
                if self.metrics:
                    self.metrics.record_timing("user.get", time.time() - start_time)
                    self.metrics.increment_counter("user.get.cache_miss")

                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter("user.get.error")

                return result

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error("Failed to get user", user_id=user_id, error=str(e))

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter("user.get.error")

            return GetUserResponse(
                success=False, error_message=f"Failed to get user: {str(e)}"
            )

    def list_users(
        self,
        role: Optional[str] = None,
        department: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> ListUsersResponse:
        """List users with infrastructure integration."""
        start_time = time.time()

        try:
            # Check cache first
            cache_key = f'users:list:{role or "all"}:{department or "all"}:{status or "all"}:{page}:{page_size}'
            if self.cache_service:
                cached_users = self.cache_service.get(cache_key)
                if cached_users:
                    if self.metrics:
                        self.metrics.increment_counter("user.list.cache_hit")
                    return ListUsersResponse(**cached_users)

            # Execute use case directly with UnitOfWork
            from application.use_cases.user_use_cases import ListUsersUseCase

            list_users_uc = ListUsersUseCase(self.unit_of_work)

            result = list_users_uc.execute(role, department, status, page, page_size)

            if result.success:
                # Cache the result
                if self.cache_service:
                    self.cache_service.set(cache_key, result.__dict__, ttl=60)

                # Record metrics
                if self.metrics:
                    self.metrics.record_timing("user.list", time.time() - start_time)
                    self.metrics.increment_counter("user.list.cache_miss")

                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter("user.list.error")

                return result

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to list users",
                    role=role,
                    department=department,
                    status=status,
                    error=str(e),
                )

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter("user.list.error")

            return ListUsersResponse(
                success=False, error_message=f"Failed to list users: {str(e)}"
            )

    def delete_user(self, user_id: str) -> DeleteUserResponse:
        """Delete a user with infrastructure integration."""
        start_time = time.time()

        try:
            # Log the operation
            if self.logger:
                self.logger.info("Deleting user", user_id=user_id)

            # Execute use case directly with UnitOfWork
            from application.use_cases.user_use_cases import DeleteUserUseCase

            delete_user_uc = DeleteUserUseCase(self.unit_of_work)

            result = delete_user_uc.execute(user_id)

            if result.success:
                # Publish domain event
                if self.event_store:
                    user_deleted_event = UserDeleted(
                        user_id=user_id,
                        email="",  # Would need to get from user
                        deleted_by="system",
                    )
                    self.event_store.store_event(user_deleted_event)

                # Clear cache
                if self.cache_service:
                    self.cache_service.delete(f"user:{user_id}")
                    self.cache_service.delete("users:list")
                    self.cache_service.delete("users:statistics")

                # Record metrics
                if self.metrics:
                    self.metrics.record_timing("user.delete", time.time() - start_time)
                    self.metrics.increment_counter("user.deleted")

                return result
            else:
                # Record error metrics
                if self.metrics:
                    self.metrics.increment_counter("user.delete.error")

                return result

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error(
                    "Failed to delete user", user_id=user_id, error=str(e)
                )

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter("user.delete.error")

            return DeleteUserResponse(
                success=False, error_message=f"Failed to delete user: {str(e)}"
            )

    def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics with infrastructure integration."""
        start_time = time.time()

        try:
            # Check cache first
            if self.cache_service:
                cached_stats = self.cache_service.get("users:statistics")
                if cached_stats:
                    if self.metrics:
                        self.metrics.increment_counter("user.statistics.cache_hit")
                    return cached_stats

            # Get statistics using UnitOfWork
            users = self.unit_of_work.users.get_all()

            stats = {
                "total_users": len(users),
                "by_status": {},
                "by_role": {},
                "by_department": {},
                "created_today": 0,
                "updated_today": 0,
            }

            today = datetime.utcnow().date()

            for user in users:
                # Status breakdown
                status = user.status.value
                stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

                # Role breakdown
                role = user.role
                stats["by_role"][role] = stats["by_role"].get(role, 0) + 1

                # Department breakdown
                department = user.department or "unknown"
                stats["by_department"][department] = (
                    stats["by_department"].get(department, 0) + 1
                )

                # Today's activity
                if user.created_at and user.created_at.date() == today:
                    stats["created_today"] += 1
                if user.updated_at and user.updated_at.date() == today:
                    stats["updated_today"] += 1

            # Cache the result
            if self.cache_service:
                self.cache_service.set("users:statistics", stats, ttl=300)

            # Record metrics
            if self.metrics:
                self.metrics.record_timing("user.statistics", time.time() - start_time)
                self.metrics.increment_counter("user.statistics.cache_miss")

            return stats

        except Exception as e:
            # Log error
            if self.logger:
                self.logger.error("Failed to get user statistics", error=str(e))

            # Record error metrics
            if self.metrics:
                self.metrics.increment_counter("user.statistics.error")

            return {"error": f"Failed to get user statistics: {str(e)}"}
