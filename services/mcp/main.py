#!/usr/bin/env python3
"""
MCP Service - Main Application

This is the main FastAPI application for the MCP (Model Context Protocol) service.
It provides building code validation, real-time updates via WebSocket,
and comprehensive monitoring capabilities.
"""

import os
import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer

# Import our components
from models.mcp_models import BuildingModel, ValidationRequest, ValidationResponse
from validate.rule_engine import MCPRuleEngine
from websocket.websocket_routes import websocket_router
from auth.authentication import auth_manager, get_current_user, require_permission, Permission
from cache.redis_manager import redis_manager
from monitoring.prometheus_metrics import metrics_collector, MetricsMiddleware, ValidationMetrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Application lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting MCP Service...")
    
    # Initialize components
    try:
        # Test Redis connection
        redis_health = await redis_manager.health_check()
        if redis_health["status"] == "healthy":
            logger.info("✅ Redis connection established")
        else:
            logger.warning("⚠️ Redis connection issues: %s", redis_health.get("error", "Unknown"))
        
        # Initialize rule engine
        rule_engine = MCPRuleEngine()
        logger.info("✅ Rule engine initialized")
        
        # Store components in app state
        app.state.rule_engine = rule_engine
        app.state.redis_manager = redis_manager
        app.state.metrics_collector = metrics_collector
        
        logger.info("🚀 MCP Service started successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to start MCP Service: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down MCP Service...")
    
    try:
        # Close WebSocket connections
        from websocket.websocket_manager import websocket_manager
        await websocket_manager.close_all_connections()
        logger.info("✅ WebSocket connections closed")
        
        # Close Redis connections
        # Redis client will handle cleanup automatically
        
        logger.info("✅ MCP Service shutdown complete")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")

# Create FastAPI application
app = FastAPI(
    title="MCP Service",
    description="Model Context Protocol Service for Building Code Validation",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add metrics middleware
app = MetricsMiddleware(app)

# Security
security = HTTPBearer()

# Include routers
app.include_router(websocket_router, prefix="/api/v1")

# Include report routes
from report.report_routes import router as report_router
app.include_router(report_router, prefix="/api/v1")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Redis health
        redis_health = await redis_manager.health_check()
        
        # Check rule engine
        rule_engine = app.state.rule_engine
        
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "components": {
                "redis": redis_health,
                "rule_engine": "operational",
                "websocket": "operational"
            }
        }
        
        # Determine overall status
        if redis_health["status"] != "healthy":
            health_status["status"] = "degraded"
            health_status["issues"] = ["Redis connection issues"]
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
        )

# Metrics endpoint
@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    return metrics_collector.generate_metrics_response()

# Authentication endpoints
@app.post("/api/v1/auth/login")
async def login(username: str, password: str):
    """User login endpoint"""
    try:
        user = auth_manager.authenticate_user(username, password)
        
        if not user:
            metrics_collector.record_login_attempt("failed", "unknown")
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )
        
        # Create access token
        token_data = {
            "sub": user.user_id,
            "username": user.username,
            "roles": [role.value for role in user.roles],
            "permissions": [perm.value for perm in user.permissions]
        }
        
        access_token = auth_manager.create_access_token(token_data)
        refresh_token = auth_manager.create_refresh_token(token_data)
        
        metrics_collector.record_login_attempt("success", user.roles[0].value if user.roles else "unknown")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "roles": [role.value for role in user.roles]
            }
        }
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@app.post("/api/v1/auth/refresh")
async def refresh_token(refresh_token: str):
    """Refresh access token"""
    try:
        # Verify refresh token
        payload = auth_manager.verify_token(refresh_token)
        
        # Create new access token
        token_data = {
            "sub": payload.user_id,
            "username": payload.username,
            "roles": payload.roles,
            "permissions": payload.permissions
        }
        
        new_access_token = auth_manager.create_access_token(token_data)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=401, detail="Invalid refresh token")

# Validation endpoints
@app.post("/api/v1/validate", response_model=ValidationResponse)
async def validate_building(
    request: ValidationRequest,
    current_user = Depends(get_current_user)
):
    """Validate building model against applicable codes"""
    try:
        start_time = time.time()
        
        # Check permissions
        if not auth_manager.has_permission(current_user, Permission.READ_VALIDATION):
            raise HTTPException(
                status_code=403,
                detail="Permission denied: read_validation required"
            )
        
        # Check cache first
        cached_result = await redis_manager.get_cached_validation(request.building_model.building_id)
        
        if cached_result:
            # Return cached result
            metrics_collector.record_cache_operation("validation_lookup", "validation_result", "hit")
            logger.info(f"Returning cached validation for building {request.building_model.building_id}")
            return ValidationResponse(**cached_result)
        
        # Perform validation
        rule_engine = app.state.rule_engine
        
        # Auto-detect applicable codes if not provided
        mcp_files = request.mcp_files
        if not mcp_files:
            jurisdiction_info = rule_engine.get_jurisdiction_info(request.building_model)
            mcp_files = [f"mcp/{code}.json" for code in jurisdiction_info.get("applicable_codes", [])]
        
        # Run validation
        validation_report = rule_engine.validate_building_model(request.building_model, mcp_files)
        
        # Cache result
        await redis_manager.cache_validation(
            request.building_model.building_id,
            validation_report.dict()
        )
        
        # Record metrics
        duration = time.time() - start_time
        metrics = ValidationMetrics(
            building_id=request.building_model.building_id,
            jurisdiction="unknown",  # Could be extracted from building model
            total_rules=validation_report.total_rules,
            passed_rules=validation_report.total_rules - validation_report.total_violations,
            failed_rules=validation_report.total_violations,
            violations_count=validation_report.total_violations,
            warnings_count=validation_report.total_warnings,
            duration_seconds=duration,
            cache_hit=False,
            user_id=current_user.user_id
        )
        metrics_collector.record_validation(metrics)
        
        # Broadcast to WebSocket if real-time updates are enabled
        if hasattr(request, 'enable_realtime') and request.enable_realtime:
            from websocket.websocket_manager import websocket_manager
            await websocket_manager.broadcast_validation(
                request.building_model.building_id,
                validation_report.dict()
            )
        
        return validation_report
        
    except Exception as e:
        logger.error(f"Validation error: {e}")
        metrics_collector.record_validation_error("validation_failed", "unknown")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@app.get("/api/v1/validate/{building_id}")
async def get_validation_result(
    building_id: str,
    current_user = Depends(get_current_user)
):
    """Get cached validation result for a building"""
    try:
        # Check permissions
        if not auth_manager.has_permission(current_user, Permission.READ_VALIDATION):
            raise HTTPException(
                status_code=403,
                detail="Permission denied: read_validation required"
            )
        
        # Get cached result
        cached_result = await redis_manager.get_cached_validation(building_id)
        
        if not cached_result:
            raise HTTPException(
                status_code=404,
                detail="Validation result not found"
            )
        
        return cached_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting validation result: {e}")
        raise HTTPException(status_code=500, detail="Failed to get validation result")

# Jurisdiction endpoints
@app.get("/api/v1/jurisdiction/{building_id}")
async def get_jurisdiction_info(
    building_id: str,
    current_user = Depends(get_current_user)
):
    """Get jurisdiction information for a building"""
    try:
        # Check permissions
        if not auth_manager.has_permission(current_user, Permission.READ_BUILDING_MODELS):
            raise HTTPException(
                status_code=403,
                detail="Permission denied: read_building_models required"
            )
        
        # Get cached jurisdiction info
        cached_info = await redis_manager.get_cached_jurisdiction_match(building_id)
        
        if cached_info:
            return cached_info
        
        # Get from rule engine
        rule_engine = app.state.rule_engine
        
        # Create a minimal building model for jurisdiction lookup
        building_model = BuildingModel(
            building_id=building_id,
            building_name="Unknown",
            objects=[],
            metadata={}
        )
        
        jurisdiction_info = rule_engine.get_jurisdiction_info(building_model)
        
        # Cache the result
        await redis_manager.cache_jurisdiction_match(building_id, jurisdiction_info)
        
        return jurisdiction_info
        
    except Exception as e:
        logger.error(f"Error getting jurisdiction info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get jurisdiction info")

# Cache management endpoints (admin only)
@app.get("/api/v1/cache/stats")
async def get_cache_stats(current_user = Depends(require_permission(Permission.SYSTEM_ADMIN))):
    """Get cache statistics"""
    try:
        stats = await redis_manager.get_cache_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cache stats")

@app.delete("/api/v1/cache/{building_id}")
async def invalidate_building_cache(
    building_id: str,
    current_user = Depends(require_permission(Permission.SYSTEM_ADMIN))
):
    """Invalidate cache for a building"""
    try:
        success = await redis_manager.invalidate_building_cache(building_id)
        if success:
            return {"message": f"Cache invalidated for building {building_id}"}
        else:
            raise HTTPException(status_code=404, detail="Building cache not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to invalidate cache")

@app.delete("/api/v1/cache")
async def clear_all_cache(current_user = Depends(require_permission(Permission.SYSTEM_ADMIN))):
    """Clear all cache"""
    try:
        success = await redis_manager.clear_all_cache()
        if success:
            return {"message": "All cache cleared"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear cache")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")

# Monitoring endpoints
@app.get("/api/v1/monitoring/metrics")
async def get_metrics_summary(current_user = Depends(require_permission(Permission.SYSTEM_ADMIN))):
    """Get metrics summary"""
    try:
        summary = metrics_collector.get_metrics_summary()
        return summary
    except Exception as e:
        logger.error(f"Error getting metrics summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics summary")

@app.get("/api/v1/monitoring/redis")
async def get_redis_metrics(current_user = Depends(require_permission(Permission.SYSTEM_ADMIN))):
    """Get Redis performance metrics"""
    try:
        metrics = await redis_manager.get_performance_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error getting Redis metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Redis metrics")

# User management endpoints (admin only)
@app.get("/api/v1/users")
async def get_users(current_user = Depends(require_permission(Permission.MANAGE_USERS))):
    """Get all users"""
    try:
        users = auth_manager.get_all_users()
        return {
            "users": [
                {
                    "user_id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "roles": [role.value for role in user.roles],
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "last_login": user.last_login.isoformat() if user.last_login else None
                }
                for user in users
            ]
        }
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(status_code=500, detail="Failed to get users")

@app.get("/api/v1/users/stats")
async def get_user_stats(current_user = Depends(require_permission(Permission.MANAGE_USERS))):
    """Get user statistics"""
    try:
        stats = auth_manager.get_user_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user stats")

# WebSocket status endpoints
@app.get("/api/v1/websocket/status")
async def get_websocket_status(current_user = Depends(get_current_user)):
    """Get WebSocket connection status"""
    try:
        from websocket.websocket_manager import websocket_manager
        stats = websocket_manager.get_connection_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting WebSocket status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get WebSocket status")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "MCP Service",
        "version": "1.0.0",
        "description": "Model Context Protocol Service for Building Code Validation",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "api_docs": "/docs",
            "validation": "/api/v1/validate",
            "websocket": "/api/v1/ws/validation/{building_id}",
            "authentication": "/api/v1/auth/login"
        }
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found", "path": str(request.url)}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8001"))
    reload = os.getenv("MCP_RELOAD", "false").lower() == "true"
    
    logger.info(f"Starting MCP Service on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    ) 