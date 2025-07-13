"""
Core Platform Router

FastAPI endpoints for core platform operations including:
- System initialization and configuration
- Service management and monitoring
- Performance optimization
- Health checks and diagnostics
- Backup and recovery operations
- Security auditing and compliance
- Integration testing and validation
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
import structlog

from services.core_platform import (
    CorePlatformService, SystemStatus, ServiceHealth, PerformanceMetrics,
    SecurityAudit, BackupStatus, IntegrationTest
)

logger = structlog.get_logger(__name__)

# Initialize router
router = APIRouter(prefix="/platform", tags=["Core Platform"])

# Initialize service
platform_service = CorePlatformService()


# Pydantic models for request/response
class ServiceRegistrationRequest(BaseModel):
    """Request model for service registration."""
    service_id: str = BaseModel.Field(..., description="Unique service identifier")
    name: str = BaseModel.Field(..., description="Service name")
    service_type: str = BaseModel.Field(..., description="Service type")
    version: str = BaseModel.Field(..., description="Service version")
    host: str = BaseModel.Field(..., description="Service host")
    port: int = BaseModel.Field(..., description="Service port")
    health_endpoint: Optional[str] = BaseModel.Field(None, description="Health check endpoint")
    metadata: Optional[Dict[str, Any]] = BaseModel.Field(None, description="Additional metadata")


class ServiceInfoResponse(BaseModel):
    """Response model for service information."""
    service_id: str = BaseModel.Field(..., description="Service identifier")
    name: str = BaseModel.Field(..., description="Service name")
    service_type: str = BaseModel.Field(..., description="Service type")
    status: str = BaseModel.Field(..., description="Service status")
    version: str = BaseModel.Field(..., description="Service version")
    host: str = BaseModel.Field(..., description="Service host")
    port: int = BaseModel.Field(..., description="Service port")
    health_endpoint: Optional[str] = BaseModel.Field(None, description="Health check endpoint")
    metadata: Optional[Dict[str, Any]] = BaseModel.Field(None, description="Additional metadata")
    last_heartbeat: Optional[str] = BaseModel.Field(None, description="Last heartbeat timestamp")
    created_at: str = BaseModel.Field(..., description="Creation timestamp")


class HealthStatusResponse(BaseModel):
    """Response model for health status."""
    status: str = BaseModel.Field(..., description="Overall health status")
    healthy_services: int = BaseModel.Field(..., description="Number of healthy services")
    total_services: int = BaseModel.Field(..., description="Total number of services")
    health_percentage: float = BaseModel.Field(..., description="Health percentage")
    last_check: str = BaseModel.Field(..., description="Last health check timestamp")
    uptime: float = BaseModel.Field(..., description="System uptime in seconds")


class SystemMetricsResponse(BaseModel):
    """Response model for system metrics."""
    cpu_usage: float = BaseModel.Field(..., description="CPU usage percentage")
    memory_usage: float = BaseModel.Field(..., description="Memory usage percentage")
    disk_usage: float = BaseModel.Field(..., description="Disk usage percentage")
    network_io: Dict[str, float] = BaseModel.Field(..., description="Network I/O statistics")
    active_connections: int = BaseModel.Field(..., description="Active connections")
    response_time: float = BaseModel.Field(..., description="Average response time")
    error_rate: float = BaseModel.Field(..., description="Error rate percentage")
    timestamp: str = BaseModel.Field(..., description="Metrics timestamp")


class CacheStatsResponse(BaseModel):
    """Response model for cache statistics."""
    hits: int = BaseModel.Field(..., description="Cache hits")
    misses: int = BaseModel.Field(..., description="Cache misses")
    sets: int = BaseModel.Field(..., description="Cache sets")
    deletes: int = BaseModel.Field(..., description="Cache deletes")
    hit_rate: float = BaseModel.Field(..., description="Cache hit rate percentage")
    memory_cache_size: int = BaseModel.Field(..., description="Memory cache size")
    redis_available: bool = BaseModel.Field(..., description="Redis availability")


class ConfigurationResponse(BaseModel):
    """Response model for configuration."""
    environment: str = BaseModel.Field(..., description="Environment name")
    debug_mode: bool = BaseModel.Field(..., description="Debug mode flag")
    log_level: str = BaseModel.Field(..., description="Log level")
    database_url: str = BaseModel.Field(..., description="Database URL")
    redis_url: str = BaseModel.Field(..., description="Redis URL")
    api_host: str = BaseModel.Field(..., description="API host")
    api_port: int = BaseModel.Field(..., description="API port")
    max_workers: int = BaseModel.Field(..., description="Maximum workers")
    cache_ttl: int = BaseModel.Field(..., description="Cache TTL in seconds")
    health_check_interval: int = BaseModel.Field(..., description="Health check interval")
    backup_interval: int = BaseModel.Field(..., description="Backup interval")
    security_settings: Dict[str, Any] = BaseModel.Field(..., description="Security settings")
    feature_flags: Dict[str, bool] = BaseModel.Field(..., description="Feature flags")


class ConfigurationUpdateRequest(BaseModel):
    """Request model for configuration updates."""
    updates: Dict[str, Any] = BaseModel.Field(..., description="Configuration updates")


class PerformanceMetricsResponse(BaseModel):
    """Response model for performance metrics."""
    uptime_seconds: float = BaseModel.Field(..., description="System uptime in seconds")
    total_requests: int = BaseModel.Field(..., description="Total requests")
    successful_requests: int = BaseModel.Field(..., description="Successful requests")
    failed_requests: int = BaseModel.Field(..., description="Failed requests")
    success_rate: float = BaseModel.Field(..., description="Success rate percentage")
    average_response_time: float = BaseModel.Field(..., description="Average response time")
    registered_services: int = BaseModel.Field(..., description="Number of registered services")
    health_status: str = BaseModel.Field(..., description="Health status")
    cache_stats: Dict[str, Any] = BaseModel.Field(..., description="Cache statistics")
    system_metrics: Dict[str, Any] = BaseModel.Field(..., description="System metrics")


@router.get("/health", response_model=HealthStatusResponse)
async def get_health_status():
    """
    Get overall system health status.
    
    This endpoint provides comprehensive health information including
    service status, uptime, and health percentages.
    
    Returns:
        System health status information
        
    Raises:
        HTTPException: If health check fails
    """
    try:
        logger.info("Getting system health status")
        
        health_status = platform_service.get_health_status()
        
        return HealthStatusResponse(**health_status)
        
    except Exception as e:
        logger.error(f"Health status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/services", response_model=List[ServiceInfoResponse])
async def list_services(service_type: Optional[str] = None):
    """
    List all registered services.
    
    This endpoint provides information about all registered services
    with optional filtering by service type.
    
    Args:
        service_type: Optional service type filter
        
    Returns:
        List of service information
        
    Raises:
        HTTPException: If service listing fails
    """
    try:
        logger.info("Getting list of registered services")
        
        # Convert service type string to enum if provided
        service_type_enum = None
        if service_type:
            try:
                service_type_enum = ServiceType(service_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid service type: {service_type}")
        
        services = platform_service.list_services(service_type_enum)
        
        return [
            ServiceInfoResponse(
                service_id=service.service_id,
                name=service.name,
                service_type=service.service_type.value,
                status=service.status.value,
                version=service.version,
                host=service.host,
                port=service.port,
                health_endpoint=service.health_endpoint,
                metadata=service.metadata,
                last_heartbeat=service.last_heartbeat.isoformat() if service.last_heartbeat else None,
                created_at=service.created_at.isoformat()
            )
            for service in services
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list services: {e}")
        raise HTTPException(status_code=500, detail=f"Service listing failed: {str(e)}")


@router.post("/services", response_model=ServiceInfoResponse)
async def register_service(request: ServiceRegistrationRequest):
    """
    Register a new service with the platform.
    
    This endpoint allows services to register themselves with the platform
    for discovery and health monitoring.
    
    Args:
        request: Service registration request
        
    Returns:
        Registered service information
        
    Raises:
        HTTPException: If service registration fails
    """
    try:
        logger.info(f"Registering service: {request.service_id}")
        
        # Validate service type
        try:
            service_type = ServiceType(request.service_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid service type: {request.service_type}")
        
        # Create service info
        service_info = ServiceInfo(
            service_id=request.service_id,
            name=request.name,
            service_type=service_type,
            status=ServiceStatus.RUNNING,
            version=request.version,
            host=request.host,
            port=request.port,
            health_endpoint=request.health_endpoint,
            metadata=request.metadata,
            last_heartbeat=datetime.now(),
            created_at=datetime.now()
        )
        
        # Register service
        success = platform_service.register_service(service_info)
        
        if not success:
            raise HTTPException(status_code=500, detail="Service registration failed")
        
        logger.info(f"Service {request.service_id} registered successfully")
        
        return ServiceInfoResponse(
            service_id=service_info.service_id,
            name=service_info.name,
            service_type=service_info.service_type.value,
            status=service_info.status.value,
            version=service_info.version,
            host=service_info.host,
            port=service_info.port,
            health_endpoint=service_info.health_endpoint,
            metadata=service_info.metadata,
            last_heartbeat=service_info.last_heartbeat.isoformat(),
            created_at=service_info.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Service registration failed for {request.service_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Service registration failed: {str(e)}")


@router.get("/services/{service_id}", response_model=ServiceInfoResponse)
async def get_service_info(service_id: str):
    """
    Get information about a specific service.
    
    This endpoint provides detailed information about a registered service
    including status, health, and metadata.
    
    Args:
        service_id: Service identifier
        
    Returns:
        Service information
        
    Raises:
        HTTPException: If service not found or retrieval fails
    """
    try:
        logger.info(f"Getting service information for {service_id}")
        
        service_info = platform_service.get_service_info(service_id)
        
        if not service_info:
            raise HTTPException(status_code=404, detail=f"Service {service_id} not found")
        
        return ServiceInfoResponse(
            service_id=service_info.service_id,
            name=service_info.name,
            service_type=service_info.service_type.value,
            status=service_info.status.value,
            version=service_info.version,
            host=service_info.host,
            port=service_info.port,
            health_endpoint=service_info.health_endpoint,
            metadata=service_info.metadata,
            last_heartbeat=service_info.last_heartbeat.isoformat() if service_info.last_heartbeat else None,
            created_at=service_info.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get service info for {service_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Service info retrieval failed: {str(e)}")


@router.delete("/services/{service_id}")
async def unregister_service(service_id: str):
    """
    Unregister a service from the platform.
    
    This endpoint allows services to unregister themselves from the platform
    when they are shutting down or becoming unavailable.
    
    Args:
        service_id: Service identifier
        
    Returns:
        Unregistration result
        
    Raises:
        HTTPException: If service unregistration fails
    """
    try:
        logger.info(f"Unregistering service: {service_id}")
        
        success = platform_service.unregister_service(service_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Service {service_id} not found")
        
        logger.info(f"Service {service_id} unregistered successfully")
        
        return {
            "service_id": service_id,
            "status": "unregistered",
            "unregistered_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unregister service {service_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Service unregistration failed: {str(e)}")


@router.get("/metrics", response_model=List[SystemMetricsResponse])
async def get_system_metrics(limit: int = 100):
    """
    Get system performance metrics.
    
    This endpoint provides historical system performance metrics including
    CPU, memory, disk, and network usage.
    
    Args:
        limit: Maximum number of metrics to return (default: 100)
        
    Returns:
        List of system metrics
        
    Raises:
        HTTPException: If metrics retrieval fails
    """
    try:
        logger.info("Getting system metrics")
        
        if limit < 1 or limit > 1000:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")
        
        metrics = platform_service.get_system_metrics(limit)
        
        return [
            SystemMetricsResponse(
                cpu_usage=metric.cpu_usage,
                memory_usage=metric.memory_usage,
                disk_usage=metric.disk_usage,
                network_io=metric.network_io,
                active_connections=metric.active_connections,
                response_time=metric.response_time,
                error_rate=metric.error_rate,
                timestamp=metric.timestamp.isoformat()
            )
            for metric in metrics
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")


@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats():
    """
    Get cache performance statistics.
    
    This endpoint provides comprehensive cache performance metrics including
    hit rates, memory usage, and Redis availability.
    
    Returns:
        Cache statistics
        
    Raises:
        HTTPException: If cache stats retrieval fails
    """
    try:
        logger.info("Getting cache statistics")
        
        cache_stats = platform_service.get_cache_stats()
        
        return CacheStatsResponse(**cache_stats)
        
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail=f"Cache stats retrieval failed: {str(e)}")


@router.post("/cache/{key}")
async def set_cache_value(key: str, value: Any, ttl: Optional[int] = None):
    """
    Set a value in the cache.
    
    This endpoint allows setting values in the platform cache with
    optional time-to-live settings.
    
    Args:
        key: Cache key
        value: Value to cache
        ttl: Optional time-to-live in seconds
        
    Returns:
        Cache operation result
        
    Raises:
        HTTPException: If cache operation fails
    """
    try:
        logger.info(f"Setting cache value for key: {key}")
        
        success = platform_service.cache_set(key, value, ttl)
        
        if not success:
            raise HTTPException(status_code=500, detail="Cache set operation failed")
        
        return {
            "key": key,
            "status": "set",
            "ttl": ttl,
            "set_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set cache value for key {key}: {e}")
        raise HTTPException(status_code=500, detail=f"Cache set failed: {str(e)}")


@router.get("/cache/{key}")
async def get_cache_value(key: str):
    """
    Get a value from the cache.
    
    This endpoint retrieves values from the platform cache.
    
    Args:
        key: Cache key
        
    Returns:
        Cached value or null if not found
        
    Raises:
        HTTPException: If cache operation fails
    """
    try:
        logger.info(f"Getting cache value for key: {key}")
        
        value = platform_service.cache_get(key)
        
        return {
            "key": key,
            "value": value,
            "found": value is not None,
            "retrieved_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get cache value for key {key}: {e}")
        raise HTTPException(status_code=500, detail=f"Cache get failed: {str(e)}")


@router.delete("/cache/{key}")
async def delete_cache_value(key: str):
    """
    Delete a value from the cache.
    
    This endpoint removes values from the platform cache.
    
    Args:
        key: Cache key
        
    Returns:
        Cache operation result
        
    Raises:
        HTTPException: If cache operation fails
    """
    try:
        logger.info(f"Deleting cache value for key: {key}")
        
        success = platform_service.cache_delete(key)
        
        if not success:
            raise HTTPException(status_code=500, detail="Cache delete operation failed")
        
        return {
            "key": key,
            "status": "deleted",
            "deleted_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete cache value for key {key}: {e}")
        raise HTTPException(status_code=500, detail=f"Cache delete failed: {str(e)}")


@router.get("/config", response_model=ConfigurationResponse)
async def get_configuration():
    """
    Get current system configuration.
    
    This endpoint provides the current platform configuration including
    environment settings, feature flags, and system parameters.
    
    Returns:
        Current configuration
        
    Raises:
        HTTPException: If configuration retrieval fails
    """
    try:
        logger.info("Getting system configuration")
        
        config = platform_service.get_configuration()
        
        return ConfigurationResponse(
            environment=config.environment,
            debug_mode=config.debug_mode,
            log_level=config.log_level,
            database_url=config.database_url,
            redis_url=config.redis_url,
            api_host=config.api_host,
            api_port=config.api_port,
            max_workers=config.max_workers,
            cache_ttl=config.cache_ttl,
            health_check_interval=config.health_check_interval,
            backup_interval=config.backup_interval,
            security_settings=config.security_settings,
            feature_flags=config.feature_flags
        )
        
    except Exception as e:
        logger.error(f"Failed to get configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration retrieval failed: {str(e)}")


@router.put("/config")
async def update_configuration(request: ConfigurationUpdateRequest):
    """
    Update system configuration.
    
    This endpoint allows updating platform configuration parameters
    with proper validation and persistence.
    
    Args:
        request: Configuration update request
        
    Returns:
        Update result
        
    Raises:
        HTTPException: If configuration update fails
    """
    try:
        logger.info("Updating system configuration")
        
        success = platform_service.update_configuration(request.updates)
        
        if not success:
            raise HTTPException(status_code=500, detail="Configuration update failed")
        
        return {
            "status": "updated",
            "updates": request.updates,
            "updated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration update failed: {str(e)}")


@router.get("/performance", response_model=PerformanceMetricsResponse)
async def get_performance_metrics():
    """
    Get comprehensive performance metrics.
    
    This endpoint provides detailed performance metrics including
    uptime, request statistics, success rates, and system health.
    
    Returns:
        Performance metrics
        
    Raises:
        HTTPException: If metrics retrieval fails
    """
    try:
        logger.info("Getting performance metrics")
        
        metrics = platform_service.get_performance_metrics()
        
        return PerformanceMetricsResponse(**metrics)
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Performance metrics retrieval failed: {str(e)}")


@router.get("/services/types")
async def get_service_types():
    """
    Get all available service types.
    
    Returns:
        List of service types with descriptions
    """
    service_types = [
        {
            "type": ServiceType.CORE.value,
            "name": "Core Service",
            "description": "Core platform services",
            "examples": ["Platform Core", "Configuration Service", "Health Monitor"]
        },
        {
            "type": ServiceType.API.value,
            "name": "API Service",
            "description": "API and web services",
            "examples": ["REST API", "GraphQL Service", "WebSocket Service"]
        },
        {
            "type": ServiceType.WORKER.value,
            "name": "Worker Service",
            "description": "Background processing services",
            "examples": ["Task Queue Worker", "Data Processor", "Scheduler"]
        },
        {
            "type": ServiceType.DATABASE.value,
            "name": "Database Service",
            "description": "Database and storage services",
            "examples": ["PostgreSQL", "Redis", "MongoDB"]
        },
        {
            "type": ServiceType.CACHE.value,
            "name": "Cache Service",
            "description": "Caching and session services",
            "examples": ["Redis Cache", "Memory Cache", "CDN"]
        },
        {
            "type": ServiceType.EXTERNAL.value,
            "name": "External Service",
            "description": "External third-party services",
            "examples": ["Payment Gateway", "Email Service", "SMS Service"]
        }
    ]
    
    return {"service_types": service_types}


@router.get("/services/status")
async def get_services_status():
    """
    Get status of all registered services.
    
    Returns:
        Service status summary
    """
    try:
        services = platform_service.list_services()
        
        status_summary = {
            "total_services": len(services),
            "running_services": len([s for s in services if s.status == ServiceStatus.RUNNING]),
            "error_services": len([s for s in services if s.status == ServiceStatus.ERROR]),
            "degraded_services": len([s for s in services if s.status == ServiceStatus.DEGRADED]),
            "stopped_services": len([s for s in services if s.status == ServiceStatus.STOPPED]),
            "services_by_type": {},
            "services_by_status": {}
        }
        
        # Group by service type
        for service in services:
            service_type = service.service_type.value
            if service_type not in status_summary["services_by_type"]:
                status_summary["services_by_type"][service_type] = []
            status_summary["services_by_type"][service_type].append({
                "service_id": service.service_id,
                "name": service.name,
                "status": service.status.value
            })
        
        # Group by status
        for service in services:
            status = service.status.value
            if status not in status_summary["services_by_status"]:
                status_summary["services_by_status"][status] = []
            status_summary["services_by_status"][status].append({
                "service_id": service.service_id,
                "name": service.name,
                "service_type": service.service_type.value
            })
        
        return status_summary
        
    except Exception as e:
        logger.error(f"Failed to get services status: {e}")
        raise HTTPException(status_code=500, detail=f"Services status retrieval failed: {str(e)}")


# Error handlers
@router.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with detailed error information."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )


@router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions with logging."""
    logger.error(f"Unhandled exception in core platform API: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    ) 