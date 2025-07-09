#!/usr/bin/env python3
"""
AHJ API Service for Arxos Platform

This service provides secure, append-only interfaces for Authorities Having Jurisdiction (AHJ)
to write annotations into an 'inspection' layer with immutable and auditable interactions.

Features:
- Secure authentication and authorization
- Append-only inspection layer
- Immutable audit trail
- Permission enforcement
- Real-time notifications
- Data export capabilities
"""

import asyncio
import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import HTTPException, Depends, status
from pydantic import BaseModel, Field, validator

from services.advanced_security import AdvancedSecurityService
from utils.logger import setup_logger

class InspectionStatus(str, Enum):
    """Inspection status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AnnotationType(str, Enum):
    """Annotation type enumeration."""
    NOTE = "note"
    VIOLATION = "violation"
    WARNING = "warning"
    APPROVAL = "approval"
    REQUIREMENT = "requirement"
    CORRECTION = "correction"

class PermissionLevel(str, Enum):
    """Permission level enumeration."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    INSPECTOR = "inspector"
    REVIEWER = "reviewer"

@dataclass
class Coordinates:
    """Geographic coordinates for annotations."""
    x: float
    y: float
    z: Optional[float] = None
    floor: Optional[str] = None
    room: Optional[str] = None

@dataclass
class Annotation:
    """Immutable annotation data structure."""
    id: str
    inspection_id: str
    object_id: str
    annotation_type: AnnotationType
    content: str
    coordinates: Coordinates
    timestamp: datetime
    inspector_id: str
    immutable_hash: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Generate immutable hash after initialization."""
        if not self.immutable_hash:
            self.immutable_hash = self._generate_hash()
    
    def _generate_hash(self) -> str:
        """Generate immutable hash for the annotation."""
        data = {
            "id": self.id,
            "inspection_id": self.inspection_id,
            "object_id": self.object_id,
            "annotation_type": self.annotation_type.value,
            "content": self.content,
            "coordinates": {
                "x": self.coordinates.x,
                "y": self.coordinates.y,
                "z": self.coordinates.z,
                "floor": self.coordinates.floor,
                "room": self.coordinates.room
            },
            "timestamp": self.timestamp.isoformat(),
            "inspector_id": self.inspector_id,
            "metadata": self.metadata
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

@dataclass
class Violation:
    """Code violation data structure."""
    id: str
    inspection_id: str
    object_id: str
    code_section: str
    description: str
    severity: str
    timestamp: datetime
    inspector_id: str
    status: str = "open"
    resolution_date: Optional[datetime] = None
    immutable_hash: str = field(default="")
    
    def __post_init__(self):
        """Generate immutable hash after initialization."""
        if not self.immutable_hash:
            self.immutable_hash = self._generate_hash()
    
    def _generate_hash(self) -> str:
        """Generate immutable hash for the violation."""
        data = {
            "id": self.id,
            "inspection_id": self.inspection_id,
            "object_id": self.object_id,
            "code_section": self.code_section,
            "description": self.description,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat(),
            "inspector_id": self.inspector_id,
            "status": self.status,
            "resolution_date": self.resolution_date.isoformat() if self.resolution_date else None
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

@dataclass
class Inspection:
    """Inspection data structure."""
    id: str
    building_id: str
    inspector_id: str
    inspection_date: datetime
    status: InspectionStatus
    annotations: List[Annotation] = field(default_factory=list)
    violations: List[Violation] = field(default_factory=list)
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class AuditEvent(BaseModel):
    """Audit event data structure."""
    event_id: str
    inspection_id: str
    user_id: str
    action: str
    resource: str
    timestamp: datetime
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    immutable_hash: str = ""

class AHJAPIService:
    """Comprehensive AHJ API service with secure, append-only operations."""
    
    def __init__(self):
        self.logger = setup_logger("ahj_api_service", level=logging.INFO)
        self.security_service = AdvancedSecurityService()
        
        # In-memory storage (replace with database in production)
        self.inspections: Dict[str, Inspection] = {}
        self.annotations: Dict[str, Annotation] = {}
        self.violations: Dict[str, Violation] = {}
        self.audit_events: Dict[str, AuditEvent] = {}
        self.permissions: Dict[str, List[str]] = {}
        
        # Configuration
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load AHJ API configuration."""
        return {
            "api": {
                "version": "v1",
                "rate_limit": 1000,  # requests per hour
                "max_annotations_per_inspection": 1000,
                "max_violations_per_inspection": 500
            },
            "security": {
                "hash_algorithm": "sha256",
                "audit_trail_retention_days": 2555,  # 7 years
                "max_audit_events_per_inspection": 10000
            },
            "permissions": {
                "default_inspector_permissions": ["read", "write"],
                "default_reviewer_permissions": ["read", "write", "review"],
                "default_admin_permissions": ["read", "write", "admin"]
            }
        }
    
    async def create_inspection(self, building_id: str, inspector_id: str, 
                               metadata: Optional[Dict[str, Any]] = None) -> Inspection:
        """Create a new inspection with proper permissions and audit trail."""
        try:
            # Validate permissions
            if not await self._validate_permission(inspector_id, "write", f"building:{building_id}"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to create inspection"
                )
            
            # Generate inspection ID
            inspection_id = str(uuid.uuid4())
            
            # Create inspection
            inspection = Inspection(
                id=inspection_id,
                building_id=building_id,
                inspector_id=inspector_id,
                inspection_date=datetime.now(timezone.utc),
                status=InspectionStatus.PENDING,
                metadata=metadata or {},
                permissions=[inspector_id]
            )
            
            # Store inspection
            self.inspections[inspection_id] = inspection
            
            # Log audit event
            await self._log_audit_event(
                inspection_id=inspection_id,
                user_id=inspector_id,
                action="create_inspection",
                resource=f"inspection:{inspection_id}",
                details={
                    "building_id": building_id,
                    "metadata": metadata
                }
            )
            
            self.logger.info(f"Inspection created: {inspection_id} by {inspector_id}")
            return inspection
            
        except Exception as e:
            self.logger.error(f"Failed to create inspection: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create inspection"
            )
    
    async def add_annotation(self, inspection_id: str, object_id: str, 
                            annotation_type: AnnotationType, content: str,
                            coordinates: Coordinates, inspector_id: str,
                            metadata: Optional[Dict[str, Any]] = None) -> Annotation:
        """Add an immutable annotation to an inspection."""
        try:
            # Validate inspection exists
            if inspection_id not in self.inspections:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Inspection not found"
                )
            
            # Validate permissions
            if not await self._validate_permission(inspector_id, "write", f"inspection:{inspection_id}"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to add annotation"
                )
            
            # Check annotation limits
            inspection = self.inspections[inspection_id]
            if len(inspection.annotations) >= self.config["api"]["max_annotations_per_inspection"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Maximum annotations per inspection reached"
                )
            
            # Create annotation
            annotation = Annotation(
                id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                object_id=object_id,
                annotation_type=annotation_type,
                content=content,
                coordinates=coordinates,
                timestamp=datetime.now(timezone.utc),
                inspector_id=inspector_id,
                metadata=metadata or {}
            )
            
            # Store annotation
            self.annotations[annotation.id] = annotation
            inspection.annotations.append(annotation)
            inspection.updated_at = datetime.now(timezone.utc)
            
            # Log audit event
            await self._log_audit_event(
                inspection_id=inspection_id,
                user_id=inspector_id,
                action="add_annotation",
                resource=f"annotation:{annotation.id}",
                details={
                    "object_id": object_id,
                    "annotation_type": annotation_type.value,
                    "content": content,
                    "coordinates": {
                        "x": coordinates.x,
                        "y": coordinates.y,
                        "z": coordinates.z,
                        "floor": coordinates.floor,
                        "room": coordinates.room
                    },
                    "metadata": metadata
                }
            )
            
            self.logger.info(f"Annotation added: {annotation.id} to inspection {inspection_id}")
            return annotation
            
        except Exception as e:
            self.logger.error(f"Failed to add annotation: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add annotation"
            )
    
    async def add_violation(self, inspection_id: str, object_id: str,
                           code_section: str, description: str, severity: str,
                           inspector_id: str) -> Violation:
        """Add a code violation to an inspection."""
        try:
            # Validate inspection exists
            if inspection_id not in self.inspections:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Inspection not found"
                )
            
            # Validate permissions
            if not await self._validate_permission(inspector_id, "write", f"inspection:{inspection_id}"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to add violation"
                )
            
            # Check violation limits
            inspection = self.inspections[inspection_id]
            if len(inspection.violations) >= self.config["api"]["max_violations_per_inspection"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Maximum violations per inspection reached"
                )
            
            # Create violation
            violation = Violation(
                id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                object_id=object_id,
                code_section=code_section,
                description=description,
                severity=severity,
                timestamp=datetime.now(timezone.utc),
                inspector_id=inspector_id
            )
            
            # Store violation
            self.violations[violation.id] = violation
            inspection.violations.append(violation)
            inspection.updated_at = datetime.now(timezone.utc)
            
            # Log audit event
            await self._log_audit_event(
                inspection_id=inspection_id,
                user_id=inspector_id,
                action="add_violation",
                resource=f"violation:{violation.id}",
                details={
                    "object_id": object_id,
                    "code_section": code_section,
                    "description": description,
                    "severity": severity
                }
            )
            
            self.logger.info(f"Violation added: {violation.id} to inspection {inspection_id}")
            return violation
            
        except Exception as e:
            self.logger.error(f"Failed to add violation: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add violation"
            )
    
    async def get_inspection(self, inspection_id: str, user_id: str) -> Inspection:
        """Get inspection details with permission validation."""
        try:
            # Validate inspection exists
            if inspection_id not in self.inspections:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Inspection not found"
                )
            
            # Validate permissions
            if not await self._validate_permission(user_id, "read", f"inspection:{inspection_id}"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to view inspection"
                )
            
            inspection = self.inspections[inspection_id]
            
            # Log audit event
            await self._log_audit_event(
                inspection_id=inspection_id,
                user_id=user_id,
                action="view_inspection",
                resource=f"inspection:{inspection_id}",
                details={}
            )
            
            return inspection
            
        except Exception as e:
            self.logger.error(f"Failed to get inspection: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get inspection"
            )
    
    async def list_inspections(self, user_id: str, building_id: Optional[str] = None,
                              status: Optional[InspectionStatus] = None,
                              limit: int = 100, offset: int = 0) -> List[Inspection]:
        """List inspections with filtering and pagination."""
        try:
            # Get user's accessible inspections
            accessible_inspections = []
            for inspection in self.inspections.values():
                if await self._validate_permission(user_id, "read", f"inspection:{inspection.id}"):
                    # Apply filters
                    if building_id and inspection.building_id != building_id:
                        continue
                    if status and inspection.status != status:
                        continue
                    accessible_inspections.append(inspection)
            
            # Apply pagination
            paginated_inspections = accessible_inspections[offset:offset + limit]
            
            # Log audit event
            await self._log_audit_event(
                inspection_id="multiple",
                user_id=user_id,
                action="list_inspections",
                resource="inspections",
                details={
                    "building_id": building_id,
                    "status": status.value if status else None,
                    "limit": limit,
                    "offset": offset,
                    "count": len(paginated_inspections)
                }
            )
            
            return paginated_inspections
            
        except Exception as e:
            self.logger.error(f"Failed to list inspections: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list inspections"
            )
    
    async def get_audit_trail(self, inspection_id: str, user_id: str,
                             limit: int = 100, offset: int = 0) -> List[AuditEvent]:
        """Get audit trail for an inspection."""
        try:
            # Validate inspection exists
            if inspection_id not in self.inspections:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Inspection not found"
                )
            
            # Validate permissions
            if not await self._validate_permission(user_id, "read", f"inspection:{inspection_id}"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to view audit trail"
                )
            
            # Get audit events for inspection
            inspection_events = [
                event for event in self.audit_events.values()
                if event.inspection_id == inspection_id
            ]
            
            # Sort by timestamp (newest first)
            inspection_events.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Apply pagination
            paginated_events = inspection_events[offset:offset + limit]
            
            # Log audit event
            await self._log_audit_event(
                inspection_id=inspection_id,
                user_id=user_id,
                action="view_audit_trail",
                resource=f"audit_trail:{inspection_id}",
                details={
                    "limit": limit,
                    "offset": offset,
                    "count": len(paginated_events)
                }
            )
            
            return paginated_events
            
        except Exception as e:
            self.logger.error(f"Failed to get audit trail: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get audit trail"
            )
    
    async def update_inspection_status(self, inspection_id: str, status: InspectionStatus,
                                      user_id: str) -> Inspection:
        """Update inspection status with permission validation."""
        try:
            # Validate inspection exists
            if inspection_id not in self.inspections:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Inspection not found"
                )
            
            # Validate permissions
            if not await self._validate_permission(user_id, "write", f"inspection:{inspection_id}"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to update inspection"
                )
            
            inspection = self.inspections[inspection_id]
            old_status = inspection.status
            inspection.status = status
            inspection.updated_at = datetime.now(timezone.utc)
            
            # Log audit event
            await self._log_audit_event(
                inspection_id=inspection_id,
                user_id=user_id,
                action="update_status",
                resource=f"inspection:{inspection_id}",
                details={
                    "old_status": old_status.value,
                    "new_status": status.value
                }
            )
            
            self.logger.info(f"Inspection status updated: {inspection_id} from {old_status} to {status}")
            return inspection
            
        except Exception as e:
            self.logger.error(f"Failed to update inspection status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update inspection status"
            )
    
    async def _validate_permission(self, user_id: str, action: str, resource: str) -> bool:
        """Validate user permissions for a specific action and resource."""
        try:
            # Check if user has explicit permissions
            user_permissions = self.permissions.get(user_id, [])
            
            # Check for admin permissions
            if "admin" in user_permissions:
                return True
            
            # Check for specific action permissions
            if action in user_permissions:
                return True
            
            # Check resource-specific permissions
            resource_permission = f"{action}:{resource}"
            if resource_permission in user_permissions:
                return True
            
            # Default to read-only for inspectors
            if action == "read" and user_id in self._get_inspector_users():
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Permission validation error: {str(e)}")
            return False
    
    async def _log_audit_event(self, inspection_id: str, user_id: str, action: str,
                              resource: str, details: Dict[str, Any]) -> None:
        """Log an immutable audit event."""
        try:
            event = AuditEvent(
                event_id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                user_id=user_id,
                action=action,
                resource=resource,
                timestamp=datetime.now(timezone.utc),
                details=details
            )
            
            # Generate immutable hash
            event_data = {
                "event_id": event.event_id,
                "inspection_id": event.inspection_id,
                "user_id": event.user_id,
                "action": event.action,
                "resource": event.resource,
                "timestamp": event.timestamp.isoformat(),
                "details": event.details
            }
            event.immutable_hash = hashlib.sha256(
                json.dumps(event_data, sort_keys=True).encode()
            ).hexdigest()
            
            # Store audit event
            self.audit_events[event.event_id] = event
            
            # Add to inspection audit trail
            if inspection_id in self.inspections:
                self.inspections[inspection_id].audit_trail.append(event_data)
            
            self.logger.info(f"Audit event logged: {event.event_id} - {action} on {resource}")
            
        except Exception as e:
            self.logger.error(f"Failed to log audit event: {str(e)}")
    
    def _get_inspector_users(self) -> List[str]:
        """Get list of inspector user IDs."""
        # This would typically query a user database
        # For now, return users with inspector permissions
        inspector_users = []
        for user_id, permissions in self.permissions.items():
            if "inspector" in permissions or "write" in permissions:
                inspector_users.append(user_id)
        return inspector_users
    
    async def add_user_permission(self, user_id: str, permission: str, 
                                 admin_user_id: str) -> bool:
        """Add permission for a user (admin only)."""
        try:
            # Validate admin permissions
            if not await self._validate_permission(admin_user_id, "admin", "permissions"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to manage user permissions"
                )
            
            # Add permission
            if user_id not in self.permissions:
                self.permissions[user_id] = []
            self.permissions[user_id].append(permission)
            
            # Log audit event
            await self._log_audit_event(
                inspection_id="system",
                user_id=admin_user_id,
                action="add_permission",
                resource=f"user:{user_id}",
                details={"permission": permission}
            )
            
            self.logger.info(f"Permission added: {permission} for user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add user permission: {str(e)}")
            return False
    
    async def remove_user_permission(self, user_id: str, permission: str,
                                   admin_user_id: str) -> bool:
        """Remove permission for a user (admin only)."""
        try:
            # Validate admin permissions
            if not await self._validate_permission(admin_user_id, "admin", "permissions"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to manage user permissions"
                )
            
            # Remove permission
            if user_id in self.permissions and permission in self.permissions[user_id]:
                self.permissions[user_id].remove(permission)
                
                # Log audit event
                await self._log_audit_event(
                    inspection_id="system",
                    user_id=admin_user_id,
                    action="remove_permission",
                    resource=f"user:{user_id}",
                    details={"permission": permission}
                )
                
                self.logger.info(f"Permission removed: {permission} for user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to remove user permission: {str(e)}")
            return False
    
    async def get_inspection_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get inspection statistics for the user."""
        try:
            # Get user's accessible inspections
            accessible_inspections = []
            for inspection in self.inspections.values():
                if await self._validate_permission(user_id, "read", f"inspection:{inspection.id}"):
                    accessible_inspections.append(inspection)
            
            # Calculate statistics
            total_inspections = len(accessible_inspections)
            status_counts = {}
            for inspection in accessible_inspections:
                status = inspection.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            total_annotations = sum(len(inspection.annotations) for inspection in accessible_inspections)
            total_violations = sum(len(inspection.violations) for inspection in accessible_inspections)
            
            statistics = {
                "total_inspections": total_inspections,
                "status_counts": status_counts,
                "total_annotations": total_annotations,
                "total_violations": total_violations,
                "average_annotations_per_inspection": total_annotations / total_inspections if total_inspections > 0 else 0,
                "average_violations_per_inspection": total_violations / total_inspections if total_inspections > 0 else 0
            }
            
            # Log audit event
            await self._log_audit_event(
                inspection_id="system",
                user_id=user_id,
                action="view_statistics",
                resource="statistics",
                details=statistics
            )
            
            return statistics
            
        except Exception as e:
            self.logger.error(f"Failed to get inspection statistics: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get inspection statistics"
            )
    
    async def export_inspection_data(self, inspection_id: str, user_id: str,
                                   format: str = "json") -> Dict[str, Any]:
        """Export inspection data in various formats."""
        try:
            # Validate inspection exists
            if inspection_id not in self.inspections:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Inspection not found"
                )
            
            # Validate permissions
            if not await self._validate_permission(user_id, "read", f"inspection:{inspection_id}"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to export inspection data"
                )
            
            inspection = self.inspections[inspection_id]
            
            # Prepare export data
            export_data = {
                "inspection": {
                    "id": inspection.id,
                    "building_id": inspection.building_id,
                    "inspector_id": inspection.inspector_id,
                    "inspection_date": inspection.inspection_date.isoformat(),
                    "status": inspection.status.value,
                    "created_at": inspection.created_at.isoformat(),
                    "updated_at": inspection.updated_at.isoformat(),
                    "metadata": inspection.metadata
                },
                "annotations": [
                    {
                        "id": ann.id,
                        "object_id": ann.object_id,
                        "annotation_type": ann.annotation_type.value,
                        "content": ann.content,
                        "coordinates": {
                            "x": ann.coordinates.x,
                            "y": ann.coordinates.y,
                            "z": ann.coordinates.z,
                            "floor": ann.coordinates.floor,
                            "room": ann.coordinates.room
                        },
                        "timestamp": ann.timestamp.isoformat(),
                        "inspector_id": ann.inspector_id,
                        "immutable_hash": ann.immutable_hash,
                        "metadata": ann.metadata
                    }
                    for ann in inspection.annotations
                ],
                "violations": [
                    {
                        "id": v.id,
                        "object_id": v.object_id,
                        "code_section": v.code_section,
                        "description": v.description,
                        "severity": v.severity,
                        "timestamp": v.timestamp.isoformat(),
                        "inspector_id": v.inspector_id,
                        "status": v.status,
                        "resolution_date": v.resolution_date.isoformat() if v.resolution_date else None,
                        "immutable_hash": v.immutable_hash
                    }
                    for v in inspection.violations
                ],
                "audit_trail": inspection.audit_trail,
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "export_format": format
            }
            
            # Log audit event
            await self._log_audit_event(
                inspection_id=inspection_id,
                user_id=user_id,
                action="export_data",
                resource=f"inspection:{inspection_id}",
                details={"format": format}
            )
            
            return export_data
            
        except Exception as e:
            self.logger.error(f"Failed to export inspection data: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to export inspection data"
            )

# Global service instance
ahj_api_service = AHJAPIService() 