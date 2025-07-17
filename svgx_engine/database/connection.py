"""
SVGX Engine - Database Connection Management

Provides database connection management for SVGX Engine with:
- SQLAlchemy integration with connection pooling
- Environment-based configuration
- Connection health monitoring
- Proper error handling and recovery
- Support for multiple database backends
"""

import os
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager
from datetime import datetime, timedelta

from sqlalchemy import create_engine, Engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError, OperationalError

logger = logging.getLogger(__name__)


class DatabaseConnectionManager:
    """Manages database connections for SVGX Engine."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize database connection manager."""
        self.config = config or self._load_config()
        self.engine: Optional[Engine] = None
        self.session_factory: Optional[sessionmaker] = None
        self._connection_health = {
            "last_check": None,
            "is_healthy": True,
            "error_count": 0
        }
        
    def _load_config(self) -> Dict[str, Any]:
        """Load database configuration from environment."""
        return {
            "database_url": os.getenv("SVGX_DATABASE_URL", "sqlite:///svgx_engine.db"),
            "pool_size": int(os.getenv("SVGX_DB_POOL_SIZE", "10")),
            "max_overflow": int(os.getenv("SVGX_DB_MAX_OVERFLOW", "20")),
            "pool_timeout": int(os.getenv("SVGX_DB_POOL_TIMEOUT", "30")),
            "pool_recycle": int(os.getenv("SVGX_DB_POOL_RECYCLE", "3600")),
            "echo": os.getenv("SVGX_DB_ECHO", "false").lower() == "true",
            "connect_args": self._get_connect_args()
        }
    
    def _get_connect_args(self) -> Dict[str, Any]:
        """Get database-specific connection arguments."""
        database_url = self.config["database_url"]
        
        if "postgresql" in database_url:
            return {
                "connect_timeout": 10,
                "application_name": "svgx_engine"
            }
        elif "mysql" in database_url:
            return {
                "connect_timeout": 10,
                "charset": "utf8mb4"
            }
        else:
            return {}
    
    def initialize(self) -> bool:
        """Initialize database connection."""
        try:
            logger.info("Initializing database connection...")
            
            # Create engine with connection pooling
            self.engine = create_engine(
                self.config["database_url"],
                poolclass=QueuePool,
                pool_size=self.config["pool_size"],
                max_overflow=self.config["max_overflow"],
                pool_timeout=self.config["pool_timeout"],
                pool_recycle=self.config["pool_recycle"],
                echo=self.config["echo"],
                connect_args=self.config["connect_args"]
            )
            
            # Create session factory
            self.session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False
            )
            
            # Test connection
            self._test_connection()
            
            # Set up connection event handlers
            self._setup_event_handlers()
            
            logger.info("Database connection initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            return False
    
    def _test_connection(self) -> bool:
        """Test database connection health."""
        try:
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            self._connection_health.update({
                "last_check": datetime.now(),
                "is_healthy": True,
                "error_count": 0
            })
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            self._connection_health.update({
                "last_check": datetime.now(),
                "is_healthy": False,
                "error_count": self._connection_health["error_count"] + 1
            })
            return False
    
    def _setup_event_handlers(self):
        """Set up SQLAlchemy event handlers."""
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set SQLite pragmas for better performance."""
            if "sqlite" in self.config["database_url"]:
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA cache_size=10000")
                cursor.execute("PRAGMA temp_store=MEMORY")
                cursor.close()
        
        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Handle connection checkout."""
            logger.debug("Database connection checked out")
        
        @event.listens_for(self.engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Handle connection checkin."""
            logger.debug("Database connection checked in")
    
    @contextmanager
    def get_session(self) -> Session:
        """Get database session with automatic cleanup."""
        if not self.session_factory:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_connection_health(self) -> Dict[str, Any]:
        """Get database connection health status."""
        # Test connection if last check was more than 5 minutes ago
        if (not self._connection_health["last_check"] or 
            datetime.now() - self._connection_health["last_check"] > timedelta(minutes=5)):
            self._test_connection()
        
        return {
            "is_healthy": self._connection_health["is_healthy"],
            "last_check": self._connection_health["last_check"],
            "error_count": self._connection_health["error_count"],
            "pool_size": self.config["pool_size"],
            "max_overflow": self.config["max_overflow"]
        }
    
    def close(self):
        """Close database connections."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")


# Global database manager instance
db_manager: Optional[DatabaseConnectionManager] = None


def get_db_manager() -> DatabaseConnectionManager:
    """Get global database manager instance."""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseConnectionManager()
    return db_manager


def initialize_database() -> bool:
    """Initialize global database connection."""
    global db_manager
    db_manager = DatabaseConnectionManager()
    return db_manager.initialize()


def close_database():
    """Close global database connection."""
    global db_manager
    if db_manager:
        db_manager.close()
        db_manager = None 