"""
Floor DTOs - Data Transfer Objects for Floor Operations

This module contains DTOs for floor-related operations including
create, read, update, delete, and list operations.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class CreateFloorRequest:
    """Request DTO for creating a floor."""
    
    building_id: str
    floor_number: int
    description: Optional[str] = None
    created_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CreateFloorResponse:
    """Response DTO for floor creation."""
    
    success: bool
    floor_id: Optional[str] = None
    message: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class UpdateFloorRequest:
    """Request DTO for updating a floor."""
    
    floor_id: str
    floor_number: Optional[int] = None
    description: Optional[str] = None
    status: Optional[str] = None
    updated_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class UpdateFloorResponse:
    """Response DTO for floor updates."""
    
    success: bool
    floor_id: Optional[str] = None
    message: Optional[str] = None
    error_message: Optional[str] = None
    updated_at: Optional[datetime] = None


@dataclass
class GetFloorResponse:
    """Response DTO for getting a floor."""
    
    success: bool
    floor: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


@dataclass
class ListFloorsResponse:
    """Response DTO for listing floors."""
    
    success: bool
    floors: List[Dict[str, Any]] = None
    total_count: int = 0
    page: int = 1
    page_size: int = 10
    error_message: Optional[str] = None


@dataclass
class DeleteFloorResponse:
    """Response DTO for deleting a floor."""
    
    success: bool
    floor_id: Optional[str] = None
    message: Optional[str] = None
    error_message: Optional[str] = None
    deleted_at: Optional[datetime] = None 