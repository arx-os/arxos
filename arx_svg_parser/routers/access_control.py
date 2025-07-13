"""
Access Control Router
FastAPI endpoints for role-based permissions, floor-specific access controls, audit trails, and permission inheritance
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
import structlog

from services.access_control import (
    access_control_service, UserRole, ResourceType, ActionType, 
    PermissionLevel, User, Permission, AuditLog
)

logger = structlog.get_logger(__name__)

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
    logger.info("user_creation_attempt",
               username=request.username,
               email=request.email,
               primary_role=request.primary_role,
               organization=request.organization)
    
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
            logger.warning("user_creation_failed",
                          username=request.username,
                          error=result["message"])
            raise HTTPException(status_code=400, detail=result["message"])
        
        logger.info("user_creation_successful",
                   username=request.username,
                   user_id=result.get("user_id"))
        
        return result
        
    except ValueError as e:
        logger.error("user_creation_invalid_role",
                    username=request.username,
                    error=str(e))
        raise HTTPException(status_code=400, detail=f"Invalid role: {str(e)}")
    except Exception as e:
        logger.error("user_creation_failed",
                    username=request.username,
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/users/{user_id}", response_model=Dict[str, Any])
async def get_user(user_id: str):
    """Get user information"""
    logger.debug("user_retrieval_attempt", user_id=user_id)
    
    try:
        result = access_control_service.get_user(user_id)
        
        if not result["success"]:
            logger.warning("user_retrieval_failed",
                          user_id=user_id,
                          error=result["message"])
            raise HTTPException(status_code=404, detail=result["message"])
        
        logger.debug("user_retrieval_successful", user_id=user_id)
        return result
        
    except Exception as e:
        logger.error("user_retrieval_failed",
                    user_id=user_id,
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/users", response_model=Dict[str, Any])
async def list_users(
    role: Optional[str] = Query(None, description="Filter by role"),
    organization: Optional[str] = Query(None, description="Filter by organization"),
    active_only: bool = Query(True, description="Show only active users")
):
    """List users with optional filters"""
    logger.info("user_listing_attempt",
               role_filter=role,
               organization_filter=organization,
               active_only=active_only)
    
    try:
        # This would need to be implemented in the service
        # For now, return a placeholder
        result = {
            "success": True,
            "users": [],
            "total": 0,
            "message": "User listing not yet implemented"
        }
        
        logger.info("user_listing_completed",
                   total_users=result["total"])
        
        return result
        
    except Exception as e:
        logger.error("user_listing_failed",
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Internal server error")

# Permission Management Endpoints
@router.post("/permissions", response_model=Dict[str, Any])
async def grant_permission(request: PermissionGrantRequest):
    """Grant permission to a role"""
    logger.info("permission_grant_attempt",
               role=request.role,
               resource_type=request.resource_type,
               resource_id=request.resource_id,
               floor_id=request.floor_id,
               building_id=request.building_id,
               permission_level=request.permission_level)
    
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
            logger.warning("permission_grant_failed",
                          role=request.role,
                          resource_type=request.resource_type,
                          error=result["message"])
            raise HTTPException(status_code=400, detail=result["message"])
        
        logger.info("permission_grant_successful",
                   role=request.role,
                   resource_type=request.resource_type,
                   permission_id=result.get("permission_id"))
        
        return result
        
    except ValueError as e:
        logger.error("permission_grant_invalid_parameter",
                    role=request.role,
                    resource_type=request.resource_type,
                    error=str(e))
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(e)}")
    except Exception as e:
        logger.error("permission_grant_failed",
                    role=request.role,
                    resource_type=request.resource_type,
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/permissions/{permission_id}", response_model=Dict[str, Any])
async def revoke_permission(permission_id: str):
    """Revoke a permission"""
    logger.info("permission_revoke_attempt", permission_id=permission_id)
    
    try:
        result = access_control_service.revoke_permission(permission_id)
        
        if not result["success"]:
            logger.warning("permission_revoke_failed",
                          permission_id=permission_id,
                          error=result["message"])
            raise HTTPException(status_code=404, detail=result["message"])
        
        logger.info("permission_revoke_successful", permission_id=permission_id)
        return result
        
    except Exception as e:
        logger.error("permission_revoke_failed",
                    permission_id=permission_id,
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/permissions/check", response_model=Dict[str, Any])
async def check_permission(request: PermissionCheckRequest):
    """Check if a user has permission for a specific action"""
    logger.debug("permission_check_attempt",
                user_id=request.user_id,
                resource_type=request.resource_type,
                action=request.action,
                resource_id=request.resource_id,
                floor_id=request.floor_id,
                building_id=request.building_id)
    
    try:
        result = access_control_service.check_permission(
            user_id=request.user_id,
            resource_type=request.resource_type,
            action=request.action,
            resource_id=request.resource_id,
            floor_id=request.floor_id,
            building_id=request.building_id
        )
        
        logger.debug("permission_check_completed",
                    user_id=request.user_id,
                    resource_type=request.resource_type,
                    action=request.action,
                    has_permission=result.get("has_permission", False))
        
        return result
        
    except Exception as e:
        logger.error("permission_check_failed",
                    user_id=request.user_id,
                    resource_type=request.resource_type,
                    action=request.action,
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/permissions/floor/{building_id}/{floor_id}", response_model=Dict[str, Any])
async def get_floor_permissions(building_id: str, floor_id: str):
    """Get all permissions for a specific floor"""
    logger.info("floor_permissions_retrieval_attempt",
               building_id=building_id,
               floor_id=floor_id)
    
    try:
        result = access_control_service.get_floor_permissions(building_id, floor_id)
        
        logger.info("floor_permissions_retrieval_completed",
                   building_id=building_id,
                   floor_id=floor_id,
                   permissions_count=len(result.get("permissions", [])))
        
        return result
        
    except Exception as e:
        logger.error("floor_permissions_retrieval_failed",
                    building_id=building_id,
                    floor_id=floor_id,
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/permissions/role/{role}", response_model=Dict[str, Any])
async def get_role_permissions(role: str):
    """Get all permissions for a specific role"""
    logger.info("role_permissions_retrieval_attempt", role=role)
    
    try:
        result = access_control_service.get_role_permissions(role)
        
        logger.info("role_permissions_retrieval_completed",
                   role=role,
                   permissions_count=len(result.get("permissions", [])))
        
        return result
        
    except Exception as e:
        logger.error("role_permissions_retrieval_failed",
                    role=role,
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Internal server error")

# Audit Logging Endpoints
@router.post("/audit-logs", response_model=Dict[str, Any])
async def log_audit_event(request: AuditLogRequest):
    """Log an audit event"""
    logger.info("audit_event_logging",
               user_id=request.user_id,
               action=request.action,
               resource_type=request.resource_type,
               resource_id=request.resource_id,
               floor_id=request.floor_id,
               building_id=request.building_id,
               success=request.success)
    
    try:
        result = access_control_service.log_audit_event(
            user_id=request.user_id,
            action=request.action,
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            floor_id=request.floor_id,
            building_id=request.building_id,
            details=request.details,
            ip_address=request.ip_address,
            user_agent=request.user_agent,
            success=request.success,
            error_message=request.error_message
        )
        
        logger.info("audit_event_logged",
                   user_id=request.user_id,
                   action=request.action,
                   log_id=result.get("log_id"))
        
        return result
        
    except Exception as e:
        logger.error("audit_event_logging_failed",
                    user_id=request.user_id,
                    action=request.action,
                    error=str(e),
                    error_type=type(e).__name__)
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
    logger.info("audit_logs_retrieval_attempt",
               user_id_filter=user_id,
               resource_type_filter=resource_type,
               resource_id_filter=resource_id,
               start_date=start_date,
               end_date=end_date,
               limit=limit)
    
    try:
        result = access_control_service.get_audit_logs(
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        logger.info("audit_logs_retrieval_completed",
                   logs_count=len(result.get("logs", [])),
                   total_count=result.get("total_count", 0))
        
        return result
        
    except Exception as e:
        logger.error("audit_logs_retrieval_failed",
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/audit-logs/user/{user_id}", response_model=Dict[str, Any])
async def get_user_audit_logs(
    user_id: str,
    limit: int = Query(100, description="Maximum number of logs to return")
):
    """Get audit logs for a specific user"""
    logger.info("user_audit_logs_retrieval_attempt",
               user_id=user_id,
               limit=limit)
    
    try:
        result = access_control_service.get_user_audit_logs(user_id, limit)
        
        logger.info("user_audit_logs_retrieval_completed",
                   user_id=user_id,
                   logs_count=len(result.get("logs", [])))
        
        return result
        
    except Exception as e:
        logger.error("user_audit_logs_retrieval_failed",
                    user_id=user_id,
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/audit-logs/floor/{building_id}/{floor_id}", response_model=Dict[str, Any])
async def get_floor_audit_logs(
    building_id: str,
    floor_id: str,
    limit: int = Query(100, description="Maximum number of logs to return")
):
    """Get audit logs for a specific floor"""
    logger.info("floor_audit_logs_retrieval_attempt",
               building_id=building_id,
               floor_id=floor_id,
               limit=limit)
    
    try:
        result = access_control_service.get_floor_audit_logs(building_id, floor_id, limit)
        
        logger.info("floor_audit_logs_retrieval_completed",
                   building_id=building_id,
                   floor_id=floor_id,
                   logs_count=len(result.get("logs", [])))
        
        return result
        
    except Exception as e:
        logger.error("floor_audit_logs_retrieval_failed",
                    building_id=building_id,
                    floor_id=floor_id,
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Internal server error")

# System Information Endpoints
@router.get("/roles", response_model=Dict[str, Any])
async def get_roles():
    """Get all available roles"""
    logger.debug("roles_retrieval_attempt")
    
    try:
        result = access_control_service.get_roles()
        
        logger.debug("roles_retrieval_completed",
                    roles_count=len(result.get("roles", [])))
        
        return result
        
    except Exception as e:
        logger.error("roles_retrieval_failed",
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/roles/{role}/hierarchy", response_model=Dict[str, Any])
async def get_role_hierarchy(role: str):
    """Get the hierarchy for a specific role"""
    logger.debug("role_hierarchy_retrieval_attempt", role=role)
    
    try:
        result = access_control_service.get_role_hierarchy(role)
        
        logger.debug("role_hierarchy_retrieval_completed",
                    role=role,
                    hierarchy_levels=len(result.get("hierarchy", [])))
        
        return result
        
    except Exception as e:
        logger.error("role_hierarchy_retrieval_failed",
                    role=role,
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/resource-types", response_model=Dict[str, Any])
async def get_resource_types():
    """Get all available resource types"""
    logger.debug("resource_types_retrieval_attempt")
    
    try:
        result = access_control_service.get_resource_types()
        
        logger.debug("resource_types_retrieval_completed",
                    resource_types_count=len(result.get("resource_types", [])))
        
        return result
        
    except Exception as e:
        logger.error("resource_types_retrieval_failed",
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/permission-levels", response_model=Dict[str, Any])
async def get_permission_levels():
    """Get all available permission levels"""
    logger.debug("permission_levels_retrieval_attempt")
    
    try:
        result = access_control_service.get_permission_levels()
        
        logger.debug("permission_levels_retrieval_completed",
                    permission_levels_count=len(result.get("permission_levels", [])))
        
        return result
        
    except Exception as e:
        logger.error("permission_levels_retrieval_failed",
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/action-types", response_model=Dict[str, Any])
async def get_action_types():
    """Get all available action types"""
    logger.debug("action_types_retrieval_attempt")
    
    try:
        result = access_control_service.get_action_types()
        
        logger.debug("action_types_retrieval_completed",
                    action_types_count=len(result.get("action_types", [])))
        
        return result
        
    except Exception as e:
        logger.error("action_types_retrieval_failed",
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Internal server error")

# Floor-specific Permission Management
@router.post("/floors/{building_id}/{floor_id}/permissions/bulk", response_model=Dict[str, Any])
async def grant_floor_permissions_bulk(
    building_id: str,
    floor_id: str,
    permissions: List[PermissionGrantRequest]
):
    """Grant multiple permissions for a specific floor"""
    logger.info("floor_permissions_bulk_grant_attempt",
               building_id=building_id,
               floor_id=floor_id,
               permissions_count=len(permissions))
    
    try:
        result = access_control_service.grant_floor_permissions_bulk(
            building_id=building_id,
            floor_id=floor_id,
            permissions=permissions
        )
        
        logger.info("floor_permissions_bulk_grant_completed",
                   building_id=building_id,
                   floor_id=floor_id,
                   successful_count=result.get("successful_count", 0),
                   failed_count=result.get("failed_count", 0))
        
        return result
        
    except Exception as e:
        logger.error("floor_permissions_bulk_grant_failed",
                    building_id=building_id,
                    floor_id=floor_id,
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/floors/{building_id}/{floor_id}/permissions", response_model=Dict[str, Any])
async def revoke_floor_permissions(building_id: str, floor_id: str, role: Optional[str] = None):
    """Revoke all permissions for a specific floor"""
    logger.info("floor_permissions_revoke_attempt",
               building_id=building_id,
               floor_id=floor_id,
               role_filter=role)
    
    try:
        result = access_control_service.revoke_floor_permissions(building_id, floor_id, role)
        
        logger.info("floor_permissions_revoke_completed",
                   building_id=building_id,
                   floor_id=floor_id,
                   revoked_count=result.get("revoked_count", 0))
        
        return result
        
    except Exception as e:
        logger.error("floor_permissions_revoke_failed",
                    building_id=building_id,
                    floor_id=floor_id,
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/floors/{building_id}/{floor_id}/access-summary", response_model=Dict[str, Any])
async def get_floor_access_summary(building_id: str, floor_id: str):
    """Get an access summary for a specific floor"""
    logger.info("floor_access_summary_retrieval_attempt",
               building_id=building_id,
               floor_id=floor_id)
    
    try:
        result = access_control_service.get_floor_access_summary(building_id, floor_id)
        
        logger.info("floor_access_summary_retrieval_completed",
                   building_id=building_id,
                   floor_id=floor_id,
                   total_users=result.get("total_users", 0),
                   total_permissions=result.get("total_permissions", 0))
        
        return result
        
    except Exception as e:
        logger.error("floor_access_summary_retrieval_failed",
                    building_id=building_id,
                    floor_id=floor_id,
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Internal server error")

# Health Check
@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint"""
    logger.debug("access_control_health_check")
    
    try:
        result = access_control_service.health_check()
        
        logger.debug("access_control_health_check_completed",
                    status=result.get("status"))
        
        return result
        
    except Exception as e:
        logger.error("access_control_health_check_failed",
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Internal server error") 