"""
Database models and configuration for Arxos SVG-BIM Integration System.

This module provides SQLAlchemy models and database configuration that supports
both SQLite (development) and PostgreSQL (production) with proper connection pooling.
"""

from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, Dict, Any, List
import logging
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Create declarative base
Base = declarative_base()


class DatabaseConfig:
    """Database configuration with support for SQLite and PostgreSQL."""
    
    def __init__(
        self,
        database_url: str,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        echo: bool = False
    ):
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.echo = echo
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Create database config from environment variables."""
        database_url = os.getenv('DATABASE_URL', 'sqlite:///./data/arx_svg_parser.db')
        pool_size = int(os.getenv('DATABASE_POOL_SIZE', '10'))
        max_overflow = int(os.getenv('DATABASE_MAX_OVERFLOW', '20'))
        pool_timeout = int(os.getenv('DATABASE_POOL_TIMEOUT', '30'))
        pool_recycle = int(os.getenv('DATABASE_POOL_RECYCLE', '3600'))
        echo = os.getenv('DATABASE_ECHO', 'false').lower() == 'true'
        
        return cls(
            database_url=database_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            echo=echo
        )


class DatabaseManager:
    """Database manager with connection pooling and session management."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engine = None
        self.SessionLocal = None
        self._setup_engine()
    
    def _setup_engine(self):
        """Set up SQLAlchemy engine with connection pooling."""
        try:
            # Create engine with pooling configuration
            self.engine = create_engine(
                self.config.database_url,
                poolclass=QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                echo=self.config.echo,
                # SQLite specific settings
                connect_args={"check_same_thread": False} if "sqlite" in self.config.database_url else {}
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info(f"Database engine configured: {self.config.database_url}")
            
        except Exception as e:
            logger.error(f"Failed to setup database engine: {e}")
            raise
    
    def create_tables(self):
        """Create all tables in the database."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get a database session."""
        if not self.SessionLocal:
            raise RuntimeError("Database session factory not initialized")
        return self.SessionLocal()
    
    def close(self):
        """Close database connections."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")


# Database Models
class BIMModel(Base):
    """BIM model storage."""
    __tablename__ = "bim_models"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    model_data = Column(JSON, nullable=False)
    model_metadata = Column(JSON)  # Renamed from 'metadata'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255))
    project_id = Column(String(255))
    version = Column(String(50), default="1.0")
    is_active = Column(Boolean, default=True)
    
    # Relationships
    elements = relationship("BIMModelElement", back_populates="model", cascade="all, delete-orphan")
    systems = relationship("BIMModelSystem", back_populates="model", cascade="all, delete-orphan")
    spaces = relationship("BIMModelSpace", back_populates="model", cascade="all, delete-orphan")
    relationships = relationship("BIMModelRelationship", back_populates="model", cascade="all, delete-orphan")


class BIMModelElement(Base):
    """BIM model elements."""
    __tablename__ = "bim_model_elements"
    
    id = Column(String(36), primary_key=True)
    model_id = Column(String(36), ForeignKey("bim_models.id"), nullable=False)
    element_type = Column(String(100), nullable=False)
    element_data = Column(JSON, nullable=False)
    geometry = Column(JSON)
    properties = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    model = relationship("BIMModel", back_populates="elements")


class BIMModelSystem(Base):
    """BIM model systems."""
    __tablename__ = "bim_model_systems"
    
    id = Column(String(36), primary_key=True)
    model_id = Column(String(36), ForeignKey("bim_models.id"), nullable=False)
    system_type = Column(String(100), nullable=False)
    system_data = Column(JSON, nullable=False)
    properties = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    model = relationship("BIMModel", back_populates="systems")


class BIMModelSpace(Base):
    """BIM model spaces."""
    __tablename__ = "bim_model_spaces"
    
    id = Column(String(36), primary_key=True)
    model_id = Column(String(36), ForeignKey("bim_models.id"), nullable=False)
    space_type = Column(String(100), nullable=False)
    space_data = Column(JSON, nullable=False)
    geometry = Column(JSON)
    properties = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    model = relationship("BIMModel", back_populates="spaces")


class BIMModelRelationship(Base):
    """BIM model relationships."""
    __tablename__ = "bim_model_relationships"
    
    id = Column(String(36), primary_key=True)
    model_id = Column(String(36), ForeignKey("bim_models.id"), nullable=False)
    relationship_type = Column(String(100), nullable=False)
    source_id = Column(String(36), nullable=False)
    target_id = Column(String(36), nullable=False)
    relationship_data = Column(JSON, nullable=False)
    properties = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    model = relationship("BIMModel", back_populates="relationships")


class SymbolLibrary(Base):
    """Symbol library storage."""
    __tablename__ = "symbol_library"
    
    id = Column(String(36), primary_key=True)
    symbol_id = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    system = Column(String(100), nullable=False)
    category = Column(String(100))
    symbol_data = Column(JSON, nullable=False)
    svg_content = Column(Text)
    properties = Column(JSON)
    connections = Column(JSON)
    symbol_metadata = Column(JSON)  # Renamed from 'metadata'
    version = Column(String(50), default="1.0")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ValidationJob(Base):
    """Validation job tracking."""
    __tablename__ = "validation_jobs"
    
    id = Column(String(36), primary_key=True)
    job_type = Column(String(100), nullable=False)
    status = Column(String(50), default="pending")
    progress = Column(Integer, default=0)
    total_items = Column(Integer, default=0)
    processed_items = Column(Integer, default=0)
    errors = Column(JSON)
    warnings = Column(JSON)
    result_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)


class ExportJob(Base):
    """Export job tracking."""
    __tablename__ = "export_jobs"
    
    id = Column(String(36), primary_key=True)
    job_type = Column(String(100), nullable=False)
    status = Column(String(50), default="pending")
    progress = Column(Integer, default=0)
    total_items = Column(Integer, default=0)
    processed_items = Column(Integer, default=0)
    export_format = Column(String(50))
    file_path = Column(String(500))
    file_size = Column(Integer)
    errors = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)


class User(Base):
    """User model for authentication and RBAC."""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    roles = Column(JSON, default=list)  # List of role strings
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    user_metadata = Column(JSON)  # Additional user data


# Database session dependency
def get_db_session() -> Session:
    """Get database session for dependency injection."""
    config = DatabaseConfig.from_env()
    db_manager = DatabaseManager(config)
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get global database manager instance."""
    global _db_manager
    if _db_manager is None:
        config = DatabaseConfig.from_env()
        _db_manager = DatabaseManager(config)
    return _db_manager


def init_database():
    """Initialize database with tables."""
    db_manager = get_db_manager()
    db_manager.create_tables()
    logger.info("Database initialized successfully")


def close_database():
    """Close database connections."""
    global _db_manager
    if _db_manager:
        _db_manager.close()
        _db_manager = None
        logger.info("Database connections closed") 