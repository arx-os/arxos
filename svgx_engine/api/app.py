"""
FastAPI Application for Arxos Clean Architecture

This module provides the main FastAPI application with proper dependency injection,
middleware, error handling, and API endpoints following Clean Architecture principles.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import uvicorn
from typing import Dict, Any

from svgx_engine.infrastructure.container import Container
from svgx_engine.api.endpoints.building_api import router as building_router
from svgx_engine.utils.errors import SVGXError, ValidationError, ResourceNotFoundError
from core.security.auth_middleware import get_current_user, User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI, user: User = Depends(get_current_user)):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Arxos Clean Architecture API...")
    
    # Initialize dependency injection container
    app.state.container = Container()
    logger.info("Dependency injection container initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Arxos Clean Architecture API...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="Arxos Clean Architecture API",
        description="Enterprise-grade API following Clean Architecture principles",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add Gzip compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Include API routers
    app.include_router(building_router, prefix="/api/v1/buildings", tags=["buildings"])
    
    # Global exception handlers
    @app.exception_handler(SVGXError)
    async def svgx_exception_handler(request, exc: SVGXError, user: User = Depends(get_current_user)):
        """Handle SVGX-specific exceptions."""
        return JSONResponse(
            status_code=400,
            content={
                "error": "SVGX Error",
                "message": str(exc),
                "context": exc.context
            }
        )
    
    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request, exc: ValidationError, user: User = Depends(get_current_user)):
        """Handle validation exceptions."""
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "message": str(exc),
                "field": exc.field
            }
        )
    
    @app.exception_handler(ResourceNotFoundError)
    async def not_found_exception_handler(request, exc: ResourceNotFoundError, user: User = Depends(get_current_user)):
        """Handle resource not found exceptions."""
        return JSONResponse(
            status_code=404,
            content={
                "error": "Resource Not Found",
                "message": str(exc),
                "resource_type": exc.resource_type,
                "resource_id": exc.resource_id
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc: Exception, user: User = Depends(get_current_user)):
        """Handle general exceptions."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred"
            }
        )
    
    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check(user: User = Depends(get_current_user)):
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "Arxos Clean Architecture API",
            "version": "1.0.0"
        }
    
    # Root endpoint
    @app.get("/", tags=["root"])
    async def root(user: User = Depends(get_current_user)):
        """Root endpoint with API information."""
        return {
            "message": "Welcome to Arxos Clean Architecture API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health"
        }
    
    return app


# Dependency injection helper
def get_container() -> Container:
    """Get the dependency injection container."""
    from fastapi import Request
    request = Request()
    return request.app.state.container


# Create the application instance
app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "svgx_engine.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 