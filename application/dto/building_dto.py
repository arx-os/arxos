"""
Building DTOs - Data Transfer Objects for Building Operations

This module contains DTOs for building-related operations including
create, read, update, delete, and list operations.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class CreateBuildingRequest:
    """Request DTO for creating a building."""
    
    name: str
    address: str
    description: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    dimensions: Optional[Dict[str, float]] = None
    created_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CreateBuildingResponse:
    """Response DTO for building creation."""
    
    success: bool
    building_id: Optional[str] = None
    message: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class UpdateBuildingRequest:
    """Request DTO for updating a building."""
    
    building_id: str
    name: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    dimensions: Optional[Dict[str, float]] = None
    status: Optional[str] = None
    updated_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class UpdateBuildingResponse:
    """Response DTO for building updates."""
    
    success: bool
    building_id: Optional[str] = None
    message: Optional[str] = None
    error_message: Optional[str] = None
    updated_at: Optional[datetime] = None


@dataclass
class GetBuildingResponse:
    """Response DTO for getting a building."""
    
    success: bool
    building: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


@dataclass
class ListBuildingsResponse:
    """Response DTO for listing buildings."""
    
    success: bool
    buildings: List[Dict[str, Any]] = None
    total_count: int = 0
    page: int = 1
    page_size: int = 10
    error_message: Optional[str] = None


@dataclass
class DeleteBuildingResponse:
    """Response DTO for deleting a building."""
    
    success: bool
    building_id: Optional[str] = None
    message: Optional[str] = None
    error_message: Optional[str] = None
    deleted_at: Optional[datetime] = None 