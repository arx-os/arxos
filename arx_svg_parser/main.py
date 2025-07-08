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

# Initialize logging first
from utils.logging_config import initialize_logging, get_logger

# Initialize logging
initialize_logging()
logger = get_logger(__name__)

def main():
    """Main application entry point."""
    try:
        logger.info("Starting Arxos SVG-BIM Integration System")
        
        # Import and run the FastAPI application
        from api.main import app
        import uvicorn
        
        # Get configuration from environment
        host = os.getenv("API_HOST", "0.0.0.0")
        port = int(os.getenv("API_PORT", "8000"))
        reload = os.getenv("API_RELOAD", "true").lower() == "true"
        workers = int(os.getenv("API_WORKERS", "1"))
        
        logger.info(f"Starting server on {host}:{port}")
        logger.info(f"Reload mode: {reload}")
        logger.info(f"Workers: {workers}")
        
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
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application failed to start: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main() 