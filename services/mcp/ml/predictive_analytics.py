"""
Predictive Analytics for ML Integration

Provides AI-powered predictions for compliance risk, cost estimates, construction time,
maintenance needs, energy efficiency, and safety risk.
"""

import time
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
import numpy as np
from datetime import datetime, timedelta
import random

from .models import PredictionRequest, PredictionResult, PredictionType
from .model_manager import ModelManager, ModelStatus


logger = logging.getLogger(__name__)


class PredictiveAnalytics:
    """AI-powered predictive analytics engine for building projects"""

    def __init__(self, model_manager: ModelManager):
        """
        Initialize the predictive analytics engine

        Args:
            model_manager: Model manager instance
        """
        self.model_manager = model_manager
        self.prediction_models = {
            PredictionType.COMPLIANCE_RISK: "compliance_risk_predictor",
            PredictionType.COST_ESTIMATE: "cost_estimator",
            PredictionType.CONSTRUCTION_TIME: "construction_time_predictor",
            PredictionType.MAINTENANCE_NEEDS: "maintenance_predictor",
            PredictionType.ENERGY_EFFICIENCY: "energy_efficiency_predictor",
            PredictionType.SAFETY_RISK: "safety_risk_predictor",
        }

        # Initialize prediction models
        self._initialize_prediction_models()

        logger.info("Predictive Analytics initialized")

    def _initialize_prediction_models(self) -> None:
        """Initialize prediction models"""
        try:
            # Register sample prediction models if available
            # In a real implementation, these would be trained models
            logger.info("Initializing prediction models")

        except Exception as e:
            logger.warning(f"Failed to initialize prediction models: {e}")

    def _extract_prediction_features(
        self, building_data: Dict[str, Any], prediction_type: PredictionType
    ) -> np.ndarray:
        """
        Extract features for prediction models

        Args:
            building_data: Building design data
            prediction_type: Type of prediction

        Returns:
            Feature array for prediction model
        """
        # Extract basic building features
        building_area = building_data.get("area", 0)
        building_height = building_data.get("height", 0)
        building_type = building_data.get("type", "unknown")
        occupancy_type = building_data.get("occupancy", "unknown")
        floor_count = building_data.get("floors", 1)

        # Convert categorical variables
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

        # Extract prediction-specific features
        if prediction_type == PredictionType.COMPLIANCE_RISK:
            # Features for compliance risk prediction
            complexity_score = building_data.get("complexity", 1)
            code_requirements = building_data.get("code_requirements", 0)
            jurisdiction_strictness = building_data.get("jurisdiction_strictness", 1)

            features = [
                building_area,
                building_height,
                building_type_code,
                occupancy_code,
                floor_count,
                complexity_score,
                code_requirements,
                jurisdiction_strictness,
            ]

        elif prediction_type == PredictionType.COST_ESTIMATE:
            # Features for cost estimation
            construction_type = building_data.get("construction_type", "unknown")
            site_conditions = building_data.get("site_conditions", 1)
            material_quality = building_data.get("material_quality", 2)

            construction_mapping = {
                "wood": 1,
                "steel": 2,
                "concrete": 3,
                "masonry": 4,
                "unknown": 0,
            }
            construction_code = construction_mapping.get(construction_type, 0)

            features = [
                building_area,
                building_height,
                building_type_code,
                occupancy_code,
                floor_count,
                construction_code,
                site_conditions,
                material_quality,
            ]

        elif prediction_type == PredictionType.CONSTRUCTION_TIME:
            # Features for construction time prediction
            project_complexity = building_data.get("complexity", 1)
            crew_size = building_data.get("crew_size", 10)
            weather_conditions = building_data.get("weather_conditions", 1)

            features = [
                building_area,
                building_height,
                building_type_code,
                occupancy_code,
                floor_count,
                project_complexity,
                crew_size,
                weather_conditions,
            ]

        elif prediction_type == PredictionType.MAINTENANCE_NEEDS:
            # Features for maintenance prediction
            building_age = building_data.get("building_age", 0)
            system_complexity = building_data.get("system_complexity", 1)
            usage_intensity = building_data.get("usage_intensity", 1)

            features = [
                building_area,
                building_height,
                building_type_code,
                occupancy_code,
                floor_count,
                building_age,
                system_complexity,
                usage_intensity,
            ]

        elif prediction_type == PredictionType.ENERGY_EFFICIENCY:
            # Features for energy efficiency prediction
            insulation_rating = building_data.get("insulation_rating", 1)
            hvac_efficiency = building_data.get("hvac_efficiency", 1)
            window_efficiency = building_data.get("window_efficiency", 1)

            features = [
                building_area,
                building_height,
                building_type_code,
                occupancy_code,
                floor_count,
                insulation_rating,
                hvac_efficiency,
                window_efficiency,
            ]

        elif prediction_type == PredictionType.SAFETY_RISK:
            # Features for safety risk prediction
            occupancy_load = building_data.get("occupancy_load", 1)
            emergency_systems = building_data.get("emergency_systems", False)
            fire_protection = building_data.get("fire_protection", 1)

            features = [
                building_area,
                building_height,
                building_type_code,
                occupancy_code,
                floor_count,
                occupancy_load,
                int(emergency_systems),
                fire_protection,
            ]

        else:
            # Default features
            features = [
                building_area,
                building_height,
                building_type_code,
                occupancy_code,
                floor_count,
            ]

        # Normalize features
        features = np.array(features, dtype=float)
        if np.max(features) > 0:
            features = features / np.max(features)

        return features.reshape(1, -1)

    def _generate_mock_prediction(
        self, building_data: Dict[str, Any], prediction_type: PredictionType
    ) -> Tuple[Union[float, str, bool], float]:
        """
        Generate mock prediction when no model is available

        Args:
            building_data: Building design data
            prediction_type: Type of prediction

        Returns:
            Tuple of (predicted_value, confidence_score)
        """
        building_area = building_data.get("area", 0)
        building_height = building_data.get("height", 0)
        building_type = building_data.get("type", "unknown")

        # Generate mock predictions based on building data
        if prediction_type == PredictionType.COMPLIANCE_RISK:
            # Risk score based on building complexity
            risk_score = min(1.0, (building_area / 10000) * (building_height / 30))
            return risk_score, 0.75

        elif prediction_type == PredictionType.COST_ESTIMATE:
            # Cost estimate based on area and type
            base_cost_per_sqft = {
                "residential": 150,
                "commercial": 200,
                "industrial": 250,
                "mixed": 180,
                "unknown": 200,
            }
            cost_per_sqft = base_cost_per_sqft.get(building_type, 200)
            total_cost = building_area * cost_per_sqft
            return total_cost, 0.8

        elif prediction_type == PredictionType.CONSTRUCTION_TIME:
            # Construction time in months
            base_time = building_area / 5000  # 5000 sqft per month
            complexity_factor = building_height / 20  # Height factor
            total_months = max(1, base_time * complexity_factor)
            return total_months, 0.7

        elif prediction_type == PredictionType.MAINTENANCE_NEEDS:
            # Maintenance needs score
            maintenance_score = min(
                1.0, (building_area / 20000) + (building_height / 50)
            )
            return maintenance_score, 0.65

        elif prediction_type == PredictionType.ENERGY_EFFICIENCY:
            # Energy efficiency score (0-100)
            efficiency_score = max(
                0, 100 - (building_area / 1000) - (building_height * 2)
            )
            return efficiency_score, 0.7

        elif prediction_type == PredictionType.SAFETY_RISK:
            # Safety risk score
            risk_score = min(1.0, (building_area / 15000) + (building_height / 40))
            return risk_score, 0.8

        else:
            return 0.5, 0.5

    def _generate_confidence_interval(
        self, predicted_value: float, confidence_score: float
    ) -> Dict[str, float]:
        """
        Generate confidence interval for prediction

        Args:
            predicted_value: Predicted value
            confidence_score: Confidence score

        Returns:
            Confidence interval dictionary
        """
        # Calculate margin of error based on confidence score
        margin_of_error = (1 - confidence_score) * predicted_value * 0.2

        return {
            "lower": max(0, predicted_value - margin_of_error),
            "upper": predicted_value + margin_of_error,
            "confidence_level": confidence_score,
        }

    def _generate_factors(
        self, building_data: Dict[str, Any], prediction_type: PredictionType
    ) -> List[Dict[str, Any]]:
        """
        Generate factors influencing the prediction

        Args:
            building_data: Building design data
            prediction_type: Type of prediction

        Returns:
            List of influencing factors
        """
        factors = []

        if prediction_type == PredictionType.COMPLIANCE_RISK:
            factors = [
                {
                    "factor": "building_area",
                    "value": building_data.get("area", 0),
                    "impact": "high",
                },
                {
                    "factor": "building_height",
                    "value": building_data.get("height", 0),
                    "impact": "high",
                },
                {
                    "factor": "complexity",
                    "value": building_data.get("complexity", 1),
                    "impact": "medium",
                },
                {
                    "factor": "code_requirements",
                    "value": building_data.get("code_requirements", 0),
                    "impact": "high",
                },
            ]

        elif prediction_type == PredictionType.COST_ESTIMATE:
            factors = [
                {
                    "factor": "building_area",
                    "value": building_data.get("area", 0),
                    "impact": "high",
                },
                {
                    "factor": "construction_type",
                    "value": building_data.get("construction_type", "unknown"),
                    "impact": "high",
                },
                {
                    "factor": "material_quality",
                    "value": building_data.get("material_quality", 2),
                    "impact": "medium",
                },
                {
                    "factor": "site_conditions",
                    "value": building_data.get("site_conditions", 1),
                    "impact": "medium",
                },
            ]

        elif prediction_type == PredictionType.CONSTRUCTION_TIME:
            factors = [
                {
                    "factor": "building_area",
                    "value": building_data.get("area", 0),
                    "impact": "high",
                },
                {
                    "factor": "complexity",
                    "value": building_data.get("complexity", 1),
                    "impact": "high",
                },
                {
                    "factor": "crew_size",
                    "value": building_data.get("crew_size", 10),
                    "impact": "medium",
                },
                {
                    "factor": "weather_conditions",
                    "value": building_data.get("weather_conditions", 1),
                    "impact": "low",
                },
            ]

        elif prediction_type == PredictionType.MAINTENANCE_NEEDS:
            factors = [
                {
                    "factor": "building_age",
                    "value": building_data.get("building_age", 0),
                    "impact": "high",
                },
                {
                    "factor": "system_complexity",
                    "value": building_data.get("system_complexity", 1),
                    "impact": "high",
                },
                {
                    "factor": "usage_intensity",
                    "value": building_data.get("usage_intensity", 1),
                    "impact": "medium",
                },
                {
                    "factor": "building_area",
                    "value": building_data.get("area", 0),
                    "impact": "medium",
                },
            ]

        elif prediction_type == PredictionType.ENERGY_EFFICIENCY:
            factors = [
                {
                    "factor": "insulation_rating",
                    "value": building_data.get("insulation_rating", 1),
                    "impact": "high",
                },
                {
                    "factor": "hvac_efficiency",
                    "value": building_data.get("hvac_efficiency", 1),
                    "impact": "high",
                },
                {
                    "factor": "window_efficiency",
                    "value": building_data.get("window_efficiency", 1),
                    "impact": "medium",
                },
                {
                    "factor": "building_area",
                    "value": building_data.get("area", 0),
                    "impact": "medium",
                },
            ]

        elif prediction_type == PredictionType.SAFETY_RISK:
            factors = [
                {
                    "factor": "occupancy_load",
                    "value": building_data.get("occupancy_load", 1),
                    "impact": "high",
                },
                {
                    "factor": "emergency_systems",
                    "value": building_data.get("emergency_systems", False),
                    "impact": "high",
                },
                {
                    "factor": "fire_protection",
                    "value": building_data.get("fire_protection", 1),
                    "impact": "high",
                },
                {
                    "factor": "building_height",
                    "value": building_data.get("height", 0),
                    "impact": "medium",
                },
            ]

        return factors

    def predict(self, request: PredictionRequest) -> PredictionResult:
        """
        Perform predictive analytics

        Args:
            request: Prediction request

        Returns:
            Prediction result
        """
        start_time = time.time()

        try:
            # Find active model for this prediction type
            active_models = self.model_manager.list_models(status=ModelStatus.ACTIVE)
            model_info = None

            for model in active_models:
                if request.prediction_type.value in model.model_name.lower():
                    model_info = model
                    break

            if not model_info:
                # Use mock prediction
                logger.warning(
                    f"No active model found for {request.prediction_type}, using mock prediction"
                )
                predicted_value, confidence_score = self._generate_mock_prediction(
                    request.building_data, request.prediction_type
                )
                model_version = "mock-1.0.0"
            else:
                # Get the model
                model = self.model_manager.get_model(model_info.model_id)
                if not model:
                    logger.error(f"Failed to load model: {model_info.model_id}")
                    predicted_value, confidence_score = self._generate_mock_prediction(
                        request.building_data, request.prediction_type
                    )
                    model_version = "mock-1.0.0"
                else:
                    # Extract features
                    features = self._extract_prediction_features(
                        request.building_data, request.prediction_type
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
                        confidence_score = 0.8

                    predicted_value = prediction[0] if len(prediction) > 0 else 0.5
                    model_version = model_info.version

            # Generate confidence interval if requested
            confidence_interval = None
            if request.include_confidence and isinstance(predicted_value, (int, float)):
                confidence_interval = self._generate_confidence_interval(
                    predicted_value, confidence_score
                )

            # Generate influencing factors
            factors = self._generate_factors(
                request.building_data, request.prediction_type
            )

            processing_time = time.time() - start_time

            return PredictionResult(
                prediction_type=request.prediction_type,
                predicted_value=predicted_value,
                confidence_score=confidence_score,
                confidence_interval=confidence_interval,
                factors=factors,
                model_version=model_version,
                processing_time=processing_time,
            )

        except Exception as e:
            logger.error(f"Error during prediction: {e}")
            processing_time = time.time() - start_time

            return PredictionResult(
                prediction_type=request.prediction_type,
                predicted_value=0.0,
                confidence_score=0.0,
                confidence_interval=None,
                factors=[],
                model_version="error",
                processing_time=processing_time,
            )

    def get_prediction_statistics(self) -> Dict[str, Any]:
        """Get prediction statistics"""
        active_models = self.model_manager.list_models(status=ModelStatus.ACTIVE)

        return {
            "active_models": len(active_models),
            "prediction_types": list(self.prediction_models.keys()),
            "model_versions": [model.version for model in active_models],
            "total_models": self.model_manager.get_total_models_count(),
        }
