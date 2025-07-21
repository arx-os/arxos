from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from svgx_engine.runtime.advanced_behavior_engine import AdvancedBehaviorEngine
from pydantic import ValidationError
import logging
from svgx_engine.services.websocket_interface import router as websocket_router
from svgx_engine.services.metrics_collector import metrics_collector
import time
from fastapi.responses import Response
from svgx_engine.services.error_handler import error_handler, ErrorSeverity, ErrorCategory
from svgx_engine.services.health_checker import health_checker
from svgx_engine.services.auth_middleware import (
    auth_middleware, get_current_user, require_read_permission, 
    require_write_permission, require_admin_permission, User
)
from svgx_engine.services.rate_limiter import rate_limit_middleware

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SVGX Engine API",
    description="Advanced behavior engine for SVG processing and collaboration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.middleware("http")(rate_limit_middleware)

# Initialize engine
engine = AdvancedBehaviorEngine()

# Mount WebSocket router
app.include_router(websocket_router)

# Authentication endpoints
@app.post("/auth/login", tags=["Authentication"], summary="Login and get access token")
async def login(request: Request):
    """
    Login with email and password to get access token.
    Request: { "email": "user@example.com", "password": "password" }
    Response: { "access_token": "...", "token_type": "bearer", "expires_in": 1800 }
    """
    start_time = time.time()
    try:
        data = await request.json()
        email = data.get("email")
        password = data.get("password")
        
        if not email or not password:
            error_result = error_handler.handle_error(
                ValueError("Missing email or password"),
                context={"data": data},
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.VALIDATION
            )
            return JSONResponse(error_result, status_code=400)
        
        # Authenticate user
        user = auth_middleware.authenticate_user(email, password)
        if not user:
            error_result = error_handler.handle_error(
                ValueError("Invalid credentials"),
                context={"email": email},
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.AUTHENTICATION
            )
            return JSONResponse(error_result, status_code=401)
        
        # Create access token
        token_data = {
            "sub": user.user_id,
            "username": user.username,
            "role": user.role
        }
        access_token = auth_middleware.create_access_token(token_data)
        
        processing_time = (time.time() - start_time) * 1000
        
        # Record metrics
        metrics_collector.record_performance_metric(
            operation="login",
            duration_ms=processing_time,
            success=True,
            additional_labels={"user_role": user.role}
        )
        
        # Log authentication event
        auth_middleware.log_auth_event("login", user.user_id, True, f"Role: {user.role}")
        
        return JSONResponse({
            "status": "success",
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 1800,  # 30 minutes
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        })
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        metrics_collector.record_performance_metric(
            operation="login",
            duration_ms=processing_time,
            success=False
        )
        
        error_result = error_handler.handle_error(
            e,
            context={"endpoint": "login", "data": data},
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.INTERNAL
        )
        return JSONResponse(error_result, status_code=500)

@app.post("/auth/refresh", tags=["Authentication"], summary="Refresh access token")
async def refresh_token(current_user: User = Depends(get_current_user)):
    """
    Refresh the current access token.
    Requires: Authorization header with current token
    Response: { "access_token": "...", "token_type": "bearer", "expires_in": 1800 }
    """
    start_time = time.time()
    try:
        # Create new token with same user data
        token_data = {
            "sub": current_user.user_id,
            "username": current_user.username,
            "role": current_user.role
        }
        access_token = auth_middleware.create_access_token(token_data)
        
        processing_time = (time.time() - start_time) * 1000
        
        # Record metrics
        metrics_collector.record_performance_metric(
            operation="refresh_token",
            duration_ms=processing_time,
            success=True,
            additional_labels={"user_role": current_user.role}
        )
        
        # Log authentication event
        auth_middleware.log_auth_event("refresh_token", current_user.user_id, True)
        
        return JSONResponse({
            "status": "success",
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 1800
        })
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        metrics_collector.record_performance_metric(
            operation="refresh_token",
            duration_ms=processing_time,
            success=False
        )
        
        error_result = error_handler.handle_error(
            e,
            context={"endpoint": "refresh_token", "user_id": current_user.user_id},
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.INTERNAL
        )
        return JSONResponse(error_result, status_code=500)

@app.get("/auth/me", tags=["Authentication"], summary="Get current user information")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get information about the currently authenticated user.
    Requires: Authorization header with valid token
    Response: { "user": { "user_id": "...", "username": "...", ... } }
    """
    return JSONResponse({
        "status": "success",
        "user": {
            "user_id": current_user.user_id,
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role,
            "permissions": current_user.permissions
        }
    })

# Root endpoint (no authentication required)
@app.get("/", tags=["System"], summary="API root")
async def root():
    """Get API root information."""
    return JSONResponse({
        "status": "success",
        "message": "SVGX Engine API",
        "version": "1.0.0",
        "endpoints": {
            "authentication": "/auth/",
            "runtime": "/runtime/",
            "health": "/health/",
            "metrics": "/metrics/",
            "websocket": "/runtime/events"
        }
    })

# Health check endpoints (no authentication required)
@app.get("/health/", tags=["System"], summary="System health check")
async def health_check():
    """Get comprehensive system health status."""
    start_time = time.time()
    try:
        health_data = health_checker.get_current_health()
        processing_time = (time.time() - start_time) * 1000
        
        # Record metrics
        metrics_collector.record_performance_metric(
            operation="health_check",
            duration_ms=processing_time,
            success=True
        )
        
        return JSONResponse(health_data)
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        metrics_collector.record_performance_metric(
            operation="health_check",
            duration_ms=processing_time,
            success=False
        )
        
        error_result = error_handler.handle_error(
            e,
            context={"endpoint": "health_check"},
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.INTERNAL
        )
        return JSONResponse(error_result, status_code=500)

@app.get("/health/summary/", tags=["System"], summary="Health summary")
async def health_summary():
    """Get health summary."""
    start_time = time.time()
    try:
        health_data = health_checker.get_current_health()
        summary = {
            "overall_status": health_data["overall_status"],
            "timestamp": health_data["timestamp"],
            "check_duration_ms": health_data["check_duration_ms"]
        }
        processing_time = (time.time() - start_time) * 1000
        
        metrics_collector.record_performance_metric(
            operation="health_summary",
            duration_ms=processing_time,
            success=True
        )
        
        return JSONResponse(summary)
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        metrics_collector.record_performance_metric(
            operation="health_summary",
            duration_ms=processing_time,
            success=False
        )
        
        error_result = error_handler.handle_error(
            e,
            context={"endpoint": "health_summary"},
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.INTERNAL
        )
        return JSONResponse(error_result, status_code=500)

@app.get("/health/history/", tags=["System"], summary="Health history")
async def health_history(hours: int = 24):
    """Get health history for the specified number of hours."""
    start_time = time.time()
    try:
        history = health_checker.get_health_history(hours)
        processing_time = (time.time() - start_time) * 1000
        
        metrics_collector.record_performance_metric(
            operation="health_history",
            duration_ms=processing_time,
            success=True
        )
        
        return JSONResponse({
            "status": "success",
            "history": history,
            "hours": hours
        })
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        metrics_collector.record_performance_metric(
            operation="health_history",
            duration_ms=processing_time,
            success=False
        )
        
        error_result = error_handler.handle_error(
            e,
            context={"endpoint": "health_history", "hours": hours},
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.INTERNAL
        )
        return JSONResponse(error_result, status_code=500)

# Metrics endpoints (read permission required)
@app.get("/metrics/", tags=["Monitoring"], summary="Get metrics in JSON format")
async def get_metrics(current_user: User = Depends(require_read_permission)):
    """Get metrics in JSON format."""
    start_time = time.time()
    try:
        metrics_data = metrics_collector.get_metrics_summary()
        processing_time = (time.time() - start_time) * 1000
        
        metrics_collector.record_performance_metric(
            operation="get_metrics",
            duration_ms=processing_time,
            success=True
        )
        
        return JSONResponse(metrics_data)
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        metrics_collector.record_performance_metric(
            operation="get_metrics",
            duration_ms=processing_time,
            success=False
        )
        
        error_result = error_handler.handle_error(
            e,
            context={"endpoint": "get_metrics"},
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.INTERNAL
        )
        return JSONResponse(error_result, status_code=500)

@app.get("/metrics/prometheus", tags=["Monitoring"], summary="Get metrics in Prometheus format")
async def get_prometheus_metrics(current_user: User = Depends(require_read_permission)):
    """Get metrics in Prometheus format."""
    start_time = time.time()
    try:
        prometheus_data = metrics_collector.export_prometheus_format()
        processing_time = (time.time() - start_time) * 1000
        
        metrics_collector.record_performance_metric(
            operation="get_prometheus_metrics",
            duration_ms=processing_time,
            success=True
        )
        
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(prometheus_data)
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        metrics_collector.record_performance_metric(
            operation="get_prometheus_metrics",
            duration_ms=processing_time,
            success=False
        )
        
        error_result = error_handler.handle_error(
            e,
            context={"endpoint": "get_prometheus_metrics"},
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.INTERNAL
        )
        return JSONResponse(error_result, status_code=500)

# Error statistics endpoint (admin permission required)
@app.get("/errors/stats/", tags=["Monitoring"], summary="Get error statistics")
async def get_error_stats(current_user: User = Depends(require_admin_permission)):
    """Get error statistics (admin only)."""
    start_time = time.time()
    try:
        error_stats = error_handler.get_error_statistics()
        processing_time = (time.time() - start_time) * 1000
        
        metrics_collector.record_performance_metric(
            operation="get_error_stats",
            duration_ms=processing_time,
            success=True
        )
        
        return JSONResponse(error_stats)
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        metrics_collector.record_performance_metric(
            operation="get_error_stats",
            duration_ms=processing_time,
            success=False
        )
        
        error_result = error_handler.handle_error(
            e,
            context={"endpoint": "get_error_stats"},
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.INTERNAL
        )
        return JSONResponse(error_result, status_code=500)

# Runtime endpoints (write permission required)
@app.post("/runtime/ui-event/", tags=["Runtime"], summary="Handle UI event")
async def handle_ui_event(request: Request, current_user: User = Depends(require_write_permission)):
    """Handle UI event with authentication and rate limiting."""
    start_time = time.time()
    try:
        data = await request.json()
        processing_time = (time.time() - start_time) * 1000
        
        # Add user context to event
        data["user_id"] = current_user.user_id
        data["session_id"] = getattr(request.state, 'session_id', 'unknown')
        
        # Record metrics
        metrics_collector.record_ui_event(
            event_type=data.get("event_type", "unknown"),
            processing_time_ms=processing_time,
            success=True,
            canvas_id=data.get("canvas_id"),
            user_id=current_user.user_id
        )
        
        feedback = engine.handle_ui_event(data)
        return JSONResponse(feedback)
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        metrics_collector.record_ui_event(
            event_type=data.get("event_type", "unknown") if 'data' in locals() else "unknown",
            processing_time_ms=processing_time,
            success=False,
            canvas_id=data.get("canvas_id") if 'data' in locals() else None,
            user_id=current_user.user_id
        )
        
        error_result = error_handler.handle_error(
            e,
            context={"endpoint": "handle_ui_event", "data": data if 'data' in locals() else None},
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.INTERNAL
        )
        return JSONResponse(error_result, status_code=500)

@app.post("/runtime/undo/", tags=["Runtime"], summary="Perform undo operation")
async def undo_operation(request: Request, current_user: User = Depends(require_write_permission)):
    """Perform undo operation for the specified canvas."""
    start_time = time.time()
    try:
        data = await request.json()
        canvas_id = data.get("canvas_id")
        
        if not canvas_id:
            error_result = error_handler.handle_error(
                ValueError("Missing canvas_id"),
                context={"data": data},
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.VALIDATION
            )
            return JSONResponse(error_result, status_code=400)
        
        feedback = engine.perform_undo(canvas_id)
        processing_time = (time.time() - start_time) * 1000
        
        # Record metrics
        metrics_collector.record_performance_metric(
            operation="undo",
            duration_ms=processing_time,
            success=True,
            additional_labels={"canvas_id": canvas_id, "user_id": current_user.user_id}
        )
        
        return JSONResponse(feedback)
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        metrics_collector.record_performance_metric(
            operation="undo",
            duration_ms=processing_time,
            success=False
        )
        
        error_result = error_handler.handle_error(
            e,
            context={"endpoint": "undo", "data": data if 'data' in locals() else None},
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.INTERNAL
        )
        return JSONResponse(error_result, status_code=500)

@app.post("/runtime/redo/", tags=["Runtime"], summary="Perform redo operation")
async def redo_operation(request: Request, current_user: User = Depends(require_write_permission)):
    """Perform redo operation for the specified canvas."""
    start_time = time.time()
    try:
        data = await request.json()
        canvas_id = data.get("canvas_id")
        
        if not canvas_id:
            error_result = error_handler.handle_error(
                ValueError("Missing canvas_id"),
                context={"data": data},
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.VALIDATION
            )
            return JSONResponse(error_result, status_code=400)
        
        feedback = engine.perform_redo(canvas_id)
        processing_time = (time.time() - start_time) * 1000
        
        # Record metrics
        metrics_collector.record_performance_metric(
            operation="redo",
            duration_ms=processing_time,
            success=True,
            additional_labels={"canvas_id": canvas_id, "user_id": current_user.user_id}
        )
        
        return JSONResponse(feedback)
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        metrics_collector.record_performance_metric(
            operation="redo",
            duration_ms=processing_time,
            success=False
        )
        
        error_result = error_handler.handle_error(
            e,
            context={"endpoint": "redo", "data": data if 'data' in locals() else None},
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.INTERNAL
        )
        return JSONResponse(error_result, status_code=500)

@app.post("/runtime/annotation/update/", tags=["Runtime"], summary="Update annotation")
async def update_annotation(request: Request, current_user: User = Depends(require_write_permission)):
    """Update an annotation for the specified target."""
    start_time = time.time()
    try:
        data = await request.json()
        canvas_id = data.get("canvas_id")
        target_id = data.get("target_id")
        annotation_index = data.get("annotation_index")
        new_data = data.get("new_data")
        
        if not all([canvas_id, target_id, annotation_index is not None, new_data]):
            error_result = error_handler.handle_error(
                ValueError("Missing required fields: canvas_id, target_id, annotation_index, new_data"),
                context={"data": data},
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.VALIDATION
            )
            return JSONResponse(error_result, status_code=400)
        
        feedback = engine.update_annotation(canvas_id, target_id, annotation_index, new_data)
        processing_time = (time.time() - start_time) * 1000
        
        # Record metrics
        metrics_collector.record_performance_metric(
            operation="update_annotation",
            duration_ms=processing_time,
            success=True,
            additional_labels={"canvas_id": canvas_id, "target_id": target_id, "user_id": current_user.user_id}
        )
        
        return JSONResponse(feedback)
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        metrics_collector.record_performance_metric(
            operation="update_annotation",
            duration_ms=processing_time,
            success=False
        )
        
        error_result = error_handler.handle_error(
            e,
            context={"endpoint": "update_annotation", "data": data if 'data' in locals() else None},
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.INTERNAL
        )
        return JSONResponse(error_result, status_code=500)

@app.post("/runtime/annotation/delete/", tags=["Runtime"], summary="Delete annotation")
async def delete_annotation(request: Request, current_user: User = Depends(require_write_permission)):
    """Delete an annotation for the specified target."""
    start_time = time.time()
    try:
        data = await request.json()
        canvas_id = data.get("canvas_id")
        target_id = data.get("target_id")
        annotation_index = data.get("annotation_index")
        
        if not all([canvas_id, target_id, annotation_index is not None]):
            error_result = error_handler.handle_error(
                ValueError("Missing required fields: canvas_id, target_id, annotation_index"),
                context={"data": data},
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.VALIDATION
            )
            return JSONResponse(error_result, status_code=400)
        
        feedback = engine.delete_annotation(canvas_id, target_id, annotation_index)
        processing_time = (time.time() - start_time) * 1000
        
        # Record metrics
        metrics_collector.record_performance_metric(
            operation="delete_annotation",
            duration_ms=processing_time,
            success=True,
            additional_labels={"canvas_id": canvas_id, "target_id": target_id, "user_id": current_user.user_id}
        )
        
        return JSONResponse(feedback)
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        metrics_collector.record_performance_metric(
            operation="delete_annotation",
            duration_ms=processing_time,
            success=False
        )
        
        error_result = error_handler.handle_error(
            e,
            context={"endpoint": "delete_annotation", "data": data if 'data' in locals() else None},
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.INTERNAL
        )
        return JSONResponse(error_result, status_code=500)

# Lock management endpoints (write permission required)
@app.post("/runtime/lock/", tags=["Collaboration"], summary="Acquire lock on object")
async def lock_object(request: Request, current_user: User = Depends(require_write_permission)):
    """Acquire a lock on an object for collaborative editing."""
    start_time = time.time()
    try:
        data = await request.json()
        canvas_id = data.get("canvas_id")
        object_id = data.get("object_id")
        session_id = data.get("session_id")
        
        if not all([canvas_id, object_id, session_id]):
            error_result = error_handler.handle_error(
                ValueError("Missing required fields: canvas_id, object_id, session_id"),
                context={"data": data},
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.VALIDATION
            )
            return JSONResponse(error_result, status_code=400)
        
        feedback = engine.lock_object(canvas_id, object_id, session_id, current_user.user_id)
        processing_time = (time.time() - start_time) * 1000
        
        # Record metrics
        metrics_collector.record_collaboration_metric(
            action="lock_object",
            canvas_id=canvas_id,
            user_id=current_user.user_id,
            object_id=object_id
        )
        metrics_collector.record_performance_metric(
            operation="lock_object",
            duration_ms=processing_time,
            success=feedback["status"] == "lock_acquired"
        )
        
        return JSONResponse(feedback)
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        metrics_collector.record_performance_metric(
            operation="lock_object",
            duration_ms=processing_time,
            success=False
        )
        
        error_result = error_handler.handle_error(
            e,
            context={"endpoint": "lock_object", "data": data if 'data' in locals() else None},
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.INTERNAL
        )
        return JSONResponse(error_result, status_code=500)

@app.post("/runtime/unlock/", tags=["Collaboration"], summary="Release lock on object")
async def unlock_object(request: Request, current_user: User = Depends(require_write_permission)):
    """Release a lock on an object."""
    start_time = time.time()
    try:
        data = await request.json()
        canvas_id = data.get("canvas_id")
        object_id = data.get("object_id")
        session_id = data.get("session_id")
        
        if not all([canvas_id, object_id, session_id]):
            error_result = error_handler.handle_error(
                ValueError("Missing required fields: canvas_id, object_id, session_id"),
                context={"data": data},
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.VALIDATION
            )
            return JSONResponse(error_result, status_code=400)
        
        feedback = engine.unlock_object(canvas_id, object_id, session_id)
        processing_time = (time.time() - start_time) * 1000
        
        # Record metrics
        metrics_collector.record_collaboration_metric(
            action="unlock_object",
            canvas_id=canvas_id,
            user_id=current_user.user_id,
            object_id=object_id
        )
        metrics_collector.record_performance_metric(
            operation="unlock_object",
            duration_ms=processing_time,
            success=feedback["status"] == "lock_released"
        )
        
        return JSONResponse(feedback)
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        metrics_collector.record_performance_metric(
            operation="unlock_object",
            duration_ms=processing_time,
            success=False
        )
        
        error_result = error_handler.handle_error(
            e,
            context={"endpoint": "unlock_object", "data": data if 'data' in locals() else None},
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.INTERNAL
        )
        return JSONResponse(error_result, status_code=500)

@app.get("/runtime/lock-status/", tags=["Collaboration"], summary="Get lock status")
async def get_lock_status(canvas_id: str, object_id: str, current_user: User = Depends(require_read_permission)):
    """Get the lock status for an object."""
    start_time = time.time()
    try:
        feedback = engine.get_lock_status(canvas_id, object_id)
        processing_time = (time.time() - start_time) * 1000
        
        # Record metrics
        metrics_collector.record_performance_metric(
            operation="get_lock_status",
            duration_ms=processing_time,
            success=True,
            additional_labels={"canvas_id": canvas_id, "object_id": object_id, "user_id": current_user.user_id}
        )
        
        return JSONResponse(feedback)
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        metrics_collector.record_performance_metric(
            operation="get_lock_status",
            duration_ms=processing_time,
            success=False
        )
        
        error_result = error_handler.handle_error(
            e,
            context={"endpoint": "get_lock_status", "canvas_id": canvas_id, "object_id": object_id},
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.INTERNAL
        )
        return JSONResponse(error_result, status_code=500)

# Lock expiry endpoints (admin permission required for configuration)
@app.post("/runtime/lock-timeout/", tags=["Collaboration"], summary="Set lock timeout duration")
async def set_lock_timeout_api(request: Request, current_user: User = Depends(require_admin_permission)):
    """
    Set the lock timeout duration in seconds.
    Request: { "timeout_seconds": 300 }
    Response: { "status": "success", "timeout_seconds": 300 }
    """
    start_time = time.time()
    try:
        data = await request.json()
        timeout_seconds = data.get("timeout_seconds")
        if not timeout_seconds or not isinstance(timeout_seconds, int) or timeout_seconds <= 0:
            error_result = error_handler.handle_error(
                ValueError("Invalid timeout_seconds: must be positive integer"),
                context={"data": data},
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.VALIDATION
            )
            return JSONResponse(error_result, status_code=400)
        
        engine.set_lock_timeout(timeout_seconds)
        processing_time = (time.time() - start_time) * 1000
        
        # Record metrics
        metrics_collector.record_performance_metric(
            operation="set_lock_timeout",
            duration_ms=processing_time,
            success=True,
            additional_labels={"user_id": current_user.user_id, "timeout_seconds": timeout_seconds}
        )
        
        return JSONResponse({
            "status": "success",
            "timeout_seconds": timeout_seconds,
            "message": f"Lock timeout set to {timeout_seconds} seconds"
        })
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        metrics_collector.record_performance_metric(
            operation="set_lock_timeout",
            duration_ms=processing_time,
            success=False
        )
        
        error_result = error_handler.handle_error(
            e,
            context={"endpoint": "set_lock_timeout", "data": data if 'data' in locals() else None},
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.INTERNAL
        )
        return JSONResponse(error_result, status_code=500)

@app.get("/runtime/lock-timeout/", tags=["Collaboration"], summary="Get current lock timeout duration")
async def get_lock_timeout_api(current_user: User = Depends(require_read_permission)):
    """
    Get the current lock timeout duration in seconds.
    Response: { "status": "success", "timeout_seconds": 300 }
    """
    start_time = time.time()
    try:
        timeout_seconds = engine.get_lock_timeout()
        processing_time = (time.time() - start_time) * 1000
        
        # Record metrics
        metrics_collector.record_performance_metric(
            operation="get_lock_timeout",
            duration_ms=processing_time,
            success=True
        )
        
        return JSONResponse({
            "status": "success",
            "timeout_seconds": timeout_seconds
        })
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        metrics_collector.record_performance_metric(
            operation="get_lock_timeout",
            duration_ms=processing_time,
            success=False
        )
        
        error_result = error_handler.handle_error(
            e,
            context={"endpoint": "get_lock_timeout"},
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.INTERNAL
        )
        return JSONResponse(error_result, status_code=500)

@app.post("/runtime/release-session-locks/", tags=["Collaboration"], summary="Release all locks for a session")
async def release_session_locks_api(request: Request, current_user: User = Depends(require_write_permission)):
    """
    Release all locks held by a session (e.g., on disconnect).
    Request: { "session_id": "session-123" }
    Response: { "status": "session_locks_released", "session_id": "session-123", "released_locks": [...], "count": 2 }
    """
    start_time = time.time()
    try:
        data = await request.json()
        session_id = data.get("session_id")
        if not session_id:
            error_result = error_handler.handle_error(
                ValueError("Missing session_id"),
                context={"data": data},
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.VALIDATION
            )
            return JSONResponse(error_result, status_code=400)
        
        result = engine.release_session_locks(session_id)
        processing_time = (time.time() - start_time) * 1000
        
        # Record metrics
        metrics_collector.record_collaboration_metric(
            action="release_session_locks",
            canvas_id="all",
            user_id=current_user.user_id
        )
        metrics_collector.record_performance_metric(
            operation="release_session_locks",
            duration_ms=processing_time,
            success=result["status"] == "session_locks_released"
        )
        
        return JSONResponse(result)
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        metrics_collector.record_performance_metric(
            operation="release_session_locks",
            duration_ms=processing_time,
            success=False
        )
        
        error_result = error_handler.handle_error(
            e,
            context={"endpoint": "release_session_locks", "data": data if 'data' in locals() else None},
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.INTERNAL
        )
        return JSONResponse(error_result, status_code=500)

@app.get("/runtime/all-locks/", tags=["Collaboration"], summary="Get all active locks")
async def get_all_locks_api(canvas_id: str = None, current_user: User = Depends(require_read_permission)):
    """
    Get all active locks, optionally filtered by canvas.
    Query: ?canvas_id=canvas-123 (optional)
    Response: { "canvas-123": { "object-456": { "session_id": "...", "user_id": "...", ... } } }
    """
    start_time = time.time()
    try:
        all_locks = engine.get_all_locks(canvas_id)
        processing_time = (time.time() - start_time) * 1000
        
        # Record metrics
        metrics_collector.record_performance_metric(
            operation="get_all_locks",
            duration_ms=processing_time,
            success=True,
            additional_labels={"canvas_filtered": str(canvas_id is not None), "user_id": current_user.user_id}
        )
        
        return JSONResponse({
            "status": "success",
            "all_locks": all_locks,
            "total_locks": sum(len(canvas_locks) for canvas_locks in all_locks.values())
        })
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        metrics_collector.record_performance_metric(
            operation="get_all_locks",
            duration_ms=processing_time,
            success=False
        )
        
        error_result = error_handler.handle_error(
            e,
            context={"endpoint": "get_all_locks", "canvas_id": canvas_id},
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.INTERNAL
        )
        return JSONResponse(error_result, status_code=500) 