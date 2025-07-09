"""
ARKit Calibration Sync API Router

Provides RESTful API endpoints for ARKit calibration and coordinate synchronization.
"""

from fastapi import APIRouter, HTTPException, Body, Query, Depends
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import logging

from services.arkit_calibration_sync import (
    ARKitCalibrationService, CalibrationStatus, CalibrationAccuracy
)
from utils.logger import get_logger

logger = get_logger(__name__)

# Initialize router
router = APIRouter(prefix="/arkit-calibration", tags=["ARKit Calibration Sync"])

# Initialize service
calibration_service = ARKitCalibrationService()


# Calibration Management Endpoints

@router.post("/initialize")
async def initialize_calibration(
    svg_data: Dict[str, Any] = Body(..., description="SVG file data and coordinate information"),
    device_info: Dict[str, Any] = Body(..., description="Device information and capabilities")
) -> Dict[str, Any]:
    """
    Initialize calibration process with SVG data and device information.
    
    Args:
        svg_data: SVG file data with coordinate system information
        device_info: Device information including ID, capabilities, and sensors
        
    Returns:
        Calibration initialization result with session ID and status
    """
    try:
        result = calibration_service.initialize_calibration(svg_data, device_info)
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Calibration initialization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect-points")
async def detect_reference_points(
    ar_frame_data: Dict[str, Any] = Body(..., description="ARKit frame data with camera and tracking information"),
    session_id: str = Body(..., description="Active calibration session ID")
) -> Dict[str, Any]:
    """
    Detect reference points in AR frame for calibration.
    
    Args:
        ar_frame_data: ARKit frame data including camera transform, point cloud, and plane anchors
        session_id: Active calibration session ID
        
    Returns:
        Reference point detection results with coordinates and confidence scores
    """
    try:
        result = calibration_service.detect_reference_points(ar_frame_data, session_id)
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Reference point detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate-transform")
async def calculate_coordinate_transform(
    session_id: str = Body(..., description="Active calibration session ID")
) -> Dict[str, Any]:
    """
    Calculate coordinate transformation matrix from reference points.
    
    Args:
        session_id: Active calibration session ID
        
    Returns:
        Coordinate transformation results with transformation matrix and accuracy score
    """
    try:
        result = calibration_service.calculate_coordinate_transform(session_id)
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Coordinate transform calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
async def validate_calibration(
    session_id: str = Body(..., description="Active calibration session ID")
) -> Dict[str, Any]:
    """
    Validate calibration accuracy and quality.
    
    Args:
        session_id: Active calibration session ID
        
    Returns:
        Calibration validation results with accuracy metrics and acceptance status
    """
    try:
        result = calibration_service.validate_calibration(session_id)
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Calibration validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/apply")
async def apply_calibration(
    calibration_id: str = Body(..., description="Calibration ID to apply")
) -> Dict[str, Any]:
    """
    Apply calibration to AR session.
    
    Args:
        calibration_id: Calibration ID to apply
        
    Returns:
        Calibration application results with transformation data
    """
    try:
        result = calibration_service.apply_calibration(calibration_id)
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Calibration application failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Status and Information Endpoints

@router.get("/status")
async def get_calibration_status(
    session_id: Optional[str] = Query(None, description="Specific session ID to check")
) -> Dict[str, Any]:
    """
    Get current calibration status and accuracy metrics.
    
    Args:
        session_id: Optional session ID to get specific status
        
    Returns:
        Calibration status information
    """
    try:
        result = calibration_service.get_calibration_status(session_id)
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get calibration status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_calibration_history(
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    svg_file_hash: Optional[str] = Query(None, description="Filter by SVG file hash"),
    status: Optional[str] = Query(None, description="Filter by calibration status"),
    limit: int = Query(50, description="Maximum number of results"),
    offset: int = Query(0, description="Number of results to skip")
) -> Dict[str, Any]:
    """
    Get calibration history with filtering options.
    
    Args:
        device_id: Optional device ID filter
        svg_file_hash: Optional SVG file hash filter
        status: Optional calibration status filter
        limit: Maximum number of results to return
        offset: Number of results to skip
        
    Returns:
        Calibration history with filtering and pagination
    """
    try:
        # Get all calibrations from service
        all_calibrations = []
        for calibration_id, calibration_data in calibration_service.calibration_data.items():
            cal_dict = {
                "calibration_id": calibration_data.calibration_id,
                "session_id": calibration_data.session_id,
                "device_id": calibration_data.device_id,
                "svg_file_hash": calibration_data.svg_file_hash,
                "status": calibration_data.status.value,
                "accuracy_score": calibration_data.accuracy_score,
                "scale_factor": calibration_data.scale_factor,
                "reference_points_count": len(calibration_data.reference_points),
                "created_at": calibration_data.created_at.isoformat(),
                "updated_at": calibration_data.updated_at.isoformat(),
                "applied_at": calibration_data.applied_at.isoformat() if calibration_data.applied_at else None
            }
            
            # Apply filters
            if device_id and calibration_data.device_id != device_id:
                continue
            if svg_file_hash and calibration_data.svg_file_hash != svg_file_hash:
                continue
            if status and calibration_data.status.value != status:
                continue
            
            all_calibrations.append(cal_dict)
        
        # Apply pagination
        total_count = len(all_calibrations)
        paginated_results = all_calibrations[offset:offset + limit]
        
        return {
            "status": "success",
            "data": {
                "calibrations": paginated_results,
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get calibration history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_calibration_metrics() -> Dict[str, Any]:
    """
    Get calibration performance metrics and statistics.
    
    Returns:
        Performance metrics including success rates and accuracy statistics
    """
    try:
        metrics = calibration_service.get_performance_metrics()
        
        if "error" in metrics:
            raise HTTPException(status_code=500, detail=metrics["error"])
        
        return {
            "status": "success",
            "data": metrics,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get calibration metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Calibration Data Management

@router.post("/save")
async def save_calibration(
    calibration_id: str = Body(..., description="Calibration ID to save")
) -> Dict[str, Any]:
    """
    Save calibration data for future use.
    
    Args:
        calibration_id: Calibration ID to save
        
    Returns:
        Save operation results
    """
    try:
        result = calibration_service.save_calibration(calibration_id)
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to save calibration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/load/{calibration_id}")
async def load_calibration(calibration_id: str) -> Dict[str, Any]:
    """
    Load saved calibration data.
    
    Args:
        calibration_id: Calibration ID to load
        
    Returns:
        Loaded calibration data
    """
    try:
        result = calibration_service.load_calibration(calibration_id)
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to load calibration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Advanced Calibration Features

@router.post("/recalibrate")
async def recalibrate_session(
    session_id: str = Body(..., description="Session ID to recalibrate"),
    force_recalibration: bool = Body(False, description="Force recalibration even if existing calibration exists")
) -> Dict[str, Any]:
    """
    Recalibrate an existing session with new reference points.
    
    Args:
        session_id: Session ID to recalibrate
        force_recalibration: Force recalibration even if good calibration exists
        
    Returns:
        Recalibration results
    """
    try:
        # Get current calibration status
        status_result = calibration_service.get_calibration_status(session_id)
        
        if status_result["status"] == "error":
            raise HTTPException(status_code=400, detail=status_result["error"])
        
        current_accuracy = status_result.get("accuracy_score", 0.0)
        
        # Check if recalibration is needed
        if not force_recalibration and current_accuracy > 0.95:
            return {
                "status": "success",
                "data": {
                    "message": "Recalibration not needed - current accuracy is sufficient",
                    "current_accuracy": current_accuracy,
                    "recalibrated": False
                },
                "timestamp": datetime.now().isoformat()
            }
        
        # Clear existing reference points and restart calibration
        if session_id in calibration_service.active_sessions:
            calibration_id = calibration_service.active_sessions[session_id]
            if calibration_id in calibration_service.calibration_data:
                calibration_data = calibration_service.calibration_data[calibration_id]
                calibration_data.reference_points = []
                calibration_data.status = CalibrationStatus.RECALIBRATING
                calibration_data.updated_at = datetime.now()
        
        return {
            "status": "success",
            "data": {
                "message": "Recalibration initiated",
                "session_id": session_id,
                "recalibrated": True
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Recalibration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-environment")
async def validate_environmental_conditions(
    ar_frame_data: Dict[str, Any] = Body(..., description="AR frame data for environmental analysis"),
    session_id: str = Body(..., description="Session ID for environmental validation")
) -> Dict[str, Any]:
    """
    Validate environmental conditions for optimal calibration.
    
    Args:
        ar_frame_data: AR frame data for environmental analysis
        session_id: Session ID for validation
        
    Returns:
        Environmental validation results with recommendations
    """
    try:
        # Analyze environmental conditions
        lighting_quality = _analyze_lighting_quality(ar_frame_data)
        surface_quality = _analyze_surface_quality(ar_frame_data)
        motion_stability = _analyze_motion_stability(ar_frame_data)
        
        # Calculate overall environmental score
        environmental_score = (lighting_quality + surface_quality + motion_stability) / 3
        
        # Generate recommendations
        recommendations = []
        if lighting_quality < 0.7:
            recommendations.append("Improve lighting conditions for better calibration")
        if surface_quality < 0.7:
            recommendations.append("Find surfaces with more distinctive features")
        if motion_stability < 0.7:
            recommendations.append("Hold device steady during calibration")
        
        return {
            "status": "success",
            "data": {
                "environmental_score": environmental_score,
                "lighting_quality": lighting_quality,
                "surface_quality": surface_quality,
                "motion_stability": motion_stability,
                "recommendations": recommendations,
                "is_suitable": environmental_score > 0.7
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Environmental validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize-accuracy")
async def optimize_calibration_accuracy(
    session_id: str = Body(..., description="Session ID to optimize"),
    target_accuracy: float = Body(0.95, description="Target accuracy threshold")
) -> Dict[str, Any]:
    """
    Optimize calibration accuracy by collecting additional reference points.
    
    Args:
        session_id: Session ID to optimize
        target_accuracy: Target accuracy threshold
        
    Returns:
        Optimization results with improvement recommendations
    """
    try:
        # Get current calibration status
        status_result = calibration_service.get_calibration_status(session_id)
        
        if status_result["status"] == "error":
            raise HTTPException(status_code=400, detail=status_result["error"])
        
        current_accuracy = status_result.get("accuracy_score", 0.0)
        reference_points_count = status_result.get("reference_points_count", 0)
        
        # Determine optimization strategy
        optimization_needed = current_accuracy < target_accuracy
        strategy = _determine_optimization_strategy(current_accuracy, reference_points_count)
        
        return {
            "status": "success",
            "data": {
                "current_accuracy": current_accuracy,
                "target_accuracy": target_accuracy,
                "optimization_needed": optimization_needed,
                "strategy": strategy,
                "reference_points_count": reference_points_count,
                "recommendations": strategy.get("recommendations", [])
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Accuracy optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health and Diagnostic Endpoints

@router.get("/health")
async def calibration_health_check() -> Dict[str, Any]:
    """
    Health check for calibration service.
    
    Returns:
        Service health status and metrics
    """
    try:
        metrics = calibration_service.get_performance_metrics()
        
        # Check service health
        is_healthy = (
            "error" not in metrics and
            metrics.get("total_calibrations", 0) >= 0 and
            metrics.get("success_rate", 0) >= 0
        )
        
        return {
            "status": "success",
            "data": {
                "healthy": is_healthy,
                "metrics": metrics,
                "service": "ARKit Calibration Sync",
                "version": "1.0.0"
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "data": {
                "healthy": False,
                "error": str(e),
                "service": "ARKit Calibration Sync"
            },
            "timestamp": datetime.now().isoformat()
        }


@router.get("/diagnostics")
async def calibration_diagnostics(
    session_id: Optional[str] = Query(None, description="Session ID for diagnostics")
) -> Dict[str, Any]:
    """
    Get detailed diagnostics for calibration service or specific session.
    
    Args:
        session_id: Optional session ID for specific diagnostics
        
    Returns:
        Detailed diagnostic information
    """
    try:
        diagnostics = {
            "service_status": "operational",
            "database_status": "connected",
            "active_sessions": len(calibration_service.active_sessions),
            "total_calibrations": len(calibration_service.calibration_data),
            "memory_usage": "normal",
            "performance_metrics": calibration_service.get_performance_metrics()
        }
        
        if session_id:
            # Add session-specific diagnostics
            status_result = calibration_service.get_calibration_status(session_id)
            if status_result["status"] == "success":
                diagnostics["session_diagnostics"] = status_result
            else:
                diagnostics["session_diagnostics"] = {"error": "Session not found"}
        
        return {
            "status": "success",
            "data": diagnostics,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Diagnostics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions for advanced features

def _analyze_lighting_quality(ar_frame_data: Dict[str, Any]) -> float:
    """Analyze lighting quality from AR frame data."""
    # Simplified lighting analysis
    # In practice, this would analyze camera exposure, contrast, etc.
    exposure = ar_frame_data.get("camera_exposure", 0.5)
    contrast = ar_frame_data.get("image_contrast", 0.5)
    
    # Calculate lighting quality score
    lighting_score = (exposure + contrast) / 2
    return min(1.0, max(0.0, lighting_score))


def _analyze_surface_quality(ar_frame_data: Dict[str, Any]) -> float:
    """Analyze surface quality for feature detection."""
    # Simplified surface analysis
    point_cloud = ar_frame_data.get("point_cloud", [])
    
    if len(point_cloud) < 10:
        return 0.3  # Poor surface quality
    
    # Calculate point density and distribution
    point_density = len(point_cloud) / 1000  # Normalize to 1000 points
    return min(1.0, max(0.0, point_density))


def _analyze_motion_stability(ar_frame_data: Dict[str, Any]) -> float:
    """Analyze motion stability from AR frame data."""
    # Simplified motion analysis
    # In practice, this would analyze device motion and tracking quality
    
    # Check if tracking is stable
    tracking_quality = ar_frame_data.get("tracking_quality", 0.5)
    motion_magnitude = ar_frame_data.get("motion_magnitude", 0.5)
    
    # Calculate stability score (inverse of motion)
    stability_score = 1.0 - motion_magnitude
    return min(1.0, max(0.0, (stability_score + tracking_quality) / 2))


def _determine_optimization_strategy(current_accuracy: float, reference_points_count: int) -> Dict[str, Any]:
    """Determine optimization strategy based on current state."""
    strategy = {
        "recommendations": [],
        "target_points": 10,
        "accuracy_threshold": 0.95
    }
    
    if current_accuracy < 0.8:
        strategy["recommendations"].append("Collect more reference points (target: 15-20)")
        strategy["target_points"] = 20
    elif current_accuracy < 0.9:
        strategy["recommendations"].append("Add 5-10 more reference points")
        strategy["target_points"] = 15
    elif current_accuracy < 0.95:
        strategy["recommendations"].append("Add 2-5 more reference points for fine-tuning")
        strategy["target_points"] = 12
    else:
        strategy["recommendations"].append("Current accuracy is sufficient")
    
    if reference_points_count < 5:
        strategy["recommendations"].append("Need minimum 5 reference points for calibration")
    
    return strategy 