"""
Mock ArxLogic Service

A development version that doesn't require SQLAlchemy dependencies.
This allows the ArxLogic service to be developed and tested without database dependencies.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationMetrics:
    """Validation metrics for building objects"""

    simulation_pass_rate: float
    ai_accuracy_rate: float
    system_completion_score: float
    error_propagation_score: float
    complexity_score: float
    validation_notes: str


@dataclass
class ValidationResult:
    """Result of building object validation"""

    is_valid: bool
    validation_score: float
    metrics: ValidationMetrics
    recommendations: List[str]
    errors: List[str]
    warnings: List[str]


class MockArxLogicService:
    """
    Mock ArxLogic Service for AI-powered building object validation

    Development version that simulates AI validation without requiring external dependencies.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # System type complexity weights
        self.system_complexity_weights = {
            "electrical": 1.0,
            "plumbing": 1.2,
            "hvac": 1.5,
            "fire_alarm": 1.7,
            "security": 2.0,
            "lighting": 1.1,
            "mechanical": 1.3,
            "structural": 1.8,
            "custom": 1.0,
        }

        # Validation thresholds
        self.validation_thresholds = {
            "min_simulation_pass_rate": 0.7,
            "min_ai_accuracy_rate": 0.8,
            "min_system_completion_score": 0.6,
            "max_error_propagation_score": 0.3,
        }

        logger.info("Mock ArxLogic Service initialized")

    async def validate_building_object(
        self, object_data: Dict[str, Any], system_type: str
    ) -> Dict[str, Any]:
        """
        Validate a building object using AI and technical analysis (mock)

        Args:
            object_data: Building object data
            system_type: Type of building system

        Returns:
            Dictionary with validation results and metrics
        """
        try:
            self.logger.info(
                f"Mock validating building object for system type: {system_type}"
            )

            # Mock comprehensive validation
            validation_result = await self._perform_mock_validation(
                object_data, system_type
            )

            # Calculate overall validation score
            validation_score = self._calculate_validation_score(
                validation_result.metrics
            )

            # Determine if object is valid
            is_valid = validation_score >= 0.7

            return {
                "is_valid": is_valid,
                "validation_score": validation_score,
                "simulation_pass_rate": validation_result.metrics.simulation_pass_rate,
                "ai_accuracy_rate": validation_result.metrics.ai_accuracy_rate,
                "system_completion_score": validation_result.metrics.system_completion_score,
                "error_propagation_score": validation_result.metrics.error_propagation_score,
                "complexity_score": validation_result.metrics.complexity_score,
                "validation_notes": validation_result.metrics.validation_notes,
                "recommendations": validation_result.recommendations,
                "errors": validation_result.errors,
                "warnings": validation_result.warnings,
            }

        except Exception as e:
            self.logger.error(f"Error in mock validation: {str(e)}")
            return {
                "is_valid": False,
                "validation_score": 0.0,
                "simulation_pass_rate": 0.0,
                "ai_accuracy_rate": 0.0,
                "system_completion_score": 0.0,
                "error_propagation_score": 1.0,
                "complexity_score": 1.0,
                "validation_notes": f"Mock validation failed: {str(e)}",
                "recommendations": [],
                "errors": [f"Mock validation error: {str(e)}"],
                "warnings": [],
            }

    async def _perform_mock_validation(
        self, object_data: Dict[str, Any], system_type: str
    ) -> ValidationResult:
        """
        Perform mock comprehensive validation of building object
        """
        # Initialize validation components
        errors = []
        warnings = []
        recommendations = []

        # Mock validation results
        simulation_pass_rate = 0.85
        ai_accuracy_rate = 0.88
        system_completion_score = 0.92
        error_propagation_score = 0.12
        complexity_score = self.system_complexity_weights.get(system_type.lower(), 1.0)

        # Generate mock validation notes
        validation_notes = f"Mock validation completed for {system_type} system"

        # Create metrics
        metrics = ValidationMetrics(
            simulation_pass_rate=simulation_pass_rate,
            ai_accuracy_rate=ai_accuracy_rate,
            system_completion_score=system_completion_score,
            error_propagation_score=error_propagation_score,
            complexity_score=complexity_score,
            validation_notes=validation_notes,
        )

        return ValidationResult(
            is_valid=len(errors) == 0,
            validation_score=0.0,  # Will be calculated separately
            metrics=metrics,
            recommendations=recommendations,
            errors=errors,
            warnings=warnings,
        )

    def _calculate_validation_score(self, metrics: ValidationMetrics) -> float:
        """
        Calculate overall validation score from metrics
        """
        weights = {
            "simulation": 0.35,
            "accuracy": 0.30,
            "completion": 0.20,
            "propagation": 0.15,
        }

        # Convert error propagation to positive score (lower propagation = higher score)
        propagation_score = 1.0 - metrics.error_propagation_score

        validation_score = (
            metrics.simulation_pass_rate * weights["simulation"]
            + metrics.ai_accuracy_rate * weights["accuracy"]
            + metrics.system_completion_score * weights["completion"]
            + propagation_score * weights["propagation"]
        )

        return min(max(validation_score, 0.0), 1.0)


# Global mock ArxLogic service instance
mock_arxlogic_service = MockArxLogicService()
