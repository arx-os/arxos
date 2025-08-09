"""
Project Database Model

This module contains the SQLAlchemy model for the Project entity,
mapping domain project objects to database tables.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Enum, Text, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from .base import BaseModel
from domain.value_objects import ProjectStatus


class ProjectModel(BaseModel):
    """Project database model."""

    __tablename__ = 'projects'

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True)

    # Foreign key to building
    building_id = Column(UUID(as_uuid=True), ForeignKey('buildings.id'), nullable=False, index=True)

    # Basic information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Status
    status = Column(Enum(ProjectStatus), nullable=False, default=ProjectStatus.DRAFT, index=True)

    # Dates
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    # Relationships
    building = relationship("BuildingModel", back_populates="projects")

    def __repr__(self) -> str:
        """String representation of the project model."""
        return f"<ProjectModel(id={self.id}, name='{self.name}', status={self.status})>"

    @property
def duration_days(self) -> Optional[int]:
        """Calculate project duration in days."""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return None

    def update_status(self, new_status: ProjectStatus, updated_by: Optional[str] = None) -> None:
        """Update project status."""
        self.status = new_status
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by

    def update_name(self, new_name: str, updated_by: Optional[str] = None) -> None:
        """Update project name."""
        self.name = new_name
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
