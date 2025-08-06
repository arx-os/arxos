"""
ML Integration API Routes

FastAPI routes for ML integration including AI validation, predictive analytics,
pattern recognition, and model management.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse

from auth.authentication import get_current_user, require_permission, Permission
from .models import (
    AIValidationRequest,
    AIValidationResult,
    ValidationType,
    PredictionRequest,
    PredictionResult,
    PredictionType,
    PatternRequest,
    PatternResult,
    PatternType,
    TrainingRequest,
    TrainingResult,
    ModelStatus,
)
from .ml_service import MLService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/ml", tags=["ML Integration"])

# Global ML service instance
ml_service: MLService = None


def get_ml_service() -> MLService:
    """Get the ML service instance"""
    global ml_service
    if ml_service is None:
        ml_service = MLService()
    return ml_service


# =============================================================================
# AI VALIDATION ENDPOINTS
# =============================================================================


@router.post("/validate", response_model=AIValidationResult)
async def validate_building_ai(
    request: AIValidationRequest,
    current_user=Depends(get_current_user),
    ml_service: MLService = Depends(get_ml_service),
):
    """
    Perform AI-powered building validation

    Uses machine learning models to validate building designs against building codes
    and provide intelligent suggestions for improvements.
    """
    try:
        result = await ml_service.validate_building(request)
        logger.info(f"AI validation completed for user {current_user.username}")
        return result

    except Exception as e:
        logger.error(f"AI validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"AI validation failed: {str(e)}")


@router.get("/validate/types")
async def get_validation_types(current_user=Depends(get_current_user)):
    """
    Get available validation types

    Returns all available AI validation types that can be performed.
    """
    return {
        "validation_types": [
            {
                "type": vt.value,
                "name": vt.name,
                "description": f"AI validation for {vt.value} compliance",
            }
            for vt in ValidationType
        ]
    }


@router.get("/validate/statistics")
async def get_validation_statistics(
    current_user=Depends(require_permission(Permission.SYSTEM_ADMIN)),
    ml_service: MLService = Depends(get_ml_service),
):
    """
    Get AI validation statistics

    Returns comprehensive statistics about AI validation performance.
    """
    try:
        stats = ml_service.get_validation_statistics()
        return stats

    except Exception as e:
        logger.error(f"Failed to get validation statistics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get validation statistics"
        )


# =============================================================================
# PREDICTIVE ANALYTICS ENDPOINTS
# =============================================================================


@router.post("/predict", response_model=PredictionResult)
async def predict_building_metrics(
    request: PredictionRequest,
    current_user=Depends(get_current_user),
    ml_service: MLService = Depends(get_ml_service),
):
    """
    Perform predictive analytics for building metrics

    Uses machine learning models to predict various building metrics including
    compliance risk, cost estimates, construction time, and more.
    """
    try:
        result = await ml_service.predict_building_metrics(request)
        logger.info(f"Prediction completed for user {current_user.username}")
        return result

    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get("/predict/types")
async def get_prediction_types(current_user=Depends(get_current_user)):
    """
    Get available prediction types

    Returns all available prediction types that can be performed.
    """
    return {
        "prediction_types": [
            {
                "type": pt.value,
                "name": pt.name,
                "description": f"Predict {pt.value} for building projects",
            }
            for pt in PredictionType
        ]
    }


@router.get("/predict/statistics")
async def get_prediction_statistics(
    current_user=Depends(require_permission(Permission.SYSTEM_ADMIN)),
    ml_service: MLService = Depends(get_ml_service),
):
    """
    Get predictive analytics statistics

    Returns comprehensive statistics about predictive analytics performance.
    """
    try:
        stats = ml_service.get_prediction_statistics()
        return stats

    except Exception as e:
        logger.error(f"Failed to get prediction statistics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get prediction statistics"
        )


# =============================================================================
# PATTERN RECOGNITION ENDPOINTS
# =============================================================================


@router.post("/patterns", response_model=PatternResult)
async def recognize_patterns(
    request: PatternRequest,
    current_user=Depends(get_current_user),
    ml_service: MLService = Depends(get_ml_service),
):
    """
    Perform pattern recognition on building data

    Uses machine learning models to recognize patterns in building designs,
    violations, optimizations, and other building-related data.
    """
    try:
        result = await ml_service.recognize_patterns(request)
        logger.info(f"Pattern recognition completed for user {current_user.username}")
        return result

    except Exception as e:
        logger.error(f"Pattern recognition failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Pattern recognition failed: {str(e)}"
        )


@router.get("/patterns/types")
async def get_pattern_types(current_user=Depends(get_current_user)):
    """
    Get available pattern types

    Returns all available pattern types that can be recognized.
    """
    return {
        "pattern_types": [
            {
                "type": pt.value,
                "name": pt.name,
                "description": f"Recognize {pt.value} in building data",
            }
            for pt in PatternType
        ]
    }


# =============================================================================
# MODEL MANAGEMENT ENDPOINTS
# =============================================================================


@router.post("/models/train", response_model=TrainingResult)
async def train_model(
    request: TrainingRequest,
    current_user=Depends(require_permission(Permission.SYSTEM_ADMIN)),
    ml_service: MLService = Depends(get_ml_service),
):
    """
    Train a new machine learning model

    Initiates training of a new machine learning model with the provided data
    and hyperparameters.
    """
    try:
        result = await ml_service.train_model(request)
        logger.info(f"Model training initiated by user {current_user.username}")
        return result

    except Exception as e:
        logger.error(f"Model training failed: {e}")
        raise HTTPException(status_code=500, detail=f"Model training failed: {str(e)}")


@router.get("/models")
async def list_models(
    status: Optional[ModelStatus] = Query(None, description="Filter by model status"),
    current_user=Depends(get_current_user),
    ml_service: MLService = Depends(get_ml_service),
):
    """
    List all machine learning models

    Returns a list of all models, optionally filtered by status.
    """
    try:
        models = ml_service.list_models(status=status)
        return {"models": models}

    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(status_code=500, detail="Failed to list models")


@router.get("/models/{model_id}")
async def get_model_info(
    model_id: str,
    current_user=Depends(get_current_user),
    ml_service: MLService = Depends(get_ml_service),
):
    """
    Get information about a specific model

    Returns detailed information about a specific machine learning model.
    """
    try:
        model_info = ml_service.get_model_info(model_id)
        if not model_info:
            raise HTTPException(status_code=404, detail="Model not found")
        return model_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get model info")


@router.post("/models/{model_id}/activate")
async def activate_model(
    model_id: str,
    current_user=Depends(require_permission(Permission.SYSTEM_ADMIN)),
    ml_service: MLService = Depends(get_ml_service),
):
    """
    Activate a model

    Activates a model, making it available for predictions and validations.
    """
    try:
        success = ml_service.activate_model(model_id)
        if success:
            logger.info(f"Model {model_id} activated by user {current_user.username}")
            return {"message": "Model activated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to activate model")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate model: {e}")
        raise HTTPException(status_code=500, detail="Failed to activate model")


@router.post("/models/{model_id}/deactivate")
async def deactivate_model(
    model_id: str,
    current_user=Depends(require_permission(Permission.SYSTEM_ADMIN)),
    ml_service: MLService = Depends(get_ml_service),
):
    """
    Deactivate a model

    Deactivates a model, removing it from active use.
    """
    try:
        success = ml_service.deactivate_model(model_id)
        if success:
            logger.info(f"Model {model_id} deactivated by user {current_user.username}")
            return {"message": "Model deactivated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to deactivate model")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate model: {e}")
        raise HTTPException(status_code=500, detail="Failed to deactivate model")


@router.delete("/models/{model_id}")
async def delete_model(
    model_id: str,
    current_user=Depends(require_permission(Permission.SYSTEM_ADMIN)),
    ml_service: MLService = Depends(get_ml_service),
):
    """
    Delete a model

    Permanently deletes a machine learning model from the system.
    """
    try:
        success = ml_service.delete_model(model_id)
        if success:
            logger.info(f"Model {model_id} deleted by user {current_user.username}")
            return {"message": "Model deleted successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to delete model")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete model: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete model")


@router.get("/models/statistics")
async def get_model_statistics(
    current_user=Depends(require_permission(Permission.SYSTEM_ADMIN)),
    ml_service: MLService = Depends(get_ml_service),
):
    """
    Get model statistics

    Returns comprehensive statistics about all models in the system.
    """
    try:
        stats = ml_service.get_model_statistics()
        return stats

    except Exception as e:
        logger.error(f"Failed to get model statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get model statistics")


# =============================================================================
# SERVICE STATUS ENDPOINTS
# =============================================================================


@router.get("/status")
async def get_ml_service_status(
    current_user=Depends(get_current_user),
    ml_service: MLService = Depends(get_ml_service),
):
    """
    Get ML service status

    Returns the current status and health of the ML service.
    """
    try:
        status = ml_service.get_service_status()
        return status.dict()

    except Exception as e:
        logger.error(f"Failed to get ML service status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get ML service status")


@router.get("/statistics")
async def get_comprehensive_statistics(
    current_user=Depends(require_permission(Permission.SYSTEM_ADMIN)),
    ml_service: MLService = Depends(get_ml_service),
):
    """
    Get comprehensive ML service statistics

    Returns comprehensive statistics about the ML service including
    service metrics, model statistics, validation statistics, and prediction statistics.
    """
    try:
        stats = ml_service.get_comprehensive_statistics()
        return stats

    except Exception as e:
        logger.error(f"Failed to get comprehensive statistics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get comprehensive statistics"
        )


@router.get("/health")
async def health_check():
    """
    ML service health check

    Returns the health status of the ML service.
    """
    try:
        # Basic health check
        return {
            "status": "healthy",
            "service": "ML Integration",
            "timestamp": "2024-01-01T00:00:00Z",
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "ML Integration",
                "error": str(e),
                "timestamp": "2024-01-01T00:00:00Z",
            },
        )
