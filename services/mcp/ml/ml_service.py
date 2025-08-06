"""
ML Service - Main Orchestrator

Coordinates all ML components including AI validation, predictive analytics,
pattern recognition, and model management for the MCP service.
"""

import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

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
    MLServiceStatus,
)
from .model_manager import ModelManager
from .ai_validator import AIValidator
from .predictive_analytics import PredictiveAnalytics
from .pattern_recognition import PatternRecognition
from .training_pipeline import TrainingPipeline


logger = logging.getLogger(__name__)


class MLService:
    """Main ML service orchestrator for the MCP service"""

    def __init__(self):
        """Initialize the ML service"""
        # Initialize model manager
        self.model_manager = ModelManager()

        # Initialize ML components
        self.ai_validator = AIValidator(self.model_manager)
        self.predictive_analytics = PredictiveAnalytics(self.model_manager)
        self.pattern_recognition = PatternRecognition(self.model_manager)
        self.training_pipeline = TrainingPipeline(self.model_manager)

        # Service statistics
        self.total_requests = 0
        self.error_count = 0
        self.start_time = datetime.utcnow()

        logger.info("ML Service initialized successfully")

    async def validate_building(
        self, request: AIValidationRequest
    ) -> AIValidationResult:
        """
        Perform AI-powered building validation

        Args:
            request: Validation request

        Returns:
            Validation result
        """
        self.total_requests += 1
        start_time = time.time()

        try:
            result = self.ai_validator.validate(request)
            logger.info(f"AI validation completed for {request.validation_type}")
            return result

        except Exception as e:
            self.error_count += 1
            logger.error(f"Error during AI validation: {e}")
            raise

    async def predict_building_metrics(
        self, request: PredictionRequest
    ) -> PredictionResult:
        """
        Perform predictive analytics for building metrics

        Args:
            request: Prediction request

        Returns:
            Prediction result
        """
        self.total_requests += 1
        start_time = time.time()

        try:
            result = self.predictive_analytics.predict(request)
            logger.info(f"Prediction completed for {request.prediction_type}")
            return result

        except Exception as e:
            self.error_count += 1
            logger.error(f"Error during prediction: {e}")
            raise

    async def recognize_patterns(self, request: PatternRequest) -> PatternResult:
        """
        Perform pattern recognition on building data

        Args:
            request: Pattern recognition request

        Returns:
            Pattern recognition result
        """
        self.total_requests += 1
        start_time = time.time()

        try:
            result = self.pattern_recognition.recognize_patterns(request)
            logger.info(f"Pattern recognition completed for {request.pattern_type}")
            return result

        except Exception as e:
            self.error_count += 1
            logger.error(f"Error during pattern recognition: {e}")
            raise

    async def train_model(self, request: TrainingRequest) -> TrainingResult:
        """
        Train a new machine learning model

        Args:
            request: Training request

        Returns:
            Training result
        """
        self.total_requests += 1
        start_time = time.time()

        try:
            result = self.training_pipeline.train_model(request)
            logger.info(f"Model training completed for {request.model_type}")
            return result

        except Exception as e:
            self.error_count += 1
            logger.error(f"Error during model training: {e}")
            raise

    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific model

        Args:
            model_id: Model ID

        Returns:
            Model information or None if not found
        """
        model_info = self.model_manager.get_model_info(model_id)
        if model_info:
            return model_info.dict()
        return None

    def list_models(self, status: Optional[ModelStatus] = None) -> List[Dict[str, Any]]:
        """
        List all models, optionally filtered by status

        Args:
            status: Optional status filter

        Returns:
            List of model information dictionaries
        """
        models = self.model_manager.list_models(status=status)
        return [model.dict() for model in models]

    def activate_model(self, model_id: str) -> bool:
        """
        Activate a model

        Args:
            model_id: Model ID

        Returns:
            True if successful, False otherwise
        """
        return self.model_manager.activate_model(model_id)

    def deactivate_model(self, model_id: str) -> bool:
        """
        Deactivate a model

        Args:
            model_id: Model ID

        Returns:
            True if successful, False otherwise
        """
        return self.model_manager.deactivate_model(model_id)

    def delete_model(self, model_id: str) -> bool:
        """
        Delete a model

        Args:
            model_id: Model ID

        Returns:
            True if successful, False otherwise
        """
        return self.model_manager.delete_model(model_id)

    def get_service_status(self) -> MLServiceStatus:
        """
        Get the current status of the ML service

        Returns:
            ML service status
        """
        # Calculate service metrics
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        error_rate = self.error_count / max(self.total_requests, 1)

        # Get model statistics
        model_stats = self.model_manager.get_model_statistics()

        # Mock system metrics (in a real implementation, these would be actual metrics)
        memory_usage = 512.5  # MB
        cpu_usage = 25.3  # Percentage

        return MLServiceStatus(
            service_status="healthy",
            active_models=model_stats["active_models"],
            total_models=model_stats["total_models"],
            last_training=datetime.utcnow() - timedelta(hours=2),  # Mock last training
            average_response_time=0.5,  # Mock average response time
            total_requests=self.total_requests,
            error_rate=error_rate,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
        )

    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation statistics"""
        return self.ai_validator.get_validation_statistics()

    def get_prediction_statistics(self) -> Dict[str, Any]:
        """Get prediction statistics"""
        return self.predictive_analytics.get_prediction_statistics()

    def get_model_statistics(self) -> Dict[str, Any]:
        """Get model statistics"""
        return self.model_manager.get_model_statistics()

    def get_comprehensive_statistics(self) -> Dict[str, Any]:
        """Get comprehensive ML service statistics"""
        service_status = self.get_service_status()

        return {
            "service": {
                "status": service_status.service_status,
                "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
                "total_requests": service_status.total_requests,
                "error_rate": service_status.error_rate,
                "average_response_time": service_status.average_response_time,
                "memory_usage_mb": service_status.memory_usage,
                "cpu_usage_percent": service_status.cpu_usage,
            },
            "models": self.get_model_statistics(),
            "validation": self.get_validation_statistics(),
            "prediction": self.get_prediction_statistics(),
        }
