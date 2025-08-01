"""
User DTOs - Data Transfer Objects for User Operations

This module contains DTOs for user-related operations including
create, read, update, delete, and list operations.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class CreateUserRequest:
    """Request DTO for creating a user."""
    
    email: str
    first_name: str
    last_name: str
    role: str
    password: Optional[str] = None
    phone_number: Optional[str] = None
    created_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CreateUserResponse:
    """Response DTO for user creation."""
    
    success: bool
    user_id: Optional[str] = None
    message: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class UpdateUserRequest:
    """Request DTO for updating a user."""
    
    user_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    phone_number: Optional[str] = None
    updated_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class UpdateUserResponse:
    """Response DTO for user updates."""
    
    success: bool
    user_id: Optional[str] = None
    message: Optional[str] = None
    error_message: Optional[str] = None
    updated_at: Optional[datetime] = None


@dataclass
class GetUserResponse:
    """Response DTO for getting a user."""
    
    success: bool
    user: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


@dataclass
class ListUsersResponse:
    """Response DTO for listing users."""
    
    success: bool
    users: List[Dict[str, Any]] = None
    total_count: int = 0
    page: int = 1
    page_size: int = 10
    error_message: Optional[str] = None


@dataclass
class DeleteUserResponse:
    """Response DTO for deleting a user."""
    
    success: bool
    user_id: Optional[str] = None
    message: Optional[str] = None
    error_message: Optional[str] = None
    deleted_at: Optional[datetime] = None 