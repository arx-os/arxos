"""
MCP-Engineering Database Models

This module contains SQLAlchemy models for MCP-Engineering entities,
following the existing database patterns in the Arxos platform.
"""

from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    Text,
    JSON,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from .base import Base


class MCPBuildingData(Base):
    """Database model for building data."""

    __tablename__ = "mcp_building_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    area = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    building_type = Column(String(100), nullable=False)
    occupancy = Column(String(100))
    floors = Column(Integer)
    jurisdiction = Column(String(100))
    address = Column(Text)
    construction_type = Column(String(100))
    year_built = Column(Integer)
    renovation_year = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    validation_sessions = relationship(
        "MCPValidationSession", back_populates="building_data"
    )
    validation_results = relationship(
        "MCPValidationResult", back_populates="building_data"
    )
    compliance_reports = relationship(
        "MCPComplianceReport", back_populates="building_data"
    )


class MCPComplianceIssue(Base):
    """Database model for compliance issues."""

    __tablename__ = "mcp_compliance_issues"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code_reference = Column(String(200), nullable=False)
    severity = Column(
        SQLEnum("critical", "high", "medium", "low", "info", name="issue_severity"),
        nullable=False,
    )
    description = Column(Text, nullable=False)
    resolution = Column(Text, nullable=False)
    affected_systems = Column(JSON)
    estimated_cost = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign keys
    validation_result_id = Column(
        UUID(as_uuid=True), ForeignKey("mcp_validation_results.id")
    )

    # Relationships
    validation_result = relationship("MCPValidationResult", back_populates="issues")


class MCPAIRecommendation(Base):
    """Database model for AI recommendations."""

    __tablename__ = "mcp_ai_recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(
        SQLEnum(
            "optimization",
            "compliance",
            "safety",
            "efficiency",
            "cost_saving",
            name="suggestion_type",
        ),
        nullable=False,
    )
    description = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    impact_score = Column(Float, nullable=False)
    implementation_cost = Column(Float)
    estimated_savings = Column(Float)
    affected_systems = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign keys
    validation_result_id = Column(
        UUID(as_uuid=True), ForeignKey("mcp_validation_results.id")
    )

    # Relationships
    validation_result = relationship(
        "MCPValidationResult", back_populates="suggestions"
    )


class MCPValidationResult(Base):
    """Database model for validation results."""

    __tablename__ = "mcp_validation_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    validation_type = Column(
        SQLEnum(
            "structural",
            "electrical",
            "mechanical",
            "plumbing",
            "fire",
            "accessibility",
            "energy",
            name="validation_type",
        ),
        nullable=False,
    )
    status = Column(
        SQLEnum(
            "pass", "fail", "warning", "pending", "error", name="validation_status"
        ),
        nullable=False,
    )
    confidence_score = Column(Float, default=0.0)
    processing_time = Column(Float, default=0.0)
    model_version = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    # Foreign keys
    building_data_id = Column(
        UUID(as_uuid=True), ForeignKey("mcp_building_data.id"), nullable=False
    )
    validation_session_id = Column(
        UUID(as_uuid=True), ForeignKey("mcp_validation_sessions.id")
    )

    # Relationships
    building_data = relationship("MCPBuildingData", back_populates="validation_results")
    validation_session = relationship(
        "MCPValidationSession", back_populates="validation_result"
    )
    issues = relationship(
        "MCPComplianceIssue",
        back_populates="validation_result",
        cascade="all, delete-orphan",
    )
    suggestions = relationship(
        "MCPAIRecommendation",
        back_populates="validation_result",
        cascade="all, delete-orphan",
    )


class MCPValidationSession(Base):
    """Database model for validation sessions."""

    __tablename__ = "mcp_validation_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), nullable=False)
    validation_type = Column(
        SQLEnum(
            "structural",
            "electrical",
            "mechanical",
            "plumbing",
            "fire",
            "accessibility",
            "energy",
            name="validation_type",
        ),
        nullable=False,
    )
    project_id = Column(String(100))
    status = Column(
        SQLEnum(
            "pass", "fail", "warning", "pending", "error", name="validation_status"
        ),
        default="pending",
    )
    include_suggestions = Column(Boolean, default=True)
    confidence_threshold = Column(Float, default=0.7)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    processing_time = Column(Float)

    # Foreign keys
    building_data_id = Column(
        UUID(as_uuid=True), ForeignKey("mcp_building_data.id"), nullable=False
    )

    # Relationships
    building_data = relationship(
        "MCPBuildingData", back_populates="validation_sessions"
    )
    validation_result = relationship(
        "MCPValidationResult", back_populates="validation_session", uselist=False
    )


class MCPKnowledgeSearchResult(Base):
    """Database model for knowledge base search results."""

    __tablename__ = "mcp_knowledge_search_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code_reference = Column(String(200), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    code_standard = Column(String(100), nullable=False)
    relevance_score = Column(Float, nullable=False)
    section_number = Column(String(50))
    subsection = Column(String(100))
    jurisdiction = Column(String(100))
    effective_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class MCPMLPrediction(Base):
    """Database model for ML predictions."""

    __tablename__ = "mcp_ml_predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_type = Column(String(100), nullable=False)
    prediction_value = Column(String(500), nullable=False)
    confidence = Column(Float, nullable=False)
    model_version = Column(String(100), nullable=False)
    model_name = Column(String(100), nullable=False)
    features = Column(JSON)
    processing_time = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class MCPComplianceReport(Base):
    """Database model for compliance reports."""

    __tablename__ = "mcp_compliance_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_type = Column(
        SQLEnum("comprehensive", "summary", "technical", name="report_type"),
        nullable=False,
    )
    format = Column(
        SQLEnum("pdf", "html", "json", name="report_format"), nullable=False
    )
    user_id = Column(String(100), nullable=False)
    project_id = Column(String(100))
    generated_at = Column(DateTime, default=datetime.utcnow)
    download_url = Column(Text)
    file_size = Column(Integer)
    checksum = Column(String(64))

    # Foreign keys
    building_data_id = Column(
        UUID(as_uuid=True), ForeignKey("mcp_building_data.id"), nullable=False
    )

    # Relationships
    building_data = relationship("MCPBuildingData", back_populates="compliance_reports")
    validation_results = relationship(
        "MCPValidationResult", secondary="mcp_report_validation_results"
    )


class MCPReportValidationResult(Base):
    """Association table for reports and validation results."""

    __tablename__ = "mcp_report_validation_results"

    report_id = Column(
        UUID(as_uuid=True), ForeignKey("mcp_compliance_reports.id"), primary_key=True
    )
    validation_result_id = Column(
        UUID(as_uuid=True), ForeignKey("mcp_validation_results.id"), primary_key=True
    )


class MCPValidationStatistics(Base):
    """Database model for validation statistics."""

    __tablename__ = "mcp_validation_statistics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    total_validations = Column(Integer, default=0)
    successful_validations = Column(Integer, default=0)
    failed_validations = Column(Integer, default=0)
    average_processing_time = Column(Float, default=0.0)
    total_processing_time = Column(Float, default=0.0)
    average_confidence_score = Column(Float, default=0.0)
    total_issues_found = Column(Integer, default=0)
    total_suggestions_generated = Column(Integer, default=0)
    most_common_validation_type = Column(String(100))
    last_validation_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
