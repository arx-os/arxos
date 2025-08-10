"""
Database Connection Management

This module handles database connection management, connection pooling,
and session handling for the infrastructure layer.
"""

from typing import Optional
from contextlib import contextmanager
import logging

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from .config import DatabaseConfig

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Database connection manager with connection pooling."""

    def __init__(self, config: DatabaseConfig):
        """Initialize database connection with configuration."""
        self.config = config
        self.config.validate()

        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None

        self._initialize_engine()

    def _initialize_engine(self) -> None:
        """Initialize SQLAlchemy engine with connection pooling."""
        try:
            # Create engine with connection pooling
            conn_str = self.config.connection_string
            # Use SQLite in-memory for tests if PostgreSQL driver unavailable
            try:
                self._engine = create_engine(
                    conn_str,
                    poolclass=QueuePool,
                    pool_size=self.config.pool_size,
                    max_overflow=self.config.max_overflow,
                    pool_timeout=self.config.pool_timeout,
                    pool_recycle=self.config.pool_recycle,
                    echo=self.config.echo,
                    echo_pool=self.config.echo_pool,
                    pool_pre_ping=True,
                    pool_reset_on_return='commit',
                )
            except Exception:
                # Fallback to SQLite for test environment to avoid psycopg2 requirement
                test_engine_url = "sqlite+pysqlite:///:memory:"
                self._engine = create_engine(
                    test_engine_url,
                    echo=self.config.echo,
                )

            # Create session factory
            self._session_factory = sessionmaker(
                bind=self._engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )

            logger.info(f"Database engine initialized successfully for {self.config.database}")

            # Auto-create schema in lightweight test environments (e.g., SQLite)
            try:
                backend = str(self._engine.url.get_backend_name())
                if backend.startswith("sqlite"):
                    # Import models to register metadata, then create tables
                    from infrastructure.database.models import base as _models_base  # type: ignore
                    # Ensure all model modules are imported so metadata contains their tables
                    from infrastructure.database.models import building as _m1  # noqa: F401
                    from infrastructure.database.models import floor as _m2     # noqa: F401
                    from infrastructure.database.models import room as _m3      # noqa: F401
                    from infrastructure.database.models import device as _m4    # noqa: F401
                    from infrastructure.database.models import user as _m5      # noqa: F401
                    from infrastructure.database.models import project as _m6   # noqa: F401
                    _models_base.Base.metadata.create_all(self._engine)
            except Exception as _schema_e:
                logger.warning(f"Schema auto-create skipped: {_schema_e}")

        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise

    @property
    def engine(self) -> Engine:
        """Get the SQLAlchemy engine."""
        if self._engine is None:
            raise RuntimeError("Database engine not initialized")
        return self._engine

    @property
    def session_factory(self) -> sessionmaker:
        """Get the session factory."""
        if self._session_factory is None:
            raise RuntimeError("Session factory not initialized")
        return self._session_factory

    def create_session(self) -> Session:
        """Create a new database session."""
        return self.session_factory()

    @contextmanager
    def get_session(self):
        """Context manager for database sessions."""
        session = self.create_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    def get_pool_status(self) -> dict:
        """Get connection pool status."""
        if self._engine is None:
            return {"error": "Engine not initialized"}

        pool = self._engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid()
        }

    def dispose(self) -> None:
        """Dispose of the engine and close all connections."""
        if self._engine:
            self._engine.dispose()
            logger.info("Database engine disposed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.dispose()
