"""
AI Validator for ML Integration

Provides AI-powered validation using machine learning models for building code compliance.
"""

import time
import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from datetime import datetime
from pathlib import Path

from .models import AIValidationRequest, AIValidationResult, ValidationType
from .model_manager import ModelManager, ModelStatus


logger = logging.getLogger(__name__)


class AIValidator:
    """AI-powered validation engine for building code compliance"""

    def __init__(self, model_manager: ModelManager):
        """
        Initialize the AI validator

        Args:
            model_manager: Model manager instance
        """
        self.model_manager = model_manager
        self.validation_models = {
            ValidationType.STRUCTURAL: "structural_validator",
            ValidationType.ELECTRICAL: "electrical_validator",
            ValidationType.FIRE_PROTECTION: "fire_protection_validator",
            ValidationType.ACCESSIBILITY: "accessibility_validator",
            ValidationType.MECHANICAL: "mechanical_validator",
            ValidationType.PLUMBING: "plumbing_validator",
            ValidationType.ENERGY: "energy_validator",
            ValidationType.GENERAL: "general_validator",
        }

        # Initialize with sample models if available
        self._initialize_sample_models()

        logger.info("AI Validator initialized")

    def _initialize_sample_models(self) -> None:
        """Initialize with sample models from the ml_models directory"""
        try:
            # Check for existing models in ml_models directory
            import os

            models_dir = Path("ml_models")

            if models_dir.exists():
                for model_file in models_dir.glob("*.pkl"):
                    model_name = model_file.stem

                    # Map file names to validation types
                    validation_mapping = {
                        "ml_rule_002_classifier": ValidationType.STRUCTURAL,
                        "ml_rule_004_classifier": ValidationType.ELECTRICAL,
                        "ml_rule_005_classifier": ValidationType.FIRE_PROTECTION,
                        "adv_rule_002_classifier": ValidationType.GENERAL,
                    }

                    if model_name in validation_mapping:
                        validation_type = validation_mapping[model_name]
                        self._register_sample_model(
                            str(model_file), validation_type, model_name
                        )

        except Exception as e:
            logger.warning(f"Failed to initialize sample models: {e}")

    def _register_sample_model(
        self, model_file: str, validation_type: ValidationType, model_name: str
    ) -> None:
        """Register a sample model"""
        try:
            model_id = self.model_manager.register_model(
                model_file=model_file,
                model_name=f"{validation_type.value.title()} Validator",
                model_type="classification",
                version="1.0.0",
                description=f"AI model for {validation_type.value} validation",
            )

            # Activate the model
            if self.model_manager.activate_model(model_id):
                logger.info(f"Registered and activated sample model: {model_name}")
            else:
                logger.warning(f"Failed to activate sample model: {model_name}")

        except Exception as e:
            logger.error(f"Failed to register sample model {model_name}: {e}")

    def _extract_features(
        self, building_data: Dict[str, Any], validation_type: ValidationType
    ) -> np.ndarray:
        """
        Extract features from building data for ML model input

        Args:
            building_data: Building design data
            validation_type: Type of validation

        Returns:
            Feature array for ML model
        """
        # This is a simplified feature extraction
        # In a real implementation, this would be much more sophisticated

        features = []

        # Extract basic building features
        building_area = building_data.get("area", 0)
        building_height = building_data.get("height", 0)
        building_type = building_data.get("type", "unknown")
        occupancy_type = building_data.get("occupancy", "unknown")

        # Convert categorical variables to numerical
        type_mapping = {
            "residential": 1,
            "commercial": 2,
            "industrial": 3,
            "mixed": 4,
            "unknown": 0,
        }
        occupancy_mapping = {
            "A": 1,
            "B": 2,
            "C": 3,
            "D": 4,
            "E": 5,
            "F": 6,
            "H": 7,
            "I": 8,
            "M": 9,
            "R": 10,
            "S": 11,
            "U": 12,
            "unknown": 0,
        }

        building_type_code = type_mapping.get(building_type, 0)
        occupancy_code = occupancy_mapping.get(occupancy_type, 0)

        # Extract validation-specific features
        if validation_type == ValidationType.STRUCTURAL:
            # Structural features
            floor_count = building_data.get("floors", 1)
            foundation_type = building_data.get("foundation", "unknown")
            structural_system = building_data.get("structural_system", "unknown")

            foundation_mapping = {
                "slab": 1,
                "basement": 2,
                "crawlspace": 3,
                "unknown": 0,
            }
            structural_mapping = {
                "wood": 1,
                "steel": 2,
                "concrete": 3,
                "masonry": 4,
                "unknown": 0,
            }

            foundation_code = foundation_mapping.get(foundation_type, 0)
            structural_code = structural_mapping.get(structural_system, 0)

            features = [
                building_area,
                building_height,
                building_type_code,
                occupancy_code,
                floor_count,
                foundation_code,
                structural_code,
            ]

        elif validation_type == ValidationType.ELECTRICAL:
            # Electrical features
            electrical_load = building_data.get("electrical_load", 0)
            panel_count = building_data.get("electrical_panels", 1)
            emergency_systems = building_data.get("emergency_systems", False)

            features = [
                building_area,
                building_height,
                building_type_code,
                occupancy_code,
                electrical_load,
                panel_count,
                int(emergency_systems),
            ]

        elif validation_type == ValidationType.FIRE_PROTECTION:
            # Fire protection features
            sprinkler_system = building_data.get("sprinkler_system", False)
            fire_alarm = building_data.get("fire_alarm", False)
            fire_rating = building_data.get("fire_rating", 0)

            features = [
                building_area,
                building_height,
                building_type_code,
                occupancy_code,
                int(sprinkler_system),
                int(fire_alarm),
                fire_rating,
            ]

        else:
            # General features for other validation types
            features = [
                building_area,
                building_height,
                building_type_code,
                occupancy_code,
            ]

        # Normalize features (simple min-max normalization)
        features = np.array(features, dtype=float)

        # Handle zero division
        if np.max(features) > 0:
            features = features / np.max(features)

        return features.reshape(1, -1)

    def _generate_violations(
        self,
        building_data: Dict[str, Any],
        validation_type: ValidationType,
        confidence_score: float,
    ) -> List[Dict[str, Any]]:
        """
        Generate violations based on validation type and building data

        Args:
            building_data: Building design data
            validation_type: Type of validation
            confidence_score: Confidence in the validation

        Returns:
            List of violations
        """
        violations = []

        # Generate sample violations based on validation type
        if validation_type == ValidationType.STRUCTURAL:
            if building_data.get("height", 0) > 30:
                violations.append(
                    {
                        "code": "IBC-504.2",
                        "description": "Building height exceeds maximum allowed",
                        "severity": "high",
                        "location": "building_height",
                        "suggestion": "Consider reducing building height or using fire-resistive construction",
                    }
                )

            if building_data.get("area", 0) > 50000:
                violations.append(
                    {
                        "code": "IBC-506.2",
                        "description": "Building area exceeds maximum allowed for construction type",
                        "severity": "medium",
                        "location": "building_area",
                        "suggestion": "Consider fire walls or fire-resistive construction",
                    }
                )

        elif validation_type == ValidationType.ELECTRICAL:
            if building_data.get("electrical_load", 0) > 1000:
                violations.append(
                    {
                        "code": "NEC-220.12",
                        "description": "Electrical load calculation exceeds service capacity",
                        "severity": "high",
                        "location": "electrical_system",
                        "suggestion": "Upgrade electrical service or reduce load",
                    }
                )

        elif validation_type == ValidationType.FIRE_PROTECTION:
            if not building_data.get("sprinkler_system", False):
                violations.append(
                    {
                        "code": "IFC-903.2",
                        "description": "Automatic sprinkler system required",
                        "severity": "high",
                        "location": "fire_protection",
                        "suggestion": "Install automatic sprinkler system",
                    }
                )

        return violations

    def _generate_suggestions(
        self,
        building_data: Dict[str, Any],
        validation_type: ValidationType,
        violations: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Generate improvement suggestions

        Args:
            building_data: Building design data
            validation_type: Type of validation
            violations: List of violations found

        Returns:
            List of suggestions
        """
        suggestions = []

        # Generate suggestions based on validation type and violations
        if validation_type == ValidationType.STRUCTURAL:
            if building_data.get("height", 0) > 20:
                suggestions.append(
                    {
                        "type": "optimization",
                        "title": "Consider fire-resistive construction",
                        "description": "For buildings over 20 feet, consider fire-resistive construction to increase height limits",
                        "impact": "high",
                        "effort": "medium",
                    }
                )

        elif validation_type == ValidationType.ELECTRICAL:
            if building_data.get("electrical_load", 0) > 500:
                suggestions.append(
                    {
                        "type": "optimization",
                        "title": "Consider energy-efficient systems",
                        "description": "Implement energy-efficient electrical systems to reduce load requirements",
                        "impact": "medium",
                        "effort": "low",
                    }
                )

        elif validation_type == ValidationType.FIRE_PROTECTION:
            if not building_data.get("fire_alarm", False):
                suggestions.append(
                    {
                        "type": "compliance",
                        "title": "Install fire alarm system",
                        "description": "Consider installing a fire alarm system for early warning",
                        "impact": "high",
                        "effort": "medium",
                    }
                )

        return suggestions

    def validate(self, request: AIValidationRequest) -> AIValidationResult:
        """
        Perform AI-powered validation

        Args:
            request: Validation request

        Returns:
            Validation result
        """
        start_time = time.time()

        try:
            # Get the appropriate model for this validation type
            model_name = self.validation_models.get(request.validation_type)
            if not model_name:
                raise ValueError(
                    f"No model available for validation type: {request.validation_type}"
                )

            # Find active model for this validation type
            active_models = self.model_manager.list_models(status=ModelStatus.ACTIVE)
            model_info = None

            for model in active_models:
                if request.validation_type.value in model.model_name.lower():
                    model_info = model
                    break

            if not model_info:
                # Use a default model or create a mock validation
                logger.warning(
                    f"No active model found for {request.validation_type}, using mock validation"
                )
                return self._mock_validation(request)

            # Get the model
            model = self.model_manager.get_model(model_info.model_id)
            if not model:
                logger.error(f"Failed to load model: {model_info.model_id}")
                return self._mock_validation(request)

            # Extract features
            features = self._extract_features(
                request.building_data, request.validation_type
            )

            # Make prediction
            prediction = model.predict(features)
            prediction_proba = (
                model.predict_proba(features)
                if hasattr(model, "predict_proba")
                else None
            )

            # Calculate confidence score
            if prediction_proba is not None:
                confidence_score = np.max(prediction_proba[0])
            else:
                confidence_score = (
                    0.8  # Default confidence for models without probability
                )

            # Determine compliance
            is_compliant = bool(prediction[0]) if len(prediction) > 0 else True

            # Apply confidence threshold
            if confidence_score < request.confidence_threshold:
                logger.warning(
                    f"Confidence score {confidence_score} below threshold {request.confidence_threshold}"
                )
                confidence_score = request.confidence_threshold

            # Generate violations and suggestions
            violations = self._generate_violations(
                request.building_data, request.validation_type, confidence_score
            )
            suggestions = (
                self._generate_suggestions(
                    request.building_data, request.validation_type, violations
                )
                if request.include_suggestions
                else []
            )

            processing_time = time.time() - start_time

            return AIValidationResult(
                is_compliant=is_compliant,
                confidence_score=confidence_score,
                violations=violations,
                suggestions=suggestions,
                validation_type=request.validation_type,
                model_version=model_info.version,
                processing_time=processing_time,
            )

        except Exception as e:
            logger.error(f"Error during AI validation: {e}")
            processing_time = time.time() - start_time

            return AIValidationResult(
                is_compliant=False,
                confidence_score=0.0,
                violations=[
                    {
                        "code": "AI_ERROR",
                        "description": f"AI validation failed: {str(e)}",
                        "severity": "high",
                        "location": "ai_system",
                        "suggestion": "Contact system administrator",
                    }
                ],
                suggestions=[],
                validation_type=request.validation_type,
                model_version="unknown",
                processing_time=processing_time,
            )

    def _mock_validation(self, request: AIValidationRequest) -> AIValidationResult:
        """
        Perform mock validation when no model is available

        Args:
            request: Validation request

        Returns:
            Mock validation result
        """
        start_time = time.time()

        # Simple mock validation based on building data
        building_area = request.building_data.get("area", 0)
        building_height = request.building_data.get("height", 0)

        # Mock compliance logic
        is_compliant = building_area <= 10000 and building_height <= 30
        confidence_score = 0.7

        # Generate mock violations
        violations = []
        if building_area > 10000:
            violations.append(
                {
                    "code": "MOCK-001",
                    "description": "Building area exceeds mock limit",
                    "severity": "medium",
                    "location": "building_area",
                    "suggestion": "Reduce building area or apply for variance",
                }
            )

        if building_height > 30:
            violations.append(
                {
                    "code": "MOCK-002",
                    "description": "Building height exceeds mock limit",
                    "severity": "high",
                    "location": "building_height",
                    "suggestion": "Reduce building height or use fire-resistive construction",
                }
            )

        # Generate mock suggestions
        suggestions = []
        if request.include_suggestions:
            suggestions.append(
                {
                    "type": "optimization",
                    "title": "Consider mock optimization",
                    "description": "This is a mock suggestion for demonstration purposes",
                    "impact": "medium",
                    "effort": "low",
                }
            )

        processing_time = time.time() - start_time

        return AIValidationResult(
            is_compliant=is_compliant,
            confidence_score=confidence_score,
            violations=violations,
            suggestions=suggestions,
            validation_type=request.validation_type,
            model_version="mock-1.0.0",
            processing_time=processing_time,
        )

    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation statistics"""
        active_models = self.model_manager.list_models(status=ModelStatus.ACTIVE)

        return {
            "active_models": len(active_models),
            "validation_types": list(self.validation_models.keys()),
            "model_versions": [model.version for model in active_models],
            "total_models": self.model_manager.get_total_models_count(),
        }
