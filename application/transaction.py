"""
Transaction Management System

This module provides comprehensive transaction management for the application
layer, including transaction contexts, rollback handling, and integration
with the dependency injection container.
"""

import logging
from typing import Any, Callable, Optional, TypeVar, Generic
from contextlib import contextmanager
from functools import wraps
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from application.exceptions import (
    ApplicationError, TransactionError, ValidationError,
    BusinessRuleError, handle_application_error
)
from application.logging_config import get_logger, log_function_call
from application.container import container

T = TypeVar('T')

logger = get_logger("transaction")


class TransactionManager:
    """Manages database transactions with proper error handling and rollback."""

    def __init__(self):
        """Initialize transaction manager."""
        self.logger = get_logger("transaction.manager")

    @contextmanager
    def transaction_context(self, session: Session):
        """Provide a transaction context with automatic rollback on error."""
        try:
            self.logger.debug("Starting database transaction")
            yield session

            # Commit the transaction
            session.commit()
            self.logger.debug("Database transaction committed successfully")

        except Exception as e:
            # Rollback on any error
            session.rollback()
            self.logger.error(f"Database transaction rolled back due to error: {e}")
            raise

    @contextmanager
    def read_only_transaction(self, session: Session):
        """Provide a read-only transaction context."""
        try:
            self.logger.debug("Starting read-only transaction")
            yield session

        except Exception as e:
            self.logger.error(f"Read-only transaction error: {e}")
            raise

    def execute_in_transaction(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute a function within a transaction context."""
        try:
            with container.get_transaction() as session:
                with self.transaction_context(session):
                    result = func(*args, **kwargs)
                    return result

        except Exception as e:
            self.logger.error(f"Transaction execution failed: {e}")
            raise TransactionError(
                operation=func.__name__,
                message=f"Transaction failed for {func.__name__}: {str(e)}"
            )

    def execute_read_only(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute a function in read-only mode."""
        try:
            with container.get_transaction() as session:
                with self.read_only_transaction(session):
                    result = func(*args, **kwargs)
                    return result

        except Exception as e:
            self.logger.error(f"Read-only execution failed: {e}")
            raise TransactionError(
                operation=func.__name__,
                message=f"Read-only operation failed for {func.__name__}: {str(e)}"
            )


class TransactionDecorator:
    """Decorator for automatic transaction management."""

    def __init__(self, read_only: bool = False):
        """Initialize transaction decorator."""
        self.read_only = read_only
        self.transaction_manager = TransactionManager()

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """Apply transaction management to the function."""
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            """Execute the function within a transaction context."""
            try:
                if self.read_only:
                    return self.transaction_manager.execute_read_only(func, *args, **kwargs)
                else:
                    return self.transaction_manager.execute_in_transaction(func, *args, **kwargs)
            except Exception as e:
                logger.error(f"Transaction decorator failed for {func.__name__}: {e}")
                raise

        return wrapper


def transactional(read_only: bool = False):
    """Decorator for automatic transaction management."""
    return TransactionDecorator(read_only=read_only)


def read_only_transaction(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator for read-only transactions."""
    return TransactionDecorator(read_only=True)(func)


class UnitOfWork:
    """Unit of Work pattern implementation for managing multiple repositories."""

    def __init__(self):
        """Initialize unit of work."""
        self.logger = get_logger("transaction.uow")
        self.session = None
        self.repositories = {}

    def __enter__(self):
        """Enter the unit of work context."""
        self.session = container.get_database_session()
        self.logger.debug("Unit of Work context entered")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the unit of work context."""
        if exc_type is not None:
            # Rollback on exception
            if self.session:
                self.session.rollback()
                self.logger.error(f"Unit of Work rolled back due to exception: {exc_val}")
        else:
            # Commit on success
            if self.session:
                self.session.commit()
                self.logger.debug("Unit of Work committed successfully")

        if self.session:
            self.session.close()

    def get_repository(self, repository_type: str):
        """Get a repository instance."""
        if repository_type not in self.repositories:
            if repository_type == "device":
                self.repositories[repository_type] = container.get_device_repository()
            elif repository_type == "room":
                self.repositories[repository_type] = container.get_room_repository()
            elif repository_type == "user":
                self.repositories[repository_type] = container.get_user_repository()
            elif repository_type == "project":
                self.repositories[repository_type] = container.get_project_repository()
            elif repository_type == "building":
                self.repositories[repository_type] = container.get_building_repository()
            else:
                raise ValueError(f"Unknown repository type: {repository_type}")

        return self.repositories[repository_type]

    def commit(self):
        """Commit the current transaction."""
        if self.session:
            self.session.commit()
            self.logger.debug("Unit of Work committed")

    def rollback(self):
        """Rollback the current transaction."""
        if self.session:
            self.session.rollback()
            self.logger.debug("Unit of Work rolled back")


class TransactionService:
    """Service for managing complex transactions across multiple repositories."""

    def __init__(self):
        """Initialize transaction service."""
        self.logger = get_logger("transaction.service")
        self.transaction_manager = TransactionManager()

    @log_function_call
    def execute_complex_operation(self, operations: list) -> bool:
        """Execute a complex operation involving multiple repositories."""
        try:
            with UnitOfWork() as uow:
                for operation in operations:
                    repo_type = operation.get('repository')
                    operation_type = operation.get('type')
                    data = operation.get('data', {})

                    repository = uow.get_repository(repo_type)

                    if operation_type == 'create':
                        entity = self._create_entity(repository, data)
                        self.logger.info(f"Created {repo_type} entity: {entity.id}")

                    elif operation_type == 'update':
                        entity = self._update_entity(repository, data)
                        self.logger.info(f"Updated {repo_type} entity: {entity.id}")

                    elif operation_type == 'delete':
                        self._delete_entity(repository, data.get('id'))
                        self.logger.info(f"Deleted {repo_type} entity: {data.get('id')}")

                    else:
                        raise ValueError(f"Unknown operation type: {operation_type}")

                # All operations successful, commit
                uow.commit()
                self.logger.info("Complex operation completed successfully")
                return True

        except Exception as e:
            self.logger.error(f"Complex operation failed: {e}")
            raise TransactionError(
                operation="complex_operation",
                message=f"Complex operation failed: {str(e)}"
            )

    def _create_entity(self, repository, data: dict):
        """Create an entity using the repository."""
        try:
            # This would need to be implemented based on the specific entity type
            # For now, we'll use a generic approach'
            entity_class = repository.entity_class
            entity = entity_class(**data)
            return repository.save(entity)
        except Exception as e:
            raise BusinessRuleError(f"Failed to create entity: {str(e)}")

    def _update_entity(self, repository, data: dict):
        """Update an entity using the repository."""
        try:
            entity_id = data.get('id')
            if not entity_id:
                raise ValidationError("Entity ID is required for update")

            entity = repository.get_by_id(entity_id)
            if not entity:
                raise BusinessRuleError(f"Entity with ID {entity_id} not found")

            # Update entity fields
            for key, value in data.items():
                if hasattr(entity, key) and key != 'id':
                    setattr(entity, key, value)

            return repository.save(entity)
        except Exception as e:
            raise BusinessRuleError(f"Failed to update entity: {str(e)}")

    def _delete_entity(self, repository, entity_id):
        """Delete an entity using the repository."""
        try:
            if not entity_id:
                raise ValidationError("Entity ID is required for deletion")

            success = repository.delete(entity_id)
            if not success:
                raise BusinessRuleError(f"Entity with ID {entity_id} not found")

        except Exception as e:
            raise BusinessRuleError(f"Failed to delete entity: {str(e)}")

    @log_function_call
    def execute_with_retry(self, func: Callable[..., T], max_retries: int = 3, *args, **kwargs) -> T:
        """Execute a function with retry logic for transient failures."""
        last_exception = None

        for attempt in range(max_retries):
            try:
                return self.transaction_manager.execute_in_transaction(func, *args, **kwargs)

            except Exception as e:
                last_exception = e
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")

                if attempt < max_retries - 1:
                    # Wait before retry (exponential backoff)
                    import time
                    time.sleep(2 ** attempt)

        # All retries failed
        self.logger.error(f"All {max_retries} attempts failed")
        raise TransactionError(
            operation=func.__name__,
            message=f"Operation failed after {max_retries} attempts: {str(last_exception)}"
        )


# Global transaction service instance
transaction_service = TransactionService()


def get_transaction_service() -> TransactionService:
    """Get the global transaction service instance."""
    return transaction_service


def with_transaction(read_only: bool = False):
    """Decorator for automatic transaction management."""
    return TransactionDecorator(read_only=read_only)


def with_retry(max_retries: int = 3):
    """Decorator for automatic retry logic."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            return transaction_service.execute_with_retry(func, max_retries, *args, **kwargs)
        return wrapper
    return decorator
