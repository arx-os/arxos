"""
Project DTOs - Data Transfer Objects for Project Operations

This module contains DTOs for project-related operations including
create, read, update, delete, and list operations.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class CreateProjectRequest:
    """Request DTO for creating a project."""
    
    name: str
    building_id: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CreateProjectResponse:
    """Response DTO for project creation."""
    
    success: bool
    project_id: Optional[str] = None
    message: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class UpdateProjectRequest:
    """Request DTO for updating a project."""
    
    project_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    updated_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class UpdateProjectResponse:
    """Response DTO for project updates."""
    
    success: bool
    project_id: Optional[str] = None
    message: Optional[str] = None
    error_message: Optional[str] = None
    updated_at: Optional[datetime] = None


@dataclass
class GetProjectResponse:
    """Response DTO for getting a project."""
    
    success: bool
    project: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


@dataclass
class ListProjectsResponse:
    """Response DTO for listing projects."""
    
    success: bool
    projects: List[Dict[str, Any]] = None
    total_count: int = 0
    page: int = 1
    page_size: int = 10
    error_message: Optional[str] = None


@dataclass
class DeleteProjectResponse:
    """Response DTO for deleting a project."""
    
    success: bool
    project_id: Optional[str] = None
    message: Optional[str] = None
    error_message: Optional[str] = None
    deleted_at: Optional[datetime] = None 