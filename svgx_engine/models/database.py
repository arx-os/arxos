"""
Database models for SVGX Engine.

This module defines SQLAlchemy models for SVGX documents, objects,
symbols, and related entities.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import create_engine, Column, String, Text, DateTime, Boolean, Integer, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

Base = declarative_base()


class DatabaseConfig:
    """Database configuration for SVGX Engine."""

    def __init__(self, database_url: str = None, echo: bool = False):
    """
    Perform __init__ operation

Args:
        database_url: Description of database_url
        echo: Description of echo

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        self.database_url = database_url or "sqlite:///svgx_engine.db"
        self.echo = echo

    def get_engine(self):
        """Get SQLAlchemy engine."""
        if self.database_url.startswith('sqlite'):
            return create_engine(
                self.database_url,
                echo=self.echo,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool
            )
        else:
            return create_engine(self.database_url, echo=self.echo)


class DatabaseManager:
    """
    Perform __init__ operation

Args:
        config: Description of config

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
    """Database manager for SVGX Engine."""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engine = config.get_engine()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # Create tables
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()

    def close(self):
        """Close database connections."""
        if hasattr(self, 'engine'):
            self.engine.dispose()


def get_db_manager(config: DatabaseConfig = None) -> DatabaseManager:
    """Get database manager instance."""
    if config is None:
        config = DatabaseConfig()
    return DatabaseManager(config)


class SVGXModel(Base):
    """SVGX document model."""

    __tablename__ = "svgx_models"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    document_data = Column(JSON, nullable=False)
    document_metadata = Column(JSON, nullable=True)
    document_type = Column(String(50), default='svgx')
    created_by = Column(String(255), nullable=True)
    project_id = Column(String(255), nullable=True)
    version = Column(String(50), default='1.0')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SVGXElement(Base):
    """SVGX element model."""

    __tablename__ = "svgx_elements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), nullable=False)
    element_type = Column(String(100), nullable=False)
    element_data = Column(JSON, nullable=False)
    position_x = Column(Float, nullable=True)
    position_y = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SVGXObject(Base):
    """SVGX object model."""

    __tablename__ = "svgx_objects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    object_type = Column(String(100), nullable=False)
    system = Column(String(100), nullable=True)
    object_data = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SVGXBehavior(Base):
    """SVGX behavior model."""

    __tablename__ = "svgx_behaviors"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    object_id = Column(String(36), nullable=False)
    behavior_type = Column(String(100), nullable=False)
    behavior_data = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SVGXPhysics(Base):
    """SVGX physics model."""

    __tablename__ = "svgx_physics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    object_id = Column(String(36), nullable=False)
    physics_type = Column(String(100), nullable=False)
    physics_data = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SymbolLibrary(Base):
    """Symbol library model."""

    __tablename__ = "symbol_library"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    system = Column(String(100), nullable=True)
    category = Column(String(100), nullable=True)
    symbol_data = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ValidationJob(Base):
    """Validation job model."""

    __tablename__ = "validation_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_type = Column(String(100), nullable=False)
    status = Column(String(50), default='pending')
    progress = Column(Integer, default=0)
    total_items = Column(Integer, default=0)
    processed_items = Column(Integer, default=0)
    errors = Column(JSON, nullable=True)
    warnings = Column(JSON, nullable=True)
    result_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ExportJob(Base):
    """Export job model."""

    __tablename__ = "export_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_type = Column(String(100), nullable=False)
    export_format = Column(String(50), nullable=False)
    status = Column(String(50), default='pending')
    progress = Column(Integer, default=0)
    total_items = Column(Integer, default=0)
    processed_items = Column(Integer, default=0)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    errors = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
