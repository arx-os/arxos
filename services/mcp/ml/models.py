"""
ML Integration Data Models

Pydantic models for ML integration components including validation requests,
predictive analytics, pattern recognition, and model management.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator


class ValidationType(str, Enum):
    """Types of AI validation"""

    STRUCTURAL = "structural"
    ELECTRICAL = "electrical"
    FIRE_PROTECTION = "fire_protection"
    ACCESSIBILITY = "accessibility"
    MECHANICAL = "mechanical"
    PLUMBING = "plumbing"
    ENERGY = "energy"
    GENERAL = "general"


class PredictionType(str, Enum):
    """Types of predictions"""

    COMPLIANCE_RISK = "compliance_risk"
    COST_ESTIMATE = "cost_estimate"
    CONSTRUCTION_TIME = "construction_time"
    MAINTENANCE_NEEDS = "maintenance_needs"
    ENERGY_EFFICIENCY = "energy_efficiency"
    SAFETY_RISK = "safety_risk"


class PatternType(str, Enum):
    """Types of patterns"""

    DESIGN_PATTERN = "design_pattern"
    VIOLATION_PATTERN = "violation_pattern"
    OPTIMIZATION_PATTERN = "optimization_pattern"
    COST_PATTERN = "cost_pattern"
    TIME_PATTERN = "time_pattern"


class ModelStatus(str, Enum):
    """Model status"""

    TRAINING = "training"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    ERROR = "error"


class AIValidationRequest(BaseModel):
    """Request for AI-powered validation"""

    building_data: Dict[str, Any] = Field(..., description="Building design data")
    validation_type: ValidationType = Field(..., description="Type of validation")
    jurisdiction: str = Field(..., description="Jurisdiction for validation")
    include_suggestions: bool = Field(
        True, description="Include improvement suggestions"
    )
    confidence_threshold: float = Field(
        0.7, ge=0.0, le=1.0, description="Minimum confidence threshold"
    )

    @validator("confidence_threshold")
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence threshold must be between 0.0 and 1.0")
        return v


class AIValidationResult(BaseModel):
    """Result of AI-powered validation"""

    is_compliant: bool = Field(..., description="Overall compliance status")
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in the validation"
    )
    violations: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of violations found"
    )
    suggestions: List[Dict[str, Any]] = Field(
        default_factory=list, description="Improvement suggestions"
    )
    validation_type: ValidationType = Field(
        ..., description="Type of validation performed"
    )
    model_version: str = Field(..., description="Version of the model used")
    processing_time: float = Field(..., description="Processing time in seconds")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Validation timestamp"
    )


class PredictionRequest(BaseModel):
    """Request for predictive analytics"""

    building_data: Dict[str, Any] = Field(..., description="Building design data")
    prediction_type: PredictionType = Field(..., description="Type of prediction")
    time_horizon: Optional[int] = Field(
        None, ge=1, description="Time horizon in months"
    )
    include_confidence: bool = Field(True, description="Include confidence intervals")

    @validator("time_horizon")
    def validate_time_horizon(cls, v):
        if v is not None and v < 1:
            raise ValueError("Time horizon must be at least 1 month")
        return v


class PredictionResult(BaseModel):
    """Result of predictive analytics"""

    prediction_type: PredictionType = Field(..., description="Type of prediction")
    predicted_value: Union[float, str, bool] = Field(..., description="Predicted value")
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in prediction"
    )
    confidence_interval: Optional[Dict[str, float]] = Field(
        None, description="Confidence interval"
    )
    factors: List[Dict[str, Any]] = Field(
        default_factory=list, description="Factors influencing prediction"
    )
    model_version: str = Field(..., description="Version of the model used")
    processing_time: float = Field(..., description="Processing time in seconds")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Prediction timestamp"
    )


class PatternRequest(BaseModel):
    """Request for pattern recognition"""

    building_data: Dict[str, Any] = Field(..., description="Building design data")
    pattern_type: PatternType = Field(..., description="Type of pattern to recognize")
    historical_data: Optional[List[Dict[str, Any]]] = Field(
        None, description="Historical data for comparison"
    )
    similarity_threshold: float = Field(
        0.8, ge=0.0, le=1.0, description="Similarity threshold"
    )

    @validator("similarity_threshold")
    def validate_similarity(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Similarity threshold must be between 0.0 and 1.0")
        return v


class PatternResult(BaseModel):
    """Result of pattern recognition"""

    pattern_type: PatternType = Field(..., description="Type of pattern recognized")
    patterns_found: List[Dict[str, Any]] = Field(
        default_factory=list, description="Patterns found"
    )
    similarity_scores: List[float] = Field(
        default_factory=list, description="Similarity scores"
    )
    recommendations: List[Dict[str, Any]] = Field(
        default_factory=list, description="Recommendations based on patterns"
    )
    model_version: str = Field(..., description="Version of the model used")
    processing_time: float = Field(..., description="Processing time in seconds")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Pattern recognition timestamp"
    )


class ModelInfo(BaseModel):
    """Information about a machine learning model"""

    model_id: str = Field(..., description="Unique model identifier")
    model_name: str = Field(..., description="Human-readable model name")
    model_type: str = Field(
        ..., description="Type of model (classification, regression, etc.)"
    )
    version: str = Field(..., description="Model version")
    status: ModelStatus = Field(..., description="Current model status")
    accuracy: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Model accuracy"
    )
    training_date: Optional[datetime] = Field(
        None, description="Date when model was trained"
    )
    features: List[str] = Field(
        default_factory=list, description="Features used by the model"
    )
    file_path: str = Field(..., description="Path to model file")
    file_size: Optional[int] = Field(None, description="Size of model file in bytes")
    description: Optional[str] = Field(None, description="Model description")


class TrainingRequest(BaseModel):
    """Request for model training"""

    model_type: str = Field(..., description="Type of model to train")
    training_data: List[Dict[str, Any]] = Field(..., description="Training data")
    validation_data: Optional[List[Dict[str, Any]]] = Field(
        None, description="Validation data"
    )
    hyperparameters: Optional[Dict[str, Any]] = Field(
        None, description="Model hyperparameters"
    )
    model_name: Optional[str] = Field(None, description="Name for the new model")
    description: Optional[str] = Field(None, description="Model description")


class TrainingResult(BaseModel):
    """Result of model training"""

    model_id: str = Field(..., description="ID of the trained model")
    model_name: str = Field(..., description="Name of the trained model")
    training_time: float = Field(..., description="Training time in seconds")
    accuracy: float = Field(..., ge=0.0, le=1.0, description="Model accuracy")
    validation_accuracy: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Validation accuracy"
    )
    loss: Optional[float] = Field(None, description="Training loss")
    model_version: str = Field(..., description="Model version")
    file_path: str = Field(..., description="Path to saved model")
    status: ModelStatus = Field(..., description="Model status")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Training timestamp"
    )


class MLServiceStatus(BaseModel):
    """Status of the ML service"""

    service_status: str = Field(..., description="Overall service status")
    active_models: int = Field(..., description="Number of active models")
    total_models: int = Field(..., description="Total number of models")
    last_training: Optional[datetime] = Field(
        None, description="Last training timestamp"
    )
    average_response_time: float = Field(
        ..., description="Average response time in seconds"
    )
    total_requests: int = Field(..., description="Total number of requests processed")
    error_rate: float = Field(..., ge=0.0, le=1.0, description="Error rate")
    memory_usage: float = Field(..., description="Memory usage in MB")
    cpu_usage: float = Field(..., description="CPU usage percentage")
