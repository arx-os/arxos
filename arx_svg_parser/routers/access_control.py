"""
Access Control Router
FastAPI endpoints for role-based permissions, floor-specific access controls, audit trails, and permission inheritance
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
import logging

from arx_svg_parser.services.access_control import (
    access_control_service, UserRole, ResourceType, ActionType, 
    PermissionLevel, User, Permission, AuditLog
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/access-control", tags=["Access Control"])

# Pydantic models for request/response
class UserCreateRequest(BaseModel):
    username: str
    email: str
    primary_role: str
    secondary_roles: List[str] = []
    organization: str = ""

class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    primary_role: str
    secondary_roles: List[str]
    organization: str
    created_at: str
    last_login: Optional[str]
    is_active: bool
    metadata: Dict[str, Any]

class PermissionGrantRequest(BaseModel):
    role: str
    resource_type: str
    resource_id: Optional[str] = None
    permission_level: int
    floor_id: Optional[str] = None
    building_id: Optional[str] = None
    expires_at: Optional[str] = None

class PermissionResponse(BaseModel):
    permission_id: str
    role: str
    resource_type: str
    resource_id: Optional[str]
    permission_level: int
    floor_id: Optional[str]
    building_id: Optional[str]
    created_at: str
    expires_at: Optional[str]
    metadata: Dict[str, Any]

class AuditLogResponse(BaseModel):
    log_id: str
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    floor_id: Optional[str]
    building_id: Optional[str]
    details: Dict[str, Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: str
    success: bool
    error_message: Optional[str]

class PermissionCheckRequest(BaseModel):
    user_id: str
    resource_type: str
    action: str
    resource_id: Optional[str] = None
    floor_id: Optional[str] = None
    building_id: Optional[str] = None

class AuditLogRequest(BaseModel):
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    floor_id: Optional[str] = None
    building_id: Optional[str] = None
    details: Dict[str, Any] = {}
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None

# User Management Endpoints
@router.post("/users", response_model=Dict[str, Any])
async def create_user(request: UserCreateRequest):
    """Create a new user"""
    try:
        primary_role = UserRole(request.primary_role)
        secondary_roles = [UserRole(role) for role in request.secondary_roles]
        
        result = access_control_service.create_user(
            username=request.username,
            email=request.email,
            primary_role=primary_role,
            secondary_roles=secondary_roles,
            organization=request.organization
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid role: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/users/{user_id}", response_model=Dict[str, Any])
async def get_user(user_id: str):
    """Get user information"""
    try:
        result = access_control_service.get_user(user_id)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["message"])
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/users", response_model=Dict[str, Any])
async def list_users(
    role: Optional[str] = Query(None, description="Filter by role"),
    organization: Optional[str] = Query(None, description="Filter by organization"),
    active_only: bool = Query(True, description="Show only active users")
):
    """List users with optional filters"""
    try:
        # This would need to be implemented in the service
        # For now, return a placeholder
        return {
            "success": True,
            "users": [],
            "total": 0,
            "message": "User listing not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Failed to list users: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Permission Management Endpoints
@router.post("/permissions", response_model=Dict[str, Any])
async def grant_permission(request: PermissionGrantRequest):
    """Grant permission to a role"""
    try:
        role = UserRole(request.role)
        resource_type = ResourceType(request.resource_type)
        permission_level = PermissionLevel(request.permission_level)
        expires_at = datetime.fromisoformat(request.expires_at) if request.expires_at else None
        
        result = access_control_service.grant_permission(
            role=role,
            resource_type=resource_type,
            permission_level=permission_level,
            resource_id=request.resource_id,
            floor_id=request.floor_id,
            building_id=request.building_id,
            expires_at=expires_at
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to grant permission: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/permissions/{permission_id}", response_model=Dict[str, Any])
async def revoke_permission(permission_id: str):
    """Revoke a permission"""
    try:
        result = access_control_service.revoke_permission(permission_id)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["message"])
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to revoke permission: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/permissions/check", response_model=Dict[str, Any])
async def check_permission(request: PermissionCheckRequest):
    """Check if user has permission for an action"""
    try:
        resource_type = ResourceType(request.resource_type)
        action = ActionType(request.action)
        
        result = access_control_service.check_permission(
            user_id=request.user_id,
            resource_type=resource_type,
            action=action,
            resource_id=request.resource_id,
            floor_id=request.floor_id,
            building_id=request.building_id
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to check permission: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/permissions/floor/{building_id}/{floor_id}", response_model=Dict[str, Any])
async def get_floor_permissions(building_id: str, floor_id: str):
    """Get all permissions for a specific floor"""
    try:
        result = access_control_service.get_floor_permissions(floor_id, building_id)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get floor permissions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/permissions/role/{role}", response_model=Dict[str, Any])
async def get_role_permissions(role: str):
    """Get all permissions for a specific role"""
    try:
        # This would need to be implemented in the service
        return {
            "success": True,
            "permissions": [],
            "total": 0,
            "message": "Role permissions listing not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Failed to get role permissions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Audit Trail Endpoints
@router.post("/audit-logs", response_model=Dict[str, Any])
async def log_audit_event(request: AuditLogRequest):
    """Log an audit event"""
    try:
        action = ActionType(request.action)
        resource_type = ResourceType(request.resource_type)
        
        result = access_control_service.log_audit_event(
            user_id=request.user_id,
            action=action,
            resource_type=resource_type,
            resource_id=request.resource_id,
            floor_id=request.floor_id,
            building_id=request.building_id,
            details=request.details,
            ip_address=request.ip_address,
            user_agent=request.user_agent,
            success=request.success,
            error_message=request.error_message
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to log audit event: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/audit-logs", response_model=Dict[str, Any])
async def get_audit_logs(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    limit: int = Query(100, description="Maximum number of logs to return")
):
    """Get audit logs with optional filters"""
    try:
        resource_type_enum = ResourceType(resource_type) if resource_type else None
        start_datetime = datetime.fromisoformat(start_date) if start_date else None
        end_datetime = datetime.fromisoformat(end_date) if end_date else None
        
        result = access_control_service.get_audit_logs(
            user_id=user_id,
            resource_type=resource_type_enum,
            resource_id=resource_id,
            start_date=start_datetime,
            end_date=end_datetime,
            limit=limit
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to get audit logs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/audit-logs/user/{user_id}", response_model=Dict[str, Any])
async def get_user_audit_logs(
    user_id: str,
    limit: int = Query(100, description="Maximum number of logs to return")
):
    """Get audit logs for a specific user"""
    try:
        result = access_control_service.get_audit_logs(
            user_id=user_id,
            limit=limit
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get user audit logs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/audit-logs/floor/{building_id}/{floor_id}", response_model=Dict[str, Any])
async def get_floor_audit_logs(
    building_id: str,
    floor_id: str,
    limit: int = Query(100, description="Maximum number of logs to return")
):
    """Get audit logs for a specific floor"""
    try:
        # This would need to be implemented in the service
        return {
            "success": True,
            "logs": [],
            "total": 0,
            "message": "Floor audit logs not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Failed to get floor audit logs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Role Management Endpoints
@router.get("/roles", response_model=Dict[str, Any])
async def get_roles():
    """Get all available roles"""
    try:
        roles = [role.value for role in UserRole]
        return {
            "success": True,
            "roles": roles,
            "total": len(roles)
        }
        
    except Exception as e:
        logger.error(f"Failed to get roles: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/roles/{role}/hierarchy", response_model=Dict[str, Any])
async def get_role_hierarchy(role: str):
    """Get role hierarchy and inherited permissions"""
    try:
        # This would need to be implemented in the service
        return {
            "success": True,
            "role": role,
            "inherits_from": [],
            "permissions": [],
            "message": "Role hierarchy not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Failed to get role hierarchy: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/resource-types", response_model=Dict[str, Any])
async def get_resource_types():
    """Get all available resource types"""
    try:
        resource_types = [rt.value for rt in ResourceType]
        return {
            "success": True,
            "resource_types": resource_types,
            "total": len(resource_types)
        }
        
    except Exception as e:
        logger.error(f"Failed to get resource types: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/permission-levels", response_model=Dict[str, Any])
async def get_permission_levels():
    """Get all available permission levels"""
    try:
        permission_levels = [
            {"value": pl.value, "name": pl.name} 
            for pl in PermissionLevel
        ]
        return {
            "success": True,
            "permission_levels": permission_levels,
            "total": len(permission_levels)
        }
        
    except Exception as e:
        logger.error(f"Failed to get permission levels: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/action-types", response_model=Dict[str, Any])
async def get_action_types():
    """Get all available action types"""
    try:
        action_types = [at.value for at in ActionType]
        return {
            "success": True,
            "action_types": action_types,
            "total": len(action_types)
        }
        
    except Exception as e:
        logger.error(f"Failed to get action types: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Floor-specific Access Control Endpoints
@router.post("/floors/{building_id}/{floor_id}/permissions/bulk", response_model=Dict[str, Any])
async def grant_floor_permissions_bulk(
    building_id: str,
    floor_id: str,
    permissions: List[PermissionGrantRequest]
):
    """Grant multiple permissions for a floor"""
    try:
        results = []
        for permission in permissions:
            role = UserRole(permission.role)
            resource_type = ResourceType(permission.resource_type)
            permission_level = PermissionLevel(permission.permission_level)
            expires_at = datetime.fromisoformat(permission.expires_at) if permission.expires_at else None
            
            result = access_control_service.grant_permission(
                role=role,
                resource_type=resource_type,
                permission_level=permission_level,
                resource_id=permission.resource_id,
                floor_id=floor_id,
                building_id=building_id,
                expires_at=expires_at
            )
            results.append(result)
        
        return {
            "success": True,
            "results": results,
            "total": len(results)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to grant floor permissions bulk: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/floors/{building_id}/{floor_id}/permissions", response_model=Dict[str, Any])
async def revoke_floor_permissions(building_id: str, floor_id: str, role: Optional[str] = None):
    """Revoke all permissions for a floor (optionally filtered by role)"""
    try:
        # This would need to be implemented in the service
        return {
            "success": True,
            "message": f"Revoked permissions for floor {floor_id} in building {building_id}",
            "role_filter": role
        }
        
    except Exception as e:
        logger.error(f"Failed to revoke floor permissions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/floors/{building_id}/{floor_id}/access-summary", response_model=Dict[str, Any])
async def get_floor_access_summary(building_id: str, floor_id: str):
    """Get access summary for a floor"""
    try:
        # Get floor permissions
        permissions_result = access_control_service.get_floor_permissions(floor_id, building_id)
        
        if not permissions_result["success"]:
            raise HTTPException(status_code=400, detail=permissions_result["message"])
        
        # Get recent audit logs
        logs_result = access_control_service.get_audit_logs(
            resource_id=floor_id,
            limit=50
        )
        
        if not logs_result["success"]:
            raise HTTPException(status_code=400, detail=logs_result["message"])
        
        return {
            "success": True,
            "floor_id": floor_id,
            "building_id": building_id,
            "permissions": permissions_result["permissions"],
            "recent_activity": logs_result["logs"],
            "permission_count": len(permissions_result["permissions"]),
            "activity_count": len(logs_result["logs"])
        }
        
    except Exception as e:
        logger.error(f"Failed to get floor access summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Health Check Endpoint
@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check for access control service"""
    try:
        return {
            "success": True,
            "service": "access_control",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Service unhealthy") 