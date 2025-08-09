"""
Database Session Management

This module provides session management utilities for the infrastructure layer,
including session scoping, transaction management, and session lifecycle handling.
"""

from typing import Optional, Callable, Any
from contextlib import contextmanager
import logging
from functools import wraps

from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class DatabaseSession:
    """Database session manager with transaction handling."""

    def __init__(self, session_factory: sessionmaker):
        """Initialize session manager with session factory."""
        self.session_factory = session_factory
        self._current_session: Optional[Session] = None

    @contextmanager
def transaction(self):
        """Context manager for database transactions."""
        session = self.session_factory()
        try:
            yield session
            session.commit()
            logger.debug("Database transaction committed successfully")
        except Exception as e:
            session.rollback()
            logger.error(f"Database transaction rolled back: {e}")
            raise
        finally:
            session.close()

    @contextmanager
def session(self):
        """Context manager for database sessions without automatic commit."""
        session = self.session_factory()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def with_transaction(self, func: Callable) -> Callable:
        """Decorator to wrap functions with database transaction."""
        @wraps(func)
def wrapper(*args, **kwargs) -> Any:
    """
    Perform wrapper operation

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = wrapper(param)
        print(result)
    """
            with self.transaction() as session:
                return func(session, *args, **kwargs)
        return wrapper

    def with_session(self, func: Callable) -> Callable:
    """
    Perform wrapper operation

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = wrapper(param)
        print(result)
    """
        """Decorator to wrap functions with database session."""
        @wraps(func)
def wrapper(*args, **kwargs) -> Any:
            with self.session() as session:
                return func(session, *args, **kwargs)
        return wrapper

    def execute_in_transaction(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute an operation within a transaction."""
        with self.transaction() as session:
            return operation(session, *args, **kwargs)

    def execute_in_session(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute an operation within a session."""
        with self.session() as session:
            return operation(session, *args, **kwargs)

    def health_check(self) -> dict:
        """Perform database health check."""
        try:
            with self.session() as session:
                result = session.execute("SELECT 1 as health_check")
                row = result.fetchone()
                if row and row[0] == 1:
                    return {
                        "status": "healthy",
                        "message": "Database connection is working"
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "message": "Database health check failed"
                    }
        except SQLAlchemyError as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"Database connection error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error during health check: {e}")
            return {
                "status": "unhealthy",
                "message": f"Unexpected error: {str(e)}"
            }


class SessionScope:
    """Session scope manager for dependency injection."""

    def __init__(self, session_factory: sessionmaker):
        """Initialize session scope."""
        self.session_factory = session_factory
        self._session_stack: list[Session] = []

    def get_current_session(self) -> Optional[Session]:
        """Get the current session from the stack."""
        return self._session_stack[-1] if self._session_stack else None

    @contextmanager
def session_scope(self):
        """Create a session scope for dependency injection."""
        session = self.session_factory()
        self._session_stack.append(session)
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
            self._session_stack.pop()

    def require_session(self, func: Callable) -> Callable:
        """Decorator to require an active session."""
        @wraps(func)
def wrapper(*args, **kwargs) -> Any:
            session = self.get_current_session()
            if session is None:
                raise RuntimeError("No active database session")
            return func(session, *args, **kwargs)
        return wrapper
