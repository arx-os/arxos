import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from arx_svg_parser.routers import parse, annotate, scale, ingest, bim, realtime, partitioning
from arx_svg_parser.routers import symbol_library, symbol_generator, version_control
from arx_svg_parser.models import HealthResponse
from arx_svg_parser.services.realtime_service import realtime_service
from arx_svg_parser.services.cache_service import cache_service
from arx_svg_parser.services.data_partitioning import data_partitioning_service
from arx_svg_parser.routers.access_control import router as access_control_router
from arx_svg_parser.routers.auto_snapshot import router as auto_snapshot_router
from arx_svg_parser.utils.response_helpers import ResponseHelper
from arx_svg_parser.utils.error_handlers import (
    handle_exception, http_exception_handler, 
    validation_exception_handler, general_exception_handler
)

# Setup logging
from arx_svg_parser.utils.logger import logger, generate_correlation_id, generate_request_id

app = FastAPI(
    title="Arx SVG Parser Microservice",
    description="Microservice for parsing SVG files and extracting building information",
    version="1.0.0"
)

logger.info("Starting Arx SVG Parser Microservice")

# CORS middleware for local/frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers with /v1 prefix
def prefix_router(router):
    # Helper to add /v1 to router prefix if not already present
    if hasattr(router, 'prefix') and not router.prefix.startswith("/v1"):
        router.prefix = "/v1" + router.prefix
    return router

app.include_router(prefix_router(parse.router))
app.include_router(prefix_router(annotate.router))
app.include_router(prefix_router(scale.router))
app.include_router(prefix_router(ingest.router))
app.include_router(prefix_router(bim.router))
app.include_router(prefix_router(symbol_library.router))
app.include_router(prefix_router(symbol_generator.router))
app.include_router(prefix_router(realtime.router))
app.include_router(prefix_router(partitioning.router))
app.include_router(prefix_router(version_control.router))
app.include_router(access_control_router, prefix="/access-control")
app.include_router(auto_snapshot_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        # Start real-time service
        await realtime_service.start()
        logger.info("Real-time service started")
        
        # Start cache service
        await cache_service.start()
        logger.info("Cache service started")
        
        # Start data partitioning service
        await data_partitioning_service.start()
        logger.info("Data partitioning service started")
        
    except Exception as e:
        logger.error(f"Error starting services: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup services on shutdown"""
    try:
        # Stop real-time service
        await realtime_service.stop()
        logger.info("Real-time service stopped")
        
        # Stop cache service
        await cache_service.stop()
        logger.info("Cache service stopped")
        
        # Stop data partitioning service
        await data_partitioning_service.stop()
        logger.info("Data partitioning service stopped")
        
    except Exception as e:
        logger.error(f"Error stopping services: {e}")

@app.get("/v1/health", response_model=HealthResponse)
async def health_check():
    logger.info("Health check endpoint called")
    return {"status": "svg-parser up and running"}

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return ResponseHelper.success_response(
        data={
            "name": "Arx SVG Parser Microservice",
            "version": "1.0.0",
            "description": "Microservice for parsing SVG files and extracting building information",
            "endpoints": {
                "health": "/v1/health",
                "symbol_recognition": "/v1/parse/recognize-symbols",
                "symbol_rendering": "/v1/parse/render-symbols",
                "auto_recognition": "/v1/parse/auto-recognize-and-render",
                "bim_extraction": "/v1/parse/extract-bim",
                "symbol_library": "/v1/parse/symbol-library",
                "systems": "/v1/parse/systems",
                "categories": "/v1/parse/categories",
                "symbol_generator": "/v1/symbol-generator",
                "realtime": {
                    "websocket": "/v1/realtime/ws/{user_id}",
                    "join_room": "/v1/realtime/join-room",
                    "acquire_lock": "/v1/realtime/acquire-lock",
                    "cache_stats": "/v1/realtime/cache-stats"
                },
                "partitioning": {
                    "partition_floor": "/v1/partitioning/partition-floor",
                    "floor_partitions": "/v1/partitioning/floor-partitions/{building_id}/{floor_id}",
                    "load_floor": "/v1/partitioning/load-floor",
                    "performance_stats": "/v1/partitioning/performance-stats",
                    "optimize_floor": "/v1/partitioning/optimize-floor/{building_id}/{floor_id}"
                },
                "version_control": {
                    "create_version": "/v1/version-control/version",
                    "get_versions": "/v1/version-control/versions/{building_id}/{floor_id}",
                    "create_branch": "/v1/version-control/branch",
                    "get_branches": "/v1/version-control/branches/{building_id}/{floor_id}",
                    "create_merge": "/v1/version-control/merge-request",
                    "add_annotation": "/v1/version-control/annotation",
                    "add_comment": "/v1/version-control/comment",
                    "branch_graph": "/v1/version-control/branch-graph/{building_id}/{floor_id}"
                }
            }
        },
        message="Arx SVG Parser Microservice is running"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
