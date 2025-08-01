"""
Room DTOs - Data Transfer Objects for Room Operations

This module contains DTOs for room-related operations including
create, read, update, delete, and list operations.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class CreateRoomRequest:
    """Request DTO for creating a room."""
    
    floor_id: str
    room_number: str
    room_type: str
    description: Optional[str] = None
    created_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CreateRoomResponse:
    """Response DTO for room creation."""
    
    success: bool
    room_id: Optional[str] = None
    message: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class UpdateRoomRequest:
    """Request DTO for updating a room."""
    
    room_id: str
    room_number: Optional[str] = None
    room_type: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    updated_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class UpdateRoomResponse:
    """Response DTO for room updates."""
    
    success: bool
    room_id: Optional[str] = None
    message: Optional[str] = None
    error_message: Optional[str] = None
    updated_at: Optional[datetime] = None


@dataclass
class GetRoomResponse:
    """Response DTO for getting a room."""
    
    success: bool
    room: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


@dataclass
class ListRoomsResponse:
    """Response DTO for listing rooms."""
    
    success: bool
    rooms: List[Dict[str, Any]] = None
    total_count: int = 0
    page: int = 1
    page_size: int = 10
    error_message: Optional[str] = None


@dataclass
class DeleteRoomResponse:
    """Response DTO for deleting a room."""
    
    success: bool
    room_id: Optional[str] = None
    message: Optional[str] = None
    error_message: Optional[str] = None
    deleted_at: Optional[datetime] = None 