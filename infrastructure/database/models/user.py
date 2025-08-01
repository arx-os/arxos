"""
User Database Model

This module contains the SQLAlchemy model for the User entity,
mapping domain user objects to database tables.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Enum, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID

from .base import BaseModel
from domain.value_objects import UserRole


class UserModel(BaseModel):
    """User database model."""
    
    __tablename__ = 'users'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True)
    
    # Basic information
    email = Column(String(255), nullable=False, unique=True, index=True)
    username = Column(String(100), nullable=False, unique=True, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    
    # Role and status
    role = Column(Enum(UserRole), nullable=False, default=UserRole.VIEWER, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    # Contact information
    phone_number = Column(String(50), nullable=True)
    country_code = Column(String(10), nullable=True, default="+1")
    
    # Additional information
    description = Column(Text, nullable=True)
    
    def __repr__(self) -> str:
        """String representation of the user model."""
        return f"<UserModel(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.username
    
    def update_role(self, new_role: UserRole, updated_by: Optional[str] = None) -> None:
        """Update user role."""
        self.role = new_role
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
    
    def deactivate(self, deactivated_by: Optional[str] = None) -> None:
        """Deactivate the user."""
        self.is_active = False
        self.updated_at = datetime.utcnow()
        self.updated_by = deactivated_by
    
    def activate(self, activated_by: Optional[str] = None) -> None:
        """Activate the user."""
        self.is_active = True
        self.updated_at = datetime.utcnow()
        self.updated_by = activated_by 