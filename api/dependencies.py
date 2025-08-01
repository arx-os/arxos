"""
API Dependencies

This module contains FastAPI dependencies for authentication, authorization,
and service injection.
"""

from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta

from application.container import container
from application.logging_config import get_logger
from application.services.device_service import DeviceApplicationService
from application.services.room_service import RoomApplicationService
from application.services.user_service import UserApplicationService
from application.services.project_service import ProjectApplicationService
from application.services.building_service import BuildingApplicationService

logger = get_logger("api.dependencies")

# Security scheme
security = HTTPBearer(auto_error=False)


class User:
    """User model for authentication."""
    
    def __init__(self, user_id: str, api_key: str, permissions: list = None):
        self.user_id = user_id
        self.api_key = api_key
        self.permissions = permissions or []
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission."""
        return permission in self.permissions


async def get_api_key(request: Request) -> Optional[str]:
    """Extract API key from request headers."""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return None
    return api_key


async def get_bearer_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[str]:
    """Extract bearer token from authorization header."""
    if not credentials:
        return None
    return credentials.credentials


async def get_current_user(
    request: Request,
    api_key: Optional[str] = Depends(get_api_key),
    bearer_token: Optional[str] = Depends(get_bearer_token)
) -> User:
    """Get current authenticated user."""
    user_id = None
    permissions = []
    
    # Check API key authentication
    if api_key:
        # Validate API key (in production, this would check against database)
        if api_key == "test-api-key":
            user_id = "test-user"
            permissions = ["read", "write"]
        elif api_key == "admin-api-key":
            user_id = "admin-user"
            permissions = ["read", "write", "admin"]
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
    
    # Check bearer token authentication
    elif bearer_token:
        try:
            # Decode JWT token (in production, this would use proper secret)
            payload = jwt.decode(bearer_token, "secret", algorithms=["HS256"])
            user_id = payload.get("sub")
            permissions = payload.get("permissions", [])
            
            # Check token expiration
            exp = payload.get("exp")
            if exp and datetime.utcnow().timestamp() > exp:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired"
                )
                
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    # No authentication provided
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Create user object
    user = User(user_id=user_id, api_key=api_key, permissions=permissions)
    
    # Store user in request state
    request.state.user = user
    
    logger.info(f"User authenticated: {user_id}", user_id=user_id, permissions=permissions)
    
    return user


async def get_current_user_optional(
    request: Request,
    api_key: Optional[str] = Depends(get_api_key),
    bearer_token: Optional[str] = Depends(get_bearer_token)
) -> Optional[User]:
    """Get current user (optional - allows anonymous access)."""
    try:
        return await get_current_user(request, api_key, bearer_token)
    except HTTPException:
        return None


async def require_permission(permission: str):
    """Dependency to require specific permission."""
    async def _require_permission(request: Request, user: User = Depends(get_current_user)) -> User:
        if not user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return user
    return _require_permission


async def require_admin():
    """Dependency to require admin permission."""
    return await require_permission("admin")


async def require_write_permission():
    """Dependency to require write permission."""
    return await require_permission("write")


async def require_read_permission():
    """Dependency to require read permission."""
    return await require_permission("read")


# Service dependencies
async def get_device_service() -> DeviceApplicationService:
    """Get device application service."""
    return container.get_device_service()


async def get_room_service() -> RoomApplicationService:
    """Get room application service."""
    return container.get_room_service()


async def get_user_service() -> UserApplicationService:
    """Get user application service."""
    return container.get_user_service()


async def get_project_service() -> ProjectApplicationService:
    """Get project application service."""
    return container.get_project_service()


async def get_building_service() -> BuildingApplicationService:
    """Get building application service."""
    return container.get_building_service()


# Request validation dependencies
async def validate_pagination_params(
    page: int = 1,
    page_size: int = 10,
    max_page_size: int = 100
) -> Dict[str, int]:
    """Validate and normalize pagination parameters."""
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page number must be greater than 0"
        )
    
    if page_size < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page size must be greater than 0"
        )
    
    if page_size > max_page_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Page size cannot exceed {max_page_size}"
        )
    
    return {
        "page": page,
        "page_size": page_size,
        "offset": (page - 1) * page_size
    }


async def validate_sorting_params(
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    allowed_fields: list = None
) -> Dict[str, Any]:
    """Validate and normalize sorting parameters."""
    if sort_by and allowed_fields and sort_by not in allowed_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sort field. Allowed fields: {', '.join(allowed_fields)}"
        )
    
    if sort_order and sort_order not in ["asc", "desc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sort order must be 'asc' or 'desc'"
        )
    
    return {
        "sort_by": sort_by,
        "sort_order": sort_order or "asc"
    }


async def validate_filter_params(
    filters: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Validate and normalize filter parameters."""
    if not filters:
        return {}
    
    # Validate filter structure
    for key, value in filters.items():
        if not isinstance(key, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filter keys must be strings"
            )
        
        if not isinstance(value, (str, int, float, bool, list)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filter values must be primitive types"
            )
    
    return filters


# Response formatting dependencies
def format_success_response(
    data: Any = None,
    message: str = "Success",
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Format success response."""
    response = {
        "success": True,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    if request_id:
        response["request_id"] = request_id
    
    return response


def format_error_response(
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Format error response."""
    response = {
        "error": True,
        "error_code": error_code,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if details:
        response["details"] = details
    
    if request_id:
        response["request_id"] = request_id
    
    return response


def format_paginated_response(
    items: list,
    total_count: int,
    page: int,
    page_size: int,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Format paginated response."""
    total_pages = (total_count + page_size - 1) // page_size
    
    response = {
        "success": True,
        "message": "Success",
        "data": {
            "items": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1
            }
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if request_id:
        response["request_id"] = request_id
    
    return response


# Rate limiting dependencies
async def check_rate_limit(request: Request, user: User = Depends(get_current_user)):
    """Check rate limit for user."""
    # This would integrate with the rate limiting middleware
    # For now, we'll just log the request
    logger.info(f"Rate limit check for user: {user.user_id}", user_id=user.user_id)
    return True


# Metrics dependencies
async def record_api_metric(
    endpoint: str,
    method: str,
    status_code: int,
    duration: float,
    user_id: Optional[str] = None
):
    """Record API metric."""
    logger.info(
        f"API metric recorded",
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        duration_ms=duration * 1000,
        user_id=user_id
    )


# Caching dependencies
async def get_cache_key(request: Request, user: User = Depends(get_current_user)) -> str:
    """Generate cache key for request."""
    # Create cache key based on request path, query parameters, and user
    path = request.url.path
    query_params = str(sorted(request.query_params.items()))
    user_id = user.user_id
    
    cache_key = f"{user_id}:{path}:{query_params}"
    return cache_key


async def check_cache(cache_key: str = Depends(get_cache_key)) -> Optional[Dict[str, Any]]:
    """Check cache for response."""
    cache_service = container.get_cache_service()
    if cache_service:
        return await cache_service.get(cache_key)
    return None


async def set_cache(
    cache_key: str = Depends(get_cache_key),
    ttl: int = 300
) -> None:
    """Set cache for response."""
    cache_service = container.get_cache_service()
    if cache_service:
        await cache_service.set(cache_key, ttl) 