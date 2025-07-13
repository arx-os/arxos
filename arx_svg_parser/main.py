#!/usr/bin/env python3
"""
Main entry point for Arxos SVG-BIM Integration System.

This module provides the main application entry point with proper logging,
configuration, and error handling.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Initialize structured logging first
from utils.logging import setup_logging_for_environment
from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
import structlog
from arx_svg_parser.schemas.error_response import ErrorResponse

# Setup environment-specific logging
setup_logging_for_environment()
logger = structlog.get_logger(__name__)

def register_exception_handlers(app: FastAPI):
    """Register structured exception handlers."""
    @app.exception_handler(Exception)
    async def catch_all_exception_handler(request: Request, exc: Exception):
        logger.error("unhandled_exception", 
                    path=str(request.url.path), 
                    method=request.method,
                    error=str(exc), 
                    error_type=str(type(exc)),
                    client_ip=request.client.host if request.client else "unknown")
        
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="Internal Server Error",
                code="INTERNAL_ERROR",
                details={"exception": str(exc)}
            ).dict()
        )

def main():
    """Main application entry point."""
    try:
        logger.info("starting_application", 
                   application="Arxos SVG-BIM Integration System",
                   version="1.0.0")
        
        # Import and run the FastAPI application
        from api.main import app
        import uvicorn
        
        # Get configuration from environment
        host = os.getenv("API_HOST", "0.0.0.0")
        port = int(os.getenv("API_PORT", "8000"))
        reload = os.getenv("API_RELOAD", "true").lower() == "true"
        workers = int(os.getenv("API_WORKERS", "1"))
        
        logger.info("server_configuration",
                   host=host,
                   port=port,
                   reload=reload,
                   workers=workers)
        
        # Start the server
        uvicorn.run(
            "api.main:app",
            host=host,
            port=port,
            reload=reload,
            workers=workers if not reload else 1,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        logger.info("application_stopped", reason="user_interrupt")
    except Exception as e:
        logger.error("application_startup_failed",
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main() 