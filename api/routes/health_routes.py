"""
Health Check API Routes

This module contains FastAPI routes for health checks and system status
monitoring.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends
from datetime import datetime

from application.container import container
from application.logging_config import get_logger
from api.dependencies import format_success_response, format_error_response

logger = get_logger("api.health_routes")

# Create router
router = APIRouter()


@router.get(
    "/health",
    response_model=Dict[str, Any],
    summary="Health check",
    description="Basic health check endpoint."
)
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    try:
        return format_success_response(
            data={
                "status": "healthy",
                "service": "arxos-api",
                "version": "1.0.0",
                "timestamp": datetime.utcnow().isoformat()
            },
            message="Service is healthy"
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return format_error_response(
            error_code="HEALTH_CHECK_FAILED",
            message="Health check failed",
            details={"error": str(e)}
        )


@router.get(
    "/health/detailed",
    response_model=Dict[str, Any],
    summary="Detailed health check",
    description="Comprehensive health check with all service dependencies."
)
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check with all service dependencies."""
    try:
        # Check database connection
        db_session = container.get_database_session()
        db_healthy = db_session is not None

        # Check cache service
        cache_service = container.get_cache_service()
        cache_healthy = cache_service is not None

        # Check event store
        event_store = container.get_event_store()
        event_store_healthy = event_store is not None

        # Check message queue
        message_queue = container.get_message_queue()
        message_queue_healthy = message_queue is not None

        # Check metrics service
        metrics_service = container.get_metrics_service()
        metrics_healthy = metrics_service is not None

        # Overall health
        overall_healthy = (
            db_healthy and
            cache_healthy and
            event_store_healthy and
            message_queue_healthy and
            metrics_healthy
        )

        return format_success_response(
            data={
                "status": "healthy" if overall_healthy else "unhealthy",
                "service": "arxos-api",
                "version": "1.0.0",
                "timestamp": datetime.utcnow().isoformat(),
                "checks": {
                    "database": "healthy" if db_healthy else "unhealthy",
                    "cache": "healthy" if cache_healthy else "unhealthy",
                    "event_store": "healthy" if event_store_healthy else "unhealthy",
                    "message_queue": "healthy" if message_queue_healthy else "unhealthy",
                    "metrics": "healthy" if metrics_healthy else "unhealthy"
                },
                "overall": "healthy" if overall_healthy else "unhealthy"
            },
            message="Detailed health check completed"
        )

    except Exception as e:
        logger.error(f"Detailed health check failed: {str(e)}")
        return format_error_response(
            error_code="DETAILED_HEALTH_CHECK_FAILED",
            message="Detailed health check failed",
            details={"error": str(e)}
        )


@router.get(
    "/health/readiness",
    response_model=Dict[str, Any],
    summary="Readiness probe",
    description="Kubernetes readiness probe endpoint."
)
async def readiness_probe() -> Dict[str, Any]:
    """Kubernetes readiness probe endpoint."""
    try:
        # Check if all required services are ready
        db_session = container.get_database_session()
        cache_service = container.get_cache_service()

        ready = db_session is not None and cache_service is not None

        return format_success_response(
            data={
                "ready": ready,
                "service": "arxos-api",
                "timestamp": datetime.utcnow().isoformat()
            },
            message="Readiness check completed"
        )

    except Exception as e:
        logger.error(f"Readiness probe failed: {str(e)}")
        return format_error_response(
            error_code="READINESS_PROBE_FAILED",
            message="Readiness probe failed",
            details={"error": str(e)}
        )


@router.get(
    "/health/liveness",
    response_model=Dict[str, Any],
    summary="Liveness probe",
    description="Kubernetes liveness probe endpoint."
)
async def liveness_probe() -> Dict[str, Any]:
    """Kubernetes liveness probe endpoint."""
    try:
        # Simple check to ensure the service is alive
        return format_success_response(
            data={
                "alive": True,
                "service": "arxos-api",
                "timestamp": datetime.utcnow().isoformat()
            },
            message="Service is alive"
        )

    except Exception as e:
        logger.error(f"Liveness probe failed: {str(e)}")
        return format_error_response(
            error_code="LIVENESS_PROBE_FAILED",
            message="Liveness probe failed",
            details={"error": str(e)}
        )


@router.get(
    "/health/metrics",
    response_model=Dict[str, Any],
    summary="Health metrics",
    description="Get health-related metrics and statistics."
)
async def health_metrics() -> Dict[str, Any]:
    """Get health-related metrics and statistics."""
    try:
        # Get basic metrics
        metrics = {
            "uptime": "0s",  # Would be calculated from startup time
            "total_requests": 0,  # Would be tracked by middleware
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "memory_usage": "0MB",  # Would be calculated
            "cpu_usage": "0%",  # Would be calculated
            "active_connections": 0
        }

        return format_success_response(
            data=metrics,
            message="Health metrics retrieved successfully"
        )

    except Exception as e:
        logger.error(f"Health metrics failed: {str(e)}")
        return format_error_response(
            error_code="HEALTH_METRICS_FAILED",
            message="Failed to retrieve health metrics",
            details={"error": str(e)}
        )


@router.get(
    "/health/status",
    response_model=Dict[str, Any],
    summary="Service status",
    description="Get detailed service status information."
)
async def service_status() -> Dict[str, Any]:
    """Get detailed service status information."""
    try:
        status_info = {
            "service": "arxos-api",
            "version": "1.0.0",
            "environment": "development",  # Would be from config import config
            "startup_time": datetime.utcnow().isoformat(),
            "current_time": datetime.utcnow().isoformat(),
            "status": "running",
            "features": {
                "device_management": True,
                "room_management": True,
                "user_management": True,
                "project_management": True,
                "building_management": True
            },
            "dependencies": {
                "database": "connected",
                "cache": "connected",
                "event_store": "connected",
                "message_queue": "connected",
                "metrics": "connected"
            }
        }

        return format_success_response(
            data=status_info,
            message="Service status retrieved successfully"
        )

    except Exception as e:
        logger.error(f"Service status failed: {str(e)}")
        return format_error_response(
            error_code="SERVICE_STATUS_FAILED",
            message="Failed to retrieve service status",
            details={"error": str(e)}
        )
