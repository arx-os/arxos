"""
Device DTOs - Data Transfer Objects for Device Operations

This module contains DTOs for device-related operations including
create, read, update, delete, and list operations.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class CreateDeviceRequest:
    """Request DTO for creating a device."""
    
    room_id: str
    device_type: str
    name: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    description: Optional[str] = None
    created_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CreateDeviceResponse:
    """Response DTO for device creation."""
    
    success: bool
    device_id: Optional[str] = None
    message: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class UpdateDeviceRequest:
    """Request DTO for updating a device."""
    
    device_id: str
    name: Optional[str] = None
    device_type: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    updated_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class UpdateDeviceResponse:
    """Response DTO for device updates."""
    
    success: bool
    device_id: Optional[str] = None
    message: Optional[str] = None
    error_message: Optional[str] = None
    updated_at: Optional[datetime] = None


@dataclass
class GetDeviceResponse:
    """Response DTO for getting a device."""
    
    success: bool
    device: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


@dataclass
class ListDevicesResponse:
    """Response DTO for listing devices."""
    
    success: bool
    devices: List[Dict[str, Any]] = None
    total_count: int = 0
    page: int = 1
    page_size: int = 10
    error_message: Optional[str] = None


@dataclass
class DeleteDeviceResponse:
    """Response DTO for deleting a device."""
    
    success: bool
    device_id: Optional[str] = None
    message: Optional[str] = None
    error_message: Optional[str] = None
    deleted_at: Optional[datetime] = None 