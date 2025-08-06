#!/usr/bin/env python3
"""
Enhanced MCP Service - Main Application

This is the enhanced FastAPI application for the MCP (Model Context Protocol) service
with advanced features including:
- Performance optimization with advanced caching
- Rate limiting and API protection
- Webhook system for real-time updates
- Enterprise-grade security features
- Comprehensive monitoring and analytics
"""

import os
import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer

# Import our enhanced components
from models.mcp_models import BuildingModel, ValidationRequest, ValidationResponse
from validate.rule_engine import MCPRuleEngine
from websocket.websocket_routes import websocket_router
from auth.authentication import (
    auth_manager,
    get_current_user,
    require_permission,
    Permission,
)
from cache.redis_manager import redis_manager
from cache.advanced_cache_manager import initialize_advanced_cache, get_advanced_cache
from api.rate_limiter import get_rate_limiter, rate_limit_manager
from api.webhook_manager import (
    webhook_manager,
    trigger_validation_event,
    WebhookEventType,
)
from security.enterprise_security import (
    security_monitor,
    audit_logger,
    encryption_manager,
    security_headers,
    input_validator,
    require_security_audit,
    validate_and_sanitize_input,
    AuditEventType,
)
from monitoring.prometheus_metrics import (
    metrics_collector,
    MetricsMiddleware,
    ValidationMetrics,
)
from knowledge.knowledge_routes import router as knowledge_router

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Application lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Enhanced application lifespan manager"""
    # Startup
    logger.info("Starting Enhanced MCP Service...")

    # Initialize components
    try:
        # Test Redis connection
        redis_health = await redis_manager.health_check()
        if redis_health["status"] == "healthy":
            logger.info("✅ Redis connection established")
        else:
            logger.warning(
                "⚠️ Redis connection issues: %s", redis_health.get("error", "Unknown")
            )

        # Initialize advanced cache manager
        advanced_cache = await initialize_advanced_cache(redis_manager)
        logger.info("✅ Advanced cache manager initialized")

        # Initialize rule engine
        rule_engine = MCPRuleEngine()
        logger.info("✅ Rule engine initialized")

        # Initialize webhook manager
        logger.info("✅ Webhook manager initialized")

        # Store components in app state
        app.state.rule_engine = rule_engine
        app.state.redis_manager = redis_manager
        app.state.advanced_cache = advanced_cache
        app.state.metrics_collector = metrics_collector
        app.state.webhook_manager = webhook_manager
        app.state.security_monitor = security_monitor

        logger.info("🚀 Enhanced MCP Service started successfully")

    except Exception as e:
        logger.error(f"❌ Failed to start Enhanced MCP Service: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Enhanced MCP Service...")

    try:
        # Close WebSocket connections
        from websocket.websocket_manager import websocket_manager

        await websocket_manager.close_all_connections()
        logger.info("✅ WebSocket connections closed")

        # Shutdown advanced cache manager
        advanced_cache = await get_advanced_cache()
        await advanced_cache.shutdown()
        logger.info("✅ Advanced cache manager shutdown")

        # Shutdown webhook manager
        await webhook_manager.shutdown()
        logger.info("✅ Webhook manager shutdown")

        logger.info("✅ Enhanced MCP Service shutdown complete")

    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


# Create enhanced FastAPI application
app = FastAPI(
    title="Enhanced MCP Service",
    description="Model Context Protocol Service with Advanced Features",
    version="2.0.0",
    lifespan=lifespan,
)

# Add enhanced middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(MetricsMiddleware)


# Security middleware
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Enhanced security middleware"""
    # Check if IP is blocked
    if security_monitor.is_ip_blocked(request.client.host):
        return JSONResponse(status_code=403, content={"error": "IP address blocked"})

    # Record request for monitoring
    security_monitor.record_request(request.client.host)

    # Analyze request for threats
    analysis = security_monitor.analyze_request(request, "anonymous")
    if analysis["risk_score"] > 70:
        # Block high-risk requests
        security_monitor.block_ip(request.client.host, 3600)
        return JSONResponse(
            status_code=403,
            content={"error": "Request blocked due to security concerns"},
        )

    # Add security headers
    response = await call_next(request)
    for name, value in security_headers.get_headers().items():
        response.headers[name] = value

    return response


# Enhanced health check
@app.get("/health")
async def health_check():
    """Enhanced health check with detailed status"""
    try:
        # Check Redis
        redis_health = await redis_manager.health_check()

        # Check advanced cache
        advanced_cache = await get_advanced_cache()
        cache_report = await advanced_cache.get_cache_performance_report()

        # Check webhook manager
        webhook_stats = webhook_manager.get_delivery_stats()

        # Check security monitor
        security_report = audit_logger.get_security_report()

        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "2.0.0",
            "components": {
                "redis": redis_health,
                "advanced_cache": cache_report,
                "webhooks": webhook_stats,
                "security": security_report,
            },
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e), "timestamp": time.time()}


# Enhanced metrics endpoint
@app.get("/metrics")
async def metrics_endpoint():
    """Enhanced metrics endpoint"""
    advanced_cache = await get_advanced_cache()
    cache_report = await advanced_cache.get_cache_performance_report()

    return {
        "cache_performance": cache_report,
        "rate_limiting": rate_limit_manager.get_metrics(),
        "webhook_delivery": webhook_manager.get_delivery_stats(),
        "security_audit": audit_logger.get_security_report(),
    }


# Enhanced authentication endpoints
@app.post("/api/v1/auth/login")
@require_security_audit(AuditEventType.LOGIN, "auth", "login")
async def login(request: Request, username: str, password: str):
    """Enhanced login with security monitoring"""
    try:
        # Validate input
        is_valid, error_msg = input_validator.validate_input("username", username)
        if not is_valid:
            raise HTTPException(
                status_code=400, detail=f"Invalid username: {error_msg}"
            )

        # Authenticate user
        user = auth_manager.authenticate_user(username, password)
        if not user:
            # Log failed login attempt
            audit_logger.log_event(
                AuditEvent(
                    id=f"login_failed_{int(time.time())}",
                    event_type=AuditEventType.LOGIN,
                    user_id=username,
                    resource="auth",
                    action="login",
                    details={"status": "failed", "reason": "invalid_credentials"},
                    ip_address=request.client.host,
                    user_agent=request.headers.get("user-agent", ""),
                    success=False,
                )
            )
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Create tokens
        access_token = auth_manager.create_access_token(
            {
                "sub": user.user_id,
                "username": user.username,
                "roles": [role.value for role in user.roles],
                "permissions": [perm.value for perm in user.permissions],
            }
        )

        refresh_token = auth_manager.create_refresh_token(
            {"sub": user.user_id, "username": user.username}
        )

        # Log successful login
        audit_logger.log_event(
            AuditEvent(
                id=f"login_success_{int(time.time())}",
                event_type=AuditEventType.LOGIN,
                user_id=user.user_id,
                resource="auth",
                action="login",
                details={
                    "status": "success",
                    "roles": [role.value for role in user.roles],
                },
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent", ""),
            )
        )

        # Trigger webhook event
        await trigger_user_event(
            WebhookEventType.USER_LOGIN,
            user.user_id,
            {
                "username": user.username,
                "roles": [role.value for role in user.roles],
                "ip_address": request.client.host,
            },
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "roles": [role.value for role in user.roles],
            },
        }

    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Enhanced validation endpoint with advanced features
@app.post("/api/v1/validate", response_model=ValidationResponse)
@require_security_audit(AuditEventType.DATA_MODIFICATION, "validation", "create")
@validate_and_sanitize_input("building_id")
async def validate_building(
    request: Request,
    validation_request: ValidationRequest,
    current_user=Depends(get_current_user),
):
    """Enhanced validation with advanced caching and webhooks"""
    try:
        building_id = validation_request.building_id

        # Check advanced cache first
        advanced_cache = await get_advanced_cache()
        cached_result = await advanced_cache.get_cached_data(
            f"validation:{building_id}", "validation_result"
        )

        if cached_result:
            # Return cached result
            return ValidationResponse(**cached_result)

        # Trigger webhook for validation start
        await trigger_validation_event(
            WebhookEventType.VALIDATION_STARTED,
            building_id,
            {"user_id": current_user.user_id, "timestamp": time.time()},
        )

        # Perform validation
        rule_engine = request.app.state.rule_engine
        validation_result = rule_engine.validate_building(
            validation_request.building_model
        )

        # Create response
        response = ValidationResponse(
            building_id=building_id,
            validation_result=validation_result,
            timestamp=time.time(),
            validated_by=current_user.user_id,
        )

        # Cache the result with high priority
        await advanced_cache.set_cached_data(
            f"validation:{building_id}",
            response.dict(),
            "validation_result",
            priority=0.9,
        )

        # Trigger webhook for validation completion
        await trigger_validation_event(
            WebhookEventType.VALIDATION_COMPLETED,
            building_id,
            {
                "user_id": current_user.user_id,
                "result": validation_result,
                "timestamp": time.time(),
            },
        )

        return response

    except Exception as e:
        logger.error(f"Validation error: {e}")

        # Trigger webhook for validation failure
        await trigger_validation_event(
            WebhookEventType.VALIDATION_FAILED,
            validation_request.building_id,
            {
                "user_id": current_user.user_id,
                "error": str(e),
                "timestamp": time.time(),
            },
        )

        raise HTTPException(status_code=500, detail="Validation failed")


# Enhanced webhook management endpoints
@app.post("/api/v1/webhooks/register")
async def register_webhook(
    request: Request,
    endpoint_data: dict,
    current_user=Depends(require_permission(Permission.SYSTEM_ADMIN)),
):
    """Register a new webhook endpoint"""
    try:
        from api.webhook_manager import WebhookEndpoint, WebhookEventType

        endpoint = WebhookEndpoint(
            id=endpoint_data["id"],
            url=endpoint_data["url"],
            secret=endpoint_data["secret"],
            events=[WebhookEventType(event) for event in endpoint_data["events"]],
        )

        success = await webhook_manager.register_endpoint(endpoint)

        if success:
            return {"status": "success", "message": "Webhook endpoint registered"}
        else:
            raise HTTPException(status_code=400, detail="Failed to register webhook")

    except Exception as e:
        logger.error(f"Webhook registration error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/webhooks/stats")
async def get_webhook_stats(
    current_user=Depends(require_permission(Permission.SYSTEM_ADMIN)),
):
    """Get webhook delivery statistics"""
    return webhook_manager.get_delivery_stats()


# Enhanced cache management endpoints
@app.get("/api/v1/cache/performance")
async def get_cache_performance(
    current_user=Depends(require_permission(Permission.SYSTEM_ADMIN)),
):
    """Get advanced cache performance report"""
    advanced_cache = await get_advanced_cache()
    return await advanced_cache.get_cache_performance_report()


@app.post("/api/v1/cache/optimize")
async def optimize_cache(
    current_user=Depends(require_permission(Permission.SYSTEM_ADMIN)),
):
    """Optimize cache based on performance metrics"""
    advanced_cache = await get_advanced_cache()
    optimizations = await advanced_cache.optimize_cache()
    return {"optimizations": optimizations}


# Enhanced security endpoints
@app.get("/api/v1/security/audit")
async def get_security_audit(
    user_id: str = None,
    event_type: str = None,
    current_user=Depends(require_permission(Permission.SYSTEM_ADMIN)),
):
    """Get security audit events"""
    events = audit_logger.get_events(
        user_id=user_id, event_type=AuditEventType(event_type) if event_type else None
    )

    return {
        "events": [
            {
                "id": event.id,
                "event_type": event.event_type.value,
                "user_id": event.user_id,
                "resource": event.resource,
                "action": event.action,
                "timestamp": event.timestamp.isoformat(),
                "success": event.success,
            }
            for event in events
        ]
    }


@app.get("/api/v1/security/report")
async def get_security_report(
    current_user=Depends(require_permission(Permission.SYSTEM_ADMIN)),
):
    """Get comprehensive security report"""
    return audit_logger.get_security_report()


# Enhanced rate limiting endpoints
@app.get("/api/v1/rate-limits/config")
async def get_rate_limit_config(
    current_user=Depends(require_permission(Permission.SYSTEM_ADMIN)),
):
    """Get rate limiting configuration"""
    return {
        "configurations": {
            name: {
                "requests_per_minute": config.requests_per_minute,
                "requests_per_hour": config.requests_per_hour,
                "strategy": config.strategy.value,
            }
            for name, config in rate_limit_manager.configs.items()
        }
    }


@app.get("/api/v1/rate-limits/metrics")
async def get_rate_limit_metrics(
    current_user=Depends(require_permission(Permission.SYSTEM_ADMIN)),
):
    """Get rate limiting metrics"""
    return rate_limit_manager.get_metrics()


# Include existing routers
app.include_router(websocket_router, prefix="/ws", tags=["websocket"])
app.include_router(knowledge_router, prefix="/api/v1/knowledge", tags=["knowledge"])


# Enhanced root endpoint
@app.get("/")
async def root():
    """Enhanced root endpoint with service information"""
    return {
        "service": "Enhanced MCP Service",
        "version": "2.0.0",
        "description": "Model Context Protocol Service with Advanced Features",
        "features": [
            "Advanced caching with predictive optimization",
            "Rate limiting with multiple strategies",
            "Webhook system for real-time updates",
            "Enterprise-grade security features",
            "Comprehensive monitoring and analytics",
        ],
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "docs": "/docs",
            "validation": "/api/v1/validate",
            "webhooks": "/api/v1/webhooks",
            "cache": "/api/v1/cache",
            "security": "/api/v1/security",
        },
    }


# Enhanced error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Enhanced 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not found",
            "path": request.url.path,
            "method": request.method,
            "timestamp": time.time(),
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    """Enhanced 500 handler"""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "timestamp": time.time()},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
