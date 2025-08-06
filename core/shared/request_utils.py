"""
Request Utilities for Arxos Platform

Provides standardized HTTP request processing functions used across
the platform. Centralizes common request operations to ensure
consistency and reduce code duplication.
"""

from typing import Any, Dict, List, Optional, Union
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import structlog
from datetime import datetime, timezone

logger = structlog.get_logger(__name__)


def get_client_ip(request: Request) -> str:
    """
    Get client IP address from request.

    Args:
        request: FastAPI request object

    Returns:
        Client IP address
    """
    # Check for forwarded headers first
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fallback to client host
    if request.client:
        return request.client.host

    return "unknown"


def get_user_agent(request: Request) -> str:
    """
    Get user agent from request.

    Args:
        request: FastAPI request object

    Returns:
        User agent string
    """
    return request.headers.get("User-Agent", "unknown")


def get_request_headers(
    request: Request, include_sensitive: bool = False
) -> Dict[str, str]:
    """
    Get request headers.

    Args:
        request: FastAPI request object
        include_sensitive: Whether to include sensitive headers

    Returns:
        Dictionary of headers
    """
    headers = dict(request.headers)

    if not include_sensitive:
        # Remove sensitive headers
        sensitive_headers = {"authorization", "cookie", "x-api-key", "x-auth-token"}
        headers = {
            k: v for k, v in headers.items() if k.lower() not in sensitive_headers
        }

    return headers


def get_request_params(request: Request) -> Dict[str, Any]:
    """
    Get all request parameters (query params + path params).

    Args:
        request: FastAPI request object

    Returns:
        Dictionary of parameters
    """
    params = {}

    # Query parameters
    for key, value in request.query_params.items():
        params[key] = value

    # Path parameters
    for key, value in request.path_params.items():
        params[key] = value

    return params


def validate_required_params(
    params: Dict[str, Any], required_params: List[str]
) -> List[str]:
    """
    Validate that required parameters are present.

    Args:
        params: Parameters to validate
        required_params: List of required parameter names

    Returns:
        List of missing parameter names
    """
    missing_params = []

    for param in required_params:
        if param not in params or params[param] is None:
            missing_params.append(param)

    return missing_params


def extract_pagination_params(request: Request) -> Dict[str, int]:
    """
    Extract pagination parameters from request.

    Args:
        request: FastAPI request object

    Returns:
        Dictionary with pagination parameters
    """
    page = int(request.query_params.get("page", 1))
    page_size = int(request.query_params.get("page_size", 50))

    # Validate limits
    page = max(1, page)
    page_size = max(1, min(page_size, 1000))  # Max 1000 items per page

    return {"page": page, "page_size": page_size, "offset": (page - 1) * page_size}


def extract_sorting_params(
    request: Request, allowed_fields: List[str]
) -> Dict[str, str]:
    """
    Extract sorting parameters from request.

    Args:
        request: FastAPI request object
        allowed_fields: List of allowed sort fields

    Returns:
        Dictionary with sorting parameters
    """
    sort_by = request.query_params.get("sort_by", "")
    sort_order = request.query_params.get("sort_order", "asc").lower()

    # Validate sort field
    if sort_by and sort_by not in allowed_fields:
        sort_by = allowed_fields[0] if allowed_fields else ""

    # Validate sort order
    if sort_order not in ["asc", "desc"]:
        sort_order = "asc"

    return {"sort_by": sort_by, "sort_order": sort_order}


def extract_filter_params(
    request: Request, allowed_filters: List[str]
) -> Dict[str, Any]:
    """
    Extract filter parameters from request.

    Args:
        request: FastAPI request object
        allowed_filters: List of allowed filter fields

    Returns:
        Dictionary with filter parameters
    """
    filters = {}

    for key, value in request.query_params.items():
        if key.startswith("filter_") and key[7:] in allowed_filters:
            filter_key = key[7:]  # Remove "filter_" prefix
            filters[filter_key] = value

    return filters


def create_request_context(request: Request) -> Dict[str, Any]:
    """
    Create standardized request context.

    Args:
        request: FastAPI request object

    Returns:
        Request context dictionary
    """
    return {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "client_ip": get_client_ip(request),
        "user_agent": get_user_agent(request),
        "headers": get_request_headers(request),
        "params": get_request_params(request),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def log_request(
    request: Request,
    response: Optional[JSONResponse] = None,
    duration: Optional[float] = None,
    user_id: Optional[str] = None,
):
    """
    Log request details.

    Args:
        request: FastAPI request object
        response: Response object (optional)
        duration: Request duration in seconds (optional)
        user_id: User ID (optional)
    """
    log_data = create_request_context(request)

    if response:
        log_data["status_code"] = response.status_code

    if duration:
        log_data["duration"] = duration

    if user_id:
        log_data["user_id"] = user_id

    logger.info("request_processed", **log_data)


def validate_content_type(request: Request, allowed_types: List[str]) -> bool:
    """
    Validate request content type.

    Args:
        request: FastAPI request object
        allowed_types: List of allowed content types

    Returns:
        True if content type is allowed
    """
    content_type = request.headers.get("content-type", "")

    for allowed_type in allowed_types:
        if content_type.startswith(allowed_type):
            return True

    return False


def extract_json_body(request: Request) -> Dict[str, Any]:
    """
    Extract JSON body from request.

    Args:
        request: FastAPI request object

    Returns:
        Request body as dictionary
    """
    try:
        return request.json()
    except Exception as e:
        logger.warning("json_body_extraction_failed", error=str(e))
        return {}


def validate_request_size(request: Request, max_size_mb: int = 10) -> bool:
    """
    Validate request size.

    Args:
        request: FastAPI request object
        max_size_mb: Maximum size in MB

    Returns:
        True if request size is acceptable
    """
    content_length = request.headers.get("content-length")

    if content_length:
        size_mb = int(content_length) / (1024 * 1024)
        return size_mb <= max_size_mb

    return True


def create_rate_limit_key(request: Request, user_id: Optional[str] = None) -> str:
    """
    Create rate limiting key for request.

    Args:
        request: FastAPI request object
        user_id: User ID (optional)

    Returns:
        Rate limiting key
    """
    if user_id:
        return f"rate_limit:{user_id}:{request.method}:{request.url.path}"
    else:
        return (
            f"rate_limit:{get_client_ip(request)}:{request.method}:{request.url.path}"
        )


def extract_api_version(request: Request) -> str:
    """
    Extract API version from request.

    Args:
        request: FastAPI request object

    Returns:
        API version string
    """
    # Check header first
    version = request.headers.get("X-API-Version")
    if version:
        return version

    # Check URL path
    path_parts = request.url.path.split("/")
    # Look for version pattern like /api/v2/...
    for i, part in enumerate(path_parts):
        if (
            part == "api"
            and i + 1 < len(path_parts)
            and path_parts[i + 1].startswith("v")
        ):
            return path_parts[i + 1]

    # Default version
    return "v1"


def create_correlation_id(request: Request) -> str:
    """
    Create or extract correlation ID for request.

    Args:
        request: FastAPI request object

    Returns:
        Correlation ID
    """
    # Check if correlation ID already exists
    correlation_id = request.headers.get("X-Correlation-ID")
    if correlation_id:
        return correlation_id

    # Generate new correlation ID
    import uuid

    return str(uuid.uuid4())


def validate_request_permissions(
    request: Request, required_permissions: List[str]
) -> bool:
    """
    Validate request permissions (placeholder for auth integration).

    Args:
        request: FastAPI request object
        required_permissions: List of required permissions

    Returns:
        True if request has required permissions
    """
    # This is a placeholder - integrate with your auth system
    # For now, return True to allow all requests
    return True


def sanitize_request_data(
    data: Dict[str, Any], sensitive_fields: List[str]
) -> Dict[str, Any]:
    """
    Sanitize request data by removing sensitive fields.

    Args:
        data: Request data to sanitize
        sensitive_fields: List of sensitive field names

    Returns:
        Sanitized data
    """
    sanitized = data.copy()

    for field in sensitive_fields:
        if field in sanitized:
            sanitized[field] = "[REDACTED]"

    return sanitized


def create_request_summary(request: Request) -> Dict[str, Any]:
    """
    Create a summary of the request for logging/monitoring.

    Args:
        request: FastAPI request object

    Returns:
        Request summary dictionary
    """
    return {
        "method": request.method,
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client_ip": get_client_ip(request),
        "user_agent": get_user_agent(request),
        "content_type": request.headers.get("content-type"),
        "content_length": request.headers.get("content-length"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
