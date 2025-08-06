"""
Database Connection Pooling for MCP Engineering

This module provides optimized database connection pooling for the MCP Engineering API,
including connection management, performance monitoring, and health checks.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
import time

from sqlalchemy import create_engine, event, text
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


@dataclass
class PoolConfig:
    """Configuration for database connection pooling."""

    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30
    pool_recycle: int = 3600
    pool_pre_ping: bool = True
    echo: bool = False
    echo_pool: bool = False
    pool_reset_on_return: str = "commit"


class DatabaseConnectionPool:
    """Optimized database connection pooling system."""

    def __init__(self, database_url: str, config: Optional[PoolConfig] = None):
        """
        Initialize database connection pool.

        Args:
            database_url: Database connection URL
            config: Pool configuration
        """
        self.database_url = database_url
        self.config = config or PoolConfig()

        # Create engine with optimized settings
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            pool_timeout=self.config.pool_timeout,
            pool_recycle=self.config.pool_recycle,
            pool_pre_ping=self.config.pool_pre_ping,
            echo=self.config.echo,
            echo_pool=self.config.echo_pool,
            pool_reset_on_return=self.config.pool_reset_on_return,
        )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        # Performance tracking
        self.connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "failed_connections": 0,
            "connection_errors": 0,
            "query_count": 0,
            "slow_queries": 0,
        }

        # Set up event listeners
        self._setup_event_listeners()

    def _setup_event_listeners(self):
        """Set up SQLAlchemy event listeners for monitoring."""

        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_connection, connection_record):
            """Track connection creation."""
            self.connection_stats["total_connections"] += 1
            self.connection_stats["active_connections"] += 1
            logger.info(
                f"Database connection established. Active: {self.connection_stats['active_connections']}"
            )

        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Track connection checkout."""
            logger.debug("Database connection checked out")

        @event.listens_for(self.engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Track connection checkin."""
            self.connection_stats["active_connections"] -= 1
            logger.debug("Database connection checked in")

        @event.listens_for(self.engine, "disconnect")
        def receive_disconnect(dbapi_connection, connection_record):
            """Track connection disconnection."""
            self.connection_stats["active_connections"] -= 1
            logger.warning("Database connection disconnected")

        @event.listens_for(self.engine, "before_cursor_execute")
        def receive_before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            """Track query execution start."""
            context._query_start_time = time.time()
            self.connection_stats["query_count"] += 1

        @event.listens_for(self.engine, "after_cursor_execute")
        def receive_after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            """Track query execution completion."""
            if hasattr(context, "_query_start_time"):
                query_time = time.time() - context._query_start_time
                if query_time > 1.0:  # Slow query threshold
                    self.connection_stats["slow_queries"] += 1
                    logger.warning(
                        f"Slow query detected: {query_time:.2f}s - {statement[:100]}..."
                    )

    @contextmanager
    def get_connection(self):
        """
        Get a database connection from the pool.

        Yields:
            Database connection
        """
        connection = None
        try:
            connection = self.engine.connect()
            yield connection
        except SQLAlchemyError as e:
            self.connection_stats["connection_errors"] += 1
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if connection:
                connection.close()

    @contextmanager
    def get_session(self):
        """
        Get a database session from the pool.

        Yields:
            Database session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    async def get_async_connection(self):
        """
        Get an async database connection.

        Returns:
            Async database connection
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.engine.connect)

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the connection pool.

        Returns:
            Health check results
        """
        try:
            with self.get_connection() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()

            return {
                "status": "healthy",
                "pool_size": self.engine.pool.size(),
                "checked_in": self.engine.pool.checkedin(),
                "checked_out": self.engine.pool.checkedout(),
                "overflow": self.engine.pool.overflow(),
                "invalid": self.engine.pool.invalid(),
                "stats": self.connection_stats.copy(),
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "stats": self.connection_stats.copy(),
            }

    def get_pool_stats(self) -> Dict[str, Any]:
        """
        Get detailed pool statistics.

        Returns:
            Pool statistics
        """
        pool = self.engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
            "connection_stats": self.connection_stats.copy(),
            "database_url": (
                self.database_url.replace(
                    self.database_url.split("@")[0].split("://")[1], "***:***"
                )
                if "@" in self.database_url
                else self.database_url
            ),
        }

    def dispose(self):
        """Dispose of the connection pool."""
        self.engine.dispose()
        logger.info("Database connection pool disposed")

    def reset_stats(self):
        """Reset connection statistics."""
        self.connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "failed_connections": 0,
            "connection_errors": 0,
            "query_count": 0,
            "slow_queries": 0,
        }
        logger.info("Database connection statistics reset")


class AsyncDatabasePool:
    """Async database connection pooling."""

    def __init__(self, database_url: str, config: Optional[PoolConfig] = None):
        """
        Initialize async database connection pool.

        Args:
            database_url: Database connection URL
            config: Pool configuration
        """
        self.database_url = database_url
        self.config = config or PoolConfig()
        self.pool = None
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Initialize the async connection pool."""
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker

        self.engine = create_async_engine(
            self.database_url,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            pool_timeout=self.config.pool_timeout,
            pool_recycle=self.config.pool_recycle,
            pool_pre_ping=self.config.pool_pre_ping,
            echo=self.config.echo,
        )

        self.AsyncSessionLocal = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

        logger.info("Async database connection pool initialized")

    @asynccontextmanager
    async def get_session(self):
        """
        Get an async database session.

        Yields:
            Async database session
        """
        if not hasattr(self, "engine"):
            await self.initialize()

        async with self.AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Async database session error: {e}")
                raise

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform async health check on the connection pool.

        Returns:
            Health check results
        """
        try:
            async with self.get_session() as session:
                result = await session.execute(text("SELECT 1"))
                await result.fetchone()

            return {
                "status": "healthy",
                "pool_size": self.engine.pool.size(),
                "checked_in": self.engine.pool.checkedin(),
                "checked_out": self.engine.pool.checkedout(),
                "overflow": self.engine.pool.overflow(),
                "invalid": self.engine.pool.invalid(),
            }
        except Exception as e:
            logger.error(f"Async database health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def dispose(self):
        """Dispose of the async connection pool."""
        if hasattr(self, "engine"):
            await self.engine.dispose()
            logger.info("Async database connection pool disposed")


class ConnectionPoolManager:
    """Manager for multiple database connection pools."""

    def __init__(self):
        """Initialize connection pool manager."""
        self.pools: Dict[str, DatabaseConnectionPool] = {}
        self.async_pools: Dict[str, AsyncDatabasePool] = {}

    def add_pool(
        self, name: str, database_url: str, config: Optional[PoolConfig] = None
    ):
        """
        Add a database connection pool.

        Args:
            name: Pool name
            database_url: Database connection URL
            config: Pool configuration
        """
        self.pools[name] = DatabaseConnectionPool(database_url, config)
        logger.info(f"Database connection pool '{name}' added")

    def add_async_pool(
        self, name: str, database_url: str, config: Optional[PoolConfig] = None
    ):
        """
        Add an async database connection pool.

        Args:
            name: Pool name
            database_url: Database connection URL
            config: Pool configuration
        """
        self.async_pools[name] = AsyncDatabasePool(database_url, config)
        logger.info(f"Async database connection pool '{name}' added")

    def get_pool(self, name: str) -> Optional[DatabaseConnectionPool]:
        """
        Get a database connection pool.

        Args:
            name: Pool name

        Returns:
            Database connection pool or None
        """
        return self.pools.get(name)

    def get_async_pool(self, name: str) -> Optional[AsyncDatabasePool]:
        """
        Get an async database connection pool.

        Args:
            name: Pool name

        Returns:
            Async database connection pool or None
        """
        return self.async_pools.get(name)

    def health_check_all(self) -> Dict[str, Any]:
        """
        Perform health check on all pools.

        Returns:
            Health check results for all pools
        """
        results = {}

        for name, pool in self.pools.items():
            results[name] = pool.health_check()

        for name, pool in self.async_pools.items():
            # Note: This would need to be awaited in an async context
            results[f"{name}_async"] = {"status": "async_pool"}

        return results

    def dispose_all(self):
        """Dispose of all connection pools."""
        for name, pool in self.pools.items():
            pool.dispose()
            logger.info(f"Database connection pool '{name}' disposed")

        for name, pool in self.async_pools.items():
            # Note: This would need to be awaited in an async context
            logger.info(f"Async database connection pool '{name}' marked for disposal")


# Global connection pool manager
pool_manager = ConnectionPoolManager()
