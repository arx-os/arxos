"""
Base Database Model

This module contains the base model class that provides common functionality
for all database models, including timestamps, metadata, and audit fields.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import Column, DateTime, String, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declared_attr

Base = declarative_base()


class BaseModel(Base):
    """Base model with common fields and functionality."""
    
    __abstract__ = True
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    
    # Metadata for extensibility
    metadata_json = Column(JSON, default=dict, nullable=False)
    
    # Soft delete support
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(String(255), nullable=True)
    
    @declared_attr
    def __tablename__(cls):
        """Generate table name from class name."""
        return cls.__name__.lower() + 's'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Update model from dictionary."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def is_deleted(self) -> bool:
        """Check if the record is soft deleted."""
        return self.deleted_at is not None
    
    def soft_delete(self, deleted_by: Optional[str] = None) -> None:
        """Soft delete the record."""
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by
        self.updated_at = datetime.utcnow()
        self.updated_by = deleted_by
    
    def restore(self, restored_by: Optional[str] = None) -> None:
        """Restore a soft deleted record."""
        self.deleted_at = None
        self.deleted_by = None
        self.updated_at = datetime.utcnow()
        self.updated_by = restored_by
    
    def update_metadata(self, metadata: Dict[str, Any], updated_by: Optional[str] = None) -> None:
        """Update metadata field."""
        if self.metadata_json is None:
            self.metadata_json = {}
        self.metadata_json.update(metadata)
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value by key."""
        if self.metadata_json is None:
            return default
        return self.metadata_json.get(key, default)
    
    def set_metadata(self, key: str, value: Any, updated_by: Optional[str] = None) -> None:
        """Set metadata value by key."""
        if self.metadata_json is None:
            self.metadata_json = {}
        self.metadata_json[key] = value
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by 