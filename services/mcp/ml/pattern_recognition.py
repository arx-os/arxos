"""
Pattern Recognition for ML Integration

Provides AI-powered pattern recognition for building designs, violations,
optimizations, and other building-related patterns.
"""

import time
import logging
from typing import Dict, List, Any, Optional
import numpy as np
from datetime import datetime

from .models import PatternRequest, PatternResult, PatternType
from .model_manager import ModelManager, ModelStatus


logger = logging.getLogger(__name__)


class PatternRecognition:
    """AI-powered pattern recognition engine for building data"""

    def __init__(self, model_manager: ModelManager):
        """
        Initialize the pattern recognition engine

        Args:
            model_manager: Model manager instance
        """
        self.model_manager = model_manager
        self.pattern_models = {
            PatternType.DESIGN_PATTERN: "design_pattern_recognizer",
            PatternType.VIOLATION_PATTERN: "violation_pattern_recognizer",
            PatternType.OPTIMIZATION_PATTERN: "optimization_pattern_recognizer",
            PatternType.COST_PATTERN: "cost_pattern_recognizer",
            PatternType.TIME_PATTERN: "time_pattern_recognizer",
        }

        # Initialize pattern recognition models
        self._initialize_pattern_models()

        logger.info("Pattern Recognition initialized")

    def _initialize_pattern_models(self) -> None:
        """Initialize pattern recognition models"""
        try:
            # Register sample pattern recognition models if available
            # In a real implementation, these would be trained models
            logger.info("Initializing pattern recognition models")

        except Exception as e:
            logger.warning(f"Failed to initialize pattern recognition models: {e}")

    def _extract_pattern_features(
        self, building_data: Dict[str, Any], pattern_type: PatternType
    ) -> np.ndarray:
        """
        Extract features for pattern recognition

        Args:
            building_data: Building design data
            pattern_type: Type of pattern to recognize

        Returns:
            Feature array for pattern recognition model
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

        # Extract pattern-specific features
        if pattern_type == PatternType.DESIGN_PATTERN:
            # Features for design pattern recognition
            complexity_score = building_data.get("complexity", 1)
            design_elements = building_data.get("design_elements", 0)
            architectural_style = building_data.get("architectural_style", "unknown")

            style_mapping = {
                "modern": 1,
                "traditional": 2,
                "contemporary": 3,
                "unknown": 0,
            }
            style_code = style_mapping.get(architectural_style, 0)

            features = [
                building_area,
                building_height,
                building_type_code,
                occupancy_code,
                floor_count,
                complexity_score,
                design_elements,
                style_code,
            ]

        elif pattern_type == PatternType.VIOLATION_PATTERN:
            # Features for violation pattern recognition
            code_violations = building_data.get("code_violations", 0)
            compliance_score = building_data.get("compliance_score", 1)
            inspection_history = building_data.get("inspection_history", 0)

            features = [
                building_area,
                building_height,
                building_type_code,
                occupancy_code,
                floor_count,
                code_violations,
                compliance_score,
                inspection_history,
            ]

        elif pattern_type == PatternType.OPTIMIZATION_PATTERN:
            # Features for optimization pattern recognition
            efficiency_score = building_data.get("efficiency_score", 1)
            cost_effectiveness = building_data.get("cost_effectiveness", 1)
            sustainability_score = building_data.get("sustainability_score", 1)

            features = [
                building_area,
                building_height,
                building_type_code,
                occupancy_code,
                floor_count,
                efficiency_score,
                cost_effectiveness,
                sustainability_score,
            ]

        elif pattern_type == PatternType.COST_PATTERN:
            # Features for cost pattern recognition
            construction_cost = building_data.get("construction_cost", 0)
            material_cost = building_data.get("material_cost", 0)
            labor_cost = building_data.get("labor_cost", 0)

            features = [
                building_area,
                building_height,
                building_type_code,
                occupancy_code,
                floor_count,
                construction_cost,
                material_cost,
                labor_cost,
            ]

        elif pattern_type == PatternType.TIME_PATTERN:
            # Features for time pattern recognition
            construction_time = building_data.get("construction_time", 0)
            planning_time = building_data.get("planning_time", 0)
            approval_time = building_data.get("approval_time", 0)

            features = [
                building_area,
                building_height,
                building_type_code,
                occupancy_code,
                floor_count,
                construction_time,
                planning_time,
                approval_time,
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

    def _generate_mock_patterns(
        self, building_data: Dict[str, Any], pattern_type: PatternType
    ) -> List[Dict[str, Any]]:
        """
        Generate mock patterns when no model is available

        Args:
            building_data: Building design data
            pattern_type: Type of pattern to recognize

        Returns:
            List of recognized patterns
        """
        patterns = []
        building_area = building_data.get("area", 0)
        building_height = building_data.get("height", 0)
        building_type = building_data.get("type", "unknown")

        if pattern_type == PatternType.DESIGN_PATTERN:
            if building_area > 5000:
                patterns.append(
                    {
                        "pattern_id": "large_building_design",
                        "name": "Large Building Design Pattern",
                        "description": "Common design patterns for buildings over 5000 sqft",
                        "confidence": 0.85,
                        "category": "size_based",
                        "applicability": "large_buildings",
                    }
                )

            if building_type == "commercial":
                patterns.append(
                    {
                        "pattern_id": "commercial_design",
                        "name": "Commercial Building Design Pattern",
                        "description": "Standard design patterns for commercial buildings",
                        "confidence": 0.80,
                        "category": "type_based",
                        "applicability": "commercial_buildings",
                    }
                )

        elif pattern_type == PatternType.VIOLATION_PATTERN:
            if building_height > 25:
                patterns.append(
                    {
                        "pattern_id": "height_violation_risk",
                        "name": "Height Violation Risk Pattern",
                        "description": "Common violations in tall buildings",
                        "confidence": 0.75,
                        "category": "compliance_risk",
                        "severity": "high",
                    }
                )

            if building_area > 10000:
                patterns.append(
                    {
                        "pattern_id": "area_violation_risk",
                        "name": "Area Violation Risk Pattern",
                        "description": "Common violations in large buildings",
                        "confidence": 0.70,
                        "category": "compliance_risk",
                        "severity": "medium",
                    }
                )

        elif pattern_type == PatternType.OPTIMIZATION_PATTERN:
            if building_type == "commercial":
                patterns.append(
                    {
                        "pattern_id": "commercial_optimization",
                        "name": "Commercial Building Optimization",
                        "description": "Optimization patterns for commercial buildings",
                        "confidence": 0.80,
                        "category": "efficiency",
                        "impact": "high",
                    }
                )

            if building_area > 8000:
                patterns.append(
                    {
                        "pattern_id": "large_building_optimization",
                        "name": "Large Building Optimization",
                        "description": "Optimization patterns for large buildings",
                        "confidence": 0.75,
                        "category": "efficiency",
                        "impact": "medium",
                    }
                )

        elif pattern_type == PatternType.COST_PATTERN:
            if building_type == "residential":
                patterns.append(
                    {
                        "pattern_id": "residential_cost_pattern",
                        "name": "Residential Cost Pattern",
                        "description": "Typical cost patterns for residential buildings",
                        "confidence": 0.85,
                        "category": "cost_analysis",
                        "trend": "stable",
                    }
                )

        elif pattern_type == PatternType.TIME_PATTERN:
            if building_area > 6000:
                patterns.append(
                    {
                        "pattern_id": "large_project_timeline",
                        "name": "Large Project Timeline Pattern",
                        "description": "Typical timeline patterns for large projects",
                        "confidence": 0.80,
                        "category": "project_management",
                        "duration": "extended",
                    }
                )

        return patterns

    def _generate_similarity_scores(
        self, patterns: List[Dict[str, Any]]
    ) -> List[float]:
        """
        Generate similarity scores for patterns

        Args:
            patterns: List of patterns

        Returns:
            List of similarity scores
        """
        # Generate mock similarity scores based on pattern confidence
        return [pattern.get("confidence", 0.5) for pattern in patterns]

    def _generate_recommendations(
        self, patterns: List[Dict[str, Any]], pattern_type: PatternType
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations based on recognized patterns

        Args:
            patterns: List of recognized patterns
            pattern_type: Type of pattern

        Returns:
            List of recommendations
        """
        recommendations = []

        for pattern in patterns:
            if pattern_type == PatternType.DESIGN_PATTERN:
                if "large_building" in pattern.get("pattern_id", ""):
                    recommendations.append(
                        {
                            "type": "design",
                            "title": "Consider modular design",
                            "description": "Large buildings benefit from modular design approaches",
                            "impact": "medium",
                            "effort": "low",
                            "priority": "medium",
                        }
                    )

            elif pattern_type == PatternType.VIOLATION_PATTERN:
                if "height_violation" in pattern.get("pattern_id", ""):
                    recommendations.append(
                        {
                            "type": "compliance",
                            "title": "Review height requirements",
                            "description": "Consider fire-resistive construction for tall buildings",
                            "impact": "high",
                            "effort": "medium",
                            "priority": "high",
                        }
                    )

            elif pattern_type == PatternType.OPTIMIZATION_PATTERN:
                if "commercial_optimization" in pattern.get("pattern_id", ""):
                    recommendations.append(
                        {
                            "type": "optimization",
                            "title": "Energy efficiency optimization",
                            "description": "Consider energy-efficient systems for commercial buildings",
                            "impact": "high",
                            "effort": "medium",
                            "priority": "high",
                        }
                    )

        return recommendations

    def recognize_patterns(self, request: PatternRequest) -> PatternResult:
        """
        Perform pattern recognition on building data

        Args:
            request: Pattern recognition request

        Returns:
            Pattern recognition result
        """
        start_time = time.time()

        try:
            # Find active model for this pattern type
            active_models = self.model_manager.list_models(status=ModelStatus.ACTIVE)
            model_info = None

            for model in active_models:
                if request.pattern_type.value in model.model_name.lower():
                    model_info = model
                    break

            if not model_info:
                # Use mock pattern recognition
                logger.warning(
                    f"No active model found for {request.pattern_type}, using mock pattern recognition"
                )
                patterns_found = self._generate_mock_patterns(
                    request.building_data, request.pattern_type
                )
                model_version = "mock-1.0.0"
            else:
                # Get the model
                model = self.model_manager.get_model(model_info.model_id)
                if not model:
                    logger.error(f"Failed to load model: {model_info.model_id}")
                    patterns_found = self._generate_mock_patterns(
                        request.building_data, request.pattern_type
                    )
                    model_version = "mock-1.0.0"
                else:
                    # Extract features
                    features = self._extract_pattern_features(
                        request.building_data, request.pattern_type
                    )

                    # Make prediction (mock for now)
                    # In a real implementation, this would use actual pattern recognition models
                    patterns_found = self._generate_mock_patterns(
                        request.building_data, request.pattern_type
                    )
                    model_version = model_info.version

            # Generate similarity scores
            similarity_scores = self._generate_similarity_scores(patterns_found)

            # Filter patterns by similarity threshold
            filtered_patterns = []
            filtered_scores = []
            for pattern, score in zip(patterns_found, similarity_scores):
                if score >= request.similarity_threshold:
                    filtered_patterns.append(pattern)
                    filtered_scores.append(score)

            # Generate recommendations
            recommendations = self._generate_recommendations(
                filtered_patterns, request.pattern_type
            )

            processing_time = time.time() - start_time

            return PatternResult(
                pattern_type=request.pattern_type,
                patterns_found=filtered_patterns,
                similarity_scores=filtered_scores,
                recommendations=recommendations,
                model_version=model_version,
                processing_time=processing_time,
            )

        except Exception as e:
            logger.error(f"Error during pattern recognition: {e}")
            processing_time = time.time() - start_time

            return PatternResult(
                pattern_type=request.pattern_type,
                patterns_found=[],
                similarity_scores=[],
                recommendations=[],
                model_version="error",
                processing_time=processing_time,
            )

    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get pattern recognition statistics"""
        active_models = self.model_manager.list_models(status=ModelStatus.ACTIVE)

        return {
            "active_models": len(active_models),
            "pattern_types": list(self.pattern_models.keys()),
            "model_versions": [model.version for model in active_models],
            "total_models": self.model_manager.get_total_models_count(),
        }
