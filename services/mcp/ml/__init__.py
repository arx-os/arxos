"""
ML Integration System for MCP

This module provides AI-powered validation, predictive analytics, pattern recognition,
model management, and training pipeline capabilities for the MCP service.

Components:
- MLService: Main ML orchestrator
- AIValidator: AI-powered validation engine
- PredictiveAnalytics: Predictive analytics engine
- PatternRecognition: Pattern recognition engine
- ModelManager: Model versioning and management
- TrainingPipeline: Training data management
"""

from .ml_service import MLService
from .ai_validator import AIValidator
from .predictive_analytics import PredictiveAnalytics
from .pattern_recognition import PatternRecognition
from .model_manager import ModelManager
from .training_pipeline import TrainingPipeline

__all__ = [
    "MLService",
    "AIValidator",
    "PredictiveAnalytics",
    "PatternRecognition",
    "ModelManager",
    "TrainingPipeline",
]
