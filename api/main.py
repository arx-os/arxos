"""
Arxos Platform API

Main FastAPI application for the Arxos platform providing REST API endpoints
for building information modeling, device management, and platform services.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, ValidationError
import structlog

from application.container import container
from application.config import get_config
from application.logging_config import setup_logging, get_logger
from application.exceptions import ApplicationError, ValidationError, BusinessRuleError
from api.routes import (
    device_router,
    room_router,
    user_router,
    project_router,
    building_router,
    health_router,
    pdf_router
)
from api.middleware import (
    RequestLoggingMiddleware,
    ErrorHandlingMiddleware,
    AuthenticationMiddleware,
    RateLimitingMiddleware
)
from api.dependencies import get_current_user, get_api_key
from core.security.auth_middleware import get_current_user, User


# Configure structured logging
setup_logging()
logger = get_logger("api.main")


class APIInfo(BaseModel):
    """API information model"""
    name: str = "Arxos Platform API"
    version: str = "1.0.0"
    description: str = "Comprehensive API for Arxos building information modeling platform"
    environment: str = os.getenv("ENVIRONMENT", "development")


class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: bool = True
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str
    request_id: Optional[str] = None


class SuccessResponse(BaseModel):
    """Standard success response model"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str
    request_id: Optional[str] = None


# Global application state
app_state: Dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI, user: User = Depends(get_current_user)):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Arxos Platform API...")
    
    try:
        # Initialize application container
        config = get_config()
        container.initialize(config)
        app_state["config"] = config
        app_state["startup_time"] = datetime.utcnow()
        
        logger.info("Application container initialized successfully")
        
        # Initialize services
        await _initialize_services()
        
        logger.info("Arxos Platform API started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start Arxos Platform API: {e}")
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down Arxos Platform API...")
        await _cleanup_services()


async def _initialize_services(user: User = Depends(get_current_user)):
    """Initialize application services"""
    try:
        # Initialize database connections
        await container.get_database_session()
        logger.info("Database connection initialized")
        
        # Initialize cache service
        cache_service = container.get_cache_service()
        if cache_service:
            await cache_service.initialize()
            logger.info("Cache service initialized")
        
        # Initialize event store
        event_store = container.get_event_store()
        if event_store:
            await event_store.initialize()
            logger.info("Event store initialized")
        
        # Initialize message queue
        message_queue = container.get_message_queue()
        if message_queue:
            await message_queue.initialize()
            logger.info("Message queue initialized")
        
        # Initialize metrics service
        metrics_service = container.get_metrics_service()
        if metrics_service:
            await metrics_service.initialize()
            logger.info("Metrics service initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise


async def _cleanup_services(user: User = Depends(get_current_user)):
    """Cleanup application services"""
    try:
        # Cleanup database connections
        await container.cleanup_database()
        logger.info("Database connections cleaned up")
        
        # Cleanup cache service
        cache_service = container.get_cache_service()
        if cache_service:
            await cache_service.cleanup()
            logger.info("Cache service cleaned up")
        
        # Cleanup event store
        event_store = container.get_event_store()
        if event_store:
            await event_store.cleanup()
            logger.info("Event store cleaned up")
        
        # Cleanup message queue
        message_queue = container.get_message_queue()
        if message_queue:
            await message_queue.cleanup()
            logger.info("Message queue cleaned up")
        
        # Cleanup metrics service
        metrics_service = container.get_metrics_service()
        if metrics_service:
            await metrics_service.cleanup()
            logger.info("Metrics service cleaned up")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


def custom_openapi():
    """Custom OpenAPI schema generator"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Arxos Platform API",
        version="1.0.0",
        description="""
        # Arxos Platform API
        
        Comprehensive REST API for the Arxos building information modeling platform.
        
        ## Features
        
        * **Device Management** - Create, read, update, and delete devices
        * **Room Management** - Manage rooms and their properties
        * **User Management** - Handle user accounts and permissions
        * **Project Management** - Manage building projects
        * **Building Management** - Handle building information and models
        
        ## Authentication
        
        API requests require authentication using API keys or JWT tokens.
        
        ## Rate Limiting
        
        API requests are rate limited to ensure fair usage.
        
        ## Error Handling
        
        All errors return consistent JSON responses with error codes and details.
        """,
        routes=app.routes,
    )
    
    # Add custom info
    openapi_schema["info"]["x-logo"] = {
        "url": "https://arxos.com/logo.png"
    }
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        },
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    # Add global security
    openapi_schema["security"] = [
        {"ApiKeyAuth": []},
        {"BearerAuth": []}
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Create FastAPI application
app = FastAPI(
    title="Arxos Platform API",
    description="Comprehensive REST API for the Arxos building information modeling platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Set custom OpenAPI schema
app.openapi = custom_openapi


# Add middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(AuthenticationMiddleware)
app.add_middleware(RateLimitingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# Global exception handlers
@app.exception_handler(ApplicationError)
async def application_error_handler(request: Request, exc: ApplicationError, user: User = Depends(get_current_user)):
    """Handle application-specific errors"""
    logger.error(f"Application error: {exc.message}", error_code=exc.error_code, details=exc.details)
    
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            timestamp=datetime.utcnow().isoformat(),
            request_id=request.state.request_id if hasattr(request.state, 'request_id') else None
        ).dict()
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError, user: User = Depends(get_current_user)):
    """Handle validation errors"""
    logger.error(f"Validation error: {exc.message}", field=exc.field, value=exc.value)
    
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error_code="VALIDATION_ERROR",
            message=exc.message,
            details={"field": exc.field, "value": exc.value},
            timestamp=datetime.utcnow().isoformat(),
            request_id=request.state.request_id if hasattr(request.state, 'request_id') else None
        ).dict()
    )


@app.exception_handler(BusinessRuleError)
async def business_rule_error_handler(request: Request, exc: BusinessRuleError, user: User = Depends(get_current_user)):
    """Handle business rule errors"""
    logger.error(f"Business rule error: {exc.message}", rule=exc.rule, context=exc.context)
    
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error_code="BUSINESS_RULE_ERROR",
            message=exc.message,
            details={"rule": exc.rule, "context": exc.context},
            timestamp=datetime.utcnow().isoformat(),
            request_id=request.state.request_id if hasattr(request.state, 'request_id') else None
        ).dict()
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception, user: User = Depends(get_current_user)):
    """Handle all other exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            details={"exception_type": type(exc).__name__},
            timestamp=datetime.utcnow().isoformat(),
            request_id=request.state.request_id if hasattr(request.state, 'request_id') else None
        ).dict()
    )


# Root endpoint
@app.get("/", response_model=Dict[str, Any])
async def root(user: User = Depends(get_current_user)):
    """Root endpoint with API information"""
    return {
        "service": "Arxos Platform API",
        "version": "1.0.0",
        "description": "Comprehensive REST API for building information modeling",
        "status": "running",
        "uptime": (datetime.utcnow() - app_state.get("startup_time", datetime.utcnow())).total_seconds(),
        "endpoints": {
            "/docs": "API documentation (Swagger UI)",
            "/redoc": "API documentation (ReDoc)",
            "/health": "Health check",
            "/api/v1/devices": "Device management",
            "/api/v1/rooms": "Room management",
            "/api/v1/users": "User management",
            "/api/v1/projects": "Project management",
            "/api/v1/buildings": "Building management"
        },
        "environment": app_state.get("config", {}).get("environment", "development")
    }


# Health check endpoint
@app.get("/health", response_model=Dict[str, Any])
async def health_check(user: User = Depends(get_current_user)):
    """Comprehensive health check endpoint"""
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
        
        # Overall health
        overall_healthy = db_healthy and cache_healthy and event_store_healthy
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "service": "arxos-api",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": "healthy" if db_healthy else "unhealthy",
                "cache": "healthy" if cache_healthy else "unhealthy",
                "event_store": "healthy" if event_store_healthy else "unhealthy"
            },
            "uptime": (datetime.utcnow() - app_state.get("startup_time", datetime.utcnow())).total_seconds()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "arxos-api",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "checks": {
                "database": "unhealthy",
                "cache": "unhealthy",
                "event_store": "unhealthy"
            }
        }


# Include API routers
app.include_router(health_router, prefix="/api/v1", tags=["Health"])
app.include_router(device_router, prefix="/api/v1/devices", tags=["Devices"])
app.include_router(room_router, prefix="/api/v1/rooms", tags=["Rooms"])
app.include_router(user_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(project_router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(building_router, prefix="/api/v1/buildings", tags=["Buildings"])
app.include_router(pdf_router, tags=["PDF Analysis"])


if __name__ == "__main__":
    # Get configuration
    config = get_config()
    
    # Run the application
    uvicorn.run(
        "api.main:app",
        host=config.api.host,
        port=config.api.port,
        reload=config.environment == "development",
        log_level=config.logging.level.lower()
    ) 