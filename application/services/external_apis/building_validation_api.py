"""
Building Validation API Integration

This module provides integration with external building validation services
for structural, electrical, mechanical, and other compliance checks.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from domain.mcp_engineering_entities import (
    BuildingData,
    ValidationResult,
    ValidationType,
    ValidationStatus,
    ComplianceIssue,
    AIRecommendation,
)
from infrastructure.services.mcp_engineering_client import (
    MCPEngineeringHTTPClient,
    APIConfig,
)


class BuildingValidationAPI:
    """
    Building validation API integration service.

    Provides integration with external building validation services for:
    - Structural compliance validation
    - Electrical compliance validation
    - Mechanical compliance validation
    - Plumbing compliance validation
    - Fire safety compliance validation
    - Accessibility compliance validation
    - Energy efficiency validation
    """

    def __init__(self, client: MCPEngineeringHTTPClient):
        """Initialize the building validation API."""
        self.client = client
        self.logger = logging.getLogger(__name__)

    async def validate_structural_compliance(
        self, building_data: BuildingData
    ) -> ValidationResult:
        """
        Validate structural compliance with external service.

        Args:
            building_data: Building data to validate

        Returns:
            ValidationResult with structural compliance results
        """
        self.logger.info(
            f"Starting structural compliance validation for building: {building_data.building_type}"
        )

        try:
            result = await self.client.validate_building(
                building_data, ValidationType.STRUCTURAL
            )

            self.logger.info(
                f"Structural validation completed: {result.status.value} "
                f"with {len(result.issues)} issues and {len(result.suggestions)} suggestions"
            )

            return result

        except Exception as e:
            self.logger.error(f"Structural validation failed: {e}")
            return ValidationResult(
                building_data=building_data,
                validation_type=ValidationType.STRUCTURAL,
                status=ValidationStatus.ERROR,
                confidence_score=0.0,
                issues=[],
                suggestions=[],
                error_message=str(e),
            )

    async def validate_electrical_compliance(
        self, building_data: BuildingData
    ) -> ValidationResult:
        """
        Validate electrical compliance with external service.

        Args:
            building_data: Building data to validate

        Returns:
            ValidationResult with electrical compliance results
        """
        self.logger.info(
            f"Starting electrical compliance validation for building: {building_data.building_type}"
        )

        try:
            result = await self.client.validate_building(
                building_data, ValidationType.ELECTRICAL
            )

            self.logger.info(
                f"Electrical validation completed: {result.status.value} "
                f"with {len(result.issues)} issues and {len(result.suggestions)} suggestions"
            )

            return result

        except Exception as e:
            self.logger.error(f"Electrical validation failed: {e}")
            return ValidationResult(
                building_data=building_data,
                validation_type=ValidationType.ELECTRICAL,
                status=ValidationStatus.ERROR,
                confidence_score=0.0,
                issues=[],
                suggestions=[],
                error_message=str(e),
            )

    async def validate_mechanical_compliance(
        self, building_data: BuildingData
    ) -> ValidationResult:
        """
        Validate mechanical compliance with external service.

        Args:
            building_data: Building data to validate

        Returns:
            ValidationResult with mechanical compliance results
        """
        self.logger.info(
            f"Starting mechanical compliance validation for building: {building_data.building_type}"
        )

        try:
            result = await self.client.validate_building(
                building_data, ValidationType.MECHANICAL
            )

            self.logger.info(
                f"Mechanical validation completed: {result.status.value} "
                f"with {len(result.issues)} issues and {len(result.suggestions)} suggestions"
            )

            return result

        except Exception as e:
            self.logger.error(f"Mechanical validation failed: {e}")
            return ValidationResult(
                building_data=building_data,
                validation_type=ValidationType.MECHANICAL,
                status=ValidationStatus.ERROR,
                confidence_score=0.0,
                issues=[],
                suggestions=[],
                error_message=str(e),
            )

    async def validate_plumbing_compliance(
        self, building_data: BuildingData
    ) -> ValidationResult:
        """
        Validate plumbing compliance with external service.

        Args:
            building_data: Building data to validate

        Returns:
            ValidationResult with plumbing compliance results
        """
        self.logger.info(
            f"Starting plumbing compliance validation for building: {building_data.building_type}"
        )

        try:
            result = await self.client.validate_building(
                building_data, ValidationType.PLUMBING
            )

            self.logger.info(
                f"Plumbing validation completed: {result.status.value} "
                f"with {len(result.issues)} issues and {len(result.suggestions)} suggestions"
            )

            return result

        except Exception as e:
            self.logger.error(f"Plumbing validation failed: {e}")
            return ValidationResult(
                building_data=building_data,
                validation_type=ValidationType.PLUMBING,
                status=ValidationStatus.ERROR,
                confidence_score=0.0,
                issues=[],
                suggestions=[],
                error_message=str(e),
            )

    async def validate_fire_safety_compliance(
        self, building_data: BuildingData
    ) -> ValidationResult:
        """
        Validate fire safety compliance with external service.

        Args:
            building_data: Building data to validate

        Returns:
            ValidationResult with fire safety compliance results
        """
        self.logger.info(
            f"Starting fire safety compliance validation for building: {building_data.building_type}"
        )

        try:
            result = await self.client.validate_building(
                building_data, ValidationType.FIRE
            )

            self.logger.info(
                f"Fire safety validation completed: {result.status.value} "
                f"with {len(result.issues)} issues and {len(result.suggestions)} suggestions"
            )

            return result

        except Exception as e:
            self.logger.error(f"Fire safety validation failed: {e}")
            return ValidationResult(
                building_data=building_data,
                validation_type=ValidationType.FIRE,
                status=ValidationStatus.ERROR,
                confidence_score=0.0,
                issues=[],
                suggestions=[],
                error_message=str(e),
            )

    async def validate_accessibility_compliance(
        self, building_data: BuildingData
    ) -> ValidationResult:
        """
        Validate accessibility compliance with external service.

        Args:
            building_data: Building data to validate

        Returns:
            ValidationResult with accessibility compliance results
        """
        self.logger.info(
            f"Starting accessibility compliance validation for building: {building_data.building_type}"
        )

        try:
            result = await self.client.validate_building(
                building_data, ValidationType.ACCESSIBILITY
            )

            self.logger.info(
                f"Accessibility validation completed: {result.status.value} "
                f"with {len(result.issues)} issues and {len(result.suggestions)} suggestions"
            )

            return result

        except Exception as e:
            self.logger.error(f"Accessibility validation failed: {e}")
            return ValidationResult(
                building_data=building_data,
                validation_type=ValidationType.ACCESSIBILITY,
                status=ValidationStatus.ERROR,
                confidence_score=0.0,
                issues=[],
                suggestions=[],
                error_message=str(e),
            )

    async def validate_energy_efficiency(
        self, building_data: BuildingData
    ) -> ValidationResult:
        """
        Validate energy efficiency with external service.

        Args:
            building_data: Building data to validate

        Returns:
            ValidationResult with energy efficiency results
        """
        self.logger.info(
            f"Starting energy efficiency validation for building: {building_data.building_type}"
        )

        try:
            result = await self.client.validate_building(
                building_data, ValidationType.ENERGY
            )

            self.logger.info(
                f"Energy efficiency validation completed: {result.status.value} "
                f"with {len(result.issues)} issues and {len(result.suggestions)} suggestions"
            )

            return result

        except Exception as e:
            self.logger.error(f"Energy efficiency validation failed: {e}")
            return ValidationResult(
                building_data=building_data,
                validation_type=ValidationType.ENERGY,
                status=ValidationStatus.ERROR,
                confidence_score=0.0,
                issues=[],
                suggestions=[],
                error_message=str(e),
            )

    async def validate_all_compliance_types(
        self, building_data: BuildingData
    ) -> Dict[ValidationType, ValidationResult]:
        """
        Validate all compliance types for a building.

        Args:
            building_data: Building data to validate

        Returns:
            Dictionary mapping validation types to results
        """
        self.logger.info(
            f"Starting comprehensive validation for building: {building_data.building_type}"
        )

        validation_types = [
            ValidationType.STRUCTURAL,
            ValidationType.ELECTRICAL,
            ValidationType.MECHANICAL,
            ValidationType.PLUMBING,
            ValidationType.FIRE,
            ValidationType.ACCESSIBILITY,
            ValidationType.ENERGY,
        ]

        results = {}

        # Run validations concurrently for better performance
        import asyncio

        tasks = []

        for validation_type in validation_types:
            if validation_type == ValidationType.STRUCTURAL:
                task = self.validate_structural_compliance(building_data)
            elif validation_type == ValidationType.ELECTRICAL:
                task = self.validate_electrical_compliance(building_data)
            elif validation_type == ValidationType.MECHANICAL:
                task = self.validate_mechanical_compliance(building_data)
            elif validation_type == ValidationType.PLUMBING:
                task = self.validate_plumbing_compliance(building_data)
            elif validation_type == ValidationType.FIRE:
                task = self.validate_fire_safety_compliance(building_data)
            elif validation_type == ValidationType.ACCESSIBILITY:
                task = self.validate_accessibility_compliance(building_data)
            elif validation_type == ValidationType.ENERGY:
                task = self.validate_energy_efficiency(building_data)
            else:
                continue

            tasks.append(task)

        # Wait for all validations to complete
        validation_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Map results to validation types
        for i, result in enumerate(validation_results):
            if isinstance(result, Exception):
                self.logger.error(
                    f"Validation failed for {validation_types[i]}: {result}"
                )
                results[validation_types[i]] = ValidationResult(
                    building_data=building_data,
                    validation_type=validation_types[i],
                    status=ValidationStatus.ERROR,
                    confidence_score=0.0,
                    issues=[],
                    suggestions=[],
                    error_message=str(result),
                )
            else:
                results[validation_types[i]] = result

        self.logger.info(
            f"Comprehensive validation completed with {len(results)} validation types"
        )

        return results

    def get_validation_summary(
        self, results: Dict[ValidationType, ValidationResult]
    ) -> Dict[str, Any]:
        """
        Generate a summary of validation results.

        Args:
            results: Dictionary of validation results

        Returns:
            Summary dictionary with statistics
        """
        total_issues = 0
        total_suggestions = 0
        passed_validations = 0
        failed_validations = 0
        error_validations = 0

        for validation_type, result in results.items():
            total_issues += len(result.issues)
            total_suggestions += len(result.suggestions)

            if result.status == ValidationStatus.PASS:
                passed_validations += 1
            elif result.status == ValidationStatus.FAIL:
                failed_validations += 1
            elif result.status == ValidationStatus.ERROR:
                error_validations += 1

        return {
            "total_validations": len(results),
            "passed_validations": passed_validations,
            "failed_validations": failed_validations,
            "error_validations": error_validations,
            "total_issues": total_issues,
            "total_suggestions": total_suggestions,
            "overall_status": (
                "pass" if failed_validations == 0 and error_validations == 0 else "fail"
            ),
        }
