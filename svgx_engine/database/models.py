"""
SVGX Engine - Database Models

Defines SQLAlchemy models for SVGX Engine entities:
- SVGX documents and elements
- Symbols and symbol libraries
- Users and collaborative sessions
- Performance metrics and telemetry
- Export and compilation history
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, String, Text, DateTime, Integer, Float, Boolean,
    JSON, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()


class SVGXDocument(Base):
    """SVGX document model."""

    __tablename__ = "svgx_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    document_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    elements: Mapped[List["SVGXElement"]] = relationship("SVGXElement", back_populates="document", cascade="all, delete-orphan")
    exports: Mapped[List["ExportHistory"]] = relationship("ExportHistory", back_populates="document", cascade="all, delete-orphan")
    collaborations: Mapped[List["CollaborationSession"]] = relationship("CollaborationSession", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_documents_name", "name"),
        Index("idx_documents_created_by", "created_by"),
        Index("idx_documents_created_at", "created_at"),
    )


class SVGXElement(Base):
    """SVGX element model."""

    __tablename__ = "svgx_elements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("svgx_documents.id"), nullable=False)
    element_id: Mapped[str] = mapped_column(String(255), nullable=False)
    element_type: Mapped[str] = mapped_column(String(100), nullable=False)
    attributes: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    position_x: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    position_y: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    width: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    height: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    layer: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    precision: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    document: Mapped["SVGXDocument"] = relationship("SVGXDocument", back_populates="elements")

    __table_args__ = (
        Index("idx_elements_document_id", "document_id"),
        Index("idx_elements_element_id", "element_id"),
        Index("idx_elements_type", "element_type"),
        Index("idx_elements_layer", "layer"),
        UniqueConstraint("document_id", "element_id", name="uq_document_element"),
    )


class Symbol(Base):
    """Symbol model for SVGX symbol library."""

    __tablename__ = "symbols"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    symbol_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    # Relationships
    symbol_usage: Mapped[List["SymbolUsage"]] = relationship("SymbolUsage", back_populates="symbol", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_symbols_name", "name"),
        Index("idx_symbols_category", "category"),
        Index("idx_symbols_created_by", "created_by"),
        UniqueConstraint("name", "version", name="uq_symbol_name_version"),
    )


class SymbolUsage(Base):
    """Symbol usage tracking model."""

    __tablename__ = "symbol_usage"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol_id: Mapped[str] = mapped_column(String(36), ForeignKey("symbols.id"), nullable=False)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("svgx_documents.id"), nullable=False)
    element_id: Mapped[str] = mapped_column(String(255), nullable=False)
    usage_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    first_used: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_used: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    symbol: Mapped["Symbol"] = relationship("Symbol", back_populates="symbol_usage")

    __table_args__ = (
        Index("idx_symbol_usage_symbol_id", "symbol_id"),
        Index("idx_symbol_usage_document_id", "document_id"),
        Index("idx_symbol_usage_last_used", "last_used"),
        UniqueConstraint("symbol_id", "document_id", "element_id", name="uq_symbol_usage"),
    )


class User(Base):
    """User model for collaborative features."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    collaboration_sessions: Mapped[List["CollaborationSession"]] = relationship("CollaborationSession", back_populates="user", cascade="all, delete-orphan")
    documents: Mapped[List["SVGXDocument"]] = relationship("SVGXDocument", foreign_keys="SVGXDocument.created_by")

    __table_args__ = (
        Index("idx_users_username", "username"),
        Index("idx_users_email", "email"),
    )


class CollaborationSession(Base):
    """Collaboration session model."""

    __tablename__ = "collaboration_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("svgx_documents.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    session_id: Mapped[str] = mapped_column(String(255), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_activity: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    document: Mapped["SVGXDocument"] = relationship("SVGXDocument", back_populates="collaborations")
    user: Mapped["User"] = relationship("User", back_populates="collaboration_sessions")
    operations: Mapped[List["CollaborationOperation"]] = relationship("CollaborationOperation", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_collaboration_document_id", "document_id"),
        Index("idx_collaboration_user_id", "user_id"),
        Index("idx_collaboration_session_id", "session_id"),
        Index("idx_collaboration_last_activity", "last_activity"),
    )


class CollaborationOperation(Base):
    """Collaboration operation model."""

    __tablename__ = "collaboration_operations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("collaboration_sessions.id"), nullable=False)
    operation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    element_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    session: Mapped["CollaborationSession"] = relationship("CollaborationSession", back_populates="operations")

    __table_args__ = (
        Index("idx_operations_session_id", "session_id"),
        Index("idx_operations_type", "operation_type"),
        Index("idx_operations_timestamp", "timestamp"),
        Index("idx_operations_sequence", "session_id", "sequence_number"),
    )


class ExportHistory(Base):
    """Export history model."""

    __tablename__ = "export_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("svgx_documents.id"), nullable=False)
    export_format: Mapped[str] = mapped_column(String(50), nullable=False)
    export_options: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    export_duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    # Relationships
    document: Mapped["SVGXDocument"] = relationship("SVGXDocument", back_populates="exports")

    __table_args__ = (
        Index("idx_export_document_id", "document_id"),
        Index("idx_export_format", "export_format"),
        Index("idx_export_created_at", "created_at"),
        Index("idx_export_success", "success"),
    )


class PerformanceMetric(Base):
    """Performance metrics model."""

    __tablename__ = "performance_metrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    metric_unit: Mapped[str] = mapped_column(String(50), nullable=False)
    context: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    session_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    __table_args__ = (
        Index("idx_metrics_name", "metric_name"),
        Index("idx_metrics_timestamp", "timestamp"),
        Index("idx_metrics_session_id", "session_id"),
        Index("idx_metrics_user_id", "user_id"),
    )


class TelemetryEvent(Base):
    """Telemetry events model."""

    __tablename__ = "telemetry_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    event_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    document_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    __table_args__ = (
        Index("idx_telemetry_type", "event_type"),
        Index("idx_telemetry_timestamp", "timestamp"),
        Index("idx_telemetry_user_id", "user_id"),
        Index("idx_telemetry_session_id", "session_id"),
        Index("idx_telemetry_document_id", "document_id"),
    )
